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


# ======================= dobles en memoria (T5-T7) ====================== #
import dataclasses  # noqa: E402

from domain.models import (  # noqa: E402
    EventoPendiente,
    FiltroEmpresa,
    TipoIncidencia,
)

from tests.test_f024_cuadrante_empresa import (  # noqa: E402
    ANIO,
    MES,
    OBRAS,
    P_ACT,
    TRABAJADORES,
    _Uow,
    _uow,
)
from tests.test_f024_rutas_empresa import BASE, api  # noqa: E402,F401

#: Catálogo activo de prueba (el de `auxhor`, design §10).
CATALOGO = [TipoIncidencia(11, "CIA", "AT", "Accidente/Enf. Profesional"),
            TipoIncidencia(12, "CIE", "B", "Enfermedad/Acc. no laboral"),
            TipoIncidencia(16, "CIP", "FJ", "Falta Justificada/Permiso"),
            TipoIncidencia(17, "CIV", "V", "Vacaciones")]


class _TiposMem:
    def __init__(self, tipos=None) -> None:
        self.tipos = list(CATALOGO if tipos is None else tipos)

    def activos(self) -> list[TipoIncidencia]:
        return sorted((t for t in self.tipos if t.activa),
                      key=lambda t: (t.letra, t.codigo))


class _IncidenciasMem:
    """Incidencias en memoria por (periodo, trabajador), con `id` propio y
    los datos de lectura (obra, letra y nombre) resueltos como el
    repositorio."""

    def __init__(self) -> None:
        self.datos: dict[tuple[int, int], list[Incidencia]] = {}
        self.siguiente = 1
        self.reemplazos: list[tuple[int, int, str]] = []

    def _resolver(self, inc: Incidencia) -> Incidencia:
        tipo = next((t for t in CATALOGO if t.codigo == inc.codigo), None)
        o = OBRAS[inc.obra_ide]
        return dataclasses.replace(
            inc, obra_cod=o.cod, obra_descripcion=o.descripcion,
            letra=tipo.letra if tipo else "", nombre=tipo.nombre if tipo else "")

    def de_trabajador(self, periodo_id: int, ide: int) -> list[Incidencia]:
        return list(self.datos.get((periodo_id, ide), []))

    def de_periodo(self, periodo_id: int) -> dict[int, list[Incidencia]]:
        return {i: list(v) for (p, i), v in self.datos.items()
                if p == periodo_id and v}

    def reemplazar(self, periodo_id: int, ide: int, lista: list[Incidencia],
                   usuario: str) -> None:
        nuevas = []
        for inc in lista:
            nuevas.append(self._resolver(dataclasses.replace(
                inc, id=self.siguiente, sigrid_estado=None,
                sigrid_parte_cod=None, sigrid_motivo=None)))
            self.siguiente += 1
        self.datos[(periodo_id, ide)] = sorted(
            nuevas, key=lambda i: (i.dia_desde, i.id))
        self.reemplazos.append((periodo_id, ide, usuario))

    def poner(self, ide: int, *incs: Incidencia, periodo_id: int = P_ACT) -> None:
        self.reemplazar(periodo_id, ide, list(incs), "previo")
        self.reemplazos.clear()


class _EventosConTipo:
    """Eventos en memoria que, como el repositorio, guardan el `tipo`."""

    def __init__(self) -> None:
        self.eventos: list[tuple[int, EventoPendiente, list]] = []
        self.deshechos: set[int] = set()

    def registrar(self, periodo_id, ide, tipo, usuario, antes, despues):
        self.eventos.append((ide, EventoPendiente(
            len(self.eventos) + 1, usuario, antes, tipo=tipo.value), despues))

    def _pendientes(self):
        return [(i, e) for i, e, _ in self.eventos if e.id not in self.deshechos]

    def ultimo_pendiente(self, periodo_id: int, ide: int):
        propios = [e for i, e in self._pendientes() if i == ide]
        return propios[-1] if propios else None

    def marcar_deshecho(self, evento_id: int) -> None:
        self.deshechos.add(evento_id)

    def autores_ultimo_pendiente(self, periodo_id: int) -> dict[int, str]:
        return {i: e.usuario for i, e in self._pendientes()}


class _UowInc(_Uow):
    def __init__(self) -> None:
        super().__init__(_uow().lineas)
        self.incidencias = _IncidenciasMem()
        self.tipos_incidencia = _TiposMem()
        self.eventos = _EventosConTipo()
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


FILTRO = FiltroEmpresa(empresa=1, por_defecto=1, empresa_obras=1)
USUARIO = "ana@ruesma.es"


