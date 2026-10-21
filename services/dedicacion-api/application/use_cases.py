# application/use_cases.py
"""Casos de uso del servicio de dedicación.

Cada caso de uso recibe una UnitOfWork ya abierta, aplica las reglas de
negocio y deja al llamante (capa API) la gestión del ciclo de vida.
"""
from __future__ import annotations

import dataclasses
import logging
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from domain.deshacer import deshacer_permitido
from domain.empresas import visible_en_empresa
from domain.errors import (
    DeshacerAjeno,
    IncidenciaInvalida,
    LineaNoEncontrada,
    LineasInvalidas,
    NadaQueDeshacer,
    ObraNoValida,
    PeriodoCerrado,
    PeriodoNoEncontrado,
    TrabajadorNoEncontrado,
)
from domain.estados import calcular_estado, completar_hasta_100, resumir
from domain.incidencias import completar_dias, identificar, validar_incidencias
from domain.models import (
    CuadranteTrabajador,
    Empresa,
    EstadoPeriodo,
    EstadoTrabajador,
    FiltroEmpresa,
    Incidencia,
    Linea,
    Obra,
    Periodo,
    ResultadoCompletado,
    ResultadoCompletarTrabajador,
    ResultadoCopia,
    ResumenPeriodo,
    TipoEvento,
    TipoIncidencia,
    Trabajador,
)
from domain.ports import SigridGateway, UnitOfWork, UniversosGateway

from application.filtros_maestros import CRITERIO_VACIO, CriterioActivoRecurso

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Lectura del cuadrante
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Cuadrante:
    periodo: Periodo
    obras: list[Obra]
    filas: list[CuadranteTrabajador]
    resumen: ResumenPeriodo
    empresa: int


class ObtenerCuadrante:
    """Cuadrante de la empresa elegida: sus trabajadores visibles, con TODAS
    sus líneas (F-024), y las obras de la empresa de las obras, sea cual sea
    la elegida (F-034, R1). `puede_deshacer` es el de `usuario` (F-027)."""

    def ejecutar(
        self, uow: UnitOfWork, anio: int, mes: int, filtro: FiltroEmpresa,
        *, usuario: str,
    ) -> Cuadrante:
        periodo_id, periodo = _periodo_o_error(uow, anio, mes)
        filas = _filas_de_empresa(uow, periodo_id, filtro)
        obras = [
            o
            for o in uow.obras.listar_para_periodo(periodo_id)
            if o.empresa == filtro.empresa_obras
        ]
        autores = uow.eventos.autores_ultimo_pendiente(periodo_id)
        incidencias = uow.incidencias.de_periodo(periodo_id)  # F-030, R21
        for fila in filas:
            fila.puede_deshacer = deshacer_permitido(
                autores.get(fila.trabajador.ide), usuario
            )
            fila.incidencias = tuple(incidencias.get(fila.trabajador.ide, ()))
        return Cuadrante(
            periodo=periodo,
            obras=obras,
            filas=filas,
            resumen=resumir(filas),
            empresa=filtro.empresa,
        )


class ObtenerFilaTrabajador:
    """Fila de un trabajador con todas sus líneas; el resumen es el de la
    empresa del filtro y `puede_deshacer`, el de `usuario` (F-027)."""

    def ejecutar(
        self,
        uow: UnitOfWork,
        anio: int,
        mes: int,
        trabajador_ide: int,
        *,
        filtro: FiltroEmpresa,
        usuario: str,
    ) -> tuple[CuadranteTrabajador, ResumenPeriodo]:
        periodo_id, _ = _periodo_o_error(uow, anio, mes)
        trabajador = _trabajador_o_error(uow, trabajador_ide)
        pendiente = uow.eventos.ultimo_pendiente(periodo_id, trabajador_ide)
        fila = CuadranteTrabajador(
            trabajador=trabajador,
            lineas=uow.asignaciones.lineas_de_trabajador(periodo_id, trabajador_ide),
            puede_deshacer=deshacer_permitido(
                pendiente.usuario if pendiente else None, usuario
            ),
            incidencias=tuple(
                uow.incidencias.de_trabajador(periodo_id, trabajador_ide)),
        )
        resumen = _resumen_periodo(uow, periodo_id, filtro)
        return fila, resumen


# ----------------------------------------------------------------------
# Escritura de asignaciones
# ----------------------------------------------------------------------
class GuardarAsignaciones:
    def ejecutar(
        self,
        uow: UnitOfWork,
        anio: int,
        mes: int,
        trabajador_ide: int,
        lineas_entrada: list[dict[str, Any]],
        usuario: str,
        *,
        filtro: FiltroEmpresa,
    ) -> tuple[CuadranteTrabajador, ResumenPeriodo]:
        periodo_id, periodo = _periodo_abierto_o_error(uow, anio, mes)
        trabajador = _trabajador_o_error(uow, trabajador_ide)
        lineas = _validar_lineas(uow, lineas_entrada)

        antes = uow.asignaciones.lineas_de_trabajador(periodo_id, trabajador_ide)
        _rechazar_nuevas_no_ofrecibles(uow, lineas, antes)
        # F-050 (R14): guardar la fila no cambia la partida de ninguna línea
        # que ya existía; la nueva entra automática.
        lineas = _conservar_partidas(lineas, antes)
        if _snapshot(antes) != _snapshot(lineas):
            uow.asignaciones.reemplazar(periodo_id, trabajador_ide, lineas, usuario)
            uow.eventos.registrar(
                periodo_id,
                trabajador_ide,
                TipoEvento.GUARDAR,
                usuario,
                _snapshot(antes),
                _snapshot(lineas),
            )
        uow.commit()
        return ObtenerFilaTrabajador().ejecutar(
            uow, anio, mes, trabajador_ide, filtro=filtro, usuario=usuario
        )


