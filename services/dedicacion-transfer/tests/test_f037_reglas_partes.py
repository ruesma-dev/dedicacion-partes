# tests/test_f037_reglas_partes.py
"""F-037 · Modelos y reglas puras copiadas de la F-031 de `partes`.

Trazabilidad con `specs/F-037-asiento-analitico-obra/requirements.md`:
R2-R5 (cuenta analítica: `cuenta_analitica.py`), R10, R13 y R15 (parte del
periodo: `estado_parte.py`) y el contrato de los modelos (R6, R15). Los
casos son los de `test_f031_estado_parte.py`, `test_f031_cuenta_partida.py`
y `test_f021_cuenta_analitica.py` de `partes`, renombrados: las dos reglas
son COPIA LITERAL (design §12), así que se prueban igual que allí.

Datos SINTÉTICOS: códigos de centro y subcuentas inventados.
"""
from __future__ import annotations

import dataclasses

import pytest
from domain.models.registro_models import (
    AccionLinea, HoraRecurso, ParteDestino, ParteSigrid, PartidaCuenta,
)

REG, CER, IMP = 1, 3, 10


# ============================ modelos (T1) ============================ #

def test_f037_r15_parte_sigrid_y_partida_cuenta_inmutables():
    p = ParteSigrid(ide=7, cod="PT26/00007", est=REG)
    assert (p.ide, p.cod, p.est) == (7, "PT26/00007", REG)
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.est = CER  # type: ignore[misc]
    q = PartidaCuenta(ide=80001, cod="CI.1.10", caa_cod="0678.CIMO03")
    assert (q.ide, q.cod, q.caa_cod) == (80001, "CI.1.10", "0678.CIMO03")
    with pytest.raises(dataclasses.FrozenInstanceError):
        q.caa_cod = None  # type: ignore[misc]


def test_f037_r2_hora_recurso_posicional_sigue_valiendo():
    """Los `HoraRecurso(...)` posicionales de antes de F-037 no cambian:
    sin cuenta y sin ser el tipo por defecto."""
    h = HoraRecurso(5, "MENC", None, 9000.0)
    assert (h.caa_cod, h.defecto) == (None, False)
    h2 = HoraRecurso(5, "MENC", None, 9000.0, caa_cod="00000.CIMO03",
                     defecto=True)
    assert (h2.caa_cod, h2.defecto) == ("00000.CIMO03", True)


def test_f037_r6_accion_lleva_el_contrato_caa_de_partes():
    a = AccionLinea(registro_id=1, accion="escribir", ano=2026, mes=7,
                    fecha_int=20260731)
    assert (a.caa_ide, a.caa_cod, a.caa_motivo, a.caa_aviso, a.caa_origen,
            a.caa_nota) == (0, None, None, None, None, None)


def test_f037_r15_parte_destino_lleva_estado_y_complementario():
    p = ParteDestino(ano=2026, mes=7)
    assert (p.obra_cod, p.estado, p.complementario, p.cerrados,
            p.del_periodo, p.aviso) == (None, None, False, [], [], None)
    # Las listas no se comparten entre instancias.
    p.cerrados.append("PT26/00004")
    assert ParteDestino(ano=2026, mes=7).cerrados == []


def test_f037_r15_ajustes_de_estado_solo_para_textos():
    from config.settings import Settings

    campos = Settings.model_fields
    assert campos["est_parte_cerrado"].default == CER
    assert campos["est_parte_cerrado"].alias == "EST_PARTE_CERRADO"
    assert campos["est_parte_imputado"].default == IMP
    assert campos["est_parte_imputado"].alias == "EST_PARTE_IMPUTADO"
    assert campos["est_parte_activo"].default == REG
    from pathlib import Path

    ejemplo = (Path(__file__).resolve().parents[1] / ".env.example"
               ).read_text(encoding="utf-8")
    assert "EST_PARTE_CERRADO=3" in ejemplo
    assert "EST_PARTE_IMPUTADO=10" in ejemplo


# ================= estado_parte.py (copia de `partes`, T2) ================= #

