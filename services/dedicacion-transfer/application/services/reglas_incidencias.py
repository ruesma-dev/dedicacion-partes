# application/services/reglas_incidencias.py
"""Reglas de las incidencias (vacaciones, bajas…) en el parte (F-030).

Aquí se IMPLEMENTAN; la fuente normativa es
`docs/ARCHITECTURE.md#regla-incidencia`. Funciones puras: sin I/O, sin
`settings` y sin cliente.

  - `decidir_incidencia`: cada incidencia son DOS líneas `hmores`, el inicio
    con su `CI*` el día `desde` y el fin con `CIZ` el día `hasta`, con
    `can = 0`. Si el recurso no tiene en `reshor` alguno de los dos códigos,
    se omiten las dos: nunca un inicio sin su fin (R24, R26).
  - `deduplicar`: una línea igual (recurso, código y `fec`) en cualquier
    parte del mes no se escribe otra vez (R27).
  - `reconciliar` (anexo R30, R40-R44): la que ya es NUESTRA en Sigrid (por
    su `ide` de la traza o por su `synckey`) no se escribe: con su `fec`, ya
    registrada; con otra, se EDITA su `fec` en su sitio, salvo que la hayan
    cambiado a mano, su parte esté cerrado o el día nuevo ya lo tenga otra
    igual. Sin la nuestra, R27 como `deduplicar`.
  - `synckey_incidencia`: la idempotencia, por incidencia y rol.

Una incidencia NO es jornada: no entra en la identidad de
`#regla-conflicto`, ni en `#regla-capacidad`, ni en `#regla-sin-partida`
(R28). Por eso no pasa por `ReglasPorcentajes` ni por `AccionLinea`.
"""
from __future__ import annotations

import calendar
from collections.abc import Iterable

from domain.models.registro_models import (
    AccionIncidencia,
    HoraRecurso,
    IncidenciaEntrada,
    LineaIncidenciaSigrid,
)

_TRAZA_ROL = {"ini": ("hmores_ide_ini", "dia_ini"),
              "fin": ("hmores_ide_fin", "dia_fin")}

from application.services.reglas_porcentajes import (
    MOTIVO_SIN_EMPRESA,
    empresa_valida,
)

#: Código de `auxhor` que cierra el tramo de cualquier incidencia.
CODIGO_FIN = "CIZ"
#: Prefijo de la `synckey` de las líneas de incidencia (distinta de la de las
#: líneas de %, `porcentajes:{id}`).
PREFIJO_SYNCKEY_INCIDENCIA = "porcentajes:inc:"
ROLES = ("ini", "fin")

#: Motivos. Caben en los 300 caracteres de `incidencia.sigrid_motivo`.
MOTIVO_INC_SIN_RECURSO = "la incidencia no trae el recurso del trabajador"
MOTIVO_INC_SIN_CODIGO = (
    "el recurso no tiene en Sigrid el tipo de hora {cod}: no se escribe la "
    "incidencia (ni su inicio ni su fin)")
MOTIVO_INC_DIAS = (
    "días de la incidencia imposibles en {mes:02d}/{ano}: del {desde} al "
    "{hasta}; no se escribe")
MOTIVO_INC_YA = "ya registrada en Sigrid (línea {ide}); no se duplica"
MOTIVO_INC_DUPLICADA = (
    "ya hay una línea {cod} del recurso el {dia:02d}/{mes:02d} en el parte "
    "{parte}: no se duplica")
#: Anexo R30 (R42, R43, R45).
MOTIVO_INC_CAMBIADA = (
    "cambiada en Sigrid (línea {ide}: otro día, código o cantidad): no se "
    "toca; para igualar, pon en el cuadrante lo que tiene Sigrid")
MOTIVO_INC_CERRADO = "el parte {parte} está cerrado: sigue del {desde} al {hasta}"
MOTIVO_INC_PAR = (
    "no se edita: la otra línea de la incidencia (línea {ide}) ya no se puede "
    "editar; se editan las dos o ninguna")
#: `can` de una línea de incidencia: 0 (con la tolerancia de la guarda).
_TOLERANCIA_CAN = 0.000001


def synckey_incidencia(incidencia_id: int, rol: str) -> str:
    """`porcentajes:inc:{id}:ini|fin`."""
    if rol not in ROLES:
        raise ValueError(f"rol de incidencia no válido: {rol!r}")
    return f"{PREFIJO_SYNCKEY_INCIDENCIA}{int(incidencia_id)}:{rol}"


def _dias_validos(inc: IncidenciaEntrada) -> bool:
    ultimo = calendar.monthrange(int(inc.ano), int(inc.mes))[1]
    return (type(inc.desde) is int and type(inc.hasta) is int
            and 1 <= inc.desde <= inc.hasta <= ultimo)


def _fecha(inc: IncidenciaEntrada, dia: int) -> int:
    return int(inc.ano) * 10000 + int(inc.mes) * 100 + int(dia)


