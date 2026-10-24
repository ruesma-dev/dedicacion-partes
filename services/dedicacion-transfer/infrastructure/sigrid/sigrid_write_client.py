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

F-050 (ARCHITECTURE.md#regla-partida): `historial_partidas` lee las líneas
`M*` con partida de los partes de trabajo de unos recursos en una ventana de
meses, para proponer la partida. Solo lectura; un `truncated` es error.

F-055 (R1): cada lectura (una llamada a `sigrid-api`) deja un log con el
nombre del método del cliente, sus filas y sus segundos, sin SQL ni
parámetros, y se apunta en las mediciones abiertas con `medir_lecturas`
(el resumen de cada preflight y la fase `medir` del script).
"""
from __future__ import annotations

import calendar
import logging
import threading
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Iterable, Iterator

import httpx

from application.services.cuenta_analitica import indexar_cuentas
from application.services.propuesta_partida import LineaHistorial
from domain.errores import ObraAmbigua
from domain.models.registro_models import (
    HoraRecurso, LineaIncidenciaSigrid, LineaSigrid, ObraEntrada,
    ParteDestino, ParteSigrid, PartidaCuenta, PartidaValida,
)

logger = logging.getLogger(__name__)

PREFIJO_SYNCKEY = "porcentajes:"
#: F-047: filas por lectura que se piden a sigrid-api si nadie dice otra
#: cosa. Debe caber en su `MAX_ALLOWED_ROWS` (500.000 en la instancia
#: desplegada, `azure-apps/sigrid_api.md` §4.1).
MAX_ROWS_POR_DEFECTO = 200_000
#: F-050: recursos por lectura del historial (el `IN` de `historial_partidas`).
LOTE_RECURSOS_HISTORIAL = 500
#: F-055 (R20): parámetros por lectura de las consultas con `IN (?…)`
#: agrupadas (`validar_partidas` y las de T5).
LOTE_PARAMETROS = 500
#: F-051 (R11): enlaces de una línea con otros documentos de Sigrid
#: (albarán, factura, dedicación, nómina); una línea con alguno no se edita.
_ENLACES = ("dvaproide", "dvfproide", "hdereside", "empdpreide",
            "empabside", "emprccide")


def synckey_de(registro_id: int) -> str:
    return f"{PREFIJO_SYNCKEY}{int(registro_id)}"


def _entero(v) -> int | None:
    """Un entero de una fila de Sigrid, o None si viene nulo."""
    return None if v is None else int(v)


def _trozos(valores: list, n: int = LOTE_PARAMETROS) -> Iterator[list]:
    """`valores` en trozos de como mucho `n` (F-055 R20)."""
    for i in range(0, len(valores), n):
        yield valores[i:i + n]


# ------------------------ medición (F-055 R1) ------------------------ #

#: Reloj de la medición (aparte para poder fijarlo en los tests).
_ahora = time.perf_counter


@dataclass(frozen=True)
class Lectura:
    """Una lectura medida: método del cliente, filas (None si falló) y
    segundos."""
    nombre: str
    filas: int | None
    segundos: float


class MedicionLecturas:
    """Las lecturas hechas mientras está abierta (`medir_lecturas`)."""

    def __init__(self) -> None:
        self.lecturas: list[Lectura] = []
        self._lock = threading.Lock()

    def apuntar(self, lectura: Lectura) -> None:
        with self._lock:
            self.lecturas.append(lectura)

    @property
    def n(self) -> int:
        return len(self.lecturas)

    @property
    def segundos(self) -> float:
        return sum(l.segundos for l in self.lecturas)


#: Mediciones abiertas en este contexto, de fuera a dentro.
_MEDICIONES: ContextVar[tuple[MedicionLecturas, ...]] = ContextVar(
    "mediciones_sigrid", default=())


@contextmanager
def medir_lecturas() -> Iterator[MedicionLecturas]:
    """Abre una medición: apunta las lecturas hechas dentro del bloque. Se
    pueden anidar; cada lectura se apunta en todas las abiertas."""
    m = MedicionLecturas()
    token = _MEDICIONES.set(_MEDICIONES.get() + (m,))
    try:
        yield m
    finally:
        _MEDICIONES.reset(token)


def apuntar_lectura(nombre: str, filas: int | None,
                    segundos: float) -> None:
    """Log de UNA lectura (R1: nombre, filas y segundos; nunca SQL ni
    parámetros) y apunte en todas las mediciones abiertas. `filas` es None
    si la lectura falló."""
    logger.info("[sigrid-read] %s filas=%s segundos=%.2f", nombre,
                "error" if filas is None else filas, segundos)
    lectura = Lectura(nombre, filas, segundos)
    for m in _MEDICIONES.get():
        m.apuntar(lectura)


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

    def _lectura(self, nombre: str, sql: str, params: list) -> list[dict]:
        """Una lectura medida (F-055 R1): `_read` con el log y el apunte de
        `apuntar_lectura`. `nombre` es el del método del cliente que la
        pide. `_read` no cambia de firma: los dobles de los tests lo
        sustituyen con `(sql, params)`."""
        t0 = _ahora()
        filas: list[dict] | None = None
        try:
            filas = self._read(sql, params)
            return filas
        finally:
            apuntar_lectura(nombre, None if filas is None else len(filas),
                            _ahora() - t0)

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
        filas = self._lectura(
            "obra_por_codigo",
            "SELECT obr.ide AS ide, con.cod AS cod, con.res AS res, "
            "obr.cenide AS cenide, con.emp AS emp FROM obr "
            "JOIN con ON con.ide = obr.ide "
            "WHERE con.cod = ? AND con.emp = ?", [cod, int(empresa)])
        return self._obra(filas, int(empresa), cod)

    def obra_por_ide(self, ide: int) -> ObraEntrada | None:
        """Obra por `ide`, que es único: no se filtra por empresa, pero se
        lee para poder comprobarla."""
        filas = self._lectura(
            "obra_por_ide",
            "SELECT obr.ide AS ide, con.cod AS cod, con.res AS res, "
            "obr.cenide AS cenide, con.emp AS emp FROM obr "
            "JOIN con ON con.ide = obr.ide "
            "WHERE obr.ide = ?", [int(ide)])
        return self._obra(filas)

    def obras_por_ide(self, ides: Iterable[int | None]
                      ) -> dict[int, ObraEntrada]:
        """F-055 (R20): `obra_por_ide` de varias obras, agrupada: el mismo
        SQL con `IN`, trozos de `LOTE_PARAMETROS` y `_obra` por `ide`. La
        que no existe no sale."""
        ides_ = sorted({int(i) for i in ides if i})
        por_ide: dict[int, list[dict]] = {}
        for trozo in _trozos(ides_):
            marcas = ",".join("?" for _ in trozo)
            for f in self._lectura(
                    "obras_por_ide",
                    "SELECT obr.ide AS ide, con.cod AS cod, con.res AS res, "
                    "obr.cenide AS cenide, con.emp AS emp FROM obr "
                    "JOIN con ON con.ide = obr.ide "
                    f"WHERE obr.ide IN ({marcas})", trozo):
                por_ide.setdefault(int(f["ide"]), []).append(f)
        return {ide: self._obra(filas) for ide, filas in por_ide.items()}

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
        return self._lectura(
            "capitulos_de_obra",
            "SELECT ide, padide, pos, tip, cod, res, "
            "CAST(tex AS NVARCHAR(400)) AS tex, ISNULL(tipdes,0) AS tipdes, "
            "cosindide, unimed FROM obrparpar WHERE obride = ? "
            "ORDER BY pos, ide", [int(obride)])

    def horas_de_recursos(
        self, resides: Iterable[int]
    ) -> dict[int, list[HoraRecurso]]:
        ides = sorted({int(i) for i in resides if i})
        filas: list[dict] = []
        # F-055 (R20): en trozos de `LOTE_PARAMETROS` recursos (un lote de
        # obras junta los de todas).
        for trozo in _trozos(ides):
            marcas = ",".join("?" for _ in trozo)
            # F-037 (R2, la de `partes` F-021): en la MISMA consulta, el
            # código de la cuenta de la ficha (`reshor.caaide`, 0 = ninguna)
            # y si es el tipo por defecto del recurso (`res.horide`).
            filas += self._lectura(
                "horas_de_recursos",
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
                "ORDER BY reshor.reside, auxhor.cod", trozo)
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
        filas = self._lectura(
            "cuentas_de_centro",
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
        filas = self._lectura(
            "partidas_de_lineas",
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

    def validar_partidas(
        self, parides: Iterable[int | None]
    ) -> dict[int, PartidaValida]:
        """F-055 (R3, R4; design §6): las partidas por `ide`, con su obra,
        si son hoja (sin hijas de su MISMA obra, como `build_arbol_partidas`)
        y si están de alta (`tipdes = 0`). UNA lectura por trozo de
        `LOTE_PARAMETROS`; sin partidas no se lee. La que no existe no sale.
        Un fallo o un `truncated` sube como excepción."""
        ides = sorted({int(i) for i in parides if i})
        out: dict[int, PartidaValida] = {}
        for i in range(0, len(ides), LOTE_PARAMETROS):
            trozo = ides[i:i + LOTE_PARAMETROS]
            marcas = ",".join("?" for _ in trozo)
            filas = self._lectura(
                "validar_partidas",
                "SELECT p.ide AS ide, p.obride AS obride, p.cod AS cod, "
                "p.res AS res, ISNULL(p.tipdes,0) AS tipdes, "
                "CASE WHEN EXISTS (SELECT 1 FROM obrparpar h WHERE "
                "h.padide = p.ide AND h.obride = p.obride) THEN 0 ELSE 1 END "
                f"AS hoja FROM obrparpar p WHERE p.ide IN ({marcas})", trozo)
            for f in filas:
                ide = int(f["ide"])
                out[ide] = PartidaValida(
                    ide=ide, obride=int(f["obride"]), cod=f["cod"],
                    res=f["res"], es_hoja=bool(f["hoja"]),
                    activa=int(f["tipdes"] or 0) == 0)
        return out

    def historial_partidas(
        self, resides: Iterable[int | None], desde: int, hasta: int
    ) -> list[LineaHistorial]:
        """F-050 (R4, R7): líneas `M*` con partida de esos recursos en partes
        de trabajo (`con.tip` del ajuste) con el mes entre `desde` y `hasta`
        (AAAAMM, incluidos), solo si la partida es del presupuesto de la
        obra del parte. En lotes de 500 recursos; sin recursos no se lee.
        Un fallo o un `truncated` sube como excepción."""
        ides = sorted({int(i) for i in resides if i})
        out: list[LineaHistorial] = []
        for i in range(0, len(ides), LOTE_RECURSOS_HISTORIAL):
            lote = ides[i:i + LOTE_RECURSOS_HISTORIAL]
            marcas = ",".join("?" for _ in lote)
            filas = self._lectura(
                "historial_partidas",
                "SELECT h.reside AS reside, m.obride AS obride, "
                "co.cod AS obra_cod, c.cod AS parte_cod, m.ano AS ano, "
                "m.mes AS mes, h.can AS can, h.paride AS paride, "
                "p.cod AS par_cod, p.res AS par_res "
                "FROM hmores h JOIN hmo m ON m.ide = h.hmoide "
                "JOIN con c ON c.ide = m.ide JOIN con co ON co.ide = m.obride "
                "JOIN auxhor a ON a.ide = h.horide "
                "JOIN obrparpar p ON p.ide = h.paride "
                f"WHERE h.reside IN ({marcas}) AND c.tip = ? "
                "AND a.cod LIKE 'M%' AND p.obride = m.obride "
                "AND (m.ano * 100 + m.mes) BETWEEN ? AND ?",
                lote + [self._tip, int(desde), int(hasta)])
            out.extend(LineaHistorial(
                reside=int(f["reside"]), obride=int(f["obride"]),
                obra_cod=(f["obra_cod"] or "").strip() or None,
                parte_cod=(f["parte_cod"] or "").strip() or None,
                ano=int(f["ano"]), mes=int(f["mes"]),
                can=float(f["can"] or 0.0), paride=int(f["paride"]),
                par_cod=(f["par_cod"] or "").strip() or None,
                par_res=(f["par_res"] or "").strip() or None)
                for f in filas)
        return out

    def partes_del_periodo(self, obra_ide: int, ano: int,
                           mes: int) -> list[ParteSigrid]:
        """F-037 (R9): TODOS los partes de obra (sin recurso) y mes, con su
        estado, por `ide` descendente. UNA lectura; un `truncated` sube como
        excepción (R16)."""
        filas = self._lectura(
            "partes_del_periodo",
            "SELECT hmo.ide AS ide, con.cod AS cod, con.est AS est FROM hmo "
            "JOIN con ON con.ide = hmo.ide "
            "WHERE hmo.obride = ? AND hmo.ano = ? AND hmo.mes = ? "
            "AND ISNULL(hmo.reside, 0) = 0 AND con.tip = ? "
            "ORDER BY hmo.ide DESC",
            [int(obra_ide), int(ano), int(mes), self._tip])
        return [ParteSigrid(ide=int(f["ide"]), cod=f["cod"],
                            est=None if f["est"] is None else int(f["est"]))
                for f in filas]

    def partes_de_periodos(
        self, obrides: Iterable[int], periodos: Iterable[tuple[int, int]]
    ) -> dict[tuple[int, int, int], list[ParteSigrid]]:
        """F-055 (R20): `partes_del_periodo` de varias obras y periodos,
        agrupada: el mismo SQL con `IN` y la clave `(obride, ano, mes)`;
        cada clave pedida sale, vacía si no hay partes, con el orden de la
        suelta (`ide` descendente). Trozos de `LOTE_PARAMETROS` obras."""
        obras = sorted({int(o) for o in obrides})
        pers = sorted({int(a) * 100 + int(m) for a, m in periodos})
        if not obras or not pers:
            return {}
        out: dict[tuple[int, int, int], list[ParteSigrid]] = {
            (o, p // 100, p % 100): [] for o in obras for p in pers}
        m_p = ",".join("?" for _ in pers)
        for trozo in _trozos(obras):
            m_o = ",".join("?" for _ in trozo)
            for f in self._lectura(
                    "partes_de_periodos",
                    "SELECT hmo.ide AS ide, con.cod AS cod, con.est AS est, "
                    "hmo.obride AS obride, hmo.ano AS ano, hmo.mes AS mes "
                    "FROM hmo JOIN con ON con.ide = hmo.ide "
                    f"WHERE hmo.obride IN ({m_o}) AND (hmo.ano * 100 + "
                    f"hmo.mes) IN ({m_p}) AND ISNULL(hmo.reside, 0) = 0 "
                    "AND con.tip = ? ORDER BY hmo.ide DESC",
                    trozo + pers + [self._tip]):
                clave = (int(f["obride"]), int(f["ano"]), int(f["mes"]))
                if clave in out:
                    out[clave].append(ParteSigrid(
                        ide=int(f["ide"]), cod=f["cod"],
                        est=None if f["est"] is None else int(f["est"])))
        return out

    def partes_existentes(
        self, obra_ide: int, periodos: Iterable[tuple[int, int]]
    ) -> dict[tuple[int, int], ParteDestino]:
        """Parte (hmo) de obra+mes SIN recurso (el parte de obra).

        Desde F-037 el pipeline NO la usa (elige con `partes_del_periodo`,
        que mira el estado); solo la fase `estado`, de solo lectura, del
        script manual `prueba_escritura_porcentajes.py`."""
        out: dict[tuple[int, int], ParteDestino] = {}
        for ano, mes in sorted(set(periodos)):
            filas = self._lectura(
                "partes_existentes",
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
        filas = self._lectura(
            "siguiente_cod_pt",
            "SELECT MAX(cod) AS maxcod FROM con WHERE cod LIKE ? AND emp = ?",
            [f"PT{yy}/%", int(empresa)])
        maxcod = (filas[0]["maxcod"] or "") if filas else ""
        try:
            n = int(str(maxcod).split("/")[1]) + 1
        except (IndexError, ValueError):
            n = 1
        return f"PT{yy}/{n:05d}"

    def max_pos(self, hmoide: int) -> int:
        filas = self._lectura("max_pos",
                              "SELECT ISNULL(MAX(pos),0) AS m FROM hmores "
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
        filas = self._lectura(
            "lineas_del_parte",
            "SELECT hmores.ide AS ide, hmores.reside AS reside, "
            "hmores.fec AS fec, hmores.horide AS horide, "
            "hmores.paride AS paride, auxhor.cod AS hora, hmores.can AS can, "
            "hmores.tot AS tot, hmores.synckey AS synckey FROM hmores "
            "LEFT JOIN auxhor ON auxhor.ide = hmores.horide "
            f"WHERE hmores.hmoide = ? AND hmores.reside IN ({m_r}) "
            "ORDER BY hmores.pos", [int(hmoide)] + res)
        return [self._linea_del_parte(f) for f in filas]

    @staticmethod
    def _linea_del_parte(f: dict) -> LineaSigrid:
        sk = (f["synckey"] or "").strip() or None
        return LineaSigrid(
            ide=int(f["ide"]), reside=int(f["reside"] or 0),
            fecha_int=int(f["fec"] or 0),
            horide=int(f["horide"] or 0) or None,
            hora_codigo=f["hora"], can=f["can"], tot=f["tot"],
            synckey=sk,
            nuestra=bool(sk and sk.startswith(PREFIJO_SYNCKEY)),
            paride=int(f["paride"] or 0))

    def lineas_de_partes(
        self, hmoides: Iterable[int], resides: Iterable[int | None]
    ) -> dict[int, list[LineaSigrid]]:
        """F-055 (R20): `lineas_del_parte` de varios partes, agrupada: el
        mismo SQL con `IN`, la clave `hmoide` y, dentro de cada parte, el
        orden de la suelta (`pos`), también cuando los recursos van en
        varios trozos (se ordena al juntar). Cada parte pedido sale, vacío si
        no tiene líneas. Trozos de `LOTE_PARAMETROS` partes y recursos."""
        partes = sorted({int(h) for h in hmoides if h})
        res = sorted({int(i) for i in resides if i})
        if not partes or not res:
            return {}
        por_pos: dict[int, list[tuple[int, LineaSigrid]]] = {
            h: [] for h in partes}
        for t_h in _trozos(partes):
            for t_r in _trozos(res):
                m_h = ",".join("?" for _ in t_h)
                m_r = ",".join("?" for _ in t_r)
                filas = self._lectura(
                    "lineas_de_partes",
                    "SELECT hmores.hmoide AS hmoide, hmores.pos AS pos, "
                    "hmores.ide AS ide, "
                    "hmores.reside AS reside, "
                    "hmores.fec AS fec, hmores.horide AS horide, "
                    "hmores.paride AS paride, auxhor.cod AS hora, "
                    "hmores.can AS can, "
                    "hmores.tot AS tot, hmores.synckey AS synckey "
                    "FROM hmores "
                    "LEFT JOIN auxhor ON auxhor.ide = hmores.horide "
                    f"WHERE hmores.hmoide IN ({m_h}) "
                    f"AND hmores.reside IN ({m_r}) "
                    "ORDER BY hmores.hmoide, hmores.pos", t_h + t_r)
                for f in filas:
                    por_pos[int(f["hmoide"])].append(
                        (int(f["pos"] or 0), self._linea_del_parte(f)))
        # `sorted` es estable: dentro de un trozo, el orden de Sigrid.
        return {h: [ls for _, ls in sorted(v, key=lambda x: x[0])]
                for h, v in por_pos.items()}

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
            filas = self._lectura(
                "lineas_por_synckey",
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

    def incidencias_en_ventana(
        self, resides: Iterable[int | None], desde: int, hasta: int, *,
        obride_pruebas: int | None = None, ides: Iterable[int | None] = (),
    ) -> list[LineaIncidenciaSigrid]:
        """F-062 (R19, design §6): las líneas de incidencia (`CI*`, también
        `CIZ`) de esos recursos con `fec` en [`desde`, `hasta`] (AAAAMMDD),
        en CUALQUIER parte y obra, más las líneas `ides` (las de las trazas,
        también de las quitadas) estén donde estén, en la MISMA lectura. De
        cada una, su parte (código, `con.est` y `con.emp`), su obra, centro,
        partida y cuenta. En pruebas (`obride_pruebas`), solo las de partes
        de esa obra. En trozos de `LOTE_PARAMETROS` recursos e `ide`; un
        fallo o un `truncated` sube como excepción. Cada línea, una vez,
        por (`fec`, `ide`)."""
        recursos = sorted({int(i) for i in resides if i})
        lineas = sorted({int(i) for i in ides if i})
        if not (recursos or lineas):
            return []
        filtro, extra = "", []
        if obride_pruebas is not None:
            filtro, extra = " AND m.obride = ?", [int(obride_pruebas)]
        out: dict[int, LineaIncidenciaSigrid] = {}
        pedidas = [("r", r) for r in recursos] + [("i", i) for i in lineas]
        for trozo in _trozos(pedidas):
            t_r = [v for t, v in trozo if t == "r"]
            t_i = [v for t, v in trozo if t == "i"]
            conds, params = [], []
            if t_r:
                conds.append(f"h.reside IN ({','.join('?' for _ in t_r)}) "
                             "AND h.fec BETWEEN ? AND ? AND a.cod LIKE ?")
                params += t_r + [int(desde), int(hasta), "CI%"]
            if t_i:
                conds.append(f"h.ide IN ({','.join('?' for _ in t_i)})")
                params += t_i
            donde = (conds[0] if not t_i else f"({' OR '.join(conds)})")
            filas = self._lectura(
                "incidencias_en_ventana",
                "SELECT h.ide AS ide, h.reside AS reside, h.fec AS fec, "
                "a.cod AS cod, h.synckey AS synckey, c.cod AS parte, "
                "h.can AS can, h.hmoide AS hmoide, c.est AS est, "
                "c.emp AS emp, m.obride AS obride, h.cenide AS cenide, "
                "h.paride AS paride, h.caaide AS caaide "
                "FROM hmores h JOIN auxhor a ON a.ide = h.horide "
                "JOIN hmo m ON m.ide = h.hmoide JOIN con c ON c.ide = m.ide "
                f"WHERE {donde}{filtro} ORDER BY h.fec, h.ide",
                params + extra)
            for f in filas:
                out.setdefault(int(f["ide"]), LineaIncidenciaSigrid(
                    ide=int(f["ide"]), reside=int(f["reside"]),
                    fecha_int=int(f["fec"]),
                    hora_codigo=(f["cod"] or "").strip() or None,
                    synckey=(f["synckey"] or "").strip() or None,
                    parte_cod=(f["parte"] or "").strip() or None,
                    can=None if f["can"] is None else float(f["can"]),
                    hmoide=_entero(f["hmoide"]),
                    parte_est=_entero(f["est"]),
                    obride=_entero(f["obride"]), cenide=_entero(f["cenide"]),
                    paride=_entero(f["paride"]), caaide=_entero(f["caaide"]),
                    parte_emp=_entero(f["emp"])))
        return sorted(out.values(), key=lambda x: (x.fecha_int, x.ide))

    def lineas_registradas(
        self, claves: Iterable[str], ides: Iterable[int | None]
    ) -> tuple[dict[str, LineaSigrid], dict[int, LineaSigrid]]:
        """F-051 (R15): lo ya registrado por `synckey` **o** por
        `hmores.ide`, en UNA lectura por trozo de `LOTE_PARAMETROS`
        parámetros. Devuelve `({synckey: línea}, {ide: línea})`. Sin `ides`
        es la consulta de hoy (`lineas_por_synckey`)."""
        ks = sorted({k for k in claves if k})
        ids = sorted({int(i) for i in ides if i})
        if not ids:
            return self.lineas_por_synckey(ks), {}
        por_sk: dict[str, LineaSigrid] = {}
        por_ide: dict[int, LineaSigrid] = {}
        pedidas = [("k", k) for k in ks] + [("i", i) for i in ids]
        for trozo in _trozos(pedidas, LOTE_PARAMETROS):
            t_k = [v for t, v in trozo if t == "k"]
            t_i = [v for t, v in trozo if t == "i"]
            conds = []
            if t_k:
                conds.append("hmores.synckey IN ("
                             + ",".join("?" for _ in t_k) + ")")
            if t_i:
                conds.append("hmores.ide IN ("
                             + ",".join("?" for _ in t_i) + ")")
            filas = self._lectura(
                "lineas_registradas",
                "SELECT hmores.ide AS ide, hmores.hmoide AS hmoide, "
                "hmores.reside AS reside, hmores.fec AS fec, "
                "hmores.horide AS horide, hmores.paride AS paride, "
                "auxhor.cod AS hora, hmores.can AS can, hmores.tot AS tot, "
                "hmores.synckey AS synckey FROM hmores "
                "LEFT JOIN auxhor ON auxhor.ide = hmores.horide "
                f"WHERE {' OR '.join(conds)}", t_k + t_i)
            for f in filas:
                ls = self._linea_del_parte(f)
                ls.hmoide = int(f["hmoide"] or 0)
                if ls.synckey in ks:
                    por_sk[ls.synckey] = ls
                if ls.ide in ids:
                    por_ide[ls.ide] = ls
        return por_sk, por_ide

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
        """Solo para `limpiar` del script de pruebas (F-051 D15): el
        registro nunca borra una línea."""
        return {"sql": "DELETE FROM hmores WHERE ide = ?",
                "parameters": [int(ide)]}

    # ------------------- edición en su sitio (F-051) ------------------- #

    def lineas_para_editar(self, ides: Iterable[int | None]
                           ) -> dict[int, LineaSigrid]:
        """F-051 (R12, R18): las líneas que se van a editar o poner a 0,
        con TODO lo que tienen (su parte y su `con.est`, `pre`, cuenta,
        `tex` y si tienen enlaces de Sigrid), justo antes de escribir. UNA
        lectura por trozo de `LOTE_PARAMETROS`; sin `ide` no se lee."""
        ids = sorted({int(i) for i in ides if i})
        out: dict[int, LineaSigrid] = {}
        for trozo in _trozos(ids, LOTE_PARAMETROS):
            enlaces = " OR ".join(f"ISNULL(hmores.{c}, 0) <> 0"
                                  for c in _ENLACES)
            filas = self._lectura(
                "lineas_para_editar",
                "SELECT hmores.ide AS ide, hmores.hmoide AS hmoide, "
                "hmores.reside AS reside, hmores.horide AS horide, "
                "auxhor.cod AS hora, hmores.paride AS paride, "
                "hmores.can AS can, hmores.pre AS pre, hmores.tot AS tot, "
                "hmores.caaide AS caaide, hmores.fec AS fec, "
                "hmores.synckey AS synckey, "
                "CAST(hmores.tex AS NVARCHAR(400)) AS tex, "
                "con.cod AS parte, con.est AS est, "
                f"CASE WHEN {enlaces} THEN 1 ELSE 0 END AS enlazada "
                "FROM hmores LEFT JOIN auxhor ON auxhor.ide = hmores.horide "
                "JOIN con ON con.ide = hmores.hmoide "
                f"WHERE hmores.ide IN ({','.join('?' for _ in trozo)})",
                trozo)
            for f in filas:
                ls = self._linea_del_parte(f)
                ls.hmoide = int(f["hmoide"])
                ls.parte_cod = f["parte"]
                ls.parte_est = None if f["est"] is None else int(f["est"])
                ls.pre = None if f["pre"] is None else float(f["pre"])
                ls.caaide = int(f["caaide"] or 0)
                ls.tex = f["tex"]
                ls.enlazada = bool(f["enlazada"])
                out[ls.ide] = ls
        return out

    def _guarda(self, ide: int, reside: int, can_leido: float | None,
                synckey_leida: str | None,
                hora: str | None = None) -> tuple[str, list]:
        """F-051 (R11): solo cambia la fila si sigue siendo del recurso,
        `M*`, con el `can` y la `synckey` leídos, sin enlaces y en un parte
        En registro. SQL Server la evalúa sobre la fila ANTES del cambio.

        Anexo R30 (R41): con `hora`, en vez de `M*` la línea tiene que
        seguir teniendo ESE código (una incidencia, `CI*`/`CIZ`). Sin ella,
        el texto de F-051 sin cambiar ni un carácter."""
        sin_enlaces = " ".join(f"AND ISNULL({c}, 0) = 0" for c in _ENLACES)
        codigo = "a.cod LIKE 'M%'" if hora is None else "a.cod = ?"
        return (
            ("WHERE ide = ? AND reside = ? "
            "AND ABS(ISNULL(can, 0) - ?) < 0.000001 "
            "AND LTRIM(RTRIM(ISNULL(synckey, ''))) = ? "
            f"{sin_enlaces} "
            "AND EXISTS (SELECT 1 FROM auxhor a WHERE a.ide = hmores.horide "
            f"AND {codigo}) "
            "AND EXISTS (SELECT 1 FROM con c WHERE c.ide = hmores.hmoide "
            "AND c.est = ?)"),
            [int(ide), int(reside), float(can_leido or 0.0),
             (synckey_leida or "").strip()]
            + ([] if hora is None else [hora.strip()]) + [self._est])

    def stmt_editar_fecha_incidencia(
        self, *, ide: int, reside: int, hora_codigo: str,
        synckey_leida: str | None, fecha_int: int, fec_leida: int,
        can_leido: float | None = 0.0,
    ) -> dict:
        """Anexo R30 (R41, design §13.5): cambia SOLO la `fec` de una línea
        de incidencia nuestra, en su sitio (ni hora, `pre`, `can`, partida,
        cuenta, `synckey`, `tex`, `pos` ni parte), con la guarda de F-051 y
        su código: mismo `ide` y recurso, `can` 0, la `synckey` leída, sin
        enlaces y en un parte En registro. D16 (design §11): y en la `fec`
        leída, `fec_leida`; si alguien la movió tras leer, no se pisa. Va
        al final, fuera de `_guarda`: el texto de F-051 no cambia.

        F-062 (R14, D12): un `CIZ` ajeno se mueve con SU `can` leído
        (`can_leido`, 0 o 1); sin él, 0, como hasta ahora (el SQL no
        cambia)."""
        guarda, params = self._guarda(ide, reside, can_leido, synckey_leida,
                                      hora_codigo)
        return {"sql": f"UPDATE hmores SET fec = ? {guarda} AND fec = ?",
                "parameters": [int(fecha_int)] + params + [int(fec_leida)]}

    def stmt_editar_linea(
        self, *, ide: int, reside: int, can_leido: float | None,
        synckey_leida: str | None, horide: int, can: float, pre: float,
        paride: int, caaide: int, fecha_int: int, synckey: str,
        tex: str | None,
    ) -> dict:
        """F-051 (R8-R11): la línea pasa a ser la que habríamos insertado
        (mismos valores y redondeos que `stmt_insert_linea`), en su sitio:
        no cambian `ide`, `pos`, parte, obra, centro ni periodo. `tex` solo
        se escribe si viene (modo pruebas, R10)."""
        guarda, params = self._guarda(ide, reside, can_leido, synckey_leida)
        con_tex = tex is not None
        return {"sql": (
            "UPDATE hmores SET can = ?, pre = ?, tot = ?, horide = ?, "
            "paride = ?, caaide = ?, fec = ?, synckey = ?"
            f"{', tex = ?' if con_tex else ''} {guarda}"),
            "parameters": [round(float(can), 4), float(pre),
                           round(float(can) * float(pre), 2), int(horide),
                           int(paride or 0), int(caaide or 0),
                           int(fecha_int), synckey]
            + ([tex] if con_tex else []) + params}

    def stmt_poner_a_cero(self, *, ide: int, reside: int,
                          can_leido: float | None,
                          synckey_leida: str | None) -> dict:
        """F-051 (R5, D14 = A): `can` y `tot` a 0, nada más, con la misma
        guarda que la edición."""
        guarda, params = self._guarda(ide, reside, can_leido, synckey_leida)
        return {"sql": f"UPDATE hmores SET can = 0, tot = 0 {guarda}",
                "parameters": params}

    # -------------------------- inspección -------------------------- #

    def inspeccionar_mensuales(self, limite: int = 20) -> list[dict[str, Any]]:
        """Últimas líneas M* reales: para fijar el mapeo antes de escribir."""
        filas = self._lectura(
            "inspeccionar_mensuales",
            f"SELECT TOP {int(limite)} hmores.ide AS ide, hmores.hmoide AS "
            "hmoide, hmores.reside AS reside, hmores.fec AS fec, "
            "auxhor.cod AS hora, hmores.can AS can, hmores.canres AS canres, "
            "hmores.pre AS pre, hmores.tot AS tot, hmores.paride AS paride, "
            "hmores.caaide AS caaide, hmores.synckey AS synckey "
            "FROM hmores JOIN auxhor ON auxhor.ide = hmores.horide "
            "WHERE auxhor.cod LIKE 'M%' ORDER BY hmores.ide DESC", [])
        return filas
