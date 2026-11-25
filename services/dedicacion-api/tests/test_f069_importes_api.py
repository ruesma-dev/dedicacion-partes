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
        "cantidad NUMERIC(12, 2)",           # D19: nulable
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
    """`reemplazar` que guarda las líneas tal cual (con sus subfilas) y las
    escrituras sueltas de subfila y comentario, anotadas."""

    def reemplazar(self, periodo_id, ide, lineas, usuario):
        self._uow.lineas.setdefault(periodo_id, {})[ide] = list(lineas)
        self._uow.reemplazados.append(ide)

    def _cambiar(self, periodo_id, ide, clave, fn):
        self._uow.lineas[periodo_id][ide] = [
            fn(ln) if ln.clave() == clave else ln
            for ln in self._uow.lineas[periodo_id][ide]]

    def guardar_subfila_importe(self, periodo_id, ide, clave, vid, valores):
        self.sueltas.append(("subfila", clave, vid, dict(valores)))
        self._cambiar(periodo_id, ide, clave, lambda ln: dataclasses.replace(
            ln, vinculados=tuple(dataclasses.replace(v, **valores)
                                 if v.vinculado_ide == vid else v
                                 for v in ln.vinculados)))

    def poner_comentario(self, periodo_id, ide, clave, comentario):
        self.sueltas.append(("comentario", clave, comentario))
        self._cambiar(periodo_id, ide, clave, lambda ln: dataclasses.replace(
            ln, comentario=comentario))

    @property
    def sueltas(self):
        return self._uow.__dict__.setdefault("sueltas", [])


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
    """D18: teclear OTRA cantidad o «Revisado» (`revisado: true`) quita el
    `copiado`; mandar la misma, no (la api no distingue teclearla igual)."""
    uow = _uow_imp(VP)
    uow.importes.filas[20] = ImporteMes(vinculado_ide=20,
                                        cantidad=Decimal("100.00"),
                                        copiado=True)
    _guardar(uow, {"vinculado_ide": 20, "cantidad": 100})
    assert uow.importes.filas[20].copiado is True
    assert uow.eventos.registrados == []
    _guardar(uow, {"vinculado_ide": 20, "cantidad": 100, "revisado": True})
    assert uow.importes.filas[20].copiado is False
    assert len(uow.eventos.registrados) == 1
    uow.importes.filas[20] = dataclasses.replace(uow.importes.filas[20],
                                                 copiado=True)
    _guardar(uow, {"vinculado_ide": 20, "cantidad": 101})
    assert uow.importes.filas[20].copiado is False


def _dos_copiadas():
    caja = dataclasses.replace(CAJA, cantidad=Decimal("80.00"), copiado=True)
    uow = _uow_imp(VP, caja)
    uow.importes.filas[20] = ImporteMes(vinculado_ide=20,
                                        cantidad=Decimal("100.00"),
                                        copiado=True)
    return uow


def test_f069_r4_d18_solo_el_comentario_no_revisa_ninguna():
    """D18 (2026-11-19, «No cuenta»): dos copiadas en el mismo `PUT`; el
    comentario de una cambia y las dos siguen `copiado`."""
    uow = _dos_copiadas()
    _guardar(uow, {"vinculado_ide": 20, "cantidad": 100,
                   "comentario": "visita"},
             {"vinculado_ide": 30, "obra_ide": 100, "cantidad": 80})
    assert (uow.importes.filas[20].copiado,
            uow.importes.filas[20].comentario) == (True, "visita")
    assert _subfila(uow, 100).copiado is True
    [(_, _, despues)] = uow.eventos.registrados
    # La del mes y la caja de las dos líneas (100 y 900), todas copiadas.
    assert [b["copiado"] for b in despues] == [True, True, True]


def test_f069_r4_d18_revisado_en_una_solo_quita_esa():
    uow = _dos_copiadas()
    _guardar(uow, {"vinculado_ide": 20, "cantidad": 100, "revisado": True},
             {"vinculado_ide": 30, "obra_ide": 100, "cantidad": 80,
              "revisado": False})
    assert uow.importes.filas[20].copiado is False
    assert _subfila(uow, 100).copiado is True
    uow = _dos_copiadas()
    _guardar(uow, {"vinculado_ide": 30, "obra_ide": 100, "cantidad": 80,
                   "revisado": True})
    assert (uow.importes.filas[20].copiado, _subfila(uow, 100).copiado) == (
        True, False)


