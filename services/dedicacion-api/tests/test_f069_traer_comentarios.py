# tests/test_f069_traer_comentarios.py
"""F-069 · T15 y T21: al traer de Sigrid, el comentario de nuestras líneas
ya registradas es el `tex` que publica el transfer, tal cual (R32, D15): el
transfer ya le quitó la marca de pruebas (D17); la api no la conoce.

- Titular por `sigrid_hmores_ide` o por su `synckey` (`porcentajes:{id}`);
  vinculado por la suya (`porcentajes:vin:{id}:{recurso}`) o su traza.
- Solo si difiere; las líneas a mano ajenas (sin traza ni `synckey`
  nuestra) no se tocan; % y cantidades, tampoco.
- Un evento `SIGRID` por trabajador (con el de lo aceptado, si lo hay); las
  cantidades del mes (vinculados por %), con su evento `IMPORTES` (D21), que
  se deshace solo.
- Una aceptada ahora trae el `tex` de su línea de menor `ide`.

UoW en memoria (la de los tests de F-054): sin red ni BBDD.
"""
from __future__ import annotations

import copy
import dataclasses
from decimal import Decimal
from types import SimpleNamespace

from application.traer_sigrid import TraerDeSigrid
from domain.importes import TipoCantidad
from domain.models import (
    ImporteMes,
    ResultadoExistentes,
    SubfilaVinculado,
    VinculadoRegistrado,
)
from infrastructure.db.repositories import PgAsignacionRepository
from sqlalchemy.dialects import postgresql

from tests.test_f054_aceptar import FILTRO, _Asig, _Datos, _ln, _s, _Uow

TIPOS = {"VP": TipoCantidad("km", "pct"), "CAJA": TipoCantidad("eur", "obra")}
VP = SubfilaVinculado(vinculado_ide=5020, tipo="VP", cod="VP")
CAJA = SubfilaVinculado(vinculado_ide=5030, tipo="CAJA", cod="CJ")


class _AsigCom(_Asig):
    def registradas(self, pid):
        return [(t, f["linea"].clave(), f["id"],
                 (f.get("traza") or {}).get("sigrid_hmores_ide"))
                for t, fs in self.d.filas.items() for f in fs]

    def _cambiar(self, ide, clave, fn):
        for f in self.d.filas.get(ide, []):
            if f["linea"].clave() == clave:
                f["linea"] = fn(f["linea"])

    def poner_comentario(self, pid, ide, clave, comentario):
        self.uow.sueltas.append(("linea", ide, clave, comentario))
        self._cambiar(ide, clave, lambda ln: dataclasses.replace(
            ln, comentario=comentario))

    def guardar_subfila_importe(self, pid, ide, clave, vid, valores):
        self.uow.sueltas.append(("subfila", ide, clave, vid, dict(valores)))
        self._cambiar(ide, clave, lambda ln: dataclasses.replace(
            ln, vinculados=tuple(dataclasses.replace(v, **valores)
                                 if v.vinculado_ide == vid else v
                                 for v in ln.vinculados)))


class _ImportesMes:
    def __init__(self, filas: dict[int, ImporteMes]) -> None:
        self.filas = filas
        self.guardados: list[ImporteMes] = []

    def de_trabajador(self, pid, ide):
        return dict(self.filas) if ide == 10 else {}

    def del_periodo(self, pid):
        return {10: dict(self.filas)}

    def guardar(self, pid, importe, usuario):
        self.guardados.append(importe)
        self.filas[importe.vinculado_ide] = importe


class _Gw:
    def __init__(self, lineas=(), vinculados=()) -> None:
        self.r = ResultadoExistentes(lineas=tuple(lineas),
                                     vinculados_registrados=tuple(vinculados))

    def porcentajes_existentes(self, *a):
        return self.r


def _uow(lineas_traza, mes=None):
    datos = _Datos({})
    datos.filas = {10: [datos.fila(ln, traza) for ln, traza in lineas_traza]}
    uow = _Uow(datos)
    uow.asignaciones = _AsigCom(uow)
    uow.sueltas = []
    uow.importes = _ImportesMes(dict(mes or {}))
    return uow


def _traer(uow, gw, aceptar=()):
    with uow:
        r = TraerDeSigrid(gw, TIPOS).ejecutar(
            uow, 2026, 9, "ana", filtro=FILTRO, aceptar=list(aceptar))
        filas = copy.deepcopy(uow.d.filas)
    return r, filas


def _eventos(uow):
    return [(e[2].value, e[4], e[5]) for e in uow.guardado.eventos]


def test_f069_r32_titular_por_hmores_y_un_evento():
    uow = _uow([(_ln(694, "100"), {"sigrid_hmores_ide": 901})])
    _, filas = _traer(uow, _Gw([_s(901, 10, 694, 1.0,
                                   tex=" mes con visita ")]))
    assert filas[10][0]["linea"].comentario == "mes con visita"
    assert filas[10][0]["traza"] == {"sigrid_hmores_ide": 901}   # sin tocar
    [(tipo, antes, despues)] = _eventos(uow)
    assert tipo == "SIGRID"
    assert "comentario" not in antes[0]
    assert despues[0]["comentario"] == "mes con visita"
    assert despues[0]["porcentaje"] == antes[0]["porcentaje"]


