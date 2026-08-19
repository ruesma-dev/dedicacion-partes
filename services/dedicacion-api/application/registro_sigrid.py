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

from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

from infrastructure.db.orm_models import (
    AsignacionORM, ObraORM, PeriodoORM, TrabajadorORM,
)
from infrastructure.transfer.transfer_client import TransferClient

logger = logging.getLogger(__name__)

#: Longitudes de las columnas de traza, declaradas en `orm_models.py`. Lo que
#: no quepa se corta antes de escribirlo: un texto de más no puede tumbar la
#: traza de un registro que en Sigrid YA se hizo.
_MAX_MOTIVO = 300
_MAX_USUARIO = 64


class RegistroSigrid:
    def __init__(self, session_factory: sessionmaker[Session],
                 transfer: TransferClient) -> None:
        self._sf = session_factory
        self._transfer = transfer

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
        """Persiste en la asignación qué hizo Sigrid con ella.

        Las sentencias se construyen con el ORM (`update(AsignacionORM)`), no
        con SQL crudo: un nombre de columna mal escrito falla al importar, no
        en producción contra la base.
        """
        ahora = datetime.now(timezone.utc)
        quien = (usuario or "")[:_MAX_USUARIO]
        with self._sf() as s:
            for e in r.get("escritas", []):
                s.execute(
                    update(AsignacionORM)
                    .where(AsignacionORM.id == e["registro_id"])
                    .values(sigrid_estado="registrado",
                            sigrid_parte_cod=e.get("parte_cod"),
                            sigrid_hmores_ide=e.get("hmores_ide"),
                            sigrid_motivo=None,
                            sigrid_registrado_at_utc=ahora,
                            sigrid_registrado_by=quien))
            for rid in r.get("ya_registradas", []):
                # Solo asciende el estado, y solo si aún no era 'registrado':
                # no se pisa la marca de tiempo de quien lo registró de verdad.
                s.execute(
                    update(AsignacionORM)
                    .where(AsignacionORM.id == rid,
                           AsignacionORM.sigrid_estado.is_distinct_from(
                               "registrado"))
                    .values(sigrid_estado="registrado"))
            for o in r.get("omitidas", []):
                s.execute(
                    update(AsignacionORM)
                    .where(AsignacionORM.id == o["registro_id"])
                    .values(sigrid_estado="omitido",
                            sigrid_motivo=(o.get("motivo") or "")[:_MAX_MOTIVO]))
            s.commit()
