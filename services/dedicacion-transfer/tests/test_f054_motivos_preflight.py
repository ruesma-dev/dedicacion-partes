# tests/test_f054_motivos_preflight.py
"""F-054 · T26: los motivos del preflight del registro, por código (R47;
D21: «trasladalo a codigos legibles, no numeros internos»).

- `CatalogoVar.codigos`: `{ide: cod}` de TODO el presupuesto de la obra VAR
  que `cargar_catalogo_var` ya lee (sin lectura nueva); vacío sin obra y por
  defecto.
- `MOTIVO_VAR_FUERA` / `_OTRA_OBRA`: la partida por el código del
  presupuesto VAR, si no por el `partida_cod` que manda la api, si no por su
  `ide`; la obra, por el código de la de la petición.
- `MOTIVO_VAR_SIN_UNIVERSO` / `_POSTVENTA`: el `partida_cod` que manda la
  api y, sin él, el `ide` (en postventa sigue sin leerse la obra VAR).
- `MOTIVO_PARTIDA_PV_NO_HOJA`: el `partida_cod` de la línea, si no el `cod`
  del nodo del presupuesto de postventa, si no el `paride`.

Los textos esperados con `partida_cod` de `test_f039_preflight_var.py`,
`test_f002_postventa.py` y `test_f025_universo_postventa.py` cambian por la
lista cerrada de T26; aquí, los casos nuevos. Sin red ni BBDD.
"""
from __future__ import annotations

from application.pipelines.registro_pipeline import MOTIVO_PARTIDA_PV_NO_HOJA
from application.services.universo_var import (
    MOTIVO_VAR_FUERA,
    MOTIVO_VAR_OTRA_OBRA,
    MOTIVO_VAR_POSTVENTA,
    MOTIVO_VAR_SIN_UNIVERSO,
    CatalogoVar,
    UniversoVar,
    cargar_catalogo_var,
)
from domain.models.registro_models import ObraEntrada

from tests.conftest import OBRA_ORIGEN, linea
from tests.test_f002_postventa import _pv
from tests.test_f039_preflight_var import P29, _pf
from tests.test_f039_universo_var import (
    DESDE,
    OBRA_VAR,
    PRESUPUESTO_VAR,
    ClienteVar,
    ajustes_var,
)


# ===================== CatalogoVar.codigos, sin leer más ================ #
def test_f054_r47_catalogo_var_guarda_los_codigos_de_todo_el_presupuesto():
    cli = ClienteVar()
    cat = cargar_catalogo_var(cli, ajustes_var(), 1)
    assert cat.codigos == {f["ide"]: f["cod"] for f in PRESUPUESTO_VAR}
    assert 417002 in cat.codigos and 417002 not in cat.partidas
    assert (cli.n_obra_por_codigo, cli.n_capitulos_de_obra) == (1, 1)


def test_f054_r47_catalogo_var_sin_obra_ni_codigos():
    assert cargar_catalogo_var(ClienteVar(var_existe=False), ajustes_var(),
                               1).codigos == {}
    assert cargar_catalogo_var(ClienteVar(), ajustes_var(var_obra_cod=""),
                               1).codigos == {}
    assert CatalogoVar(obra=None, partidas={}, motivo=None).codigos == {}


def test_f054_r47_el_universo_publicado_no_cambia():
    """`/api/var/universo` sigue publicando solo las partidas VAR."""
    r = UniversoVar(cliente=ClienteVar(), settings=ajustes_var()).calcular(1)
    assert set(r) == {"empresa", "desde", "motivo", "obra_var", "partidas"}


# ========================= VAR en el preflight ========================== #
def test_f054_r47_fuera_el_codigo_del_presupuesto_manda_sobre_la_api():
    pf = _pf(lineas=[linea(var_paride=417002, partida_cod="XX")])
    assert pf.acciones[0].motivo == MOTIVO_VAR_FUERA.format(
        paride="28", var=OBRA_VAR, desde=DESDE)


