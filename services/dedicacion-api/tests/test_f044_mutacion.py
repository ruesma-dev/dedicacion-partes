# tests/test_f044_mutacion.py
"""F-044 · T22: los huecos que destapó la campaña de mutación en la api.

Cada test nombra el superviviente que caza (`progress/mutacion_F-044.md`):
la vigencia de la cola de subfilas por periodo (R30), qué subfilas salen en
`estado` (R9), el formato de `sync.vinculados.desde` (R10), la
inmutabilidad de los modelos, el DDL de las dos tablas nuevas (R5, R30), la
subconsulta de la traza (R30), el defecto de `solo_si_vacia` (R9) y el
límite de `vinculado_ide` (R8). Sin red ni BBDD.
"""
from __future__ import annotations

import dataclasses

import pytest
from domain.models import RecursoVinculado, SubfilaVinculado
from infrastructure.db.repositories import PgAsignacionRepository
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from tests.test_f024_cuadrante_empresa import ANIO, MES, P_ACT, _ln
from tests.test_f044_cuadrante_vinculados import (
    GAS,
    TEL,
    _con,
    _mes,
    _periodos_abiertos,
    _SesionReemplazo,
    _sql,
    _uow_selector,
)
from tests.test_f055_propuestas_mes import _Retenido


# ============ propuestas_mes.py:100 · la cola de subfilas, por periodo ==== #
def test_f044_r30_en_curso_solo_el_periodo_de_la_subfila_encolada():
    """Una subfila en cola (`(periodo, trabajador, obra, pv, vinculado)`)
    pone en curso SU periodo, no el que coincida con otro campo de la
    clave (el trabajador 10) ni cualquier otro."""
    from application.propuestas_mes import PropuestasDelMes

    titular = dataclasses.replace(_ln(100, "60"), propuesta_ide=80001)
    uow = _uow_selector(_con(titular, TEL))
    _periodos_abiertos(uow)

    class _Fabrica:
        def __enter__(self):
            return uow

        def __exit__(self, *exc):
            return None

    # El ejecutor retiene la tarea: la subfila se queda en la cola.
    m = PropuestasDelMes(_Fabrica, None, _Retenido(), empresa_obras=1)
    assert m.lanzar(ANIO, MES) is True
    assert m.pendientes(P_ACT) == frozenset()     # el titular no está
    assert m.en_curso(P_ACT) is True
    assert m.en_curso(10) is False                # 10 es el trabajador
    assert m.en_curso(P_ACT + 1) is False


# ============ propuestas_mes.py:327 · qué subfilas salen en `estado` ====== #
def test_f044_r9_estado_solo_las_subfilas_automaticas_con_propuesta():
    """Con propuesta y sin elegida, sale; con elegida (aunque tenga
    propuesta) o sin propuesta, no."""
    con_prop = dataclasses.replace(TEL, propuesta_ide=81001,
                                   propuesta_cod="CICO13",
                                   propuesta_res="TELEFONIA",
                                   propuesta_metodo="ci_tipo")
    elegida = dataclasses.replace(GAS, propuesta_ide=81002, partida_ide=81002)
    sin_nada = SubfilaVinculado(vinculado_ide=12, tipo="VE", cod="VE-12")
    titular = dataclasses.replace(_ln(100, "60"), propuesta_ide=80001)
    uow = _uow_selector(_con(titular, con_prop, elegida, sin_nada))
    _periodos_abiertos(uow)
    r = _mes(uow, None).estado(uow, ANIO, MES)
    assert r["subfilas"] == [
        {"trabajador_ide": 10, "obra_ide": 100, "es_postventa": False,
         "vinculado_ide": 10, "propuesta_cod": "CICO13",
         "propuesta_res": "TELEFONIA", "propuesta_metodo": "ci_tipo"}]


# ============ sync_pipeline.py:112-113 · `desde` es AAAA-MM =============== #
def _desde(valor):
    from application.sync_pipeline import ConfigVinculados

    return ConfigVinculados.desde_config(
        {"campo": "RECASO", "sql": "SELECT 1", "desde": valor}).desde


@pytest.mark.parametrize("valor, esperado", [
    ("2026-01", (2026, 1)), ("2026-12", (2026, 12)), ("2026-10", (2026, 10))])
def test_f044_r10_desde_admite_de_enero_a_diciembre(valor, esperado):
    assert _desde(valor) == esperado


@pytest.mark.parametrize("valor", [
    "2026-00", "2026-13", "abcd-10", "2026-1x", "26-10", "2026-10-01", None])
def test_f044_r10_desde_mal_escrito_no_arranca(valor):
    with pytest.raises(ValueError, match="AAAA-MM"):
        _desde(valor)


# ============ frozen: sync_pipeline.py:81, models.py:65, models.py:84 ===== #
def test_f044_los_modelos_y_la_config_son_inmutables():
    from application.sync_pipeline import ConfigVinculados

    cfg = ConfigVinculados(campo="RECASO", desde=(2026, 10),
                           tipos_excluidos=frozenset({"VP"}), sql="S")
    rv = RecursoVinculado(ide=10, principal_ide=200, cod="TF-10",
                          descripcion=None, empresa=1, fecha_baja=None,
                          tipo="TF", tipo_res="TELEFONO", horide=31)
    for objeto, campo in ((cfg, "desde"), (rv, "principal_ide"),
                          (TEL, "partida_ide")):
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(objeto, campo, 1)


