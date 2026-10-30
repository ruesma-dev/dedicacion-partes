# application/pipelines/poner_a_cero.py
"""F-054, parte B: poner a 0 las sobrantes que el usuario confirma (R35-R36;
design §6.3; ARCHITECTURE.md#regla-obra-cero).

`PonerACero.ejecutar(empresa, ano, mes, lineas)`, con las líneas tal como
las publicó el preflight (`{hmores_ide, recurso_ide, hora, vinculado, can,
synckey}`):

1. Relee cada una (`lineas_para_editar`, F-051 R12) y, en pruebas, los
   partes del periodo de la obra de pruebas.
2. Guarda previa: sigue siendo del mismo recurso, con la hora enviada (`M*`
   para el trabajador; la suya para el vinculado, F-044 R24), el mismo
   `can` y la misma `synckey`, no es de otro sistema, sin enlaces, en un
   parte En registro y, en pruebas, en la obra de pruebas. Si no, `omitida`
   con su motivo y sin escribir.
3. `stmt_poner_a_cero` de F-051 (`can` y `tot` a 0, con su guarda en el
   SQL); el cliente escribe en lotes de `SIGRID_MAX_STATEMENTS`. Relectura
   (`lineas_registradas`): la que no quedó a 0 es `omitida`.

Log antes/después por línea (el de F-051). Ningún `DELETE`. Es aparte del
`a_cero` por obra de F-051: estas líneas no tienen asignación.
"""
from __future__ import annotations

import logging

from application.pipelines.registro_pipeline import _fila, _traza
from infrastructure.sigrid.sigrid_write_client import PREFIJO_SYNCKEY

logger = logging.getLogger(__name__)

MOTIVO_NO_ESTA = "ya no está en Sigrid"
MOTIVO_OTRO_RECURSO = "ya no es de ese recurso"
MOTIVO_OTRA_HORA = "su hora ya no es la del preflight"
MOTIVO_CAMBIADA = "cambió desde el preflight (can o synckey)"
MOTIVO_OTRO_SISTEMA = "es de otro sistema"
MOTIVO_ENLAZADA = "tiene enlaces de Sigrid"
MOTIVO_PARTE_CERRADO = "su parte no está En registro"
MOTIVO_FUERA_PRUEBAS = "no está en la obra de pruebas"
MOTIVO_NO_QUEDO = "la relectura no la da a 0"

_EPS = 0.000001


def _texto(v) -> str:
    return (v or "").strip()


class PonerACero:
    def __init__(self, *, cliente, settings) -> None:
        self._cli = cliente
        self._st = settings

    def _motivo(self, p: dict, ls, partes_pruebas: set[int] | None
                ) -> str | None:
        """La guarda previa (paso 2): None si la línea se puede poner a 0."""
        if ls is None:
            return MOTIVO_NO_ESTA
        if int(ls.reside) != int(p["recurso_ide"]):
            return MOTIVO_OTRO_RECURSO
        hora = _texto(ls.hora_codigo)
        if hora != _texto(p.get("hora")) or (
                not p.get("vinculado") and not hora.startswith("M")):
            return MOTIVO_OTRA_HORA
        if (abs(float(ls.can or 0) - float(p["can"] or 0)) >= _EPS
                or _texto(ls.synckey) != _texto(p.get("synckey"))):
            return MOTIVO_CAMBIADA
        if ls.synckey and not _texto(ls.synckey).startswith(PREFIJO_SYNCKEY):
            return MOTIVO_OTRO_SISTEMA
        if ls.enlazada:
            return MOTIVO_ENLAZADA
        if ls.parte_est != int(self._st.est_parte_activo):
            return MOTIVO_PARTE_CERRADO
        if partes_pruebas is not None and ls.hmoide not in partes_pruebas:
            return MOTIVO_FUERA_PRUEBAS
        return None

    def _partes_pruebas(self, empresa: int, ano: int, mes: int) -> set[int]:
        obra = self._cli.obra_por_codigo(self._st.obra_pruebas_cod, empresa)
        if obra is None or not obra.ide:
            return set()
        return {int(p.ide) for p in
                self._cli.partes_del_periodo(int(obra.ide), ano, mes)}

    def ejecutar(self, empresa: int, ano: int, mes: int,
                 lineas: list[dict]) -> dict:
        pedidas: dict[int, dict] = {}
        for p in lineas:
            pedidas.setdefault(int(p["hmores_ide"]), p)
        if not pedidas:
            return {"ok": True, "puestas": [], "omitidas": []}
        leidas = self._cli.lineas_para_editar(sorted(pedidas))
        partes = (self._partes_pruebas(empresa, ano, mes)
                  if self._st.obra_pruebas_forzar else None)
        omitidas: list[dict] = []
        statements: list[dict] = []
        trazas: list[dict] = []
        for ide, p in pedidas.items():
            ls = leidas.get(ide)
            motivo = self._motivo(p, ls, partes)
            if motivo:
                logger.info("[registro] no pone a 0 ide=%s: %s", ide, motivo)
                omitidas.append({"hmores_ide": ide, "motivo": motivo})
                continue
            statements.append(self._cli.stmt_poner_a_cero(
                ide=ide, reside=int(ls.reside), can_leido=ls.can,
                synckey_leida=ls.synckey,
                hora=_texto(ls.hora_codigo) if p.get("vinculado") else None))
            trazas.append(_traza("pone a 0", 0, ls,
                                 {**_fila(ls), "can": 0.0, "tot": 0.0}))
        if not statements:
            return {"ok": True, "puestas": [], "omitidas": omitidas}
        self._cli.escribir(statements)
        _, releidas = self._cli.lineas_registradas(
            [], [t["ide"] for t in trazas])
        puestas: list[dict] = []
        for t in trazas:
            r = releidas.get(t["ide"])
            if r is None or abs(float(r.can or 0)) >= _EPS:
                logger.warning("[registro] no quedó a 0 ide=%s", t["ide"])
                omitidas.append({"hmores_ide": t["ide"],
                                 "motivo": MOTIVO_NO_QUEDO})
                continue
            logger.info("[registro] puesta a 0 ide=%s parte=%s", t["ide"],
                        t["parte_cod"])
            puestas.append({"hmores_ide": t["ide"],
                            "parte_cod": t["parte_cod"],
                            "antes": t["antes"], "despues": t["despues"]})
        return {"ok": True, "puestas": puestas, "omitidas": omitidas}
