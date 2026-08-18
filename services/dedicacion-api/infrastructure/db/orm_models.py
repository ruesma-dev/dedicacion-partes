# infrastructure/db/orm_models.py
"""Modelos ORM (SQLAlchemy 2.0, estilo Mapped/mapped_column)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TrabajadorORM(Base):
    __tablename__ = "trabajador"

    ide: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # ide de Sigrid
    cod: Mapped[str | None] = mapped_column(Text)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    dni: Mapped[str | None] = mapped_column(Text)
    categoria: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sync_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("ix_trabajador_activo_nombre", "activo", "nombre"),)


class ObraORM(Base):
    __tablename__ = "obra"

    ide: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # ide de Sigrid
    cod: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False, default="")
    estado_sigrid: Mapped[str | None] = mapped_column(Text)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sync_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("ix_obra_activa_cod", "activa", "cod"),)


class PeriodoORM(Base):
    __tablename__ = "periodo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(Text, nullable=False, default="ABIERTO")
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    cerrado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("anio", "mes", name="uq_periodo_anio_mes"),
        CheckConstraint("mes BETWEEN 1 AND 12", name="ck_periodo_mes"),
        CheckConstraint("estado IN ('ABIERTO','CERRADO')", name="ck_periodo_estado"),
    )


class AsignacionORM(Base):
    __tablename__ = "asignacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    periodo_id: Mapped[int] = mapped_column(
        ForeignKey("periodo.id", ondelete="CASCADE"), nullable=False
    )
    trabajador_ide: Mapped[int] = mapped_column(
        ForeignKey("trabajador.ide"), nullable=False
    )
    obra_ide: Mapped[int] = mapped_column(ForeignKey("obra.ide"), nullable=False)
    es_postventa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    porcentaje: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    actualizado_por: Mapped[str] = mapped_column(Text, nullable=False, default="local")

    __table_args__ = (
        UniqueConstraint(
            "periodo_id",
            "trabajador_ide",
            "obra_ide",
            "es_postventa",
            name="uq_asignacion_linea",
        ),
        CheckConstraint(
            "porcentaje > 0 AND porcentaje <= 100", name="ck_asignacion_pct"
        ),
        Index("ix_asignacion_periodo_trab", "periodo_id", "trabajador_ide"),
    )


class EventoORM(Base):
    __tablename__ = "evento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    periodo_id: Mapped[int] = mapped_column(
        ForeignKey("periodo.id", ondelete="CASCADE"), nullable=False
    )
    trabajador_ide: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    usuario: Mapped[str] = mapped_column(Text, nullable=False, default="local")
    snapshot_antes: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    snapshot_despues: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    deshecho: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index(
            "ix_evento_periodo_trab_id",
            "periodo_id",
            "trabajador_ide",
            "id",
        ),
    )
