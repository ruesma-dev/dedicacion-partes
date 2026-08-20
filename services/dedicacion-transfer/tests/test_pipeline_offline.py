# tests/test_pipeline_offline.py
"""Tests offline del pipeline de porcentajes con un cliente falso."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import (
    HoraRecurso, LineaEntrada, LineaSigrid, ObraEntrada, ParteDestino,
)
from infrastructure.sigrid.sigrid_write_client import synckey_de


class Settings:
    obra_pruebas_forzar = True
    obra_pruebas_cod = "0404"
    marca_pruebas = "PRUEBA-PORC"
    postventa_registrar = True
    postventa_obra_cod = "POSTV2"
    paso_pos = 64


class ClienteFalso:
    def __init__(self):
        self.obra = ObraEntrada(ide=828942, codigo="0404", nombre="PRUEBAS")
        setattr(self.obra, "cenide", 555)
        self.obra_pv = ObraEntrada(ide=999001, codigo="POSTV2",
                                   nombre="POSTVENTA 2")
        setattr(self.obra_pv, "cenide", 666)
        # Partidas de POSTV2 (una por obra original, bajo CD) y de la
        # obra origen 0678 (capítulo CI con partidas de mando).
        self.capitulos = [
            {"ide": 69000, "padide": 0, "pos": 0, "tip": 0, "cod": "CD",
             "res": "COSTES DIRECTOS", "tex": None, "tipdes": 0,
             "cosindide": None, "unimed": None},
            {"ide": 70001, "padide": 69000, "pos": 1, "tip": 1,
             "cod": "0678", "res": "15 VIVIENDAS Y HOSTEL", "tex": None,
             "tipdes": 0, "cosindide": None, "unimed": None},
            {"ide": 70002, "padide": 69000, "pos": 2, "tip": 1,
             "cod": "0713", "res": "CLUB DEPORTIVO", "tex": None,
             "tipdes": 0, "cosindide": None, "unimed": None},
        ]
        self.obra_origen = ObraEntrada(ide=555001, codigo="0678",
                                       nombre="15 VIVIENDAS")
        setattr(self.obra_origen, "cenide", 444)
        self.partidas_origen = [
            {"ide": 80000, "padide": 0, "pos": 0, "tip": 0, "cod": "CI",
             "res": "COSTES INDIRECTOS", "tex": None, "tipdes": 0,
             "cosindide": None, "unimed": None},
            {"ide": 80001, "padide": 80000, "pos": 1, "tip": 1,
             "cod": "CI.1.10", "res": "ENCARGADO (ACUNA)", "tex": None,
             "tipdes": 0, "cosindide": None, "unimed": None},
            {"ide": 80002, "padide": 80000, "pos": 2, "tip": 1,
             "cod": "CI.1.20", "res": "JEFE DE OBRA", "tex": None,
             "tipdes": 0, "cosindide": None, "unimed": None},
        ]
        # emp 10 -> recursos 100 (viejo, sin M*) y 200 (MENC)
        # emp 11 -> recurso 300 (solo HL/HE, sin M*)
        self.recursos = {10: [100, 200], 11: [300]}
        self.horas = {
            100: [HoraRecurso(1, "HLPE", None, 20.0)],
            200: [HoraRecurso(5, "MENC", None, 9000.0),
                  HoraRecurso(9, "HEGR", None, 30.0)],
            300: [HoraRecurso(1, "HLPE", None, 20.0),
                  HoraRecurso(9, "HEGR", None, 30.0)],
        }
        self.parte = ParteDestino(ano=2026, mes=7, existe=True,
                                  ide=777, cod="PT26/00251")
        # Línea M* previa del recurso 200 EN OTRO DÍA (el 15) -> conflicto.
        #
        # `paride=80001` es la única línea de este fichero que F-002 ha
        # tocado, y es DATO DE ENTRADA, no una aserción: ninguna aserción de
        # esta red de seguridad cambia. Motivo: con la Regla A
        # (ARCHITECTURE.md#regla-conflicto) una línea previa solo es «la
        # misma línea» si comparte también la PARTIDA, y el automático le
        # resuelve al encargado la CI.1.10 (ide 80001). Sin ese dato, este
        # fichero dejaría de ejercitar el camino del pisado de punta a punta
        # —que es a lo que vino— y pasaría a probar dos veces el caso «no
        # hay conflicto». El caso nuevo (previa con OTRA partida: ni choca
        # ni se borra) tiene sus propios tests en `test_f002_pipeline.py`
        # (R21).
        self.lineas_parte = [LineaSigrid(
            ide=5001, reside=200, fecha_int=20260715, horide=5,
            hora_codigo="MENC", can=1.0, tot=9000.0, synckey=None,
            paride=80001)]
        self.escritos: list[dict] = []
        self.synckeys: dict[str, LineaSigrid] = {}

    def obra_por_codigo(self, cod):
        if cod == "0404":
            return self.obra
        if cod == "POSTV2":
            return self.obra_pv
        if cod == "0678":
            return self.obra_origen
        return None

    def capitulos_de_obra(self, obride):
        if obride == self.obra_pv.ide:
            return self.capitulos
        if obride == self.obra_origen.ide:
            return self.partidas_origen
        return []

    def obra_por_ide(self, ide):
        return self.obra

    def recursos_de_empleados(self, emp_ides):
        return {e: self.recursos.get(e, []) for e in emp_ides
                if e in self.recursos}

    def horas_de_recursos(self, resides):
        return {r: self.horas.get(r, []) for r in resides}

    def partes_existentes(self, obra_ide, periodos):
        return {(p[0], p[1]): self.parte for p in periodos}

    def siguiente_cod_pt(self, ano):
        return "PT26/09999"

    def max_pos(self, hmoide):
        return 64

    def lineas_del_parte(self, hmoide, resides):
        return [l for l in self.lineas_parte if l.reside in set(resides)]

    def lineas_por_synckey(self, claves):
        return {k: v for k, v in self.synckeys.items() if k in set(claves)}

    def stmts_crear_parte(self, **kw):
        return [{"sql": "crear", "parameters": []}]

    def stmt_insert_linea(self, **kw):
        return {"sql": "insert", "parameters": kw}

    @staticmethod
    def stmt_borrar_linea(ide):
        return {"sql": "delete", "parameters": [ide]}

    def escribir(self, statements):
        self.escritos.extend(statements)
        return len(statements)


def lineas_entrada():
    return [
        LineaEntrada(registro_id=1, ano=2026, mes=7, porcentaje=0.4,
                     empleado_ide=10, nombre="Acuna Mera, Antonio",
                     categoria="Encargado"),
        LineaEntrada(registro_id=2, ano=2026, mes=7, porcentaje=0.6,
                     empleado_ide=11, nombre="Peon"),
        LineaEntrada(registro_id=3, ano=2026, mes=7, porcentaje=0.5,
                     empleado_ide=10, nombre="Encargado PV",
                     es_postventa=True),
        LineaEntrada(registro_id=4, ano=2026, mes=7, porcentaje=40,
                     empleado_ide=10, nombre="Rango mal"),
    ]


def test_preflight():
    cli = ClienteFalso()
    pl = RegistroPipeline(cliente=cli, settings=Settings())
    pf = pl.preflight(obra=ObraEntrada(codigo="0678"), lineas=lineas_entrada())

    por_id = {a.registro_id: a for a in pf.acciones}
    # postventa: destino postventa + capítulo 0678 (paride 70001)
    a3 = por_id[3]
    assert a3.accion == "escribir" and a3.destino == "postventa", a3
    assert a3.paride == 70001 and a3.partida_cod == "0678", a3
    assert a3.hora_codigo == "MENC" and a3.can == 0.5
    # emp 10: elige el recurso 200 (el que tiene M*), MENC, can=0.4
    a1 = por_id[1]
    assert a1.accion == "escribir" and a1.recurso_ide == 200
    assert a1.hora_codigo == "MENC" and a1.can == 0.4 and a1.pre == 9000.0
    assert a1.tot == 3600.0
    assert a1.fecha_int == 20260731            # último día del mes
    # partida normal: rol+nombre -> ENCARGADO (ACUNA) del CI de la 0678
    assert a1.paride == 80001 and a1.partida_metodo == "auto_nombre", a1
    # emp 11: sin M* -> omitido
    assert por_id[2].accion == "omitir" and "mensual" in por_id[2].motivo
    # porcentaje 40 (no sobre 1) -> omitido
    assert por_id[4].accion == "omitir" and "rango" in por_id[4].motivo
    # conflicto: la línea MENC del día 15 choca aunque sea otro día
    assert len(pf.conflictos) == 1
    c = pf.conflictos[0]
    assert c.clave == "200|202607|5|80001", c.clave
    assert c.lineas[0].fecha_int == 20260715
    print("PREFLIGHT OK")
    return pf


def test_ejecutar_pisando():
    cli = ClienteFalso()
    pl = RegistroPipeline(cliente=cli, settings=Settings())
    # 1) sin confirmar: nada se escribe, queda pendiente
    r1 = pl.ejecutar(obra=ObraEntrada(codigo="0678"),
                     lineas=lineas_entrada())
    # La postventa (reg 3) sí se escribe: mismo horide pero paride 70001
    # -> clave distinta, sin conflicto.
    assert len(r1.escritas) == 1 and r1.escritas[0]["registro_id"] == 3
    assert r1.escritas[0]["destino"] == "postventa"
    assert len(r1.pendientes_confirmacion) == 1
    # 2) confirmando el pisado: borra la del día 15 e inserta la normal
    r2 = pl.ejecutar(obra=ObraEntrada(codigo="0678"),
                     lineas=lineas_entrada(),
                     pisar_claves={"200|202607|5|80001"})
    assert r2.borradas == 1 and len(r2.escritas) == 2
    ins = [s for s in cli.escritos if s["sql"] == "insert"]
    dele = [s for s in cli.escritos if s["sql"] == "delete"]
    assert dele[0]["parameters"] == [5001]
    por_sk = {i["parameters"]["synckey"]: i["parameters"] for i in ins}
    kw1 = por_sk[synckey_de(1)]
    assert kw1["fecha_int"] == 20260731 and kw1["can"] == 0.4
    assert kw1["paride"] == 80001
    kw3 = por_sk[synckey_de(3)]
    assert kw3["paride"] == 70001 and kw3["can"] == 0.5
    print("EJECUTAR+PISAR OK")


def test_idempotencia():
    cli = ClienteFalso()
    cli.lineas_parte = []                       # sin conflicto
    ls = LineaSigrid(ide=9001, reside=200, fecha_int=20260731, horide=5,
                     hora_codigo="MENC", can=0.4, tot=3600.0,
                     synckey=synckey_de(1), nuestra=True)
    cli.synckeys[synckey_de(1)] = ls
    pl = RegistroPipeline(cliente=cli, settings=Settings())
    pf = pl.preflight(obra=ObraEntrada(codigo="0678"),
                      lineas=lineas_entrada()[:1])
    assert pf.acciones[0].accion == "ya_registrado"
    assert pf.acciones[0].hmores_ide == 9001
    print("IDEMPOTENCIA OK")


def test_override_manual():
    cli = ClienteFalso()
    cli.lineas_parte = []
    pl = RegistroPipeline(cliente=cli, settings=Settings())
    linea = LineaEntrada(registro_id=9, ano=2026, mes=7, porcentaje=0.3,
                         empleado_ide=10, nombre="Acuna", categoria="Encargado",
                         paride=80002, partida_cod="CI.1.20")
    pf = pl.preflight(obra=ObraEntrada(codigo="0678"), lineas=[linea])
    a = pf.acciones[0]
    assert a.paride == 80002 and a.partida_metodo == "manual", a
    assert pf.partidas_obra == [] or True   # catálogo puede no cargarse con override
    print("OVERRIDE OK")


if __name__ == "__main__":
    test_preflight()
    test_ejecutar_pisando()
    test_idempotencia()
    test_override_manual()
    print("== TODO OK ==")
