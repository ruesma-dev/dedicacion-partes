# tests/test_f044_cuadrante_vinculados.py
"""F-044 · T6: el cuadrante con las subfilas de los vinculados (api).

- R6: bajo cada línea de un trabajador con vinculados vigentes en el mes,
  una subfila por vinculado (tipo, código, partida). Sin vinculados, la
  línea y la respuesta son las de hoy.
- R7: el % de la subfila es el del titular: la subfila no lo lleva.
- R8: la partida de la subfila se cambia con `PUT …/partida` y
  `vinculado_ide` (evento `PARTIDA_VINCULADO`); deshacer la devuelve,
  guardar la fila la conserva y copiar el mes la copia (sin su propuesta).
  `GET …/partidas` con `vinculado_ide` da el catálogo y la propuesta de la
  subfila. Sin `vinculado_ide`, las rutas de F-050 como hoy.
- R9: la propuesta de la subfila (la del transfer) se guarda como en
  F-055: en el selector, en el preflight y en segundo plano, solo si la
  subfila sigue sin elegida.

Sesiones, transfer y UoW dobles: sin red ni BBDD.
"""
from __future__ import annotations

import dataclasses
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest
from application.use_cases import (
    CambiarPartida,
    CopiarPeriodoAnterior,
    CopiarTrabajadorAnterior,
    DeshacerUltimaModificacion,
    GuardarAsignaciones,
)
from domain.errors import LineaNoEncontrada, ObraNoValida
from domain.models import (
    EventoPendiente,
    FiltroEmpresa,
    Linea,
    SubfilaVinculado,
    TipoEvento,
)
from infrastructure.db.orm_models import (
    AsignacionORM,
    AsignacionVinculadoORM,
    PeriodoORM,
    RecursoVinculadoORM,
)
from infrastructure.db.repositories import PgAsignacionRepository
from sqlalchemy.dialects import postgresql

from tests.test_f024_cuadrante_empresa import (
    ANIO,
    DEF,
    MES,
    P_ACT,
    P_ANT,
    _Asignaciones,
    _Eventos,
    _ln,
    _Uow,
)

FILTRO = FiltroEmpresa(empresa=DEF, por_defecto=DEF, empresa_obras=DEF)
TEL = SubfilaVinculado(vinculado_ide=10, tipo="TF", tipo_res="TELEFONO",
                       cod="TF-10")
GAS = SubfilaVinculado(vinculado_ide=11, tipo="CO", tipo_res="GASOIL",
                       cod="CO-11")
ELEGIDA = {"ide": 81002, "cod": "CIGA14", "res": "GASOIL"}
PROP = {"propuesta_ide": 81001, "propuesta_cod": "CICO13",
        "propuesta_res": "TELEFONIA", "propuesta_metodo": "ci_tipo",
        "propuesta_origen": None}


def _sql(stmt) -> str:
    return " ".join(str(stmt.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True})).split())


# ======================= repositorio: leer subfilas ====================== #
def _asig(id_: int | None, trabajador: int, obra: int = 7,
          pv: bool = False) -> SimpleNamespace:
    a = SimpleNamespace(obra_ide=obra, es_postventa=pv,
                        trabajador_ide=trabajador,
                        porcentaje=Decimal("40.00"), partida_ide=None,
                        partida_cod=None, partida_res=None,
                        **dict.fromkeys(("propuesta_ide", "propuesta_cod",
                                         "propuesta_res", "propuesta_metodo",
                                         "propuesta_origen")))
    if id_ is not None:
        a.id = id_
    return a


def _obra(ide: int = 7, var: bool = False) -> SimpleNamespace:
    return SimpleNamespace(ide=ide, cod=f"{ide:04d}", descripcion="OBRA",
                           activa=True, empresa=1, admite_postventa=True,
                           registro_paride=55 if var else None)


def _rv(ide: int, trabajador: int, tipo: str = "TF",
        fecha_baja: int | None = None, activo: bool = True,
        cod: str | None = None) -> RecursoVinculadoORM:
    return RecursoVinculadoORM(
        ide=ide, trabajador_ide=trabajador, tipo=tipo, tipo_res=f"T {tipo}",
        cod=cod or f"{tipo}-{ide}", descripcion="NO SALE", empresa_recurso=1,
        fecha_baja_recurso=fecha_baja, horide=900, activo=activo,
        estado_vinculo="vinculado")


class _Filas:
    def __init__(self, filas: list[Any]) -> None:
        self._filas = filas

    def all(self) -> list[Any]:
        return list(self._filas)


