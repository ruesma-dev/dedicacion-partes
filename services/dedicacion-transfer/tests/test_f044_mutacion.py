# tests/test_f044_mutacion.py
"""F-044 · T22: los huecos que destapó la campaña de mutación en el transfer.

Cada test nombra el superviviente que caza (`progress/mutacion_F-044.md`).

- `EscrituraVinculados` (R24, R28), con un doble mínimo del cliente: lo
  que llevan la traza y la sentencia de una edición (partida, cuenta y
  `tex`), el parte y la `pos` de cada inserción, qué conflictos planea
  editar, cuándo una línea ya no vale y la relectura tras escribir.
- El preflight con vinculados (R12-R23): la lectura de partidas válidas,
  la partida con titular sin partida, en postventa y con propuesta
  guardada, la idempotencia por `hmores.ide`, el contexto del pisado, el
  cero de un omitido, el redondeo de la sobrecarga y el aviso de la línea
  al 0 %. Y el alta del parte desde los vinculados.

Sin red ni BBDD; los `ide` son inventados.
"""
from __future__ import annotations

import dataclasses
from dataclasses import replace

import pytest
from application.pipelines.registro_pipeline import _traza
from application.pipelines.registro_vinculados import (
    EscrituraVinculados,
    motivo_de_conflicto,
)
from application.services.reglas_porcentajes import (
    AVISO_LINEA_CERO,
    MOTIVO_LINEA_CAMBIADA,
)
from application.services.reglas_vinculados import (
    MOTIVO_ELEGIDA_NO_VALIDA,
    MOTIVO_SIN_CI,
    MOTIVO_SIN_PARTIDA_VINCULADO,
    MOTIVO_SOBRECARGA_VINCULADO,
    PartidaElegida,
    por_que_sin_ci,
    synckey_vinculado,
)
from domain.models.registro_models import (
    AccionVinculado,
    Conflicto,
    LineaSigrid,
    ObraEntrada,
    ParteDestino,
    ResultadoRegistro,
)

from tests.conftest import linea, linea_previa
from tests.test_f044_pipeline_vinculados import (
    ClienteEje,
    ClientePre,
    _eje,
    _ls_vin,
    _pf,
    _por,
    _v,
)

OBRA = ObraEntrada(ide=828942, codigo="0404", nombre="PRUEBAS", empresa=1)
VIN = {"tipo": "TF", "cod": "TF-10"}


# ===================== EscrituraVinculados, a solas ====================== #
class _Cli:
    """Lo que `EscrituraVinculados` pide al cliente. `leer`: las líneas de
    Sigrid por `ide` (con su parte); `escribir` les aplica la edición y la
    puesta a 0 salvo a las de `guarda_falla`; `relee` sustituye lo que ve
    la relectura (None: ya no está)."""

    def __init__(self, *leer: LineaSigrid) -> None:
        self.leer = {ls.ide: ls for ls in leer}
        self.relee: dict[int, LineaSigrid | None] = {}
        self.guarda_falla: set[int] = set()
        self.escritos: list[dict] = []
        self.para_editar: list[list[int]] = []

    def stmt_editar_linea(self, **kw):
        return {"sql": "editar", "parameters": kw}

    def stmt_poner_a_cero(self, **kw):
        return {"sql": "a_cero", "parameters": kw}

    def stmt_insert_linea(self, **kw):
        return {"sql": "insert", "parameters": kw}

    def max_pos(self, hmoide):
        return 64

    def lineas_para_editar(self, ides):
        self.para_editar.append(sorted(ides))
        return {i: self.leer[i] for i in ides if i in self.leer}

    def escribir(self, statements):
        self.escritos.extend(statements)
        for st in statements:
            kw = st["parameters"]
            if st["sql"] == "insert" or kw["ide"] in self.guarda_falla:
                continue
            ls = self.leer[kw["ide"]]
            self.leer[kw["ide"]] = (
                replace(ls, can=0.0) if st["sql"] == "a_cero"
                else replace(ls, can=kw["can"], synckey=kw["synckey"]))
        return len(statements)

    def lineas_registradas(self, claves, ides=()):
        por_ide = {}
        for i in ides:
            ls = self.relee[i] if i in self.relee else self.leer.get(i)
            if ls is not None:
                por_ide[i] = ls
        return {}, por_ide

    def de(self, sql: str) -> list[dict]:
        return [s["parameters"] for s in self.escritos if s["sql"] == sql]


