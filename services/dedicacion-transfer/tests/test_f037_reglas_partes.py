# tests/test_f037_reglas_partes.py
"""F-037 · Modelos y reglas puras copiadas de la F-031 de `partes`.

Trazabilidad con `specs/F-037-asiento-analitico-obra/requirements.md`:
R2-R5 (cuenta analítica: `cuenta_analitica.py`), R10, R13 y R15 (parte del
periodo: `estado_parte.py`) y el contrato de los modelos (R6, R15). Los
casos son los de `test_f031_estado_parte.py`, `test_f031_cuenta_partida.py`
y `test_f021_cuenta_analitica.py` de `partes`, renombrados: las dos reglas
son COPIA LITERAL (design §12), así que se prueban igual que allí.

Datos SINTÉTICOS: códigos de centro y subcuentas inventados.
"""
from __future__ import annotations

import dataclasses

import pytest
from domain.models.registro_models import (
    AccionLinea, HoraRecurso, ParteDestino, ParteSigrid, PartidaCuenta,
)

REG, CER, IMP = 1, 3, 10


# ============================ modelos (T1) ============================ #

def test_f037_r15_parte_sigrid_y_partida_cuenta_inmutables():
    p = ParteSigrid(ide=7, cod="PT26/00007", est=REG)
    assert (p.ide, p.cod, p.est) == (7, "PT26/00007", REG)
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.est = CER  # type: ignore[misc]
    q = PartidaCuenta(ide=80001, cod="CI.1.10", caa_cod="0678.CIMO03")
    assert (q.ide, q.cod, q.caa_cod) == (80001, "CI.1.10", "0678.CIMO03")
    with pytest.raises(dataclasses.FrozenInstanceError):
        q.caa_cod = None  # type: ignore[misc]


def test_f037_r2_hora_recurso_posicional_sigue_valiendo():
    """Los `HoraRecurso(...)` posicionales de antes de F-037 no cambian:
    sin cuenta y sin ser el tipo por defecto."""
    h = HoraRecurso(5, "MENC", None, 9000.0)
    assert (h.caa_cod, h.defecto) == (None, False)
    h2 = HoraRecurso(5, "MENC", None, 9000.0, caa_cod="00000.CIMO03",
                     defecto=True)
    assert (h2.caa_cod, h2.defecto) == ("00000.CIMO03", True)


def test_f037_r6_accion_lleva_el_contrato_caa_de_partes():
    a = AccionLinea(registro_id=1, accion="escribir", ano=2026, mes=7,
                    fecha_int=20260731)
    assert (a.caa_ide, a.caa_cod, a.caa_motivo, a.caa_aviso, a.caa_origen,
            a.caa_nota) == (0, None, None, None, None, None)


def test_f037_r15_parte_destino_lleva_estado_y_complementario():
    p = ParteDestino(ano=2026, mes=7)
    assert (p.obra_cod, p.estado, p.complementario, p.cerrados,
            p.del_periodo, p.aviso) == (None, None, False, [], [], None)
    # Las listas no se comparten entre instancias.
    p.cerrados.append("PT26/00004")
    assert ParteDestino(ano=2026, mes=7).cerrados == []


def test_f037_r15_ajustes_de_estado_solo_para_textos():
    from config.settings import Settings

    campos = Settings.model_fields
    assert campos["est_parte_cerrado"].default == CER
    assert campos["est_parte_cerrado"].alias == "EST_PARTE_CERRADO"
    assert campos["est_parte_imputado"].default == IMP
    assert campos["est_parte_imputado"].alias == "EST_PARTE_IMPUTADO"
    assert campos["est_parte_activo"].default == REG
    from pathlib import Path

    ejemplo = (Path(__file__).resolve().parents[1] / ".env.example"
               ).read_text(encoding="utf-8")
    assert "EST_PARTE_CERRADO=3" in ejemplo
    assert "EST_PARTE_IMPUTADO=10" in ejemplo
