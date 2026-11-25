# tests/test_f080_caja_api.py
"""F-080 · la caja de obra, una por trabajador y repartida con su %, como
los km (R1, R2, R4, R5, R11, R12; design §2, §6).

- R1: `config.yaml` declara `CAJA: {unidad: eur, reparto: pct}`; `VIAJE` y
  `VP`, como antes; el reparto `obra` sigue siendo válido (D1 a).
- R2: con los tipos de la config, el cuadrante saca la caja UNA vez por
  trabajador en `importes` y cada subfila de caja con `reparto: pct`, sin
  `cantidad` de subfila (aunque la subfila guarde un resto por obra).
- R4: `PUT …/importes` guarda la caja como caja del mes aunque traiga
  `obra_ide`; dos elementos de la misma caja, 422 «repetido».
- R5: al registrar, cada línea lleva su caja con `reparto: pct`, la
  cantidad del mes (`null` si falta), su `copiado` y el comentario del mes,
  en la misma lectura de las cantidades del mes (F-069 R16).

Los dobles son los de F-069 (`test_f069_importes_api.py`); los tipos, los
de la config versionada. Sin red ni BBDD.
"""
from __future__ import annotations

import dataclasses
from decimal import Decimal
from pathlib import Path

import pytest
from application.sync_pipeline import ConfigVinculados
from application.use_cases import (
    CopiarPeriodoAnterior,
    CopiarTrabajadorAnterior,
    GuardarImportes,
    ObtenerCuadrante,
    _sin_propuesta,
)
from config.settings import cargar_config
from domain.errors import ImporteInvalido
from domain.importes import TipoCantidad, tipos_de_config
from domain.models import ImporteMes, Linea, SubfilaVinculado
from interface_adapters.api.schemas import a_trabajador_out

from tests.test_f024_cuadrante_empresa import ANIO, DEF, MES, P_ACT, P_ANT, _ln
from tests.test_f024_rutas_empresa import (
    BASE,
    api,  # noqa: F401  (fixture)
)
from tests.test_f051_hmores_ide import _fila
from tests.test_f069_importes_api import (
    CAJA,
    FILTRO,
    TEL,
    TIPOS,
    VP,
    _LeerImportes,
    _payload,
    _subfila,
    _uow_copia,
    _uow_imp,
)

#: Los tipos de cantidad de la config versionada (los que usa la api).
TIPOS_CFG = ConfigVinculados.desde_config(
    cargar_config()["sync"]["vinculados"]).importes


# ================================ R1 ===================================== #
def test_f080_r1_config_caja_en_euros_por_pct():
    assert TIPOS_CFG == {"CAJA": TipoCantidad("eur", "pct"),
                         "VIAJE": TipoCantidad("eur", "pct"),
                         "VP": TipoCantidad("km", "pct")}


def test_f080_r1_el_reparto_obra_sigue_siendo_valido():
    """D1 a: el mecanismo de F-069 se queda, sin tipo que lo use."""
    assert tipos_de_config({"X": {"unidad": "eur", "reparto": "obra"}}) == {
        "X": TipoCantidad("eur", "obra")}


# ================================ R2 ===================================== #
def _cuadrante_ana(uow) -> dict:
    cuadrante = ObtenerCuadrante().ejecutar(uow, ANIO, MES, FILTRO,
                                            usuario="pgris")
    [ana] = [f for f in cuadrante.filas if f.trabajador.ide == 10]
    return a_trabajador_out(ana, DEF, tipos=TIPOS_CFG).model_dump(
        mode="json")


