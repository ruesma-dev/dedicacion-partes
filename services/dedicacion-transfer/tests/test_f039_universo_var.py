# tests/test_f039_universo_var.py
"""F-039 · El universo VAR, calculado en un solo sitio (R1-R4).

La regla es `docs/ARCHITECTURE.md#regla-var`; aquí solo se comprueba que el
universo que publica `POST /api/var/universo` sale de las funciones de
`application/services/universo_var.py` (las mismas que usa el preflight,
`test_f039_preflight_var.py`), con el umbral del ajuste y sin escribir.

Sin red ni BBDD: el doble `ClienteVar` amplía el `ClienteFalso` de
`conftest.py` con la obra VAR y su presupuesto. Los `ide` de la obra VAR,
de su centro y de la partida 29 son los de Sigrid (lectura del 2026-10-06);
el resto, inventados.
"""
from __future__ import annotations

import pytest
from domain.errores import ObraAmbigua
from domain.models.registro_models import ObraEntrada

from tests.conftest import EMPRESA, ClienteFalso, SettingsFalso, _fila

#: Código de la obra VAR del doble. No es configuración del servicio: es
#: dato del test, igual que `OBRA_POSTVENTA` en `conftest.py`.
OBRA_VAR = "VAR"
VAR_IDE = 683806
VAR_CENIDE = 683807
#: Umbral por defecto del ajuste `VAR_PARTIDA_DESDE`.
DESDE = 29

#: Presupuesto de la obra VAR: las hojas numeradas cuelgan de `CD` y cada
#: una es una obra pequeña; el resto son capítulos y partidas `CI.*`. Las
#: filas NO van en orden de `ide`, para que el orden de la salida no pueda
#: salir del de Sigrid.
PRESUPUESTO_VAR: list[dict] = [
    _fila(52979, 0, 0, "CD", "COSTES DIRECTOS"),
    _fila(417058, 52979, 9, "100", "OBRA CIEN"),
    _fila(417001, 52979, 1, "05", "OBRA CINCO"),
    _fila(417002, 52979, 2, "28", "OBRA VEINTIOCHO"),
    _fila(417055, 52979, 3, "29", "ACOND. NAVE MODUL-A, ARROYOMOLINOS"),
    _fila(417056, 52979, 4, "29.1", "AMPLIACION 29"),
    _fila(417057, 52979, 5, "30", "OBRA TREINTA"),
    _fila(417059, 52979, 6, "029", "OBRA CERO VEINTINUEVE"),
    _fila(417060, 52979, 7, "29A", "OBRA 29 FASE A"),
    # Capítulo de código numérico (tiene hija): no es hoja, no entra; su
    # hija sí es hoja con número inicial 31.
    _fila(417061, 52979, 8, "31", "CAPITULO TREINTA Y UNO"),
    _fila(417062, 417061, 1, "31.1", "HIJA DEL 31"),
    # Hoja de número alto pero dada de baja.
    _fila(417063, 52979, 10, "32", "OBRA DE BAJA", tipdes=1),
    _fila(60000, 0, 1, "CI", "COSTES INDIRECTOS"),
    _fila(60001, 60000, 1, "CI.1.3", "ENCARGADO VARIOS"),
]

#: Partidas VAR del presupuesto con el umbral 29, por `ide`.
UNIVERSO_29 = {417055: "29", 417056: "29.1", 417057: "30", 417058: "100",
               417059: "029", 417060: "29A", 417062: "31.1"}


class ClienteVar(ClienteFalso):
    """`ClienteFalso` con la obra VAR (empresa `EMPRESA`), su centro y su
    presupuesto. `var_existe=False`: la obra VAR no está en Sigrid;
    `var_ambigua=True`: la búsqueda falla con `ObraAmbigua`."""

    def __init__(self, *, var_existe: bool = True, var_ambigua: bool = False,
                 presupuesto_var: list[dict] | None = None, **kw) -> None:
        super().__init__(**kw)
        self.obra_var = ObraEntrada(ide=VAR_IDE, codigo=OBRA_VAR,
                                    nombre="OBRAS VARIAS", empresa=EMPRESA)
        self.obra_var.cenide = VAR_CENIDE
        self._var_existe = var_existe
        self._var_ambigua = var_ambigua
        self.presupuesto_var = (PRESUPUESTO_VAR if presupuesto_var is None
                                else presupuesto_var)
        # Lecturas del presupuesto de la obra VAR (además del contador
        # común `n_capitulos_de_obra`, que suma todas las obras).
        self.n_presupuesto_var = 0

    def obra_por_codigo(self, cod, empresa):
        if cod == OBRA_VAR and empresa == EMPRESA:
            self.n_obra_por_codigo += 1
            if self._var_ambigua:
                raise ObraAmbigua(f"obra {cod} ambigua: 2 fichas en la "
                                  f"empresa {empresa}")
            return self.obra_var if self._var_existe else None
        return super().obra_por_codigo(cod, empresa)

    def obra_por_ide(self, ide):
        """Por `ide`: la VAR y la de origen; el resto, como el padre."""
        por_ide = {VAR_IDE: self.obra_var,
                   self.obra_origen.ide: self.obra_origen}
        return por_ide.get(ide) or super().obra_por_ide(ide)

    def capitulos_de_obra(self, obride):
        if obride == VAR_IDE:
            self.n_capitulos_de_obra += 1
            self.n_presupuesto_var += 1
            return self.presupuesto_var
        return super().capitulos_de_obra(obride)

    def cuentas_de_centro(self, cenide, empresa, subcuentas):
        """UNA cuenta `VAR.<subcuenta>` por subcuenta en el centro VAR."""
        if cenide == VAR_CENIDE:
            return {s: [(91000 + i, f"{OBRA_VAR}.{s}")]
                    for i, s in enumerate(sorted(subcuentas), start=1)}
        return super().cuentas_de_centro(cenide, empresa, subcuentas)


