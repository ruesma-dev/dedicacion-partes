# tests/test_f030_catalogo.py
"""F-030 · Catálogo de incidencias desde Sigrid (R3, R5, R6, R7).

El sync de maestros y su preview leen de `auxhor` los `CI*` salvo `CIZ` y
los guardan en `tipo_incidencia`; `GET /api/v1/incidencias` sirve las
activas por orden de letra. Nada viene de `partes` (D1).

Offline: Sigrid es un doble que devuelve listas, el repositorio trabaja
contra una sesión doble y el contenedor real se monta con los dobles de
`test_f023_sync_empresa.py`. Ni red, ni BBDD, ni `.env`.
"""
from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.dialects import postgresql

from tests.conftest import UniversoFalso

DIALECTO = postgresql.dialect()
SQL_INC = "SELECT ... FROM dbo.auxhor AS aux"


def _fila(ide: Any, cod: str, res: Any, fecbaj: Any = 0) -> dict[str, Any]:
    return {"ide": ide, "cod": cod, "res": res, "fecbaj": fecbaj}


AUXHOR = [
    _fila(11, "CIA", "Accidente/Enf. Profesional(AT)"),
    _fila(12, "CIE", "Enfermedad/Acc. no laboral(B)"),
    _fila(16, "CIP", "Falta Justificada/Permiso(FJ)"),
    _fila(17, "CIV", "Vacaciones(V)"),
]


def _plano(sql: str) -> str:
    return " ".join(sql.split())


# ---------------------------- config (R3) -------------------------------- #
def test_f030_r3_config_lee_auxhor_ci_sin_ciz_con_los_alias_exactos():
    from config.settings import cargar_config

    sql = _plano(cargar_config()["sync"]["incidencias"]["sql"])
    assert sql == (
        "SELECT aux.ide AS ide, aux.cod AS cod, aux.res AS res, "
        "aux.fecbaj AS fecbaj FROM dbo.auxhor AS aux "
        "WHERE aux.cod LIKE 'CI%' AND aux.cod <> 'CIZ' ORDER BY aux.cod")
    for prohibida in ("INSERT", "UPDATE", "DELETE", "MERGE", "EXEC", ";"):
        assert prohibida not in sql.upper(), prohibida


# --------------------------- repositorio (R3, R5) ------------------------ #
class _Resultado:
    def __init__(self, filas: list[Any]) -> None:
        self._filas = filas

    def all(self) -> list[Any]:
        return list(self._filas)


class _SesionRepo:
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
    from infrastructure.db.repositories import PgTipoIncidenciaRepository

    sesion = _SesionRepo(previas)
    return PgTipoIncidenciaRepository(sesion), sesion  # type: ignore[arg-type]


def _orm(ide: int, codigo: str, letra: str, nombre: str,
         activa: bool = True) -> Any:
    from infrastructure.db.orm_models import TipoIncidenciaORM

    return TipoIncidenciaORM(ide=ide, codigo=codigo, letra=letra,
                             nombre=nombre, activa=activa)


def _campos(o: Any) -> tuple[Any, ...]:
    return (o.ide, o.codigo, o.letra, o.nombre, o.activa)


def _cuenta(r: Any) -> tuple[int, int, int, int]:
    return (r.recibidos, r.altas, r.actualizados, r.desactivados)


def test_f030_r3_repo_alta_con_letra_y_nombre_de_res():
    repo, sesion = _repo()
    r = repo.sincronizar([
        _fila(17, " CIV ", "Vacaciones(V)"),
        _fila("16", "CIP", "Falta Justificada/Permiso(FJ)", None),
        _fila(19, "CIQ", "Sin letra"),
    ])
    assert [_campos(o) for o in sesion.anadidas] == [
        (17, "CIV", "V", "Vacaciones", True),
        (16, "CIP", "FJ", "Falta Justificada/Permiso", True),
        (19, "CIQ", "Q", "Sin letra", True),
    ]
    assert _cuenta(r) == (3, 3, 0, 0)


def test_f030_r5_repo_fecha_de_baja_la_deja_inactiva():
    repo, sesion = _repo()
    r = repo.sincronizar([_fila(17, "CIV", "Vacaciones(V)", 20250101),
                          _fila(12, "CIE", "Enfermedad(B)", 0)])
    assert [(o.codigo, o.activa) for o in sesion.anadidas] == [
        ("CIV", False), ("CIE", True)]
    assert _cuenta(r) == (2, 2, 0, 0)