class _SesionPorTabla:
    """Responde a cada sentencia según la tabla que pide (y apunta las
    sentencias): `execute` las asignaciones con su obra; `scalars` los
    vinculados y las filas de subfila; `get` el periodo."""

    def __init__(self, asignaciones: list[tuple], vinculados=(), filas=(),
                 periodo=(ANIO, MES)) -> None:
        self.asignaciones = asignaciones
        self.vinculados = list(vinculados)
        self.filas = list(filas)
        self.periodo = periodo
        self.sentencias: list[Any] = []
        self.gets: list[Any] = []

    def execute(self, stmt):
        self.sentencias.append(stmt)
        return _Filas(self.asignaciones)

    def scalars(self, stmt):
        self.sentencias.append(stmt)
        entidad = stmt.column_descriptions[0]["entity"]
        if entidad is RecursoVinculadoORM:
            return _Filas(self.vinculados)
        if entidad is AsignacionVinculadoORM:
            return _Filas(self.filas)
        raise AssertionError(f"consulta inesperada: {entidad}")

    def get(self, modelo, ide):
        self.gets.append((modelo, ide))
        assert modelo is PeriodoORM
        return SimpleNamespace(id=ide, anio=self.periodo[0],
                               mes=self.periodo[1])


def test_f044_r6_sin_vinculados_la_linea_de_hoy():
    s = _SesionPorTabla([(_asig(41, 14), _obra())])
    [ln] = PgAsignacionRepository(s).lineas_de_trabajador(2, 14)  # type: ignore[arg-type]
    assert ln.vinculados == ()
    assert dataclasses.replace(ln, vinculados=()) == ln


def test_f044_r6_una_subfila_por_vinculado_vigente_en_cada_linea():
    s = _SesionPorTabla(
        [(_asig(41, 14), _obra(7)), (_asig(42, 14, 8, pv=True), _obra(8))],
        vinculados=[_rv(11, 14, "CO"), _rv(10, 14, "TF"),
                    _rv(12, 14, "VE", fecha_baja=20260630),   # baja en junio
                    _rv(13, 14, "VE", fecha_baja=20260701)])  # baja en julio
    lineas = PgAsignacionRepository(s).lineas_de_trabajador(2, 14)  # type: ignore[arg-type]
    for ln in lineas:
        assert [(v.vinculado_ide, v.tipo, v.cod) for v in ln.vinculados] == [
            (11, "CO", "CO-11"), (10, "TF", "TF-10"), (13, "VE", "VE-13")]
    assert s.gets == [(PeriodoORM, 2)]


def test_f044_r6_la_subfila_lleva_su_elegida_propuesta_y_traza():
    fila = AsignacionVinculadoORM(
        asignacion_id=41, vinculado_ide=10, partida_ide=81002,
        partida_cod="CIGA14", partida_res="GASOIL", **PROP,
        sigrid_estado="registrado", sigrid_motivo=None,
        sigrid_parte="PT26/00012", sigrid_hmores_ide=990011)
    otra = AsignacionVinculadoORM(asignacion_id=99, vinculado_ide=10,
                                  partida_ide=5)
    s = _SesionPorTabla([(_asig(41, 14), _obra()), (_asig(43, 14, 9),
                                                    _obra(9))],
                        vinculados=[_rv(10, 14)], filas=[fila, otra])
    a, b = PgAsignacionRepository(s).lineas_de_trabajador(2, 14)  # type: ignore[arg-type]
    [v] = a.vinculados
    assert (v.partida_ide, v.partida_cod, v.partida_res, v.propuesta_ide,
            v.propuesta_metodo, v.sigrid_estado, v.sigrid_parte,
            v.sigrid_hmores_ide) == (81002, "CIGA14", "GASOIL", 81001,
                                     "ci_tipo", "registrado", "PT26/00012",
                                     990011)
    [w] = b.vinculados
    assert (w.partida_ide, w.propuesta_ide, w.sigrid_estado) == (None,) * 3


def test_f044_r6_solo_consulta_los_activos_del_trabajador():
    s = _SesionPorTabla([(_asig(41, 14), _obra())], vinculados=[_rv(10, 14)])
    PgAsignacionRepository(s).lineas_del_periodo(2)  # type: ignore[arg-type]
    sql_v, sql_f = (_sql(x) for x in s.sentencias[1:])
    assert "FROM recurso_vinculado" in sql_v
    assert "recurso_vinculado.activo IS true" in sql_v
    assert "recurso_vinculado.trabajador_ide IN (14)" in sql_v
    assert "FROM asignacion_vinculado" in sql_f
    assert "asignacion_vinculado.asignacion_id IN (41)" in sql_f


def test_f044_r6_del_periodo_cada_trabajador_con_los_suyos():
    s = _SesionPorTabla([(_asig(41, 14), _obra()), (_asig(51, 15), _obra())],
                        vinculados=[_rv(10, 14), _rv(20, 15), _rv(21, 15)])
    r = PgAsignacionRepository(s).lineas_del_periodo(2)  # type: ignore[arg-type]
    assert [v.vinculado_ide for v in r[14][0].vinculados] == [10]
    assert [v.vinculado_ide for v in r[15][0].vinculados] == [20, 21]


def test_f044_r6_sin_ids_no_consulta_nada_mas():
    """Las asignaciones sin `id` (no hay nada que casar) no piden ni el
    periodo ni los vinculados."""
    s = _SesionPorTabla([(_asig(None, 14), _obra())],
                        vinculados=[_rv(10, 14)])
    [ln] = PgAsignacionRepository(s).lineas_de_trabajador(2, 14)  # type: ignore[arg-type]
    assert ln.vinculados == () and s.gets == [] and len(s.sentencias) == 1


