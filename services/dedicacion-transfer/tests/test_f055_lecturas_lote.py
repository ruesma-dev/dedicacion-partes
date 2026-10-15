# tests/test_f055_lecturas_lote.py
"""F-055 · T6: `LecturasDelLote` (R20, R22-R24; design §2 y §5.2).

- R20: `precargar` lee agrupado, en rondas A-C, lo que pedirán las obras.
- R22: lo precargado responde solo si la consulta está entera dentro; si
  no, va al cliente real (nunca vacío ni datos de otra consulta) y cuenta
  como fallo de memoria.
- R23: hasta `limite` lecturas a la vez (1 = en serie); el ajuste
  `SIGRID_LECTURAS_PARALELAS` vale 4 y fuera de 1-8 el transfer no arranca.
- R24: una lectura agrupada que falla hace fallar la precarga; una
  compartida, solo a quien la pide.
- Un solo vuelo por clave; `escribir` prohibido; la medición de F-055 R1
  sigue a las lecturas hechas en los hilos.

Sin red ni BBDD; `ClienteFalso` de `conftest.py` que anota cada llamada.
"""
from __future__ import annotations

import threading
import time

import pytest
from application.services.lecturas_lote import LecturasDelLote
from domain.models.registro_models import ObraEntrada
from infrastructure.sigrid.sigrid_write_client import (
    apuntar_lectura,
    medir_lecturas,
    synckey_de,
)

from tests.conftest import (
    OBRA_ORIGEN,
    OBRA_POSTVENTA,
    OBRA_PRUEBAS,
    ClienteFalso,
    SettingsFalso,
    linea,
    linea_previa,
)
from tests.test_f050_pipeline import _h

LECTURAS = (
    "obra_por_ide", "obras_por_ide", "obra_por_codigo", "capitulos_de_obra",
    "horas_de_recursos", "validar_partidas", "partidas_de_lineas",
    "lineas_por_synckey", "historial_partidas", "partes_del_periodo",
    "partes_de_periodos", "lineas_del_parte", "lineas_de_partes",
    "cuentas_de_centro", "siguiente_cod_pt")


class ClienteQueAnota(ClienteFalso):
    """Anota cada lectura (nombre, args) y, si se pide, la hace lenta para
    ver cuántas van a la vez. Con historial propio."""

    def __init__(self, *, espera: float = 0.0, historial=(), **kw) -> None:
        super().__init__(**kw)
        self.llamadas: list[tuple] = []
        self.espera = espera
        self.historial = list(historial)
        self._en_vuelo = 0
        self.max_a_la_vez = 0
        self._mutex = threading.Lock()
        self._hilo = threading.local()
        self.obra_origen.ide = 555001
        for nombre in LECTURAS:
            setattr(self, nombre, self._anotada(nombre,
                                                getattr(self, nombre)))

    def historial_partidas(self, resides, desde, hasta):
        return [l for l in self.historial if l.reside in set(resides)]

    def obra_por_ide(self, ide):
        return {555001: self.obra_origen}.get(int(ide), self.obra)

    def _anotada(self, nombre, lectura):
        def anotada(*a):
            # Las agrupadas del doble llaman a sus sueltas: solo cuenta la de
            # fuera, que es la que haría el cliente real.
            if getattr(self._hilo, "dentro", False):
                return lectura(*a)
            self._hilo.dentro = True
            try:
                return medida(*a)
            finally:
                self._hilo.dentro = False

        def medida(*a):
            with self._mutex:
                self.llamadas.append((nombre,) + a)
                self._en_vuelo += 1
                self.max_a_la_vez = max(self.max_a_la_vez, self._en_vuelo)
            try:
                if self.espera:
                    time.sleep(self.espera)
                r = lectura(*a)
                apuntar_lectura(nombre, 0, 0.0)
                return r
            finally:
                with self._mutex:
                    self._en_vuelo -= 1
        return anotada

    def nombres(self) -> list[str]:
        return [c[0] for c in self.llamadas]


