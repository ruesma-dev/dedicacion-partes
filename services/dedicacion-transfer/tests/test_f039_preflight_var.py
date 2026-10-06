# tests/test_f039_preflight_var.py
"""F-039 · La línea VAR en el preflight y en la escritura (R5-R9).

La regla es `docs/ARCHITECTURE.md#regla-var`. Lo que se comprueba:

- una línea con `var_paride` se imputa a esa partida solo si está en el
  universo VAR calculado con las MISMAS funciones que `POST /api/var/universo`
  y la obra de la petición es la obra VAR (R5), y si no se omite con motivo
  (R6);
- el override manual no la cambia (R7) y sigue las reglas de siempre (R8);
- una línea sin `var_paride` se trata exactamente como antes (R9);
- el cruce: «en el universo» ⇔ «el preflight la escribe con
  `partida_metodo = "var"`», en real y en pruebas.

Sin red ni BBDD: dobles de `test_f039_universo_var.py` y `conftest.py`.
"""
from __future__ import annotations

from dataclasses import asdict

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.universo_var import (
    MOTIVO_VAR_FUERA,
    MOTIVO_VAR_OFF,
    MOTIVO_VAR_OTRA_OBRA,
    MOTIVO_VAR_POSTVENTA,
    MOTIVO_VAR_SIN_UNIVERSO,
    UniversoVar,
)
from domain.models.registro_models import ObraEntrada

from tests.conftest import (
    OBRA_ORIGEN,
    OBRA_PRUEBAS,
    ClienteFalso,
    SettingsFalso,
    linea,
    linea_previa,
)
from tests.test_f039_universo_var import (
    DESDE,
    OBRA_VAR,
    PRESUPUESTO_VAR,
    UNIVERSO_29,
    VAR_IDE,
    ClienteVar,
    ajustes_var,
)

#: La obra de la petición tal como la manda la api para una entrada VAR
#: (`registro_obra_ide`, `registro_obra_cod`, sin nombre).
OBRA_VAR_PETICION = ObraEntrada(ide=VAR_IDE, codigo=OBRA_VAR, nombre=None)
P29 = 417055


def _pl(cli, forzar: bool = False, **ajustes) -> RegistroPipeline:
    return RegistroPipeline(
        cliente=cli,
        settings=ajustes_var(obra_pruebas_forzar=forzar, **ajustes))


def _pf(cli=None, *, obra=OBRA_VAR_PETICION, lineas=None, forzar=False,
        **ajustes):
    cli = ClienteVar() if cli is None else cli
    lineas = [linea(var_paride=P29)] if lineas is None else lineas
    return _pl(cli, forzar, **ajustes).preflight(obra=obra, lineas=lineas)


# ======================= R5 · se imputa a su partida ==================== #

def test_f039_r5_en_real_la_linea_va_a_la_obra_var_con_su_partida():
    """R5, R8 · En real: acción `escribir` en la obra VAR, partida 29 fija
    (`partida_metodo = "var"`), cuenta del centro de la obra VAR y parte de
    la obra VAR."""
    pf = _pf()
    a = pf.acciones[0]
    assert (a.accion, a.destino) == ("escribir", "obra"), a
    assert (a.paride, a.partida_cod, a.partida_metodo) == (P29, "29", "var")
    assert a.caa_cod == f"{OBRA_VAR}.CIMO03" and a.aviso is None
    assert pf.obra_destino.codigo == OBRA_VAR and not pf.forzada_pruebas
    assert [p.obra_cod for p in pf.partes] == [OBRA_VAR]
    assert pf.conflictos == []


def test_f039_r8_en_pruebas_va_a_la_obra_de_pruebas_con_la_partida_var():
    """R8 · En pruebas (`#regla-pruebas`): a la obra de pruebas, con la
    partida VAR y la cuenta del centro de la obra de pruebas."""
    pf = _pf(forzar=True)
    a = pf.acciones[0]
    assert a.accion == "escribir", a
    assert (a.paride, a.partida_cod, a.partida_metodo) == (P29, "29", "var")
    assert a.caa_cod == f"{OBRA_PRUEBAS}.CIMO03"
    assert pf.forzada_pruebas and pf.obra_destino.codigo == OBRA_PRUEBAS
    assert [p.obra_cod for p in pf.partes] == [OBRA_PRUEBAS]


def test_f039_r5_sin_casado_por_categoria_ni_nombre_y_una_carga():
    """R5 · Dos líneas VAR: el presupuesto de la obra VAR se lee UNA vez
    (el catálogo), no se casa por categoría (no se publica `partidas_obra`)
    y la obra VAR se busca una sola vez."""
    cli = ClienteVar()
    pf = _pf(cli, lineas=[linea(registro_id=1, var_paride=P29),
                          linea(registro_id=2, recurso_ide=400,
                                var_paride=417057)])
    assert [(a.paride, a.partida_metodo) for a in pf.acciones] == [
        (P29, "var"), (417057, "var")]
    assert (cli.n_obra_por_codigo, cli.n_capitulos_de_obra) == (1, 1)
    assert pf.partidas_obra == []


