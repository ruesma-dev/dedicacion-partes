# tests/test_f013_sin_partida.py
"""F-013 · Una línea sin partida no se escribe en silencio (R1-R6).

La regla está en `docs/ARCHITECTURE.md#regla-sin-partida`: si el casado de
partida de la obra normal falla, la línea **no se escribe sin confirmación
explícita**. Hasta F-013 se escribía igual, con `paride = 0` y un aviso
informativo que nadie tenía que atender: en el preflight real del periodo
2026-07 eso eran 2.132,28 € de una jefa de obra colgando de la obra sin
imputar a ninguna partida.

`R1`-`R6` son los criterios `acceptance` de F-013 en
`harness/features.json`, en su orden (la feature es `sdd: false`, así que
no hay `requirements.md` al que trazar):

  R1 · conflicto con motivo propio, distinguible de los otros dos
  R2 · sin confirmar: no se escribe y queda omitida con su motivo
  R3 · con confirmación: se escribe con `paride = 0`
  R4 · el contrato con el front no cambia (degradación elegante)
  R5 · tests offline, con las fixtures de `conftest.py`
  R6 · la regla vive en la fuente única, con su procedencia

Sin red ni BBDD: el pipeline solo habla con el `ClienteFalso` de
`conftest.py`.
"""
from __future__ import annotations

import re
from dataclasses import asdict
from pathlib import Path

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.reglas_porcentajes import (
    AVISO_SIN_PARTIDA,
    MOTIVO_SIN_PARTIDA,
    PREFIJO_CLAVE_SIN_PARTIDA,
    PREFIJO_CLAVE_SOBRECARGA,
    clave_conflicto,
    clave_sin_partida,
    clave_sobrecarga,
    sin_partida,
)
from domain.models.registro_models import AccionLinea, ObraEntrada

from tests.conftest import (
    OBRA_ORIGEN,
    ClienteFalso,
    SettingsFalso,
    linea,
    linea_previa,
)

OBRA = ObraEntrada(codigo=OBRA_ORIGEN)

RAIZ = Path(__file__).resolve().parents[3]
ARQUITECTURA = RAIZ / "docs" / "ARCHITECTURE.md"


def _pipeline(cli: ClienteFalso, **ajustes) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli, settings=SettingsFalso(**ajustes))


def linea_que_no_casa(**kw):
    """Línea de obra normal cuyo casado de partida falla.

    El presupuesto de la obra origen de `conftest.py` solo tiene
    `CI.1.10 ENCARGADO (ACUNA)` y `CI.1.20 JEFE DE OBRA`: ni la categoría
    ni el nombre de esta línea casan con ninguna de las dos. Es el caso real
    de julio (una jefa de obra sin partida en su presupuesto), no un caso
    inventado para el test.
    """
    datos = dict(registro_id=1, porcentaje=0.4, empleado_ide=12,
                 nombre="Arriaza Garcia, Raquel", categoria="Delineante")
    datos.update(kw)
    return linea(**datos)


def accion(**kw) -> AccionLinea:
    """Acción de escritura del jefe de obra (recurso 400, MJEFO)."""
    datos = dict(registro_id=1, accion="escribir", ano=2026, mes=7,
                 fecha_int=20260731, recurso_ide=400, hora_ide=6,
                 hora_codigo="MJEFO", can=0.385, pre=11000.0, tot=4235.0,
                 destino="obra", paride=0)
    datos.update(kw)
    return AccionLinea(**datos)


# ---------------- premisa: el escenario es el que creemos ---------- #

def test_f013_premisa_la_linea_no_casa_ninguna_partida():
    """Premisa del fichero entero: si esta línea empezara a casar partida,
    todos los tests de abajo pasarían por el motivo equivocado."""
    cli = ClienteFalso()
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=[linea_que_no_casa()])

    a = pf.acciones[0]
    assert a.accion == "escribir" and a.paride == 0, a
    assert a.partida_cod is None and a.partida_metodo is None


def test_f013_premisa_una_linea_que_si_casa_no_molesta():
    """Control positivo del escenario: la línea por defecto de `conftest`
    (Encargado / Acuña) SÍ casa, y por tanto no puede emitir ningún aviso.
    Sin este control, un pipeline que avisara de TODAS las líneas pasaría
    los tests de R1 igual de bien."""
    cli = ClienteFalso()
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=[linea(registro_id=1)])

    assert pf.acciones[0].paride == 80001
    assert pf.conflictos == []