def test_f030_r5_repo_idempotente():
    previas = [_orm(17, "CIV", "V", "Vacaciones"),
               _orm(12, "CIE", "B", "Enfermedad")]
    repo, sesion = _repo(previas)
    r = repo.sincronizar([_fila(17, "CIV", "Vacaciones(V)"),
                          _fila(12, "CIE", "Enfermedad(B)")])
    assert sesion.anadidas == []
    assert _cuenta(r) == (2, 0, 0, 0)
    assert [_campos(o) for o in previas] == [
        (17, "CIV", "V", "Vacaciones", True), (12, "CIE", "B", "Enfermedad", True)]


@pytest.mark.parametrize("fila, esperado", [
    (_fila(17, "CIV", "Vacaciones anuales(V)"),
     (17, "CIV", "V", "Vacaciones anuales", True)),
    (_fila(17, "CIW", "Vacaciones(V)"), (17, "CIW", "V", "Vacaciones", True)),
    (_fila(17, "CIV", "Vacaciones(VA)"), (17, "CIV", "VA", "Vacaciones", True)),
    (_fila(17, "CIV", "Vacaciones(V)", 20261001),
     (17, "CIV", "V", "Vacaciones", False)),
])
def test_f030_r5_repo_actualiza_lo_que_cambia_en_sigrid(fila, esperado):
    previa = _orm(17, "CIV", "V", "Vacaciones")
    repo, sesion = _repo([previa])
    r = repo.sincronizar([fila])
    assert _campos(previa) == esperado
    assert sesion.anadidas == []
    assert _cuenta(r) == (1, 0, 1, 0)


def test_f030_r5_repo_reactiva_la_que_vuelve_sin_baja():
    previa = _orm(17, "CIV", "V", "Vacaciones", activa=False)
    repo, _ = _repo([previa])
    r = repo.sincronizar([_fila(17, "CIV", "Vacaciones(V)")])
    assert previa.activa is True
    assert _cuenta(r) == (1, 0, 1, 0)


def test_f030_r5_repo_la_que_deja_de_leerse_queda_inactiva_y_no_se_borra():
    ausente = _orm(13, "CIF", "F", "Falta injustificada")
    ya_inactiva = _orm(14, "CIH", "H", "Huelga", activa=False)
    repo, sesion = _repo([ausente, ya_inactiva, _orm(17, "CIV", "V", "Vacaciones")])
    r = repo.sincronizar([_fila(17, "CIV", "Vacaciones(V)")])
    assert ausente.activa is False and ausente.nombre == "Falta injustificada"
    assert ya_inactiva.activa is False
    assert sesion.anadidas == []
    assert _cuenta(r) == (1, 0, 0, 1)


def test_f030_r3_repo_omite_filas_sin_ide_o_sin_codigo_y_no_duplica():
    repo, sesion = _repo()
    r = repo.sincronizar([_fila(None, "CIV", "Vacaciones(V)"),
                          _fila(18, "  ", "Nada(N)"),
                          _fila(17, "CIV", "Vacaciones(V)"),
                          _fila(17, "CIV", "Vacaciones bis(V)")])
    assert [_campos(o) for o in sesion.anadidas] == [
        (17, "CIV", "V", "Vacaciones bis", True)]
    assert _cuenta(r) == (1, 1, 0, 0)


def test_f030_r6_repo_activos_por_letra():
    from domain.models import TipoIncidencia

    repo, sesion = _repo([_orm(16, "CIP", "FJ", "Permiso"),
                          _orm(12, "CIE", "B", "Enfermedad")])
    assert repo.activos() == [TipoIncidencia(16, "CIP", "FJ", "Permiso", True),
                              TipoIncidencia(12, "CIE", "B", "Enfermedad", True)]
    [stmt] = sesion.sentencias
    sql = _plano(str(stmt.compile(dialect=DIALECTO)))
    assert sql.startswith("SELECT tipo_incidencia.ide, tipo_incidencia.codigo")
    assert sql.endswith(
        "FROM tipo_incidencia WHERE tipo_incidencia.activa IS true "
        "ORDER BY tipo_incidencia.letra, tipo_incidencia.codigo")


