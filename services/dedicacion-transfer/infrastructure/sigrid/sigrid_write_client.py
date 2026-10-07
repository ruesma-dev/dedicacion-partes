# infrastructure/sigrid/sigrid_write_client.py
"""Adaptador de Sigrid (lectura + ESCRITURA) vía sigrid-api.

Modelo del parte de trabajo (confirmado contra datos reales, 25/07/2026):
  con    : emp, tip=35, est=1, cod='PT<aa>/<nnnnn>', res, fec=último día
           del mes del parte.
  hmo    : MISMO ide que con; cenide (centro de la obra), obride, ano, mes,
           reside=0 (es parte de obra, no de recurso).
  hmores : hmoide, reside, cenide, obride, paride, pos (de 64 en 64), fec,
           horide, can, pre, tot, ano, mes, fac=0, ortide=0 (NOT NULL sin
           default), caaide, tex, synckey (clave de idempotencia).

Particular de PORCENTAJES: fec = último día del mes, horide = código M*
del recurso, can = porcentaje sobre 1, pre = importe mensual (reshor),
synckey con prefijo propio para no cruzarse con los partes diarios.

F-037 (ARCHITECTURE.md#regla-analitica, copia de la F-031 de `partes`):
`hmores.caaide` es la cuenta analítica de la línea, resuelta en el pipeline
y recibida como parámetro (0 = sin cuenta). `horas_de_recursos` trae la
plantilla del recurso (`reshor.caaide`) y si el tipo es el de por defecto,
`cuentas_de_centro` las cuentas candidatas del centro de la obra,
`partidas_de_lineas` la cuenta de cada partida (respaldo) y
`partes_del_periodo` TODOS los partes de obra y mes con su estado
(`con.est`), para no escribir nunca en uno cerrado. Una lectura con
``truncated: true`` es una excepción: nunca se decide con filas parciales.
Ninguna sentencia toca asientos (`asi`, `asa`, `apu`, `apa`) ni cambia el
estado de un parte: el asiento analítico lo genera Sigrid al contabilizar.

F-047: el tope de filas que se pide a sigrid-api (`max_rows`) es
configurable (`SIGRID_MAX_ROWS`, 200.000 por defecto). Hasta el 2026-10-07
era 2.000 fijo y `capitulos_de_obra`, que lee el presupuesto entero, se
truncaba en las obras con más partidas (la 0696 tiene 3.024). Subir el tope
no relaja la regla: un `truncated` sigue siendo un error.
"""
from __future__ import annotations

import calendar
import logging
from typing import Any, Iterable

import httpx

from application.services.cuenta_analitica import indexar_cuentas
from domain.errores import ObraAmbigua
from domain.models.registro_models import (
    HoraRecurso, LineaSigrid, ObraEntrada, ParteDestino, ParteSigrid,
    PartidaCuenta,
)

logger = logging.getLogger(__name__)

PREFIJO_SYNCKEY = "porcentajes:"
#: F-047: filas por lectura que se piden a sigrid-api si nadie dice otra
#: cosa. Debe caber en su `MAX_ALLOWED_ROWS` (500.000 en la instancia
#: desplegada, `azure-apps/sigrid_api.md` §4.1).
MAX_ROWS_POR_DEFECTO = 200_000


def synckey_de(registro_id: int) -> str:
    return f"{PREFIJO_SYNCKEY}{int(registro_id)}"