def test_f054_r47_fuera_inexistente_con_el_codigo_de_la_api():
    pf = _pf(lineas=[linea(var_paride=999999, partida_cod="77")])
    assert pf.acciones[0].motivo == MOTIVO_VAR_FUERA.format(
        paride="77", var=OBRA_VAR, desde=DESDE)


def test_f054_r47_otra_obra_por_los_codigos():
    cli = ClienteVar()
    pf = _pf(cli, obra=ObraEntrada(ide=cli.obra_origen.ide,
                                   codigo=OBRA_ORIGEN),
             lineas=[linea(var_paride=999999)])
    assert pf.acciones[0].motivo == MOTIVO_VAR_OTRA_OBRA.format(
        paride=999999, obra=OBRA_ORIGEN, var=OBRA_VAR)


def test_f054_r47_otra_obra_por_el_codigo_de_la_obra_resuelta():
    """La obra, por el `codigo` de la obra resuelta en Sigrid (`origen`),
    aunque la petición no lo traiga (la reserva al `ide` de
    `partida_var_de`, en `test_f054_traduccion.py`)."""
    cli = ClienteVar()
    pf = _pf(cli, obra=ObraEntrada(ide=cli.obra_origen.ide, codigo=None))
    assert pf.acciones[0].motivo == MOTIVO_VAR_OTRA_OBRA.format(
        paride="29", obra=OBRA_ORIGEN, var=OBRA_VAR)


def test_f054_r47_sin_universo_con_el_codigo_de_la_api():
    cli = ClienteVar(var_existe=False)
    pf = _pf(cli, lineas=[linea(var_paride=P29, partida_cod="29")])
    motivo = cargar_catalogo_var(ClienteVar(var_existe=False), ajustes_var(),
                                 1).motivo
    assert pf.acciones[0].motivo == MOTIVO_VAR_SIN_UNIVERSO.format(
        paride="29", motivo=motivo)


def test_f054_r47_postventa_con_var_paride_con_el_codigo_de_la_api():
    cli = ClienteVar()
    pf = _pf(cli, obra=ObraEntrada(codigo=OBRA_ORIGEN), lineas=[
        linea(es_postventa=True, var_paride=P29, partida_cod="29")])
    assert pf.acciones[0].motivo == MOTIVO_VAR_POSTVENTA.format(paride="29")
    assert cli.n_presupuesto_var == 0


def test_f054_r47_el_partida_cod_de_la_var_no_decide_nada():
    """Con o sin `partida_cod`, la línea VAR válida se escribe igual, en la
    partida de su `var_paride`."""
    con = _pf(lineas=[linea(var_paride=P29, partida_cod="OTRA")]).acciones[0]
    sin = _pf(lineas=[linea(var_paride=P29)]).acciones[0]
    assert (con.accion, con.paride, con.partida_cod, con.partida_metodo) == (
        sin.accion, sin.paride, sin.partida_cod, sin.partida_metodo) == (
        "escribir", P29, "29", "var")


# ===================== postventa: partida no hoja ======================= #
def test_f054_r47_postventa_no_hoja_sin_partida_cod_el_cod_del_nodo():
    _, pf = _pv("hojas", paride=69100)
    assert pf.acciones[0].motivo == MOTIVO_PARTIDA_PV_NO_HOJA.format(
        paride="11")


def test_f054_r47_postventa_no_hoja_sin_nodo_el_paride():
    _, pf = _pv("hojas", paride=99999)
    assert pf.acciones[0].motivo == MOTIVO_PARTIDA_PV_NO_HOJA.format(
        paride=99999)


def test_f054_r47_postventa_no_hoja_el_partida_cod_manda():
    _, pf = _pv("hojas", paride=69100, partida_cod="X.1")
    assert pf.acciones[0].motivo == MOTIVO_PARTIDA_PV_NO_HOJA.format(
        paride="X.1")
