# tests/test_f023_sync_empresa.py
"""Tests offline de F-023: empresa en los maestros y activo según el recurso.

Trazabilidad con `specs/F-023-sync-empresa-y-estado-recurso/requirements.md`
(R1-R18; R19 es MANUAL, tasks T10). Tabla de design §6.

Nada abre un socket ni una conexión: las filas de Sigrid son dicts, el
`SigridGateway` es un doble que devuelve listas, el repositorio trabaja
contra una sesión doble (patrón de `test_f003_esquema.py`) y el DDL se
compila con el dialecto PostgreSQL sin motor.

Los módulos que F-023 crea o amplía se importan DENTRO de los tests, no en
la cabecera: así cada tarea de `tasks.md` puede verificarse con su `-k` sin
que el fichero entero caiga en la colección por lo que aún no existe.
"""
from __future__ import annotations

import dataclasses
import re
from typing import Any

import pytest
from domain.models import ResultadoSyncMaestro
from infrastructure.db.orm_models import Base, ObraORM, TrabajadorORM
from sqlalchemy.dialects import postgresql

DIALECTO = postgresql.dialect()
SQL_EMP = "SELECT ... FROM dbo.emp AS emp"
SQL_OBR = "SELECT ... FROM dbo.obr AS obr"
#: Desde F-026 (R13) solo cae la baja ANTERIOR a la ventana de bajas.
FECHA_BAJA = "(baja anterior a la ventana)"
#: Ventana de bajas de las pruebas de depuración (1 de septiembre de 2026).
VENTANA = 20260901
AUXILIARES = ("cif", "estado_recurso", "baja_laboral")


# --- Fixtures de filas --------------------------------------------------------


def _emp(ide: int, **cambios: Any) -> dict[str, Any]:
    """Fila de `sync.empleados.sql` de un recurso activo de la empresa 1.

    Desde F-026 (R1) una fila por recurso: sin `recurso_ide` ni
    `empresa_recurso`, y la baja del recurso se llama `fecha_baja`."""
    fila: dict[str, Any] = {
        "ide": ide,
        "cod": f"E{ide}",
        "nombre": f"Persona {ide}",
        "dni": f"{ide:08d}X",
        "empresa": 1,
        "categoria": "Técnico",
        "estado_recurso": "Activo",
        "fecha_baja": None,
        "baja_laboral": 0,
        "cod_hora_mes": "MENC",
        "importe_mes": 100,
    }
    fila.update(cambios)
    return fila


def _obr(ide: int, **cambios: Any) -> dict[str, Any]:
    fila: dict[str, Any] = {
        "ide": ide,
        "cod": f"0{ide}",
        "descripcion": f"Obra {ide}",
        "estado_sigrid": "En curso",
        "empresa": 1,
    }
    fila.update(cambios)
    return fila


def _filtros() -> Any:
    from application import filtros_maestros

    return filtros_maestros


def _criterio(**kwargs: Any) -> Any:
    return _filtros().CriterioActivoRecurso(**kwargs)


def _depurar(filas: list[dict[str, Any]], **kwargs: Any) -> Any:
    return _filtros().depurar_empleados(filas, [], False, **kwargs)


def _ides(filas: list[dict[str, Any]]) -> list[int]:
    return sorted(int(f["ide"]) for f in filas)


# --- Dobles de prueba ---------------------------------------------------------


class _Resultado:
    def __init__(self, filas: list[Any]) -> None:
        self._filas = filas

    def all(self) -> list[Any]:
        return list(self._filas)


class _SesionRepo:
    """Sesión doble: `scalars()` devuelve las filas previas, `add` las apunta."""

    def __init__(self, previas: list[Any] | None = None) -> None:
        self.previas = list(previas or [])
        self.anadidas: list[Any] = []

    def scalars(self, _sentencia: Any) -> _Resultado:
        return _Resultado(self.previas)

    def add(self, orm: Any) -> None:
        self.anadidas.append(orm)

    def get(self, _modelo: Any, ide: int) -> Any:
        return next((o for o in self.previas if o.ide == ide), None)


