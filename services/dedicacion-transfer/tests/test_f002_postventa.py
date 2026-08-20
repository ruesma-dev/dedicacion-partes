# tests/test_f002_postventa.py
"""F-002 · Destino de la postventa (R15-R19), la decisión D1.

La regla está en `docs/ARCHITECTURE.md#regla-p5`; aquí solo se comprueba que
el código la cumple. Lo que se vigila, en una frase: **la línea de postventa
solo puede acabar en una partida HOJA y ACTIVA del presupuesto de la obra de
postventa, casada por CÓDIGO EXACTO y elegida de forma determinista.**

El defecto que da origen a la mitad de estos tests está en
`progress/sigrid_F-002.md`: `resolver_postventa` llamaba `hojas` a una lista
que no filtraba por hoja, así que la cascada podía devolver un capítulo —que
nunca es destino válido y que el desplegable del front nunca ofrece—. En el
presupuesto real hay capítulos con código numérico (`3`, `4`, … `11`), o sea
que el riesgo no era teórico.

Sin red ni BBDD: todo sale de las fixtures de `conftest.py`.
"""
from __future__ import annotations

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.partida_catalog import partidas_hoja
from application.services.partida_resolver import (
    construir_catalogo,
    resolver_postventa,
)
from application.services.reglas_porcentajes import MOTIVO_PARTIDA_PV_NO_HOJA
from domain.models.registro_models import ObraEntrada

from tests.conftest import (
    OBRA_ORIGEN,
    PRESUPUESTOS_PV,
    ClienteFalso,
    SettingsFalso,
    linea,
)

OBRA = ObraEntrada(codigo=OBRA_ORIGEN)


def _pipeline(cli: ClienteFalso, **ajustes) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli, settings=SettingsFalso(**ajustes))


def _nodos(variante: str):
    return construir_catalogo(PRESUPUESTOS_PV[variante])


def _pv(variante: str, registro_id: int = 3, **kw):
    """Preflight de UNA línea de postventa contra el presupuesto dado."""
    cli = ClienteFalso(presupuesto_postventa=variante)
    pf = _pipeline(cli).preflight(
        obra=OBRA, lineas=[linea(registro_id=registro_id,
                                 es_postventa=True, **kw)])
    return cli, pf


# ------------- R15 · la obra de postventa no está en Sigrid -------------- #

def test_f002_r15_obra_postventa_no_encontrada():
    """R15 · Sin obra de postventa no se inventa un destino: se omite."""
    cli = ClienteFalso(obra_postventa_existe=False)
    pf = _pipeline(cli).preflight(
        obra=OBRA, lineas=[linea(registro_id=3, es_postventa=True)])

    a = pf.acciones[0]
    assert a.accion == "omitir", a
    assert "obra de postventa" in (a.motivo or "")
    assert "no encontrada" in (a.motivo or "")


def test_f002_r15_el_motivo_llega_al_preflight():
    """R15 · Y el motivo es visible, no un silencio: el preflight lo cuenta
    como omisión y no escribe nada."""
    cli = ClienteFalso(obra_postventa_existe=False)
    res = _pipeline(cli).ejecutar(
        obra=OBRA, lineas=[linea(registro_id=3, es_postventa=True)])

    assert cli.inserts() == []
    assert [o["registro_id"] for o in res.omitidas] == [3]
    assert "no encontrada" in res.omitidas[0]["motivo"]


def test_f002_r15_la_obra_normal_no_se_ve_afectada():
    """R15 · Control: que falte la obra de postventa no puede bloquear las
    líneas normales, que no la necesitan para nada."""
    cli = ClienteFalso(obra_postventa_existe=False)
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=[
        linea(registro_id=1),
        linea(registro_id=3, es_postventa=True),
    ])
    assert [e["registro_id"] for e in res.escritas] == [1]


# ---------------- R16 · el destino es una hoja activa ------------------- #

def test_f002_r16_solo_partida_hoja_activa():
    """R16 · Con el presupuesto real, la partida resuelta es hoja y activa."""
    nodos = _nodos("hojas")
    nodo = resolver_postventa(nodos, OBRA_ORIGEN, None)
    assert nodo is not None and nodo.es_hoja and nodo.activa, nodo
    assert nodo.cod == OBRA_ORIGEN


