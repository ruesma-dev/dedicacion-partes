# tests/test_f055_propuesta_guardada.py
"""F-055 · La propuesta GUARDADA de cada línea automática en la api.

- R13 (T9): columnas nulables `asignacion.propuesta_*` en el ORM, campos de
  `Linea`, el mapeo del repositorio, lo que escribe `reemplazar` y
  `guardar_propuesta` (sesión falsa).
- R17 (T9): guardar la fila conserva la propuesta de cada línea que ya
  existía; la nueva entra sin ella; copiar el mes, F8 y completar no la
  copian; deshacer no la restaura; cambiar la elegida no la borra.
- R15/R18 (T11): abrir el selector guarda (y reescribe) la propuesta que
  devuelve el transfer si la línea sigue sin elegida, sin evento.
- R27 (T11): `LineaOut` publica `propuesta_cod`, `_res` y `_metodo`.

Casos de uso con la UnitOfWork en memoria de F-024/F-050, ampliada AQUÍ
para que `reemplazar` guarde también la propuesta. Sin red ni BBDD.
"""
from __future__ import annotations

import dataclasses
from decimal import Decimal
from types import SimpleNamespace

import pytest
from application.use_cases import (
    CambiarPartida,
    CompletarHasta100,
    CopiarPeriodoAnterior,
    CopiarTrabajadorAnterior,
    DeshacerUltimaModificacion,
    GuardarAsignaciones,
    _conservar_partidas,
    _snapshot,
    _validar_lineas,
)
from domain.models import Linea
from infrastructure.db.orm_models import AsignacionORM
from infrastructure.db.repositories import (
    PgAsignacionRepository,
    _a_linea_con_partida,
)
from sqlalchemy.dialects import postgresql

from tests.test_f024_cuadrante_empresa import (
    ANIO,
    MES,
    P_ACT,
    P_ANT,
    _Asignaciones,
    _ln,
    _Uow,
)
from tests.test_f050_partida_linea import FILTRO, P, _orm_obra

#: Propuesta guardada de una línea (columnas de `asignacion`).
PR = {"propuesta_ide": 80002, "propuesta_cod": "CI.1.20",
      "propuesta_res": "JEFE DE OBRA", "propuesta_metodo": "parte_anterior",
      "propuesta_origen": "parte PT26/00050 · 05/2026 · obra 0678"}
#: La misma, como la devuelve el transfer (`asdict(Propuesta)`).
DEL_TRANSFER = {"paride": 80002, "cod": "CI.1.20", "res": "JEFE DE OBRA",
                "metodo": "parte_anterior",
                "origen": "parte PT26/00050 · 05/2026 · obra 0678"}
CAMPOS = tuple(PR)


def _lp(obra_ide: int, pct: str, pv: bool = False, **kw) -> Linea:
    return dataclasses.replace(_ln(obra_ide, pct), es_postventa=pv, **kw)


class _AsignacionesConPropuesta(_Asignaciones):
    """`reemplazar` que conserva modo, partida y propuesta, y
    `guardar_propuesta` en memoria con sus dos condiciones."""

    def reemplazar(self, periodo_id, ide, lineas, usuario):
        self._uow.lineas.setdefault(periodo_id, {})[ide] = [
            _lp(ln.obra_ide, str(ln.porcentaje), ln.es_postventa,
                partida_ide=ln.partida_ide, partida_cod=ln.partida_cod,
                partida_res=ln.partida_res,
                **{c: getattr(ln, c) for c in CAMPOS}) for ln in lineas]
        self._uow.reemplazados.append(ide)

    def guardar_propuesta(self, periodo_id, ide, clave, propuesta, *,
                          solo_si_vacia=False):
        lineas = self._uow.lineas.get(periodo_id, {}).get(ide, [])
        for i, ln in enumerate(lineas):
            if ln.clave() != tuple(clave) or ln.partida_ide is not None \
                    or (solo_si_vacia and ln.propuesta_ide is not None):
                continue
            lineas[i] = dataclasses.replace(ln, **_columnas(propuesta))
            self._uow.propuestas.append((periodo_id, ide, tuple(clave)))
            return True
        return False


def _columnas(propuesta: dict) -> dict:
    return {"propuesta_ide": propuesta["paride"],
            "propuesta_cod": propuesta["cod"],
            "propuesta_res": propuesta["res"],
            "propuesta_metodo": propuesta["metodo"],
            "propuesta_origen": propuesta["origen"]}


def _uow(actual=None, anterior=None) -> _Uow:
    uow = _Uow({P_ACT: actual or {}, P_ANT: anterior or {}})
    uow.asignaciones = _AsignacionesConPropuesta(uow)
    uow.propuestas = []
    return uow