def _av(registro: int = 1, recurso: int = 10, **kw) -> AccionVinculado:
    hora = {10: (31, "OTEL", 81001, 90001),
            11: (33, "OGAS", 81002, 90002)}[recurso]
    datos = {"registro_id": registro, "recurso_ide": recurso, "accion": "escribir",
                 "ano": 2026, "mes": 7, "fecha_int": 20260731, "tipo": "TF",
                 "cod": f"TF-{recurso}", "hora_ide": hora[0], "hora_codigo": hora[1],
                 "can": 0.4, "pre": 30.0, "tot": 12.0, "paride": hora[2],
                 "partida_cod": "CI", "caa_ide": hora[3]}
    datos.update(kw)
    return AccionVinculado(**datos)


def _ls(ide: int, recurso: int = 10, can: float = 0.0, **kw) -> LineaSigrid:
    horide, hora, paride = {10: (31, "OTEL", 81001),
                            11: (33, "OGAS", 81002)}[recurso]
    datos = {"ide": ide, "reside": recurso, "fecha_int": 20260731, "horide": horide,
                 "hora_codigo": hora, "can": can, "tot": 0.0, "synckey": None,
                 "paride": paride, "hmoide": 777, "parte_cod": "PT26/00251",
                 "parte_est": 1}
    datos.update(kw)
    return LineaSigrid(**datos)


def _escritura(cli: _Cli, tex: str | None = None,
               creados: list | None = None) -> EscrituraVinculados:
    def crear(p, d):
        (creados if creados is not None else []).append((p.ano, p.mes))
        p.existe, p.ide = True, 900 + p.mes

    return EscrituraVinculados(cli, est=1, paso_pos=64, tex=tex,
                               obra_de=lambda av: OBRA, crear_parte=crear,
                               traza=_traza)


def _ejecutar(cli: _Cli, vinculados, *, partes=(), conflictos=(),
              pisar=(), tex=None) -> ResultadoRegistro:
    res = ResultadoRegistro(ok=True, obra_destino=OBRA, forzada_pruebas=True)
    res.escritas = [{"registro_id": r}
                    for r in sorted({av.registro_id for av in vinculados})]
    _escritura(cli, tex).ejecutar(res, list(partes), list(vinculados),
                                  list(conflictos), set(pisar), {})
    return res


# ---- registro_vinculados.py:559-561, :567 · la edición, campo a campo ---- #
def test_f044_r24_editar_lleva_partida_cuenta_y_tex_de_la_linea():
    """Sin partida ni cuenta (confirmado «sin partida»): 0, no 1. Fuera de
    pruebas (`tex` None), la traza conserva el texto de la línea."""
    cli = _Cli(_ls(5201, tex="A MANO"), _ls(5202, 11))
    sin = _av(1, 10, paride=0, caa_ide=0, linea_cero={"ide": 5201})
    con = _av(2, 11, linea_cero={"ide": 5202})
    res = _ejecutar(cli, [sin, con])
    st = {p["ide"]: (p["paride"], p["caaide"], p["tex"])
          for p in cli.de("editar")}
    assert st == {5201: (0, 0, None), 5202: (81002, 90002, None)}
    despues = {t["ide"]: (t["despues"]["paride"], t["despues"]["caaide"],
                          t["despues"]["tex"]) for t in res.editadas}
    assert despues == {5201: (0, 0, "A MANO"), 5202: (81002, 90002, None)}
    assert (sin.hmores_ide, con.hmores_ide) == (5201, 5202)