class GuardarIncidencias:
    """Sustituye las incidencias del trabajador en el periodo (F-030,
    R17-R19, docs/ARCHITECTURE.md#regla-incidencia) y deja un evento
    `INCIDENCIAS`, deshacible como cualquier otro (R20). No toca sus líneas
    de % ni cuenta para el 100 % (R2, R22).

    Todo o nada: periodo inexistente (404) o cerrado (409), trabajador
    inexistente (404) o una incidencia que no vale (422, `IncidenciaInvalida`:
    código no activo, obra que no se ofrece como normal o entrada VAR, días
    fuera del mes, `desde > hasta` o dos que comparten días). Un día vacío se
    completa con `completar_dias` (D2). Si no cambia nada, ni escribe ni deja
    evento.

    Anexo R30: con `id`, la incidencia es la guardada (conserva fila y
    traza); un `id` ajeno o una registrada con otra obra o código es 422, y
    la registrada que no viene queda `quitada` (`identificar`, R36, R38).
    Las quitadas no cuentan en los solapes. El evento guarda `id` y
    `quitada` (R47)."""

    def ejecutar(
        self,
        uow: UnitOfWork,
        anio: int,
        mes: int,
        trabajador_ide: int,
        entrada: list[dict[str, Any]],
        usuario: str,
        *,
        filtro: FiltroEmpresa,
    ) -> tuple[CuadranteTrabajador, ResumenPeriodo]:
        periodo_id, _ = _periodo_abierto_o_error(uow, anio, mes)
        _trabajador_o_error(uow, trabajador_ide)
        brutas = [_parsear_incidencia(b) for b in entrada]
        activos = {t.codigo for t in uow.tipos_incidencia.activos()}
        for inc in brutas:
            if inc.codigo not in activos:
                raise IncidenciaInvalida(
                    f"El código {inc.codigo} no es una incidencia activa")
        _validar_obras_incidencia(uow, periodo_id,
                                  {i.obra_ide for i in brutas}, filtro)
        despues = [
            dataclasses.replace(inc, dia_desde=desde, dia_hasta=hasta)
            for inc in brutas
            for desde, hasta in [completar_dias(inc.dia_desde, inc.dia_hasta,
                                                anio, mes)]
        ]
        antes = uow.incidencias.de_trabajador(periodo_id, trabajador_ide)
        previsto = identificar(despues, antes)
        validar_incidencias(despues, anio, mes)
        if _snapshot_incidencias(antes) != _snapshot_incidencias(previsto):
            uow.incidencias.reemplazar(periodo_id, trabajador_ide, despues,
                                       usuario)
            uow.eventos.registrar(
                periodo_id,
                trabajador_ide,
                TipoEvento.INCIDENCIAS,
                usuario,
                _snapshot_incidencias(antes),
                _snapshot_incidencias(uow.incidencias.de_trabajador(
                    periodo_id, trabajador_ide)),
            )
        uow.commit()
        return ObtenerFilaTrabajador().ejecutar(
            uow, anio, mes, trabajador_ide, filtro=filtro, usuario=usuario
        )


def _entero_estricto(valor: Any) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool)


def _parsear_incidencia(bruto: dict[str, Any]) -> Incidencia:
    """Una incidencia de la entrada (o de un snapshot): `obra_ide` entero,
    `codigo` con texto, días enteros o vacíos (`None`, aún sin completar),
    `id` entero o vacío (R36) y `quitada` booleana (solo en snapshots, R47)."""
    codigo = bruto.get("codigo")
    if not isinstance(codigo, str) or not codigo.strip():
        raise IncidenciaInvalida(f"Incidencia sin código: {bruto}")
    obra_ide = bruto.get("obra_ide")
    desde, hasta = bruto.get("dia_desde"), bruto.get("dia_hasta")
    id_, quitada = bruto.get("id"), bruto.get("quitada", False)
    if not _entero_estricto(obra_ide) or any(
            d is not None and not _entero_estricto(d)
            for d in (desde, hasta, id_)) or not isinstance(quitada, bool):
        raise IncidenciaInvalida(f"Incidencia inválida: {bruto}")
    return Incidencia(obra_ide=obra_ide, codigo=codigo.strip(),
                      dia_desde=desde, dia_hasta=hasta,  # type: ignore[arg-type]
                      id=id_, quitada=quitada)


def _validar_obras_incidencia(uow: UnitOfWork, periodo_id: int,
                              ides: set[int], filtro: FiltroEmpresa) -> None:
    """La obra de una incidencia es una obra NORMAL de la lista que ofrece el
    cuadrante: de la empresa de las obras, activa y que no sea una entrada
    VAR (F-030, R19, D7). Ni `Postv-` ni VAR: no son partes «de» la persona."""
    normales = {o.ide for o in uow.obras.listar_para_periodo(periodo_id)
                if o.empresa == filtro.empresa_obras and o.activa}
    for obra_ide in sorted(ides - normales):
        raise IncidenciaInvalida(
            f"La obra {obra_ide} no se ofrece como obra normal")
    for obra_ide in sorted(uow.obras.entradas_var(ides)):
        raise IncidenciaInvalida(
            f"La obra {obra_ide} es una entrada VAR: no admite incidencias")


