# tests/test_f026_sync_recurso.py
"""Tests offline de F-026: el sync de trabajadores parte del RECURSO.

Trazabilidad con `specs/F-026-recursos-sin-ficha-empleado/requirements.md`:
R1 (consulta en `config.yaml`), R2-R4 (una fila por recurso, ficha
opcional, aviso de posible misma persona), R5 (columnas obligatorias), R6
(claves retiradas del preview), R12-R13 (ventana de bajas) y R17 (claves
nuevas del preview).

Nada abre un socket ni una conexión: las filas de Sigrid son dicts y el
`SigridGateway` es un doble que devuelve listas. Los módulos de F-026 se
importan dentro de los tests, para que cada tarea se verifique con su `-k`.
"""
from __future__ import annotations

import re
from typing import Any


# --- R1: la consulta versionada parte de dbo.res ----------------------------


def _config_empleados() -> dict[str, Any]:
    from config.settings import cargar_config

    return cargar_config()["sync"]["empleados"]


def _plano(sql: str) -> str:
    return " ".join(sql.split())


#: Alias de R1, en orden, con la expresión de la que salen (design §6).
ALIAS_R1 = [
    ("res.ide", "ide"),
    ("rcon.cod", "cod"),
    ("rcon.res", "nombre"),
    ("emp.dni", "dni"),
    ("res.cif", "cif"),
    ("rcon.emp", "empresa"),
    ("tip.res", "categoria"),
    ("COALESCE(rest.res, CAST(rcon.est AS VARCHAR(16)))", "estado_recurso"),
    ("NULLIF(rcon.fecbaj, 0)", "fecha_baja"),
    ("uh.fecbaj", "baja_laboral"),
    ("hm.cod", "cod_hora_mes"),
    ("hm.pre", "importe_mes"),
]


def _select(sql: str) -> str:
    return sql.split(" FROM dbo.res AS res ", 1)[0]


def _columnas(select: str) -> list[str]:
    """Columnas del SELECT, partiendo por las comas de nivel 0."""
    columnas, actual, nivel = [], "", 0
    for caracter in select.removeprefix("SELECT "):
        nivel += {"(": 1, ")": -1}.get(caracter, 0)
        if caracter == "," and nivel == 0:
            columnas.append(actual.strip())
            actual = ""
        else:
            actual += caracter
    return [*columnas, actual.strip()]


def test_f026_r1_parte_de_res_y_filtra_personas() -> None:
    sql = _plano(_config_empleados()["sql"])
    assert " FROM dbo.res AS res JOIN dbo.con AS rcon ON rcon.ide = res.ide " in sql
    assert re.search(r"\) AS hm WHERE res\.cla = 1 ORDER BY ", sql)
    assert "FROM dbo.emp AS" not in sql
    assert "JOIN dbo.emp AS emp" in sql


def test_f026_r1_ficha_de_empleado_solo_por_left_join() -> None:
    sql = _plano(_config_empleados()["sql"])
    assert ("LEFT JOIN dbo.emp AS emp ON emp.ide = res.conide "
            "AND res.conide > 0") in sql
    assert len(re.findall(r"JOIN dbo\.emp AS", sql)) == 1
    assert "WHERE h.empide = emp.ide" in sql


def test_f026_r1_alias_exactos_y_en_orden() -> None:
    select = _select(_plano(_config_empleados()["sql"]))
    columnas = _columnas(select)
    assert [tuple(c.rsplit(" AS ", 1)) for c in columnas] == ALIAS_R1


def test_f026_r1_sin_empleado_ide_ni_alias_antiguos() -> None:
    sql = _plano(_config_empleados()["sql"])
    for retirado in ("empleado_ide", "recurso_ide", "empresa_recurso",
                     "baja_recurso", "emp.ide AS ide"):
        assert retirado not in sql, retirado
    # Ni rastro del `con` de la ficha de empleado: todo sale del `rcon`.
    assert not re.search(r"(?<![\w.])con\.", sql)


def test_f026_r1_sin_where_de_actividad() -> None:
    sql = _plano(_config_empleados()["sql"])
    principal = sql.split(") AS hm ", 1)[1]
    assert principal.startswith("WHERE res.cla = 1 ORDER BY ")
    assert "fecbaj" not in principal


def test_f026_r1_orden_por_empresa_nombre_y_recurso() -> None:
    sql = _plano(_config_empleados()["sql"])
    assert sql.endswith("ORDER BY rcon.emp, rcon.res, res.ide")


# --- R13: la clave de configuración nueva -----------------------------------


def test_f026_r13_config_excluye_solo_la_baja_anterior_a_la_ventana() -> None:
    cfg = _config_empleados()
    assert cfg["filtro_estado_recurso"] is True
    assert cfg["estados_recurso_excluidos"] == []
    assert cfg["excluir_baja_anterior_a_ventana"] is True
    assert "excluir_recurso_con_fecha_baja" not in cfg