# ---- registro_vinculados.py:603, :609, :616 · la inserción ------------- #
def test_f044_r24_insertar_en_el_parte_de_su_periodo_tras_el_maximo():
    sin = _av(1, 10, paride=0, caa_ide=0)
    otro = _av(2, 11)
    agosto = _av(3, 10, mes=8, fecha_int=20260831)
    partes = [ParteDestino(2026, 7, obra_cod="0404", existe=True, ide=777,
                           cod="PT26/00251"),
              ParteDestino(2026, 8, obra_cod="0404", existe=True, ide=778,
                           cod="PT26/00300")]
    cli = _Cli()
    _ejecutar(cli, [agosto, otro, sin], partes=partes)
    assert [(p["synckey"], p["hmoide"], p["pos"], p["paride"], p["caaide"])
            for p in cli.de("insert")] == [
        ("porcentajes:vin:1:10", 777, 128, 0, 0),
        ("porcentajes:vin:2:11", 777, 192, 81002, 90002),
        ("porcentajes:vin:3:10", 778, 128, 81001, 90001)]
    assert agosto.parte_cod == "PT26/00300"


# ---- registro_vinculados.py:636 · solo los pisados confirmados, suyos --- #
def test_f044_r24_no_planea_un_pisado_sin_confirmar_ni_uno_sin_escribibles():
    cli = _Cli(_ls(5101, 11, 0.5), _ls(5102, 11, 0.45))
    e = _escritura(cli)
    av = _av(1, 11)
    lineas = [cli.leer[5101], cli.leer[5102]]
    sin_confirmar = Conflicto(clave="11|202607|33|81002", recurso_ide=11,
                              nombre=None, ano=2026, mes=7, parte_cod="PT",
                              lineas=lineas, registros=[1], vinculado=VIN)
    assert e._planear([av], [sin_confirmar], set(), set()) == ({}, [], {})
    # Confirmado, pero de un registro que no se escribe (su titular cayó).
    ajeno = replace(sin_confirmar, registros=[9])
    assert e._planear([av], [ajeno], {ajeno.clave}, set()) == ({}, [], {})
    assert cli.para_editar == []


# ---- registro_vinculados.py:663-666 · la línea ya no vale --------------- #
@pytest.mark.parametrize("cambio", [
    "desaparece", "enlazada", "parte_cerrado"])
def test_f044_r24_la_linea_al_cero_que_ya_no_vale_omite_al_vinculado(cambio):
    ls = _ls(5201)
    cli = _Cli(*{"desaparece": [],
                 "enlazada": [replace(ls, enlazada=True)],
                 "parte_cerrado": [replace(ls, parte_est=3)]}[cambio])
    av = _av(1, 10, linea_cero={"ide": 5201})
    res = _ejecutar(cli, [av])
    assert (av.accion, av.motivo) == ("omitir",
                                      MOTIVO_LINEA_CAMBIADA.format(ide=5201))
    assert {"registro_id": 1, "vinculado_ide": 10,
            "motivo": av.motivo} in res.omitidas
    assert cli.de("editar") == [] and cli.de("insert") == []


def test_f044_r24_la_linea_al_cero_que_vale_se_edita():
    cli = _Cli(_ls(5201))
    av = _av(1, 10, linea_cero={"ide": 5201})
    _ejecutar(cli, [av])
    assert [p["ide"] for p in cli.de("editar")] == [5201]
    assert (av.accion, av.hmores_ide) == ("escribir", 5201)


# ---- registro_vinculados.py:688-690 · la relectura de lo editado -------- #
@pytest.mark.parametrize("can, relee", [
    (0.4, {"can": 0.4, "synckey": None}),                     # sk de antes
    (0.4, {"can": 0.0, "synckey": "porcentajes:vin:1:10"}),   # can de antes
    (0.0, {"can": 0.000001, "synckey": "porcentajes:vin:1:10"})])
def test_f044_r24_editada_que_no_quedo_como_se_escribio_se_omite(can, relee):
    cli = _Cli(_ls(5201))
    cli.relee[5201] = replace(cli.leer[5201], **relee)
    av = _av(1, 10, can=can, linea_cero={"ide": 5201})
    res = _ejecutar(cli, [av])
    assert (av.accion, av.motivo) == ("omitir",
                                      MOTIVO_LINEA_CAMBIADA.format(ide=5201))
    assert res.editadas == [] and av.hmores_ide is None


