# tests/test_f051_hmores_ide.py
"""F-051 · La api manda y guarda el `hmores.ide` de cada asignación (R14,
R16).

El transfer localiza lo ya registrado por `hmores.ide` además de por
`synckey` (una línea editada de otro sistema conserva su `synckey`). La api
manda en cada línea el `sigrid_hmores_ide` que tenga la asignación y, al
volver de `ejecutar`, guarda el de cada escrita (como hoy) y el de cada ya
registrada (`ya_registradas_ide`, nuevo): así se completan las registradas
antes de F-051.

Sesión y transfer falsos de `test_f022_empresa_en_linea.py`. Ni red ni BBDD.
"""
from __future__ import annotations

from types import SimpleNamespace

from application.registro_sigrid import RegistroSigrid

from tests.test_f022_empresa_en_linea import _Sesion, _Transfer


def _fila(asig_id: int, **asig) -> tuple:
    asignacion = SimpleNamespace(id=asig_id, porcentaje=40,
                                 es_postventa=False,
                                 partida_ide=None, partida_cod=None,
                                 propuesta_ide=None, propuesta_cod=None,
                                 propuesta_res=None, propuesta_metodo=None,
                                 propuesta_origen=None, **asig)
    trabajador = SimpleNamespace(ide=200 + asig_id, dni=None,
                                 nombre=f"T{asig_id}", categoria="Encargado",
                                 empresa=None, activo=True, fecha_baja=None)
    obra = SimpleNamespace(ide=678, cod="0678", descripcion="OBRA",
                           empresa=1, registro_obra_ide=None,
                           registro_obra_cod=None, registro_paride=None)
    return asignacion, trabajador, obra


def _lineas(filas: list[tuple]) -> list[dict]:
    transfer = _Transfer()
    RegistroSigrid(lambda: _Sesion(filas), transfer, 1).ejecutar(
        2026, 10, pisar_claves=[])
    [payload] = transfer.payloads
    return payload["lineas"]


def test_f051_r14_la_linea_lleva_su_hmores_ide():
    lineas = _lineas([_fila(1, sigrid_hmores_ide=410600),
                      _fila(2, sigrid_hmores_ide=None)])
    assert lineas[0]["hmores_ide"] == 410600
    assert "hmores_ide" not in lineas[1]


def test_f051_r14_sin_la_columna_viaja_como_hoy():
    """Una asignación sin `sigrid_hmores_ide` (los dobles de antes de
    F-051 no la traen) viaja exactamente como antes."""
    con, sin = _lineas([_fila(1, sigrid_hmores_ide=None)]), _lineas([_fila(1)])
    assert con == sin and "hmores_ide" not in sin[0]


# ------------------------------- R16 · traza ------------------------------- #
class _SesionQueAnota:
    def __init__(self) -> None:
        self.sentencias: list = []

    def __enter__(self) -> _SesionQueAnota:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def execute(self, sentencia) -> None:
        self.sentencias.append(sentencia)

    def commit(self) -> None:
        return None


def _trazar(respuesta: dict) -> list[tuple[int, dict]]:
    """(id de la asignación, valores) de cada UPDATE de la traza."""
    sesion = _SesionQueAnota()
    RegistroSigrid(lambda: sesion, _Transfer(), 1)._trazar(respuesta, "yo")
    out = []
    for st in sesion.sentencias:
        p = st.compile().params
        out.append((p["id_1"], {k: v for k, v in p.items()
                                if not k.endswith("_1")}))
    return out


def test_f051_r16_guarda_el_ide_de_cada_ya_registrada():
    trazas = _trazar({"escritas": [], "omitidas": [],
                      "ya_registradas": [2, 3],
                      "ya_registradas_ide": {"2": 9002, "3": None}})
    assert [(i, v) for i, v in trazas if "sigrid_hmores_ide" in v] == [
        (2, {"sigrid_hmores_ide": 9002})]
    # El estado sube como hoy, para las dos.
    assert [i for i, v in trazas if v.get("sigrid_estado")] == [2, 3]


def test_f051_r16_la_escrita_editada_guarda_su_ide_como_hoy():
    trazas = _trazar({"escritas": [{"registro_id": 1, "editada": True,
                                    "hmores_ide": 410600,
                                    "parte_cod": "PT26/00370"}],
                      "omitidas": [], "ya_registradas": []})
    [(i, v)] = trazas
    assert (i, v["sigrid_hmores_ide"], v["sigrid_parte_cod"]) == (
        1, 410600, "PT26/00370")


def test_f051_r16_respuesta_sin_ya_registradas_ide_como_hoy():
    sin = _trazar({"escritas": [], "omitidas": [], "ya_registradas": [2]})
    assert sin == [(2, {"sigrid_estado": "registrado"})]
