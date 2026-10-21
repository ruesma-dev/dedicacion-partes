# infrastructure/db/repositories.py
"""Implementación PostgreSQL de los puertos de persistencia.

Todos los repositorios comparten la misma Session; la frontera
transaccional la marca SqlAlchemyUnitOfWork (commit/rollback único).
"""
from __future__ import annotations

import dataclasses
import logging
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, distinct, func, select, update
from sqlalchemy.orm import Session, sessionmaker

from domain.empresas import empresa_de_baja
from domain.incidencias import letra_y_nombre
from domain.normalizacion import texto_o_none as _texto
from domain.vigencia import vigente_en
from domain.models import (
    Empresa,
    EstadoPeriodo,
    EventoPendiente,
    Incidencia,
    Linea,
    Obra,
    Periodo,
    ResultadoSyncMaestro,
    TipoEvento,
    TipoIncidencia,
    Trabajador,
)
from infrastructure.db.orm_models import (
    AsignacionORM,
    EmpresaORM,
    EventoORM,
    IncidenciaORM,
    ObraORM,
    PeriodoORM,
    TipoIncidenciaORM,
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
                        empresa=_entero(fila.get("empresa")),
                        fecha_baja=_fecha(fila.get("fecha_baja")),
                    )
                )
                altas += 1
            else:
                cambio = (
                    existente.nombre != (_texto(fila.get("nombre")) or existente.nombre)
                    or existente.dni != _texto(fila.get("dni"))
                    or existente.categoria != _texto(fila.get("categoria"))
                    or existente.cod != _texto(fila.get("cod"))
                    or existente.empresa != _entero(fila.get("empresa"))
                    or existente.fecha_baja != _fecha(fila.get("fecha_baja"))
                    or not existente.activo
                )
                existente.cod = _texto(fila.get("cod"))
                existente.nombre = _texto(fila.get("nombre")) or existente.nombre
                existente.dni = _texto(fila.get("dni"))
                existente.categoria = _texto(fila.get("categoria"))
                existente.empresa = _entero(fila.get("empresa"))
                existente.fecha_baja = _fecha(fila.get("fecha_baja"))
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
        """Vigentes en el mes del periodo más los que tienen líneas en él,
        con `activo` = «vigente en ese mes» (F-026 R15,
        `domain.vigencia.vigente_en`). Cuadrante, resumen, copia y export
        del mes salen de aquí, así que todos pasan a ser por mes."""
        periodo = self._s.get(PeriodoORM, periodo_id)
        con_lineas = select(AsignacionORM.trabajador_ide).where(
            AsignacionORM.periodo_id == periodo_id
        )
        ides_con_lineas = set(self._s.scalars(con_lineas).all())
        stmt = (
            select(TrabajadorORM)
            .where(TrabajadorORM.activo.is_(True) | TrabajadorORM.ide.in_(con_lineas))
            .order_by(TrabajadorORM.nombre)
        )
        listados = []
        for orm in self._s.scalars(stmt).all():
            vigente = vigente_en(orm.activo, orm.fecha_baja, periodo.anio, periodo.mes)
            if vigente or orm.ide in ides_con_lineas:
                listados.append(
                    dataclasses.replace(_a_trabajador(orm), activo=vigente)
                )
        return listados

    def obtener(self, ide: int) -> Trabajador | None:
        orm = self._s.get(TrabajadorORM, ide)
        return _a_trabajador(orm) if orm else None

    def empresas_activas(self) -> set[int]:
        """Empresas con al menos un trabajador activo (F-024, R1)."""
        stmt = select(distinct(TrabajadorORM.empresa)).where(
            TrabajadorORM.activo.is_(True), TrabajadorORM.empresa.is_not(None)
        )
        return set(self._s.scalars(stmt).all())


