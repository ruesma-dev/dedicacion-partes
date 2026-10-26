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


# ============================ T3: el sync ================================= #
def _fila(ide: int, principal: int | None, tipo: str = "TF",
          fecbaj: int | None = 0, cod: str | None = None) -> dict[str, Any]:
    """Una fila de la consulta de `sync.vinculados` (alias de design §7.1)."""
    return {"ide": ide, "principal_ide": principal, "cod": cod or f"TF-{ide}",
            "descripcion": f" CONSUMOS PEPE {ide} ", "empresa": 1,
            "fecbaj": fecbaj, "tipo": tipo, "tipo_res": " TELEFONO ",
            "horide": 901}


def _emp(ide: int) -> dict[str, Any]:
    return {"ide": ide, "cod": f"E{ide}", "nombre": f"Persona {ide}",
            "dni": None, "empresa": 1, "categoria": "Técnico",
            "estado_recurso": "1", "fecha_baja": None, "baja_laboral": 0,
            "cod_hora_mes": "MENC", "importe_mes": 1}


SQL_EMP = "SELECT ... FROM dbo.emp"
SQL_VIN = "SELECT ... FROM conext x WHERE RTRIM(x.cod) = ?"


class _SigridVin:
    """Empleados para cualquier consulta salvo la de vinculados y la de
    obras (por su texto); apunta cada lectura con sus parámetros."""

    def __init__(self, vinculados: list[dict[str, Any]],
                 empleados: list[dict[str, Any]] | None = None,
                 fallo: Exception | None = None) -> None:
        self.vinculados = vinculados
        self.empleados = [_emp(7), _emp(8)] if empleados is None else empleados
        self.fallo = fallo
        self.leidas: list[tuple[str, list[Any] | None]] = []

    def leer(self, sql: str, parametros: list[Any] | None = None
             ) -> list[dict[str, Any]]:
        self.leidas.append((sql, parametros))
        if "conext" in sql:
            if self.fallo is not None:
                raise self.fallo
            return [dict(f) for f in self.vinculados]
        if "dbo.obr" in sql:
            return [{"ide": 70, "cod": "0070", "empresa": 1,
                     "descripcion": "OBRA", "estado_sigrid": "En curso"}]
        if "dbo.aux" in sql:
            return []
        return [dict(f) for f in self.empleados]


def _cfg(**kw: Any) -> Any:
    from application.sync_pipeline import ConfigVinculados

    base = {"campo": "5", "desde": "2026-10", "tipos_excluidos": ["VP"],
            "sql": SQL_VIN}
    base.update(kw)
    return ConfigVinculados.desde_config(base)


class _RepoVin:
    def __init__(self) -> None:
        self.recibido: Any = None

    def sincronizar(self, resultado: Any) -> Any:
        from domain.models import ResultadoSyncMaestro

        self.recibido = resultado
        return ResultadoSyncMaestro(recibidos=len(resultado.vinculos),
                                    altas=len(resultado.vinculos))


class _RepoEmp:
    def __init__(self) -> None:
        self.recibido: list[dict[str, Any]] | None = None

    def sincronizar(self, filas: list[dict[str, Any]]) -> Any:
        from domain.models import ResultadoSyncMaestro

        self.recibido = filas
        return ResultadoSyncMaestro(recibidos=len(filas))


class _UowVin:
    def __init__(self) -> None:
        self.trabajadores = _RepoEmp()
        self.obras = _RepoEmp()
        self.vinculados = _RepoVin()
        self.periodos = SimpleNamespace(listar=list)
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


def _pipeline(sigrid: _SigridVin, cfg: Any = None) -> Any:
    from application import sync_pipeline as sp

    from tests.conftest import UniversoFalso
    return sp.SyncMaestrosPipeline([
        sp.FetchEmpleadosStep(sigrid, SQL_EMP),
        sp.FetchObrasStep(sigrid, "SELECT ... FROM dbo.obr",
                          universo=UniversoFalso(), empresa_obras=1),
        sp.FetchVinculadosStep(sigrid, cfg or _cfg()),
        sp.UpsertTrabajadoresStep(),
        sp.UpsertObrasStep(),
        sp.UpsertVinculadosStep(),
    ])