def test_f069_r4_d19_comentario_sin_cantidad_se_guarda_tambien_por_pct():
    """D19 («Guardarlo igual»): km `null` con comentario ⇒ fila sin cantidad
    y con el comentario; sin los dos ⇒ sin fila."""
    uow = _uow_imp(VP, CAJA)
    _guardar(uow, {"vinculado_ide": 20, "cantidad": None,
                   "comentario": "visita a proveedor"})
    assert uow.importes.filas[20] == ImporteMes(
        vinculado_ide=20, cantidad=None, copiado=False,
        comentario="visita a proveedor")
    [(_, _, despues)] = uow.eventos.registrados
    assert despues == [{"vinculado_ide": 20, "obra_ide": None,
                        "es_postventa": False, "cantidad": None,
                        "copiado": False, "comentario": "visita a proveedor"}]
    _guardar(uow, {"vinculado_ide": 20, "cantidad": 100,
                   "comentario": "visita a proveedor"})
    assert uow.importes.filas[20].cantidad == Decimal("100.00")
    _guardar(uow, {"vinculado_ide": 20, "cantidad": None,
                   "comentario": None})
    assert 20 not in uow.importes.filas
    assert uow.importes.escrituras[-1] == ("borrar", 20)


def test_f069_r4_d19_deshacer_vuelve_al_comentario_sin_cantidad():
    uow = _uow_imp(VP)
    _guardar(uow, {"vinculado_ide": 20, "comentario": "solo comentario"})
    _guardar(uow, {"vinculado_ide": 20, "cantidad": 5,
                   "comentario": "solo comentario"})
    DeshacerUltimaModificacion().ejecutar(uow, ANIO, MES, 10, "pgris",
                                          filtro=FILTRO)
    assert uow.importes.filas[20] == ImporteMes(
        vinculado_ide=20, cantidad=None, copiado=False,
        comentario="solo comentario")


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
    # D18 (R5): `revisado`, booleano (el 20 ya va el primero: la caja).
    {"vinculado_ide": 30, "obra_ide": 900, "cantidad": 1, "revisado": "si"},
    {"vinculado_ide": 30, "obra_ide": 100, "cantidad": 1, "revisado": 1},
    {"vinculado_ide": 30, "obra_ide": 100, "cantidad": 1, "revisado": "true"},
])
def test_f069_r5_r6_lo_que_no_vale_es_422_sin_guardar_nada(malo):
    uow = _uow_imp(VP, CAJA, TEL)
    with pytest.raises(ImporteInvalido):
        _guardar(uow, {"vinculado_ide": 20, "cantidad": 3}, malo)
    assert uow.importes.escrituras == [] and uow.reemplazados == []
    assert uow.asignaciones.sueltas == [] and uow.eventos.registrados == []


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
    uow.asignaciones.sueltas.clear()
    _guardar(uow, {"vinculado_ide": 20, "cantidad": "5.00"},
             {"vinculado_ide": 30, "obra_ide": 100, "cantidad": 8.0})
    _guardar(uow)
    assert uow.importes.escrituras == [] and uow.reemplazados == []
    assert uow.asignaciones.sueltas == []
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
    ({"importes": [{"vinculado_ide": 20, "cantidad": 3,
                    "revisado": "si"}]}, 422),
    ({}, 422),
])
def test_f069_r5_r6_put_importes_errores(api_imp, cuerpo, codigo):
    cliente, uow = api_imp
    r = cliente.put(RUTA, json=cuerpo)
    assert r.status_code == codigo, r.text
    assert uow.importes.escrituras == []


def test_f069_r4_put_importes_con_revisado(api_imp):
    """D18: la ruta acepta `revisado` (el esquema lo declara) y lo pasa."""
    cliente, uow = api_imp
    uow.importes.filas[20] = ImporteMes(vinculado_ide=20,
                                        cantidad=Decimal("100.00"),
                                        copiado=True)
    r = cliente.put(RUTA, json={"importes": [
        {"vinculado_ide": 20, "cantidad": 100, "revisado": True}]})
    assert r.status_code == 200, r.text
    assert r.json()["trabajador"]["importes"][0]["copiado"] is False


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