# ----------------------------------------------------------------------
# Obras
# ----------------------------------------------------------------------
#: Columnas de la entrada VAR que `sincronizar` copia tal cual de la fila
#: (F-039, R13, docs/ARCHITECTURE.md#regla-var).
_REGISTRO_VAR = ("registro_obra_ide", "registro_obra_cod", "registro_paride")


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
            # Las dos marcas las decide `depurar_obras` (F-025, R13):
            # `activa` por estado y `admite_postventa` por el universo.
            activa = fila["activa"]
            admite = fila["admite_postventa"]
            # Obra y partida de registro de una entrada VAR (F-039, R13);
            # `None` en las obras normales, que no traen las claves.
            registro = {campo: fila.get(campo) for campo in _REGISTRO_VAR}
            existente = actuales.get(ide)
            if existente is None:
                self._s.add(
                    ObraORM(
                        ide=ide,
                        cod=cod,
                        descripcion=_texto(fila.get("descripcion")) or "",
                        estado_sigrid=_texto(fila.get("estado_sigrid")),
                        activa=activa,
                        empresa=_entero(fila.get("empresa")),
                        admite_postventa=admite,
                        **registro,
                    )
                )
                altas += 1
            else:
                cambio = (
                    existente.cod != cod
                    or existente.descripcion != (_texto(fila.get("descripcion")) or "")
                    or existente.estado_sigrid != _texto(fila.get("estado_sigrid"))
                    or existente.empresa != _entero(fila.get("empresa"))
                    or existente.activa != activa
                    or existente.admite_postventa != admite
                    or any(getattr(existente, campo) != valor
                           for campo, valor in registro.items())
                )
                existente.cod = cod
                existente.descripcion = _texto(fila.get("descripcion")) or ""
                existente.estado_sigrid = _texto(fila.get("estado_sigrid"))
                existente.empresa = _entero(fila.get("empresa"))
                existente.activa = activa
                existente.admite_postventa = admite
                for campo, valor in registro.items():
                    setattr(existente, campo, valor)
                if cambio:
                    actualizados += 1
        # La que no llega (excluida por estado y fuera del universo) se queda
        # sin ninguna marca, como antes de F-025 (R14).
        desactivadas = 0
        for ide, orm in actuales.items():
            if ide not in recibidos and (orm.activa or orm.admite_postventa):
                orm.activa = False
                orm.admite_postventa = False
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
        # Ofrecidas: activas (normal), las que admiten postventa (`Postv-`,
        # también cerradas) y las usadas en el periodo (F-025, R17).
        stmt = (
            select(ObraORM)
            .where(
                ObraORM.activa.is_(True)
                | ObraORM.admite_postventa.is_(True)
                | ObraORM.ide.in_(usadas)
            )
            .order_by(ObraORM.cod)
        )
        return [_a_obra(o) for o in self._s.scalars(stmt).all()]

    def existen(self, ides: set[int]) -> set[int]:
        if not ides:
            return set()
        stmt = select(ObraORM.ide).where(ObraORM.ide.in_(ides))
        return set(self._s.scalars(stmt).all())

    def modos_ofrecibles(self, ides: set[int]) -> dict[int, tuple[bool, bool]]:
        """(activa, admite_postventa) de cada obra de `ides` (F-025, R20)."""
        if not ides:
            return {}
        stmt = select(
            ObraORM.ide, ObraORM.activa, ObraORM.admite_postventa
        ).where(ObraORM.ide.in_(ides))
        return {ide: (activa, admite)
                for ide, activa, admite in self._s.execute(stmt).all()}


