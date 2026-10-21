# tests/test_f030_r30_identidad.py
"""F-030 · Anexo R30 en la api: la incidencia conserva su identidad.

Cambiar los días de una ya registrada no es otra incidencia: el PUT manda su
`id` (R36, R37), la fila y su traza se conservan, la que se quita estando
registrada queda `quitada` (R38, D11), la traza guarda por rol el `ide` y el
día de Sigrid (R39) y deshacer repone `id` y traza (R47).

Offline: metadatos del ORM, dobles en memoria de la sesión y de la unidad de
trabajo. Ni red, ni BBDD, ni `.env`.
"""
from __future__ import annotations

import dataclasses

import pytest
from domain.models import Incidencia


# ============================ esquema (T23) ============================= #
def test_f030_r30_esquema_alters_anade_las_tres_columnas_de_incidencia():
    """Sobre una base con la tabla de T1-T19, `alters_faltantes` emite los
    tres `ADD COLUMN` (R38, R39) y nada para `asignacion` ni otra tabla."""
    from infrastructure.db.esquema import alters_faltantes
    from infrastructure.db.orm_models import Base

    al_dia = {t.name: {c.name for c in t.columns}
              for t in Base.metadata.tables.values()}
    vieja = dict(al_dia)
    vieja["incidencia"] = al_dia["incidencia"] - {
        "quitada", "sigrid_dia_ini", "sigrid_dia_fin"}
    assert alters_faltantes(Base.metadata, vieja) == [
        ("ALTER TABLE incidencia ADD COLUMN IF NOT EXISTS "
         "quitada BOOLEAN DEFAULT false NOT NULL"),
        "ALTER TABLE incidencia ADD COLUMN IF NOT EXISTS sigrid_dia_ini SMALLINT",
        "ALTER TABLE incidencia ADD COLUMN IF NOT EXISTS sigrid_dia_fin SMALLINT"]
    assert alters_faltantes(Base.metadata, al_dia) == []


def test_f030_r30_esquema_quitada_por_defecto_falsa_en_python_y_servidor():
    from infrastructure.db.orm_models import IncidenciaORM

    col = IncidenciaORM.__table__.columns["quitada"]
    assert (col.nullable, col.default.arg) == (False, False)
    for nombre in ("sigrid_dia_ini", "sigrid_dia_fin"):
        c = IncidenciaORM.__table__.columns[nombre]
        assert (c.nullable, c.default, c.server_default) == (True, None, None)


def test_f030_r30_esquema_modelo_de_dominio_con_identidad_y_traza():
    inc = Incidencia(obra_ide=100, codigo="CIV", dia_desde=5, dia_hasta=9)
    assert (inc.quitada, inc.sigrid_ide_ini, inc.sigrid_ide_fin,
            inc.sigrid_dia_ini, inc.sigrid_dia_fin) == (False, None, None,
                                                        None, None)
    with pytest.raises(dataclasses.FrozenInstanceError):
        inc.quitada = True  # type: ignore[misc]


def test_f030_r30_esquema_entrada_con_id_opcional_y_salida_con_quitada():
    from interface_adapters.api.schemas import (
        IncidenciaIn,
        IncidenciasIn,
        a_incidencia_out,
    )
    from pydantic import ValidationError

    assert IncidenciaIn(obra_ide=1, codigo="CIV").id is None
    cuerpo = IncidenciasIn.model_validate({"incidencias": [
        {"id": 7, "obra_ide": 1, "codigo": "CIV", "dia_desde": 6,
         "dia_hasta": 9}]})
    assert cuerpo.incidencias[0].id == 7
    with pytest.raises(ValidationError):
        IncidenciaIn.model_validate({"obra_ide": 1, "codigo": "CIV",
                                     "quitada": True})   # la decide la api
    inc = Incidencia(obra_ide=1, codigo="CIV", dia_desde=5, dia_hasta=9,
                     id=7, quitada=True, sigrid_ide_ini=9001)
    out = a_incidencia_out(inc).model_dump()
    assert (out["id"], out["quitada"]) == (7, True)
    assert "sigrid_ide_ini" not in out          # la traza no viaja al front
    assert a_incidencia_out(dataclasses.replace(inc, quitada=False)
                            ).quitada is False


