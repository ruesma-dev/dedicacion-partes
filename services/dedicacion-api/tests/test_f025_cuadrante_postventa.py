# tests/test_f025_cuadrante_postventa.py
"""Tests offline de F-025 en el cuadrante de la api (R17-R20).

Trazabilidad con `specs/F-025-obras-postventa-postv2/requirements.md`. Una
obra se ofrece como normal si está `activa` y como `Postv-` si
`admite_postventa`; una línea es `ofrecible` según su modo, con UNA sola
definición (`Linea.ofrecible`). La regla está en
`docs/ARCHITECTURE.md#regla-p5`.

Offline: los repositorios con una sesión falsa que captura la sentencia y
los casos de uso con una UnitOfWork en memoria. Ni red, ni BBDD, ni `.env`.
"""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest
from application.use_cases import (
    CopiarPeriodoAnterior,
    CopiarTrabajadorAnterior,
    DeshacerUltimaModificacion,
    GuardarAsignaciones,
    ObtenerCuadrante,
)
from domain.errors import ObraNoValida
from domain.models import (
    CuadranteTrabajador,
    FiltroEmpresa,
    Linea,
    Obra,
    Periodo,
    Trabajador,
)
from infrastructure.db.repositories import PgObraRepository, _a_linea, _a_obra
from interface_adapters.api.schemas import a_obra_out, a_trabajador_out
from sqlalchemy.dialects import postgresql

from tests.test_f024_rutas_empresa import BASE, api  # noqa: F401 (fixture)

ANIO, MES = 2026, 7
P_ACT, P_ANT = 2, 1


def _o(ide: int, activa: bool, admite: bool, empresa: int = 1) -> Obra:
    return Obra(ide=ide, cod=f"0{ide}", descripcion=f"OBRA {ide}",
                estado_sigrid=None, activa=activa, empresa=empresa,
                admite_postventa=admite)


#: 200 solo normal · 201 solo postventa (cerrada en el universo) · 202 las
#: dos · 203 ninguna (cerrada fuera del universo, usada en el periodo) ·
#: 900 solo postventa pero de la 28.
OBRAS = {o.ide: o for o in [
    _o(200, True, False), _o(201, False, True), _o(202, True, True),
    _o(203, False, False), _o(900, False, True, empresa=28)]}


def _ln(obra_ide: int, pv: bool, pct: str = "10") -> Linea:
    o = OBRAS[obra_ide]
    return Linea(obra_ide=obra_ide, es_postventa=pv, porcentaje=Decimal(pct),
                 cod=o.cod, descripcion=o.descripcion, obra_activa=o.activa,
                 obra_empresa=o.empresa,
                 obra_admite_postventa=o.admite_postventa)


# ============================ R17 · repositorio ========================== #
class _Escalares:
    def __init__(self, valores: list[Any]) -> None:
        self._valores = valores

    def all(self) -> list[Any]:
        return list(self._valores)


class _Sesion:
    """Sesión falsa: guarda cada sentencia y devuelve las filas fijadas."""

    def __init__(self, valores: list[Any] | None = None) -> None:
        self.valores = valores or []
        self.sentencias: list[Any] = []

    def scalars(self, stmt: Any) -> _Escalares:
        self.sentencias.append(stmt)
        return _Escalares(self.valores)

    def execute(self, stmt: Any) -> _Escalares:
        self.sentencias.append(stmt)
        return _Escalares(self.valores)


def _sql(stmt: Any) -> str:
    return " ".join(str(stmt.compile(dialect=postgresql.dialect())).split())


def _orm(ide: int, activa: bool, admite: bool) -> SimpleNamespace:
    return SimpleNamespace(ide=ide, cod=f"0{ide}", descripcion=f"OBRA {ide}",
                           estado_sigrid="CERRADA", activa=activa, empresa=1,
                           admite_postventa=admite)