# ----------------------------------------------------------------------
# Empresas (catálogo `auxemp` de Sigrid, F-032)
# ----------------------------------------------------------------------
class PgEmpresaRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def sincronizar(self, filas: list[dict[str, Any]]) -> ResultadoSyncMaestro:
        """Upsert por `numemp`. Idempotente: las mismas filas dos veces no
        cambian nada. Una empresa que deja de llegar NO se borra: su nombre
        sigue sirviendo para las fichas que la referencian."""
        actuales = {e.numemp: e for e in self._s.scalars(select(EmpresaORM)).all()}
        recibidos: set[int] = set()
        altas = actualizados = 0
        for fila in filas:
            numemp = _entero(fila.get("numemp"))
            if numemp is None:
                logger.warning("Empresa sin numemp en auxemp; omitida: %s", fila)
                continue
            recibidos.add(numemp)
            valores = {
                "cod": _texto(fila.get("cod")),
                "nombre": _texto(fila.get("nombre")),
                "fecbaj": _entero(fila.get("fecbaj")),
                "desact": _entero(fila.get("desact")),
            }
            existente = actuales.get(numemp)
            if existente is None:
                nueva = EmpresaORM(numemp=numemp, **valores)
                self._s.add(nueva)
                # Si `numemp` llegara repetido, la segunda fila actualiza la
                # misma alta en vez de crear otra con la misma clave.
                actuales[numemp] = nueva
                altas += 1
                continue
            cambio = any(getattr(existente, k) != v for k, v in valores.items())
            for campo, valor in valores.items():
                setattr(existente, campo, valor)
            if cambio:
                actualizados += 1
        return ResultadoSyncMaestro(
            recibidos=len(recibidos),
            altas=altas,
            actualizados=actualizados,
            desactivados=0,
        )

    def listar(self) -> list[Empresa]:
        stmt = select(EmpresaORM).order_by(EmpresaORM.numemp)
        return [_a_empresa(e) for e in self._s.scalars(stmt).all()]


# ----------------------------------------------------------------------
# Tipos de incidencia (catálogo `auxhor` de Sigrid, F-030)
# ----------------------------------------------------------------------
class PgTipoIncidenciaRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def sincronizar(self, filas: list[dict[str, Any]]) -> ResultadoSyncMaestro:
        """Upsert por `ide` de `auxhor` (R3). Letra y nombre, de
        `letra_y_nombre` (R4); `activa` = sin fecha de baja (R5). El que deja
        de llegar queda `activa = false`: no se borra, sus incidencias ya
        guardadas lo siguen nombrando."""
        actuales = {t.ide: t for t in self._s.scalars(select(TipoIncidenciaORM)).all()}
        recibidos: set[int] = set()
        nuevas: set[int] = set()
        altas = actualizados = 0
        for fila in filas:
            ide = _entero(fila.get("ide"))
            codigo = _texto(fila.get("cod"))
            if ide is None or codigo is None:
                logger.warning("Incidencia de auxhor sin ide o código; omitida: %s",
                               fila)
                continue
            recibidos.add(ide)
            letra, nombre = letra_y_nombre(fila.get("res"), codigo)
            valores = {"codigo": codigo, "letra": letra, "nombre": nombre,
                       "activa": _fecha(fila.get("fecbaj")) is None}
            existente = actuales.get(ide)
            if existente is None:
                nueva = TipoIncidenciaORM(ide=ide, **valores)
                self._s.add(nueva)
                # Un `ide` repetido actualiza la misma alta (la última manda).
                actuales[ide] = nueva
                nuevas.add(ide)
                altas += 1
                continue
            cambio = any(getattr(existente, k) != v for k, v in valores.items())
            for campo, valor in valores.items():
                setattr(existente, campo, valor)
            if cambio and ide not in nuevas:
                actualizados += 1
        desactivados = 0
        for ide, orm in actuales.items():
            if ide not in recibidos and orm.activa:
                orm.activa = False
                desactivados += 1
        return ResultadoSyncMaestro(
            recibidos=len(recibidos),
            altas=altas,
            actualizados=actualizados,
            desactivados=desactivados,
        )

    def activos(self) -> list[TipoIncidencia]:
        """Los activos, por letra y código (R6)."""
        stmt = (
            select(TipoIncidenciaORM)
            .where(TipoIncidenciaORM.activa.is_(True))
            .order_by(TipoIncidenciaORM.letra, TipoIncidenciaORM.codigo)
        )
        return [_a_tipo_incidencia(t) for t in self._s.scalars(stmt).all()]


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
        return [_a_linea_con_partida(a, o)
                for a, o in self._s.execute(stmt).all()]

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
                _a_linea_con_partida(asignacion, obra)
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
                    partida_ide=linea.partida_ide,
                    partida_cod=linea.partida_cod,
                    partida_res=linea.partida_res,
                    propuesta_ide=linea.propuesta_ide,
                    propuesta_cod=linea.propuesta_cod,
                    propuesta_res=linea.propuesta_res,
                    propuesta_metodo=linea.propuesta_metodo,
                    propuesta_origen=linea.propuesta_origen,
                )
            )
        self._s.flush()

    def guardar_propuesta(
        self,
        periodo_id: int,
        trabajador_ide: int,
        clave: tuple[int, bool],
        propuesta: dict[str, Any],
        *,
        solo_si_vacia: bool = False,
    ) -> bool:
        """F-055 (R14, R15, R31): guarda la propuesta del transfer
        (`{paride, cod, res, metodo, origen}`) en la línea `clave` (obra,
        postventa) SOLO si sigue sin elegida y, con `solo_si_vacia`, sin
        propuesta. Un `UPDATE` condicional del ORM: no pisa lo que otro haya
        puesto entre medias. Devuelve si la guardó. Sin evento."""
        obra_ide, es_postventa = clave
        condiciones = [
            AsignacionORM.periodo_id == periodo_id,
            AsignacionORM.trabajador_ide == trabajador_ide,
            AsignacionORM.obra_ide == obra_ide,
            AsignacionORM.es_postventa == bool(es_postventa),
            AsignacionORM.partida_ide.is_(None),
        ]
        if solo_si_vacia:
            condiciones.append(AsignacionORM.propuesta_ide.is_(None))
        r = self._s.execute(
            update(AsignacionORM).where(*condiciones).values(
                propuesta_ide=propuesta["paride"],
                propuesta_cod=propuesta["cod"],
                propuesta_res=propuesta["res"],
                propuesta_metodo=propuesta["metodo"],
                propuesta_origen=propuesta["origen"],
            )
        )
        return bool(r.rowcount)


