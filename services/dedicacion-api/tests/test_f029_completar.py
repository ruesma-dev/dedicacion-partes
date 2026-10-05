# tests/test_f029_completar.py
"""F-029 · Completar hasta el 100 % en una obra, por lote (R14-R26).

Tres bloques, uno por capa: la regla pura del dominio
(`domain.estados.completar_hasta_100`), el caso de uso `CompletarHasta100`
con la UnitOfWork en memoria de `test_f024_cuadrante_empresa.py` (sin
editarla: lo que falta se amplía aquí) y la ruta
`POST /periodos/{anio}/{mes}/completar` con la fixture `api` de
`test_f024_rutas_empresa.py`. Ni red, ni BBDD, ni `.env`. La regla, en
`docs/ARCHITECTURE.md#regla-completar`.
"""
from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest
from application.use_cases import (
    CompletarHasta100,
    DeshacerUltimaModificacion,
    ObtenerCuadrante,
    _snapshot,
)
from domain.errors import (
    DeshacerAjeno,
    ObraNoValida,
    PeriodoCerrado,
    PeriodoNoEncontrado,
)
from domain.estados import calcular_estado, completar_hasta_100
from domain.models import (
    Completado,
    EstadoPeriodo,
    EstadoTrabajador,
    FiltroEmpresa,
    Linea,
    Obra,
    Periodo,
    ResultadoCompletado,
    ResultadoCompletarTrabajador,
    ResumenPeriodo,
    TipoEvento,
)

from tests.test_f024_cuadrante_empresa import (
    ANIO,
    MES,
    OBRAS,
    P_ACT,
    _Asignaciones,
    _Eventos,
    _lineas_actuales,
    _ln,
    _Periodos,
    _Uow,
)
from tests.test_f024_rutas_empresa import BASE, api  # noqa: F401 (fixture)


# ============================== dominio (T1) ============================ #
def _l(obra_ide: int, pct: str, pv: bool = False, cod: str = "") -> Linea:
    return Linea(obra_ide=obra_ide, es_postventa=pv, porcentaje=Decimal(pct),
                 cod=cod)


def _total(lineas: list[Linea]) -> Decimal:
    return sum((ln.porcentaje for ln in lineas), Decimal("0"))


def test_f029_r15_dominio_falta_suma_a_la_linea_existente():
    """R15 · En FALTA con línea en el destino: lo que falta se suma a esa
    línea, en su sitio; las demás salen idénticas (el mismo objeto)."""
    otra = _l(100, "30.00", cod="0100")
    destino = _l(101, "20.50", cod="0101")
    resultado = completar_hasta_100([otra, destino], 101, False)
    assert resultado == Completado(
        lineas=[otra, _l(101, "70.00", cod="0101")], anadido=Decimal("49.50"))
    assert resultado.lineas[0] is otra
    # La sumada conserva el resto de sus datos (código incluido).
    assert resultado.lineas[1].cod == "0101"


def test_f029_r15_dominio_falta_sin_linea_anade_una_al_final():
    """R15 · En FALTA sin línea en el destino: línea nueva al final con lo
    que falta; las demás, idénticas y en su orden."""
    a, b = _l(100, "30"), _l(900, "25.25")
    resultado = completar_hasta_100([a, b], 101, False)
    assert resultado is not None
    assert resultado.lineas[:2] == [a, b]
    assert resultado.lineas[0] is a and resultado.lineas[1] is b
    nueva = resultado.lineas[2]
    assert (nueva.obra_ide, nueva.es_postventa, nueva.porcentaje) == (
        101, False, Decimal("44.75"))
    assert resultado.anadido == Decimal("44.75")
    assert len(resultado.lineas) == 3


def test_f029_r15_dominio_sin_carga_crea_la_linea_del_100():
    """R15 · SIN_CARGA: una sola línea nueva con el 100 %."""
    resultado = completar_hasta_100([], 101, False)
    assert resultado == Completado(
        lineas=[Linea(obra_ide=101, es_postventa=False,
                      porcentaje=Decimal("100.00"))],
        anadido=Decimal("100.00"))


@pytest.mark.parametrize("lineas", [
    [_l(100, "60"), _l(101, "40")],          # exacto
    [_l(100, "99.995")],                      # dentro de la épsilon (OK)
    [_l(100, "100.005")],                     # dentro de la épsilon (OK)
])
def test_f029_r17_dominio_ok_no_se_toca(lineas):
    """R17 · OK (con la misma épsilon que `calcular_estado`): nada."""
    assert calcular_estado(_total(lineas), len(lineas)) is EstadoTrabajador.OK
    assert completar_hasta_100(lineas, 101, False) is None