# ---- registro_vinculados.py:700 · la relectura de lo puesto a 0 --------- #
def test_f044_r24_puesta_a_cero_que_no_quedo_sale_de_a_cero():
    cli = _Cli(_ls(5101, 11, 0.45), _ls(5102, 11, 0.5))
    c = Conflicto(clave="11|202607|33|81002", recurso_ide=11, nombre=None,
                  ano=2026, mes=7, parte_cod="PT26/00251",
                  lineas=[cli.leer[5101], cli.leer[5102]], registros=[1],
                  vinculado=VIN)
    cli.relee[5102] = cli.leer[5102]            # sigue con su 0,5
    res = _ejecutar(cli, [_av(1, 11)], conflictos=[c], pisar={c.clave})
    assert [p["ide"] for p in cli.de("a_cero")] == [5102]
    assert res.a_cero == []
    assert [t["ide"] for t in res.editadas] == [5101]


def test_f044_r24_puesta_a_cero_que_quedo_sigue_en_a_cero():
    cli = _Cli(_ls(5101, 11, 0.45), _ls(5102, 11, 0.5))
    c = Conflicto(clave="11|202607|33|81002", recurso_ide=11, nombre=None,
                  ano=2026, mes=7, parte_cod="PT26/00251",
                  lineas=[cli.leer[5101], cli.leer[5102]], registros=[1],
                  vinculado=VIN)
    res = _ejecutar(cli, [_av(1, 11)], conflictos=[c], pisar={c.clave})
    assert [t["ide"] for t in res.a_cero] == [5102]


# ---- registro_vinculados.py:470-477 · el motivo de un vinculado retenido  #
def test_f044_r26_motivo_de_la_sobrecarga_y_del_sin_partida():
    base = {"clave": "k", "recurso_ide": 10, "nombre": None, "ano": 2026, "mes": 7,
                "parte_cod": "PT", "hora_codigo": "OTEL", "vinculado": VIN}
    sobre = Conflicto(**base, motivo="sobrecarga", suma_existente=0.8,
                      suma_total=1.2, nuevas=[{"can": 0.4}])
    sin = Conflicto(**base, motivo="sin_partida")
    assert motivo_de_conflicto(sobre) == (MOTIVO_SOBRECARGA_VINCULADO.format(
        tipo="TF", cod="TF-10", hora="OTEL", total=1.2, existente=0.8,
        nueva=0.4), True)
    assert motivo_de_conflicto(sin) == (MOTIVO_SIN_PARTIDA_VINCULADO.format(
        tipo="TF", cod="TF-10"), True)
    assert "TF TF-10" in motivo_de_conflicto(sin)[0]


# ---- reglas_vinculados.py:278, :88 -------------------------------------- #
def test_f044_r16_por_que_sin_ci_en_palabras_o_tal_cual():
    # F-068 (R9, R22): el texto dice también que ni el historial ni el
    # nombre decidieron (orden nuevo de la enmienda).
    assert por_que_sin_ci(MOTIVO_SIN_CI) == (
        "ninguna partida del presupuesto tiene la cuenta de su tipo y ni el "
        "historial ni el nombre deciden")
    assert por_que_sin_ci("otro motivo") == "otro motivo"
    assert por_que_sin_ci(None) == ""


def test_f044_la_partida_elegida_es_inmutable():
    with pytest.raises(dataclasses.FrozenInstanceError):
        PartidaElegida(81001).paride = 1        # type: ignore[misc]


# ============================ el preflight =============================== #
def _todas(validadas: list[list[int]]) -> set[int]:
    return {i for v in validadas for i in v}


# ---- registro_pipeline.py:645 · solo se validan las de un titular vivo -- #
def test_f044_r27_no_valida_la_elegida_de_un_titular_omitido():
    cli = ClientePre()
    pf = _pf(cli, linea(recurso_ide=300, vinculados=_v(
        10, paride=81002, partida_cod="CIGA14")))
    assert pf.acciones[0].accion == "omitir"
    assert 81002 not in _todas(cli.validadas)


# ---- registro_vinculados.py:219 · titular sin partida no es «su partida»  #
def test_f044_r16_titular_sin_partida_el_vinculado_a_la_ci_de_su_tipo():
    pf = _pf(ClientePre(), linea(categoria="X", nombre="Nadie",
                                 vinculados=_v(10)))
    assert pf.acciones[0].paride == 0
    [v] = pf.vinculados
    assert (v.paride, v.partida_cod, v.partida_metodo) == (
        81001, "CICO13", "ci_tipo")