# ----------------------------------------------------------------------
# Incidencias (F-030)
# ----------------------------------------------------------------------
def _consulta_incidencias(periodo_id: int) -> Any:
    """Las incidencias del periodo con su obra y, si el código sigue en el
    catálogo, su letra y nombre (`LEFT JOIN`: una incidencia guardada no
    desaparece porque su código deje de leerse)."""
    return (
        select(IncidenciaORM, ObraORM.cod, ObraORM.descripcion,
               TipoIncidenciaORM.letra, TipoIncidenciaORM.nombre)
        .join(ObraORM, ObraORM.ide == IncidenciaORM.obra_ide)
        .outerjoin(TipoIncidenciaORM,
                   TipoIncidenciaORM.codigo == IncidenciaORM.codigo)
        .where(IncidenciaORM.periodo_id == periodo_id)
    )


_ORDEN_INCIDENCIAS = (IncidenciaORM.trabajador_ide, IncidenciaORM.dia_desde,
                      IncidenciaORM.id)


class PgIncidenciaRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def de_periodo(self, periodo_id: int) -> dict[int, list[Incidencia]]:
        stmt = _consulta_incidencias(periodo_id).order_by(*_ORDEN_INCIDENCIAS)
        resultado: dict[int, list[Incidencia]] = {}
        for fila in self._s.execute(stmt).all():
            resultado.setdefault(fila[0].trabajador_ide, []).append(
                _a_incidencia(*fila))
        return resultado

    def de_trabajador(self, periodo_id: int,
                      trabajador_ide: int) -> list[Incidencia]:
        stmt = (_consulta_incidencias(periodo_id)
                .where(IncidenciaORM.trabajador_ide == trabajador_ide)
                .order_by(*_ORDEN_INCIDENCIAS))
        return [_a_incidencia(*fila) for fila in self._s.execute(stmt).all()]


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
    ) -> EventoPendiente | None:
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
        if orm is None:
            return None
        return EventoPendiente(id=orm.id, usuario=orm.usuario,
                               snapshot_antes=orm.snapshot_antes)

    def marcar_deshecho(self, evento_id: int) -> None:
        self._s.execute(
            update(EventoORM).where(EventoORM.id == evento_id).values(deshecho=True)
        )

    def autores_ultimo_pendiente(self, periodo_id: int) -> dict[int, str]:
        """Autor del ÚLTIMO evento no deshecho de cada trabajador del
        periodo, en una sola consulta (F-027): el último es el de mayor `id`
        (el mismo orden que `ultimo_pendiente`), no «alguno pendiente»."""
        ultimos = (
            select(func.max(EventoORM.id))
            .where(
                EventoORM.periodo_id == periodo_id, EventoORM.deshecho.is_(False)
            )
            .group_by(EventoORM.trabajador_ide)
        )
        stmt = select(EventoORM.trabajador_ide, EventoORM.usuario).where(
            EventoORM.id.in_(ultimos)
        )
        return {ide: usuario for ide, usuario in self._s.execute(stmt).all()}


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
        self.empresas = PgEmpresaRepository(s)
        self.tipos_incidencia = PgTipoIncidenciaRepository(s)
        self.periodos = PgPeriodoRepository(s)
        self.asignaciones = PgAsignacionRepository(s)
        self.incidencias = PgIncidenciaRepository(s)
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
def _entero(valor: Any) -> int | None:
    """Entero de Sigrid (p. ej. `con.emp`) o None si viene NULL."""
    return None if valor is None else int(valor)


