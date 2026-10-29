# application/services/reglas_incidencias.py
"""Reglas de las incidencias (vacaciones, bajas…) en el parte (F-030).

Aquí se IMPLEMENTAN; la fuente normativa es
`docs/ARCHITECTURE.md#regla-incidencia`. Funciones puras: sin I/O, sin
`settings` y sin cliente.

  - `decidir_incidencia`: cada incidencia son DOS líneas `hmores`, el inicio
    con su `CI*` el día `desde` y el fin con `CIZ` el día `hasta`, con
    `can = 0`. Si el recurso no tiene en `reshor` alguno de los dos códigos,
    se omiten las dos: nunca un inicio sin su fin (R24, R26).
  - F-062: `reconciliar` (R27 y anexo R30) ya no existe: lo que ya está en
    Sigrid lo decide la racha (`rachas.py`, `#regla-incidencia`).
  - `sigue_editable` y `no_editar_el_par`: la guarda de la relectura de
    `ejecutar` (R45; F-062 R14, por cadena).
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
#: F-062 (R12): la `synckey` del `CIZ` con que se cierra en M−1 una
#: racha de inicio ajeno: `porcentajes:inc:cierre:{ide del inicio}`.
PREFIJO_CIERRE = "porcentajes:inc:cierre:"
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
#: Sin uso en el código desde F-062 (lo citan los tests de F-030 que se
#: reescriben en su T11).
MOTIVO_INC_DUPLICADA = (
    "ya hay una línea {cod} del recurso el {dia:02d}/{mes:02d} en el parte "
    "{parte}: no se duplica")
#: Anexo R30 (R42, R43, R45).
MOTIVO_INC_CAMBIADA = (
    "cambiada en Sigrid (línea {ide}: otro día, código o cantidad): no se "
    "toca; para igualar, pon en el cuadrante lo que tiene Sigrid")
MOTIVO_INC_CERRADO = "el parte {parte} está cerrado: sigue del {desde} al {hasta}"
#: F-062 (R14): la guarda va por cadena (`ini`, `fin` y `devolver`).
MOTIVO_INC_PAR = (
    "no se edita: otra línea de la racha (línea {ide}) ya no se puede "
    "editar; se editan todas o ninguna")
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


def _codigo(linea: LineaIncidenciaSigrid) -> str:
    return (linea.hora_codigo or "").strip()


def sigue_editable(linea, a: AccionIncidencia, est: int) -> bool:
    """R45 y F-062 R14 (D12): la línea releída justo antes de escribir (la
    de F-051 R12) sigue cumpliendo para la acción `editar` `a`: existe, sin
    enlaces, del recurso, con su código, en la `fec` que vio el preflight
    (`fec_antes`), en un parte En registro (`est`) y con el `can` y la
    `synckey` leídos: los nuestros (0, nulo cuenta como 0, y nuestra
    `synckey`) o, si es un `CIZ` ajeno (`a.ajena`), los suyos
    (`can_leido` y `synckey_leida`)."""
    if a.ajena:
        sk, can = (a.synckey_leida or "").strip(), float(a.can_leido or 0.0)
    else:
        sk, can = synckey_incidencia(a.id, a.rol), 0.0
    return (linea is not None and not linea.enlazada
            and linea.reside == a.recurso_ide
            and _codigo(linea) == a.hora_codigo
            and abs(float(linea.can or 0.0) - can) < _TOLERANCIA_CAN
            and (linea.synckey or "").strip() == sk
            and linea.fecha_int == a.fec_antes and linea.parte_est == est)


def no_editar_el_par(acciones: Iterable[AccionIncidencia],
                     fallan: set[int]) -> None:
    """R45 y F-062 R14: si una línea `editar` de una cadena ya no se puede
    editar (su `hmores_ide` en `fallan`), no se edita ninguna de la cadena
    (`ini`, `fin` y `devolver`; todas llevan el `id` de la dueña): esa va a
    `omitir` «cambiada en Sigrid» y las demás, con `MOTIVO_INC_PAR`. Cambia
    las acciones en sitio."""
    acciones = [a for a in acciones if a.accion == "editar"]
    malas = {a.id: a.hmores_ide for a in acciones if a.hmores_ide in fallan}
    for a in acciones:
        if a.id not in malas:
            continue
        motivo = (MOTIVO_INC_CAMBIADA if a.hmores_ide in fallan
                  else MOTIVO_INC_PAR)
        a.accion, a.fec_antes = "omitir", None
        a.motivo = motivo.format(
            ide=a.hmores_ide if a.hmores_ide in fallan else malas[a.id])