@pytest.mark.parametrize("lineas", [
    [_l(100, "60"), _l(101, "40.01")],
    [_l(101, "150")],
])
def test_f029_r17_dominio_exceso_no_se_toca(lineas):
    """R17 · EXCESO: nada (ni se resta)."""
    assert calcular_estado(_total(lineas),
                           len(lineas)) is EstadoTrabajador.EXCESO
    assert completar_hasta_100(lineas, 101, False) is None


def test_f029_r16_dominio_falta_0_01_se_completa_y_queda_en_100_00():
    """D5 · Falta 0,01 (fuera de la épsilon de 0,005): se completa y el
    total queda exactamente en 100,00, estado OK."""
    resultado = completar_hasta_100([_l(100, "99.99")], 100, False)
    assert resultado is not None
    assert resultado.anadido == Decimal("0.01")
    assert _total(resultado.lineas) == Decimal("100.00")
    assert calcular_estado(_total(resultado.lineas),
                           len(resultado.lineas)) is EstadoTrabajador.OK


@pytest.mark.parametrize("lineas, obra, pv", [
    ([_l(100, "33.33"), _l(900, "33.33")], 101, False),
    ([_l(100, "12.34", pv=True)], 100, False),
    ([_l(100, "0.01")], 100, True),
])
def test_f029_r16_dominio_el_total_queda_exactamente_en_100(lineas, obra, pv):
    """R16 · Tras completar, total = 100,00 exacto y estado OK."""
    resultado = completar_hasta_100(lineas, obra, pv)
    assert resultado is not None
    assert _total(resultado.lineas) == Decimal("100.00")
    assert resultado.anadido == Decimal("100.00") - _total(lineas)


def test_f029_r16_dominio_lo_que_falta_va_a_escala_de_centesimas():
    """D5 · La escala de la columna (`Numeric(6,2)`): lo añadido sale con
    dos decimales aunque el total llegue con más."""
    resultado = completar_hasta_100([_l(100, "50.004")], 101, False)
    assert resultado is not None
    assert resultado.anadido == Decimal("50.00")
    assert resultado.anadido.as_tuple().exponent == -2


def test_f029_r18_dominio_postventa_no_suma_a_la_normal_ni_al_reves():
    """R18 · `es_postventa` es parte de la clave (`#regla-p5`)."""
    normal = _l(100, "40")
    resultado = completar_hasta_100([normal], 100, True)
    assert resultado is not None
    assert resultado.lineas[0] is normal
    assert resultado.lineas[1].clave() == (100, True)
    assert resultado.lineas[1].porcentaje == Decimal("60.00")

    postv = _l(100, "40", pv=True)
    resultado = completar_hasta_100([postv], 100, False)
    assert resultado is not None
    assert resultado.lineas[0] is postv
    assert resultado.lineas[1].clave() == (100, False)

    resultado = completar_hasta_100([normal, postv], 100, True)
    assert resultado is not None
    assert resultado.lineas == [normal, _l(100, "60.00", pv=True)]


def test_f029_r19_dominio_tipos_nuevos():
    """R19, R25 · El evento `COMPLETAR` y los resultados posibles, con el
    valor igual al nombre; el resultado por trabajador lleva 0 por defecto."""
    assert TipoEvento.COMPLETAR.value == "COMPLETAR"
    assert [r.value for r in ResultadoCompletado] == [
        "COMPLETADO", "YA_AL_100", "EXCESO", "NO_VIGENTE", "NO_VISIBLE"]
    r = ResultadoCompletarTrabajador(trabajador_ide=7,
                                     resultado=ResultadoCompletado.NO_VISIBLE)
    assert r.anadido == Decimal("0")


def test_f029_r25_dominio_resultados_inmutables():
    """R25 · Lo que devuelve la regla y el resultado por trabajador no se
    pueden reescribir entre el caso de uso y la respuesta (como
    `EventoPendiente` en F-027): son `frozen`."""
    completado = Completado(lineas=[], anadido=Decimal("1"))
    with pytest.raises(dataclasses.FrozenInstanceError):
        completado.anadido = Decimal("2")  # type: ignore[misc]
    r = ResultadoCompletarTrabajador(7, ResultadoCompletado.EXCESO)
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.resultado = ResultadoCompletado.COMPLETADO  # type: ignore[misc]
    assert (completado.anadido, r.resultado) == (
        Decimal("1"), ResultadoCompletado.EXCESO)