from application.services.estado_parte import (  # noqa: E402
    MOTIVO_PARTE_CERRADO, aviso_de_parte, elegir_parte, motivo_choque,
    nombre_estado,
)


def _elegir(partes):
    return elegir_parte(2026, 1, partes, est_registro=REG)


def test_f037_r10_mayor_ide_en_registro_aunque_haya_cerrados_mayores():
    partes = [ParteSigrid(5, "PT26/00005", REG),
              ParteSigrid(9, "PT26/00009", CER),
              ParteSigrid(7, "PT26/00007", REG),
              ParteSigrid(12, "PT26/00012", IMP)]
    p = _elegir(partes)
    assert (p.ano, p.mes, p.existe, p.ide, p.cod, p.estado) == \
        (2026, 1, True, 7, "PT26/00007", REG)
    assert p.complementario is True
    # Por `ide` descendente, sea cual sea el orden de llegada.
    assert [x.ide for x in p.del_periodo] == [12, 9, 7, 5]
    assert p.cerrados == ["PT26/00012", "PT26/00009"]
    assert p.creado is False and p.aviso is None


@pytest.mark.parametrize("orden", [[0, 1], [1, 0]], ids=["asc", "desc"])
def test_f037_r10_el_orden_de_llegada_no_decide(orden):
    dos = [ParteSigrid(5, "PT26/00005", REG),
           ParteSigrid(8, "PT26/00008", REG)]
    p = _elegir([dos[i] for i in orden])
    assert (p.ide, p.cod, p.complementario) == (8, "PT26/00008", False)


def test_f037_r10_un_solo_parte_en_registro_no_es_complementario():
    p = _elegir([ParteSigrid(5, "PT26/00005", REG)])
    assert (p.existe, p.ide, p.cod, p.estado, p.complementario,
            p.cerrados) == (True, 5, "PT26/00005", REG, False, [])


def test_f037_r10_el_predicado_es_el_estado_de_registro_que_se_pasa():
    p = elegir_parte(2026, 1, [ParteSigrid(5, "PT26/00005", 7)],
                     est_registro=7)
    assert (p.existe, p.complementario) == (True, False)


@pytest.mark.parametrize("est", [CER, IMP, 4, None])
def test_f037_r10_todos_cerrados_propone_complementario_nuevo(est):
    p = _elegir([ParteSigrid(4, "PT26/00004", est)])
    assert (p.existe, p.ide, p.cod, p.estado) == (False, None, None, None)
    assert (p.complementario, p.cerrados) == (True, ["PT26/00004"])
    assert p.del_periodo == [ParteSigrid(4, "PT26/00004", est)]


def test_f037_r10_sin_partes_parte_nuevo_sin_complementario():
    p = _elegir([])
    assert p == ParteDestino(ano=2026, mes=1)
    assert (p.existe, p.estado, p.complementario, p.cerrados,
            p.del_periodo, p.aviso) == (False, None, False, [], [], None)


def test_f037_r15_nombres_de_estado():
    kw = dict(est_cerrado=CER, est_imputado=IMP)
    assert nombre_estado(CER, **kw) == "Cerrado"
    assert nombre_estado(IMP, **kw) == "Imputado"
    assert nombre_estado(4, **kw) == "estado 4"
    assert nombre_estado(None, **kw) == "estado None"
    assert nombre_estado(8, est_cerrado=8, est_imputado=9) == "Cerrado"
    assert nombre_estado(9, est_cerrado=8, est_imputado=9) == "Imputado"


def test_f037_r15_aviso_complementario_nuevo():
    p = _elegir([ParteSigrid(4, "PT26/00004", IMP)])
    p.cod = "PT26/00350"
    assert aviso_de_parte(p, {"PT26/00004": "Imputado"}) == (
        "el parte PT26/00004 (Imputado) de 01/2026 esta cerrado: las "
        "lineas van al parte complementario PT26/00350 (se creara)")