def _peticiones(*lineas_por_obra, codigo=False):
    obra = (ObraEntrada(codigo=OBRA_ORIGEN) if codigo
            else ObraEntrada(ide=555001, codigo=OBRA_ORIGEN))
    return [(obra, list(ls)) for ls in lineas_por_obra]


def _precargado(cli, peticiones, limite=4, **ajustes):
    m = LecturasDelLote(cli, limite)
    m.precargar(peticiones, SettingsFalso(**ajustes))
    return m


ELEGIDA = dict(paride=80002, partida_cod="CI.1.20")


# ========================= R20 · las rondas A-C ========================== #
def test_f055_r20_precarga_agrupada_una_lectura_por_tipo():
    cli = ClienteQueAnota()
    cli.lineas_parte = [linea_previa()]
    _precargado(cli, _peticiones(
        [linea(registro_id=1, **ELEGIDA)],
        [linea(registro_id=2, recurso_ide=400, **ELEGIDA)]))
    assert sorted(cli.nombres()) == sorted([
        "obras_por_ide", "obra_por_codigo", "horas_de_recursos",
        "lineas_por_synckey", "validar_partidas", "partes_de_periodos",
        "lineas_de_partes"])
    assert ("horas_de_recursos", [200, 400]) in cli.llamadas
    assert ("lineas_por_synckey", [synckey_de(1), synckey_de(2)]) \
        in cli.llamadas
    assert ("partes_de_periodos", [cli.obra.ide], [(2026, 7)]) \
        in cli.llamadas
    assert ("lineas_de_partes", [777], [200, 400]) in cli.llamadas


def test_f055_r20_las_rondas_van_en_orden():
    cli = ClienteQueAnota()
    _precargado(cli, _peticiones([linea(**ELEGIDA)]), limite=1)
    n = cli.nombres()
    ronda_a = ("obras_por_ide", "obra_por_codigo", "horas_de_recursos",
               "lineas_por_synckey")
    ronda_b = ("partes_de_periodos", "validar_partidas")
    assert min(n.index(x) for x in ronda_b) > max(n.index(x)
                                                  for x in ronda_a)
    assert n.index("lineas_de_partes") > max(n.index(x) for x in ronda_b)


def test_f055_c2_cada_ronda_de_una_obra_con_elegidas_cabe_en_4(monkeypatch):
    """Rondas medidas por estructura, no por reloj: cada `_ronda` son
    ceil(tareas / límite) tandas; con elegidas en modo pruebas, A (origen,
    pruebas, horas, `synckey`), B (partes, validación) y C (líneas), una
    tanda cada una."""
    tandas = contar_tandas(monkeypatch)
    _precargado(ClienteQueAnota(), _peticiones([linea(**ELEGIDA)],
                                               codigo=True), limite=4)
    assert tandas == [(4, 1), (2, 1), (1, 1)]


def contar_tandas(monkeypatch) -> list[tuple[int, int]]:
    """Parchea `LecturasDelLote._ronda` y apunta (tareas, tandas) de cada
    ronda no vacía."""
    import math
    tandas: list[tuple[int, int]] = []
    original = LecturasDelLote._ronda

    def ronda(self, tareas):
        if tareas:
            tandas.append((len(tareas), math.ceil(len(tareas)
                                                  / self._limite)))
        return original(self, tareas)

    monkeypatch.setattr(LecturasDelLote, "_ronda", ronda)
    return tandas


def test_f055_r20_pendientes_historial_y_presupuesto_una_vez():
    cli = ClienteQueAnota(historial=[_h()])
    m = _precargado(cli, _peticiones(
        [linea(registro_id=1), linea(registro_id=2, recurso_ide=400,
                                     propuesta_paride=80002)]))
    assert ("historial_partidas", [200, 400], 202407, 202607) \
        in cli.llamadas
    assert ("capitulos_de_obra", 555001) in cli.llamadas
    cli.llamadas.clear()
    assert m.historial_partidas([200], 202407, 202607) == [_h()]
    assert m.capitulos_de_obra(555001) == cli.partidas_origen
    assert cli.llamadas == [] and m.fallos_de_memoria == {}