def decidir_incidencia(
    inc: IncidenciaEntrada,
    horas_por_recurso: dict[int, list[HoraRecurso]],
    *,
    motivo_empresa: str | None = None,
) -> list[AccionIncidencia]:
    """Las dos acciones de la incidencia, `[inicio, fin]` (R24, R26).

    Se omiten LAS DOS, con el mismo motivo, sin empresa (o con la obra en
    otra, `motivo_empresa`), sin recurso, con días imposibles para el mes o
    si el recurso no tiene en `reshor` el código o `CIZ`."""
    validos = _dias_validos(inc)
    fechas = ((_fecha(inc, inc.desde), _fecha(inc, inc.hasta)) if validos
              else (0, 0))
    base = {"id": int(inc.id), "recurso_ide": inc.recurso_ide,
            "ano": int(inc.ano), "mes": int(inc.mes),
            "paride": int(inc.paride or 0)}

    def omitir(motivo: str) -> list[AccionIncidencia]:
        return [AccionIncidencia(rol=rol, accion="omitir", fecha_int=fecha,
                                 motivo=motivo, **base)
                for rol, fecha in zip(ROLES, fechas)]

    if not empresa_valida(inc.empresa):
        return omitir(MOTIVO_SIN_EMPRESA)
    if motivo_empresa:
        return omitir(motivo_empresa)
    if not inc.recurso_ide:
        return omitir(MOTIVO_INC_SIN_RECURSO)
    if not validos:
        return omitir(MOTIVO_INC_DIAS.format(
            desde=inc.desde, hasta=inc.hasta, mes=int(inc.mes),
            ano=int(inc.ano)))
    por_codigo = {h.cod: h for h in horas_por_recurso.get(
        int(inc.recurso_ide), [])}
    horas = [por_codigo.get(cod) for cod in (inc.codigo, CODIGO_FIN)]
    for cod, hora in zip((inc.codigo, CODIGO_FIN), horas):
        if hora is None:
            return omitir(MOTIVO_INC_SIN_CODIGO.format(cod=cod))
    return [AccionIncidencia(rol=rol, accion="escribir", fecha_int=fecha,
                             hora_ide=hora.horide, hora_codigo=hora.cod,
                             pre=float(hora.pre or 0.0), **base)
            for rol, fecha, hora in zip(ROLES, fechas, horas)]


def deduplicar(acciones: Iterable[AccionIncidencia],
               existentes: Iterable[LineaIncidenciaSigrid]) -> None:
    """R27: cada acción `escribir` que ya está en algún parte del mes (el
    mismo recurso, código y `fec`) no se escribe: `ya_registrado` si la
    línea es la nuestra (su `synckey`); si no, `omitir` con el parte donde
    está. R30: la que ya tiene su `synckey` en el mes es `ya_registrado`
    aunque hayan cambiado sus días (eso es F-033). Cada línea del par se
    decide sola. Cambia las acciones en sitio."""
    existentes = list(existentes)
    por_synckey = {e.synckey: e for e in existentes if e.synckey}
    for a in acciones:
        if a.accion != "escribir":
            continue
        nuestra = por_synckey.get(synckey_incidencia(a.id, a.rol))
        if nuestra is not None:
            a.accion, a.hmores_ide = "ya_registrado", nuestra.ide
            a.parte_cod = nuestra.parte_cod
            a.motivo = MOTIVO_INC_YA.format(ide=nuestra.ide)
            continue
        igual = next((e for e in existentes
                      if e.reside == a.recurso_ide
                      and e.fecha_int == a.fecha_int
                      and (e.hora_codigo or "").strip() == a.hora_codigo),
                     None)
        if igual is None:
            continue
        a.parte_cod = igual.parte_cod
        if igual.synckey == synckey_incidencia(a.id, a.rol):
            a.accion, a.hmores_ide = "ya_registrado", igual.ide
            a.motivo = MOTIVO_INC_YA.format(ide=igual.ide)
        else:
            a.accion = "omitir"
            a.motivo = MOTIVO_INC_DUPLICADA.format(
                cod=a.hora_codigo, dia=a.fecha_int % 100, mes=a.mes,
                parte=igual.parte_cod)


def _codigo(linea: LineaIncidenciaSigrid) -> str:
    return (linea.hora_codigo or "").strip()


def _nuestra(a: AccionIncidencia, entrada: IncidenciaEntrada | None,
             por_ide: dict[int, LineaIncidenciaSigrid],
             por_synckey: dict[str, LineaIncidenciaSigrid]
             ) -> LineaIncidenciaSigrid | None:
    """R40: la línea nuestra de esta acción: la de su `ide` en la traza o
    la de su `synckey`, siempre del recurso y con NUESTRA `synckey`."""
    sk = synckey_incidencia(a.id, a.rol)
    ide = (getattr(entrada, _TRAZA_ROL[a.rol][0]) if entrada is not None
           else None)
    for linea in (por_ide.get(int(ide)) if ide else None,
                  por_synckey.get(sk)):
        if (linea is not None and linea.reside == a.recurso_ide
                and linea.synckey == sk):
            return linea
    return None