def _fecha(valor: Any) -> int | None:
    """Fecha entera de Sigrid (AAAAMMDD) con 0 como «sin fecha» (None)."""
    return _entero(valor) or None


def _a_empresa(orm: EmpresaORM) -> Empresa:
    return Empresa(
        numero=orm.numemp,
        nombre=orm.nombre,
        de_baja=empresa_de_baja(orm.fecbaj, orm.desact),
    )


def _a_tipo_incidencia(orm: TipoIncidenciaORM) -> TipoIncidencia:
    return TipoIncidencia(ide=orm.ide, codigo=orm.codigo, letra=orm.letra,
                          nombre=orm.nombre, activa=orm.activa)


def _a_incidencia(orm: IncidenciaORM, obra_cod: str, obra_descripcion: str,
                  letra: str | None, nombre: str | None) -> Incidencia:
    """Sin el código en el catálogo, la letra de `letra_y_nombre` (el código
    sin `CI`) y sin nombre."""
    if letra is None:
        letra, nombre = letra_y_nombre(None, orm.codigo)
    return Incidencia(
        obra_ide=orm.obra_ide, codigo=orm.codigo, dia_desde=orm.dia_desde,
        dia_hasta=orm.dia_hasta, id=orm.id, obra_cod=obra_cod,
        obra_descripcion=obra_descripcion, letra=letra, nombre=nombre or "",
        sigrid_estado=orm.sigrid_estado, sigrid_parte_cod=orm.sigrid_parte_cod,
        sigrid_motivo=orm.sigrid_motivo)


def _a_trabajador(orm: TrabajadorORM) -> Trabajador:
    return Trabajador(
        ide=orm.ide,
        cod=orm.cod,
        nombre=orm.nombre,
        dni=orm.dni,
        categoria=orm.categoria,
        activo=orm.activo,
        empresa=orm.empresa,
        fecha_baja=orm.fecha_baja,
    )


def _a_obra(orm: ObraORM) -> Obra:
    return Obra(
        ide=orm.ide,
        cod=orm.cod,
        descripcion=orm.descripcion,
        estado_sigrid=orm.estado_sigrid,
        activa=orm.activa,
        empresa=orm.empresa,
        admite_postventa=orm.admite_postventa,
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
        obra_empresa=o.empresa,
        obra_admite_postventa=o.admite_postventa,
    )


def _a_linea_con_partida(a: AsignacionORM, o: ObraORM) -> Linea:
    """`_a_linea` más la partida elegida de la asignación y si es fija (la
    obra es una entrada VAR, `registro_paride` no nulo) (F-050, R12, R18)."""
    return dataclasses.replace(
        _a_linea(a, o),
        partida_ide=a.partida_ide,
        partida_cod=a.partida_cod,
        partida_res=a.partida_res,
        partida_fija=o.registro_paride is not None,
        propuesta_ide=a.propuesta_ide,
        propuesta_cod=a.propuesta_cod,
        propuesta_res=a.propuesta_res,
        propuesta_metodo=a.propuesta_metodo,
        propuesta_origen=a.propuesta_origen,
    )