def test_f030_r3_la_unidad_de_trabajo_trae_el_repositorio():
    from infrastructure.db.repositories import (
        PgTipoIncidenciaRepository,
        SqlAlchemyUnitOfWork,
    )

    class _Sesion:
        def close(self) -> None:
            return None

    with SqlAlchemyUnitOfWork(lambda: _Sesion()) as uow:  # type: ignore[arg-type]
        assert isinstance(uow.tipos_incidencia, PgTipoIncidenciaRepository)


# ------------------------- sync y preview (R3, R7) ----------------------- #
class _Sigrid:
    def __init__(self, auxhor: list[dict[str, Any]] | None = None,
                 fallo: Exception | None = None) -> None:
        self.auxhor = AUXHOR if auxhor is None else auxhor
        self.fallo = fallo
        self.leidas: list[str] = []

    def leer(self, sql: str, parametros: Any = None) -> list[dict[str, Any]]:
        self.leidas.append(sql)
        # F-044 (lista cerrada): los recursos vinculados, fuera de F-030.
        if "dbo.conext" in sql:
            return []
        if "FROM dbo.auxhor AS aux" in sql:  # no el JOIN de empleados
            if self.fallo is not None:
                raise self.fallo
            return [dict(f) for f in self.auxhor]
        if "dbo.auxemp" in sql:
            return [{"numemp": 1, "nombre": "RUESMA"}]
        if "dbo.obr" in sql:
            return [{"ide": 7, "cod": "0007", "empresa": 1,
                     "descripcion": "OBRA", "estado_sigrid": "En curso"}]
        return [{"ide": 3, "cod": "E3", "nombre": "Persona", "dni": "3X",
                 "empresa": 1, "categoria": "Técnico", "estado_recurso": "1",
                 "fecha_baja": None, "baja_laboral": 0,
                 "cod_hora_mes": "MENC", "importe_mes": 1}]


class _RepoEspia:
    def __init__(self) -> None:
        self.recibido: list[dict[str, Any]] | None = None

    def sincronizar(self, filas: list[dict[str, Any]]) -> Any:
        from domain.models import ResultadoSyncMaestro

        self.recibido = [dict(f) for f in filas]
        return ResultadoSyncMaestro(recibidos=len(filas), altas=len(filas))


class _Periodos:
    def listar(self) -> list[Any]:
        return []


class _Uow:
    def __init__(self) -> None:
        self.trabajadores = _RepoEspia()
        self.obras = _RepoEspia()
        self.empresas = _RepoEspia()
        self.tipos_incidencia = _RepoEspia()
        # F-044 (lista cerrada): el paso de vinculados del sync real.
        from tests.test_f023_sync_empresa import _RepoVinculadosVacio
        self.vinculados = _RepoVinculadosVacio()
        self.periodos = _Periodos()
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


def _pipeline(sigrid: _Sigrid) -> Any:
    from application import sync_pipeline as sp

    return sp.SyncMaestrosPipeline([
        sp.FetchEmpleadosStep(sigrid, "SELECT ... FROM dbo.emp"),
        sp.FetchObrasStep(sigrid, "SELECT ... FROM dbo.obr",
                          universo=UniversoFalso(), empresa_obras=1),
        sp.FetchTiposIncidenciaStep(sigrid, SQL_INC),
        sp.UpsertTrabajadoresStep(),
        sp.UpsertObrasStep(),
        sp.UpsertTiposIncidenciaStep(),
    ])


def test_f030_r3_sync_lee_y_guarda_el_catalogo():
    sigrid, uow = _Sigrid(), _Uow()
    resultado = _pipeline(sigrid).ejecutar(uow)
    assert SQL_INC in sigrid.leidas
    assert uow.tipos_incidencia.recibido == AUXHOR
    assert resultado.incidencias.recibidos == 4
    assert resultado.incidencias.altas == 4
    assert uow.commits == 1


def test_f030_r3_sync_sin_los_pasos_deja_el_catalogo_a_cero():
    from application import sync_pipeline as sp
    from domain.models import ResultadoSyncMaestro

    sigrid = _Sigrid()
    resultado = sp.SyncMaestrosPipeline([
        sp.FetchEmpleadosStep(sigrid, "SELECT ... FROM dbo.emp"),
        sp.FetchObrasStep(sigrid, "SELECT ... FROM dbo.obr",
                          universo=UniversoFalso(), empresa_obras=1),
        sp.UpsertTrabajadoresStep(),
        sp.UpsertObrasStep(),
    ]).ejecutar(_Uow())
    assert resultado.incidencias == ResultadoSyncMaestro()


