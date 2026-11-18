# application/traer_sigrid.py
"""F-054, parte A: traer al cuadrante lo que ya hay en los partes de Sigrid
(R2-R3, R13-R27; design §5.2).

`TraerDeSigrid` compara siempre y escribe solo lo que el usuario acepta:
cada aceptada `distinta` o `solo_sigrid` pisa **solo esa** línea
(`aceptar_entrada`, en su sitio); las demás vuelven con su motivo. Un evento
`SIGRID` por trabajador tocado, con el snapshot de toda su fila (subfilas
incluidas) antes y después: deshacerlo devuelve solo lo aceptado. Todo en
una transacción (R22): el periodo se comprueba antes de llamar al transfer
(R2) y se relee antes del único `commit`.
"""
from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from domain.importes import (
    MARCA_PRUEBAS,
    REPARTO_PCT,
    TipoCantidad,
    comentario_de_sigrid,
    tipo_de,
)

from domain.models import (
    FiltroEmpresa,
    ImporteMes,
    Linea,
    Obra,
    TipoEvento,
    Trabajador,
)
from domain.obras import ide_entrada
from domain.ports import PorcentajesSigridGateway, UnitOfWork
from domain.traer_sigrid import (
    Comparada,
    Contadores,
    EstadoEntrada,
    NoTraida,
    a_linea,
    comparar,
    entradas_por_trabajador,
)

from application.use_cases import (
    _foto_importes,
    _periodo_abierto_o_error,
    _snapshot,
    _snapshot_importes,
)

#: R20: por qué una aceptada no se escribe.
MOTIVO_SOLO_CUADRANTE = "solo está en el cuadrante: la escribe el registro"
MOTIVO_SIN_ENTRADA = "no es una entrada de Sigrid de este trabajador"
MOTIVO_NO_ACEPTABLE = "su estado es {estado}: solo se acepta distinta o solo_sigrid"

_ACEPTABLES = (EstadoEntrada.DISTINTA, EstadoEntrada.SOLO_SIGRID)

Clave = tuple[int, int, bool]  # (trabajador_ide, obra_ide, es_postventa)


@dataclass(frozen=True)
class TrabajadorTraido:
    """R27: un trabajador con alguna entrada de Sigrid, sus entradas
    comparadas y lo que se le aceptó."""

    trabajador: Trabajador
    comparadas: list[Comparada]
    aceptadas: list[tuple[int, bool]] = field(default_factory=list)
    rechazadas: list[tuple[tuple[int, bool], str]] = field(
        default_factory=list)


@dataclass(frozen=True)
class ResultadoTraer:
    """R27: la comparación entera, lo aceptado y lo rechazado (con motivo),
    y los trabajadores escritos (`tocados`, para las propuestas: R26)."""

    trabajadores: list[TrabajadorTraido]
    no_traidas: list[NoTraida]
    contadores: Contadores
    lineas_leidas: int
    excluidas_pruebas: int
    motivo_postventa: str | None
    motivo_var: str | None
    rechazadas: list[tuple[Clave, str]]
    tocados: list[int]
    #: Las obras de las entradas comparadas (código y nombre en la salida).
    obras: dict[int, Obra] = field(default_factory=dict)


def _obras(uow: UnitOfWork, periodo_id: int, ides: set[int]
           ) -> dict[int, Obra]:
    """Las del periodo (activas, de postventa y usadas) más las de `ides`
    que están en la base sin ofrecerse: inactivas y sin postventa (si no,
    saldrían en el listado), para que su motivo sea «no se ofrece», con su
    `cod` (T25, R46: el código, no el `ide`)."""
    obras = {o.ide: o for o in uow.obras.listar_para_periodo(periodo_id)}
    codigos = uow.obras.codigos(ides - set(obras))
    for ide in sorted(codigos):
        obras[ide] = Obra(ide=ide, cod=codigos[ide], descripcion="",
                          estado_sigrid=None, activa=False, empresa=None,
                          admite_postventa=False)
    return obras


def _trabajadores(uow: UnitOfWork, periodo_id: int, recursos: set[int],
                  vinculados: set[int]) -> dict[int, Trabajador]:
    """Los del periodo y los del maestro que no salen en él (no vigentes y
    sin líneas): así su motivo es «no vigente», no «fuera del maestro»."""
    trab = {t.ide: t for t in uow.trabajadores.listar_para_periodo(periodo_id)}
    for ide in sorted(recursos - set(trab) - vinculados):
        t = uow.trabajadores.obtener(ide)
        if t is not None:
            trab[ide] = t
    return trab


