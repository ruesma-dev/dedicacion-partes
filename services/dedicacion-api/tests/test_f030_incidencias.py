# tests/test_f030_incidencias.py
"""F-030 · Incidencias en el cuadrante: dominio, esquema, guardado,
deshacer y copias (R4, R5, R17-R22).

Offline: funciones puras, metadatos del ORM y casos de uso con una
UnitOfWork en memoria. Ni red, ni BBDD, ni `.env`.
"""
from __future__ import annotations

import pytest
from domain.errors import ErrorDominio, IncidenciaInvalida
from domain.incidencias import completar_dias, letra_y_nombre, validar_incidencias
from domain.models import Incidencia


# ============================ dominio (T2) ============================== #
@pytest.mark.parametrize("res, cod, esperado", [
    ("Vacaciones(V)", "CIV", ("V", "Vacaciones")),
    ("Falta Justificada/Permiso(FJ)", "CIP", ("FJ", "Falta Justificada/Permiso")),
    ("Accidente/Enf. Profesional(AT)", "CIA", ("AT", "Accidente/Enf. Profesional")),
    ("Enfermedad/Acc. no laboral(B)", "CIE", ("B", "Enfermedad/Acc. no laboral")),
    ("  Huelga (H)  ", "CIH", ("H", "Huelga")),
    ("Maternidad/Paternidad( M )", "CIM", ("M", "Maternidad/Paternidad")),
])
def test_f030_r4_dominio_letra_entre_parentesis_al_final(res, cod, esperado):
    assert letra_y_nombre(res, cod) == esperado


@pytest.mark.parametrize("res, cod, esperado", [
    ("Fin de Incidencia", "CIZ", ("Z", "Fin de Incidencia")),
    ("Otra cosa", " CIQ ", ("Q", "Otra cosa")),
    ("Sin letra()", "CIX", ("X", "Sin letra()")),
    ("(V) delante", "CIV", ("V", "(V) delante")),
    ("Raro", "XYZ", ("XYZ", "Raro")),
    (None, "CIV", ("V", "")),
    ("   ", "CIV", ("V", "")),
])
def test_f030_r4_dominio_sin_parentesis_la_letra_es_el_codigo_sin_ci(res, cod, esperado):
    assert letra_y_nombre(res, cod) == esperado


@pytest.mark.parametrize("desde, hasta, anio, mes, esperado", [
    (None, None, 2026, 9, (1, 30)),
    (None, None, 2026, 10, (1, 31)),
    (None, None, 2026, 2, (1, 28)),
    (None, None, 2028, 2, (1, 29)),
    (5, None, 2026, 9, (5, 30)),
    (None, 9, 2026, 9, (1, 9)),
    (5, 9, 2026, 9, (5, 9)),
    (31, 31, 2026, 9, (31, 31)),   # completar no valida: lo hace validar
])
def test_f030_r17_dominio_completar_dias(desde, hasta, anio, mes, esperado):
    assert completar_dias(desde, hasta, anio, mes) == esperado


def _inc(desde: int, hasta: int, obra: int = 1, cod: str = "CIV") -> Incidencia:
    return Incidencia(obra_ide=obra, codigo=cod, dia_desde=desde, dia_hasta=hasta)


@pytest.mark.parametrize("lista", [
    [],
    [_inc(1, 30)],
    [_inc(1, 1)],
    [_inc(30, 30)],
    [_inc(1, 4), _inc(5, 9), _inc(10, 30)],
    [_inc(10, 12), _inc(1, 9)],             # el orden de llegada no importa
    [_inc(5, 9, obra=1), _inc(10, 10, obra=2, cod="CIE")],
])
def test_f030_r19_dominio_validas(lista):
    assert validar_incidencias(lista, 2026, 9) is None


@pytest.mark.parametrize("lista, motivo", [
    ([_inc(0, 3)], "fuera del mes"),
    ([_inc(3, 31)], "fuera del mes"),
    ([_inc(31, 31)], "fuera del mes"),
    ([_inc(-1, 3)], "fuera del mes"),
    ([_inc(9, 5)], "posterior"),
    ([_inc(5, 9), _inc(9, 12)], "comparten"),
    ([_inc(5, 9), _inc(1, 5)], "comparten"),
    ([_inc(1, 30), _inc(10, 12, obra=2, cod="CIE")], "comparten"),
    ([_inc(1, 3), _inc(10, 20), _inc(15, 15)], "comparten"),
    ([_inc(10, 20), _inc(1, 3), _inc(2, 2)], "comparten"),
])
def test_f030_r19_dominio_invalidas_con_motivo(lista, motivo):
    with pytest.raises(IncidenciaInvalida, match=motivo):
        validar_incidencias(lista, 2026, 9)


