# tests/test_f044_payload_traza.py
"""F-044 · T18: la api manda los vinculados al transfer y guarda su traza.

- R10: cada línea de un periodo ≥ `sync.vinculados.desde` lleva
  `vinculados` (recurso, tipo, descripción del tipo, código, partida elegida
  o propuesta guardada y `hmores_ide`) si su trabajador tiene alguno vigente
  en el mes. Antes de `desde`, sin vinculados o sin `desde` (el contenedor
  lo pasa de `config.yaml`): el payload de hoy, sin leer nada más.
- R30: al volver de `ejecutar`, por asignación y vinculado, estado, parte,
  motivo y `hmores.ide` en `asignacion_vinculado`; la entrada de `omitidas`
  de un vinculado (`vinculado_ide`) no toca la asignación del titular.

Sesiones y transfer falsos de `test_f022_empresa_en_linea.py`; las subfilas,
con un cargador falso. Ni red ni BBDD.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from application.registro_sigrid import RegistroSigrid
from domain.models import SubfilaVinculado

from tests.test_f022_empresa_en_linea import _Sesion, _Transfer
from tests.test_f051_hmores_ide import _fila, _SesionQueAnota


class _Cargador:
    """Las subfilas de cada asignación por su `id` (cada llamada, anotada
    con los `id` que pide y el mes)."""

    def __init__(self, por_id: dict[int, tuple]) -> None:
        self.por_id = por_id
        self.llamadas: list[tuple[list[int], tuple[int, int]]] = []

    def __call__(self, s, asignaciones, anio_mes):
        self.llamadas.append((sorted(a.id for a in asignaciones), anio_mes))
        return lambda a: self.por_id.get(a.id, ())


_TEL = SubfilaVinculado(vinculado_ide=10, tipo="TF", tipo_res="TELEFONO",
                        cod="TF-10")
_GAS = SubfilaVinculado(vinculado_ide=11, tipo="GA", tipo_res="GASOIL",
                        cod="GA-11", partida_ide=81002, partida_cod="CIGA14",
                        partida_res="GASOIL", sigrid_hmores_ide=5301)
_VEH = SubfilaVinculado(vinculado_ide=12, tipo="VE", tipo_res="VEHICULO",
                        cod="VE-12", propuesta_ide=81003,
                        propuesta_cod="CIVE15", propuesta_res="VEHICULOS",
                        propuesta_metodo="ci_tipo", propuesta_origen=None)


def _lineas(filas, *, desde=None, cargador=None, anio=2026, mes=10):
    transfer = _Transfer()
    kw = {} if desde is None else {"vinculados_desde": desde}
    if cargador is not None:
        kw["subfilas"] = cargador
    RegistroSigrid(lambda: _Sesion(filas), transfer, 1, **kw).ejecutar(
        anio, mes, pisar_claves=[])
    [payload] = transfer.payloads
    return payload["lineas"]


# ================================ R10 ==================================== #
def test_f044_r10_cada_linea_lleva_sus_vinculados():
    cargador = _Cargador({1: (_TEL, _GAS, _VEH)})
    [l] = _lineas([_fila(1)], desde=(2026, 10), cargador=cargador)
    assert l["vinculados"] == [
        {"recurso_ide": 10, "tipo": "TF", "tipo_res": "TELEFONO",
         "cod": "TF-10"},
        {"recurso_ide": 11, "tipo": "GA", "tipo_res": "GASOIL",
         "cod": "GA-11", "paride": 81002, "partida_cod": "CIGA14",
         "hmores_ide": 5301},
        {"recurso_ide": 12, "tipo": "VE", "tipo_res": "VEHICULO",
         "cod": "VE-12", "propuesta_paride": 81003,
         "propuesta_cod": "CIVE15", "propuesta_res": "VEHICULOS",
         "propuesta_metodo": "ci_tipo", "propuesta_origen": None}]
    assert cargador.llamadas == [([1], (2026, 10))]


def test_f044_r10_sin_vinculados_la_linea_de_hoy():
    hoy = _lineas([_fila(1), _fila(2)])
    con = _lineas([_fila(1), _fila(2)], desde=(2026, 10),
                  cargador=_Cargador({2: (_TEL,)}))
    assert con[0] == hoy[0] and "vinculados" not in con[0]
    assert {k: v for k, v in con[1].items() if k != "vinculados"} == hoy[1]


@pytest.mark.parametrize("desde", [None, (2026, 11), (2027, 1)])
def test_f044_r10_antes_de_desde_o_sin_desde_ni_se_leen(desde):
    cargador = _Cargador({1: (_TEL,)})
    [l] = _lineas([_fila(1)], desde=desde, cargador=cargador)
    assert "vinculados" not in l
    assert cargador.llamadas == []


def test_f044_r10_desde_es_el_primer_periodo_que_los_lleva():
    cargador = _Cargador({1: (_TEL,)})
    [l] = _lineas([_fila(1)], desde=(2025, 12), cargador=cargador,
                  anio=2026, mes=1)
    assert [v["recurso_ide"] for v in l["vinculados"]] == [10]


def test_f044_r10_un_no_vigente_ni_se_manda_ni_se_le_buscan():
    no_vigente = _fila(2)
    no_vigente[1].activo = False
    cargador = _Cargador({1: (_TEL,), 2: (_GAS,)})
    lineas = _lineas([_fila(1), no_vigente], desde=(2026, 10),
                     cargador=cargador)
    assert [l["registro_id"] for l in lineas] == [1]
    assert cargador.llamadas == [([1], (2026, 10))]


def test_f044_r10_el_contenedor_pasa_desde_de_config(monkeypatch):
    from config.settings import Settings
    from interface_adapters.api import deps

    from tests.conftest import UniversoFalso
    from tests.test_f023_sync_empresa import _UowLectura
    from tests.test_f025_sync_postventa import _sigrid

    monkeypatch.setattr(deps, "TransferClient", lambda _s: UniversoFalso())
    monkeypatch.setattr(deps, "SqlAlchemyUnitOfWork", _UowLectura)
    monkeypatch.setattr(deps, "SigridApiClient", lambda _s: _sigrid())
    contenedor = deps.construir_contenedor(Settings(_env_file=None), None)
    assert contenedor.registro_sigrid._vinculados_desde == (2026, 10)


# ================================ R30 ==================================== #
def _trazar(respuesta: dict) -> list:
    sesion = _SesionQueAnota()
    RegistroSigrid(lambda: sesion, _Transfer(), 1)._trazar(respuesta, "yo")
    return sesion.sentencias


def _tabla(st) -> str | None:
    return getattr(getattr(st, "table", None), "name", None)


def _de_subfila(sentencias: list) -> list[dict]:
    """Los valores de cada `INSERT … ON CONFLICT` en `asignacion_vinculado`
    (con su asignación y su vinculado): las columnas del `INSERT … SELECT`
    en orden, con los literales `param_N` de la subconsulta."""
    from sqlalchemy.dialects import postgresql
    out = []
    for st in sentencias:
        if _tabla(st) != "asignacion_vinculado":
            continue
        p = st.compile(dialect=postgresql.dialect()).params
        columnas = st._select_names[1:]
        valores = [p[f"param_{i}"] for i in range(1, len(columnas) + 1)]
        fila = dict(zip(columnas, valores, strict=True))
        fila["asignacion"] = p["id_1"]
        fila["vinculado"] = fila.pop("vinculado_ide")
        out.append(fila)
    return out


def _de_asignacion(sentencias: list) -> list[int]:
    return [st.compile().params["id_1"] for st in sentencias
            if _tabla(st) == "asignacion"]


_RESPUESTA = {
    "escritas": [{"registro_id": 1, "parte_cod": "PT26/00251",
                  "hmores_ide": 5101}],
    "omitidas": [
        {"registro_id": 2, "motivo": "sin partida"},
        {"registro_id": 1, "vinculado_ide": 12,
         "motivo": "el vehículo VE-12 no tiene partida CI de su tipo"},
        {"registro_id": 2, "vinculado_ide": 10,
         "motivo": "sigue al trabajador: sin partida"}],
    "ya_registradas": [],
    "vinculados": [
        {"registro_id": 1, "recurso_ide": 10, "accion": "escribir",
         "parte_cod": "PT26/00251", "hmores_ide": 5201, "motivo": None},
        {"registro_id": 1, "recurso_ide": 11, "accion": "ya_registrado",
         "parte_cod": None, "hmores_ide": 5301, "motivo": None},
        {"registro_id": 1, "recurso_ide": 12, "accion": "omitir",
         "parte_cod": None, "hmores_ide": None,
         "motivo": "el vehículo VE-12 no tiene partida CI de su tipo"},
        {"registro_id": 1, "recurso_ide": 13, "accion": "omitir",
         "parte_cod": None, "hmores_ide": None,
         "motivo": "pendiente de confirmar el pisado"},
        {"registro_id": 2, "recurso_ide": 10, "accion": "omitir",
         "parte_cod": None, "hmores_ide": None,
         "motivo": "sigue al trabajador: sin partida"}],
}


def test_f044_r30_la_traza_de_cada_vinculado():
    trazas = _de_subfila(_trazar(_RESPUESTA))
    por = {(t["asignacion"], t["vinculado"]): t for t in trazas}
    assert set(por) == {(1, 10), (1, 11), (1, 12), (2, 10)}
    assert (por[(1, 10)]["sigrid_estado"], por[(1, 10)]["sigrid_parte"],
            por[(1, 10)]["sigrid_hmores_ide"], por[(1, 10)]["sigrid_motivo"]
            ) == ("registrado", "PT26/00251", 5201, None)
    # La ya registrada, como la del titular: sin tocar parte ni motivo.
    assert por[(1, 11)] == {"sigrid_estado": "registrado",
                            "sigrid_hmores_ide": 5301, "asignacion": 1,
                            "vinculado": 11}
    assert (por[(1, 12)]["sigrid_estado"], por[(1, 12)]["sigrid_motivo"]) == (
        "omitido", "el vehículo VE-12 no tiene partida CI de su tipo")
    assert por[(2, 10)]["sigrid_motivo"] == "sigue al trabajador: sin partida"


def test_f044_r30_el_omitido_de_un_vinculado_no_toca_su_titular():
    sentencias = _trazar(_RESPUESTA)
    # La escrita (1) y la omitida del titular (2); ni una más.
    assert _de_asignacion(sentencias) == [1, 2]


def test_f044_r30_sin_vinculados_la_traza_de_hoy():
    sin = {k: v for k, v in _RESPUESTA.items() if k != "vinculados"}
    sin["omitidas"] = [o for o in sin["omitidas"] if "vinculado_ide" not in o]
    sentencias = _trazar(sin)
    assert _de_subfila(sentencias) == []
    assert _de_asignacion(sentencias) == [1, 2]


def test_f044_r30_el_motivo_se_corta_a_300():
    largo = {"registro_id": 1, "vinculado_ide": 12, "motivo": "x" * 400}
    [t] = _de_subfila(_trazar({"escritas": [], "ya_registradas": [],
                               "omitidas": [largo], "vinculados": [
                                   {"registro_id": 1, "recurso_ide": 12,
                                    "accion": "omitir", "motivo": "x" * 400}
                               ]}))
    assert len(t["sigrid_motivo"]) == 300


def test_f044_r30_una_asignacion_que_ya_no_existe_no_inserta():
    """La traza va por la subconsulta del `id` (sin línea, no inserta): un
    `reemplazar` entre preflight y traza no tumba la del titular."""
    [st] = [s for s in _trazar({"escritas": [], "omitidas": [],
                                "ya_registradas": [], "vinculados": [
                                    {"registro_id": 1, "recurso_ide": 10,
                                     "accion": "escribir",
                                     "parte_cod": "PT", "hmores_ide": 1}]})
            if _tabla(s) == "asignacion_vinculado"]
    assert "SELECT asignacion.id" in str(st)


def test_f044_r30_la_traza_no_es_de_las_que_no_hacen_nada():
    """Un vinculado en `escribir` sin `hmores_ide` (la relectura no lo
    vio) no se traza como registrado."""
    sentencias = _trazar({"escritas": [], "omitidas": [],
                          "ya_registradas": [], "vinculados": [
                              {"registro_id": 1, "recurso_ide": 10,
                               "accion": "escribir", "parte_cod": "PT",
                               "hmores_ide": None}]})
    assert _de_subfila(sentencias) == []


def test_f044_r30_el_payload_manda_el_hmores_ide_guardado():
    sub = SimpleNamespace(**_GAS.__dict__)
    [l] = _lineas([_fila(1)], desde=(2026, 10),
                  cargador=_Cargador({1: (sub,)}))
    assert l["vinculados"][0]["hmores_ide"] == 5301
