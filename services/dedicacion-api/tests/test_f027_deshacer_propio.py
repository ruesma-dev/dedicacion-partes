# tests/test_f027_deshacer_propio.py
"""F-027 · Deshacer solo lo propio (decisión A del 2026-10-04).

Solo se deshace si el ÚLTIMO evento pendiente del trabajador en el periodo es
del usuario que lo pide; si es de otro, se rechaza con un motivo que lo
nombra y el mismo 409 que «nada que deshacer». `puede_deshacer` (cuadrante y
fila) sigue la misma regla. Los usuarios se comparan sin mayúsculas ni
espacios en los extremos (`domain/deshacer.py`).

Offline: el repositorio con una sesión falsa que captura la sentencia, los
casos de uso con la UnitOfWork en memoria de `test_f024_cuadrante_empresa`
(con dos usuarios) y la API con `TestClient`. Ni red, ni BBDD, ni `.env`.
"""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest
from application.use_cases import (
    CopiarTrabajadorAnterior,
    DeshacerUltimaModificacion,
    GuardarAsignaciones,
    ObtenerCuadrante,
    ObtenerFilaTrabajador,
)
from domain.deshacer import clave_usuario, deshacer_permitido
from domain.errors import DeshacerAjeno, ErrorDominio, NadaQueDeshacer
from domain.models import EventoPendiente, FiltroEmpresa
from infrastructure.db.repositories import PgEventoRepository
from sqlalchemy.dialects import postgresql

from tests.test_f024_cuadrante_empresa import ANIO, MES, P_ACT, P_ANT, _ln, _uow, _Uow
from tests.test_f024_rutas_empresa import BASE, api  # noqa: F401 (fixture)


# =========================== dominio (T1) ============================== #
@pytest.mark.parametrize("autor, usuario", [
    ("pablo@ruesma.es", "pablo@ruesma.es"),
    ("Pablo@Ruesma.ES", "pablo@ruesma.es"),
    ("  pablo@ruesma.es\t", "PABLO@ruesma.es "),
])
def test_f027_r4_mismo_usuario_sin_mayusculas_ni_espacios(autor, usuario):
    assert deshacer_permitido(autor, usuario) is True


@pytest.mark.parametrize("autor, usuario", [
    ("ana@ruesma.es", "pablo@ruesma.es"),
    ("pablo@ruesma.es", "pablo@ruesma.es.otro"),   # prefijo no es el mismo
    ("pa blo@ruesma.es", "pablo@ruesma.es"),       # el interior no se toca
    (None, "pablo@ruesma.es"),                     # nada pendiente
])
def test_f027_r4_otro_usuario_o_nada_pendiente(autor, usuario):
    assert deshacer_permitido(autor, usuario) is False


def test_f027_r4_clave_usuario_es_la_unica_normalizacion():
    assert clave_usuario("  Ana.López@Ruesma.ES  ") == "ana.lópez@ruesma.es"


def test_f027_r1_el_error_es_de_dominio_y_distinto_de_nada_que_deshacer():
    assert issubclass(DeshacerAjeno, ErrorDominio)
    assert not issubclass(DeshacerAjeno, NadaQueDeshacer)


# ========================= repositorio (T2) ============================ #
class _Filas:
    def __init__(self, valores: list[Any]) -> None:
        self._valores = valores

    def all(self) -> list[Any]:
        return list(self._valores)

    def first(self) -> Any:
        return self._valores[0] if self._valores else None


class _Sesion:
    """Sesión falsa: guarda cada sentencia y devuelve los valores fijados."""

    def __init__(self, valores: list[Any]) -> None:
        self.valores = valores
        self.sentencias: list[Any] = []

    def scalars(self, stmt: Any) -> _Filas:
        self.sentencias.append(stmt)
        return _Filas(self.valores)

    def execute(self, stmt: Any) -> _Filas:
        self.sentencias.append(stmt)
        return _Filas(self.valores)


def _compilada(stmt: Any) -> tuple[str, dict[str, Any]]:
    c = stmt.compile(dialect=postgresql.dialect())
    return " ".join(str(c).split()), dict(c.params)


def test_f027_r3_ultimo_pendiente_trae_su_autor():
    orm = SimpleNamespace(id=7, usuario="ana@ruesma.es",
                          snapshot_antes=[{"obra_ide": 100}])
    sesion = _Sesion([orm])
    pendiente = PgEventoRepository(sesion).ultimo_pendiente(3, 10)  # type: ignore[arg-type]
    assert pendiente == EventoPendiente(id=7, usuario="ana@ruesma.es",
                                        snapshot_antes=[{"obra_ide": 100}])
    assert PgEventoRepository(_Sesion([])).ultimo_pendiente(3, 10) is None  # type: ignore[arg-type]


