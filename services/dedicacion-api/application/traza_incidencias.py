# application/traza_incidencias.py
"""Traza de las incidencias registradas en Sigrid (F-030, R31).

Lo que hizo el transfer con las dos líneas de cada incidencia (`ini`: su
`CI*`; `fin`: `CIZ`) se guarda en la propia incidencia (columnas `sigrid_*`
de `IncidenciaORM`), como `registro_sigrid._trazar` lo hace en la
asignación (docs/ARCHITECTURE.md#regla-incidencia). Va en su módulo porque
es la traza de OTRA tabla: `test_f030_registro.py` vigila que los nombres
`sigrid_*` de aquí sean columnas de `incidencia`, como `test_f003` vigila los
de `registro_sigrid.py` contra `asignacion`.
"""
from __future__ import annotations

from datetime import datetime

from infrastructure.db.orm_models import IncidenciaORM
from sqlalchemy import update
from sqlalchemy.orm import Session

#: Longitud de la columna del motivo: lo que no quepa se corta antes de
#: escribirlo (un texto de más no puede tumbar la traza de lo ya escrito).
MAX_MOTIVO = IncidenciaORM.__table__.c.sigrid_motivo.type.length


def trazar_incidencias(s: Session, acciones: list[dict],
                       ahora: datetime, quien: str) -> None:
    """F-030 (R31): por incidencia, con sus dos líneas (`ini`, `fin`).
    Ninguna escrita ni ya registrada: `omitido` con el motivo. Si no,
    `registrado`, con el parte y el `hmores.ide` de cada línea, y el
    motivo de la que se omitió (si alguna); quién y cuándo, solo si se
    escribió alguna (como `ya_registradas` en la asignación).
    """
    por_id: dict[int, dict[str, dict]] = {}
    for a in acciones:
        por_id.setdefault(int(a["id"]), {})[a["rol"]] = a
    for inc_id, roles in por_id.items():
        lineas = [roles[r] for r in ("ini", "fin") if r in roles]
        hechas = [a for a in lineas
                  if a["accion"] in ("escribir", "ya_registrado")]
        motivos = [a.get("motivo") for a in lineas
                   if a["accion"] == "omitir" and a.get("motivo")]
        motivo = ("; ".join(dict.fromkeys(motivos))[:MAX_MOTIVO]
                  if motivos else None)
        if not hechas:
            valores = {"sigrid_estado": "omitido",
                       "sigrid_motivo": motivo or ""}
        else:
            valores = {
                "sigrid_estado": "registrado",
                "sigrid_parte_cod": hechas[0].get("parte_cod"),
                "sigrid_ide_ini": roles.get("ini", {}).get("hmores_ide"),
                "sigrid_ide_fin": roles.get("fin", {}).get("hmores_ide"),
                "sigrid_motivo": motivo}
            if any(a["accion"] == "escribir" for a in hechas):
                valores.update(sigrid_registrado_at_utc=ahora,
                               sigrid_registrado_by=quien)
        s.execute(update(IncidenciaORM)
                  .where(IncidenciaORM.id == inc_id).values(**valores))
