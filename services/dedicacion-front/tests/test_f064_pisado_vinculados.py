# tests/test_f064_pisado_vinculados.py
"""F-064 · El pisado de los recursos vinculados, confirmado por defecto en el
modal de registro (enmienda de F-044 R20 y R31).

La casilla de un conflicto de vinculado (`c.vinculado`) con `motivo`
«pisado» —o sin motivo, que el modal ya rotula como «Pisar»— sale MARCADA la
primera vez que se enseña; el humano puede desmarcarla. Las demás (pisado del
trabajador, sobrecarga y sin partida de trabajador o vinculado, cierres de
racha de F-062) siguen desmarcadas. Repetir el preflight de una obra no
vuelve a marcar una desmarcada; un preflight nuevo vuelve al valor por
defecto. «Registrar» manda en `pisar_claves` exactamente las marcadas.

Código REAL de `app.js` en `node` (`registroPreflight`, `repreflightPartida`,
`pintarModalPreflight`, `registroEjecutar` y lo que necesitan) con un DOM y
una api de mentira: las casillas salen del HTML pintado y el escenario las
marca o desmarca como el humano. Sin `node` se saltan con su motivo (el
reviewer los exige `passed`). Sin red ni BBDD.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from tests.test_f050_modal_registro import (
    ESCAPE,
    JS,
    _funcion,
    _node,
    _registro,
)

RAIZ_REPO = Path(__file__).resolve().parents[3]

#: Funciones reales del flujo del modal.
FUNCIONES = ("fmtPct", "pctNuevas", "rotuloConflicto", "textoPartidaAccion",
             "rotuloOrigen", "diaMes", "nombreTrabajador",
             "pintarCierresRacha", "pintarModalPreflight", "pedirPreflight",
             "registroPreflight", "unirPreflight", "repreflightPartida",
             "registroEjecutar")

#: DOM y api de mentira. `abrirModal` lee del HTML pintado cada casilla
#: `.chk-pisar` y si sale marcada; `poner` la marca o desmarca como el
#: humano; `querySelectorAll(".chk-pisar:checked")` devuelve las marcadas.
#: Cada `api()` queda pendiente hasta que el escenario la responde.
ARNES = r"""
const MESES = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
const state = {anio: 2026, mes: 9, trabajadores: [{ide: 77, nombre: "GONZALEZ PANIAGUA"}]};
const llamadas = [];
function api(url, o) {
  return new Promise((res, rej) => llamadas.push(
    {url, body: o && o.body ? JSON.parse(o.body) : null, res, rej}));
}
const toasts = [];
function toast(m, e) { toasts.push([m, !!e]); }
const dom = {oculto: true, casillas: new Map(), botones: {}, html: ""};
function boton(id) {
  return dom.botones[id] || (dom.botones[id] =
    {disabled: false, textContent: "", addEventListener() {}});
}
function $(sel) {
  if (sel === "#modal-registro") {
    return {classList: {contains: (c) => c === "oculto" && dom.oculto}};
  }
  return boton(sel);
}
function abrirModal(h) {
  dom.oculto = false; dom.html = h;
  dom.casillas = new Map([...h.matchAll(
    /<input type="checkbox" class="chk-pisar" value="([^"]*)"( checked)?>/g)]
    .map((m) => [m[1], !!m[2]]));
}
function cerrarModal() { dom.oculto = true; }
// `addEventListener`: `registroEjecutar` es la última función de `app.js` y
// su extracción arrastra el `DOMContentLoaded` que cuelga el botón.
const document = {addEventListener() {}, body: {dataset: {usuario: "u"}},
  querySelectorAll: (s) => s === ".chk-pisar:checked"
    ? [...dom.casillas].filter(([, v]) => v).map(([k]) => ({value: k})) : []};