def test_f030_r30_esquema_el_repo_mapea_quitada_e_ides_y_dias_de_sigrid():
    from infrastructure.db.orm_models import IncidenciaORM
    from infrastructure.db.repositories import _a_incidencia

    orm = IncidenciaORM(id=7, periodo_id=3, trabajador_ide=14, obra_ide=100,
                        codigo="CIV", dia_desde=6, dia_hasta=9, quitada=True,
                        sigrid_ide_ini=9001, sigrid_ide_fin=9002,
                        sigrid_dia_ini=5, sigrid_dia_fin=9,
                        sigrid_estado="registrado")
    inc = _a_incidencia(orm, "0100", "OBRA 100", "V", "Vacaciones")
    assert (inc.id, inc.quitada, inc.sigrid_ide_ini, inc.sigrid_ide_fin,
            inc.sigrid_dia_ini, inc.sigrid_dia_fin) == (7, True, 9001, 9002,
                                                        5, 9)
    orm.quitada = None                  # fila aún sin `flush`: no es quitada
    assert _a_incidencia(orm, "0100", "OBRA", "V", "V").quitada is False


# ================= guardar con `id` y quitadas (T24) ==================== #
from tests.test_f030_incidencias import (
    P_ACT,
    USUARIO,
    _e,
    _guardar,
    _orm_inc,
    _SesionReemplazo,
    _uow_guardar,
)


def _reg(id_: int, desde: int, hasta: int, obra: int = 100, cod: str = "CIV",
         ini: int | None = 9001, fin: int | None = 9002, **kw) -> Incidencia:
    """Una incidencia ya guardada; con `ini`/`fin`, registrada (R36)."""
    traza = bool(ini or fin)
    return Incidencia(obra_ide=obra, codigo=cod, dia_desde=desde,
                      dia_hasta=hasta, id=id_,
                      sigrid_estado="registrado" if traza else None,
                      sigrid_parte_cod="PT26/1" if traza else None,
                      sigrid_ide_ini=ini, sigrid_ide_fin=fin,
                      sigrid_dia_ini=desde if ini else None,
                      sigrid_dia_fin=hasta if fin else None, **kw)


def _con_id(id_: int, **kw) -> dict:
    return {"id": id_, **_e(**kw)}


def _snap(id_, obra, cod, desde, hasta, quitada=False) -> dict:
    return {"id": id_, "obra_ide": obra, "codigo": cod, "dia_desde": desde,
            "dia_hasta": hasta, "quitada": quitada}


def _traza(inc: Incidencia) -> tuple:
    return (inc.sigrid_estado, inc.sigrid_parte_cod, inc.sigrid_ide_ini,
            inc.sigrid_ide_fin, inc.sigrid_dia_ini, inc.sigrid_dia_fin)


def test_f030_r36_guardar_con_id_conserva_fila_id_y_traza():
    uow = _uow_guardar()
    uow.incidencias.poner(14, _reg(7, 5, 9))
    fila, _ = _guardar(uow, [_con_id(7, desde=6, hasta=9)])
    [inc] = fila.incidencias
    assert (inc.id, inc.dia_desde, inc.dia_hasta, inc.quitada) == (7, 6, 9, False)
    assert _traza(inc) == ("registrado", "PT26/1", 9001, 9002, 5, 9)
    [(_, evento, despues)] = uow.eventos.eventos
    assert evento.snapshot_antes == [_snap(7, 100, "CIV", 5, 9)]
    assert despues == [_snap(7, 100, "CIV", 6, 9)]


