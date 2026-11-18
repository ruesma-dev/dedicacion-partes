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
