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


def _ddl(tabla) -> list[str]:
    from sqlalchemy.dialects import postgresql
    from sqlalchemy.schema import CreateTable

    texto = str(CreateTable(tabla).compile(dialect=postgresql.dialect()))
    return [l.strip().rstrip(",") for l in texto.strip().splitlines()]


def test_f030_r3_r17_esquema_ddl_y_defectos():
    """Mutación: el DDL entero de PostgreSQL (obligatorias, `SERIAL`,
    defectos de servidor) y los defectos de Python de las dos tablas."""
    from infrastructure.db.orm_models import IncidenciaORM, TipoIncidenciaORM

    assert _ddl(TipoIncidenciaORM.__table__) == [
        "CREATE TABLE tipo_incidencia (", "ide BIGINT NOT NULL",
        "codigo TEXT NOT NULL", "letra TEXT NOT NULL", "nombre TEXT NOT NULL",
        "activa BOOLEAN NOT NULL",
        "sync_en TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL",
        "PRIMARY KEY (ide)", ")"]
    ddl = _ddl(IncidenciaORM.__table__)
    assert ddl[1] == "id SERIAL NOT NULL"
    assert ddl[8] == "actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL"
    assert TipoIncidenciaORM.__table__.columns["activa"].default.arg is True
    assert IncidenciaORM.__table__.columns["actualizado_por"].default.arg         == "local"


def test_f030_r17_los_modelos_son_inmutables():
    import dataclasses

    from domain.models import Incidencia, TipoIncidencia

    tipo = TipoIncidencia(ide=17, codigo="CIV", letra="V", nombre="Vacaciones")
    inc = Incidencia(obra_ide=100, codigo="CIV", dia_desde=5, dia_hasta=9)
    for objeto, campo in ((tipo, "activa"), (inc, "dia_hasta")):
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(objeto, campo, 1)


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
    _ln,
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

    def first(self):
        return self._filas[0] if self._filas else None


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


# ============================= guardar (T6) ============================= #
from decimal import Decimal  # noqa: E402


class _ObrasConVar:
    """Las obras de F-024 y, como el repositorio, cuáles son entradas VAR."""

    def __init__(self, base, var=frozenset()) -> None:
        self._base = base
        self.var = set(var)

    def __getattr__(self, nombre):
        return getattr(self._base, nombre)

    def entradas_var(self, ides: set[int]) -> set[int]:
        return set(ides) & self.var


def _uow_guardar(var=frozenset()) -> _UowInc:
    uow = _UowInc()
    uow.obras = _ObrasConVar(uow.obras, var)
    return uow


def _guardar(uow, entrada, ide=14, usuario=USUARIO, anio=ANIO, mes=MES):
    from application.use_cases import GuardarIncidencias

    return GuardarIncidencias().ejecutar(uow, anio, mes, ide, entrada, usuario,
                                         filtro=FILTRO)


def _e(obra=100, codigo="CIV", desde=None, hasta=None) -> dict:
    return {"obra_ide": obra, "codigo": codigo, "dia_desde": desde,
            "dia_hasta": hasta}


def _tramos(incs) -> list[tuple]:
    return [(i.obra_ide, i.codigo, i.dia_desde, i.dia_hasta) for i in incs]


def test_f030_r17_guardar_sustituye_completa_los_dias_y_deja_evento():
    uow = _uow_guardar()
    fila, resumen = _guardar(uow, [_e(101, "CIE", 20, None), _e(100, " CIV ", None, 9)])
    # MES = 7: «hasta» vacío = 31; «desde» vacío = 1. Ordenadas por día.
    assert _tramos(fila.incidencias) == [(100, "CIV", 1, 9), (101, "CIE", 20, 31)]
    assert [(i.letra, i.obra_cod) for i in fila.incidencias] == [("V", "0100"),
                                                                 ("B", "0101")]
    assert uow.incidencias.reemplazos == [(P_ACT, 14, USUARIO)]
    [(ide, evento, despues)] = uow.eventos.eventos
    assert (ide, evento.usuario, evento.tipo) == (14, USUARIO, "INCIDENCIAS")
    assert evento.snapshot_antes == []
    assert despues == [
        {"obra_ide": 100, "codigo": "CIV", "dia_desde": 1, "dia_hasta": 9},
        {"obra_ide": 101, "codigo": "CIE", "dia_desde": 20, "dia_hasta": 31}]
    assert uow.commits == 1
    assert fila.puede_deshacer is True