def _snapshot_incidencias(incs: list[Incidencia]) -> list[dict[str, Any]]:
    """Lo que guarda un evento `INCIDENCIAS` (R20): `id` (vacío = nueva),
    obra, código, días y si está `quitada` (R47)."""
    return [
        {"id": i.id, "obra_ide": i.obra_ide, "codigo": i.codigo,
         "dia_desde": i.dia_desde, "dia_hasta": i.dia_hasta,
         "quitada": i.quitada}
        for i in sorted(incs, key=lambda i: (i.dia_desde, i.dia_hasta,
                                             i.obra_ide, i.codigo, i.quitada,
                                             i.id or 0))
    ]


class CambiarPartida:
    """Cambia SOLO la partida elegida de una línea (obra + modo) del
    trabajador y deja un evento `PARTIDA`, deshacible como cualquier otro
    (F-050, R13, docs/ARCHITECTURE.md#regla-partida). `partida` es
    `{ide, cod, res}` o None (automática). Una línea VAR tiene la partida
    fija: `ObraNoValida`. Si no cambia nada, ni escribe ni deja evento."""

    def ejecutar(
        self,
        uow: UnitOfWork,
        anio: int,
        mes: int,
        trabajador_ide: int,
        obra_ide: int,
        es_postventa: bool,
        partida: dict[str, Any] | None,
        usuario: str,
        *,
        filtro: FiltroEmpresa,
    ) -> tuple[CuadranteTrabajador, ResumenPeriodo]:
        periodo_id, _ = _periodo_abierto_o_error(uow, anio, mes)
        _trabajador_o_error(uow, trabajador_ide)
        antes = uow.asignaciones.lineas_de_trabajador(periodo_id, trabajador_ide)
        clave = (obra_ide, es_postventa)
        linea = next((ln for ln in antes if ln.clave() == clave), None)
        if linea is None:
            raise LineaNoEncontrada(
                f"El trabajador {trabajador_ide} no tiene la obra {obra_ide} "
                f"(postventa={es_postventa}) en el periodo"
            )
        if linea.partida_fija:
            raise ObraNoValida(
                f"La línea de la obra {obra_ide} es una entrada VAR: su "
                "partida es fija"
            )
        elegida = partida or {}
        despues = [
            dataclasses.replace(
                ln,
                partida_ide=elegida.get("ide"),
                partida_cod=elegida.get("cod"),
                partida_res=elegida.get("res"),
            )
            if ln is linea else ln
            for ln in antes
        ]
        if _snapshot(antes) != _snapshot(despues):
            uow.asignaciones.reemplazar(periodo_id, trabajador_ide, despues,
                                        usuario)
            uow.eventos.registrar(
                periodo_id,
                trabajador_ide,
                TipoEvento.PARTIDA,
                usuario,
                _snapshot(antes),
                _snapshot(despues),
            )
        uow.commit()
        return ObtenerFilaTrabajador().ejecutar(
            uow, anio, mes, trabajador_ide, filtro=filtro, usuario=usuario
        )


class DeshacerUltimaModificacion:
    """Restaura la fila al `snapshot_antes` de su último evento pendiente.

    Solo si ese evento es de `usuario` (F-027, decisión A,
    `domain/deshacer.py`): si es de otro, `DeshacerAjeno` sin tocar nada.
    Nunca se deshace un evento que no sea el último.

    F-030 (R20): despacha por el tipo del evento ANTES de leer su snapshot.
    Uno `INCIDENCIAS` devuelve las incidencias del trabajador a su
    `snapshot_antes` y no toca las líneas; los demás, las líneas, como hoy.
    """

    def ejecutar(
        self,
        uow: UnitOfWork,
        anio: int,
        mes: int,
        trabajador_ide: int,
        usuario: str,
        *,
        filtro: FiltroEmpresa,
    ) -> tuple[CuadranteTrabajador, ResumenPeriodo]:
        periodo_id, _ = _periodo_abierto_o_error(uow, anio, mes)
        _trabajador_o_error(uow, trabajador_ide)
        pendiente = uow.eventos.ultimo_pendiente(periodo_id, trabajador_ide)
        if pendiente is None:
            raise NadaQueDeshacer("No hay modificaciones que deshacer")
        if not deshacer_permitido(pendiente.usuario, usuario):
            raise DeshacerAjeno(
                "La última modificación de este trabajador es de "
                f"{pendiente.usuario}: solo puede deshacerla quien la hizo"
            )
        if pendiente.tipo == TipoEvento.INCIDENCIAS.value:
            uow.incidencias.reemplazar(
                periodo_id, trabajador_ide,
                [_parsear_incidencia(b) for b in pendiente.snapshot_antes],
                usuario)
        else:
            lineas = _validar_lineas(
                uow, pendiente.snapshot_antes, permitir_inactivas=True
            )
            uow.asignaciones.reemplazar(periodo_id, trabajador_ide, lineas,
                                        usuario)
        uow.eventos.marcar_deshecho(pendiente.id)
        uow.commit()
        return ObtenerFilaTrabajador().ejecutar(
            uow, anio, mes, trabajador_ide, filtro=filtro, usuario=usuario
        )


