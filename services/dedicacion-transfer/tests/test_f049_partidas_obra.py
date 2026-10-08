# tests/test_f049_partidas_obra.py
"""F-049 (ampliación d) · `partidas_obra` se publica aunque todas las líneas
de obra normal lleven partida manual.

Fallo que encontró el humano en la MANUAL de F-049 (2026-10-08): al elegir
una partida en el modal y volver a previsualizar, el desplegable salía vacío
(«— sin partida —»). Las partidas elegidas viajan como `paride` de la línea
(override manual) y el pipeline solo leía el presupuesto de la obra de
origen si alguna línea NO la traía (`registro_pipeline.py`, paso 4): con
todas manuales, `partidas_obra` salía `[]` y el front no tenía con qué
pintar la partida que se iba a escribir.

Lo que se fija aquí:

- con todas las líneas de obra normal manuales, `partidas_obra` trae el
  catálogo (hojas activas) de la obra de origen;
- una sola lectura del presupuesto de origen por petición, mezclen o no
  manuales y automáticas (como hoy);
- sin líneas de obra normal a escribir (solo postventa) no se lee nada de
  más ni se publica nada (como hoy);
- lo que se escribe no cambia: la partida manual manda.

Sin red ni BBDD: el pipeline solo habla con el `ClienteFalso` de
`conftest.py`.
"""
from __future__ import annotations

from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import ObraEntrada

from tests.conftest import (
    OBRA_ORIGEN,
    ClienteFalso,
    SettingsFalso,
    linea,
)

OBRA = ObraEntrada(codigo=OBRA_ORIGEN)

#: Hojas activas del presupuesto de origen de `conftest.py`, como las
#: publica `_cat` (`CI` es capítulo: no sale).
CATALOGO_ORIGEN = [
    {"ide": 80001, "cod": "CI.1.10", "res": "ENCARGADO (ACUNA)",
     "categoria": "CI"},
    {"ide": 80002, "cod": "CI.1.20", "res": "JEFE DE OBRA",
     "categoria": "CI"},
]


def _cliente() -> tuple[ClienteFalso, list[int]]:
    """Doble que además apunta QUÉ obra se lee (el contador común suma
    todas)."""
    cli = ClienteFalso()
    leidas: list[int] = []
    original = cli.capitulos_de_obra

    def capitulos_de_obra(obride):
        leidas.append(int(obride))
        return original(obride)

    cli.capitulos_de_obra = capitulos_de_obra
    return cli, leidas


def _pf(cli, lineas):
    return RegistroPipeline(cliente=cli, settings=SettingsFalso()).preflight(
        obra=OBRA, lineas=lineas)


def _manual(**kw):
    datos = dict(registro_id=1, paride=80002, partida_cod="CI.1.20")
    datos.update(kw)
    return linea(**datos)


def test_f049_d_todas_manuales_publica_el_catalogo_de_origen():
    """El caso del humano: la única línea de obra lleva la partida elegida
    en el modal y aun así el desplegable tiene que poder pintarla."""
    cli, leidas = _cliente()
    pf = _pf(cli, [_manual()])

    a = pf.acciones[0]
    assert (a.accion, a.paride, a.partida_metodo) == (
        "escribir", 80002, "manual"), a
    assert pf.partidas_obra == CATALOGO_ORIGEN
    assert leidas == [cli.obra_origen.ide]


def test_f049_d_varias_manuales_una_sola_lectura():
    cli, leidas = _cliente()
    pf = _pf(cli, [_manual(registro_id=1),
                   _manual(registro_id=2, recurso_ide=400, paride=80001,
                           partida_cod="CI.1.10")])

    assert [a.paride for a in pf.acciones] == [80002, 80001]
    assert pf.partidas_obra == CATALOGO_ORIGEN
    assert leidas == [cli.obra_origen.ide]


def test_f049_d_manual_y_automatica_una_sola_lectura_como_hoy():
    """Control: con una línea sin partida manual el catálogo ya se leía;
    la ampliación no añade una segunda lectura."""
    cli, leidas = _cliente()
    pf = _pf(cli, [_manual(registro_id=1, recurso_ide=400),
                   linea(registro_id=2)])

    assert [(a.paride, a.partida_metodo) for a in pf.acciones] == [
        (80002, "manual"), (80001, "auto_nombre")]
    assert pf.partidas_obra == CATALOGO_ORIGEN
    assert leidas == [cli.obra_origen.ide]


def test_f049_d_solo_postventa_no_lee_el_presupuesto_de_origen():
    """Sin líneas de obra normal no hay desplegable de obra que pintar: ni
    lectura de más ni `partidas_obra`."""
    cli, leidas = _cliente()
    pf = _pf(cli, [_manual(es_postventa=True, paride=None,
                           partida_cod=None)])

    assert [a.destino for a in pf.acciones] == ["postventa"]
    assert pf.partidas_obra == []
    assert cli.obra_origen.ide not in leidas


def test_f049_d_lo_que_se_escribe_no_cambia():
    """La partida manual sigue mandando en la escritura (la ampliación solo
    publica el catálogo)."""
    cli, _ = _cliente()
    res = RegistroPipeline(cliente=cli, settings=SettingsFalso()).ejecutar(
        obra=OBRA, lineas=[_manual()])

    assert res.ok, res
    assert [i["paride"] for i in cli.inserts()] == [80002]
