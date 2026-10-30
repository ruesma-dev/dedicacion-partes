# application/services/reglas_obra_cero.py
"""F-054, parte B: al registrar, la obra sin nada en la plataforma es un
0 % (R31-R34, R38; design §6.1; ARCHITECTURE.md#regla-obra-cero).

Puro, sin lecturas. Una línea mensual de Sigrid (`LineaMensualSigrid`) de
un recurso del lote es **sobrante** si ninguna acción de ESE recurso la
cubre, en cualquier estado (también omitida: la obra se la da la
plataforma):

- normal: alguna acción no de postventa ni VAR va a esa obra;
- en la obra de postventa: alguna de postventa resolvió esa partida;
- en la VAR: alguna viene de una entrada VAR con ese `var_paride`;
- en pruebas (R32) solo cuentan las de la obra de pruebas: cubierta si una
  acción la reconoce (ya registrada, choque, al 0) o tiene su partida.

Los vinculados (R38, D16), igual con sus `AccionVinculado`. Solo los
recursos de las LÍNEAS del lote (D14). La obra especial se reconoce por su
código (`obra_cod` de la lectura, que va por empresa), no por su `ide`: el
preflight no siempre la resuelve (sin acciones de postventa no la lee).
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from domain.models.registro_models import (
    LineaEntrada,
    LineaMensualSigrid,
    Preflight,
    Sobrante,
)
from infrastructure.sigrid.sigrid_write_client import PREFIJO_SYNCKEY

#: R34: por qué una sobrante no se puede confirmar.
MOTIVO_CERRADO = "el parte {parte} no está En registro"
MOTIVO_OTRO_SISTEMA = "la línea es de otro sistema (synckey {synckey})"


@dataclass(frozen=True)
class Cobertura:
    """Lo que de una acción decide si cubre una línea: la obra de su
    preflight, su destino, su partida resuelta (0 si no) y el `var_paride`
    de su línea de entrada (None si no es VAR)."""

    obra_ide: int | None
    destino: str
    paride: int
    var_paride: int | None


def coberturas_de(pf: Preflight, lineas: Iterable[LineaEntrada]
                  ) -> dict[int, list[Cobertura]]:
    """Por recurso, las coberturas de todas las acciones de un preflight (de
    trabajador y de vinculado), en orden."""
    por_id = {l.registro_id: l for l in lineas}
    obra = pf.obra_destino.ide if pf.obra_destino else None
    out: dict[int, list[Cobertura]] = {}
    for a in pf.acciones:
        linea = por_id.get(a.registro_id)
        recurso = a.recurso_ide or (linea.recurso_ide if linea else None)
        if recurso is None:
            continue
        out.setdefault(int(recurso), []).append(Cobertura(
            obra, a.destino, int(a.paride or 0),
            linea.var_paride if linea else None))
    for v in pf.vinculados:
        titular = por_id.get(v.registro_id)
        out.setdefault(int(v.recurso_ide), []).append(Cobertura(
            obra, v.destino, int(v.paride or 0),
            titular.var_paride if titular else None))
    return out


def reconocidas_de(pf: Preflight) -> set[int]:
    """R32: los `hmores.ide` que el preflight reconoce: ya registrados, la
    línea al 0 que se edita y las de los choques."""
    ides: set[int] = set()
    for a in [*pf.acciones, *pf.vinculados]:
        if a.hmores_ide:
            ides.add(int(a.hmores_ide))
        if a.linea_cero and a.linea_cero.get("ide"):
            ides.add(int(a.linea_cero["ide"]))
    for c in pf.conflictos:
        ides |= {int(l.ide) for l in c.lineas}
        if c.edita_ide:
            ides.add(int(c.edita_ide))
        ides |= {int(i) for i in c.a_cero_ides}
    return ides


def cubierta(linea: LineaMensualSigrid, coberturas: Iterable[Cobertura], *,
             cod_pv: str, cod_var: str, modo_pruebas: bool,
             reconocidas: set[int]) -> bool:
    """R31-R32: ¿alguna acción del recurso cubre la línea? En pruebas,
    `sobrantes` ya deja solo las de la obra de pruebas."""
    cob = list(coberturas)
    paride = int(linea.paride or 0)
    if modo_pruebas:
        return linea.hmores_ide in reconocidas or any(
            c.paride == paride for c in cob)
    if linea.obra_cod == cod_pv:
        return any(c.destino == "postventa" and c.paride == paride
                   for c in cob)
    if linea.obra_cod == cod_var:
        return any(c.var_paride == paride for c in cob)
    return any(c.destino != "postventa" and c.var_paride is None
               and c.obra_ide == linea.obra_ide for c in cob)


def confirmable(linea: LineaMensualSigrid) -> tuple[bool, str | None]:
    """R34 (D15): solo En registro y nuestra o sin `synckey` (las
    `porcentajes:vin:` también son nuestras)."""
    if not linea.en_registro:
        return False, MOTIVO_CERRADO.format(parte=linea.parte_cod)
    if linea.synckey and not linea.synckey.startswith(PREFIJO_SYNCKEY):
        return False, MOTIVO_OTRO_SISTEMA.format(synckey=linea.synckey)
    return True, None


def sobrantes(mensuales: Iterable[LineaMensualSigrid],
              coberturas: dict[int, list[Cobertura]], *,
              vinculados: dict[int, dict], reconocidas: set[int],
              excluidos: set[int], cod_pv: str, cod_var: str,
              cod_pruebas: str, modo_pruebas: bool) -> list[Sobrante]:
    """R31-R34, R38: las sobrantes, por `hmores_ide`. Solo de los recursos
    de `coberturas` (los de las líneas del lote y sus vinculados, D14) que
    no están en `excluidos` (los de una petición que falló: sin su
    preflight no se sabe qué los cubre)."""
    out: list[Sobrante] = []
    for l in sorted(mensuales, key=lambda x: x.hmores_ide):
        if l.recurso_ide not in coberturas or l.recurso_ide in excluidos:
            continue
        if modo_pruebas and l.obra_cod != cod_pruebas:
            continue
        if cubierta(l, coberturas[l.recurso_ide], cod_pv=cod_pv,
                    cod_var=cod_var, modo_pruebas=modo_pruebas,
                    reconocidas=reconocidas):
            continue
        ok, motivo = confirmable(l)
        out.append(Sobrante(
            clave=f"cero:{l.hmores_ide}", hmores_ide=l.hmores_ide,
            recurso_ide=l.recurso_ide,
            vinculado=vinculados.get(l.recurso_ide), obra_ide=l.obra_ide,
            obra_cod=l.obra_cod, parte_cod=l.parte_cod,
            parte_est=l.parte_est, hora=l.hora, paride=int(l.paride or 0),
            partida_cod=l.partida_cod, can=l.can, synckey=l.synckey,
            confirmable=ok, motivo=motivo))
    return out