# =========================== caso de uso (T2) =========================== #
# Doble de F-024 SIN editarlo: lo que le falta (conservar `es_postventa` al
# reemplazar, anotar el tipo de evento, contar los commits y un periodo
# CERRADO) se amplía aquí con subclases.
USUARIO = "pablo@ruesma.es"


def _lnv(obra_ide: int, pct: str, pv: bool = False) -> Linea:
    """Línea del doble con su modo (el `_ln` de F-024 es siempre normal)."""
    o = OBRAS[obra_ide]
    return dataclasses.replace(_ln(obra_ide, pct), es_postventa=pv,
                               obra_admite_postventa=o.admite_postventa)


class _AsignacionesConModo(_Asignaciones):
    """Como el de F-024, pero conserva `es_postventa` (aquel usa `_ln`)."""

    def reemplazar(self, periodo_id: int, ide: int, lineas: list[Linea],
                   usuario: str) -> None:
        self._uow.lineas.setdefault(periodo_id, {})[ide] = [
            _lnv(ln.obra_ide, str(ln.porcentaje), ln.es_postventa)
            for ln in lineas]
        self._uow.reemplazados.append(ide)


class _EventosConTipo(_Eventos):
    """Como el de F-024, pero anota tipo, autor y snapshots de cada uno."""

    def __init__(self) -> None:
        super().__init__()
        self.registros: list[tuple] = []

    def registrar(self, periodo_id, ide, tipo, usuario, antes, despues):
        self.registros.append((periodo_id, ide, tipo, usuario, antes, despues))
        super().registrar(periodo_id, ide, tipo, usuario, antes, despues)


class _PeriodosCerrados(_Periodos):
    def obtener(self, anio: int, mes: int) -> tuple[int, Periodo] | None:
        encontrado = super().obtener(anio, mes)
        if encontrado is None:
            return None
        return encontrado[0], Periodo(anio, mes, EstadoPeriodo.CERRADO)


class _UowF029(_Uow):
    def __init__(self, lineas: dict[int, dict[int, list[Linea]]]) -> None:
        super().__init__(lineas)
        self.asignaciones = _AsignacionesConModo(self)
        self.eventos = _EventosConTipo()
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


def _uow29(**cambios: list[Linea]) -> _UowF029:
    """Periodo en curso de F-024 con las filas cambiadas que se pidan
    (clave `t<ide>`)."""
    lineas = _lineas_actuales()
    for clave, valor in cambios.items():
        lineas[int(clave[1:])] = valor
    return _UowF029({P_ACT: lineas})


F1 = FiltroEmpresa(empresa=1, por_defecto=1, empresa_obras=1)


def _completar(uow, trabajadores, obra_ide, pv=False, usuario=USUARIO,
               anio=ANIO, mes=MES):
    return CompletarHasta100().ejecutar(uow, anio, mes, trabajadores,
                                        obra_ide, pv, usuario, filtro=F1)


def _r(ide, resultado, anadido="0"):
    return ResultadoCompletarTrabajador(ide, ResultadoCompletado[resultado],
                                        Decimal(anadido))


def _claves(lineas: list[Linea]) -> list[tuple[int, bool, Decimal]]:
    return [(ln.obra_ide, ln.es_postventa, ln.porcentaje) for ln in lineas]


@pytest.fixture
def obras_pv(monkeypatch):
    """Obras de la 1 que admiten postventa: 103 (activa) y 104 (cerrada:
    solo `Postv-`)."""
    for obra in (Obra(103, "0103", "OBRA 103", None, activa=True, empresa=1,
                      admite_postventa=True),
                 Obra(104, "0104", "OBRA 104", None, activa=False, empresa=1,
                      admite_postventa=True)):
        monkeypatch.setitem(OBRAS, obra.ide, obra)


# ------------------------------ R15 / R16 ------------------------------ #
def test_f029_r15_caso_falta_suma_a_la_linea_existente():
    uow = _uow29(t14=[_ln(100, "30"), _ln(900, "20.50")])
    resultados, _ = _completar(uow, [14], 100)
    assert resultados == [_r(14, "COMPLETADO", "49.50")]
    assert _claves(uow.lineas[P_ACT][14]) == [
        (100, False, Decimal("79.50")), (900, False, Decimal("20.50"))]