# ============ orm_models.py:341-386 · el DDL de las tablas nuevas ========= #
def _ddl(tabla) -> list[str]:
    texto = str(CreateTable(tabla).compile(dialect=postgresql.dialect()))
    return [x.strip().rstrip(",") for x in texto.strip().splitlines()]


def test_f044_r5_r30_esquema_ddl_y_defectos():
    """Obligatorias, longitudes de la traza (las de `asignacion`), zona
    horaria, `ON DELETE CASCADE` y el defecto de `activo`."""
    from infrastructure.db.orm_models import (
        AsignacionVinculadoORM,
        RecursoVinculadoORM,
    )

    assert _ddl(RecursoVinculadoORM.__table__) == [
        "CREATE TABLE recurso_vinculado (", "ide BIGINT NOT NULL",
        "trabajador_ide BIGINT", "tipo TEXT", "tipo_res TEXT", "cod TEXT",
        "descripcion TEXT", "empresa INTEGER", "fecha_baja INTEGER",
        "horide BIGINT", "activo BOOLEAN NOT NULL",
        "estado_vinculo TEXT NOT NULL",
        "sincronizado_en TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL",
        "PRIMARY KEY (ide)",
        "FOREIGN KEY(trabajador_ide) REFERENCES trabajador (ide)", ")"]
    assert _ddl(AsignacionVinculadoORM.__table__) == [
        "CREATE TABLE asignacion_vinculado (", "id SERIAL NOT NULL",
        "asignacion_id INTEGER NOT NULL", "vinculado_ide BIGINT NOT NULL",
        "partida_ide BIGINT", "partida_cod TEXT", "partida_res TEXT",
        "propuesta_ide BIGINT", "propuesta_cod TEXT", "propuesta_res TEXT",
        "propuesta_metodo TEXT", "propuesta_origen TEXT",
        "sigrid_estado VARCHAR(16)", "sigrid_motivo VARCHAR(300)",
        "sigrid_parte VARCHAR(24)", "sigrid_hmores_ide INTEGER",
        "PRIMARY KEY (id)",
        ("CONSTRAINT uq_asignacion_vinculado UNIQUE (asignacion_id, "
        "vinculado_ide)"),
        ("FOREIGN KEY(asignacion_id) REFERENCES asignacion (id) ON DELETE "
        "CASCADE"),
        "FOREIGN KEY(vinculado_ide) REFERENCES recurso_vinculado (ide)", ")"]
    assert RecursoVinculadoORM.__table__.columns["activo"].default.arg is True


# ============ traza_vinculados.py:35 · la subconsulta de SU asignación ==== #
def test_f044_r30_la_traza_va_a_la_asignacion_de_su_registro():
    from application.traza_vinculados import trazar_vinculados

    from tests.test_f051_hmores_ide import _SesionQueAnota

    s = _SesionQueAnota()
    trazar_vinculados(s, {"vinculados": [
        {"registro_id": 7, "recurso_ide": 10, "accion": "escribir",
         "parte_cod": "PT", "hmores_ide": 5201}]})
    [st] = s.sentencias
    sql = _sql(st)
    assert "SELECT asignacion.id, 10" in sql
    assert "FROM asignacion WHERE asignacion.id = 7" in sql


# ============ repositories.py:549 · `solo_si_vacia` por defecto, no ======= #
def test_f044_r9_guardar_propuesta_de_subfila_por_defecto_pisa_la_propuesta():
    """Sin `solo_si_vacia` (el selector): solo exige que siga sin elegida."""
    s = _SesionReemplazo()
    PgAsignacionRepository(s).guardar_propuesta_vinculado(  # type: ignore[arg-type]
        3, 14, (100, False), 10,
        {"paride": 81001, "cod": "CICO13", "res": "TELEFONIA",
         "metodo": "ci_tipo", "origen": None})
    [stmt] = s.ejecutadas
    sql = _sql(stmt)
    assert "WHERE asignacion_vinculado.partida_ide IS NULL" in sql
    assert "propuesta_ide IS NULL" not in sql


# ============ routes.py:357, schemas.py:78 · `vinculado_ide` ≥ 1 ========== #
def test_f044_r8_partida_in_admite_el_vinculado_1():
    from interface_adapters.api.schemas import PartidaIn

    assert PartidaIn(obra_ide=1, partida=None, vinculado_ide=1
                     ).vinculado_ide == 1


@pytest.mark.parametrize("vinculado, estado", [(1, 200), (0, 422)])
def test_f044_r8_get_partidas_vinculado_desde_1(monkeypatch, vinculado,
                                                estado):
    from tests.test_f044_cuadrante_vinculados import _SelectorEspia
    from tests.test_f050_rutas_partida import BASE, _cliente

    espia = _SelectorEspia()
    cliente, _ = _cliente({14: []}, monkeypatch, partidas_linea=espia)
    r = cliente.get(f"{BASE}/trabajadores/14/partidas",
                    params={"obra_ide": 100, "vinculado_ide": vinculado})
    assert r.status_code == estado, r.text
    if estado == 200:
        assert espia.llamadas == [{"empresa_obras": 1, "vinculado_ide": 1}]
