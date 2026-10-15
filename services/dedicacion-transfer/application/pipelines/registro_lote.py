# application/pipelines/registro_lote.py
"""Preflight de VARIAS obras en una petición (F-055, R19-R25; design §5.3).

`RegistroLote.preflight` precarga agrupado lo que van a leer las obras
(`LecturasDelLote`) y luego corre, por obra y en paralelo (hasta el límite
de `SIGRID_LECTURAS_PARALELAS`), el MISMO `RegistroPipeline.preflight` que
la petición suelta, con la memoria como cliente: el resultado de cada obra
es el de su petición suelta con los mismos datos de Sigrid (R21).

- Un fallo propio de una obra (no encontrada, empresas mezcladas…) vuelve
  como excepción en SU posición; el resto sigue (R24).
- Una lectura agrupada que falla hace fallar el lote entero (R24): la
  excepción sube.
- Sin estado entre llamadas: memoria y pipelines son de cada llamada
  (F-025 R9, D4). `ejecutar` no va en lote (D6).
"""
from __future__ import annotations

import contextvars
from concurrent.futures import ThreadPoolExecutor

from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.lecturas_lote import LecturasDelLote
from domain.models.registro_models import (
    LineaEntrada, ObraEntrada, Preflight,
)


class RegistroLote:
    def __init__(self, *, cliente, settings, limite: int | None = None) -> None:
        self._cli = cliente
        self._st = settings
        self._limite = int(limite if limite is not None
                           else settings.sigrid_lecturas_paralelas)

    def _por_obra(self, memoria: LecturasDelLote, tareas: list) -> list:
        """Cada tarea en el pool, con su copia del contexto (medición de
        F-055 R1); su excepción vuelve en su posición."""
        def protegida(tarea):
            try:
                return tarea()
            except Exception as exc:                 # noqa: BLE001
                return exc
        with ThreadPoolExecutor(max_workers=self._limite) as pool:
            futuros = [pool.submit(contextvars.copy_context().run,
                                   protegida, t) for t in tareas]
        return [f.result() for f in futuros]

    def preflight(self, peticiones: list[tuple[ObraEntrada,
                                               list[LineaEntrada]]]
                  ) -> list[Preflight | Exception]:
        """R19: un resultado por petición, en su orden."""
        memoria = LecturasDelLote(self._cli, self._limite)
        memoria.precargar(peticiones, self._st)
        return self._por_obra(memoria, [
            (lambda o=obra, ls=lineas: RegistroPipeline(
                cliente=memoria, settings=self._st).preflight(
                    obra=o, lineas=ls))
            for obra, lineas in peticiones])
