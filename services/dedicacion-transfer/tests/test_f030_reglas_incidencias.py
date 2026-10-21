# tests/test_f030_reglas_incidencias.py
"""F-030 · Reglas de las incidencias (ARCHITECTURE.md#regla-incidencia).

Funciones puras de `reglas_incidencias`, sin pipeline ni cliente:

- `decidir_incidencia` (R24, R26): cada incidencia son DOS líneas, el inicio
  con su `CI*` el día `desde` y el fin con `CIZ` el día `hasta`; si el
  recurso no tiene alguno de los dos códigos, se omiten las dos.
- `reconciliar` (R27; anexo R30 en `test_f030_r30_editar.py`): una línea
  que ya está en algún parte del mes (mismo recurso, código y `fec`) no se
  escribe: «ya registrada» si es nuestra; si no, omitida con el parte donde
  está. Hasta el anexo R30 era `deduplicar`.
- `synckey_incidencia`: `porcentajes:inc:{id}:ini|fin`.
"""
from __future__ import annotations

import pytest
from application.services.reglas_incidencias import (
    CODIGO_FIN,
    MOTIVO_INC_DIAS,
    MOTIVO_INC_SIN_CODIGO,
    MOTIVO_INC_SIN_RECURSO,
    decidir_incidencia,
    synckey_incidencia,
)
from application.services.reglas_porcentajes import MOTIVO_SIN_EMPRESA
from domain.models.registro_models import (
    AccionIncidencia,
    HoraRecurso,
    IncidenciaEntrada,
)

#: Recurso 200: mensual con las incidencias de Sigrid (CIV, CIE y el fin CIZ)
#: y su cuenta de plantilla. Recurso 300: tiene CIV pero no CIZ. Recurso 400:
#: tiene CIZ pero no CIE.
HORAS = {
    200: [HoraRecurso(5, "MENC", None, 9000.0),
          HoraRecurso(71, "CIV", "Vacaciones(V)", 12.5, caa_cod="64000"),
          HoraRecurso(72, "CIE", "Enfermedad(B)", 0.0),
          HoraRecurso(79, "CIZ", "Fin de Incidencia", 0.0)],
    300: [HoraRecurso(71, "CIV", None, 0.0)],
    400: [HoraRecurso(79, "CIZ", None, 3.0), HoraRecurso(71, "CIV", None, 0.0)],
}


def _inc(**kw) -> IncidenciaEntrada:
    base = {"id": 7, "recurso_ide": 200, "empresa": 1, "codigo": "CIV",
            "ano": 2026, "mes": 7, "desde": 5, "hasta": 9, "paride": 0}
    base.update(kw)
    return IncidenciaEntrada(**base)


# ============================== synckey ================================== #
def test_f030_r24_decidir_synckey_por_incidencia_y_rol():
    assert synckey_incidencia(7, "ini") == "porcentajes:inc:7:ini"
    assert synckey_incidencia("12", "fin") == "porcentajes:inc:12:fin"
    with pytest.raises(ValueError, match="rol"):
        synckey_incidencia(7, "medio")


def test_f030_r24_decidir_el_fin_es_ciz():
    assert CODIGO_FIN == "CIZ"


# ================================ R24 ==================================== #
def test_f030_r24_decidir_inicio_con_su_codigo_y_fin_con_ciz():
    ini, fin = decidir_incidencia(_inc(paride=80003), HORAS)
    assert ini == AccionIncidencia(
        id=7, rol="ini", accion="escribir", recurso_ide=200, ano=2026, mes=7,
        fecha_int=20260705, hora_ide=71, hora_codigo="CIV", pre=12.5,
        paride=80003)
    assert fin == AccionIncidencia(
        id=7, rol="fin", accion="escribir", recurso_ide=200, ano=2026, mes=7,
        fecha_int=20260709, hora_ide=79, hora_codigo="CIZ", pre=0.0,
        paride=80003)
    assert (ini.destino, ini.motivo, ini.parte_cod, ini.hmores_ide,
            ini.caa_ide) == ("obra", None, None, None, 0)


def test_f030_r24_decidir_un_dia_y_extremos_del_mes():
    ini, fin = decidir_incidencia(_inc(desde=31, hasta=31), HORAS)
    assert (ini.fecha_int, fin.fecha_int) == (20260731, 20260731)
    ini, fin = decidir_incidencia(_inc(desde=1, hasta=28, mes=2), HORAS)
    assert (ini.fecha_int, fin.fecha_int) == (20260201, 20260228)
    ini, fin = decidir_incidencia(_inc(codigo="CIE", paride=None), HORAS)
    assert (ini.hora_ide, ini.hora_codigo, ini.paride) == (72, "CIE", 0)
    ini, fin = decidir_incidencia(_inc(recurso_ide=400, codigo="CIV"), HORAS)
    assert (fin.hora_ide, fin.pre) == (79, 3.0)