def test_f029_r15_caso_sin_linea_crea_una_y_las_demas_no_cambian():
    uow = _uow29(t14=[_ln(100, "30"), _ln(900, "20.50")])
    resultados, _ = _completar(uow, [14], 101)
    assert resultados == [_r(14, "COMPLETADO", "49.50")]
    assert _claves(uow.lineas[P_ACT][14]) == [
        (100, False, Decimal("30")), (900, False, Decimal("20.50")),
        (101, False, Decimal("49.50"))]


def test_f029_r15_caso_sin_carga_queda_al_100_en_el_destino():
    """Eva (14, de la 1, sin carga) → 100 en la 101."""
    uow = _uow29()
    resultados, _ = _completar(uow, [14], 101)
    assert resultados == [_r(14, "COMPLETADO", "100.00")]
    assert _claves(uow.lineas[P_ACT][14]) == [(101, False, Decimal("100.00"))]


def test_f029_r16_caso_total_100_y_estado_ok_en_el_cuadrante():
    uow = _uow29(t14=[_ln(100, "33.33"), _ln(900, "33.33")])
    _completar(uow, [14], 101)
    cuadrante = ObtenerCuadrante().ejecutar(uow, ANIO, MES, F1,
                                            usuario=USUARIO)
    [eva] = [f for f in cuadrante.filas if f.trabajador.ide == 14]
    assert eva.total == Decimal("100.00")
    assert calcular_estado(eva.total, len(eva.lineas)) is EstadoTrabajador.OK


# --------------------------------- R17 --------------------------------- #
def test_f029_r17_caso_ok_y_exceso_no_se_tocan_ni_dejan_evento():
    """Ana (10, 60 + 40) sale YA_AL_100; con 60 + 50, EXCESO."""
    uow = _uow29()
    resultados, _ = _completar(uow, [10], 101)
    assert resultados == [_r(10, "YA_AL_100")]
    assert uow.reemplazados == [] and uow.eventos.registros == []
    uow = _uow29(t10=[_ln(100, "60"), _ln(900, "50")])
    resultados, _ = _completar(uow, [10], 101)
    assert resultados == [_r(10, "EXCESO")]
    assert uow.reemplazados == [] and uow.eventos.registros == []
    assert _claves(uow.lineas[P_ACT][10]) == [
        (100, False, Decimal("60")), (900, False, Decimal("50"))]


# --------------------------------- R18 --------------------------------- #
def test_f029_r18_caso_postv_no_suma_a_la_normal(obras_pv):
    uow = _uow29(t14=[_lnv(103, "40")])
    resultados, _ = _completar(uow, [14], 103, pv=True)
    assert resultados == [_r(14, "COMPLETADO", "60")]
    assert _claves(uow.lineas[P_ACT][14]) == [
        (103, False, Decimal("40")), (103, True, Decimal("60"))]


def test_f029_r18_caso_normal_no_suma_a_la_postv(obras_pv):
    uow = _uow29(t14=[_lnv(103, "40", pv=True)])
    _completar(uow, [14], 103, pv=False)
    assert _claves(uow.lineas[P_ACT][14]) == [
        (103, True, Decimal("40")), (103, False, Decimal("60"))]


def test_f029_r18_caso_postv_suma_a_la_postv(obras_pv):
    uow = _uow29(t14=[_lnv(103, "40"), _lnv(103, "10", pv=True)])
    _completar(uow, [14], 103, pv=True)
    assert _claves(uow.lineas[P_ACT][14]) == [
        (103, False, Decimal("40")), (103, True, Decimal("60"))]


# --------------------------------- R19 --------------------------------- #
def test_f029_r19_caso_un_evento_completar_por_trabajador_cambiado():
    uow = _uow29(t14=[_ln(100, "30")])
    _completar(uow, [14, 10, 11], 101)
    [(periodo, ide, tipo, usuario, antes, despues)] = uow.eventos.registros
    assert (periodo, ide, tipo, usuario) == (
        P_ACT, 14, TipoEvento.COMPLETAR, USUARIO)
    assert antes == _snapshot([_ln(100, "30")])
    assert despues == [
        {"obra_ide": 100, "es_postventa": False, "porcentaje": "30"},
        {"obra_ide": 101, "es_postventa": False, "porcentaje": "70.00"}]


