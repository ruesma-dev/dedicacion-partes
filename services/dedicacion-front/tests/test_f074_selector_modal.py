# tests/test_f074_selector_modal.py
"""F-074 · T12: la opción sin elegida del selector y el selector en la
omitida por partida no válida (R21, R22).

- R21 (D5): la opción «automática (la propone el registro)» pasa a «sin
  elegir · usar la propuesta» o, sin propuesta, «sin elegir · no encuentra
  partida»; sigue borrando la elegida (`partida` nula).
- R22: en el modal, la línea o subfila omitida porque su partida definida
  no vale (`partida_no_valida`) lleva el MISMO selector (F-050 R29) con la
  partida que nombra el transfer, junto a su motivo.

El código REAL de `app.js` en `node` con el DOM mínimo de F-050; lo demás en
estático.
"""
from __future__ import annotations

import re

from tests.test_f050_modal_registro import _accion, _boton, _modal, _obra
from tests.test_f050_selector_partida import _funcion, _plano

MOTIVO_NO_VALIDA = ("la partida CI.1.8 propuesta no es una partida hoja "
                    "activa del presupuesto de la obra 0694: no se escribe; "
                    "elige otra partida")


# ============================ R21 · el selector ========================== #
def test_f074_r21_rotulo_de_la_opcion_sin_elegida():
    montar = _plano(_funcion("montarSelectorPartida"))
    assert "automática (la propone el registro)" not in montar
    assert ('${resp.propuesta ? "sin elegir · usar la propuesta" : '
            '"sin elegir · no encuentra partida"}') in montar


def test_f074_r21_sigue_borrando_la_elegida():
    montar = _plano(_funcion("montarSelectorPartida"))
    assert "{ automatica: true }" in montar
    assert ("const partida = op.automatica ? null : { ide: op.ide, cod: "
            "op.cod, res: op.res };") in montar


# ============================== R22 · el modal =========================== #
def test_f074_r22_omitida_por_no_valida_lleva_el_selector():
    obs = _modal([_obra([_accion(accion="omitir", paride=0,
                                 partida_cod=None, motivo=MOTIVO_NO_VALIDA,
                                 partida_no_valida="CI.1.8")])], """
      botones[0]._h.click(); obs.aperturas = aperturas;
    """)
    assert _boton(obs["html"], 3001) == "CI.1.8"
    assert f'<span class="motivo">{MOTIVO_NO_VALIDA}</span>' in obs["html"]
    assert obs["lineas"] == {
        "3001": {"trabajador": 77, "obra_ide": 694, "es_postventa": False}}
    assert obs["aperturas"] == [[77, 694, False, "3001", True]]


def test_f074_r22_postventa_omitida_por_no_valida_tambien():
    obs = _modal([_obra([_accion(accion="omitir", paride=0,
                                 destino="postventa", es_postventa=True,
                                 motivo="la partida 0656 de la obra de "
                                        "postventa no vale",
                                 partida_no_valida="0656")])])
    assert _boton(obs["html"], 3001) == "0656"
    assert obs["lineas"]["3001"]["es_postventa"] is True


def test_f074_r22_otras_omitidas_siguen_sin_boton():
    obs = _modal([_obra([_accion(accion="omitir", motivo="otra empresa",
                                 partida_no_valida=None)])])
    assert "sel-partida" not in obs["html"] and obs["lineas"] == {}


def test_f074_r22_el_codigo_se_escapa():
    obs = _modal([_obra([_accion(accion="omitir", motivo="x",
                                 partida_no_valida="A<b>")])])
    assert _boton(obs["html"], 3001) == "A&lt;b&gt;"


def test_f074_r22_subfila_omitida_por_no_valida_lleva_su_selector():
    obra = _obra([_accion()])
    obra["vinculados"] = [{
        "registro_id": 3001, "recurso_ide": 10, "tipo": "TF",
        "tipo_res": "TELEFONO", "cod": "TF-10", "destino": "obra",
        "accion": "omitir", "can": 0.5, "hora_codigo": "MADM",
        "motivo": "la propuesta CICO13 del vinculado no vale",
        "partida_no_valida": "CICO13"}]
    html = _modal([obra])["html"]
    m = re.search(r'<button type="button" class="sel-partida" '
                  r'data-reg="3001" data-vinculado="10">([^<]*)</button>',
                  html)
    assert m and m.group(1) == "CICO13"
    assert "la propuesta CICO13 del vinculado no vale" in html
