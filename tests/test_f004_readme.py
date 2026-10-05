# tests/test_f004_readme.py
"""Comprueba que el README de la raíz no miente (F-004).

Un README que documenta un puerto o una ruta que ya no existe hace más daño
que no tenerlo: se lee, se cree y se pierde el tiempo. Estos tests atan el
documento al código, así que un cambio de puerto o un fichero movido rompe la
suite en vez de pudrir el README en silencio.

No se importa nada de los servicios: cada uno vive en su propio venv y la
suite de la raíz no puede depender de ellos. Se lee el texto fuente.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
README = RAIZ / "README.md"


@pytest.fixture(scope="module")
def texto() -> str:
    return README.read_text(encoding="utf-8")


def test_f004_a1_existe_readme_en_la_raiz() -> None:
    """A1: el monorepo tiene README en la raíz."""
    assert README.is_file(), "falta README.md en la raíz del monorepo"


def test_f004_a1_documenta_los_tres_servicios_con_su_puerto(texto: str) -> None:
    """A1: mapa de servicios con el puerto en el que escucha cada uno."""
    for servicio, puerto in (
        ("dedicacion-transfer", "8006"),
        ("dedicacion-api", "8090"),
        ("dedicacion-front", "8080"),
    ):
        assert servicio in texto, f"el README no nombra {servicio}"
        assert puerto in texto, f"el README no cita el puerto {puerto}"


def test_f004_a1_arranque_en_el_orden_que_funciona(texto: str) -> None:
    """A1: el arranque se documenta transfer -> api -> front, y en ese orden.

    El orden no es decorativo: cada servicio llama al anterior.
    """
    posiciones = [
        texto.index(f"cd services/dedicacion-{s} ") for s in ("transfer", "api", "front")
    ]
    assert posiciones == sorted(posiciones), (
        "el README documenta el arranque en un orden distinto de "
        "transfer -> api -> front"
    )


@pytest.mark.parametrize(
    "fichero_env, variable, puerto",
    [
        ("services/dedicacion-transfer/.env.example", "API_PORT", "8006"),
        ("services/dedicacion-api/.env.example", "API_PORT", "8090"),
        ("services/dedicacion-front/.env.example", "FRONT_PORT", "8080"),
    ],
)
def test_f004_a1_los_puertos_del_readme_son_los_reales(
    fichero_env: str, variable: str, puerto: str
) -> None:
    """A1: el puerto que documenta el README es el que trae el .env.example."""
    contenido = (RAIZ / fichero_env).read_text(encoding="utf-8")
    declarado = re.search(rf"^{variable}=(\d+)$", contenido, re.MULTILINE)
    assert declarado, f"{fichero_env} no declara {variable}"
    assert declarado.group(1) == puerto, (
        f"{fichero_env} declara {variable}={declarado.group(1)}, "
        f"pero el README documenta {puerto}"
    )


def test_f004_a1_toda_url_de_la_api_lleva_su_prefijo_real(texto: str) -> None:
    """A1: `/api/v1/health` es la ruta buena; `/health` a secas da 404.

    Es un tropiezo real y caro. No basta con que el README lo mencione en
    algún sitio: NINGUNA url del puerto 8090 puede aparecer sin el prefijo
    que declara el router, o el lector copiará la equivocada.
    """
    routes = RAIZ / "services/dedicacion-api/interface_adapters/api/routes.py"
    declarado = re.search(r'APIRouter\(prefix="([^"]+)"\)', routes.read_text(encoding="utf-8"))
    assert declarado, "no se encontró el prefijo del router de dedicacion-api"
    prefijo = declarado.group(1)

    rutas_citadas = re.findall(r"127\.0\.0\.1:8090(/[A-Za-z0-9/_.-]*)", texto)
    assert rutas_citadas, "el README no cita ninguna url de dedicacion-api"
    sin_prefijo = [r for r in rutas_citadas if not r.startswith(prefijo)]
    assert not sin_prefijo, (
        f"el README cita urls de la api sin el prefijo {prefijo}: {sin_prefijo}"
    )
    assert f"{prefijo}/health" in rutas_citadas, (
        f"el README no documenta la salud de la api como {prefijo}/health"
    )


def test_f004_a1_los_env_example_que_manda_copiar_existen(texto: str) -> None:
    """A1: los `.env.example` que el arranque manda copiar están en su sitio."""
    origenes = re.findall(r"^cp (services/\S+/\.env\.example) ", texto, re.MULTILINE)
    assert len(origenes) == 3, f"el README manda copiar {len(origenes)} .env.example, esperados 3"
    for origen in origenes:
        assert (RAIZ / origen).is_file(), f"el README manda copiar {origen}, que no existe"


def test_f004_a2_los_enlaces_relativos_resuelven(texto: str) -> None:
    """A2: enlaza en vez de duplicar; los enlaces tienen que llevar a algo."""
    enlaces = re.findall(r"\]\((?!https?://)([^)#]+)(?:#[^)]*)?\)", texto)
    assert enlaces, "el README no enlaza a ningún documento del repositorio"
    rotos = [destino for destino in enlaces if not (RAIZ / destino).exists()]
    assert not rotos, f"enlaces rotos en el README: {rotos}"


def test_f004_a2_remite_a_la_arquitectura_y_a_azure_apps(texto: str) -> None:
    """A2: las reglas y el ecosistema se enlazan, no se copian aquí."""
    assert "docs/ARCHITECTURE.md" in texto, "el README no remite a docs/ARCHITECTURE.md"
    assert "azure-apps" in texto, "el README no remite al repositorio azure-apps"


def test_f004_a3_sin_secretos_ni_valores_de_credencial(texto: str) -> None:
    """A3: se nombran las variables, nunca sus valores.

    `127.0.0.1` es loopback y sí puede aparecer: no es una IP interna.
    """
    sin_loopback = texto.replace("127.0.0.1", "<loopback>")
    sospechosos = [
        r"(?i)(password|contrase\w+|secret|function_key|api_key)\s*[:=]\s*\S+",
        r"[A-Za-z0-9+/]{40,}={0,2}",                      # claves y tokens en base64
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        r"\b\d{1,3}(?:\.\d{1,3}){3}\b",                   # IPs (salvo loopback)
        r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",  # GUID
    ]
    for patron in sospechosos:
        hallado = re.search(patron, sin_loopback)
        assert not hallado, f"posible secreto en el README: {hallado.group(0)!r}"
