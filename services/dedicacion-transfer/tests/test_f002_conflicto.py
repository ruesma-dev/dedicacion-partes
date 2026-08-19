# tests/test_f002_conflicto.py
"""F-002 · La clave del conflicto y el criterio de choque no pueden divergir.

R14. Las dos salen de la misma tupla (`CAMPOS_CLAVE`) y del mismo derivado
(`campos_identidad`). Lo que se vigila aquí no es un valor concreto: es que
tocar la tupla mueva **las dos cosas a la vez**. Divergieron una vez —la
clave incluía la partida y el filtro del pipeline no la comparaba— y estos
tests están para que no vuelva a pasar en silencio.

Los enunciados normativos viven en `docs/ARCHITECTURE.md`
(`#regla-conflicto`). Aquí solo se comprueba el mecanismo.

R20-R22 son la **Regla A**, la decisión D2: la identidad de una línea del
parte es recurso + mes + código de hora + **partida**, con el mismo criterio
en la obra normal y en la de postventa. Los dos tests de T4 que fijaban la
conducta contraria están reescritos como R20; no se han borrado, se han
dado la vuelta, que es justo para lo que se escribieron.
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
    assert set(campos_identidad()) <= set(CAMPOS_CLAVE)


def test_f002_r14_todo_campo_comparado_sabe_leerse_de_las_dos_partes():
    """R14 · Un campo de la identidad, o se sabe leer de la línea existente,
    o está declarado implícito del parte. No hay tercera opción silenciosa."""
    for campo in campos_identidad():
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

    assert campos_identidad() == ("recurso", "periodo", "hora")
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
    assert criterio_choque(linea_previa(fecha_int=20260715, paride=80001),
                           accion(), mias=set()) is True


def test_f002_r14_no_choca_otro_recurso():
    assert criterio_choque(linea_previa(reside=999, paride=80001), accion(),
                           mias=set()) is False


def test_f002_r14_no_choca_otro_codigo_de_hora():
    assert criterio_choque(
        linea_previa(horide=9, hora_codigo="HEGR", paride=80001),
        accion(), mias=set()) is False


# -------------- R20 · la partida entra en la identidad ------------- #

@pytest.mark.parametrize("destino, paride", [("obra", 80001),
                                             ("postventa", 70001)])
def test_f002_r20_la_partida_entra_en_la_identidad(destino, paride):
    """R20 · La identidad es recurso + mes + código de hora + PARTIDA, en la
    obra normal y en la de postventa, **con el mismo criterio**.

    Este test sustituye a los dos de T4 que fijaban la conducta contraria:
    `..._en_obra_normal_la_partida_no_distingue` (versión del README, que era
    lo que hacía el código) y `..._en_postventa_la_partida_si_distingue`. La
    decisión D2 dice que no hay dos criterios: hay uno.
    """
    a = accion(destino=destino, paride=paride)
    assert criterio_choque(linea_previa(paride=paride), a,
                           mias=set()) is True
    assert criterio_choque(linea_previa(paride=paride + 1), a,
                           mias=set()) is False


def test_f002_r20_los_cuatro_campos_deciden():
    """R20 · Y son los CUATRO: cambiar cualquiera de ellos rompe la
    identidad. El periodo no se compara contra la línea existente porque el
    propio parte ya lo fija (`IMPLICITOS_DEL_PARTE`)."""
    a = accion(destino="obra", paride=80001)
    assert criterio_choque(linea_previa(paride=80001), a, mias=set()) is True

    for cambio in ({"reside": 999}, {"horide": 9}, {"paride": 80002}):
        previa = linea_previa(**{"paride": 80001, **cambio})
        assert criterio_choque(previa, a, mias=set()) is False, cambio


def test_f002_r20_el_destino_ya_no_decide_nada():
    """R20 · La misma línea previa y la misma partida dan el mismo veredicto
    sea cual sea el destino. Mientras `campos_identidad` recibía el destino,
    dos líneas idénticas podían chocar o no según de dónde vinieran."""
    for paride in (0, 80001):
        previa = linea_previa(paride=paride)
        assert criterio_choque(previa, accion(destino="obra", paride=paride),
                               mias=set()) \
            == criterio_choque(previa,
                               accion(destino="postventa", paride=paride),
                               mias=set())


# ------- R21 · otra partida no es conflicto, y no se toca ---------- #

def test_f002_r21_otra_partida_no_es_conflicto():
    """R21 · EL cambio de conducta de la feature. Una línea `M*` previa del
    mismo recurso y mes con OTRA partida es una línea legítima distinta —la
    metió Administración a mano contra otra partida— y no se pisa.

    Antes chocaba, y confirmar el pisado la borraba."""
    assert criterio_choque(linea_previa(paride=0), accion(paride=80001),
                           mias=set()) is False


def test_f002_r21_sin_partida_en_las_dos_si_choca():
    """R21 · Control positivo: si ninguna de las dos tiene partida (`0` y
    `None` son lo mismo en Sigrid), sí son la misma línea. La regla nueva no
    es «nunca choca»: es «choca cuando coincide la partida»."""
    a = accion(paride=0)
    assert criterio_choque(linea_previa(paride=0), a, mias=set()) is True
    assert criterio_choque(linea_previa(paride=None), a, mias=set()) is True


# ------------ R22 · lo nuestro no choca con nosotros mismos -------- #

def test_f002_r22_lo_nuestro_no_choca_con_nosotros_mismos():
    """R22 · Una línea con una synckey de esta misma ejecución no es
    conflicto: se reescribe sin preguntar. (Estaba en R14; su sitio es R22.)"""
    previa = linea_previa(synckey="porcentajes:1", paride=80001)
    assert criterio_choque(previa, accion(), mias={"porcentajes:1"}) is False


def test_f002_r22_una_synckey_ajena_si_choca():
    """R22 · Pero una synckey que NO es de esta ejecución sigue siendo un
    apunte de otro: choca como cualquier otra línea."""
    previa = linea_previa(synckey="porcentajes:777", paride=80001)
    assert criterio_choque(previa, accion(), mias={"porcentajes:1"}) is True


def test_f002_r22_una_linea_sin_synckey_choca():
    """R22 · La línea metida a mano por Administración no tiene synckey."""
    assert criterio_choque(linea_previa(synckey=None, paride=80001),
                           accion(), mias={"porcentajes:1"}) is True


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
