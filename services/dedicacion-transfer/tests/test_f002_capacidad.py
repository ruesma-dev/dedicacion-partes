# tests/test_f002_capacidad.py
"""F-002 · Regla B, la capacidad de un parte (R23-R27, R30, R31, R33).

La regla está en `docs/ARCHITECTURE.md#regla-capacidad`: por trabajador y
parte, la suma de `can` de sus líneas `M*` no puede pasar de 1. Es la regla
que el repositorio NO tenía, y la que caza el efecto secundario de la Regla
A: al dejar de chocar las líneas con otra partida, un parte puede acabar con
dos líneas donde antes había una sustitución.

Lo que aquí se prueba es la DETECCIÓN (la función pura y el conflicto que
sale del preflight). Que sin confirmar no se escriba, y que confirmar no
borre nada, es R28/R29 y vive en `test_f002_pipeline.py`.

Sin red ni BBDD.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.reglas_porcentajes import (
    EPSILON_CAPACIDAD, LIMITE_CAPACIDAD, MOTIVO_SOBRECARGA,
    PREFIJO_CLAVE_SOBRECARGA, clave_conflicto, clave_sobrecarga,
    es_linea_mensual, evaluar_capacidad,
)
from domain.models.registro_models import AccionLinea, ObraEntrada

from tests.conftest import (
    OBRA_ORIGEN, ClienteFalso, SettingsFalso, linea, linea_previa,
)

OBRA = ObraEntrada(codigo=OBRA_ORIGEN)


def _pipeline(cli: ClienteFalso, **ajustes) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli, settings=SettingsFalso(**ajustes))


def accion(**kw) -> AccionLinea:
    """Acción de escritura del encargado (recurso 200, MENC) en julio."""
    datos = dict(registro_id=1, accion="escribir", ano=2026, mes=7,
                 fecha_int=20260731, recurso_ide=200, hora_ide=5,
                 hora_codigo="MENC", can=0.4, pre=9000.0, tot=3600.0,
                 destino="obra", paride=80001)
    datos.update(kw)
    return AccionLinea(**datos)


# ------------------------ R23 · qué se suma ------------------------ #

def test_f002_r23_suma_existentes_mas_nuevas():
    """R23 · La jornada del mes es lo que ya hay en el parte más lo que
    vamos a añadir. 0,7 + 0,4 = 1,1: se pasa."""
    cap = evaluar_capacidad(
        [linea_previa(ide=5001, can=0.7, paride=90001)],
        [accion(can=0.4)], mias=set(), pisadas=set())

    assert cap.existente == pytest.approx(0.7)
    assert cap.nueva == pytest.approx(0.4)
    assert cap.total == pytest.approx(1.1)
    assert cap.exceso == pytest.approx(0.1)
    assert cap.sobrecarga is True
    assert [ls.ide for ls in cap.contadas] == [5001]


def test_f002_r23_la_linea_pisada_no_se_cuenta_dos_veces():
    """R23 · Si nuestra línea sustituye a una existente, la existente sale
    del cómputo: no van a convivir. Contarla sería inventar una sobrecarga
    en el caso MÁS común de todos —reescribir lo que ya pusimos ayer—."""
    previa = linea_previa(ide=5001, can=0.7, paride=80001)
    cap = evaluar_capacidad([previa], [accion(can=0.4)],
                            mias=set(), pisadas={5001})

    assert cap.existente == pytest.approx(0.0)
    assert cap.total == pytest.approx(0.4)
    assert cap.sobrecarga is False
    assert cap.contadas == ()


def test_f002_r23_las_mias_no_distorsionan():
    """R23 · Una línea con `synckey` de esta misma ejecución tampoco cuenta:
    ya está representada por la acción pendiente que la reescribe."""
    previa = linea_previa(ide=5001, can=0.7, paride=90001,
                          synckey="porcentajes:1")
    cap = evaluar_capacidad([previa], [accion(can=0.4)],
                            mias={"porcentajes:1"}, pisadas=set())

    assert cap.existente == pytest.approx(0.0)
    assert cap.sobrecarga is False


def test_f002_r23_una_ya_registrada_cuenta_una_vez():
    """R23 · Y una línea nuestra de una ejecución ANTERIOR sí cuenta como
    ocupación, y solo una vez: su acción ya no está entre las pendientes
    (el paso 6 la marcó `ya_registrado`), así que no entra por el otro
    lado."""
    vieja = linea_previa(ide=5001, can=0.7, paride=90001,
                         synckey="porcentajes:99")
    cap = evaluar_capacidad([vieja], [accion(can=0.4)],
                            mias={"porcentajes:1"}, pisadas=set())

    assert cap.existente == pytest.approx(0.7)
    assert cap.total == pytest.approx(1.1)
    assert [ls.ide for ls in cap.contadas] == [5001]


def test_f002_r23_sin_nada_previo_solo_cuentan_las_nuestras():
    """R23 · Control: un parte vacío no aporta ocupación."""
    cap = evaluar_capacidad([], [accion(can=0.4), accion(registro_id=2,
                                                         can=0.5)],
                            mias=set(), pisadas=set())
    assert cap.existente == 0.0 and cap.nueva == pytest.approx(0.9)
    assert cap.sobrecarga is False


def test_f002_r23_un_can_a_none_vale_cero():
    """R23 · `can` sin valor no revienta la suma: en Sigrid es 0, como en el
    resto del módulo."""
    cap = evaluar_capacidad([linea_previa(ide=5001, can=None, paride=90001)],
                            [accion(can=None)], mias=set(), pisadas=set())
    assert cap.total == 0.0 and cap.sobrecarga is False


# ------------------ R24 · qué líneas son mensuales ----------------- #

@pytest.mark.parametrize("cod", ("MENC", "MCAP", "MJEFO", "menc", "M"))
def test_f002_r24_cuenta_cualquier_codigo_mensual(cod):
    """R24 · El límite es la JORNADA de la persona, no un concepto: cuenta
    cualquier código que empiece por M, no solo el que vamos a escribir."""
    ls = linea_previa(ide=5001, hora_codigo=cod, horide=7, can=0.7,
                      paride=90001)
    assert es_linea_mensual(ls) is True

    cap = evaluar_capacidad([ls], [accion(can=0.4)], mias=set(),
                            pisadas=set())
    assert cap.sobrecarga is True, cod


@pytest.mark.parametrize("cod", ("HLPE", "HEGR", "", None))
def test_f002_r24_no_cuenta_las_no_mensuales(cod):
    """R24 · Y las horas de convenio no cuentan: van en otra escala (horas,
    no fracción de mes) y sumarlas no significaría nada."""
    ls = linea_previa(ide=5001, hora_codigo=cod, horide=9, can=0.7,
                      paride=90001)
    assert es_linea_mensual(ls) is False

    cap = evaluar_capacidad([ls], [accion(can=0.4)], mias=set(),
                            pisadas=set())
    assert cap.existente == 0.0 and cap.sobrecarga is False, cod


# --------------- R25 · pasarse emite conflicto con cifras ---------- #

def _parte_con_sobrecarga():
    """Recurso 200 con 0,7 ya puesto en otra partida y 0,4 pendiente."""
    cli = ClienteFalso(lineas_parte=[
        linea_previa(ide=5001, can=0.7, paride=90001, hora_codigo="MCAP",
                     horide=7)])
    return cli, [linea(registro_id=1, porcentaje=0.4)]


def test_f002_r25_sobrecarga_emite_conflicto():
    """R25 · El preflight lo enseña como un conflicto más: es el mecanismo
    que ya existe para «esto no lo decido yo»."""
    cli, lineas = _parte_con_sobrecarga()
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=lineas)

    assert len(pf.conflictos) == 1, pf.conflictos
    c = pf.conflictos[0]
    assert c.motivo == "sobrecarga"
    assert c.registros == [1]
    assert c.lineas == []               # una sobrecarga no borra nada


def test_f002_r25_con_su_detalle_numerico():
    """R25 · Con las cuatro cifras que justifican el aviso: qué había, qué
    se añade, cuánto suma y cuánto se pasa. Sin ellas el humano confirma a
    ciegas."""
    cli, lineas = _parte_con_sobrecarga()
    c = _pipeline(cli).preflight(obra=OBRA, lineas=lineas).conflictos[0]

    assert c.suma_existente == pytest.approx(0.7)
    assert c.nueva_can == pytest.approx(0.4)
    assert c.suma_total == pytest.approx(1.1)
    assert c.exceso == pytest.approx(0.1)
    assert [ls.ide for ls in c.contexto] == [5001]


def test_f002_r25_las_cifras_se_redondean_a_cuatro_decimales():
    """R25 · Las cifras del conflicto van redondeadas a 4 decimales, la
    misma escala en la que se escribe `can` (P3). Sin el redondeo, el humano
    lee «se pasa en 0.023456000000000045», que es ruido de coma flotante
    disfrazado de precisión."""
    cli = ClienteFalso(lineas_parte=[
        linea_previa(ide=5001, can=0.123456, paride=90001)])
    c = _pipeline(cli).preflight(
        obra=OBRA,
        lineas=[linea(registro_id=1, porcentaje=0.9)]).conflictos[0]

    assert c.suma_existente == 0.1235
    assert c.suma_total == 1.0235
    assert c.exceso == 0.0235


def test_f002_r25_el_escenario_viejo_de_r13_ahora_es_una_sobrecarga():
    """R25 · La otra cara de la Regla A, y la razón por la que las dos
    reglas van en la misma feature.

    Dos líneas nuestras con partidas distintas (0,4 y 0,6) y una línea
    previa del mismo recurso sin partida (1,0). Antes: las dos chocaban con
    ella y confirmar el pisado la BORRABA. Ahora: no choca ninguna, así que
    no se borra nada… y la suma se va a 2,0. Sin la Regla B eso se
    escribiría en silencio y el trabajador acabaría con el 200 % del mes.
    """
    cli = ClienteFalso(lineas_parte=[linea_previa(ide=5001, can=1.0,
                                                  paride=0)])
    lineas = [linea(registro_id=1, porcentaje=0.4, paride=80001,
                    partida_cod="CI.1.10"),
              linea(registro_id=2, porcentaje=0.6, paride=80002,
                    partida_cod="CI.1.20")]
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=lineas)

    assert [c.motivo for c in pf.conflictos] == ["sobrecarga"]
    c = pf.conflictos[0]
    assert c.lineas == []                       # no se borra nada
    assert sorted(c.registros) == [1, 2]        # las dos quedan retenidas
    assert c.suma_total == pytest.approx(2.0)


# ---------------- R26 · exactamente 1 no es sobrecarga ------------- #

def test_f002_r26_justo_uno_no_es_sobrecarga():
    """R26 · Una jornada de exactamente 1,0 repartida entre varias partidas
    es LEGÍTIMA y se escribe sin preguntar. Es el caso normal de un jefe de
    obra con dos obras, y avisar aquí convertiría la regla en ruido."""
    cap = evaluar_capacidad(
        [linea_previa(ide=5001, can=0.6, paride=90001)],
        [accion(can=0.4)], mias=set(), pisadas=set())

    assert cap.total == pytest.approx(1.0)
    assert cap.sobrecarga is False


def test_f002_r26_el_limite_es_uno():
    """R26 · Control del propio límite: pasarse de 1 en más que la
    tolerancia sí avisa."""
    assert LIMITE_CAPACIDAD == 1.0
    cap = evaluar_capacidad(
        [linea_previa(ide=5001, can=0.6, paride=90001)],
        [accion(can=0.4 + 10 * EPSILON_CAPACIDAD)],
        mias=set(), pisadas=set())
    assert cap.sobrecarga is True


@pytest.mark.parametrize("extra, avisa", [
    (EPSILON_CAPACIDAD / 2, False),     # dentro de la tolerancia
    (EPSILON_CAPACIDAD * 2, True),      # fuera
])
def test_f002_r26_la_tolerancia_decide_el_borde(extra, avisa):
    """R26 · El borde exacto: la tolerancia absorbe el último decimal, no
    una desviación de negocio."""
    cap = evaluar_capacidad([], [accion(can=1.0 + extra)],
                            mias=set(), pisadas=set())
    assert cap.sobrecarga is avisa, (extra, cap)


def test_f002_r26_el_borde_exacto_de_la_tolerancia_no_existe():
    """R26 · Documenta por qué la comparación es `>` y no `>=`, y por qué da
    igual: en coma flotante de doble precisión **no existe** un caso con
    `exceso == EPSILON_CAPACIDAD`.

    Para un `total` entre 1 y 2 la resta `total - 1.0` es exacta y solo
    puede dar múltiplos del ULP de esa franja (2⁻⁵², ~2,2e-16); el `double`
    más cercano a 0,00005 no lo es. El `>=` es, por tanto, una mutación
    equivalente, y esto lo deja escrito en un test en vez de en un comentario
    que nadie comprueba.
    """
    alcanzables = {(1.0 + k * 2.0 ** -52) - 1.0 for k in range(1, 2000)}
    assert EPSILON_CAPACIDAD not in alcanzables
    assert (1.0 + EPSILON_CAPACIDAD) - 1.0 != EPSILON_CAPACIDAD


def test_f002_r26_la_tolerancia_es_la_del_cuadrante():
    """R26 · Y no es un número redondo elegido a ojo: es la MISMA épsilon
    que usa el cuadrante en `dedicacion-api/domain/estados.py`, convertida
    de la escala 0-100 a la 0-1 de Sigrid.

    Se lee del fichero de la API a propósito, aunque sea otro servicio: si
    alguien la cambia allí, este test cae y obliga a decidir las dos a la
    vez. Un cuadrante que la API da por `OK` no puede convertirse aquí en
    una sobrecarga fantasma."""
    raiz = Path(__file__).resolve().parents[3]
    estados = (raiz / "services" / "dedicacion-api" / "domain" /
               "estados.py").read_text(encoding="utf-8")
    assert '_EPSILON = Decimal("0.005")' in estados, (
        "la épsilon del cuadrante ha cambiado: hay que cambiar "
        "EPSILON_CAPACIDAD con ella (ARCHITECTURE.md#regla-capacidad)")
    assert EPSILON_CAPACIDAD == 0.005 / 100


# ------------- R27 · la sobrecarga no se confunde con un pisado ---- #

def test_f002_r27_la_clave_de_sobrecarga_no_colisiona():
    """R27 · Confirmar un pisado no puede confirmar una sobrecarga del mismo
    recurso, ni al revés: son dos decisiones distintas del humano."""
    a = accion()
    assert clave_sobrecarga(a) != clave_conflicto(a)
    assert clave_sobrecarga(a).startswith(PREFIJO_CLAVE_SOBRECARGA)
    assert not clave_conflicto(a).startswith(PREFIJO_CLAVE_SOBRECARGA)


def test_f002_r27_la_clave_de_sobrecarga_es_por_recurso_y_periodo():
    """R27 · Y es una sola por trabajador y parte, sea cual sea la partida:
    la sobrecarga la provoca el conjunto, no una línea concreta."""
    assert clave_sobrecarga(accion(paride=80001)) == \
        clave_sobrecarga(accion(paride=80002))
    assert clave_sobrecarga(accion(recurso_ide=201)) != \
        clave_sobrecarga(accion(recurso_ide=200))
    assert clave_sobrecarga(accion(mes=1)) != clave_sobrecarga(accion(mes=7))


def test_f002_r27_el_motivo_distingue():
    """R27 · Y el conflicto lleva un campo propio que dice de qué tipo es,
    para que un cliente pueda tratarlos distinto sin adivinar por la forma."""
    cli, lineas = _parte_con_sobrecarga()
    c = _pipeline(cli).preflight(obra=OBRA, lineas=lineas).conflictos[0]
    assert c.motivo == "sobrecarga"

    cli2 = ClienteFalso(lineas_parte=[linea_previa(ide=5001, can=0.1,
                                                   paride=80001)])
    c2 = _pipeline(cli2).preflight(
        obra=OBRA, lineas=[linea(registro_id=1)]).conflictos[0]
    assert c2.motivo == "pisado"


def test_f002_r27_el_motivo_es_legible_y_corto():
    """R27 · El texto de la omisión cabe en los 300 caracteres a los que
    `dedicacion-api` recorta `asignacion.sigrid_motivo`, y dice las cuatro
    cifras. Un motivo truncado a mitad de frase no informa de nada."""
    texto = MOTIVO_SOBRECARGA.format(total=1.1, existente=0.7, n=1,
                                     nueva=0.4)
    assert len(texto) <= 300, len(texto)
    assert "110.00%" in texto and "70.00%" in texto and "40.00%" in texto


# ---------- R30 · pisado y sobrecarga a la vez, en ese orden ------- #

def _parte_con_pisado_y_sobrecarga():
    """El recurso 200 tiene DOS líneas previas: una de la misma partida que
    la nuestra (se pisa) y otra de otra partida con 0,9 (no se pisa, y por
    eso hace que la suma se vaya a 1,3)."""
    cli = ClienteFalso(lineas_parte=[
        linea_previa(ide=5001, can=0.5, paride=80001),
        linea_previa(ide=5002, can=0.9, paride=90001, hora_codigo="MCAP",
                     horide=7),
    ])
    return cli, [linea(registro_id=1, porcentaje=0.4)]


def test_f002_r30_pisado_y_sobrecarga_a_la_vez():
    """R30 · Un mismo recurso puede tener las dos cosas, y se le enseñan las
    dos: son decisiones independientes."""
    cli, lineas = _parte_con_pisado_y_sobrecarga()
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=lineas)

    motivos = [c.motivo for c in pf.conflictos]
    assert motivos == ["pisado", "sobrecarga"], motivos


def test_f002_r30_el_orden_es_pisado_primero():
    """R30 · Y en ese orden: el pisado explica qué se borra, y la cifra de
    la sobrecarga ya presupone que el pisado ocurre. Al revés, el humano lee
    una suma que no cuadra con lo que tiene delante."""
    cli, lineas = _parte_con_pisado_y_sobrecarga()
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=lineas)

    assert pf.conflictos[0].motivo == "pisado"
    assert pf.conflictos[0].lineas[0].ide == 5001
    assert pf.conflictos[1].motivo == "sobrecarga"


# ---- R31 · la suma supone confirmados todos los pisados propuestos - #

def test_f002_r31_la_suma_supone_los_pisados_confirmados():
    """R31 · La línea 5001 se va a pisar, así que su 0,5 NO cuenta: quedan
    0,9 + 0,4 = 1,3. Es la única hipótesis segura: cualquier otra
    combinación escribe estrictamente menos, porque denegar un pisado
    bloquea la línea pendiente y deja la existente intacta."""
    cli, lineas = _parte_con_pisado_y_sobrecarga()
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=lineas)

    sobre = pf.conflictos[1]
    assert sobre.suma_existente == pytest.approx(0.9)
    assert sobre.suma_total == pytest.approx(1.3)
    assert [ls.ide for ls in sobre.contexto] == [5002]


def test_f002_r31_sin_la_hipotesis_habria_falso_positivo():
    """R31 · Control: si el pisado NO se descontara, la suma sería 1,8. La
    diferencia entre las dos cifras es exactamente el `can` de la pisada, y
    es la razón por la que `evaluar_capacidad` recibe `pisadas`."""
    previas = [linea_previa(ide=5001, can=0.5, paride=80001),
               linea_previa(ide=5002, can=0.9, paride=90001)]
    con = evaluar_capacidad(previas, [accion(can=0.4)], mias=set(),
                            pisadas={5001})
    sin = evaluar_capacidad(previas, [accion(can=0.4)], mias=set(),
                            pisadas=set())

    assert con.total == pytest.approx(1.3)
    assert sin.total == pytest.approx(1.8)


# ---------------- R33 · el contrato no se rompe -------------------- #

def test_f002_r33_el_conflicto_serializa_los_campos_de_siempre():
    """R33 · Un cliente que ignore los campos nuevos sigue funcionando: los
    de siempre conservan nombre, tipo y semántica, y los nuevos tienen
    valor por defecto."""
    from dataclasses import asdict

    cli, lineas = _parte_con_sobrecarga()
    c = _pipeline(cli).preflight(obra=OBRA, lineas=lineas).conflictos[0]
    d = asdict(c)

    for campo in ("clave", "recurso_ide", "nombre", "ano", "mes",
                  "parte_cod", "horide", "hora_codigo", "lineas",
                  "contexto", "nuevas", "registros"):
        assert campo in d, campo
    assert isinstance(d["clave"], str) and isinstance(d["registros"], list)
    assert d["nuevas"][0]["can"] == pytest.approx(0.4)


def test_f002_r33_los_campos_nuevos_tienen_defecto():
    """R33 · Y un `Conflicto` construido como antes de la feature —sin los
    campos nuevos— sigue siendo válido y se comporta como un pisado."""
    from domain.models.registro_models import Conflicto

    c = Conflicto(clave="200|202607|5|80001", recurso_ide=200, nombre=None,
                  ano=2026, mes=7, parte_cod="PT26/00251")
    assert c.motivo == "pisado"
    assert c.suma_existente == 0.0 and c.suma_total == 0.0
    assert c.exceso == 0.0