# ================================ R26 ==================================== #
@pytest.mark.parametrize("recurso, codigo, falta", [
    (300, "CIV", "CIZ"),            # tiene el inicio, no el fin
    (400, "CIE", "CIE"),            # tiene el fin, no el inicio
    (999, "CIV", "CIV"),            # sin horas: el primero que falta
])
def test_f030_r26_decidir_sin_codigo_se_omiten_las_dos(recurso, codigo, falta):
    ini, fin = decidir_incidencia(_inc(recurso_ide=recurso, codigo=codigo), HORAS)
    motivo = MOTIVO_INC_SIN_CODIGO.format(cod=falta)
    assert (ini.accion, ini.motivo, fin.accion, fin.motivo) == (
        "omitir", motivo, "omitir", motivo)
    assert falta in motivo
    assert (ini.rol, fin.rol, ini.fecha_int, fin.fecha_int) == (
        "ini", "fin", 20260705, 20260709)
    assert (ini.hora_ide, fin.hora_ide) == (None, None)


@pytest.mark.parametrize("cambios, motivo", [
    ({"recurso_ide": None}, MOTIVO_INC_SIN_RECURSO),
    ({"recurso_ide": 0}, MOTIVO_INC_SIN_RECURSO),
    ({"empresa": None}, MOTIVO_SIN_EMPRESA),
    ({"empresa": 0}, MOTIVO_SIN_EMPRESA),
    ({"empresa": True}, MOTIVO_SIN_EMPRESA),
])
def test_f030_r23_decidir_sin_recurso_o_sin_empresa(cambios, motivo):
    ini, fin = decidir_incidencia(_inc(**cambios), HORAS)
    assert (ini.accion, ini.motivo, fin.accion, fin.motivo) == (
        "omitir", motivo, "omitir", motivo)


def test_f030_r23_decidir_obra_de_otra_empresa():
    ini, fin = decidir_incidencia(_inc(), HORAS, motivo_empresa="otra empresa")
    assert [(a.accion, a.motivo) for a in (ini, fin)] == [
        ("omitir", "otra empresa")] * 2
    # La empresa de la incidencia se mira antes.
    ini, _ = decidir_incidencia(_inc(empresa=None), HORAS,
                                motivo_empresa="otra empresa")
    assert ini.motivo == MOTIVO_SIN_EMPRESA


@pytest.mark.parametrize("desde, hasta, mes", [
    (0, 9, 7), (5, 32, 7), (9, 5, 7), (1, 29, 2), (None, 9, 7), (5, None, 7),
])
def test_f030_r24_decidir_dias_imposibles_no_se_escriben(desde, hasta, mes):
    ini, fin = decidir_incidencia(_inc(desde=desde, hasta=hasta, mes=mes), HORAS)
    motivo = MOTIVO_INC_DIAS.format(desde=desde, hasta=hasta, mes=mes, ano=2026)
    assert (ini.accion, ini.motivo, fin.accion, fin.motivo) == (
        "omitir", motivo, "omitir", motivo)
    assert (ini.fecha_int, fin.fecha_int) == (0, 0)


def test_f030_r24_decidir_dias_validos_en_los_bordes():
    for desde, hasta, mes in ((1, 1, 7), (31, 31, 7), (1, 31, 7), (28, 28, 2)):
        ini, fin = decidir_incidencia(_inc(desde=desde, hasta=hasta, mes=mes), HORAS)
        assert (ini.accion, fin.accion) == ("escribir", "escribir"), (desde, hasta, mes)


# ================================ R27 ==================================== #
def _existente(ide, reside, fec, cod, synckey=None, parte="PT26/00012",
               **kw):
    from domain.models.registro_models import LineaIncidenciaSigrid

    return LineaIncidenciaSigrid(ide=ide, reside=reside, fecha_int=fec,
                                 hora_codigo=cod, synckey=synckey,
                                 parte_cod=parte, **kw)


def deduplicar(acciones, existentes):
    """R27 con `reconciliar` sin traza de la api (anexo R30): lo mismo que
    hacía `deduplicar`, que desapareció con el anexo."""
    from application.services.reglas_incidencias import reconciliar

    reconciliar(acciones, [], existentes, est=1)


def _par(**kw):
    ini, fin = decidir_incidencia(_inc(**kw), HORAS)
    ini.parte_cod = fin.parte_cod = "PT26/00099"     # el elegido en el paso 5
    return ini, fin