def _alias(sql: str) -> set[str]:
    import re
    return set(re.findall(r"\bAS\s+([a-z_]+)\b", sql))


# ================================ R1 ===================================== #
def test_f044_r1_config_versionada():
    from application.sync_pipeline import COLUMNAS_VINCULADOS
    from config.settings import cargar_config

    cfg = cargar_config()["sync"]["vinculados"]
    assert (cfg["campo"], cfg["desde"], cfg["tipos_excluidos"]) == (
        "5", "2026-10", ["VP"])
    sql = cfg["sql"]
    assert sql.count("?") == 1
    assert _alias(sql) == set(COLUMNAS_VINCULADOS)
    assert frozenset({
        "ide", "principal_ide", "cod", "descripcion", "empresa", "fecbaj",
        "tipo", "tipo_res", "horide"}) == COLUMNAS_VINCULADOS
    plano = " ".join(sql.split())
    for trozo in ("FROM dbo.conext x", "RTRIM(x.cod) = ?",
                  "RTRIM(x.camtab) = 'res'", "r.cla <> 1",
                  "LEFT JOIN dbo.auxrestip t ON t.ide = r.restipide",
                  "x.valn AS principal_ide", "r.horide AS horide"):
        assert trozo in plano, trozo
    assert "'5'" not in sql  # el código del campo va como parámetro
    _cfg(**cfg)  # la versionada se lee sin error


def test_f044_r1_config_se_lee_entera():
    c = _cfg(tipos_excluidos=[" vp ", "Co"])
    assert (c.campo, c.desde, c.tipos_excluidos, c.sql) == (
        "5", (2026, 10), frozenset({"VP", "CO"}), SQL_VIN)
    assert _cfg(tipos_excluidos=None).tipos_excluidos == frozenset()
    assert _cfg(campo=" 5 ").campo == "5"


@pytest.mark.parametrize("desde", ["2026", "2026-13", "2026-00", "x-10", "",
                                   None, "2026-1-1"])
def test_f044_r1_desde_mal_escrito_no_arranca(desde):
    with pytest.raises(ValueError, match=r"sync\.vinculados\.desde"):
        _cfg(desde=desde)


@pytest.mark.parametrize("falta", ["campo", "sql"])
@pytest.mark.parametrize("valor", [" ", None])
def test_f044_r1_sin_campo_o_sin_sql_no_arranca(falta, valor):
    from application.sync_pipeline import ConfigVinculados

    base = {"campo": "5", "desde": "2026-10", "sql": "SELECT 1"}
    base[falta] = valor
    with pytest.raises(ValueError, match=rf"sync\.vinculados\.{falta}"):
        ConfigVinculados.desde_config(base)


def test_f044_r1_el_step_lee_con_el_campo_como_parametro():
    from application.sync_pipeline import FetchVinculadosStep, SyncContext

    sigrid = _SigridVin([_fila(10, 7)])
    ctx = SyncContext(filas_empleados=[_emp(7)])
    FetchVinculadosStep(sigrid, _cfg(campo="5")).ejecutar(ctx, _UowVin())
    assert sigrid.leidas == [(SQL_VIN, ["5"])]
    assert ctx.vinculos is not None
    [(v, trabajador)] = ctx.vinculos.vinculos
    assert trabajador == 7
    assert v == RecursoVinculado(
        ide=10, principal_ide=7, cod="TF-10", descripcion="CONSUMOS PEPE 10",
        empresa=1, fecha_baja=None, tipo="TF", tipo_res="TELEFONO",
        horide=901)


def test_f044_r1_fila_a_recurso_con_baja_y_nulos():
    from application.sync_pipeline import fila_a_vinculado

    v = fila_a_vinculado({**_fila(10, None, fecbaj=20261015), "cod": "  ",
                          "horide": None, "empresa": None, "tipo": None})
    assert (v.principal_ide, v.fecha_baja, v.cod, v.horide, v.empresa,
            v.tipo) == (None, 20261015, None, None, None, None)
    assert fila_a_vinculado(_fila(10, "7")).principal_ide == 7  # type: ignore[arg-type]
    assert fila_a_vinculado(_fila(10, 7, fecbaj=None)).fecha_baja is None


