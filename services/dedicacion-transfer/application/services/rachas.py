# application/services/rachas.py
"""Rachas de incidencia como Administración (F-062).

Aquí se IMPLEMENTAN; la fuente normativa es
`docs/ARCHITECTURE.md#regla-incidencia`. Funciones puras, como
`reglas_incidencias.py`: sin I/O, sin `settings` y sin cliente; las fechas
son `int` AAAAMMDD.

  - `pegado` (D2) y `llega_a_fin` (D7): entre dos días solo hay sábados y
    domingos (o nada); tras el último día del tramo solo quedan sábados y
    domingos (o nada). Los festivos no cuentan (F-059).
  - `emparejar` (D5): cada `CIZ` cierra el inicio abierto más reciente de su
    recurso, por (`fec`, inicio antes que `CIZ`, `ide`); un inicio sin `CIZ`
    es una racha abierta y un `CIZ` sin inicio abierto no forma racha.
"""
from __future__ import annotations

import calendar
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from datetime import date, timedelta

from domain.models.registro_models import (
    AccionIncidencia,
    IncidenciaEntrada,
    LineaIncidenciaSigrid,
    ParteSigrid,
)

from application.services.reglas_incidencias import (
    CODIGO_FIN,
    MOTIVO_INC_CAMBIADA,
    MOTIVO_INC_CERRADO,
    MOTIVO_INC_YA,
    PREFIJO_CIERRE,
    PREFIJO_SYNCKEY_INCIDENCIA,
    synckey_incidencia,
)

#: Sábado y domingo en `date.weekday()`.
_FIN_DE_SEMANA = (5, 6)