# ------- R1 · conflicto con motivo propio, distinguible ------------ #

def test_f013_r1_una_linea_sin_partida_emite_conflicto():
    """R1 · El casado fallido deja de ser un aviso informativo y pasa a ser
    un conflicto: el mecanismo que el repositorio ya tiene para «esto no lo
    decido yo». Avisar y escribir igualmente no era avisar."""
    cli = ClienteFalso()
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=[linea_que_no_casa()])

    assert len(pf.conflictos) == 1, pf.conflictos
    c = pf.conflictos[0]
    assert c.motivo == "sin_partida"
    assert c.registros == [1]
    assert c.lineas == []           # no borra nada: no sustituye a nadie
    assert c.recurso_ide == 400 and c.hora_codigo == "MJEFO"
    assert c.nuevas[0]["can"] == pytest.approx(0.4)


def test_f013_r1_el_motivo_distingue_de_los_otros_dos():
    """R1 · Un cliente tiene que poder tratarlo distinto sin adivinar por la
    forma: los tres motivos son valores distintos del mismo campo."""
    cli = ClienteFalso()
    c = _pipeline(cli).preflight(
        obra=OBRA, lineas=[linea_que_no_casa()]).conflictos[0]
    assert c.motivo not in ("pisado", "sobrecarga")


def test_f013_r1_la_clave_no_colisiona_con_las_otras_dos():
    """R1 · Y confirmar una cosa no puede confirmar otra: son tres
    decisiones distintas del humano sobre la misma línea."""
    a = accion()
    assert clave_sin_partida(a) != clave_conflicto(a)
    assert clave_sin_partida(a) != clave_sobrecarga(a)
    assert clave_sin_partida(a).startswith(PREFIJO_CLAVE_SIN_PARTIDA)
    assert not clave_sin_partida(a).startswith(PREFIJO_CLAVE_SOBRECARGA)
    assert not clave_conflicto(a).startswith(PREFIJO_CLAVE_SIN_PARTIDA)


def test_f013_r1_la_clave_es_por_linea_y_no_por_trabajador():
    """R1 · A diferencia de la sobrecarga —que es del CONJUNTO de líneas del
    trabajador—, que el casado falle es propiedad de UNA línea: su categoría
    y su nombre. Si la clave agrupara, confirmar una arrastraría a otra que
    el humano no ha mirado."""
    assert clave_sin_partida(accion(registro_id=1)) != \
        clave_sin_partida(accion(registro_id=2))
    assert clave_sin_partida(accion(recurso_ide=200)) == \
        clave_sin_partida(accion(recurso_ide=400))


def test_f013_r1_dos_lineas_sin_partida_son_dos_conflictos():
    """R1 · Y el pipeline las publica por separado, con su clave cada una."""
    cli = ClienteFalso()
    lineas = [linea_que_no_casa(registro_id=1),
              linea_que_no_casa(registro_id=2, empleado_ide=10,
                                nombre="Otro Sin Casar", categoria="Peon")]
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=lineas)

    sinp = [c for c in pf.conflictos if c.motivo == "sin_partida"]
    assert [c.registros for c in sinp] == [[1], [2]], pf.conflictos
    assert len({c.clave for c in sinp}) == 2


def test_f013_r1_el_predicado_solo_mira_lo_que_se_escribe():
    """R1 · `sin_partida` es una función pura sobre la acción: cae si —y solo
    si— la línea se va a escribir con `paride` a 0, que es exactamente lo
    que acabaría en `hmores.paride`. Una acción omitida no se escribe, así
    que no hay nada que confirmar."""
    assert sin_partida(accion(paride=0)) is True
    assert sin_partida(accion(paride=80001)) is False
    assert sin_partida(accion(paride=None)) is True
    assert sin_partida(accion(accion="omitir", paride=0)) is False
    assert sin_partida(accion(accion="ya_registrado", paride=0)) is False


def test_f013_r1_tambien_avisa_con_el_parte_por_crear():
    """R1 · El aviso no depende de que el parte exista: no habla de lo que
    ya hay en Sigrid, sino de dónde se imputa lo que vamos a escribir. Los
    conflictos de pisado sí se saltan el parte nuevo, y copiar esa guarda
    aquí habría dejado sin vigilar justo el mes que se registra primero."""
    cli = ClienteFalso(parte_existe=False)
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=[linea_que_no_casa()])

    assert [c.motivo for c in pf.conflictos] == ["sin_partida"]