def test_f030_r17_guardar_snapshot_antes_son_las_incidencias_previas():
    uow = _uow_guardar()
    uow.incidencias.poner(14, _inc(5, 9, obra=100))
    _guardar(uow, [_e(100, "CIV", 5, 9), _e(100, "CIP", 12, 12)])
    [(_, evento, despues)] = uow.eventos.eventos
    assert evento.snapshot_antes == [
        {"obra_ide": 100, "codigo": "CIV", "dia_desde": 5, "dia_hasta": 9}]
    assert len(despues) == 2


def test_f030_r17_guardar_lo_mismo_no_escribe_ni_deja_evento():
    uow = _uow_guardar()
    uow.incidencias.poner(14, _inc(1, 31, obra=100))
    fila, _ = _guardar(uow, [_e(100, "CIV")])          # vacío = mes entero
    assert uow.incidencias.reemplazos == []
    assert uow.eventos.eventos == []
    assert uow.commits == 1
    assert _tramos(fila.incidencias) == [(100, "CIV", 1, 31)]


def test_f030_r17_guardar_lista_vacia_las_borra():
    uow = _uow_guardar()
    uow.incidencias.poner(14, _inc(5, 9, obra=100))
    fila, _ = _guardar(uow, [])
    assert fila.incidencias == ()
    [(_, evento, despues)] = uow.eventos.eventos
    assert (evento.tipo, despues) == ("INCIDENCIAS", [])


def test_f030_r2_r22_guardar_no_toca_asignaciones_ni_el_100():
    uow = _uow_guardar()
    lineas_antes = {k: list(v) for k, v in uow.lineas[P_ACT].items()}
    _, resumen_sin = _guardar(_uow_guardar(), [])
    fila, resumen = _guardar(uow, [_e(100, "CIV", 1, 30)], ide=10)
    assert uow.lineas[P_ACT] == lineas_antes
    assert uow.reemplazados == []
    assert resumen == resumen_sin
    assert (fila.total, len(fila.lineas)) == (Decimal("100"), 2)


@pytest.mark.parametrize("entrada, motivo", [
    ([_e(100, "CIZ")], "CIZ"),                        # fin: no se elige
    ([_e(100, "CIX")], "CIX"),                        # no está en el catálogo
    ([_e(100, "")], "código"),
    ([_e(999)], "999"),                               # no existe
    ([_e(900)], "900"),                               # de otra empresa
    ([_e(102)], "102"),                               # cerrada: no es normal
    ([_e(100, "CIV", 0, 3)], "fuera del mes"),
    ([_e(100, "CIV", 5, 32)], "fuera del mes"),       # julio
    ([_e(100, "CIV", 9, 5)], "posterior"),
    ([_e(100, "CIV", 5, 9), _e(101, "CIE", 9, 12)], "comparten"),
    ([_e(100, "CIV", None, None), _e(101, "CIE", 30, None)], "comparten"),
    ([{"obra_ide": "x", "codigo": "CIV"}], "inválida"),
    ([{"codigo": "CIV"}], "inválida"),
    ([{"obra_ide": 100, "codigo": "CIV", "dia_desde": "5"}], "inválida"),
    ([{"obra_ide": 100, "codigo": "CIV", "dia_hasta": True}], "inválida"),
    ([{"obra_ide": 100, "codigo": None}], "código"),
])
def test_f030_r19_guardar_invalidas_422_sin_tocar_nada(entrada, motivo):
    from domain.errors import IncidenciaInvalida

    uow = _uow_guardar()
    uow.incidencias.poner(14, _inc(5, 9, obra=100))
    with pytest.raises(IncidenciaInvalida, match=motivo):
        _guardar(uow, entrada)
    assert uow.incidencias.reemplazos == []
    assert uow.eventos.eventos == []
    assert uow.commits == 0