def _propuestas(lineas) -> list[tuple]:
    return [(ln.obra_ide, ln.propuesta_ide, ln.propuesta_metodo)
            for ln in lineas]


# ================================ R13 ==================================== #
@pytest.mark.parametrize("nombre, tipo", [
    ("propuesta_ide", "BIGINT"), ("propuesta_cod", "TEXT"),
    ("propuesta_res", "TEXT"), ("propuesta_metodo", "TEXT"),
    ("propuesta_origen", "TEXT")])
def test_f055_r13_columnas_nulables_sin_default(nombre, tipo):
    col = AsignacionORM.__table__.columns[nombre]
    assert col.type.compile(dialect=postgresql.dialect()) == tipo
    assert col.nullable is True
    assert col.default is None and col.server_default is None


def test_f055_r13_linea_sin_propuesta_por_defecto_al_final():
    ln = Linea(obra_ide=1, es_postventa=False, porcentaje=Decimal(10))
    assert tuple(getattr(ln, c) for c in CAMPOS) == (None,) * 5
    nombres = [f.name for f in dataclasses.fields(Linea)]
    assert nombres[-5:] == list(CAMPOS)
    assert dataclasses.replace(ln, **PR).clave() == (1, False)


def test_f055_r13_el_repositorio_mapea_la_propuesta():
    a = SimpleNamespace(obra_ide=7, es_postventa=False,
                        porcentaje=Decimal("40.00"), partida_ide=None,
                        partida_cod=None, partida_res=None, **PR)
    ln = _a_linea_con_partida(a, _orm_obra())
    assert {c: getattr(ln, c) for c in CAMPOS} == PR


class _Sesion:
    def __init__(self, filas: int = 1) -> None:
        self.anadidos: list = []
        self.ejecutadas: list = []
        self._filas = filas

    def execute(self, stmt):
        self.ejecutadas.append(stmt)
        return SimpleNamespace(rowcount=self._filas)

    def add(self, objeto):
        self.anadidos.append(objeto)

    def flush(self):
        return None


def test_f055_r13_reemplazar_escribe_la_propuesta():
    s = _Sesion()
    PgAsignacionRepository(s).reemplazar(  # type: ignore[arg-type]
        3, 10, [_lp(100, "60", **PR), _lp(101, "40")], "pgris")
    assert [tuple(getattr(o, c) for c in CAMPOS) for o in s.anadidos] == [
        tuple(PR.values()), (None,) * 5]


def _sql(stmt) -> str:
    return str(stmt.compile(dialect=postgresql.dialect(),
                            compile_kwargs={"literal_binds": True}))


@pytest.mark.parametrize("solo_si_vacia", [False, True])
def test_f055_r13_guardar_propuesta_update_condicional(solo_si_vacia):
    s = _Sesion(filas=1)
    hecho = PgAsignacionRepository(s).guardar_propuesta(  # type: ignore
        3, 10, (100, False), DEL_TRANSFER, solo_si_vacia=solo_si_vacia)
    assert hecho is True
    [stmt] = s.ejecutadas
    sql = " ".join(_sql(stmt).split())
    assert sql.startswith("UPDATE asignacion SET propuesta_ide=80002, "
                          "propuesta_cod='CI.1.20', "
                          "propuesta_res='JEFE DE OBRA', "
                          "propuesta_metodo='parte_anterior', "
                          "propuesta_origen='parte PT26/00050 · 05/2026 · "
                          "obra 0678' WHERE ")
    for trozo in ("asignacion.periodo_id = 3",
                  "asignacion.trabajador_ide = 10",
                  "asignacion.obra_ide = 100",
                  "asignacion.es_postventa = false",
                  "asignacion.partida_ide IS NULL"):
        assert trozo in sql, trozo
    assert ("asignacion.propuesta_ide IS NULL" in sql) is solo_si_vacia


def test_f055_r13_guardar_propuesta_sin_fila_devuelve_falso():
    s = _Sesion(filas=0)
    assert PgAsignacionRepository(s).guardar_propuesta(  # type: ignore
        3, 10, (100, True), DEL_TRANSFER) is False


# ================================ R17 ==================================== #
def test_f055_r17_conservar_copia_la_propuesta_por_clave():
    antes = [_lp(100, "60", **PR), _lp(101, "40", pv=True, **P)]
    nuevas = [_lp(100, "50"), _lp(101, "30", pv=True), _lp(102, "20")]
    assert _propuestas(_conservar_partidas(nuevas, antes)) == [
        (100, 80002, "parte_anterior"), (101, None, None),
        (102, None, None)]


