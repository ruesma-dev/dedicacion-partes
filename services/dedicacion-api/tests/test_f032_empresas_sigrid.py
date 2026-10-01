# tests/test_f032_empresas_sigrid.py
"""Tests offline de F-032: nombres de empresa sincronizados desde Sigrid.

Trazabilidad con los `acceptance` de F-032 en `harness/features.json`
(sdd=false), numerados en su orden:

  R1  el sync lee `auxemp` por sigrid-api y lo guarda en la tabla `empresa`
      declarada en el ORM, sin DDL a mano;
  R2  `GET /api/v1/empresas` toma el nombre de esa tabla (alta o cambio de
      nombre en Sigrid llega con el siguiente sync);
  R3  sin `empresas.nombres` en `config.yaml`; «Empresa N» solo si la
      empresa no está en la tabla;
  R4  el preview del sync informa de las empresas leídas;
  R5  una empresa de baja o desactivada con trabajadores activos sale
      marcada «(de baja)», nunca oculta.

R6 (sync real y selector en local) es MANUAL; R7 es la review.

Nada abre un socket ni una conexión: Sigrid es un doble que devuelve
listas, el repositorio trabaja contra una sesión doble y el DDL se compila
con el dialecto PostgreSQL sin motor. Los módulos que F-032 crea o amplía
se importan DENTRO de cada test (patrón de `test_f023_sync_empresa.py`).
"""
from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.dialects import postgresql

DIALECTO = postgresql.dialect()
SQL_EMPRESAS = "SELECT ... FROM dbo.auxemp AS emp"


def _fila(numemp: Any, **cambios: Any) -> dict[str, Any]:
    """Fila de `sync.empresas.sql`: empresa en alta y activa."""
    fila: dict[str, Any] = {
        "numemp": numemp,
        "cod": f"E{numemp}",
        "nombre": f"EMPRESA {numemp} SL",
        "fecbaj": 0,
        "desact": 0,
    }
    fila.update(cambios)
    return fila


# --- R1 · tabla `empresa` en el ORM, sin DDL a mano ---------------------------


def test_f032_r1_tabla_empresa_declarada_en_el_orm() -> None:
    from infrastructure.db.orm_models import Base, EmpresaORM

    tabla = EmpresaORM.__table__
    assert tabla.name == "empresa"
    assert Base.metadata.tables["empresa"] is tabla
    assert [c.name for c in tabla.primary_key.columns] == ["numemp"]
    tipos = {c.name: c.type.compile(dialect=DIALECTO) for c in tabla.columns}
    assert tipos == {
        "numemp": "INTEGER",
        "cod": "TEXT",
        "nombre": "TEXT",
        "fecbaj": "INTEGER",
        "desact": "INTEGER",
        "sync_en": "TIMESTAMP WITH TIME ZONE",
    }


def test_f032_r1_numemp_no_es_autoincremental() -> None:
    """La clave es el `numemp` de Sigrid: nunca la genera PostgreSQL."""
    from infrastructure.db.orm_models import EmpresaORM

    assert EmpresaORM.__table__.columns["numemp"].autoincrement is False


def test_f032_r1_esquema_la_crea_create_all_y_no_un_alter() -> None:
    """Sobre una base sin la tabla, `alters_faltantes` no emite nada para
    ella (la crea `create_all` al arrancar); sobre una base que la tiene
    entera, tampoco."""
    from infrastructure.db.esquema import alters_faltantes
    from infrastructure.db.orm_models import Base

    al_dia = {t.name: {c.name for c in t.columns}
              for t in Base.metadata.tables.values()}
    sin_empresa = {k: v for k, v in al_dia.items() if k != "empresa"}
    assert alters_faltantes(Base.metadata, sin_empresa) == []
    assert alters_faltantes(Base.metadata, al_dia) == []


# --- R5 · regla «de baja» (dominio) ------------------------------------------


@pytest.mark.parametrize(("fecbaj", "desact", "de_baja"), [
    (0, 0, False),
    (None, None, False),
    (None, 0, False),
    (20240101, 0, True),          # fecha de baja informada
    (1, None, True),
    (0, 1, True),                 # desactivada
    (20240101, 1, True),
    (-1, 0, False),               # una fecha no positiva no es baja
    (0, 2, False),                # desact solo vale 0 / 1
])
def test_f032_r5_empresa_de_baja(fecbaj: Any, desact: Any, de_baja: bool) -> None:
    from domain.empresas import empresa_de_baja

    assert empresa_de_baja(fecbaj, desact) is de_baja