# ===================== T8 · R8 · copiar el mes ============================ #
from application.use_cases import (  # noqa: E402
    CopiarPeriodoAnterior,
    CopiarTrabajadorAnterior,
)

from tests.test_f024_cuadrante_empresa import P_ANT  # noqa: E402


class _ImportesPorPeriodo:
    def __init__(self, filas=None) -> None:
        self.filas: dict[int, dict[int, ImporteMes]] = filas or {}
        self.escrituras: list[tuple] = []

    def de_trabajador(self, periodo_id, ide):
        return dict(self.filas.get(periodo_id, {}))

    def del_periodo(self, periodo_id):
        return {10: self.de_trabajador(periodo_id, 10)}

    def guardar(self, periodo_id, importe, usuario):
        self.escrituras.append((periodo_id, importe.vinculado_ide))
        self.filas.setdefault(periodo_id, {})[importe.vinculado_ide] = importe

    def borrar(self, periodo_id, vid):
        self.escrituras.append((periodo_id, "borrar", vid))
        self.filas.get(periodo_id, {}).pop(vid, None)


def _uow_copia(destino_mes=None, origen_mes=None):
    caja = dataclasses.replace(CAJA, cantidad=Decimal("80.00"), copiado=False,
                               comentario="caja")
    previas = [dataclasses.replace(_ln(100, "60"), comentario="visita",
                                   vinculados=(VP, caja)),
               dataclasses.replace(_ln(101, "40"), vinculados=(VP, CAJA))]
    uow = _Uow({P_ACT: {}, P_ANT: {10: previas}})
    uow.asignaciones = _AsigMem(uow)
    uow.eventos = _EventosTipo()
    uow.importes = _ImportesPorPeriodo({
        P_ANT: origen_mes if origen_mes is not None else {
            20: ImporteMes(vinculado_ide=20, cantidad=Decimal("100.00"),
                           comentario="km"),
            77: ImporteMes(vinculado_ide=77, cantidad=Decimal("1.00"))},
        P_ACT: destino_mes or {}})
    return uow


def _copiar_trabajador(uow):
    return CopiarTrabajadorAnterior().ejecutar(uow, ANIO, MES, 10, "pgris",
                                               filtro=FILTRO)


@pytest.mark.parametrize("copiar", [
    _copiar_trabajador,
    lambda uow: CopiarPeriodoAnterior().ejecutar(uow, ANIO, MES, "pgris",
                                                 filtro=FILTRO)])
def test_f069_r8_copia_cantidades_y_comentarios_con_copiado(copiar):
    uow = _uow_copia()
    copiar(uow)
    lineas = uow.lineas[P_ACT][10]
    assert lineas[0].comentario == "visita"
    caja = _subfila(uow, 100)
    assert (caja.cantidad, caja.copiado, caja.comentario) == (
        Decimal("80.00"), True, "caja")
    assert _subfila(uow, 101).copiado is None
    # Solo las de sus vinculados (el 77 ya no es suyo), con `copiado`.
    assert uow.importes.filas[P_ACT] == {20: ImporteMes(
        vinculado_ide=20, cantidad=Decimal("100.00"), copiado=True,
        comentario="km")}
    assert [t for t, _, _ in uow.eventos.registrados] == ["COPIA", "IMPORTES"]
    _, antes, despues = uow.eventos.registrados[1]
    assert [b["obra_ide"] for b in antes] == [100]
    assert [(b["vinculado_ide"], b["copiado"]) for b in despues] == [
        (20, True), (30, True)]


def test_f069_r8_nunca_pisa_lo_del_destino():
    propia = ImporteMes(vinculado_ide=20, cantidad=Decimal("5.00"))
    uow = _uow_copia(destino_mes={20: propia})
    _copiar_trabajador(uow)
    assert uow.importes.filas[P_ACT] == {20: propia}
    assert uow.importes.escrituras == []
    assert [t for t, _, _ in uow.eventos.registrados] == ["COPIA"]