def test_f044_r6_sin_lineas_no_consulta_nada_mas():
    s = _SesionPorTabla([])
    assert PgAsignacionRepository(s).lineas_del_periodo(2) == {}  # type: ignore[arg-type]
    assert len(s.sentencias) == 1


# ===================== repositorio: guardar subfilas ===================== #
class _SesionReemplazo:
    def __init__(self) -> None:
        self.anadidos: list[Any] = []
        self.ejecutadas: list[Any] = []
        self.flushes = 0

    def execute(self, stmt):
        self.ejecutadas.append(stmt)
        return SimpleNamespace(rowcount=1)

    def add(self, objeto):
        self.anadidos.append(objeto)

    def flush(self):
        self.flushes += 1
        for i, o in enumerate(self.anadidos, start=500):
            if isinstance(o, AsignacionORM) and o.id is None:
                o.id = i


def _lv(obra: int, pct: str, *vinculados: SubfilaVinculado, **kw) -> Linea:
    return Linea(obra_ide=obra, es_postventa=False, porcentaje=Decimal(pct),
                 vinculados=vinculados, **kw)


def test_f044_r8_reemplazar_guarda_lo_de_cada_subfila():
    s = _SesionReemplazo()
    tel = dataclasses.replace(TEL, **PROP)
    gas = dataclasses.replace(GAS, partida_ide=81002, partida_cod="CIGA14",
                              partida_res="GASOIL")
    PgAsignacionRepository(s).reemplazar(  # type: ignore[arg-type]
        3, 14, [_lv(100, "60", tel, gas), _lv(101, "40", TEL)], "pgris")
    asig = [o for o in s.anadidos if isinstance(o, AsignacionORM)]
    subs = [o for o in s.anadidos if isinstance(o, AsignacionVinculadoORM)]
    assert [(o.asignacion_id, o.vinculado_ide, o.partida_ide,
             o.propuesta_ide, o.propuesta_metodo) for o in subs] == [
        (asig[0].id, 10, None, 81001, "ci_tipo"),
        (asig[0].id, 11, 81002, None, None)]
    assert s.flushes == 2
    assert all(o.sigrid_estado is None for o in subs)


def test_f044_r8_reemplazar_sin_subfilas_que_guardar_como_hoy():
    s = _SesionReemplazo()
    PgAsignacionRepository(s).reemplazar(  # type: ignore[arg-type]
        3, 14, [_lv(100, "60", TEL)], "pgris")
    assert [type(o) for o in s.anadidos] == [AsignacionORM]
    assert s.flushes == 1


@pytest.mark.parametrize("solo_si_vacia, condicion", [
    (False, "WHERE asignacion_vinculado.partida_ide IS NULL"),
    (True, ("WHERE asignacion_vinculado.partida_ide IS NULL AND "
            "asignacion_vinculado.propuesta_ide IS NULL"))])
def test_f044_r9_guardar_propuesta_de_subfila(solo_si_vacia, condicion):
    s = _SesionReemplazo()
    hecho = PgAsignacionRepository(s).guardar_propuesta_vinculado(  # type: ignore[arg-type]
        3, 14, (100, True), 10,
        {"paride": 81001, "cod": "CICO13", "res": "TELEFONIA",
         "metodo": "ci_tipo", "origen": None}, solo_si_vacia=solo_si_vacia)
    assert hecho is True
    [stmt] = s.ejecutadas
    sql = _sql(stmt)
    assert sql.startswith(
        "INSERT INTO asignacion_vinculado (asignacion_id, vinculado_ide, "
        "propuesta_ide, propuesta_cod, propuesta_res, propuesta_metodo, "
        "propuesta_origen) SELECT asignacion.id, 10")
    for trozo in ("asignacion.periodo_id = 3", "asignacion.trabajador_ide = 14",
                  "asignacion.obra_ide = 100", "asignacion.es_postventa = true",
                  "ON CONFLICT (asignacion_id, vinculado_ide) DO UPDATE SET"):
        assert trozo in sql, trozo
    assert sql.endswith(
        (condicion, condicion + " RETURNING asignacion_vinculado.id"))


# ======================== casos de uso (memoria) ========================= #
class _AsigVin(_Asignaciones):
    """`reemplazar` que conserva modo, partida, propuesta y subfilas."""

    def reemplazar(self, periodo_id, ide, lineas, usuario):
        self._uow.lineas.setdefault(periodo_id, {})[ide] = [
            dataclasses.replace(
                _ln(ln.obra_ide, str(ln.porcentaje)),
                es_postventa=ln.es_postventa, partida_ide=ln.partida_ide,
                partida_cod=ln.partida_cod, partida_res=ln.partida_res,
                partida_fija=ln.partida_fija,
                **{c: getattr(ln, c) for c in PROP},
                vinculados=tuple(
                    dataclasses.replace(
                        v, tipo=None, tipo_res=None, cod=None)
                    for v in ln.vinculados))
            for ln in lineas]
        self._uow.reemplazados.append(ide)


