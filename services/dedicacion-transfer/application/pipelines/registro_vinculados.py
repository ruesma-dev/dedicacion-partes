# application/pipelines/registro_vinculados.py
"""F-044 · `PasoVinculados`: los recursos vinculados dentro del pipeline de
registro (design §6.3; ARCHITECTURE.md#regla-vinculado).

Aparte de `registro_pipeline.py` para no engordarlo. Hoy hace la propuesta
de partida de cada subfila (`proponer`, R9 y R29) con la misma regla que
usará el preflight (`reglas_vinculados.partida_del_vinculado`): la partida
del titular en postventa, VAR o partida no `CI*`; si no, la CI del tipo
del vinculado, buscada por la subcuenta de la cuenta de su hora por
defecto (`reshor.caaide`) entre las cuentas del presupuesto de la obra.

Lecturas (R27): las horas de los vinculados y las cuentas del presupuesto,
UNA vez por petición cada una y solo si alguna subfila las necesita. Sin
vinculados no se lee nada más que antes.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from application.services.cuenta_analitica import subcuenta_de_linea
from application.services.partida_catalog import PartidaNodo
from application.services.propuesta_partida import Propuesta
from application.services.reglas_vinculados import (
    METODO_MANUAL,
    PartidaTitular,
    partida_ci_del_tipo,
    partida_del_vinculado,
)


class _UnaVez:
    """El resultado de `leer`, leído la primera vez que se pide."""

    def __init__(self, leer: Callable[[], Any]) -> None:
        self._leer = leer
        self._leido = False
        self._valor: Any = None

    def __call__(self) -> Any:
        if not self._leido:
            self._valor = self._leer()
            self._leido = True
        return self._valor


def _titular_de_propuesta(linea: dict, catalogo: dict[int, PartidaNodo],
                          propuesta: Propuesta | None
                          ) -> PartidaTitular | None:
    """La partida del titular de una línea del selector: la elegida si es
    hoja activa de su catálogo (si no, None: en el preflight se omitiría y
    sus vinculados con él); sin elegida, su propuesta (o sin partida)."""
    destino = "postventa" if linea["es_postventa"] else "obra"
    elegida = linea.get("paride")
    if elegida:
        nodo = catalogo.get(int(elegida))
        if nodo is None or not (nodo.es_hoja and nodo.activa):
            return None
        return PartidaTitular(destino=destino, paride=int(nodo.ide),
                              cod=nodo.cod, res=nodo.res,
                              metodo=METODO_MANUAL)
    if propuesta is None:
        return PartidaTitular(destino=destino, paride=0)
    return PartidaTitular(destino=destino, paride=int(propuesta.paride),
                          cod=propuesta.cod, res=propuesta.res,
                          metodo=propuesta.metodo)


class PasoVinculados:
    """Los vinculados de una petición sobre el mismo cliente (o la memoria
    del lote) que el pipeline."""

    def __init__(self, cliente) -> None:
        self._cli = cliente

    def proponer(self, *, origen_ide: int, nodos: dict[int, PartidaNodo],
                 nodos_pv: dict[int, PartidaNodo], lineas: list[dict],
                 propuestas: dict[str, Propuesta | None]
                 ) -> dict[str, dict[str, dict | None]]:
        """R9: por línea con `vinculados`, la propuesta de cada uno
        (`{paride, cod, res, metodo, origen}`, como la del titular) o None
        (sin partida). Vacío si ninguna línea trae vinculados."""
        con = [l for l in lineas if l.get("vinculados")]
        if not con:
            return {}
        horas = _UnaVez(lambda: self._cli.horas_de_recursos(sorted({
            int(v["recurso_ide"]) for l in con for v in l["vinculados"]})))
        cuentas = _UnaVez(
            lambda: self._cli.cuentas_del_presupuesto(int(origen_ide)))
        out: dict[str, dict[str, dict | None]] = {}
        for l in con:
            titular = _titular_de_propuesta(
                l, nodos_pv if l["es_postventa"] else nodos,
                propuestas.get(l["clave"]))
            por_recurso: dict[str, dict | None] = {}
            for v in l["vinculados"]:
                rid = int(v["recurso_ide"])
                if titular is None:
                    por_recurso[str(rid)] = None
                    continue

                def ci(rid: int = rid):
                    sub = subcuenta_de_linea(horas().get(rid, []), None)
                    return partida_ci_del_tipo(nodos, cuentas(), sub)

                p = partida_del_vinculado(titular, None, True, ci)
                por_recurso[str(rid)] = (
                    asdict(Propuesta(p.paride, p.cod, p.res, p.metodo))
                    if p.paride else None)
            out[l["clave"]] = por_recurso
        return out
