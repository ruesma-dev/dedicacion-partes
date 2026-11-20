# tests/test_f069_existentes_tex.py
"""F-069 · T14: `POST /api/porcentajes/existentes` publica el `tex` de cada
línea y, en UNA lectura más, las líneas del periodo con `synckey`
`porcentajes:vin:` con su `tex` (R31, D15, D16).

- La lectura de las mensuales gana `CAST(h.tex AS NVARCHAR(400)) AS tex`.
- La nueva (`lineas_por_synckey_del_periodo`) va parametrizada (el prefijo
  es un `?`, nunca concatenado), con los mismos filtros de parte, periodo y
  empresa, y un `truncated` lanza.
- La respuesta gana `vinculados_registrados` (`hmores_ide`, `recurso_ide`,
  `synckey`, `tex`) y `tex` en cada línea.

Sin red ni BBDD.
"""
from __future__ import annotations

import pytest
from application.services.porcentajes_existentes import (
    PREFIJO_VINCULADOS,
    PorcentajesExistentes,
)
from domain.models.registro_models import LineaVinculadoSigrid

from tests.test_f050_propuesta import _cliente_historial
from tests.test_f054_lectura_mensuales import BASE, FILA
from tests.test_f054_traduccion import (
    O0678,
    ClienteExistentes,
    _l,
    ajustes_var,
)

SQL_VIN = (
    "SELECT h.ide AS ide, h.reside AS reside, h.synckey AS synckey, "
    "CAST(h.tex AS NVARCHAR(400)) AS tex "
    "FROM hmores h JOIN hmo m ON m.ide = h.hmoide JOIN con c ON c.ide = m.ide "
    "JOIN con co ON co.ide = m.obride "
    "WHERE c.tip = ? AND ISNULL(m.reside, 0) = 0 AND m.ano = ? AND m.mes = ? "
    "AND co.emp = ? AND h.synckey LIKE ? ORDER BY h.ide")


class ClienteTex(ClienteExistentes):
    """`ClienteExistentes` con las líneas de los vinculados del periodo y
    cada lectura suya anotada."""

    def __init__(self, mensuales=(), vinculados=(), **kw) -> None:
        super().__init__(mensuales, **kw)
        self.vin = list(vinculados)
        self.leidas_vin: list[tuple] = []

    def lineas_por_synckey_del_periodo(self, empresa, ano, mes, prefijo):
        self.leidas_vin.append((empresa, ano, mes, prefijo))
        return list(self.vin)


# ========================= la lectura de Sigrid ========================== #
def test_f069_r31_las_mensuales_traen_el_tex():
    cli, falso = _cliente_historial([{**FILA, "tex": "  visita  "}],
                                    tip_parte=35)
    [ls] = cli.lineas_mensuales_del_periodo(1, 2026, 9)
    [(sql, _)] = falso.llamadas
    assert "h.synckey AS synckey, CAST(h.tex AS NVARCHAR(400)) AS tex " in sql
    assert sql == BASE + " AND a.cod LIKE 'M%' ORDER BY h.ide"
    assert ls.tex == "visita"
    cli, _ = _cliente_historial([{**FILA, "tex": None}])
    assert cli.lineas_mensuales_del_periodo(1, 2026, 9)[0].tex is None


def test_f069_r31_lectura_de_vinculados_parametrizada():
    filas = [{"ide": "9101", "reside": "20", "synckey": " porcentajes:vin:7:20 ",
              "tex": "PRUEBA-PORC km"},
             {"ide": 9102, "reside": 22, "synckey": "porcentajes:vin:7:22",
              "tex": "   "}]
    cli, falso = _cliente_historial(filas, tip_parte=35)
    r = cli.lineas_por_synckey_del_periodo(1, 2026, 11, "porcentajes:vin:")
    [(sql, params)] = falso.llamadas
    assert sql == SQL_VIN
    assert params == [35, 2026, 11, 1, "porcentajes:vin:%"]
    assert "porcentajes:vin:" not in sql            # nunca concatenado
    assert r == [
        LineaVinculadoSigrid(hmores_ide=9101, recurso_ide=20,
                             synckey="porcentajes:vin:7:20",
                             tex="PRUEBA-PORC km"),
        LineaVinculadoSigrid(hmores_ide=9102, recurso_ide=22,
                             synckey="porcentajes:vin:7:22", tex=None)]


def test_f069_r31_truncated_lanza(monkeypatch):
    from infrastructure.sigrid import sigrid_write_client as modulo

    class Respuesta:
        status_code = 200
        text = ""

        @staticmethod
        def json():
            return {"ok": True, "truncated": True, "columns": ["ide"],
                    "rows": [[1]]}

    monkeypatch.setattr(modulo.httpx, "post", lambda *a, **kw: Respuesta())
    cli = modulo.SigridWriteClient(base_url="http://sigrid.invalid",
                                   function_key="sin-clave",
                                   database="ruesma")
    with pytest.raises(RuntimeError, match="truncada"):
        cli.lineas_por_synckey_del_periodo(1, 2026, 11, "porcentajes:vin:")


