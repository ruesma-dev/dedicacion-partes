# tests/test_f061_recarga.py
"""F-061 · El catálogo de incidencias se recarga tras cada sync (criterio 4).

Tras un `POST /sync` con éxito el front vuelve a pedir `GET /incidencias` y
el desplegable usa el catálogo nuevo sin recargar la página; si esa petición
falla, se avisa y se queda el que hubiera (como al abrir, F-030 R6). Un sync
fallido no la pide.

Se ejecutan las funciones REALES `sincronizar` y `cargarTiposIncidencia` en
node con dobles de `api`, `toast`, `$` y `cargarPeriodo`. Sin red ni BBDD.
"""
from __future__ import annotations

import json

from tests.test_f042_sugerencias import _funcion, _node

VIEJO = [{"codigo": "CIV", "letra": "V", "nombre": "Vacaciones"}]
NUEVO = [{"codigo": "CIE", "letra": "B", "nombre": "Enfermedad",
          "palabras": ["baja"], "orden_busqueda": 0}]

SYNC_OK = ("{ duracion_s: 1, empleados: { recibidos: 1, altas: 0, desactivados: 0 },"
           " obras: { recibidos: 1, altas: 0, desactivados: 0 } }")


def _sincronizar(sync: str, incidencias: str) -> dict:
    """`sync` / `incidencias`: «ok» o «falla» para cada petición."""
    return _node("\n".join([
        f"var state = {{ anio: 2026, mes: 10, tiposIncidencia: {json.dumps(VIEJO)} }};",
        "var pedidas = []; var avisos = [];",
        "var boton = { disabled: false, textContent: '' };",
        "function $(sel) { return boton; }",
        "function toast(m, e) { avisos.push([m, !!e]); }",
        "async function cargarPeriodo() { pedidas.push('cargarPeriodo'); }",
        "async function api(ruta) {",
        "  pedidas.push(ruta);",
        f"  if (ruta === '/sync') {{ if ('{sync}' === 'falla') throw new Error('sin sigrid');"
        f" return {SYNC_OK}; }}",
        f"  if ('{incidencias}' === 'falla') throw new Error('caida');",
        f"  return {{ incidencias: {json.dumps(NUEVO)} }};",
        "}",
        _funcion("cargarTiposIncidencia"),
        _funcion("sincronizar"),
        "sincronizar().then(() => process.stdout.write(JSON.stringify(",
        "  { pedidas, avisos, catalogo: state.tiposIncidencia, boton })));",
    ]))


def test_f061_r4_tras_un_sync_con_exito_se_pide_el_catalogo_nuevo():
    r = _sincronizar("ok", "ok")
    assert r["pedidas"] == ["/sync", "cargarPeriodo", "/incidencias"]
    assert r["catalogo"] == NUEVO
    assert [e for _m, e in r["avisos"]] == [False]
    assert r["boton"] == {"disabled": False, "textContent": "Sincronizar Sigrid"}


def test_f061_r4_si_la_recarga_falla_se_avisa_y_queda_el_que_habia():
    r = _sincronizar("ok", "falla")
    assert r["pedidas"] == ["/sync", "cargarPeriodo", "/incidencias"]
    assert r["catalogo"] == VIEJO
    assert r["avisos"][-1] == ["No se pudo cargar el catálogo de incidencias: caida", True]


def test_f061_r4_un_sync_fallido_no_recarga_el_catalogo():
    r = _sincronizar("falla", "ok")
    assert r["pedidas"] == ["/sync"]
    assert r["catalogo"] == VIEJO
    assert r["avisos"] == [["sin sigrid", True]]
