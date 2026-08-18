# application/use_cases.py
"""Casos de uso del servicio de dedicación.

Cada caso de uso recibe una UnitOfWork ya abierta, aplica las reglas de
negocio y deja al llamante (capa API) la gestión del ciclo de vida.
"""
from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from domain.errors import (
    LineasInvalidas,
    NadaQueDeshacer,
    ObraNoValida,
    PeriodoCerrado,
    PeriodoNoEncontrado,
    TrabajadorNoEncontrado,
)
from domain.estados import resumir
from domain.models import (
    CuadranteTrabajador,
    EstadoPeriodo,
    Linea,
    Obra,
    Periodo,
    ResultadoCopia,
    ResumenPeriodo,
    TipoEvento,
    Trabajador,
)
from domain.ports import SigridGateway, UnitOfWork

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


class ObtenerCuadrante:
    def ejecutar(self, uow: UnitOfWork, anio: int, mes: int) -> Cuadrante:
        periodo_id, periodo = _periodo_o_error(uow, anio, mes)
        trabajadores = uow.trabajadores.listar_para_periodo(periodo_id)
        obras = uow.obras.listar_para_periodo(periodo_id)
        lineas_por_trabajador = uow.asignaciones.lineas_del_periodo(periodo_id)
        con_deshacer = uow.eventos.trabajadores_con_pendientes(periodo_id)
        filas = [
            CuadranteTrabajador(
                trabajador=t,
                lineas=lineas_por_trabajador.get(t.ide, []),
                puede_deshacer=t.ide in con_deshacer,
            )
            for t in trabajadores
        ]
        return Cuadrante(
            periodo=periodo, obras=obras, filas=filas, resumen=resumir(filas)
        )


class ObtenerFilaTrabajador:
    def ejecutar(
        self, uow: UnitOfWork, anio: int, mes: int, trabajador_ide: int
    ) -> tuple[CuadranteTrabajador, ResumenPeriodo]:
        periodo_id, _ = _periodo_o_error(uow, anio, mes)
        trabajador = _trabajador_o_error(uow, trabajador_ide)
        fila = CuadranteTrabajador(
            trabajador=trabajador,
            lineas=uow.asignaciones.lineas_de_trabajador(periodo_id, trabajador_ide),
            puede_deshacer=uow.eventos.ultimo_pendiente(periodo_id, trabajador_ide)
            is not None,
        )
        resumen = _resumen_periodo(uow, periodo_id)
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
    ) -> tuple[CuadranteTrabajador, ResumenPeriodo]:
        periodo_id, periodo = _periodo_abierto_o_error(uow, anio, mes)
        trabajador = _trabajador_o_error(uow, trabajador_ide)
        lineas = _validar_lineas(uow, lineas_entrada)

        antes = uow.asignaciones.lineas_de_trabajador(periodo_id, trabajador_ide)
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
        return ObtenerFilaTrabajador().ejecutar(uow, anio, mes, trabajador_ide)


class DeshacerUltimaModificacion:
    def ejecutar(
        self,
        uow: UnitOfWork,
        anio: int,
        mes: int,
        trabajador_ide: int,
        usuario: str,
    ) -> tuple[CuadranteTrabajador, ResumenPeriodo]:
        periodo_id, _ = _periodo_abierto_o_error(uow, anio, mes)
        _trabajador_o_error(uow, trabajador_ide)
        pendiente = uow.eventos.ultimo_pendiente(periodo_id, trabajador_ide)
        if pendiente is None:
            raise NadaQueDeshacer("No hay modificaciones que deshacer")
        evento_id, snapshot_antes = pendiente
        lineas = _validar_lineas(uow, snapshot_antes, permitir_inactivas=True)
        uow.asignaciones.reemplazar(periodo_id, trabajador_ide, lineas, usuario)
        uow.eventos.marcar_deshecho(evento_id)
        uow.commit()
        return ObtenerFilaTrabajador().ejecutar(uow, anio, mes, trabajador_ide)