def test_f069_r32_titular_por_su_synckey():
    uow = _uow([(_ln(694, "100"), None)])
    _traer(uow, _Gw([_s(905, 10, 694, 1.0, synckey="porcentajes:1",
                        tex="b"),
                     _s(904, 10, 694, 1.0, synckey="porcentajes:1",
                        tex="a")]))
    assert uow.sueltas == [("linea", 10, (694, False), "a")]   # el de menor ide


def test_f069_r32_solo_si_difiere_y_las_ajenas_no():
    con = dataclasses.replace(_ln(694, "60"), comentario="igual")
    uow = _uow([(con, {"sigrid_hmores_ide": 901}),
                (_ln(713, "40"), None)])
    _, filas = _traer(uow, _Gw([_s(901, 10, 694, 0.6, tex="igual"),
                                _s(902, 10, 713, 0.4, tex="a mano",
                                   synckey="partes:7")]))
    assert uow.sueltas == [] and _eventos(uow) == []
    assert filas[10][1]["linea"].comentario is None


def test_f069_r32_un_tex_vacio_borra_el_de_la_app():
    con = dataclasses.replace(_ln(694, "100"), comentario="viejo")
    uow = _uow([(con, {"sigrid_hmores_ide": 901})])
    _traer(uow, _Gw([_s(901, 10, 694, 1.0, tex=None)]))
    assert uow.sueltas == [("linea", 10, (694, False), None)]


def test_f069_r32_la_api_no_quita_ninguna_marca():
    """D17: un `tex` «PRUEBA-PORC x» (el transfer ya quitó SU marca: lo que
    queda es texto) se guarda tal cual, en línea, subfila y mes."""
    mes = {5020: ImporteMes(vinculado_ide=5020, cantidad=Decimal("100"))}
    caja = dataclasses.replace(CAJA, cantidad=Decimal("80"))
    uow = _uow([(_ln(694, "100", vinculados=(VP, caja)),
                 {"sigrid_hmores_ide": 901})], mes)
    _, filas = _traer(uow, _Gw(
        [_s(901, 10, 694, 1.0, tex="PRUEBA-PORC x")],
        [VinculadoRegistrado(7002, 5030, "porcentajes:vin:1:5030",
                             "PRUEBA-PORC caja"),
         VinculadoRegistrado(7003, 5020, "porcentajes:vin:1:5020",
                             "PRUEBA-PORC km")]))
    ln = filas[10][0]["linea"]
    assert ln.comentario == "PRUEBA-PORC x"
    assert ln.vinculados[1].comentario == "PRUEBA-PORC caja"
    assert [g.comentario for g in uow.importes.guardados] == [
        "PRUEBA-PORC km"]


def test_f069_r32_d21_sigrid_e_importes_y_deshacer_el_de_importes():
    """D21: titular y caja en el evento `SIGRID`; la cantidad del mes, en
    uno `IMPORTES` propio, el último: deshacerlo repone el comentario del
    mes y no toca el del titular."""
    from application.use_cases import DeshacerUltimaModificacion
    from domain.models import TipoEvento

    from tests.test_f054_aceptar import FILTRO as F

    mes = {5020: ImporteMes(vinculado_ide=5020, cantidad=Decimal("100"),
                            comentario="viejo")}
    uow = _uow([(_ln(694, "100", vinculados=(VP,)),
                 {"sigrid_hmores_ide": 901})], mes)
    _traer(uow, _Gw([_s(901, 10, 694, 1.0, tex="titular")],
                    [VinculadoRegistrado(7003, 5020,
                                         "porcentajes:vin:1:5020", "km")]))
    assert [t for t, _, _ in _eventos(uow)] == ["SIGRID", "IMPORTES"]
    assert uow.importes.filas[5020].comentario == "km"
    uow.importes.borrar = lambda pid, vid: uow.importes.filas.pop(vid)
    with uow:
        DeshacerUltimaModificacion().ejecutar(uow, 2026, 9, 10, "ana",
                                              filtro=F)
    assert uow.importes.filas[5020].comentario == "viejo"
    assert uow.importes.filas[5020].cantidad == Decimal("100")
    assert uow.guardado.filas[10][0]["linea"].comentario == "titular"
    assert uow.guardado.eventos[-1][2] is TipoEvento.IMPORTES


def test_f069_r32_vinculado_de_linea_y_por_obra_en_su_subfila():
    caja = dataclasses.replace(CAJA, cantidad=Decimal("80"), copiado=False)
    tel = SubfilaVinculado(vinculado_ide=5000, tipo="TF",
                           sigrid_hmores_ide=7001)
    uow = _uow([(_ln(694, "100", vinculados=(tel, caja)), None)])
    _, filas = _traer(uow, _Gw(vinculados=[
        VinculadoRegistrado(7001, 5000, "porcentajes:vin:1:5000", "tel"),
        VinculadoRegistrado(7002, 5030, "porcentajes:vin:1:5030",
                            "caja de obra")]))
    tel2, caja2 = filas[10][0]["linea"].vinculados
    assert (tel2.comentario, caja2.comentario) == ("tel", "caja de obra")
    assert caja2.cantidad == Decimal("80")           # no toca cantidades
    assert [x[0] for x in uow.sueltas] == ["subfila", "subfila"]
    assert [t for t, _, _ in _eventos(uow)] == ["SIGRID"]