def test_f030_r36_guardar_sin_id_es_nueva():
    uow = _uow_guardar()
    uow.incidencias.poner(14, _reg(7, 5, 9, ini=None, fin=None))
    fila, _ = _guardar(uow, [_e(100, "CIV", 5, 9)])
    [inc] = fila.incidencias
    assert inc.id not in (None, 7)
    [(_, evento, despues)] = uow.eventos.eventos
    assert evento.snapshot_antes == [_snap(7, 100, "CIV", 5, 9)]
    assert despues == [_snap(inc.id, 100, "CIV", 5, 9)]


def test_f030_r36_guardar_lo_mismo_con_su_id_no_escribe():
    uow = _uow_guardar()
    uow.incidencias.poner(14, _reg(7, 5, 9), _reg(8, 12, 12, cod="CIP",
                                                   ini=None, fin=None))
    _guardar(uow, [_con_id(8, codigo="CIP", desde=12, hasta=12),
                   _con_id(7, desde=5, hasta=9)])
    assert uow.incidencias.reemplazos == [] and uow.eventos.eventos == []


@pytest.mark.parametrize("entrada, motivo", [
    ([_con_id(99, desde=5, hasta=9)], "99 no es"),          # no existe
    ([_con_id(3, desde=5, hasta=9)], "3 no es"),            # de otro trabajador
    ([_con_id(7, desde=5, hasta=6),
      _con_id(7, desde=8, hasta=9)], "repetida"),
    ([{**_e(100, "CIV", 5, 9), "id": "7"}], "inválida"),
    ([{**_e(100, "CIV", 5, 9), "id": True}], "inválida"),
    ([_con_id(7, obra=101, desde=5, hasta=9)], "registrada"),     # D13
    ([_con_id(7, codigo="CIE", desde=5, hasta=9)], "registrada"),  # D12
])
def test_f030_r36_guardar_id_ajeno_o_registrada_cambiada_422(entrada, motivo):
    from domain.errors import IncidenciaInvalida

    uow = _uow_guardar()
    uow.incidencias.poner(14, _reg(7, 5, 9))
    uow.incidencias.poner(10, _reg(3, 1, 2, ini=None, fin=None))
    with pytest.raises(IncidenciaInvalida, match=motivo):
        _guardar(uow, entrada)
    assert uow.incidencias.reemplazos == [] and uow.eventos.eventos == []
    assert uow.commits == 0


def test_f030_r36_guardar_no_registrada_si_cambia_de_obra_o_codigo():
    uow = _uow_guardar()
    uow.incidencias.poner(14, _reg(7, 5, 9, ini=None, fin=None))
    fila, _ = _guardar(uow, [_con_id(7, obra=101, codigo="CIE", desde=5,
                                     hasta=9)])
    assert [(i.id, i.obra_ide, i.codigo) for i in fila.incidencias] == [
        (7, 101, "CIE")]


@pytest.mark.parametrize("ini, fin", [(9001, 9002), (9001, None), (None, 9002)])
def test_f030_r38_guardar_registrada_ausente_queda_quitada(ini, fin):
    uow = _uow_guardar()
    uow.incidencias.poner(14, _reg(7, 5, 9, ini=ini, fin=fin),
                          _reg(8, 12, 12, cod="CIP", ini=None, fin=None))
    fila, _ = _guardar(uow, [])
    [inc] = fila.incidencias                     # la 8, borrada
    assert (inc.id, inc.quitada, inc.sigrid_ide_ini, inc.sigrid_ide_fin) == (
        7, True, ini, fin)
    [(_, evento, despues)] = uow.eventos.eventos
    assert evento.snapshot_antes == [_snap(7, 100, "CIV", 5, 9),
                                     _snap(8, 100, "CIP", 12, 12)]
    assert despues == [_snap(7, 100, "CIV", 5, 9, quitada=True)]