def test_f030_r7_sync_falla_entero_si_la_lectura_falla_o_viene_truncada():
    """El cliente de sigrid-api lanza `SigridError` ante un error o un
    `truncated` (lo fija `test_f030_r7_el_cliente_lanza_ante_truncated`): el
    sync falla como con cualquier maestro, sin persistir ni confirmar."""
    from domain.errors import SigridError

    uow = _Uow()
    with pytest.raises(SigridError, match="truncado"):
        _pipeline(_Sigrid(fallo=SigridError("Resultado truncado"))).ejecutar(uow)
    assert uow.trabajadores.recibido is None
    assert uow.tipos_incidencia.recibido is None
    assert uow.commits == 0


@pytest.mark.parametrize("falta", ["ide", "cod", "res", "fecbaj"])
def test_f030_r7_sync_sin_las_columnas_no_guarda_nada(falta):
    from application import sync_pipeline as sp

    filas = [{k: v for k, v in AUXHOR[0].items() if k != falta}]
    uow = _Uow()
    with pytest.raises(ValueError, match=rf"sync\.incidencias\.sql.*{falta}"):
        sp.SyncMaestrosPipeline([
            sp.FetchTiposIncidenciaStep(_Sigrid(filas), SQL_INC),
            sp.UpsertTiposIncidenciaStep(),
        ]).ejecutar(uow)
    assert uow.tipos_incidencia.recibido is None
    assert uow.commits == 0


def test_f030_r7_el_cliente_lanza_ante_truncated(monkeypatch):
    from config.settings import Settings
    from domain.errors import SigridError
    from infrastructure.sigrid import sigrid_client

    class _Resp:
        status_code = 200
        text = ""

        def json(self) -> dict[str, Any]:
            return {"ok": True, "truncated": True, "columns": ["ide"],
                    "rows": [[1]]}

    monkeypatch.setattr(sigrid_client.httpx, "post", lambda *a, **k: _Resp())
    cliente = sigrid_client.SigridApiClient(Settings(
        _env_file=None, sigrid_api_base_url="http://x",
        sigrid_api_function_key="k"))
    with pytest.raises(SigridError, match="truncado"):
        cliente.leer(SQL_INC)


def _preview(sigrid: _Sigrid, sql_inc: str | None = SQL_INC) -> Any:
    from application.use_cases import PreviewSync

    return PreviewSync(sigrid, "SELECT ... FROM dbo.emp",
                       "SELECT ... FROM dbo.obr",
                       sql_empresas="SELECT ... FROM dbo.auxemp",
                       sql_incidencias=sql_inc,
                       universo=UniversoFalso(), empresa_obras=1)


def test_f030_r3_preview_informa_del_catalogo_sin_persistir():
    sigrid = _Sigrid(AUXHOR + [_fila(18, "CIH", "Huelga(H)", 20240101)])
    salida = _preview(sigrid).ejecutar()
    assert salida["incidencias"] == {
        "leidas": 5,
        "activas": 4,
        "de_baja": ["CIH"],
        "letras": {"CIA": "AT · Accidente/Enf. Profesional",
                   "CIE": "B · Enfermedad/Acc. no laboral",
                   "CIP": "FJ · Falta Justificada/Permiso",
                   "CIV": "V · Vacaciones",
                   "CIH": "H · Huelga"},
    }
    # Se lee antes que las empresas, que siguen siendo la última lectura.
    assert sigrid.leidas[-2:] == [SQL_INC, "SELECT ... FROM dbo.auxemp"]


def test_f030_r3_preview_sin_ide_o_sin_codigo_no_cuenta():
    """Mutación: basta con que falte UNO de los dos para que la fila no
    cuente (como en el sync), y una fila sin los dos tampoco."""
    filas = [_fila(None, "CIX", "Sin ide(X)"), _fila(19, "", "Sin código(Y)"),
             _fila(None, None, "Nada(Z)"), *AUXHOR[:1]]
    salida = _preview(_Sigrid(filas)).ejecutar()
    assert salida["incidencias"] == {
        "leidas": 4, "activas": 1, "de_baja": [],
        "letras": {"CIA": "AT · Accidente/Enf. Profesional"}}