def test_f069_r8_sin_nada_en_origen_ni_filas_ni_evento():
    uow = _uow_copia(origen_mes={})
    _copiar_trabajador(uow)
    assert uow.importes.escrituras == []
    assert [t for t, _, _ in uow.eventos.registrados] == ["COPIA"]


def test_f069_r8_deshacer_dos_veces_deshace_la_copia_entera():
    uow = _uow_copia()
    _copiar_trabajador(uow)
    deshacer = DeshacerUltimaModificacion()
    deshacer.ejecutar(uow, ANIO, MES, 10, "pgris", filtro=FILTRO)
    assert uow.importes.filas[P_ACT] == {}
    assert _subfila(uow, 100).cantidad == Decimal("80.00")
    deshacer.ejecutar(uow, ANIO, MES, 10, "pgris", filtro=FILTRO)
    assert uow.lineas[P_ACT][10] == []


def test_f069_r8_d19_un_comentario_sin_cantidad_se_copia_sin_copiado():
    """D19 + R8: `copiado = true` solo si se copia una cantidad; el
    comentario sin cantidad del mes o de la caja se copia igual, sin la
    marca (no hay nada que revisar: no se registra)."""
    uow = _uow_copia(origen_mes={20: ImporteMes(
        vinculado_ide=20, cantidad=None, comentario="visita")})
    caja = dataclasses.replace(CAJA, comentario="sin caja")
    uow.lineas[P_ANT][10] = [dataclasses.replace(
        uow.lineas[P_ANT][10][0], vinculados=(VP, caja))]
    _copiar_trabajador(uow)
    assert uow.importes.filas[P_ACT] == {20: ImporteMes(
        vinculado_ide=20, cantidad=None, copiado=False, comentario="visita")}
    sub = _subfila(uow, 100)
    assert (sub.cantidad, sub.copiado, sub.comentario) == (
        None, None, "sin caja")
    _, _, despues = uow.eventos.registrados[1]
    assert [(b["vinculado_ide"], b["copiado"]) for b in despues] == [
        (20, False), (30, False)]


def test_f069_r8_la_copia_repetida_del_trabajador_solo_completa_el_mes():
    uow = _uow_copia()
    _copiar_trabajador(uow)
    uow.importes.filas[P_ACT].clear()
    _copiar_trabajador(uow)
    assert [t for t, _, _ in uow.eventos.registrados] == [
        "COPIA", "IMPORTES", "IMPORTES"]
    assert uow.importes.filas[P_ACT][20].copiado is True


# ================= T9 · R15, R16 · el payload del registro ================= #
from application.registro_sigrid import RegistroSigrid  # noqa: E402

from tests.test_f022_empresa_en_linea import (  # noqa: E402
    _Sesion as _SesionReg,
    _Transfer as _TransferReg,
)
from tests.test_f044_payload_traza import _TEL, _Cargador  # noqa: E402
from tests.test_f051_hmores_ide import _fila  # noqa: E402


class _LeerImportes:
    def __init__(self, filas: dict[int, ImporteMes]) -> None:
        self.filas = filas
        self.llamadas: list[tuple] = []

    def __call__(self, s, anio, mes, vinculados):
        self.llamadas.append((anio, mes, sorted(vinculados)))
        return dict(self.filas)


def _payload(filas, por_id, *, tipos=TIPOS, leer=None, precio=Decimal("0.20")):
    transfer = _TransferReg()
    leer = leer or _LeerImportes({})
    RegistroSigrid(lambda: _SesionReg(filas), transfer, 1,
                   vinculados_desde=(2026, 10), subfilas=_Cargador(por_id),
                   importes=tipos, precio_km=precio,
                   leer_importes=leer).ejecutar(2026, 10, pisar_claves=[])
    [p] = transfer.payloads
    return p["lineas"], leer