def test_f055_r17_guardar_la_fila_conserva_y_la_nueva_sin_propuesta():
    uow = _uow(actual={14: [_lp(100, "60", **PR)]})
    GuardarAsignaciones().ejecutar(
        uow, ANIO, MES, 14,
        [{"obra_ide": 100, "porcentaje": "70"},
         {"obra_ide": 101, "porcentaje": "30"}], "u", filtro=FILTRO)
    assert _propuestas(uow.lineas[P_ACT][14]) == [
        (100, 80002, "parte_anterior"), (101, None, None)]


def test_f055_r17_el_evento_no_lleva_la_propuesta():
    assert _snapshot([_lp(100, "60", **PR)]) == [
        {"obra_ide": 100, "es_postventa": False, "porcentaje": "60"}]
    [ln] = _validar_lineas(_uow(), [{"obra_ide": 100, "porcentaje": "60",
                                     **PR}])
    assert ln.propuesta_ide is None


def test_f055_r17_guardar_solo_con_otra_propuesta_no_es_cambio():
    """La propuesta no cuenta como cambio de la fila: sin evento."""
    uow = _uow(actual={14: [_lp(100, "60.00", **PR)]})
    GuardarAsignaciones().ejecutar(
        uow, ANIO, MES, 14, [{"obra_ide": 100, "porcentaje": "60"}], "u",
        filtro=FILTRO)
    assert uow.eventos.eventos == [] and uow.reemplazados == []


def test_f055_r17_copiar_el_mes_no_copia_la_propuesta():
    uow = _uow(anterior={14: [_lp(100, "100", **P, **PR)]})
    CopiarPeriodoAnterior().ejecutar(uow, ANIO, MES, "u", filtro=FILTRO)
    [ln] = uow.lineas[P_ACT][14]
    assert (ln.partida_ide, ln.propuesta_ide) == (80003, None)


def test_f055_r17_f8_no_copia_la_propuesta():
    uow = _uow(anterior={14: [_lp(100, "100", **PR)]})
    CopiarTrabajadorAnterior().ejecutar(uow, ANIO, MES, 14, "u",
                                        filtro=FILTRO)
    assert _propuestas(uow.lineas[P_ACT][14]) == [(100, None, None)]


def test_f055_r17_completar_la_nueva_sin_propuesta_y_conserva_la_suya():
    uow = _uow(actual={14: [_lp(100, "60", **PR)]})
    CompletarHasta100().ejecutar(uow, ANIO, MES, [14], 101, False, "u",
                                 filtro=FILTRO)
    assert _propuestas(uow.lineas[P_ACT][14]) == [
        (100, 80002, "parte_anterior"), (101, None, None)]


def test_f055_r17_deshacer_no_restaura_la_propuesta():
    uow = _uow(actual={14: [_lp(100, "60", **PR)]})
    GuardarAsignaciones().ejecutar(
        uow, ANIO, MES, 14, [{"obra_ide": 101, "porcentaje": "100"}], "u",
        filtro=FILTRO)
    DeshacerUltimaModificacion().ejecutar(uow, ANIO, MES, 14, "u",
                                          filtro=FILTRO)
    assert _propuestas(uow.lineas[P_ACT][14]) == [(100, None, None)]


def test_f055_r17_cambiar_la_elegida_no_borra_la_propuesta():
    uow = _uow(actual={14: [_lp(100, "100", **PR)]})
    CambiarPartida().ejecutar(uow, ANIO, MES, 14, 100, False,
                              {"ide": 80003, "cod": "CI.1.9",
                               "res": "ADMINISTRATIVO"}, "u", filtro=FILTRO)
    [ln] = uow.lineas[P_ACT][14]
    assert (ln.partida_ide, ln.propuesta_ide) == (80003, 80002)
    CambiarPartida().ejecutar(uow, ANIO, MES, 14, 100, False, None, "u",
                              filtro=FILTRO)
    [ln] = uow.lineas[P_ACT][14]
    assert (ln.partida_ide, ln.propuesta_ide) == (None, 80002)


# ============================ R15 · R18 (T11) ============================ #
class _TransferSelector:
    def __init__(self, propuesta) -> None:
        self.propuesta = propuesta
        self.llamadas = 0

    def propuesta_partidas(self, payload):
        self.llamadas += 1
        return {"ok": True, "partidas_obra": [], "partidas_postventa": [],
                "propuestas": {"linea": self.propuesta},
                "mayor_inicial": {"linea": None}}


def _selector(uow, propuesta, obra=100, pv=False):
    from application.partidas_linea import PartidasDeLinea
    commits = []
    uow.commit = lambda: commits.append(True)
    r = PartidasDeLinea(_TransferSelector(propuesta)).ejecutar(
        uow, ANIO, MES, 14, obra, pv, empresa_obras=1)
    return r, commits


