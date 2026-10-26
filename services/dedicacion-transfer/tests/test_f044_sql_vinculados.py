# tests/test_f044_sql_vinculados.py
"""F-044 · SQL del transfer para los recursos vinculados.

- R27 (T4): `cuentas_del_presupuesto(obra_ide)`, UNA lectura parametrizada
  (design §7.1): el código de la cuenta de cada partida del presupuesto que
  la tiene; nada concatenado; un fallo o `truncated` sube.

Sin red ni BBDD: `_read` sustituido por un doble.
"""
from __future__ import annotations

import pytest
from infrastructure.sigrid.sigrid_write_client import (
    SigridWriteClient,
    medir_lecturas,
)


class _Falso:
    def __init__(self, filas: list[dict] | None = None,
                 fallo: Exception | None = None) -> None:
        self.filas = filas or []
        self.fallo = fallo
        self.llamadas: list[tuple[str, list]] = []

    def __call__(self, sql: str, params: list) -> list[dict]:
        self.llamadas.append((sql, params))
        if self.fallo is not None:
            raise self.fallo
        return [dict(f) for f in self.filas]


def _cliente(falso: _Falso) -> SigridWriteClient:
    cli = SigridWriteClient(base_url="http://sigrid.invalid",
                            function_key="sin-clave", database="ruesma")
    cli._read = falso                        # type: ignore[method-assign]
    return cli


# ================================ R27 ==================================== #
def test_f044_r27_sql_de_las_cuentas_del_presupuesto():
    falso = _Falso()
    _cliente(falso).cuentas_del_presupuesto(694001)
    [(sql, params)] = falso.llamadas
    assert " ".join(sql.split()) == (
        "SELECT p.ide AS ide, cc.cod AS cod FROM obrparpar p "
        "JOIN con cc ON cc.ide = p.caaide "
        "WHERE p.obride = ? AND ISNULL(p.caaide,0) <> 0")
    assert params == [694001]


def test_f044_r27_mapea_ide_y_codigo():
    falso = _Falso([{"ide": 70001, "cod": " 0694.CI.4.13 "},
                    {"ide": "70002", "cod": "0694.CI.4.14"},
                    {"ide": 70003, "cod": None}])
    assert _cliente(falso).cuentas_del_presupuesto("694001") == {
        70001: "0694.CI.4.13", 70002: "0694.CI.4.14", 70003: None}
    assert falso.llamadas[0][1] == [694001]


def test_f044_r27_una_lectura_medida_con_su_nombre():
    with medir_lecturas() as m:
        _cliente(_Falso([{"ide": 1, "cod": "X.CI.1"}])
                 ).cuentas_del_presupuesto(5)
    assert [(l.nombre, l.filas) for l in m.lecturas] == [
        ("cuentas_del_presupuesto", 1)]


def test_f044_r27_un_fallo_sube():
    falso = _Falso(fallo=RuntimeError(
        "sigrid-api devolvio una respuesta truncada"))
    with pytest.raises(RuntimeError, match="truncada"):
        _cliente(falso).cuentas_del_presupuesto(5)