def _aceptadas(aceptar: list[dict[str, Any]]) -> list[Clave]:
    """Las claves pedidas, sin repetir y en el orden en que llegan."""
    claves: list[Clave] = []
    for item in aceptar:
        clave = (int(item["trabajador_ide"]), int(item["obra_ide"]),
                 bool(item.get("es_postventa", False)))
        if clave not in claves:
            claves.append(clave)
    return claves


def _despues(antes: list[Linea], nuevas: list[Linea]) -> list[Linea]:
    """La fila tras aceptar: cada nueva en el sitio de la de su clave, con
    las subfilas de esa (`aceptar_entrada` no las toca), o añadida."""
    por_clave = {ln.clave(): ln for ln in nuevas}
    fila = [dataclasses.replace(por_clave.pop(ln.clave()),
                                vinculados=ln.vinculados)
            if ln.clave() in por_clave else ln for ln in antes]
    return fila + list(por_clave.values())


#: F-069 (R32): el `registro_id` de nuestras `synckey`.
_SYNCKEY_TITULAR = "porcentajes:{}"
_SYNCKEY_VINCULADO = "porcentajes:vin:{}:{}"


def _tex_por(lineas: Any) -> tuple[dict[int, str | None], dict[str, str | None]]:
    """El `tex` de cada línea por `hmores_ide` y, por `synckey`, el de la
    de menor `hmores_ide` (R32)."""
    por_ide: dict[int, str | None] = {}
    por_clave: dict[str, tuple[int, str | None]] = {}
    for x in lineas:
        por_ide[int(x.hmores_ide)] = x.tex
        if x.synckey and (x.synckey not in por_clave
                          or x.hmores_ide < por_clave[x.synckey][0]):
            por_clave[x.synckey] = (int(x.hmores_ide), x.tex)
    return por_ide, {k: v for k, (_, v) in por_clave.items()}


