# tests/test_f002_pipeline.py
"""F-002 · Pipeline de registro, offline (R10, R11, R13, R21).

Cuatro cosas que solo se ven con el pipeline entero montado: que reejecutar
no duplique (`synckey`), que el modo pruebas desvíe la escritura sin falsear
el casado de la postventa, que una línea previa con OTRA partida no se borre
(Regla A), y que dos conflictos que apuntan a la misma línea de Sigrid no la
borren dos veces.

Sin red ni BBDD: el pipeline solo habla con el `ClienteFalso` de
`conftest.py`, que se limita a acumular las sentencias que se le mandan.
"""
from __future__ import annotations

from dataclasses import replace

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


# ------ R21 · una línea de otra partida ni choca ni se borra ------- #

def _dos_partidas_distintas():
    """Dos líneas pendientes del MISMO recurso y mes con partidas distintas,
    y una línea previa sin partida (`paride = 0`), de las que mete
    Administración a mano.

    Era el escenario de R13 —cuando la partida no entraba en la identidad,
    las dos chocaban con ella—. Con la Regla A ya no choca ninguna, y de ahí
    sale el control de R21.

    Las cantidades suman 0,9 a propósito: aquí se mira la identidad, y una
    sobrecarga metería por medio un conflicto de otro tipo. El mismo
    escenario pasado de 1 está en `test_f002_capacidad.py` (R25)."""
    cli = ClienteFalso(lineas_parte=[linea_previa(ide=5001, paride=0,
                                                  can=0.2)])
    lineas = [
        linea(registro_id=1, porcentaje=0.3, paride=80001,
              partida_cod="CI.1.10"),
        linea(registro_id=2, porcentaje=0.4, paride=80002,
              partida_cod="CI.1.20"),
    ]
    return cli, lineas


def test_f002_r21_otra_partida_no_produce_conflicto_en_el_pipeline():
    """R21 · Visto desde el pipeline entero: la línea previa tiene otra
    partida, así que no hay nada que confirmar y las dos se escriben."""
    cli, lineas = _dos_partidas_distintas()
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=lineas)

    assert len(cli.lineas_parte) == 1
    assert pf.conflictos == [], pf.conflictos


def test_f002_r21_no_se_borra_la_linea_de_otra_partida():
    """R21 · Y lo que importa de verdad: ese apunte de Administración NO se
    borra. Antes de la Regla A, confirmar el pisado lo borraba y escribía la
    nuestra encima."""
    cli, lineas = _dos_partidas_distintas()
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=lineas)

    assert cli.borrados() == [] and res.borradas == 0
    assert sorted(e["registro_id"] for e in res.escritas) == [1, 2]
    assert res.pendientes_confirmacion == []


# ------------------- R13 · un solo borrado por línea --------------- #

def _una_previa_de_la_misma_partida(**kw):
    """Una línea previa que SÍ es la misma línea que la de `registro_id=1`:
    mismo recurso, mismo código de hora y la misma partida (`80001`, la que
    el automático le resuelve al encargado)."""
    return linea_previa(**{"ide": 5001, "paride": 80001, **kw})


def test_f002_r13_borrado_unico_por_ide():
    """R13 · Si dos conflictos confirmados apuntan a la MISMA línea de
    Sigrid, solo sale un `DELETE` y `borradas` cuenta 1.

    El escenario original de este test —dos pendientes con partidas
    distintas chocando con la misma línea previa— **ya no es alcanzable**
    con la Regla A: una línea existente casa, como mucho, con una identidad.
    La salvaguarda se queda igualmente, y para probarla hay que inyectar el
    par de conflictos a mano. Emitir dos `DELETE` del mismo `ide` deja el
    segundo borrando nada y el recuento mintiendo al humano.
    """
    clave = _pipeline(
        ClienteFalso(lineas_parte=[_una_previa_de_la_misma_partida()])
    ).preflight(obra=OBRA, lineas=[linea(registro_id=1)]).conflictos[0].clave

    cli = ClienteFalso(lineas_parte=[_una_previa_de_la_misma_partida()])
    pl = _pipeline(cli)
    original = pl.preflight

    def con_conflicto_gemelo(**kw):
        pf = original(**kw)
        c = pf.conflictos[0]
        pf.conflictos.append(replace(c, clave=f"{c.clave}|gemelo"))
        return pf

    pl.preflight = con_conflicto_gemelo
    res = pl.ejecutar(obra=OBRA, lineas=[linea(registro_id=1)],
                      pisar_claves={clave, f"{clave}|gemelo"})

    assert cli.borrados() == [5001], cli.borrados()
    assert res.borradas == 1
    assert [e["registro_id"] for e in res.escritas] == [1]


def test_f002_r13_dos_lineas_distintas_se_borran_las_dos():
    """R13 · Control negativo: dos líneas previas DISTINTAS de la misma
    identidad (mismo recurso, código y partida, en dos días del mes) sí se
    borran las dos. La deduplicación es por `ide`, no un tope de uno."""
    def previas():
        return [_una_previa_de_la_misma_partida(),
                _una_previa_de_la_misma_partida(ide=5002,
                                                fecha_int=20260710)]

    lineas = [linea(registro_id=1)]
    claves = {c.clave for c in
              _pipeline(ClienteFalso(lineas_parte=previas()))
              .preflight(obra=OBRA, lineas=lineas).conflictos}

    cli = ClienteFalso(lineas_parte=previas())
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=lineas,
                                  pisar_claves=claves)

    assert sorted(cli.borrados()) == [5001, 5002]
    assert res.borradas == 2


def test_f002_r13_sin_confirmar_no_se_borra_nada():
    """R13 · Y sin confirmar el pisado no se borra ni se escribe esa línea:
    queda pendiente de confirmación."""
    cli = ClienteFalso(lineas_parte=[_una_previa_de_la_misma_partida()])
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=[linea(registro_id=1)])

    assert cli.borrados() == [] and res.borradas == 0
    assert res.escritas == []
    assert len(res.pendientes_confirmacion) == 1