def test_f025_r17_el_periodo_lista_activas_las_que_admiten_y_las_usadas():
    """R17 · El maestro del periodo trae las obras activas, las que admiten
    postventa (aunque estén cerradas) y las usadas en el periodo."""
    sesion = _Sesion([_orm(201, False, True)])
    obras = PgObraRepository(sesion).listar_para_periodo(P_ACT)  # type: ignore[arg-type]
    [stmt] = sesion.sentencias
    assert ("WHERE obra.activa IS true OR obra.admite_postventa IS true OR "
            "obra.ide IN (SELECT asignacion.obra_ide") in _sql(stmt)
    assert [(o.ide, o.activa, o.admite_postventa) for o in obras] == [
        (201, False, True)]


@pytest.mark.parametrize("admite", [True, False])
def test_f025_r17_la_obra_de_dominio_lleva_su_marca(admite: bool):
    """R17 · `_a_obra` copia `admite_postventa` de la fila."""
    assert _a_obra(_orm(1, True, admite)).admite_postventa is admite  # type: ignore[arg-type]


def test_f025_r20_modos_ofrecibles_lee_las_dos_marcas():
    """R20 · `modos_ofrecibles` devuelve (activa, admite_postventa) por obra."""
    sesion = _Sesion([(200, True, False), (201, False, True)])
    modos = PgObraRepository(sesion).modos_ofrecibles({200, 201})  # type: ignore[arg-type]
    assert modos == {200: (True, False), 201: (False, True)}
    [stmt] = sesion.sentencias
    sql = _sql(stmt)
    assert sql.startswith(
        "SELECT obra.ide, obra.activa, obra.admite_postventa FROM obra")
    assert "WHERE obra.ide IN (__[POSTCOMPILE_ide_1])" in sql


def test_f025_r20_modos_ofrecibles_sin_ides_no_consulta():
    """R20 · Sin obras no hay consulta."""
    sesion = _Sesion([(200, True, False)])
    assert PgObraRepository(sesion).modos_ofrecibles(set()) == {}  # type: ignore[arg-type]
    assert sesion.sentencias == []


# ======================= R17-R18 · salida de la API ====================== #
@pytest.mark.parametrize("admite", [True, False])
def test_f025_r17_obra_out_publica_admite_postventa(admite: bool):
    """R17 · Cada obra del cuadrante publica `admite_postventa`."""
    out = a_obra_out(_o(201, False, admite))
    assert out.admite_postventa is admite and out.activa is False


@pytest.mark.parametrize("admite", [True, False])
def test_f025_r18_a_linea_mapea_la_marca_de_la_obra(admite: bool):
    """R18 · La línea leída lleva `obra_admite_postventa` de su obra."""
    asignacion = SimpleNamespace(obra_ide=201, es_postventa=True,
                                 porcentaje=Decimal("40.00"))
    linea = _a_linea(asignacion, _orm(201, False, admite))  # type: ignore[arg-type]
    assert linea.obra_admite_postventa is admite
    assert linea.ofrecible is admite


def test_f025_r18_linea_out_publica_la_marca_y_ofrecible():
    """R18 · Cada línea publica `obra_admite_postventa` y `ofrecible`, que
    sale de `Linea.ofrecible` (la normal en 201 no lo es; su `Postv-`, sí)."""
    t = Trabajador(ide=10, cod="10", nombre="Ana", dni=None, categoria=None,
                   empresa=1)
    lineas = [_ln(200, False), _ln(200, True), _ln(201, False),
              _ln(201, True), _ln(203, False)]
    out = a_trabajador_out(CuadranteTrabajador(trabajador=t, lineas=lineas), 1)
    assert [(ln.obra_ide, ln.es_postventa, ln.obra_admite_postventa,
             ln.ofrecible) for ln in out.lineas] == [
        (200, False, False, True), (200, True, False, False),
        (201, False, True, False), (201, True, True, True),
        (203, False, False, False)]


# ===================== casos de uso: UoW en memoria ====================== #
class _Obras:
    def listar_para_periodo(self, periodo_id: int) -> list[Obra]:
        return list(OBRAS.values())

    def existen(self, ides: set[int]) -> set[int]:
        return ides & set(OBRAS)

    def modos_ofrecibles(self, ides: set[int]) -> dict[int, tuple[bool, bool]]:
        return {i: (OBRAS[i].activa, OBRAS[i].admite_postventa)
                for i in ides & set(OBRAS)}


