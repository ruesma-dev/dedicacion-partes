# infrastructure/sigrid/sigrid_write_client.py
"""Adaptador de Sigrid (lectura + ESCRITURA) vía sigrid-api.

Modelo del parte de trabajo (confirmado contra datos reales, 25/07/2026):
  con    : emp, tip=35, est=1, cod='PT<aa>/<nnnnn>', res, fec=último día
           del mes del parte.
  hmo    : MISMO ide que con; cenide (centro de la obra), obride, ano, mes,
           reside=0 (es parte de obra, no de recurso).
  hmores : hmoide, reside, cenide, obride, paride, pos (de 64 en 64), fec,
           horide, can, pre, tot, ano, mes, fac=0, ortide=0 (NOT NULL sin
           default), caaide=0, tex, synckey (clave de idempotencia).

Particular de PORCENTAJES: fec = último día del mes, horide = código M*
del recurso, can = porcentaje sobre 1, pre = importe mensual (reshor),
synckey con prefijo propio para no cruzarse con los partes diarios.
"""
from __future__ import annotations

import calendar
import logging
from typing import Any, Iterable

import httpx

from domain.models.registro_models import (
    HoraRecurso, LineaSigrid, ObraEntrada, ParteDestino,
)

logger = logging.getLogger(__name__)

PREFIJO_SYNCKEY = "porcentajes:"


def synckey_de(registro_id: int) -> str:
    return f"{PREFIJO_SYNCKEY}{int(registro_id)}"


