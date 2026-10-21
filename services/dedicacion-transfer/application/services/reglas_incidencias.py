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
    está. Cada línea del par se decide sola. Cambia las acciones en sitio."""
    existentes = list(existentes)
    for a in acciones:
        if a.accion != "escribir":
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