# ----------------------------------------------------------------------
# Copia desde el periodo anterior
# ----------------------------------------------------------------------
class CopiarPeriodoAnterior:
    """Rellena el periodo con las asignaciones del último periodo con datos.

    Solo actúa sobre trabajadores activos SIN carga en el periodo destino:
    nunca pisa trabajo ya hecho. Las líneas de obras desactivadas se omiten
    y se contabilizan.
    """

    def ejecutar(
        self, uow: UnitOfWork, anio: int, mes: int, usuario: str
    ) -> ResultadoCopia:
        periodo_id, _ = _periodo_abierto_o_error(uow, anio, mes)
        origen = uow.periodos.anterior_con_datos(anio, mes)
        if origen is None:
            return ResultadoCopia(periodo_origen=None)
        origen_id, periodo_origen = origen

        lineas_origen = uow.asignaciones.lineas_del_periodo(origen_id)
        lineas_destino = uow.asignaciones.lineas_del_periodo(periodo_id)
        activos = {
            t.ide for t in uow.trabajadores.listar_para_periodo(periodo_id) if t.activo
        }

        copiados = con_carga = sin_datos = omitidas = 0
        for trabajador_ide in sorted(activos):
            if lineas_destino.get(trabajador_ide):
                con_carga += 1
                continue
            previas = lineas_origen.get(trabajador_ide, [])
            if not previas:
                sin_datos += 1
                continue
            utilizables = [ln for ln in previas if ln.obra_activa]
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
    ) -> tuple[CuadranteTrabajador, ResumenPeriodo, Periodo | None, int]:
        periodo_id, _ = _periodo_abierto_o_error(uow, anio, mes)
        _trabajador_o_error(uow, trabajador_ide)
        origen = uow.periodos.anterior_con_datos(anio, mes)
        if origen is None:
            fila, resumen = ObtenerFilaTrabajador().ejecutar(
                uow, anio, mes, trabajador_ide
            )
            return fila, resumen, None, 0
        origen_id, periodo_origen = origen
        previas = uow.asignaciones.lineas_de_trabajador(origen_id, trabajador_ide)
        utilizables = [ln for ln in previas if ln.obra_activa]
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
            uow, anio, mes, trabajador_ide
        )
        return fila, resumen, periodo_origen, omitidas


# ----------------------------------------------------------------------
# Gestión de periodos
# ----------------------------------------------------------------------
class ListarPeriodos:
    def ejecutar(self, uow: UnitOfWork) -> list[Periodo]:
        return uow.periodos.listar()


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
    filtro de categorías y de estados de obra) y desglosa lo incluido y
    lo excluido para poder ajustar config.yaml con datos reales.
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
    ) -> None:
        self._sigrid = sigrid
        self._sql_empleados = sql_empleados
        self._sql_obras = sql_obras
        self._categorias = categorias_incluidas or []
        self._filtro_categorias = filtro_categorias and bool(self._categorias)
        self._estados = estados_excluidos or []
        self._filtro_estados = filtro_estados and bool(self._estados)
        self._exigir_mes = bool(exigir_codigo_mes)

    def ejecutar(self) -> dict[str, Any]:
        from application.filtros_maestros import (
            depurar_empleados,
            depurar_obras,
        )

        emp = depurar_empleados(
            self._sigrid.leer(self._sql_empleados),
            self._categorias,
            self._filtro_categorias,
            exigir_codigo_mes=self._exigir_mes,
        )
        obr = depurar_obras(
            self._sigrid.leer(self._sql_obras),
            self._estados,
            self._filtro_estados,
        )
        por_categoria = Counter(
            str(f.get("categoria") or "(sin categoría)") for f in emp.filas
        )
        por_codigo_mes = Counter(
            str(f.get("cod_hora_mes") or "(sin código)") for f in emp.filas
        )
        por_estado = Counter(
            str(f.get("estado_sigrid") or "(sin estado)") for f in obr.filas
        )
        return {
            "empleados": {
                "brutos": emp.brutos,
                "duplicados_recurso": emp.duplicados_recurso,
                "duplicados_persona": emp.duplicados_persona,
                "excluidos_sin_codigo_mes": emp.excluidos_sin_codigo_mes,
                "por_codigo_mes": dict(por_codigo_mes.most_common()),
                "excluidos_por_categoria": dict(
                    emp.excluidos_detalle.most_common()
                ),
                "total": len(emp.filas),
                "por_categoria": dict(por_categoria.most_common()),
                "muestra": emp.filas[:5],
            },
            "obras": {
                "brutas": obr.brutos,
                "excluidas_por_estado": dict(
                    obr.excluidos_detalle.most_common()
                ),
                "total": len(obr.filas),
                "por_estado": dict(por_estado.most_common()),
                "muestra": obr.filas[:5],
            },
        }


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


def _resumen_periodo(uow: UnitOfWork, periodo_id: int) -> ResumenPeriodo:
    trabajadores = uow.trabajadores.listar_para_periodo(periodo_id)
    lineas = uow.asignaciones.lineas_del_periodo(periodo_id)
    filas = [
        CuadranteTrabajador(trabajador=t, lineas=lineas.get(t.ide, []))
        for t in trabajadores
    ]
    return resumir(filas)


def _snapshot(lineas: list[Linea]) -> list[dict[str, Any]]:
    return [
        {
            "obra_ide": ln.obra_ide,
            "es_postventa": ln.es_postventa,
            "porcentaje": str(ln.porcentaje),
        }
        for ln in sorted(lineas, key=lambda x: (x.obra_ide, x.es_postventa))
    ]
