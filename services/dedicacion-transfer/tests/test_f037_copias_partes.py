# tests/test_f037_copias_partes.py
"""F-037 · Anti-divergencia de las copias de `partes` (design §12).

`estado_parte.py` y `cuenta_analitica.py` son COPIA LITERAL de los de
`services/partes-transfer/application/services/` en el repositorio
`partes` (lista cerrada de copias de `CLAUDE.md`, D15 y D18): los dos
servicios escriben en el MISMO parte de Sigrid y tienen que decidir igual.

Se comparan byte a byte con `git -C <partes> show <ref>:<ruta>`, sin hacer
checkout ni tocar nada en `partes`:

- contra `COMMIT_COPIADO`, el commit del que se copió (inmutable: si falla,
  la copia de aquí se ha editado);
- contra `REF_VIGILADA`, la rama de la F-031 de `partes` hasta que llegue a
  su `dev`; entonces se cambia a `dev` en el mismo trabajo. Si falla, se
  mira el diff (design §12): estilo o texto, se recopia; regla, se para.

Sin el repositorio `partes` al lado, o sin la ref: `skip` con motivo.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

#: Commit de `partes` del que se copiaron los dos ficheros: el último que
#: los cambia en la rama (la punta de la rama al copiar era `dc5666b`).
COMMIT_COPIADO = "9b202e9f6fa3571d778bb39b27c77ff65660ee11"
#: Ref que se vigila (design §12).
REF_VIGILADA = "feature/F-031-asiento-analitico"

TRANSFER = Path(__file__).resolve().parents[1]
REPO_PARTES = TRANSFER.parents[2] / "partes"
RUTA_EN_PARTES = "services/partes-transfer/application/services/{}"
COPIAS = ("estado_parte.py", "cuenta_analitica.py")


def _de_partes(ref: str, fichero: str) -> bytes:
    if not (REPO_PARTES / ".git").exists():
        pytest.skip(f"sin el repositorio partes en {REPO_PARTES}")
    r = subprocess.run(
        ["git", "-C", str(REPO_PARTES), "show",
         f"{ref}:{RUTA_EN_PARTES.format(fichero)}"],
        capture_output=True, check=False)
    if r.returncode != 0:
        pytest.skip(f"partes no tiene {ref}:{fichero}: "
                    f"{r.stderr.decode(errors='replace').strip()}")
    return r.stdout


def _nuestra(fichero: str) -> bytes:
    return (TRANSFER / "application" / "services" / fichero).read_bytes()


@pytest.mark.parametrize("fichero", COPIAS)
def test_f037_copia_literal_del_commit_copiado(fichero):
    assert _nuestra(fichero) == _de_partes(COMMIT_COPIADO, fichero), (
        f"{fichero} ya no es copia literal de partes@{COMMIT_COPIADO[:7]}")


@pytest.mark.parametrize("fichero", COPIAS)
def test_f037_copia_igual_a_la_ref_vigilada(fichero):
    assert _nuestra(fichero) == _de_partes(REF_VIGILADA, fichero), (
        f"{fichero} diverge de partes {REF_VIGILADA}: ver design §12")
