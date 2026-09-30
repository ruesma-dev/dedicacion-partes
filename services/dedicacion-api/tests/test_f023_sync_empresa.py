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
FECHA_BAJA = "(fecha de baja del recurso)"
AUXILIARES = ("recurso_ide", "empresa_recurso", "estado_recurso",
              "baja_recurso", "baja_laboral")


# --- Fixtures de filas --------------------------------------------------------


def _emp(ide: int, **cambios: Any) -> dict[str, Any]:
    """Fila de `sync.empleados.sql` de un recurso activo de la empresa 1."""
    fila: dict[str, Any] = {
        "ide": ide,
        "cod": f"E{ide}",
        "nombre": f"Persona {ide}",
        "dni": f"{ide:08d}X",
        "empresa": 1,
        "categoria": "Técnico",
        "recurso_ide": ide * 10,
        "empresa_recurso": 1,
        "estado_recurso": "Activo",
        "baja_recurso": 0,
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
    sql = _plano(_config_sync()["empleados"]["sql"])
    for esperado in (
        "con.emp AS empresa,",
        "rcon.emp AS empresa_recurso,",
        "COALESCE(rest.res, CAST(rcon.est AS VARCHAR(16))) AS estado_recurso,",
        "rcon.fecbaj AS baja_recurso,",
        "uh.fecbaj AS baja_laboral,",
        "LEFT JOIN dbo.con AS rcon ON rcon.ide = res.ide",
        "LEFT JOIN dbo.conest AS rest ON rest.tip = rcon.tip AND rest.est = rcon.est",
    ):
        assert esperado in sql, esperado


def test_f023_r5_empleados_sin_filtro_de_emphis() -> None:
    sql = _plano(_config_sync()["empleados"]["sql"])
    assert "COALESCE(uh.fecbaj" not in sql
    # El único WHERE que queda es el de las subconsultas OUTER APPLY.
    assert not re.search(r"\)\s*AS hm\s+WHERE", sql)


def test_f023_r5_config_criterio_del_recurso_entra_vacio_por_d1() -> None:
    cfg = _config_sync()["empleados"]
    assert cfg["filtro_estado_recurso"] is True
    assert cfg["estados_recurso_excluidos"] == []
    assert cfg["excluir_recurso_con_fecha_baja"] is False


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


# --- R9: recurso de otra empresa ----------------------------------------------


def test_f023_r9_recurso_de_otra_empresa_se_descarta_y_se_cuenta() -> None:
    res = _depurar([
        _emp(1, empresa=1, empresa_recurso=18),
        _emp(2, empresa=1, empresa_recurso=1),
        _emp(3, empresa=1, empresa_recurso=None),
    ], criterio=_criterio())
    assert _ides(res.filas) == [2, 3]
    assert res.excluidos_otra_empresa == 1
    assert res.brutos == 3


def test_f023_r9_empresa_nula_con_recurso_informado_se_descarta() -> None:
    res = _depurar([_emp(1, empresa=None, empresa_recurso=1)],
                   criterio=_criterio())
    assert res.filas == []
    assert res.excluidos_otra_empresa == 1


def test_f023_r9_la_empresa_del_recurso_se_descarta_aun_sin_criterio_activo() -> None:
    res = _depurar([_emp(1, empresa_recurso=18)],
                   criterio=_criterio(activo=False))
    assert res.filas == [] and res.excluidos_otra_empresa == 1


# --- R10-R11: dedupe por persona dentro de cada empresa -----------------------


def test_f023_r10_mismo_dni_misma_empresa_queda_una_ficha() -> None:
    res = _depurar([
        _emp(1, dni="12.345.678-a", empresa=1),
        _emp(2, dni="12345678A", empresa=1),
    ])
    assert _ides(res.filas) == [2]      # misma preferencia que hoy: ide mayor
    assert res.duplicados_persona == 1


def test_f023_r10_mismo_nombre_sin_dni_misma_empresa_queda_una_ficha() -> None:
    res = _depurar([
        _emp(1, dni=None, nombre="Ana Pérez", empresa=18, empresa_recurso=18),
        _emp(2, dni="", nombre="ANA PEREZ", empresa=18, empresa_recurso=18),
    ])
    assert _ides(res.filas) == [2]
    assert res.duplicados_persona == 1


def test_f023_r10_se_mantiene_la_preferencia_por_codigo_mensual() -> None:
    res = _depurar([
        _emp(1, dni="1A", cod_hora_mes="MENC"),
        _emp(2, dni="1A", cod_hora_mes=None),
    ])
    assert _ides(res.filas) == [1]


def test_f023_r11_mismo_dni_en_dos_empresas_quedan_las_dos() -> None:
    res = _depurar([
        _emp(1, dni="12345678A", empresa=1, empresa_recurso=1),
        _emp(2, dni="12345678A", empresa=18, empresa_recurso=18),
    ])
    assert _ides(res.filas) == [1, 2]
    assert res.duplicados_persona == 0
    assert sorted(f["empresa"] for f in res.filas) == [1, 18]


def test_f023_r11_mismo_nombre_sin_dni_en_dos_empresas_quedan_las_dos() -> None:
    res = _depurar([
        _emp(1, dni=None, nombre="Ana", empresa=1, empresa_recurso=1),
        _emp(2, dni=None, nombre="Ana", empresa=31, empresa_recurso=31),
    ])
    assert _ides(res.filas) == [1, 2]
    assert res.duplicados_persona == 0


def test_f023_r11_empresa_nula_no_se_mezcla_con_ninguna() -> None:
    res = _depurar([
        _emp(1, dni="1A", empresa=1),
        _emp(2, dni="1A", empresa=None, empresa_recurso=None),
    ])
    assert _ides(res.filas) == [1, 2]


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
    res = _depurar([_emp(1, estado_recurso="Baja", baja_recurso=80000)],
                   criterio=_criterio(estados_excluidos=("baja",),
                                      excluir_con_fecha_baja=True,
                                      activo=False))
    assert _ides(res.filas) == [1]
    assert not res.excluidos_estado_recurso


def test_f023_r13_fecha_de_baja_del_recurso_con_interruptor() -> None:
    filas = [
        _emp(1, baja_recurso=80000),
        _emp(2, baja_recurso=0),
        _emp(3, baja_recurso=None),
        _emp(4, baja_recurso=1),
    ]
    encendido = _depurar(filas, criterio=_criterio(excluir_con_fecha_baja=True))
    assert _ides(encendido.filas) == [2, 3]
    assert dict(encendido.excluidos_estado_recurso) == {FECHA_BAJA: 2}
    apagado = _depurar(filas, criterio=_criterio(excluir_con_fecha_baja=False))
    assert _ides(apagado.filas) == [1, 2, 3, 4]
    assert not apagado.excluidos_estado_recurso


def test_f023_r13_estado_y_fecha_a_la_vez_se_cuentan_una_sola_vez() -> None:
    res = _depurar([_emp(1, estado_recurso="Baja", baja_recurso=80000)],
                   criterio=_criterio(estados_excluidos=("baja",),
                                      excluir_con_fecha_baja=True))
    assert dict(res.excluidos_estado_recurso) == {"Baja": 1}


def test_f023_r14_recurso_inactivo_mas_reciente_no_tapa_al_activo() -> None:
    res = _depurar([
        _emp(1, recurso_ide=10, cod_hora_mes="MENC", estado_recurso="Activo"),
        _emp(1, recurso_ide=20, cod_hora_mes="MCAP", estado_recurso="Baja"),
    ], criterio=_criterio(estados_excluidos=("baja",)))
    assert [f["cod_hora_mes"] for f in res.filas] == ["MENC"]
    assert res.duplicados_recurso == 0
    assert dict(res.excluidos_estado_recurso) == {"Baja": 1}


def test_f023_r14_recurso_de_otra_empresa_mas_reciente_no_tapa_al_propio() -> None:
    res = _depurar([
        _emp(1, recurso_ide=10, cod_hora_mes="MENC", empresa_recurso=1),
        _emp(1, recurso_ide=20, cod_hora_mes="MCAP", empresa_recurso=18),
    ], criterio=_criterio())
    assert [f["cod_hora_mes"] for f in res.filas] == ["MENC"]
    assert res.duplicados_recurso == 0


def test_f023_r14_fecha_de_baja_del_recurso_mas_reciente_no_tapa_al_activo() -> None:
    res = _depurar([
        _emp(1, recurso_ide=10, cod_hora_mes="MENC", baja_recurso=0),
        _emp(1, recurso_ide=20, cod_hora_mes="MCAP", baja_recurso=80000),
    ], criterio=_criterio(excluir_con_fecha_baja=True))
    assert [f["cod_hora_mes"] for f in res.filas] == ["MENC"]


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
        _emp(1, estado_recurso="Baja", baja_recurso=80000),
        _emp(2, estado_recurso="Activo"),
    ]
    sin_criterio = _depurar([dict(f) for f in filas])
    con_criterio = _depurar([dict(f) for f in filas], criterio=_criterio())
    assert _ides(sin_criterio.filas) == _ides(con_criterio.filas) == [1, 2]
    assert not con_criterio.excluidos_estado_recurso
    assert con_criterio.excluidos_otra_empresa == 0