def test_f013_r1_el_aviso_de_la_accion_ya_no_promete_que_se_escribe():
    """R1 · El texto que ve el humano en la tabla del preflight decía «se
    imputa sin partida (editable)». Con F-013 eso es falso: no se imputa
    nada mientras no confirme."""
    cli = ClienteFalso()
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=[linea_que_no_casa()])

    assert pf.acciones[0].aviso == AVISO_SIN_PARTIDA
    assert "se imputa sin partida" not in AVISO_SIN_PARTIDA


# ---- R2 · sin confirmar: no se escribe y queda omitida con motivo -- #

def test_f013_r2_sin_confirmar_no_se_escribe():
    """R2 · EL requisito de la feature: sin confirmación no se escribe.
    Es el caso real de julio, y lo que hoy pasaba en silencio."""
    cli = ClienteFalso()
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=[linea_que_no_casa()])

    assert cli.inserts() == [] and res.escritas == []
    assert [c.motivo for c in res.pendientes_confirmacion] == ["sin_partida"]


def test_f013_r2_queda_listada_en_omitidas_con_motivo():
    """R2 · Y queda listada como OMITIDA con su motivo.

    No es cosmética: `dedicacion-api` solo mira `omitidas` para escribir
    `asignacion.sigrid_estado`. Sin esto, la línea se quedaría en la base
    con su estado anterior, que miente, y el silencio que la feature viene a
    romper seguiría intacto un escalón más arriba.
    """
    cli = ClienteFalso()
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=[linea_que_no_casa()])

    assert [o["registro_id"] for o in res.omitidas] == [1]
    assert res.omitidas[0]["motivo"] == MOTIVO_SIN_PARTIDA


def test_f013_r2_el_motivo_es_legible_y_cabe_en_la_base():
    """R2 · El texto cabe en los 300 caracteres a los que `dedicacion-api`
    recorta `asignacion.sigrid_motivo`, y dice qué hacer. Un motivo truncado
    a mitad de frase no informa de nada."""
    assert len(MOTIVO_SIN_PARTIDA) <= 300, len(MOTIVO_SIN_PARTIDA)
    assert MOTIVO_SIN_PARTIDA.startswith("sin partida:")
    assert "confirma" in MOTIVO_SIN_PARTIDA


def test_f013_r2_lo_que_si_casa_se_escribe_igual():
    """R2 · La retención es por línea, no un «ante la duda, no hagas nada»:
    en la misma ejecución, la línea que sí casa partida se escribe."""
    cli = ClienteFalso()
    lineas = [linea_que_no_casa(registro_id=1),
              linea(registro_id=2)]
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=lineas)

    assert [e["registro_id"] for e in res.escritas] == [2]
    assert [o["registro_id"] for o in res.omitidas] == [1]


# ------- R3 · con confirmación se escribe con paride = 0 ----------- #

def _clave_sin_partida_del_preflight(cli, lineas) -> str:
    conflictos = _pipeline(cli).preflight(obra=OBRA,
                                          lineas=lineas).conflictos
    sinp = [c for c in conflictos if c.motivo == "sin_partida"]
    assert len(sinp) == 1, conflictos
    return sinp[0].clave


def test_f013_r3_confirmada_se_escribe_con_paride_cero():
    """R3 · Confirmar devuelve el comportamiento de hoy: la línea se escribe
    imputada a nada. Lo que cambia no es qué se escribe, es que alguien lo
    haya dicho."""
    clave = _clave_sin_partida_del_preflight(ClienteFalso(),
                                             [linea_que_no_casa()])
    cli = ClienteFalso()
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=[linea_que_no_casa()],
                                  pisar_claves={clave})

    assert [e["registro_id"] for e in res.escritas] == [1]
    assert cli.inserts()[0]["paride"] == 0
    assert res.omitidas == [] and res.pendientes_confirmacion == []


def test_f013_r3_confirmarla_no_borra_nada():
    """R3 · Y no borra nada: no sustituye a ninguna línea de Sigrid, igual
    que la sobrecarga. Que sea cierto por construcción —`lineas` vacío— y no
    por una comprobación que alguien pueda quitar es la misma decisión que
    tomó F-002."""
    previa = linea_previa(ide=5001, reside=400, can=0.2, paride=90001,
                          hora_codigo="MJEFO", horide=6)
    clave = _clave_sin_partida_del_preflight(
        ClienteFalso(lineas_parte=[previa]), [linea_que_no_casa()])

    cli = ClienteFalso(lineas_parte=[previa])
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=[linea_que_no_casa()],
                                  pisar_claves={clave})

    assert cli.borrados() == [] and res.borradas == 0
    assert [e["registro_id"] for e in res.escritas] == [1]