def ajustes_var(*, var_obra_cod: str = OBRA_VAR, var_partida_desde=DESDE,
                **kw) -> SettingsFalso:
    """`SettingsFalso` con los dos ajustes VAR puestos en la instancia."""
    st = SettingsFalso(**kw)
    st.var_obra_cod = var_obra_cod
    st.var_partida_desde = var_partida_desde
    return st


def _universo(cli=None, empresa: int = EMPRESA, **ajustes) -> dict:
    from application.services.universo_var import UniversoVar

    cli = ClienteVar() if cli is None else cli
    return UniversoVar(cliente=cli,
                       settings=ajustes_var(**ajustes)).calcular(empresa)


# ================== R2 · qué partida es partida VAR =================== #

@pytest.mark.parametrize("cod, numero", [
    ("29", 29), ("30", 30), ("100", 100), ("029", 29), ("29.1", 29),
    ("29A", 29), (" 29 ", 29), ("28", 28), ("05", 5), ("0", 0),
    ("CI.1.1", None), ("A29", None), ("", None), ("   ", None), (None, None),
])
def test_f039_r2_numero_inicial(cod, numero):
    """R2 · El número inicial son los dígitos con que empieza el código
    (tras quitar espacios); sin dígito inicial no hay número."""
    from application.services.universo_var import numero_inicial

    assert numero_inicial(cod) == numero


def _nodo(cod, *, hoja: bool = True, activa: bool = True):
    from application.services.partida_catalog import PartidaNodo

    return PartidaNodo(ide=1, padide=0, cod=cod, res=None, tex=None,
                       es_hoja=hoja, activa=activa)


@pytest.mark.parametrize("cod, hoja, activa, es_var", [
    ("29", True, True, True), ("30", True, True, True),
    ("100", True, True, True), ("029", True, True, True),
    ("29.1", True, True, True), ("29A", True, True, True),
    ("28", True, True, False), ("05", True, True, False),
    ("CI.1.1", True, True, False), (None, True, True, False),
    ("31", False, True, False),         # capítulo
    ("32", True, False, False),         # de baja
], ids=lambda v: repr(v))
def test_f039_r2_es_partida_var(cod, hoja, activa, es_var):
    """R2 · Hoja activa con número inicial ≥ umbral; nada más."""
    from application.services.universo_var import es_partida_var

    assert es_partida_var(_nodo(cod, hoja=hoja, activa=activa), DESDE) \
        is es_var


def test_f039_r2_el_umbral_es_inclusivo_y_es_el_que_se_pasa():
    """R2 · `29` entra con umbral 29 y no con 30: el umbral es el ajuste, no
    una constante."""
    from application.services.universo_var import es_partida_var

    assert es_partida_var(_nodo("29"), 29) is True
    assert es_partida_var(_nodo("29"), 30) is False
    assert es_partida_var(_nodo("30"), 30) is True


# ====================== R1 · el universo de VAR ======================= #

def test_f039_r1_universo_publica_la_obra_y_sus_partidas_por_ide():
    """R1 · Obra VAR (`ide`, `codigo`, `nombre`, `empresa`), umbral y las
    partidas VAR (`ide`, `cod`, `res`) ordenadas por `ide`. Sin escribir."""
    cli = ClienteVar()
    r = _universo(cli)
    assert r["empresa"] == EMPRESA and r["desde"] == DESDE
    assert r["motivo"] is None
    assert r["obra_var"] == {"ide": VAR_IDE, "codigo": OBRA_VAR,
                             "nombre": "OBRAS VARIAS", "empresa": EMPRESA}
    assert [p["ide"] for p in r["partidas"]] == sorted(UNIVERSO_29)
    assert {p["ide"]: p["cod"] for p in r["partidas"]} == UNIVERSO_29
    assert r["partidas"][0] == {"ide": 417055, "cod": "29",
                                "res": "ACOND. NAVE MODUL-A, ARROYOMOLINOS"}
    assert cli.escritos == []


