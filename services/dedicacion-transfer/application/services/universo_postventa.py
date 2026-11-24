# application/services/universo_postventa.py
"""Universo de postventa: qué obras admiten una línea de postventa.

La regla es `docs/ARCHITECTURE.md#regla-p5`; aquí solo se implementa. La
obra de postventa es la del ajuste `POSTVENTA_OBRA_COD`, dentro de la
empresa de la petición (ARCHITECTURE.md#regla-empresa).

Dos funciones y un único sitio (F-025, D1): el preflight y
`POST /api/postventa/universo` cargan el catálogo con
`cargar_catalogo_postventa` y casan cada obra con `casar_postventa`. Así una
obra está en el universo con la partida X si y solo si el preflight de su
línea de postventa publica X: no hay dos criterios que puedan divergir.

Ningún catálogo se guarda en una instancia: vive lo que dura la petición
que lo leyó.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from domain.errores import ObraAmbigua
from domain.models.registro_models import ObraEntrada

from application.services.partida_catalog import PartidaNodo
from application.services.partida_resolver import (
    construir_catalogo,
    resolver_postventa,
)
from application.services.reglas_porcentajes import MOTIVO_POSTVENTA_OFF


@dataclass(frozen=True)
class CatalogoPostventa:
    """Obra de postventa resuelta en la empresa y su presupuesto.

    Sin obra (`obra is None`), `nodos` está vacío y `motivo` dice por qué.
    """

    obra: ObraEntrada | None
    nodos: dict[int, PartidaNodo]
    motivo: str | None


def obra_de_postventa(cliente, settings,
                      empresa: int) -> tuple[ObraEntrada | None, str | None]:
    """La obra de postventa de `empresa` (una lectura) y, sin ella, por qué.

    Con el registro de postventa desactivado no lee nada. F-074 (R3): el
    preflight la resuelve así, como destino, sin leer su presupuesto.
    """
    if not settings.postventa_registrar:
        return None, MOTIVO_POSTVENTA_OFF
    cod_pv = settings.postventa_obra_cod
    try:
        obra_pv = cliente.obra_por_codigo(cod_pv, empresa)
    except ObraAmbigua as exc:
        return None, (f"obra de postventa '{cod_pv}' ambigua en la empresa "
                      f"{empresa}: {exc}")
    if obra_pv is None:
        return None, (f"obra de postventa '{cod_pv}' no encontrada en Sigrid "
                      f"en la empresa {empresa}")
    return obra_pv, None


def cargar_catalogo_postventa(cliente, settings,
                              empresa: int) -> CatalogoPostventa:
    """Lee la obra de postventa de `empresa` y su presupuesto (dos lecturas).

    Con el registro de postventa desactivado no lee nada. Con la obra
    ausente o ambigua en la empresa, devuelve el motivo sin presupuesto.
    """
    obra_pv, motivo = obra_de_postventa(cliente, settings, empresa)
    if obra_pv is None:
        return CatalogoPostventa(obra=None, nodos={}, motivo=motivo)
    nodos = construir_catalogo(cliente.capitulos_de_obra(int(obra_pv.ide)))
    return CatalogoPostventa(obra=obra_pv, nodos=nodos, motivo=None)


def casar_postventa(catalogo: CatalogoPostventa, codigo: str | None,
                    nombre: str | None
                    ) -> tuple[dict | None, str | None]:
    """(partida, motivo) de una obra contra el catálogo ya cargado.

    Sin catálogo, el motivo es el suyo; sin casado, «no casa».
    """
    if catalogo.obra is None:
        return None, catalogo.motivo
    nodo = resolver_postventa(catalogo.nodos, codigo, nombre)
    if nodo is None:
        return None, (f"la obra {codigo or nombre} no casa con ninguna "
                      f"partida de {catalogo.obra.codigo}")
    return {"ide": nodo.ide, "cod": nodo.cod, "res": nodo.res}, None


class UniversoPostventa:
    """Universo de postventa de una empresa: sus obras que casan con una
    partida de la obra de postventa (contrato de
    `POST /api/postventa/universo`). Solo lee; sin estado entre peticiones."""

    def __init__(self, *, cliente, settings) -> None:
        self._cli = cliente
        self._st = settings

    def calcular(self, empresa: int, obras: list[ObraEntrada]) -> dict:
        """Una carga del catálogo por petición (R7) y un casado por obra.

        Sin obras no se lee nada. Un fallo de lectura sube tal cual: no hay
        universo parcial (R6). F-074 (R10, D6 b): `motivos`, el texto de
        `casar_postventa` de cada obra pedida que no casa, por su `ide`;
        solo si hay alguna (sin ella, la respuesta de siempre).
        """
        catalogo = (cargar_catalogo_postventa(self._cli, self._st, empresa)
                    if obras else CatalogoPostventa(None, {}, None))
        casadas = []
        motivos: dict[int, str | None] = {}
        for obra in obras:
            partida, motivo = casar_postventa(catalogo, obra.codigo,
                                              obra.nombre)
            if partida is not None:
                casadas.append({"ide": obra.ide, "partida": partida})
            elif obra.ide is not None:
                motivos[obra.ide] = motivo
        return {
            "empresa": empresa,
            "obra_postventa": asdict(catalogo.obra) if catalogo.obra else None,
            "motivo": catalogo.motivo,
            "casadas": len(casadas),
            "obras": casadas,
            **({"motivos": motivos} if motivos else {}),
        }
