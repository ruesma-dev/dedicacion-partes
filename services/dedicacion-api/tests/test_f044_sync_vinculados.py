# tests/test_f044_sync_vinculados.py
"""F-044 · el vínculo en la base y en el sync de maestros.

- R5 (T2): `recurso_vinculado` y `asignacion_vinculado` en el ORM (las crea
  `create_all`; ningún DDL a mano). El repositorio guarda el vínculo: el que
  sale del sync o pierde su trabajador queda inactivo y no se borra.
- R30 (T2): la traza por asignación y vinculado (estado, parte, motivo y
  `hmores.ide`) es un `INSERT … ON CONFLICT` del ORM sobre la pareja única.
- R1, R3, R5 (T3): `sync.vinculados` en `config.yaml`, `FetchVinculadosStep`
  (SQL parametrizada con el código del campo, alias exactos, `truncated` ⇒
  el sync falla sin persistir), `UpsertVinculadosStep` y el bloque
  `vinculados` del preview (contadores y códigos, sin nombres).

Sesiones y Sigrid dobles: sin red ni BBDD.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from domain.models import RecursoVinculado
from domain.vinculados import vincular
from infrastructure.db.orm_models import (
    AsignacionVinculadoORM,
    Base,
    RecursoVinculadoORM,
)
from infrastructure.db.repositories import (
    PgVinculadoRepository,
    upsert_asignacion_vinculado,
)
from sqlalchemy.dialects import postgresql


def _v(ide: int, principal: int | None, tipo: str = "TF",
       fecha_baja: int | None = None, cod: str | None = None
       ) -> RecursoVinculado:
    return RecursoVinculado(
        ide=ide, principal_ide=principal, cod=cod or f"TF-{ide}",
        descripcion=f"CONSUMOS {ide}", empresa=1, fecha_baja=fecha_baja,
        tipo=tipo, tipo_res=f"TIPO {tipo}", horide=901)


class _Resultado:
    def __init__(self, filas: list[Any]) -> None:
        self._filas = filas

    def all(self) -> list[Any]:
        return list(self._filas)


class _SesionRepo:
    """`scalars()` devuelve las filas previas; `add` las apunta."""

    def __init__(self, previas: list[Any] | None = None) -> None:
        self.previas = list(previas or [])
        self.anadidas: list[Any] = []
        self.borradas: list[Any] = []

    def scalars(self, _sentencia: Any) -> _Resultado:
        return _Resultado(self.previas)

    def add(self, orm: Any) -> None:
        self.anadidas.append(orm)

    def delete(self, orm: Any) -> None:
        self.borradas.append(orm)


def _previo(ide: int, trabajador: int | None, **kw: Any) -> RecursoVinculadoORM:
    base: dict[str, Any] = {
        "ide": ide, "trabajador_ide": trabajador, "tipo": "TF",
        "tipo_res": "TIPO TF", "cod": f"TF-{ide}",
        "descripcion": f"CONSUMOS {ide}", "empresa_recurso": 1,
        "fecha_baja_recurso": None, "horide": 901, "activo": True,
        "estado_vinculo": "vinculado"}
    base.update(kw)
    return RecursoVinculadoORM(**base)


def _sql(stmt) -> str:
    """SQL en una línea; sin el `RETURNING id` que el dialecto añade al
    compilar un INSERT de una tabla con clave autoincremental."""
    sql = " ".join(str(stmt.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True})).split())
    return sql.removesuffix(" RETURNING asignacion_vinculado.id")


# ================================ R5 ===================================== #
def test_f044_r5_las_tablas_salen_del_orm():
    tablas = Base.metadata.tables
    assert {"recurso_vinculado", "asignacion_vinculado"} <= set(tablas)
    rv = tablas["recurso_vinculado"].columns
    assert [c.name for c in rv] == [
        "ide", "trabajador_ide", "tipo", "tipo_res", "cod", "descripcion",
        "empresa_recurso", "fecha_baja_recurso", "horide", "activo",
        "estado_vinculo", "sincronizado_en"]
    assert rv["ide"].primary_key and rv["ide"].autoincrement is False
    assert rv["trabajador_ide"].nullable is True
    [fk] = rv["trabajador_ide"].foreign_keys
    assert fk.target_fullname == "trabajador.ide"


def test_f044_r5_asignacion_vinculado_unica_y_en_cascada():
    t = Base.metadata.tables["asignacion_vinculado"]
    assert [c.name for c in t.columns] == [
        "id", "asignacion_id", "vinculado_ide", "partida_ide", "partida_cod",
        "partida_res", "propuesta_ide", "propuesta_cod", "propuesta_res",
        "propuesta_metodo", "propuesta_origen", "sigrid_estado",
        "sigrid_motivo", "sigrid_parte", "sigrid_hmores_ide"]
    [fk_a] = t.columns["asignacion_id"].foreign_keys
    assert (fk_a.target_fullname, fk_a.ondelete) == ("asignacion.id",
                                                     "CASCADE")
    [fk_v] = t.columns["vinculado_ide"].foreign_keys
    assert fk_v.target_fullname == "recurso_vinculado.ide"
    unicas = [tuple(c.name for c in u.columns) for u in t.constraints
              if u.__class__.__name__ == "UniqueConstraint"]
    assert unicas == [("asignacion_id", "vinculado_ide")]
    assert t.columns["sigrid_motivo"].type.length == 300
    for c in t.columns:
        if c.name not in ("id", "asignacion_id", "vinculado_ide"):
            assert c.nullable and c.default is None, c.name


def test_f044_r5_alta_del_vinculado_con_su_trabajador():
    s = _SesionRepo()
    r = PgVinculadoRepository(s).sincronizar(  # type: ignore[arg-type]
        vincular([_v(10, 7)], {7}, set()))
    [orm] = s.anadidas
    assert (orm.ide, orm.trabajador_ide, orm.activo, orm.estado_vinculo,
            orm.tipo, orm.tipo_res, orm.cod, orm.horide) == (
        10, 7, True, "vinculado", "TF", "TIPO TF", "TF-10", 901)
    assert (r.recibidos, r.altas, r.actualizados, r.desactivados) == (
        1, 1, 0, 0)


def test_f044_r5_sin_campo_y_hacia_no_trabajador_se_guardan_inactivos():
    s = _SesionRepo()
    PgVinculadoRepository(s).sincronizar(  # type: ignore[arg-type]
        vincular([_v(10, None), _v(11, 555)], {7}, set()))
    assert [(o.ide, o.trabajador_ide, o.activo, o.estado_vinculo)
            for o in s.anadidas] == [(10, None, False, "sin_campo"),
                                     (11, None, False, "no_trabajador")]


def test_f044_r5_el_excluido_no_se_guarda():
    s = _SesionRepo()
    r = PgVinculadoRepository(s).sincronizar(  # type: ignore[arg-type]
        vincular([_v(10, 7, tipo="VP")], {7}, {"VP"}))
    assert s.anadidas == [] and r.recibidos == 0


def test_f044_r5_el_que_pierde_su_trabajador_queda_inactivo():
    previo = _previo(10, 7)
    s = _SesionRepo([previo])
    r = PgVinculadoRepository(s).sincronizar(  # type: ignore[arg-type]
        vincular([_v(10, 8)], {7}, set()))
    assert (previo.trabajador_ide, previo.activo, previo.estado_vinculo) == (
        None, False, "no_trabajador")
    assert s.borradas == [] and s.anadidas == []
    assert (r.recibidos, r.altas, r.actualizados, r.desactivados) == (
        1, 0, 1, 1)


def test_f044_r5_el_que_sale_del_sync_queda_inactivo_sin_borrarse():
    previo, otro = _previo(10, 7), _previo(12, 7, activo=False)
    s = _SesionRepo([previo, otro])
    r = PgVinculadoRepository(s).sincronizar(  # type: ignore[arg-type]
        vincular([], {7}, set()))
    assert (previo.activo, previo.trabajador_ide,
            previo.estado_vinculo) == (False, 7, "vinculado")
    assert s.borradas == []
    assert (r.recibidos, r.desactivados) == (0, 1)


def test_f044_r5_actualiza_lo_que_cambia_y_reactiva():
    previo = _previo(10, 7, activo=False, cod="VIEJO",
                     fecha_baja_recurso=20250101,
                     estado_vinculo="sin_campo", trabajador_ide=None)
    s = _SesionRepo([previo])
    r = PgVinculadoRepository(s).sincronizar(  # type: ignore[arg-type]
        vincular([_v(10, 7, fecha_baja=20261231)], {7}, set()))
    assert (previo.cod, previo.fecha_baja_recurso, previo.activo,
            previo.trabajador_ide, previo.estado_vinculo) == (
        "TF-10", 20261231, True, 7, "vinculado")
    assert (r.altas, r.actualizados, r.desactivados) == (0, 1, 0)


def test_f044_r5_sin_cambios_no_cuenta_actualizado():
    previo = _previo(10, 7)
    s = _SesionRepo([previo])
    r = PgVinculadoRepository(s).sincronizar(  # type: ignore[arg-type]
        vincular([_v(10, 7)], {7}, set()))
    assert (r.recibidos, r.altas, r.actualizados, r.desactivados) == (
        1, 0, 0, 0)


@pytest.mark.parametrize("campo, valor", [
    ("tipo", "CO"), ("tipo_res", "OTRO"), ("descripcion", "X"),
    ("empresa_recurso", 2), ("horide", 5)])
def test_f044_r5_cada_campo_cuenta_como_cambio(campo, valor):
    previo = _previo(10, 7, **{campo: valor})
    r = PgVinculadoRepository(_SesionRepo([previo])).sincronizar(  # type: ignore[arg-type]
        vincular([_v(10, 7)], {7}, set()))
    assert r.actualizados == 1
    assert getattr(previo, campo) == getattr(_previo(10, 7), campo)


# ================================ R30 ==================================== #
def test_f044_r30_traza_es_un_upsert_sobre_la_pareja():
    stmt = upsert_asignacion_vinculado(
        41, 10, {"sigrid_estado": "registrado", "sigrid_parte": "PT26/00012",
                 "sigrid_motivo": None, "sigrid_hmores_ide": 990011})
    sql = _sql(stmt)
    assert sql.startswith(
        "INSERT INTO asignacion_vinculado (asignacion_id, vinculado_ide, "
        "sigrid_estado, sigrid_motivo, sigrid_parte, sigrid_hmores_ide) "
        "VALUES (41, 10, 'registrado', NULL, 'PT26/00012', 990011) "
        "ON CONFLICT (asignacion_id, vinculado_ide) DO UPDATE SET ")
    for trozo in ("sigrid_estado = excluded.sigrid_estado",
                  "sigrid_parte = excluded.sigrid_parte",
                  "sigrid_motivo = excluded.sigrid_motivo",
                  "sigrid_hmores_ide = excluded.sigrid_hmores_ide"):
        assert trozo in sql, trozo
    assert " WHERE " not in sql


def test_f044_r30_el_motivo_se_corta_a_300():
    stmt = upsert_asignacion_vinculado(41, 10, {"sigrid_motivo": "x" * 400})
    params = stmt.compile(dialect=postgresql.dialect()).params
    assert params["sigrid_motivo"] == "x" * 300


def test_f044_r30_con_condicion_solo_actualiza_si_se_cumple():
    stmt = upsert_asignacion_vinculado(
        41, 10, {"propuesta_ide": 5},
        donde=AsignacionVinculadoORM.partida_ide.is_(None))
    assert _sql(stmt).endswith(
        "DO UPDATE SET propuesta_ide = excluded.propuesta_ide "
        "WHERE asignacion_vinculado.partida_ide IS NULL")


def test_f044_r30_no_admite_columnas_que_no_son_suyas():
    with pytest.raises(ValueError):
        upsert_asignacion_vinculado(41, 10, {"porcentaje": 5})
    with pytest.raises(ValueError):
        upsert_asignacion_vinculado(41, 10, {})


def test_f044_r30_la_asignacion_puede_ser_una_subconsulta():
    """Para guardar sin conocer el `id` (selector y cola): la asignación se
    busca por periodo, trabajador y línea en la misma sentencia."""
    from infrastructure.db.repositories import id_de_asignacion
    stmt = upsert_asignacion_vinculado(
        id_de_asignacion(3, 14, (100, False)), 10, {"propuesta_ide": 5})
    sql = _sql(stmt)
    assert sql.startswith(
        "INSERT INTO asignacion_vinculado (asignacion_id, vinculado_ide, "
        "propuesta_ide) SELECT asignacion.id, 10 AS anon_1, 5 AS anon_2 "
        "FROM asignacion WHERE ")
    for trozo in ("asignacion.periodo_id = 3", "asignacion.trabajador_ide = 14",
                  "asignacion.obra_ide = 100",
                  "asignacion.es_postventa = false"):
        assert trozo in sql, trozo


def test_f044_r30_el_repositorio_no_borra_nunca():
    """`sincronizar` no llama a `delete` ni con todo fuera del sync."""
    s = _SesionRepo([_previo(i, 7) for i in range(10, 15)])
    PgVinculadoRepository(s).sincronizar(  # type: ignore[arg-type]
        vincular([], set(), set()))
    assert s.borradas == []
    assert all(not o.activo for o in s.previas)


def test_f044_r5_el_uow_expone_el_repositorio():
    from infrastructure.db.repositories import SqlAlchemyUnitOfWork
    uow = SqlAlchemyUnitOfWork(  # type: ignore[arg-type]
        lambda: SimpleNamespace(close=lambda: None))
    with uow as u:
        assert isinstance(u.vinculados, PgVinculadoRepository)