# --- R1 · consulta versionada en config.yaml ---------------------------------


def _plano(sql: str) -> str:
    return " ".join(sql.split())


def test_f032_r1_config_lee_auxemp_con_los_alias_exactos() -> None:
    from config.settings import cargar_config

    sql = _plano(cargar_config()["sync"]["empresas"]["sql"])
    assert sql == (
        "SELECT aux.numemp AS numemp, aux.cod AS cod, aux.res AS nombre, "
        "aux.fecbaj AS fecbaj, aux.desact AS desact "
        "FROM dbo.auxemp AS aux ORDER BY aux.numemp"
    )


def test_f032_r1_config_consulta_de_solo_lectura() -> None:
    from config.settings import cargar_config

    sql = _plano(cargar_config()["sync"]["empresas"]["sql"]).upper()
    assert sql.startswith("SELECT ")
    for prohibida in ("INSERT", "UPDATE", "DELETE", "MERGE", "EXEC", ";"):
        assert prohibida not in sql, prohibida


# --- R1/R2 · repositorio: upsert idempotente y lectura --------------------------


class _Resultado:
    def __init__(self, filas: list[Any]) -> None:
        self._filas = filas

    def all(self) -> list[Any]:
        return list(self._filas)


class _SesionRepo:
    """Sesión doble: `scalars()` devuelve las filas previas (y apunta la
    sentencia), `add` apunta las altas."""

    def __init__(self, previas: list[Any] | None = None) -> None:
        self.previas = list(previas or [])
        self.anadidas: list[Any] = []
        self.sentencias: list[Any] = []

    def scalars(self, sentencia: Any) -> _Resultado:
        self.sentencias.append(sentencia)
        return _Resultado(self.previas)

    def add(self, orm: Any) -> None:
        self.anadidas.append(orm)


def _repo(previas: list[Any] | None = None) -> tuple[Any, _SesionRepo]:
    from infrastructure.db.repositories import PgEmpresaRepository

    sesion = _SesionRepo(previas)
    return PgEmpresaRepository(sesion), sesion  # type: ignore[arg-type]


def _orm(numemp: int, **cambios: Any) -> Any:
    from infrastructure.db.orm_models import EmpresaORM

    datos = {k: v for k, v in _fila(numemp).items() if k != "numemp"}
    datos.update(cambios)
    return EmpresaORM(numemp=numemp, **datos)


def _campos(orm: Any) -> tuple[Any, ...]:
    return (orm.numemp, orm.cod, orm.nombre, orm.fecbaj, orm.desact)


def test_f032_r1_repo_alta_de_empresas_nuevas() -> None:
    repo, sesion = _repo()
    resultado = repo.sincronizar([
        _fila(18, nombre=" RUESMA SERVICIOS SL ", cod=" 18 "),
        _fila("31", nombre="UTE RUESMA-INESCO TOLEDO", fecbaj="20250101",
              desact=None),
    ])
    assert [_campos(o) for o in sesion.anadidas] == [
        (18, "18", "RUESMA SERVICIOS SL", 0, 0),
        (31, "E31", "UTE RUESMA-INESCO TOLEDO", 20250101, None),
    ]
    assert (resultado.recibidos, resultado.altas, resultado.actualizados,
            resultado.desactivados) == (2, 2, 0, 0)


def test_f032_r1_repo_es_idempotente() -> None:
    """Mismas filas sobre una tabla ya al día: nada que dar de alta ni que
    actualizar, y los valores no cambian."""
    previas = [_orm(1), _orm(18)]
    repo, sesion = _repo(previas)
    resultado = repo.sincronizar([_fila(1), _fila(18)])
    assert sesion.anadidas == []
    assert (resultado.recibidos, resultado.altas,
            resultado.actualizados) == (2, 0, 0)
    assert [_campos(o) for o in previas] == [
        (1, "E1", "EMPRESA 1 SL", 0, 0), (18, "E18", "EMPRESA 18 SL", 0, 0)]