class _SigridFalso:
    """Devuelve filas según la consulta sea de empleados o de obras."""

    def __init__(self, empleados: list[dict[str, Any]],
                 obras: list[dict[str, Any]]) -> None:
        self._empleados = empleados
        self._obras = obras

    def leer(self, sql: str) -> list[dict[str, Any]]:
        if "dbo.auxemp" in sql:  # catálogo de empresas (F-032): fuera de F-023
            return []
        origen = self._obras if "dbo.obr" in sql else self._empleados
        return [dict(fila) for fila in origen]


class _RepoEspia:
    def __init__(self) -> None:
        self.recibido: list[dict[str, Any]] | None = None

    def sincronizar(self, filas: list[dict[str, Any]]) -> ResultadoSyncMaestro:
        self.recibido = [dict(f) for f in filas]
        return ResultadoSyncMaestro(recibidos=len(filas))


class _UowEspia:
    def __init__(self) -> None:
        self.trabajadores = _RepoEspia()
        self.obras = _RepoEspia()
        self.empresas = _RepoEspia()  # paso de empresas del sync (F-032)
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


def _pipeline(sigrid: _SigridFalso, criterio: Any = None) -> Any:
    from application import sync_pipeline as sp

    extra = {} if criterio is None else {"criterio": criterio}
    return sp.SyncMaestrosPipeline([
        sp.FetchEmpleadosStep(sigrid, SQL_EMP, **extra),
        sp.FetchObrasStep(sigrid, SQL_OBR),
        sp.UpsertTrabajadoresStep(),
        sp.UpsertObrasStep(),
    ])


def _preview(sigrid: _SigridFalso, criterio: Any = None) -> Any:
    from application.use_cases import PreviewSync

    extra = {} if criterio is None else {"criterio": criterio}
    return PreviewSync(sigrid, SQL_EMP, SQL_OBR, **extra)


# --- R1-R2: esquema derivado del ORM ------------------------------------------


@pytest.mark.parametrize("modelo", [TrabajadorORM, ObraORM])
def test_f023_r1_columna_empresa_integer_nulable_sin_default(modelo: Any) -> None:
    columna = modelo.__table__.columns["empresa"]
    assert columna.type.compile(dialect=DIALECTO) == "INTEGER"
    assert columna.nullable is True
    assert columna.default is None
    assert columna.server_default is None


def test_f023_r1_empresa_solo_en_trabajador_y_obra() -> None:
    con_empresa = {t.name for t in Base.metadata.tables.values()
                   if "empresa" in t.columns}
    assert con_empresa == {"trabajador", "obra"}


def test_f023_r2_alters_de_una_base_sin_empresa() -> None:
    from infrastructure.db.esquema import alters_faltantes

    existentes = {t.name: {c.name for c in t.columns}
                  for t in Base.metadata.tables.values()}
    existentes["trabajador"].discard("empresa")
    existentes["obra"].discard("empresa")
    assert alters_faltantes(Base.metadata, existentes) == [
        "ALTER TABLE trabajador ADD COLUMN IF NOT EXISTS empresa INTEGER",
        "ALTER TABLE obra ADD COLUMN IF NOT EXISTS empresa INTEGER",
    ]


# --- R3-R5: consultas versionadas en config.yaml ------------------------------


def _config_sync() -> dict[str, Any]:
    from config.settings import cargar_config

    return cargar_config()["sync"]


def _plano(sql: str) -> str:
    return " ".join(sql.split())


def test_f023_r3_obras_devuelven_empresa_de_su_ficha() -> None:
    assert "con.emp AS empresa," in _plano(_config_sync()["obras"]["sql"])


def test_f023_r4_empleados_devuelven_los_cinco_alias() -> None:
    """Desde F-026 (R1) la empresa, el estado y la baja salen del concepto
    del RECURSO (`rcon`), que es la fila base: ya no hay `empresa_recurso`."""
    sql = _plano(_config_sync()["empleados"]["sql"])
    for esperado in (
        "rcon.emp AS empresa,",
        "COALESCE(rest.res, CAST(rcon.est AS VARCHAR(16))) AS estado_recurso,",
        "NULLIF(rcon.fecbaj, 0) AS fecha_baja,",
        "uh.fecbaj AS baja_laboral,",
        "JOIN dbo.con AS rcon ON rcon.ide = res.ide",
        "LEFT JOIN dbo.conest AS rest ON rest.tip = rcon.tip AND rest.est = rcon.est",
    ):
        assert esperado in sql, esperado


