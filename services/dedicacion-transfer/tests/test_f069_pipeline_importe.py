# tests/test_f069_pipeline_importe.py
"""F-069 · el pipeline con vinculados de cantidad y comentarios.

- R23 (T3): el `tex` de la línea escrita (titular o vinculado) es su
  comentario; en modo pruebas, la marca seguida del comentario. Sin
  comentario, como hoy: vacía al insertar (None al cliente) y la de antes al
  editar.
- R24 (T1): sin `importe_mensual` ni `comentario`, todo como en F-044: las
  mismas sentencias, valores y lecturas.
- R25-R28 (T4): pisado y capacidad de F-044/F-064 (la caja, `can` 1, más
  una a mano de esa obra con su hora ⇒ sobrecarga a confirmar); ya
  registrado aunque cambie la cantidad o el comentario; el lote da lo mismo
  que la suelta; la respuesta lleva `km`, `precio_km` y `reparto`.

Sin red ni BBDD; los `ide` son inventados.
"""
from __future__ import annotations

from dataclasses import asdict, replace
from typing import Any

from application.pipelines.registro_lote import RegistroLote
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.texto_linea import tex_de
from domain.models.registro_models import (
    HoraRecurso,
    LineaSigrid,
    ObraEntrada,
    VinculadoEntrada,
)

from tests.conftest import OBRA_ORIGEN, ClienteFalso, SettingsFalso, linea, \
    linea_previa
from tests.test_f044_pipeline_vinculados import ClienteEje
from tests.test_f055_lote import _ajustes

#: Horas por defecto de los vinculados de cantidad, con `pre` 0 (como en
#: Sigrid) y la cuenta de su hora.
HORAS_CANT = {
    20: [HoraRecurso(41, "KM", None, 0.0, caa_cod="RES.CI.4.13",
                     defecto=True)],
    22: [HoraRecurso(43, "CO", None, 0.0, caa_cod="RES.CI.4.13",
                     defecto=True)],
}


class ClienteCant(ClienteEje):
    """`ClienteEje` con las horas de los vinculados de cantidad."""

    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self.horas = {**self.horas, **HORAS_CANT}


def _km(**kw) -> VinculadoEntrada:
    datos = dict(recurso_ide=20, tipo="VP", tipo_res="KILOMETROS",
                 cod="VP0020", paride=81001, partida_cod="CICO13",
                 importe_mensual=True, unidad="km", reparto="pct",
                 cantidad=100.0, copiado=False, comentario=None,
                 precio_km=0.2)
    datos.update(kw)
    return VinculadoEntrada(**datos)


def _caja(**kw) -> VinculadoEntrada:
    datos = dict(recurso_ide=22, tipo="CAJA", tipo_res="CAJA OBRA",
                 cod="CA0022", paride=81001, partida_cod="CICO13",
                 importe_mensual=True, unidad="eur", reparto="obra",
                 cantidad=80.0)
    datos.update(kw)
    return VinculadoEntrada(**datos)


def _titular(**kw):
    return linea(paride=80001, partida_cod="CI.1.10", **kw)


def _eje(cli: ClienteFalso, *lineas_, pisar: set[str] | None = None,
         real: bool = False):
    st = SettingsFalso(obra_pruebas_forzar=False) if real else SettingsFalso()
    return RegistroPipeline(cliente=cli, settings=st).ejecutar(
        obra=ObraEntrada(codigo=OBRA_ORIGEN), lineas=list(lineas_),
        pisar_claves=pisar or set())


def _pf(cli: ClienteFalso, *lineas_):
    return RegistroPipeline(cliente=cli, settings=SettingsFalso()).preflight(
        obra=ObraEntrada(codigo=OBRA_ORIGEN), lineas=list(lineas_))


def _escritas(cli) -> list[dict]:
    return [s["parameters"] for x in cli.llamadas for s in x]


def _por_sk(cli) -> dict[str, dict]:
    return {p["synckey"]: p for p in _escritas(cli) if "synckey" in p}


# =============================== R23 · tex =============================== #
def test_f069_r23_tex_de():
    assert tex_de("visita a proveedor", None) == "visita a proveedor"
    assert tex_de("  visita  ", "PRUEBA-PORC") == "PRUEBA-PORC visita"
    assert tex_de(None, "PRUEBA-PORC") == "PRUEBA-PORC"
    assert tex_de("   ", "PRUEBA-PORC") == "PRUEBA-PORC"
    assert tex_de(None, None) is None
    assert tex_de("", "") is None


def test_f069_r23_modo_real_el_tex_es_el_comentario():
    cli = ClienteCant()
    _eje(cli, _titular(comentario="mes con visita",
                       vinculados=[_km(comentario="visita a proveedor")]),
         real=True)
    sk = _por_sk(cli)
    assert sk["porcentajes:1"]["tex"] == "mes con visita"
    assert sk["porcentajes:vin:1:20"]["tex"] == "visita a proveedor"