@pytest.mark.parametrize("campo, valor, esperado", [
    ("nombre", "NUEVO NOMBRE SL", "NUEVO NOMBRE SL"),
    ("cod", "X18", "X18"),
    ("fecbaj", 20260930, 20260930),
    ("desact", 1, 1),
])
def test_f032_r2_repo_actualiza_cambios_de_sigrid(
    campo: str, valor: Any, esperado: Any
) -> None:
    """Un cambio de nombre (o de baja) en Sigrid llega con el siguiente sync."""
    previa = _orm(18)
    repo, sesion = _repo([previa, _orm(1)])
    resultado = repo.sincronizar([_fila(18, **{campo: valor}), _fila(1)])
    assert getattr(previa, campo) == esperado
    assert sesion.anadidas == []
    assert (resultado.altas, resultado.actualizados) == (0, 1)


def test_f032_r1_repo_omite_filas_sin_numemp_y_no_borra_las_ausentes() -> None:
    """Sin `numemp` no hay con qué casar: se omite. Una empresa que ya no
    llega no se borra (su nombre sigue sirviendo) ni cuenta como cambio."""
    ausente = _orm(28, nombre="PORSAN E HIJOS CONSTRUCCIONES SL")
    repo, sesion = _repo([ausente])
    resultado = repo.sincronizar([_fila(None), _fila(1)])
    assert [o.numemp for o in sesion.anadidas] == [1]
    assert ausente.nombre == "PORSAN E HIJOS CONSTRUCCIONES SL"
    assert (resultado.recibidos, resultado.altas, resultado.actualizados,
            resultado.desactivados) == (1, 1, 0, 0)


def test_f032_r1_repo_numemp_repetido_no_da_dos_altas() -> None:
    """`numemp` es único en Sigrid; si llegara dos veces, una sola fila (la
    última manda) y nunca dos altas con la misma clave."""
    repo, sesion = _repo()
    resultado = repo.sincronizar([_fila(5, nombre="A"), _fila(5, nombre="B")])
    assert [(o.numemp, o.nombre) for o in sesion.anadidas] == [(5, "B")]
    assert (resultado.recibidos, resultado.altas) == (1, 1)


def test_f032_r2_r5_repo_listar_mapea_nombre_y_baja() -> None:
    from domain.models import Empresa

    repo, sesion = _repo([
        _orm(1, nombre="CONSTRUCCIONES RUESMA"),
        _orm(12, nombre="CP PRIMO DE RIVERA UTE", fecbaj=20240630),
        _orm(14, nombre=None, desact=1),
    ])
    assert repo.listar() == [
        Empresa(numero=1, nombre="CONSTRUCCIONES RUESMA", de_baja=False),
        Empresa(numero=12, nombre="CP PRIMO DE RIVERA UTE", de_baja=True),
        Empresa(numero=14, nombre=None, de_baja=True),
    ]
    [sentencia] = sesion.sentencias
    sql = " ".join(str(sentencia.compile(dialect=DIALECTO)).split())
    assert sql.startswith("SELECT empresa.numemp, empresa.cod, empresa.nombre")
    assert sql.endswith("FROM empresa ORDER BY empresa.numemp")


def test_f032_r1_la_unidad_de_trabajo_trae_el_repositorio() -> None:
    from infrastructure.db.repositories import (
        PgEmpresaRepository,
        SqlAlchemyUnitOfWork,
    )

    class _Sesion:
        def close(self) -> None:
            return None

    with SqlAlchemyUnitOfWork(lambda: _Sesion()) as uow:  # type: ignore[arg-type]
        assert isinstance(uow.empresas, PgEmpresaRepository)


# --- R1 · el sync de maestros trae y guarda las empresas ----------------------