def test_f030_r38_guardar_las_quitadas_no_cuentan_en_los_solapes():
    uow = _uow_guardar()
    uow.incidencias.poner(14, _reg(7, 5, 9, quitada=True))
    fila, _ = _guardar(uow, [_e(101, "CIE", 5, 9)])
    assert sorted((i.codigo, i.quitada) for i in fila.incidencias) == [
        ("CIE", False), ("CIV", True)]
    # Otra vez ausente: sigue quitada y no hay nada que escribir.
    uow = _uow_guardar()
    uow.incidencias.poner(14, _reg(7, 5, 9, quitada=True))
    _guardar(uow, [])
    assert uow.incidencias.reemplazos == [] and uow.eventos.eventos == []


def test_f030_r38_guardar_volver_a_mandar_la_quitada_la_repone():
    uow = _uow_guardar()
    uow.incidencias.poner(14, _reg(7, 5, 9, quitada=True))
    fila, _ = _guardar(uow, [_con_id(7, desde=5, hasta=9)])
    [inc] = fila.incidencias
    assert (inc.id, inc.quitada, inc.sigrid_ide_ini) == (7, False, 9001)


def test_f030_r36_r38_repo_reemplazar_por_id_quita_o_borra():
    from infrastructure.db.repositories import PgIncidenciaRepository

    cambia = _orm_inc(3, 14, 100, "CIV", 5, 9, sigrid_ide_ini=9001,
                      sigrid_ide_fin=9002, sigrid_dia_ini=5, sigrid_dia_fin=9,
                      sigrid_estado="registrado", quitada=True,
                      actualizado_por="previo")
    igual = _orm_inc(4, 14, 100, "CIP", 12, 12, actualizado_por="previo",
                     quitada=False)
    borrar = _orm_inc(5, 14, 101, "CIE", 20, 22, quitada=False)
    queda = _orm_inc(6, 14, 101, "CIE", 25, 26, sigrid_ide_fin=9010,
                     quitada=False, actualizado_por="previo")
    ya_quitada = _orm_inc(8, 14, 101, "CIE", 27, 27, sigrid_ide_ini=9011,
                          quitada=True, actualizado_por="previo")
    sesion = _SesionReemplazo([cambia, igual, borrar, queda, ya_quitada])
    PgIncidenciaRepository(sesion).reemplazar(  # type: ignore[arg-type]
        P_ACT, 14, [_reg(3, 6, 12, ini=None, fin=None),
                    _reg(4, 12, 12, cod="CIP", ini=None, fin=None),
                    _reg(4, 13, 13, cod="CIP", ini=None, fin=None),   # repetida
                    _reg(99, 14, 14, cod="CIP", ini=None, fin=None),  # no está
                    Incidencia(obra_ide=100, codigo="CIA", dia_desde=1,
                               dia_hasta=2)], USUARIO)
    # Con `id`: obra, código y días nuevos; repuesta; la traza, intacta.
    assert (cambia.id, cambia.dia_desde, cambia.dia_hasta, cambia.quitada,
            cambia.actualizado_por) == (3, 6, 12, False, USUARIO)
    assert (cambia.sigrid_ide_ini, cambia.sigrid_ide_fin, cambia.sigrid_dia_ini,
            cambia.sigrid_dia_fin, cambia.sigrid_estado) == (
        9001, 9002, 5, 9, "registrado")
    assert (igual.dia_desde, igual.actualizado_por) == (12, "previo")
    # Ausentes: la no registrada se borra; la registrada queda quitada.
    assert sesion.borradas == [borrar]
    assert (queda.quitada, queda.actualizado_por, queda.sigrid_ide_fin) == (
        True, USUARIO, 9010)
    assert (ya_quitada.quitada, ya_quitada.actualizado_por) == (True, "previo")
    # Sin `id`, con uno repetido o con uno que no está: nuevas.
    assert [(o.id, o.codigo, o.dia_desde, o.quitada, o.actualizado_por,
             o.sigrid_ide_ini) for o in sesion.anadidas] == [
        (None, "CIP", 13, False, USUARIO, None),
        (None, "CIP", 14, False, USUARIO, None),
        (None, "CIA", 1, False, USUARIO, None)]
    assert sesion.flushes == 1


