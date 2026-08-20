# tests/test_f008_imagenes.py
"""F-008 · Empaquetado de los tres servicios e inventario de imágenes.

Trazabilidad con `specs/F-008-infra-azure/requirements.md`:

  - **R24**: `infra/imagenes.json` está versionado y dice qué tag se publicó
    para cada servicio y cuándo. Con tags fechados, «qué código está
    corriendo» tiene que poder responderse **desde git**, sin abrir Azure.
  - **R25**: ningún `.env` entra en una imagen. Los `.env` no se versionan, así
    que la única defensa que queda es el `.dockerignore` de cada servicio, y
    el contexto de build que prepara `infra/build_images_dedicacion.ps1`.
  - **R26**: el transfer tiene `Dockerfile`. Era el único de los tres sin él
    (`docs/ARCHITECTURE.md`), y sin `Dockerfile` no hay imagen que desplegar.

Todo se comprueba leyendo ficheros del repositorio: aquí no se construye
ninguna imagen. El build real es MANUAL (humano), T25 de `tasks.md`.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SERVICIOS_DIR = RAIZ / "services"
INVENTARIO = RAIZ / "infra" / "imagenes.json"

#: Los tres servicios y el puerto que cada uno escucha. Es la referencia
#: INDEPENDIENTE del `Dockerfile`: si alguien cambia el `EXPOSE` sin cambiar
#: esta tabla (o al revés), el test lo caza. Los puertos son los de
#: `docs/ARCHITECTURE.md` y los que usan los scripts de `infra/`.
PUERTOS: dict[str, int] = {
    "dedicacion-transfer": 8006,
    "dedicacion-api": 8090,
    "dedicacion-front": 8080,
}

#: Tag fechado obligatorio (`docs/CONVENTIONS.md`): nunca `latest`, nunca
#: reescribir un tag ya publicado.
TAG_FECHADO = re.compile(r"^r\d{8}-\d{4}$")

#: Fecha de publicación en ISO, para poder ordenar y comparar sin ambigüedad.
FECHA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?)?$")


def dockerfile(servicio: str) -> Path:
    return SERVICIOS_DIR / servicio / "Dockerfile"


def dockerignore(servicio: str) -> Path:
    return SERVICIOS_DIR / servicio / ".dockerignore"


def lineas_utiles(fichero: Path) -> list[str]:
    """Líneas con contenido, sin comentarios ni espacios sobrantes."""
    return [
        linea.strip()
        for linea in fichero.read_text(encoding="utf-8").splitlines()
        if linea.strip() and not linea.strip().startswith("#")
    ]


# --- R25 y R26 · los tres servicios se pueden empaquetar --------------------


@pytest.mark.parametrize("servicio", sorted(PUERTOS))
def test_f008_r26_cada_servicio_tiene_dockerfile(servicio: str):
    """Sin `Dockerfile` no hay imagen, y sin imagen no hay despliegue."""
    assert dockerfile(servicio).is_file(), (
        f"{servicio} no tiene Dockerfile: no se puede construir su imagen"
    )


@pytest.mark.parametrize("servicio", sorted(PUERTOS))
def test_f008_r26_cada_dockerfile_expone_el_puerto_de_su_servicio(servicio: str):
    """El `EXPOSE` y el `--target-port` del Container App tienen que casar.

    Si no casan, el ingress apunta a un puerto donde no escucha nadie y el
    servicio parece caído estando vivo.
    """
    texto = dockerfile(servicio).read_text(encoding="utf-8")

    assert f"EXPOSE {PUERTOS[servicio]}" in texto


@pytest.mark.parametrize("servicio", sorted(PUERTOS))
def test_f008_r26_cada_dockerfile_arranca_por_main_py(servicio: str):
    """`python main.py`, no `uvicorn` a pelo.

    En la api, arrancar por `uvicorn` se salta la puesta al día del esquema
    (`main.py` lo dice en su docstring); en el transfer, se salta la
    configuración del log. Es la misma trampa en los tres.
    """
    texto = dockerfile(servicio).read_text(encoding="utf-8")

    assert 'CMD ["python", "main.py"]' in texto


@pytest.mark.parametrize("servicio", sorted(PUERTOS))
def test_f008_r26_las_dependencias_se_instalan_antes_de_copiar_el_codigo(
    servicio: str,
):
    """`requirements.txt` primero: cachear la capa cara es lo que hace que
    reconstruir tras tocar una línea de código no reinstale medio PyPI."""
    lineas = lineas_utiles(dockerfile(servicio))
    copia_requirements = next(
        i for i, linea in enumerate(lineas) if linea.startswith("COPY requirements.txt")
    )
    instalacion = next(i for i, linea in enumerate(lineas) if linea.startswith("RUN pip"))
    copia_codigo = next(i for i, linea in enumerate(lineas) if linea.startswith("COPY . "))

    assert copia_requirements < instalacion < copia_codigo


@pytest.mark.parametrize("servicio", sorted(PUERTOS))
def test_f008_r25_cada_servicio_excluye_su_env_de_la_imagen(servicio: str):
    """R25: el `.env` no entra en la imagen. Ni uno.

    Los `.env` llevan la function key de `sigrid-api` —la credencial de
    ESCRITURA sobre el ERP— y la contraseña de PostgreSQL. Una imagen es un
    fichero que se copia; lo que entra en ella, viaja.
    """
    fichero = dockerignore(servicio)
    assert fichero.is_file(), f"{servicio} no tiene .dockerignore"

    assert ".env" in lineas_utiles(fichero)


@pytest.mark.parametrize("servicio", sorted(PUERTOS))
def test_f008_r25_ningun_dockerfile_copia_el_env_a_mano(servicio: str):
    """Un `COPY .env` explícito se saltaría el `.dockerignore` sin avisar."""
    for linea in lineas_utiles(dockerfile(servicio)):
        assert not re.match(r"^COPY\s+\.env\b", linea), (
            f"{servicio}: el Dockerfile copia el .env explícitamente"
        )


# --- R24 · el inventario de imágenes ----------------------------------------


def test_f008_r24_el_inventario_de_imagenes_existe_y_esta_versionado():
    """`infra/imagenes.json` es lo que responde «qué hay desplegado».

    Con tag fechado y sin `latest`, la única forma de saberlo sin abrir Azure
    es que el tag publicado quede escrito en el repositorio.
    """
    assert INVENTARIO.is_file(), (
        "falta infra/imagenes.json: sin él, «qué código está corriendo» solo "
        "se puede responder abriendo Azure"
    )


def test_f008_r24_el_inventario_parsea_y_cubre_los_tres_servicios():
    datos = json.loads(INVENTARIO.read_text(encoding="utf-8"))

    assert set(datos["servicios"]) == set(PUERTOS)


@pytest.mark.parametrize("servicio", sorted(PUERTOS))
def test_f008_r24_cada_entrada_declara_repositorio_tag_y_fecha(servicio: str):
    """Un tag sin fecha de publicación no sirve para reconstruir la historia."""
    entrada = json.loads(INVENTARIO.read_text(encoding="utf-8"))["servicios"][servicio]

    assert set(entrada) >= {"repositorio", "tag", "publicado"}
    assert entrada["repositorio"] == servicio


@pytest.mark.parametrize("servicio", sorted(PUERTOS))
def test_f008_r23_el_tag_publicado_es_fechado_y_nunca_latest(servicio: str):
    """`rAAAAMMDD-HHmm` o nada. `latest` está prohibido por convención.

    `null` es un estado legítimo y honesto: ese servicio todavía no se ha
    publicado nunca (la fase 7 de `tasks.md` es MANUAL del humano). Lo que no
    es legítimo es un tag mutable.
    """
    entrada = json.loads(INVENTARIO.read_text(encoding="utf-8"))["servicios"][servicio]
    tag, publicado = entrada["tag"], entrada["publicado"]

    if tag is None:
        assert publicado is None, "hay fecha de publicación pero no hay tag"
        return

    assert TAG_FECHADO.match(tag), f"{servicio}: tag '{tag}' no es rAAAAMMDD-HHmm"
    assert publicado is not None, "hay tag publicado pero no consta cuándo"
    assert FECHA_ISO.match(publicado), f"{servicio}: fecha '{publicado}' no es ISO"


def test_f008_r23_ningun_tag_mutable_en_el_inventario():
    """Ningún tag es `latest`, ni se referencia una imagen `:latest`.

    Se comprueba sobre los VALORES, no sobre el texto: el inventario sí puede
    —y debe— explicar en su `$doc` por qué `latest` está prohibido. Es la
    diferencia entre nombrar una regla y saltársela.
    """
    texto = INVENTARIO.read_text(encoding="utf-8")
    datos = json.loads(texto)

    assert ":latest" not in texto
    for servicio, entrada in datos["servicios"].items():
        assert entrada["tag"] != "latest", f"{servicio} publicado con tag mutable"