def test_f039_r8_ejecutar_inserta_con_su_partida_synckey_y_cuenta():
    """R8 · La escritura lleva la partida VAR, la `synckey` de siempre, la
    cuenta del centro y va al parte de la obra VAR."""
    cli = ClienteVar()
    r = _pl(cli).ejecutar(obra=OBRA_VAR_PETICION,
                          lineas=[linea(var_paride=P29)])
    assert r.ok and len(r.escritas) == 1
    ins = cli.inserts()[0]
    assert ins["paride"] == P29 and ins["synckey"] == "porcentajes:1"
    assert ins["obra"].codigo == OBRA_VAR and ins["caaide"] == 91001
    assert r.escritas[0]["partida_cod"] == "29"


# ===================== R6 · si no cumple, se omite ====================== #

@pytest.mark.parametrize("paride", [417002, 417001, 60001, 417061, 417063,
                                    52979, 999999],
                         ids=["28", "05", "CI.1.3", "capitulo-31", "baja-32",
                              "CD", "inexistente"])
def test_f039_r6_partida_fuera_del_universo_se_omite(paride):
    """R6 · Fuera del universo (número < umbral, `CI.*`, capítulo, de baja o
    inexistente): omitida con el motivo que nombra partida y obra, sin aviso
    de «sin partida»."""
    pf = _pf(lineas=[linea(var_paride=paride)])
    a = pf.acciones[0]
    assert a.accion == "omitir", a
    assert a.motivo == MOTIVO_VAR_FUERA.format(paride=paride, var=OBRA_VAR,
                                               desde=DESDE)
    assert a.aviso is None and pf.conflictos == []


def test_f039_r6_otra_obra_se_omite():
    """R6 · La partida VAR en la petición de otra obra no se escribe ni
    en esa obra ni en la VAR."""
    cli = ClienteVar()
    pf = _pf(cli, obra=ObraEntrada(ide=cli.obra_origen.ide,
                                   codigo=OBRA_ORIGEN))
    a = pf.acciones[0]
    assert a.accion == "omitir", a
    assert a.motivo == MOTIVO_VAR_OTRA_OBRA.format(
        paride=P29, obra=cli.obra_origen.ide, var=OBRA_VAR)
    assert a.aviso is None and pf.conflictos == []


@pytest.mark.parametrize("cliente, ajustes, trozo", [
    (lambda: ClienteVar(var_existe=False), {}, "no encontrada"),
    (lambda: ClienteVar(var_ambigua=True), {}, "ambigua"),
    (ClienteVar, {"var_obra_cod": ""}, MOTIVO_VAR_OFF),
], ids=["ausente", "ambigua", "sin-ajuste"])
def test_f039_r6_sin_universo_se_omite(cliente, ajustes, trozo):
    """R6 · Sin universo (R3): omitida con el motivo del catálogo, el mismo
    que publica el universo."""
    cli = cliente()
    pf = _pf(cli, **ajustes)
    universo = UniversoVar(cliente=cliente(),
                           settings=ajustes_var(**ajustes)).calcular(1)
    a = pf.acciones[0]
    assert a.accion == "omitir", a
    assert trozo in universo["motivo"]
    assert a.motivo == MOTIVO_VAR_SIN_UNIVERSO.format(
        paride=P29, motivo=universo["motivo"])
    assert a.aviso is None and pf.conflictos == []


def test_f039_r6_postventa_con_var_paride_se_omite_sin_leer_la_var():
    """R6 · Una línea de postventa con `var_paride` no se imputa a la
    partida VAR: se omite, y no hace falta leer la obra VAR."""
    cli = ClienteVar()
    pf = _pf(cli, obra=ObraEntrada(codigo=OBRA_ORIGEN), lineas=[
        linea(es_postventa=True, var_paride=P29)])
    a = pf.acciones[0]
    assert a.accion == "omitir", a
    assert a.motivo == MOTIVO_VAR_POSTVENTA.format(paride=P29)
    assert cli.n_presupuesto_var == 0


# ====================== R7 · el override no cambia ====================== #

def test_f039_r7_el_paride_manual_no_cambia_la_partida_var():
    """R7 · Un `paride` manual en la misma línea no la mueve."""
    pf = _pf(lineas=[linea(var_paride=P29, paride=60001,
                           partida_cod="CI.1.3")])
    a = pf.acciones[0]
    assert (a.paride, a.partida_cod, a.partida_metodo) == (P29, "29", "var")


# ===================== R8 · las reglas de siempre ======================= #

def test_f039_r8_ya_registrada_por_synckey():
    """R8 · Idempotencia por `synckey`: si ya está, `ya_registrado`."""
    cli = ClienteVar(synckeys={"porcentajes:1": linea_previa(
        ide=8001, synckey="porcentajes:1", paride=P29)})
    a = _pf(cli).acciones[0]
    assert a.accion == "ya_registrado" and a.hmores_ide == 8001


