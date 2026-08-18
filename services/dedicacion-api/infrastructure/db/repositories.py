# infrastructure/db/repositories.py
"""Implementación PostgreSQL de los puertos de persistencia.

Todos los repositorios comparten la misma Session; la frontera
transaccional la marca SqlAlchemyUnitOfWork (commit/rollback único).
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session, sessionmaker

from domain.models import (
    EstadoPeriodo,
    Linea,
    Obra,
    Periodo,
    ResultadoSyncMaestro,
    TipoEvento,
    Trabajador,
)
from infrastructure.db.orm_models import (
    AsignacionORM,
    EventoORM,
    ObraORM,
    PeriodoORM,
    TrabajadorORM,
)

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Trabajadores
# ----------------------------------------------------------------------
class PgTrabajadorRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def sincronizar(self, filas: list[dict[str, Any]]) -> ResultadoSyncMaestro:
        actuales = {t.ide: t for t in self._s.scalars(select(TrabajadorORM)).all()}
        recibidos: set[int] = set()
        altas = actualizados = 0
        for fila in filas:
            ide = int(fila["ide"])
            recibidos.add(ide)
            existente = actuales.get(ide)
            if existente is None:
                self._s.add(
                    TrabajadorORM(
                        ide=ide,
                        cod=_texto(fila.get("cod")),
                        nombre=_texto(fila.get("nombre")) or f"(sin nombre {ide})",
                        dni=_texto(fila.get("dni")),
                        categoria=_texto(fila.get("categoria")),
                        activo=True,
                    )
                )
                altas += 1
            else:
                cambio = (
                    existente.nombre != (_texto(fila.get("nombre")) or existente.nombre)
                    or existente.dni != _texto(fila.get("dni"))
                    or existente.categoria != _texto(fila.get("categoria"))
                    or existente.cod != _texto(fila.get("cod"))
                    or not existente.activo
                )
                existente.cod = _texto(fila.get("cod"))
                existente.nombre = _texto(fila.get("nombre")) or existente.nombre
                existente.dni = _texto(fila.get("dni"))
                existente.categoria = _texto(fila.get("categoria"))
                existente.activo = True
                if cambio:
                    actualizados += 1
        desactivados = 0
        for ide, orm in actuales.items():
            if ide not in recibidos and orm.activo:
                orm.activo = False
                desactivados += 1
        return ResultadoSyncMaestro(
            recibidos=len(recibidos),
            altas=altas,
            actualizados=actualizados,
            desactivados=desactivados,
        )

    def listar_para_periodo(self, periodo_id: int) -> list[Trabajador]:
        con_lineas = select(AsignacionORM.trabajador_ide).where(
            AsignacionORM.periodo_id == periodo_id
        )
        stmt = (
            select(TrabajadorORM)
            .where(TrabajadorORM.activo.is_(True) | TrabajadorORM.ide.in_(con_lineas))
            .order_by(TrabajadorORM.nombre)
        )
        return [_a_trabajador(t) for t in self._s.scalars(stmt).all()]

    def obtener(self, ide: int) -> Trabajador | None:
        orm = self._s.get(TrabajadorORM, ide)
        return _a_trabajador(orm) if orm else None


# ----------------------------------------------------------------------
# Obras
# ----------------------------------------------------------------------
class PgObraRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def sincronizar(self, filas: list[dict[str, Any]]) -> ResultadoSyncMaestro:
        actuales = {o.ide: o for o in self._s.scalars(select(ObraORM)).all()}
        recibidos: set[int] = set()
        altas = actualizados = 0
        for fila in filas:
            ide = int(fila["ide"])
            cod = _texto(fila.get("cod"))
            if not cod:
                logger.warning("Obra %s sin código; omitida", ide)
                continue
            recibidos.add(ide)
            existente = actuales.get(ide)
            if existente is None:
                self._s.add(
                    ObraORM(
                        ide=ide,
                        cod=cod,
                        descripcion=_texto(fila.get("descripcion")) or "",
                        estado_sigrid=_texto(fila.get("estado_sigrid")),
                        activa=True,
                    )
                )
                altas += 1
            else:
                cambio = (
                    existente.cod != cod
                    or existente.descripcion != (_texto(fila.get("descripcion")) or "")
                    or existente.estado_sigrid != _texto(fila.get("estado_sigrid"))
                    or not existente.activa
                )
                existente.cod = cod
                existente.descripcion = _texto(fila.get("descripcion")) or ""
                existente.estado_sigrid = _texto(fila.get("estado_sigrid"))
                existente.activa = True
                if cambio:
                    actualizados += 1
        desactivadas = 0
        for ide, orm in actuales.items():
            if ide not in recibidos and orm.activa:
                orm.activa = False
                desactivadas += 1
        return ResultadoSyncMaestro(
            recibidos=len(recibidos),
            altas=altas,
            actualizados=actualizados,
            desactivados=desactivadas,
        )

    def listar_para_periodo(self, periodo_id: int) -> list[Obra]:
        usadas = select(AsignacionORM.obra_ide).where(
            AsignacionORM.periodo_id == periodo_id
        )
        stmt = (
            select(ObraORM)
            .where(ObraORM.activa.is_(True) | ObraORM.ide.in_(usadas))
            .order_by(ObraORM.cod)
        )
        return [_a_obra(o) for o in self._s.scalars(stmt).all()]

    def existen(self, ides: set[int]) -> set[int]:
        if not ides:
            return set()
        stmt = select(ObraORM.ide).where(ObraORM.ide.in_(ides))
        return set(self._s.scalars(stmt).all())


# ----------------------------------------------------------------------
# Periodos
# ----------------------------------------------------------------------
class PgPeriodoRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def listar(self) -> list[Periodo]:
        stmt = select(PeriodoORM).order_by(
            PeriodoORM.anio.desc(), PeriodoORM.mes.desc()
        )
        return [_a_periodo(p) for p in self._s.scalars(stmt).all()]

    def obtener(self, anio: int, mes: int) -> tuple[int, Periodo] | None:
        stmt = select(PeriodoORM).where(
            PeriodoORM.anio == anio, PeriodoORM.mes == mes
        )
        orm = self._s.scalars(stmt).first()
        return (orm.id, _a_periodo(orm)) if orm else None

    def crear(self, anio: int, mes: int) -> tuple[int, Periodo]:
        orm = PeriodoORM(anio=anio, mes=mes, estado=EstadoPeriodo.ABIERTO.value)
        self._s.add(orm)
        self._s.flush()
        return orm.id, _a_periodo(orm)

    def cambiar_estado(self, anio: int, mes: int, estado: str) -> Periodo:
        stmt = select(PeriodoORM).where(
            PeriodoORM.anio == anio, PeriodoORM.mes == mes
        )
        orm = self._s.scalars(stmt).one()
        orm.estado = estado
        from datetime import datetime, timezone

        orm.cerrado_en = (
            datetime.now(timezone.utc)
            if estado == EstadoPeriodo.CERRADO.value
            else None
        )
        return _a_periodo(orm)

    def anterior_con_datos(self, anio: int, mes: int) -> tuple[int, Periodo] | None:
        clave = anio * 100 + mes
        stmt = (
            select(PeriodoORM)
            .join(AsignacionORM, AsignacionORM.periodo_id == PeriodoORM.id)
            .where((PeriodoORM.anio * 100 + PeriodoORM.mes) < clave)
            .order_by(PeriodoORM.anio.desc(), PeriodoORM.mes.desc())
            .limit(1)
        )
        orm = self._s.scalars(stmt).first()
        return (orm.id, _a_periodo(orm)) if orm else None


# ----------------------------------------------------------------------
# Asignaciones
# ----------------------------------------------------------------------
class PgAsignacionRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def lineas_de_trabajador(
        self, periodo_id: int, trabajador_ide: int
    ) -> list[Linea]:
        stmt = (
            select(AsignacionORM, ObraORM)
            .join(ObraORM, ObraORM.ide == AsignacionORM.obra_ide)
            .where(
                AsignacionORM.periodo_id == periodo_id,
                AsignacionORM.trabajador_ide == trabajador_ide,
            )
            .order_by(ObraORM.cod, AsignacionORM.es_postventa)
        )
        return [_a_linea(a, o) for a, o in self._s.execute(stmt).all()]

    def lineas_del_periodo(self, periodo_id: int) -> dict[int, list[Linea]]:
        stmt = (
            select(AsignacionORM, ObraORM)
            .join(ObraORM, ObraORM.ide == AsignacionORM.obra_ide)
            .where(AsignacionORM.periodo_id == periodo_id)
            .order_by(
                AsignacionORM.trabajador_ide, ObraORM.cod, AsignacionORM.es_postventa
            )
        )
        resultado: dict[int, list[Linea]] = {}
        for asignacion, obra in self._s.execute(stmt).all():
            resultado.setdefault(asignacion.trabajador_ide, []).append(
                _a_linea(asignacion, obra)
            )
        return resultado

    def reemplazar(
        self,
        periodo_id: int,
        trabajador_ide: int,
        lineas: list[Linea],
        usuario: str,
    ) -> None:
        self._s.execute(
            delete(AsignacionORM).where(
                AsignacionORM.periodo_id == periodo_id,
                AsignacionORM.trabajador_ide == trabajador_ide,
            )
        )
        for linea in lineas:
            self._s.add(
                AsignacionORM(
                    periodo_id=periodo_id,
                    trabajador_ide=trabajador_ide,
                    obra_ide=linea.obra_ide,
                    es_postventa=linea.es_postventa,
                    porcentaje=linea.porcentaje,
                    actualizado_por=usuario,
                )
            )
        self._s.flush()


# ----------------------------------------------------------------------
# Eventos (histórico / deshacer)
# ----------------------------------------------------------------------
class PgEventoRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def registrar(
        self,
        periodo_id: int,
        trabajador_ide: int,
        tipo: TipoEvento,
        usuario: str,
        antes: list[dict[str, Any]],
        despues: list[dict[str, Any]],
    ) -> None:
        self._s.add(
            EventoORM(
                periodo_id=periodo_id,
                trabajador_ide=trabajador_ide,
                tipo=tipo.value,
                usuario=usuario,
                snapshot_antes=antes,
                snapshot_despues=despues,
            )
        )

    def ultimo_pendiente(
        self, periodo_id: int, trabajador_ide: int
    ) -> tuple[int, list[dict[str, Any]]] | None:
        stmt = (
            select(EventoORM)
            .where(
                EventoORM.periodo_id == periodo_id,
                EventoORM.trabajador_ide == trabajador_ide,
                EventoORM.deshecho.is_(False),
            )
            .order_by(EventoORM.id.desc())
            .limit(1)
        )
        orm = self._s.scalars(stmt).first()
        return (orm.id, orm.snapshot_antes) if orm else None

    def marcar_deshecho(self, evento_id: int) -> None:
        self._s.execute(
            update(EventoORM).where(EventoORM.id == evento_id).values(deshecho=True)
        )

    def trabajadores_con_pendientes(self, periodo_id: int) -> set[int]:
        stmt = (
            select(EventoORM.trabajador_ide)
            .where(
                EventoORM.periodo_id == periodo_id, EventoORM.deshecho.is_(False)
            )
            .distinct()
        )
        return set(self._s.scalars(stmt).all())


# ----------------------------------------------------------------------
# Unit of Work
# ----------------------------------------------------------------------
class SqlAlchemyUnitOfWork:
    """Agrupa los repositorios sobre una única Session/transacción."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._session_factory()
        s = self._session
        self.trabajadores = PgTrabajadorRepository(s)
        self.obras = PgObraRepository(s)
        self.periodos = PgPeriodoRepository(s)
        self.asignaciones = PgAsignacionRepository(s)
        self.eventos = PgEventoRepository(s)
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        assert self._session is not None
        try:
            if exc_type is not None:
                self._session.rollback()
        finally:
            self._session.close()
            self._session = None

    def commit(self) -> None:
        assert self._session is not None
        self._session.commit()

    def rollback(self) -> None:
        assert self._session is not None
        self._session.rollback()


# ----------------------------------------------------------------------
# Mapeos ORM → dominio
# ----------------------------------------------------------------------
def _texto(valor: Any) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def _a_trabajador(orm: TrabajadorORM) -> Trabajador:
    return Trabajador(
        ide=orm.ide,
        cod=orm.cod,
        nombre=orm.nombre,
        dni=orm.dni,
        categoria=orm.categoria,
        activo=orm.activo,
    )


def _a_obra(orm: ObraORM) -> Obra:
    return Obra(
        ide=orm.ide,
        cod=orm.cod,
        descripcion=orm.descripcion,
        estado_sigrid=orm.estado_sigrid,
        activa=orm.activa,
    )


def _a_periodo(orm: PeriodoORM) -> Periodo:
    return Periodo(anio=orm.anio, mes=orm.mes, estado=EstadoPeriodo(orm.estado))


def _a_linea(a: AsignacionORM, o: ObraORM) -> Linea:
    return Linea(
        obra_ide=a.obra_ide,
        es_postventa=a.es_postventa,
        porcentaje=Decimal(a.porcentaje),
        cod=o.cod,
        descripcion=o.descripcion,
        obra_activa=o.activa,
    )