class _EventosConTipo(_Eventos):
    def __init__(self) -> None:
        super().__init__()
        self.tipos: list[str] = []
        self.despues: list[list[dict]] = []

    def registrar(self, periodo_id, ide, tipo, usuario, antes, despues):
        self.tipos.append(tipo.value)
        self.despues.append(despues)
        self.eventos.append((ide, EventoPendiente(
            len(self.eventos) + 1, usuario, antes, tipo=tipo.value)))


def _uow(actual: list[Linea], anterior: list[Linea] | None = None) -> _Uow:
    uow = _Uow({P_ACT: {10: actual}, P_ANT: {10: anterior or []}})
    uow.asignaciones = _AsigVin(uow)
    uow.eventos = _EventosConTipo()
    return uow


def _con(ln: Linea, *vinculados: SubfilaVinculado, **kw) -> Linea:
    return dataclasses.replace(ln, vinculados=vinculados, **kw)


def _subs(uow: _Uow, periodo: int = P_ACT) -> list[tuple]:
    return [(ln.obra_ide, v.vinculado_ide, v.partida_ide, v.propuesta_ide)
            for ln in uow.lineas[periodo][10] for v in ln.vinculados]


def _cambiar(uow, partida, vinculado_ide=10, obra=100, **kw):
    return CambiarPartida().ejecutar(
        uow, ANIO, MES, 10, obra, False, partida, "pgris", filtro=FILTRO,
        vinculado_ide=vinculado_ide, **kw)


def test_f044_r8_cambiar_la_partida_de_la_subfila_deja_su_evento():
    uow = _uow([_con(_ln(100, "60"), TEL, GAS), _ln(101, "40")])
    _cambiar(uow, ELEGIDA, vinculado_ide=11)
    assert _subs(uow) == [(100, 10, None, None), (100, 11, 81002, None)]
    assert uow.eventos.tipos == [TipoEvento.PARTIDA_VINCULADO.value]
    assert uow.eventos.despues[0][0]["vinculados"] == [
        {"vinculado_ide": 11, "partida_ide": 81002, "partida_cod": "CIGA14",
         "partida_res": "GASOIL"}]
    # La partida del titular no cambia.
    assert uow.lineas[P_ACT][10][0].partida_ide is None


def test_f044_r8_la_elegida_se_lleva_la_propuesta_de_la_subfila():
    uow = _uow([_con(_ln(100, "60"), dataclasses.replace(TEL, **PROP))])
    _cambiar(uow, ELEGIDA)
    assert _subs(uow) == [(100, 10, 81002, 81001)]
    _cambiar(uow, None)                                   # automática
    assert _subs(uow) == [(100, 10, None, 81001)]


def test_f044_r8_misma_partida_ni_escribe_ni_deja_evento():
    sub = dataclasses.replace(TEL, partida_ide=81002, partida_cod="CIGA14",
                              partida_res="GASOIL")
    uow = _uow([_con(_ln(100, "60"), sub)])
    _cambiar(uow, ELEGIDA)
    assert uow.reemplazados == [] and uow.eventos.tipos == []


def test_f044_r8_vinculado_que_no_es_de_la_linea():
    uow = _uow([_con(_ln(100, "60"), TEL)])
    with pytest.raises(LineaNoEncontrada, match="vinculado 99"):
        _cambiar(uow, ELEGIDA, vinculado_ide=99)


def test_f044_r8_la_subfila_de_una_entrada_var_tiene_la_partida_fija():
    uow = _uow([_con(_ln(100, "60"), TEL, partida_fija=True)])
    with pytest.raises(ObraNoValida, match="fija"):
        _cambiar(uow, ELEGIDA)


def test_f044_r8_deshacer_devuelve_la_partida_de_la_subfila():
    sub = dataclasses.replace(TEL, partida_ide=5, partida_cod="CIX",
                              partida_res="X")
    uow = _uow([_con(_ln(100, "60"), sub, GAS)])
    _cambiar(uow, ELEGIDA)
    assert _subs(uow)[0][2] == 81002
    DeshacerUltimaModificacion().ejecutar(uow, ANIO, MES, 10, "pgris",
                                          filtro=FILTRO)
    assert _subs(uow) == [(100, 10, 5, None)]


def test_f044_r8_guardar_la_fila_conserva_la_subfila():
    sub = dataclasses.replace(TEL, partida_ide=81002, partida_cod="CIGA14",
                              partida_res="GASOIL", **PROP)
    uow = _uow([_con(_ln(100, "60"), sub), _ln(101, "40")])
    GuardarAsignaciones().ejecutar(
        uow, ANIO, MES, 10, [{"obra_ide": 100, "porcentaje": "50"},
                             {"obra_ide": 101, "porcentaje": "50"}],
        "pgris", filtro=FILTRO)
    assert _subs(uow) == [(100, 10, 81002, 81001)]