def test_f023_r16_criterio_por_defecto_es_vacio() -> None:
    criterio = _criterio()
    assert criterio.estados_excluidos == ()
    assert criterio.excluir_con_fecha_baja is False
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
        _emp(4, empresa=1, empresa_recurso=18),              # otra empresa
        _emp(5, estado_recurso="Baja definitiva"),           # estado
        _emp(6, baja_recurso=80000),                         # fecha de baja
        _emp(7, cod_hora_mes=None),                          # sin código M*
        _emp(2, recurso_ide=5),                              # dup. de recurso
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
                           excluir_con_fecha_baja=True),
    ).ejecutar()
    emp, obr = salida["empleados"], salida["obras"]
    assert emp["excluidos_por_estado_recurso"] == {
        "Baja definitiva": 1, FECHA_BAJA: 1}
    assert emp["excluidos_recurso_otra_empresa"] == 1
    assert emp["con_baja_laboral"] == 1
    assert emp["por_empresa"] == {"1": 2, "18": 1}
    assert emp["brutos"] == 8
    assert emp["duplicados_recurso"] == 1
    assert emp["duplicados_persona"] == 0
    assert emp["excluidos_sin_codigo_mes"] == 1
    assert emp["excluidos_por_categoria"] == {"(sin código de hora mensual)": 1}
    assert emp["por_codigo_mes"] == {"MENC": 3}
    assert emp["por_categoria"] == {"Técnico": 3}
    assert emp["total"] == 3
    assert _ides(emp["muestra"]) == [1, 2, 3]
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
        [_emp(1), _emp(2, estado_recurso="Baja"), _emp(3, baja_recurso=80000),
         _emp(4, empresa_recurso=18)],
        [_obr(1), _obr(2, estado_sigrid="Terminada")],
    )