class SigridWriteClient:
    def __init__(
        self,
        *,
        base_url: str,
        function_key: str,
        database: str,
        empresa: int = 1,
        timeout_s: float = 60.0,
        max_statements: int = 15,
        tip_parte: int = 35,
        est_parte: int = 1,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._headers = {"x-functions-key": function_key,
                         "Content-Type": "application/json"}
        self._db = database
        self._empresa = int(empresa)
        self._timeout = float(timeout_s)
        self._max_st = int(max_statements)
        self._tip = int(tip_parte)
        self._est = int(est_parte)

    # ----------------------------- HTTP ----------------------------- #

    def _read(self, sql: str, params: list) -> list[dict]:
        r = httpx.post(f"{self._base}/api/sql/read", headers=self._headers,
                       timeout=self._timeout + 30, json={
                           "database": self._db, "sql": sql,
                           "parameters": params,
                           "timeout_seconds": int(self._timeout),
                           "max_rows": 2000})
        if r.status_code >= 400:
            raise RuntimeError(f"sigrid-api read HTTP {r.status_code}: "
                               f"{r.text[:400]}")
        body = r.json()
        if not body.get("ok"):
            raise RuntimeError(f"sigrid-api read ok=false: {str(body)[:400]}")
        cols = [c.lower() for c in body["columns"]]
        return [dict(zip(cols, row)) for row in body["rows"]]

    def escribir(self, statements: list[dict]) -> int:
        """Escribe por lotes (tope de sentencias de sigrid-api). Cada lote es
        una transacción; devuelve el total de filas afectadas."""
        total = 0
        for i in range(0, len(statements), self._max_st):
            lote = statements[i:i + self._max_st]
            for st in lote:
                logger.info("[sigrid-write] %s | %s",
                            " ".join(st["sql"].split())[:150],
                            st["parameters"])
            r = httpx.post(f"{self._base}/api/sql/write",
                           headers=self._headers,
                           timeout=self._timeout + 60,
                           json={"database": self._db, "statements": lote})
            if r.status_code >= 400:
                raise RuntimeError(f"sigrid-api write HTTP {r.status_code}: "
                                   f"{r.text[:500]}")
            body = r.json()
            if not body.get("ok") or not body.get("committed"):
                raise RuntimeError(
                    f"escritura no confirmada: {str(body)[:400]}")
            total += int(body.get("total_affected_rows") or 0)
        return total

    # ----------------------------- lecturas ----------------------------- #

    def obra_por_codigo(self, cod: str) -> ObraEntrada | None:
        filas = self._read(
            "SELECT obr.ide AS ide, con.cod AS cod, con.res AS res, "
            "obr.cenide AS cenide FROM obr JOIN con ON con.ide = obr.ide "
            "WHERE con.cod = ?", [cod])
        return self._obra(filas)

    def obra_por_ide(self, ide: int) -> ObraEntrada | None:
        filas = self._read(
            "SELECT obr.ide AS ide, con.cod AS cod, con.res AS res, "
            "obr.cenide AS cenide FROM obr JOIN con ON con.ide = obr.ide "
            "WHERE obr.ide = ?", [int(ide)])
        return self._obra(filas)

    @staticmethod
    def _obra(filas: list[dict]) -> ObraEntrada | None:
        if not filas:
            return None
        f = filas[0]
        o = ObraEntrada(ide=int(f["ide"]), codigo=f["cod"], nombre=f["res"])
        setattr(o, "cenide", int(f["cenide"] or 0))
        return o

    def capitulos_de_obra(self, obride: int) -> list[dict]:
        """Partidas/capítulos activos del presupuesto de una obra
        (obrparpar): para localizar el capítulo de la obra original dentro
        de la obra de postventa."""
        return self._read(
            "SELECT ide, padide, pos, tip, cod, res, "
            "CAST(tex AS NVARCHAR(400)) AS tex, ISNULL(tipdes,0) AS tipdes, "
            "cosindide, unimed FROM obrparpar WHERE obride = ? "
            "ORDER BY pos, ide", [int(obride)])

    def recursos_de_empleados(
        self, emp_ides: Iterable[int]
    ) -> dict[int, list[int]]:
        """empleado (con/emp.ide) -> [recurso_ide, …] vía res.conide."""
        ides = sorted({int(i) for i in emp_ides if i})
        if not ides:
            return {}
        marcas = ",".join("?" for _ in ides)
        filas = self._read(
            "SELECT res.ide AS reside, res.conide AS empide FROM res "
            f"WHERE res.conide IN ({marcas}) ORDER BY res.ide", ides)
        out: dict[int, list[int]] = {}
        for f in filas:
            out.setdefault(int(f["empide"]), []).append(int(f["reside"]))
        return out

    def horas_de_recursos(
        self, resides: Iterable[int]
    ) -> dict[int, list[HoraRecurso]]:
        ides = sorted({int(i) for i in resides if i})
        if not ides:
            return {}
        marcas = ",".join("?" for _ in ides)
        filas = self._read(
            "SELECT reshor.reside AS reside, reshor.horide AS horide, "
            "auxhor.cod AS cod, auxhor.res AS res, reshor.pre AS pre "
            "FROM reshor JOIN auxhor ON auxhor.ide = reshor.horide "
            f"WHERE reshor.reside IN ({marcas}) "
            "ORDER BY reshor.reside, auxhor.cod", ides)
        out: dict[int, list[HoraRecurso]] = {}
        for f in filas:
            out.setdefault(int(f["reside"]), []).append(HoraRecurso(
                horide=int(f["horide"]), cod=(f["cod"] or "").strip(),
                res=f["res"], pre=float(f["pre"] or 0.0)))
        return out

    def partes_existentes(
        self, obra_ide: int, periodos: Iterable[tuple[int, int]]
    ) -> dict[tuple[int, int], ParteDestino]:
        """Parte (hmo) de obra+mes SIN recurso (el parte de obra)."""
        out: dict[tuple[int, int], ParteDestino] = {}
        for ano, mes in sorted(set(periodos)):
            filas = self._read(
                "SELECT hmo.ide AS ide, con.cod AS cod FROM hmo "
                "JOIN con ON con.ide = hmo.ide "
                "WHERE hmo.obride = ? AND hmo.ano = ? AND hmo.mes = ? "
                "AND ISNULL(hmo.reside, 0) = 0 AND con.tip = ? "
                "ORDER BY hmo.ide DESC",
                [int(obra_ide), int(ano), int(mes), self._tip])
            if filas:
                out[(ano, mes)] = ParteDestino(
                    ano=ano, mes=mes, existe=True, ide=int(filas[0]["ide"]),
                    cod=filas[0]["cod"])
            else:
                out[(ano, mes)] = ParteDestino(ano=ano, mes=mes, existe=False)
        return out

    def siguiente_cod_pt(self, ano: int) -> str:
        yy = str(int(ano))[-2:]
        filas = self._read(
            "SELECT MAX(cod) AS maxcod FROM con WHERE cod LIKE ?",
            [f"PT{yy}/%"])
        maxcod = (filas[0]["maxcod"] or "") if filas else ""
        try:
            n = int(str(maxcod).split("/")[1]) + 1
        except (IndexError, ValueError):
            n = 1
        return f"PT{yy}/{n:05d}"

    def max_pos(self, hmoide: int) -> int:
        filas = self._read("SELECT ISNULL(MAX(pos),0) AS m FROM hmores "
                           "WHERE hmoide = ?", [int(hmoide)])
        return int((filas[0]["m"] if filas else 0) or 0)

    def lineas_del_parte(
        self, hmoide: int, resides: Iterable[int]
    ) -> list[LineaSigrid]:
        """TODAS las líneas del parte de esos recursos (cualquier día).

        Para porcentajes el conflicto no lleva día: un registro M* del
        mismo recurso/mes en otro día también debe aflorar.
        """
        res = sorted({int(i) for i in resides if i})
        if not res:
            return []
        m_r = ",".join("?" for _ in res)
        filas = self._read(
            "SELECT hmores.ide AS ide, hmores.reside AS reside, "
            "hmores.fec AS fec, hmores.horide AS horide, "
            "hmores.paride AS paride, auxhor.cod AS hora, hmores.can AS can, "
            "hmores.tot AS tot, hmores.synckey AS synckey FROM hmores "
            "LEFT JOIN auxhor ON auxhor.ide = hmores.horide "
            f"WHERE hmores.hmoide = ? AND hmores.reside IN ({m_r}) "
            "ORDER BY hmores.pos", [int(hmoide)] + res)
        out: list[LineaSigrid] = []
        for f in filas:
            sk = (f["synckey"] or "").strip() or None
            out.append(LineaSigrid(
                ide=int(f["ide"]), reside=int(f["reside"] or 0),
                fecha_int=int(f["fec"] or 0),
                horide=int(f["horide"] or 0) or None,
                hora_codigo=f["hora"], can=f["can"], tot=f["tot"],
                synckey=sk,
                nuestra=bool(sk and sk.startswith(PREFIJO_SYNCKEY)),
                paride=int(f["paride"] or 0)))
        return out

    def lineas_por_synckey(
        self, claves: Iterable[str]
    ) -> dict[str, LineaSigrid]:
        ks = sorted({k for k in claves if k})
        if not ks:
            return {}
        out: dict[str, LineaSigrid] = {}
        for i in range(0, len(ks), 200):
            trozo = ks[i:i + 200]
            marcas = ",".join("?" for _ in trozo)
            filas = self._read(
                "SELECT hmores.ide AS ide, hmores.hmoide AS hmoide, "
                "hmores.reside AS reside, hmores.fec AS fec, "
                "hmores.horide AS horide, "
                "auxhor.cod AS hora, hmores.can AS can, hmores.tot AS tot, "
                "hmores.synckey AS synckey FROM hmores "
                "LEFT JOIN auxhor ON auxhor.ide = hmores.horide "
                f"WHERE hmores.synckey IN ({marcas})", trozo)
            for f in filas:
                sk = (f["synckey"] or "").strip()
                ls = LineaSigrid(
                    ide=int(f["ide"]), reside=int(f["reside"] or 0),
                    fecha_int=int(f["fec"] or 0),
                    horide=int(f["horide"] or 0) or None,
                    hora_codigo=f["hora"], can=f["can"], tot=f["tot"],
                    synckey=sk, nuestra=True)
                setattr(ls, "hmoide", int(f["hmoide"] or 0))
                out[sk] = ls
        return out

    # -------------------------- sentencias -------------------------- #

    def stmts_crear_parte(
        self, *, obra: ObraEntrada, ano: int, mes: int, cod: str, desc: str
    ) -> list[dict]:
        """Cabecera (con) + extensión (hmo) del parte de obra/mes."""
        ultimo = calendar.monthrange(int(ano), int(mes))[1]
        fec = int(f"{int(ano)}{int(mes):02d}{ultimo:02d}")
        cenide = int(getattr(obra, "cenide", 0) or 0)
        return [
            {"sql": ("INSERT INTO con (ide, emp, tip, est, cod, res, fec) "
                     "SELECT ISNULL(MAX(ide),0)+1, ?, ?, ?, ?, ?, ? "
                     "FROM con WITH (UPDLOCK, HOLDLOCK)"),
             "parameters": [self._empresa, self._tip, self._est,
                            cod, desc[:128], fec]},
            {"sql": ("INSERT INTO hmo (ide, cenide, obride, ano, mes, reside, "
                     "cenmul) SELECT ide, ?, ?, ?, ?, 0, 0 FROM con "
                     "WHERE cod = ? AND tip = ?"),
             "parameters": [cenide, int(obra.ide), int(ano), int(mes),
                            cod, self._tip]},
        ]

    def stmt_insert_linea(
        self, *, hmoide: int, obra: ObraEntrada, reside: int, pos: int,
        fecha_int: int, horide: int, can: float, pre: float,
        ano: int, mes: int, synckey: str, tex: str | None,
        paride: int = 0,
    ) -> dict:
        """Línea porcentual: can = % sobre 1. paride = capítulo (solo
        postventa); caaide a 0 (pendiente de confirmar con 'inspeccionar'
        si Sigrid lo exige)."""
        cenide = int(getattr(obra, "cenide", 0) or 0)
        return {"sql": (
            "INSERT INTO hmores (ide, hmoide, reside, cenide, obride, paride, "
            "pos, fec, horide, can, pre, tot, ano, mes, fac, ortide, caaide, "
            "tex, synckey) SELECT ISNULL(MAX(ide),0)+1, ?, ?, ?, ?, ?, ?, ?, "
            "?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ? "
            "FROM hmores WITH (UPDLOCK, HOLDLOCK)"),
            "parameters": [int(hmoide), int(reside), cenide, int(obra.ide),
                           int(paride or 0), int(pos), int(fecha_int),
                           int(horide), round(float(can), 4), float(pre),
                           round(float(can) * float(pre), 2), int(ano),
                           int(mes), (tex or ""), synckey]}

    @staticmethod
    def stmt_borrar_linea(ide: int) -> dict:
        return {"sql": "DELETE FROM hmores WHERE ide = ?",
                "parameters": [int(ide)]}

    # -------------------------- inspección -------------------------- #

    def inspeccionar_mensuales(self, limite: int = 20) -> list[dict[str, Any]]:
        """Últimas líneas M* reales: para fijar el mapeo antes de escribir."""
        filas = self._read(
            f"SELECT TOP {int(limite)} hmores.ide AS ide, hmores.hmoide AS "
            "hmoide, hmores.reside AS reside, hmores.fec AS fec, "
            "auxhor.cod AS hora, hmores.can AS can, hmores.canres AS canres, "
            "hmores.pre AS pre, hmores.tot AS tot, hmores.paride AS paride, "
            "hmores.caaide AS caaide, hmores.synckey AS synckey "
            "FROM hmores JOIN auxhor ON auxhor.ide = hmores.horide "
            "WHERE auxhor.cod LIKE 'M%' ORDER BY hmores.ide DESC", [])
        return filas