def test_f044_r8_copiar_el_mes_copia_la_elegida_sin_la_propuesta():
    sub = dataclasses.replace(TEL, partida_ide=81002, partida_cod="CIGA14",
                              partida_res="GASOIL", **PROP)
    gas = dataclasses.replace(GAS, **PROP)
    for caso in (CopiarPeriodoAnterior, CopiarTrabajadorAnterior):
        uow = _uow([], anterior=[_con(_ln(100, "100"), sub, gas)])
        if caso is CopiarPeriodoAnterior:
            caso().ejecutar(uow, ANIO, MES, "pgris", filtro=FILTRO)
        else:
            caso().ejecutar(uow, ANIO, MES, 10, "pgris", filtro=FILTRO)
        assert _subs(uow) == [(100, 10, 81002, None), (100, 11, None, None)]


def test_f044_r9_cambiar_la_partida_del_titular_borra_las_propuestas():
    """La propuesta de la subfila depende de la partida del titular: al
    cambiarla se recalcula (la elegida de la subfila se queda)."""
    elegida = dataclasses.replace(GAS, partida_ide=7, partida_cod="CIX")
    uow = _uow([_con(_ln(100, "60"), dataclasses.replace(TEL, **PROP),
                     elegida)])
    CambiarPartida().ejecutar(uow, ANIO, MES, 10, 100, False,
                              {"ide": 81101, "cod": "CD.1", "res": "H"},
                              "pgris", filtro=FILTRO)
    assert _subs(uow) == [(100, 10, None, None), (100, 11, 7, None)]
    assert uow.eventos.tipos == [TipoEvento.PARTIDA.value]


def test_f044_r15_snapshot_sin_elegidas_de_subfila_como_hoy():
    from application.use_cases import _snapshot
    assert _snapshot([_con(_ln(100, "60"), dataclasses.replace(TEL, **PROP))]
                     ) == [{"obra_ide": 100, "es_postventa": False,
                            "porcentaje": "60"}]


def test_f044_r8_validar_lineas_lee_las_subfilas_del_snapshot():
    from application.use_cases import _validar_lineas
    [ln] = _validar_lineas(_uow([]), [
        {"obra_ide": 100, "porcentaje": "60", "vinculados": [
            {"vinculado_ide": 11, "partida_ide": 81002,
             "partida_cod": "CIGA14", "partida_res": "GASOIL"}]}])
    assert ln.vinculados == (SubfilaVinculado(
        vinculado_ide=11, partida_ide=81002, partida_cod="CIGA14",
        partida_res="GASOIL"),)


# ============================== salida =================================== #
CAMPOS_SUBFILA = {"vinculado_ide", "tipo", "tipo_res", "cod", "partida_ide",
                  "partida_cod", "partida_res", "partida_fija",
                  "propuesta_cod", "propuesta_res", "propuesta_metodo"}


def _fila(*lineas: Linea):
    from domain.models import CuadranteTrabajador

    from tests.test_f024_cuadrante_empresa import TRABAJADORES
    return CuadranteTrabajador(trabajador=TRABAJADORES[10],
                               lineas=list(lineas))


def test_f044_r6_salida_sin_vinculados_sin_la_clave():
    from interface_adapters.api.schemas import a_trabajador_out

    from tests.test_f034_rutas import CAMPOS_LINEA
    out = a_trabajador_out(_fila(_ln(100, "60")), DEF).model_dump(mode="json")
    assert set(out["lineas"][0]) == CAMPOS_LINEA


def test_f044_r6_r7_salida_con_las_subfilas():
    from interface_adapters.api.schemas import a_trabajador_out

    from tests.test_f034_rutas import CAMPOS_LINEA
    sub = dataclasses.replace(TEL, **PROP, sigrid_estado="registrado")
    out = a_trabajador_out(_fila(_con(_ln(100, "60"), sub, GAS,
                                      partida_fija=True)), DEF
                           ).model_dump(mode="json")
    [ln] = out["lineas"]
    assert set(ln) == {*CAMPOS_LINEA, "vinculados"}
    assert ln["vinculados"] == [
        {"vinculado_ide": 10, "tipo": "TF", "tipo_res": "TELEFONO",
         "cod": "TF-10", "partida_ide": None, "partida_cod": None,
         "partida_res": None, "partida_fija": True, "propuesta_cod": "CICO13",
         "propuesta_res": "TELEFONIA", "propuesta_metodo": "ci_tipo"},
        {"vinculado_ide": 11, "tipo": "CO", "tipo_res": "GASOIL",
         "cod": "CO-11", "partida_ide": None, "partida_cod": None,
         "partida_res": None, "partida_fija": True, "propuesta_cod": None,
         "propuesta_res": None, "propuesta_metodo": None}]
    assert all(set(v) == CAMPOS_SUBFILA for v in ln["vinculados"])
    assert "porcentaje" not in ln["vinculados"][0]          # R7


def test_f044_r8_partida_in_admite_el_vinculado():
    from interface_adapters.api.schemas import PartidaIn
    from pydantic import ValidationError

    assert PartidaIn(obra_ide=1, partida=None).vinculado_ide is None
    assert PartidaIn(obra_ide=1, partida=None, vinculado_ide=10
                     ).vinculado_ide == 10
    with pytest.raises(ValidationError):
        PartidaIn(obra_ide=1, partida=None, vinculado_ide=0)