# ---- registro_vinculados.py:239 · la elegida en postventa, hoja activa -- #
def test_f044_r15_elegida_en_postventa_capitulo_o_ajena_no_vale():
    pf = _pf(ClientePre(), linea(es_postventa=True, vinculados=[
        *_v(10, paride=69100, partida_cod="11"),            # capítulo
        *_v(11, paride=123456, partida_cod="X"),            # no es de ella
        *_v(12, paride=70002, partida_cod="0713")]))        # hoja
    v = _por(pf)
    assert (v[(1, 10)].accion, v[(1, 10)].motivo) == (
        "omitir", MOTIVO_ELEGIDA_NO_VALIDA.format(cod="11"))
    assert (v[(1, 11)].accion, v[(1, 11)].motivo) == (
        "omitir", MOTIVO_ELEGIDA_NO_VALIDA.format(cod="X"))
    assert (v[(1, 12)].paride, v[(1, 12)].partida_metodo,
            v[(1, 12)].partida_res) == (70002, "manual", "CLUB DEPORTIVO")


# ---- registro_vinculados.py:257, :264 · la propuesta guardada ----------- #
def test_f044_r15_propuesta_guardada_que_no_es_de_su_ci_no_cuenta():
    [v] = _pf(ClientePre(), linea(vinculados=_v(
        10, propuesta_paride=81002, propuesta_cod="CIGA14",
        propuesta_metodo="titular"))).vinculados
    assert (v.paride, v.partida_metodo) == (81001, "ci_tipo")


def test_f044_r15_propuesta_guardada_sin_descripcion_toma_la_del_presupuesto():
    [v] = _pf(ClientePre(), linea(vinculados=_v(
        10, propuesta_paride=81001, propuesta_cod="CICO13",
        propuesta_metodo="ci_tipo"))).vinculados
    assert (v.paride, v.partida_res) == (81001, "TELEFONIA")


# ---- registro_vinculados.py:303-306 · ya registrado por `hmores.ide` ---- #
def _con_hmores(ls: LineaSigrid):
    cli = ClientePre()
    cli.synckeys = {"en otro parte": ls}
    return _por(_pf(cli, linea(vinculados=_v(10, hmores_ide=ls.ide))))


def test_f044_r30_la_linea_de_su_hmores_ide_lo_da_por_registrado():
    v = _con_hmores(_ls_vin(5901, 10, 0.4, synckey="partes:x"))[(1, 10)]
    assert (v.accion, v.hmores_ide) == ("ya_registrado", 5901)


@pytest.mark.parametrize("cambio", [
    {"horide": 35, "hora_codigo": "OKM"},           # de otra hora
    {"synckey": "porcentajes:vin:2:10"}])           # nuestra de otro
def test_f044_r30_su_hmores_ide_de_otra_hora_o_de_otro_no_vale(cambio):
    ls = replace(_ls_vin(5901, 10, 0.4), **cambio)
    assert _con_hmores(ls)[(1, 10)].accion == "escribir"


def test_f044_r30_sin_hmores_ide_no_toma_la_linea_de_otro():
    """Dos líneas con el mismo vinculado: la de la 1 lleva su `hmores_ide`
    (1, con la `synckey` de otro sistema); la 2 no lleva ninguno."""
    cli = ClientePre()
    cli.synckeys = {"en otro parte": _ls_vin(1, 10, 0.4, synckey="partes:x")}
    v = _por(_pf(cli, linea(vinculados=_v(10, hmores_ide=1)),
                 linea(registro_id=2, es_postventa=True, porcentaje=0.6,
                       vinculados=_v(10))))
    assert (v[(1, 10)].accion, v[(2, 10)].accion) == ("ya_registrado",
                                                      "escribir")


