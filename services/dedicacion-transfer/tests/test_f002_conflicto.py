# tests/test_f002_conflicto.py
"""F-002 · La clave del conflicto y el criterio de choque no pueden divergir.

R14. Las dos salen de la misma tupla (`CAMPOS_CLAVE`) y del mismo derivado
(`campos_identidad`). Lo que se vigila aquí no es un valor concreto: es que
tocar la tupla mueva **las dos cosas a la vez**. Divergieron una vez —la
clave incluía la partida y el filtro del pipeline no la comparaba— y estos
tests están para que no vuelva a pasar en silencio.

Los enunciados normativos viven en `docs/ARCHITECTURE.md`
(`#regla-conflicto`). Aquí solo se comprueba el mecanismo.

R18 y R19 (qué cuenta como conflicto en la obra normal) NO están aquí: son
la decisión D2, pendiente de Administración. Lo que estos tests fijan es la
conducta de HOY, para que el cambio de D2 se vea.
"""
from __future__ import annotations

import pytest

import application.services.reglas_porcentajes as rp
from application.services.reglas_porcentajes import (
    CAMPOS_CLAVE, IMPLICITOS_DEL_PARTE, campos_identidad, clave_conflicto,
    criterio_choque,
)
from domain.models.registro_models import AccionLinea

from tests.conftest import linea_previa


def accion(**kw) -> AccionLinea:
    """Acción de escritura del encargado (recurso 200, MENC) en julio."""
    datos = dict(registro_id=1, accion="escribir", ano=2026, mes=7,
                 fecha_int=20260731, recurso_ide=200, hora_ide=5,
                 hora_codigo="MENC", can=0.4, pre=9000.0, tot=3600.0,
                 destino="obra", paride=80001)
    datos.update(kw)
    return AccionLinea(**datos)


# --------------------- R14 · una sola fuente ---------------------- #

def test_f002_r14_la_identidad_es_subconjunto_de_la_clave():
    """R14 · Todo lo que se compara está en la clave. Si el criterio mirara
    un campo que la clave no lleva, dos líneas distintas compartirían clave
    y el humano confirmaría a ciegas."""
    for destino in ("obra", "postventa"):
        assert set(campos_identidad(destino)) <= set(CAMPOS_CLAVE), destino


def test_f002_r14_todo_campo_comparado_sabe_leerse_de_las_dos_partes():
    """R14 · Un campo de la identidad, o se sabe leer de la línea existente,
    o está declarado implícito del parte. No hay tercera opción silenciosa."""
    for destino in ("obra", "postventa"):
        for campo in campos_identidad(destino):
            assert campo in IMPLICITOS_DEL_PARTE or campo in rp._DE_LINEA, campo
            assert campo in rp._DE_ACCION, campo


def test_f002_r14_cambiar_la_tupla_cambia_la_clave_y_el_criterio(monkeypatch):
    """R14 · EL test de la feature: se quita `paride` de `CAMPOS_CLAVE` y
    cambian LAS DOS cosas — la clave deja de llevar la partida y la
    postventa deja de distinguir por partida."""
    a = accion(destino="postventa", paride=70001)
    previa = linea_previa(paride=99999)

    # Conducta de partida: la clave lleva la partida y el criterio la mira.
    assert clave_conflicto(a) == "200|202607|5|70001"
    assert criterio_choque(previa, a, mias=set()) is False

    monkeypatch.setattr(rp, "CAMPOS_CLAVE", ("recurso", "periodo", "hora"))

    assert campos_identidad("postventa") == ("recurso", "periodo", "hora")
    assert campos_identidad("obra") == ("recurso", "periodo", "hora")
    assert clave_conflicto(a) == "200|202607|5"
    assert criterio_choque(previa, a, mias=set()) is True


def test_f002_r14_un_campo_nuevo_sin_lector_falla_en_alto(monkeypatch):
    """R14 · Añadir un campo a la clave sin enseñar a leerlo de la línea de
    Sigrid revienta. Ignorarlo en silencio es la avería que trae la
    feature: el criterio se quedaría más flojo que la clave."""
    monkeypatch.setattr(rp, "CAMPOS_CLAVE", (*CAMPOS_CLAVE, "obra"))
    a = accion(destino="postventa")
    with pytest.raises(KeyError):
        criterio_choque(linea_previa(paride=a.paride), a, mias=set())
    with pytest.raises(KeyError):
        clave_conflicto(a)