def test_f027_r3_autores_del_ultimo_pendiente_de_todo_el_periodo():
    """El autor es el del ÚLTIMO pendiente de cada trabajador (max(id) de
    los no deshechos del periodo), no «alguno pendiente mío»."""
    sesion = _Sesion([(10, "ana@ruesma.es"), (14, "pablo@ruesma.es")])
    autores = PgEventoRepository(sesion).autores_ultimo_pendiente(3)  # type: ignore[arg-type]
    assert autores == {10: "ana@ruesma.es", 14: "pablo@ruesma.es"}
    [stmt] = sesion.sentencias
    sql, params = _compilada(stmt)
    assert sql.startswith(
        "SELECT evento.trabajador_ide, evento.usuario FROM evento "
        "WHERE evento.id IN (SELECT max(evento.id) AS max_1 FROM evento "
        "WHERE evento.periodo_id = %(periodo_id_1)s "
        "AND evento.deshecho IS false GROUP BY evento.trabajador_ide)")
    assert params == {"periodo_id_1": 3}


# ========================= casos de uso (T3) =========================== #
ANA = "ana@ruesma.es"
PABLO = "pablo@ruesma.es"
EVA = 14            # Eva, de la 1 y sin carga: lienzo limpio
F1 = FiltroEmpresa(empresa=1, por_defecto=1, empresa_obras=1)


def _guardar(uow: _Uow, usuario: str, *lineas: tuple[int, str], ide=EVA):
    return GuardarAsignaciones().ejecutar(
        uow, ANIO, MES, ide,
        [{"obra_ide": o, "porcentaje": p} for o, p in lineas], usuario,
        filtro=F1)


def _deshacer(uow: _Uow, usuario: str, ide=EVA):
    return DeshacerUltimaModificacion().ejecutar(
        uow, ANIO, MES, ide, usuario, filtro=F1)


def _obras(uow: _Uow, ide=EVA) -> list[tuple[int, Decimal]]:
    return [(ln.obra_ide, ln.porcentaje)
            for ln in uow.lineas[P_ACT].get(ide, [])]


def _mensaje_ajeno(autor: str) -> str:
    return (f"La última modificación de este trabajador es de {autor}: "
            "solo puede deshacerla quien la hizo")


def test_f027_r6_deshago_lo_mio():
    uow = _uow()
    _guardar(uow, PABLO, (100, "100"))
    fila, _ = _deshacer(uow, PABLO)
    assert fila.lineas == [] and _obras(uow) == []
    assert uow.eventos.deshechos == {1}


def test_f027_r1_no_deshago_lo_del_otro():
    """Motivo legible que nombra al autor; nada se toca."""
    uow = _uow()
    _guardar(uow, ANA, (100, "100"))
    with pytest.raises(DeshacerAjeno) as exc:
        _deshacer(uow, PABLO)
    assert str(exc.value) == _mensaje_ajeno(ANA)
    assert _obras(uow) == [(100, Decimal(100))]
    assert uow.reemplazados == [EVA]          # solo el guardado de Ana
    assert uow.eventos.deshechos == set()


def test_f027_r2_el_otro_cambia_despues_y_ya_no_puedo():
    """Decisión A: tras mi cambio hay uno de Ana; no deshago el mío (no es el
    último) ni el suyo. Cuando Ana deshace el suyo, el mío vuelve a ser el
    último y entonces sí."""
    uow = _uow()
    _guardar(uow, PABLO, (100, "100"))
    _guardar(uow, ANA, (101, "100"))
    with pytest.raises(DeshacerAjeno) as exc:
        _deshacer(uow, PABLO)
    assert str(exc.value) == _mensaje_ajeno(ANA)
    assert _obras(uow) == [(101, Decimal(100))]
    assert uow.eventos.deshechos == set()

    fila_ana, _ = _deshacer(uow, ANA)
    assert _obras(uow) == [(100, Decimal(100))]
    assert fila_ana.puede_deshacer is False   # el último es ya de Pablo
    fila_pablo, _ = _deshacer(uow, PABLO)
    assert _obras(uow) == [] and fila_pablo.puede_deshacer is False
    assert uow.eventos.deshechos == {1, 2}


def test_f027_r1_nada_que_deshacer_sigue_igual():
    with pytest.raises(NadaQueDeshacer):
        _deshacer(_uow(), PABLO)


def test_f027_r4_deshago_lo_mio_con_otras_mayusculas_y_espacios():
    uow = _uow()
    _guardar(uow, ANA, (100, "100"))
    _deshacer(uow, "  ANA@Ruesma.ES ")
    assert _obras(uow) == []