# ============================ deshacer (T25) ============================ #
def _deshacer(uow, ide=14):
    from tests.test_f030_incidencias import _deshacer as deshacer

    return deshacer(uow, ide=ide)


def _estado(fila) -> list[tuple]:
    return [(i.id, i.dia_desde, i.dia_hasta, i.quitada, i.sigrid_ide_ini,
             i.sigrid_ide_fin) for i in fila.incidencias]


def test_f030_r47_deshacer_un_cambio_de_dias_repone_id_y_traza():
    uow = _uow_guardar()
    uow.incidencias.poner(14, _reg(7, 5, 9))
    _guardar(uow, [_con_id(7, desde=12, hasta=14)])
    fila, _ = _deshacer(uow)
    assert _estado(fila) == [(7, 5, 9, False, 9001, 9002)]
    assert _traza(fila.incidencias[0]) == ("registrado", "PT26/1", 9001, 9002,
                                           5, 9)


def test_f030_r47_deshacer_quitar_la_repone():
    uow = _uow_guardar()
    uow.incidencias.poner(14, _reg(7, 5, 9))
    _guardar(uow, [])
    fila, _ = _deshacer(uow)
    assert _estado(fila) == [(7, 5, 9, False, 9001, 9002)]


def test_f030_r47_deshacer_reponer_una_quitada_la_vuelve_a_quitar():
    uow = _uow_guardar()
    uow.incidencias.poner(14, _reg(7, 5, 9, quitada=True))
    _guardar(uow, [_con_id(7, desde=5, hasta=9)])
    fila, _ = _deshacer(uow)
    assert _estado(fila) == [(7, 5, 9, True, 9001, 9002)]


def test_f030_r47_deshacer_lo_que_quitaria_una_registrada_la_deja_quitada():
    """Alta, el registro le pone traza y luego se deshace el alta: no se
    borra (sigue en Sigrid), queda quitada."""
    uow = _uow_guardar()
    fila, _ = _guardar(uow, [_e(100, "CIV", 5, 9)])
    [nueva] = fila.incidencias
    uow.incidencias.poner(14, _reg(nueva.id, 5, 9))       # la traza (R39)
    fila, _ = _deshacer(uow)
    assert _estado(fila) == [(nueva.id, 5, 9, True, 9001, 9002)]


def test_f030_r47_deshacer_snapshot_sin_id_son_nuevas():
    """Un evento de antes del anexo (sin `id`): lo suyo vuelve como nuevo y
    la no registrada de ahora se borra."""
    from domain.models import TipoEvento

    uow = _uow_guardar()
    uow.incidencias.poner(14, _reg(7, 12, 14, ini=None, fin=None))
    uow.eventos.registrar(P_ACT, 14, TipoEvento.INCIDENCIAS, USUARIO, [
        {"obra_ide": 100, "codigo": "CIV", "dia_desde": 5, "dia_hasta": 9}],
        [])
    fila, _ = _deshacer(uow)
    [inc] = fila.incidencias
    assert (inc.id not in (None, 7), inc.dia_desde, inc.dia_hasta,
            inc.quitada) == (True, 5, 9, False)


# ===================== registro y traza (T26) =========================== #
from tests.test_f024_registro_empresa import _fila, _Transfer
from tests.test_f030_registro import _inc as _inc_reg
from tests.test_f030_registro import _registro, _Sesion, _trazas


def _inc_traza(inc_id, trab, obra, codigo="CIV", desde=5, hasta=9, *,
               ini=None, fin=None, dia_ini=None, dia_fin=None, quitada=False,
               parte=None):
    i, t, o = _inc_reg(inc_id, trab, obra, codigo, desde, hasta)
    i.sigrid_ide_ini, i.sigrid_ide_fin = ini, fin
    i.sigrid_dia_ini, i.sigrid_dia_fin = dia_ini, dia_fin
    i.quitada, i.sigrid_parte_cod = quitada, parte
    return i, t, o


