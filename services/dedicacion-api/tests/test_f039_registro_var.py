# tests/test_f039_registro_var.py
"""Tests offline de F-039 en la api: registro, `ofrecible` y cuadrante de las
entradas VAR (R19-R21).

La regla es `docs/ARCHITECTURE.md#regla-var`. Una entrada `VAR-NN` es una
fila de `obra` como cualquier otra para el cuadrante, Completar, las copias
y el Excel; solo el registro la trata aparte: sus líneas viajan en la
petición de la obra VAR, con `var_paride` y sin `paride` manual.

Sesión y transfer falsos de `test_f022_empresa_en_linea.py`; UoW en memoria
de `test_f024_cuadrante_empresa.py` (Completar, F-029). Ni red ni BBDD.
"""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest
from application.registro_sigrid import RegistroSigrid
from domain.models import Linea, Obra

from tests.test_f022_empresa_en_linea import _Sesion, _Transfer

VAR_IDE = 683806


def _obra(ide: int, cod: str, descripcion: str = "OBRA", *,
          registro: tuple | None = None) -> SimpleNamespace:
    """Obra como la devuelve la consulta; `registro` = (obra_ide, obra_cod,
    paride) de una entrada VAR, o nada en una obra normal."""
    ide_r, cod_r, paride_r = registro or (None, None, None)
    return SimpleNamespace(ide=ide, cod=cod, descripcion=descripcion,
                           empresa=1, registro_obra_ide=ide_r,
                           registro_obra_cod=cod_r, registro_paride=paride_r)


VAR = _obra(VAR_IDE, "VAR", "OBRAS VARIAS")
VAR_29 = _obra(-417055, "VAR-29", "NAVE", registro=(VAR_IDE, "VAR", 417055))
VAR_30 = _obra(-417057, "VAR-30", "OTRA", registro=(VAR_IDE, "VAR", 417057))
O678 = _obra(678, "0678", "15 VIVIENDAS")


def _fila(asig_id: int, trab_ide: int, obra: SimpleNamespace,
          pv: bool = False) -> tuple:
    asignacion = SimpleNamespace(id=asig_id, porcentaje=40, es_postventa=pv)
    trabajador = SimpleNamespace(ide=trab_ide, dni=None, nombre=f"T{trab_ide}",
                                 categoria="Encargado", empresa=1,
                                 activo=True, fecha_baja=None)
    return asignacion, trabajador, obra


def _payloads(filas: list[tuple], fase: str = "preflight",
              overrides: dict | None = None) -> list[dict]:
    transfer = _Transfer()
    registro = RegistroSigrid(lambda: _Sesion(filas), transfer, 1)
    if fase == "preflight":
        registro.preflight(2026, 8, overrides=overrides)
    else:
        registro.ejecutar(2026, 8, pisar_claves=[], overrides=overrides)
    return transfer.payloads


# --- R20 · el registro agrupa por la obra de registro -------------------------


@pytest.mark.parametrize("fase", ["preflight", "ejecutar"])
def test_f039_r20_las_entradas_van_en_la_peticion_de_la_obra_var(fase):
    """R20 · Las líneas de `VAR-29` y `VAR-30` van en UNA petición, la de la
    obra VAR (su `ide` y código de registro, sin nombre), con `var_paride`;
    la obra normal, en la suya y como hoy."""
    payloads = _payloads([_fila(1, 10, VAR_29), _fila(2, 11, VAR_30),
                          _fila(3, 10, O678)], fase)
    assert [p["obra"] for p in payloads] == [
        {"ide": VAR_IDE, "codigo": "VAR", "nombre": None},
        {"ide": 678, "codigo": "0678", "nombre": "15 VIVIENDAS"}]
    var, normal = payloads
    assert [(ln["registro_id"], ln["var_paride"]) for ln in var["lineas"]] \
        == [(1, 417055), (2, 417057)]
    assert "var_paride" not in normal["lineas"][0]


def test_f039_r20_junto_a_las_lineas_de_la_propia_obra_var():
    """R19-R20 · Una línea ya guardada en la obra VAR (no ofrecible desde
    D1) se manda como hoy, en la MISMA petición que las entradas."""
    payloads = _payloads([_fila(1, 10, VAR), _fila(2, 10, VAR_29)])
    assert len(payloads) == 1
    assert payloads[0]["obra"]["ide"] == VAR_IDE
    lineas = payloads[0]["lineas"]
    assert [ln["registro_id"] for ln in lineas] == [1, 2]
    assert "var_paride" not in lineas[0] and lineas[1]["var_paride"] == 417055


def test_f039_r20_el_override_manual_no_viaja_en_la_entrada():
    """R20 · Una entrada nunca lleva `paride` manual; la obra normal, sí."""
    payloads = _payloads([_fila(1, 10, VAR_29), _fila(2, 10, O678)],
                         overrides={1: 60001, 2: 80002})
    entrada, normal = payloads[0]["lineas"][0], payloads[1]["lineas"][0]
    assert "paride" not in entrada and entrada["var_paride"] == 417055
    assert normal["paride"] == 80002 and "var_paride" not in normal