def test_f039_r1_una_lectura_de_obra_y_una_de_presupuesto():
    """R1 · La obra y su presupuesto se leen UNA vez por petición."""
    cli = ClienteVar()
    _universo(cli)
    assert (cli.n_obra_por_codigo, cli.n_capitulos_de_obra) == (1, 1)


def test_f039_r1_el_umbral_sale_del_ajuste():
    """R1 · Con `VAR_PARTIDA_DESDE=30`, el 29 y sus variantes salen."""
    r = _universo(var_partida_desde=30)
    assert r["desde"] == 30
    assert {p["cod"] for p in r["partidas"]} == {"30", "100", "31.1"}


def test_f039_r1_la_obra_se_busca_con_el_codigo_del_ajuste():
    """R1 · El código de la obra es el del ajuste (con espacios de relleno
    fuera): otro código, otra obra; aquí, ninguna."""
    cli = ClienteVar()
    r = _universo(cli, var_obra_cod=" VAR ")
    assert r["obra_var"]["codigo"] == OBRA_VAR
    r = _universo(ClienteVar(), var_obra_cod="OTRA")
    assert r["obra_var"] is None and "'OTRA'" in r["motivo"]


# ======== R3 · sin obra VAR: universo vacío con su motivo ============= #

@pytest.mark.parametrize("cliente, motivo", [
    (lambda: ClienteVar(var_existe=False),
     f"obra VAR '{OBRA_VAR}' no encontrada en Sigrid en la empresa 1"),
    (lambda: ClienteVar(var_ambigua=True),
     f"obra VAR '{OBRA_VAR}' ambigua en la empresa 1: obra {OBRA_VAR} "
     f"ambigua: 2 fichas en la empresa 1"),
], ids=["ausente", "ambigua"])
def test_f039_r3_sin_obra_var_universo_vacio_con_su_motivo(cliente, motivo):
    """R3 · Obra VAR ausente o ambigua en la empresa: `obra_var` nula,
    ninguna partida y el motivo, sin leer el presupuesto."""
    cli = cliente()
    r = _universo(cli)
    assert r["obra_var"] is None and r["partidas"] == []
    assert r["motivo"] == motivo
    assert cli.n_capitulos_de_obra == 0


def test_f039_r3_la_empresa_pedida_es_la_que_se_busca():
    """R3 · La VAR de otra empresa no cuenta: en la 28 el doble no tiene
    obra VAR, así que no hay universo."""
    r = _universo(empresa=28)
    assert r["empresa"] == 28 and r["obra_var"] is None
    assert r["partidas"] == []
    assert "en la empresa 28" in r["motivo"]


@pytest.mark.parametrize("vacio", ["", "   "])
def test_f039_r3_sin_codigo_de_obra_var_no_lee_sigrid(vacio):
    """R3 · `VAR_OBRA_COD` vacío: sin universo, con su motivo y sin leer
    Sigrid."""
    from application.services.universo_var import MOTIVO_VAR_OFF

    cli = ClienteVar()
    r = _universo(cli, var_obra_cod=vacio)
    assert r["obra_var"] is None and r["partidas"] == []
    assert r["motivo"] == MOTIVO_VAR_OFF
    assert (cli.n_obra_por_codigo, cli.n_capitulos_de_obra) == (0, 0)


def test_f039_r3_el_catalogo_es_inmutable_y_solo_trae_partidas_var():
    """R3 · El catálogo de una petición no se modifica a medias y solo
    guarda las partidas VAR (ni capítulos ni `CI.*`)."""
    import dataclasses

    from application.services.universo_var import cargar_catalogo_var

    cat = cargar_catalogo_var(ClienteVar(), ajustes_var(), EMPRESA)
    assert set(cat.partidas) == set(UNIVERSO_29)
    assert cat.obra.ide == VAR_IDE and cat.motivo is None
    with pytest.raises(dataclasses.FrozenInstanceError):
        cat.obra = None  # type: ignore[misc]


def test_f039_r3_un_fallo_de_sigrid_sube():
    """R4 (la parte del servicio) · Un fallo de lectura no se convierte en
    universo parcial: sube tal cual."""
    cli = ClienteVar()

    def _roto(_obride):
        raise RuntimeError("sigrid-api caído")

    cli.capitulos_de_obra = _roto
    with pytest.raises(RuntimeError, match="caído"):
        _universo(cli)