# ----------------------------------------------------------------------
# Copia desde el periodo anterior
# ----------------------------------------------------------------------
class CopiarPeriodoAnterior:
    """Rellena el periodo con las asignaciones del último periodo con datos.

    Solo actúa sobre trabajadores activos visibles en la empresa del filtro
    (F-024, R14) y SIN carga en el periodo destino: nunca pisa trabajo ya
    hecho. Las líneas no ofrecibles (`Linea.ofrecible`, F-025 R19) se
    omiten y se contabilizan.
    """

    def ejecutar(
        self,
        uow: UnitOfWork,
        anio: int,
        mes: int,
        usuario: str,
        *,
        filtro: FiltroEmpresa,
    ) -> ResultadoCopia:
        periodo_id, _ = _periodo_abierto_o_error(uow, anio, mes)
        origen = uow.periodos.anterior_con_datos(anio, mes)
        if origen is None:
            return ResultadoCopia(periodo_origen=None)
        origen_id, periodo_origen = origen

        lineas_origen = uow.asignaciones.lineas_del_periodo(origen_id)
        filas_destino = _filas_de_empresa(uow, periodo_id, filtro)
        lineas_destino = {f.trabajador.ide: f.lineas for f in filas_destino}
        activos = {f.trabajador.ide for f in filas_destino if f.trabajador.activo}

        copiados = con_carga = sin_datos = omitidas = 0
        for trabajador_ide in sorted(activos):
            if lineas_destino.get(trabajador_ide):
                con_carga += 1
                continue
            previas = lineas_origen.get(trabajador_ide, [])
            if not previas:
                sin_datos += 1
                continue
            utilizables = _sin_propuesta(
                [ln for ln in previas if ln.ofrecible])
            omitidas += len(previas) - len(utilizables)
            if not utilizables:
                sin_datos += 1
                continue
            uow.asignaciones.reemplazar(
                periodo_id, trabajador_ide, utilizables, usuario
            )
            uow.eventos.registrar(
                periodo_id,
                trabajador_ide,
                TipoEvento.COPIA,
                usuario,
                [],
                _snapshot(utilizables),
            )
            copiados += 1
        uow.commit()
        return ResultadoCopia(
            periodo_origen=periodo_origen,
            trabajadores_copiados=copiados,
            con_carga_previa=con_carga,
            sin_datos_origen=sin_datos,
            lineas_omitidas_obra_inactiva=omitidas,
        )


class CopiarTrabajadorAnterior:
    """Copia (sustituyendo) las líneas del periodo anterior de UN trabajador."""

    def ejecutar(
        self,
        uow: UnitOfWork,
        anio: int,
        mes: int,
        trabajador_ide: int,
        usuario: str,
        *,
        filtro: FiltroEmpresa,
    ) -> tuple[CuadranteTrabajador, ResumenPeriodo, Periodo | None, int]:
        periodo_id, _ = _periodo_abierto_o_error(uow, anio, mes)
        _trabajador_o_error(uow, trabajador_ide)
        origen = uow.periodos.anterior_con_datos(anio, mes)
        if origen is None:
            fila, resumen = ObtenerFilaTrabajador().ejecutar(
                uow, anio, mes, trabajador_ide, filtro=filtro, usuario=usuario
            )
            return fila, resumen, None, 0
        origen_id, periodo_origen = origen
        previas = uow.asignaciones.lineas_de_trabajador(origen_id, trabajador_ide)
        utilizables = _sin_propuesta([ln for ln in previas if ln.ofrecible])
        omitidas = len(previas) - len(utilizables)
        antes = uow.asignaciones.lineas_de_trabajador(periodo_id, trabajador_ide)
        if _snapshot(antes) != _snapshot(utilizables):
            uow.asignaciones.reemplazar(
                periodo_id, trabajador_ide, utilizables, usuario
            )
            uow.eventos.registrar(
                periodo_id,
                trabajador_ide,
                TipoEvento.COPIA,
                usuario,
                _snapshot(antes),
                _snapshot(utilizables),
            )
        uow.commit()
        fila, resumen = ObtenerFilaTrabajador().ejecutar(
            uow, anio, mes, trabajador_ide, filtro=filtro, usuario=usuario
        )
        return fila, resumen, periodo_origen, omitidas