def test_f030_r19_guardar_entrada_var_no_vale():
    from domain.errors import IncidenciaInvalida

    uow = _uow_guardar(var={101})
    with pytest.raises(IncidenciaInvalida, match="VAR"):
        _guardar(uow, [_e(101)])
    assert uow.incidencias.reemplazos == [] and uow.commits == 0
    fila, _ = _guardar(uow, [_e(100)])              # la normal, sí
    assert _tramos(fila.incidencias) == [(100, "CIV", 1, 31)]


def test_f030_r19_guardar_codigo_inactivo_no_vale():
    from domain.errors import IncidenciaInvalida

    uow = _uow_guardar()
    uow.tipos_incidencia = _TiposMem([dataclasses.replace(CATALOGO[3], activa=False)])
    with pytest.raises(IncidenciaInvalida, match="CIV"):
        _guardar(uow, [_e(100, "CIV")])


def test_f030_r18_guardar_periodo_inexistente_trabajador_inexistente_o_cerrado():
    from domain.errors import PeriodoCerrado, PeriodoNoEncontrado, TrabajadorNoEncontrado
    from domain.models import EstadoPeriodo, Periodo

    uow = _uow_guardar()
    with pytest.raises(PeriodoNoEncontrado):
        _guardar(uow, [_e()], anio=ANIO + 1)
    with pytest.raises(TrabajadorNoEncontrado):
        _guardar(uow, [_e()], ide=999)
    uow.periodos.obtener = lambda a, m: (P_ACT, Periodo(a, m, EstadoPeriodo.CERRADO))
    with pytest.raises(PeriodoCerrado):
        _guardar(uow, [_e()])
    assert uow.incidencias.reemplazos == [] and uow.eventos.eventos == []
    assert uow.commits == 0


# ----------------------------- ruta (T6) -------------------------------- #
def _api_inc(api, var=frozenset()):
    cliente, contenedor = api
    uow = contenedor.uow()
    uow.incidencias = _IncidenciasMem()
    uow.tipos_incidencia = _TiposMem()
    uow.obras = _ObrasConVar(uow.obras, var)
    uow.eventos = _EventosConTipo()
    return cliente, contenedor, uow


def test_f030_r17_guardar_ruta_put_devuelve_la_fila(api):
    cliente, contenedor, uow = _api_inc(api)
    r = cliente.put(f"{BASE}/trabajadores/10/incidencias",
                    json={"incidencias": [{"obra_ide": 100, "codigo": "CIV",
                                           "dia_desde": 5}]},
                    headers={"X-Usuario": USUARIO})
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert [(i["codigo"], i["letra"], i["dia_desde"], i["dia_hasta"])
            for i in cuerpo["trabajador"]["incidencias"]] == [("CIV", "V", 5, 31)]
    assert cuerpo["trabajador"]["total"] == 100.0
    assert set(cuerpo) == {"trabajador", "resumen", "propuestas_en_curso"}
    assert contenedor.propuestas_mes.lanzadas == [(ANIO, MES, [10])]
    [(ide, evento, _)] = uow.eventos.eventos
    assert (ide, evento.usuario, evento.tipo) == (10, USUARIO, "INCIDENCIAS")


@pytest.mark.parametrize("cuerpo", [
    {"incidencias": [{"obra_ide": 100, "codigo": "CIV", "pv": True}]},
    {"incidencias": [{"obra_ide": 100}]},
    {"incidencias": [{"obra_ide": 100, "codigo": "CIV", "dia_desde": 1.5}]},
    {"lineas": []},
])
def test_f030_r19_guardar_ruta_cuerpo_invalido_422(api, cuerpo):
    cliente, _, uow = _api_inc(api)
    r = cliente.put(f"{BASE}/trabajadores/10/incidencias", json=cuerpo)
    assert r.status_code == 422
    assert uow.incidencias.reemplazos == []