def test_f030_r27_deduplicar_nada_igual_se_escribe():
    ini, fin = _par()
    deduplicar([ini, fin], [
        _existente(1, 200, 20260706, "CIV"),          # otro día
        _existente(2, 201, 20260705, "CIV"),          # otro recurso
        _existente(3, 200, 20260705, "CIE"),          # otro código
        _existente(4, 200, 20260708, "CIZ")])
    assert [(a.accion, a.parte_cod, a.motivo) for a in (ini, fin)] == [
        ("escribir", "PT26/00099", None)] * 2


def test_f030_r27_deduplicar_la_nuestra_es_ya_registrada():
    from application.services.reglas_incidencias import MOTIVO_INC_YA

    ini, fin = _par()
    deduplicar([ini, fin], [
        _existente(51, 200, 20260705, "CIV ", "porcentajes:inc:7:ini", "PT26/00031")])
    assert (ini.accion, ini.hmores_ide, ini.parte_cod, ini.motivo) == (
        "ya_registrado", 51, "PT26/00031", MOTIVO_INC_YA.format(ide=51))
    assert "51" in ini.motivo
    assert (fin.accion, fin.hmores_ide, fin.parte_cod) == ("escribir", None, "PT26/00099")


def test_f030_r27_deduplicar_la_de_otro_se_omite_con_su_parte():
    from application.services.reglas_incidencias import MOTIVO_INC_DUPLICADA

    ini, fin = _par()
    deduplicar([ini, fin], [
        _existente(60, 200, 20260709, "CIZ", None, "PT26/00040"),
        _existente(61, 200, 20260705, "CIV", "partes:9:1", "PT26/00041"),
        _existente(62, 200, 20260705, "CIV", "porcentajes:inc:8:ini", "PT26/00042")])
    assert (fin.accion, fin.parte_cod, fin.hmores_ide) == ("omitir", "PT26/00040", None)
    assert fin.motivo == MOTIVO_INC_DUPLICADA.format(cod="CIZ", dia=9, mes=7,
                                                     parte="PT26/00040")
    assert fin.motivo == ("ya hay una línea CIZ del recurso el 09/07 en el parte "
                          "PT26/00040: no se duplica")
    # La primera igual manda (la de `partes`), aunque luego haya otra.
    assert (ini.accion, ini.parte_cod) == ("omitir", "PT26/00041")


def test_f030_r27_deduplicar_solo_mira_las_que_se_escriben():
    ini, fin = decidir_incidencia(_inc(recurso_ide=300), HORAS)      # omitidas
    antes = (ini.motivo, fin.motivo)
    deduplicar([ini, fin], [_existente(1, 300, 20260705, "CIV",
                                       "porcentajes:inc:7:ini")])
    assert (ini.accion, fin.accion, (ini.motivo, fin.motivo)) == (
        "omitir", "omitir", antes)
    assert ini.hmores_ide is None and ini.parte_cod is None
    ya, _ = _par()
    ya.accion = "ya_registrado"
    deduplicar([ya], [_existente(2, 200, 20260705, "CIV")])
    assert (ya.accion, ya.parte_cod) == ("ya_registrado", "PT26/00099")


def test_f030_r27_deduplicar_codigo_nulo_en_sigrid_no_casa():
    ini, fin = _par()
    deduplicar([ini, fin], [_existente(1, 200, 20260705, None)])
    assert ini.accion == "escribir"


def test_f030_r30_deduplicar_la_nuestra_aunque_cambien_los_dias():
    """Anexo R30 (design §13.7): la nuestra con otros días ya no es «ya
    registrada» sino `editar` (R41); y solo es nuestra si es del recurso
    (R40): la 52, de otro, no cuenta y la 53 de otra incidencia ocupa."""
    from application.services.reglas_incidencias import MOTIVO_INC_DUPLICADA

    ini, fin = _par(desde=6, hasta=10)
    deduplicar([ini, fin], [
        _existente(51, 200, 20260705, "CIV", "porcentajes:inc:7:ini", "PT26/00031",
                   can=0.0, hmoide=31, parte_est=1),
        _existente(52, 999, 20260709, "CIZ", "porcentajes:inc:7:fin", "PT26/00032"),
        _existente(53, 200, 20260710, "CIZ", "porcentajes:inc:8:fin", "PT26/00033")])
    assert (ini.accion, ini.hmores_ide, ini.parte_cod, ini.fec_antes,
            ini.motivo) == ("editar", 51, "PT26/00031", 20260705, None)
    assert (fin.accion, fin.hmores_ide, fin.parte_cod, fin.motivo) == (
        "omitir", None, "PT26/00033", MOTIVO_INC_DUPLICADA.format(
            cod="CIZ", dia=10, mes=7, parte="PT26/00033"))