@pytest.mark.parametrize("codigo", ("0678", "11"))
def test_f002_r16_un_capitulo_no_es_destino(codigo):
    """R16 · EL test del defecto. En el presupuesto donde las obras son
    CAPÍTULOS (tienen partidas dentro), y con el capítulo de código numérico
    del presupuesto real, la resolución NO puede devolver el capítulo:
    `hmores.paride` tiene que apuntar a una hoja."""
    variante = "capitulos" if codigo == "0678" else "hojas"
    nodo = resolver_postventa(_nodos(variante), codigo, None)
    assert nodo is None or (nodo.es_hoja and nodo.activa), (codigo, nodo)


def test_f002_r16_el_capitulo_no_llega_al_paride_de_la_linea():
    """R16 · Y lo mismo visto desde el pipeline, que es donde acabaría
    escribiéndose: el `paride` de la acción es un ide de hoja activa."""
    _cli, pf = _pv("capitulos")
    hojas = {n.ide for n in partidas_hoja(_nodos("capitulos"))}
    a = pf.acciones[0]
    assert a.accion == "escribir" and a.destino == "postventa", a
    assert a.paride in hojas, (a.paride, sorted(hojas))


def test_f002_r16_una_hoja_inactiva_no_es_destino():
    """R16 · Una partida dada de baja (`tipdes != 0`) tampoco vale, aunque
    su código case exacto: escribir contra ella es escribir en una partida
    que Administración retiró."""
    nodos = _nodos("hojas_inactivas")
    assert nodos[70001].cod == OBRA_ORIGEN and not nodos[70001].activa
    assert resolver_postventa(nodos, OBRA_ORIGEN, None) is None


def test_f002_r16_la_hoja_inactiva_omite_la_linea_con_motivo():
    """R16 · Sin casado no se escribe: la línea se omite con su motivo, no
    se cuela con `paride = 0`."""
    cli, pf = _pv("hojas_inactivas")
    a = pf.acciones[0]
    assert a.accion == "omitir", a
    assert "no casa" in (a.motivo or "")
    assert cli.inserts() == []


def test_f002_r16_un_override_manual_a_un_capitulo_se_omite():
    """R16 · La otra puerta de entrada es el override del front: el usuario
    puede mandar cualquier `paride`. Si no es hoja activa del presupuesto de
    postventa, la línea se omite con motivo propio."""
    cli, pf = _pv("capitulos", paride=70001, partida_cod="0678")
    a = pf.acciones[0]
    assert a.accion == "omitir", a
    assert a.motivo == MOTIVO_PARTIDA_PV_NO_HOJA.format(paride=70001), a.motivo
    assert cli.inserts() == []


def test_f002_r16_un_override_manual_a_una_hoja_si_vale():
    """R16 · Control positivo: el override a una hoja activa se respeta tal
    cual, que es para lo que está."""
    _cli, pf = _pv("capitulos", paride=70011, partida_cod="0678.MO")
    a = pf.acciones[0]
    assert a.accion == "escribir" and a.partida_metodo == "manual", a
    assert a.paride == 70011


def test_f002_r16_el_override_de_la_obra_normal_no_se_valida_contra_postventa():
    """R16 · Control negativo: la validación es de la postventa. Un override
    en una línea de obra normal apunta al presupuesto de SU obra, y no se le
    puede exigir estar en el de postventa."""
    cli = ClienteFalso()
    pf = _pipeline(cli).preflight(
        obra=OBRA, lineas=[linea(registro_id=1, paride=80002,
                                 partida_cod="CI.1.20")])
    a = pf.acciones[0]
    assert a.accion == "escribir" and a.paride == 80002, a


# --------- R17 · el automático y el desplegable, mismo universo --------- #

@pytest.mark.parametrize("variante", ("hojas", "capitulos"))
def test_f002_r17_el_automatico_y_el_desplegable_comparten_universo(variante):
    """R17 · Lo que el automático puede elegir y lo que el front ofrece son
    el MISMO conjunto. Si divergen, el usuario ve un desplegable que no
    incluye lo que el sistema acaba de decidir por él, y no puede corregirlo
    sin salirse de la lista."""
    _cli, pf = _pv(variante)
    desplegable = {p["ide"] for p in getattr(pf, "partidas_postventa")}
    universo = {n.ide for n in partidas_hoja(_nodos(variante))}
    assert desplegable == universo, variante

    elegida = getattr(pf, "capitulo_postventa")
    assert elegida is not None and elegida["ide"] in desplegable, elegida