def test_f023_r5_empleados_sin_filtro_de_emphis() -> None:
    sql = _plano(_config_sync()["empleados"]["sql"])
    assert "COALESCE(uh.fecbaj" not in sql
    # Tras las subconsultas OUTER APPLY solo queda el WHERE de clase persona
    # de F-026 R1, que no mira ninguna fecha de baja.
    principal = re.split(r"\)\s*AS hm\s+", sql, maxsplit=1)[1]
    assert re.fullmatch(r"WHERE res\.cla = 1 ORDER BY [^()]*", principal)
    assert "fecbaj" not in principal


def test_f023_r5_config_inactivo_es_la_fecha_de_baja_del_recurso() -> None:
    """D1 de F-023 (2026-10-01): inactivo por `con.fecbaj` del recurso, y
    desde F-026 (D3) solo si la baja es anterior a la ventana. La lista de
    literales queda vacía: el tipo 33 no tiene estados en `conest`."""
    cfg = _config_sync()["empleados"]
    assert cfg["filtro_estado_recurso"] is True
    assert cfg["estados_recurso_excluidos"] == []
    assert cfg["excluir_baja_anterior_a_ventana"] is True


# --- R6: sin columna `empresa` no se persiste nada ----------------------------


@pytest.mark.parametrize(("sin_empresa", "consulta"), [
    ("empleados", "sync.empleados.sql"),
    ("obras", "sync.obras.sql"),
])
def test_f023_r6_pipeline_falla_sin_empresa_y_no_persiste(
    sin_empresa: str, consulta: str
) -> None:
    empleados, obras = [_emp(1)], [_obr(1)]
    for fila in (empleados if sin_empresa == "empleados" else obras):
        del fila["empresa"]
    uow = _UowEspia()
    with pytest.raises(ValueError) as fallo:
        _pipeline(_SigridFalso(empleados, obras), _criterio()).ejecutar(uow)
    assert consulta in str(fallo.value)
    assert "'empresa'" in str(fallo.value)
    assert uow.trabajadores.recibido is None
    assert uow.obras.recibido is None
    assert uow.commits == 0


@pytest.mark.parametrize(("sin_empresa", "consulta"), [
    ("empleados", "sync.empleados.sql"),
    ("obras", "sync.obras.sql"),
])
def test_f023_r6_preview_falla_sin_empresa(sin_empresa: str, consulta: str) -> None:
    empleados, obras = [_emp(1)], [_obr(1)]
    for fila in (empleados if sin_empresa == "empleados" else obras):
        del fila["empresa"]
    with pytest.raises(ValueError) as fallo:
        _preview(_SigridFalso(empleados, obras), _criterio()).ejecutar()
    assert consulta in str(fallo.value)
    assert "'empresa'" in str(fallo.value)


def test_f023_r6_las_demas_columnas_requeridas_se_siguen_exigiendo() -> None:
    sin_nombre = [{k: v for k, v in _emp(1).items() if k != "nombre"}]
    with pytest.raises(ValueError, match="nombre"):
        _pipeline(_SigridFalso(sin_nombre, [_obr(1)]), _criterio()).ejecutar(
            _UowEspia())
    sin_cod = [{k: v for k, v in _obr(1).items() if k != "cod"}]
    with pytest.raises(ValueError, match="cod"):
        _preview(_SigridFalso([_emp(1)], sin_cod), _criterio()).ejecutar()


# --- R7-R8: el repositorio guarda la empresa ----------------------------------


def _repos() -> Any:
    from infrastructure.db import repositories

    return repositories