def _dia(f: int) -> date:
    return date(f // 10000, f // 100 % 100, f % 100)


def ultimo_dia(ano: int, mes: int) -> int:
    """El último día del mes, AAAAMMDD."""
    return ano * 10000 + mes * 100 + calendar.monthrange(ano, mes)[1]


def _solo_fin_de_semana(desde: date, hasta: date) -> bool:
    """¿Todos los días de [`desde`, `hasta`] son sábado o domingo? Vacío:
    sí."""
    d = desde
    while d <= hasta:
        if d.weekday() not in _FIN_DE_SEMANA:
            return False
        d += timedelta(days=1)
    return True


def pegado(c: int, d: int) -> bool:
    """D2: `d` está pegado a `c` si `c < d` y entre ambos solo hay sábados
    y domingos, o nada (también de un mes al siguiente)."""
    return c < d and _solo_fin_de_semana(_dia(c) + timedelta(days=1),
                                         _dia(d) - timedelta(days=1))


def llega_a_fin(h: int) -> bool:
    """D7: tras el día `h` solo quedan sábados y domingos de su mes, o
    nada."""
    return _solo_fin_de_semana(_dia(h) + timedelta(days=1),
                               _dia(ultimo_dia(h // 10000, h // 100 % 100)))


def codigo(linea: LineaIncidenciaSigrid) -> str:
    return (linea.hora_codigo or "").strip()


def es_inicio(linea: LineaIncidenciaSigrid) -> bool:
    cod = codigo(linea)
    return cod.startswith("CI") and cod != CODIGO_FIN


def es_fin(linea: LineaIncidenciaSigrid) -> bool:
    return codigo(linea) == CODIGO_FIN


@dataclass(frozen=True)
class Racha:
    """Un inicio `CI*` y su `CIZ` (None: abierta)."""
    codigo: str
    inicio: LineaIncidenciaSigrid
    cierre: LineaIncidenciaSigrid | None


def emparejar(lineas: Iterable[LineaIncidenciaSigrid]) -> list[Racha]:
    """D5: las rachas de las líneas, por recurso, ordenadas por inicio
    (`fec`, `ide`). Las líneas que no son `CI*` no cuentan."""
    por_recurso: dict[int, list[LineaIncidenciaSigrid]] = {}
    for ls in lineas:
        if es_inicio(ls) or es_fin(ls):
            por_recurso.setdefault(int(ls.reside), []).append(ls)
    rachas: list[Racha] = []
    for del_recurso in por_recurso.values():
        pila: list[LineaIncidenciaSigrid] = []
        cerradas: dict[int, LineaIncidenciaSigrid] = {}
        for ls in sorted(del_recurso, key=lambda x: (x.fecha_int,
                                                 0 if es_inicio(x) else 1,
                                                 x.ide)):
            if es_inicio(ls):
                pila.append(ls)
            elif pila:
                cerradas[pila.pop().ide] = ls
        rachas += [Racha(codigo(ls), ls, cerradas.get(ls.ide))
                   for ls in del_recurso if es_inicio(ls)]
    return sorted(rachas, key=lambda r: (r.inicio.fecha_int, r.inicio.ide))


@dataclass
class Cadena:
    """Incidencias del recurso y código en el mes, cada una pegada a la
    anterior (también de obras distintas, D11); la DUEÑA es la primera.
    `desde` y `hasta`, AAAAMMDD."""
    recurso: int
    codigo: str
    duena: IncidenciaEntrada
    miembros: list[IncidenciaEntrada]
    desde: int
    hasta: int


def fechas_de(inc: IncidenciaEntrada) -> tuple[int, int] | None:
    """(`desde`, `hasta`) AAAAMMDD de una incidencia con días posibles en
    su mes (como `decidir_incidencia`); si no, None."""
    ultimo = calendar.monthrange(int(inc.ano), int(inc.mes))[1]
    if not (type(inc.desde) is int and type(inc.hasta) is int
            and 1 <= inc.desde <= inc.hasta <= ultimo):
        return None
    base = int(inc.ano) * 10000 + int(inc.mes) * 100
    return base + inc.desde, base + inc.hasta


def _con_traza(inc: IncidenciaEntrada) -> bool:
    return bool(inc.hmores_ide_ini or inc.hmores_ide_fin)


def cadenas(incidencias_mes: Iterable[IncidenciaEntrada]) -> list[Cadena]:
    """D11, R11: por (recurso, código, `desde`), cada incidencia se une a la
    cadena anterior si está pegada a su último día (D2) y no tiene traza
    (una con línea propia sigue abriendo su racha). Las que no tienen
    recurso o días posibles no forman cadena."""
    validas = [(inc, f) for inc in incidencias_mes if inc.recurso_ide
               for f in [fechas_de(inc)] if f is not None]
    validas.sort(key=lambda x: (int(x[0].recurso_ide),
                                (x[0].codigo or "").strip(), x[1][0],
                                int(x[0].id)))
    out: list[Cadena] = []
    for inc, (desde, hasta) in validas:
        cod = (inc.codigo or "").strip()
        ultima = out[-1] if out else None
        if (ultima is not None and ultima.recurso == int(inc.recurso_ide)
                and ultima.codigo == cod and pegado(ultima.hasta, desde)
                and not _con_traza(inc)):
            ultima.miembros.append(inc)
            ultima.hasta = hasta
            continue
        out.append(Cadena(int(inc.recurso_ide), cod, inc, [inc], desde,
                          hasta))
    return out


def propias_de(inc: IncidenciaEntrada,
               lineas: Iterable[LineaIncidenciaSigrid]
               ) -> dict[str, LineaIncidenciaSigrid]:
    """R15 (F-030 R39): por rol, la línea del recurso con la `synckey` de
    la incidencia o la del `ide` de su traza; por `ide`, con nuestra
    `synckey` o, el `fin` con `dia_fin_antes`, el `CIZ` ajeno que movimos.
    El `ide` de la traza manda sobre la `synckey`."""
    lineas = [ls for ls in lineas if ls.reside == inc.recurso_ide]
    por_ide = {ls.ide: ls for ls in lineas}
    out: dict[str, LineaIncidenciaSigrid] = {}
    for rol, ide in (("ini", inc.hmores_ide_ini), ("fin", inc.hmores_ide_fin)):
        sk = synckey_incidencia(inc.id, rol)
        ls = por_ide.get(int(ide)) if ide else None
        ajena = (rol == "fin" and inc.dia_fin_antes is not None
                 and ls is not None and es_fin(ls))
        if ls is None or not (ajena or (ls.synckey or "").strip() == sk):
            ls = next((x for x in lineas if (x.synckey or "").strip() == sk),
                      None)
        if ls is not None:
            out[rol] = ls
    return out


def propias(cadena: Cadena, lineas: Iterable[LineaIncidenciaSigrid]
            ) -> dict[str, LineaIncidenciaSigrid]:
    """Las líneas propias de la DUEÑA de la cadena (las que escribe)."""
    return propias_de(cadena.duena, lineas)


#: R10 (D8): la racha pegada que no es previa, con su `CIZ`.
AVISO_R10_MES_ANTERIOR = (
    "la racha {cod} del {ini} se cerró el {dia} en el parte {parte} (línea "
    "{ide}), del mes anterior: se abre otra")
AVISO_R10_NO_MOVIBLE = (
    "la racha {cod} del {ini} se cierra el {dia} en el parte {parte} (línea "
    "{ide}), que no se puede mover: se abre otra")


def ddmm(f: int) -> str:
    """AAAAMMDD → «dd/mm»."""
    return f"{f % 100:02d}/{f // 100 % 100:02d}"


def _mes(f: int) -> int:
    return f // 100


def mes_anterior(mes: int) -> int:
    """AAAAMM del mes anterior a AAAAMM."""
    return mes - 1 if mes % 100 > 1 else (mes // 100 - 1) * 100 + 12


def abierta_en(r: Racha, mes: int) -> bool:
    """¿La racha sigue abierta al acabar el mes AAAAMM? Sin `CIZ`, o con su
    `CIZ` en un mes posterior (R21)."""
    return r.cierre is None or _mes(r.cierre.fecha_int) > mes


def destino_del_cierre(cadena: Cadena) -> int:
    """Dónde acaba el `CIZ` de la cadena si se mueve: el último día del mes
    si llega a fin de mes (R11), si no su último día (R4)."""
    if llega_a_fin(cadena.hasta):
        return ultimo_dia(cadena.hasta // 10000, cadena.hasta // 100 % 100)
    return cadena.hasta


def movible(linea: LineaIncidenciaSigrid, *, est: int,
            obride_pruebas: int | None = None) -> bool:
    """R10, R14: un `CIZ` ajeno se puede mover si su parte está En registro
    y, en pruebas, es de la obra de pruebas (los enlaces se miran al
    releer, en `ejecutar`)."""
    return linea.parte_est == est and (obride_pruebas is None
                                       or linea.obride == obride_pruebas)


def previa(rachas: Iterable[Racha], cadena: Cadena, *, est: int,
           obride_pruebas: int | None = None
           ) -> tuple[Racha | None, list[str]]:
    """R1 y R10: la racha del mismo código con inicio en `d` o antes que la
    cadena continúa, de las leídas (sin las propias de la cadena y con los
    `CIZ` ajenos movidos en su día original): (a) abierta con inicio en M;
    (b) abierta con inicio anterior a M y `d` pegado al último día de M−1
    (D4); (c) con su `CIZ` en M, en `d` o después o pegado a `d`. De
    varias, la de inicio más reciente.

    R10 (D8): no es previa la pegada cuyo `CIZ` es de M−1, ni la de (c)
    cuyo `CIZ` habría que mover y no se puede; cada una, con su aviso."""
    d, mes = cadena.desde, _mes(cadena.desde)
    fin_m1 = ultimo_dia(mes_anterior(mes) // 100, mes_anterior(mes) % 100)
    validas: list[Racha] = []
    avisos: list[str] = []
    for r in rachas:
        if (r.codigo != cadena.codigo or r.inicio.fecha_int > d
                or r.inicio.reside != cadena.recurso):
            continue
        ini = _mes(r.inicio.fecha_int)
        if abierta_en(r, mes):
            if ini == mes or pegado(fin_m1, d):
                validas.append(r)
            continue
        f = r.cierre.fecha_int
        if not (f >= d or pegado(f, d)):
            continue
        texto = {"cod": r.codigo, "ini": ddmm(r.inicio.fecha_int),
                 "dia": ddmm(f), "parte": r.cierre.parte_cod,
                 "ide": r.cierre.ide}
        if _mes(f) < mes:
            avisos.append(AVISO_R10_MES_ANTERIOR.format(**texto))
        elif f < destino_del_cierre(cadena) and not movible(
                r.cierre, est=est, obride_pruebas=obride_pruebas):
            avisos.append(AVISO_R10_NO_MOVIBLE.format(**texto))
        else:
            validas.append(r)
    if not validas:
        return None, avisos
    mejor = max(validas, key=lambda r: (r.inicio.fecha_int, r.inicio.ide))
    return mejor, avisos


#: Motivos y avisos de `decidir_cadena` (R4, R8, R9, R11, R16, R21). Caben
#: en los 300 caracteres de `incidencia.sigrid_motivo`.
MOTIVO_CONTINUA_CADENA = "continúa (cadena de la incidencia {id})"
MOTIVO_CONTINUA_RACHA = (
    "continúa la racha {cod} del {dia} (parte {parte}, línea {ide})")
MOTIVO_ABIERTA = "llega a fin de mes: queda abierta (sin CIZ)"
MOTIVO_CUBIERTA = "la cierra el CIZ del {dia} (parte {parte}, línea {ide})"
MOTIVO_MUEVE = (
    "se mueve el CIZ (línea {ide}, parte {parte}) del {antes} al {dia}")
MOTIVO_EN_EL_TRAMO = (
    "en el tramo ya está la línea {ide} ({cod}, {dia}) del parte {parte}, "
    "{origen}: no se escribe ni se mueve nada")
MOTIVO_DEVUELVE = (
    "se devuelve el CIZ (línea {ide}) a su día original, el {dia}")
MOTIVO_NO_DEVUELVE = (
    "el CIZ (línea {ide}) no se puede devolver al {dia}: el parte {parte} no "
    "está En registro")
AVISO_R11_INICIO = (
    "no se une a la racha {cod} del {dia} (parte {parte}): su inicio (línea "
    "{ide}) ya está escrito")
AVISO_R11_CIZ = (
    "no se deja abierta: el CIZ (línea {ide}) ya está en el mes; va al último "
    "día")
AVISO_R21 = (
    "la racha sigue en {mes:02d}/{ano}: su CIZ (línea {ide}) es del {dia} en "
    "el parte {parte}; no se escribe el CIZ")
#: `can` de una línea nuestra de incidencia: 0, con la tolerancia de F-051.
_TOLERANCIA_CAN = 0.000001


def origen_de(linea: LineaIncidenciaSigrid) -> str:
    """De quién es una línea, por su `synckey` (R9)."""
    sk = (linea.synckey or "").strip()
    if not sk:
        return "de Administración"
    if sk.startswith(PREFIJO_CIERRE):
        return "de un cierre de racha de porcentajes"
    if sk.startswith(PREFIJO_SYNCKEY_INCIDENCIA):
        resto = sk[len(PREFIJO_SYNCKEY_INCIDENCIA):]
        return f"de la incidencia {resto.split(':')[0]}"
    if sk.startswith("partes:"):
        return "de partes"
    return "de otro sistema"


@dataclass
class RachaResumen:
    """R22: lo que el modal enseña de cada incidencia de la petición."""
    id: int
    papel: str                          # abre | continua
    inicio_fec: int | None
    inicio_parte: str | None
    cierre: str                         # cierra | abierta | cubierta | cadena
    cierre_fec: int | None
    cierre_parte: str | None
    duena_id: int
    avisos: list[str] = field(default_factory=list)


@dataclass
class PlanCadena:
    """Las acciones de cada incidencia de la cadena (`ini`, `fin` y, si la
    dueña devuelve un `CIZ` ajeno, `devolver`), su resumen y los `ide` de
    las líneas de la previa que continúa (R30: no «solo en Sigrid»)."""
    acciones: list[AccionIncidencia]
    resumenes: list[RachaResumen]
    previas: set[int] = field(default_factory=set)


def _propia_cambiada(a: AccionIncidencia, linea: LineaIncidenciaSigrid,
                     dia_traza: int | None) -> bool:
    """F-030 R42 (D14): una línea nuestra tocada a mano en Sigrid: fuera
    del día registrado (si no consta, fuera del mes), con otro código o
    con `can` distinto de 0 (nulo cuenta como 0)."""
    if dia_traza is not None:
        fuera = linea.fecha_int != a.ano * 10000 + a.mes * 100 + int(dia_traza)
    else:
        fuera = linea.fecha_int // 100 != a.ano * 100 + a.mes
    return (fuera or codigo(linea) != a.hora_codigo
            or abs(float(linea.can or 0.0)) >= _TOLERANCIA_CAN)


def _decidir_propia(a: AccionIncidencia, linea: LineaIncidenciaSigrid,
                    objetivo: int, dia_traza: int | None, est: int,
                    dias: tuple[int | None, int | None]) -> None:
    """R14 (F-030 R41-R43): una línea NUESTRA va a `objetivo` editando su
    `fec` en su sitio; con la `fec` pedida, ya registrada; tocada a mano o
    en un parte que no está En registro, no se toca. `dias`: los de las
    dos líneas propias de la incidencia, para el motivo del parte cerrado."""
    a.hmores_ide, a.hmoide, a.parte_cod = (linea.ide, linea.hmoide,
                                           linea.parte_cod)
    a.fecha_int = objetivo
    if linea.fecha_int == objetivo:
        a.accion, a.motivo = "ya_registrado", MOTIVO_INC_YA.format(
            ide=linea.ide)
    elif _propia_cambiada(a, linea, dia_traza):
        a.accion = "omitir"
        a.motivo = MOTIVO_INC_CAMBIADA.format(ide=linea.ide)
    elif linea.parte_est != est:
        a.accion, a.motivo = "omitir", MOTIVO_INC_CERRADO.format(
            parte=linea.parte_cod, desde=dias[0] or "?", hasta=dias[1] or "?")
    else:
        a.accion, a.fec_antes = "editar", linea.fecha_int
        a.synckey_leida, a.can_leido = linea.synckey, 0.0


def _mover_ajena(a: AccionIncidencia, linea: LineaIncidenciaSigrid,
                 objetivo: int) -> None:
    """R4, R14 (D12): el `CIZ` ajeno de la previa va a `objetivo` (solo
    hacia delante; `previa` ya miró que se puede mover), con su `can` y su
    `synckey` leídos; ya en `objetivo`, ya registrado."""
    a.hmores_ide, a.hmoide, a.parte_cod = (linea.ide, linea.hmoide,
                                           linea.parte_cod)
    a.fecha_int, a.ajena = objetivo, True
    if linea.fecha_int == objetivo:
        a.accion, a.motivo = "ya_registrado", MOTIVO_INC_YA.format(
            ide=linea.ide)
        return
    a.accion, a.fec_antes = "editar", linea.fecha_int
    a.synckey_leida, a.can_leido = linea.synckey, float(linea.can or 0.0)
    a.motivo = MOTIVO_MUEVE.format(ide=linea.ide, parte=linea.parte_cod,
                                   antes=ddmm(linea.fecha_int),
                                   dia=ddmm(objetivo))


def parte_vale(linea: LineaIncidenciaSigrid, *, est: int, empresa: int,
               obride_pruebas: int | None = None) -> bool:
    """R5, R12: el parte de una línea recibe un `CIZ` si está En registro,
    es de la empresa y, en pruebas, de la obra de pruebas."""
    return (linea.parte_est == est and linea.parte_emp == empresa
            and (obride_pruebas is None or linea.obride == obride_pruebas))


def _al_parte_de(a: AccionIncidencia, inicio: LineaIncidenciaSigrid) -> None:
    """R5: el `CIZ` que se escribe va al parte del inicio, con su obra,
    centro, partida y cuenta (E-6, E-13)."""
    a.hmoide_destino, a.parte_cod = inicio.hmoide, inicio.parte_cod
    a.obride, a.cenide = inicio.obride, inicio.cenide
    a.paride, a.caa_ide = int(inicio.paride or 0), int(inicio.caaide or 0)


def _continua(m: IncidenciaEntrada, duena_id: int) -> list[AccionIncidencia]:
    """R8: una no dueña de la cadena no escribe."""
    f = fechas_de(m)
    base = {"id": int(m.id), "accion": "continua",
            "recurso_ide": m.recurso_ide, "ano": int(m.ano),
            "mes": int(m.mes), "paride": int(m.paride or 0),
            "motivo": MOTIVO_CONTINUA_CADENA.format(id=duena_id)}
    return [AccionIncidencia(rol="ini", fecha_int=f[0], hora_codigo=m.codigo,
                             **base),
            AccionIncidencia(rol="fin", fecha_int=f[1], hora_codigo=CODIGO_FIN,
                             **base)]


def _omitir_todo(cadena: Cadena, base: list[AccionIncidencia],
                 motivo: str) -> PlanCadena:
    """La cadena no escribe ni mueve nada (R9, R26): cada línea de cada
    incidencia, `omitir` con el mismo motivo."""
    acciones = []
    for m in cadena.miembros:
        if m is cadena.duena:
            acciones += [replace(a, accion="omitir", motivo=motivo)
                         for a in base]
        else:
            acciones += [replace(a, accion="omitir", motivo=motivo)
                         for a in _continua(m, cadena.duena.id)]
    return PlanCadena(acciones, [])


def _devolver(duena: IncidenciaEntrada, linea: LineaIncidenciaSigrid,
              original: int, est: int) -> AccionIncidencia:
    """R16 (D10): el `CIZ` ajeno que movimos vuelve a su día original con el
    `UPDATE` de R14; en un parte que no está En registro, no."""
    a = AccionIncidencia(
        id=int(duena.id), rol="devolver", accion="editar", fecha_int=original,
        recurso_ide=duena.recurso_ide, ano=int(duena.ano), mes=int(duena.mes),
        hora_codigo=CODIGO_FIN, parte_cod=linea.parte_cod,
        hmores_ide=linea.ide, hmoide=linea.hmoide, fec_antes=linea.fecha_int,
        synckey_leida=linea.synckey, can_leido=float(linea.can or 0.0),
        ajena=True, motivo=MOTIVO_DEVUELVE.format(ide=linea.ide,
                                                  dia=ddmm(original)))
    if linea.parte_est != est:
        a.accion, a.fec_antes = "omitir", None
        a.motivo = MOTIVO_NO_DEVUELVE.format(ide=linea.ide, dia=ddmm(original),
                                             parte=linea.parte_cod)
    return a


def movidas_de(inc: IncidenciaEntrada,
               lineas: Iterable[LineaIncidenciaSigrid]
               ) -> tuple[LineaIncidenciaSigrid, int] | None:
    """R15: el `CIZ` ajeno que la incidencia movió (su `fin` por `ide` con
    `dia_fin_antes`) y su día original, AAAAMMDD; None si no movió ninguno
    o ya no está."""
    if inc.dia_fin_antes is None:
        return None
    ls = propias_de(inc, lineas).get("fin")
    if ls is None or (ls.synckey or "").strip() == synckey_incidencia(
            inc.id, "fin"):
        return None
    return ls, int(inc.ano) * 10000 + int(inc.mes) * 100 + int(
        inc.dia_fin_antes)


def decidir_cadena(cadena: Cadena, lineas: Iterable[LineaIncidenciaSigrid],
                   base: list[AccionIncidencia], *, est: int, empresa: int,
                   obride_pruebas: int | None = None) -> PlanCadena:
    """R1-R11, R14, R16, R18, R21 (design §2, pasos 1-5). `base`: las dos
    acciones de la dueña de `decidir_incidencia` (R26: si omite, se omite
    la cadena). `lineas`: las `CI*`/`CIZ` leídas (R19)."""
    duena = cadena.duena
    if any(a.accion != "escribir" for a in base):
        return _omitir_todo(cadena, base, base[0].motivo)
    ini, fin = (replace(a) for a in base)
    ini.fecha_int, fin.fecha_int = cadena.desde, cadena.hasta
    mes = _mes(cadena.desde)
    fin_m = ultimo_dia(mes // 100, mes % 100)
    lineas = [ls for ls in lineas if ls.reside == cadena.recurso]
    # Paso 1: sin las propias de la cadena y con el CIZ ajeno que movió la
    # dueña en su día original.
    suyas = propias(cadena, lineas)
    fuera = {ls.ide for m in cadena.miembros
             for ls in propias_de(m, lineas).values()}
    movida = movidas_de(duena, lineas)
    leidas = [ls for ls in lineas if ls.ide not in fuera]
    if movida is not None:
        leidas.append(replace(movida[0], fecha_int=movida[1]))
    por_ide = {ls.ide: ls for ls in lineas}
    rachas = emparejar(leidas)
    avisos: list[str] = []
    propio_ini = suyas.get("ini")
    propio_fin = (suyas.get("fin") if movida is None
                  or suyas.get("fin") is not movida[0] else None)
    # Paso 3 (antes que la guarda, que la necesita): la previa.
    r_previa, avisos_previa = previa(rachas, cadena, est=est,
                                     obride_pruebas=obride_pruebas)
    if propio_ini is not None:
        # R11: una con inicio propio sigue abriendo su racha.
        if r_previa is not None:
            avisos.append(AVISO_R11_INICIO.format(
                cod=r_previa.codigo, dia=ddmm(r_previa.inicio.fecha_int),
                parte=r_previa.inicio.parte_cod, ide=propio_ini.ide))
        r_previa = None
    else:
        avisos += avisos_previa
    # Paso 2: la guarda (R9, D13).
    de_la_previa = set() if r_previa is None else {
        r_previa.inicio.ide, *([r_previa.cierre.ide] if r_previa.cierre
                               else [])}
    en_tramo = sorted((ls for ls in leidas
                       if cadena.desde <= ls.fecha_int <= cadena.hasta
                       and (es_inicio(ls) or es_fin(ls))
                       and ls.ide not in de_la_previa),
                      key=lambda x: (x.fecha_int, x.ide))
    if en_tramo:
        x = en_tramo[0]
        return _omitir_todo(cadena, base, MOTIVO_EN_EL_TRAMO.format(
            ide=x.ide, cod=codigo(x), dia=ddmm(x.fecha_int),
            parte=x.parte_cod, origen=origen_de(x)))
    dias = tuple(ls.fecha_int % 100 if ls is not None else None
                 for ls in (propio_ini, suyas.get("fin")))
    # Paso 3: el inicio.
    inicio: LineaIncidenciaSigrid | None = None
    if propio_ini is not None:
        _decidir_propia(ini, propio_ini, cadena.desde, duena.dia_ini, est,
                        dias)
        inicio, papel = propio_ini, "abre"
        resumen_ini = (cadena.desde, propio_ini.parte_cod)
    elif r_previa is not None:
        inicio, papel = r_previa.inicio, "continua"
        ini.accion = "continua"
        ini.parte_cod = r_previa.inicio.parte_cod
        ini.motivo = MOTIVO_CONTINUA_RACHA.format(
            cod=r_previa.codigo, dia=ddmm(r_previa.inicio.fecha_int),
            parte=r_previa.inicio.parte_cod, ide=r_previa.inicio.ide)
        resumen_ini = (r_previa.inicio.fecha_int, r_previa.inicio.parte_cod)
    else:
        papel, resumen_ini = "abre", (cadena.desde, None)
    # Paso 4: el cierre.
    ciz_previa = (r_previa.cierre if r_previa is not None
                  and r_previa.cierre is not None
                  and _mes(r_previa.cierre.fecha_int) == mes else None)
    usada = None            # el CIZ ajeno que la cadena usa en su sitio
    cierre = "cierra"
    if llega_a_fin(cadena.hasta):
        if propio_fin is not None and _mes(propio_fin.fecha_int) == mes:
            _decidir_propia(fin, propio_fin, fin_m, duena.dia_fin, est, dias)
            avisos.append(AVISO_R11_CIZ.format(ide=propio_fin.ide))
        elif ciz_previa is not None:
            usada = por_ide.get(ciz_previa.ide, ciz_previa)
            _mover_ajena(fin, usada, fin_m)
            avisos.append(AVISO_R11_CIZ.format(ide=ciz_previa.ide))
        else:
            fin.accion, fin.motivo, cierre = "abierta", MOTIVO_ABIERTA, \
                "abierta"
    elif propio_fin is not None:
        _decidir_propia(fin, propio_fin, cadena.hasta, duena.dia_fin, est,
                        dias)
    elif ciz_previa is not None and ciz_previa.fecha_int >= cadena.hasta:
        # R4: una ajena nunca se acorta: la cubre.
        fin.accion, fin.fecha_int = "ya_registrado", ciz_previa.fecha_int
        fin.parte_cod, cierre = ciz_previa.parte_cod, "cubierta"
        fin.motivo = MOTIVO_CUBIERTA.format(
            dia=ddmm(ciz_previa.fecha_int), parte=ciz_previa.parte_cod,
            ide=ciz_previa.ide)
    elif ciz_previa is not None:
        usada = por_ide.get(ciz_previa.ide, ciz_previa)
        _mover_ajena(fin, usada, cadena.hasta)
    else:
        siguiente = _ciz_posterior(r_previa, propio_ini, cadena, leidas, mes)
        if siguiente is not None:
            # R21: la racha sigue en M+1; no se escribe el CIZ.
            aviso = AVISO_R21.format(
                mes=_mes(siguiente.fecha_int) % 100,
                ano=siguiente.fecha_int // 10000, ide=siguiente.ide,
                dia=ddmm(siguiente.fecha_int), parte=siguiente.parte_cod)
            fin.accion, fin.motivo, cierre = "abierta", aviso, "abierta"
            avisos.append(aviso)
        elif inicio is not None and _mes(inicio.fecha_int) <= mes and (
                inicio is propio_ini or _mes(inicio.fecha_int) == mes) \
                and parte_vale(inicio, est=est, empresa=empresa,
                               obride_pruebas=obride_pruebas):
            _al_parte_de(fin, inicio)
    acciones = [ini, fin]
    if movida is not None and movida[0] is not usada \
            and movida[0].fecha_int != movida[1]:
        acciones.append(_devolver(duena, movida[0], movida[1], est))
    cierre_fec = (None if cierre == "abierta" else fin.fecha_int)
    resumen = RachaResumen(
        id=int(duena.id), papel=papel, inicio_fec=resumen_ini[0],
        inicio_parte=resumen_ini[1], cierre=cierre, cierre_fec=cierre_fec,
        cierre_parte=fin.parte_cod if cierre != "abierta" else None,
        duena_id=int(duena.id), avisos=avisos)
    resumenes = [resumen]
    for m in cadena.miembros[1:]:
        acciones += _continua(m, duena.id)
        resumenes.append(replace(resumen, id=int(m.id), papel="continua",
                                 cierre="cadena", avisos=[]))
    return PlanCadena(acciones, resumenes, de_la_previa)


def _ciz_posterior(r_previa: Racha | None,
                   propio_ini: LineaIncidenciaSigrid | None, cadena: Cadena,
                   leidas: list[LineaIncidenciaSigrid], mes: int
                   ) -> LineaIncidenciaSigrid | None:
    """R21: el `CIZ` de M+1 de la racha de la cadena (la previa abierta o
    la del inicio propio, puesto en `desde`), si lo tiene."""
    if r_previa is not None:
        racha = r_previa
    elif propio_ini is not None:
        nuevo = replace(propio_ini, fecha_int=cadena.desde)
        racha = next((r for r in emparejar([*leidas, nuevo])
                      if r.inicio is nuevo), None)
    else:
        return None
    if racha is None or racha.cierre is None \
            or _mes(racha.cierre.fecha_int) <= mes:
        return None
    return racha.cierre


# ================= Cierre del mes anterior (R12, R13, D14) ================ #

MOTIVO_CIERRE = ("la racha {cod} del {ini} (parte {parte}) no sigue en "
                 "{mes:02d}/{ano}: CIZ el {dia} en el parte {destino}")
MOTIVO_CIERRE_YA = ("la racha {cod} del {ini} (parte {parte}) ya está "
                    "cerrada el {dia} (línea {ide}, parte {destino})")
AVISO_CIERRE_PARTE = (
    "la racha {cod} del {ini} (parte {parte}) no sigue en {mes:02d}/{ano} y "
    "no se puede cerrar el {dia}: el parte {parte} no está En registro, no "
    "es de la empresa o no es de la obra de pruebas")
AVISO_CIERRE_SIN_PARTE = (
    "la racha {cod} del {ini} (parte {parte}) no sigue en {mes:02d}/{ano} y "
    "no se puede cerrar el {dia}: su obra no tiene en {mes1:02d}/{ano1} "
    "ningún parte En registro")


@dataclass
class CierreRacha:
    """R12-R13, R22: el `CIZ` del último día de M−1 de una racha abierta
    que ninguna incidencia de M continúa. `accion`: `escribir` (en el parte
    `hmoide`, con la obra, centro, partida y cuenta del inicio),
    `ya_registrado` (`hmores_ide`, la línea que ya la cierra) o `aviso` (no
    hay parte que valga). `incidencia_id`: la nuestra del inicio, o None si
    el inicio es ajeno."""
    recurso_ide: int
    codigo: str
    inicio_ide: int
    inicio_fec: int
    inicio_parte: str | None
    accion: str
    fecha_int: int
    synckey: str
    incidencia_id: int | None
    motivo: str
    parte_cod: str | None = None
    hmoide: int | None = None
    obride: int | None = None
    cenide: int | None = None
    paride: int | None = None
    caaide: int | None = None
    hmores_ide: int | None = None


def synckey_de_cierre(inicio: LineaIncidenciaSigrid
                      ) -> tuple[str, int | None]:
    """R12: la `synckey` del `CIZ` de cierre y su incidencia: la nuestra
    del inicio (`porcentajes:inc:{id}:fin`) o, si el inicio es ajeno,
    `porcentajes:inc:cierre:{ide del inicio}` y None."""
    sk = (inicio.synckey or "").strip()
    resto = sk[len(PREFIJO_SYNCKEY_INCIDENCIA):].split(":")
    if (sk.startswith(PREFIJO_SYNCKEY_INCIDENCIA) and len(resto) == 2
            and resto[0].isdigit() and resto[1] == "ini"):
        return synckey_incidencia(int(resto[0]), "fin"), int(resto[0])
    return f"{PREFIJO_CIERRE}{int(inicio.ide)}", None


def _sin_continuar(rachas: list[Racha], recurso: int,
                   incidencias_mes: list[IncidenciaEntrada], mes: int,
                   est: int, obride_pruebas: int | None
                   ) -> tuple[list[Racha], list[Racha]]:
    """Las rachas del recurso con inicio anterior a M: las abiertas que
    ninguna cadena de M continúa (R1 b) y las ya cerradas el último día de
    M−1 por un `CIZ` con la `synckey` de cierre (R18)."""
    mias = [r for r in rachas if r.inicio.reside == recurso
            and _mes(r.inicio.fecha_int) < mes]
    m1 = mes_anterior(mes)
    fin_m1 = ultimo_dia(m1 // 100, m1 % 100)
    seguidas = set()
    for c in cadenas(incidencias_mes):
        if c.recurso == recurso:
            r, _ = previa(mias, c, est=est, obride_pruebas=obride_pruebas)
            if r is not None:
                seguidas.add(r.inicio.ide)
    abiertas = [r for r in mias if r.cierre is None
                and r.inicio.ide not in seguidas]
    hechas = [r for r in mias if r.cierre is not None
              and r.cierre.fecha_int == fin_m1
              and (r.cierre.synckey or "").strip()
              == synckey_de_cierre(r.inicio)[0]]
    return abiertas, hechas


def obras_de_cierres(rachas: Iterable[Racha], recurso: int,
                     incidencias_mes: Iterable[IncidenciaEntrada], ano: int,
                     mes: int, *, est: int,
                     obride_pruebas: int | None = None) -> set[int]:
    """D14: las obras de los inicios anteriores a M−1 por cerrar; sus
    partes de M−1 se leen solo si las hay (R20, ronda D)."""
    m = int(ano) * 100 + int(mes)
    abiertas, _ = _sin_continuar(list(rachas), recurso,
                                 list(incidencias_mes), m, est,
                                 obride_pruebas)
    return {int(r.inicio.obride) for r in abiertas
            if _mes(r.inicio.fecha_int) < mes_anterior(m)
            and r.inicio.obride is not None}


def _parte_de_m1(inicio: LineaIncidenciaSigrid,
                 partes: list[ParteSigrid] | None, *, est: int, empresa: int,
                 obride_pruebas: int | None) -> ParteSigrid | None:
    """D14 = B: el parte de M−1 de la obra del inicio En registro, de la
    empresa y (pruebas) de la obra de pruebas, el de mayor `ide`. La
    empresa y la obra se miran en el parte del inicio (misma obra)."""
    if inicio.parte_emp != empresa or (obride_pruebas is not None
                                       and inicio.obride != obride_pruebas):
        return None
    validos = [p for p in partes or [] if p.est == est]
    return max(validos, key=lambda p: p.ide) if validos else None


def cierres_mes_anterior(rachas: Iterable[Racha], recurso: int,
                         incidencias_mes: Iterable[IncidenciaEntrada],
                         partes_m1: dict[tuple[int, int, int],
                                         list[ParteSigrid]],
                         ano: int, mes: int, *, est: int, empresa: int,
                         obride_pruebas: int | None = None
                         ) -> list[CierreRacha]:
    """R12-R13 (D14 = B): al registrar el mes M de un recurso designado,
    un `CIZ` el último día de M−1 por cada racha suya abierta con inicio
    anterior a M que ninguna incidencia de M continúa. Inicio en M−1: en
    el parte del inicio, si vale (R5); anterior: en el parte de M−1 de la
    obra del inicio que vale (`partes_m1`, por `(obride, ano, mes)`), sin
    crear ninguno. Sin parte que valga, `aviso`."""
    m = int(ano) * 100 + int(mes)
    m1 = mes_anterior(m)
    fin_m1 = ultimo_dia(m1 // 100, m1 % 100)
    abiertas, hechas = _sin_continuar(list(rachas), recurso,
                                      list(incidencias_mes), m, est,
                                      obride_pruebas)
    out: list[CierreRacha] = []
    for r in sorted([*abiertas, *hechas],
                    key=lambda r: (r.inicio.fecha_int, r.inicio.ide)):
        ini = r.inicio
        sk, inc_id = synckey_de_cierre(ini)
        texto = {"cod": r.codigo, "ini": ddmm(ini.fecha_int),
                 "parte": ini.parte_cod, "mes": m % 100, "ano": m // 100,
                 "dia": ddmm(fin_m1), "mes1": m1 % 100, "ano1": m1 // 100}
        c = CierreRacha(recurso_ide=int(recurso), codigo=r.codigo,
                        inicio_ide=ini.ide, inicio_fec=ini.fecha_int,
                        inicio_parte=ini.parte_cod, accion="aviso",
                        fecha_int=fin_m1, synckey=sk, incidencia_id=inc_id,
                        motivo="")
        out.append(c)
        if r.cierre is not None:
            c.accion, c.hmores_ide = "ya_registrado", r.cierre.ide
            c.parte_cod, c.hmoide = r.cierre.parte_cod, r.cierre.hmoide
            c.motivo = MOTIVO_CIERRE_YA.format(
                **texto, ide=r.cierre.ide, destino=r.cierre.parte_cod)
            continue
        if _mes(ini.fecha_int) == m1:
            vale = parte_vale(ini, est=est, empresa=empresa,
                              obride_pruebas=obride_pruebas)
            destino = (ini.hmoide, ini.parte_cod) if vale else None
            aviso = AVISO_CIERRE_PARTE
        else:
            p = _parte_de_m1(
                ini, partes_m1.get((int(ini.obride or 0), m1 // 100,
                                    m1 % 100)),
                est=est, empresa=empresa, obride_pruebas=obride_pruebas)
            destino = (p.ide, p.cod) if p is not None else None
            aviso = AVISO_CIERRE_SIN_PARTE
        if destino is None:
            c.motivo = aviso.format(**texto)
            continue
        c.accion, (c.hmoide, c.parte_cod) = "escribir", destino
        c.obride, c.cenide = ini.obride, ini.cenide
        c.paride, c.caaide = ini.paride, ini.caaide
        c.motivo = MOTIVO_CIERRE.format(**texto, destino=destino[1])
    return out


# ============ «No coincide con Sigrid» (R17, R30, D15, D16) ============== #

MOTIVO_NC_QUITADA = "quitada en la plataforma; sigue en Sigrid"
MOTIVO_NC_SOLO_SIGRID = "en Sigrid y no en la plataforma"


@dataclass(frozen=True)
class LineaVista:
    """Una línea de Sigrid tal como se enseña para editarla a mano."""
    ide: int
    codigo: str
    fecha_int: int
    parte_cod: str | None


@dataclass
class NoCoincide:
    """R17, R30, R22: lo que no coincide con Sigrid. `tipo` `quitada` (una
    por quitada, con sus propias que siguen en Sigrid; `en_sigrid`, sus
    `ide`: vacío, la api la borra y no hay aviso) o `solo_sigrid` (las de
    una racha de M que nada de la plataforma explica)."""
    tipo: str
    recurso_ide: int
    incidencia_id: int | None
    lineas: list[LineaVista]
    motivo: str
    en_sigrid: list[int] = field(default_factory=list)


def _vista(ls: LineaIncidenciaSigrid) -> LineaVista:
    return LineaVista(ls.ide, codigo(ls), ls.fecha_int, ls.parte_cod)


def no_coincide(lineas: Iterable[LineaIncidenciaSigrid], recurso: int,
                quitadas: Iterable[IncidenciaEntrada],
                incidencias_mes: Iterable[IncidenciaEntrada],
                previas: set[int], ano: int, mes: int, *,
                designado: bool = True) -> list[NoCoincide]:
    """R17 (D16): por cada quitada del recurso, sus propias que siguen en
    Sigrid, menos el `CIZ` ajeno que movió (se devuelve, R16). R30 (D15),
    solo si el recurso es el designado: por racha, sus líneas del mes M
    cuando ninguna de la racha es propia de una incidencia o quitada del
    mes ni de una previa que continúa una cadena (`previas`, por `ide`)."""
    lineas = [ls for ls in lineas if ls.reside == recurso]
    m = int(ano) * 100 + int(mes)
    out: list[NoCoincide] = []
    explicadas = set(previas)
    for inc in incidencias_mes:
        if inc.recurso_ide == recurso:
            explicadas |= {ls.ide for ls in propias_de(inc, lineas).values()}
    for q in sorted((q for q in quitadas if q.recurso_ide == recurso),
                    key=lambda q: int(q.id)):
        suyas = propias_de(q, lineas)
        explicadas |= {ls.ide for ls in suyas.values()}
        movida = movidas_de(q, lineas)
        siguen = sorted((ls for ls in suyas.values()
                         if movida is None or ls is not movida[0]),
                        key=lambda x: (x.fecha_int, x.ide))
        out.append(NoCoincide("quitada", int(recurso), int(q.id),
                              [_vista(ls) for ls in siguen],
                              MOTIVO_NC_QUITADA, [ls.ide for ls in siguen]))
    if not designado:
        return out
    grupos = [[x for x in (r.inicio, r.cierre) if x is not None]
              for r in emparejar(lineas)]
    en_racha = {ls.ide for g in grupos for ls in g}
    grupos += [[ls] for ls in lineas if ls.ide not in en_racha]
    solo: list[list[LineaIncidenciaSigrid]] = []
    for g in grupos:
        del_mes = [ls for ls in g if _mes(ls.fecha_int) == m]
        if del_mes and not any(ls.ide in explicadas for ls in g):
            solo.append(del_mes)
    for g in sorted(solo, key=lambda g: (g[0].fecha_int, g[0].ide)):
        out.append(NoCoincide("solo_sigrid", int(recurso), None,
                              [_vista(ls) for ls in g],
                              MOTIVO_NC_SOLO_SIGRID))
    return out