# ============================ cuadrante (T5) ============================ #
def test_f030_r21_cuadrante_y_fila_llevan_las_incidencias_del_trabajador():
    from application.use_cases import ObtenerCuadrante, ObtenerFilaTrabajador

    uow = _UowInc()
    uow.incidencias.poner(14, _inc(5, 9, obra=100), _inc(20, 20, obra=101, cod="CIE"))
    cuadrante = ObtenerCuadrante().ejecutar(uow, ANIO, MES, FILTRO, usuario=USUARIO)
    filas = {f.trabajador.ide: f for f in cuadrante.filas}
    assert [(i.obra_cod, i.letra, i.dia_desde, i.dia_hasta)
            for i in filas[14].incidencias] == [("0100", "V", 5, 9),
                                                ("0101", "B", 20, 20)]
    assert all(f.incidencias == () for i, f in filas.items() if i != 14)
    fila, _ = ObtenerFilaTrabajador().ejecutar(uow, ANIO, MES, 14,
                                               filtro=FILTRO, usuario=USUARIO)
    assert fila.incidencias == filas[14].incidencias
    otra, _ = ObtenerFilaTrabajador().ejecutar(uow, ANIO, MES, 10,
                                               filtro=FILTRO, usuario=USUARIO)
    assert otra.incidencias == ()


def test_f030_r22_cuadrante_total_estado_y_resumen_como_sin_incidencias():
    from application.use_cases import ObtenerCuadrante

    sin = ObtenerCuadrante().ejecutar(_UowInc(), ANIO, MES, FILTRO, usuario=USUARIO)
    uow = _UowInc()
    uow.incidencias.poner(14, _inc(1, 30, obra=100))
    uow.incidencias.poner(10, _inc(1, 3, obra=100))
    con = ObtenerCuadrante().ejecutar(uow, ANIO, MES, FILTRO, usuario=USUARIO)
    assert con.resumen == sin.resumen
    assert [(f.total, len(f.lineas)) for f in con.filas] == [
        (f.total, len(f.lineas)) for f in sin.filas]


def test_f030_r21_cuadrante_salida_json_de_las_incidencias():
    from domain.models import CuadranteTrabajador
    from interface_adapters.api.schemas import a_trabajador_out

    inc = dataclasses.replace(
        _inc(5, 9, obra=100), id=7, obra_cod="0100", obra_descripcion="OBRA 100",
        letra="V", nombre="Vacaciones", sigrid_estado="registrado",
        sigrid_parte_cod="PT26/1", sigrid_motivo=None)
    fila = CuadranteTrabajador(trabajador=TRABAJADORES[14], lineas=[],
                               incidencias=(inc,))
    out = a_trabajador_out(fila, 1).model_dump()
    assert out["incidencias"] == [{
        "id": 7, "obra_ide": 100, "obra_cod": "0100",
        "obra_descripcion": "OBRA 100", "codigo": "CIV", "letra": "V",
        "nombre": "Vacaciones", "dia_desde": 5, "dia_hasta": 9,
        "sigrid_estado": "registrado", "sigrid_parte_cod": "PT26/1",
        "sigrid_motivo": None}]
    # R22: sin líneas sigue «sin carga», con incidencias o sin ellas.
    assert (out["total"], out["estado"], out["desviacion"]) == (0.0, "SIN_CARGA", 0.0)
    sin = a_trabajador_out(CuadranteTrabajador(trabajador=TRABAJADORES[14]), 1)
    assert sin.model_dump()["incidencias"] == []


def test_f030_r21_cuadrante_ruta_publica_las_incidencias(api):
    cliente, contenedor = api
    uow = contenedor.uow()
    uow.incidencias = _IncidenciasMem()
    uow.incidencias.poner(10, _inc(5, 9, obra=100))
    r = cliente.get(f"{BASE}/cuadrante", headers={"X-Usuario": USUARIO})
    assert r.status_code == 200, r.text
    filas = {t["ide"]: t for t in r.json()["trabajadores"]}
    assert [(i["codigo"], i["dia_desde"], i["dia_hasta"])
            for i in filas[10]["incidencias"]] == [("CIV", 5, 9)]
    assert filas[14]["incidencias"] == []
    assert filas[10]["total"] == 100.0       # R22: 60 + 40, nada más


# =========================== repositorio (T5) =========================== #
class _Filas:
    def __init__(self, filas):
        self._filas = filas

    def all(self):
        return list(self._filas)


class _SesionInc:
    def __init__(self, filas=()):
        self.filas = list(filas)
        self.sentencias: list = []
        self.anadidas: list = []

    def execute(self, stmt):
        self.sentencias.append(stmt)
        return _Filas(self.filas)

    def add(self, orm):
        self.anadidas.append(orm)

    def flush(self):
        return None


