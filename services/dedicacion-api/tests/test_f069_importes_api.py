# tests/test_f069_importes_api.py
"""F-069 · T6: el esquema y el repositorio de las cantidades (R3, R9).

- `importe_vinculado` (nueva, por `create_all`): periodo × vinculado único,
  `cantidad` NOT NULL, `copiado` NOT NULL con defecto falso, comentario 200.
- `asignacion_vinculado` gana `cantidad`, `copiado`, `comentario` y
  `asignacion` su `comentario`: nulables, sin default, y el `ALTER … ADD
  COLUMN` lo deriva `esquema.alters_faltantes` sobre una base de antes.
- `_valores_subfila` guarda la fila con solo cantidad o comentario, y
  `reemplazar` lleva el comentario de la línea.
- `PgImporteRepository`: upsert sobre `uq_importe_vinculado`, borrado del
  vinculado, lecturas por trabajador y del periodo.

Sin red ni BBDD (sentencias compiladas y sesiones dobles).
"""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from domain.models import ImporteMes, Linea, SubfilaVinculado
from infrastructure.db import esquema
from infrastructure.db.orm_models import (
    AsignacionORM,
    AsignacionVinculadoORM,
    Base,
    ImporteVinculadoORM,
)
from infrastructure.db.repositories import (
    PgAsignacionRepository,
    PgImporteRepository,
    _valores_subfila,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable


def _ddl(tabla) -> list[str]:
    texto = str(CreateTable(tabla).compile(dialect=postgresql.dialect()))
    return [x.strip().rstrip(",") for x in texto.strip().splitlines()]


def _sql(stmt) -> str:
    return " ".join(str(stmt.compile(dialect=postgresql.dialect())).split())


# ================================ R3 ===================================== #
def test_f069_r3_ddl_de_importe_vinculado():
    assert _ddl(ImporteVinculadoORM.__table__) == [
        "CREATE TABLE importe_vinculado (", "id SERIAL NOT NULL",
        "periodo_id INTEGER NOT NULL", "vinculado_ide BIGINT NOT NULL",
        "cantidad NUMERIC(12, 2) NOT NULL",
        "copiado BOOLEAN DEFAULT false NOT NULL",
        "comentario VARCHAR(200)",
        "actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL",
        "actualizado_por TEXT NOT NULL",
        "PRIMARY KEY (id)",
        ("CONSTRAINT uq_importe_vinculado UNIQUE (periodo_id, "
         "vinculado_ide)"),
        "FOREIGN KEY(periodo_id) REFERENCES periodo (id) ON DELETE CASCADE",
        "FOREIGN KEY(vinculado_ide) REFERENCES recurso_vinculado (ide)", ")"]


def test_f069_r3_columnas_nuevas_nulables_sin_default():
    for tabla, nombre, tipo in (
            (AsignacionVinculadoORM, "cantidad", "NUMERIC(12, 2)"),
            (AsignacionVinculadoORM, "copiado", "BOOLEAN"),
            (AsignacionVinculadoORM, "comentario", "VARCHAR(200)"),
            (AsignacionORM, "comentario", "VARCHAR(200)")):
        col = tabla.__table__.columns[nombre]
        assert col.type.compile(dialect=postgresql.dialect()) == tipo
        assert col.nullable is True
        assert col.default is None and col.server_default is None


def test_f069_r3_esquema_deriva_los_alter_de_una_base_de_antes():
    existentes = {t.name: {c.name for c in t.columns}
                  for t in Base.metadata.tables.values()
                  if t.name != "importe_vinculado"}
    existentes["asignacion"] -= {"comentario"}
    existentes["asignacion_vinculado"] -= {"cantidad", "copiado",
                                           "comentario"}
    assert esquema.alters_faltantes(Base.metadata, existentes) == [
        "ALTER TABLE asignacion ADD COLUMN IF NOT EXISTS comentario "
        "VARCHAR(200)",
        "ALTER TABLE asignacion_vinculado ADD COLUMN IF NOT EXISTS cantidad "
        "NUMERIC(12, 2)",
        "ALTER TABLE asignacion_vinculado ADD COLUMN IF NOT EXISTS copiado "
        "BOOLEAN",
        "ALTER TABLE asignacion_vinculado ADD COLUMN IF NOT EXISTS "
        "comentario VARCHAR(200)"]


def test_f069_r3_la_subfila_con_solo_cantidad_o_comentario_tiene_fila():
    assert _valores_subfila(SubfilaVinculado(vinculado_ide=1)) == {}
    con = _valores_subfila(SubfilaVinculado(
        vinculado_ide=1, cantidad=Decimal("80"), copiado=True))
    assert (con["cantidad"], con["copiado"], con["comentario"]) == (
        Decimal("80"), True, None)
    assert _valores_subfila(SubfilaVinculado(
        vinculado_ide=1, comentario="x"))["comentario"] == "x"


class _Sesion:
    def __init__(self, filas=()) -> None:
        self.sentencias: list = []
        self.anadidos: list = []
        self.filas = list(filas)

    def execute(self, stmt):
        self.sentencias.append(stmt)
        return SimpleNamespace(all=lambda: list(self.filas), rowcount=1)

    def add(self, objeto):
        if getattr(objeto, "id", None) is None:
            objeto.id = len(self.anadidos) + 1
        self.anadidos.append(objeto)

    def flush(self):
        return None


def test_f069_r9_reemplazar_lleva_el_comentario_y_la_caja_de_la_subfila():
    s = _Sesion()
    ln = Linea(obra_ide=7, es_postventa=False, porcentaje=Decimal("60"),
               comentario="visita", vinculados=(SubfilaVinculado(
                   vinculado_ide=10, cantidad=Decimal("80"), copiado=False,
                   comentario="caja"),))
    PgAsignacionRepository(s).reemplazar(1, 5, [ln], "pgris")
    asig, sub = s.anadidos
    assert asig.comentario == "visita"
    assert (sub.vinculado_ide, sub.cantidad, sub.copiado, sub.comentario) == (
        10, Decimal("80"), False, "caja")


def test_f069_r3_guardar_es_un_upsert_sobre_la_pareja():
    s = _Sesion()
    PgImporteRepository(s).guardar(3, ImporteMes(
        vinculado_ide=20, cantidad=Decimal("100.00"), comentario="km"),
        "pgris")
    [stmt] = s.sentencias
    sql = _sql(stmt)
    assert sql.startswith("INSERT INTO importe_vinculado (periodo_id, "
                          "vinculado_ide, cantidad, copiado, comentario, "
                          "actualizado_por)")
    assert "ON CONFLICT ON CONSTRAINT uq_importe_vinculado DO UPDATE" in sql
    assert "actualizado_en = now()" in sql
    params = stmt.compile(dialect=postgresql.dialect()).params
    assert (params["periodo_id"], params["vinculado_ide"], params["cantidad"],
            params["copiado"], params["comentario"]) == (
        3, 20, Decimal("100.00"), False, "km")


def test_f069_r3_borrar_solo_el_del_vinculado_y_periodo():
    s = _Sesion()
    PgImporteRepository(s).borrar(3, 20)
    assert _sql(s.sentencias[0]) == (
        "DELETE FROM importe_vinculado WHERE importe_vinculado.periodo_id = "
        "%(periodo_id_1)s AND importe_vinculado.vinculado_ide = "
        "%(vinculado_ide_1)s")


def test_f069_r3_lecturas_por_trabajador_y_del_periodo():
    f = ImporteVinculadoORM(periodo_id=3, vinculado_ide=20,
                            cantidad=Decimal("12.5"), copiado=True,
                            comentario=None)
    s = _Sesion([(f, 5)])
    repo = PgImporteRepository(s)
    esperado = {20: ImporteMes(vinculado_ide=20, cantidad=Decimal("12.5"),
                               copiado=True)}
    assert repo.de_trabajador(3, 5) == esperado
    assert "recurso_vinculado.trabajador_ide = " in _sql(s.sentencias[0])
    assert repo.del_periodo(3) == {5: esperado}
    assert "importe_vinculado.periodo_id = " in _sql(s.sentencias[1])


# ===================== T7 · GuardarImportes (memoria) ===================== #
import dataclasses  # noqa: E402

import pytest  # noqa: E402
from application.use_cases import (  # noqa: E402
    DeshacerUltimaModificacion,
    GuardarAsignaciones,
    GuardarImportes,
)
from domain.errors import (  # noqa: E402
    ImporteInvalido,
    LineasInvalidas,
    PeriodoCerrado,
    PeriodoNoEncontrado,
)
from domain.importes import TipoCantidad  # noqa: E402
from domain.models import (  # noqa: E402
    EstadoPeriodo,
    EventoPendiente,
    FiltroEmpresa,
    Periodo,
)

from tests.test_f024_cuadrante_empresa import (  # noqa: E402
    ANIO,
    DEF,
    MES,
    P_ACT,
    _Asignaciones,
    _Eventos,
    _ln,
    _Uow,
)

TIPOS = {"CAJA": TipoCantidad("eur", "obra"), "VP": TipoCantidad("km", "pct"),
         "VIAJE": TipoCantidad("eur", "pct")}
FILTRO = FiltroEmpresa(empresa=DEF, por_defecto=DEF, empresa_obras=DEF)
CAJA = SubfilaVinculado(vinculado_ide=30, tipo="CAJA", cod="CJ-30")
VP = SubfilaVinculado(vinculado_ide=20, tipo="VP", cod="VP-20")
TEL = SubfilaVinculado(vinculado_ide=10, tipo="TF", cod="TF-10")
LARGO = "x" * 201


class _AsigMem(_Asignaciones):
    """`reemplazar` que guarda las líneas tal cual (con sus subfilas)."""

    def reemplazar(self, periodo_id, ide, lineas, usuario):
        self._uow.lineas.setdefault(periodo_id, {})[ide] = list(lineas)
        self._uow.reemplazados.append(ide)


class _ImportesMem:
    def __init__(self) -> None:
        self.filas: dict[int, ImporteMes] = {}
        self.escrituras: list[tuple] = []

    def de_trabajador(self, periodo_id, ide):
        return dict(self.filas)

    def del_periodo(self, periodo_id):
        return {10: dict(self.filas)} if self.filas else {}

    def guardar(self, periodo_id, importe, usuario):
        self.escrituras.append(("guardar", importe.vinculado_ide))
        self.filas[importe.vinculado_ide] = importe

    def borrar(self, periodo_id, vid):
        self.escrituras.append(("borrar", vid))
        self.filas.pop(vid, None)


class _EventosTipo(_Eventos):
    def __init__(self) -> None:
        super().__init__()
        self.registrados: list[tuple] = []

    def registrar(self, periodo_id, ide, tipo, usuario, antes, despues):
        self.registrados.append((tipo.value, antes, despues))
        self.eventos.append((ide, EventoPendiente(
            len(self.eventos) + 1, usuario, antes, tipo=tipo.value)))


def _uow_imp(*subfilas: SubfilaVinculado) -> _Uow:
    lineas = [dataclasses.replace(_ln(100, "60"), vinculados=subfilas),
              dataclasses.replace(_ln(900, "40"), vinculados=subfilas)]
    uow = _Uow({P_ACT: {10: lineas}})
    uow.asignaciones = _AsigMem(uow)
    uow.importes = _ImportesMem()
    uow.eventos = _EventosTipo()
    return uow


def _guardar(uow, *importes, tipos=TIPOS):
    return GuardarImportes(tipos).ejecutar(
        uow, ANIO, MES, 10, list(importes), "pgris", filtro=FILTRO)


def _subfila(uow, obra, vid=30):
    [ln] = [x for x in uow.lineas[P_ACT][10] if x.obra_ide == obra]
    return next(v for v in ln.vinculados if v.vinculado_ide == vid)


def test_f069_r4_por_pct_se_guarda_sin_copiado_y_deja_evento():
    uow = _uow_imp(VP, CAJA)
    fila, _ = _guardar(uow, {"vinculado_ide": 20, "cantidad": "100",
                             "comentario": " visita "})
    assert uow.importes.filas[20] == ImporteMes(
        vinculado_ide=20, cantidad=Decimal("100.00"), copiado=False,
        comentario="visita")
    [(tipo, antes, despues)] = uow.eventos.registrados
    assert (tipo, antes) == ("IMPORTES", [])
    assert despues == [{"vinculado_ide": 20, "obra_ide": None,
                        "es_postventa": False, "cantidad": "100.00",
                        "copiado": False, "comentario": "visita"}]
    assert uow.reemplazados == []              # los % no se tocan
    assert [i.vinculado_ide for i in fila.importes] == [20]


def test_f069_r4_por_obra_en_la_subfila_de_esa_linea():
    uow = _uow_imp(VP, CAJA)
    _guardar(uow, {"vinculado_ide": 30, "obra_ide": 100, "cantidad": 80})
    assert (_subfila(uow, 100).cantidad, _subfila(uow, 100).copiado) == (
        Decimal("80.00"), False)
    assert _subfila(uow, 900).cantidad is None
    assert uow.importes.filas == {}
    [(_, _, despues)] = uow.eventos.registrados
    assert despues[0]["obra_ide"] == 100


def test_f069_r4_null_borra_y_lo_que_no_viene_no_se_toca():
    uow = _uow_imp(VP, CAJA)
    _guardar(uow, {"vinculado_ide": 20, "cantidad": 5},
             {"vinculado_ide": 30, "obra_ide": 100, "cantidad": 80,
              "comentario": "caja"},
             {"vinculado_ide": 30, "obra_ide": 900, "cantidad": 7})
    _guardar(uow, {"vinculado_ide": 20, "cantidad": None},
             {"vinculado_ide": 30, "obra_ide": 100, "cantidad": None,
              "comentario": "caja"})
    assert 20 not in uow.importes.filas
    assert (_subfila(uow, 100).cantidad, _subfila(uow, 100).comentario) == (
        None, "caja")
    assert _subfila(uow, 900).cantidad == Decimal("7.00")


def test_f069_r4_una_cantidad_tecleada_quita_el_copiado():
    uow = _uow_imp(VP)
    uow.importes.filas[20] = ImporteMes(vinculado_ide=20,
                                        cantidad=Decimal("100.00"),
                                        copiado=True)
    _guardar(uow, {"vinculado_ide": 20, "cantidad": 100})
    assert uow.importes.filas[20].copiado is False
    assert len(uow.eventos.registrados) == 1


@pytest.mark.parametrize("malo", [
    {"vinculado_ide": 20, "cantidad": -1},
    {"vinculado_ide": 20, "cantidad": "1,5"},
    {"vinculado_ide": 20, "cantidad": 100000},          # km: tope 99.999,99
    {"vinculado_ide": 20, "cantidad": 1, "comentario": LARGO},
    {"vinculado_ide": 10, "cantidad": 1},               # TF: no es de cantidad
    {"vinculado_ide": 99, "cantidad": 1},               # no es suyo
    {"vinculado_ide": "20", "cantidad": 1},
    {"vinculado_ide": True, "cantidad": 1},
    {"vinculado_ide": 30, "cantidad": 1},               # caja sin obra
    {"vinculado_ide": 30, "obra_ide": 101, "cantidad": 1},   # sin línea ahí
    {"vinculado_ide": 30, "obra_ide": 100, "es_postventa": True,
     "cantidad": 1},
    {"vinculado_ide": 30, "obra_ide": 100, "es_postventa": "no",
     "cantidad": 1},
])
def test_f069_r5_r6_lo_que_no_vale_es_422_sin_guardar_nada(malo):
    uow = _uow_imp(VP, CAJA, TEL)
    with pytest.raises(ImporteInvalido):
        _guardar(uow, {"vinculado_ide": 20, "cantidad": 3}, malo)
    assert uow.importes.escrituras == [] and uow.reemplazados == []
    assert uow.eventos.registrados == []


def test_f069_r6_repetido_es_422():
    uow = _uow_imp(VP, CAJA)
    with pytest.raises(ImporteInvalido, match="repetido"):
        _guardar(uow, {"vinculado_ide": 20, "cantidad": 1},
                 {"vinculado_ide": 20, "cantidad": 2})
    with pytest.raises(ImporteInvalido, match="repetido"):
        _guardar(uow, {"vinculado_ide": 30, "obra_ide": 100, "cantidad": 1},
                 {"vinculado_ide": 30, "obra_ide": 100, "cantidad": 2})


def test_f069_r6_sin_tipos_de_cantidad_nada_es_de_cantidad():
    with pytest.raises(ImporteInvalido):
        _guardar(_uow_imp(VP), {"vinculado_ide": 20, "cantidad": 1}, tipos={})


def test_f069_r6_periodo_inexistente_y_cerrado():
    uow = _uow_imp(VP)
    with pytest.raises(PeriodoNoEncontrado):
        GuardarImportes(TIPOS).ejecutar(uow, ANIO, MES + 1, 10, [], "pgris",
                                        filtro=FILTRO)
    uow.periodos.obtener = lambda a, m: (P_ACT, Periodo(
        a, m, estado=EstadoPeriodo.CERRADO))
    with pytest.raises(PeriodoCerrado):
        _guardar(uow, {"vinculado_ide": 20, "cantidad": 1})


def test_f069_r7_sin_cambios_ni_escribe_ni_deja_evento():
    uow = _uow_imp(VP, CAJA)
    _guardar(uow, {"vinculado_ide": 20, "cantidad": 5},
             {"vinculado_ide": 30, "obra_ide": 100, "cantidad": 8})
    uow.importes.escrituras.clear()
    uow.reemplazados.clear()
    _guardar(uow, {"vinculado_ide": 20, "cantidad": "5.00"},
             {"vinculado_ide": 30, "obra_ide": 100, "cantidad": 8.0})
    _guardar(uow)
    assert uow.importes.escrituras == [] and uow.reemplazados == []
    assert len(uow.eventos.registrados) == 1


def test_f069_r7_deshacer_vuelve_a_la_foto_de_antes():
    uow = _uow_imp(VP, CAJA)
    _guardar(uow, {"vinculado_ide": 20, "cantidad": 5},
             {"vinculado_ide": 30, "obra_ide": 100, "cantidad": 8})
    _guardar(uow, {"vinculado_ide": 20, "cantidad": 6, "comentario": "b"},
             {"vinculado_ide": 30, "obra_ide": 100, "cantidad": None},
             {"vinculado_ide": 30, "obra_ide": 900, "cantidad": 9})
    pct = [ln.porcentaje for ln in uow.lineas[P_ACT][10]]
    DeshacerUltimaModificacion().ejecutar(uow, ANIO, MES, 10, "pgris",
                                          filtro=FILTRO)
    assert uow.importes.filas[20].cantidad == Decimal("5.00")
    assert uow.importes.filas[20].comentario is None
    assert _subfila(uow, 100).cantidad == Decimal("8.00")
    assert _subfila(uow, 900).cantidad is None
    assert [ln.porcentaje for ln in uow.lineas[P_ACT][10]] == pct
    DeshacerUltimaModificacion().ejecutar(uow, ANIO, MES, 10, "pgris",
                                          filtro=FILTRO)
    assert uow.importes.filas == {}
    assert _subfila(uow, 100).cantidad is None


# ===================== R9 · el comentario del titular ===================== #
def _guardar_lineas(uow, *lineas):
    return GuardarAsignaciones().ejecutar(uow, ANIO, MES, 10, list(lineas),
                                          "pgris", filtro=FILTRO)


def test_f069_r9_el_comentario_se_guarda_y_entra_en_el_evento():
    uow = _uow_imp(CAJA)
    _guardar_lineas(uow, {"obra_ide": 100, "porcentaje": "60",
                          "comentario": "  mes con visita "},
                    {"obra_ide": 900, "porcentaje": "40"})
    assert [ln.comentario for ln in uow.lineas[P_ACT][10]] == [
        "mes con visita", None]
    [(tipo, _, despues)] = uow.eventos.registrados
    assert tipo == "GUARDAR"
    assert despues[0]["comentario"] == "mes con visita"
    assert "comentario" not in despues[1]


def test_f069_r9_sin_la_clave_se_conserva_y_con_null_se_borra():
    uow = _uow_imp(CAJA)
    _guardar_lineas(uow, {"obra_ide": 100, "porcentaje": "60",
                          "comentario": "a"},
                    {"obra_ide": 900, "porcentaje": "40"})
    _guardar_lineas(uow, {"obra_ide": 100, "porcentaje": "50"},
                    {"obra_ide": 900, "porcentaje": "50"})
    assert uow.lineas[P_ACT][10][0].comentario == "a"
    _guardar_lineas(uow, {"obra_ide": 100, "porcentaje": "50",
                          "comentario": None},
                    {"obra_ide": 900, "porcentaje": "50"})
    assert uow.lineas[P_ACT][10][0].comentario is None


def test_f069_r9_comentario_de_mas_de_200_es_422():
    with pytest.raises(LineasInvalidas):
        _guardar_lineas(_uow_imp(), {"obra_ide": 100, "porcentaje": "100",
                                     "comentario": LARGO})


def test_f069_r9_guardar_la_fila_conserva_la_caja_y_deshacer_la_devuelve():
    uow = _uow_imp(CAJA)
    _guardar(uow, {"vinculado_ide": 30, "obra_ide": 100, "cantidad": 80,
                   "comentario": "caja"})
    _guardar_lineas(uow, {"obra_ide": 100, "porcentaje": "70"},
                    {"obra_ide": 900, "porcentaje": "30"})
    assert (_subfila(uow, 100).cantidad, _subfila(uow, 100).comentario) == (
        Decimal("80.00"), "caja")
    _, antes, _ = uow.eventos.registrados[-1]
    assert antes[0]["vinculados"] == [{
        "vinculado_ide": 30, "partida_ide": None, "partida_cod": None,
        "partida_res": None, "cantidad": "80.00", "copiado": False,
        "comentario": "caja"}]


# ===================== R4-R6, R10 · la ruta PUT …/importes ================ #
from config.settings import Settings  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from interface_adapters.api.app import build_app  # noqa: E402
from interface_adapters.api.deps import obtener_contenedor  # noqa: E402

from tests.test_f024_rutas_empresa import (  # noqa: E402
    _Contenedor,
    _PropuestasFalsas,
)

RUTA = f"/api/v1/periodos/{ANIO}/{MES}/trabajadores/10/importes"


class _UowCMImp(_Uow):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None


@pytest.fixture
def api_imp(monkeypatch):
    monkeypatch.delenv("EMPRESA_IMPUTACION", raising=False)
    settings = Settings(_env_file=None)
    base = _uow_imp(VP, CAJA, TEL)
    uow = _UowCMImp(base.lineas)
    uow.asignaciones = _AsigMem(uow)
    uow.importes = _ImportesMem()
    uow.eventos = _EventosTipo()
    contenedor = _Contenedor(settings=settings, uow=lambda: uow,
                             propuestas_mes=_PropuestasFalsas(),
                             importes=TIPOS)
    app = build_app(settings)
    app.dependency_overrides[obtener_contenedor] = lambda: contenedor
    return TestClient(app), uow


def test_f069_r4_r10_put_importes_responde_la_fila(api_imp):
    cliente, uow = api_imp
    r = cliente.put(RUTA, json={"importes": [
        {"vinculado_ide": 20, "cantidad": 100, "comentario": "visita"},
        {"vinculado_ide": 30, "obra_ide": 100, "cantidad": "80.5"}]})
    assert r.status_code == 200, r.text
    t = r.json()["trabajador"]
    assert t["importes"] == [{
        "vinculado_ide": 20, "tipo": "VP", "cod": "VP-20", "unidad": "km",
        "cantidad": 100.0, "copiado": False, "comentario": "visita"}]
    vp, caja, tel = t["lineas"][0]["vinculados"]
    assert (vp["reparto"], vp["unidad"]) == ("pct", "km")
    assert "cantidad" not in vp                 # la del mes va en `importes`
    assert (caja["reparto"], caja["unidad"], caja["cantidad"],
            caja["copiado"]) == ("obra", "eur", 80.5, False)
    assert "comentario" not in caja
    assert not {"reparto", "unidad", "cantidad"} & set(tel)   # F-044 tal cual
    caja900 = t["lineas"][1]["vinculados"][1]
    assert caja900["reparto"] == "obra"          # sin cantidad: sin la clave
    assert not {"cantidad", "copiado"} & set(caja900)


@pytest.mark.parametrize("cuerpo, codigo", [
    ({"importes": [{"vinculado_ide": 20, "cantidad": -3}]}, 422),
    ({"importes": [{"vinculado_ide": 10, "cantidad": 3}]}, 422),
    ({"importes": [{"vinculado_ide": 20, "cantidad": 3, "otra": 1}]}, 422),
    ({}, 422),
])
def test_f069_r5_r6_put_importes_errores(api_imp, cuerpo, codigo):
    cliente, uow = api_imp
    r = cliente.put(RUTA, json=cuerpo)
    assert r.status_code == codigo, r.text
    assert uow.importes.escrituras == []


def test_f069_r6_put_importes_periodo_inexistente_404(api_imp):
    cliente, _ = api_imp
    r = cliente.put(RUTA.replace(f"/{MES}/", f"/{MES + 1}/"),
                    json={"importes": []})
    assert r.status_code == 404, r.text


def test_f069_r9_put_asignaciones_con_y_sin_comentario(api_imp):
    cliente, uow = api_imp
    ruta = RUTA.replace("/importes", "/asignaciones")
    r = cliente.put(ruta, json={"lineas": [
        {"obra_ide": 100, "porcentaje": 60, "comentario": "visita"},
        {"obra_ide": 900, "porcentaje": 40}]})
    assert r.status_code == 200, r.text
    lineas = r.json()["trabajador"]["lineas"]
    assert lineas[0]["comentario"] == "visita"
    assert "comentario" not in lineas[1]
    r = cliente.put(ruta, json={"lineas": [
        {"obra_ide": 100, "porcentaje": 50},
        {"obra_ide": 900, "porcentaje": 50}]})
    assert r.json()["trabajador"]["lineas"][0]["comentario"] == "visita"
