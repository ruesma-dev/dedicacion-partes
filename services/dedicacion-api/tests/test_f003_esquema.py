# tests/test_f003_esquema.py
"""Tests offline de F-003: el ORM como única fuente de verdad del esquema.

Trazabilidad con los requisitos EARS de
`specs/F-003-orm-columnas-sigrid/requirements.md`:

  - R1/R5/R6: las seis columnas de traza están en `AsignacionORM` con el tipo
    y la nulabilidad exactos, compilados con el dialecto PostgreSQL.
  - R2: no queda DDL escrito a mano en `application/registro_sigrid.py`.
  - R3/R17: el DDL complementario se DERIVA del ORM y coincide, columna a
    columna, con lo que el código de traza escribe.
  - R4: construir `RegistroSigrid` no ejecuta ninguna sentencia.
  - R7/R14: las tres ramas de `_trazar` y los truncados a 300 y a 64.
  - R8-R13: el mecanismo de `alters_faltantes` según el estado de la base.
  - R16: no hay `SELECT *` ni `INSERT` a mano sobre `asignacion`.

Nada de esto abre un socket ni una conexión: SQLAlchemy compila DDL y DML
contra un dialecto sin motor, el estado de la base entra como dato y las
sesiones son dobles de prueba. Lo que exige una base real es la verificación
MANUAL (humano) T8 de `tasks.md`.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateColumn

from application.registro_sigrid import RegistroSigrid
from infrastructure.db.orm_models import AsignacionORM, Base

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]
FUENTE_REGISTRO = RAIZ_SERVICIO / "application" / "registro_sigrid.py"
FUENTE_MAIN = RAIZ_SERVICIO / "main.py"

DIALECTO = postgresql.dialect()

#: Las seis columnas de traza y el tipo PostgreSQL que deben emitir, según la
#: tabla de R5. Es la referencia INDEPENDIENTE del código: si alguien toca el
#: ORM sin tocar esta tabla (o al revés), los tests de R5 y R17 lo cazan.
COLUMNAS_TRAZA: dict[str, str] = {
    "sigrid_estado": "VARCHAR(16)",
    "sigrid_parte_cod": "VARCHAR(24)",
    "sigrid_hmores_ide": "INTEGER",
    "sigrid_motivo": "VARCHAR(300)",
    "sigrid_registrado_at_utc": "TIMESTAMP WITH TIME ZONE",
    "sigrid_registrado_by": "VARCHAR(64)",
}

#: Las columnas que `asignacion` ya tenía antes de F-003. Son OCHO, no diez:
#: `requirements.md` R8 dice «las diez actuales más las seis» y «dieciséis»,
#: pero contadas en `orm_models.py` son ocho, así que el total queda en
#: catorce. Es un desliz aritmético de la prosa de la spec, no del diseño: la
#: tabla normativa de R5 sigue listando seis columnas nuevas. Anotado en
#: `progress/impl_F-003.md`.
COLUMNAS_PREVIAS = (
    "id", "periodo_id", "trabajador_ide", "obra_ide", "es_postventa",
    "porcentaje", "actualizado_en", "actualizado_por",
)


@pytest.fixture()
def esquema():
    """El módulo bajo prueba.

    Se importa dentro de una fixture, y no en la cabecera, para que los tests
    del ORM (R1, R5, R6) se puedan ejecutar aunque `esquema.py` todavía no
    exista: es lo que separa la fase RED de T1 de la de T3.
    """
    from infrastructure.db import esquema as modulo

    return modulo


# --- Dobles de prueba -------------------------------------------------------


class _SesionFalsa:
    """Sesión que apunta lo que le mandan ejecutar en vez de ejecutarlo."""

    def __init__(self, registro: list[Any]) -> None:
        self.registro = registro
        self.commits = 0

    def __enter__(self) -> "_SesionFalsa":
        return self

    def __exit__(self, *_excepcion: object) -> bool:
        return False

    def execute(self, sentencia: Any, *_args: object, **_kwargs: object) -> None:
        self.registro.append(sentencia)

    def commit(self) -> None:
        self.commits += 1


class _FabricaSesiones:
    """`session_factory` de mentira que cuenta cuántas sesiones se abren."""

    def __init__(self) -> None:
        self.sentencias: list[Any] = []
        self.aperturas = 0

    def __call__(self) -> _SesionFalsa:
        self.aperturas += 1
        return _SesionFalsa(self.sentencias)


def _sql(sentencia: Any) -> str:
    """SQL compilado con el dialecto PostgreSQL, sin conexión."""
    return str(sentencia.compile(dialect=DIALECTO))


def _valores(sentencia: Any) -> dict[str, Any]:
    """Columnas que fija el SET de un UPDATE, con su valor.

    Los binds del WHERE llevan sufijo numérico (`id_1`, `sigrid_estado_1`), así
    que filtrar por nombre exacto de columna deja solo el SET.
    """
    compilada = sentencia.compile(dialect=DIALECTO)
    nombres = {columna.name for columna in AsignacionORM.__table__.columns}
    return {
        clave: valor
        for clave, valor in compilada.params.items()
        if clave in nombres
    }


def _trazar(respuesta: dict[str, Any], usuario: str = "pgris") -> list[Any]:
    """Ejecuta `_trazar` sobre sesiones falsas y devuelve lo que emitió."""
    fabrica = _FabricaSesiones()
    registro = RegistroSigrid(fabrica, transfer=object())
    registro._trazar(respuesta, usuario)
    return fabrica.sentencias


# --- R1, R5, R6: el ORM declara las seis columnas ---------------------------


@pytest.mark.parametrize("nombre", list(COLUMNAS_TRAZA))
def test_f003_r1_la_columna_esta_declarada_en_el_orm(nombre: str) -> None:
    assert hasattr(AsignacionORM, nombre), (
        f"AsignacionORM no declara {nombre}: sigue habiendo dos verdades del "
        "esquema (ORM y DDL escrito a mano)"
    )
    assert nombre in AsignacionORM.__table__.columns


@pytest.mark.parametrize(("nombre", "tipo"), list(COLUMNAS_TRAZA.items()))
def test_f003_r5_el_tipo_compilado_es_el_de_la_tabla(nombre: str, tipo: str) -> None:
    """El tipo que PostgreSQL vería, comparado como cadena exacta."""
    columna = AsignacionORM.__table__.columns[nombre]
    assert columna.type.compile(dialect=DIALECTO) == tipo


@pytest.mark.parametrize("nombre", list(COLUMNAS_TRAZA))
def test_f003_r5_la_columna_es_nulable_y_sin_default(nombre: str) -> None:
    """Una asignación recién creada no está registrada en Sigrid: la ausencia
    de valor es el estado inicial legítimo (R5, y lo que permite el R16)."""
    columna = AsignacionORM.__table__.columns[nombre]
    assert columna.nullable is True
    assert columna.default is None
    assert columna.server_default is None
    assert columna.primary_key is False


def test_f003_r8_la_tabla_queda_con_las_previas_mas_las_seis() -> None:
    """Las de antes siguen ahí: F-003 añade, no reordena ni quita."""
    presentes = {columna.name for columna in AsignacionORM.__table__.columns}
    assert presentes == set(COLUMNAS_PREVIAS) | set(COLUMNAS_TRAZA)


def test_f003_r6_la_marca_de_tiempo_lleva_zona_horaria() -> None:
    """`TIMESTAMP WITH TIME ZONE`, no `TIMESTAMP` a secas: si la columna fuera
    naíf, la hora escrita desde otro huso quedaría desplazada sin aviso."""
    columna = AsignacionORM.__table__.columns["sigrid_registrado_at_utc"]
    assert columna.type.timezone is True


# --- R17: el DDL derivado contra lo que el código de traza espera ------------


def test_f003_r17_el_orm_tiene_exactamente_las_columnas_de_traza() -> None:
    """Ni una de más ni una de menos que la tabla de referencia."""
    en_el_orm = {
        columna.name
        for columna in AsignacionORM.__table__.columns
        if columna.name.startswith("sigrid_")
    }
    assert en_el_orm == set(COLUMNAS_TRAZA)


def test_f003_r17_la_traza_escribe_exactamente_esas_columnas() -> None:
    """El otro lado del contrato: los nombres `sigrid_*` que menciona
    `registro_sigrid.py` son los mismos que declara el ORM. Añadir una columna
    a un lado y no al otro rompe aquí."""
    fuente = FUENTE_REGISTRO.read_text(encoding="utf-8")
    mencionadas = set(re.findall(r"\bsigrid_[a-z_]+\b", fuente))
    assert mencionadas == set(COLUMNAS_TRAZA)


def test_f003_r17_el_ddl_derivado_es_el_esperado_caracter_a_caracter(
    esquema: Any,
) -> None:
    """La pieza central: sobre una base con la tabla pero sin las seis
    columnas, el DDL derivado del ORM es exactamente estas seis sentencias, en
    el orden de declaración."""
    esperado = [
        f"ALTER TABLE asignacion ADD COLUMN IF NOT EXISTS {nombre} {tipo}"
        for nombre, tipo in COLUMNAS_TRAZA.items()
    ]
    obtenido = esquema.alters_faltantes(Base.metadata, _base_sin_traza())
    assert obtenido == esperado


def _base_sin_traza() -> dict[str, set[str]]:
    """Estado de una base con `asignacion` creada antes de F-003."""
    return {
        "asignacion": {
            columna.name
            for columna in AsignacionORM.__table__.columns
            if not columna.name.startswith("sigrid_")
        }
    }


def _base_al_dia() -> dict[str, set[str]]:
    """Estado de una base con TODAS las tablas y columnas del ORM."""
    return {
        tabla.name: {columna.name for columna in tabla.columns}
        for tabla in Base.metadata.tables.values()
    }


# --- R3: el texto del tipo sale del ORM, no de una lista paralela -----------


@pytest.mark.parametrize(("nombre", "tipo"), list(COLUMNAS_TRAZA.items()))
def test_f003_r3_ddl_add_column_compila_una_columna(
    esquema: Any, nombre: str, tipo: str
) -> None:
    tabla = AsignacionORM.__table__
    sentencia = esquema.ddl_add_column(tabla, tabla.columns[nombre])
    assert sentencia == (
        f"ALTER TABLE asignacion ADD COLUMN IF NOT EXISTS {nombre} {tipo}"
    )


def test_f003_r3_ddl_add_column_arrastra_default_y_not_null(esquema: Any) -> None:
    """El texto sale de compilar la columna, no de escribirlo a mano: una
    columna con `server_default` y `NOT NULL` los arrastra sola."""
    metadata = MetaData()
    tabla = Table(
        "ejemplo",
        metadata,
        Column("marca", DateTime(timezone=True), nullable=False,
               server_default=func.now()),
    )
    assert esquema.ddl_add_column(tabla, tabla.columns["marca"]) == (
        "ALTER TABLE ejemplo ADD COLUMN IF NOT EXISTS marca "
        "TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL"
    )


# --- R8-R13: el mecanismo, por estado de la base ---------------------------


def test_f003_r8_tabla_ausente_no_genera_ningun_alter(esquema: Any) -> None:
    """Base limpia: la tabla la crea `create_all` con las dieciséis columnas;
    aquí no se emite nada."""
    assert esquema.alters_faltantes(Base.metadata, {}) == []


def test_f003_r9_base_al_dia_no_genera_ningun_alter(esquema: Any) -> None:
    """El caso del entorno local de hoy: no debe pasar nada."""
    assert esquema.alters_faltantes(Base.metadata, _base_al_dia()) == []


def test_f003_r10_se_emite_una_sentencia_por_columna_faltante(
    esquema: Any,
) -> None:
    existentes = _base_al_dia()
    existentes["asignacion"] -= {"sigrid_motivo", "sigrid_registrado_by"}
    assert esquema.alters_faltantes(Base.metadata, existentes) == [
        "ALTER TABLE asignacion ADD COLUMN IF NOT EXISTS "
        "sigrid_motivo VARCHAR(300)",
        "ALTER TABLE asignacion ADD COLUMN IF NOT EXISTS "
        "sigrid_registrado_by VARCHAR(64)",
    ]


def test_f003_r11_aplicar_el_ddl_lo_deja_todo_al_dia(esquema: Any) -> None:
    """Idempotencia: tras la primera pasada, la segunda no encuentra nada.

    Se simula el efecto del DDL sobre la base añadiendo las columnas emitidas
    al estado de partida.
    """
    existentes = _base_sin_traza()
    primera = esquema.alters_faltantes(Base.metadata, existentes)
    assert len(primera) == len(COLUMNAS_TRAZA)
    existentes["asignacion"] |= set(COLUMNAS_TRAZA)
    assert esquema.alters_faltantes(Base.metadata, existentes) == []


def test_f003_r12_columna_not_null_sin_default_aborta(esquema: Any) -> None:
    """No se adivina un valor de relleno para una tabla con filas: se para."""
    metadata = MetaData()
    Table(
        "asignacion",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("obligatoria", String(8), nullable=False),
    )
    with pytest.raises(esquema.EsquemaNoDerivable) as fallo:
        esquema.alters_faltantes(metadata, {"asignacion": {"id"}})
    mensaje = str(fallo.value)
    assert "asignacion" in mensaje
    assert "obligatoria" in mensaje


def test_f003_r12_columna_not_null_con_default_si_se_puede_anadir(
    esquema: Any,
) -> None:
    """La otra mitad de la condición: con `server_default` PostgreSQL sabe qué
    poner en las filas existentes, así que no hay nada que decidir."""
    metadata = MetaData()
    Table(
        "asignacion",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("obligatoria", String(8), nullable=False, server_default="x"),
    )
    assert esquema.alters_faltantes(metadata, {"asignacion": {"id"}}) == [
        "ALTER TABLE asignacion ADD COLUMN IF NOT EXISTS "
        "obligatoria VARCHAR(8) DEFAULT 'x' NOT NULL"
    ]


def test_f003_r13_el_ddl_derivado_solo_anade_columnas(esquema: Any) -> None:
    """Límite declarado: ni `DROP`, ni `ALTER COLUMN`, ni `ADD CONSTRAINT`.

    Se le dan dos tablas a las que les falta todo menos la clave primaria (y
    que tienen además un índice y una restricción única declarados), para que
    el mecanismo emita cuanto es capaz de emitir. Nada de lo que emite sale de
    la forma `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.
    """
    metadata = MetaData()
    Table(
        "uno",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("texto", String(10)),
        Column("marca", DateTime(timezone=True), nullable=False,
               server_default=func.now()),
    )
    Table(
        "dos",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("n", Integer),
    )
    sentencias = esquema.alters_faltantes(
        metadata, {"uno": {"id"}, "dos": {"id"}}
    ) + esquema.alters_faltantes(Base.metadata, _base_sin_traza())
    assert len(sentencias) == 3 + len(COLUMNAS_TRAZA)
    for sentencia in sentencias:
        assert sentencia.startswith("ALTER TABLE ")
        assert " ADD COLUMN IF NOT EXISTS " in sentencia
        assert "DROP" not in sentencia
        assert "ALTER COLUMN" not in sentencia
        assert "ADD CONSTRAINT" not in sentencia


def test_f003_r13_una_columna_sobrante_en_la_base_no_se_toca(
    esquema: Any,
) -> None:
    """Lo que hay de más en la base y no está en el ORM se deja en paz."""
    existentes = _base_al_dia()
    existentes["asignacion"] |= {"columna_de_otra_epoca"}
    assert esquema.alters_faltantes(Base.metadata, existentes) == []


# --- R4: el arranque, y solo el arranque, ejecuta DDL -----------------------


def test_f003_r4_construir_registro_sigrid_no_ejecuta_nada() -> None:
    """El constructor era quien disparaba los `ALTER`: importar y construir la
    app abría una conexión a PostgreSQL. Ya no."""
    fabrica = _FabricaSesiones()
    RegistroSigrid(fabrica, transfer=object())
    assert fabrica.aperturas == 0
    assert fabrica.sentencias == []


def test_f003_r4_main_sincroniza_el_esquema_al_arrancar() -> None:
    """El DDL complementario vive en `main.py`, no en la capa `application`."""
    fuente = FUENTE_MAIN.read_text(encoding="utf-8")
    assert "sincronizar_esquema(engine)" in fuente
    assert "create_all" not in fuente


def test_f003_r4_sincronizar_esquema_crea_tablas_antes_de_inspeccionar(
    esquema: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Orden y efecto de la única función impura, sin base de datos.

    `create_all` debe ir ANTES de mirar qué columnas hay: si no, una tabla
    recién creada se inspeccionaría como inexistente. Después se ejecuta una
    sentencia por cada `ALTER` derivado, dentro de una transacción.
    """
    orden: list[str] = []
    ejecutadas: list[str] = []

    class _Conexion:
        def __enter__(self) -> "_Conexion":
            return self

        def __exit__(self, *_excepcion: object) -> bool:
            return False

        def execute(self, sentencia: Any) -> None:
            ejecutadas.append(str(sentencia))

    class _MotorFalso:
        def begin(self) -> _Conexion:
            orden.append("begin")
            return _Conexion()

    def _crear_todas(_motor: object) -> None:
        orden.append("create_all")

    def _columnas(_motor: object) -> dict[str, set[str]]:
        orden.append("inspeccion")
        return _base_sin_traza()

    monkeypatch.setattr(Base.metadata, "create_all", _crear_todas)
    monkeypatch.setattr(esquema, "columnas_existentes", _columnas)

    aplicadas = esquema.sincronizar_esquema(_MotorFalso())

    assert orden == ["create_all", "inspeccion", "begin"]
    assert aplicadas == [
        f"ALTER TABLE asignacion ADD COLUMN IF NOT EXISTS {nombre} {tipo}"
        for nombre, tipo in COLUMNAS_TRAZA.items()
    ]
    assert ejecutadas == aplicadas


def test_f003_r9_sincronizar_esquema_no_ejecuta_nada_si_no_falta_nada(
    esquema: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """El caso del entorno local: cero sentencias DDL emitidas."""
    ejecutadas: list[str] = []

    class _Conexion:
        def __enter__(self) -> "_Conexion":
            return self

        def __exit__(self, *_excepcion: object) -> bool:
            return False

        def execute(self, sentencia: Any) -> None:
            ejecutadas.append(str(sentencia))

    class _MotorFalso:
        def begin(self) -> _Conexion:
            return _Conexion()

    monkeypatch.setattr(Base.metadata, "create_all", lambda _motor: None)
    monkeypatch.setattr(esquema, "columnas_existentes", lambda _motor: _base_al_dia())

    assert esquema.sincronizar_esquema(_MotorFalso()) == []
    assert ejecutadas == []


def test_f003_r8_columnas_existentes_radiografia_la_base(
    esquema: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """La lectura del estado real, con un inspector de mentira."""

    class _Inspector:
        def get_table_names(self) -> list[str]:
            return ["asignacion", "periodo"]

        def get_columns(self, tabla: str) -> list[dict[str, str]]:
            columnas = {"asignacion": ["id", "sigrid_estado"], "periodo": ["id"]}
            return [{"name": nombre} for nombre in columnas[tabla]]

    monkeypatch.setattr(esquema, "inspect", lambda _motor: _Inspector())
    assert esquema.columnas_existentes(object()) == {
        "asignacion": {"id", "sigrid_estado"},
        "periodo": {"id"},
    }


# --- R2: no queda DDL escrito a mano en la capa `application` ---------------


@pytest.mark.parametrize("prohibido", ["ALTER TABLE", "_ALTERS", "text("])
def test_f003_r2_el_registro_no_contiene_ddl_ni_sql_crudo(prohibido: str) -> None:
    """Guardia anti-regresión de la avería que en `partes` costó la F-010."""
    fuente = FUENTE_REGISTRO.read_text(encoding="utf-8")
    assert prohibido not in fuente


def test_f003_r16_el_servicio_no_tiene_select_estrella() -> None:
    """Un `SELECT *` reintroduciría el acoplamiento al orden de columnas."""
    paquetes = ("domain", "application", "infrastructure", "interface_adapters")
    fuentes = [
        ruta
        for paquete in paquetes
        for ruta in (RAIZ_SERVICIO / paquete).rglob("*.py")
    ]
    assert fuentes, "no se encontró ningún fuente que revisar"
    for ruta in fuentes:
        texto = ruta.read_text(encoding="utf-8").upper()
        assert "SELECT *" not in texto, f"{ruta.name} usa SELECT *"


# --- R7, R14: las tres ramas de la traza ------------------------------------


def test_f003_r14_rama_escritas_fija_las_seis_columnas() -> None:
    antes = datetime.now(timezone.utc)
    sentencias = _trazar(
        {"escritas": [{"registro_id": 11, "parte_cod": "P-1", "hmores_ide": 7}]},
        usuario="pgris",
    )
    assert len(sentencias) == 1
    valores = _valores(sentencias[0])
    marca = valores.pop("sigrid_registrado_at_utc")
    assert valores == {
        "sigrid_estado": "registrado",
        "sigrid_parte_cod": "P-1",
        "sigrid_hmores_ide": 7,
        "sigrid_motivo": None,
        "sigrid_registrado_by": "pgris",
    }
    assert _sql(sentencias[0]).endswith("WHERE asignacion.id = %(id_1)s")
    # R6: la marca es consciente de zona horaria y está en UTC.
    assert marca.tzinfo is not None
    assert marca.utcoffset() == timedelta(0)
    assert marca >= antes


def test_f003_r14_rama_ya_registradas_solo_asciende_el_estado() -> None:
    """Solo el estado, y solo si aún no era `registrado`: no se pisa la marca
    de tiempo de quien lo registró de verdad."""
    sentencias = _trazar({"ya_registradas": [3]})
    assert len(sentencias) == 1
    assert _valores(sentencias[0]) == {"sigrid_estado": "registrado"}
    assert "IS DISTINCT FROM" in _sql(sentencias[0])


def test_f003_r14_rama_omitidas_guarda_el_motivo() -> None:
    sentencias = _trazar(
        {"omitidas": [{"registro_id": 5, "motivo": "sin parte abierto"}]}
    )
    assert len(sentencias) == 1
    assert _valores(sentencias[0]) == {
        "sigrid_estado": "omitido",
        "sigrid_motivo": "sin parte abierto",
    }


def test_f003_r14_omitida_sin_motivo_guarda_cadena_vacia_no_null() -> None:
    """`(motivo or "")`: sin motivo se escribe cadena vacía, no `None`."""
    sentencias = _trazar({"omitidas": [{"registro_id": 5}]})
    assert _valores(sentencias[0])["sigrid_motivo"] == ""


def test_f003_r14_las_tres_ramas_conviven_en_una_sola_sesion() -> None:
    """Una respuesta completa emite las tres sentencias y hace un solo commit."""
    fabrica = _FabricaSesiones()
    registro = RegistroSigrid(fabrica, transfer=object())
    registro._trazar(
        {
            "escritas": [{"registro_id": 1, "parte_cod": "P", "hmores_ide": 2}],
            "ya_registradas": [3],
            "omitidas": [{"registro_id": 4, "motivo": "m"}],
        },
        "pgris",
    )
    assert fabrica.aperturas == 1
    assert len(fabrica.sentencias) == 3


def test_f003_r14_respuesta_vacia_no_emite_ninguna_sentencia() -> None:
    assert _trazar({}) == []


@pytest.mark.parametrize("longitud", [300, 301, 900])
def test_f003_r14_el_motivo_se_trunca_a_300(longitud: int) -> None:
    """`sigrid_motivo` es `VARCHAR(300)`: pasarse aborta la transacción de
    traza en PostgreSQL. El corte es exactamente 300, ni 299 ni 301."""
    sentencias = _trazar(
        {"omitidas": [{"registro_id": 5, "motivo": "x" * longitud}]}
    )
    escrito = _valores(sentencias[0])["sigrid_motivo"]
    assert escrito == "x" * min(longitud, 300)
    assert len(escrito) == min(longitud, 300)


@pytest.mark.parametrize("longitud", [64, 65, 200])
def test_f003_r7_el_usuario_se_trunca_a_64(longitud: int) -> None:
    """`sigrid_registrado_by` es `VARCHAR(64)`. Un usuario de Easy Auth largo
    no puede tumbar la traza de un registro que ya se hizo en Sigrid."""
    sentencias = _trazar(
        {"escritas": [{"registro_id": 1, "parte_cod": "P", "hmores_ide": 2}]},
        usuario="u" * longitud,
    )
    escrito = _valores(sentencias[0])["sigrid_registrado_by"]
    assert escrito == "u" * min(longitud, 64)
    assert len(escrito) == min(longitud, 64)


def test_f003_r7_usuario_vacio_no_revienta() -> None:
    sentencias = _trazar(
        {"escritas": [{"registro_id": 1, "parte_cod": "P", "hmores_ide": 2}]},
        usuario="",
    )
    assert _valores(sentencias[0])["sigrid_registrado_by"] == ""


def test_f003_r5_el_parte_cod_no_se_trunca() -> None:
    """Decisión D2: el código de parte NO se trunca. Si un día no cupiera en
    `VARCHAR(24)` preferimos un error ruidoso a un código mutilado."""
    largo = "P" * 40
    sentencias = _trazar(
        {"escritas": [{"registro_id": 1, "parte_cod": largo, "hmores_ide": 2}]}
    )
    assert _valores(sentencias[0])["sigrid_parte_cod"] == largo


# --- Coherencia entre el tipo declarado y lo que la traza escribe -----------


def test_f003_r5_los_recortes_coinciden_con_las_longitudes_del_orm() -> None:
    """Cierra el círculo: los cortes de `_trazar` no son números sueltos, son
    la longitud de la columna. Si alguien cambia el `VARCHAR`, esto avisa."""
    columnas = AsignacionORM.__table__.columns
    assert columnas["sigrid_motivo"].type.length == 300
    assert columnas["sigrid_registrado_by"].type.length == 64
    fuente = FUENTE_REGISTRO.read_text(encoding="utf-8")
    assert "[:300]" in fuente
    assert "[:64]" in fuente


def test_f003_r3_el_ddl_derivado_usa_el_compilador_de_sqlalchemy(
    esquema: Any,
) -> None:
    """R3 literal: el texto del tipo sale de compilar la columna del ORM, no de
    una lista de tipos escrita por una persona. Se comprueba comparando con la
    compilación hecha aquí mismo, por separado."""
    tabla = AsignacionORM.__table__
    for nombre in COLUMNAS_TRAZA:
        definicion = CreateColumn(tabla.columns[nombre]).compile(
            dialect=DIALECTO
        ).string
        assert esquema.ddl_add_column(tabla, tabla.columns[nombre]) == (
            f"ALTER TABLE asignacion ADD COLUMN IF NOT EXISTS {definicion}"
        )
