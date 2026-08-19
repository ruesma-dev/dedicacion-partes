# tests/test_f002_pipeline.py
"""F-002 · Pipeline de registro, offline (R10, R11, R13, R21, R28, R29, R32).

Lo que solo se ve con el pipeline entero montado: que reejecutar no duplique
(`synckey`), que el modo pruebas desvíe la escritura sin falsear el casado de
la postventa, que una línea previa con OTRA partida no se borre (Regla A),
que dos conflictos que apuntan a la misma línea de Sigrid no la borren dos
veces, qué pasa con una sobrecarga confirmada y sin confirmar, y —lo más
importante de todo— que no se borre nunca sin escribir el sustituto.

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


def test_f002_r13_el_contexto_es_solo_del_mismo_recurso():
    """El `contexto` de un conflicto es informativo, pero informa DE ALGUIEN:
    son las otras líneas mensuales **de ese mismo trabajador**. Colar en él
    las de otro convierte el aviso en una acusación falsa —«además tiene
    estas»— sobre líneas que no son suyas."""
    cli = ClienteFalso(lineas_parte=[
        _una_previa_de_la_misma_partida(),                  # la que se pisa
        linea_previa(ide=5002, hora_codigo="HEGR", horide=9,  # no es M*
                     paride=90001),
        linea_previa(ide=5003, reside=400, hora_codigo="MJEFO",  # otro
                     horide=6, can=0.3, paride=90002),
    ])
    lineas = [linea(registro_id=1),
              linea(registro_id=9, porcentaje=0.5, empleado_ide=12,
                    nombre="Jefe de obra", categoria="Jefe de obra")]
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=lineas)

    pisado = [c for c in pf.conflictos if c.motivo == "pisado"][0]
    assert pisado.recurso_ide == 200
    assert [ls.ide for ls in pisado.lineas] == [5001]
    assert pisado.contexto == [], [ls.ide for ls in pisado.contexto]


def test_f002_r13_el_contexto_si_recoge_otro_codigo_del_mismo_recurso():
    """Control positivo: otra línea `M*` del MISMO trabajador con otro
    código sí entra en el contexto. Es para lo que está."""
    cli = ClienteFalso(lineas_parte=[
        _una_previa_de_la_misma_partida(),
        linea_previa(ide=5002, hora_codigo="MCAP", horide=7, can=0.2,
                     paride=90001),
    ])
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=[linea(registro_id=1)])

    pisado = [c for c in pf.conflictos if c.motivo == "pisado"][0]
    assert [ls.ide for ls in pisado.contexto] == [5002]


# ---------- R28 / R29 · la sobrecarga, en la escritura ------------- #

def _sobrecarga_de_un_recurso():
    """El recurso 200 ya tiene 0,9 en otra partida y le añadimos 0,4."""
    cli = ClienteFalso(lineas_parte=[
        linea_previa(ide=5001, can=0.9, paride=90001, hora_codigo="MCAP",
                     horide=7)])
    return cli, [linea(registro_id=1, porcentaje=0.4)]


def _clave_del_conflicto(cli_lineas) -> str:
    """La clave del único conflicto que produce ese escenario."""
    cli, lineas = cli_lineas
    conflictos = _pipeline(cli).preflight(obra=OBRA, lineas=lineas).conflictos
    assert len(conflictos) == 1, conflictos
    return conflictos[0].clave


def test_f002_r28_sin_confirmar_no_se_escribe():
    """R28 · Una sobrecarga sin confirmar bloquea sus líneas: no se escribe
    ni una. Avisar y escribir igualmente no sería avisar."""
    cli, lineas = _sobrecarga_de_un_recurso()
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=lineas)

    assert cli.inserts() == [] and res.escritas == []
    assert [c.motivo for c in res.pendientes_confirmacion] == ["sobrecarga"]


def test_f002_r28_queda_listada_en_omitidas_con_motivo():
    """R28 · Y queda listada como OMITIDA, con las cifras.

    No es cosmética: `dedicacion-api` solo mira `omitidas` para escribir
    `asignacion.sigrid_estado`. Sin esto, una línea bloqueada por sobrecarga
    se queda en la base con su estado anterior, que miente; con esto queda
    `omitido` con el motivo real, y pasa a `registrado` en cuanto el humano
    confirme y reejecute.
    """
    cli, lineas = _sobrecarga_de_un_recurso()
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=lineas)

    assert [o["registro_id"] for o in res.omitidas] == [1]
    motivo = res.omitidas[0]["motivo"]
    assert motivo.startswith("sobrecarga:"), motivo
    assert "130.00%" in motivo and "90.00%" in motivo, motivo
    assert len(motivo) <= 300, len(motivo)


def test_f002_r28_un_pisado_sin_confirmar_no_va_a_omitidas():
    """R28 · Control: esto NO se hace con los pisados. Un pisado sin
    confirmar es un paso normal del flujo («repite y marca pisar»); una
    sobrecarga es una anomalía entre el cuadrante y Sigrid, y tiene que
    dejar rastro aunque nadie vuelva a ejecutar."""
    cli = ClienteFalso(lineas_parte=[_una_previa_de_la_misma_partida()])
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=[linea(registro_id=1)])

    assert res.omitidas == []
    assert [c.motivo for c in res.pendientes_confirmacion] == ["pisado"]


def test_f002_r29_confirmada_se_escribe_y_no_borra_nada():
    """R29 · Confirmar una sobrecarga escribe la línea y NO borra nada: la
    línea previa de Administración se queda donde está, que es justo lo que
    el humano acaba de aceptar (que convivan y sumen más de 1)."""
    clave = _clave_del_conflicto(_sobrecarga_de_un_recurso())

    cli, lineas = _sobrecarga_de_un_recurso()
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=lineas,
                                  pisar_claves={clave})

    assert [e["registro_id"] for e in res.escritas] == [1]
    assert cli.borrados() == [] and res.borradas == 0
    assert res.omitidas == []
    assert res.pendientes_confirmacion == []


# ---------- R32 · no se borra sin escribir el sustituto ------------ #

def _pisado_y_sobrecarga_mas_otro_trabajador():
    """El recurso 200 tiene un pisado (línea 5001, misma partida) y además
    una sobrecarga (línea 5002, otra partida, 0,9). El empleado 12 no tiene
    ni una cosa ni la otra: está para que quede algo que escribir y el
    pipeline no salga por el atajo de «nada que hacer»."""
    cli = ClienteFalso(lineas_parte=[
        _una_previa_de_la_misma_partida(can=0.5),
        linea_previa(ide=5002, can=0.9, paride=90001, hora_codigo="MCAP",
                     horide=7),
    ])
    lineas = [linea(registro_id=1, porcentaje=0.4),
              linea(registro_id=9, porcentaje=0.5, empleado_ide=12,
                    nombre="Jefe de obra", categoria="Jefe de obra")]
    return cli, lineas


def test_f002_r32_premisa_hay_pisado_y_sobrecarga_del_mismo_recurso():
    """Premisa del caso: si dejara de haber los dos conflictos, el test de
    abajo pasaría por el motivo equivocado."""
    cli, lineas = _pisado_y_sobrecarga_mas_otro_trabajador()
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=lineas)

    assert [c.motivo for c in pf.conflictos] == ["pisado", "sobrecarga"]
    assert pf.conflictos[0].lineas[0].ide == 5001


def test_f002_r32_no_se_borra_si_no_se_escribe():
    """R32 · EL requisito que impide perder un apunte de Administración.

    El humano confirma el pisado pero NO la sobrecarga. El borrado se emite
    por conflicto confirmado y la escritura se bloquea por registro, así que
    sin esta guarda se borraría la línea 5001 **sin escribir la que la
    sustituye**: pérdida de dato neta, y encima silenciosa.
    """
    cli0, lineas0 = _pisado_y_sobrecarga_mas_otro_trabajador()
    clave_pisado = _pipeline(cli0).preflight(
        obra=OBRA, lineas=lineas0).conflictos[0].clave

    cli, lineas = _pisado_y_sobrecarga_mas_otro_trabajador()
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=lineas,
                                  pisar_claves={clave_pisado})

    assert cli.borrados() == [], cli.borrados()
    assert res.borradas == 0
    # …y lo que no estaba bloqueado sí se escribe: la guarda es por
    # conflicto, no un «ante la duda, no hagas nada».
    assert [e["registro_id"] for e in res.escritas] == [9]


def test_f002_r32_confirmando_las_dos_si_se_borra():
    """R32 · Control positivo: confirmadas las dos, el sustituto se escribe
    y entonces sí se borra la línea vieja. La guarda no es «no borres
    nunca»: es «no borres sin escribir»."""
    cli0, lineas0 = _pisado_y_sobrecarga_mas_otro_trabajador()
    claves = {c.clave for c in
              _pipeline(cli0).preflight(obra=OBRA, lineas=lineas0).conflictos}

    cli, lineas = _pisado_y_sobrecarga_mas_otro_trabajador()
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=lineas,
                                  pisar_claves=claves)

    assert cli.borrados() == [5001]
    assert res.borradas == 1
    assert sorted(e["registro_id"] for e in res.escritas) == [1, 9]