def test_f055_r20_sin_pendientes_ni_historial_ni_presupuesto():
    cli = ClienteQueAnota()
    _precargado(cli, _peticiones([linea(**ELEGIDA),
                                  linea(registro_id=2,
                                        propuesta_paride=80001)]))
    assert "historial_partidas" not in cli.nombres()
    assert "capitulos_de_obra" not in cli.nombres()


def test_f055_r20_postventa_y_real_destinos_y_presupuesto():
    cli = ClienteQueAnota()
    _precargado(cli, _peticiones([linea(), linea(registro_id=2,
                                                 es_postventa=True)]),
                obra_pruebas_forzar=False)
    assert ("obra_por_codigo", OBRA_POSTVENTA, 1) in cli.llamadas
    assert ("obra_por_codigo", OBRA_PRUEBAS, 1) not in cli.llamadas
    assert ("capitulos_de_obra", cli.obra_pv.ide) in cli.llamadas
    [partes] = [c for c in cli.llamadas if c[0] == "partes_de_periodos"]
    assert partes[1] == sorted([555001, cli.obra_pv.ide])


def test_f055_r20_obra_por_codigo_sin_ide():
    cli = ClienteQueAnota()
    m = _precargado(cli, _peticiones([linea(**ELEGIDA)], codigo=True))
    assert ("obra_por_codigo", OBRA_ORIGEN, 1) in cli.llamadas
    assert "obras_por_ide" not in cli.nombres()
    cli.llamadas.clear()
    assert m.obra_por_codigo(OBRA_ORIGEN, 1) is cli.obra_origen
    assert cli.llamadas == []


def test_f055_r20_partidas_de_lineas_solo_si_falta_subcuenta():
    cli = ClienteQueAnota()
    _precargado(cli, _peticiones([linea(**ELEGIDA)]))
    assert "partidas_de_lineas" not in cli.nombres()
    cli = ClienteQueAnota()
    for h in cli.horas[200]:
        h.caa_cod = None
    m = _precargado(cli, _peticiones([linea(**ELEGIDA)]))
    assert ("partidas_de_lineas", [80002]) in cli.llamadas
    cli.llamadas.clear()
    assert m.partidas_de_lineas([80002]) == {}
    assert cli.llamadas == []


# ===================== R22 · solo si está dentro ========================= #
@pytest.mark.parametrize("metodo, dentro, fuera", [
    ("horas_de_recursos", ([200],), ([200, 300],)),
    ("validar_partidas", ([80002],), ([80001],)),
    ("lineas_por_synckey", ([synckey_de(1)],), ([synckey_de(9)],)),
    ("partes_del_periodo", (828942, 2026, 7), (828942, 2026, 6)),
    ("lineas_del_parte", (777, [200]), (777, [300])),
    ("obra_por_ide", (555001,), (555002,)),
    ("historial_partidas", ([200], 202407, 202607), ([200], 202406, 202606)),
])
def test_f055_r22_responde_si_esta_dentro_y_si_no_lee(metodo, dentro,
                                                       fuera):
    cli = ClienteQueAnota(historial=[_h()])
    cli.lineas_parte = [linea_previa()]
    m = _precargado(cli, _peticiones([linea(registro_id=1, **ELEGIDA),
                                      linea(registro_id=2)]))
    cli.llamadas.clear()
    suelto = ClienteQueAnota(historial=[_h()])
    suelto.lineas_parte = [linea_previa()]
    assert getattr(m, metodo)(*dentro) == getattr(suelto, metodo)(*dentro)
    assert cli.llamadas == [] and m.fallos_de_memoria == {}
    assert getattr(m, metodo)(*fuera) == getattr(suelto, metodo)(*fuera)
    assert cli.llamadas == [(metodo,) + fuera]
    assert m.fallos_de_memoria == {metodo: 1}