def test_f069_r15_r16_los_de_cantidad_con_sus_claves_y_una_lectura():
    caja = dataclasses.replace(CAJA, cantidad=Decimal("80.00"), copiado=True,
                               comentario="caja")
    viaje = SubfilaVinculado(vinculado_ide=21, tipo="VIAJE", cod="VJ-21")
    leer = _LeerImportes({20: ImporteMes(
        vinculado_ide=20, cantidad=Decimal("724.50"), comentario="visita")})
    [ln], leer = _payload([_fila(1)], {1: (_TEL, VP, viaje, caja)}, leer=leer)
    tel, vp, vj, cj = ln["vinculados"]
    assert tel == {"recurso_ide": 10, "tipo": "TF", "tipo_res": "TELEFONO",
                   "cod": "TF-10"}
    assert vp == {"recurso_ide": 20, "tipo": "VP", "tipo_res": None,
                  "cod": "VP-20", "importe_mensual": True, "unidad": "km",
                  "reparto": "pct", "cantidad": 724.5, "copiado": False,
                  "comentario": "visita", "precio_km": 0.2}
    assert (vj["unidad"], vj["reparto"], vj["cantidad"], vj["copiado"],
            vj["comentario"]) == ("eur", "pct", None, False, None)
    assert "precio_km" not in vj
    assert (cj["reparto"], cj["cantidad"], cj["copiado"],
            cj["comentario"]) == ("obra", 80.0, True, "caja")
    assert leer.llamadas == [(2026, 10, [20, 21])]       # la caja no se lee


def test_f069_r16_sin_vinculados_de_cantidad_ni_se_lee_y_el_payload_de_hoy():
    hoy, _ = _payload([_fila(1)], {1: (_TEL,)}, tipos={})
    con, leer = _payload([_fila(1)], {1: (_TEL,)})
    assert con == hoy and leer.llamadas == []
    sin_tipos, leer = _payload([_fila(1)], {1: (_TEL, VP, CAJA)}, tipos={})
    assert leer.llamadas == []
    assert all("importe_mensual" not in v for v in sin_tipos[0]["vinculados"])


def test_f069_r16_solo_caja_tampoco_lee():
    _, leer = _payload([_fila(1)], {1: (CAJA,)})
    assert leer.llamadas == []


def test_f069_r15_la_linea_lleva_su_comentario_solo_si_lo_tiene():
    fila = _fila(1)
    fila[0].comentario = "mes con visita"
    [ln], _ = _payload([fila], {})
    assert ln["comentario"] == "mes con visita"
    [ln], _ = _payload([_fila(2)], {})
    assert "comentario" not in ln


def test_f069_r15_el_contenedor_pasa_tipos_y_precio(monkeypatch):
    from interface_adapters.api import deps

    capturado: dict = {}

    class _Espia(RegistroSigrid):
        def __init__(self, *a, **kw):
            capturado.update(kw)
            super().__init__(*a, **kw)

    monkeypatch.setattr(deps, "RegistroSigrid", _Espia)
    monkeypatch.delenv("EMPRESA_IMPUTACION", raising=False)
    contenedor = deps.construir_contenedor(Settings(_env_file=None),
                                           lambda: None)
    # F-080 (R1): los de la config versionada, con la caja por % (`TIPOS`,
    # con la caja por obra, es el doble de los tests del mecanismo `obra`).
    tipos_cfg = {**TIPOS, "CAJA": TipoCantidad("eur", "pct")}
    assert capturado["importes"] == tipos_cfg
    assert capturado["precio_km"] == Decimal("0.20")
    # Mutación (deps.py:172-173, sin mutantes del generador): los mismos
    # tipos llegan a las rutas (`PUT …/importes`, cuadrante) y a traer de
    # Sigrid (comentario de las cantidades del mes, R32).
    assert contenedor.importes == tipos_cfg
    assert contenedor.traer_sigrid._importes == tipos_cfg


# ======================= R10 · el cuadrante ============================== #
from application.use_cases import ObtenerCuadrante  # noqa: E402
from domain.importes import importes_del_mes  # noqa: E402
from infrastructure.db.repositories import importes_del_mes_de  # noqa: E402


class _ImportesQueCuentan(_ImportesMem):
    def __init__(self) -> None:
        super().__init__()
        self.lecturas = 0

    def del_periodo(self, periodo_id):
        self.lecturas += 1
        return super().del_periodo(periodo_id)