class _SigridFalso:
    """Devuelve filas según la tabla que lea la consulta y anota las SQL."""

    def __init__(self, empresas: list[dict[str, Any]] | None = None) -> None:
        self.empresas = empresas if empresas is not None else [_fila(1)]
        self.leidas: list[str] = []

    def leer(self, sql: str) -> list[dict[str, Any]]:
        self.leidas.append(sql)
        if "dbo.auxemp" in sql:
            return [dict(f) for f in self.empresas]
        if "dbo.obr" in sql:
            return [{"ide": 7, "cod": "0007", "empresa": 1,
                     "descripcion": "OBRA", "estado_sigrid": "En curso"}]
        return [{"ide": 3, "cod": "E3", "nombre": "Persona", "dni": "3X",
                 "empresa": 1, "categoria": "Técnico", "recurso_ide": 30,
                 "empresa_recurso": 1, "estado_recurso": "1",
                 "baja_recurso": 0, "baja_laboral": 0,
                 "cod_hora_mes": "MENC", "importe_mes": 1}]


class _RepoEspia:
    def __init__(self) -> None:
        self.recibido: list[dict[str, Any]] | None = None

    def sincronizar(self, filas: list[dict[str, Any]]) -> Any:
        from domain.models import ResultadoSyncMaestro

        self.recibido = [dict(f) for f in filas]
        return ResultadoSyncMaestro(recibidos=len(filas), altas=len(filas))


class _UowEspia:
    def __init__(self) -> None:
        self.trabajadores = _RepoEspia()
        self.obras = _RepoEspia()
        self.empresas = _RepoEspia()
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


def test_f032_r1_pipeline_lee_y_guarda_las_empresas() -> None:
    from application import sync_pipeline as sp

    filas = [_fila(1), _fila(18, nombre="RUESMA SERVICIOS SL")]
    sigrid, uow = _SigridFalso(filas), _UowEspia()
    resultado = sp.SyncMaestrosPipeline([
        sp.FetchEmpleadosStep(sigrid, "SELECT ... FROM dbo.emp"),
        sp.FetchObrasStep(sigrid, "SELECT ... FROM dbo.obr"),
        sp.FetchEmpresasStep(sigrid, SQL_EMPRESAS),
        sp.UpsertTrabajadoresStep(),
        sp.UpsertObrasStep(),
        sp.UpsertEmpresasStep(),
    ]).ejecutar(uow)
    assert sigrid.leidas[-1] == SQL_EMPRESAS
    assert uow.empresas.recibido == filas
    assert resultado.empresas.recibidos == 2
    assert resultado.empresas.altas == 2
    assert uow.commits == 1


def test_f032_r1_sin_numemp_o_nombre_no_se_guarda_nada() -> None:
    from application import sync_pipeline as sp

    for falta in ("numemp", "nombre"):
        filas = [{k: v for k, v in _fila(1).items() if k != falta}]
        uow = _UowEspia()
        with pytest.raises(ValueError, match=rf"sync\.empresas\.sql.*{falta}"):
            sp.SyncMaestrosPipeline([
                sp.FetchEmpresasStep(_SigridFalso(filas), SQL_EMPRESAS),
                sp.UpsertEmpresasStep(),
            ]).ejecutar(uow)
        assert uow.empresas.recibido is None
        assert uow.commits == 0


def _contenedor(monkeypatch: pytest.MonkeyPatch, sigrid: _SigridFalso) -> Any:
    """Contenedor REAL (config.yaml versionado) con Sigrid sustituido."""
    from config.settings import Settings
    from interface_adapters.api import deps

    monkeypatch.setattr(deps, "SigridApiClient", lambda _settings: sigrid)
    return deps.construir_contenedor(Settings(_env_file=None), None)  # type: ignore[arg-type]