def test_f044_r1_sin_columnas_el_sync_falla():
    from application.sync_pipeline import FetchVinculadosStep, SyncContext

    fila = {k: v for k, v in _fila(10, 7).items() if k != "principal_ide"}
    with pytest.raises(ValueError,
                       match=r"sync\.vinculados\.sql.*principal_ide"):
        FetchVinculadosStep(_SigridVin([fila]), _cfg()).ejecutar(
            SyncContext(filas_empleados=[_emp(7)]), _UowVin())


def test_f044_r1_el_cliente_manda_los_parametros(monkeypatch):
    from config.settings import Settings
    from infrastructure.sigrid import sigrid_client

    enviados: list[dict[str, Any]] = []

    class _Resp:
        status_code = 200
        text = ""

        def json(self) -> dict[str, Any]:
            return {"ok": True, "columns": ["ide"], "rows": [[1]]}

    def post(_url: str, json: dict[str, Any], **_k: Any) -> _Resp:
        enviados.append(json)
        return _Resp()

    monkeypatch.setattr(sigrid_client.httpx, "post", post)
    cliente = sigrid_client.SigridApiClient(Settings(
        _env_file=None, sigrid_api_base_url="http://x",
        sigrid_api_function_key="k"))
    assert cliente.leer("SELECT ? AS ide", ["5"]) == [{"ide": 1}]
    assert cliente.leer("SELECT 1 AS ide") == [{"ide": 1}]
    assert [e["parameters"] for e in enviados] == [["5"], []]


# ================================ R5 (sync) ============================== #
def test_f044_r5_el_sync_guarda_el_vinculo_de_los_trabajadores_leidos():
    sigrid = _SigridVin([_fila(10, 7), _fila(11, 8, tipo="CO"),
                         _fila(12, 999), _fila(13, None),
                         _fila(14, 7, tipo="VP")])
    uow = _UowVin()
    resultado = _pipeline(sigrid).ejecutar(uow)
    r = uow.vinculados.recibido
    assert [(v.ide, t) for v, t in r.vinculos] == [(10, 7), (11, 8)]
    assert [v.ide for v in r.hacia_no_trabajador] == [12]
    assert [v.ide for v in r.sin_campo] == [13]
    assert [v.ide for v in r.excluidos] == [14]
    assert uow.commits == 1
    assert resultado.vinculados.recibidos == 2


def test_f044_r5_los_trabajadores_son_los_que_guarda_el_sync():
    """El que apunta a un recurso que el sync de empleados descarta (sin
    código de hora mensual) no se vincula."""
    sin_mes = {**_emp(8), "cod_hora_mes": None}
    sigrid = _SigridVin([_fila(10, 7), _fila(11, 8)],
                        empleados=[_emp(7), sin_mes])
    uow = _UowVin()
    _pipeline(sigrid).ejecutar(uow)
    r = uow.vinculados.recibido
    assert [v.ide for v, _ in r.vinculos] == [10]
    assert [v.ide for v in r.hacia_no_trabajador] == [11]


def test_f044_r5_truncated_el_sync_falla_sin_persistir():
    from domain.errors import SigridError

    uow = _UowVin()
    sigrid = _SigridVin([_fila(10, 7)], fallo=SigridError("truncado"))
    with pytest.raises(SigridError, match="truncado"):
        _pipeline(sigrid).ejecutar(uow)
    assert uow.vinculados.recibido is None
    assert uow.trabajadores.recibido is None
    assert uow.commits == 0


def test_f044_r5_sin_los_pasos_el_resultado_queda_a_cero():
    from application import sync_pipeline as sp
    from domain.models import ResultadoSyncMaestro

    from tests.conftest import UniversoFalso
    sigrid = _SigridVin([_fila(10, 7)])
    resultado = sp.SyncMaestrosPipeline([
        sp.FetchEmpleadosStep(sigrid, SQL_EMP),
        sp.FetchObrasStep(sigrid, "SELECT ... FROM dbo.obr",
                          universo=UniversoFalso(), empresa_obras=1),
        sp.UpsertTrabajadoresStep(), sp.UpsertObrasStep(),
    ]).ejecutar(_UowVin())
    assert resultado.vinculados == ResultadoSyncMaestro()
    assert not any("conext" in sql for sql, _ in sigrid.leidas)