def test_f080_r2_la_caja_una_vez_por_trabajador_en_importes():
    resto = dataclasses.replace(CAJA, cantidad=Decimal("80.00"),
                                copiado=True, comentario="resto")
    uow = _uow_imp(VP, resto, TEL)
    uow.importes.filas[30] = ImporteMes(vinculado_ide=30,
                                        cantidad=Decimal("300.00"),
                                        comentario="caja de noviembre")
    t = _cuadrante_ana(uow)
    assert [i for i in t["importes"] if i["vinculado_ide"] == 30] == [{
        "vinculado_ide": 30, "tipo": "CAJA", "cod": "CJ-30", "unidad": "eur",
        "cantidad": 300.0, "copiado": False,
        "comentario": "caja de noviembre"}]
    assert [i["vinculado_ide"] for i in t["importes"]] == [20, 30]
    for ln in t["lineas"]:
        caja = next(v for v in ln["vinculados"] if v["vinculado_ide"] == 30)
        assert (caja["reparto"], caja["unidad"]) == ("pct", "eur")
        # Ni la cantidad, ni el copiado ni el comentario del resto por obra.
        assert not {"cantidad", "copiado", "comentario"} & set(caja)


def test_f080_r2_sin_caja_del_mes_sale_la_casilla_vacia():
    t = _cuadrante_ana(_uow_imp(CAJA))
    assert t["importes"] == [{
        "vinculado_ide": 30, "tipo": "CAJA", "cod": "CJ-30", "unidad": "eur",
        "cantidad": None, "copiado": False, "comentario": None}]


# ================================ R4 ===================================== #
def _guardar(uow, *importes):
    return GuardarImportes(TIPOS_CFG).ejecutar(
        uow, ANIO, MES, 10, list(importes), "pgris", filtro=FILTRO)


@pytest.mark.parametrize("elemento", [
    {"vinculado_ide": 30, "cantidad": "300"},
    {"vinculado_ide": 30, "obra_ide": 100, "cantidad": "300"},  # editor viejo
])
def test_f080_r4_la_caja_se_guarda_como_caja_del_mes(elemento):
    uow = _uow_imp(VP, CAJA)
    _guardar(uow, elemento)
    assert uow.importes.filas[30] == ImporteMes(
        vinculado_ide=30, cantidad=Decimal("300.00"), copiado=False)
    assert _subfila(uow, 100).cantidad is None
    assert _subfila(uow, 900).cantidad is None
    assert uow.asignaciones.sueltas == []
    [(tipo, _, despues)] = uow.eventos.registrados
    assert tipo == "IMPORTES"
    assert despues == [{"vinculado_ide": 30, "obra_ide": None,
                        "es_postventa": False, "cantidad": "300.00",
                        "copiado": False, "comentario": None}]


def test_f080_r4_dos_de_la_misma_caja_es_422_repetido():
    uow = _uow_imp(VP, CAJA)
    with pytest.raises(ImporteInvalido, match="repetido"):
        _guardar(uow, {"vinculado_ide": 30, "obra_ide": 100, "cantidad": 1},
                 {"vinculado_ide": 30, "obra_ide": 900, "cantidad": 2})
    assert uow.importes.escrituras == [] and uow.eventos.registrados == []


# ================================ R5 ===================================== #
def _caja_del_payload(ln: dict) -> dict:
    return next(v for v in ln["vinculados"] if v["recurso_ide"] == 30)


def test_f080_r5_cada_linea_lleva_la_caja_del_mes_por_pct():
    resto = dataclasses.replace(CAJA, cantidad=Decimal("80.00"),
                                copiado=True, comentario="resto")
    leer = _LeerImportes({30: ImporteMes(
        vinculado_ide=30, cantidad=Decimal("300.00"), comentario="caja")})
    lineas, leer = _payload([_fila(1), _fila(2)],
                            {1: (VP, resto), 2: (CAJA,)},
                            tipos=TIPOS_CFG, leer=leer)
    for ln in lineas:
        caja = _caja_del_payload(ln)
        assert (caja["importe_mensual"], caja["unidad"], caja["reparto"],
                caja["cantidad"], caja["copiado"], caja["comentario"]) == (
            True, "eur", "pct", 300.0, False, "caja")
        assert "precio_km" not in caja
    # Una sola lectura de las del mes, con la caja dentro (la lista lleva un
    # vinculado por subfila; la consulta los deduplica, F-069 R16).
    [(anio, mes, vinculados)] = leer.llamadas
    assert (anio, mes, set(vinculados)) == (2026, 10, {20, 30})