const tick = () => new Promise((r) => setTimeout(r, 0));
const marcadas = () => [...dom.casillas].filter(([, v]) => v).map(([k]) => k).sort();
const casillas = () => [...dom.casillas.keys()].sort();
function poner(clave, valor) {
  if (!dom.casillas.has(clave)) throw new Error("no hay casilla " + clave);
  dom.casillas.set(clave, valor);
}
async function abrir(pf) {
  registroPreflight(null); await tick();
  llamadas[llamadas.length - 1].res(pf); await tick();
}
async function repetir(obraIde, pf) {
  repreflightPartida(obraIde); await tick();
  llamadas[llamadas.length - 1].res(pf); await tick();
}
async function registrar() {
  registroEjecutar(); await tick();
  const l = llamadas[llamadas.length - 1];
  l.res({ok: true, obras: []}); await tick();
  return l;
}
"""


def _escenario(cuerpo: str, datos: dict) -> dict:
    programa = "\n".join([
        _registro(), ESCAPE, ARNES,
        *(_funcion(f) for f in FUNCIONES),
        "const D = " + json.dumps(datos, ensure_ascii=False) + ";",
        "(async () => { const obs = {};", cuerpo,
        "process.stdout.write(JSON.stringify(obs)); })();"])
    return _node(programa)


# ------------------------------------------------------------- datos
def _conflicto(clave: str, motivo: str | None = "pisado",
               vinculado: dict | None = None) -> dict:
    c = {"clave": clave, "motivo": motivo, "recurso_ide": 77,
         "nombre": "GONZALEZ PANIAGUA", "hora_codigo": "MADM",
         "parte_cod": "PT26/00251", "nuevas": [{"can": 0.6}],
         "lineas": [{"ide": 5702, "hora_codigo": "MADM", "can": 0.4,
                     "fecha_int": 20260930}],
         "edita_ide": 5702, "a_cero_ides": [], "contexto": [],
         "suma_existente": 0.4, "suma_total": 1.0, "exceso": 0.0}
    if vinculado is not None:
        c["vinculado"] = vinculado
    return c


TF = {"tipo": "TF", "cod": "TF-10"}
CO = {"tipo": "CO", "cod": "CO-11"}
VE = {"tipo": "VE", "cod": "VE-12"}

PIS_TRAB = "77|202609|31|80002"          # pisado del trabajador
PIS_VIN = "10|202609|31|81001"           # pisado de vinculado
PIS_VIN_SIN_MOTIVO = "11|202609|31|81002"  # vinculado sin motivo
SOB_TRAB = "sobrecarga:77|2026-09"
SOB_VIN = "sobrecarga:12|2026-09"
SINP_TRAB = "sin_partida:3001"
SINP_VIN = "sin_partida:3001:12"
OTRO_VIN = "13|202609|31|81003"          # motivo que el front no conoce
CIERRE = "cierre:51"

CONFLICTOS = [
    _conflicto(PIS_TRAB),
    _conflicto(PIS_VIN, vinculado=TF),
    _conflicto(PIS_VIN_SIN_MOTIVO, motivo=None, vinculado=CO),
    _conflicto(SOB_TRAB, "sobrecarga"),
    _conflicto(SOB_VIN, "sobrecarga", vinculado=VE),
    _conflicto(SINP_TRAB, "sin_partida"),
    _conflicto(SINP_VIN, "sin_partida", vinculado=VE),
    _conflicto(OTRO_VIN, "otra_cosa", vinculado=TF),
]

CIERRE_RACHA = {"accion": "escribir", "requiere_confirmar": True,
                "clave": CIERRE, "recurso_ide": 77, "codigo": "CIV",
                "inicio_fec": 20260720, "inicio_parte": "PT26/00100",
                "fecha_int": 20260905, "parte_cod": "PT26/00251"}


def _obra(ide: int, conflictos: list[dict], cierres=()) -> dict:
    return {"obra": {"ide": ide, "codigo": f"0{ide}", "nombre": "Obra"},
            "ok": True, "forzada_pruebas": False, "partes": [],
            "acciones": [], "conflictos": conflictos,
            "cierres_racha": list(cierres)}


def _pf(*obras: dict) -> dict:
    return {"ok": True, "obras": list(obras)}


TODAS = _pf(_obra(694, CONFLICTOS, [CIERRE_RACHA]))


# ================ marcadaPorDefecto · la función pura ===================== #
def _marcada() -> str:
    """El cuerpo de `const marcadaPorDefecto = (c) => {…};` en `app.js`."""
    m = re.search(r"^const marcadaPorDefecto = \(c\) => \{.*?^\};$", JS,
                  re.DOTALL | re.MULTILINE)
    assert m, "no está `const marcadaPorDefecto = (c) => {...};` en app.js"
    return m.group(0)


def test_f064_marcada_por_defecto_solo_el_pisado_de_vinculado():
    casos = [_conflicto(PIS_TRAB), _conflicto(PIS_VIN, vinculado=TF),
             _conflicto(PIS_VIN_SIN_MOTIVO, motivo=None, vinculado=CO),
             _conflicto("x", motivo="", vinculado=CO),
             _conflicto(SOB_TRAB, "sobrecarga"),
             _conflicto(SOB_VIN, "sobrecarga", vinculado=VE),
             _conflicto(SINP_TRAB, "sin_partida"),
             _conflicto(SINP_VIN, "sin_partida", vinculado=VE),
             _conflicto(OTRO_VIN, "otra_cosa", vinculado=TF),
             _conflicto("y", vinculado=None), {"clave": "z"}]
    r = _node("\n".join([
        _marcada(),
        "process.stdout.write(JSON.stringify(" + json.dumps(casos)
        + ".map(marcadaPorDefecto)));"]))
    assert r == [False, True, True, True, False, False, False, False, False,
                 False, False]


def test_f064_marcada_por_defecto_es_pura_y_la_usa_el_modal():
    cuerpo = _marcada()
    for prohibido in ("registro", "document", "state", "$("):
        assert prohibido not in cuerpo, prohibido
    modal = " ".join(_funcion("pintarModalPreflight").split())
    propia = modal.split("const marcadaPorDefecto")[0]
    assert ("if (marcadaPorDefecto(c) && !registro.vistas.has(c.clave)) {"
            in propia)
    # El modal ya no mira el motivo por su cuenta (test de F-013 R4).
    assert "c.motivo" not in propia


# ======================= criterio 1 · al abrir el modal ================== #
def test_f064_al_abrir_solo_el_pisado_de_vinculado_sale_marcado():
    obs = _escenario("""
      await abrir(D.pf);
      obs.casillas = casillas(); obs.marcadas = marcadas();
    """, {"pf": TODAS})
    # Todas las casillas se pintan (ninguna se pierde ni se inventa) …
    assert obs["casillas"] == sorted([c["clave"] for c in CONFLICTOS]
                                     + [CIERRE])
    # … y solo salen marcadas las de pisado de vinculado (con motivo
    # «pisado» o sin motivo); el resto, desmarcadas como hoy.
    assert obs["marcadas"] == sorted([PIS_VIN, PIS_VIN_SIN_MOTIVO])


def test_f064_sin_vinculados_el_modal_de_hoy_todo_desmarcado():
    obs = _escenario("""
      await abrir(D.pf); obs.marcadas = marcadas();
      obs.n = casillas().length;
    """, {"pf": _pf(_obra(694, [_conflicto(PIS_TRAB),
                                _conflicto(SOB_TRAB, "sobrecarga"),
                                _conflicto(SINP_TRAB, "sin_partida")],
                          [CIERRE_RACHA]))})
    assert obs["marcadas"] == [] and obs["n"] == 4


def test_f064_la_casilla_marcada_lleva_checked_en_el_html():
    obs = _escenario("""
      await abrir(D.pf); obs.html = dom.html;
    """, {"pf": _pf(_obra(694, [_conflicto(PIS_VIN, vinculado=TF),
                                _conflicto(PIS_TRAB)]))})
    assert (f'<input type="checkbox" class="chk-pisar" value="{PIS_VIN}" '
            "checked>") in obs["html"]
    assert (f'<input type="checkbox" class="chk-pisar" value="{PIS_TRAB}">'
            in obs["html"])


# ============ criterio 2 · repetir el preflight y abrir de nuevo ========= #
def test_f064_desmarcada_sigue_desmarcada_al_repetir_el_preflight():
    nuevo = "14|202609|31|81004"
    repetido = _pf(_obra(694, CONFLICTOS + [_conflicto(nuevo, vinculado=TF)],
                         [CIERRE_RACHA]))
    obs = _escenario("""
      await abrir(D.pf);
      poner(D.pis_vin, false);          // el humano la desmarca
      poner(D.pis_trab, true);          // y marca el pisado del trabajador
      await repetir(694, D.repetido);
      obs.marcadas = marcadas();
      await repetir(694, D.repetido);   // y otra vez: nada cambia
      obs.otra_vez = marcadas();
    """, {"pf": TODAS, "repetido": repetido, "pis_vin": PIS_VIN,
          "pis_trab": PIS_TRAB})
    esperado = sorted([PIS_VIN_SIN_MOTIVO, PIS_TRAB, nuevo])
    assert obs["marcadas"] == esperado
    assert obs["otra_vez"] == esperado


def test_f064_repetir_una_obra_no_toca_lo_desmarcado_en_otra():
    obs = _escenario("""
      await abrir(D.pf);
      poner(D.b, false);
      await repetir(694, D.solo_a);
      obs.marcadas = marcadas();
    """, {"pf": _pf(_obra(694, [_conflicto(PIS_VIN, vinculado=TF)]),
                    _obra(695, [_conflicto("20|202609|31|1", vinculado=CO)])),
          "solo_a": _pf(_obra(694, [_conflicto(PIS_VIN, vinculado=TF)])),
          "b": "20|202609|31|1"})
    assert obs["marcadas"] == [PIS_VIN]


def test_f064_un_preflight_nuevo_vuelve_al_valor_por_defecto():
    obs = _escenario("""
      await abrir(D.pf);
      poner(D.pis_vin, false); poner(D.pis_vin_sm, false);
      poner(D.pis_trab, true);
      await repetir(694, D.pf);
      obs.antes = marcadas();
      cerrarModal();
      await abrir(D.pf);                // abrir de nuevo: preflight nuevo
      obs.despues = marcadas();
    """, {"pf": TODAS, "pis_vin": PIS_VIN, "pis_vin_sm": PIS_VIN_SIN_MOTIVO,
          "pis_trab": PIS_TRAB})
    assert obs["antes"] == [PIS_TRAB]
    assert obs["despues"] == sorted([PIS_VIN, PIS_VIN_SIN_MOTIVO])


# ======================= criterio 3 · «Registrar» ======================== #
def test_f064_registrar_por_defecto_manda_los_pisados_de_vinculado():
    obs = _escenario("""
      await abrir(D.pf);
      const l = await registrar();
      obs.url = l.url; obs.claves = l.body.pisar_claves.slice().sort();
    """, {"pf": TODAS})
    assert obs["url"] == "/periodos/2026/9/registro/ejecutar"
    assert obs["claves"] == sorted([PIS_VIN, PIS_VIN_SIN_MOTIVO])


def test_f064_registrar_manda_exactamente_las_marcadas():
    obs = _escenario("""
      await abrir(D.pf);
      poner(D.pis_vin_sm, false);       // una de vinculado desmarcada
      poner(D.pis_trab, true); poner(D.cierre, true); poner(D.sob, true);
      await repetir(694, D.pf);
      const l = await registrar();
      obs.claves = l.body.pisar_claves.slice().sort();
      obs.marcadas = marcadas();
    """, {"pf": TODAS, "pis_vin_sm": PIS_VIN_SIN_MOTIVO, "pis_trab": PIS_TRAB,
          "cierre": CIERRE, "sob": SOB_VIN})
    esperado = sorted([PIS_VIN, PIS_TRAB, CIERRE, SOB_VIN])
    assert obs["claves"] == esperado == obs["marcadas"]


# ================= criterio 4 · enmienda en F-044 R20 y R31 ============== #
def _requisito(texto: str, rid: str) -> str:
    m = re.search(rf"^- \*\*{rid}\.\*\*.*?(?=^- \*\*R\d+\.\*\*|^#|\Z)", texto,
                  re.DOTALL | re.MULTILINE)
    assert m, f"no está {rid}"
    return m.group(0)


def test_f064_enmienda_anotada_en_r20_y_r31_de_f044():
    texto = (RAIZ_REPO / "specs" / "F-044-recursos-vinculados"
             / "requirements.md").read_text(encoding="utf-8")
    for rid in ("R20", "R31"):
        assert "Enmienda F-064 (2026-10-26)" in _requisito(texto, rid), rid
