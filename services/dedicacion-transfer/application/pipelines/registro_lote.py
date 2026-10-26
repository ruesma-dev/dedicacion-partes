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
- F-030: una petición puede traer, en tercer lugar, sus incidencias; sin
  ellas, la petición de siempre `(obra, lineas)`. F-062: en cuarto lugar,
  su `ContextoRachas` (el pipeline de esa obra lo lleva, como en suelto).
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

    def proponer(self, peticiones: list[dict]) -> list[dict | Exception]:
        """R34: las propuestas de cada petición (`{empresa, obra, ano, mes,
        lineas}`, como `RegistroPipeline.proponer`), en su orden:
        `{ok: true, propuestas}` (las mismas que la suelta, R21) o `{ok:
        false, error}` (obra de otra empresa); un fallo propio de una obra,
        su excepción. Una lectura compartida que falla sube (R24)."""
        memoria = LecturasDelLote(self._cli, self._limite)
        memoria.precargar_propuestas(peticiones, self._st)

        def una(p: dict) -> dict:
            r = RegistroPipeline(cliente=memoria,
                                 settings=self._st).proponer(**p)
            if not r["ok"]:
                return r
            return {"ok": True, "propuestas": r["propuestas"]}
        return self._por_obra(memoria, [(lambda p=p: una(p))
                                        for p in peticiones])

    def preflight(self, peticiones: list[tuple]
                  ) -> list[Preflight | Exception]:
        """R19: un resultado por petición, en su orden. Cada petición es
        `(obra, lineas)`, `(obra, lineas, incidencias)` (F-030) o `(obra,
        lineas, incidencias, contexto)` (F-062)."""
        memoria = LecturasDelLote(self._cli, self._limite)
        memoria.precargar(peticiones, self._st)

        def una(obra: ObraEntrada, lineas: list[LineaEntrada], *resto):
            kw = {"incidencias": resto[0]} if resto and resto[0] else {}
            contexto = resto[1] if len(resto) > 1 else None
            return RegistroPipeline(cliente=memoria, settings=self._st,
                                    contexto=contexto).preflight(
                obra=obra, lineas=lineas, **kw)
        return self._por_obra(memoria, [(lambda p=p: una(*p))
                                        for p in peticiones])