@pytest.mark.parametrize("usuario, esperado", [
    (ANA, {"Ana": True, "Eva": False}),
    (PABLO, {"Ana": False, "Eva": True}),
    (" PABLO@ruesma.es ", {"Ana": False, "Eva": True}),
    ("eva@ruesma.es", {"Ana": False, "Eva": False}),
])
def test_f027_r3_puede_deshacer_por_usuario_en_el_cuadrante(usuario, esperado):
    """Ana tocó a Ana (10) y Pablo a Eva; Pablo tocó antes a Ana, pero el
    último de Ana es de Ana: no basta con «tener algo pendiente mío»."""
    uow = _uow()
    _guardar(uow, PABLO, (100, "100"), ide=10)
    _guardar(uow, ANA, (101, "100"), ide=10)
    _guardar(uow, PABLO, (100, "100"))
    cuadrante = ObtenerCuadrante().ejecutar(uow, ANIO, MES, F1,
                                            usuario=usuario)
    por_nombre = {f.trabajador.nombre: f.puede_deshacer
                  for f in cuadrante.filas}
    assert {n: por_nombre[n] for n in esperado} == esperado
    assert sum(por_nombre.values()) == sum(esperado.values())


def test_f027_r3_puede_deshacer_por_usuario_en_la_fila():
    """La fila de guardar, de deshacer y de copiar es la del que pregunta."""
    uow = _uow()
    fila, _ = _guardar(uow, ANA, (100, "100"))
    assert fila.puede_deshacer is True
    fila, _ = ObtenerFilaTrabajador().ejecutar(uow, ANIO, MES, EVA,
                                               filtro=F1, usuario=PABLO)
    assert fila.puede_deshacer is False
    # Pablo guarda lo mismo que hay: no hay evento y el último sigue de Ana.
    fila, _ = _guardar(uow, PABLO, (100, "100"))
    assert fila.puede_deshacer is False
    # Dos cambios seguidos de Pablo: deshecho uno, el otro sigue siendo suyo.
    _guardar(uow, PABLO, (101, "100"))
    _guardar(uow, PABLO, (101, "50"), (100, "50"))
    fila, _ = _deshacer(uow, PABLO)
    assert fila.puede_deshacer is True
    uow.lineas[P_ANT] = {EVA: [_ln(102, "100")]}
    fila, _r, _o, _om = CopiarTrabajadorAnterior().ejecutar(
        uow, ANIO, MES, EVA, ANA, filtro=F1)
    assert fila.puede_deshacer is True


# ============================== API (T4) =============================== #
EVA_URL = f"{BASE}/trabajadores/{EVA}"


def _como(usuario: str) -> dict[str, str]:
    return {"x-usuario": usuario}


def _put(cliente, usuario: str, obra: int = 100):
    return cliente.put(f"{EVA_URL}/asignaciones", headers=_como(usuario),
                       json={"lineas": [{"obra_ide": obra, "porcentaje": 100}]})


def _puede(cliente, usuario: str) -> dict[str, bool]:
    r = cliente.get(f"{BASE}/cuadrante", headers=_como(usuario))
    assert r.status_code == 200, r.text
    return {t["nombre"]: t["puede_deshacer"] for t in r.json()["trabajadores"]}


def test_f027_r1_por_http_lo_del_otro_es_409_con_su_nombre(api):  # noqa: F811
    """Mismo código que «nada que deshacer» y el motivo en `error`."""
    cliente, _ = api
    assert _put(cliente, ANA).json()["trabajador"]["puede_deshacer"] is True
    r = cliente.post(f"{EVA_URL}/deshacer", headers=_como(PABLO))
    assert r.status_code == 409, r.text
    assert r.json() == {"error": _mensaje_ajeno(ANA)}
    nada = cliente.post(f"{BASE}/trabajadores/10/deshacer",
                        headers=_como(PABLO))
    assert nada.status_code == r.status_code

    r = cliente.post(f"{EVA_URL}/deshacer", headers=_como(" Ana@Ruesma.es "))
    assert r.status_code == 200, r.text
    assert r.json()["trabajador"]["lineas"] == []


def test_f027_r2_por_http_el_otro_cambia_despues(api):  # noqa: F811
    cliente, _ = api
    _put(cliente, PABLO, 100)
    _put(cliente, ANA, 101)
    r = cliente.post(f"{EVA_URL}/deshacer", headers=_como(PABLO))
    assert r.status_code == 409 and ANA in r.json()["error"]
    r = cliente.post(f"{EVA_URL}/deshacer", headers=_como(ANA))
    assert r.status_code == 200, r.text
    assert r.json()["trabajador"]["puede_deshacer"] is False


def test_f027_r3_por_http_puede_deshacer_por_usuario(api):  # noqa: F811
    cliente, _ = api
    _put(cliente, PABLO)
    assert _puede(cliente, PABLO)["Eva"] is True
    assert _puede(cliente, " PABLO@ruesma.es")["Eva"] is True
    assert _puede(cliente, ANA)["Eva"] is False
    assert not any(_puede(cliente, ANA).values())