def test_f013_r3_la_confirmacion_no_estrena_canal():
    """R3 · Y viaja por `pisar_claves`, el mismo canal que ya usan el pisado
    y la sobrecarga: `ejecutar` no gana ni un parámetro. Un canal nuevo
    obligaría a tocar `dedicacion-api` y `dedicacion-front`, que es justo lo
    que F-013 no hace."""
    import inspect

    firma = inspect.signature(RegistroPipeline.ejecutar)
    assert list(firma.parameters) == ["self", "obra", "lineas",
                                      "pisar_claves", "usuario"]


def test_f013_r3_una_clave_ajena_no_confirma_nada():
    """R3 · Y la clave tiene que ser LA suya: mandar cualquier otra cosa en
    `pisar_claves` no desbloquea la línea."""
    cli = ClienteFalso()
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=[linea_que_no_casa()],
                                  pisar_claves={"sin_partida:99", "x"})

    assert res.escritas == [] and cli.inserts() == []
    assert [c.motivo for c in res.pendientes_confirmacion] == ["sin_partida"]


def test_f013_r3_confirmar_una_no_confirma_la_otra():
    """R3 · Con dos líneas sin partida, confirmar la de un trabajador no
    escribe la del otro. Es la consecuencia observable de que la clave sea
    por línea."""
    lineas = [linea_que_no_casa(registro_id=1),
              linea_que_no_casa(registro_id=2, empleado_ide=10,
                                nombre="Otro Sin Casar", categoria="Peon")]
    pf = _pipeline(ClienteFalso()).preflight(obra=OBRA, lineas=lineas)
    claves = {c.registros[0]: c.clave for c in pf.conflictos
              if c.motivo == "sin_partida"}
    assert sorted(claves) == [1, 2], pf.conflictos

    cli = ClienteFalso()
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=lineas,
                                  pisar_claves={claves[1]})

    assert [e["registro_id"] for e in res.escritas] == [1]
    assert [o["registro_id"] for o in res.omitidas] == [2]


# ---------- R4 · el contrato con el front no cambia ---------------- #

def test_f013_r4_el_conflicto_serializa_los_campos_de_siempre():
    """R4 · Degradación elegante: un cliente que ignore el motivo nuevo lee
    los mismos campos que siempre y sigue funcionando. Lo que NO significa
    es que la línea se escriba igual: si nadie confirma, no se escribe, y
    eso es exactamente lo que la feature persigue."""
    cli = ClienteFalso()
    c = _pipeline(cli).preflight(
        obra=OBRA, lineas=[linea_que_no_casa()]).conflictos[0]
    d = asdict(c)

    for campo in ("clave", "recurso_ide", "nombre", "ano", "mes",
                  "parte_cod", "horide", "hora_codigo", "lineas",
                  "contexto", "nuevas", "registros", "motivo"):
        assert campo in d, campo
    assert isinstance(d["clave"], str) and isinstance(d["registros"], list)
    assert d["nuevas"][0]["registro_id"] == 1


def test_f013_r4_no_hace_falta_ningun_campo_nuevo():
    """R4 · F-013 no añade ni un campo al `Conflicto`: el tercer caso cabe
    entero en el contrato que dejó F-002. Si hiciera falta uno nuevo, habría
    que revisar si el patrón encajaba de verdad."""
    cli = ClienteFalso()
    c = _pipeline(cli).preflight(
        obra=OBRA, lineas=[linea_que_no_casa()]).conflictos[0]
    d = asdict(c)

    assert set(d) == {"clave", "recurso_ide", "nombre", "ano", "mes",
                      "parte_cod", "horide", "hora_codigo", "lineas",
                      "contexto", "nuevas", "registros", "motivo",
                      "suma_existente", "suma_total", "exceso"}


#: Los dos ficheros que tendrían que cambiar si el contrato no aguantara el
#: tercer motivo: el que pinta los conflictos y el que persiste el resultado.
FRONT_JS = (RAIZ / "services" / "dedicacion-front" / "static" / "js" /
            "app.js")
