# tests/test_f032_empresas_sigrid.py
"""Tests offline de F-032: nombres de empresa sincronizados desde Sigrid.

Trazabilidad con los `acceptance` de F-032 en `harness/features.json`
(sdd=false), numerados en su orden:

  R1  el sync lee `auxemp` por sigrid-api y lo guarda en la tabla `empresa`
      declarada en el ORM, sin DDL a mano;
  R2  `GET /api/v1/empresas` toma el nombre de esa tabla (alta o cambio de
      nombre en Sigrid llega con el siguiente sync);
  R3  sin `empresas.nombres` en `config.yaml`; «Empresa N» solo si la
      empresa no está en la tabla;
  R4  el preview del sync informa de las empresas leídas;
  R5  una empresa de baja o desactivada con trabajadores activos sale
      marcada «(de baja)», nunca oculta.

R6 (sync real y selector en local) es MANUAL; R7 es la review.

Nada abre un socket ni una conexión: Sigrid es un doble que devuelve
listas, el repositorio trabaja contra una sesión doble y el DDL se compila
con el dialecto PostgreSQL sin motor. Los módulos que F-032 crea o amplía
se importan DENTRO de cada test (patrón de `test_f023_sync_empresa.py`).
"""
from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.dialects import postgresql

DIALECTO = postgresql.dialect()
SQL_EMPRESAS = "SELECT ... FROM dbo.auxemp AS emp"


def _fila(numemp: Any, **cambios: Any) -> dict[str, Any]:
    """Fila de `sync.empresas.sql`: empresa en alta y activa."""
    fila: dict[str, Any] = {
        "numemp": numemp,
        "cod": f"E{numemp}",
        "nombre": f"EMPRESA {numemp} SL",
        "fecbaj": 0,
        "desact": 0,
    }
    fila.update(cambios)
    return fila


# --- R1 · tabla `empresa` en el ORM, sin DDL a mano ---------------------------


def test_f032_r1_tabla_empresa_declarada_en_el_orm() -> None:
    from infrastructure.db.orm_models import Base, EmpresaORM

    tabla = EmpresaORM.__table__
    assert tabla.name == "empresa"
    assert Base.metadata.tables["empresa"] is tabla
    assert [c.name for c in tabla.primary_key.columns] == ["numemp"]
    tipos = {c.name: c.type.compile(dialect=DIALECTO) for c in tabla.columns}
    assert tipos == {
        "numemp": "INTEGER",
        "cod": "TEXT",
        "nombre": "TEXT",
        "fecbaj": "INTEGER",
        "desact": "INTEGER",
        "sync_en": "TIMESTAMP WITH TIME ZONE",
    }


def test_f032_r1_numemp_no_es_autoincremental() -> None:
    """La clave es el `numemp` de Sigrid: nunca la genera PostgreSQL."""
    from infrastructure.db.orm_models import EmpresaORM

    assert EmpresaORM.__table__.columns["numemp"].autoincrement is False


def test_f032_r1_esquema_la_crea_create_all_y_no_un_alter() -> None:
    """Sobre una base sin la tabla, `alters_faltantes` no emite nada para
    ella (la crea `create_all` al arrancar); sobre una base que la tiene
    entera, tampoco."""
    from infrastructure.db.esquema import alters_faltantes
    from infrastructure.db.orm_models import Base

    al_dia = {t.name: {c.name for c in t.columns}
              for t in Base.metadata.tables.values()}
    sin_empresa = {k: v for k, v in al_dia.items() if k != "empresa"}
    assert alters_faltantes(Base.metadata, sin_empresa) == []
    assert alters_faltantes(Base.metadata, al_dia) == []


# --- R5 · regla «de baja» (dominio) ------------------------------------------


@pytest.mark.parametrize(("fecbaj", "desact", "de_baja"), [
    (0, 0, False),
    (None, None, False),
    (None, 0, False),
    (20240101, 0, True),          # fecha de baja informada
    (1, None, True),
    (0, 1, True),                 # desactivada
    (20240101, 1, True),
    (-1, 0, False),               # una fecha no positiva no es baja
    (0, 2, False),                # desact solo vale 0 / 1
])
def test_f032_r5_empresa_de_baja(fecbaj: Any, desact: Any, de_baja: bool) -> None:
    from domain.empresas import empresa_de_baja

    assert empresa_de_baja(fecbaj, desact) is de_baja
