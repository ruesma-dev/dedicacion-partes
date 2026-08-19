# tests/test_f002_pipeline.py
"""F-002 · Pipeline de registro, offline (R10, R11, R13).

Tres cosas que solo se ven con el pipeline entero montado: que reejecutar no
duplique (`synckey`), que el modo pruebas desvíe la escritura sin falsear el
casado de la postventa, y que dos líneas que chocan con la MISMA línea de
Sigrid no la borren dos veces.

Sin red ni BBDD: el pipeline solo habla con el `ClienteFalso` de
`conftest.py`, que se limita a acumular las sentencias que se le mandan.
"""
from __future__ import annotations

from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import LineaSigrid, ObraEntrada
from infrastructure.sigrid.sigrid_write_client import synckey_de

from tests.conftest import (
    OBRA_ORIGEN, OBRA_POSTVENTA, OBRA_PRUEBAS, ClienteFalso, SettingsFalso,
    linea, linea_previa,
)

OBRA = ObraEntrada(codigo=OBRA_ORIGEN)


def _pipeline(cli: ClienteFalso, **ajustes) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli, settings=SettingsFalso(**ajustes))


# ------------------------- R10 · idempotencia ---------------------- #

def test_f002_r10_idempotencia_synckey():
    """R10 · Si la línea ya está en Sigrid con nuestra synckey, se marca
    `ya_registrado` y no se vuelve a escribir."""
    ya = LineaSigrid(ide=9001, reside=200, fecha_int=20260731, horide=5,
                     hora_codigo="MENC", can=0.4, tot=3600.0,
                     synckey=synckey_de(1), nuestra=True)
    cli = ClienteFalso(synckeys={synckey_de(1): ya})
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=[linea(registro_id=1)])

    a = pf.acciones[0]
    assert a.accion == "ya_registrado", a
    assert a.hmores_ide == 9001
    assert "no se duplica" in (a.motivo or "")
    assert pf.n_escribir == 0 and pf.n_ya == 1


def test_f002_r10_la_reejecucion_no_inserta_nada():
    """R10 · Y `ejecutar` no manda ni un INSERT: la idempotencia no es solo
    una etiqueta del preflight."""
    ya = LineaSigrid(ide=9001, reside=200, fecha_int=20260731, horide=5,
                     hora_codigo="MENC", can=0.4, tot=3600.0,
                     synckey=synckey_de(1), nuestra=True)
    cli = ClienteFalso(synckeys={synckey_de(1): ya})
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=[linea(registro_id=1)])

    assert res.ya_registradas == [1]
    assert res.escritas == [] and cli.inserts() == []


def test_f002_r10_sin_synckey_previa_si_se_escribe():
    """R10 · Control positivo: la misma línea, sin registro previo, se
    escribe. Sin esto, el test de arriba pasaría con un pipeline que no
    escribe nunca."""
    cli = ClienteFalso()
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=[linea(registro_id=1)])
    assert [e["registro_id"] for e in res.escritas] == [1]


# ------------------------ R11 · modo pruebas ----------------------- #

def test_f002_r11_modo_pruebas_destino_y_partida():
    """R11 · En pruebas TODO se escribe en la obra de pruebas, pero la
    partida de la postventa se sigue resolviendo contra la obra de postventa
    REAL: si no, la prueba no validaría el casado, que es a lo que va."""
    cli = ClienteFalso()
    pf = _pipeline(cli, obra_pruebas_forzar=True).preflight(
        obra=OBRA, lineas=[linea(registro_id=3, es_postventa=True,
                                 porcentaje=0.5)])

    assert pf.forzada_pruebas is True
    assert pf.obra_destino.codigo == OBRA_PRUEBAS
    # El parte de postventa también cae en la obra de pruebas...
    assert getattr(pf, "obra_postventa").codigo == OBRA_PRUEBAS
    # ...pero la partida sale del presupuesto de la obra de postventa real.
    a = pf.acciones[0]
    assert a.accion == "escribir" and a.destino == "postventa", a
    assert a.paride == 70001 and a.partida_cod == OBRA_ORIGEN, a
    assert getattr(pf, "capitulo_postventa")["cod"] == OBRA_ORIGEN


def test_f002_r11_modo_pruebas_marca_las_lineas():
    """R11 · Y lo escrito lleva la marca de pruebas en `tex`, que es lo que
    permite localizarlo y limpiarlo después."""
    cli = ClienteFalso()
    _pipeline(cli, obra_pruebas_forzar=True).ejecutar(
        obra=OBRA, lineas=[linea(registro_id=1)])
    assert [i["tex"] for i in cli.inserts()] == ["PRUEBA-PORC"]