API_REGISTRO = (RAIZ / "services" / "dedicacion-api" / "application" /
                "registro_sigrid.py")


@pytest.mark.parametrize("ruta", (FRONT_JS, API_REGISTRO),
                         ids=lambda r: r.name)
@pytest.mark.parametrize("motivo", ("pisado", "sobrecarga", "sin_partida"))
def test_f013_r4_ni_la_api_ni_el_front_enumeran_los_motivos(ruta, motivo):
    """R4 · La degradación elegante no es una promesa: es que ninguno de los
    dos servicios ramifica por el motivo. Pintan el conflicto y persisten
    `omitidas` sin mirar de qué tipo son. El día que uno de los dos escriba
    un `if motivo === ...`, este test cae y obliga a decidir si el contrato
    sigue siendo el de F-002."""
    assert ruta.is_file(), ruta
    assert motivo not in ruta.read_text(encoding="utf-8"), ruta.name


# --------- interacción con la SOBRECARGA (F-002, Regla B) ---------- #

def _sin_partida_y_sobrecarga():
    """El recurso 400 ya tiene 0,9 en otra partida (no se pisa: otra
    partida) y le añadimos 0,4 que además no casa partida. Las dos cosas a
    la vez sobre la misma línea."""
    cli = ClienteFalso(lineas_parte=[
        linea_previa(ide=5001, reside=400, can=0.9, paride=90001,
                     hora_codigo="MCAP", horide=7)])
    return cli, [linea_que_no_casa(porcentaje=0.4)]


def test_f013_los_dos_avisos_se_ensenan_a_la_vez():
    """Una misma línea puede caer en los dos avisos, y se le enseñan LOS
    DOS: son decisiones independientes («impútalo sin partida» y «acepto que
    se pase del 100 %»), y esconder una haría que el humano confirmara la
    otra sin saber lo que firma."""
    cli, lineas = _sin_partida_y_sobrecarga()
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=lineas)

    assert [c.motivo for c in pf.conflictos] == ["sin_partida", "sobrecarga"]


def test_f013_el_orden_es_sin_partida_primero():
    """Y en ese orden, por la misma razón por la que F-002 puso el pisado
    antes que la sobrecarga: el aviso que va después DA POR HECHO el de
    antes. La suma de la sobrecarga incluye el `can` de esta línea, así que
    la decisión que la sostiene se lee primero."""
    cli, lineas = _sin_partida_y_sobrecarga()
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=lineas)

    assert pf.conflictos[0].motivo == "sin_partida"
    assert pf.conflictos[1].motivo == "sobrecarga"
    assert pf.conflictos[1].suma_total == pytest.approx(1.3)


def test_f013_confirmar_solo_la_sobrecarga_no_escribe():
    """Confirmar uno de los dos no basta: la línea sigue retenida por el
    otro. Es la propiedad que hace que dos avisos sobre la misma línea sean
    seguros de componer."""
    cli0, lineas0 = _sin_partida_y_sobrecarga()
    pf = _pipeline(cli0).preflight(obra=OBRA, lineas=lineas0)
    clave_sobre = [c.clave for c in pf.conflictos
                   if c.motivo == "sobrecarga"][0]

    cli, lineas = _sin_partida_y_sobrecarga()
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=lineas,
                                  pisar_claves={clave_sobre})

    assert cli.inserts() == [] and res.escritas == []
    assert [c.motivo for c in res.pendientes_confirmacion] == ["sin_partida"]


def test_f013_confirmar_solo_la_sin_partida_tampoco_escribe():
    """Y al revés, que es el control que impide que el test de arriba pase
    con un pipeline que no escriba nunca."""
    cli0, lineas0 = _sin_partida_y_sobrecarga()
    pf = _pipeline(cli0).preflight(obra=OBRA, lineas=lineas0)
    clave_sinp = [c.clave for c in pf.conflictos
                  if c.motivo == "sin_partida"][0]

    cli, lineas = _sin_partida_y_sobrecarga()
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=lineas,
                                  pisar_claves={clave_sinp})

    assert cli.inserts() == [] and res.escritas == []
    assert [c.motivo for c in res.pendientes_confirmacion] == ["sobrecarga"]