def test_f023_r7_mismo_codigo_en_dos_empresas_son_dos_obras() -> None:
    sesion = _SesionRepo()
    res = _repos().PgObraRepository(sesion).sincronizar([
        _obr(100, cod="0658", empresa=1),
        _obr(200, cod="0658", empresa=28),
    ])
    assert res.altas == 2
    assert sorted((o.ide, o.cod, o.empresa) for o in sesion.anadidas) == [
        (100, "0658", 1), (200, "0658", 28)]


def test_f023_r8_alta_de_trabajador_guarda_su_empresa() -> None:
    sesion = _SesionRepo()
    res = _repos().PgTrabajadorRepository(sesion).sincronizar([_emp(7, empresa=18)])
    assert res.altas == 1
    assert [(t.ide, t.empresa) for t in sesion.anadidas] == [(7, 18)]


def _trabajador_orm(ide: int, empresa: int | None) -> TrabajadorORM:
    fila = _emp(ide)
    return TrabajadorORM(ide=ide, cod=fila["cod"], nombre=fila["nombre"],
                         dni=fila["dni"], categoria=fila["categoria"],
                         activo=True, empresa=empresa)


def _obra_orm(ide: int, empresa: int | None) -> ObraORM:
    fila = _obr(ide)
    return ObraORM(ide=ide, cod=fila["cod"], descripcion=fila["descripcion"],
                   estado_sigrid=fila["estado_sigrid"], activa=True,
                   empresa=empresa)


@pytest.mark.parametrize(("previa", "nueva", "actualizados"), [
    (1, 28, 1),       # cambio de empresa: cuenta como actualizado
    (None, 1, 1),     # fila anterior a F-023: el sync la rellena
    (28, 28, 0),      # nada cambia
])
def test_f023_r8_cambio_de_empresa_en_obra(
    previa: int | None, nueva: int, actualizados: int
) -> None:
    existente = _obra_orm(100, previa)
    res = _repos().PgObraRepository(_SesionRepo([existente])).sincronizar(
        [_obr(100, empresa=nueva)])
    assert (res.altas, res.actualizados) == (0, actualizados)
    assert existente.empresa == nueva


@pytest.mark.parametrize(("previa", "nueva", "actualizados"), [
    (1, 18, 1),
    (None, 1, 1),
    (18, 18, 0),
])
def test_f023_r8_cambio_de_empresa_en_trabajador(
    previa: int | None, nueva: int, actualizados: int
) -> None:
    existente = _trabajador_orm(7, previa)
    res = _repos().PgTrabajadorRepository(_SesionRepo([existente])).sincronizar(
        [_emp(7, empresa=nueva)])
    assert (res.altas, res.actualizados) == (0, actualizados)
    assert existente.empresa == nueva


def test_f023_r8_empresa_en_texto_se_guarda_como_entero() -> None:
    sesion = _SesionRepo()
    _repos().PgObraRepository(sesion).sincronizar([_obr(1, empresa="28")])
    assert sesion.anadidas[0].empresa == 28


def test_f023_r8_empresa_nula_se_guarda_nula() -> None:
    sesion = _SesionRepo()
    _repos().PgTrabajadorRepository(sesion).sincronizar([_emp(7, empresa=None)])
    assert sesion.anadidas[0].empresa is None


def test_f023_r8_el_dominio_expone_la_empresa() -> None:
    repos = _repos()
    trabajador = repos.PgTrabajadorRepository(
        _SesionRepo([_trabajador_orm(7, 18)])).obtener(7)
    assert trabajador is not None and trabajador.empresa == 18
    obras = repos.PgObraRepository(
        _SesionRepo([_obra_orm(100, 28)])).listar_para_periodo(1)
    assert [(o.ide, o.empresa) for o in obras] == [(100, 28)]


# --- R9-R11: retirados por F-026 --------------------------------------------
# El descarte por empresa del recurso y los dedupes por empleado y por
# persona ya no existen (F-026 R3, R6): los sustituyen
# `test_f026_r3_*` y `test_f026_r4_*` de `test_f026_sync_recurso.py`.


# --- R12-R16: activo según el estado del recurso ------------------------------