def test_f030_r19_guardar_ruta_motivo_en_el_422(api):
    cliente, _, uow = _api_inc(api, var={101})
    r = cliente.put(f"{BASE}/trabajadores/10/incidencias",
                    json={"incidencias": [{"obra_ide": 101, "codigo": "CIV"}]})
    assert r.status_code == 422
    assert "VAR" in r.json()["error"]
    r = cliente.put(f"{BASE}/trabajadores/10/incidencias",
                    json={"incidencias": [{"obra_ide": 100, "codigo": "CIV",
                                           "dia_desde": 40}]})
    assert r.status_code == 422 and "fuera del mes" in r.json()["error"]
    assert uow.incidencias.reemplazos == []


def test_f030_r18_guardar_ruta_404(api):
    cliente, _, uow = _api_inc(api)
    r = cliente.put(f"/api/v1/periodos/{ANIO + 1}/{MES}/trabajadores/10/incidencias",
                    json={"incidencias": []})
    assert r.status_code == 404
    r = cliente.put(f"{BASE}/trabajadores/999/incidencias", json={"incidencias": []})
    assert r.status_code == 404


# -------------------------- repositorio (T6) ---------------------------- #
class _SesionReemplazo:
    def __init__(self, previas):
        self.previas = list(previas)
        self.borradas: list = []
        self.anadidas: list = []
        self.sentencias: list = []
        self.flushes = 0

    def scalars(self, stmt):
        self.sentencias.append(stmt)
        return _Filas(self.previas)

    def delete(self, orm):
        self.borradas.append(orm)

    def add(self, orm):
        self.anadidas.append(orm)

    def flush(self):
        self.flushes += 1


def test_f030_r17_guardar_repo_reemplazar_conserva_las_iguales():
    """Las que no cambian conservan su `id` y su traza (su `synckey` en
    Sigrid es `porcentajes:inc:{id}`); las demás se borran o se añaden."""
    from infrastructure.db.repositories import PgIncidenciaRepository

    igual = _orm_inc(3, 14, 100, "CIV", 5, 9, sigrid_estado="registrado")
    cambia = _orm_inc(4, 14, 101, "CIE", 20, 22)
    sesion = _SesionReemplazo([igual, cambia])
    PgIncidenciaRepository(sesion).reemplazar(  # type: ignore[arg-type]
        P_ACT, 14, [_inc(5, 9, obra=100), _inc(20, 23, obra=101, cod="CIE"),
                    _inc(25, 25, obra=100, cod="CIP")], USUARIO)
    assert sesion.borradas == [cambia]
    assert [(o.periodo_id, o.trabajador_ide, o.obra_ide, o.codigo, o.dia_desde,
             o.dia_hasta, o.actualizado_por) for o in sesion.anadidas] == [
        (P_ACT, 14, 101, "CIE", 20, 23, USUARIO),
        (P_ACT, 14, 100, "CIP", 25, 25, USUARIO)]
    assert igual.sigrid_estado == "registrado" and igual.id == 3
    assert sesion.flushes == 1
    [stmt] = sesion.sentencias
    assert _sql(stmt).endswith(
        "FROM incidencia WHERE incidencia.periodo_id = %(periodo_id_1)s "
        "AND incidencia.trabajador_ide = %(trabajador_ide_1)s "
        "ORDER BY incidencia.id")


