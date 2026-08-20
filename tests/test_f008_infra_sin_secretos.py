# tests/test_f008_infra_sin_secretos.py
"""F-008 · Guardián permanente: ningún secreto entra en el repositorio.

**Esto es un repositorio git: lo que entra, se queda en el historial aunque
luego se borre.** Por eso la única defensa que sirve es la que actúa antes del
commit, y por eso este fichero es un guardián y no una comprobación de una
vez: seguirá barriendo `infra/`, `specs/` y `docs/` mucho después de que
F-008 se cierre. `postventa-incidencias` tiene el suyo por el mismo motivo.

Trazabilidad con `specs/F-008-infra-azure/requirements.md`:

  - **R21**: ni contraseñas, ni cadenas de conexión, ni function keys, ni IDs
    de suscripción, tenant, aplicación, grupo u objeto, ni IPs internas. Los
    valores reales viven en ficheros `infra/*.local.ps1`, **no versionados**.
  - **R22**: los secretos se nombran por su **clave en Key Vault**
    (`PG-PASSWORD`, `SIGRID-API-FUNCTION-KEY`, `EASYAUTH-CLIENT-SECRET`),
    nunca por su valor.

## Qué se busca, y qué NO

Los patrones exigen un **valor** detrás del `=`, no la mención del nombre. La
diferencia no es un detalle: estas mismas specs escriben `AccountKey=` y
`password=` en prosa al describir este barrido, y un patrón ingenuo se
acusaría a sí mismo. Un guardián que grita con todo se acaba desactivando, y
entonces ya no guarda nada. Los dos tests de las dos caras —el que inyecta un
valor inventado y el que pasa la prosa legítima— son los que sostienen ese
equilibrio.

Tampoco se persiguen los **nombres de recurso** (`psql-albaranes-rs9k2`,
`acralbaranesdev`, `func-sigridapi-dev-huyke`). Son públicos dentro de la
casa, la propia R2 obliga a declararlos, y `azure-apps` los nombra en todos
sus documentos. Lo que no puede entrar es un **valor de conexión**: una
credencial, un identificador de la suscripción o una IP interna.

Todos los valores de los controles positivos de este fichero son
**inventados**: no existen, no apuntan a nada y no se han copiado de ningún
sitio.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]

#: Los tres árboles que se barren (R22). `infra/` porque es donde nacen los
#: scripts de despliegue; `specs/` y `docs/` porque son los ficheros que más
#: tientan a pegar «un ejemplo real para que se entienda».
DIRECTORIOS = ("infra", "specs", "docs")

#: Nada de esto es código que haya que leer, y algunos ni siquiera son texto.
IGNORADOS = ("__pycache__", ".pytest_cache", ".ruff_cache", ".git")

#: Sufijos que sí se leen. Un binario que se colara aquí no se decodifica.
SUFIJOS = frozenset(
    {".md", ".ps1", ".psm1", ".json", ".txt", ".yaml", ".yml", ".py", ".sql", ".env", ""}
)

#: El GUID de «acceso por defecto» de una Enterprise App de Entra. Es una
#: constante documentada de la plataforma, igual para todo el mundo, no un
#: identificador de nuestra suscripción. `setup_front_easyauth.ps1` lo necesita.
GUID_ADMITIDOS = frozenset({"00000000-0000-0000-0000-000000000000"})

#: Marcadores que ocupan el sitio de un valor real sin serlo. El valor de
#: verdad vive en la copia local no versionada (`infra/*.local.ps1`).
MARCADORES = ("REDACTADO-VER-COPIA-LOCAL", "AUTO", "TU-", "<", "$")

PATRONES: dict[str, re.Pattern[str]] = {
    # IDs de suscripción, tenant, aplicación, grupo u objeto de Entra.
    "guid": re.compile(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
        re.IGNORECASE,
    ),
    # Clave de cuenta de Storage dentro de una cadena de conexión.
    "account_key": re.compile(r"(?i)AccountKey\s*=\s*[A-Za-z0-9+/=]{20,}"),
    # Una credencial con valor. Se excluyen a propósito las REFERENCIAS
    # (`secretref:`, `keyvaultref:`), las variables de PowerShell (`$...`) y
    # los marcadores: nombrar dónde vive un secreto es justo lo que R22 pide.
    #
    # La comilla de apertura se CONSUME antes de mirar el valor. Es la
    # diferencia entre cazar `PG_PASSWORD = "loQueSea"` y dejarlo pasar: la
    # primera versión de este patrón excluía todo lo que empezara por comilla
    # y se le coló justo el caso más habitual en un script de PowerShell.
    #
    # Un valor que empieza por `[` es un acelerador de tipo .NET
    # (`[System.Net.NetworkCredential]::new(...)`), no un literal: ninguna
    # credencial empieza así, y sin esta exclusión el guardián señalaba la
    # línea que precisamente EVITA escribir la contraseña en el script.
    "credencial": re.compile(
        r"(?i)(?:password|passwd|pwd|secret|token|api[_-]?key|function[_-]?key)"
        r"\s*=\s*[\"']?"
        r"(?!secretref:|keyvaultref:|\$|<|%|@|\[|REDACTADO|AUTO\b|TU-)"
        r"[^\s\"'`,;)\]}]{4,}"
    ),
    # Una clave larga en base64 con su relleno (las function keys de Azure
    # Functions terminan así). Exigir el `=` de relleno es lo que evita que
    # el patrón salte con cualquier identificador largo.
    "clave_base64": re.compile(r"[A-Za-z0-9+/_-]{30,}={1,2}(?![A-Za-z0-9+/_=-])"),
    # Una URI con usuario y contraseña incrustados.
    "cadena_de_conexion": re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^\s/@]+:[^\s/@]+@"),
    # IP INTERNA (RFC 1918). `0.0.0.0` (escuchar en todas / regla de firewall
    # de servicios de Azure) y `127.0.0.1` no lo son y sí pueden aparecer.
    "ip_privada": re.compile(
        r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        r"|192\.168\.\d{1,3}\.\d{1,3}"
        r"|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"
    ),
}


def hallazgos(texto: str) -> dict[str, list[str]]:
    """Lo que cada patrón encuentra en ese texto, ya descontado lo admitido."""
    encontrado: dict[str, list[str]] = {}
    for nombre, patron in PATRONES.items():
        coincidencias = [
            hallado
            for hallado in patron.findall(texto)
            if not (nombre == "guid" and hallado.lower() in GUID_ADMITIDOS)
        ]
        if coincidencias:
            encontrado[nombre] = coincidencias
    return encontrado


def ficheros_barridos() -> list[Path]:
    """Todos los ficheros de texto bajo los tres directorios vigilados."""
    encontrados: list[Path] = []
    for directorio in DIRECTORIOS:
        raiz = RAIZ / directorio
        if not raiz.is_dir():
            continue
        for fichero in sorted(raiz.rglob("*")):
            if not fichero.is_file():
                continue
            if any(parte in IGNORADOS for parte in fichero.parts):
                continue
            if fichero.suffix.lower() in SUFIJOS:
                encontrados.append(fichero)
    return encontrados


def hallazgos_con_linea(fichero: Path) -> list[str]:
    """Fichero, línea y familia de cada hallazgo, para poder ir a arreglarlo."""
    texto = fichero.read_text(encoding="utf-8", errors="replace")
    fallos: list[str] = []
    for numero, linea in enumerate(texto.splitlines(), start=1):
        for familia in hallazgos(linea):
            fallos.append(
                f"{fichero.relative_to(RAIZ).as_posix()}:{numero} [{familia}]"
            )
    return fallos


# --- El barrido de verdad ---------------------------------------------------


def test_f008_r21_el_barrido_alcanza_los_tres_directorios():
    """Sin esto, el peor final posible sería pasar barriendo la nada.

    Un guardián que no encuentra ficheros da verde igual que uno que no
    encuentra secretos, y las dos cosas se leen exactamente igual en la
    salida de pytest.
    """
    barridos = ficheros_barridos()
    directorios = {fichero.relative_to(RAIZ).parts[0] for fichero in barridos}

    assert directorios == set(DIRECTORIOS)
    assert len(barridos) >= 10


def test_f008_r21_ningun_secreto_ni_identificador_en_el_repositorio():
    """El barrido real sobre `infra/`, `specs/` y `docs/`.

    Si esto falla, **no se relaja el patrón**: se saca el valor del fichero. Y
    si el valor ya está commiteado, se avisa al humano, porque el historial de
    git no lo suelta solo: hay que rotar la credencial.
    """
    fallos: list[str] = []
    for fichero in ficheros_barridos():
        fallos.extend(hallazgos_con_linea(fichero))

    assert fallos == [], "Posibles secretos en el repositorio:\n" + "\n".join(fallos)


def test_f008_r22_los_secretos_se_nombran_por_su_clave_en_key_vault():
    """Las tres claves del `design.md` §5, por su nombre, en `infra/`.

    Es la otra mitad de R22: no basta con que no haya valores; tiene que
    quedar escrito **dónde** vive cada secreto para que alguien pueda
    desplegar sin preguntar.
    """
    texto = "\n".join(
        fichero.read_text(encoding="utf-8", errors="replace")
        for fichero in ficheros_barridos()
        if fichero.relative_to(RAIZ).parts[0] == "infra"
    )

    for clave in ("PG-PASSWORD", "SIGRID-API-FUNCTION-KEY", "EASYAUTH-CLIENT-SECRET"):
        assert clave in texto, f"ningún script de infra/ nombra {clave}"


def test_f008_r21_los_valores_reales_no_se_versionan():
    """`infra/.gitignore` deja fuera las copias locales con los valores."""
    ignorados = (RAIZ / "infra" / ".gitignore").read_text(encoding="utf-8")

    assert "*.local.ps1" in ignorados


# --- Las dos caras del guardián (T10) ---------------------------------------


@pytest.mark.parametrize(
    ("familia", "inyectado"),
    (
        ("guid", "$Global:SUBSCRIPTION = 12345678-90ab-4cde-8f01-234567890abc"),
        ("guid", "el grupo tiene objectId aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"),
        (
            "account_key",
            "DefaultEndpointsProtocol=https;AccountKey=SUx1c3RvUGFyYVByb2JhckVsQmFycmlkbw==",
        ),
        ("credencial", "PG_PASSWORD=inventada-no-existe"),
        # Entre comillas, que es como se escribe en un .ps1: el caso que se
        # coló en la primera versión del patrón y por el que existe la fase
        # RED de T10.
        ("credencial", '$Global:PG_PASSWORD  = "InventadaDelTodoNoExiste"'),
        ("credencial", "$secret = 'inventadaTampocoExiste'"),
        ("credencial", "SIGRID_API_FUNCTION_KEY=zzInventadaNoExiste"),
        ("credencial", "password = inventada-tampoco"),
        ("credencial", "client_secret=Abc123InventadoDelTodo"),
        (
            "clave_base64",
            "la clave es SUx1c3RvUGFyYVByb2JhckVsQmFycmlkb051bmNhRXhpc3Rpbw==",
        ),
        ("cadena_de_conexion", "postgresql://usuario:inventada@servidor:5432/base"),
        ("ip_privada", "10.0.0.4"),
        ("ip_privada", "192.168.1.20"),
        ("ip_privada", "172.16.31.9"),
    ),
)
def test_f008_r21_el_barrido_caza_cada_patron_inyectado(familia: str, inyectado: str):
    """Control positivo, uno por familia. Todos los valores son inventados.

    Un patrón que nunca se ha visto saltar no protege nada: podría estar mal
    escrito desde el primer día y nadie se enteraría.
    """
    assert familia in hallazgos(inyectado)


@pytest.mark.parametrize(
    "legitimo",
    (
        # La prosa de estas mismas specs, que describe el barrido.
        "patrones de GUID, `AccountKey=`, `password=`/`pwd=` con valor",
        "busca `AccountKey=`, `password=`, IP privada y clave larga en base64",
        # Nombrar dónde vive un secreto es lo que R22 EXIGE.
        "el secreto `PG-PASSWORD` se lee del Key Vault por keyvaultref",
        '"PG_PASSWORD=secretref:pg-password"',
        '"SIGRID_API_FUNCTION_KEY=secretref:sigrid-key"',
        '"easyauth-client-secret=keyvaultref:$KV_URI/secrets/EASYAUTH-CLIENT-SECRET"',
        '$Global:SUBSCRIPTION = "REDACTADO-VER-COPIA-LOCAL"',
        "$PGPASS = [System.Net.NetworkCredential]::new(\"\", $sec).Password",
        # La línea que EVITA escribir la contraseña en el script: se lee de un
        # SecureString pedido por consola. El guardián la señalaba.
        '$PGADMIN_PWD = [System.Net.NetworkCredential]::new("", $secAdmin).Password',
        '$env:PGPASSWORD = $PGPASS',
        "CREATE ROLE dedicacion_app LOGIN PASSWORD '$APP_PWD_SQL'",
        '$secApp = Read-Host "  Contrasena" -AsSecureString',
        # Nombres de recurso: públicos dentro de la casa y exigidos por R2.
        "el servidor compartido `psql-albaranes-rs9k2` y el registro `acralbaranesdev`",
        "la pasarela `sigrid-api` (`func-sigridapi-dev-huyke`)",
        # Configuración que no es secreta.
        '"PG_SSLMODE=require", "AUTO_CREATE_DATABASE=false"',
        '"OBRA_PRUEBAS_FORZAR=true", "MARCA_PRUEBAS=PRUEBA-PORC"',
        "--start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0",
        '"API_HOST=0.0.0.0", "API_PORT=8006"',
        "API_BASE_URL=http://127.0.0.1:8090",
        # El GUID de acceso por defecto de Entra: constante de la plataforma.
        'appRoleId = "00000000-0000-0000-0000-000000000000"',
        # Un tag fechado, que se parece a un identificador y no lo es.
        "imagen dedicacion-api:r20260820-1830",
    ),
)
def test_f008_r21_el_barrido_no_salta_con_el_texto_legitimo(legitimo: str):
    """Control negativo. Un guardián que grita con todo se acaba quitando.

    Estas son frases que los scripts y la documentación **tienen** que poder
    decir. Si alguna empieza a saltar, se arregla el patrón, no el texto.
    """
    assert hallazgos(legitimo) == {}