class _SesionTipos(_Sesion):
    """Como la de `test_f030_registro`, y la lectura del catálogo devuelve
    (código, letra)."""

    def execute(self, sentencia):
        if "FROM tipo_incidencia" in str(sentencia):
            self._anotado["selects"].append(str(sentencia))
            return _Resultado_([("CIV", "V"), ("CIE", "B")])
        return super().execute(sentencia)


class _Resultado_:
    def __init__(self, filas):
        self._filas = filas

    def all(self):
        return list(self._filas)


def _registro_tipos(transfer, filas=(), incidencias=(), anotado=None):
    from application.registro_sigrid import RegistroSigrid

    anotado = anotado if anotado is not None else {"updates": [],
                                                   "selects": []}
    return RegistroSigrid(
        lambda: _SesionTipos(list(filas), list(incidencias), anotado),
        transfer, 1)


def test_f030_r39_registro_la_registrada_viaja_con_su_traza():
    transfer = _Transfer()
    incs = [_inc_traza(7, (10, 1), (678, 1), desde=6, ini=9001, fin=9002,
                       dia_ini=5, dia_fin=9),
            _inc_traza(8, (11, 1), (678, 1), ini=None, fin=9010, dia_fin=9),
            _inc_traza(9, (12, 1), (678, 1))]                  # sin registrar
    _registro(transfer, [], incs).preflight(2026, 7)
    i7, i8, i9 = transfer.payloads[0]["incidencias"]
    assert i7 == {"id": 7, "recurso_ide": 10, "empresa": 1, "codigo": "CIV",
                  "ano": 2026, "mes": 7, "desde": 6, "hasta": 9, "paride": 0,
                  "hmores_ide_ini": 9001, "hmores_ide_fin": 9002,
                  "dia_ini": 5, "dia_fin": 9}
    assert (i8["hmores_ide_ini"], i8["hmores_ide_fin"], i8["dia_ini"],
            i8["dia_fin"]) == (None, 9010, None, 9)
    # Sin traza, la petición de siempre (sin las cuatro claves).
    assert set(i9) == {"id", "recurso_ide", "empresa", "codigo", "ano", "mes",
                       "desde", "hasta", "paride"}


@pytest.mark.parametrize("fase", ["preflight", "ejecutar"])
def test_f030_r38_registro_las_quitadas_no_van_al_transfer(fase):
    transfer = _Transfer()
    incs = [_inc_traza(7, (10, 1), (678, 1), ini=9001, fin=9002, quitada=True),
            _inc_traza(8, (10, 1), (694, 1), ini=9003, fin=9004, quitada=True),
            _inc_traza(9, (11, 1), (694, 1))]
    reg = _registro_tipos(transfer, [_fila(1, (10, 1), (678, 1))], incs)
    r = (reg.preflight(2026, 7) if fase == "preflight"
         else reg.ejecutar(2026, 7, pisar_claves=[]))
    p678, p694 = transfer.payloads
    assert "incidencias" not in p678              # solo tenía la quitada
    assert [i["id"] for i in p694["incidencias"]] == [9]
    if fase == "ejecutar":
        assert "incidencias_quitadas" not in r