# ----------------------------------------------------------------------
# Completar hasta el 100 % por lote (F-029)
# ----------------------------------------------------------------------
class CompletarHasta100:
    """Pone a cada trabajador del lote lo que le falta hasta el 100 % en la
    obra destino (obra + modo), en UNA transacción
    (docs/ARCHITECTURE.md#regla-completar).

    Todo o nada ante un error global (periodo inexistente o cerrado, obra
    que no existe, no es de la empresa de las obras o no se ofrece en ese
    modo): se valida antes de tocar a nadie. Por trabajador, en el orden de
    llegada y una vez cada `ide`: no visible en la empresa del filtro →
    `NO_VISIBLE`; no vigente en el mes → `NO_VIGENTE`; en OK o EXCESO →
    `YA_AL_100` / `EXCESO` sin tocarlo; si no, se completa y deja un evento
    `COMPLETAR`, deshacible como cualquier otro (`#regla-deshacer`). No
    llama ni al transfer ni a Sigrid.
    """

    def ejecutar(
        self,
        uow: UnitOfWork,
        anio: int,
        mes: int,
        trabajadores: list[int],
        obra_ide: int,
        es_postventa: bool,
        usuario: str,
        *,
        filtro: FiltroEmpresa,
    ) -> tuple[list[ResultadoCompletarTrabajador], ResumenPeriodo]:
        periodo_id, _ = _periodo_abierto_o_error(uow, anio, mes)
        _obra_destino_o_error(uow, periodo_id, obra_ide, es_postventa, filtro)
        filas = {
            f.trabajador.ide: f
            for f in _filas_de_empresa(uow, periodo_id, filtro)
        }
        resultados = [
            _completar_uno(uow, periodo_id, ide, filas.get(ide), obra_ide,
                           es_postventa, usuario)
            for ide in dict.fromkeys(trabajadores)
        ]
        uow.commit()
        return resultados, _resumen_periodo(uow, periodo_id, filtro)


def _completar_uno(
    uow: UnitOfWork,
    periodo_id: int,
    ide: int,
    fila: CuadranteTrabajador | None,
    obra_ide: int,
    es_postventa: bool,
    usuario: str,
) -> ResultadoCompletarTrabajador:
    """Un trabajador del lote: qué le pasa y, si se completa, su escritura y
    su evento `COMPLETAR` (R15-R19, R23, R24)."""
    if fila is None:
        return ResultadoCompletarTrabajador(ide, ResultadoCompletado.NO_VISIBLE)
    if not fila.trabajador.activo:
        return ResultadoCompletarTrabajador(ide, ResultadoCompletado.NO_VIGENTE)
    completado = completar_hasta_100(fila.lineas, obra_ide, es_postventa)
    if completado is None:
        # Mismo `calcular_estado` que decidió no tocarlo: no hay un segundo
        # criterio de «al 100 %» (D5).
        estado = calcular_estado(fila.total, len(fila.lineas))
        return ResultadoCompletarTrabajador(
            ide,
            ResultadoCompletado.EXCESO
            if estado is EstadoTrabajador.EXCESO
            else ResultadoCompletado.YA_AL_100,
        )
    uow.asignaciones.reemplazar(periodo_id, ide, completado.lineas, usuario)
    uow.eventos.registrar(
        periodo_id,
        ide,
        TipoEvento.COMPLETAR,
        usuario,
        _snapshot(fila.lineas),
        _snapshot(completado.lineas),
    )
    return ResultadoCompletarTrabajador(
        ide, ResultadoCompletado.COMPLETADO, completado.anadido
    )


def _obra_destino_o_error(
    uow: UnitOfWork,
    periodo_id: int,
    obra_ide: int,
    es_postventa: bool,
    filtro: FiltroEmpresa,
) -> Obra:
    """Obra destino del lote (F-029, R22): la de la lista que ofrece el
    cuadrante (empresa de las obras) y ofrecible en ese modo según la ÚNICA
    definición, `Linea.ofrecible`. Si no, `ObraNoValida` con el motivo."""
    obra = next(
        (
            o
            for o in uow.obras.listar_para_periodo(periodo_id)
            if o.ide == obra_ide and o.empresa == filtro.empresa_obras
        ),
        None,
    )
    if obra is None:
        raise ObraNoValida(
            f"La obra {obra_ide} no existe o no es de la empresa de las obras"
        )
    linea = Linea(
        obra_ide=obra_ide,
        es_postventa=es_postventa,
        porcentaje=Decimal("0"),
        obra_activa=obra.activa,
        obra_admite_postventa=obra.admite_postventa,
    )
    if not linea.ofrecible:
        modo = "como Postv-" if es_postventa else "como normal"
        raise ObraNoValida(f"La obra {obra.cod} no se ofrece {modo}")
    return obra


# ----------------------------------------------------------------------
# Gestión de periodos
# ----------------------------------------------------------------------
class ListarPeriodos:
    def ejecutar(self, uow: UnitOfWork) -> list[Periodo]:
        return uow.periodos.listar()


class ListarTiposIncidencia:
    """Catálogo del desplegable de incidencias (F-030, R6): los activos, por
    orden de letra. Sale del sync de `auxhor`; nada viene de `partes`."""

    def ejecutar(self, uow: UnitOfWork) -> list[TipoIncidencia]:
        return uow.tipos_incidencia.activos()


class ListarEmpresas:
    """Empresas del selector (F-024 R1, F-032): las que tienen algún
    trabajador activo más la por defecto, ordenadas.

    Nombre y baja salen del catálogo `auxemp` que trae el sync (tabla
    `empresa`); «Empresa N» solo si la empresa no está en la tabla o no tiene
    nombre. Una empresa de baja o desactivada se enseña marcada, nunca se
    oculta: ocultarla escondería carga (decisión del humano, 2026-10-01).
    """

    def __init__(self, por_defecto: int) -> None:
        self._por_defecto = por_defecto

    def ejecutar(self, uow: UnitOfWork) -> tuple[int, list[Empresa]]:
        numeros = uow.trabajadores.empresas_activas() | {self._por_defecto}
        fichas = {e.numero: e for e in uow.empresas.listar()}
        empresas = []
        for numero in sorted(numeros):
            ficha = fichas.get(numero)
            empresas.append(Empresa(
                numero=numero,
                nombre=(ficha.nombre if ficha else None) or f"Empresa {numero}",
                de_baja=ficha.de_baja if ficha else False,
            ))
        return self._por_defecto, empresas


