# domain/vinculados.py
"""Vínculo de los recursos no persona con su trabajador (F-044, R2-R4;
docs/ARCHITECTURE.md#regla-vinculado).

El vínculo es el campo extendido «Recurso Asociado» de Sigrid (`defext` 46,
D2): su valor es el `res.ide` del trabajador. Aquí se decide, en UNA función
pura, quién es de quién; no se casa por nombre (D2): el campo cubre los
activos y un segundo criterio solo daría discrepancias.

- `vincular` reparte los candidatos en vinculados, sin campo, hacia quien no
  es trabajador de dedicación y de un tipo excluido (D1b), en orden de `ide`
  para que el resultado no dependa del orden de la lectura.
- `vigentes`: los que cuentan en un mes, con la regla de vigencia de los
  trabajadores sobre su propia baja (R4).
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from domain.models import RecursoVinculado
from domain.vigencia import vigente_en

#: Estados del vínculo que se guardan en `recurso_vinculado.estado_vinculo`.
ESTADO_VINCULADO = "vinculado"
ESTADO_SIN_CAMPO = "sin_campo"
ESTADO_NO_TRABAJADOR = "no_trabajador"


@dataclass(frozen=True)
class ResultadoVinculos:
    """Lo que decide `vincular`: los vinculados con su trabajador y los que
    no se vinculan, por qué y en orden de `ide`."""

    vinculos: tuple[tuple[RecursoVinculado, int], ...] = ()
    sin_campo: tuple[RecursoVinculado, ...] = ()
    hacia_no_trabajador: tuple[RecursoVinculado, ...] = ()
    excluidos: tuple[RecursoVinculado, ...] = ()

    def por_trabajador(self) -> dict[int, list[RecursoVinculado]]:
        """Trabajador → TODOS sus vinculados (R2), en orden de `ide`."""
        out: dict[int, list[RecursoVinculado]] = {}
        for v, trabajador in self.vinculos:
            out.setdefault(trabajador, []).append(v)
        return out

    def estado(self, ide: int) -> str | None:
        """El estado que se guarda del recurso `ide`; None si es de un tipo
        excluido o no ha llegado (no se guarda)."""
        if any(v.ide == ide for v, _ in self.vinculos):
            return ESTADO_VINCULADO
        if any(v.ide == ide for v in self.sin_campo):
            return ESTADO_SIN_CAMPO
        if any(v.ide == ide for v in self.hacia_no_trabajador):
            return ESTADO_NO_TRABAJADOR
        return None


def _tipo(valor: str | None) -> str:
    return (valor or "").strip().upper()


def vincular(candidatos: Iterable[RecursoVinculado], trabajadores: set[int],
             tipos_excluidos: Iterable[str]) -> ResultadoVinculos:
    """R2-R3: el vinculado es del trabajador cuyo `ide` es el valor de su
    campo. Primero el tipo excluido (D1b), luego el campo vacío y luego el
    que apunta a un recurso que no está en `trabajadores`."""
    excluidos = {_tipo(t) for t in tipos_excluidos}
    vinculos: list[tuple[RecursoVinculado, int]] = []
    sin_campo: list[RecursoVinculado] = []
    no_trabajador: list[RecursoVinculado] = []
    fuera: list[RecursoVinculado] = []
    for v in sorted(candidatos, key=lambda c: c.ide):
        if _tipo(v.tipo) in excluidos:
            fuera.append(v)
        elif not v.principal_ide:
            sin_campo.append(v)
        elif int(v.principal_ide) not in trabajadores:
            no_trabajador.append(v)
        else:
            vinculos.append((v, int(v.principal_ide)))
    return ResultadoVinculos(vinculos=tuple(vinculos),
                             sin_campo=tuple(sin_campo),
                             hacia_no_trabajador=tuple(no_trabajador),
                             excluidos=tuple(fuera))


def codigos(recursos: Iterable[RecursoVinculado]) -> list[str]:
    """Los códigos de unos recursos, ordenados (lo que publica el preview,
    sin nombres); sin código, `R<ide>`."""
    return sorted(v.cod or f"R{v.ide}" for v in recursos)


def vigentes(vinculados: Iterable[RecursoVinculado], anio: int,
             mes: int) -> list[RecursoVinculado]:
    """R4: los que cuentan en el mes, por su propia baja, en su orden."""
    return [v for v in vinculados
            if vigente_en(True, v.fecha_baja, anio, mes)]