def test_f069_r23_modo_pruebas_marca_y_comentario():
    cli = ClienteCant()
    _eje(cli, _titular(comentario="mes con visita",
                       vinculados=[_km(comentario="visita a proveedor"),
                                   _caja()]))
    sk = _por_sk(cli)
    assert sk["porcentajes:1"]["tex"] == "PRUEBA-PORC mes con visita"
    assert sk["porcentajes:vin:1:20"]["tex"] == (
        "PRUEBA-PORC visita a proveedor")
    assert sk["porcentajes:vin:1:22"]["tex"] == "PRUEBA-PORC"


def test_f069_r23_sin_comentario_como_hoy():
    cli = ClienteCant()
    _eje(cli, _titular(vinculados=[_km()]), real=True)
    assert {k: p["tex"] for k, p in _por_sk(cli).items()} == {
        "porcentajes:1": None, "porcentajes:vin:1:20": None}


def test_f069_r23_al_editar_sin_comentario_conserva_y_con_el_lo_pone():
    previa = linea_previa(ide=5301, can=0.0, tex="lo de antes")
    cli = ClienteCant(lineas_parte=[previa])
    res = _eje(cli, _titular(), real=True)
    [e] = [s["parameters"] for s in cli.llamadas[0]]
    assert (e["ide"], e["tex"]) == (5301, None)
    assert res.editadas[0]["despues"]["tex"] == "lo de antes"
    cli = ClienteCant(lineas_parte=[replace(previa, can=0.0)])
    res = _eje(cli, _titular(comentario="nuevo"), real=True)
    [e] = [s["parameters"] for s in cli.llamadas[0]]
    assert e["tex"] == "nuevo"
    assert res.editadas[0]["despues"]["tex"] == "nuevo"


def test_f069_r23_el_vinculado_al_editar_su_linea_al_cero():
    cero = LineaSigrid(ide=5201, reside=20, fecha_int=20260731, horide=41,
                       hora_codigo="KM", can=0.0, tot=None, synckey=None,
                       paride=81001, tex="antiguo")
    cli = ClienteCant(lineas_parte=[cero])
    res = _eje(cli, _titular(vinculados=[_km(comentario="km del mes")]),
               real=True)
    [e] = [s["parameters"] for s in cli.llamadas[-1]]
    assert (e["ide"], e["tex"], e["can"], e["pre"]) == (5201, "km del mes",
                                                        0.4, 20.0)
    [t] = [t for t in res.editadas if t.get("vinculado_ide")]
    assert t["despues"]["tex"] == "km del mes"


# ====================== R24 · sin claves, F-044 tal cual ================= #
def test_f069_r24_sin_las_claves_mismas_sentencias_y_lecturas():
    from interface_adapters.api.app import LineaIn

    def correr(vinculado: dict):
        cli = ClienteCant()
        entrada = LineaIn.model_validate({
            "registro_id": 1, "ano": 2026, "mes": 7, "porcentaje": 0.4,
            "recurso_ide": 200, "nombre": "Acuna Mera, Antonio",
            "categoria": "Encargado", "empresa": 1, "paride": 80001,
            "partida_cod": "CI.1.10", "vinculados": [vinculado]})
        res = _eje(cli, entrada.para_pipeline())
        return cli, res

    viejo = {"recurso_ide": 10, "tipo": "TF", "cod": "TF-10"}
    nuevo = {**viejo, "importe_mensual": False, "unidad": None,
             "reparto": None, "cantidad": None, "copiado": False,
             "comentario": None, "precio_km": None}
    (c1, r1), (c2, r2) = correr(viejo), correr(nuevo)
    assert c1.llamadas == c2.llamadas
    assert c1.horas_leidas == c2.horas_leidas
    assert c1.registradas == c2.registradas
    assert c1.lecturas_lineas == c2.lecturas_lineas
    assert [asdict(v) for v in r1.vinculados] == [
        asdict(v) for v in r2.vinculados]
    [v] = r1.vinculados
    assert (v.pre, v.tot, v.km, v.precio_km, v.reparto) == (
        30.0, 12.0, None, None, None)


# ====================== R25 · pisado y capacidad ========================= #
def _caja_a_mano(ide: int = 5801, can: float = 1.0) -> LineaSigrid:
    return LineaSigrid(ide=ide, reside=22, fecha_int=20260731, horide=43,
                       hora_codigo="CO", can=can, tot=50.0, synckey=None,
                       paride=81002)


def test_f069_r25_caja_mas_una_a_mano_de_su_hora_sobrecarga_a_confirmar():
    cli = ClienteCant(lineas_parte=[_caja_a_mano()])
    pf = _pf(cli, _titular(vinculados=[_caja()]))
    [c] = [c for c in pf.conflictos if c.vinculado]
    assert (c.motivo, c.recurso_ide, c.suma_existente, c.suma_total) == (
        "sobrecarga", 22, 1.0, 2.0)
    assert [ls.ide for ls in c.contexto] == [5801]
    res = _eje(ClienteCant(lineas_parte=[_caja_a_mano()]),
               _titular(vinculados=[_caja()]))
    [v] = res.vinculados
    assert v.accion == "omitir" and "sobrecarga" in v.motivo
    res = _eje(cli := ClienteCant(lineas_parte=[_caja_a_mano()]),
               _titular(vinculados=[_caja()]), pisar={c.clave})
    assert _por_sk(cli)["porcentajes:vin:1:22"]["can"] == 1.0
    assert cli.borrados() == []