def test_f037_r15_aviso_complementario_existente_y_varios_cerrados():
    p = _elegir([ParteSigrid(4, "PT26/00004", IMP),
                 ParteSigrid(9, "PT26/00009", CER),
                 ParteSigrid(11, "PT26/00350", REG)])
    assert aviso_de_parte(p, {"PT26/00004": "Imputado",
                              "PT26/00009": "Cerrado"}) == (
        "los partes PT26/00009 (Cerrado), PT26/00004 (Imputado) de 01/2026 "
        "estan cerrados: las lineas van al parte complementario PT26/00350 "
        "(ya existe, en registro)")


def test_f037_r15_aviso_con_estado_sin_nombre():
    p = _elegir([ParteSigrid(4, "PT26/00004", 4)])
    p.cod = "PT26/00350"
    assert "PT26/00004 (estado ?)" in aviso_de_parte(p, {})


@pytest.mark.parametrize("partes", [
    [], [ParteSigrid(5, "PT26/00005", REG)],
    [ParteSigrid(5, "PT26/00005", REG), ParteSigrid(6, "PT26/00006", REG)],
])
def test_f037_r15_sin_cerrados_no_hay_aviso(partes):
    assert aviso_de_parte(_elegir(partes), {}) is None


def test_f037_r13_motivo_choque_con_prefijo_y_sin_nombres():
    assert MOTIVO_PARTE_CERRADO == "parte_cerrado"
    texto = motivo_choque("PT26/00004", "Cerrado")
    assert texto == (
        "parte_cerrado: ya hay horas de ese recurso, dia y tipo en el parte "
        "PT26/00004 (Cerrado); no se registran")
    assert texto.startswith(MOTIVO_PARTE_CERRADO + ": ")


# =============== cuenta_analitica.py (copia de `partes`, T2) =============== #

from application.services.cuenta_analitica import (  # noqa: E402
    MOTIVO_CUENTA_AMBIGUA, MOTIVO_OBRA_SIN_CUENTA, MOTIVO_RECURSO_SIN_CUENTA,
    SUBCUENTAS_COSTE_PARTIDA, CuentaLinea, OrigenSubcuenta, indexar_cuentas,
    origen_subcuenta, resolver_cuenta, subcuenta, subcuenta_de_linea,
    subcuenta_de_partida,
)

HL, HE, CI, OTRA = 11, 12, 13, 14


def _h(horide, caa_cod=None, *, defecto=False, cod="HL01") -> HoraRecurso:
    return HoraRecurso(horide=horide, cod=cod, res=None, pre=10.0,
                       caa_cod=caa_cod, defecto=defecto)


@pytest.mark.parametrize("cod, esperado", [
    ("00000.CIMO09", "CIMO09"),          # forma normal <centro>.<subcuenta>
    ("0404.CIMO09", "CIMO09"),
    ("  00000 .  CIMO09  ", "CIMO09"),   # espacios a los lados: fuera
    ("00000.A.B", "A.B"),                # varios puntos: tras el PRIMERO
    ("00000..B", ".B"),
    (".X", "X"),                         # centro vacío: la subcuenta vale
    ("SINPUNTO", None),                  # sin punto: no tiene
    ("00000.", None),                    # vacía tras el punto
    ("00000.   ", None),
    ("", None),
    ("   ", None),
    (None, None),
])
def test_f037_r2_subcuenta_del_codigo(cod, esperado):
    assert subcuenta(cod) == esperado


def test_f037_r2_la_del_tipo_de_hora_que_se_escribe():
    horas = [_h(HL, "00000.LAB", defecto=True), _h(HE, "00000.EXT")]
    assert subcuenta_de_linea(horas, HE) == "EXT"
    assert subcuenta_de_linea(horas, HL) == "LAB"


def test_f037_r2_manda_el_tipo_escrito_aunque_el_defecto_tenga_otra():
    horas = [_h(HE, "00000.EXT"), _h(HL, "00000.LAB", defecto=True)]
    assert subcuenta_de_linea(horas, HE) == "EXT"


def test_f037_r2_sin_plantilla_del_tipo_va_la_del_tipo_por_defecto():
    horas = [_h(HL, "00000.LAB", defecto=True), _h(CI, None, cod="CIV")]
    assert subcuenta_de_linea(horas, CI) == "LAB"