def test_f069_r10_el_cuadrante_lee_las_del_mes_una_vez_y_solo_con_vinculados():
    uow = _uow_imp(VP, CAJA)
    uow.importes = _ImportesQueCuentan()
    uow.importes.filas[20] = ImporteMes(vinculado_ide=20,
                                        cantidad=Decimal("100.00"))
    cuadrante = ObtenerCuadrante().ejecutar(uow, ANIO, MES, FILTRO,
                                            usuario="pgris")
    assert uow.importes.lecturas == 1
    [ana] = [f for f in cuadrante.filas if f.trabajador.ide == 10]
    assert [i.vinculado_ide for i in ana.importes] == [20]
    sin = _uow_imp()
    sin.importes = _ImportesQueCuentan()
    ObtenerCuadrante().ejecutar(sin, ANIO, MES, FILTRO, usuario="pgris")
    assert sin.importes.lecturas == 0


def test_f069_r10_importes_del_mes_uno_por_vinculado_por_pct():
    lineas = [dataclasses.replace(_ln(100, "60"), vinculados=(VP, CAJA, TEL)),
              dataclasses.replace(_ln(900, "40"), vinculados=(VP, CAJA, TEL))]
    guardada = ImporteMes(vinculado_ide=20, cantidad=Decimal("5.00"),
                          copiado=True, comentario="c")
    assert importes_del_mes(lineas, {20: guardada}, TIPOS) == [ImporteMes(
        vinculado_ide=20, tipo="VP", cod="VP-20", unidad="km",
        cantidad=Decimal("5.00"), copiado=True, comentario="c")]
    assert importes_del_mes(lineas, {}, TIPOS)[0].cantidad is None
    assert importes_del_mes(lineas, {}, {}) == []


def test_f069_r16_la_lectura_del_registro_es_una_y_por_periodo():
    s = _Sesion()
    s.scalars = lambda stmt: (s.sentencias.append(stmt)
                              or SimpleNamespace(all=lambda: []))
    assert importes_del_mes_de(s, 2026, 10, []) == {}
    assert s.sentencias == []
    importes_del_mes_de(s, 2026, 10, [21, 20, 21])
    [stmt] = s.sentencias
    sql = _sql(stmt)
    assert "JOIN periodo ON periodo.id = importe_vinculado.periodo_id" in sql
    assert "importe_vinculado.vinculado_ide IN" in sql
    assert stmt.compile(dialect=postgresql.dialect()).params[
        "vinculado_ide_1"] == [20, 21]


# ================== R30 · la traza conserva cantidad y comentario ========= #
from application.traza_vinculados import trazar_vinculados  # noqa: E402


class _SesionTraza:
    """Apunta cada sentencia que ejecuta la traza (sin base)."""

    def __init__(self) -> None:
        self.sentencias: list = []

    def execute(self, stmt):
        self.sentencias.append(stmt)


def _columnas_traza(stmt) -> tuple[set[str], set[str]]:
    """Las columnas del `INSERT` y las del `ON CONFLICT DO UPDATE SET`."""
    sql = " ".join(str(stmt.compile(dialect=postgresql.dialect())).split())
    insert = sql.split("(", 1)[1].split(")", 1)[0]
    set_ = sql.split("DO UPDATE SET", 1)[1]
    return ({c.strip() for c in insert.split(",")},
            {p.split("=")[0].strip() for p in set_.split(", ")})


def test_f069_r30_la_traza_de_una_caja_conserva_cantidad_copiado_y_comentario():
    """R30 (review 1, cambio 5): la traza que `registro_sigrid` escribe en
    la subfila de un vinculado (escrito, ya registrado u omitido) solo toca
    `sigrid_*`: la cantidad, el `copiado` y el comentario de la caja siguen
    como estaban (el `ON CONFLICT` no los nombra)."""
    s = _SesionTraza()
    trazar_vinculados(s, {
        "vinculados": [
            {"registro_id": 7, "recurso_ide": 30, "accion": "escribir",
             "hmores_ide": 5301, "parte_cod": "P-1", "reparto": "obra",
             "cantidad": 80.0, "copiado": True, "comentario": "caja"},
            {"registro_id": 7, "recurso_ide": 31, "accion": "ya_registrado",
             "hmores_ide": 5302, "cantidad": 10.0, "comentario": "otra"}],
        "omitidas": [{"registro_id": 7, "vinculado_ide": 32,
                      "motivo": "sin partida"}]})
    assert len(s.sentencias) == 3
    for stmt in s.sentencias:
        insert, set_ = _columnas_traza(stmt)
        assert not ({"cantidad", "copiado", "comentario"} & (insert | set_)), (
            insert, set_)
        assert set_ and all(c.startswith("sigrid_") for c in set_), set_


