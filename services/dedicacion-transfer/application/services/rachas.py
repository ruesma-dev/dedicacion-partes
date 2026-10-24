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
from dataclasses import dataclass
from datetime import date, timedelta

from domain.models.registro_models import (
    IncidenciaEntrada, LineaIncidenciaSigrid,
)

#: Código de `auxhor` que cierra la racha de cualquier incidencia.
CODIGO_FIN = "CIZ"
#: Prefijo de la `synckey` de las líneas de incidencia (F-030).
PREFIJO_SYNCKEY_INCIDENCIA = "porcentajes:inc:"
#: Sábado y domingo en `date.weekday()`.
_FIN_DE_SEMANA = (5, 6)


def _dia(f: int) -> date:
    return date(f // 10000, f // 100 % 100, f % 100)


def _int(d: date) -> int:
    return d.year * 10000 + d.month * 100 + d.day


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


def synckey_de_rol(incidencia_id: int, rol: str) -> str:
    """`porcentajes:inc:{id}:ini|fin` (la de `reglas_incidencias`)."""
    return f"{PREFIJO_SYNCKEY_INCIDENCIA}{int(incidencia_id)}:{rol}"


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
        sk = synckey_de_rol(inc.id, rol)
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
        if r.codigo != cadena.codigo or r.inicio.fecha_int > d                 or r.inicio.reside != cadena.recurso:
            continue
        ini = _mes(r.inicio.fecha_int)
        if abierta_en(r, mes):
            if ini == mes or pegado(fin_m1, d):
                validas.append(r)
            continue
        f = r.cierre.fecha_int
        if not (f >= d or pegado(f, d)):
            continue
        texto = dict(cod=r.codigo, ini=ddmm(r.inicio.fecha_int), dia=ddmm(f),
                     parte=r.cierre.parte_cod, ide=r.cierre.ide)
        if _mes(f) < mes:
            avisos.append(AVISO_R10_MES_ANTERIOR.format(**texto))
        elif f < destino_del_cierre(cadena) and not movible(
                r.cierre, est=est, obride_pruebas=obride_pruebas):
            avisos.append(AVISO_R10_NO_MOVIBLE.format(**texto))
        else:
            validas.append(r)
    if not validas:
        return None, avisos
    return max(validas, key=lambda r: (r.inicio.fecha_int, r.inicio.ide)),         avisos