def test_f039_r1_el_modulo_no_lleva_el_literal_de_la_obra_ni_el_umbral():
    """R1-R2 · `universo_var.py` cita los ajustes, nunca sus valores (como
    `test_f025_r25_…`)."""
    import re
    from pathlib import Path

    texto = (Path(__file__).resolve().parents[1] / "application" /
             "services" / "universo_var.py").read_text(encoding="utf-8")
    assert not re.search(r"""["']VAR["']""", texto)
    assert not re.search(r"\b29\b", texto)
    assert "VAR_OBRA_COD" in texto and "VAR_PARTIDA_DESDE" in texto


def test_f039_r1_ajustes_del_transfer():
    """R1 · Los dos ajustes existen con su alias y su defecto, y están en
    `.env.example`."""
    from pathlib import Path

    from config.settings import Settings

    campos = Settings.model_fields
    assert campos["var_obra_cod"].alias == "VAR_OBRA_COD"
    assert campos["var_obra_cod"].default == OBRA_VAR
    assert campos["var_partida_desde"].alias == "VAR_PARTIDA_DESDE"
    assert campos["var_partida_desde"].default == DESDE
    ejemplo = (Path(__file__).resolve().parents[1] / ".env.example"
               ).read_text(encoding="utf-8")
    assert f"VAR_OBRA_COD={OBRA_VAR}" in ejemplo
    assert f"VAR_PARTIDA_DESDE={DESDE}" in ejemplo


# ================ R4 · la ruta POST /api/var/universo ================= #

@pytest.fixture
def ruta(monkeypatch):
    """`build_app` con ajustes falsos (con los dos VAR) y el cliente de
    Sigrid sustituido por el doble que se le pase."""
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from interface_adapters.api import app as modulo

    def fabricar(cli, **cambios):
        ajustes = SimpleNamespace(**{
            **vars(ajustes_var()),
            "sigrid_api_base_url": "http://sigrid.invalid",
            "sigrid_api_function_key": "sin-clave",
            "sigrid_api_database": "ruesma", "sigrid_api_timeout_s": 1.0,
            "sigrid_max_statements": 15, "tip_parte_trabajo": 35,
            "est_parte_activo": 1, **cambios})
        monkeypatch.setattr(modulo, "SigridWriteClient", lambda **_kw: cli)
        return TestClient(modulo.build_app(ajustes))

    return fabricar


def test_f039_r1_ruta_devuelve_el_contrato(ruta):
    """R1 · Contrato de design §5 por HTTP: `ok`, `empresa`, `desde`,
    `motivo`, `obra_var` y `partidas`, sin escribir."""
    cli = ClienteVar()
    r = ruta(cli).post("/api/var/universo", json={"empresa": 1})
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo == {
        "ok": True, "empresa": 1, "desde": DESDE, "motivo": None,
        "obra_var": {"ide": VAR_IDE, "codigo": OBRA_VAR,
                     "nombre": "OBRAS VARIAS", "empresa": 1},
        "partidas": cuerpo["partidas"]}
    assert cuerpo["partidas"][0] == {
        "ide": 417055, "cod": "29",
        "res": "ACOND. NAVE MODUL-A, ARROYOMOLINOS"}
    assert len(cuerpo["partidas"]) == len(UNIVERSO_29)
    assert cli.escritos == []


def test_f039_r3_ruta_sin_obra_var_200_con_motivo(ruta):
    """R3 · Sin obra VAR no es un error: 200, `obra_var` nula, sin
    partidas y el motivo."""
    r = ruta(ClienteVar(var_existe=False)).post("/api/var/universo",
                                                json={"empresa": 1})
    assert r.status_code == 200, r.text
    assert r.json()["obra_var"] is None and r.json()["partidas"] == []
    assert "no encontrada" in r.json()["motivo"]


@pytest.mark.parametrize("empresa", ["ausente", None, 0, -1])
def test_f039_r4_sin_empresa_valida_422_sin_leer(ruta, empresa):
    """R4 · Sin empresa válida: 422 `{"ok": false, "error": …}` y ninguna
    lectura de Sigrid."""
    cli = ClienteVar()
    cuerpo = {} if empresa == "ausente" else {"empresa": empresa}
    r = ruta(cli).post("/api/var/universo", json=cuerpo)
    assert r.status_code == 422, r.text
    assert r.json() == {"ok": False,
                        "error": f"empresa no válida: {cuerpo.get('empresa')!r}"}
    assert (cli.n_obra_por_codigo, cli.n_capitulos_de_obra) == (0, 0)


def test_f039_r4_fallo_de_sigrid_502(ruta):
    """R4 · Un fallo de lectura de Sigrid es un 502 con el error, nunca un
    universo parcial."""
    cli = ClienteVar()

    def _roto(_obride):
        raise RuntimeError("sigrid-api caído")

    cli.capitulos_de_obra = _roto
    r = ruta(cli).post("/api/var/universo", json={"empresa": 1})
    assert r.status_code == 502, r.text
    assert r.json() == {"ok": False, "error": "sigrid-api caído"}
