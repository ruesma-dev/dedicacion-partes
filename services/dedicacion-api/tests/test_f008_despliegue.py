# tests/test_f008_despliegue.py
"""F-008 · Por qué `dedicacion-api` NO puede tener ingress externo (R8).

Este fichero no comprueba una funcionalidad: **fija una carencia**. La api no
tiene autenticación propia. Su único control de identidad es
`interface_adapters/api/deps.py::obtener_usuario`, que lee la cabecera
`X-Usuario` y se la cree, exactamente igual que hace `partes` con `sv5`.

Con ingress externo, cualquiera en Internet podría llamar a
`POST /api/v1/registro/ejecutar` poniendo la cabecera que quisiera; la api
llamaría al transfer, y el transfer es **la única pluma del sistema sobre el
ERP**. Por eso el ingress interno de la api no es una preferencia de
despliegue: es su control de acceso (`design.md` §2.1).

El test existe para que la carencia esté escrita y con nombre. Si algún día
alguien añade autenticación de verdad a la api, este fichero fallará: ese
fallo **es la señal** de que la decisión de exposición se puede reabrir, y de
que hay que reabrirla a conciencia y no de pasada.

Trazabilidad: R8 de `specs/F-008-infra-azure/requirements.md`.
"""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest
from interface_adapters.api.deps import obtener_usuario

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]
FUENTE_DEPS = RAIZ_SERVICIO / "interface_adapters" / "api" / "deps.py"


class _PeticionFalsa:
    """Lo único que `obtener_usuario` mira de una Request: sus cabeceras."""

    def __init__(self, cabeceras: dict[str, str]) -> None:
        self.headers = cabeceras


@pytest.mark.parametrize(
    "declarado",
    (
        "rafael.alvarez",
        "  con espacios alrededor  ",
        "administrador",
        "cualquiera@dominio-ajeno.example",
        "'; DROP TABLE asignacion; --",
    ),
)
def test_f008_r8_obtener_usuario_se_cree_la_cabecera_sin_validarla(declarado):
    """Lo que venga en `X-Usuario` se acepta tal cual (solo se recortan
    los espacios). No hay lista blanca, ni firma, ni token: nada.

    De ahí sale el requisito de ingress interno. Un valor de esta lista
    llegando desde Internet acabaría en la auditoría de la tabla `evento`
    como si fuera una persona.
    """
    usuario = obtener_usuario(_PeticionFalsa({"x-usuario": declarado}))

    assert usuario == declarado.strip()


@pytest.mark.parametrize(
    "cabeceras",
    (
        {},
        {"x-usuario": ""},
        {"x-usuario": "   "},
        {"authorization": "Bearer da-igual-lo-que-ponga"},
    ),
)
def test_f008_r8_sin_cabecera_util_se_audita_como_local(cabeceras: dict[str, str]):
    """Sin `X-Usuario` no se rechaza la petición: se sigue, como 'local'.

    Es el segundo motivo del ingress interno. La api **no corta** ninguna
    petición por falta de identidad; una llamada anónima entra igual. Y una
    cabecera `Authorization`, que es lo que alguien esperaría que valiese,
    aquí no la mira nadie.
    """
    assert obtener_usuario(_PeticionFalsa(cabeceras)) == "local"


def test_f008_r8_obtener_usuario_no_depende_de_nada_mas_que_la_peticion():
    """No hay verificador escondido: la firma no recibe ni clave ni sesión."""
    firma = inspect.signature(obtener_usuario)

    assert list(firma.parameters) == ["request"]


def test_f008_r8_la_api_no_tiene_ningun_verificador_de_credenciales():
    """`deps.py` no importa nada que sirva para autenticar.

    Si mañana aparece aquí un `HTTPBearer`, un `verify_token` o una clave de
    API, este test cae y toca revisar `docs/INTEGRACION.md` y la decisión de
    exposición **antes** de abrir el ingress de la api.
    """
    fuente = FUENTE_DEPS.read_text(encoding="utf-8")

    for senal in (
        "HTTPBearer",
        "HTTPBasic",
        "OAuth2",
        "APIKeyHeader",
        "jwt",
        "verificar_token",
    ):
        assert senal not in fuente, (
            f"'{senal}' en deps.py: la api ya no sería el servicio sin "
            f"autenticación que describe R8. Revisa la exposición."
        )


def test_f008_r8_la_cabecera_de_confianza_es_la_que_inyecta_el_front():
    """El único puente de identidad es `X-Usuario`, puesto por el proxy.

    El front la escribe a partir de `X-MS-CLIENT-PRINCIPAL-NAME` de Easy Auth
    (R11). Que esa cabecera valga como identidad **solo** se sostiene si nadie
    más puede escribirla, y eso lo garantiza el ingress interno, no el código.
    """
    fuente = FUENTE_DEPS.read_text(encoding="utf-8")

    assert "x-usuario" in fuente.lower()
