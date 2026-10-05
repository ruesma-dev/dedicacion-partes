# tests/test_f026_sync_recurso.py
"""Tests offline de F-026: el sync de trabajadores parte del RECURSO.

Trazabilidad con `specs/F-026-recursos-sin-ficha-empleado/requirements.md`:
R1 (consulta en `config.yaml`), R2-R4 (una fila por recurso, ficha
opcional, aviso de posible misma persona), R5 (columnas obligatorias), R6
(claves retiradas del preview), R12-R13 (ventana de bajas) y R17 (claves
nuevas del preview).

Nada abre un socket ni una conexión: las filas de Sigrid son dicts y el
`SigridGateway` es un doble que devuelve listas. Los módulos de F-026 se
importan dentro de los tests, para que cada tarea se verifique con su `-k`.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any

import pytest

from tests.conftest import UniversoFalso


# --- R1: la consulta versionada parte de dbo.res ----------------------------


def _config_empleados() -> dict[str, Any]:
    from config.settings import cargar_config

    return cargar_config()["sync"]["empleados"]


def _plano(sql: str) -> str:
    return " ".join(sql.split())


#: Alias de R1, en orden, con la expresión de la que salen (design §6).
ALIAS_R1 = [
    ("res.ide", "ide"),
    ("rcon.cod", "cod"),
    ("rcon.res", "nombre"),
    ("emp.dni", "dni"),
    ("res.cif", "cif"),
    ("rcon.emp", "empresa"),
    ("tip.res", "categoria"),
    ("COALESCE(rest.res, CAST(rcon.est AS VARCHAR(16)))", "estado_recurso"),
    ("NULLIF(rcon.fecbaj, 0)", "fecha_baja"),
    ("uh.fecbaj", "baja_laboral"),
    ("hm.cod", "cod_hora_mes"),
    ("hm.pre", "importe_mes"),
]


def _select(sql: str) -> str:
    return sql.split(" FROM dbo.res AS res ", 1)[0]


def _columnas(select: str) -> list[str]:
    """Columnas del SELECT, partiendo por las comas de nivel 0."""
    columnas, actual, nivel = [], "", 0
    for caracter in select.removeprefix("SELECT "):
        nivel += {"(": 1, ")": -1}.get(caracter, 0)
        if caracter == "," and nivel == 0:
            columnas.append(actual.strip())
            actual = ""
        else:
            actual += caracter
    return [*columnas, actual.strip()]


def test_f026_r1_parte_de_res_y_filtra_personas() -> None:
    sql = _plano(_config_empleados()["sql"])
    assert " FROM dbo.res AS res JOIN dbo.con AS rcon ON rcon.ide = res.ide " in sql
    assert re.search(r"\) AS hm WHERE res\.cla = 1 ORDER BY ", sql)
    assert "FROM dbo.emp AS" not in sql
    assert "JOIN dbo.emp AS emp" in sql


def test_f026_r1_ficha_de_empleado_solo_por_left_join() -> None:
    sql = _plano(_config_empleados()["sql"])
    assert ("LEFT JOIN dbo.emp AS emp ON emp.ide = res.conide "
            "AND res.conide > 0") in sql
    assert len(re.findall(r"JOIN dbo\.emp AS", sql)) == 1
    assert "WHERE h.empide = emp.ide" in sql


def test_f026_r1_alias_exactos_y_en_orden() -> None:
    select = _select(_plano(_config_empleados()["sql"]))
    columnas = _columnas(select)
    assert [tuple(c.rsplit(" AS ", 1)) for c in columnas] == ALIAS_R1


def test_f026_r1_sin_empleado_ide_ni_alias_antiguos() -> None:
    sql = _plano(_config_empleados()["sql"])
    for retirado in ("empleado_ide", "recurso_ide", "empresa_recurso",
                     "baja_recurso", "emp.ide AS ide"):
        assert retirado not in sql, retirado
    # Ni rastro del `con` de la ficha de empleado: todo sale del `rcon`.
    assert not re.search(r"(?<![\w.])con\.", sql)


def test_f026_r1_sin_where_de_actividad() -> None:
    sql = _plano(_config_empleados()["sql"])
    principal = sql.split(") AS hm ", 1)[1]
    assert principal.startswith("WHERE res.cla = 1 ORDER BY ")
    assert "fecbaj" not in principal


def test_f026_r1_orden_por_empresa_nombre_y_recurso() -> None:
    sql = _plano(_config_empleados()["sql"])
    assert sql.endswith("ORDER BY rcon.emp, rcon.res, res.ide")


# --- R13: la clave de configuración nueva -----------------------------------


def test_f026_r13_config_excluye_solo_la_baja_anterior_a_la_ventana() -> None:
    cfg = _config_empleados()
    assert cfg["filtro_estado_recurso"] is True
    assert cfg["estados_recurso_excluidos"] == []
    assert cfg["excluir_baja_anterior_a_ventana"] is True
    assert "excluir_recurso_con_fecha_baja" not in cfg


# --- R2-R4, R13: depuración sin filtro de empresa ni dedupes ------------------

#: Clave del recuento de las bajas anteriores a la ventana (R13).
BAJA_ANTERIOR = "(baja anterior a la ventana)"
#: Ventana de las pruebas: 1 de septiembre de 2026.
VENTANA = 20260901


def _fila(ide: int, **cambios: Any) -> dict[str, Any]:
    """Fila de `sync.empleados.sql` (R1): un recurso persona M* sin baja."""
    fila: dict[str, Any] = {
        "ide": ide,
        "cod": f"MO/{ide:04d}",
        "nombre": f"Persona {ide}",
        "dni": f"{ide:08d}X",
        "cif": f"{ide:08d}X",
        "empresa": 1,
        "categoria": "Encargado",
        "estado_recurso": "1",
        "fecha_baja": None,
        "baja_laboral": None,
        "cod_hora_mes": "MENC",
        "importe_mes": 100,
    }
    fila.update(cambios)
    return fila


def _criterio(**kwargs: Any) -> Any:
    from application.filtros_maestros import CriterioActivoRecurso

    return CriterioActivoRecurso(**kwargs)


def _depurar(filas: list[dict[str, Any]], **kwargs: Any) -> Any:
    from application.filtros_maestros import depurar_empleados

    return depurar_empleados([dict(f) for f in filas], [], False, **kwargs)


def _ides(filas: list[dict[str, Any]]) -> list[int]:
    return sorted(int(f["ide"]) for f in filas)


def test_f026_r2_recurso_sin_ficha_de_empleado_entra() -> None:
    res = _depurar([_fila(772, dni=None), _fila(5)])
    assert _ides(res.filas) == [5, 772]
    (eusebio,) = [f for f in res.filas if f["ide"] == 772]
    assert eusebio["dni"] is None
    assert eusebio["cod"] == "MO/0772"


def test_f026_r3_misma_persona_en_la_misma_empresa_son_dos_filas() -> None:
    res = _depurar([_fila(61, dni="1A", cod_hora_mes="MENC"),
                    _fila(736, dni="1A", cod_hora_mes="MCAP")])
    assert _ides(res.filas) == [61, 736]
    assert sorted(f["cod_hora_mes"] for f in res.filas) == ["MCAP", "MENC"]


def test_f026_r3_misma_persona_en_dos_empresas_cada_una_en_la_suya() -> None:
    res = _depurar([_fila(496, dni="1A", empresa=1),
                    _fila(6, dni="1A", empresa=18)])
    assert sorted((f["ide"], f["empresa"]) for f in res.filas) == [
        (6, 18), (496, 1)]


def test_f026_r3_recurso_de_otra_empresa_que_la_ficha_ya_no_se_descarta() -> None:
    """La empresa es la del recurso: ninguna columna la contrasta con la de
    la ficha de empleado (se retira el descarte de F-023 R9)."""
    res = _depurar([_fila(1, empresa=18)], criterio=_criterio())
    assert [(f["ide"], f["empresa"]) for f in res.filas] == [(1, 18)]


def test_f026_r4_posible_misma_persona_por_dni_normalizado() -> None:
    res = _depurar([_fila(61, dni="12.345.678-a"), _fila(736, dni="12345678 A"),
                    _fila(7)])
    assert res.posible_misma_persona == [["MO/0061", "MO/0736"]]
    assert _ides(res.filas) == [7, 61, 736]


def test_f026_r4_sin_dni_agrupa_por_cif() -> None:
    res = _depurar([_fila(1, dni=None, cif="b-1"), _fila(2, dni="", cif="B1"),
                    _fila(3, dni=None, cif="B1")])
    assert res.posible_misma_persona == [["MO/0001", "MO/0002", "MO/0003"]]


def test_f026_r4_el_dni_manda_sobre_el_cif() -> None:
    res = _depurar([_fila(1, dni="1A", cif="C"), _fila(2, dni="2B", cif="C")])
    assert res.posible_misma_persona == []


def test_f026_r4_nunca_agrupa_por_nombre() -> None:
    res = _depurar([_fila(1, dni=None, cif=None, nombre="Ana Pérez"),
                    _fila(2, dni=" ", cif="", nombre="ANA PEREZ")])
    assert res.posible_misma_persona == []
    assert _ides(res.filas) == [1, 2]


def test_f026_r4_solo_dentro_de_la_misma_empresa() -> None:
    res = _depurar([_fila(1, dni="1A", empresa=1),
                    _fila(2, dni="1A", empresa=18)])
    assert res.posible_misma_persona == []


def test_f026_r4_solo_entre_incluidos() -> None:
    res = _depurar([_fila(1, dni="1A"), _fila(2, dni="1A", cod_hora_mes=None)])
    assert res.posible_misma_persona == []


def test_f026_r4_varios_grupos_ordenados() -> None:
    res = _depurar([_fila(9, dni="9Z"), _fila(2, dni="1A"), _fila(8, dni="9Z"),
                    _fila(1, dni="1A")])
    assert res.posible_misma_persona == [["MO/0001", "MO/0002"],
                                         ["MO/0008", "MO/0009"]]


def test_f026_r6_resultado_sin_recuentos_retirados() -> None:
    res = _depurar([_fila(1)])
    for retirado in ("duplicados_recurso", "duplicados_persona",
                     "excluidos_otra_empresa"):
        assert not hasattr(res, retirado), retirado


def test_f026_r13_baja_anterior_a_la_ventana_fuera_y_contada() -> None:
    res = _depurar([
        _fila(1, fecha_baja=VENTANA - 1),          # 31/08: fuera
        _fila(2, fecha_baja=VENTANA),              # 01/09: dentro
        _fila(3, fecha_baja=20261015),             # en curso: dentro
        _fila(4, fecha_baja=None),
        _fila(5, fecha_baja=0),
        _fila(6, fecha_baja=20200101),             # muy antigua: fuera
    ], criterio=_criterio(excluir_baja_anterior_a_ventana=True),
        baja_desde=VENTANA)
    assert _ides(res.filas) == [2, 3, 4, 5]
    assert dict(res.excluidos_estado_recurso) == {BAJA_ANTERIOR: 2}
    assert {f["ide"]: f["fecha_baja"] for f in res.filas} == {
        2: VENTANA, 3: 20261015, 4: None, 5: 0}
    assert res.incluidos_con_baja == 2


def test_f026_r13_sin_ventana_o_sin_interruptor_no_excluye_por_baja() -> None:
    filas = [_fila(1, fecha_baja=20200101), _fila(2)]
    sin_ventana = _depurar(filas, criterio=_criterio(
        excluir_baja_anterior_a_ventana=True))
    apagado = _depurar(filas, criterio=_criterio(), baja_desde=VENTANA)
    general = _depurar(filas, criterio=_criterio(
        excluir_baja_anterior_a_ventana=True, activo=False), baja_desde=VENTANA)
    for res in (sin_ventana, apagado, general):
        assert _ides(res.filas) == [1, 2]
        assert not res.excluidos_estado_recurso
        assert res.incluidos_con_baja == 1


def test_f026_r13_estado_y_baja_a_la_vez_cuentan_una_vez_por_estado() -> None:
    res = _depurar([_fila(1, estado_recurso="Baja", fecha_baja=20200101)],
                   criterio=_criterio(estados_excluidos=("baja",),
                                      excluir_baja_anterior_a_ventana=True),
                   baja_desde=VENTANA)
    assert dict(res.excluidos_estado_recurso) == {"Baja": 1}


def test_f026_r13_baja_que_no_llega_al_upsert_no_cuenta_como_incluida() -> None:
    res = _depurar([_fila(1, fecha_baja=20261015, cod_hora_mes=None)],
                   baja_desde=VENTANA)
    assert res.filas == [] and res.incluidos_con_baja == 0


def test_f026_r13_upsert_recibe_fecha_baja_sin_auxiliares() -> None:
    (fila,) = _depurar([_fila(1, fecha_baja=20261015, baja_laboral=20261001)],
                       baja_desde=VENTANA).filas
    assert fila["fecha_baja"] == 20261015
    for auxiliar in ("cif", "estado_recurso", "baja_laboral"):
        assert auxiliar not in fila, auxiliar
    assert {"ide", "cod", "nombre", "dni", "empresa", "categoria",
            "cod_hora_mes", "importe_mes"} <= set(fila)


# --- R5, R12: el step del sync calcula la ventana ----------------------------


class _SigridFalso:
    """Devuelve las filas de empleados a cualquier consulta."""

    def __init__(self, filas: list[dict[str, Any]]) -> None:
        self._filas = filas
        self.leidas: list[str] = []

    def leer(self, sql: str) -> list[dict[str, Any]]:
        self.leidas.append(sql)
        return [dict(f) for f in self._filas]


class _RepoEspia:
    def __init__(self) -> None:
        self.recibido: list[dict[str, Any]] | None = None

    def sincronizar(self, filas: list[dict[str, Any]]) -> Any:
        from domain.models import ResultadoSyncMaestro

        self.recibido = [dict(f) for f in filas]
        return ResultadoSyncMaestro(recibidos=len(filas))


class _PeriodosFalsos:
    def __init__(self, periodos: list[Any]) -> None:
        self._periodos = periodos
        self.llamadas = 0

    def listar(self) -> list[Any]:
        self.llamadas += 1
        return list(self._periodos)


class _UowEspia:
    def __init__(self, periodos: list[Any] | None = None) -> None:
        self.trabajadores = _RepoEspia()
        self.obras = _RepoEspia()
        self.periodos = _PeriodosFalsos(periodos or [])
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


def _periodo(anio: int, mes: int, abierto: bool = True) -> Any:
    from domain.models import EstadoPeriodo, Periodo

    estado = EstadoPeriodo.ABIERTO if abierto else EstadoPeriodo.CERRADO
    return Periodo(anio, mes, estado)


#: Hoy en las pruebas del step y del preview.
HOY = date(2026, 10, 2)

#: Filas con bajas alrededor de las ventanas de las pruebas.
FILAS_BAJA = [
    _fila(1, fecha_baja=20260430),     # antes de cualquier ventana
    _fila(2, fecha_baja=20260515),     # mayo: solo si mayo contara (cerrado)
    _fila(3, fecha_baja=20260601),     # junio (abierto más antiguo)
    _fila(4, fecha_baja=20260831),     # agosto
    _fila(5, fecha_baja=20260901),     # septiembre (mes anterior a HOY)
    _fila(6),
]


def _step(filas: list[dict[str, Any]], **kwargs: Any) -> Any:
    from application.sync_pipeline import FetchEmpleadosStep

    criterio = _criterio(excluir_baja_anterior_a_ventana=True)
    return FetchEmpleadosStep(_SigridFalso(filas), "SELECT ... FROM dbo.res",
                              criterio=criterio, hoy=lambda: HOY, **kwargs)


def _ejecutar_step(step: Any, uow: _UowEspia) -> list[int]:
    from application.sync_pipeline import SyncContext

    ctx = SyncContext()
    step.ejecutar(ctx, uow)
    return _ides(ctx.filas_empleados)


def test_f026_r12_el_step_usa_los_periodos_abiertos_y_hoy() -> None:
    uow = _UowEspia([_periodo(2026, 10), _periodo(2026, 5, abierto=False),
                     _periodo(2026, 6), _periodo(2026, 8)])
    assert _ejecutar_step(_step(FILAS_BAJA), uow) == [3, 4, 5, 6]
    assert uow.periodos.llamadas == 1


def test_f026_r12_el_step_sin_abiertos_usa_el_mes_anterior_a_hoy() -> None:
    uow = _UowEspia([_periodo(2026, 6, abierto=False)])
    assert _ejecutar_step(_step(FILAS_BAJA), uow) == [5, 6]


def test_f026_r12_el_reloj_por_defecto_es_el_del_dia() -> None:
    from application.sync_pipeline import FetchEmpleadosStep

    step = FetchEmpleadosStep(_SigridFalso([]), "SELECT 1")
    assert step._hoy == date.today


@pytest.mark.parametrize("columna", ["ide", "nombre", "empresa"])
def test_f026_r5_sync_falla_sin_columna_obligatoria_y_no_persiste(
    columna: str,
) -> None:
    from application import sync_pipeline as sp

    filas = [{k: v for k, v in _fila(1).items() if k != columna}]
    uow = _UowEspia()
    pipeline = sp.SyncMaestrosPipeline([
        _step(filas), sp.UpsertTrabajadoresStep()])
    with pytest.raises(ValueError, match=f"sync.empleados.sql.*'{columna}'"):
        pipeline.ejecutar(uow)
    assert uow.trabajadores.recibido is None
    assert uow.commits == 0


# --- R5, R6, R17: el preview publica la ventana y no persiste -----------------


class _UowLectura(_UowEspia):
    """UoW de la fábrica del preview: cuenta entradas, salidas y commits."""

    def __init__(self, periodos: list[Any]) -> None:
        super().__init__(periodos)
        self.entradas = self.salidas = 0

    def __enter__(self) -> "_UowLectura":
        self.entradas += 1
        return self

    def __exit__(self, *_exc: object) -> None:
        self.salidas += 1


SQL_OBR = "SELECT ... FROM dbo.obr AS obr"


class _SigridPreview:
    def __init__(self, empleados: list[dict[str, Any]]) -> None:
        self._empleados = empleados

    def leer(self, sql: str) -> list[dict[str, Any]]:
        if "dbo.obr" in sql:
            return [{"ide": 1, "cod": "0001", "descripcion": "Obra",
                     "estado_sigrid": "En curso", "empresa": 1}]
        return [dict(f) for f in self._empleados]


def _preview(filas: list[dict[str, Any]], **kwargs: Any) -> Any:
    from application.use_cases import PreviewSync

    return PreviewSync(_SigridPreview(filas), "SELECT ... FROM dbo.res", SQL_OBR,
                       criterio=_criterio(excluir_baja_anterior_a_ventana=True),
                       hoy=lambda: HOY, universo=UniversoFalso(),
                       empresa_obras=1, **kwargs)


def test_f026_r17_preview_con_fabrica_usa_los_periodos_abiertos() -> None:
    uow = _UowLectura([_periodo(2026, 6), _periodo(2026, 5, abierto=False)])
    emp = _preview(FILAS_BAJA, uow_factory=lambda: uow).ejecutar()["empleados"]
    assert emp["ventana_baja"] == 20260601
    assert emp["total"] == 4 and _ides(emp["muestra"]) == [3, 4, 5, 6]
    assert emp["excluidos_por_estado_recurso"] == {BAJA_ANTERIOR: 2}
    assert emp["incluidos_con_baja"] == 3
    assert (uow.entradas, uow.salidas, uow.commits) == (1, 1, 0)
    assert uow.trabajadores.recibido is None


def test_f026_r17_preview_sin_fabrica_usa_el_mes_anterior() -> None:
    emp = _preview(FILAS_BAJA).ejecutar()["empleados"]
    assert emp["ventana_baja"] == 20260901
    assert _ides(emp["muestra"]) == [5, 6]
    assert emp["incluidos_con_baja"] == 1
    assert emp["excluidos_por_estado_recurso"] == {BAJA_ANTERIOR: 4}


def test_f026_r17_preview_publica_posible_misma_persona() -> None:
    emp = _preview([_fila(61, dni="1A"), _fila(736, dni="1-a"),
                    _fila(7)]).ejecutar()["empleados"]
    assert emp["posible_misma_persona"] == [["MO/0061", "MO/0736"]]
    assert emp["total"] == 3


def test_f026_r6_preview_sin_claves_retiradas() -> None:
    emp = _preview([_fila(1)]).ejecutar()["empleados"]
    for retirada in ("excluidos_recurso_otra_empresa", "duplicados_recurso",
                     "duplicados_persona"):
        assert retirada not in emp, retirada


def test_f026_r17_el_reloj_del_preview_por_defecto_es_el_del_dia() -> None:
    from application.use_cases import PreviewSync

    assert PreviewSync(_SigridPreview([]), "", SQL_OBR,
                       universo=UniversoFalso(),
                       empresa_obras=1)._hoy == date.today


@pytest.mark.parametrize("columna", ["ide", "nombre", "empresa"])
def test_f026_r5_preview_falla_sin_columna_obligatoria(columna: str) -> None:
    filas = [{k: v for k, v in _fila(1).items() if k != columna}]
    uow = _UowLectura([])
    with pytest.raises(ValueError, match=f"sync.empleados.sql.*'{columna}'"):
        _preview(filas, uow_factory=lambda: uow).ejecutar()
    assert uow.commits == 0 and uow.trabajadores.recibido is None


def test_f026_r17_cualquier_fecha_de_baja_positiva_cuenta_como_con_baja() -> None:
    """Superviviente de la mutación (`> 0` → `> 1`): «con baja» es cualquier
    `fecha_baja` informada, como en el descarte (`0 < fecha_baja`), también
    el valor mínimo 1; 0 y NULL no cuentan."""
    res = _depurar([_fila(1, fecha_baja=1), _fila(2, fecha_baja=0),
                    _fila(3, fecha_baja=None)])
    assert _ides(res.filas) == [1, 2, 3]
    assert res.incluidos_con_baja == 1