# ============================= selector (R8, R9) ========================= #
CATALOGO = [
    {"ide": 80001, "cod": "CI.1.10", "res": "ENCARGADO", "categoria": "CI",
     "mayor": "CI"},
    {"ide": 81001, "cod": "CICO13", "res": "TELEFONIA", "categoria": "CI",
     "mayor": "CI"},
    {"ide": 81101, "cod": "CD.1", "res": "HORMIGON", "categoria": "CD",
     "mayor": "CD"}]
PROP_TRANSFER = {"paride": 81001, "cod": "CICO13", "res": "TELEFONIA",
                 "metodo": "ci_tipo", "origen": None}


class _Transfer:
    def __init__(self, vinculados: dict | None = None) -> None:
        self.payloads: list[dict] = []
        self.vinculados = vinculados

    def propuesta_partidas(self, payload: dict) -> dict:
        self.payloads.append(payload)
        r = {"ok": True, "partidas_obra": CATALOGO, "partidas_postventa": [],
             "propuestas": {"linea": {"paride": 80001, "cod": "CI.1.10",
                                      "res": "ENCARGADO",
                                      "metodo": "auto_nombre",
                                      "origen": None}},
             "mayor_inicial": {"linea": "CI"}}
        if self.vinculados is not None:
            r["vinculados"] = self.vinculados
        return r


class _AsigGuarda(_AsigVin):
    def __init__(self, uow) -> None:
        super().__init__(uow)
        self.guardadas: list[tuple] = []

    def guardar_propuesta(self, *a, **kw):
        self.guardadas.append(("titular", a))
        return True

    def guardar_propuesta_vinculado(self, periodo_id, trabajador_ide, clave,
                                    vinculado_ide, propuesta, *,
                                    solo_si_vacia=False):
        self.guardadas.append(("vinculado", periodo_id, trabajador_ide,
                               clave, vinculado_ide, propuesta,
                               solo_si_vacia))
        return True


def _selector(uow, transfer, **kw):
    from application.partidas_linea import PartidasDeLinea

    return PartidasDeLinea(transfer).ejecutar(
        uow, ANIO, MES, 10, 100, False, empresa_obras=DEF, **kw)


def _uow_selector(*lineas: Linea) -> _Uow:
    uow = _uow(list(lineas))
    uow.asignaciones = _AsigGuarda(uow)
    return uow


def test_f044_r9_selector_de_la_subfila_propone_y_guarda():
    uow = _uow_selector(_con(_ln(100, "60"), TEL, partida_ide=80002,
                             partida_cod="CI.1.20"))
    t = _Transfer({"linea": {"10": PROP_TRANSFER}})
    r = _selector(uow, t, vinculado_ide=10)
    [p] = t.payloads
    assert p["lineas"] == [{
        "clave": "linea", "recurso_ide": 10, "nombre": "Ana",
        "categoria": "Encargado", "es_postventa": False, "paride": 80002,
        "vinculados": [{"recurso_ide": 10, "tipo": "TF", "categoria": None,
                        "cod": "TF-10"}]}]
    assert r == {"partidas": CATALOGO, "partidas_postventa": [],
                 "ambito": "CI", "propuesta": PROP_TRANSFER,
                 "elegida": None, "fija": None}
    assert uow.asignaciones.guardadas == [
        ("vinculado", P_ACT, 10, (100, False), 10, PROP_TRANSFER, False)]


def test_f044_r9_selector_de_la_subfila_con_elegida_no_guarda():
    sub = dataclasses.replace(TEL, partida_ide=81101, partida_cod="CD.1",
                              partida_res="HORMIGON")
    uow = _uow_selector(_con(_ln(100, "60"), sub))
    r = _selector(uow, _Transfer({"linea": {"10": PROP_TRANSFER}}),
                  vinculado_ide=10)
    assert (r["elegida"], r["ambito"]) == (
        {"ide": 81101, "cod": "CD.1", "res": "HORMIGON"}, "CD")
    assert uow.asignaciones.guardadas == []


def test_f044_r9_selector_sin_propuesta_de_la_subfila_sale_en_ci():
    uow = _uow_selector(_con(_ln(100, "60"), TEL))
    r = _selector(uow, _Transfer({"linea": {"10": None}}), vinculado_ide=10)
    assert (r["propuesta"], r["ambito"]) == (None, "CI")
    assert uow.asignaciones.guardadas == []


def test_f044_r9_selector_de_un_vinculado_que_no_es_de_la_linea():
    uow = _uow_selector(_con(_ln(100, "60"), TEL))
    with pytest.raises(LineaNoEncontrada, match="vinculado 99"):
        _selector(uow, _Transfer(), vinculado_ide=99)


def test_f044_r9_selector_de_la_subfila_var_es_fija_sin_transfer():
    uow = _uow_selector(_con(_ln(100, "60"), TEL, partida_fija=True))
    t = _Transfer()
    r = _selector(uow, t, vinculado_ide=10)
    assert r["fija"] == {"ide": -100, "cod": "0100", "res": "OBRA 100"}
    assert t.payloads == []