def test_f039_r8_pisado_con_la_misma_partida_y_no_con_otra():
    """R8 · `#regla-conflicto`: la identidad incluye la partida; la misma
    partida VAR choca, otra partida VAR no."""
    misma = _pf(ClienteVar(lineas_parte=[linea_previa(paride=P29)]))
    otra = _pf(ClienteVar(lineas_parte=[linea_previa(paride=417057,
                                                     can=0.1)]))
    assert [c.motivo for c in misma.conflictos] == ["pisado"]
    assert misma.conflictos[0].nuevas[0]["partida_cod"] == "29"
    assert otra.conflictos == []


def test_f039_r8_sobrecarga_con_otra_partida():
    """R8 · `#regla-capacidad`: con 0,8 ya imputado en otra partida, el 0,4
    nuevo se pasa de la jornada."""
    pf = _pf(ClienteVar(lineas_parte=[linea_previa(paride=417057, can=0.8)]))
    assert [c.motivo for c in pf.conflictos] == ["sobrecarga"]


# ================ R9 · sin var_paride, exactamente como hoy ============== #

class ClienteVarAnotado(ClienteVar):
    """`ClienteVar` que anota cada búsqueda de obra por código."""

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.busquedas: list[tuple] = []

    def obra_por_codigo(self, cod, empresa):
        self.busquedas.append((cod, empresa))
        return super().obra_por_codigo(cod, empresa)


@pytest.mark.parametrize("lineas", [
    [linea(registro_id=1)],
    [linea(registro_id=1), linea(registro_id=3, es_postventa=True)],
    [linea(registro_id=1, paride=80002, partida_cod="CI.1.20")],
], ids=["normal", "normal-y-postventa", "override"])
@pytest.mark.parametrize("forzar", [True, False], ids=["pruebas", "real"])
def test_f039_r9_sin_var_paride_el_preflight_no_cambia(lineas, forzar):
    """R9 · Mismas acciones, partes y conflictos que con el doble y los
    ajustes de antes de F-039, y la obra VAR ni se busca."""
    obra = ObraEntrada(codigo=OBRA_ORIGEN)
    cli = ClienteVarAnotado()
    nuevo = _pl(cli, forzar).preflight(obra=obra, lineas=lineas)
    viejo = RegistroPipeline(
        cliente=ClienteFalso(),
        settings=SettingsFalso(obra_pruebas_forzar=forzar)).preflight(
            obra=obra, lineas=lineas)
    assert [asdict(a) for a in nuevo.acciones] == \
        [asdict(a) for a in viejo.acciones]
    assert [asdict(p) for p in nuevo.partes] == \
        [asdict(p) for p in viejo.partes]
    assert nuevo.conflictos == viejo.conflictos
    assert cli.n_presupuesto_var == 0
    assert cli.busquedas and all(c != OBRA_VAR for c, _e in cli.busquedas)


def test_f039_r9_la_linea_trae_var_paride_opcional():
    """R9 · `var_paride` es opcional en la entrada y en el contrato HTTP;
    por defecto, ninguno."""
    from interface_adapters.api.app import LineaIn

    assert linea().var_paride is None
    assert LineaIn.model_fields["var_paride"].default is None
    assert LineaIn(registro_id=1, ano=2026, mes=7, porcentaje=0.4,
                   var_paride=P29).var_paride == P29


# ========== Cruce · en el universo ⇔ el preflight la escribe ============ #

@pytest.mark.parametrize("forzar", [False, True], ids=["real", "pruebas"])
@pytest.mark.parametrize("paride", sorted(f["ide"] for f in PRESUPUESTO_VAR))
def test_f039_cruce_universo_y_preflight(paride, forzar):
    """R1 ⇔ R5 · EL test de la feature: una partida está en el universo VAR
    si y solo si el preflight escribe su línea con esa partida y
    `partida_metodo = "var"`; fuera, si y solo si la omite."""
    universo = {p["ide"] for p in UniversoVar(
        cliente=ClienteVar(), settings=ajustes_var()).calcular(1)["partidas"]}
    a = _pf(lineas=[linea(var_paride=paride)], forzar=forzar).acciones[0]
    assert (paride in universo) is (paride in UNIVERSO_29)
    if paride in universo:
        assert (a.accion, a.paride, a.partida_metodo) == (
            "escribir", paride, "var"), a
    else:
        assert a.accion == "omitir", a


def test_f039_r5_el_pipeline_no_guarda_el_catalogo_var():
    """R5 · Ningún catálogo VAR sobrevive a su petición (como F-025 R9)."""
    pl = _pl(ClienteVar())
    antes = set(vars(pl))
    pl.preflight(obra=OBRA_VAR_PETICION, lineas=[linea(var_paride=P29)])
    assert set(vars(pl)) == antes