class CrearObtenerPeriodo:
    def ejecutar(self, uow: UnitOfWork, anio: int, mes: int) -> tuple[Periodo, bool]:
        existente = uow.periodos.obtener(anio, mes)
        if existente:
            return existente[1], False
        _, periodo = uow.periodos.crear(anio, mes)
        uow.commit()
        return periodo, True


class CambiarEstadoPeriodo:
    def ejecutar(
        self, uow: UnitOfWork, anio: int, mes: int, estado: EstadoPeriodo
    ) -> Periodo:
        _periodo_o_error(uow, anio, mes)
        periodo = uow.periodos.cambiar_estado(anio, mes, estado.value)
        uow.commit()
        return periodo


# ----------------------------------------------------------------------
# Export y preview de sincronización
# ----------------------------------------------------------------------
class PreviewSync:
    """Muestra qué sincronizaría el sync SIN persistir nada.

    Aplica la misma depuración que el pipeline (dedupe de recursos,
    filtro de categorías y de estados de obra, empresa y estado del
    recurso) con la misma validación de columnas, y desglosa lo incluido
    y lo excluido para poder ajustar config.yaml con datos reales. Desde
    F-032 informa también del catálogo de empresas leído.

    Ventana de bajas (F-026 R12, R17): con `uow_factory`, abre una UoW SOLO
    para leer los periodos `ABIERTO` (sin `commit`); sin ella, la ventana es
    el mes anterior a `hoy`. Se publica en `empleados.ventana_baja`.

    Universo de postventa (F-025, R16): lo pide igual que el sync
    (`sync_pipeline.pedir_universo`) y publica en `obras`
    `admiten_postventa`, `solo_postventa` y `motivo_postventa`.

    Código de obra y VAR (F-039, R17): prepara las obras con la MISMA
    `sync_pipeline.preparar_obras` y publica `excluidas_por_codigo`,
    `muestra_excluidas_por_codigo` (hasta 10), `entradas_var`, `obra_var`
    y `motivo_var`.
    """

    def __init__(
        self,
        sigrid: SigridGateway,
        sql_empleados: str,
        sql_obras: str,
        categorias_incluidas: list[str] | None = None,
        filtro_categorias: bool = True,
        estados_excluidos: list[str] | None = None,
        filtro_estados: bool = True,
        exigir_codigo_mes: bool = True,
        criterio: CriterioActivoRecurso = CRITERIO_VACIO,
        sql_empresas: str | None = None,
        uow_factory: Callable[[], UnitOfWork] | None = None,
        hoy: Callable[[], date] = date.today,
        *,
        universo: UniversosGateway,
        empresa_obras: int,
        digitos_excluidos: int = 0,
        sql_incidencias: str | None = None,
    ) -> None:
        self._sigrid = sigrid
        self._sql_empleados = sql_empleados
        self._sql_obras = sql_obras
        # Catálogo `auxemp` (F-032). Sin consulta, el preview no lo lee ni
        # publica la sección; el contenedor la pasa siempre.
        self._sql_empresas = sql_empresas
        # Catálogo de incidencias de `auxhor` (F-030, R3), con el mismo
        # criterio: sin consulta no se lee ni se publica la sección.
        self._sql_incidencias = sql_incidencias
        self._categorias = categorias_incluidas or []
        self._filtro_categorias = filtro_categorias and bool(self._categorias)
        self._estados = estados_excluidos or []
        self._filtro_estados = filtro_estados and bool(self._estados)
        self._exigir_mes = bool(exigir_codigo_mes)
        self._criterio = criterio
        self._uow_factory = uow_factory
        self._hoy = hoy
        self._universo = universo
        self._empresa_obras = empresa_obras
        self._digitos = digitos_excluidos

    def _ventana_baja(self) -> int:
        from application.sync_pipeline import ventana_de_bajas

        if self._uow_factory is None:
            return ventana_de_bajas([], self._hoy())
        with self._uow_factory() as uow:
            return ventana_de_bajas(uow.periodos.listar(), self._hoy())

    def ejecutar(self) -> dict[str, Any]:
        from application.filtros_maestros import (
            depurar_empleados,
            resumir_empresas,
            resumir_tipos_incidencia,
        )
        from application.sync_pipeline import (
            COLUMNAS_EMPLEADOS,
            COLUMNAS_EMPRESAS,
            COLUMNAS_INCIDENCIAS,
            COLUMNAS_OBRAS,
            _validar_columnas,
            preparar_obras,
        )

        brutas_emp = self._sigrid.leer(self._sql_empleados)
        _validar_columnas(brutas_emp, COLUMNAS_EMPLEADOS, "sync.empleados.sql")
        ventana_baja = self._ventana_baja()
        emp = depurar_empleados(
            brutas_emp,
            self._categorias,
            self._filtro_categorias,
            exigir_codigo_mes=self._exigir_mes,
            criterio=self._criterio,
            baja_desde=ventana_baja,
        )
        brutas_obr = self._sigrid.leer(self._sql_obras)
        _validar_columnas(brutas_obr, COLUMNAS_OBRAS, "sync.obras.sql")
        prep = preparar_obras(brutas_obr, self._universo,
                              self._empresa_obras, self._estados,
                              self._filtro_estados, self._digitos)
        obr, universo, uvar = prep.depurado, prep.universo_pv, prep.universo_var
        por_categoria = Counter(
            str(f.get("categoria") or "(sin categoría)") for f in emp.filas
        )
        por_codigo_mes = Counter(
            str(f.get("cod_hora_mes") or "(sin código)") for f in emp.filas
        )
        por_estado = Counter(
            str(f.get("estado_sigrid") or "(sin estado)") for f in obr.filas
        )
        salida: dict[str, Any] = {
            "empleados": {
                "brutos": emp.brutos,
                "excluidos_sin_codigo_mes": emp.excluidos_sin_codigo_mes,
                "por_codigo_mes": dict(por_codigo_mes.most_common()),
                "excluidos_por_categoria": dict(
                    emp.excluidos_detalle.most_common()
                ),
                "excluidos_por_estado_recurso": dict(
                    emp.excluidos_estado_recurso.most_common()
                ),
                "ventana_baja": ventana_baja,
                "incluidos_con_baja": emp.incluidos_con_baja,
                "posible_misma_persona": emp.posible_misma_persona,
                "con_baja_laboral": emp.con_baja_laboral,
                "total": len(emp.filas),
                "por_categoria": dict(por_categoria.most_common()),
                "por_empresa": _por_empresa(emp.filas),
                "muestra": emp.filas[:5],
            },
            "obras": {
                "brutas": obr.brutos,
                "excluidas_por_estado": dict(
                    obr.excluidos_detalle.most_common()
                ),
                "total": len(obr.filas),
                "por_estado": dict(por_estado.most_common()),
                "por_empresa": _por_empresa(obr.filas),
                "muestra": obr.filas[:5],
                "admiten_postventa": obr.admiten_postventa,
                "solo_postventa": obr.solo_postventa,
                "motivo_postventa": universo.motivo,
                "excluidas_por_codigo": len(prep.descartadas),
                "muestra_excluidas_por_codigo": [
                    f.get("cod") for f in prep.descartadas[:10]],
                "entradas_var": len(prep.entradas),
                "obra_var": uvar.obra_cod,
                "motivo_var": uvar.motivo,
            },
        }
        if self._sql_incidencias is not None:
            # Antes que las empresas, en el mismo orden que el sync.
            brutas_inc = self._sigrid.leer(self._sql_incidencias)
            _validar_columnas(brutas_inc, COLUMNAS_INCIDENCIAS,
                              "sync.incidencias.sql")
            salida["incidencias"] = resumir_tipos_incidencia(brutas_inc)
        if self._sql_empresas is not None:
            brutas_empresas = self._sigrid.leer(self._sql_empresas)
            _validar_columnas(brutas_empresas, COLUMNAS_EMPRESAS,
                              "sync.empresas.sql")
            salida["empresas"] = resumir_empresas(brutas_empresas)
        return salida