def test_f029_r19_caso_deshacer_lo_devuelve_solo_para_quien_lanzo_el_lote():
    uow = _uow29(t14=[_ln(100, "30")])
    _completar(uow, [14], 101)

    def puede(usuario):
        cuadrante = ObtenerCuadrante().ejecutar(uow, ANIO, MES, F1,
                                                usuario=usuario)
        return {f.trabajador.ide: f.puede_deshacer for f in cuadrante.filas}

    assert puede(USUARIO)[14] is True
    assert puede("ana@ruesma.es")[14] is False
    with pytest.raises(DeshacerAjeno):
        DeshacerUltimaModificacion().ejecutar(uow, ANIO, MES, 14,
                                              "ana@ruesma.es", filtro=F1)
    fila, _ = DeshacerUltimaModificacion().ejecutar(uow, ANIO, MES, 14,
                                                    USUARIO, filtro=F1)
    assert _claves(fila.lineas) == [(100, False, Decimal("30"))]


# ------------------------------ R20 / R22 ------------------------------ #
@pytest.mark.parametrize("obra, pv, motivo", [
    (102, False, "no se ofrece como normal"),      # inactiva
    (101, True, "no se ofrece como Postv-"),       # no admite postventa
    (104, False, "no se ofrece como normal"),      # cerrada, solo Postv-
    (900, False, "no existe o no es de la empresa de las obras"),  # de la 28
    (999, False, "no existe o no es de la empresa de las obras"),
])
def test_f029_r22_caso_obra_no_valida_422_sin_tocar_a_nadie(obras_pv, obra,
                                                            pv, motivo):
    uow = _uow29(t14=[_ln(100, "30")])
    with pytest.raises(ObraNoValida, match=motivo):
        _completar(uow, [14, 10], obra, pv=pv)
    assert uow.reemplazados == [] and uow.eventos.registros == []
    assert uow.commits == 0


def test_f029_r22_caso_postv_de_obra_cerrada_que_la_admite(obras_pv):
    uow = _uow29()
    resultados, _ = _completar(uow, [14], 104, pv=True)
    assert resultados == [_r(14, "COMPLETADO", "100.00")]


# --------------------------------- R21 --------------------------------- #
def test_f029_r21_caso_periodo_inexistente_o_cerrado():
    uow = _uow29(t14=[_ln(100, "30")])
    with pytest.raises(PeriodoNoEncontrado):
        _completar(uow, [14], 101, mes=MES + 1)
    uow.periodos = _PeriodosCerrados()
    with pytest.raises(PeriodoCerrado):
        _completar(uow, [14], 101)
    assert uow.reemplazados == [] and uow.eventos.registros == []
    assert uow.commits == 0


# ---------------------------- R14 / R23 / R24 -------------------------- #
def test_f029_r23_r24_caso_no_visible_y_no_vigente_no_paran_el_lote():
    """Bea (11, de la 28), Fran (15, de la 18) y 999 (no existe): no
    visibles en E = 1. Carlos (12) y Dani (13), en FALTA pero no vigentes:
    no se tocan. Eva (14) sí."""
    uow = _uow29()
    resultados, _ = _completar(uow, [11, 12, 999, 13, 15, 14], 101)
    assert resultados == [
        _r(11, "NO_VISIBLE"), _r(12, "NO_VIGENTE"), _r(999, "NO_VISIBLE"),
        _r(13, "NO_VIGENTE"), _r(15, "NO_VISIBLE"),
        _r(14, "COMPLETADO", "100.00")]
    assert uow.reemplazados == [14]
    assert _claves(uow.lineas[P_ACT][12]) == [(900, False, Decimal("50"))]


def test_f029_r14_caso_repetidos_una_vez_en_orden_de_llegada():
    uow = _uow29()
    resultados, _ = _completar(uow, [14, 11, 14, 10, 11], 101)
    assert [r.trabajador_ide for r in resultados] == [14, 11, 10]
    assert uow.reemplazados == [14]
    assert len(uow.eventos.registros) == 1


# --------------------------------- R25 --------------------------------- #
def test_f029_r25_caso_resumen_despues_del_lote_y_un_solo_commit():
    """Antes: 5 visibles, 2 OK, 2 FALTA, 1 sin carga (Eva). Después de
    completar a Eva: 3 OK y ninguno sin carga."""
    uow = _uow29()
    _, resumen = _completar(uow, [14, 10], 101)
    assert resumen == ResumenPeriodo(total=5, ok=3, falta=2, exceso=0,
                                     sin_carga=0)
    assert uow.commits == 1


# ================================ ruta (T3) ============================= #
COMPLETAR = f"{BASE}/completar"


