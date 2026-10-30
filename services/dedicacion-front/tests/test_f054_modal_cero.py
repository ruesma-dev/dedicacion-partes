# tests/test_f054_modal_cero.py
"""F-054 · T15: las sobrantes en el modal de registro (R33-R35, D17;
design §7).

`pintarModalPreflight` gana la sección «En Sigrid, en obras que no tiene en
la plataforma» si el preflight trae `sobrantes`: una casilla `.chk-cero`
por sobrante confirmable, **desmarcada** (D17: sin `marcadaPorDefecto` ni
`vistas` de F-064), con su trabajador o su vinculado (tipo y código), y las
no confirmables como aviso con su motivo. «Registrar» manda en
`sobrantes_a_cero` las marcadas, tal como las publicó el preflight, aparte
de `pisar_claves` (que nunca lleva claves `cero:`); sin marcar, la petición
de hoy. Repetir el preflight de una obra (`unirPreflight`) conserva la
sección y lo marcado; un preflight nuevo lo desmarca. Los pisados de
vinculado siguen saliendo marcados (F-064).

Código REAL de `app.js` en `node` con el DOM y la api de mentira del modal
(como `test_f064_pisado_vinculados.py`). Sin `node` se saltan con su
motivo. Sin red ni BBDD.
"""
from __future__ import annotations

import json

from tests.test_f050_modal_registro import ESCAPE, _funcion, _node, _registro
from tests.test_f064_pisado_vinculados import PIS_VIN, TF, _conflicto, _obra

FUNCIONES = ("fmtPct", "pctNuevas", "rotuloConflicto", "textoPartidaAccion",
             "rotuloOrigen", "diaMes", "nombreTrabajador",
             "pintarCierresRacha", "pintarSobrantes", "pintarModalPreflight",
             "pedirPreflight", "registroPreflight", "unirPreflight",
             "repreflightPartida", "registroEjecutar")

#: Como el de F-064, con las casillas `.chk-cero` además de las `.chk-pisar`.
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
    /<input type="checkbox" class="(chk-pisar|chk-cero)" value="([^"]*)"( checked)?>/g)]
    .map((m) => [m[1] + " " + m[2], !!m[3]]));
}
function cerrarModal() { dom.oculto = true; }
const marcadasDe = (clase) => [...dom.casillas].filter(([k, v]) => v
  && k.startsWith(clase + " ")).map(([k]) => ({value: k.slice(clase.length + 1)}));