def test_f023_r12_estado_excluido_se_descarta_por_su_literal_original() -> None:
    res = _depurar([
        _emp(1, estado_recurso="BAJA definitiva"),
        _emp(2, estado_recurso="Dado de baja"),
        _emp(3, estado_recurso="Activo"),
        _emp(4, estado_recurso=None),
    ], criterio=_criterio(estados_excluidos=("Bajá",)))
    assert _ides(res.filas) == [3, 4]
    assert dict(res.excluidos_estado_recurso) == {
        "BAJA definitiva": 1, "Dado de baja": 1}


def test_f023_r12_literal_vacio_no_excluye_a_nadie() -> None:
    res = _depurar([_emp(1), _emp(2, estado_recurso=None)],
                   criterio=_criterio(estados_excluidos=("  ",)))
    assert _ides(res.filas) == [1, 2]
    assert not res.excluidos_estado_recurso


def test_f023_r12_interruptor_apagado_no_filtra_por_estado() -> None:
    res = _depurar([_emp(1, estado_recurso="Baja", fecha_baja=80000)],
                   criterio=_criterio(estados_excluidos=("baja",),
                                      excluir_baja_anterior_a_ventana=True,
                                      activo=False),
                   baja_desde=VENTANA)
    assert _ides(res.filas) == [1]
    assert not res.excluidos_estado_recurso


def test_f023_r13_fecha_de_baja_del_recurso_con_interruptor() -> None:
    filas = [
        _emp(1, fecha_baja=80000),
        _emp(2, fecha_baja=0),
        _emp(3, fecha_baja=None),
        _emp(4, fecha_baja=1),
    ]
    encendido = _depurar(filas, criterio=_criterio(
        excluir_baja_anterior_a_ventana=True), baja_desde=VENTANA)
    assert _ides(encendido.filas) == [2, 3]
    assert dict(encendido.excluidos_estado_recurso) == {FECHA_BAJA: 2}
    apagado = _depurar(filas, criterio=_criterio(
        excluir_baja_anterior_a_ventana=False), baja_desde=VENTANA)
    assert _ides(apagado.filas) == [1, 2, 3, 4]
    assert not apagado.excluidos_estado_recurso


def test_f023_r13_estado_y_fecha_a_la_vez_se_cuentan_una_sola_vez() -> None:
    res = _depurar([_emp(1, estado_recurso="Baja", fecha_baja=80000)],
                   criterio=_criterio(estados_excluidos=("baja",),
                                      excluir_baja_anterior_a_ventana=True),
                   baja_desde=VENTANA)
    assert dict(res.excluidos_estado_recurso) == {"Baja": 1}


# R14 retirado por F-026: sin dedupe por empleado no hay recurso «más
# reciente» que pueda tapar a otro (una fila por recurso, R3).


def test_f023_r15_baja_laboral_no_excluye_pero_se_cuenta() -> None:
    res = _depurar([
        _emp(1, baja_laboral=80000),
        _emp(2, baja_laboral=0),
        _emp(3, baja_laboral=None),
        _emp(4, baja_laboral=1, cod_hora_mes=None),   # cae por código mensual
        _emp(5, baja_laboral=1),                      # cualquier fecha > 0
    ], criterio=_criterio())
    assert _ides(res.filas) == [1, 2, 3, 5]
    assert res.con_baja_laboral == 2


def test_f023_r16_criterio_vacio_no_descarta_por_estado() -> None:
    filas = [
        _emp(1, estado_recurso="Baja", fecha_baja=80000),
        _emp(2, estado_recurso="Activo"),
    ]
    sin_criterio = _depurar([dict(f) for f in filas])
    con_criterio = _depurar([dict(f) for f in filas], criterio=_criterio())
    assert _ides(sin_criterio.filas) == _ides(con_criterio.filas) == [1, 2]
    assert not con_criterio.excluidos_estado_recurso


def test_f023_r16_criterio_por_defecto_es_vacio() -> None:
    criterio = _criterio()
    assert criterio.estados_excluidos == ()
    assert criterio.excluir_baja_anterior_a_ventana is False
    assert criterio.activo is True