# ------------- R14 · la clave, con los valores de hoy -------------- #

def test_f002_r14_la_clave_lleva_los_cuatro_campos():
    assert clave_conflicto(accion()) == "200|202607|5|80001"


def test_f002_r14_la_clave_rellena_el_mes_a_dos_digitos():
    """Sin el relleno, enero (2026 + 1) y octubre (202 + 61) podrían
    colisionar al concatenar."""
    assert clave_conflicto(accion(mes=1)) == "200|202601|5|80001"


def test_f002_r14_la_clave_de_una_accion_incompleta_no_revienta():
    """Una acción omitida no tiene recurso, hora ni partida: la clave se
    calcula igual (el API la publica para TODAS las acciones)."""
    a = accion(accion="omitir", recurso_ide=None, hora_ide=None, paride=0)
    assert clave_conflicto(a) == "0|202607|0|0"


def test_f002_r14_la_clave_no_depende_del_destino():
    """La misma acción da la misma clave en obra y en postventa: la cadena
    viaja al front y vuelve, y ahí no hay destino."""
    assert clave_conflicto(accion(destino="obra")) == \
        clave_conflicto(accion(destino="postventa"))


# ------- R14 · el criterio, con la conducta de hoy (pre-D2) -------- #

def test_f002_r14_choca_el_mismo_recurso_y_codigo_en_otro_dia():
    """La línea previa es del día 15 y la nuestra del 31: choca igual, el
    parte es mensual."""
    assert criterio_choque(linea_previa(fecha_int=20260715), accion(),
                           mias=set()) is True


def test_f002_r14_no_choca_otro_recurso():
    assert criterio_choque(linea_previa(reside=999), accion(),
                           mias=set()) is False


def test_f002_r14_no_choca_otro_codigo_de_hora():
    assert criterio_choque(linea_previa(horide=9, hora_codigo="HEGR"),
                           accion(), mias=set()) is False


def test_f002_r14_en_obra_normal_la_partida_no_distingue():
    """Conducta de HOY (versión A del README). La cambia D2, y cuando la
    cambie, este test es el que lo dirá."""
    assert criterio_choque(linea_previa(paride=0), accion(paride=80001),
                           mias=set()) is True


def test_f002_r14_en_postventa_la_partida_si_distingue():
    """En la obra de postventa cada partida es una obra original distinta:
    un mismo recurso tiene una línea legítima por cada una."""
    a = accion(destino="postventa", paride=70001)
    assert criterio_choque(linea_previa(paride=70001), a, mias=set()) is True
    assert criterio_choque(linea_previa(paride=70002), a, mias=set()) is False


def test_f002_r14_lo_nuestro_no_choca_con_nosotros_mismos():
    """Una línea con una synckey de esta misma ejecución no es conflicto:
    se reescribe sin preguntar."""
    previa = linea_previa(synckey="porcentajes:1")
    assert criterio_choque(previa, accion(), mias={"porcentajes:1"}) is False


def test_f002_r14_una_synckey_ajena_si_choca():
    """Pero una synckey que NO es de esta ejecución sigue siendo un apunte
    de otro: choca como cualquier otra línea."""
    previa = linea_previa(synckey="porcentajes:777")
    assert criterio_choque(previa, accion(), mias={"porcentajes:1"}) is True


def test_f002_r14_una_linea_sin_synckey_choca():
    """La línea metida a mano por Administración no tiene synckey."""
    assert criterio_choque(linea_previa(synckey=None), accion(),
                           mias={"porcentajes:1"}) is True


def test_f002_r14_los_valores_ausentes_valen_cero():
    """`paride = None` en Sigrid y `paride = 0` son el mismo destino: sin
    partida. Si no se normalizaran, `None != 0` inventaría un conflicto que
    no existe (o al revés)."""
    a = accion(destino="postventa", paride=0)
    assert criterio_choque(linea_previa(paride=None), a, mias=set()) is True
    assert criterio_choque(linea_previa(paride=0), a, mias=set()) is True
    sin_hora = accion(hora_ide=None, destino="postventa", paride=0)
    assert criterio_choque(linea_previa(horide=None, paride=None), sin_hora,
                           mias=set()) is True