def test_f069_r25_caja_sola_no_sobrecarga_y_km_tampoco():
    pf = _pf(ClienteCant(), _titular(vinculados=[_caja(), _km()]))
    assert not [c for c in pf.conflictos if c.vinculado]
    assert {(v.recurso_ide, v.accion) for v in pf.vinculados} == {
        (22, "escribir"), (20, "escribir")}


def test_f069_r25_choque_con_su_identidad_es_pisado_a_confirmar():
    previa = replace(_caja_a_mano(), paride=81001, can=1.0)
    pf = _pf(ClienteCant(lineas_parte=[previa]),
             _titular(vinculados=[_caja()]))
    [c] = [c for c in pf.conflictos if c.vinculado]
    assert c.motivo == "pisado" and [ls.ide for ls in c.lineas] == [5801]


# ========================== R26 · ya registrado ========================== #
def test_f069_r26_ya_registrado_aunque_cambie_la_cantidad_o_el_comentario():
    previa = LineaSigrid(ide=5901, reside=20, fecha_int=20260731, horide=41,
                         hora_codigo="KM", can=0.4, tot=8.0,
                         synckey="porcentajes:vin:1:20", paride=81001,
                         tex="otro")
    cli = ClienteCant(synckeys={"porcentajes:vin:1:20": previa})
    res = _eje(cli, _titular(vinculados=[_km(cantidad=350.0,
                                             comentario="cambiado")]))
    [v] = res.vinculados
    assert (v.accion, v.hmores_ide) == ("ya_registrado", 5901)
    assert "porcentajes:vin:1:20" not in _por_sk(cli)


# ========================= R27 · suelto = lote =========================== #
def test_f069_r27_el_lote_da_lo_mismo_que_la_suelta():
    peticion = (ObraEntrada(codigo=OBRA_ORIGEN),
                [_titular(comentario="c", vinculados=[_km(), _caja()])])
    suelto = _pf(ClienteCant(), *peticion[1])
    [lote] = RegistroLote(cliente=ClienteCant(),
                          settings=_ajustes()).preflight([peticion])
    assert [asdict(v) for v in lote.vinculados] == [
        asdict(v) for v in suelto.vinculados]
    assert [(v.pre, v.tot, v.km) for v in lote.vinculados] == [
        (20.0, 8.0, 100.0), (80.0, 80.0, None)]


# ======================= R28 · la respuesta ============================== #
def test_f069_r28_la_respuesta_lleva_km_precio_km_y_reparto():
    from interface_adapters.api.app import _respuesta_preflight

    pf = _pf(ClienteCant(), _titular(vinculados=[
        _km(), _caja(), VinculadoEntrada(recurso_ide=10, tipo="TF",
                                         cod="TF-10")]))
    r = _respuesta_preflight(pf)
    por = {v["recurso_ide"]: v for v in r["vinculados"]}
    assert {k: por[20][k] for k in ("km", "precio_km", "reparto", "pre",
                                    "tot", "can")} == {
        "km": 100.0, "precio_km": 0.2, "reparto": "pct", "pre": 20.0,
        "tot": 8.0, "can": 0.4}
    assert {k: por[22][k] for k in ("km", "precio_km", "reparto")} == {
        "km": None, "precio_km": None, "reparto": "obra"}
    assert {k: por[10][k] for k in ("km", "precio_km", "reparto")} == {
        "km": None, "precio_km": None, "reparto": None}


def test_f069_r28_ejecutar_publica_las_mismas_claves():
    res = _eje(ClienteCant(), _titular(vinculados=[_km()]))
    [v] = res.vinculados
    assert (v.accion, v.km, v.precio_km, v.reparto) == (
        "escribir", 100.0, 0.2, "pct")


# ================== R23 · el script de pruebas, por prefijo ============== #
def test_f069_r23_limpiar_busca_la_marca_como_prefijo(capsys):
    import prueba_escritura_porcentajes as script

    from tests.test_f044_sql_vinculados import _ScriptFalso

    filas = [{"ide": 1, "hmoide": 777, "reside": 20, "fec": 20261130,
              "can": 0.6, "synckey": "porcentajes:vin:9:20"}]
    cli = _ScriptFalso(filas)
    script.fase_limpiar(cli, SettingsFalso(), False)
    [(sql, params)] = cli.lecturas
    assert "CAST(tex AS NVARCHAR(400)) LIKE ?" in sql
    assert "= ?" not in sql
    assert params[0] == "PRUEBA-PORC%"
    # Con comentario, el `tex` es «marca comentario»: casa con el prefijo.
    assert "PRUEBA-PORC visita a proveedor".startswith(params[0][:-1])
    assert cli.escritos == []
    assert "Líneas marcadas 'PRUEBA-PORC' de este hilo: 1" in (
        capsys.readouterr().out)