def test_f002_r11_sin_modo_pruebas_va_a_la_obra_real():
    """R11 · Control positivo: apagado el modo pruebas, el destino es la
    obra origen y las líneas van sin marca."""
    cli = ClienteFalso()
    pl = _pipeline(cli, obra_pruebas_forzar=False)
    pf = pl.preflight(obra=OBRA, lineas=[linea(registro_id=3,
                                               es_postventa=True)])
    assert pf.forzada_pruebas is False
    assert pf.obra_destino.codigo == OBRA_ORIGEN
    assert getattr(pf, "obra_postventa").codigo == OBRA_POSTVENTA

    cli2 = ClienteFalso()
    _pipeline(cli2, obra_pruebas_forzar=False).ejecutar(
        obra=OBRA, lineas=[linea(registro_id=1)])
    assert [i["tex"] for i in cli2.inserts()] == [None]


# ------------------- R13 · un solo borrado por línea --------------- #

def _dos_lineas_contra_la_misma():
    """Dos líneas pendientes del MISMO recurso y mes con partidas distintas.
    En la obra normal la partida no distingue (conducta de hoy), así que las
    dos chocan con la única línea previa del parte."""
    cli = ClienteFalso(lineas_parte=[linea_previa(ide=5001)])
    lineas = [
        linea(registro_id=1, porcentaje=0.4, paride=80001,
              partida_cod="CI.1.10"),
        linea(registro_id=2, porcentaje=0.6, paride=80002,
              partida_cod="CI.1.20"),
    ]
    return cli, lineas


def test_f002_r13_las_dos_lineas_chocan_con_la_misma():
    """Premisa del caso: hay una sola línea previa y las dos pendientes
    apuntan a ella. Si esto dejara de ser cierto, el test de abajo pasaría
    por el motivo equivocado."""
    cli, lineas = _dos_lineas_contra_la_misma()
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=lineas)

    assert len(cli.lineas_parte) == 1
    ides = [ls.ide for c in pf.conflictos for ls in c.lineas]
    assert ides == [5001, 5001], ides


def test_f002_r13_borrado_unico_por_ide():
    """R13 · Confirmadas las dos, la línea 5001 se borra UNA vez y
    `borradas` cuenta 1. Emitir dos DELETE del mismo `ide` deja el segundo
    borrando nada y el recuento mintiendo al humano."""
    cli, lineas = _dos_lineas_contra_la_misma()
    claves = {c.clave for c in
              _pipeline(cli).preflight(obra=OBRA, lineas=lineas).conflictos}

    cli2, lineas2 = _dos_lineas_contra_la_misma()
    res = _pipeline(cli2).ejecutar(obra=OBRA, lineas=lineas2,
                                   pisar_claves=claves)

    assert cli2.borrados() == [5001], cli2.borrados()
    assert res.borradas == 1
    assert sorted(e["registro_id"] for e in res.escritas) == [1, 2]


def test_f002_r13_dos_lineas_distintas_se_borran_las_dos():
    """R13 · Control negativo: dos líneas previas DISTINTAS sí se borran las
    dos. La deduplicación es por `ide`, no un tope de uno."""
    cli = ClienteFalso(lineas_parte=[
        linea_previa(ide=5001, horide=5),
        linea_previa(ide=5002, horide=5, fecha_int=20260710),
    ])
    lineas = [linea(registro_id=1)]
    claves = {c.clave for c in
              _pipeline(cli).preflight(obra=OBRA, lineas=lineas).conflictos}

    cli2 = ClienteFalso(lineas_parte=[
        linea_previa(ide=5001, horide=5),
        linea_previa(ide=5002, horide=5, fecha_int=20260710),
    ])
    res = _pipeline(cli2).ejecutar(obra=OBRA, lineas=lineas,
                                   pisar_claves=claves)

    assert sorted(cli2.borrados()) == [5001, 5002]
    assert res.borradas == 2


def test_f002_r13_sin_confirmar_no_se_borra_nada():
    """R13 · Y sin confirmar el pisado no se borra ni se escribe esa línea:
    queda pendiente de confirmación."""
    cli, lineas = _dos_lineas_contra_la_misma()
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=lineas)

    assert cli.borrados() == [] and res.borradas == 0
    assert res.escritas == []
    assert len(res.pendientes_confirmacion) == 2