def test_f030_r3_preview_sin_columnas_avisa_como_el_sync():
    filas = [{k: v for k, v in AUXHOR[0].items() if k != "res"}]
    with pytest.raises(ValueError, match=r"sync\.incidencias\.sql.*res"):
        _preview(_Sigrid(filas)).ejecutar()


def test_f030_r3_preview_sin_consulta_no_lee_auxhor():
    sigrid = _Sigrid()
    salida = _preview(sigrid, sql_inc=None).ejecutar()
    assert "incidencias" not in salida
    assert not any("dbo.auxhor" in sql for sql in sigrid.leidas)


def _contenedor(monkeypatch: pytest.MonkeyPatch, sigrid: _Sigrid) -> Any:
    from config.settings import Settings
    from interface_adapters.api import deps

    from tests.test_f023_sync_empresa import _UowLectura

    monkeypatch.setattr(deps, "SigridApiClient", lambda _s: sigrid)
    monkeypatch.setattr(deps, "SqlAlchemyUnitOfWork", _UowLectura)
    monkeypatch.setattr(deps, "TransferClient", lambda _s: UniversoFalso())
    return deps.construir_contenedor(Settings(_env_file=None), None)  # type: ignore[arg-type]


def test_f030_r3_el_sync_y_el_preview_reales_usan_la_consulta_de_config(monkeypatch):
    from config.settings import cargar_config

    sql = cargar_config()["sync"]["incidencias"]["sql"]
    sigrid, uow = _Sigrid(), _Uow()
    contenedor = _contenedor(monkeypatch, sigrid)
    resultado = contenedor.sync_pipeline.ejecutar(uow)
    assert sql in sigrid.leidas
    assert uow.tipos_incidencia.recibido == AUXHOR
    assert resultado.incidencias.recibidos == 4
    sigrid.leidas.clear()
    assert contenedor.preview_sync.ejecutar()["incidencias"]["leidas"] == 4
    assert sql in sigrid.leidas


def test_f030_r3_la_respuesta_del_sync_trae_el_catalogo():
    from domain.models import ResultadoSync, ResultadoSyncMaestro
    from interface_adapters.api.schemas import a_sync_out

    salida = a_sync_out(ResultadoSync(
        empleados=ResultadoSyncMaestro(recibidos=3),
        obras=ResultadoSyncMaestro(recibidos=2), duracion_s=1.0,
        incidencias=ResultadoSyncMaestro(recibidos=7, altas=1, desactivados=2)))
    assert salida.model_dump()["incidencias"] == {
        "recibidos": 7, "altas": 1, "actualizados": 0, "desactivados": 2}


# ------------------------------ ruta (R6) -------------------------------- #
def test_f030_r6_ruta_incidencias_activas_por_letra():
    from config.settings import Settings
    from domain.models import TipoIncidencia
    from fastapi.testclient import TestClient
    from interface_adapters.api.app import build_app
    from interface_adapters.api.deps import obtener_contenedor

    from tests.test_f024_rutas_empresa import _Contenedor, _UowCM

    class _Tipos:
        def activos(self):
            return [TipoIncidencia(11, "CIA", "AT", "Accidente"),
                    TipoIncidencia(12, "CIE", "B", "Enfermedad"),
                    TipoIncidencia(17, "CIV", "V", "Vacaciones")]

    uow = _UowCM({})
    uow.tipos_incidencia = _Tipos()
    settings = Settings(_env_file=None)
    app = build_app(settings)
    app.dependency_overrides[obtener_contenedor] = lambda: _Contenedor(
        settings=settings, uow=lambda: uow)
    r = TestClient(app).get("/api/v1/incidencias")
    assert r.status_code == 200, r.text
    # F-061 (lista cerrada, autorizado por el humano el 2026-10-23): cada
    # incidencia trae además `palabras` y `orden_busqueda` de config.yaml.
    assert r.json() == {"incidencias": [
        {"codigo": "CIA", "letra": "AT", "nombre": "Accidente",
         "palabras": ["baja", "accidente de trabajo"], "orden_busqueda": 1},
        {"codigo": "CIE", "letra": "B", "nombre": "Enfermedad",
         "palabras": ["baja", "IT", "enfermedad común"], "orden_busqueda": 0},
        {"codigo": "CIV", "letra": "V", "nombre": "Vacaciones",
         "palabras": [], "orden_busqueda": 5}]}