class _Uow:
    def __init__(self, lineas: dict[int, dict[int, list[Linea]]]) -> None:
        self.lineas = lineas
        self.reemplazos: list[tuple[int, list[tuple[int, bool]]]] = []
        self.pendientes: dict[int, list[dict[str, Any]]] = {}
        t = Trabajador(ide=10, cod="10", nombre="Ana", dni=None,
                       categoria=None, empresa=1)
        uow = self
        self.trabajadores = SimpleNamespace(
            listar_para_periodo=lambda _p: [t], obtener=lambda _i: t)
        self.obras = _Obras()
        self.periodos = SimpleNamespace(
            obtener=lambda a, m: (P_ACT, Periodo(a, m)),
            anterior_con_datos=lambda a, m: (P_ANT, Periodo(a, m - 1)))

        class _Asig:
            def lineas_de_trabajador(self, p: int, ide: int) -> list[Linea]:
                return list(uow.lineas.get(p, {}).get(ide, []))

            def lineas_del_periodo(self, p: int) -> dict[int, list[Linea]]:
                return {k: list(v) for k, v in uow.lineas.get(p, {}).items()}

            def reemplazar(self, p, ide, lineas, usuario) -> None:
                uow.lineas.setdefault(p, {})[ide] = [
                    _ln(ln.obra_ide, ln.es_postventa, str(ln.porcentaje))
                    for ln in lineas]
                uow.reemplazos.append(
                    (p, [(ln.obra_ide, ln.es_postventa) for ln in lineas]))

        class _Eventos:
            def registrar(self, p, ide, tipo, usuario, antes, despues):
                uow.pendientes[ide] = antes

            def ultimo_pendiente(self, p, ide):
                return (1, uow.pendientes[ide]) if ide in uow.pendientes \
                    else None

            def marcar_deshecho(self, evento_id):
                uow.pendientes.clear()

            def trabajadores_con_pendientes(self, p):
                return set(uow.pendientes)

        self.asignaciones = _Asig()
        self.eventos = _Eventos()

    def commit(self) -> None:
        return None


F = FiltroEmpresa(empresa=1, por_defecto=1, empresa_obras=1)

#: Las seis combinaciones del periodo anterior: tres ofrecibles.
ANTERIOR = [_ln(200, False), _ln(200, True), _ln(201, False),
            _ln(201, True), _ln(202, True), _ln(203, False)]
OFRECIBLES = [(200, False), (201, True), (202, True)]


@pytest.mark.parametrize("filtro", [F, FiltroEmpresa(28, 1, 1)])
def test_f025_r17_el_cuadrante_ofrece_las_de_la_empresa_de_las_obras(filtro):
    """R17 · Con cualquier empresa elegida, las obras ofrecidas son las de
    la empresa de las obras: también la cerrada que solo admite postventa
    (201) y la usada sin ninguna marca (203); la 900 (de la 28), no."""
    cuadrante = ObtenerCuadrante().ejecutar(_Uow({}), ANIO, MES, filtro)
    assert sorted(o.ide for o in cuadrante.obras) == [200, 201, 202, 203]


def test_f025_r19_copiar_el_periodo_solo_copia_las_ofrecibles():
    """R19 · Copia del periodo entero: solo las líneas ofrecibles; las demás
    se cuentan como omitidas."""
    uow = _Uow({P_ANT: {10: ANTERIOR}})
    r = CopiarPeriodoAnterior().ejecutar(uow, ANIO, MES, "u", filtro=F)
    assert uow.reemplazos == [(P_ACT, OFRECIBLES)]
    assert (r.trabajadores_copiados, r.lineas_omitidas_obra_inactiva) == (1, 3)


def test_f025_r19_sin_ninguna_ofrecible_no_se_copia_nada():
    """R19 · Si ninguna línea es ofrecible, el trabajador cuenta como sin
    datos y no se escribe nada."""
    uow = _Uow({P_ANT: {10: [_ln(201, False), _ln(203, False)]}})
    r = CopiarPeriodoAnterior().ejecutar(uow, ANIO, MES, "u", filtro=F)
    assert uow.reemplazos == []
    assert (r.sin_datos_origen, r.lineas_omitidas_obra_inactiva) == (1, 2)


