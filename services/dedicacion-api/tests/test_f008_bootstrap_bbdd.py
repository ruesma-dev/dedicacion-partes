# tests/test_f008_bootstrap_bbdd.py
"""F-008 · El arranque de dedicacion-api deja de crear bases y roles.

Hoy `infrastructure/db/database.py::asegurar_base_datos` conecta en CADA
arranque como **administrador del servidor** y ejecuta `CREATE ROLE` y
`CREATE DATABASE`. Contra `localhost` es una comodidad; contra
`psql-albaranes-rs9k2` —compartido con albaranes, partes, datamart y
postventa— es justo lo que el ecosistema prohíbe por escrito.

Trazabilidad con `specs/F-008-infra-azure/requirements.md`:

  - **R13**: no se ejecuta `CREATE DATABASE` ni `CREATE ROLE` al arrancar
    contra un servidor desplegado. Lo que decide es el conmutador, no que la
    función esté muerta: con el conmutador encendido el DDL sigue estando.
  - **R14**: existe `AUTO_CREATE_DATABASE`, y su valor por defecto es
    `false`. Una variable olvidada al desplegar hace lo prudente.
  - **R15**: con el conmutador apagado **ni siquiera se abre la conexión de
    administración**. No basta con saltarse el DDL: si no se abre la
    conexión, el servicio desplegado no necesita —ni puede filtrar— las
    credenciales de administrador del servidor compartido.
  - **R16**: si la base no existe y el bootstrap está apagado, el arranque
    falla con un mensaje que **nombra la base y el script que la crea**, en
    vez de con el error crudo del driver.

Nada de esto abre un socket: `psycopg.connect` se sustituye por un doble que
**falla si lo llaman**, el engine de SQLAlchemy es otro doble y los errores
del driver entran como dato. Los tests no llevan ni una credencial
(`docs/CONVENTIONS.md`, sección «Tests»).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Self

import psycopg
import pytest
from config.settings import Settings
from infrastructure.db import database
from infrastructure.db.database import (
    BaseDatosNoExiste,
    asegurar_base_datos,
    comprobar_base_datos,
    es_base_inexistente,
)

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]
FUENTE_MAIN = RAIZ_SERVICIO / "main.py"
ENV_EXAMPLE = RAIZ_SERVICIO / ".env.example"

#: El script que crea la base, una sola vez y ejecutado por una persona. Su
#: nombre tiene que aparecer en el error: es la única pista útil para quien se
#: encuentra el servicio caído en Azure.
SCRIPT_DE_ALTA = "infra/crear_base_dedicacion.ps1"


# --- Dobles de prueba (ninguno toca la red) ---------------------------------


class _ResultadoFalso:
    """Lo que devuelve `conn.execute(...)`: solo sabe hacer `fetchone`."""

    def __init__(self, fila: tuple[Any, ...] | None) -> None:
        self._fila = fila

    def fetchone(self) -> tuple[Any, ...] | None:
        return self._fila


class _ConexionFalsa:
    """Conexión psycopg de mentira: apunta lo que se le pide y responde."""

    def __init__(self, respuestas: list[tuple[Any, ...] | None]) -> None:
        self._respuestas = list(respuestas)
        self.sentencias: list[Any] = []

    def execute(self, consulta: Any, params: Any = None) -> _ResultadoFalso:
        self.sentencias.append(consulta)
        fila = self._respuestas.pop(0) if self._respuestas else None
        return _ResultadoFalso(fila)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_excepcion: object) -> bool:
        return False


class _EngineFalso:
    """Engine de SQLAlchemy de mentira: conecta, o revienta como se le diga."""

    def __init__(self, error: BaseException | None = None) -> None:
        self._error = error
        self.conexiones = 0

    def connect(self) -> _ConexionFalsa:
        self.conexiones += 1
        if self._error is not None:
            raise self._error
        return _ConexionFalsa([])


def ajustes(**cambios: Any) -> Settings:
    """Settings de laboratorio: sin `.env` y sin una sola credencial real."""
    base: dict[str, Any] = {
        "pg_host": "servidor-de-mentira",
        "pg_db": "dedicacion",
        "pg_user": "dedicacion_app",
        "pg_admin_user": "administrador",
    }
    base.update(cambios)
    return Settings(_env_file=None, **base)


# --- R14 · el conmutador y su valor por defecto -----------------------------


def test_f008_r14_auto_create_database_por_defecto_es_false():
    """Seguro por defecto: una variable olvidada al desplegar no crea nada.

    Es la mitad del requisito que de verdad protege el servidor compartido:
    si el defecto fuese `True`, desplegar sin acordarse de la variable
    volvería a poner un servicio ajeno a crear bases y roles en producción.
    """
    assert ajustes().auto_create_database is False


def test_f008_r14_auto_create_database_se_enciende_por_entorno(monkeypatch):
    """En local sí se quiere: `AUTO_CREATE_DATABASE=true` lo enciende."""
    monkeypatch.setenv("AUTO_CREATE_DATABASE", "true")

    assert Settings(_env_file=None).auto_create_database is True


def test_f008_r14_el_env_example_local_lo_trae_encendido():
    """El ejemplo es para trabajar en el portátil, donde crear la base ayuda.

    El valor peligroso vive en el fichero que NO se despliega; el valor
    prudente es el del código.
    """
    texto = ENV_EXAMPLE.read_text(encoding="utf-8")

    assert "AUTO_CREATE_DATABASE=true" in texto


# --- R13 y R15 · el cortocircuito -------------------------------------------


def test_f008_r15_apagado_no_abre_la_conexion_de_administracion(monkeypatch):
    """Con el conmutador apagado, `psycopg.connect` no se llama NUNCA.

    Si se llamara, el Container App necesitaría la contraseña del
    administrador del servidor compartido, y lo que no se guarda no se
    filtra (`design.md` §5).
    """
    intentos: list[Any] = []

    def _explota(*args: Any, **kwargs: Any) -> None:
        intentos.append(args)
        raise AssertionError(
            "asegurar_base_datos abrió la conexión de administración con "
            "AUTO_CREATE_DATABASE apagado"
        )

    monkeypatch.setattr(psycopg, "connect", _explota)

    asegurar_base_datos(ajustes(auto_create_database=False))

    assert intentos == []


def test_f008_r13_apagado_no_ejecuta_ninguna_sentencia(monkeypatch):
    """Ni `CREATE ROLE` ni `CREATE DATABASE`: ni una sentencia siquiera.

    El doble de conexión apunta todo lo que se le pide; con el conmutador
    apagado no debe llegarle nada, porque no debe llegar a existir.
    """
    conexion = _ConexionFalsa([(1,), (1,)])
    monkeypatch.setattr(psycopg, "connect", lambda *_a, **_k: conexion)

    asegurar_base_datos(ajustes(auto_create_database=False))

    assert conexion.sentencias == []


def test_f008_r13_encendido_sigue_haciendo_el_bootstrap(monkeypatch):
    """Lo que apaga el DDL es el conmutador, no que la función esté muerta.

    Sin este test, borrar el cuerpo entero de `asegurar_base_datos` pasaría
    los demás y rompería el arranque en local, que es donde el bootstrap se
    usa a diario.
    """
    conexion = _ConexionFalsa([(1,), (1,)])
    abiertas: list[dict[str, Any]] = []

    def _conectar(*_args: Any, **kwargs: Any) -> _ConexionFalsa:
        abiertas.append(kwargs)
        return conexion

    monkeypatch.setattr(psycopg, "connect", _conectar)

    asegurar_base_datos(ajustes(auto_create_database=True))

    assert len(abiertas) == 1
    assert conexion.sentencias, "con el conmutador encendido sí se consulta"


def test_f008_r15_el_cortocircuito_deja_rastro_en_el_log(monkeypatch, caplog):
    """Un servicio que no hace algo tiene que decir que no lo hace.

    Sin esta línea, quien mire los logs de un arranque que falla más abajo no
    tiene forma de saber si el bootstrap se saltó a propósito.
    """
    monkeypatch.setattr(psycopg, "connect", _no_llamar)

    with caplog.at_level("INFO", logger=database.__name__):
        asegurar_base_datos(ajustes(auto_create_database=False))

    registrado = "\n".join(r.getMessage() for r in caplog.records)
    assert "AUTO_CREATE_DATABASE" in registrado
    assert "dedicacion" in registrado


def _no_llamar(*_args: Any, **_kwargs: Any) -> None:
    raise AssertionError("no se debía abrir ninguna conexión")


# --- R16 · el error con mensaje útil ----------------------------------------


def test_f008_r16_reconoce_el_error_del_driver_por_tipo():
    """`psycopg.errors.InvalidCatalogName` es el caso limpio: base ausente."""
    fallo = psycopg.errors.InvalidCatalogName("lo que sea")

    assert es_base_inexistente(fallo, "dedicacion") is True


def test_f008_r16_reconoce_el_error_por_el_texto_del_driver():
    """SQLAlchemy envuelve el error del driver: hay que mirar el texto."""
    fallo = RuntimeError('FATAL: database "dedicacion" does not exist')

    assert es_base_inexistente(fallo, "dedicacion") is True


def test_f008_r16_reconoce_el_error_encadenado_como_causa():
    """El caso real: `sqlalchemy.exc.OperationalError` con el driver debajo."""
    original = psycopg.errors.InvalidCatalogName("la de abajo")
    envuelto = RuntimeError("(psycopg.errors.InvalidCatalogName)")
    envuelto.__cause__ = original

    assert es_base_inexistente(envuelto, "dedicacion") is True


def test_f008_r16_no_confunde_la_base_de_otro_proyecto():
    """El servidor es compartido: que falte `partes` no es asunto nuestro.

    Traducir ese error a «crea la base `dedicacion`» mandaría a quien
    diagnostica en la dirección contraria.
    """
    fallo = RuntimeError('FATAL: database "partes" does not exist')

    assert es_base_inexistente(fallo, "dedicacion") is False


def test_f008_r16_un_fallo_de_red_no_es_una_base_que_falta():
    """Servidor caído, contraseña mala o TLS rechazado no se disfrazan."""
    fallo = RuntimeError("connection to server failed: timeout expired")

    assert es_base_inexistente(fallo, "dedicacion") is False


def test_f008_r16_el_arranque_falla_nombrando_la_base_y_el_script():
    """El mensaje tiene que servir para arreglarlo, no solo para asustar."""
    original = psycopg.errors.InvalidCatalogName("no existe")
    engine = _EngineFalso(error=original)

    with pytest.raises(BaseDatosNoExiste) as capturado:
        comprobar_base_datos(engine, ajustes(auto_create_database=False))

    mensaje = str(capturado.value)
    assert "dedicacion" in mensaje
    assert SCRIPT_DE_ALTA in mensaje
    assert capturado.value.__cause__ is original


def test_f008_r16_los_demas_errores_de_conexion_pasan_tal_cual():
    """No se envuelve lo que no se entiende: se deja subir el error real."""
    original = RuntimeError("password authentication failed")
    engine = _EngineFalso(error=original)

    with pytest.raises(RuntimeError) as capturado:
        comprobar_base_datos(engine, ajustes())

    assert capturado.value is original


def test_f008_r16_con_la_base_creada_no_estorba():
    """El camino feliz: se abre la conexión, no se lanza nada y se sigue."""
    engine = _EngineFalso()

    comprobar_base_datos(engine, ajustes())

    assert engine.conexiones == 1


def test_f008_r16_el_arranque_comprueba_la_base_antes_de_sincronizar():
    """`main.py` es quien tiene que traducir el fallo, y en el orden bueno.

    Comprobar después de `sincronizar_esquema` no serviría de nada: el DDL
    reventaría antes con el error crudo del driver.
    """
    fuente = FUENTE_MAIN.read_text(encoding="utf-8")

    assert "comprobar_base_datos" in fuente
    assert fuente.index("comprobar_base_datos(") > fuente.index("crear_engine(")
    assert fuente.index("comprobar_base_datos(") < fuente.index("sincronizar_esquema(")