def test_f030_r38_registro_el_preflight_lista_las_quitadas():
    transfer = _Transfer()
    anotado = {"updates": [], "selects": []}
    incs = [_inc_traza(7, (10, 1), (678, 1), ini=9001, fin=9002, quitada=True,
                       parte="PT26/00251"),
            _inc_traza(8, (11, 1), (694, 1), codigo="CIE", desde=1, hasta=3,
                       ini=None, fin=9004, quitada=True, parte="PT26/00252"),
            _inc_traza(9, (11, 1), (694, 1)),
            _inc_traza(6, (12, 28), (678, 1), ini=1, quitada=True)]  # no visible
    reg = _registro_tipos(transfer, [], incs, anotado)
    r = reg.preflight(2026, 7, empresa=1)
    assert r["incidencias_quitadas"] == [
        {"id": 7, "trabajador_ide": 10, "trabajador": "T10", "obra_ide": 678,
         "obra_cod": "0678", "obra_nombre": "OBRA", "codigo": "CIV",
         "letra": "V", "desde": 5, "hasta": 9, "parte_cod": "PT26/00251",
         "hmores_ide_ini": 9001, "hmores_ide_fin": 9002},
        {"id": 8, "trabajador_ide": 11, "trabajador": "T11", "obra_ide": 694,
         "obra_cod": "0694", "obra_nombre": "OBRA", "codigo": "CIE",
         "letra": "B", "desde": 1, "hasta": 3, "parte_cod": "PT26/00252",
         "hmores_ide_ini": None, "hmores_ide_fin": 9004}]
    [tipos] = [s for s in anotado["selects"] if "FROM tipo_incidencia" in s]
    assert "tipo_incidencia.codigo IN" in " ".join(tipos.split())
    # La de una obra: solo sus quitadas. Sin quitadas, ni la clave ni la
    # lectura del catálogo.
    r = _registro_tipos(_Transfer(), [], incs).preflight(2026, 7, empresa=1,
                                                         obra_ide=694)
    assert [q["id"] for q in r["incidencias_quitadas"]] == [8]
    anotado = {"updates": [], "selects": []}
    r = _registro_tipos(_Transfer(), [], incs[2:3], anotado).preflight(2026, 7)
    assert "incidencias_quitadas" not in r
    assert not [s for s in anotado["selects"] if "tipo_incidencia" in s]


def test_f030_r38_registro_letra_sin_catalogo():
    incs = [_inc_traza(7, (10, 1), (678, 1), codigo="CIQ", ini=1,
                       quitada=True)]
    r = _registro_tipos(_Transfer(), [], incs).preflight(2026, 7)
    assert r["incidencias_quitadas"][0]["letra"] == "Q"


def _resp(*acciones):
    return {"ok": True, "escritas": [], "omitidas": [], "ya_registradas": [],
            "incidencias": [
                {"id": i, "rol": rol, "accion": acc, "fecha_int": fec,
                 "hora_codigo": "CIV", "paride": 0, "parte_cod": parte,
                 "hmores_ide": ide, "motivo": motivo}
                for i, rol, acc, fec, parte, ide, motivo in acciones]}


def _ejecutar_traza(*acciones):
    anotado = {"updates": [], "selects": []}
    _registro(_Transfer(_resp(*acciones)), [_fila(1, (10, 1), (678, 1))], [],
              anotado).ejecutar(2026, 7, pisar_claves=[], usuario="ana")
    return _trazas(anotado), anotado["wheres"]


def test_f030_r39_traza_escrita_guarda_ide_y_dia_por_rol():
    [t7], _ = _ejecutar_traza(
        (7, "ini", "escribir", 20260705, "PT26/1", 9001, None),
        (7, "fin", "escribir", 20260709, "PT26/1", 9002, None))
    assert (t7["sigrid_estado"], t7["sigrid_ide_ini"], t7["sigrid_dia_ini"],
            t7["sigrid_ide_fin"], t7["sigrid_dia_fin"],
            t7["sigrid_registrado_by"]) == ("registrado", 9001, 5, 9002, 9,
                                            "ana")


def test_f030_r39_traza_editada_y_ya_registrada():
    [t7], _ = _ejecutar_traza(
        (7, "ini", "editar", 20260712, "PT26/1", 9001, None),
        (7, "fin", "ya_registrado", 20260709, "PT26/1", 9002, "ya está"))
    assert (t7["sigrid_ide_ini"], t7["sigrid_dia_ini"], t7["sigrid_ide_fin"],
            t7["sigrid_dia_fin"], t7["sigrid_motivo"]) == (9001, 12, 9002, 9,
                                                           None)
    assert t7["sigrid_registrado_by"] == "ana"      # editar también escribe
    [t8], _ = _ejecutar_traza(
        (8, "ini", "ya_registrado", 20260705, "PT26/1", 9001, None),
        (8, "fin", "ya_registrado", 20260709, "PT26/1", 9002, None))
    assert "sigrid_registrado_by" not in t8 and t8["sigrid_dia_fin"] == 9