def test_f044_r8_selector_sin_vinculado_como_hoy():
    uow = _uow_selector(_con(_ln(100, "60"), TEL))
    t = _Transfer({"linea": {"10": PROP_TRANSFER}})
    _selector(uow, t)
    assert t.payloads[0]["lineas"] == [{
        "clave": "linea", "recurso_ide": 10, "nombre": "Ana",
        "categoria": "Encargado", "es_postventa": False}]


# ============================ preflight (R9) ============================= #
def test_f044_r9_el_preflight_guarda_las_propuestas_de_las_subfilas():
    from application.registro_sigrid import RegistroSigrid

    class _S:
        def __init__(self) -> None:
            self.ejecutadas: list[Any] = []
            self.commits = 0

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return None

        def execute(self, stmt):
            self.ejecutadas.append(stmt)

        def commit(self):
            self.commits += 1

    s = _S()
    reg = RegistroSigrid(lambda: s, None, 1)  # type: ignore[arg-type]
    reg._guardar_propuestas([{"ok": True, "acciones": [], "vinculados": [
        {"registro_id": 41, "recurso_ide": 10, "accion": "escribir",
         "paride": 81001, "partida_cod": "CICO13", "partida_res": "TELEFONIA",
         "partida_metodo": "ci_tipo", "partida_origen": None},
        {"registro_id": 41, "recurso_ide": 11, "paride": 81002,
         "partida_metodo": "manual"},
        {"registro_id": 42, "recurso_ide": 10, "paride": 0,
         "partida_metodo": None},
        {"registro_id": 43, "recurso_ide": 12, "paride": 70001,
         "partida_cod": "0678", "partida_metodo": "titular"}]}])
    cabecera = ("INSERT INTO asignacion_vinculado (asignacion_id, "
                "vinculado_ide, propuesta_ide, propuesta_cod, propuesta_res, "
                "propuesta_metodo, propuesta_origen) VALUES ")
    assert [_sql(x).split(" ON CONFLICT")[0] for x in s.ejecutadas] == [
        cabecera + "(41, 10, 81001, 'CICO13', 'TELEFONIA', 'ci_tipo', NULL)",
        cabecera + "(43, 12, 70001, '0678', NULL, 'titular', NULL)"]
    assert all(_sql(x).endswith("WHERE asignacion_vinculado.partida_ide IS "
                                "NULL RETURNING asignacion_vinculado.id")
               for x in s.ejecutadas)
    assert s.commits == 1


def test_f044_r9_metodos_de_propuesta_de_subfila():
    from application.registro_sigrid import es_metodo_de_propuesta_vinculado

    assert [es_metodo_de_propuesta_vinculado(m) for m in (
        "ci_tipo", "titular", "manual", "auto_nombre", None)] == [
        True, True, False, False, False]


# ========================= segundo plano (R9) ============================ #
class _TransferLote:
    def __init__(self, respuesta) -> None:
        self.respuesta = respuesta
        self.peticiones: list[list[dict]] = []

    def propuesta_lote(self, peticiones):
        self.peticiones.append(peticiones)
        return self.respuesta(peticiones)


class _EjecutorEnLinea:
    def submit(self, fn, *a):
        fn(*a)


def _mes(uow, transfer):
    from application.propuestas_mes import PropuestasDelMes

    class _Fabrica:
        def __call__(self):
            return self

        def __enter__(self):
            return uow

        def __exit__(self, *exc):
            return None

    return PropuestasDelMes(_Fabrica(), transfer, _EjecutorEnLinea(),
                            empresa_obras=DEF)


def _periodos_abiertos(uow) -> None:
    from domain.models import Periodo
    uow.periodos.obtener = lambda a, m: (P_ACT, Periodo(a, m))


def test_f044_r9_en_segundo_plano_se_proponen_las_subfilas():
    titular = dataclasses.replace(_ln(100, "60"), propuesta_ide=80001,
                                  propuesta_metodo="auto_nombre")
    pv = dataclasses.replace(_ln(101, "40"), es_postventa=True)
    uow = _uow_selector(_con(titular, TEL), _con(pv, GAS))
    _periodos_abiertos(uow)

    def respuesta(peticiones):
        return {"ok": True, "obras": [
            {"ok": True, "propuestas": {}, "vinculados": {
                ln["clave"]: {str(v["recurso_ide"]): PROP_TRANSFER
                              for v in ln["vinculados"]}
                for ln in p["lineas"]}} for p in peticiones]}

    t = _TransferLote(respuesta)
    _, pendientes = _mes(uow, t).encolar(ANIO, MES)
    [peticiones] = t.peticiones
    assert [p["lineas"] for p in peticiones] == [
        [{"clave": "10", "recurso_ide": 10, "nombre": "Ana",
          "categoria": "Encargado", "es_postventa": False,
          "vinculados": [{"recurso_ide": 10, "tipo": "TF", "categoria": None,
                          "cod": "TF-10"}]}],
        [{"clave": "10:pv", "recurso_ide": 10, "nombre": "Ana",
          "categoria": "Encargado", "es_postventa": True,
          "vinculados": [{"recurso_ide": 11, "tipo": "CO", "categoria": None,
                          "cod": "CO-11"}]}]]
    assert uow.asignaciones.guardadas == [
        ("vinculado", P_ACT, 10, (100, False), 10, PROP_TRANSFER, True),
        ("vinculado", P_ACT, 10, (101, True), 11, PROP_TRANSFER, True)]
    assert pendientes == frozenset()            # el titular no estaba