def _por_empresa(filas: list[dict[str, Any]]) -> dict[str, int]:
    """Incluidos por empresa (`con.emp`), con la clave en texto como el
    resto de desgloses del preview."""
    return dict(Counter(
        "(sin empresa)" if f.get("empresa") is None else str(f["empresa"])
        for f in filas
    ).most_common())


# ----------------------------------------------------------------------
# Helpers internos
# ----------------------------------------------------------------------
def _periodo_o_error(uow: UnitOfWork, anio: int, mes: int) -> tuple[int, Periodo]:
    resultado = uow.periodos.obtener(anio, mes)
    if resultado is None:
        raise PeriodoNoEncontrado(f"Periodo {mes:02d}/{anio} no existe")
    return resultado


def _periodo_abierto_o_error(
    uow: UnitOfWork, anio: int, mes: int
) -> tuple[int, Periodo]:
    periodo_id, periodo = _periodo_o_error(uow, anio, mes)
    if periodo.estado is not EstadoPeriodo.ABIERTO:
        raise PeriodoCerrado(f"El periodo {mes:02d}/{anio} está cerrado")
    return periodo_id, periodo


def _trabajador_o_error(uow: UnitOfWork, ide: int) -> Trabajador:
    trabajador = uow.trabajadores.obtener(ide)
    if trabajador is None:
        raise TrabajadorNoEncontrado(f"Trabajador {ide} no existe")
    return trabajador