def test_f025_r19_copiar_un_trabajador_solo_copia_las_ofrecibles():
    """R19 · Copia de un trabajador: lo mismo, y devuelve las omitidas."""
    uow = _Uow({P_ANT: {10: ANTERIOR}})
    *_, omitidas = CopiarTrabajadorAnterior().ejecutar(
        uow, ANIO, MES, 10, "u", filtro=F)
    assert uow.reemplazos == [(P_ACT, OFRECIBLES)]
    assert omitidas == 3


def _guardar(uow: _Uow, *lineas: tuple[int, bool, str]) -> None:
    GuardarAsignaciones().ejecutar(
        uow, ANIO, MES, 10,
        [{"obra_ide": o, "es_postventa": pv, "porcentaje": p}
         for o, pv, p in lineas], "u", filtro=F)


@pytest.mark.parametrize("obra, pv", [(201, False), (200, True), (203, False)],
                         ids=["normal-solo-pv", "pv-sin-universo", "ninguna"])
def test_f025_r20_guardar_rechaza_una_linea_nueva_no_ofrecible(obra, pv):
    """R20 · Una línea NUEVA no ofrecible tumba el guardado entero (422,
    `ObraNoValida`): ni la ofrecible que la acompaña se guarda."""
    uow = _Uow({})
    with pytest.raises(ObraNoValida, match=f"{obra}"):
        _guardar(uow, (200, False, "50"), (obra, pv, "50"))
    assert uow.reemplazos == []


def test_f025_r20_guardar_acepta_las_lineas_nuevas_ofrecibles():
    """R20 · Control: las ofrecibles en su modo se guardan."""
    uow = _Uow({})
    _guardar(uow, (200, False, "40"), (201, True, "30"), (202, True, "30"))
    assert uow.reemplazos == [(P_ACT, [(200, False), (201, True), (202, True)])]


def test_f025_r20_la_linea_ya_guardada_se_puede_volver_a_guardar():
    """R20 · Lo ya guardado se queda (D5): la línea no ofrecible que ya
    estaba (misma obra y modo) se puede volver a guardar, aunque cambie su
    porcentaje."""
    uow = _Uow({P_ACT: {10: [_ln(203, False, "60"), _ln(201, False, "40")]}})
    _guardar(uow, (203, False, "50"), (201, False, "50"))
    assert uow.reemplazos == [(P_ACT, [(203, False), (201, False)])]


def test_f025_r20_cambiar_de_modo_es_una_linea_nueva():
    """R20 · Guardada como `Postv-` 201 (ofrecible), pasarla a normal es una
    línea nueva no ofrecible: se rechaza."""
    uow = _Uow({P_ACT: {10: [_ln(201, True, "100")]}})
    with pytest.raises(ObraNoValida):
        _guardar(uow, (201, False, "100"))


def test_f025_r20_deshacer_no_cambia():
    """R20 · Deshacer restaura lo de antes, ofrecible o no."""
    uow = _Uow({P_ACT: {10: [_ln(203, False, "100")]}})
    _guardar(uow, (200, False, "100"))
    DeshacerUltimaModificacion().ejecutar(uow, ANIO, MES, 10, "u", filtro=F)
    assert uow.reemplazos[-1] == (P_ACT, [(203, False)])


def test_f025_r20_el_422_por_http(api):  # noqa: F811
    """R20 · Por HTTP: `PUT …/asignaciones` con una línea nueva no ofrecible
    (normal en la obra 102 de `test_f024_…`, desactivada) responde 422."""
    cliente, _contenedor = api
    r = cliente.put(f"{BASE}/trabajadores/14/asignaciones", json={
        "lineas": [{"obra_ide": 102, "es_postventa": False,
                    "porcentaje": 100}]})
    assert r.status_code == 422, r.text
    assert "102" in r.json()["error"]
