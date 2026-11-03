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
from dataclasses import dataclass, field
from typing import Any

from domain.models import (
    FiltroEmpresa,
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

from application.use_cases import _periodo_abierto_o_error, _snapshot

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


class TraerDeSigrid:
    """R2-R3, R13-R27: comparar con Sigrid y escribir lo aceptado."""

    def __init__(self, gateway: PorcentajesSigridGateway) -> None:
        self._gateway = gateway

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

        for t in sorted(nuevas):
            antes = uow.asignaciones.lineas_de_trabajador(periodo_id, t)
            for ln, c in zip(nuevas[t], por_aceptar[t]):
                assert c.entrada is not None
                uow.asignaciones.aceptar_entrada(
                    periodo_id, t, ln, hmores_ide=c.entrada.hmores_ide,
                    parte_cod=c.entrada.parte_cod, usuario=usuario)
            uow.eventos.registrar(
                periodo_id, t, TipoEvento.SIGRID, usuario, _snapshot(antes),
                _snapshot(_despues(antes, nuevas[t])))
        if nuevas:
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
