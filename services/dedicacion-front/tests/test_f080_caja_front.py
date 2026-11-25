# tests/test_f080_caja_front.py
"""F-080 · T3: regresión del front con la caja POR % (R3, R9). Sin cambio en
`app.js`: pinta lo que dice `reparto`. Ejecuta las funciones REALES de
`app.js` en node, como `test_f069_importes_front.py`.

- R3: con la fila de R2 (la caja una vez en `importes` y cada subfila de caja
  con `reparto: pct`, sin cantidad), el editor enseña UNA casilla de caja en
  € («CAJA <código>») y ninguna «Caja · <obra>»; su `PUT` va sin `obra_ide`;
  la subfila enseña la caja del mes o «falta importe».
- R9: el modal enseña la caja como km y viajes («180,00 € de 300,00 €»),
  nunca «caja de esta obra».
"""
from __future__ import annotations

from tests.test_f030_tabla_incidencias import _editor
from tests.test_f042_sugerencias import _funcion, _node
from tests.test_f044_vinculados_front import (
    _accion_reg,
    _filas_tabla,
    _modal_vin,
    _obra_reg,
    _vin_reg,
)
from tests.test_f069_importes_front import CARGAR, PINTAR

#: La fila que devuelve la api tras F-080 (R2): la caja por % como los km.
FILA = """
  const t = {
    ide: 14,
    lineas: [
      { obra_ide: 1, es_postventa: false, porcentaje: 60, cod: "0001",
        vinculados: [
          { vinculado_ide: 20, tipo: "VP", cod: "VP-20", reparto: "pct", unidad: "km" },
          { vinculado_ide: 30, tipo: "CAJA", cod: "CJ", reparto: "pct", unidad: "eur" }] },
      { obra_ide: 2, es_postventa: true, porcentaje: 40, cod: "0002",
        vinculados: [
          { vinculado_ide: 20, tipo: "VP", cod: "VP-20", reparto: "pct", unidad: "km" },
          { vinculado_ide: 30, tipo: "CAJA", cod: "CJ", reparto: "pct", unidad: "eur" }] }],
    importes: [
      { vinculado_ide: 20, tipo: "VP", cod: "VP-20", unidad: "km",
        cantidad: 724.5, copiado: false, comentario: null },
      { vinculado_ide: 30, tipo: "CAJA", cod: "CJ", unidad: "eur",
        cantidad: 300, copiado: false, comentario: "caja" }],
    incidencias: [] };
"""


# ================================ R3 ===================================== #
def test_f080_r3_una_casilla_de_caja_por_trabajador_y_ninguna_por_obra():
    r = _editor(CARGAR, FILA + """
      cargarEdicion(t);
      const casillas = state.importesEdicion;
      casillas[1].cantidad = "250";
      resultado = { casillas, cuerpo: cuerpoImportes(casillas) };
    """)
    assert [(c["vinculado_ide"], c.get("obra_ide"), c["etiqueta"], c["unidad"],
             c["comentario"]) for c in r["casillas"]] == [
        (20, None, "VP VP-20", "km", ""),
        (30, None, "CAJA CJ", "eur", "caja")]
    assert not any(c["etiqueta"].startswith("Caja ·") for c in r["casillas"])
    # El PUT de la caja, sin obra: la caja del mes (R4).
    assert r["cuerpo"] == [{"vinculado_ide": 30, "cantidad": 250,
                            "comentario": "caja"}]


def test_f080_r3_la_subfila_ensena_la_caja_del_mes_o_falta_importe():
    r = _node("\n".join([PINTAR, FILA, """
      const cajas = t.lineas.map((l) => l.vinculados[1]);
      const sin = { ...t, importes: [t.importes[0]] };
      process.stdout.write(JSON.stringify({
        con: cajas.map((v) => htmlCantidadVinculado(t, v)),
        sin: cajas.map((v) => htmlCantidadVinculado(sin, v)),
        comentarios: cajas.map((v) => comentarioVinculado(t, v)) }));
    """]))
    assert r["con"] == ['<span class="cantidad-vin">300,00 €</span>'] * 2
    assert r["sin"] == ['<span class="cantidad-vin falta">falta importe</span>'] * 2
    assert r["comentarios"] == ["caja", "caja"]


# ================================ R9 ===================================== #
def test_f080_r9_el_modal_ensena_la_caja_como_los_km():
    texto = "\n".join(_funcion(f) for f in ("fmtCantidad",
                                            "textoImporteVinculado"))
    caja = dict(recurso_ide=22, tipo="CAJA", tipo_res="CAJA OBRA", cod="CJ",
                hora_codigo="CO", reparto="pct", pre=300.0)
    obs = _modal_vin([_obra_reg(
        [_accion_reg(can=0.6),
         _accion_reg(registro_id=3002, can=0.4, destino="postventa",
                     es_postventa=True)],
        [_vin_reg(can=0.6, tot=180.0, **caja),
         _vin_reg(registro_id=3002, can=0.4, tot=120.0, destino="postventa",
                  **caja)])], texto)
    filas = _filas_tabla(obs["html"])
    cajas = [f for f in filas if "CAJA OBRA" in f]
    assert len(cajas) == 2
    assert "180,00 € de 300,00 €" in cajas[0]
    assert "120,00 € de 300,00 €" in cajas[1] and "Postventa" in cajas[1]
    assert "caja de esta obra" not in obs["html"]