def test_f032_r1_el_sync_real_incluye_las_empresas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`POST /sync` (el pipeline del contenedor) lee la consulta de
    `config.yaml` y guarda sus filas, en la misma transacción que el resto."""
    from config.settings import cargar_config

    sigrid, uow = _SigridFalso(), _UowEspia()
    resultado = _contenedor(monkeypatch, sigrid).sync_pipeline.ejecutar(uow)
    sql = cargar_config()["sync"]["empresas"]["sql"]
    assert sql in sigrid.leidas
    assert uow.empresas.recibido == [_fila(1)]
    assert uow.trabajadores.recibido and uow.obras.recibido
    assert resultado.empresas.recibidos == 1
    assert uow.commits == 1


def test_f032_r1_la_respuesta_del_sync_trae_las_empresas() -> None:
    from domain.models import ResultadoSync, ResultadoSyncMaestro
    from interface_adapters.api.schemas import a_sync_out

    salida = a_sync_out(ResultadoSync(
        empleados=ResultadoSyncMaestro(recibidos=3),
        obras=ResultadoSyncMaestro(recibidos=2),
        duracion_s=1.5,
        empresas=ResultadoSyncMaestro(recibidos=19, altas=2, actualizados=1),
    ))
    assert salida.model_dump()["empresas"] == {
        "recibidos": 19, "altas": 2, "actualizados": 1, "desactivados": 0}


def test_f032_r1_pipeline_sin_pasos_de_empresas_las_deja_a_cero() -> None:
    """La composición es del punto de entrada: sin los pasos de empresas el
    resultado las da a cero, nunca `None` (la respuesta del sync las pinta)."""
    from application import sync_pipeline as sp
    from domain.models import ResultadoSyncMaestro

    sigrid = _SigridFalso()
    resultado = sp.SyncMaestrosPipeline([
        sp.FetchEmpleadosStep(sigrid, "SELECT ... FROM dbo.emp"),
        sp.FetchObrasStep(sigrid, "SELECT ... FROM dbo.obr"),
        sp.UpsertTrabajadoresStep(),
        sp.UpsertObrasStep(),
    ]).ejecutar(_UowEspia())
    assert resultado.empresas == ResultadoSyncMaestro()


# --- R4 · el preview informa de las empresas leídas ---------------------------


def _preview(sigrid: _SigridFalso, sql_empresas: str | None = SQL_EMPRESAS) -> Any:
    from application.use_cases import PreviewSync

    return PreviewSync(sigrid, "SELECT ... FROM dbo.emp",
                       "SELECT ... FROM dbo.obr", sql_empresas=sql_empresas)


def test_f032_r4_preview_informa_de_las_empresas_leidas() -> None:
    sigrid = _SigridFalso([
        _fila(1, nombre="CONSTRUCCIONES RUESMA"),
        _fila(12, nombre="CP PRIMO DE RIVERA UTE", fecbaj=20240630),
        _fila("18", nombre="RUESMA SERVICIOS SL", fecbaj=None, desact=None),
        _fila(26, nombre="UTE HOSPITAL HSFA", desact="1"),
        _fila(None, nombre="SIN NÚMERO"),
    ])
    salida = _preview(sigrid).ejecutar()
    assert salida["empresas"] == {
        "leidas": 5,
        "sin_numero": 1,
        "de_baja": [12, 26],
        "nombres": {
            "1": "CONSTRUCCIONES RUESMA",
            "12": "CP PRIMO DE RIVERA UTE",
            "18": "RUESMA SERVICIOS SL",
            "26": "UTE HOSPITAL HSFA",
        },
    }
    assert SQL_EMPRESAS in sigrid.leidas
    # Lo de F-023 sigue ahí.
    assert salida["empleados"]["total"] == 1
    assert salida["obras"]["total"] == 1


def test_f032_r4_preview_sin_numemp_o_nombre_avisa_como_el_sync() -> None:
    filas = [{k: v for k, v in _fila(1).items() if k != "nombre"}]
    with pytest.raises(ValueError, match=r"sync\.empresas\.sql.*nombre"):
        _preview(_SigridFalso(filas)).ejecutar()


def test_f032_r4_preview_sin_consulta_no_lee_empresas() -> None:
    sigrid = _SigridFalso()
    salida = _preview(sigrid, sql_empresas=None).ejecutar()
    assert "empresas" not in salida
    assert not any("dbo.auxemp" in sql for sql in sigrid.leidas)


def test_f032_r4_el_preview_real_usa_la_consulta_de_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Preview y sync del contenedor leen la MISMA consulta de empresas."""
    from config.settings import cargar_config

    sigrid = _SigridFalso([_fila(31, nombre="UTE RUESMA-INESCO TOLEDO")])
    salida = _contenedor(monkeypatch, sigrid).preview_sync.ejecutar()
    assert sigrid.leidas[-1] == cargar_config()["sync"]["empresas"]["sql"]
    assert salida["empresas"]["nombres"] == {"31": "UTE RUESMA-INESCO TOLEDO"}