const document = {addEventListener() {}, body: {dataset: {usuario: "u"}},
  querySelectorAll: (s) => s === ".chk-pisar:checked" ? marcadasDe("chk-pisar")
    : s === ".chk-cero:checked" ? marcadasDe("chk-cero") : []};
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
async function registrar(respuesta) {
  registroEjecutar(); await tick();
  const l = llamadas[llamadas.length - 1];
  l.res(respuesta || {ok: true, obras: []}); await tick();
  return l;
}
"""


def _escenario(cuerpo: str, datos: dict) -> dict:
    programa = "\n".join([
        _registro(), ESCAPE, ARNES, *(_funcion(f) for f in FUNCIONES),
        "const D = " + json.dumps(datos, ensure_ascii=False) + ";",
        "(async () => { const obs = {};", cuerpo,
        "process.stdout.write(JSON.stringify(obs)); })();"])
    return _node(programa)


def _sob(ide, *, recurso=77, vinculado=None, confirmable=True, motivo=None,
         obra="0713"):
    return {"clave": f"cero:{ide}", "hmores_ide": ide, "recurso_ide": recurso,
            "vinculado": vinculado, "obra_ide": int(obra), "obra_cod": obra,
            "parte_cod": "PT26/00300", "parte_est": 1, "hora": "MADM",
            "paride": 9, "partida_cod": "CI.1.5", "can": 0.2,
            "synckey": None, "confirmable": confirmable, "motivo": motivo}


SOBRANTES = [
    _sob(7001),
    _sob(7002, recurso=5000, vinculado={**TF, "titular_ide": 77}),
    _sob(7003, confirmable=False,
         motivo="la línea es de otro sistema (synckey partes:9)"),
]


def _pf(sobrantes=SOBRANTES, conflictos=()):
    pf = {"ok": True, "obras": [_obra(694, list(conflictos))]}
    if sobrantes is not None:
        pf["sobrantes"] = sobrantes
    return pf


def test_f054_r33_seccion_casillas_desmarcadas_y_avisos():
    r = _escenario("""
      await abrir(D.pf);
      obs.casillas = casillas(); obs.marcadas = marcadas(); obs.html = dom.html;
    """, {"pf": _pf(conflictos=[_conflicto(PIS_VIN, vinculado=TF)])})
    assert r["casillas"] == ["chk-cero cero:7001", "chk-cero cero:7002",
                             f"chk-pisar {PIS_VIN}"]
    # D17: las de cero, desmarcadas; el pisado de vinculado, marcado (F-064).
    assert r["marcadas"] == [f"chk-pisar {PIS_VIN}"]
    html = r["html"]
    assert "En Sigrid, en obras que no tiene en la plataforma" in html
    for texto in ("GONZALEZ PANIAGUA", "TF TF-10 de GONZALEZ PANIAGUA",
                  "obra 0713", "parte PT26/00300", "MADM", "CI.1.5", "20%",
                  "la línea es de otro sistema (synckey partes:9)"):
        assert texto in html, texto
    assert 'value="cero:7003"' not in html


def test_f054_r33_sin_sobrantes_el_modal_de_hoy():
    sin = _escenario("await abrir(D.pf); obs.html = dom.html;",
                     {"pf": _pf(sobrantes=None)})
    vacio = _escenario("await abrir(D.pf); obs.html = dom.html;",
                       {"pf": _pf(sobrantes=[])})
    assert sin["html"] == vacio["html"]
    assert "chk-cero" not in sin["html"] and "En Sigrid" not in sin["html"]


def test_f054_r35_sin_marcar_no_se_manda_nada():
    r = _escenario("""
      await abrir(D.pf);
      const l = await registrar(); obs.body = l.body;
    """, {"pf": _pf()})
    assert r["body"] == {"pisar_claves": [], "trabajador_ide": None,
                         "usuario": "u"}


def test_f054_r35_marcadas_van_en_sobrantes_a_cero_y_no_en_pisar():
    r = _escenario("""
      await abrir(D.pf);
      poner("chk-cero cero:7002", true);
      const l = await registrar({ok: true, obras: [],
        sobrantes_a_cero: {puestas: [{hmores_ide: 7002}],
                           omitidas: [{hmores_ide: 7009, motivo: "x"}]}});
      obs.body = l.body; obs.toasts = toasts;
    """, {"pf": _pf(conflictos=[_conflicto(PIS_VIN, vinculado=TF)])})
    assert r["body"]["pisar_claves"] == [PIS_VIN]
    assert r["body"]["sobrantes_a_cero"] == [SOBRANTES[1]]
    assert not any(k.startswith("cero:") for k in r["body"]["pisar_claves"])
    assert "1 puestas a 0" in r["toasts"][-1][0]
    assert "1 sin poner a 0: x" in r["toasts"][-1][0]
    assert r["toasts"][-1][1] is True       # O5: no sale como éxito


def test_f054_r33_repreflight_de_una_obra_conserva_seccion_y_marcadas():
    r = _escenario("""
      await abrir(D.pf);
      poner("chk-cero cero:7001", true);
      await repetir(694, D.una);
      obs.casillas = casillas(); obs.marcadas = marcadas();
      await abrir(D.pf);
      obs.nuevo = marcadas();
    """, {"pf": _pf(), "una": _pf(sobrantes=None)})
    assert r["casillas"] == ["chk-cero cero:7001", "chk-cero cero:7002"]
    assert r["marcadas"] == ["chk-cero cero:7001"]
    assert r["nuevo"] == []


# ---- T17: lo que la campaña de mutación de `app.js` dejó vivo ---- #
def test_f054_r33_el_texto_de_cada_sobrante_en_su_seccion():
    """Lo que dice cada sobrante, mirado SOLO en su sección (el pisado de
    vinculado de F-064 repite nombre y hora fuera de ella): el vinculado
    con su tipo, su código y el nombre de su trabajador; la hora."""
    r = _escenario("await abrir(D.pf); obs.html = dom.html;",
                   {"pf": _pf(conflictos=[_conflicto(PIS_VIN, vinculado=TF)])})
    html = r["html"]
    inicio = html.index("En Sigrid, en obras que no tiene en la plataforma")
    seccion = html[inicio:html.index('class="pie-modal"', inicio)]
    [v7001, v7002, v7003] = seccion.split("<div class=")[2:]
    assert "GONZALEZ PANIAGUA · obra 0713" in v7001
    assert "TF TF-10 de GONZALEZ PANIAGUA · obra 0713" in v7002
    for bloque in (v7001, v7002, v7003):
        assert "parte PT26/00300 · MADM · CI.1.5 · 20%" in bloque, bloque


def test_f054_r35_o5_sin_omitidas_es_exito_y_los_motivos_se_unen():
    r = _escenario("""
      await abrir(D.pf);
      poner("chk-cero cero:7001", true);
      await registrar({ok: true, obras: [],
        sobrantes_a_cero: {puestas: [{hmores_ide: 7001}], omitidas: []}});
      obs.bien = toasts[toasts.length - 1];
      await abrir(D.pf);
      poner("chk-cero cero:7001", true);
      await registrar({ok: true, obras: [],
        sobrantes_a_cero: {puestas: [], omitidas: [
          {hmores_ide: 1, motivo: "cambió"},
          {hmores_ide: 2, motivo: "cerrado"}]}});
      obs.mal = toasts[toasts.length - 1];
    """, {"pf": _pf()})
    assert r["bien"][1] is False and "sin poner a 0" not in r["bien"][0]
    assert r["mal"][1] is True
    assert "2 sin poner a 0: cambió; cerrado" in r["mal"][0]