def test_f055_r22_lo_servido_es_lo_mismo_que_lee_el_cliente():
    cli = ClienteQueAnota(historial=[_h(), _h(recurso=400)])
    cli.lineas_parte = [linea_previa(), linea_previa(ide=5002, reside=400)]
    cli.synckeys = {synckey_de(1): linea_previa(ide=9)}
    m = _precargado(cli, _peticiones([linea(registro_id=1, **ELEGIDA),
                                      linea(registro_id=2, recurso_ide=400)]))
    suelto = ClienteFalso()
    assert m.horas_de_recursos([400]) == suelto.horas_de_recursos([400])
    assert m.lineas_del_parte(777, [400]) == [cli.lineas_parte[1]]
    assert m.lineas_por_synckey([synckey_de(1), synckey_de(2)]) == {
        synckey_de(1): cli.synckeys[synckey_de(1)]}
    assert m.historial_partidas([400], 202407, 202607) == [_h(recurso=400)]
    assert m.validar_partidas([80002]) == suelto.validar_partidas([80002])
    assert m.partes_del_periodo(828942, 2026, 7) == \
        suelto.partes_del_periodo(828942, 2026, 7)


def test_f055_r22_sin_precarga_todo_va_al_cliente():
    cli = ClienteQueAnota()
    m = LecturasDelLote(cli, 4)
    assert m.horas_de_recursos([200]) == cli.horas_de_recursos([200])
    m.validar_partidas([80002])
    m.partidas_de_lineas([80002])
    m.lineas_por_synckey(["x"])
    m.historial_partidas([200], 1, 2)
    m.partes_del_periodo(1, 2026, 7)
    m.lineas_del_parte(777, [200])
    m.obra_por_ide(555001)
    assert sum(m.fallos_de_memoria.values()) == 8


def test_f055_r22_fallo_de_memoria_deja_log(caplog):
    import logging
    caplog.set_level(logging.INFO)
    LecturasDelLote(ClienteQueAnota(), 1).horas_de_recursos([200])
    assert "[lote] fallo de memoria horas_de_recursos: se lee de Sigrid" in [
        r.getMessage() for r in caplog.records]