@pytest.mark.parametrize("cod_tipo", ["SINPUNTO", "00000.", "", "  "])
def test_f037_r2_plantilla_sin_subcuenta_tambien_cae_al_defecto(cod_tipo):
    horas = [_h(CI, cod_tipo, cod="CIV"), _h(HL, "00000.LAB", defecto=True)]
    assert subcuenta_de_linea(horas, CI) == "LAB"


def test_f037_r2_tipo_que_no_esta_en_la_ficha_cae_al_defecto():
    horas = [_h(HL, "00000.LAB", defecto=True)]
    assert subcuenta_de_linea(horas, 999) == "LAB"
    assert subcuenta_de_linea(horas, None) == "LAB"


def test_f037_r2_defecto_sin_subcuenta_salta_al_siguiente_defecto():
    horas = [_h(HL, None, defecto=True), _h(HE, "00000.EXT", defecto=True)]
    assert subcuenta_de_linea(horas, CI) == "EXT"


def test_f037_r2_ni_tipo_ni_defecto_dan_subcuenta():
    horas = [_h(HL, None, defecto=True), _h(CI, None, cod="CIV")]
    assert subcuenta_de_linea(horas, CI) is None
    assert subcuenta_de_linea([], CI) is None


def test_f037_r2_otra_fila_con_cuenta_no_interviene():
    """Una fila de OTRO tipo que no es el defecto no aporta nada."""
    horas = [_h(OTRA, "00000.OTRA"), _h(HL, None, defecto=True),
             _h(CI, None, cod="CIV")]
    assert subcuenta_de_linea(horas, CI) is None
    assert subcuenta_de_linea(horas, HL) is None


def test_f037_r2_una_fila_sin_marcar_no_es_el_tipo_por_defecto():
    otra = HoraRecurso(horide=OTRA, cod="HL09", res=None, pre=1.0,
                       caa_cod="00000.OTRA")
    assert subcuenta_de_linea([otra], CI) is None


def test_f037_r3_subcuentas_de_coste_son_ci_y_cd():
    assert SUBCUENTAS_COSTE_PARTIDA == ("CI", "CD")


@pytest.mark.parametrize("caa_cod, esperado", [
    ("0100.CIMO12", "CIMO12"),
    ("0100.CDQA01", "CDQA01"),
    ("0100. CICO01 ", "CICO01"),
    ("0100.cimo12", "cimo12"),         # el prefijo se mira en mayúsculas
    ("0100.cd01", "cd01"),
    ("0100.CI", "CI"),
])
def test_f037_r3_subcuenta_de_partida_de_coste(caa_cod, esperado):
    assert subcuenta_de_partida(caa_cod) == esperado


@pytest.mark.parametrize("caa_cod", [
    "0100.CP00", "0100.INGR", "0100.C", "0100.CX01", "0100.ICIMO",
    "CIMO12", "0100.", "", None,
])
def test_f037_r3_subcuenta_de_partida_que_no_vale(caa_cod):
    assert subcuenta_de_partida(caa_cod) is None


CON_CUENTA = [_h(HL, "00000.CIMO09", defecto=True), _h(HE)]
SIN_CUENTA = [_h(HL, None, defecto=True), _h(HE)]
MAQUINISTA = PartidaCuenta(300, "01.02", "0100.CIMO12")


def test_f037_r3_el_recurso_manda_aunque_la_partida_tenga_otra():
    assert origen_subcuenta(CON_CUENTA, HL, MAQUINISTA) == \
        OrigenSubcuenta("CIMO09", "recurso", None)
    assert origen_subcuenta(CON_CUENTA, HE, MAQUINISTA) == \
        OrigenSubcuenta("CIMO09", "recurso", None)
    assert origen_subcuenta(CON_CUENTA, HL, None) == \
        OrigenSubcuenta("CIMO09", "recurso", None)


