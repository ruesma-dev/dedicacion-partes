# tests/test_f054_aceptar.py
"""F-054 · T6 y T7: aceptar entradas traídas de Sigrid (R19-R25; design
§5.2 y §5.3).

T6 (`-k repositorio`): `PgAsignacionRepository.aceptar_entrada` es UNA
sentencia `INSERT … ON CONFLICT (uq_asignacion_linea) DO UPDATE` de la
línea de esa clave: si existe, se actualiza EN SU SITIO (mismo `id`; sus
filas de `asignacion_vinculado`, que cuelgan de él con `ON DELETE CASCADE`,
no se tocan); si no, se crea. Ninguna otra fila del trabajador: ni `DELETE`
ni `UPDATE` fuera de esa clave. Lleva la traza de R23 (`sigrid_hmores_ide`,
`sigrid_parte_cod`, `sigrid_estado = registrado`, el motivo «traída de
Sigrid», sin fecha ni autor de registro) y la propuesta a nulo. Compila con
las columnas del ORM, sin base.

T7 (el resto): `TraerDeSigrid` sobre una UoW en memoria con transacción.
Comprueba el periodo antes de llamar al transfer (R2) y no escribe si este
falla (R3); sin `aceptar` solo compara (R18); cada aceptada `distinta` o
`solo_sigrid` pisa solo su línea, en su sitio y con sus subfilas (R19, R21);
las demás vuelven con motivo (R20); todo o nada (R22); la traza (R23); que
guardar la fila la pierde (R24); un evento `SIGRID` por trabajador que se
deshace (R25); D11 y el cierre entre medias.

Sin red ni BBDD.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from domain.models import Linea
from infrastructure.db.orm_models import AsignacionORM
from infrastructure.db.repositories import (
    MOTIVO_TRAIDA_DE_SIGRID,
    PgAsignacionRepository,
)
from sqlalchemy.dialects import postgresql


class _Sesion:
    """Sesión falsa: anota cada sentencia ejecutada."""

    def __init__(self) -> None:
        self.sentencias: list[Any] = []

    def execute(self, stmt: Any) -> Any:
        self.sentencias.append(stmt)
        return None


def _aceptar(linea: Linea, **kw):
    s = _Sesion()
    PgAsignacionRepository(s).aceptar_entrada(
        7, 4321, linea, hmores_ide=kw.get("hmores_ide", 9001),
        parte_cod=kw.get("parte_cod", "PT26/00319"),
        usuario=kw.get("usuario", "ana@ruesma.es"))
    return s.sentencias


def _compilada(stmt):
    return stmt.compile(dialect=postgresql.dialect())


LINEA = Linea(obra_ide=694, es_postventa=False, porcentaje=Decimal("95.00"),
              partida_ide=2105, partida_cod="CI.1.5", partida_res="JEFE")


def test_f054_r19_repositorio_una_sentencia_upsert_de_esa_clave():
    [stmt] = _aceptar(LINEA)
    sql = " ".join(str(_compilada(stmt)).split())
    assert sql.startswith("INSERT INTO asignacion (")
    assert "ON CONFLICT ON CONSTRAINT uq_asignacion_linea DO UPDATE SET" in sql
    assert "DELETE" not in sql
    p = _compilada(stmt).params
    assert (p["periodo_id"], p["trabajador_ide"], p["obra_ide"],
            p["es_postventa"]) == (7, 4321, 694, False)


def test_f054_r19_repositorio_el_update_conserva_id_y_clave():
    """El `SET` del conflicto no toca `id` ni la clave: la fila sigue
    siendo la misma (y sus subfilas, que cuelgan de su `id`)."""
    [stmt] = _aceptar(LINEA)
    sql = " ".join(str(_compilada(stmt)).split())
    puesto = sql.split("DO UPDATE SET", 1)[1]
    columnas = {t.split(" = ")[0].strip() for t in puesto.split(", ")}
    assert columnas == {
        "porcentaje", "partida_ide", "partida_cod", "partida_res",
        "propuesta_ide", "propuesta_cod", "propuesta_res",
        "propuesta_metodo", "propuesta_origen", "actualizado_en",
        "actualizado_por", "sigrid_estado", "sigrid_parte_cod",
        "sigrid_hmores_ide", "sigrid_motivo", "sigrid_registrado_at_utc",
        "sigrid_registrado_by"}
    assert not {"id", "periodo_id", "trabajador_ide", "obra_ide",
                "es_postventa"} & columnas
    orm = {c.name for c in AsignacionORM.__table__.columns}
    assert columnas <= orm


def test_f054_r23_repositorio_traza_y_valores():
    [stmt] = _aceptar(LINEA, hmores_ide=9001, parte_cod="PT26/00319",
                      usuario="ana@ruesma.es")
    p = _compilada(stmt).params
    assert p["porcentaje"] == Decimal("95.00")
    assert (p["partida_ide"], p["partida_cod"], p["partida_res"]) == (
        2105, "CI.1.5", "JEFE")
    assert (p["sigrid_estado"], p["sigrid_hmores_ide"],
            p["sigrid_parte_cod"], p["sigrid_motivo"]) == (
        "registrado", 9001, "PT26/00319", MOTIVO_TRAIDA_DE_SIGRID)
    assert MOTIVO_TRAIDA_DE_SIGRID == "traída de Sigrid"
    assert p["sigrid_registrado_at_utc"] is None
    assert p["sigrid_registrado_by"] is None
    assert p["actualizado_por"] == "ana@ruesma.es"
    assert all(p[c] is None for c in (
        "propuesta_ide", "propuesta_cod", "propuesta_res",
        "propuesta_metodo", "propuesta_origen"))


def test_f054_r17_repositorio_postventa_automatica_y_cortes():
    linea = Linea(obra_ide=678, es_postventa=True, porcentaje=Decimal(10))
    [stmt] = _aceptar(linea, parte_cod="P" * 40, usuario="u" * 90)
    p = _compilada(stmt).params
    assert p["es_postventa"] is True and p["partida_ide"] is None
    assert p["sigrid_parte_cod"] == "P" * 24
    assert p["actualizado_por"] == "u" * 90


# ===================== T7 · el caso de uso TraerDeSigrid ================= #
# UoW en memoria con transacción: `__enter__` trabaja sobre una copia de lo
# guardado y solo `commit` la deja; sin `commit`, nada (como el rollback).
# Cada fila guarda su `id` y su traza: así se ve qué fila se pisa en su
# sitio y qué traza sobrevive.
import copy
from dataclasses import replace
from types import SimpleNamespace

import pytest
from application.traer_sigrid import (
    MOTIVO_NO_ACEPTABLE,
    MOTIVO_SIN_ENTRADA,
    MOTIVO_SOLO_CUADRANTE,
    TraerDeSigrid,
)
from application.use_cases import (
    DeshacerUltimaModificacion,
    GuardarAsignaciones,
)
from domain.errors import (
    DeshacerAjeno,
    PeriodoCerrado,
    PeriodoNoEncontrado,
    PorcentajesSigridNoDisponible,
)
from domain.models import (
    EstadoPeriodo,
    EventoPendiente,
    FiltroEmpresa,
    LineaSigridTraida,
    Obra,
    Periodo,
    ResultadoExistentes,
    SubfilaVinculado,
    TipoEvento,
    Trabajador,
)
from domain.traer_sigrid import EstadoEntrada

from tests.test_f051_hmores_ide import _fila as _fila_registro
from tests.test_f051_hmores_ide import _lineas as _payload

PID = 3
FILTRO = FiltroEmpresa(empresa=1, por_defecto=1, empresa_obras=1)


def _obra(ide, activa=True, pv=False, empresa=1):
    return Obra(ide=ide, cod=f"{ide:04d}", descripcion=f"OBRA {ide}",
                estado_sigrid=None, activa=activa, empresa=empresa,
                admite_postventa=pv)


OBRAS = {o.ide: o for o in [_obra(694), _obra(678, pv=True), _obra(713),
                             _obra(900, empresa=28, pv=True)]}
TRAB = {t.ide: t for t in [
    Trabajador(ide=10, cod="10", nombre="Ana", dni=None, categoria=None,
               empresa=1),
    Trabajador(ide=20, cod="20", nombre="Bea", dni=None, categoria=None,
               empresa=1),
    Trabajador(ide=30, cod="30", nombre="Cris", dni=None, categoria=None,
               empresa=1, activo=False),
    Trabajador(ide=40, cod="40", nombre="Dan", dni=None, categoria=None,
               empresa=28)]}
SUB = (SubfilaVinculado(vinculado_ide=5000, tipo="TF", partida_ide=81,
                        partida_cod="CI.4", partida_res="TEL"),)


def _ln(obra, pct, *, pv=False, partida=None, vinculados=()):
    o = OBRAS[obra]
    return Linea(obra_ide=obra, es_postventa=pv,
                 porcentaje=Decimal(pct).quantize(Decimal("0.01")),
                 cod=o.cod, descripcion=o.descripcion, obra_activa=o.activa,
                 obra_empresa=o.empresa,
                 obra_admite_postventa=o.admite_postventa,
                 partida_ide=partida, vinculados=vinculados)


class _Datos:
    """Lo guardado: filas (`id`, `Linea`, traza), eventos y el periodo."""

    def __init__(self, lineas: dict[int, list[Linea]]) -> None:
        self.n = 0
        self.filas: dict[int, list[dict]] = {
            t: [self.fila(ln) for ln in ls] for t, ls in lineas.items()}
        self.eventos: list[tuple] = []
        self.deshechos: set[int] = set()
        self.estado = EstadoPeriodo.ABIERTO
        self.cerrar_al_aceptar = False

    def fila(self, ln: Linea, traza=None) -> dict:
        self.n += 1
        return {"id": self.n, "linea": ln, "traza": dict(traza or {})}


class _Asig:
    def __init__(self, uow) -> None:
        self.uow = uow

    @property
    def d(self) -> _Datos:
        return self.uow.d

    def lineas_de_trabajador(self, pid, ide):
        return [f["linea"] for f in self.d.filas.get(ide, [])]

    def lineas_del_periodo(self, pid):
        return {t: [f["linea"] for f in fs]
                for t, fs in self.d.filas.items() if fs}

    def reemplazar(self, pid, ide, lineas, usuario):
        """Como el de verdad: borra y recrea, sin traza."""
        self.d.filas[ide] = [self.d.fila(ln) for ln in lineas]

    def aceptar_entrada(self, pid, ide, linea, *, hmores_ide, parte_cod,
                        usuario):
        self.uow.aceptadas.append((ide, linea.clave()))
        if len(self.uow.aceptadas) == self.uow.fallar_en:
            raise RuntimeError("la base se cae a mitad")
        if self.d.cerrar_al_aceptar:
            self.d.estado = EstadoPeriodo.CERRADO
        traza = {"sigrid_hmores_ide": hmores_ide,
                 "sigrid_parte_cod": parte_cod, "sigrid_estado": "registrado",
                 "sigrid_motivo": MOTIVO_TRAIDA_DE_SIGRID}
        filas = self.d.filas.setdefault(ide, [])
        for f in filas:
            if f["linea"].clave() == linea.clave():
                f["linea"] = replace(linea, vinculados=f["linea"].vinculados)
                f["traza"] = traza
                return
        filas.append(self.d.fila(linea, traza))


class _Eventos:
    def __init__(self, uow) -> None:
        self.uow = uow

    def registrar(self, pid, ide, tipo, usuario, antes, despues):
        ev = self.uow.d.eventos
        ev.append((ide, len(ev) + 1, tipo, usuario, antes, despues))

    def ultimo_pendiente(self, pid, ide):
        d = self.uow.d
        propios = [e for e in d.eventos
                   if e[0] == ide and e[1] not in d.deshechos]
        if not propios:
            return None
        _, i, tipo, u, antes, _ = propios[-1]
        return EventoPendiente(i, u, antes, tipo.value)

    def marcar_deshecho(self, i):
        self.uow.d.deshechos.add(i)


class _Uow:
    def __init__(self, datos: _Datos, fallar_en: int = 0) -> None:
        self.guardado = datos
        self.fallar_en = fallar_en
        self.aceptadas: list = []
        self.commits = 0
        self.trabajadores = SimpleNamespace(
            listar_para_periodo=lambda pid: [
                t for t in TRAB.values()
                if t.activo or self.d.filas.get(t.ide)],
            obtener=lambda ide: TRAB.get(ide))
        self.obras = SimpleNamespace(
            listar_para_periodo=lambda pid: list(OBRAS.values()),
            existen=lambda ides: set(ides) & set(OBRAS),
            modos_ofrecibles=lambda ides: {
                i: (OBRAS[i].activa, OBRAS[i].admite_postventa)
                for i in ides if i in OBRAS})
        self.vinculados = SimpleNamespace(ides=lambda: {5000})
        self.incidencias = SimpleNamespace(de_trabajador=lambda p, i: [])
        self.periodos = SimpleNamespace(obtener=lambda a, m: (
            (PID, Periodo(a, m, self.d.estado)) if (a, m) == (2026, 9)
            else None))
        self.asignaciones = _Asig(self)
        self.eventos = _Eventos(self)

    def __enter__(self):
        self.d = copy.deepcopy(self.guardado)
        return self

    def __exit__(self, *exc):
        return None

    def commit(self):
        self.commits += 1
        self.guardado.__dict__.update(copy.deepcopy(self.d.__dict__))


class _Gateway:
    def __init__(self, lineas=(), fallo=None) -> None:
        self.lineas = list(lineas)
        self.fallo = fallo
        self.llamadas: list = []

    def porcentajes_existentes(self, empresa, anio, mes, obras):
        self.llamadas.append((empresa, anio, mes, obras))
        if self.fallo:
            raise self.fallo
        return ResultadoExistentes(lineas_leidas=len(self.lineas) + 1,
                                   excluidas_pruebas=1,
                                   motivo_postventa="pv", motivo_var=None,
                                   lineas=tuple(self.lineas))


def _s(ide, recurso, obra, can, **kw):
    return LineaSigridTraida(hmores_ide=ide, recurso_ide=recurso,
                             obra_ide=obra, obra_cod=f"{obra:04d}",
                             parte_cod=f"PT26/{ide}", can=can, **kw)


SIGRID = [_s(901, 10, 694, 0.95, paride=2105, partida_cod="CI.1.5",
             partida_res="JEFE"),
          _s(902, 10, 713, 0.05),
          _s(903, 20, 694, 1.0)]


def _traer(datos, aceptar=(), gateway=None, usuario="ana", uow=None):
    gateway = gateway or _Gateway(SIGRID)
    uow = uow or _Uow(datos)
    with uow:
        r = TraerDeSigrid(gateway).ejecutar(
            uow, 2026, 9, usuario, filtro=FILTRO, aceptar=list(aceptar))
    return r, uow, gateway


def _datos():
    """Ana: 694 al 60 % (con subfila) y 678 al 40 %; Bea, sin líneas."""
    return _Datos({10: [_ln(694, "60", vinculados=SUB), _ln(678, "40")]})


def _acepta(t, obra, pv=False):
    return {"trabajador_ide": t, "obra_ide": obra, "es_postventa": pv}


def _estados(r, ide):
    t = next(x for x in r.trabajadores if x.trabajador.ide == ide)
    return {(c.obra_ide, c.es_postventa): c.estado for c in t.comparadas}


def test_f054_r2_periodo_inexistente_o_cerrado_sin_llamar_al_transfer():
    d = _datos()
    g = _Gateway(SIGRID)
    uow = _Uow(d)
    with uow, pytest.raises(PeriodoNoEncontrado):
        TraerDeSigrid(g).ejecutar(uow, 2026, 8, "ana", filtro=FILTRO,
                                  aceptar=[])
    d.estado = EstadoPeriodo.CERRADO
    with pytest.raises(PeriodoCerrado):
        _traer(d, gateway=g)
    assert g.llamadas == []


def test_f054_r2_al_transfer_las_de_postventa_de_la_empresa_de_las_obras():
    _, _, g = _traer(_datos())
    assert g.llamadas == [(1, 2026, 9, [
        {"ide": 678, "codigo": "0678", "nombre": "OBRA 678"}])]


def test_f054_r3_si_el_transfer_falla_no_se_toca_la_base():
    d = _datos()
    antes = copy.deepcopy(d.__dict__)
    with pytest.raises(PorcentajesSigridNoDisponible):
        _traer(d, [_acepta(20, 694)],
               gateway=_Gateway(fallo=PorcentajesSigridNoDisponible("x")))
    assert d.__dict__ == antes


def test_f054_r18_sin_aceptar_compara_y_no_escribe():
    d = _datos()
    antes = copy.deepcopy(d.__dict__)
    r, uow, _ = _traer(d)
    assert _estados(r, 10) == {
        (678, False): EstadoEntrada.SOLO_CUADRANTE,
        (694, False): EstadoEntrada.DISTINTA,
        (713, False): EstadoEntrada.SOLO_SIGRID}
    assert _estados(r, 20) == {(694, False): EstadoEntrada.SOLO_SIGRID}
    assert [t.trabajador.ide for t in r.trabajadores] == [10, 20]
    assert d.__dict__ == antes and uow.commits == 0
    assert uow.aceptadas == [] and r.tocados == [] and r.rechazadas == []
    assert (r.lineas_leidas, r.excluidas_pruebas) == (4, 1)
    assert (r.motivo_postventa, r.motivo_var) == ("pv", None)


def test_f054_r19_aceptar_una_de_dos_deja_la_otra_y_las_subfilas():
    d = _Datos({10: [_ln(694, "60", vinculados=SUB),
                     _ln(713, "40", vinculados=SUB)]})
    d.filas[10][1]["traza"] = {"sigrid_hmores_ide": 777}
    ids = [f["id"] for f in d.filas[10]]
    r, uow, _ = _traer(d, [_acepta(10, 694)])
    f694, f713 = d.filas[10]
    assert [f694["id"], f713["id"]] == ids
    assert f694["linea"].porcentaje == Decimal("95.00")
    assert (f694["linea"].partida_ide, f694["linea"].partida_cod,
            f694["linea"].partida_res) == (2105, "CI.1.5", "JEFE")
    assert f694["linea"].vinculados == SUB
    assert f694["traza"]["sigrid_hmores_ide"] == 901
    assert f713["linea"] == _ln(713, "40", vinculados=SUB)
    assert f713["traza"] == {"sigrid_hmores_ide": 777}
    [t] = [x for x in r.trabajadores if x.trabajador.ide == 10]
    assert t.aceptadas == [(694, False)] and t.rechazadas == []
    assert r.tocados == [10] and uow.commits == 1
    assert uow.aceptadas == [(10, (694, False))]


@pytest.mark.parametrize("item, motivo", [
    (_acepta(10, 678), MOTIVO_SOLO_CUADRANTE),
    (_acepta(10, 999), MOTIVO_SIN_ENTRADA),
    (_acepta(10, 694, pv=True), MOTIVO_SIN_ENTRADA),
    (_acepta(77, 694), MOTIVO_SIN_ENTRADA),
])
def test_f054_r20_lo_que_no_se_acepta_vuelve_con_motivo(item, motivo):
    d = _datos()
    antes = copy.deepcopy(d.__dict__)
    r, uow, _ = _traer(d, [item])
    assert r.rechazadas == [((item["trabajador_ide"], item["obra_ide"],
                              item["es_postventa"]), motivo)]
    assert r.tocados == [] and uow.aceptadas == [] and uow.commits == 0
    assert d.__dict__ == antes


def test_f054_r20_igual_y_no_traducible_con_motivo():
    d = _Datos({10: [_ln(694, "95")]})
    g = _Gateway([*SIGRID,
                  _s(904, 10, 999001, 0.5, destino="postventa",
                     obra_origen_ide=678, paride=7),
                  _s(905, 10, 999001, 0.7, destino="postventa",
                     obra_origen_ide=678, paride=7)])
    r, uow, _ = _traer(d, [_acepta(10, 694), _acepta(10, 678, pv=True)], g)
    assert r.rechazadas == [
        ((10, 694, False), MOTIVO_NO_ACEPTABLE.format(estado="igual")),
        ((10, 678, True), MOTIVO_NO_ACEPTABLE.format(
            estado="no_traducible"))]
    [t] = [x for x in r.trabajadores if x.trabajador.ide == 10]
    assert t.rechazadas == [
        ((694, False), MOTIVO_NO_ACEPTABLE.format(estado="igual")),
        ((678, True), MOTIVO_NO_ACEPTABLE.format(estado="no_traducible"))]
    assert uow.aceptadas == [] and uow.commits == 0


def test_f054_r21_la_solo_sigrid_sin_lineas_solo_si_se_acepta():
    d = _datos()
    _traer(d, [_acepta(10, 713)])
    assert 20 not in d.filas
    r, _, _ = _traer(d, [_acepta(20, 694)])
    assert [(f["linea"].obra_ide, f["linea"].porcentaje)
            for f in d.filas[20]] == [(694, Decimal("100.00"))]
    assert r.tocados == [20]


def test_f054_r22_error_a_mitad_no_deja_nada():
    d = _datos()
    antes = copy.deepcopy(d.__dict__)
    with pytest.raises(RuntimeError, match="a mitad"):
        _traer(d, [_acepta(10, 694), _acepta(20, 694)],
               uow=_Uow(d, fallar_en=2))
    assert d.__dict__ == antes


def test_f054_r22_aceptar_dos_veces_no_cambia_nada():
    d = _datos()
    _traer(d, [_acepta(10, 694), _acepta(10, 694)])
    despues = copy.deepcopy(d.__dict__)
    assert len(d.eventos) == 1
    r, uow, _ = _traer(d, [_acepta(10, 694)])
    assert d.__dict__ == despues and uow.commits == 0
    assert r.rechazadas == [((10, 694, False),
                             MOTIVO_NO_ACEPTABLE.format(estado="igual"))]


def test_f054_r23_la_traza_de_la_aceptada():
    d = _datos()
    _traer(d, [_acepta(10, 713)])
    f = next(f for f in d.filas[10] if f["linea"].obra_ide == 713)
    assert f["traza"] == {"sigrid_hmores_ide": 902,
                          "sigrid_parte_cod": "PT26/902",
                          "sigrid_estado": "registrado",
                          "sigrid_motivo": "traída de Sigrid"}
    assert f["linea"].porcentaje == Decimal("5.00")


def test_f054_r23_el_menor_hmores_ide_de_sus_lineas():
    g = _Gateway([_s(950, 20, 694, 0.4), _s(920, 20, 694, 0.6)])
    d = _datos()
    _traer(d, [_acepta(20, 694)], g)
    assert d.filas[20][0]["traza"]["sigrid_hmores_ide"] == 920
    assert d.filas[20][0]["traza"]["sigrid_parte_cod"] == "PT26/920"


def test_f054_r24_tras_guardar_la_fila_el_payload_no_lleva_hmores_ide():
    """La aceptada viaja al registro con su `hmores_ide` (ya registrada);
    guardar la fila (`reemplazar`) pierde la traza y el registro pide un
    pisado como hoy."""
    d = _datos()
    _traer(d, [_acepta(10, 694)])

    def hmores():
        return [ln.get("hmores_ide") for ln in _payload([
            _fila_registro(f["id"], sigrid_hmores_ide=f["traza"].get(
                "sigrid_hmores_ide")) for f in d.filas[10]])]

    assert hmores() == [901, None]
    uow = _Uow(d)
    with uow:
        GuardarAsignaciones().ejecutar(
            uow, 2026, 9, 10, [{"obra_ide": 694, "porcentaje": "90"},
                               {"obra_ide": 678, "porcentaje": "10"}],
            "ana", filtro=FILTRO)
    assert hmores() == [None, None]


def test_f054_r25_un_evento_por_trabajador_con_subfilas_y_deshacer():
    d = _Datos({10: [_ln(694, "60", partida=2000, vinculados=SUB),
                     _ln(678, "40")]})
    _traer(d, [_acepta(10, 694), _acepta(10, 713), _acepta(20, 694)],
           usuario="ana")
    assert [(e[0], e[2], e[3]) for e in d.eventos] == [
        (10, TipoEvento.SIGRID, "ana"), (20, TipoEvento.SIGRID, "ana")]
    antes, despues = d.eventos[0][4], d.eventos[0][5]
    assert antes[1]["vinculados"] == despues[1]["vinculados"] == [{
        "vinculado_ide": 5000, "partida_ide": 81, "partida_cod": "CI.4",
        "partida_res": "TEL"}]
    assert [(x["obra_ide"], x["porcentaje"]) for x in despues] == [
        (678, "40.00"), (694, "95.00"), (713, "5.00")]
    assert despues[1]["partida_ide"] == 2105
    assert d.eventos[1][4] == []
    uow = _Uow(d)
    with uow, pytest.raises(DeshacerAjeno):
        DeshacerUltimaModificacion().ejecutar(uow, 2026, 9, 10, "bea",
                                              filtro=FILTRO)
    uow = _Uow(d)
    with uow:
        DeshacerUltimaModificacion().ejecutar(uow, 2026, 9, 10, "ana",
                                              filtro=FILTRO)
    lineas = {f["linea"].obra_ide: f["linea"] for f in d.filas[10]}
    assert set(lineas) == {694, 678}
    assert lineas[694].porcentaje == Decimal("60.00")
    assert lineas[694].partida_ide == 2000
    assert [(v.vinculado_ide, v.partida_ide)
            for v in lineas[694].vinculados] == [(5000, 81)]
    assert lineas[678].porcentaje == Decimal("40.00")
    assert [f["linea"].obra_ide for f in d.filas[20]] == [694]


def test_f054_d11_no_vigente_o_no_visible_no_se_trae():
    g = _Gateway([_s(960, 30, 694, 0.5), _s(961, 40, 694, 1.0)])
    r, uow, _ = _traer(_datos(), [_acepta(30, 694), _acepta(40, 694)], g)
    assert [(n.hmores_ide, n.motivo) for n in r.no_traidas] == [
        (960, "el trabajador no está vigente en 09/2026"),
        (961, "el trabajador no se ve en la empresa 1")]
    assert [m for _, m in r.rechazadas] == [MOTIVO_SIN_ENTRADA] * 2
    assert r.trabajadores == [] and uow.aceptadas == []


def test_f054_r14_de_vinculados_y_fuera_del_maestro_en_el_resultado():
    g = _Gateway([_s(970, 5000, 694, 1.0, hora="MESVE"),
                  _s(971, 8888, 694, 1.0)])
    r, _, _ = _traer(_datos(), gateway=g)
    assert (r.contadores.de_vinculados, r.contadores.fuera_maestro) == (1, 1)
    assert r.trabajadores == [] and r.no_traidas == []


def test_f054_r14_obra_en_la_base_sin_ofrecerse_y_obra_var():
    """Una obra fuera del listado del periodo pero en la base (inactiva y
    sin postventa) da «no se ofrece»; la entrada VAR va a `−var_paride`."""
    class _UowVar(_Uow):
        def __init__(self, d):
            super().__init__(d)
            var = _obra(-2105)
            self.obras.listar_para_periodo = lambda pid: [
                *OBRAS.values(), var]
            self.obras.existen = lambda ides: set(ides) & {694, 678, 713,
                                                           900, 555, -2105}

    g = _Gateway([_s(980, 20, 555, 0.3),
                  _s(981, 20, 777, 0.7, destino="var", var_paride=2105)])
    d = _datos()
    r, _, _ = _traer(d, [_acepta(20, -2105)], g, uow=_UowVar(d))
    assert [(n.hmores_ide, n.motivo) for n in r.no_traidas] == [
        (980, "la obra 555 no se ofrece normal")]
    [f] = d.filas[20]
    assert (f["linea"].obra_ide, f["linea"].porcentaje,
            f["linea"].partida_fija) == (-2105, Decimal("70.00"), True)


def test_f054_cerrado_entre_medias_409_y_nada_guardado():
    d = _datos()
    d.cerrar_al_aceptar = True
    antes = copy.deepcopy(d.__dict__)
    with pytest.raises(PeriodoCerrado):
        _traer(d, [_acepta(10, 694)])
    assert d.__dict__ == antes