def test_f023_r18_preview_y_sync_aplican_el_mismo_criterio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contenedor = _contenedor(monkeypatch, _entrada_r18(), _config_prueba({
        "filtro_estado_recurso": True,
        "estados_recurso_excluidos": ["baja"],
        "excluir_recurso_con_fecha_baja": True,
    }))
    assert _mismos_netos(contenedor) == ([1], [1])


def test_f023_r18_interruptor_general_apagado_llega_a_los_dos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contenedor = _contenedor(monkeypatch, _entrada_r18(), _config_prueba({
        "filtro_estado_recurso": False,
        "estados_recurso_excluidos": ["baja"],
        "excluir_recurso_con_fecha_baja": True,
    }))
    assert _mismos_netos(contenedor) == ([1, 2, 3], [1])


def test_f023_r18_config_sin_claves_de_recurso_no_filtra_por_estado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un config.yaml anterior a F-023 (sin las tres claves) se comporta como
    el criterio vacío (R16): los valores por defecto no filtran."""
    contenedor = _contenedor(monkeypatch, _entrada_r18(), _config_prueba({}))
    assert _mismos_netos(contenedor) == ([1, 2, 3], [1])


def test_f023_r18_filtro_estado_recurso_encendido_por_defecto(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Con literales y sin el interruptor explícito, el filtro se aplica."""
    contenedor = _contenedor(monkeypatch, _entrada_r18(), _config_prueba({
        "estados_recurso_excluidos": ["baja"],
    }))
    assert _mismos_netos(contenedor) == ([1, 3], [1])


def test_f023_r18_con_el_config_real_nadie_cae_por_estado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D1 abierta: con `config.yaml` tal cual, el estado no descarta a nadie
    (R16); solo cae el recurso de otra empresa (R9)."""
    contenedor = _contenedor(monkeypatch, _entrada_r18())
    netos_emp, _ = _mismos_netos(contenedor)
    assert netos_emp == [1, 2, 3]