def test_f002_r17_el_desplegable_no_ofrece_capitulos_ni_bajas():
    """R17 · Control: el universo es «hojas activas», no «todo el árbol»."""
    _cli, pf = _pv("hojas_inactivas")
    ides = {p["ide"] for p in getattr(pf, "partidas_postventa")}
    assert 69000 not in ides            # CD es capítulo
    assert 70001 not in ides            # 0678 está de baja
    assert 70002 in ides                # 0713 es hoja activa


# ------------------- R18 · casado por código exacto -------------------- #

def test_f002_r18_casado_por_codigo_exacto():
    """R18 · El código de la obra se compara contra `cod`, entero. Gana el
    exacto aunque haya otra partida cuya DESCRIPCIÓN empiece por ese mismo
    código (tercer escalón de la cascada)."""
    nodo = resolver_postventa(_nodos("hojas"), "0664", None)
    assert nodo is not None and nodo.cod == "0664", nodo
    assert nodo.ide == 70004


def test_f002_r18_0656_no_casa_con_656():
    """R18 · `normalize_code` NO quita ceros a la izquierda, y así debe
    seguir: en el presupuesto real conviven las dos, `0656` bajo `CD` y
    `656` suelta en la raíz. Casarlas sería imputar a la partida de otro."""
    nodos = _nodos("hojas")
    con_cero = resolver_postventa(nodos, "0656", None)
    sin_cero = resolver_postventa(nodos, "656", None)

    assert con_cero is not None and sin_cero is not None
    assert con_cero.cod == "0656" and sin_cero.cod == "656"
    assert con_cero.ide != sin_cero.ide


def test_f002_r18_la_cascada_solo_actua_sin_exacto():
    """R18 · Control positivo de la cascada: sin partida de código exacto sí
    se busca el código en la descripción. La cascada se conserva; lo que R18
    exige es que no adelante al exacto."""
    nodo = resolver_postventa(_nodos("hojas"), "0777", None)
    assert nodo is not None and nodo.ide == 70006, nodo
    assert nodo.cod == "0998"           # casó por la descripción, no por cod


def test_f002_r18_el_ultimo_escalon_casa_por_nombre_de_obra():
    """R18 · Cuarto y último escalón: si la obra no trae código utilizable,
    se busca su NOMBRE dentro de la descripción de la partida. Es el que
    salva a las obras que en Sigrid se identifican por nombre."""
    nodo = resolver_postventa(_nodos("hojas"), None, "CLUB DEPORTIVO")
    assert nodo is not None and nodo.ide == 70002, nodo


def test_f002_r18_el_escalon_del_nombre_tambien_mira_solo_hojas_activas():
    """R18 · Y no es una puerta trasera: el último escalón busca en el mismo
    universo que los otros tres. Con la partida de la obra dada de baja, no
    devuelve nada aunque el nombre case."""
    nodos = _nodos("hojas_inactivas")
    assert "15 VIVIENDAS" in (nodos[70001].res or "")
    assert resolver_postventa(nodos, None, "15 VIVIENDAS") is None


def test_f002_r18_sin_ninguna_coincidencia_no_hay_partida():
    """R18 · Y si no casa por ningún escalón, no se inventa una: `None`, que
    el pipeline convierte en omisión con motivo."""
    assert resolver_postventa(_nodos("hojas"), "9999", None) is None


# --------------------- R19 · elección determinista --------------------- #

def test_f002_r19_la_eleccion_no_depende_del_orden_de_las_filas():
    """R19 · Sigrid devuelve las filas sin `ORDER BY` garantizado. Con las
    MISMAS filas en orden inverso, la partida elegida tiene que ser la misma:
    si no, dos ejecuciones seguidas imputan a partidas distintas y nadie
    sabría por qué."""
    directo = resolver_postventa(_nodos("hojas"), "06", None)
    invertido = resolver_postventa(_nodos("orden_invertido"), "06", None)

    assert directo is not None and invertido is not None
    assert directo.ide == invertido.ide, (directo.cod, invertido.cod)


def test_f002_r19_el_desempate_es_por_codigo():
    """R19 · Y el criterio de desempate es explicable: el menor código. Que
    sea determinista no basta si nadie puede predecirlo."""
    nodo = resolver_postventa(_nodos("hojas"), "06", None)
    candidatos = [n.cod for n in partidas_hoja(_nodos("hojas"))
                  if (n.cod or "").startswith("06")]
    assert len(candidatos) > 1, candidatos
    assert nodo.cod == min(candidatos), (nodo.cod, candidatos)