def test_f039_r20_la_entrada_lleva_lo_mismo_que_una_linea_normal():
    """R20 · Fuera de `var_paride`, la línea de la entrada es la de siempre
    (recurso, porcentaje sobre 1, empresa de las obras, postventa)."""
    linea = _payloads([_fila(1, 10, VAR_29)])[0]["lineas"][0]
    assert linea == {"registro_id": 1, "ano": 2026, "mes": 8,
                     "porcentaje": 0.4, "recurso_ide": 10, "dni": None,
                     "nombre": "T10", "categoria": "Encargado",
                     "es_postventa": False, "empresa": 1,
                     "var_paride": 417055}


# --- R19 · lo ya guardado se queda, marcado ----------------------------------


def test_f039_r19_la_linea_de_una_entrada_retirada_no_es_ofrecible():
    """R15, R19 · La entrada que sale del universo (`activa = false`) o la
    obra VAR (D1) dejan sus líneas como no ofrecibles; una entrada viva,
    ofrecible como obra normal y nunca como postventa (R21)."""
    def ln(activa: bool, pv: bool = False) -> Linea:
        return Linea(obra_ide=-417055, es_postventa=pv, porcentaje=Decimal(40),
                     cod="VAR-29", obra_activa=activa,
                     obra_admite_postventa=False)

    assert ln(False).ofrecible is False
    assert ln(True).ofrecible is True
    assert ln(True, pv=True).ofrecible is False


def test_f039_r19_el_registro_manda_la_entrada_retirada_como_hoy():
    """R19 · La consulta del registro no mira `activa`: la línea guardada en
    una entrada retirada se manda igual, con su `var_paride` (el transfer
    decide si está en el universo, R6)."""
    retirada = _obra(-417056, "VAR-29.1", registro=(VAR_IDE, "VAR", 417056))
    retirada.activa = False
    payloads = _payloads([_fila(1, 10, retirada)])
    assert payloads[0]["lineas"][0]["var_paride"] == 417056


# --- R21 · como cualquier obra en el cuadrante, Completar y Excel -------------


ENTRADA = Obra(-417055, "VAR-29", "ACOND. NAVE MODUL-A", None, activa=True,
               empresa=1, admite_postventa=False)


@pytest.fixture
def con_entrada(monkeypatch):
    """La entrada `VAR-29` en las obras de la UoW en memoria de F-024."""
    from tests.test_f024_cuadrante_empresa import OBRAS

    monkeypatch.setitem(OBRAS, ENTRADA.ide, ENTRADA)


def test_f039_r21_completar_hacia_la_entrada(con_entrada):
    """R21 · Completar al 100 % hacia `VAR-29` como hacia cualquier obra."""
    from tests.test_f024_cuadrante_empresa import P_ACT, _ln
    from tests.test_f029_completar import _completar, _r, _uow29

    uow = _uow29(t14=[_ln(100, "30")])
    resultados, _ = _completar(uow, [14], ENTRADA.ide)
    assert resultados == [_r(14, "COMPLETADO", "70.00")]
    assert [(ln.obra_ide, ln.porcentaje) for ln in uow.lineas[P_ACT][14]] == [
        (100, Decimal(30)), (ENTRADA.ide, Decimal("70.00"))]


def test_f039_r21_completar_en_postventa_hacia_la_entrada_no_vale(con_entrada):
    """R21 · Sin modo postventa: Completar en `Postv-` hacia la entrada se
    rechaza como en cualquier obra que no admite postventa."""
    from domain.errors import ObraNoValida

    from tests.test_f029_completar import _completar, _uow29

    with pytest.raises(ObraNoValida):
        _completar(_uow29(), [14], ENTRADA.ide, pv=True)


def test_f039_r21_el_excel_lleva_el_codigo_de_la_entrada():
    """R21 · El export a Excel saca `VAR-29` y su descripción como una obra
    normal (sin prefijo de postventa)."""
    import io

    from domain.models import CuadranteTrabajador, Periodo, Trabajador
    from infrastructure.excel.exporter import OpenpyxlExcelExporter
    from openpyxl import load_workbook

    fila = CuadranteTrabajador(
        trabajador=Trabajador(ide=10, cod="10", nombre="Ana", dni=None,
                              categoria="Encargado"),
        lineas=[Linea(obra_ide=ENTRADA.ide, es_postventa=False,
                      porcentaje=Decimal("45.5"), cod=ENTRADA.cod,
                      descripcion=ENTRADA.descripcion)])
    libro = load_workbook(io.BytesIO(OpenpyxlExcelExporter("Postv-").exportar(
        Periodo(anio=2026, mes=8), [fila])))
    # Formato de F-040: datos desde la fila 3, sin la columna «Obra(código)»;
    # Código en C, Obra en D y % en E. Una sola línea: nada combinado.
    detalle = [c.value for c in libro["Obras"][3]]
    assert detalle[2:5] == ["VAR-29", "ACOND. NAVE MODUL-A", 0.455]
    assert libro["Resumen"]["C3"].value == "VAR-29 ACOND. NAVE MODUL-A = 45,50%"