class TraerDeSigrid:
    """R2-R3, R13-R27: comparar con Sigrid y escribir lo aceptado.

    F-069 (R32, D15): y poner como comentario de cada línea NUESTRA ya
    registrada (titular por `sigrid_hmores_ide` o su `synckey`; vinculado
    por la suya) el `tex` de Sigrid sin la marca de pruebas, si difiere. No
    toca % ni cantidades. Los de líneas, en el evento `SIGRID` del
    trabajador; los de las cantidades del mes (vinculados por %), en un
    evento `IMPORTES` propio (su snapshot no es de líneas)."""

    def __init__(self, gateway: PorcentajesSigridGateway,
                 importes: Mapping[str, TipoCantidad] | None = None,
                 marca: str | None = MARCA_PRUEBAS) -> None:
        self._gateway = gateway
        self._importes = dict(importes or {})
        self._marca = marca

    def ejecutar(self, uow: UnitOfWork, anio: int, mes: int, usuario: str, *,
                 filtro: FiltroEmpresa, aceptar: list[dict[str, Any]]
                 ) -> ResultadoTraer:
        periodo_id, _ = _periodo_abierto_o_error(uow, anio, mes)  # R2
        listadas = uow.obras.listar_para_periodo(periodo_id)
        pv = [{"ide": o.ide, "codigo": o.cod, "nombre": o.descripcion}
              for o in listadas
              if o.admite_postventa and o.empresa == filtro.empresa_obras]
        # R3: si falla, se propaga sin haber escrito nada.
        traido = self._gateway.porcentajes_existentes(
            filtro.empresa_obras, anio, mes, pv)

        vinculados = uow.vinculados.ides()
        recursos = {ln.recurso_ide for ln in traido.lineas}
        trabajadores = _trabajadores(uow, periodo_id, recursos, vinculados)
        obras = _obras(uow, periodo_id, {
            ide for ln in traido.lineas
            for ide in (ln.obra_ide, ln.obra_origen_ide,
                        None if ln.var_paride is None
                        else ide_entrada(int(ln.var_paride)))
            if ide is not None})
        entradas, no_traidas, contadores = entradas_por_trabajador(
            traido.lineas, obras, filtro=filtro, anio=anio, mes=mes,
            trabajadores=trabajadores, vinculados=vinculados)
        cuadrante = uow.asignaciones.lineas_del_periodo(periodo_id)
        comparadas = {t: comparar(cuadrante.get(t, []), es)
                      for t, es in entradas.items()}

        rechazadas: list[tuple[Clave, str]] = []
        nuevas: dict[int, list[Linea]] = {}
        por_aceptar: dict[int, list[Comparada]] = {}
        for clave in _aceptadas(aceptar):
            t, obra, es_pv = clave
            c = next((c for c in comparadas.get(t, [])
                      if (c.obra_ide, c.es_postventa) == (obra, es_pv)), None)
            if c is None:
                rechazadas.append((clave, MOTIVO_SIN_ENTRADA))
            elif c.estado is EstadoEntrada.SOLO_CUADRANTE:
                rechazadas.append((clave, MOTIVO_SOLO_CUADRANTE))
            elif c.estado not in _ACEPTABLES:
                rechazadas.append((clave, MOTIVO_NO_ACEPTABLE.format(
                    estado=c.estado.value)))
            else:
                assert c.entrada is not None
                nuevas.setdefault(t, []).append(
                    a_linea(c.entrada, obras[c.obra_ide]))
                por_aceptar.setdefault(t, []).append(c)

        # F-069 (R32): los comentarios traídos, por trabajador.
        comentarios = self._comentarios(
            uow, periodo_id, traido,
            {t: _despues(cuadrante.get(t, []), nuevas.get(t, []))
             for t in set(cuadrante) | set(nuevas)}, por_aceptar)
        tocados = sorted(set(nuevas) | set(comentarios))
        for t in tocados:
            antes = uow.asignaciones.lineas_de_trabajador(periodo_id, t)
            for ln, c in zip(nuevas.get(t, []), por_aceptar.get(t, [])):
                assert c.entrada is not None
                uow.asignaciones.aceptar_entrada(
                    periodo_id, t, ln, hmores_ide=c.entrada.hmores_ide,
                    parte_cod=c.entrada.parte_cod, usuario=usuario)
            despues = _despues(antes, nuevas.get(t, []))
            lineas_c, mes_c = comentarios.get(t, ({}, {}))
            despues = self._poner_comentarios(uow, periodo_id, t, despues,
                                              lineas_c)
            if _snapshot(antes) != _snapshot(despues):
                uow.eventos.registrar(
                    periodo_id, t, TipoEvento.SIGRID, usuario,
                    _snapshot(antes), _snapshot(despues))
            if mes_c:
                self._poner_comentarios_mes(uow, periodo_id, t, despues,
                                            mes_c, usuario)
        if tocados:
            _periodo_abierto_o_error(uow, anio, mes)  # cerrado entre medias
            uow.commit()

        return ResultadoTraer(
            trabajadores=[TrabajadorTraido(
                trabajador=trabajadores[t], comparadas=comparadas[t],
                aceptadas=[(c.obra_ide, c.es_postventa)
                           for c in por_aceptar.get(t, [])],
                rechazadas=[((o, pv), m) for (tt, o, pv), m in rechazadas
                            if tt == t])
                for t in sorted(comparadas)],
            no_traidas=no_traidas, contadores=contadores,
            lineas_leidas=traido.lineas_leidas,
            excluidas_pruebas=traido.excluidas_pruebas,
            motivo_postventa=traido.motivo_postventa,
            motivo_var=traido.motivo_var, rechazadas=rechazadas,
            tocados=sorted(nuevas),
            obras={c.obra_ide: obras[c.obra_ide]
                   for cs in comparadas.values() for c in cs
                   if c.obra_ide in obras})

    # ------------------------- F-069 · R32 -------------------------- #
    def _comentarios(self, uow: UnitOfWork, periodo_id: int, traido: Any,
                     cuadrante: dict[int, list[Linea]],  # con las aceptadas
                     por_aceptar: dict[int, list[Comparada]],
                     ) -> dict[int, tuple[dict, dict[int, str | None]]]:
        """Por trabajador: los comentarios que cambian en sus líneas
        (`{(clave, vinculado_ide | None): comentario}`) y en sus cantidades
        del mes (`{vinculado_ide: comentario}`). Solo las líneas nuestras
        registradas que están en Sigrid; una aceptada ahora trae el `tex` de
        su línea de menor `ide`."""
        tex_l, tex_lk = _tex_por(traido.lineas)
        tex_v, tex_vk = _tex_por(getattr(traido, "vinculados_registrados", ()))
        aceptadas = {(t, (c.obra_ide, c.es_postventa)): c.entrada.hmores_ide
                     for t, cs in por_aceptar.items() for c in cs if c.entrada}
        ids: dict[tuple[int, tuple[int, bool]], tuple[int, int | None]] = {
            (t, clave): (i, h)
            for t, clave, i, h in uow.asignaciones.registradas(periodo_id)}
        mes_actual = uow.importes.del_periodo(periodo_id) if any(
            tipo_de(v.tipo, self._importes) for ls in cuadrante.values()
            for ln in ls for v in ln.vinculados) else {}
        out: dict[int, tuple[dict, dict[int, str | None]]] = {}
        for t, lineas in cuadrante.items():
            de_lineas: dict = {}
            mes: dict[int, tuple[int, str | None]] = {}
            for ln in lineas:
                asig, hmores = ids.get((t, ln.clave()), (None, None))
                hmores = aceptadas.get((t, ln.clave()), hmores)
                tex = self._tex(tex_l, tex_lk, hmores,
                                None if asig is None
                                else _SYNCKEY_TITULAR.format(asig))
                if tex is not False and tex != ln.comentario:
                    de_lineas[(ln.clave(), None)] = tex
                for v in ln.vinculados:
                    tex = self._tex(tex_v, tex_vk, v.sigrid_hmores_ide,
                                    None if asig is None else
                                    _SYNCKEY_VINCULADO.format(
                                        asig, v.vinculado_ide))
                    if tex is False:
                        continue
                    tipo = tipo_de(v.tipo, self._importes)
                    if tipo is not None and tipo.reparto == REPARTO_PCT:
                        orden = v.sigrid_hmores_ide or 0
                        if (v.vinculado_ide not in mes
                                or orden < mes[v.vinculado_ide][0]):
                            mes[v.vinculado_ide] = (orden, tex)
                    elif tex != v.comentario:
                        de_lineas[(ln.clave(), v.vinculado_ide)] = tex
            suyas = mes_actual.get(t, {})
            de_mes = {vid: tex for vid, (_, tex) in mes.items()
                      if vid in suyas and suyas[vid].comentario != tex}
            if de_lineas or de_mes:
                out[t] = (de_lineas, de_mes)
        return out

    def _tex(self, por_ide: dict, por_clave: dict, hmores: int | None,
             synckey: str | None) -> str | None | bool:
        """El comentario de Sigrid de una línea nuestra (sin la marca), o
        `False` si no está en Sigrid."""
        if hmores and int(hmores) in por_ide:
            return comentario_de_sigrid(por_ide[int(hmores)], self._marca)
        if synckey and synckey in por_clave:
            return comentario_de_sigrid(por_clave[synckey], self._marca)
        return False

    @staticmethod
    def _poner_comentarios(uow: UnitOfWork, periodo_id: int, t: int,
                           lineas: list[Linea], cambios: dict) -> list[Linea]:
        """Escribe los comentarios de líneas y subfilas (sin tocar la línea
        ni su traza) y devuelve la fila como queda."""
        for (clave, vid), tex in sorted(cambios.items(),
                                        key=lambda kv: (kv[0][0],
                                                        kv[0][1] or 0)):
            if vid is None:
                uow.asignaciones.poner_comentario(periodo_id, t, clave, tex)
            else:
                uow.asignaciones.guardar_subfila_importe(
                    periodo_id, t, clave, vid, {"comentario": tex})
        return [dataclasses.replace(
            ln, comentario=cambios.get((ln.clave(), None), ln.comentario),
            vinculados=tuple(dataclasses.replace(
                v, comentario=cambios.get((ln.clave(), v.vinculado_ide),
                                          v.comentario))
                for v in ln.vinculados)) for ln in lineas]

    @staticmethod
    def _poner_comentarios_mes(uow: UnitOfWork, periodo_id: int, t: int,
                               lineas: list[Linea],
                               cambios: dict[int, str | None],
                               usuario: str) -> None:
        """Los de las cantidades del mes, con su evento `IMPORTES`."""
        mes = uow.importes.de_trabajador(periodo_id, t)
        nuevo = dict(mes)
        for vid, tex in sorted(cambios.items()):
            nuevo[vid] = dataclasses.replace(mes[vid], comentario=tex)
            uow.importes.guardar(periodo_id, nuevo[vid], usuario)
        uow.eventos.registrar(
            periodo_id, t, TipoEvento.IMPORTES, usuario,
            _snapshot_importes(_foto_importes(lineas, mes)),
            _snapshot_importes(_foto_importes(lineas, nuevo)))