def test_f055_r15_el_selector_guarda_la_propuesta():
    uow = _uow(actual={14: [_lp(100, "100")]})
    r, commits = _selector(uow, DEL_TRANSFER)
    [ln] = uow.lineas[P_ACT][14]
    assert {c: getattr(ln, c) for c in CAMPOS} == PR
    assert commits == [True] and uow.eventos.eventos == []
    assert r["propuesta"] == DEL_TRANSFER and r["elegida"] is None


def test_f055_r18_el_selector_reescribe_la_guardada():
    uow = _uow(actual={14: [_lp(100, "100", **dict(
        PR, propuesta_ide=1, propuesta_metodo="auto_nombre"))]})
    _selector(uow, DEL_TRANSFER)
    [ln] = uow.lineas[P_ACT][14]
    assert (ln.propuesta_ide, ln.propuesta_metodo) == (80002,
                                                      "parte_anterior")


@pytest.mark.parametrize("linea, propuesta", [
    (_lp(100, "100", **P), DEL_TRANSFER),                   # con elegida
    (_lp(100, "100"), None),                                # sin propuesta
    (_lp(100, "100", pv=True), dict(DEL_TRANSFER, metodo="postventa")),
], ids=["elegida", "sin_propuesta", "postventa"])
def test_f055_r15_no_guarda(linea, propuesta):
    uow = _uow(actual={14: [linea]})
    _selector(uow, propuesta, pv=linea.es_postventa)
    assert uow.propuestas == []
    assert uow.lineas[P_ACT][14][0].propuesta_ide is None


def test_f055_r15_la_var_ni_llama_ni_guarda():
    uow = _uow(actual={14: [_lp(100, "100", partida_fija=True)]})
    r, commits = _selector(uow, DEL_TRANSFER)
    assert r["fija"] is not None and commits == [] and uow.propuestas == []


# =============================== R27 (T11) =============================== #
def test_f055_r27_linea_out_publica_la_propuesta():
    from domain.models import CuadranteTrabajador
    from interface_adapters.api.schemas import a_trabajador_out

    from tests.test_f024_cuadrante_empresa import TRABAJADORES
    fila = CuadranteTrabajador(trabajador=TRABAJADORES[14],
                               lineas=[_lp(100, "60", **PR), _lp(101, "40")])
    out = a_trabajador_out(fila, 1).model_dump()
    assert [(ln["propuesta_cod"], ln["propuesta_res"],
             ln["propuesta_metodo"]) for ln in out["lineas"]] == [
        ("CI.1.20", "JEFE DE OBRA", "parte_anterior"), (None, None, None)]
    assert "propuesta_ide" not in out["lineas"][0]
    assert "propuesta_origen" not in out["lineas"][0]


# =========== T16 · huecos que dejó la campaña de mutación (api) ========== #
def test_f055_r13_guardar_propuesta_por_defecto_pisa_la_guardada():
    """Superviviente `solo_si_vacia: bool = True`: por defecto (preflight y
    selector, R14 y R15) se reescribe la propuesta; solo el segundo plano
    pide `solo_si_vacia`. Lo mismo en el puerto."""
    import inspect

    from domain.ports import AsignacionRepository
    s = _Sesion()
    PgAsignacionRepository(s).guardar_propuesta(  # type: ignore[arg-type]
        3, 10, (100, False), DEL_TRANSFER)
    assert "propuesta_ide IS NULL" not in _sql(s.ejecutadas[0])
    firma = inspect.signature(AsignacionRepository.guardar_propuesta)
    assert firma.parameters["solo_si_vacia"].default is False


def test_f055_r37_las_salidas_sin_cola_por_defecto():
    """Supervivientes `propuestas_en_curso: bool = True` en los esquemas: sin
    decirlo, ninguna salida dice que haya propuestas en curso."""
    from domain.models import Periodo, ResultadoCopia, ResumenPeriodo
    from interface_adapters.api.schemas import (
        CuadranteOut,
        FilaOut,
        a_completar_out,
        a_copia_periodo_out,
        a_periodo_out,
        a_resumen_out,
    )
    resumen = a_resumen_out(ResumenPeriodo(0, 0, 0, 0, 0))
    assert a_copia_periodo_out(ResultadoCopia(None)).propuestas_en_curso \
        is False
    assert a_completar_out([], ResumenPeriodo(0, 0, 0, 0, 0)) \
        .propuestas_en_curso is False
    assert CuadranteOut(periodo=a_periodo_out(Periodo(2026, 9)), empresa=1,
                        obras=[], trabajadores=[], resumen=resumen) \
        .propuestas_en_curso is False
    assert "propuestas_en_curso" in FilaOut.model_fields
    assert FilaOut.model_fields["propuestas_en_curso"].default is False