def test_f069_r32_por_pct_a_su_cantidad_del_mes_con_su_evento():
    mes = {5020: ImporteMes(vinculado_ide=5020, cantidad=Decimal("100"))}
    uow = _uow([(_ln(694, "60", vinculados=(VP,)), None),
                (_ln(713, "40", vinculados=(VP,)), None)], mes)
    _traer(uow, _Gw(vinculados=[
        VinculadoRegistrado(7004, 5020, "porcentajes:vin:2:5020", "segunda"),
        VinculadoRegistrado(7003, 5020, "porcentajes:vin:1:5020", "visita")]))
    [guardado] = uow.importes.guardados
    assert (guardado.comentario, guardado.cantidad) == ("visita",
                                                       Decimal("100"))
    [(tipo, antes, despues)] = _eventos(uow)
    assert tipo == "IMPORTES"
    assert (antes[0]["comentario"], despues[0]["comentario"]) == (
        None, "visita")
    assert uow.sueltas == []


def test_f069_r32_por_pct_sin_cantidad_guardada_no_se_escribe():
    uow = _uow([(_ln(694, "100", vinculados=(VP,)), None)])
    _traer(uow, _Gw(vinculados=[
        VinculadoRegistrado(7003, 5020, "porcentajes:vin:1:5020", "x")]))
    assert uow.importes.guardados == [] and _eventos(uow) == []


def test_f069_r32_una_aceptada_trae_el_tex_de_su_linea_de_menor_ide():
    uow = _uow([])
    uow.guardado.filas = {}
    _, filas = _traer(uow, _Gw([_s(912, 10, 694, 0.5, tex="segunda"),
                                _s(911, 10, 694, 0.5, tex="primera")]),
                      aceptar=[{"trabajador_ide": 10, "obra_ide": 694,
                                "es_postventa": False}])
    [f] = filas[10]
    assert f["linea"].comentario == "primera"
    [(tipo, _, despues)] = _eventos(uow)
    assert tipo == "SIGRID" and despues[0]["comentario"] == "primera"


# ======================= el repositorio (SQL) ============================= #
def _sql(stmt) -> str:
    return " ".join(str(stmt.compile(dialect=postgresql.dialect())).split())


class _S:
    def __init__(self, filas=()):
        self.st = []
        self.filas = list(filas)

    def execute(self, stmt):
        self.st.append(stmt)
        return SimpleNamespace(all=lambda: list(self.filas), rowcount=1)


def test_f069_r32_repositorio_poner_comentario_y_subfila_sin_reemplazar():
    s = _S()
    repo = PgAsignacionRepository(s)
    repo.poner_comentario(3, 10, (694, False), "x")
    assert _sql(s.st[0]).startswith(
        "UPDATE asignacion SET comentario=%(comentario)s WHERE "
        "asignacion.periodo_id = ")
    repo.guardar_subfila_importe(3, 10, (694, False), 5030,
                                 {"comentario": "c"})
    sql = _sql(s.st[1])
    assert sql.startswith("INSERT INTO asignacion_vinculado (asignacion_id, "
                          "vinculado_ide, comentario) SELECT asignacion.id")
    assert "ON CONFLICT (asignacion_id, vinculado_ide) DO UPDATE SET " \
           "comentario = excluded.comentario" in sql


def test_f069_r32_repositorio_registradas():
    s = _S([(10, 694, False, 1, 901), (10, 713, True, 2, None)])
    assert PgAsignacionRepository(s).registradas(3) == [
        (10, (694, False), 1, 901), (10, (713, True), 2, None)]
    assert "asignacion.sigrid_hmores_ide" in _sql(s.st[0])


# ===================== R31 · el cliente del transfer ====================== #
from tests.test_f054_rutas import LINEA, RESPUESTA, _cliente  # noqa: E402


def test_f069_r31_el_cliente_lee_tex_y_vinculados_registrados(monkeypatch):
    cli, _ = _cliente(monkeypatch, {**RESPUESTA, "lineas": [
        {**LINEA, "tex": "visita"}], "vinculados_registrados": [
        {"hmores_ide": "7001", "recurso_ide": 5000,
         "synckey": "porcentajes:vin:1:5000", "tex": None}]})
    r = cli.porcentajes_existentes(1, 2026, 9, [])
    assert r.lineas[0].tex == "visita"
    assert r.vinculados_registrados == (VinculadoRegistrado(
        7001, 5000, "porcentajes:vin:1:5000", None),)
    cli, _ = _cliente(monkeypatch, RESPUESTA)          # transfer de antes
    assert cli.porcentajes_existentes(1, 2026, 9, []).vinculados_registrados \
        == ()
