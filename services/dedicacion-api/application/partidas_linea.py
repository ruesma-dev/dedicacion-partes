# application/partidas_linea.py
"""Catálogo, propuesta y partida elegida de UNA línea del cuadrante, para el
selector de partida (F-050, R17, docs/ARCHITECTURE.md#regla-partida).

La api no propone ni clasifica: pide al transfer (`POST
/api/partidas/propuesta`) el catálogo con el mayor de cada partida y la
propuesta, y solo busca en esa lista el mayor de la elegida para decidir el
botón que sale preelegido (`ambito`). Una entrada VAR tiene la partida fija
(docs/ARCHITECTURE.md#regla-var): no se llama al transfer.

F-055 (R15, R18): la propuesta que devuelve el transfer para una línea sin
elegida se GUARDA en su asignación (y reescribe la que hubiera), sin evento.

F-044 (R8, R9): con `vinculado_ide`, lo mismo para la SUBFILA de ese
vinculado: la línea va al transfer con la elegida del titular (`paride`) y
ese vinculado; vuelven el catálogo de la línea y la propuesta de la subfila,
que se guarda en `asignacion_vinculado` si sigue sin elegida.
"""
from __future__ import annotations

from typing import Any, Protocol

from domain.errors import LineaNoEncontrada
from domain.models import Linea, SubfilaVinculado
from domain.ports import UnitOfWork

from application.registro_sigrid import (
    es_metodo_de_propuesta,
    es_metodo_de_propuesta_vinculado,
)
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
        vinculado_ide: int | None = None,
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
        subfila = None
        if vinculado_ide is not None:
            subfila = next((v for v in linea.vinculados
                            if v.vinculado_ide == vinculado_ide), None)
            if subfila is None:
                raise LineaNoEncontrada(
                    f"La línea de la obra {obra_ide} (postventa="
                    f"{es_postventa}) del trabajador {trabajador_ide} no "
                    f"tiene el vinculado {vinculado_ide}"
                )
        if linea.partida_fija:
            # La entrada VAR guarda su partida en `obra.registro_paride`, y
            # su `ide` en el cuadrante es esa partida en negativo
            # (`domain.obras.ide_entrada`).
            return {"partidas": [], "partidas_postventa": [], "ambito": None,
                    "propuesta": None, "elegida": None,
                    "fija": {"ide": -linea.obra_ide, "cod": linea.cod,
                             "res": linea.descripcion}}
        peticion: dict[str, Any] = {
            "clave": CLAVE, "recurso_ide": trabajador.ide,
            "nombre": trabajador.nombre, "categoria": trabajador.categoria,
            "es_postventa": es_postventa}
        if subfila is not None:
            peticion.update(peticion_de_subfilas(linea, [subfila]))
        r = self._transfer.propuesta_partidas({
            "empresa": empresa_obras, "ano": anio, "mes": mes,
            "obra": {"ide": linea.obra_ide, "codigo": linea.cod,
                     "nombre": linea.descripcion},
            "lineas": [peticion],
        })
        if subfila is not None:
            return self._de_subfila(uow, periodo_id, trabajador_ide, linea,
                                    subfila, r)
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
        propuesta = r["propuestas"][CLAVE]
        if elegida is None and propuesta is not None \
                and es_metodo_de_propuesta(propuesta.get("metodo")):
            uow.asignaciones.guardar_propuesta(
                periodo_id, trabajador_ide, (obra_ide, es_postventa),
                propuesta)
            uow.commit()
        if mayor_elegida is None:
            ambito = r["mayor_inicial"][CLAVE]
        else:
            # OTRO no tiene botón: sale en «Todas» (None).
            ambito = None if mayor_elegida == "OTRO" else mayor_elegida
        return {
            "partidas": r["partidas_obra"],
            "partidas_postventa": r["partidas_postventa"],
            "ambito": ambito,
            "propuesta": propuesta,
            "elegida": elegida,
            "fija": None,
        }

    @staticmethod
    def _de_subfila(uow: UnitOfWork, periodo_id: int, trabajador_ide: int,
                    linea: Linea, subfila: SubfilaVinculado,
                    r: dict[str, Any]) -> dict[str, Any]:
        """La respuesta del selector para la subfila (R8, R9): su elegida,
        su propuesta (un transfer sin F-044 no la da: None) guardada si no
        hay elegida, y el botón preelegido por el mayor de la elegida o, sin
        ella, de la propuesta; sin ninguna, «CI» (la partida de un
        vinculado es una CI, D4) o «Todas» en postventa."""
        propuesta = (r.get("vinculados") or {}).get(CLAVE, {}).get(
            str(subfila.vinculado_ide))
        elegida = (
            {"ide": subfila.partida_ide, "cod": subfila.partida_cod,
             "res": subfila.partida_res}
            if subfila.partida_ide is not None else None
        )
        if elegida is None and propuesta is not None \
                and es_metodo_de_propuesta_vinculado(propuesta.get("metodo")):
            uow.asignaciones.guardar_propuesta_vinculado(
                periodo_id, trabajador_ide, linea.clave(),
                subfila.vinculado_ide, propuesta)
            uow.commit()
        catalogo = (r["partidas_postventa"] if linea.es_postventa
                    else r["partidas_obra"])
        buscada = (elegida or {}).get("ide") or (propuesta or {}).get("paride")
        mayor = next((p["mayor"] for p in catalogo
                      if buscada is not None and p["ide"] == buscada), None)
        if mayor is None:
            ambito = None if linea.es_postventa else "CI"
        else:
            ambito = None if mayor == "OTRO" else mayor
        return {
            "partidas": r["partidas_obra"],
            "partidas_postventa": r["partidas_postventa"],
            "ambito": ambito,
            "propuesta": propuesta,
            "elegida": elegida,
            "fija": None,
        }


def peticion_de_subfilas(linea: Linea, subfilas: list[SubfilaVinculado]
                         ) -> dict[str, Any]:
    """Lo que una línea del transfer gana para proponer sus subfilas (R9,
    contrato de T5): la elegida del titular (`paride`, si la tiene) y los
    vinculados. Lo usan el selector y la cola del mes."""
    extra: dict[str, Any] = {}
    if linea.partida_ide is not None:
        extra["paride"] = linea.partida_ide
    extra["vinculados"] = [
        {"recurso_ide": v.vinculado_ide, "tipo": v.tipo, "categoria": None,
         "cod": v.cod} for v in subfilas]
    return extra