def test_f029_r25_ruta_200_con_resultados_y_resumen(api):
    """Eva (14) sin carga → 100 en la 101; Bea (11) no visible en la 1; Ana
    (10) ya al 100 %. El resumen es el de E después del lote."""
    cliente, contenedor = api
    r = cliente.post(COMPLETAR, json={"trabajadores": [14, 11, 10, 14],
                                      "obra_ide": 101},
                     headers={"X-Usuario": USUARIO})
    assert r.status_code == 200, r.text
    assert r.json() == {
        "resultados": [
            {"trabajador_ide": 14, "resultado": "COMPLETADO", "anadido": 100.0},
            {"trabajador_ide": 11, "resultado": "NO_VISIBLE", "anadido": 0.0},
            {"trabajador_ide": 10, "resultado": "YA_AL_100", "anadido": 0.0},
        ],
        "resumen": {"total": 5, "ok": 3, "falta": 2, "exceso": 0,
                    "sin_carga": 0},
    }
    [uow] = contenedor.uows
    assert uow.reemplazados == [14]
    # R19 · el evento lleva el usuario de `X-Usuario`: solo él lo deshace.
    assert uow.eventos.ultimo_pendiente(P_ACT, 14).usuario == USUARIO
    # R26 · ni transfer ni Sigrid.
    assert contenedor.registro_sigrid.llamadas == []


def test_f029_r14_ruta_empresa_por_query_como_el_resto(api):
    """Con E = 28 Eva no es visible y Bea (100 en la 900) ya está al 100."""
    cliente, contenedor = api
    r = cliente.post(COMPLETAR, params={"empresa": 28},
                     json={"trabajadores": [14, 11], "obra_ide": 101})
    assert r.status_code == 200, r.text
    assert [x["resultado"] for x in r.json()["resultados"]] == [
        "NO_VISIBLE", "YA_AL_100"]
    assert r.json()["resumen"]["total"] == 1
    assert contenedor.uows[0].reemplazados == []


@pytest.mark.parametrize("params, cuerpo", [
    ({"empresa": "0"}, {"trabajadores": [14], "obra_ide": 101}),
    ({"empresa": "abc"}, {"trabajadores": [14], "obra_ide": 101}),
    ({}, {"trabajadores": [], "obra_ide": 101}),
    ({}, {"trabajadores": list(range(1, 502)), "obra_ide": 101}),
    ({}, {"trabajadores": [14], "obra_ide": 101, "porcentaje": 50}),
    ({}, {"trabajadores": [14]}),
    ({}, {"trabajadores": [14], "obra_ide": 101, "es_postventa": "quizá"}),
], ids=["empresa-0", "empresa-texto", "lista-vacia", "501-ides",
        "campo-extra", "sin-obra", "postventa-no-booleano"])
def test_f029_r14_ruta_422_sin_abrir_uow(api, params, cuerpo):
    cliente, contenedor = api
    r = cliente.post(COMPLETAR, params=params, json=cuerpo)
    assert r.status_code == 422, r.text
    assert contenedor.uows == []


def test_f029_r14_ruta_admite_500_ides():
    """El tope es 500 incluido (R14)."""
    from interface_adapters.api.schemas import CompletarIn

    entrada = CompletarIn(trabajadores=list(range(1, 501)), obra_ide=101)
    assert len(entrada.trabajadores) == 500
    assert entrada.es_postventa is False


@pytest.mark.parametrize("obra, pv, motivo", [
    (102, False, "no se ofrece como normal"),
    (101, True, "no se ofrece como Postv-"),
    (900, False, "no existe o no es de la empresa de las obras"),
    (999, False, "no existe o no es de la empresa de las obras"),
])
def test_f029_r22_ruta_obra_no_valida_422_con_motivo(api, obra, pv, motivo):
    cliente, contenedor = api
    r = cliente.post(COMPLETAR, json={"trabajadores": [14], "obra_ide": obra,
                                      "es_postventa": pv})
    assert r.status_code == 422, r.text
    assert motivo in r.json()["error"]
    assert contenedor.uows[0].reemplazados == []


def test_f029_r21_ruta_periodo_inexistente_404(api):
    cliente, contenedor = api
    r = cliente.post(f"/api/v1/periodos/{ANIO}/{MES + 1}/completar",
                     json={"trabajadores": [14], "obra_ide": 101})
    assert r.status_code == 404, r.text
    assert contenedor.uows[0].reemplazados == []