def test_f030_r19_dominio_febrero_bisiesto_y_no_bisiesto():
    assert validar_incidencias([_inc(29, 29)], 2028, 2) is None
    with pytest.raises(IncidenciaInvalida, match="fuera del mes"):
        validar_incidencias([_inc(29, 29)], 2026, 2)


def test_f030_r19_dominio_el_error_es_de_dominio():
    assert issubclass(IncidenciaInvalida, ErrorDominio)


# ============================ esquema (T3) ============================== #
def _tipos(tabla) -> dict[str, str]:
    from sqlalchemy.dialects import postgresql

    return {c.name: c.type.compile(dialect=postgresql.dialect())
            for c in tabla.columns}


def test_f030_r3_esquema_tabla_tipo_incidencia():
    from infrastructure.db.orm_models import Base, TipoIncidenciaORM

    tabla = TipoIncidenciaORM.__table__
    assert tabla.name == "tipo_incidencia"
    assert Base.metadata.tables["tipo_incidencia"] is tabla
    assert [c.name for c in tabla.primary_key.columns] == ["ide"]
    assert tabla.columns["ide"].autoincrement is False   # el de `auxhor`
    assert _tipos(tabla) == {
        "ide": "BIGINT", "codigo": "TEXT", "letra": "TEXT", "nombre": "TEXT",
        "activa": "BOOLEAN", "sync_en": "TIMESTAMP WITH TIME ZONE"}
    assert not tabla.columns["codigo"].nullable
    assert not tabla.columns["activa"].nullable


def test_f030_r17_esquema_tabla_incidencia():
    from infrastructure.db.orm_models import Base, IncidenciaORM

    tabla = IncidenciaORM.__table__
    assert tabla.name == "incidencia"
    assert Base.metadata.tables["incidencia"] is tabla
    assert _tipos(tabla) == {
        "id": "INTEGER", "periodo_id": "INTEGER", "trabajador_ide": "BIGINT",
        "obra_ide": "BIGINT", "codigo": "TEXT", "dia_desde": "SMALLINT",
        "dia_hasta": "SMALLINT", "actualizado_en": "TIMESTAMP WITH TIME ZONE",
        "actualizado_por": "TEXT", "sigrid_estado": "VARCHAR(16)",
        "sigrid_parte_cod": "VARCHAR(24)", "sigrid_ide_ini": "INTEGER",
        "sigrid_ide_fin": "INTEGER", "sigrid_motivo": "VARCHAR(300)",
        "sigrid_registrado_at_utc": "TIMESTAMP WITH TIME ZONE",
        "sigrid_registrado_by": "VARCHAR(64)"}
    fks = {fk.parent.name: (fk.column.table.name, fk.ondelete)
           for fk in tabla.foreign_keys}
    assert fks == {"periodo_id": ("periodo", "CASCADE"),
                   "trabajador_ide": ("trabajador", None),
                   "obra_ide": ("obra", None)}
    obligatorias = {c.name for c in tabla.columns if not c.nullable}
    assert obligatorias == {"id", "periodo_id", "trabajador_ide", "obra_ide",
                            "codigo", "dia_desde", "dia_hasta",
                            "actualizado_en", "actualizado_por"}
    checks = {c.name: str(c.sqltext) for c in tabla.constraints
              if c.__class__.__name__ == "CheckConstraint"}
    assert checks == {"ck_incidencia_dias": (
        "dia_desde BETWEEN 1 AND 31 AND dia_hasta BETWEEN dia_desde AND 31")}
    assert [(i.name, [c.name for c in i.columns]) for i in tabla.indexes] == [
        ("ix_incidencia_periodo_trab", ["periodo_id", "trabajador_ide"])]


def test_f030_r2_esquema_las_crea_create_all_y_asignacion_no_cambia():
    """Dos tablas NUEVAS: sobre una base sin ellas `alters_faltantes` no
    emite nada (las crea `create_all` al arrancar) y nada para `asignacion`,
    cuyo esquema F-030 no toca (R2)."""
    from infrastructure.db.esquema import alters_faltantes
    from infrastructure.db.orm_models import AsignacionORM, Base

    al_dia = {t.name: {c.name for c in t.columns}
              for t in Base.metadata.tables.values()}
    sin_nuevas = {k: v for k, v in al_dia.items()
                  if k not in ("tipo_incidencia", "incidencia")}
    assert alters_faltantes(Base.metadata, sin_nuevas) == []
    assert alters_faltantes(Base.metadata, al_dia) == []
    assert "codigo" not in AsignacionORM.__table__.columns
    assert not any("incidencia" in c.name
                   for c in AsignacionORM.__table__.columns)