def test_f023_r16_criterio_es_inmutable() -> None:
    """El criterio por defecto es UNA instancia compartida (valor por defecto
    de `depurar_empleados`, del step y del preview): si se pudiera mutar, un
    cambio en un sitio alteraría el filtro de todos los demás."""
    criterio = _criterio()
    with pytest.raises(dataclasses.FrozenInstanceError):
        criterio.activo = False  # type: ignore[misc]


# --- R17: el preview publica los recuentos nuevos -----------------------------


def test_f023_r17_preview_publica_claves_nuevas_y_antiguas() -> None:
    empleados = [
        _emp(1, empresa=1, baja_laboral=80000),
        _emp(2, empresa=1),
        _emp(3, empresa=18, empresa_recurso=18),
        _emp(4, empresa=1, empresa_recurso=18),              # ya no filtra
        _emp(5, estado_recurso="Baja definitiva"),           # estado
        _emp(6, fecha_baja=80000),                           # baja anterior
        _emp(7, cod_hora_mes=None),                          # sin código M*
        _emp(2, recurso_ide=5),                              # ya no se funde
    ]
    obras = [
        _obr(1, empresa=1),
        _obr(2, empresa=28),
        _obr(3, estado_sigrid="Terminada"),
    ]
    from application.use_cases import PreviewSync

    salida = PreviewSync(
        _SigridFalso(empleados, obras), SQL_EMP, SQL_OBR,
        estados_excluidos=["terminada"],
        criterio=_criterio(estados_excluidos=("baja",),
                           excluir_baja_anterior_a_ventana=True),
    ).ejecutar()
    emp, obr = salida["empleados"], salida["obras"]
    assert emp["excluidos_por_estado_recurso"] == {
        "Baja definitiva": 1, FECHA_BAJA: 1}
    for retirada in ("excluidos_recurso_otra_empresa", "duplicados_recurso",
                     "duplicados_persona"):
        assert retirada not in emp, retirada          # F-026 R6
    assert emp["con_baja_laboral"] == 1
    assert emp["por_empresa"] == {"1": 4, "18": 1}
    assert emp["brutos"] == 8
    assert emp["posible_misma_persona"] == [["E2", "E2"]]   # F-026 R4
    assert emp["excluidos_sin_codigo_mes"] == 1
    assert emp["excluidos_por_categoria"] == {"(sin código de hora mensual)": 1}
    assert emp["por_codigo_mes"] == {"MENC": 5}
    assert emp["por_categoria"] == {"Técnico": 5}
    assert emp["total"] == 5
    assert _ides(emp["muestra"]) == [1, 2, 2, 3, 4]
    assert obr["por_empresa"] == {"1": 1, "28": 1}
    assert obr["brutas"] == 3
    assert obr["excluidas_por_estado"] == {"Terminada": 1}
    assert obr["total"] == 2
    assert obr["por_estado"] == {"En curso": 2}
    assert _ides(obr["muestra"]) == [1, 2]


def test_f023_r17_empresa_nula_se_publica_como_sin_empresa() -> None:
    salida = _preview(_SigridFalso(
        [_emp(1, empresa=None, empresa_recurso=None)],
        [_obr(1, empresa=None)]), _criterio()).ejecutar()
    assert salida["empleados"]["por_empresa"] == {"(sin empresa)": 1}
    assert salida["obras"]["por_empresa"] == {"(sin empresa)": 1}


# --- R18: preview y sync depuran igual, con la misma configuración ------------


def test_f023_r18_upsert_recibe_empresa_sin_columnas_auxiliares() -> None:
    res = _depurar([_emp(1, empresa=18, empresa_recurso=18)],
                   criterio=_criterio())
    (fila,) = res.filas
    assert fila["empresa"] == 18
    for columna in AUXILIARES:
        assert columna not in fila, columna


def _config_prueba(criterio: dict[str, Any]) -> dict[str, Any]:
    return {
        "sync": {
            "empleados": {"sql": SQL_EMP, **criterio},
            "obras": {"sql": SQL_OBR, "estados_excluidos": ["terminada"]},
            # Obligatoria desde F-032 (catálogo de empresas).
            "empresas": {"sql": "SELECT ... FROM dbo.auxemp AS aux"},
        },
        "export": {"prefijo_postventa": "PV"},
    }


