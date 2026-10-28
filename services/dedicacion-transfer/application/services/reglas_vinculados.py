# application/services/reglas_vinculados.py
"""F-044 · reglas puras de los recursos vinculados (design §6.2;
ARCHITECTURE.md#regla-vinculado).

Un vinculado (teléfono, gasoil, vehículo… con el campo «Recurso Asociado»
hacia el trabajador) se registra con el % de su titular en cada obra. Aquí
se decide su LÍNEA y su PARTIDA, sin leer nada:

  - `decidir_vinculados` (R12, R14, R18): una `AccionVinculado` por
    vinculado de la línea, con el `can`, la `fec`, el destino y el periodo
    del titular, sin normalizar, y la hora por defecto del vinculado
    (`hora_del_vinculado`) con su `pre`; sin ella o con `pre` 0, omitido
    («sin importe mensual»); titular omitido, omitido («sigue al
    trabajador»); titular ya registrado, se decide solo.
  - `synckey_vinculado` (R13) y `es_linea_de` (R19, R21, R23): la jornada
    del vinculado es la de SU hora, no `M*`.

  - `partida_ci_del_tipo` (R15, R16): la única hoja activa del presupuesto
    de la obra cuya cuenta analítica tiene la subcuenta de la cuenta del
    vinculado (`CICO13` ↔ `.CI.4.13`). Ninguna o varias ⇒ sin partida con
    su motivo; nunca la primera.
  - `partida_del_vinculado` (R15-R17): la elegida en su subfila si vale; si
    el titular va a postventa, a una entrada VAR o a una partida que no es
    `CI*`, la del titular; si no, la CI del tipo, que llega como función
    para leer las cuentas solo si hace falta (R27).

Las lecturas (presupuesto, cuentas, validez de la elegida) son del
pipeline; este módulo no importa ningún cliente.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from domain.models.registro_models import (
    AccionLinea,
    AccionVinculado,
    HoraRecurso,
    LineaEntrada,
    LineaSigrid,
)

from application.services import text_match as tm
from application.services.cuenta_analitica import subcuenta
from application.services.partida_catalog import PartidaNodo
from application.services.partida_matcher import match_partida
from application.services.reglas_porcentajes import (
    PREFIJO_CLAVE_SIN_PARTIDA,
    es_de_la_hora,
)

#: Métodos de la partida de un vinculado (`partida_metodo`).
METODO_MANUAL = "manual"        # la elegida en su subfila
METODO_TITULAR = "titular"      # la de su titular (R17)
METODO_CI_TIPO = "ci_tipo"      # la CI de su tipo (R15)

#: Sin partida (R16): ninguna hoja activa con la subcuenta, o varias.
MOTIVO_SIN_CI = "sin_ci"
MOTIVO_VARIAS_CI = "varias_ci"
#: R15: la elegida que no es hoja activa del presupuesto (como F-050).
MOTIVO_ELEGIDA_NO_VALIDA = (
    "la partida {cod} elegida para el recurso vinculado no es una partida "
    "hoja activa del presupuesto: no se escribe; elige otra partida")

#: R14 (D1b): sin hora por defecto o con `pre` 0. Se formatea con tipo, cod
#: y hora; cabe en los 300 caracteres de `sigrid_motivo` de la api.
MOTIVO_SIN_IMPORTE = (
    "sin importe mensual: el recurso vinculado {tipo} {cod} no tiene precio "
    "en su hora por defecto ({hora}): no se registra")
#: R18 (D10): el titular no se escribe; se formatea con su motivo.
MOTIVO_SIGUE_AL_TRABAJADOR = "sigue al trabajador: {motivo}"
#: R28: el titular no quedó escrito sin estar en `omitidas` (su pisado sin
#: confirmar, que no deja rastro allí).
MOTIVO_TITULAR_SIN_ESCRIBIR = (
    "el trabajador no se ha escrito en esta ejecución (pendiente de "
    "confirmar)")
#: R26: el pisado del vinculado sin confirmar; se formatea con la clave.
MOTIVO_PISADO_PENDIENTE = (
    "pendiente de confirmar el pisado del recurso vinculado (clave {clave})")
#: R13 (D9): empieza por el prefijo de las nuestras (`PREFIJO_SYNCKEY`,
#: `porcentajes:`), que no se importa aquí: este módulo no toca la
#: infraestructura (lo vigila un test).
PREFIJO_SYNCKEY_VINCULADO = "porcentajes:vin:"

#: Destinos y métodos del titular con los que el vinculado va a su partida.
_DESTINO_POSTVENTA = "postventa"
_METODO_VAR = "var"


@dataclass(frozen=True)
class PartidaElegida:
    """Una partida concreta: la elegida en la subfila o la CI del tipo."""
    paride: int
    cod: str | None = None
    res: str | None = None


@dataclass(frozen=True)
class PartidaTitular:
    """Lo que el vinculado necesita de la partida de su titular: destino
    (`obra` | `postventa`), partida (0 = sin partida) y método (`var` en
    una entrada VAR)."""
    destino: str
    paride: int
    cod: str | None = None
    res: str | None = None
    metodo: str | None = None


@dataclass(frozen=True)
class PartidaVinculado:
    """La partida decidida para un vinculado. `paride = 0` con
    `sin_partida` es «sin partida» a confirmar (R16, motivo `sin_ci` o
    `varias_ci`); con `omitir`, la elegida no vale y no se escribe (R15)."""
    paride: int = 0
    cod: str | None = None
    res: str | None = None
    metodo: str | None = None
    motivo: str | None = None
    sin_partida: bool = False
    omitir: bool = False


def _es_ci(cod: str | None) -> bool:
    return (cod or "").strip().upper().startswith("CI")


def va_con_el_titular(titular: PartidaTitular) -> bool:
    """R17: postventa, entrada VAR o una partida que no es `CI*` (`CP*`,
    `CD*`…). Un titular normal sin partida no tiene partida que dar."""
    if titular.destino == _DESTINO_POSTVENTA or titular.metodo == _METODO_VAR:
        return True
    return bool(titular.paride) and not _es_ci(titular.cod)


def hojas_con_subcuenta(hojas: dict[int, PartidaNodo],
                        cuentas: dict[int, str | None],
                        sub: str | None) -> list[PartidaNodo]:
    """F-068 (R4-R6): las hojas activas de `hojas` (el presupuesto de la
    obra) cuya cuenta (`cuentas`, por `ide` de partida) tiene la subcuenta
    `sub` (comparada entera, sin espacios ni mayúsculas), por `ide`. Sin
    `sub`, ninguna."""
    buscada = (sub or "").strip().upper()
    if not buscada:
        return []
    return [
        n for ide, cod in sorted(cuentas.items())
        for n in [hojas.get(ide)]
        if n is not None and n.es_hoja and n.activa
        and (subcuenta(cod) or "").upper() == buscada]


def es_capitulo_ci4(cod: str | None) -> bool:
    """F-068 (R8, D1): el código normalizado (mayúsculas, sin espacios ni
    guiones), partido por puntos, tiene `CI` como primer trozo y como
    segundo un número igual a 4 (`CI.4.13`, `CI.04.13`; no `CI0.04.05`)."""
    trozos = tm.normalize_code(cod).split(".")
    return (len(trozos) > 1 and trozos[0] == "CI"
            and trozos[1].isascii() and trozos[1].isdigit()
            and int(trozos[1]) == 4)


def puntuar(candidatas: list[PartidaNodo], tipo_res: str | None,
            descripcion: str | None, *, solo_casadas: bool
            ) -> dict[int, tuple[float, str | None]]:
    """F-068 (R5-R6): la puntuación del casador del trabajador
    (`match_partida`, categoría = `tipo_res`, nombre = `descripcion`) de
    cada candidata, UNA A UNA (el casador elige «la primera» en un empate y
    aquí el empate se tiene que ver): `{ide: (puntuación, método)}`. La que
    no casa, `(0.0, None)`, o fuera con `solo_casadas`."""
    out: dict[int, tuple[float, str | None]] = {}
    for n in candidatas:
        m = match_partida(tipo_res, descripcion, [n])
        if m is not None:
            out[int(n.ide)] = (m.score, m.metodo)
        elif not solo_casadas:
            out[int(n.ide)] = (0.0, None)
    return out


def desempate_ci4(empatadas: list[PartidaNodo]) -> PartidaNodo | None:
    """F-068 (R7, D1): la ÚNICA empatada del capítulo CI.4; con ninguna o
    con varias, None (nunca «la primera»)."""
    del_ci4 = [n for n in empatadas if es_capitulo_ci4(n.cod)]
    return del_ci4[0] if len(del_ci4) == 1 else None


def partida_ci_del_tipo(hojas: dict[int, PartidaNodo],
                        cuentas: dict[int, str | None],
                        sub: str | None) -> tuple[PartidaElegida | None, str]:
    """R15-R16: la ÚNICA hoja activa de `hojas` (el presupuesto de la obra)
    cuya cuenta (`cuentas`, por `ide` de partida) tiene la subcuenta `sub`
    (comparada entera, sin espacios ni mayúsculas). Devuelve la partida y
    `ci_tipo`, o None y el motivo: `sin_ci` (ninguna) o `varias_ci`."""
    candidatas = hojas_con_subcuenta(hojas, cuentas, sub)
    if not candidatas:
        return None, MOTIVO_SIN_CI
    if len(candidatas) > 1:
        return None, MOTIVO_VARIAS_CI
    n = candidatas[0]
    return PartidaElegida(paride=int(n.ide), cod=n.cod, res=n.res), \
        METODO_CI_TIPO


def partida_del_vinculado(
    titular: PartidaTitular,
    elegida: PartidaElegida | None,
    elegida_valida: bool,
    ci: Callable[[], tuple[PartidaElegida | None, str]],
) -> PartidaVinculado:
    """R15-R17, en este orden: la elegida (si no vale, se omite); la del
    titular en postventa, VAR o partida no `CI*`; la CI del tipo (`ci`, que
    solo se llama aquí); sin ella, sin partida con su motivo."""
    if elegida is not None:
        if not elegida_valida:
            return PartidaVinculado(
                motivo=MOTIVO_ELEGIDA_NO_VALIDA.format(
                    cod=elegida.cod or elegida.paride),
                omitir=True)
        return PartidaVinculado(paride=int(elegida.paride), cod=elegida.cod,
                                res=elegida.res, metodo=METODO_MANUAL)
    if va_con_el_titular(titular):
        return PartidaVinculado(paride=int(titular.paride or 0),
                                cod=titular.cod, res=titular.res,
                                metodo=METODO_TITULAR)
    partida, motivo = ci()
    if partida is None:
        return PartidaVinculado(motivo=motivo, sin_partida=True)
    return PartidaVinculado(paride=partida.paride, cod=partida.cod,
                            res=partida.res, metodo=METODO_CI_TIPO)


# ------------------------------------------------------------------ #
#  La línea del vinculado (R12-R14, R18, R19)
# ------------------------------------------------------------------ #

def synckey_vinculado(registro_id: int, recurso_ide: int) -> str:
    """R13 (D9): `porcentajes:vin:{registro_id}:{recurso_ide}`."""
    return f"{PREFIJO_SYNCKEY_VINCULADO}{int(registro_id)}:{int(recurso_ide)}"


def hora_del_vinculado(horas: list[HoraRecurso]) -> HoraRecurso | None:
    """R14 (D3): la hora por defecto del vinculado (`res.horide`, marcada
    `defecto` en su `reshor`); sin ella o con `pre` 0, None."""
    hora = next((h for h in horas if h.defecto), None)
    if hora is None or not float(hora.pre or 0.0):
        return None
    return hora


def es_linea_de(hora_codigo: str) -> Callable[[LineaSigrid], bool]:
    """R19, R21, R23: ¿la línea es de la hora `hora_codigo` del vinculado?
    Su jornada, en vez de `es_linea_mensual` (la del trabajador): una
    `MESVE` empieza por `M` y no es `M*` del trabajador."""
    return lambda ls: es_de_la_hora(ls, hora_codigo)


def decidir_vinculados(titular: AccionLinea, linea: LineaEntrada,
                       horas: dict[int, list[HoraRecurso]]
                       ) -> list[AccionVinculado]:
    """R12, R14, R18: una acción por vinculado de `linea`, en su orden, con
    el `can`, la `fec`, el destino y el periodo del titular (sin
    normalizar), la hora por defecto del vinculado, su `pre` y `tot =
    round(can × pre, 2)`, como `stmt_insert_linea`. La partida, la cuenta,
    el parte y lo que ya hay en Sigrid los decide el paso del pipeline."""
    out = []
    for v in linea.vinculados:
        base = {
            "registro_id": int(titular.registro_id),
            "recurso_ide": int(v.recurso_ide), "ano": int(titular.ano),
            "mes": int(titular.mes), "fecha_int": int(titular.fecha_int),
            "tipo": v.tipo, "tipo_res": v.tipo_res, "cod": v.cod,
            "nombre": titular.nombre, "destino": titular.destino}
        if titular.accion == "omitir":
            out.append(AccionVinculado(
                accion="omitir", motivo=MOTIVO_SIGUE_AL_TRABAJADOR.format(
                    motivo=titular.motivo), **base))
            continue
        suyas = horas.get(int(v.recurso_ide), [])
        hora = hora_del_vinculado(suyas)
        if hora is None:
            defecto = next((h for h in suyas if h.defecto), None)
            out.append(AccionVinculado(
                accion="omitir", motivo=MOTIVO_SIN_IMPORTE.format(
                    tipo=v.tipo, cod=v.cod,
                    hora=defecto.cod if defecto else "sin hora"), **base))
            continue
        can = float(titular.can)
        pre = float(hora.pre)
        out.append(AccionVinculado(
            accion="escribir", hora_ide=int(hora.horide),
            hora_codigo=hora.cod, can=can, pre=pre,
            tot=round(can * pre, 2), **base))
    return out


# ------------------------------------------------------------------ #
#  Avisos y claves del vinculado (R16, R23, R26)
# ------------------------------------------------------------------ #

#: R16: por qué no hay CI del tipo, en palabras.
_POR_QUE_SIN_CI = {
    MOTIVO_SIN_CI: "ninguna partida del presupuesto tiene la cuenta de su tipo",
    MOTIVO_VARIAS_CI: "varias partidas del presupuesto tienen la cuenta de "
                      "su tipo",
}
#: R16: aviso de la acción (lo pinta el modal) y motivo de la omisión si
#: nadie confirma; se formatean con tipo, cod y por_que. Caben en los 300
#: caracteres de `sigrid_motivo`.
AVISO_SIN_PARTIDA_VINCULADO = (
    "sin partida para el recurso vinculado {tipo} {cod} ({por_que}): no se "
    "escribe sin confirmarlo — elige una partida o marca la confirmación")
MOTIVO_SIN_PARTIDA_VINCULADO = (
    "sin partida para el recurso vinculado {tipo} {cod}: elige una partida o "
    "confirma para imputarlo SIN partida")
#: R23 (D11): se formatea con tipo, cod, hora, total, existente y nueva.
MOTIVO_SOBRECARGA_VINCULADO = (
    "sobrecarga del recurso vinculado {tipo} {cod}: sumaría {total:.2%} de "
    "{hora} en el parte (ya tiene {existente:.2%}, se añade {nueva:.2%}); "
    "confirma para escribirlo igualmente")


def por_que_sin_ci(motivo: str | None) -> str:
    """R16: el motivo de `partida_ci_del_tipo` en palabras."""
    return _POR_QUE_SIN_CI.get(motivo or "", motivo or "")


def clave_sin_partida_vinculado(registro_id: int, recurso_ide: int) -> str:
    """R16, R26: la clave con la que se confirma un vinculado sin partida.
    Por línea Y recurso: la del titular (`sin_partida:{registro_id}`) no lo
    confirma ni al revés."""
    return (f"{PREFIJO_CLAVE_SIN_PARTIDA}{int(registro_id)}:"
            f"{int(recurso_ide)}")