def test_f080_r5_sin_caja_del_mes_va_nula_y_copiada_con_su_marca():
    [ln], _ = _payload([_fila(1)], {1: (CAJA,)}, tipos=TIPOS_CFG)
    caja = _caja_del_payload(ln)
    assert (caja["reparto"], caja["cantidad"], caja["copiado"],
            caja["comentario"]) == ("pct", None, False, None)
    leer = _LeerImportes({30: ImporteMes(
        vinculado_ide=30, cantidad=Decimal("250.00"), copiado=True)})
    [ln], _ = _payload([_fila(1)], {1: (CAJA,)}, tipos=TIPOS_CFG, leer=leer)
    caja = _caja_del_payload(ln)
    assert (caja["cantidad"], caja["copiado"]) == (250.0, True)


# ================================ R11 ==================================== #
#: Un resto por obra de la caja (por % tras F-080) con su partida elegida, un
#: vinculado que no es de cantidad con comentario y el km sin nada.
RESTO = dataclasses.replace(CAJA, cantidad=Decimal("80.00"), copiado=False,
                            comentario="resto", partida_ide=81001,
                            partida_cod="CICA10", partida_res="CAJA")
TEL_C = dataclasses.replace(TEL, comentario="del móvil", partida_ide=81002,
                            partida_cod="CITF13", partida_res="TELEFONO")


def _copiar(uow, copiar: str, tipos):
    if copiar == "trabajador":
        return CopiarTrabajadorAnterior(tipos).ejecutar(
            uow, ANIO, MES, 10, "pgris", filtro=FILTRO)
    return CopiarPeriodoAnterior(tipos).ejecutar(uow, ANIO, MES, "pgris",
                                                 filtro=FILTRO)


def _uow_resto():
    uow = _uow_copia(origen_mes={30: ImporteMes(
        vinculado_ide=30, cantidad=Decimal("300.00"), comentario="caja")})
    uow.lineas[P_ANT][10] = [
        dataclasses.replace(_ln(100, "60"), vinculados=(VP, RESTO, TEL_C)),
        dataclasses.replace(_ln(101, "40"), vinculados=(VP, CAJA, TEL))]
    return uow


@pytest.mark.parametrize("copiar", ["trabajador", "periodo"])
def test_f080_r11_el_resto_por_obra_de_un_tipo_por_pct_no_se_copia(copiar):
    uow = _uow_resto()
    _copiar(uow, copiar, TIPOS_CFG)
    caja = _subfila(uow, 100)
    assert (caja.cantidad, caja.copiado, caja.comentario) == (None, None,
                                                               None)
    # La partida elegida de la subfila, como hoy (F-050 R16).
    assert (caja.partida_ide, caja.partida_cod, caja.partida_res) == (
        81001, "CICA10", "CAJA")
    # El vinculado que no es de cantidad, como hoy: su comentario se copia.
    tel = _subfila(uow, 100, vid=10)
    assert (tel.comentario, tel.partida_ide) == ("del móvil", 81002)
    # La caja del mes sí se copia, sin revisar (F-069 R8).
    assert uow.importes.filas[P_ACT] == {30: ImporteMes(
        vinculado_ide=30, cantidad=Decimal("300.00"), copiado=True,
        comentario="caja")}


@pytest.mark.parametrize("copiar", ["trabajador", "periodo"])
def test_f080_r11_un_tipo_por_obra_y_sin_tipos_como_hoy(copiar):
    for tipos in (TIPOS, None):          # `TIPOS`: la caja por obra de F-069
        uow = _uow_resto()
        _copiar(uow, copiar, tipos)
        caja = _subfila(uow, 100)
        assert (caja.cantidad, caja.copiado, caja.comentario) == (
            Decimal("80.00"), True, "resto")


