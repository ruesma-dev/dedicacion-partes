# tests/test_f008_identidad.py
"""F-008 · La identidad del usuario, de Easy Auth hasta la api (R11, R12).

El front es el único servicio expuesto a Internet y el único punto donde la
identidad existe de verdad: Easy Auth (Entra) pone
`X-MS-CLIENT-PRINCIPAL-NAME` y el proxy la traduce a `X-Usuario` para la
auditoría del backend (tabla `evento`). No hay ningún otro camino:

    Entra -> Easy Auth -> X-MS-CLIENT-PRINCIPAL-NAME
                             -> _usuario() -> X-Usuario -> dedicacion-api

Lo que este fichero fija, y por qué importa:

  - **R11**: la cabecera de Easy Auth se propaga como `X-Usuario`, y sin ella
    se usa `DEFAULT_USER`.
  - **R11 (la otra mitad)**: la cabecera `X-Usuario` que llegue **de fuera**
    se descarta. El proxy la escribe él, no la reenvía. Si la reenviara,
    cualquiera con sesión podría firmar la auditoría con el nombre de otro.
  - **R12**: `DEFAULT_USER` es configurable, y en Azure vale `desconocido`
    (no `local`): una petición sin identificar debe quedar registrada como tal
    y no con un nombre de aspecto legítimo.

Sin red: el backend se sustituye por un `httpx.MockTransport`, que responde en
memoria. No se abre ni un socket (`docs/CONVENTIONS.md`, sección «Tests»).
"""
from __future__ import annotations

from typing import Any

import httpx
import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from interface_adapters.web import app as modulo_app

#: URL del backend en los tests. No existe: el transporte de prueba
#: intercepta la petición antes de que salga a ninguna parte.
API_DE_MENTIRA = "http://api-de-mentira"

#: El valor que R12 exige desplegar en Azure.
USUARIO_SIN_IDENTIFICAR = "desconocido"


class _BackendEspia:
    """Sustituye a `dedicacion-api`: apunta lo que le llega y responde 200."""

    def __init__(self) -> None:
        self.peticiones: list[httpx.Request] = []

    def __call__(self, peticion: httpx.Request) -> httpx.Response:
        self.peticiones.append(peticion)
        return httpx.Response(200, json={"ok": True})

    @property
    def ultima(self) -> httpx.Request:
        assert self.peticiones, "el proxy no llegó a llamar al backend"
        return self.peticiones[-1]

    def cabecera(self, nombre: str) -> str | None:
        return self.ultima.headers.get(nombre)


@pytest.fixture
def backend(monkeypatch: pytest.MonkeyPatch) -> _BackendEspia:
    """Cablea el proxy del front contra el backend espía, sin tocar la red."""
    espia = _BackendEspia()
    cliente_real = httpx.AsyncClient

    def _fabricar(**kwargs: Any) -> httpx.AsyncClient:
        return cliente_real(transport=httpx.MockTransport(espia), **kwargs)

    monkeypatch.setattr(modulo_app.httpx, "AsyncClient", _fabricar)
    return espia


def cliente(**ajustes: Any) -> TestClient:
    """Front de laboratorio: sin `.env`, con los ajustes que pida el test."""
    settings = Settings(
        _env_file=None,
        api_base_url=API_DE_MENTIRA,
        **ajustes,
    )
    return TestClient(modulo_app.build_app(settings))


# --- R11 · la identidad de Easy Auth llega al backend -----------------------


def test_f008_r11_la_cabecera_de_easy_auth_se_propaga_como_x_usuario(backend):
    """El caso normal en Azure: quien entra al portal firma lo que registra."""
    with cliente() as web:
        respuesta = web.get(
            "/api/v1/periodos",
            headers={"X-MS-CLIENT-PRINCIPAL-NAME": "rafael.alvarez"},
        )

    assert respuesta.status_code == 200
    assert backend.cabecera("x-usuario") == "rafael.alvarez"


def test_f008_r11_sin_cabecera_de_easy_auth_se_usa_el_usuario_por_defecto(backend):
    """En local no hay Easy Auth y el sistema tiene que seguir funcionando."""
    with cliente(default_user="local") as web:
        web.get("/api/v1/periodos")

    assert backend.cabecera("x-usuario") == "local"


def test_f008_r11_la_cabecera_de_easy_auth_se_recorta(backend):
    """Espacios alrededor no crean un usuario distinto en la auditoría."""
    with cliente() as web:
        web.get(
            "/api/v1/periodos",
            headers={"X-MS-CLIENT-PRINCIPAL-NAME": "  rafael.alvarez  "},
        )

    assert backend.cabecera("x-usuario") == "rafael.alvarez"