def test_f030_r39_traza_un_omitir_no_borra_el_ide_de_su_rol():
    [t7], _ = _ejecutar_traza(
        (7, "ini", "editar", 20260706, "PT26/1", 9001, None),
        (7, "fin", "omitir", 20260712, "PT26/1", None, "cambiada en Sigrid"))
    assert (t7["sigrid_ide_ini"], t7["sigrid_dia_ini"], t7["sigrid_motivo"]) \
        == (9001, 6, "cambiada en Sigrid")
    assert "sigrid_ide_fin" not in t7 and "sigrid_dia_fin" not in t7


def test_f030_r39_traza_todo_omitido_solo_degrada_la_no_registrada():
    (motivo, estado), wheres = _ejecutar_traza(
        (7, "ini", "omitir", 20260706, None, None, "el parte X está cerrado"),
        (7, "fin", "omitir", 20260712, None, None, "el parte X está cerrado"))
    assert motivo == {"id_1": 7, "sigrid_motivo": "el parte X está cerrado"}
    assert estado == {"id_1": 7, "sigrid_estado": "omitido"}
    assert wheres[-2:] == [
        "incidencia.id = :id_1",
        ("incidencia.id = :id_1 AND incidencia.sigrid_ide_ini IS NULL "
         "AND incidencia.sigrid_ide_fin IS NULL")]


def test_f030_r39_traza_docstring_explica_el_import_de_orm():
    """Obs. 5 de la review: el import del ORM en `application/` se queda
    (precedente `registro_sigrid.py`) y su docstring lo dice."""
    from application import traza_incidencias

    assert "registro_sigrid.py" in traza_incidencias.__doc__
    assert "importa el ORM" in traza_incidencias.__doc__


# ================= huecos de la 4.ª campaña de mutación ================= #
def test_f030_r36_registrada_con_cualquiera_de_sus_dos_lineas():
    """Una sola línea con `ide` en la traza basta (la otra se omitió o la
    borraron): la incidencia está registrada."""
    from domain.incidencias import registrada

    assert registrada(_reg(7, 5, 9, ini=9001, fin=None)) is True
    assert registrada(_reg(7, 5, 9, ini=None, fin=9002)) is True
    assert registrada(_reg(7, 5, 9, ini=9001, fin=9002)) is True
    assert registrada(_reg(7, 5, 9, ini=None, fin=None)) is False


def test_f030_r47_snapshot_iguales_salvo_el_id_por_id_y_la_nueva_primero():
    """El orden del evento no depende del de entrada: con todo igual, la
    nueva (sin `id`) va primero y las demás por su `id`."""
    from application.use_cases import _snapshot_incidencias

    base = Incidencia(obra_ide=100, codigo="CIV", dia_desde=5, dia_hasta=9)
    incs = [dataclasses.replace(base, id=2), dataclasses.replace(base, id=1),
            dataclasses.replace(base, id=None)]
    assert [s["id"] for s in _snapshot_incidencias(incs)] == [None, 1, 2]
    assert [s["id"] for s in _snapshot_incidencias(incs[::-1])] == [None, 1, 2]


def test_f030_r38_salida_sin_quitada_es_no_quitada():
    from interface_adapters.api.schemas import IncidenciaOut

    out = IncidenciaOut(id=7, obra_ide=1, obra_cod="0001", obra_descripcion="Una",
                        codigo="CIV", letra="V", nombre="Vacaciones",
                        dia_desde=5, dia_hasta=9, sigrid_estado=None,
                        sigrid_parte_cod=None, sigrid_motivo=None)
    assert out.quitada is False