def _contenedor(monkeypatch: pytest.MonkeyPatch, sigrid: _SigridFalso,
                config: dict[str, Any] | None = None) -> Any:
    from config.settings import Settings
    from interface_adapters.api import deps

    monkeypatch.setattr(deps, "SigridApiClient", lambda _settings: sigrid)
    if config is not None:
        monkeypatch.setattr(deps, "cargar_config", lambda: config)
    return deps.construir_contenedor(Settings(_env_file=None), None)


def _mismos_netos(contenedor: Any) -> tuple[list[int], list[int]]:
    uow = _UowEspia()
    contenedor.sync_pipeline.ejecutar(uow)
    preview = contenedor.preview_sync.ejecutar()
    assert uow.trabajadores.recibido is not None
    assert uow.obras.recibido is not None
    assert preview["empleados"]["total"] == len(uow.trabajadores.recibido)
    assert preview["obras"]["total"] == len(uow.obras.recibido)
    netos_emp = _ides(uow.trabajadores.recibido)
    netos_obr = _ides(uow.obras.recibido)
    assert _ides(preview["empleados"]["muestra"]) == netos_emp
    assert _ides(preview["obras"]["muestra"]) == netos_obr
    return netos_emp, netos_obr


def _entrada_r18() -> _SigridFalso:
    return _SigridFalso(
        [_emp(1), _emp(2, estado_recurso="Baja"), _emp(3, fecha_baja=80000),
         _emp(4, empresa_recurso=18)],
        [_obr(1), _obr(2, estado_sigrid="Terminada")],
    )


def test_f023_r18_preview_y_sync_aplican_el_mismo_criterio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contenedor = _contenedor(monkeypatch, _entrada_r18(), _config_prueba({
        "filtro_estado_recurso": True,
        "estados_recurso_excluidos": ["baja"],
        "excluir_baja_anterior_a_ventana": True,
    }))
    assert _mismos_netos(contenedor) == ([1, 4], [1])


def test_f023_r18_interruptor_general_apagado_llega_a_los_dos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contenedor = _contenedor(monkeypatch, _entrada_r18(), _config_prueba({
        "filtro_estado_recurso": False,
        "estados_recurso_excluidos": ["baja"],
        "excluir_baja_anterior_a_ventana": True,
    }))
    assert _mismos_netos(contenedor) == ([1, 2, 3, 4], [1])


def test_f023_r18_config_sin_claves_de_recurso_no_filtra_por_estado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un config.yaml anterior a F-023 (sin las tres claves) se comporta como
    el criterio vacío (R16): los valores por defecto no filtran."""
    contenedor = _contenedor(monkeypatch, _entrada_r18(), _config_prueba({}))
    assert _mismos_netos(contenedor) == ([1, 2, 3, 4], [1])


def test_f023_r18_filtro_estado_recurso_encendido_por_defecto(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Con literales y sin el interruptor explícito, el filtro se aplica."""
    contenedor = _contenedor(monkeypatch, _entrada_r18(), _config_prueba({
        "estados_recurso_excluidos": ["baja"],
    }))
    assert _mismos_netos(contenedor) == ([1, 3, 4], [1])


def test_f023_r18_con_el_config_real_cae_el_recurso_con_fecha_de_baja(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D1 cerrada: con `config.yaml` tal cual, cae el recurso con fecha de
    baja anterior a la ventana (R13, F-026 R13) y cuenta como tal; el 2
    sigue aunque su estado diga «Baja» porque la lista de literales está
    vacía; y el 4 ya no cae por la empresa del recurso (F-026 R3). Preview
    y sync, con los mismos netos."""
    contenedor = _contenedor(monkeypatch, _entrada_r18())
    assert _mismos_netos(contenedor) == ([1, 2, 4], [1])
    emp = contenedor.preview_sync.ejecutar()["empleados"]
    assert emp["excluidos_por_estado_recurso"] == {FECHA_BAJA: 1}
    assert "excluidos_recurso_otra_empresa" not in emp
