# tests/test_f030_r30_punta_a_punta.py
"""F-030 · R30 de punta a punta, mitad del transfer (design §13.6, T22).

La petición sale de `tests/contratos/f030_r30.json`, que es la que la api
TIENE que mandar (lo comprueba la otra mitad,
`services/dedicacion-api/tests/test_f030_r30_punta_a_punta.py`). Aquí se
ejecuta por HTTP (`app.py` y el `RegistroPipeline` reales) contra un Sigrid falso que ya tiene
el par de la incidencia 7 (9001, `CIV` el 5; 9002, `CIZ` el 9): cambiar sus
días edita en su sitio la `fec` de esas líneas, y nada más: ningún `INSERT`
ni `DELETE` (R30, R41). Ni red ni BBDD.
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from domain.models.registro_models import LineaIncidenciaSigrid, LineaSigrid

from tests.test_f030_pipeline_incidencias import ClienteEscribe

CONTRATO = json.loads(
    (Path(__file__).resolve().parents[3] / "tests" / "contratos"
     / "f030_r30.json").read_text(encoding="utf-8"))


class ClienteConElPar(ClienteEscribe):
    """El Sigrid falso con el par ya escrito en su parte (777, En
    registro): la lectura de R33 y la de F-051 R12 salen de esas líneas, y
    `stmt_editar_fecha_incidencia` les cambia la `fec` como lo haría el
    `UPDATE` (con su guarda: recurso, código, `can` 0 y `synckey`)."""

    def __init__(self, peticion: dict) -> None:
        reg = CONTRATO["registro"]
        recurso = peticion["incidencias"][0]["recurso_ide"]
        par = [LineaSigrid(ide=reg[rol]["hmores_ide"], reside=recurso,
                           fecha_int=reg[rol]["fecha_int"],
                           horide=71 if rol == "ini" else 79,
                           hora_codigo=reg[rol]["hora_codigo"], can=0.0,
                           tot=0.0, synckey=f"porcentajes:inc:7:{rol}")
               for rol in ("ini", "fin")]
        super().__init__(lineas_parte=par)

    def incidencias_del_mes(self, resides, ano, mes, hmoides=None, ides=()):
        self.leidas_inc.append((sorted(resides), ano, mes, hmoides))
        base = int(ano) * 10000 + int(mes) * 100
        out = []
        for ls in self.lineas_parte:
            if not ((ls.reside in set(resides)
                     and base < ls.fecha_int <= base + 31)
                    or ls.ide in set(ides)):
                continue
            leida = LineaIncidenciaSigrid(
                ide=ls.ide, reside=ls.reside, fecha_int=ls.fecha_int,
                hora_codigo=ls.hora_codigo, synckey=ls.synckey,
                parte_cod=self.parte.cod)
            # Las columnas del anexo (design §13.5): `can`, parte y estado.
            leida.can, leida.hmoide, leida.parte_est = (
                ls.can, int(self.parte.ide), 1)
            out.append(leida)
        return out

    @staticmethod
    def stmt_editar_fecha_incidencia(**kw):
        return {"sql": "editar_fec", "parameters": kw}

    def escribir(self, statements):
        n = super().escribir(statements)
        for st in statements:
            if st["sql"] != "editar_fec":
                continue
            kw = st["parameters"]
            for i, ls in enumerate(self.lineas_parte):
                if (ls.ide == kw["ide"] and ls.reside == kw["reside"]
                        and ls.hora_codigo == kw["hora_codigo"]
                        and not ls.can and ls.synckey == kw["synckey_leida"]):
                    self.lineas_parte[i] = replace(ls,
                                                   fecha_int=kw["fecha_int"])
        return n

    def sentencias(self) -> list[str]:
        return [s["sql"] for s in self.escritos]


@pytest.mark.parametrize("caso", CONTRATO["casos"],
                         ids=[f"{c['dias'][0]}-{c['dias'][1]}"
                              for c in CONTRATO["casos"]])
def test_f030_r30_punta_a_punta_el_transfer_edita_el_par_en_su_sitio(
        monkeypatch, caso):
    """Por HTTP, como la manda la api: `POST /api/registro/ejecutar`."""
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from interface_adapters.api import app as modulo_app

    from tests.test_f050_endpoint_propuesta import AJUSTES

    peticion = caso["peticion"]
    cli = ClienteConElPar(peticion)
    monkeypatch.setattr(modulo_app, "SigridWriteClient", lambda **kw: cli)
    http = TestClient(modulo_app.build_app(SimpleNamespace(**AJUSTES)))
    r = http.post("/api/registro/ejecutar", json=peticion)
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert [[x["rol"], x["accion"], x["fecha_int"], x.get("fec_antes")]
            for x in cuerpo["incidencias"]] == caso["esperado"]["acciones"]
    # Solo `UPDATE` de la `fec`: ni INSERT, ni DELETE, ni parte nuevo.
    assert set(cli.sentencias()) == {"editar_fec"}
    assert [[e["parameters"]["ide"], e["parameters"]["fecha_int"]]
            for e in cli.escritos] == caso["esperado"]["ediciones"]
    # Los mismos dos `ide`, con la `fec` nueva y nada más en el parte.
    assert [(ls.ide, ls.fecha_int) for ls in cli.lineas_parte] == [
        (9001, 20260700 + caso["dias"][0]), (9002, 20260700 + caso["dias"][1])]
    assert [x["hmores_ide"] for x in cuerpo["incidencias"]] == [9001, 9002]