def test_f037_r3_recurso_sin_cuenta_usa_la_partida_de_coste():
    assert origen_subcuenta(SIN_CUENTA, HL, MAQUINISTA) == OrigenSubcuenta(
        "CIMO12", "partida",
        "el recurso no tiene cuenta para esa hora: se usa la de la partida "
        "01.02 (.CIMO12)")
    o = origen_subcuenta([], HL, PartidaCuenta(301, "02.01", "0100.CDQA01"))
    assert (o.sub, o.origen) == ("CDQA01", "partida")


@pytest.mark.parametrize("partida", [
    None,
    PartidaCuenta(302, "09.01", "0100.CP00"),
    PartidaCuenta(303, "10.01", "0100.INGR"),
    PartidaCuenta(304, "11.01", None),
])
def test_f037_r3_sin_cuenta_de_recurso_ni_de_partida(partida):
    assert origen_subcuenta(SIN_CUENTA, HL, partida) == \
        OrigenSubcuenta(None, None, None)


def test_f037_r4_indexar_agrupa_por_subcuenta():
    filas = [(701, "0404.LAB"), (702, "0404.EXT"), (703, " 0404 .LAB "),
             (704, "SINPUNTO"), (705, "0404."), (706, None)]
    assert indexar_cuentas(filas) == {
        "LAB": [(701, "0404.LAB"), (703, "0404 .LAB")],
        "EXT": [(702, "0404.EXT")],
    }
    (cuenta,) = indexar_cuentas([("701", "0404.LAB")])["LAB"]
    assert cuenta == (701, "0404.LAB") and isinstance(cuenta[0], int)
    assert indexar_cuentas([]) == {}


CUENTAS = {"LAB": [(701, "0404.LAB")], "EXT": [(702, "0404.EXT")],
           "DOS": [(703, "0404.DOS"), (704, "0404. DOS")]}


def test_f037_r4_la_cuenta_del_centro_con_esa_subcuenta():
    assert resolver_cuenta("LAB", CUENTAS, "0404") == \
        CuentaLinea(caa_ide=701, caa_cod="0404.LAB", motivo=None, aviso=None)
    assert resolver_cuenta("EXT", CUENTAS, "0404").caa_ide == 702


def test_f037_r5_sin_subcuenta_va_sin_cuenta_y_sin_aviso():
    assert resolver_cuenta(None, CUENTAS, "0404") == CuentaLinea(
        caa_ide=0, caa_cod=None, motivo=MOTIVO_RECURSO_SIN_CUENTA,
        aviso=None)


def test_f037_r5_la_obra_no_tiene_esa_subcuenta():
    c = resolver_cuenta("NOHAY", CUENTAS, "0404")
    assert (c.caa_ide, c.caa_cod, c.motivo) == \
        (0, None, MOTIVO_OBRA_SIN_CUENTA)
    assert c.aviso == ("la obra 0404 no tiene la cuenta analitica .NOHAY: "
                       "la linea ira sin cuenta")


def test_f037_r5_varias_candidatas_no_se_elige_ninguna():
    c = resolver_cuenta("DOS", CUENTAS, "0404")
    assert (c.caa_ide, c.caa_cod, c.motivo) == \
        (0, None, MOTIVO_CUENTA_AMBIGUA)
    assert c.aviso == ("la obra 0404 tiene varias cuentas .DOS: la linea "
                       "ira sin cuenta")


def test_f037_r5_motivos_distintos_y_estables():
    assert (MOTIVO_RECURSO_SIN_CUENTA, MOTIVO_OBRA_SIN_CUENTA,
            MOTIVO_CUENTA_AMBIGUA) == (
        "recurso_sin_cuenta", "obra_sin_cuenta", "cuenta_ambigua")
    c = resolver_cuenta("LAB", CUENTAS, "0404")
    with pytest.raises(dataclasses.FrozenInstanceError):
        c.caa_ide = 1  # type: ignore[misc]


def test_f037_r3_el_origen_de_la_subcuenta_es_inmutable():
    """T10 (campaña sin el test de copias): `OrigenSubcuenta` es un valor."""
    o = origen_subcuenta(CON_CUENTA, HL, None)
    with pytest.raises(dataclasses.FrozenInstanceError):
        o.sub = "OTRA"  # type: ignore[misc]
