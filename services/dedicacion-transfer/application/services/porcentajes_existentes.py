# application/services/porcentajes_existentes.py
"""F-054, parte A: los porcentajes que YA hay en los partes de Sigrid,
traducidos a las entradas del cuadrante (R4-R12; design §4.2,
ARCHITECTURE.md#regla-traer-sigrid).

Solo lee. El transfer lee (`lineas_mensuales_del_periodo`) y traduce cada
línea a su entrada: una obra normal (`destino = normal`), la de postventa
(`destino = postventa` y la obra de origen) o la VAR (`destino = var` y su
`var_paride`). Quién es trabajador lo decide la api por recurso (R14): aquí
no se mira el recurso.

La traducción usa las MISMAS funciones que el preflight (R12):
`casar_postventa` (`#regla-p5`), al revés, para saber de qué obra viene una
línea de la obra de postventa, y `partida_var_de` (`#regla-var`) para la
VAR. Así lo traído se registra en la partida de la que vino. Los catálogos
de postventa y VAR se leen solo si alguna línea es de esa obra (R11); las
de la obra de pruebas solo se cuentan (R5).
"""
from __future__ import annotations

from dataclasses import asdict

from domain.models.registro_models import LineaMensualSigrid, ObraEntrada

from application.services.universo_postventa import (
    CatalogoPostventa,
    cargar_catalogo_postventa,
    casar_postventa,
)
from application.services.universo_var import (
    CatalogoVar,
    cargar_catalogo_var,
    partida_var_de,
)

#: R9: la partida de la línea de postventa no casa con ninguna obra de las
#: que admiten postventa, o casa con varias.
MOTIVO_PV_NINGUNA = ("la partida {partida} de {pv} no casa con ninguna obra "
                     "que admita postventa")
MOTIVO_PV_VARIAS = ("la partida {partida} de {pv} casa con varias obras "
                    "({obras})")


def _cod(valor: str | None) -> str:
    return (valor or "").strip()


def obras_por_partida(catalogo: CatalogoPostventa,
                      obras: list[ObraEntrada]
                      ) -> dict[int, list[ObraEntrada]]:
    """El casado de postventa al revés (R9): por partida de la obra de
    postventa, las obras de `obras` cuyo `casar_postventa` la da, por
    `ide`. Sin catálogo, vacío."""
    out: dict[int, list[ObraEntrada]] = {}
    for obra in obras:
        partida, _ = casar_postventa(catalogo, obra.codigo, obra.nombre)
        if partida is not None:
            out.setdefault(int(partida["ide"]), []).append(obra)
    return {k: sorted(v, key=lambda o: int(o.ide)) for k, v in out.items()}


def traducir(linea: LineaMensualSigrid, *, cod_pruebas: str,
             cod_postventa: str, cod_var: str,
             inverso: dict[int, list[ObraEntrada]],
             catalogo_var: CatalogoVar | None, desde: int,
             motivo_postventa: str | None = None) -> dict | None:
    """La línea con lo de R6 y su entrada: `destino`, `obra_origen_ide`
    (postventa), `var_paride` (VAR) y `motivo` si no se puede traer. `None`
    si es de la obra de pruebas (R5). `motivo_postventa`, el del catálogo
    de postventa si no lo hay."""
    obra = _cod(linea.obra_cod)
    if obra and obra == _cod(cod_pruebas):
        return None
    out = {**asdict(linea), "destino": "normal", "obra_origen_ide": None,
           "var_paride": None, "motivo": None}
    if obra and obra == _cod(cod_postventa):
        out["destino"] = "postventa"
        casan = inverso.get(int(linea.paride or 0), [])
        if motivo_postventa:
            out["motivo"] = motivo_postventa
        elif len(casan) == 1:
            out["obra_origen_ide"] = int(casan[0].ide)
        elif casan:
            out["motivo"] = MOTIVO_PV_VARIAS.format(
                partida=linea.paride, pv=obra,
                obras=", ".join(str(o.ide) for o in casan))
        else:
            out["motivo"] = MOTIVO_PV_NINGUNA.format(partida=linea.paride,
                                                     pv=obra)
    elif obra and obra == _cod(cod_var) and catalogo_var is not None:
        out["destino"] = "var"
        nodo, motivo = partida_var_de(catalogo_var, linea.obra_ide,
                                      int(linea.paride or 0), int(desde))
        if nodo is None:
            out["motivo"] = motivo
        else:
            out["var_paride"] = int(nodo.ide)
    return out


class PorcentajesExistentes:
    """Contrato de `POST /api/porcentajes/existentes` (design §1). Solo lee;
    sin estado entre peticiones."""

    def __init__(self, *, cliente, settings) -> None:
        self._cli = cliente
        self._st = settings

    def calcular(self, empresa: int, ano: int, mes: int,
                 obras: list[ObraEntrada]) -> dict:
        """UNA lectura de las líneas (R4) y, solo si hacen falta, los
        catálogos de postventa y VAR (R11). Un fallo de lectura sube."""
        leidas = self._cli.lineas_mensuales_del_periodo(empresa, ano, mes)
        cod_pv = _cod(self._st.postventa_obra_cod)
        cod_var = _cod(getattr(self._st, "var_obra_cod", ""))
        codigos = {_cod(l.obra_cod) for l in leidas}
        catalogo_pv = (cargar_catalogo_postventa(self._cli, self._st, empresa)
                       if cod_pv and cod_pv in codigos else None)
        catalogo_var = (cargar_catalogo_var(self._cli, self._st, empresa)
                        if cod_var and cod_var in codigos else None)
        inverso = (obras_por_partida(catalogo_pv, obras)
                   if catalogo_pv is not None else {})
        traducidas = [traducir(
            l, cod_pruebas=self._st.obra_pruebas_cod, cod_postventa=cod_pv,
            cod_var=cod_var, inverso=inverso, catalogo_var=catalogo_var,
            desde=int(getattr(self._st, "var_partida_desde", 0) or 0),
            motivo_postventa=catalogo_pv.motivo if catalogo_pv else None)
            for l in leidas]
        lineas = sorted((t for t in traducidas if t is not None),
                        key=lambda t: t["hmores_ide"])
        return {
            "lineas_leidas": len(leidas),
            "excluidas_pruebas": len(leidas) - len(lineas),
            "obra_postventa": (asdict(catalogo_pv.obra)
                               if catalogo_pv and catalogo_pv.obra else None),
            "motivo_postventa": catalogo_pv.motivo if catalogo_pv else None,
            "obra_var": (asdict(catalogo_var.obra)
                         if catalogo_var and catalogo_var.obra else None),
            "motivo_var": catalogo_var.motivo if catalogo_var else None,
            "lineas": lineas,
        }