def _sql(stmt) -> str:
    from sqlalchemy.dialects import postgresql

    return " ".join(str(stmt.compile(dialect=postgresql.dialect())).split())


def _orm_inc(id_, trab, obra, cod, desde, hasta, **traza):
    from infrastructure.db.orm_models import IncidenciaORM

    return IncidenciaORM(id=id_, periodo_id=P_ACT, trabajador_ide=trab,
                         obra_ide=obra, codigo=cod, dia_desde=desde,
                         dia_hasta=hasta, **traza)


def test_f030_r21_cuadrante_repo_de_periodo_mapea_y_agrupa():
    from infrastructure.db.repositories import PgIncidenciaRepository

    sesion = _SesionInc([
        (_orm_inc(3, 10, 100, "CIV", 5, 9, sigrid_estado="omitido",
                  sigrid_parte_cod="PT1", sigrid_motivo="ya está"),
         "0100", "OBRA 100", "V", "Vacaciones"),
        (_orm_inc(4, 10, 101, "CIQ", 12, 12), "0101", "OBRA 101", None, None),
        (_orm_inc(5, 14, 100, "CIE", 1, 30), "0100", "OBRA 100", "B", "Enf"),
    ])
    res = PgIncidenciaRepository(sesion).de_periodo(P_ACT)  # type: ignore[arg-type]
    assert res == {
        10: [Incidencia(obra_ide=100, codigo="CIV", dia_desde=5, dia_hasta=9,
                        id=3, obra_cod="0100", obra_descripcion="OBRA 100",
                        letra="V", nombre="Vacaciones", sigrid_estado="omitido",
                        sigrid_parte_cod="PT1", sigrid_motivo="ya está"),
             Incidencia(obra_ide=101, codigo="CIQ", dia_desde=12, dia_hasta=12,
                        id=4, obra_cod="0101", obra_descripcion="OBRA 101",
                        letra="Q", nombre="")],
        14: [Incidencia(obra_ide=100, codigo="CIE", dia_desde=1, dia_hasta=30,
                        id=5, obra_cod="0100", obra_descripcion="OBRA 100",
                        letra="B", nombre="Enf")]}
    [stmt] = sesion.sentencias
    assert _sql(stmt) == (
        "SELECT incidencia.id, incidencia.periodo_id, incidencia.trabajador_ide, "
        "incidencia.obra_ide, incidencia.codigo, incidencia.dia_desde, "
        "incidencia.dia_hasta, incidencia.actualizado_en, "
        "incidencia.actualizado_por, incidencia.sigrid_estado, "
        "incidencia.sigrid_parte_cod, incidencia.sigrid_ide_ini, "
        "incidencia.sigrid_ide_fin, incidencia.sigrid_motivo, "
        "incidencia.sigrid_registrado_at_utc, incidencia.sigrid_registrado_by, "
        "obra.cod, obra.descripcion, tipo_incidencia.letra, "
        "tipo_incidencia.nombre FROM incidencia "
        "JOIN obra ON obra.ide = incidencia.obra_ide "
        "LEFT OUTER JOIN tipo_incidencia "
        "ON tipo_incidencia.codigo = incidencia.codigo "
        "WHERE incidencia.periodo_id = %(periodo_id_1)s "
        "ORDER BY incidencia.trabajador_ide, incidencia.dia_desde, incidencia.id")


def test_f030_r21_cuadrante_repo_de_trabajador_filtra():
    from infrastructure.db.repositories import PgIncidenciaRepository

    sesion = _SesionInc([(_orm_inc(3, 10, 100, "CIV", 5, 9), "0100", "O",
                          "V", "Vacaciones")])
    res = PgIncidenciaRepository(sesion).de_trabajador(P_ACT, 10)  # type: ignore[arg-type]
    assert [(i.id, i.letra) for i in res] == [(3, "V")]
    [stmt] = sesion.sentencias
    assert _sql(stmt).endswith(
        "WHERE incidencia.periodo_id = %(periodo_id_1)s "
        "AND incidencia.trabajador_ide = %(trabajador_ide_1)s "
        "ORDER BY incidencia.trabajador_ide, incidencia.dia_desde, incidencia.id")
    assert PgIncidenciaRepository(_SesionInc()).de_trabajador(P_ACT, 10) == []  # type: ignore[arg-type]


def test_f030_r21_cuadrante_la_unidad_de_trabajo_trae_el_repositorio():
    from infrastructure.db.repositories import (
        PgIncidenciaRepository,
        SqlAlchemyUnitOfWork,
    )

    class _S:
        def close(self) -> None:
            return None

    with SqlAlchemyUnitOfWork(lambda: _S()) as uow:  # type: ignore[arg-type]
        assert isinstance(uow.incidencias, PgIncidenciaRepository)
