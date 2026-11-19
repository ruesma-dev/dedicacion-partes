# domain/importes.py
"""F-069 · los vinculados de CANTIDAD: caja, km y viajes (R1, R2, R5, R8,
R32; design §6.1; docs/ARCHITECTURE.md#regla-vinculado, «Cantidad y
comentario»).

Puro, sin dependencias. Un vinculado es de cantidad si su tipo
(`auxrestip.cod`) está en `sync.vinculados.importes` de `config.yaml`, que
da su UNIDAD (`eur` | `km`) y su REPARTO: `pct`, una cantidad del mes que
se reparte con el % del titular (km y viajes), u `obra`, una cantidad por
cada línea del titular, entera a esa obra (caja). La api guarda lo que se
teclea tal cual (km o €): no multiplica; el importe lo calcula el transfer.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from domain.errors import ImporteInvalido
from domain.models import ImporteMes, Linea

#: R1 (D2, D12): las unidades y los repartos que se admiten en la config.
UNIDADES = ("eur", "km")
REPARTOS = ("pct", "obra")
REPARTO_PCT = "pct"
REPARTO_OBRA = "obra"
UNIDAD_KM = "km"
#: R5: la cantidad más alta por unidad (cabe en `Numeric(12, 2)`).
TOPES = {"eur": Decimal("999999.99"), "km": Decimal("99999.99")}
#: R5, R9: el largo máximo de un comentario (`String(200)`).
COMENTARIO_MAX = 200
_CENTIMO = Decimal("0.01")


@dataclass(frozen=True)
class TipoCantidad:
    """R1, R2: la unidad (`eur` | `km`) y el reparto (`pct` | `obra`) de un
    tipo de vinculado de cantidad."""

    unidad: str
    reparto: str


def normalizar_tipo(tipo: str | None) -> str:
    """El tipo sin espacios (ni a los lados ni dentro) y en mayúsculas."""
    return "".join((tipo or "").split()).upper()


def tipos_de_config(cfg: Any) -> dict[str, TipoCantidad]:
    """R1: `sync.vinculados.importes` como `{tipo: TipoCantidad}`. Sin la
    clave, ninguno. Un tipo vacío, una entrada que no es un mapa o una
    unidad o un reparto fuera de la lista: `ValueError` (la api no
    arranca)."""
    if cfg is None:
        return {}
    if not isinstance(cfg, Mapping):
        raise ValueError("sync.vinculados.importes debe ser un mapa "
                         "tipo -> {unidad, reparto}")
    out: dict[str, TipoCantidad] = {}
    for tipo, datos in cfg.items():
        clave = normalizar_tipo(str(tipo))
        if not clave or not isinstance(datos, Mapping):
            raise ValueError(
                f"sync.vinculados.importes: entrada no válida {tipo!r}")
        unidad = str(datos.get("unidad") or "").strip().lower()
        reparto = str(datos.get("reparto") or "").strip().lower()
        if unidad not in UNIDADES or reparto not in REPARTOS:
            raise ValueError(
                f"sync.vinculados.importes.{clave}: unidad {unidad!r} o "
                f"reparto {reparto!r} desconocidos")
        out[clave] = TipoCantidad(unidad=unidad, reparto=reparto)
    return out


def precio_km_de_config(valor: Any) -> Decimal | None:
    """R1 (D10): `sync.vinculados.precio_km`; sin él, None; un booleano, un
    texto que no es número o un valor ≤ 0: `ValueError`."""
    if valor is None:
        return None
    try:
        if isinstance(valor, bool):
            raise InvalidOperation
        precio = Decimal(str(valor))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(
            f"sync.vinculados.precio_km no es un número: {valor!r}") from exc
    if not precio.is_finite() or precio <= 0:
        raise ValueError(
            f"sync.vinculados.precio_km debe ser > 0: {valor!r}")
    return precio


def tipo_de(tipo: str | None, importes: Mapping[str, TipoCantidad]
            ) -> TipoCantidad | None:
    """R2: la unidad y el reparto del tipo de un vinculado, o None si no es
    de cantidad (fuera de la lista: el vinculado de F-044, como hoy)."""
    return importes.get(normalizar_tipo(tipo))


def validar_cantidad(valor: Any, unidad: str) -> Decimal | None:
    """R5: la cantidad como `Decimal` con dos decimales, o None si no hay.
    Un booleano, un texto que no es número, un no finito, un negativo, más
    de dos decimales o más del tope de su unidad: `ImporteInvalido`."""
    if valor is None:
        return None
    if isinstance(valor, bool) or not isinstance(
            valor, (int, float, str, Decimal)):
        raise ImporteInvalido(f"La cantidad {valor!r} no es un número")
    try:
        cantidad = Decimal(str(valor).strip())
    except InvalidOperation as exc:
        raise ImporteInvalido(f"La cantidad {valor!r} no es un número") \
            from exc
    if not cantidad.is_finite():
        raise ImporteInvalido(f"La cantidad {valor!r} no es un número")
    if cantidad < 0:
        raise ImporteInvalido(f"La cantidad {valor!r} es negativa")
    redondeada = cantidad.quantize(_CENTIMO)
    if redondeada != cantidad:
        raise ImporteInvalido(
            f"La cantidad {valor!r} tiene más de dos decimales")
    tope = TOPES.get(unidad, TOPES["eur"])
    if redondeada > tope:
        raise ImporteInvalido(
            f"La cantidad {valor!r} pasa del máximo ({tope} {unidad})")
    return redondeada


def validar_comentario(texto: Any) -> str | None:
    """R5, R9: el comentario sin espacios a los lados; vacío ⇒ None; un no
    texto o más de 200 caracteres: `ImporteInvalido`."""
    if texto is None:
        return None
    if not isinstance(texto, str):
        raise ImporteInvalido(f"El comentario {texto!r} no es un texto")
    limpio = texto.strip()
    if len(limpio) > COMENTARIO_MAX:
        raise ImporteInvalido(
            f"El comentario pasa de {COMENTARIO_MAX} caracteres")
    return limpio or None


def a_copiar(origen: Mapping[Any, Any], destino: Mapping[Any, Any]
             ) -> dict[Any, Any]:
    """R8 (D7): de `origen`, lo que no está en `destino` (copiar el mes
    nunca pisa lo que ya hay)."""
    return {k: v for k, v in origen.items() if k not in destino}


def comentario_de_sigrid(tex: str | None) -> str | None:
    """R32 (D15, D17): el comentario de un `tex` que publica el transfer:
    sin espacios a los lados; vacío ⇒ None. La marca de pruebas ya la quitó
    el transfer (D17, 2026-11-19): la api no la conoce ni la busca."""
    return (tex or "").strip() or None


def importes_del_mes(lineas: list[Linea], filas: Mapping[int, ImporteMes],
                     importes: Mapping[str, TipoCantidad]) -> list[ImporteMes]:
    """R10: uno por vinculado POR % de las subfilas del trabajador (en
    orden de vinculado), con su tipo, código y unidad y, si la hay, la
    cantidad del mes guardada (`filas`). Sin subfilas de cantidad, []."""
    vistos: dict[int, ImporteMes] = {}
    for ln in lineas:
        for v in ln.vinculados:
            tipo = tipo_de(v.tipo, importes)
            if (tipo is None or tipo.reparto != REPARTO_PCT
                    or v.vinculado_ide in vistos):
                continue
            fila = filas.get(v.vinculado_ide)
            vistos[v.vinculado_ide] = ImporteMes(
                vinculado_ide=v.vinculado_ide, tipo=v.tipo, cod=v.cod,
                unidad=tipo.unidad,
                cantidad=fila.cantidad if fila else None,
                copiado=bool(fila.copiado) if fila else False,
                comentario=fila.comentario if fila else None)
    return [vistos[k] for k in sorted(vistos)]
