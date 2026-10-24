# application/traza_incidencias.py
"""Traza de las incidencias registradas en Sigrid (F-030, R31).

Lo que hizo el transfer con las dos líneas de cada incidencia (`ini`: su
`CI*`; `fin`: `CIZ`) se guarda en la propia incidencia (columnas `sigrid_*`
de `IncidenciaORM`), como `registro_sigrid._trazar` lo hace en la
asignación (docs/ARCHITECTURE.md#regla-incidencia). Va en su módulo porque
es la traza de OTRA tabla: `test_f030_registro.py` vigila que los nombres
`sigrid_*` de aquí sean columnas de `incidencia`, como `test_f003` vigila los
de `registro_sigrid.py` contra `asignacion`.

Anexo R30 (R39): por rol, el `hmores.ide` y el día de la línea escrita,
editada o ya registrada; un `omitir` no toca los de su rol, y la incidencia
solo pasa a `omitido` si no le queda ningún `ide` (una registrada que esta
vez se omite sigue registrada, con el motivo).

Obs. 5 de la review: este módulo de `application/` importa el ORM
(`IncidenciaORM`) para construir sus `UPDATE`, igual que hace
`registro_sigrid.py` con `AsignacionORM`: un nombre de columna mal escrito
falla al importar y no contra la base. Se queda así a propósito.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from infrastructure.db.orm_models import IncidenciaORM
from sqlalchemy import update
from sqlalchemy.orm import Session

#: Longitud de la columna del motivo: lo que no quepa se corta antes de
#: escribirlo (un texto de más no puede tumbar la traza de lo ya escrito).
MAX_MOTIVO = IncidenciaORM.__table__.c.sigrid_motivo.type.length

#: Columnas de la traza de cada rol: su `hmores.ide` y su día (R39).
_COLUMNAS_ROL = {"ini": ("sigrid_ide_ini", "sigrid_dia_ini"),
                 "fin": ("sigrid_ide_fin", "sigrid_dia_fin")}
#: Acciones tras las que la línea está en Sigrid con su `ide` (R39).
_HECHAS = ("escribir", "editar", "ya_registrado")


def campos_de_traza(inc: Any) -> dict[str, Any]:
    """R39: lo que la api manda al transfer de la traza de una incidencia
    (`hmores_ide_*` y `dia_*`, nulos los que falten). Sin ninguno (no
    registrada), nada: la petición de siempre. F-062 (R15): y
    `dia_fin_antes`, el día original del `CIZ` ajeno que movió, solo si lo
    hay (sin él, la traza de F-030 tal cual)."""
    traza = {"hmores_ide_ini": inc.sigrid_ide_ini,
             "hmores_ide_fin": inc.sigrid_ide_fin,
             "dia_ini": inc.sigrid_dia_ini, "dia_fin": inc.sigrid_dia_fin}
    antes = getattr(inc, "sigrid_dia_fin_antes", None)
    if antes is not None:
        traza["dia_fin_antes"] = antes
    return traza if any(v is not None for v in traza.values()) else {}


def quitada_para_el_modal(inc: Any, trabajador: Any, obra: Any,
                          letra: str) -> dict[str, Any]:
    """R38: una quitada como la lista el preflight, para retirarla a mano
    en Sigrid (trabajador, obra, código y letra, días, parte e `ide`s)."""
    return {"id": inc.id, "trabajador_ide": trabajador.ide,
            "trabajador": trabajador.nombre, "obra_ide": obra.ide,
            "obra_cod": obra.cod, "obra_nombre": obra.descripcion,
            "codigo": inc.codigo, "letra": letra, "desde": inc.dia_desde,
            "hasta": inc.dia_hasta, "parte_cod": inc.sigrid_parte_cod,
            "hmores_ide_ini": inc.sigrid_ide_ini,
            "hmores_ide_fin": inc.sigrid_ide_fin}


def trazar_incidencias(s: Session, acciones: list[dict],
                       ahora: datetime, quien: str) -> None:
    """F-030 (R31, R39): por incidencia, con sus dos líneas (`ini`, `fin`).

    Alguna escrita, editada o ya registrada: `registrado`, con el parte, el
    `hmores.ide` y el día de CADA una de esas (las omitidas no tocan los de
    su rol) y el motivo de la que se omitió (si alguna); quién y cuándo,
    solo si se escribió o editó alguna (como `ya_registradas` en la
    asignación). Ninguna: el motivo y, solo si no le queda ningún `ide`
    (no estaba registrada), `omitido`.
    """
    por_id: dict[int, dict[str, dict]] = {}
    for a in acciones:
        por_id.setdefault(int(a["id"]), {})[a["rol"]] = a
    for inc_id, roles in por_id.items():
        lineas = [roles[r] for r in _COLUMNAS_ROL if r in roles]
        hechas = [a for a in lineas if a["accion"] in _HECHAS]
        motivos = [a.get("motivo") for a in lineas
                   if a["accion"] == "omitir" and a.get("motivo")]
        motivo = ("; ".join(dict.fromkeys(motivos))[:MAX_MOTIVO]
                  if motivos else None)
        if not hechas:
            s.execute(update(IncidenciaORM)
                      .where(IncidenciaORM.id == inc_id)
                      .values(sigrid_motivo=motivo or ""))
            s.execute(update(IncidenciaORM)
                      .where(IncidenciaORM.id == inc_id,
                             IncidenciaORM.sigrid_ide_ini.is_(None),
                             IncidenciaORM.sigrid_ide_fin.is_(None))
                      .values(sigrid_estado="omitido"))
            continue
        valores = {"sigrid_estado": "registrado",
                   "sigrid_parte_cod": hechas[0].get("parte_cod"),
                   "sigrid_motivo": motivo}
        for a in hechas:
            col_ide, col_dia = _COLUMNAS_ROL[a["rol"]]
            valores[col_ide] = a.get("hmores_ide")
            valores[col_dia] = int(a["fecha_int"]) % 100
        if any(a["accion"] != "ya_registrado" for a in hechas):
            valores.update(sigrid_registrado_at_utc=ahora,
                           sigrid_registrado_by=quien)
        s.execute(update(IncidenciaORM)
                  .where(IncidenciaORM.id == inc_id).values(**valores))