def test_f008_r11_una_cabecera_vacia_de_easy_auth_no_borra_la_identidad(backend):
    """Cabecera presente pero vacía = no hay identidad: `DEFAULT_USER`.

    Sin esto, una cadena vacía llegaría a la auditoría como si fuera el
    nombre de una persona.
    """
    with cliente(default_user=USUARIO_SIN_IDENTIFICAR) as web:
        web.get("/api/v1/periodos", headers={"X-MS-CLIENT-PRINCIPAL-NAME": "   "})

    assert backend.cabecera("x-usuario") == USUARIO_SIN_IDENTIFICAR


def test_f008_r11_el_x_usuario_que_llega_de_fuera_se_descarta(backend):
    """El proxy ESCRIBE `X-Usuario`; no reenvía la que traiga el navegador.

    Es la mitad del requisito que de verdad protege la auditoría: si el
    cliente pudiera colar su propio `X-Usuario`, cualquiera con sesión podría
    registrar en Sigrid a nombre de otro. La api se cree esa cabecera (R8),
    así que aquí es donde se decide.
    """
    with cliente(default_user=USUARIO_SIN_IDENTIFICAR) as web:
        web.get("/api/v1/periodos", headers={"X-Usuario": "el-jefe"})

    assert backend.cabecera("x-usuario") == USUARIO_SIN_IDENTIFICAR


def test_f008_r11_easy_auth_gana_a_la_cabecera_inyectada(backend):
    """Con las dos presentes, manda la que pone la plataforma."""
    with cliente() as web:
        web.get(
            "/api/v1/periodos",
            headers={
                "X-MS-CLIENT-PRINCIPAL-NAME": "rafael.alvarez",
                "X-Usuario": "el-jefe",
            },
        )

    assert backend.cabecera("x-usuario") == "rafael.alvarez"


def test_f008_r11_la_cabecera_de_easy_auth_no_viaja_al_backend(backend):
    """La api no debe aprender a leer la cabecera de la plataforma.

    Su único puente de identidad es `X-Usuario`; que la de Easy Auth no
    llegue mantiene esa frontera de un solo camino.
    """
    with cliente() as web:
        web.get(
            "/api/v1/periodos",
            headers={"X-MS-CLIENT-PRINCIPAL-NAME": "rafael.alvarez"},
        )

    assert backend.cabecera("x-ms-client-principal-name") is None


def test_f008_r11_la_identidad_tambien_viaja_en_las_escrituras(backend):
    """`registro/ejecutar` es POST: si la identidad se perdiera ahí, la
    auditoría no serviría justo donde hace falta."""
    with cliente() as web:
        respuesta = web.post(
            "/api/v1/registro/ejecutar",
            json={"periodo_id": 1},
            headers={"X-MS-CLIENT-PRINCIPAL-NAME": "rafael.alvarez"},
        )

    assert respuesta.status_code == 200
    assert backend.ultima.method == "POST"
    assert backend.cabecera("x-usuario") == "rafael.alvarez"


# --- R12 · el valor que se despliega en Azure -------------------------------


def test_f008_r12_default_user_es_configurable_y_por_defecto_es_local():
    """En el código, el valor cómodo de trabajar en el portátil...

    ...y en Azure se despliega `desconocido` desde
    `infra/create_front_dedicacion.ps1` (R12). El defecto del código no se
    cambia: quien despliega es quien lo dice.
    """
    assert Settings(_env_file=None).default_user == "local"
    assert (
        Settings(_env_file=None, default_user=USUARIO_SIN_IDENTIFICAR).default_user
        == USUARIO_SIN_IDENTIFICAR
    )


def test_f008_r12_el_env_example_avisa_del_valor_de_azure():
    """El `.env.example` es el único inventario de variables que queda.

    Quien lo lea tiene que enterarse de que en Azure `DEFAULT_USER` vale
    `desconocido` y `API_TIMEOUT_S` sube a 200 (R28), sin abrir `infra/`.
    """
    from pathlib import Path

    ejemplo = Path(__file__).resolve().parents[1] / ".env.example"
    texto = ejemplo.read_text(encoding="utf-8")

    assert USUARIO_SIN_IDENTIFICAR in texto
    assert "200" in texto


# --- El proxy sigue haciendo su trabajo -------------------------------------


def test_f008_r11_el_health_del_front_no_pasa_por_el_backend(backend):
    """`/health` responde el propio front: es lo que mira la plataforma.

    Ojo, y consta en `docs/INTEGRACION.md`: con Easy Auth activo, pedirlo de
    forma anónima devuelve una redirección al login, no este JSON (R35).
    """
    with cliente() as web:
        respuesta = web.get("/health")

    assert respuesta.status_code == 200
    assert respuesta.json()["ok"] is True
    assert backend.peticiones == []