def test_f030_r17_guardar_repo_reemplazar_duplicadas_y_vacia():
    from infrastructure.db.repositories import PgIncidenciaRepository

    a = _orm_inc(3, 14, 100, "CIV", 5, 9)
    b = _orm_inc(4, 14, 100, "CIV", 5, 9)      # misma clave, dos filas
    sesion = _SesionReemplazo([a, b])
    PgIncidenciaRepository(sesion).reemplazar(  # type: ignore[arg-type]
        P_ACT, 14, [_inc(5, 9, obra=100)], USUARIO)
    assert sesion.borradas == [b] and sesion.anadidas == []
    sesion = _SesionReemplazo([a])
    PgIncidenciaRepository(sesion).reemplazar(P_ACT, 14, [], USUARIO)  # type: ignore[arg-type]
    assert sesion.borradas == [a] and sesion.anadidas == []


def test_f030_r19_guardar_repo_entradas_var():
    from infrastructure.db.repositories import PgObraRepository

    sesion = _SesionInc()
    sesion.scalars = lambda stmt: (sesion.sentencias.append(stmt), _Filas([101]))[1]
    repo = PgObraRepository(sesion)  # type: ignore[arg-type]
    assert repo.entradas_var({100, 101}) == {101}
    assert _sql(sesion.sentencias[0]).startswith(
        "SELECT obra.ide FROM obra WHERE obra.ide IN (__[POSTCOMPILE_ide_1]) "
        "AND obra.registro_obra_ide IS NOT NULL")
    assert repo.entradas_var(set()) == set()
    assert len(sesion.sentencias) == 1


# ======================= deshacer y copias (T7) ========================= #
def _deshacer(uow, ide=14, usuario=USUARIO):
    from application.use_cases import DeshacerUltimaModificacion

    return DeshacerUltimaModificacion().ejecutar(uow, ANIO, MES, ide, usuario,
                                                 filtro=FILTRO)


def test_f030_r20_deshacer_incidencias_vuelve_al_snapshot_antes():
    uow = _uow_guardar()
    uow.incidencias.poner(14, _inc(5, 9, obra=100))
    _guardar(uow, [_e(101, "CIE", 1, 3)])
    lineas_antes = {k: list(v) for k, v in uow.lineas[P_ACT].items()}
    fila, _ = _deshacer(uow)
    assert _tramos(fila.incidencias) == [(100, "CIV", 5, 9)]
    assert uow.incidencias.reemplazos[-1] == (P_ACT, 14, USUARIO)
    assert uow.eventos.deshechos == {1}
    assert uow.lineas[P_ACT] == lineas_antes and uow.reemplazados == []
    assert fila.puede_deshacer is False


def test_f030_r20_deshacer_la_primera_incidencia_las_deja_vacias():
    uow = _uow_guardar()
    _guardar(uow, [_e(100, "CIV", 1, 3)])
    fila, _ = _deshacer(uow)
    assert fila.incidencias == ()


def test_f030_r20_deshacer_va_por_orden_sea_del_tipo_que_sea():
    """GUARDAR y luego INCIDENCIAS: el primer Ctrl+Z deshace las incidencias
    y no toca las líneas; el segundo, las líneas y no toca las incidencias."""
    from application.use_cases import GuardarAsignaciones

    uow = _uow_guardar()
    GuardarAsignaciones().ejecutar(
        uow, ANIO, MES, 14, [{"obra_ide": 100, "porcentaje": "100"}], USUARIO,
        filtro=FILTRO)
    _guardar(uow, [_e(101, "CIE", 1, 3)])
    fila, _ = _deshacer(uow)
    assert fila.incidencias == ()
    assert [(ln.obra_ide, ln.porcentaje) for ln in fila.lineas] == [
        (100, Decimal("100"))]
    uow.incidencias.poner(14, _inc(1, 3, obra=101, cod="CIE"))  # sin evento
    fila, _ = _deshacer(uow)                        # el GUARDAR
    assert fila.lineas == []
    assert _tramos(fila.incidencias) == [(101, "CIE", 1, 3)]