# ====================== un solo vuelo y escribir ========================= #
def test_f055_r20_un_solo_vuelo_dos_hilos_una_lectura():
    cli = ClienteQueAnota(espera=0.05)
    m = LecturasDelLote(cli, 4)
    res = []
    hilos = [threading.Thread(target=lambda: res.append(
        m.obra_por_codigo(OBRA_PRUEBAS, 1))) for _ in range(2)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    assert res == [cli.obra, cli.obra]
    assert cli.nombres() == ["obra_por_codigo"]


def test_f055_r20_un_solo_vuelo_la_misma_excepcion():
    cli = ClienteQueAnota()
    llamadas = []

    def falla(*a):
        llamadas.append(a)
        raise RuntimeError("sigrid-api caída")

    cli.cuentas_de_centro = falla
    m = LecturasDelLote(cli, 4)
    for _ in range(2):
        with pytest.raises(RuntimeError, match="caída"):
            m.cuentas_de_centro(1, 1, ["B", "A", None])
    assert llamadas == [(1, 1, ("A", "B"))]


@pytest.mark.parametrize("metodo, args", [
    ("capitulos_de_obra", (555001,)),
    ("siguiente_cod_pt", (2026, 1)),
    ("cuentas_de_centro", (5, 1, ["X"])),
])
def test_f055_r20_compartidas_una_vez_por_lote(metodo, args):
    cli = ClienteQueAnota()
    m = LecturasDelLote(cli, 4)
    assert getattr(m, metodo)(*args) == getattr(m, metodo)(*args)
    assert cli.nombres() == [metodo]


def test_f055_r22_escribir_esta_prohibido():
    with pytest.raises(RuntimeError, match="no escriben"):
        LecturasDelLote(ClienteQueAnota(), 1).escribir([{"sql": "x"}])


# =============== R23 · paralelo, límite y contexto =================== #
def _diez(cli):
    return _peticiones(*[[linea(registro_id=i, recurso_ide=200 + i,
                                propuesta_paride=80002)]
                         for i in range(10)])


def test_f055_r23_limite_1_en_serie():
    cli = ClienteQueAnota(espera=0.02)
    _precargado(cli, _diez(cli), limite=1)
    assert cli.max_a_la_vez == 1


def test_f055_r23_limite_4_en_paralelo():
    cli = ClienteQueAnota(espera=0.3)
    _precargado(cli, _diez(cli), limite=4)
    assert 1 < cli.max_a_la_vez <= 4


def test_f055_r1_la_medicion_sigue_a_los_hilos():
    cli = ClienteQueAnota()
    with medir_lecturas() as m:
        _precargado(cli, _peticiones([linea(**ELEGIDA)]))
    assert sorted(l.nombre for l in m.lecturas) == sorted(cli.nombres())
    assert m.n >= 5


@pytest.mark.parametrize("valor, vale", [
    ("1", True), ("4", True), ("8", True), ("0", False), ("9", False)])
def test_f055_r23_ajuste_de_lecturas_paralelas(monkeypatch, valor, vale):
    from config.settings import Settings
    from pydantic import ValidationError
    monkeypatch.setenv("SIGRID_API_BASE_URL", "http://sigrid.invalid")
    monkeypatch.setenv("SIGRID_API_FUNCTION_KEY", "sin-clave")
    monkeypatch.delenv("SIGRID_LECTURAS_PARALELAS", raising=False)
    assert Settings(_env_file=None).sigrid_lecturas_paralelas == 4
    monkeypatch.setenv("SIGRID_LECTURAS_PARALELAS", valor)
    if vale:
        assert Settings(_env_file=None).sigrid_lecturas_paralelas == \
            int(valor)
    else:
        with pytest.raises(ValidationError):
            Settings(_env_file=None)


# ========================= R24 · fallos ================================== #
def test_f055_r24_una_agrupada_que_falla_para_la_precarga():
    cli = ClienteQueAnota()

    def falla(*a):
        raise RuntimeError("sigrid-api devolvio una respuesta truncada")

    cli.horas_de_recursos = falla
    with pytest.raises(RuntimeError, match="truncada"):
        _precargado(cli, _peticiones([linea(**ELEGIDA)]))


def test_f055_r24_una_compartida_que_falla_no_para_y_vuelve_a_quien_la_pide():
    cli = ClienteQueAnota()
    original = cli.obra_por_codigo

    def ambigua(cod, emp):
        if cod == OBRA_PRUEBAS:
            raise RuntimeError("obra de pruebas ambigua")
        return original(cod, emp)

    cli.obra_por_codigo = ambigua
    m = _precargado(cli, _peticiones([linea(**ELEGIDA)]))
    with pytest.raises(RuntimeError, match="ambigua"):
        m.obra_por_codigo(OBRA_PRUEBAS, 1)
    assert "partes_de_periodos" not in [c[0] for c in cli.llamadas]


def test_f055_r24_peticion_con_empresas_mezcladas_no_rompe_la_precarga():
    cli = ClienteQueAnota()
    _precargado(cli, _peticiones([linea(registro_id=1, empresa=1),
                                  linea(registro_id=2, empresa=2)],
                                 [linea(registro_id=3, **ELEGIDA)]))
    assert "horas_de_recursos" in cli.nombres()


# ========== T16 · huecos que dejó la campaña de mutación (transfer) ======= #
def test_f055_r20_real_sin_obra_de_postventa_la_precarga_sigue():
    """Superviviente `pv is not None or …`: en real, con líneas de
    postventa y sin obra de postventa en la empresa, la precarga no la usa
    como destino (y no revienta); su línea se omite como en suelto."""
    cli = ClienteQueAnota(obra_postventa_existe=False)
    m = _precargado(cli, _peticiones([linea(), linea(registro_id=2,
                                                     es_postventa=True)]),
                    obra_pruebas_forzar=False)
    [partes] = [c for c in cli.llamadas if c[0] == "partes_de_periodos"]
    assert partes[1] == [555001]
    assert m.obra_por_codigo(OBRA_POSTVENTA, 1) is None


def test_f055_r20_validacion_solo_de_obra_normal_sin_var():
    """Superviviente `not es_postventa or var is None`: la elegida de una
    línea de postventa no se valida por `ide` (va contra su catálogo)."""
    cli = ClienteQueAnota()
    _precargado(cli, _peticiones([
        linea(**ELEGIDA),
        linea(registro_id=2, es_postventa=True, paride=70002)]))
    assert ("validar_partidas", [80002]) in cli.llamadas


def test_f055_r20_la_obra_var_se_busca_en_la_precarga():
    """Supervivientes `var_obra_cod and ""` y `empresas[i] != emp`: con
    líneas VAR de la empresa, la obra VAR se busca en la ronda A."""
    from tests.test_f039_universo_var import ajustes_var
    cli = ClienteQueAnota()
    m = LecturasDelLote(cli, 4)
    m.precargar(_peticiones([linea(var_paride=417055)]), ajustes_var())
    assert ("obra_por_codigo", "VAR", 1) in cli.llamadas


def test_f055_r20_cuentas_de_partida_de_guardadas_y_var():
    """Superviviente `propuesta_paride and var_paride`: sin subcuenta se
    precargan las cuentas de la propuesta guardada y de la VAR."""
    from tests.test_f039_universo_var import ajustes_var
    cli = ClienteQueAnota()
    for h in cli.horas[200]:
        h.caa_cod = None
    m = LecturasDelLote(cli, 4)
    m.precargar(_peticiones([linea(propuesta_paride=80001),
                             linea(registro_id=2, var_paride=417055)]),
                ajustes_var())
    assert ("partidas_de_lineas", [80001, 417055]) in cli.llamadas


def test_f055_r20_sin_partes_no_se_leen_lineas():
    """Superviviente `hmoides or resides`: sin partes del periodo no hay
    líneas que leer."""
    cli = ClienteQueAnota(parte_existe=False)
    _precargado(cli, _peticiones([linea(**ELEGIDA)]))
    assert "lineas_de_partes" not in cli.nombres()


def test_f055_r20_linea_sin_recurso_no_rompe_ni_pide_cuentas():
    """Supervivientes de `_sin_subcuenta` (`and` y `return True`): una línea
    sin recurso (se omitirá) no hace leer cuentas de partida ni revienta."""
    cli = ClienteQueAnota()
    _precargado(cli, _peticiones([linea(**ELEGIDA),
                                  linea(registro_id=2, recurso_ide=None,
                                        paride=80001)]))
    assert "partidas_de_lineas" not in cli.nombres()


def test_f055_r34_propuestas_obra_por_codigo_solo_si_no_hay_ide():
    """Supervivientes `not o.ide or o.codigo` y `o.ide and o.codigo`: sin
    `ide`, la obra se busca por código en la ronda A (y su presupuesto va en
    B); con `ide`, no se busca por código."""
    cli = ClienteQueAnota()
    m = LecturasDelLote(cli, 4)
    lineas = [{"clave": "a", "recurso_ide": 200, "nombre": "X",
               "categoria": "Encargado", "es_postventa": False}]
    m.precargar_propuestas([
        {"empresa": 1, "obra": ObraEntrada(codigo=OBRA_ORIGEN), "ano": 2026,
         "mes": 7, "lineas": lineas},
        {"empresa": 1, "obra": ObraEntrada(ide=555001, codigo="NO-BUSCAR"),
         "ano": 2026, "mes": 7, "lineas": lineas}], SettingsFalso())
    assert ("obra_por_codigo", OBRA_ORIGEN, 1) in cli.llamadas
    assert ("obra_por_codigo", "NO-BUSCAR", 1) not in cli.llamadas
    assert ("capitulos_de_obra", 555001) in cli.llamadas