# ---- registro_vinculados.py:369-372 · el contexto del pisado ------------ #
def test_f044_r20_contexto_solo_las_suyas_de_su_hora_que_no_chocan():
    cli = ClientePre(lineas_parte=[
        _ls_vin(5101, 11, 0.95, paride=81002),                  # choque
        _ls_vin(5102, 11, 0.0, paride=81002),                   # al 0 %
        _ls_vin(5103, 11, 0.3, paride=81003),                   # contexto
        LineaSigrid(ide=5104, reside=11, fecha_int=20260731, horide=32,
                    hora_codigo="HLPE", can=0.5, tot=None, synckey=None,
                    paride=81002),                              # otra hora
        LineaSigrid(ide=5105, reside=200, fecha_int=20260731, horide=33,
                    hora_codigo="OGAS", can=0.1, tot=None, synckey=None,
                    paride=0)])                                 # otro recurso
    [c] = [c for c in _pf(cli, linea(vinculados=_v(11))).conflictos
           if c.vinculado]
    assert [ls.ide for ls in c.lineas] == [5101]
    assert [ls.ide for ls in c.contexto] == [5103]


# ---- registro_vinculados.py:385 · el omitido no edita su línea al 0 % --- #
def test_f044_r22_omitido_por_un_cerrado_no_se_queda_su_linea_al_cero():
    cli = ClientePre(cerradas=[_ls_vin(5401, 11, 0.95, paride=81002)],
                     lineas_parte=[_ls_vin(5202, 11, 0.0, paride=81002)])
    v = _por(_pf(cli, linea(vinculados=_v(11))))[(1, 11)]
    assert v.accion == "omitir" and "PT26/00200" in v.motivo
    assert v.linea_cero is None


# ---- registro_vinculados.py:412-413 · la sobrecarga, a 4 decimales ------ #
def test_f044_r23_sobrecarga_redondeada_a_cuatro_decimales():
    cli = ClientePre(lineas_parte=[_ls_vin(5501, 11, 0.7777777,
                                           paride=81001)])
    [c] = [c for c in _pf(cli, linea(vinculados=_v(11))).conflictos
           if c.vinculado]
    assert (c.suma_existente, c.suma_total, c.exceso) == (0.7778, 1.1778,
                                                          0.1778)


# ---- registro_vinculados.py:436 · el aviso de su línea al 0 % ----------- #
def test_f044_r21_aviso_de_la_linea_al_cero_con_su_partida():
    cli = ClientePre(lineas_parte=[_ls_vin(5201, 10, 0.0, paride=81001),
                                   _ls_vin(5202, 11, 0.0, paride=70001)])
    v = _por(_pf(cli, linea(vinculados=_v(10, 11))))
    assert AVISO_LINEA_CERO.format(ide=5201, parte="PT26/00251", hora="OTEL",
                                   partida="CICO13") in v[(1, 10)].aviso
    assert AVISO_LINEA_CERO.format(ide=5202, parte="PT26/00251", hora="OGAS",
                                   partida=70001) in v[(1, 11)].aviso


# ============== registro_pipeline.py:1412 · el alta del parte ============ #
class _CreaParte(ClienteEje):
    """Sin parte en el periodo hasta que se da de alta (lo apunta)."""

    def __init__(self, **kw) -> None:
        super().__init__(parte_existe=False, **kw)
        self.altas: list[dict] = []

    def stmts_crear_parte(self, **kw):
        self.altas.append(kw)
        self.parte = ParteDestino(ano=kw["ano"], mes=kw["mes"], existe=True,
                                  ide=777, cod=kw["cod"])
        return [{"sql": "crear", "parameters": kw}]


def test_f044_r28_titular_ya_registrado_el_vinculado_da_de_alta_el_parte():
    previa = linea_previa(ide=6001, can=0.4, paride=80001,
                          synckey="porcentajes:1")
    cli = _CreaParte(synckeys={"porcentajes:1": previa})
    res = _eje(cli, linea(paride=80001, partida_cod="CI.1.10",
                          vinculados=_v(10)))
    assert res.ya_registradas == [1]
    assert [(a["desc"], a["obra"].codigo) for a in cli.altas] == [
        ("Parte PRUEBAS (PRUEBA-PORC)", "0404")]
    assert [p["synckey"] for p in cli.inserts()] == [synckey_vinculado(1, 10)]
    assert res.vinculados[0].parte_cod == cli.altas[0]["cod"]