def test_f044_r5_upsert_sin_fetch_no_guarda_nada():
    from application.sync_pipeline import SyncContext, UpsertVinculadosStep

    uow = _UowVin()
    ctx = SyncContext()
    UpsertVinculadosStep().ejecutar(ctx, uow)
    assert uow.vinculados.recibido is None
    assert ctx.resultado_vinculados is None


# ================================ R3 (preview) =========================== #
def _preview(sigrid: _SigridVin, cfg: Any = "defecto", **kw: Any) -> Any:
    from application.use_cases import PreviewSync

    from tests.conftest import UniversoFalso
    return PreviewSync(sigrid, SQL_EMP, "SELECT ... FROM dbo.obr",
                       universo=UniversoFalso(), empresa_obras=1,
                       vinculados=_cfg() if cfg == "defecto" else cfg, **kw)


def test_f044_r3_preview_publica_contadores_y_codigos_sin_nombres():
    sigrid = _SigridVin([
        _fila(10, 7), _fila(11, 7, tipo="CO"), _fila(15, 8),
        _fila(12, 999, cod="TF-B"), _fila(16, 555, cod="TF-A"),
        _fila(13, None, cod="GA-1"), _fila(14, 7, tipo="VP"),
        _fila(17, 8, tipo="VP"), _fila(18, 8, tipo=None)])
    salida = _preview(sigrid).ejecutar()
    assert salida["vinculados"] == {
        "leidos": 9,
        "vinculados": 4,
        "trabajadores": 2,
        "por_tipo": {"TF": 2, "CO": 1, "(sin tipo)": 1},
        "sin_campo": {"total": 1, "codigos": ["GA-1"]},
        "hacia_no_trabajador": {"total": 2, "codigos": ["TF-A", "TF-B"]},
        "excluidos": {"total": 2, "por_tipo": {"VP": 2}},
    }
    assert "PEPE" not in repr(salida["vinculados"])
    assert (SQL_VIN, ["5"]) in sigrid.leidas


def test_f044_r3_preview_y_sync_deciden_lo_mismo():
    filas = [_fila(10, 7), _fila(12, 999), _fila(13, None),
             _fila(14, 7, tipo="VP")]
    uow = _UowVin()
    _pipeline(_SigridVin(filas)).ejecutar(uow)
    r = uow.vinculados.recibido
    salida = _preview(_SigridVin(filas)).ejecutar()["vinculados"]
    assert (salida["vinculados"], salida["sin_campo"]["total"],
            salida["hacia_no_trabajador"]["total"],
            salida["excluidos"]["total"]) == (
        len(r.vinculos), len(r.sin_campo), len(r.hacia_no_trabajador),
        len(r.excluidos)) == (1, 1, 1, 1)


def test_f044_r3_preview_sin_config_no_lee_ni_publica():
    sigrid = _SigridVin([_fila(10, 7)])
    salida = _preview(sigrid, cfg=None).ejecutar()
    assert "vinculados" not in salida
    assert not any("conext" in sql for sql, _ in sigrid.leidas)


def test_f044_r3_preview_lee_antes_que_incidencias_y_empresas():
    """El orden de lecturas de antes se conserva al final: incidencias y
    empresas siguen siendo las dos últimas."""
    sigrid = _SigridVin([_fila(10, 7)])
    _preview(sigrid, sql_empresas="SELECT ... FROM dbo.auxemp",
             sql_incidencias="SELECT ... FROM dbo.auxhor AS aux").ejecutar()
    assert [sql for sql, _ in sigrid.leidas][-3:] == [
        SQL_VIN, "SELECT ... FROM dbo.auxhor AS aux",
        "SELECT ... FROM dbo.auxemp"]
