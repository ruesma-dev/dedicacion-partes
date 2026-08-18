# application/registro_sigrid.py
"""Registro del periodo en Sigrid vía porcentajes-transfer.

Agrupa las asignaciones del periodo por OBRA (el contrato del transfer es
por obra), llama a preflight/ejecutar secuencialmente y persiste la traza
en la propia asignación (columnas sigrid_*). El porcentaje viaja SOBRE 1.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select, text
from sqlalchemy.orm import Session, sessionmaker

from infrastructure.db.orm_models import (
    AsignacionORM, ObraORM, PeriodoORM, TrabajadorORM,
)
from infrastructure.transfer.transfer_client import TransferClient

logger = logging.getLogger(__name__)

_ALTERS = [
    "ALTER TABLE asignacion ADD COLUMN IF NOT EXISTS sigrid_estado VARCHAR(16)",
    "ALTER TABLE asignacion ADD COLUMN IF NOT EXISTS sigrid_parte_cod VARCHAR(24)",
    "ALTER TABLE asignacion ADD COLUMN IF NOT EXISTS sigrid_hmores_ide INTEGER",
    "ALTER TABLE asignacion ADD COLUMN IF NOT EXISTS sigrid_motivo VARCHAR(300)",
    "ALTER TABLE asignacion ADD COLUMN IF NOT EXISTS "
    "sigrid_registrado_at_utc TIMESTAMPTZ",
    "ALTER TABLE asignacion ADD COLUMN IF NOT EXISTS "
    "sigrid_registrado_by VARCHAR(64)",
]


class RegistroSigrid:
    def __init__(self, session_factory: sessionmaker[Session],
                 transfer: TransferClient) -> None:
        self._sf = session_factory
        self._transfer = transfer
        with self._sf() as s:
            for stmt in _ALTERS:
                s.execute(text(stmt))
            s.commit()

    # ------------------------------------------------------------- #
    def _payloads(self, s: Session, anio: int, mes: int,
                  overrides: dict[int, int],
                  trabajador_ide: Optional[int] = None
                  ) -> list[dict[str, Any]]:
        filas = s.execute(
            select(AsignacionORM, TrabajadorORM, ObraORM)
            .join(PeriodoORM, PeriodoORM.id == AsignacionORM.periodo_id)
            .join(TrabajadorORM,
                  TrabajadorORM.ide == AsignacionORM.trabajador_ide)
            .join(ObraORM, ObraORM.ide == AsignacionORM.obra_ide)
            .where(PeriodoORM.anio == anio, PeriodoORM.mes == mes,
                   AsignacionORM.porcentaje > 0,
                   *( [AsignacionORM.trabajador_ide == trabajador_ide]
                      if trabajador_ide else [] ))
            .order_by(ObraORM.cod, TrabajadorORM.nombre)
        ).all()
        por_obra: dict[int, dict[str, Any]] = {}
        for a, t, o in filas:
            grupo = por_obra.setdefault(o.ide, {
                "obra": {"ide": o.ide, "codigo": o.cod,
                         "nombre": o.descripcion},
                "lineas": [],
            })
            linea = {
                "registro_id": a.id, "ano": anio, "mes": mes,
                "porcentaje": round(float(a.porcentaje) / 100.0, 4),
                "empleado_ide": t.ide, "dni": t.dni, "nombre": t.nombre,
                "categoria": t.categoria,
                "es_postventa": bool(a.es_postventa),
            }
            if overrides.get(a.id):
                linea["paride"] = int(overrides[a.id])
            grupo["lineas"].append(linea)
        return list(por_obra.values())

    # ------------------------------------------------------------- #
    def preflight(self, anio: int, mes: int,
                  overrides: Optional[dict[int, int]] = None,
                  trabajador_ide: Optional[int] = None) -> dict:
        with self._sf() as s:
            payloads = self._payloads(s, anio, mes, overrides or {},
                                      trabajador_ide)
        resultados = []
        for p in payloads:
            r = self._transfer.preflight({**p, "pisar_claves": []})
            resultados.append({"obra": p["obra"], **r})
        return {"ok": all(r.get("ok") for r in resultados) if resultados
                else True, "obras": resultados}

    # ------------------------------------------------------------- #
    def ejecutar(self, anio: int, mes: int, *, pisar_claves: list[str],
                 overrides: Optional[dict[int, int]] = None,
                 usuario: str = "local",
                 trabajador_ide: Optional[int] = None) -> dict:
        with self._sf() as s:
            payloads = self._payloads(s, anio, mes, overrides or {},
                                      trabajador_ide)
        resultados = []
        for p in payloads:
            r = self._transfer.ejecutar({**p, "pisar_claves": pisar_claves,
                                         "usuario": usuario})
            resultados.append({"obra": p["obra"], **r})
            if r.get("ok"):
                self._trazar(r, usuario)
        return {"ok": all(x.get("ok") for x in resultados) if resultados
                else True, "obras": resultados}

    def _trazar(self, r: dict, usuario: str) -> None:
        ahora = datetime.now(timezone.utc)
        with self._sf() as s:
            for e in r.get("escritas", []):
                s.execute(text(
                    "UPDATE asignacion SET sigrid_estado='registrado', "
                    "sigrid_parte_cod=:p, sigrid_hmores_ide=:h, "
                    "sigrid_motivo=NULL, sigrid_registrado_at_utc=:t, "
                    "sigrid_registrado_by=:u WHERE id=:i"),
                    {"p": e.get("parte_cod"), "h": e.get("hmores_ide"),
                     "t": ahora, "u": usuario, "i": e["registro_id"]})
            for rid in r.get("ya_registradas", []):
                s.execute(text(
                    "UPDATE asignacion SET sigrid_estado='registrado' "
                    "WHERE id=:i AND sigrid_estado IS DISTINCT FROM "
                    "'registrado'"), {"i": rid})
            for o in r.get("omitidas", []):
                s.execute(text(
                    "UPDATE asignacion SET sigrid_estado='omitido', "
                    "sigrid_motivo=:m WHERE id=:i"),
                    {"m": (o.get("motivo") or "")[:300],
                     "i": o["registro_id"]})
            s.commit()