# ============ Pasada de campaña: supervivientes de la mutación ============ #
# (progress/mutacion_F-069.md). Cada test nombra el mutante que mata.
from application.use_cases import _snapshot_importes  # noqa: E402
from infrastructure.db.repositories import (  # noqa: E402
    PgAsignacionRepository,
    PgImporteRepository,
    _a_importe,
)
from interface_adapters.api.schemas import SubfilaOut, _cantidad_out  # noqa: E402


def test_f069_r32_poner_comentario_solo_en_esa_linea():
    """`poner_comentario` filtra por trabajador, obra y modo con `=`
    (mutantes `!=` de repositories.py:574-576)."""
    s = _Sesion()
    PgAsignacionRepository(s).poner_comentario(7, 10, (694, False), "x")
    [stmt] = s.sentencias
    sql = _sql(stmt)
    for col in ("periodo_id", "trabajador_ide", "obra_ide", "es_postventa"):
        assert f"asignacion.{col} = " in sql, sql
    assert "!=" not in sql


def test_f069_r16_importes_del_mes_de_ese_anio_y_mes():
    """repositories.py:834: `anio = ` (no `!=`)."""
    s = _Sesion()
    s.scalars = lambda stmt: (s.sentencias.append(stmt)
                              or SimpleNamespace(all=lambda: []))
    importes_del_mes_de(s, 2026, 10, [20])
    sql = _sql(s.sentencias[0])
    assert "periodo.anio = " in sql and "periodo.mes = " in sql
    assert "!=" not in sql


def test_f069_r3_las_del_mes_se_cruzan_con_su_vinculado():
    """repositories.py:850: el `JOIN` con `recurso_vinculado` por su `ide`."""
    s = _Sesion()
    PgImporteRepository(s).de_trabajador(7, 10)
    sql = _sql(s.sentencias[0])
    assert ("JOIN recurso_vinculado ON recurso_vinculado.ide = "
            "importe_vinculado.vinculado_ide") in sql
    assert "!=" not in sql


def test_f069_r3_una_cantidad_cero_se_lee_como_cero():
    """repositories.py:819: `cantidad is None`, no `not cantidad`: 0 € es
    una cantidad («a 0, nada que escribir»), no «sin cantidad»."""
    f = SimpleNamespace(vinculado_ide=20, cantidad=Decimal("0.00"),
                        copiado=False, comentario=None)
    assert _a_importe(f).cantidad == Decimal("0.00")


def test_f069_r7_el_snapshot_ordena_por_vinculado_y_obra():
    """use_cases.py:1304: orden por (vinculado, obra, modo), no por el
    `copiado`: dos cajas del mismo vinculado en dos obras."""
    foto = {(30, 100, False): (Decimal("1"), True, None),
            (30, 200, False): (Decimal("2"), False, None)}
    assert [b["obra_ide"] for b in _snapshot_importes(foto)] == [100, 200]


def test_f069_r10_una_caja_a_cero_y_sin_copiado_sale_con_sus_claves():
    """schemas.py:153 (y :154): `exclude_if=v is None`: la cantidad 0 y el
    `copiado` false salen (solo se omite lo nulo)."""
    v = SimpleNamespace(cantidad=Decimal("0.00"), copiado=False,
                        comentario=None)
    sub = SubfilaOut(vinculado_ide=30, tipo="CAJA", tipo_res=None, cod="CJ",
                     partida_ide=None, partida_cod=None, partida_res=None,
                     partida_fija=False,
                     **_cantidad_out(v, TipoCantidad("eur", "obra")))
    out = sub.model_dump(mode="json")
    assert (out["cantidad"], out["copiado"]) == (0.0, False)
    assert "comentario" not in out