def test_f080_r11_sin_propuesta_por_tipo():
    ln = Linea(obra_ide=7, es_postventa=False, porcentaje=Decimal(100),
               propuesta_ide=5, propuesta_cod="CI.1", vinculados=(
                   dataclasses.replace(RESTO, propuesta_ide=9,
                                       propuesta_cod="CICA"),
                   dataclasses.replace(VP, cantidad=Decimal("1.00")),
                   SubfilaVinculado(vinculado_ide=40, tipo=" caja ",
                                    cantidad=Decimal("2.00"),
                                    comentario="x")))
    [out] = _sin_propuesta([ln], TIPOS_CFG)
    assert (out.propuesta_ide, out.propuesta_cod) == (None, None)
    for v in out.vinculados:
        assert (v.cantidad, v.copiado, v.comentario) == (None, None, None)
        assert (v.propuesta_ide, v.propuesta_cod) == (None, None)
    [hoy] = _sin_propuesta([ln])
    assert [(v.cantidad, v.copiado) for v in hoy.vinculados] == [
        (Decimal("80.00"), True), (Decimal("1.00"), True),
        (Decimal("2.00"), True)]


def _espia(monkeypatch, nombre: str) -> list:
    from interface_adapters.api import routes
    real = getattr(routes, nombre)
    vistos: list = []

    class _Espia(real):
        def __init__(self, tipos=None):
            vistos.append(tipos)
            super().__init__(tipos)

    monkeypatch.setattr(routes, nombre, _Espia)
    return vistos


@pytest.mark.parametrize("nombre, ruta", [
    ("CopiarPeriodoAnterior", "/copiar-anterior"),
    ("CopiarTrabajadorAnterior", "/trabajadores/14/copiar-anterior")])
def test_f080_r11_las_rutas_pasan_los_tipos_del_contenedor(
        api, monkeypatch, nombre, ruta):  # noqa: F811
    cliente, contenedor = api
    vistos = _espia(monkeypatch, nombre)
    assert cliente.post(f"{BASE}{ruta}").status_code == 200
    contenedor.importes = TIPOS_CFG
    assert cliente.post(f"{BASE}{ruta}").status_code == 200
    assert vistos == [{}, TIPOS_CFG]


# ================================ R12 ==================================== #
_RAIZ_REPO = Path(__file__).resolve().parents[3]


def _regla_vinculado() -> str:
    """El bloque «Cantidad y comentario» de `#regla-vinculado`, en una línea
    (sin los saltos ni la sangría del Markdown)."""
    texto = (_RAIZ_REPO / "docs/ARCHITECTURE.md").read_text(encoding="utf-8")
    inicio = texto.index("**Cantidad y comentario")
    fin = texto.index('<a id="regla-traer-sigrid">')
    return " ".join(texto[inicio:fin].split())


def test_f080_r12_la_doc_dice_caja_por_pct_y_sin_restos():
    doc = _regla_vinculado()
    assert "Hoy `CAJA` (€, `pct`), `VIAJE` (€, `pct`) y `VP` (km, `pct`)" in doc
    assert "`CAJA` (€, `obra`)" not in doc
    assert "**Hoy ningún tipo lo usa**" in doc
    assert "**no se copian** al mes nuevo (F-080 R11" in doc
    assert "**ni se pasan** a la cantidad del mes (D2" in doc
    assert "falta la caja del mes» con la obra" not in doc   # «Se omite»
    assert "*Decidido el 2026-11-25 (Pablo Gris): «la caja de obra se " \
           "comporte como los km" in doc
    assert "300 € de caja al 60 % y al 40 % ⇒ `tot` 180 y 120" in doc


def test_f080_r12_el_comentario_de_la_config_tambien():
    texto = (_RAIZ_REPO / "services/dedicacion-api/config/config.yaml"
             ).read_text(encoding="utf-8")
    comentario = " ".join(texto[texto.index("# `importes` (F-069"):
                                texto.index("# `precio_km`")].split())
    assert "la caja se asigna a la obra" not in comentario
    assert "Hoy ningún tipo es `obra`: la caja pasó a `pct` con F-080" in \
        comentario.replace("# ", "")