def test_f044_r9_en_segundo_plano_titular_y_subfila_en_la_misma_linea():
    uow = _uow_selector(_con(_ln(100, "60"), TEL))
    _periodos_abiertos(uow)
    t = _TransferLote(lambda ps: {"ok": True, "obras": [
        {"ok": True, "propuestas": {"10": {**PROP_TRANSFER,
                                           "metodo": "auto_nombre"}},
         "vinculados": {"10": {"10": None}}}]})
    m = _mes(uow, t)
    m.encolar(ANIO, MES)
    assert [g[0] for g in uow.asignaciones.guardadas] == ["titular"]
    assert t.peticiones[0][0]["lineas"][0]["vinculados"][0]["recurso_ide"] \
        == 10
    # La subfila sin propuesta posible no se vuelve a pedir hasta un sync.
    m.encolar(ANIO, MES)
    assert len(t.peticiones) == 2
    assert "vinculados" not in t.peticiones[1][0]["lineas"][0]


def test_f044_r9_en_segundo_plano_sin_subfilas_la_peticion_de_hoy():
    uow = _uow_selector(_ln(100, "60"))
    _periodos_abiertos(uow)
    t = _TransferLote(lambda ps: {"ok": True, "obras": [
        {"ok": True, "propuestas": {"10": None}}]})
    _mes(uow, t).encolar(ANIO, MES)
    assert t.peticiones[0][0]["lineas"] == [
        {"clave": "10", "recurso_ide": 10, "nombre": "Ana",
         "categoria": "Encargado", "es_postventa": False}]


def test_f044_r9_en_segundo_plano_ni_elegidas_ni_var_ni_ya_propuestas():
    elegida = dataclasses.replace(TEL, partida_ide=5)
    propuesta = dataclasses.replace(GAS, propuesta_ide=6)
    titular = dataclasses.replace(_ln(100, "60"), propuesta_ide=80001)
    var = dataclasses.replace(_ln(101, "40"), partida_fija=True)
    uow = _uow_selector(_con(titular, elegida, propuesta), _con(var, TEL))
    _periodos_abiertos(uow)
    t = _TransferLote(lambda ps: {"ok": True, "obras": []})
    assert _mes(uow, t).encolar(ANIO, MES) == (False, frozenset())
    assert t.peticiones == []


# ================================ rutas (R8) ============================= #
class _SelectorEspia:
    def __init__(self) -> None:
        self.llamadas: list[dict] = []

    def ejecutar(self, uow, anio, mes, ide, obra, pv, **kw):
        self.llamadas.append(kw)
        return {"partidas": [], "partidas_postventa": [], "ambito": None,
                "propuesta": None, "elegida": None, "fija": None}


@pytest.mark.parametrize("params, esperado", [
    ({}, {"empresa_obras": DEF}),
    ({"vinculado_ide": 10}, {"empresa_obras": DEF, "vinculado_ide": 10})])
def test_f044_r8_get_partidas_pasa_el_vinculado_solo_si_viene(
        monkeypatch, params, esperado):
    from tests.test_f050_rutas_partida import BASE, _cliente
    espia = _SelectorEspia()
    cliente, _ = _cliente({14: []}, monkeypatch, partidas_linea=espia)
    r = cliente.get(f"{BASE}/trabajadores/14/partidas",
                    params={"obra_ide": 100, **params})
    assert r.status_code == 200, r.text
    assert espia.llamadas == [esperado]


def test_f044_r8_put_partida_de_la_subfila(monkeypatch):
    from tests.test_f050_partida_linea import _lp
    from tests.test_f050_rutas_partida import BASE, PARTIDA, _cliente
    cliente, uow = _cliente({14: [_con(_lp(100, "60"), TEL)]}, monkeypatch)
    uow.asignaciones = _AsigVin(uow)
    cuerpo = {"obra_ide": 100, "partida": PARTIDA}
    r = cliente.put(f"{BASE}/trabajadores/14/partida",
                    headers={"X-Usuario": "ana"},
                    json={**cuerpo, "vinculado_ide": 10})
    assert r.status_code == 200, r.text
    assert [t for _, t, *_ in uow.eventos.tipos] == ["PARTIDA_VINCULADO"]
    [ln] = r.json()["trabajador"]["lineas"]
    assert (ln["partida_ide"], [(v["vinculado_ide"], v["partida_cod"])
                                for v in ln["vinculados"]]) == (
        None, [(10, PARTIDA["cod"])])
    r = cliente.put(f"{BASE}/trabajadores/14/partida",
                    headers={"X-Usuario": "ana"},
                    json={**cuerpo, "vinculado_ide": 99})
    assert r.status_code == 404, r.text
    assert "vinculado 99" in r.text
