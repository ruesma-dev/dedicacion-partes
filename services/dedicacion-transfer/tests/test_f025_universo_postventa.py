# tests/test_f025_universo_postventa.py
"""F-025 · El universo de postventa, calculado en un solo sitio (R1-R9, R25).

La regla es `docs/ARCHITECTURE.md#regla-p5`; aquí solo se comprueba que el
universo que publica `POST /api/postventa/universo` y lo que el preflight
hace con la línea de postventa salen de las MISMAS funciones, y que ningún
catálogo sobrevive a la petición que lo leyó.

Sin red ni BBDD: todo sale de los dobles de `conftest.py` y de
`test_f022_obra_por_empresa.py`.
"""
from __future__ import annotations

from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.reglas_porcentajes import MOTIVO_PARTIDA_PV_NO_HOJA
from domain.models.registro_models import ObraEntrada

from tests.conftest import (
    OBRA_ORIGEN,
    PRESUPUESTO_PV_HOJAS,
    ClienteFalso,
    SettingsFalso,
    _fila,
    linea,
)

OBRA = ObraEntrada(codigo=OBRA_ORIGEN)


def _pipeline(cli, **ajustes) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli, settings=SettingsFalso(**ajustes))


# ------------- R8 · sin líneas de postventa, catálogo vacío -------------- #

def test_f025_r8_preflight_sin_postventa_tras_otro_con_postventa():
    """R8 · La instancia del pipeline es única en la app (F-022): un preflight
    sin líneas de postventa no puede publicar el catálogo que leyó el
    anterior, que era de otra petición."""
    pl = _pipeline(ClienteFalso())
    con_pv = pl.preflight(obra=OBRA, lineas=[
        linea(registro_id=3, es_postventa=True)])
    assert con_pv.partidas_postventa, "control: el primero sí lo publica"

    sin_pv = pl.preflight(obra=OBRA, lineas=[linea(registro_id=1)])
    assert sin_pv.partidas_postventa == []


def test_f025_r8_preflight_sin_postventa_en_instancia_nueva():
    """R8 · Control: en una instancia recién creada también sale vacío."""
    pf = _pipeline(ClienteFalso()).preflight(obra=OBRA,
                                             lineas=[linea(registro_id=1)])
    assert pf.partidas_postventa == []


# ------------- R9 · el catálogo no sobrevive a su petición -------------- #

def test_f025_r9_el_pipeline_no_guarda_estado_entre_peticiones():
    """R9 · Ningún catálogo sobrevive a la petición que lo leyó: tras un
    preflight con postventa, la instancia solo conserva lo que tenía al
    nacer (cliente y ajustes)."""
    pl = _pipeline(ClienteFalso())
    antes = set(vars(pl))
    pl.preflight(obra=OBRA, lineas=[linea(registro_id=3, es_postventa=True)])
    assert set(vars(pl)) == antes


def test_f025_r9_override_validado_contra_el_presupuesto_de_su_peticion():
    """R9 · El override a `0713` vale con el presupuesto `hojas`; si en la
    petición siguiente `0713` ya tiene partidas debajo (es capítulo), el
    mismo override se omite: se valida contra lo leído en ESA petición."""
    cli = ClienteFalso()
    pl = _pipeline(cli)
    override = dict(registro_id=3, es_postventa=True, paride=70002,
                    partida_cod="0713")
    primero = pl.preflight(obra=OBRA, lineas=[linea(**override)])
    assert primero.acciones[0].partida_metodo == "manual", primero.acciones

    cli.capitulos = PRESUPUESTO_PV_HOJAS + [
        _fila(70031, 70002, 1, "0713.MO", "MANO DE OBRA")]
    segundo = pl.preflight(obra=OBRA, lineas=[linea(**override)])
    a = segundo.acciones[0]
    assert a.accion == "omitir", a
    assert a.motivo == MOTIVO_PARTIDA_PV_NO_HOJA.format(paride=70002)