def test_f013_confirmando_las_dos_se_escribe_una_vez():
    """Control positivo: con las dos confirmadas la línea se escribe, una
    sola vez y con `paride` a 0."""
    cli0, lineas0 = _sin_partida_y_sobrecarga()
    claves = {c.clave for c in
              _pipeline(cli0).preflight(obra=OBRA,
                                        lineas=lineas0).conflictos}

    cli, lineas = _sin_partida_y_sobrecarga()
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=lineas,
                                  pisar_claves=claves)

    assert [e["registro_id"] for e in res.escritas] == [1]
    assert [i["paride"] for i in cli.inserts()] == [0]


def test_f013_la_omision_no_se_duplica_con_los_dos_avisos():
    """Y sin confirmar ninguno, la línea aparece UNA vez por cada aviso que
    la retiene, nunca más: `dedicacion-api` escribe el motivo de cada
    `omitidas` sobre la misma asignación, así que dos entradas del mismo
    motivo serían una escritura repetida y ruido en la traza."""
    cli, lineas = _sin_partida_y_sobrecarga()
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=lineas)

    motivos = sorted(o["motivo"][:12] for o in res.omitidas)
    assert motivos == ["sin partida:", "sobrecarga:"], res.omitidas


# ------------ interacción con el PISADO (F-002, Regla A) ----------- #

def _sin_partida_y_pisado():
    """La línea previa del recurso 400 tiene `paride = 0`, el mismo código
    de hora y el mismo mes: es LA MISMA línea (Regla A), así que además de
    no casar partida, la nuestra la pisa."""
    cli = ClienteFalso(lineas_parte=[
        linea_previa(ide=5001, reside=400, can=0.3, paride=0,
                     hora_codigo="MJEFO", horide=6)])
    return cli, [linea_que_no_casa(porcentaje=0.4)]


def test_f013_pisado_y_sin_partida_a_la_vez():
    """Sin partida y pisado también se dan juntos, y también se enseñan los
    dos: la identidad de la Regla A incluye `paride`, y `paride = 0` es un
    valor de identidad como cualquier otro."""
    cli, lineas = _sin_partida_y_pisado()
    pf = _pipeline(cli).preflight(obra=OBRA, lineas=lineas)

    assert [c.motivo for c in pf.conflictos] == ["sin_partida", "pisado"]
    assert [ls.ide for ls in pf.conflictos[1].lineas] == [5001]


def test_f013_confirmar_el_pisado_sin_la_partida_no_borra():
    """EL riesgo de componer los dos avisos, y la razón por la que hay que
    probarlo: el borrado se emite por conflicto confirmado y la escritura se
    bloquea por registro. Si la guarda de F-002 (R32) no cubriera este
    tercer caso, confirmar el pisado borraría la línea vieja SIN escribir la
    que la sustituye: pérdida neta de un apunte, y en silencio."""
    cli0, lineas0 = _sin_partida_y_pisado()
    pf = _pipeline(cli0).preflight(obra=OBRA, lineas=lineas0)
    clave_pisado = [c.clave for c in pf.conflictos
                    if c.motivo == "pisado"][0]

    cli, lineas = _sin_partida_y_pisado()
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=lineas,
                                  pisar_claves={clave_pisado})

    assert cli.borrados() == [], cli.borrados()
    assert res.borradas == 0 and res.escritas == []


def test_f013_confirmando_las_dos_si_se_pisa():
    """Control positivo: confirmadas las dos, se borra la vieja y se escribe
    la nueva. La guarda no es «no borres nunca»."""
    cli0, lineas0 = _sin_partida_y_pisado()
    claves = {c.clave for c in
              _pipeline(cli0).preflight(obra=OBRA,
                                        lineas=lineas0).conflictos}

    cli, lineas = _sin_partida_y_pisado()
    res = _pipeline(cli).ejecutar(obra=OBRA, lineas=lineas,
                                  pisar_claves=claves)

    assert cli.borrados() == [5001] and res.borradas == 1
    assert [e["registro_id"] for e in res.escritas] == [1]


# --------- la POSTVENTA sigue por su camino, que es otro ----------- #

