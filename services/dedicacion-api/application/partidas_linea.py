# application/partidas_linea.py
"""Catálogo, propuesta y partida elegida de UNA línea del cuadrante, para el
selector de partida (F-050, R17, docs/ARCHITECTURE.md#regla-partida).

La api no propone ni clasifica: pide al transfer (`POST
/api/partidas/propuesta`) el catálogo con el mayor de cada partida y la
propuesta, y solo busca en esa lista el mayor de la elegida para decidir el
botón que sale preelegido (`ambito`). Una entrada VAR tiene la partida fija
(docs/ARCHITECTURE.md#regla-var): no se llama al transfer.
"""
from __future__ import annotations

from typing import Any, Protocol

from domain.errors import LineaNoEncontrada
from domain.ports import UnitOfWork

from application.use_cases import _periodo_o_error, _trabajador_o_error

#: Clave de la única línea que se manda al transfer.
CLAVE = "linea"


class PropuestaGateway(Protocol):
    def propuesta_partidas(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Respuesta de `POST /api/partidas/propuesta` o
        `PropuestaNoDisponible`."""
        ...


class PartidasDeLinea:
    def __init__(self, transfer: PropuestaGateway) -> None:
        self._transfer = transfer

    def ejecutar(
        self,
        uow: UnitOfWork,
        anio: int,
        mes: int,
        trabajador_ide: int,
        obra_ide: int,
        es_postventa: bool,
        *,
        empresa_obras: int,
    ) -> dict[str, Any]:
        periodo_id, _ = _periodo_o_error(uow, anio, mes)
        trabajador = _trabajador_o_error(uow, trabajador_ide)
        linea = next(
            (ln for ln in uow.asignaciones.lineas_de_trabajador(
                periodo_id, trabajador_ide)
             if ln.clave() == (obra_ide, es_postventa)),
            None,
        )
        if linea is None:
            raise LineaNoEncontrada(
                f"El trabajador {trabajador_ide} no tiene la obra {obra_ide} "
                f"(postventa={es_postventa}) en el periodo"
            )
        if linea.partida_fija:
            # La entrada VAR guarda su partida en `obra.registro_paride`, y
            # su `ide` en el cuadrante es esa partida en negativo
            # (`domain.obras.ide_entrada`).
            return {"partidas": [], "partidas_postventa": [], "ambito": None,
                    "propuesta": None, "elegida": None,
                    "fija": {"ide": -linea.obra_ide, "cod": linea.cod,
                             "res": linea.descripcion}}
        r = self._transfer.propuesta_partidas({
            "empresa": empresa_obras, "ano": anio, "mes": mes,
            "obra": {"ide": linea.obra_ide, "codigo": linea.cod,
                     "nombre": linea.descripcion},
            "lineas": [{"clave": CLAVE, "recurso_ide": trabajador.ide,
                        "nombre": trabajador.nombre,
                        "categoria": trabajador.categoria,
                        "es_postventa": es_postventa}],
        })
        elegida = (
            {"ide": linea.partida_ide, "cod": linea.partida_cod,
             "res": linea.partida_res}
            if linea.partida_ide is not None else None
        )
        catalogo = r["partidas_postventa"] if es_postventa else r["partidas_obra"]
        mayor_elegida = next(
            (p["mayor"] for p in catalogo
             if elegida is not None and p["ide"] == elegida["ide"]),
            None,
        )
        if mayor_elegida is None:
            ambito = r["mayor_inicial"][CLAVE]
        else:
            # OTRO no tiene botón: sale en «Todas» (None).
            ambito = None if mayor_elegida == "OTRO" else mayor_elegida
        return {
            "partidas": r["partidas_obra"],
            "partidas_postventa": r["partidas_postventa"],
            "ambito": ambito,
            "propuesta": r["propuestas"][CLAVE],
            "elegida": elegida,
            "fija": None,
        }