# ============================ el contrato ================================ #
def test_f069_r31_calcular_una_lectura_mas_y_el_tex_en_cada_linea():
    vin = [LineaVinculadoSigrid(9101, 20, "porcentajes:vin:7:20", "km")]
    cli = ClienteTex([_l(2, 694, "0694", paride=2105)], vin)
    r = PorcentajesExistentes(cliente=cli, settings=ajustes_var()).calcular(
        1, 2026, 9, [O0678])
    assert cli.leidas_vin == [(1, 2026, 9, PREFIJO_VINCULADOS)]
    assert PREFIJO_VINCULADOS == "porcentajes:vin:"
    assert len(cli.leidas_mensuales) == 1
    assert r["vinculados_registrados"] == [
        {"hmores_ide": 9101, "recurso_ide": 20,
         "synckey": "porcentajes:vin:7:20", "tex": "km"}]
    assert r["lineas"][0]["tex"] is None


def test_f069_r31_el_tex_de_la_linea_viaja():
    from dataclasses import replace
    cli = ClienteTex([replace(_l(2, 694, "0694"), tex="mes con visita")])
    r = PorcentajesExistentes(cliente=cli, settings=ajustes_var()).calcular(
        1, 2026, 9, [O0678])
    assert r["lineas"][0]["tex"] == "mes con visita"
    assert r["vinculados_registrados"] == []


def test_f069_r31_un_fallo_de_la_lectura_nueva_sube():
    class Falla(ClienteTex):
        def lineas_por_synckey_del_periodo(self, *a):
            raise RuntimeError("sigrid-api caída")

    with pytest.raises(RuntimeError, match="caída"):
        PorcentajesExistentes(cliente=Falla(), settings=ajustes_var()
                              ).calcular(1, 2026, 9, [O0678])


# ================= D17 · el transfer publica el tex sin su marca ========== #
def test_f069_r31_comentario_de_tex_quita_la_marca_y_los_espacios():
    from application.services.texto_linea import comentario_de_tex
    assert comentario_de_tex("PRUEBA-PORC visita", "PRUEBA-PORC") == "visita"
    assert comentario_de_tex("  PRUEBA-PORC   visita  ", "PRUEBA-PORC") == (
        "visita")
    assert comentario_de_tex("PRUEBA-PORC", "PRUEBA-PORC") is None
    assert comentario_de_tex("PRUEBA-PORC  ", "PRUEBA-PORC") is None
    assert comentario_de_tex("visita PRUEBA-PORC", "PRUEBA-PORC") == (
        "visita PRUEBA-PORC")                       # solo al principio
    assert comentario_de_tex("  visita ", "PRUEBA-PORC") == "visita"
    assert comentario_de_tex("   ", "PRUEBA-PORC") is None
    assert comentario_de_tex(None, "PRUEBA-PORC") is None
    assert comentario_de_tex("PRUEBA-PORC visita", None) == (
        "PRUEBA-PORC visita")                       # sin marca, tal cual
    assert comentario_de_tex("PRUEBA-PORC visita", "") == "PRUEBA-PORC visita"


def test_f069_r31_existentes_publica_el_tex_sin_la_marca():
    from dataclasses import replace
    vin = [LineaVinculadoSigrid(9101, 20, "porcentajes:vin:7:20",
                                "PRUEBA-PORC km de obra"),
           LineaVinculadoSigrid(9102, 22, "porcentajes:vin:7:22",
                                "PRUEBA-PORC"),
           LineaVinculadoSigrid(9103, 23, "porcentajes:vin:7:23", "sin marca")]
    cli = ClienteTex([replace(_l(2, 694, "0694"), tex="PRUEBA-PORC visita"),
                      replace(_l(3, 695, "0695"), tex="PRUEBA-PORC")], vin)
    r = PorcentajesExistentes(cliente=cli, settings=ajustes_var()).calcular(
        1, 2026, 9, [O0678])
    assert [x["tex"] for x in r["lineas"]] == ["visita", None]
    assert [v["tex"] for v in r["vinculados_registrados"]] == [
        "km de obra", None, "sin marca"]


def test_f069_r31_quita_la_marca_de_los_settings():
    from dataclasses import replace
    vin = [LineaVinculadoSigrid(9101, 20, "porcentajes:vin:7:20",
                                "OTRA-MARCA km"),
           LineaVinculadoSigrid(9102, 22, "porcentajes:vin:7:22",
                                "PRUEBA-PORC km")]
    cli = ClienteTex([replace(_l(2, 694, "0694"), tex="OTRA-MARCA visita")],
                     vin)
    r = PorcentajesExistentes(
        cliente=cli, settings=ajustes_var(marca_pruebas="OTRA-MARCA")
    ).calcular(1, 2026, 9, [O0678])
    assert r["lineas"][0]["tex"] == "visita"
    assert [v["tex"] for v in r["vinculados_registrados"]] == [
        "km", "PRUEBA-PORC km"]