def _validar_lineas(
    uow: UnitOfWork,
    lineas_entrada: list[dict[str, Any]],
    permitir_inactivas: bool = False,
) -> list[Linea]:
    lineas: list[Linea] = []
    claves: set[tuple[int, bool]] = set()
    for bruto in lineas_entrada:
        try:
            obra_ide = int(bruto["obra_ide"])
            es_postventa = bool(bruto.get("es_postventa", False))
            porcentaje = Decimal(str(bruto["porcentaje"])).quantize(Decimal("0.01"))
        except (KeyError, ValueError, ArithmeticError) as exc:
            raise LineasInvalidas(f"Línea inválida: {bruto}") from exc
        if not Decimal("0") < porcentaje <= Decimal("100"):
            raise LineasInvalidas(
                f"Porcentaje fuera de rango (0, 100]: {porcentaje}"
            )
        clave = (obra_ide, es_postventa)
        if clave in claves:
            raise LineasInvalidas(
                f"Obra {obra_ide} duplicada (postventa={es_postventa})"
            )
        claves.add(clave)
        lineas.append(
            Linea(
                obra_ide=obra_ide,
                es_postventa=es_postventa,
                porcentaje=porcentaje,
                # F-050 (R15): un snapshot con partida la devuelve al deshacer.
                partida_ide=bruto.get("partida_ide"),
                partida_cod=bruto.get("partida_cod"),
                partida_res=bruto.get("partida_res"),
            )
        )
    ides = {ln.obra_ide for ln in lineas}
    existentes = uow.obras.existen(ides)
    desconocidas = ides - existentes
    if desconocidas and not permitir_inactivas:
        raise ObraNoValida(f"Obras inexistentes: {sorted(desconocidas)}")
    if desconocidas:
        lineas = [ln for ln in lineas if ln.obra_ide in existentes]
    return lineas


def _rechazar_nuevas_no_ofrecibles(
    uow: UnitOfWork, lineas: list[Linea], antes: list[Linea]
) -> None:
    """Una línea que no estaba guardada (misma obra y modo) y no es ofrecible
    tumba el guardado entero (F-025, R20, D7): defensa ante un cliente que
    no sea el front. Lo ya guardado se puede volver a guardar (D5)."""
    previas = {ln.clave() for ln in antes}
    nuevas = [ln for ln in lineas if ln.clave() not in previas]
    modos = uow.obras.modos_ofrecibles({ln.obra_ide for ln in nuevas})
    rechazadas = [
        ln.clave() for ln in nuevas
        if not dataclasses.replace(
            ln,
            obra_activa=modos[ln.obra_ide][0],
            obra_admite_postventa=modos[ln.obra_ide][1],
        ).ofrecible
    ]
    if rechazadas:
        raise ObraNoValida(
            "Obras que no se ofrecen en ese modo (obra, postventa): "
            f"{rechazadas}"
        )


def _filas_de_empresa(
    uow: UnitOfWork, periodo_id: int, filtro: FiltroEmpresa
) -> list[CuadranteTrabajador]:
    """Filas del periodo visibles en la empresa del filtro, cada una con
    TODAS sus líneas (F-024 R10; visibilidad de F-034 R2-R3). Único punto del
    filtro de trabajadores: lo usan el cuadrante, el resumen, la copia del
    mes y el lote de completar al 100 % (F-029)."""
    trabajadores = uow.trabajadores.listar_para_periodo(periodo_id)
    lineas = uow.asignaciones.lineas_del_periodo(periodo_id)
    filas = []
    for t in trabajadores:
        propias = lineas.get(t.ide, [])
        if visible_en_empresa(t.empresa, filtro):
            filas.append(CuadranteTrabajador(trabajador=t, lineas=propias))
    return filas


def _resumen_periodo(
    uow: UnitOfWork, periodo_id: int, filtro: FiltroEmpresa
) -> ResumenPeriodo:
    """Resumen de los trabajadores visibles en la empresa del filtro (R13)."""
    return resumir(_filas_de_empresa(uow, periodo_id, filtro))


#: Campos de la propuesta guardada de una línea (F-055, R13).
_CAMPOS_PROPUESTA = ("propuesta_ide", "propuesta_cod", "propuesta_res",
                     "propuesta_metodo", "propuesta_origen")


def _conservar_partidas(lineas: list[Linea], antes: list[Linea]) -> list[Linea]:
    """Cada línea cuya clave (obra, postventa) estaba en `antes` recibe la
    partida que tenía (F-050, R14) y su propuesta guardada (F-055, R17); las
    demás quedan como vienen."""
    previas = {ln.clave(): ln for ln in antes}
    return [
        dataclasses.replace(
            ln,
            partida_ide=previas[ln.clave()].partida_ide,
            partida_cod=previas[ln.clave()].partida_cod,
            partida_res=previas[ln.clave()].partida_res,
            **{c: getattr(previas[ln.clave()], c) for c in _CAMPOS_PROPUESTA},
        )
        if ln.clave() in previas else ln
        for ln in lineas
    ]


def _sin_propuesta(lineas: list[Linea]) -> list[Linea]:
    """Las líneas copiadas de otro periodo, sin su propuesta guardada
    (F-055, R17: copiar el mes y F8 no la copian; la partida elegida sí,
    F-050 R16)."""
    return [dataclasses.replace(ln, **dict.fromkeys(_CAMPOS_PROPUESTA))
            for ln in lineas]


def _snapshot(lineas: list[Linea]) -> list[dict[str, Any]]:
    """Lo que guarda un evento. La partida, solo si la línea la tiene: los
    eventos sin partida no cambian de forma (F-050, R15)."""
    return [
        {
            "obra_ide": ln.obra_ide,
            "es_postventa": ln.es_postventa,
            "porcentaje": str(ln.porcentaje),
            **(
                {
                    "partida_ide": ln.partida_ide,
                    "partida_cod": ln.partida_cod,
                    "partida_res": ln.partida_res,
                }
                if ln.partida_ide is not None
                else {}
            ),
        }
        for ln in sorted(lineas, key=lambda x: (x.obra_ide, x.es_postventa))
    ]
