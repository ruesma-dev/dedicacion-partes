# tests/test_f065_ficha_activa_en_su_sitio.py
"""F-065 · La ficha de incidencia activa que se queda a 0 sale en su sitio
(`sdd: false`; los «R» son los `acceptance` de la feature en
`harness/features.json`, por orden).

- R1: con una ficha de incidencia activa que se queda a 0, la fila de fichas
  la enseña en su posición por letra (y nombre) entre las presentes, no al
  final; con los demás casos, el orden y el contenido no cambian (eso lo
  siguen fijando los tests de F-063, sin tocar sus aserciones).

Origen: O1 de la review 1 de F-063 (`progress/review_F-063.md`). Reutiliza el
arnés de node de `test_f063_filtro_incidencia.py` (el código REAL de `app.js`
con un DOM de mentira) y sus dobles, que llevan la forma serializada de
`TrabajadorOut` / `IncidenciaOut`. Sin `node`, se saltan con su motivo. Sin
red ni BBDD.
"""
from __future__ import annotations

from tests.test_f063_filtro_incidencia import (
    FICHAS_ESTADO,
    TODOS,
    _escena,
    _estado,
    _funcion,
    _inc,
    _linea,
    _textos,
    _trab,
    _trabajadores,
)

#: Quitar en el editor todas las enfermedades del mes y repintar la cabecera,
#: como hace la pantalla tras guardar la fila.
QUITAR_ENFERMEDADES = (
    "state.trabajadores.forEach((t) => { t.incidencias = "
    "t.incidencias.filter((i) => i.codigo !== 'CIE'); }); renderCabecera()")


def test_f065_r1_la_activa_a_0_sale_por_letra_y_no_al_final():
    """«B» activa (Benito; la de Ana está quitada) y se quita en el editor la
    única enfermedad: «B Enfermedad 0» sigue delante de «P» y «V», donde
    estaba, no detrás. Con otro clic se quita y las demás no se mueven."""
    fotos = _escena(['pulsar("B Enfermedad 1")', QUITAR_ENFERMEDADES,
                     'pulsar("B Enfermedad 0")'])
    presentes = ["P Permiso 1", "V Vacaciones 2"]
    # Activa y presente: misma fila que sin filtro (ni duplicada ni movida).
    assert _textos(fotos[1]) == _textos(fotos[0]) == [
        *FICHAS_ESTADO, "B Enfermedad 1", *presentes]
    # Activa y a 0: en su sitio por letra.
    assert _textos(fotos[2]) == [*FICHAS_ESTADO, "B Enfermedad 0", *presentes]
    assert fotos[2]["activas"] == ["B Enfermedad 0"]
    assert fotos[2]["visibles"] == []
    # Quitada: desaparece y el resto sigue igual.
    assert _textos(fotos[3]) == [*FICHAS_ESTADO, *presentes]
    assert fotos[3]["activas"] == [] and fotos[3]["visibles"] == TODOS


def test_f065_r1_la_activa_a_0_desempata_por_nombre_con_la_misma_letra():
    """«V Vacaciones» activa y a 0, con «V Vacaciones año anterior» (otro
    código, misma letra) presente: a igual letra, por nombre, así que la
    activa va delante de la otra V y detrás de la P."""
    otra = {**_inc("CIV", 1, 2, id_=20), "codigo": "CIVA",
            "nombre": "Vacaciones año anterior"}
    trabajadores = [
        _trab(1, "Ana", "OK", [_linea(1, 100)], [otra]),
        _trab(2, "Benito", "OK", [_linea(1, 100)], [_inc("CIP", 3, 4, id_=21)]),
    ]
    filtro_v = {"codigo": "CIV", "letra": "V", "nombre": "Vacaciones"}
    foto = _escena([], _estado(trabajadores, filtroIncidencia=filtro_v))[0]
    assert _textos(foto)[len(FICHAS_ESTADO):] == [
        "P Permiso 1", "V Vacaciones 0", "V Vacaciones año anterior 1"]
    assert foto["activas"] == ["V Vacaciones 0"]


def test_f065_r1_sin_filtro_activo_la_fila_no_cambia():
    """Los demás casos: sin ficha activa, las del mes y en el mismo orden que
    hoy (las presentes de `_trabajadores`, sin ninguna a 0)."""
    sin_b = [{**t, "incidencias": [i for i in t["incidencias"]
                                   if i["codigo"] != "CIE"]}
             for t in _trabajadores()]
    assert _textos(_escena([], _estado(sin_b))[0]) == [
        *FICHAS_ESTADO, "P Permiso 1", "V Vacaciones 2"]


def test_f065_r1_el_orden_de_las_fichas_vive_en_un_solo_sitio():
    """El orden (letra con `localeCompare` «es», desempate por nombre) se
    define una vez, en `tiposIncidenciaDelMes`: `renderCabecera` no ordena ni
    compara por su cuenta, ni añade fichas detrás del orden."""
    cabecera = _funcion("renderCabecera") or ""
    assert cabecera, "no existe renderCabecera en app.js"
    for prohibido in ("localeCompare", ".sort(", "tipos.push("):
        assert prohibido not in cabecera, prohibido
    assert "localeCompare" in (_funcion("tiposIncidenciaDelMes") or "")
