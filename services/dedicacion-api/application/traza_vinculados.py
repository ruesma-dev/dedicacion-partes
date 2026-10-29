# application/traza_vinculados.py
"""Traza de los recursos vinculados registrados en Sigrid (F-044, R30).

Lo que hizo el transfer con cada vinculado de una línea se guarda en su
fila de `asignacion_vinculado` (columnas `sigrid_*` de
`AsignacionVinculadoORM`), como `registro_sigrid._trazar` lo hace en la
asignación (docs/ARCHITECTURE.md#regla-vinculado). Va en su módulo porque
es la traza de OTRA tabla, como `traza_incidencias.py`: `test_f003` vigila
que los nombres `sigrid_*` de `registro_sigrid.py` sean columnas de
`asignacion`, y `asignacion_vinculado` tiene `sigrid_parte` (no
`sigrid_parte_cod`).

Como `registro_sigrid.py`, importa el ORM para construir sus sentencias: un
nombre de columna mal escrito falla al importar y no contra la base.
"""
from __future__ import annotations

from typing import Any

from infrastructure.db.orm_models import AsignacionORM
from infrastructure.db.repositories import upsert_asignacion_vinculado
from sqlalchemy import select
from sqlalchemy.orm import Session


def trazar_vinculados(s: Session, r: dict) -> None:
    """F-044 (R30): la traza de cada vinculado en su fila de
    `asignacion_vinculado`: `registrado` (parte y `hmores.ide`) el escrito;
    el ya registrado, `registrado` y su `hmores.ide`; `omitido` (motivo) el que sale en `omitidas` con su
    `vinculado_ide`. El pendiente de confirmar un pisado no deja traza,
    como el titular. La asignación va por subconsulta: si ya no existe, no
    se inserta nada."""
    def guardar(rid: int, vin: int, valores: dict[str, Any]) -> None:
        s.execute(upsert_asignacion_vinculado(
            select(AsignacionORM.id).where(AsignacionORM.id == int(rid)),
            int(vin), valores))

    for v in r.get("vinculados") or []:
        if not v.get("hmores_ide"):
            continue
        if v.get("accion") == "escribir":
            guardar(v["registro_id"], v["recurso_ide"], {
                "sigrid_estado": "registrado",
                "sigrid_parte": v.get("parte_cod"),
                "sigrid_hmores_ide": int(v["hmores_ide"]),
                "sigrid_motivo": None})
        elif v.get("accion") == "ya_registrado":
            # Como la ya registrada del titular: el estado y su línea, sin
            # tocar el parte ni el motivo de quien la registró.
            guardar(v["registro_id"], v["recurso_ide"], {
                "sigrid_estado": "registrado",
                "sigrid_hmores_ide": int(v["hmores_ide"])})
    for o in r.get("omitidas", []):
        if "vinculado_ide" in o:
            guardar(o["registro_id"], o["vinculado_ide"], {
                "sigrid_estado": "omitido",
                "sigrid_motivo": o.get("motivo") or ""})