def test_f013_la_postventa_sin_partida_se_sigue_omitiendo():
    """Los dos caminos siguen separados a propósito.

    En la POSTVENTA, sin partida casada no hay destino posible: la obra de
    postventa es un presupuesto ajeno a la obra original y escribir ahí «sin
    partida» no significaría nada. Por eso P5 la OMITE en `decidir`, antes
    de llegar a ser una acción de escritura, y no hay nada que confirmar.

    En la obra NORMAL sí hay destino —la propia obra— y lo único que falta
    es la imputación analítica: por eso se puede escribir, y por eso se
    pregunta. Ver `ARCHITECTURE.md#regla-p5` y `#regla-sin-partida`.
    """
    cli = ClienteFalso(presupuesto_postventa="hojas")
    # La obra origen '0001' no casa con ninguna partida de la de postventa
    # (ni por código, ni por prefijo, ni por descripción).
    pf = _pipeline(cli).preflight(
        obra=ObraEntrada(codigo="0001"),
        lineas=[linea(registro_id=1, es_postventa=True)])

    a = pf.acciones[0]
    assert a.accion == "omitir", a
    assert "no casa con ninguna partida" in (a.motivo or "")
    assert pf.conflictos == []


def test_f013_la_postventa_que_si_casa_se_escribe_sin_preguntar():
    """Control: una postventa con su partida casada no emite ningún aviso de
    F-013 — tiene partida, que es justo lo que aquí se vigila."""
    cli = ClienteFalso()
    pf = _pipeline(cli).preflight(
        obra=OBRA, lineas=[linea(registro_id=1, es_postventa=True)])

    a = pf.acciones[0]
    assert a.accion == "escribir" and a.paride == 70001
    assert pf.conflictos == []


# ------------- R6 · la regla vive en la fuente única --------------- #

def _texto(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


def _plano(ruta: Path) -> str:
    return " ".join(_texto(ruta).split())


def _bloque(ancla: str) -> str:
    """El texto que va de un ancla a la siguiente (o al final), aplanado."""
    texto = _plano(ARQUITECTURA)
    inicio = texto.index(f'<a id="{ancla}"></a>')
    fin = texto.find('<a id="', inicio + 1)
    return texto[inicio:fin if fin != -1 else len(texto)]


def test_f013_r6_la_regla_tiene_su_ancla_en_la_fuente_unica():
    """R6 · La regla se enuncia en `docs/ARCHITECTURE.md`, una sola vez y
    con ancla estable, como las otras siete."""
    texto = _texto(ARQUITECTURA)
    assert texto.count('<a id="regla-sin-partida"></a>') == 1


def test_f013_r6_la_regla_dice_lo_que_decide():
    """R6 · Y dice las tres cosas que decide: que sin confirmar no se
    escribe, que queda omitida con motivo, y que confirmada se escribe sin
    partida."""
    bloque = _bloque("regla-sin-partida")
    assert "no se escribe" in bloque
    assert "omitida" in bloque
    assert "confirma" in bloque.lower()


#: El mismo patrón que exige F-002 (R4): quién, cuándo y con qué respaldo.
PATRON_PROCEDENCIA = r"Confirmado por [^·]{3,120} el \d{4}-\d{2}-\d{2} · \S+"


def test_f013_r6_la_regla_lleva_su_procedencia():
    """R6 · Con su procedencia fechada: quién la decidió, cuándo y con qué
    respaldo. Una regla sin interlocutor no se le puede repreguntar a
    nadie."""
    bloque = _bloque("regla-sin-partida")
    assert re.search(PATRON_PROCEDENCIA, bloque), bloque[:400]
    assert "2026-08-20" in bloque


def test_f013_r6_el_respaldo_es_el_preflight_real_de_julio():
    """R6 · Y el respaldo es el que hay, no uno inventado: el preflight real
    del periodo 2026-07. F-002 dejó escrito por qué esto importa — clavar un
    interlocutor que no consta obliga a escribir una procedencia falsa para
    poner el test en verde."""
    bloque = _bloque("regla-sin-partida")
    assert "2026-07" in bloque
    assert "Administración" not in bloque


@pytest.mark.parametrize("ruta", (
    RAIZ / "services" / "dedicacion-transfer" / "application" / "services" /
    "reglas_porcentajes.py",
    RAIZ / "services" / "dedicacion-transfer" / "application" / "pipelines" /
    "registro_pipeline.py",
), ids=lambda r: r.name)
def test_f013_r6_el_codigo_remite_en_vez_de_reenunciar(ruta):
    """R6 · Y el código que la implementa remite al ancla en vez de contarla
    otra vez con palabras propias, que es la avería que F-002 vino a cerrar
    y que una feature nueva puede reabrir sin darse cuenta."""
    assert "ARCHITECTURE.md#regla-sin-partida" in _texto(ruta), ruta.name
