# application/services/universo_var.py
"""Universo VAR: las partidas de la obra de obras varias que se ofrecen
como obras propias del cuadrante.

La regla es `docs/ARCHITECTURE.md#regla-var`; aquí solo se implementa. La
obra es la del ajuste `VAR_OBRA_COD`, dentro de la empresa de la petición
(ARCHITECTURE.md#regla-empresa), y el umbral del número inicial, el del
ajuste `VAR_PARTIDA_DESDE`.

Un único sitio (F-039, como F-025 con la postventa): el universo de
`POST /api/var/universo` y la validación del `var_paride` en el preflight
cargan el catálogo con `cargar_catalogo_var` y lo consultan con
`partida_var_de`. Así una partida está en el universo si y solo si el
preflight acepta una línea imputada a ella: no hay dos criterios que puedan
divergir. Ningún catálogo se guarda en una instancia.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from domain.errores import ObraAmbigua
from domain.models.registro_models import ObraEntrada

from application.services.partida_catalog import PartidaNodo
from application.services.partida_resolver import construir_catalogo

#: Sin `VAR_OBRA_COD` no hay obra VAR: ni universo ni líneas VAR.
MOTIVO_VAR_OFF = "registro VAR desactivado (VAR_OBRA_COD vacío)"
#: Motivos con los que el preflight omite una línea con `var_paride` (R6).
#: Todos nombran la partida y, si viene al caso, la obra.
MOTIVO_VAR_SIN_UNIVERSO = "partida VAR {paride} no registrable: {motivo}"
MOTIVO_VAR_OTRA_OBRA = ("partida VAR {paride}: la obra {obra} no es la obra "
                        "VAR {var}")
MOTIVO_VAR_FUERA = ("partida VAR {paride} fuera del universo VAR de {var} "
                    "(hoja activa con número inicial >= {desde})")
MOTIVO_VAR_POSTVENTA = ("partida VAR {paride}: una línea de postventa no se "
                        "imputa a una partida VAR")

_NUMERO = re.compile(r"[0-9]+")


@dataclass(frozen=True)
class CatalogoVar:
    """Obra VAR resuelta en la empresa y SOLO sus partidas VAR, por `ide`.

    Sin obra (`obra is None`), `partidas` está vacío y `motivo` dice por qué.
    """

    obra: ObraEntrada | None
    partidas: dict[int, PartidaNodo]
    motivo: str | None


def numero_inicial(cod: str | None) -> int | None:
    """Los dígitos con que empieza el código, tras quitar espacios, como
    número (`007` → 7, `7.1` → 7); `None` si no empieza por dígito."""
    m = _NUMERO.match((cod or "").strip())
    return int(m.group()) if m else None


def es_partida_var(nodo: PartidaNodo, desde: int) -> bool:
    """Hoja activa cuyo número inicial es mayor o igual que `desde`."""
    numero = numero_inicial(nodo.cod)
    return (nodo.es_hoja and nodo.activa and numero is not None
            and numero >= desde)


def cargar_catalogo_var(cliente, settings, empresa: int) -> CatalogoVar:
    """Lee la obra VAR de `empresa` y su presupuesto (dos lecturas) y se
    queda con las partidas VAR.

    Sin `VAR_OBRA_COD` no lee nada. Con la obra ausente o ambigua en la
    empresa, devuelve el motivo sin presupuesto.
    """
    cod = (settings.var_obra_cod or "").strip()
    if not cod:
        return CatalogoVar(obra=None, partidas={}, motivo=MOTIVO_VAR_OFF)
    try:
        obra = cliente.obra_por_codigo(cod, empresa)
    except ObraAmbigua as exc:
        return CatalogoVar(
            obra=None, partidas={},
            motivo=f"obra VAR '{cod}' ambigua en la empresa {empresa}: {exc}")
    if obra is None:
        return CatalogoVar(
            obra=None, partidas={},
            motivo=(f"obra VAR '{cod}' no encontrada en Sigrid en la "
                    f"empresa {empresa}"))
    desde = int(settings.var_partida_desde)
    nodos = construir_catalogo(cliente.capitulos_de_obra(int(obra.ide)))
    return CatalogoVar(
        obra=obra, motivo=None,
        partidas={ide: n for ide, n in nodos.items()
                  if es_partida_var(n, desde)})


def partida_var_de(catalogo: CatalogoVar, obra_ide: int | None,
                   var_paride: int, desde: int
                   ) -> tuple[PartidaNodo | None, str | None]:
    """(partida, motivo) de una línea con `var_paride` de la obra
    `obra_ide`, contra el catálogo ya cargado: la partida solo vale si está
    en el universo y la obra es la obra VAR."""
    if catalogo.obra is None:
        return None, MOTIVO_VAR_SIN_UNIVERSO.format(paride=var_paride,
                                                    motivo=catalogo.motivo)
    var = catalogo.obra.codigo
    if obra_ide != catalogo.obra.ide:
        return None, MOTIVO_VAR_OTRA_OBRA.format(paride=var_paride,
                                                 obra=obra_ide, var=var)
    nodo = catalogo.partidas.get(var_paride)
    if nodo is None:
        return None, MOTIVO_VAR_FUERA.format(paride=var_paride, var=var,
                                             desde=desde)
    return nodo, None


class UniversoVar:
    """Universo VAR de una empresa (contrato de `POST /api/var/universo`).
    Solo lee; sin estado entre peticiones."""

    def __init__(self, *, cliente, settings) -> None:
        self._cli = cliente
        self._st = settings

    def calcular(self, empresa: int) -> dict:
        """Una carga del catálogo por petición; un fallo de lectura sube
        tal cual (no hay universo parcial)."""
        catalogo = cargar_catalogo_var(self._cli, self._st, empresa)
        return {
            "empresa": empresa,
            "desde": int(self._st.var_partida_desde),
            "motivo": catalogo.motivo,
            "obra_var": asdict(catalogo.obra) if catalogo.obra else None,
            "partidas": [{"ide": n.ide, "cod": n.cod, "res": n.res}
                         for _ide, n in sorted(catalogo.partidas.items())],
        }