def _cambiada(a: AccionIncidencia, entrada: IncidenciaEntrada | None,
              linea: LineaIncidenciaSigrid) -> bool:
    """R42 (D14): fuera de la `fec` registrada (si no consta, fuera del
    mes: una incidencia no cambia de mes, R48), con otro código o con
    `can` distinto de 0 (nulo cuenta como 0)."""
    dia = (getattr(entrada, _TRAZA_ROL[a.rol][1]) if entrada is not None
           else None)
    if dia is not None:
        fuera = linea.fecha_int != a.ano * 10000 + a.mes * 100 + int(dia)
    else:
        fuera = linea.fecha_int // 100 != a.fecha_int // 100
    return (fuera or _codigo(linea) != a.hora_codigo
            or abs(float(linea.can or 0.0)) >= _TOLERANCIA_CAN)


def _ocupada(a: AccionIncidencia, existentes: list[LineaIncidenciaSigrid],
             fec: dict[int, int], propia: int | None
             ) -> LineaIncidenciaSigrid | None:
    """R27 y R44: otra línea del recurso con el código de `a` en su `fec`,
    con las ediciones de la petición aplicadas (`fec`: la de cada línea
    tras la petición)."""
    return next((e for e in existentes
                 if e.ide != propia and e.reside == a.recurso_ide
                 and fec[e.ide] == a.fecha_int
                 and _codigo(e) == a.hora_codigo), None)


def reconciliar(acciones: Iterable[AccionIncidencia],
                entradas: Iterable[IncidenciaEntrada],
                existentes: Iterable[LineaIncidenciaSigrid], *,
                est: int) -> None:
    """Anexo R30 (R40-R44, D14, D15): cada acción `escribir` contra las
    líneas de incidencia leídas (R33, también por `ide`). Cambia las
    acciones en sitio; cada línea del par se decide sola.

    - La NUESTRA (`_nuestra`) con la `fec` pedida: `ya_registrado` (aunque
      le hayan cambiado el `can` o su parte esté cerrado, como F-051).
    - Con otra `fec`: `omitir` si la cambiaron en Sigrid (R42) o su parte
      no está En registro (`est`, R43); si no, `editar` su `fec`
      (`fec_antes`, la que tiene), salvo que el día nuevo lo tenga otra
      línea igual con las ediciones de la petición aplicadas (R44, D15).
      Hasta un punto fijo: una edición que no se hace deja su línea donde
      estaba.
    - Sin la nuestra (nunca escrita o borrada a mano): R27 contra lo
      leído, también con las ediciones aplicadas; si nada la ocupa, se
      escribe (F-051 R17)."""
    existentes = list(existentes)
    por_ide = {e.ide: e for e in existentes}
    por_synckey = {e.synckey: e for e in existentes if e.synckey}
    por_id = {int(e.id): e for e in entradas}
    nuestras: dict[int, dict[str, LineaIncidenciaSigrid]] = {}
    pendientes = []
    for a in acciones:
        if a.accion != "escribir":
            continue
        linea = _nuestra(a, por_id.get(a.id), por_ide, por_synckey)
        pendientes.append((a, linea))
        if linea is not None:
            nuestras.setdefault(a.id, {})[a.rol] = linea
    for a, linea in pendientes:
        if linea is None:
            continue
        a.hmores_ide, a.hmoide, a.parte_cod = (linea.ide, linea.hmoide,
                                               linea.parte_cod)
        if linea.fecha_int == a.fecha_int:
            a.accion, a.motivo = "ya_registrado", MOTIVO_INC_YA.format(
                ide=linea.ide)
        elif _cambiada(a, por_id.get(a.id), linea):
            a.accion = "omitir"
            a.motivo = MOTIVO_INC_CAMBIADA.format(ide=linea.ide)
        elif linea.parte_est != est:
            par = nuestras[a.id]
            dias = [par[r].fecha_int % 100 if r in par else None
                    for r in ROLES]
            a.accion = "omitir"
            a.motivo = MOTIVO_INC_CERRADO.format(
                parte=linea.parte_cod, desde=dias[0] or "?",
                hasta=dias[1] or "?")
        else:
            a.accion, a.fec_antes = "editar", linea.fecha_int
    editar = [(a, linea) for a, linea in pendientes if a.accion == "editar"]
    while True:
        fec = {e.ide: e.fecha_int for e in existentes}
        fec.update({linea.ide: a.fecha_int for a, linea in editar
                    if a.accion == "editar"})
        ocupadas = [(a, otra) for a, linea in editar if a.accion == "editar"
                    for otra in [_ocupada(a, existentes, fec, linea.ide)]
                    if otra is not None]
        if not ocupadas:
            break
        for a, otra in ocupadas:
            a.accion, a.fec_antes = "omitir", None
            a.motivo = MOTIVO_INC_DUPLICADA.format(
                cod=a.hora_codigo, dia=a.fecha_int % 100, mes=a.mes,
                parte=otra.parte_cod)
    for a, linea in pendientes:
        if linea is not None:
            continue
        otra = _ocupada(a, existentes, fec, None)
        if otra is not None:
            a.accion, a.parte_cod = "omitir", otra.parte_cod
            a.motivo = MOTIVO_INC_DUPLICADA.format(
                cod=a.hora_codigo, dia=a.fecha_int % 100, mes=a.mes,
                parte=otra.parte_cod)