class SigridWriteClient:
    def __init__(
        self,
        *,
        base_url: str,
        function_key: str,
        database: str,
        timeout_s: float = 60.0,
        max_statements: int = 15,
        tip_parte: int = 35,
        est_parte: int = 1,
        max_rows: int = MAX_ROWS_POR_DEFECTO,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._headers = {"x-functions-key": function_key,
                         "Content-Type": "application/json"}
        self._db = database
        self._timeout = float(timeout_s)
        self._max_st = int(max_statements)
        self._tip = int(tip_parte)
        self._est = int(est_parte)
        self._max_rows = int(max_rows)

    # ----------------------------- HTTP ----------------------------- #

    def _read(self, sql: str, params: list) -> list[dict]:
        r = httpx.post(f"{self._base}/api/sql/read", headers=self._headers,
                       timeout=self._timeout + 30, json={
                           "database": self._db, "sql": sql,
                           "parameters": params,
                           "timeout_seconds": int(self._timeout),
                           "max_rows": self._max_rows})
        if r.status_code >= 400:
            raise RuntimeError(f"sigrid-api read HTTP {r.status_code}: "
                               f"{r.text[:400]}")
        body = r.json()
        if not body.get("ok"):
            raise RuntimeError(f"sigrid-api read ok=false: {str(body)[:400]}")
        if body.get("truncated"):
            # F-037 (R7, R16): nunca se decide con filas parciales.
            raise RuntimeError("sigrid-api devolvio una respuesta truncada")
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

    def obra_por_codigo(self, cod: str, empresa: int) -> ObraEntrada | None:
        """Obra por código DENTRO de su empresa: el código solo es único
        ahí (ARCHITECTURE.md#regla-empresa). La empresa es obligatoria."""
        filas = self._read(
            "SELECT obr.ide AS ide, con.cod AS cod, con.res AS res, "
            "obr.cenide AS cenide, con.emp AS emp FROM obr "
            "JOIN con ON con.ide = obr.ide "
            "WHERE con.cod = ? AND con.emp = ?", [cod, int(empresa)])
        return self._obra(filas, int(empresa), cod)

    def obra_por_ide(self, ide: int) -> ObraEntrada | None:
        """Obra por `ide`, que es único: no se filtra por empresa, pero se
        lee para poder comprobarla."""
        filas = self._read(
            "SELECT obr.ide AS ide, con.cod AS cod, con.res AS res, "
            "obr.cenide AS cenide, con.emp AS emp FROM obr "
            "JOIN con ON con.ide = obr.ide "
            "WHERE obr.ide = ?", [int(ide)])
        return self._obra(filas)

    @staticmethod
    def _obra(filas: list[dict], empresa: int | None = None,
              cod: str | None = None) -> ObraEntrada | None:
        """Una ficha o ninguna; NUNCA «la primera».

        Con `empresa`, filtra también aquí aunque el SQL ya lo haga: es la
        defensa si alguien toca la consulta, y lo que hace comprobable la
        elección sin Sigrid. Una ficha sin `con.emp` no es de ninguna
        empresa válida. Sin `empresa` (búsqueda por `ide`) no se filtra.
        """
        if empresa is not None:
            filas = [f for f in filas if int(f["emp"] or 0) == empresa]
        if not filas:
            return None
        if len(filas) > 1:
            raise ObraAmbigua(
                f"obra {cod} ambigua: {len(filas)} fichas en la "
                f"empresa {empresa}")
        f = filas[0]
        o = ObraEntrada(ide=int(f["ide"]), codigo=f["cod"], nombre=f["res"],
                        empresa=int(f["emp"] or 0))
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

    def horas_de_recursos(
        self, resides: Iterable[int]
    ) -> dict[int, list[HoraRecurso]]:
        ides = sorted({int(i) for i in resides if i})
        if not ides:
            return {}
        marcas = ",".join("?" for _ in ides)
        # F-037 (R2, la de `partes` F-021): en la MISMA consulta, el código
        # de la cuenta de la ficha (`reshor.caaide`, 0 = ninguna) y si es el
        # tipo por defecto del recurso (`res.horide`).
        filas = self._read(
            "SELECT reshor.reside AS reside, reshor.horide AS horide, "
            "auxhor.cod AS cod, auxhor.res AS res, reshor.pre AS pre, "
            "cc.cod AS caacod, "
            "CASE WHEN reshor.horide = res.horide THEN 1 ELSE 0 END "
            "AS defecto "
            "FROM reshor JOIN auxhor ON auxhor.ide = reshor.horide "
            "LEFT JOIN res ON res.ide = reshor.reside "
            "LEFT JOIN con cc ON cc.ide = reshor.caaide "
            "AND ISNULL(reshor.caaide, 0) <> 0 "
            f"WHERE reshor.reside IN ({marcas}) "
            "ORDER BY reshor.reside, auxhor.cod", ides)
        out: dict[int, list[HoraRecurso]] = {}
        for f in filas:
            out.setdefault(int(f["reside"]), []).append(HoraRecurso(
                horide=int(f["horide"]), cod=(f["cod"] or "").strip(),
                res=f["res"], pre=float(f["pre"] or 0.0),
                caa_cod=(f["caacod"] or "").strip() or None,
                defecto=bool(f["defecto"])))
        return out

    def cuentas_de_centro(
        self, cenide: int, empresa: int, subcuentas: Iterable[str | None]
    ) -> dict[str, list[tuple[int, str]]]:
        """Cuentas analíticas del centro, de esa empresa, con esas
        subcuentas (F-037 R4): UNA lectura, agrupada por subcuenta.

        El filtro SQL solo acota; la agrupación la rehace `indexar_cuentas`
        con la misma `subcuenta()` del origen. Un fallo o un `truncated`
        sube como excepción (R7)."""
        subs = sorted({s for s in subcuentas if s})
        if not subs:
            return {}
        marcas = ",".join("?" for _ in subs)
        filas = self._read(
            "SELECT a.ide AS caaide, c.cod AS cod FROM caa a "
            "JOIN con c ON c.ide = a.ide WHERE a.cenide = ? AND c.emp = ? "
            "AND LTRIM(RTRIM(SUBSTRING(c.cod, CHARINDEX('.', c.cod) + 1, "
            f"24))) IN ({marcas})", [int(cenide), int(empresa)] + subs)
        return indexar_cuentas((f["caaide"], f["cod"]) for f in filas)

    def partidas_de_lineas(
        self, parides: Iterable[int | None]
    ) -> dict[int, PartidaCuenta]:
        """F-037 (R3, R7): partida -> su cuenta analítica
        (`obrparpar.caaide`, 0 = ninguna), en UNA lectura. Sin partidas no
        se lee."""
        ides = sorted({int(i) for i in parides if i})
        if not ides:
            return {}
        marcas = ",".join("?" for _ in ides)
        filas = self._read(
            "SELECT p.ide AS ide, p.cod AS cod, pc.cod AS caacod "
            "FROM obrparpar p LEFT JOIN con pc ON pc.ide = p.caaide "
            "AND ISNULL(p.caaide, 0) <> 0 "
            f"WHERE p.ide IN ({marcas})", ides)
        out: dict[int, PartidaCuenta] = {}
        for f in filas:
            ide = int(f["ide"])
            out[ide] = PartidaCuenta(
                ide=ide, cod=(f["cod"] or "").strip() or None,
                caa_cod=(f["caacod"] or "").strip() or None)
        return out

    def partes_del_periodo(self, obra_ide: int, ano: int,
                           mes: int) -> list[ParteSigrid]:
        """F-037 (R9): TODOS los partes de obra (sin recurso) y mes, con su
        estado, por `ide` descendente. UNA lectura; un `truncated` sube como
        excepción (R16)."""
        filas = self._read(
            "SELECT hmo.ide AS ide, con.cod AS cod, con.est AS est FROM hmo "
            "JOIN con ON con.ide = hmo.ide "
            "WHERE hmo.obride = ? AND hmo.ano = ? AND hmo.mes = ? "
            "AND ISNULL(hmo.reside, 0) = 0 AND con.tip = ? "
            "ORDER BY hmo.ide DESC",
            [int(obra_ide), int(ano), int(mes), self._tip])
        return [ParteSigrid(ide=int(f["ide"]), cod=f["cod"],
                            est=None if f["est"] is None else int(f["est"]))
                for f in filas]

    def partes_existentes(
        self, obra_ide: int, periodos: Iterable[tuple[int, int]]
    ) -> dict[tuple[int, int], ParteDestino]:
        """Parte (hmo) de obra+mes SIN recurso (el parte de obra).

        Desde F-037 el pipeline NO la usa (elige con `partes_del_periodo`,
        que mira el estado); solo la fase `estado`, de solo lectura, del
        script manual `prueba_escritura_porcentajes.py`."""
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

    def siguiente_cod_pt(self, ano: int, empresa: int) -> str:
        """Siguiente `PT<AA>/NNNNN` de ESA empresa (F-037 R11, como
        `partes`): el correlativo es por empresa y los números se repiten
        entre ellas. Antes de F-037 salía del mayor de TODAS."""
        yy = str(int(ano))[-2:]
        filas = self._read(
            "SELECT MAX(cod) AS maxcod FROM con WHERE cod LIKE ? AND emp = ?",
            [f"PT{yy}/%", int(empresa)])
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
        """Cabecera (con) + extensión (hmo) del parte de obra/mes, en UNA
        transacción (un solo lote de `escribir`).

        CONFLUENCIA CON `partes` (aviso de su F-031, 2026-10-06): su
        `stmts_crear_parte` es idéntico en texto y parámetros a este (el de
        `40b9feb`). Si se cambia aquí, se avisa a `partes` en el mismo
        trabajo (docs/INTEGRACION.md §7).

        `con.emp` es la empresa de la obra destino: el parte es de la
        empresa de su obra (ARCHITECTURE.md#regla-empresa). Sin ella no se
        adivina: `ValueError`.

        F-037 D17 (alta protegida, la carrera con `partes`): la cabecera
        solo se inserta si el código está libre en la empresa y si el
        periodo NO tiene ya un parte En registro, comprobado con bloqueo. Las
        dos condiciones van FUERA del agregado: un `SELECT MAX(...) ...
        WHERE NOT EXISTS` devuelve una fila aunque la condición falle. El
        `hmo` se cuelga del `con` por código, tipo y EMPRESA, y solo si ese
        `con` aún no lo tiene. El pipeline relee el periodo después.
        """
        if not obra.empresa:
            raise ValueError(
                f"la obra {obra.codigo} no trae empresa: no se crea su parte")
        ultimo = calendar.monthrange(int(ano), int(mes))[1]
        fec = int(f"{int(ano)}{int(mes):02d}{ultimo:02d}")
        cenide = int(getattr(obra, "cenide", 0) or 0)
        empresa = int(obra.empresa)
        return [
            {"sql": ("INSERT INTO con (ide, emp, tip, est, cod, res, fec) "
                     "SELECT x.n, ?, ?, ?, ?, ?, ? FROM "
                     "(SELECT ISNULL(MAX(ide),0)+1 AS n "
                     "FROM con WITH (UPDLOCK, HOLDLOCK)) x "
                     "WHERE NOT EXISTS (SELECT 1 FROM con c "
                     "WITH (UPDLOCK, HOLDLOCK) "
                     "WHERE c.cod = ? AND c.emp = ? AND c.tip = ?) "
                     "AND NOT EXISTS (SELECT 1 FROM hmo h "
                     "WITH (UPDLOCK, HOLDLOCK) JOIN con r "
                     "WITH (UPDLOCK, HOLDLOCK) ON r.ide = h.ide "
                     "WHERE h.obride = ? AND h.ano = ? AND h.mes = ? "
                     "AND ISNULL(h.reside, 0) = 0 AND r.tip = ? "
                     "AND r.est = ?)"),
             "parameters": [empresa, self._tip, self._est,
                            cod, desc[:128], fec,
                            cod, empresa, self._tip,
                            int(obra.ide), int(ano), int(mes), self._tip,
                            self._est]},
            {"sql": ("INSERT INTO hmo (ide, cenide, obride, ano, mes, reside, "
                     "cenmul) SELECT ide, ?, ?, ?, ?, 0, 0 FROM con "
                     "WHERE cod = ? AND tip = ? AND emp = ? "
                     "AND NOT EXISTS (SELECT 1 FROM hmo h "
                     "WHERE h.ide = con.ide)"),
             "parameters": [cenide, int(obra.ide), int(ano), int(mes),
                            cod, self._tip, empresa]},
        ]

    def stmt_insert_linea(
        self, *, hmoide: int, obra: ObraEntrada, reside: int, pos: int,
        fecha_int: int, horide: int, can: float, pre: float,
        ano: int, mes: int, synckey: str, tex: str | None,
        paride: int = 0, caaide: int = 0,
    ) -> dict:
        """Línea porcentual: can = % sobre 1. paride = partida de
        imputación; caaide = cuenta analítica resuelta en el pipeline
        (F-037 R1; 0 = sin cuenta)."""
        cenide = int(getattr(obra, "cenide", 0) or 0)
        return {"sql": (
            "INSERT INTO hmores (ide, hmoide, reside, cenide, obride, paride, "
            "pos, fec, horide, can, pre, tot, ano, mes, fac, ortide, caaide, "
            "tex, synckey) SELECT ISNULL(MAX(ide),0)+1, ?, ?, ?, ?, ?, ?, ?, "
            "?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ? "
            "FROM hmores WITH (UPDLOCK, HOLDLOCK)"),
            "parameters": [int(hmoide), int(reside), cenide, int(obra.ide),
                           int(paride or 0), int(pos), int(fecha_int),
                           int(horide), round(float(can), 4), float(pre),
                           round(float(can) * float(pre), 2), int(ano),
                           int(mes), int(caaide or 0), (tex or ""),
                           synckey]}

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