def test_f030_r20_deshacer_incidencias_ajeno_o_sin_pendiente():
    from domain.errors import DeshacerAjeno, NadaQueDeshacer

    uow = _uow_guardar()
    with pytest.raises(NadaQueDeshacer):
        _deshacer(uow)
    _guardar(uow, [_e(100, "CIV", 1, 3)], usuario="pablo@ruesma.es")
    with pytest.raises(DeshacerAjeno, match="pablo@ruesma.es"):
        _deshacer(uow)
    assert _tramos(uow.incidencias.de_trabajador(P_ACT, 14)) == [(100, "CIV", 1, 3)]
    assert uow.eventos.deshechos == set()


def test_f030_r20_deshacer_repo_lee_el_tipo_del_evento():
    from types import SimpleNamespace

    from infrastructure.db.repositories import PgEventoRepository

    class _S:
        def __init__(self, orm):
            self.orm = orm

        def scalars(self, stmt):
            return _Filas([self.orm])

    orm = SimpleNamespace(id=7, usuario="ana", snapshot_antes=[{"x": 1}],
                          tipo="INCIDENCIAS")
    pendiente = PgEventoRepository(_S(orm)).ultimo_pendiente(P_ACT, 14)  # type: ignore[arg-type]
    assert pendiente == EventoPendiente(7, "ana", [{"x": 1}], tipo="INCIDENCIAS")
    assert EventoPendiente(1, "a", []).tipo == "GUARDAR"


def _copias_uow() -> _UowInc:
    from tests.test_f024_cuadrante_empresa import P_ANT

    uow = _uow_guardar()
    uow.lineas[P_ANT] = {14: [_ln(101, "100")], 10: [_ln(100, "100")]}
    uow.incidencias.poner(14, _inc(1, 3, obra=101), periodo_id=P_ANT)
    uow.incidencias.poner(10, _inc(4, 6, obra=100), periodo_id=P_ACT)
    return uow


def _foto(uow) -> dict:
    return {k: list(v) for k, v in uow.incidencias.datos.items()}


def test_f030_r21_copias_f8_no_copia_ni_toca_incidencias():
    from application.use_cases import CopiarTrabajadorAnterior

    uow = _copias_uow()
    antes = _foto(uow)
    fila, *_ = CopiarTrabajadorAnterior().ejecutar(uow, ANIO, MES, 14, USUARIO,
                                                   filtro=FILTRO)
    assert [ln.obra_ide for ln in fila.lineas] == [101]
    assert fila.incidencias == ()
    assert _foto(uow) == antes and uow.incidencias.reemplazos == []


def test_f030_r21_copias_mes_no_copia_ni_toca_incidencias():
    from application.use_cases import CopiarPeriodoAnterior

    uow = _copias_uow()
    antes = _foto(uow)
    r = CopiarPeriodoAnterior().ejecutar(uow, ANIO, MES, USUARIO, filtro=FILTRO)
    assert r.trabajadores_copiados == 1
    assert _foto(uow) == antes and uow.incidencias.reemplazos == []


def test_f030_r21_copias_completar_no_toca_incidencias():
    from application.use_cases import CompletarHasta100

    uow = _copias_uow()
    antes = _foto(uow)
    resultados, _ = CompletarHasta100().ejecutar(uow, ANIO, MES, [14, 10], 101,
                                                 False, USUARIO, filtro=FILTRO)
    assert [r.resultado.value for r in resultados] == ["COMPLETADO", "YA_AL_100"]
    assert _foto(uow) == antes and uow.incidencias.reemplazos == []


def test_f030_r21_copias_f7_es_guardar_asignaciones_y_no_toca_incidencias():
    """F7 (copiar la fila de arriba) es un PUT de asignaciones del front."""
    from application.use_cases import GuardarAsignaciones

    uow = _copias_uow()
    antes = _foto(uow)
    fila, _ = GuardarAsignaciones().ejecutar(
        uow, ANIO, MES, 10, [{"obra_ide": 101, "porcentaje": "100"}], USUARIO,
        filtro=FILTRO)
    assert _tramos(fila.incidencias) == [(100, "CIV", 4, 6)]
    assert _foto(uow) == antes and uow.incidencias.reemplazos == []
