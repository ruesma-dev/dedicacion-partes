# application/registro_sigrid.py
"""Registro del periodo en Sigrid vía porcentajes-transfer.

Agrupa las asignaciones del periodo por OBRA (el contrato del transfer es
por obra), llama a preflight/ejecutar secuencialmente y persiste la traza
en la propia asignación (columnas sigrid_*). El porcentaje viaja SOBRE 1.

Las entradas VAR (filas de `obra` con `registro_obra_ide`, F-039) se
agrupan con su obra de registro y cada línea lleva `var_paride` en vez de un
`paride` manual (docs/ARCHITECTURE.md#regla-var).

Cada línea lleva el RECURSO del trabajador (`recurso_ide` = su `ide`, que
es el `res.ide` de Sigrid): el transfer no lo elige (F-026 R18-R19). Las
líneas de un trabajador no vigente en el mes no se mandan ni se trazan; sus
`registro_id` vuelven en `no_vigentes` (F-026 R16,
docs/ARCHITECTURE.md#regla-recurso).

La partida ELEGIDA de la asignación (F-050, R19,
docs/ARCHITECTURE.md#regla-partida) viaja como `paride` y `partida_cod`; un
`overrides` del cuerpo manda sobre ella; sin elegida no viaja partida y el
transfer pone la propuesta.

F-055 (R14, R16, R26): una automática con propuesta GUARDADA viaja con sus
`propuesta_*` (el transfer la valida y, si vale, la escribe); el preflight
del periodo es UNA llamada al lote del transfer y, al volver, cada acción
con método de propuesta guarda su partida en la asignación si sigue sin
elegida (sin evento ni traza). `ejecutar` sigue por obra y en serie.

F-051 (R14, R16): cada línea lleva el `sigrid_hmores_ide` de su asignación
(si lo tiene) y la traza guarda el de cada escrita y cada ya registrada: el
transfer reconoce lo suyo por `hmores.ide` aunque edite una línea de otro
sistema (docs/ARCHITECTURE.md#regla-cero).

F-030 (R23, R25, R31): cada obra lleva además la lista `incidencias` de sus
trabajadores visibles y vigentes (una obra solo con incidencias también va;
sin ninguna, la petición es la de siempre), cada una con la partida elegida
o la propuesta guardada de la asignación del trabajador en esa obra, o 0.
Al volver de `ejecutar`, la traza de cada incidencia
(docs/ARCHITECTURE.md#regla-incidencia). Anexo R30 (R38, R39): las
quitadas no viajan (el preflight las devuelve en `incidencias_quitadas`
para retirarlas a mano) y una registrada lleva sus `hmores_ide_ini`/`_fin`
y `dia_ini`/`_fin`: con ellos el transfer edita su par en vez de escribir
otro.

F-062 (R17, R24; design §9): cada petición lleva además, si no están
vacías, `incidencias_mes` (las del mes de sus recursos en cualquier obra,
con `obra_ide` y traza, sin quitadas), `quitadas` (las quitadas de su obra
con algún `ide` de Sigrid; si no hay petición de esa obra, se crea) y
`cierres_recursos` (los recursos cuya primera petición, en este orden y
tras el filtro `obra_ide`, es esa: el transfer les cierra las rachas del
mes anterior, R12).

F-044 (R10, R30; docs/ARCHITECTURE.md#regla-vinculado): desde el periodo
`sync.vinculados.desde`, cada línea de un trabajador con vinculados
vigentes en el mes lleva `vinculados` (recurso, tipo, código, la partida
elegida o la propuesta guardada de su subfila y su `hmores_ide`; en una
entrada VAR, sin partida: es la del titular). Al volver de `ejecutar`, la
traza de cada vinculado va a su fila de `asignacion_vinculado`; su entrada
de `omitidas` (con `vinculado_ide`) no toca la asignación del titular.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from collections.abc import Callable
from typing import Any, Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

from domain.empresas import visible_en_empresa
from domain.incidencias import letra_y_nombre
from domain.models import FiltroEmpresa
from domain.vigencia import vigente_en
from infrastructure.db.orm_models import (
    AsignacionORM, AsignacionVinculadoORM, IncidenciaORM, ObraORM, PeriodoORM,
    TipoIncidenciaORM, TrabajadorORM,
)
from application.traza_incidencias import (
    campos_de_traza,
    quitada_para_el_modal,
    trazar_incidencias,
)
from application.traza_vinculados import trazar_vinculados
from infrastructure.db.repositories import (
    subfilas_de,
    upsert_asignacion_vinculado,
)
from infrastructure.transfer.transfer_client import TransferClient

logger = logging.getLogger(__name__)

#: Longitudes de las columnas de traza, declaradas en `orm_models.py`. Lo que
#: no quepa se corta antes de escribirlo: un texto de más no puede tumbar la
#: traza de un registro que en Sigrid YA se hizo.
_MAX_MOTIVO = 300
_MAX_USUARIO = 64


def es_metodo_de_propuesta(metodo: str | None) -> bool:
    """¿El método es de una PROPUESTA del transfer (parte anterior, último
    parte o casamiento `auto_*`)? Solo esas se guardan (F-055, R14, R15)."""
    return metodo in ("parte_anterior", "ultimo_parte") or \
        (metodo or "").startswith("auto_")


#: Métodos de la PROPUESTA de una subfila de vinculado (F-044, R9): la CI de
#: su tipo o la partida del titular. `manual` es una elegida: no se guarda.
#: F-068 (R17): y los métodos propios del orden nuevo (historial, nombre y
#: capítulo CI.4); `manual` (la elegida) no es una propuesta.
METODOS_PROPUESTA_VINCULADO = ("ci_tipo", "titular", "parte_anterior",
                               "auto_nombre", "auto_categoria",
                               "capitulo_ci4")


def es_metodo_de_propuesta_vinculado(metodo: str | None) -> bool:
    """¿El método es de una propuesta de subfila? (F-044, R9)."""
    return metodo in METODOS_PROPUESTA_VINCULADO


def _vinculado(v: Any, es_var: bool) -> dict[str, Any]:
    """F-044 (R10): un vinculado como viaja al transfer: su recurso, tipo
    y código, la elegida de su subfila o, sin ella, la propuesta guardada
    (en una entrada VAR, ninguna: va con la del titular) y el `hmores.ide`
    del último registro (R30). Sin elegida ni propuesta, el transfer
    propone. F-068 (R18): su `descripcion`, si la tiene (el nombre con el
    que el transfer casa por nombre)."""
    out: dict[str, Any] = {"recurso_ide": int(v.vinculado_ide),
                           "tipo": v.tipo, "tipo_res": v.tipo_res,
                           "cod": v.cod}
    if v.descripcion is not None:
        out["descripcion"] = v.descripcion
    if es_var:
        pass
    elif v.partida_ide:
        out.update(paride=int(v.partida_ide), partida_cod=v.partida_cod)
    elif v.propuesta_ide:
        out.update(propuesta_paride=int(v.propuesta_ide),
                   propuesta_cod=v.propuesta_cod,
                   propuesta_res=v.propuesta_res,
                   propuesta_metodo=v.propuesta_metodo,
                   propuesta_origen=v.propuesta_origen)
    if v.sigrid_hmores_ide:
        out["hmores_ide"] = int(v.sigrid_hmores_ide)
    return out


class RegistroSigrid:
    def __init__(self, session_factory: sessionmaker[Session],
                 transfer: TransferClient, empresa_imputacion: int, *,
                 vinculados_desde: tuple[int, int] | None = None,
                 subfilas: Callable = subfilas_de) -> None:
        self._sf = session_factory
        self._transfer = transfer
        # F-044 (R10): primer periodo (anio, mes) cuyas líneas llevan sus
        # vinculados (`sync.vinculados.desde`); sin él, ninguno.
        self._vinculados_desde = vinculados_desde
        self._subfilas = subfilas
        # EMPRESA_IMPUTACION hace dos papeles (D1 de F-034): es la empresa
        # POR DEFECTO, que se usa si la petición no trae la elegida, y la
        # EMPRESA DE LAS OBRAS, la que viaja en cada línea sea cual sea la
        # elegida (docs/ARCHITECTURE.md#regla-empresa). Sin valor por defecto
        # aquí: sale siempre del ajuste.
        self._por_defecto = empresa_imputacion

    def _filtro(self, empresa: int | None) -> FiltroEmpresa:
        return FiltroEmpresa(empresa=empresa or self._por_defecto,
                             por_defecto=self._por_defecto,
                             empresa_obras=self._por_defecto)

    # ------------------------------------------------------------- #
    def _payloads(self, s: Session, anio: int, mes: int,
                  overrides: dict[int, int],
                  trabajador_ide: Optional[int],
                  filtro: FiltroEmpresa,
                  quitadas: list[tuple] | None = None,
                  ) -> tuple[list[dict[str, Any]], list[int]]:
        """Payloads por obra y `registro_id` de los no vigentes en el mes.
        Con `quitadas`, añade ahí las incidencias quitadas visibles y
        vigentes (R38), que no van en ningún payload."""
        filas = s.execute(
            select(AsignacionORM, TrabajadorORM, ObraORM)
            .join(PeriodoORM, PeriodoORM.id == AsignacionORM.periodo_id)
            .join(TrabajadorORM,
                  TrabajadorORM.ide == AsignacionORM.trabajador_ide)
            .join(ObraORM, ObraORM.ide == AsignacionORM.obra_ide)
            .where(PeriodoORM.anio == anio, PeriodoORM.mes == mes,
                   AsignacionORM.porcentaje > 0,
                   # `is not None` (F-056): un 0 filtra, no coge el mes.
                   *( [AsignacionORM.trabajador_ide == trabajador_ide]
                      if trabajador_ide is not None else [] ))
            .order_by(ObraORM.cod, TrabajadorORM.nombre)
        ).all()
        # Visibilidad por empresa: la misma regla que el cuadrante (F-034,
        # R2-R3). Cada línea viaja con la empresa de las obras, no con la
        # elegida (R7). Las líneas en obras de otra empresa se mandan igual
        # (R8): el transfer las omite con motivo y `_trazar` lo deja en la
        # asignación.
        por_obra: dict[int, dict[str, Any]] = {}
        no_vigentes: list[int] = []
        # F-044 (R10): las líneas que se mandan, para sus vinculados.
        mandadas: list[tuple[Any, dict[str, Any], bool]] = []
        # F-030 (R25): partida de la asignación de cada (trabajador, obra).
        partidas: dict[tuple[int, int], int] = {}
        for a, t, o in filas:
            if not visible_en_empresa(t.empresa, filtro):
                continue
            # Vigencia por mes (F-026 R16): ni se manda ni se traza.
            if not vigente_en(t.activo, t.fecha_baja, anio, mes):
                no_vigentes.append(a.id)
                continue
            if not a.es_postventa:
                partidas.setdefault((t.ide, o.ide), int(
                    a.partida_ide or a.propuesta_ide or 0))
            # Entrada VAR (F-039, R20): a la petición de su obra de registro,
            # junto a las demás líneas de esa obra.
            obra = ({"ide": o.registro_obra_ide,
                     "codigo": o.registro_obra_cod, "nombre": None}
                    if o.registro_obra_ide else
                    {"ide": o.ide, "codigo": o.cod, "nombre": o.descripcion})
            grupo = por_obra.setdefault(obra["ide"], {"obra": obra,
                                                      "lineas": []})
            linea = {
                "registro_id": a.id, "ano": anio, "mes": mes,
                "porcentaje": round(float(a.porcentaje) / 100.0, 4),
                "recurso_ide": t.ide, "dni": t.dni, "nombre": t.nombre,
                "categoria": t.categoria,
                "es_postventa": bool(a.es_postventa),
                "empresa": filtro.empresa_obras,
            }
            if o.registro_paride:
                # Su partida es la de la entrada; un override no la cambia.
                linea["var_paride"] = int(o.registro_paride)
            elif overrides.get(a.id):
                linea["paride"] = int(overrides[a.id])
            elif a.partida_ide:
                linea["paride"] = int(a.partida_ide)
                linea["partida_cod"] = a.partida_cod
            elif a.propuesta_ide:
                # F-055 (R16): la propuesta guardada; el transfer la valida.
                linea.update(propuesta_paride=int(a.propuesta_ide),
                             propuesta_cod=a.propuesta_cod,
                             propuesta_res=a.propuesta_res,
                             propuesta_metodo=a.propuesta_metodo,
                             propuesta_origen=a.propuesta_origen)
            # F-051 (R14): la línea de Sigrid que ya tiene la asignación,
            # para que el transfer la reconozca aunque su `synckey` sea de
            # otro sistema. Sin ella, la línea viaja como antes (`getattr`:
            # los dobles de los tests anteriores a F-051 no la traen).
            hmores_ide = getattr(a, "sigrid_hmores_ide", None)
            if hmores_ide:
                linea["hmores_ide"] = int(hmores_ide)
            grupo["lineas"].append(linea)
            mandadas.append((a, linea, bool(o.registro_paride)))
        self._sumar_vinculados(s, anio, mes, mandadas)
        del_mes = self._sumar_incidencias(s, anio, mes, trabajador_ide,
                                          filtro, por_obra, partidas,
                                          quitadas)
        payloads = list(por_obra.values())
        for p in payloads:
            recursos = {x["recurso_ide"] for x in [
                *p["lineas"], *p.get("incidencias", [])]}
            mias = [x for x in del_mes if x["recurso_ide"] in recursos]
            if mias:
                p["incidencias_mes"] = mias
        return payloads, sorted(no_vigentes)

    def _sumar_vinculados(self, s: Session, anio: int, mes: int,
                          mandadas: list[tuple[Any, dict[str, Any], bool]]
                          ) -> None:
        """F-044 (R10): `vinculados` en cada línea mandada de un periodo
        ≥ `desde` cuyo trabajador tenga alguno vigente en el mes. Antes de
        `desde`, sin él o sin líneas, no se lee nada."""
        desde = self._vinculados_desde
        if desde is None or (anio, mes) < tuple(desde) or not mandadas:
            return
        de = self._subfilas(s, [a for a, _, _ in mandadas], (anio, mes))
        for a, linea, es_var in mandadas:
            suyas = de(a)
            if suyas:
                linea["vinculados"] = [_vinculado(v, es_var) for v in suyas]

    @staticmethod
    def _designar_cierres(payloads: list[dict[str, Any]]) -> None:
        """F-062 (R24, design §9): cada recurso (de líneas o incidencias)
        va a `cierres_recursos` de la PRIMERA petición donde sale, en el
        orden de los payloads; vacía, la clave no va."""
        vistos: set[int] = set()
        for p in payloads:
            suyos = []
            for x in [*p["lineas"], *p.get("incidencias", [])]:
                r = x["recurso_ide"]
                if r and r not in vistos:
                    vistos.add(r)
                    suyos.append(r)
            if suyos:
                p["cierres_recursos"] = suyos

    def _sumar_incidencias(self, s: Session, anio: int, mes: int,
                           trabajador_ide: int | None,
                           filtro: FiltroEmpresa,
                           por_obra: dict[int, dict[str, Any]],
                           partidas: dict[tuple[int, int], int],
                           quitadas: list[tuple] | None = None,
                           ) -> list[dict[str, Any]]:
        """F-030 (R23, R25): las incidencias del periodo, en la petición de
        su obra (nunca VAR ni postventa, R19), con la visibilidad y la
        vigencia de las líneas. Una obra solo con incidencias va al final,
        en el orden de su código; sin ninguna, nada cambia.

        Anexo R30: una quitada no va (a `quitadas`, si se pide; R38); una
        con traza lleva sus `hmores_ide_*` y `dia_*`, nulos los que falten
        (R39). Sin traza, el elemento de siempre.

        F-062 (R17, R24): devuelve las del mes (no quitadas, con
        `obra_ide`), para `incidencias_mes`; una quitada con algún `ide`
        va además a `quitadas` de la petición de su obra."""
        filas = s.execute(
            select(IncidenciaORM, TrabajadorORM, ObraORM)
            .join(PeriodoORM, PeriodoORM.id == IncidenciaORM.periodo_id)
            .join(TrabajadorORM,
                  TrabajadorORM.ide == IncidenciaORM.trabajador_ide)
            .join(ObraORM, ObraORM.ide == IncidenciaORM.obra_ide)
            .where(PeriodoORM.anio == anio, PeriodoORM.mes == mes,
                   *( [IncidenciaORM.trabajador_ide == trabajador_ide]
                      if trabajador_ide is not None else [] ))
            .order_by(ObraORM.cod, TrabajadorORM.nombre,
                      IncidenciaORM.dia_desde, IncidenciaORM.id)
        ).all()
        del_mes: list[dict[str, Any]] = []
        for i, t, o in filas:
            if not visible_en_empresa(t.empresa, filtro) or \
                    not vigente_en(t.activo, t.fecha_baja, anio, mes):
                continue
            item = {
                "id": i.id, "recurso_ide": t.ide,
                "empresa": filtro.empresa_obras, "codigo": i.codigo,
                "ano": anio, "mes": mes, "desde": i.dia_desde,
                "hasta": i.dia_hasta,
                "paride": partidas.get((t.ide, o.ide), 0)}
            item.update(campos_de_traza(i))
            if i.quitada:
                if quitadas is not None:
                    quitadas.append((i, t, o))
                if item.get("hmores_ide_ini") or item.get("hmores_ide_fin"):
                    self._grupo(por_obra, o).setdefault(
                        "quitadas", []).append({**item, "obra_ide": o.ide})
                continue
            self._grupo(por_obra, o).setdefault(
                "incidencias", []).append(item)
            del_mes.append({**item, "obra_ide": o.ide})
        return del_mes

    @staticmethod
    def _grupo(por_obra: dict[int, dict[str, Any]], o: Any
               ) -> dict[str, Any]:
        """La petición de la obra `o`; si no la hay, una nueva al final."""
        return por_obra.setdefault(o.ide, {
            "obra": {"ide": o.ide, "codigo": o.cod, "nombre": o.descripcion},
            "lineas": []})

    @staticmethod
    def _quitadas(s: Session, filas: list[tuple]) -> list[dict[str, Any]]:
        """R38: las quitadas para el modal (retirarlas a mano en Sigrid):
        trabajador, obra, código con su letra, días, parte y `ide`s. La
        letra, del catálogo; sin él, la de `letra_y_nombre`."""
        if not filas:
            return []
        codigos = sorted({i.codigo for i, _, _ in filas})
        letras = dict(s.execute(
            select(TipoIncidenciaORM.codigo, TipoIncidenciaORM.letra)
            .where(TipoIncidenciaORM.codigo.in_(codigos))).all())
        return [quitada_para_el_modal(
                    i, t, o, letras.get(i.codigo)
                    or letra_y_nombre(None, i.codigo)[0])
                for i, t, o in filas]

    # ------------------------------------------------------------- #
    def preflight(self, anio: int, mes: int,
                  overrides: Optional[dict[int, int]] = None,
                  trabajador_ide: Optional[int] = None,
                  empresa: int | None = None,
                  obra_ide: int | None = None) -> dict:
        """`obra_ide` (F-050, M2 punto 5): solo la petición de esa obra, la
        del grupo (la de registro en las entradas VAR). Es lo que repite el
        modal al cambiar una partida, en vez del mes entero.

        Anexo R30 (R38): si hay incidencias quitadas, la respuesta las lista
        en `incidencias_quitadas`; si no, la clave no está."""
        filas_quitadas: list[tuple] = []
        with self._sf() as s:
            payloads, no_vigentes = self._payloads(
                s, anio, mes, overrides or {}, trabajador_ide,
                self._filtro(empresa), filas_quitadas)
            if obra_ide is not None:
                filas_quitadas = [f for f in filas_quitadas
                                  if f[2].ide == obra_ide]
            quitadas = self._quitadas(s, filas_quitadas)
        if obra_ide is not None:
            payloads = [p for p in payloads if p["obra"]["ide"] == obra_ide]
        self._designar_cierres(payloads)
        resultados = [{"obra": p["obra"], **r} for p, r in zip(
            payloads, self._preflight_lote(payloads))]
        self._guardar_propuestas(resultados)
        respuesta = {"ok": all(r.get("ok") for r in resultados) if resultados
                     else True, "obras": resultados, "no_vigentes": no_vigentes}
        if quitadas:
            respuesta["incidencias_quitadas"] = quitadas
        return respuesta

    def _preflight_lote(self, payloads: list[dict]) -> list[dict]:
        """F-055 (R26): UNA llamada al lote del transfer; por obra, la
        respuesta del preflight de hoy. Si el lote falla o no trae una
        entrada por obra, cada obra lleva el error."""
        if not payloads:
            return []
        r = self._transfer.preflight_lote(
            [{**p, "pisar_claves": []} for p in payloads])
        obras = r.get("obras")
        if r.get("ok") is True and isinstance(obras, list) \
                and len(obras) == len(payloads):
            return obras
        error = r.get("error") or "el transfer no devolvió todas las obras"
        return [{"ok": False, "error": error} for _ in payloads]

    def _guardar_propuestas(self, resultados: list[dict]) -> None:
        """F-055 (R14): la partida de cada acción con método de propuesta,
        en su asignación, SOLO si sigue sin elegida. Con el ORM, como
        `_trazar`; sin evento y sin tocar `sigrid_*` ni la respuesta."""
        propuestas = [a for r in resultados if r.get("ok")
                      for a in r.get("acciones", [])
                      if a.get("paride")
                      and es_metodo_de_propuesta(a.get("partida_metodo"))]
        # F-044 (R9): igual la de cada subfila (`vinculados` del preflight:
        # `{registro_id, recurso_ide, paride, partida_*}`), en su fila de
        # `asignacion_vinculado` y solo si sigue sin elegida.
        de_subfilas = [v for r in resultados if r.get("ok")
                       for v in r.get("vinculados") or []
                       if v.get("paride") and es_metodo_de_propuesta_vinculado(
                           v.get("partida_metodo"))]
        if not propuestas and not de_subfilas:
            return
        with self._sf() as s:
            for v in de_subfilas:
                s.execute(upsert_asignacion_vinculado(
                    int(v["registro_id"]), int(v["recurso_ide"]),
                    {"propuesta_ide": v["paride"],
                     "propuesta_cod": v.get("partida_cod"),
                     "propuesta_res": v.get("partida_res"),
                     "propuesta_metodo": v.get("partida_metodo"),
                     "propuesta_origen": v.get("partida_origen")},
                    donde=AsignacionVinculadoORM.partida_ide.is_(None)))
            for a in propuestas:
                s.execute(
                    update(AsignacionORM)
                    .where(AsignacionORM.id == a["registro_id"],
                           AsignacionORM.partida_ide.is_(None))
                    .values(propuesta_ide=a["paride"],
                            propuesta_cod=a.get("partida_cod"),
                            propuesta_res=a.get("partida_res"),
                            propuesta_metodo=a.get("partida_metodo"),
                            propuesta_origen=a.get("partida_origen")))
            s.commit()

    # ------------------------------------------------------------- #
    def ejecutar(self, anio: int, mes: int, *, pisar_claves: list[str],
                 overrides: Optional[dict[int, int]] = None,
                 usuario: str = "local",
                 trabajador_ide: Optional[int] = None,
                 empresa: int | None = None) -> dict:
        with self._sf() as s:
            payloads, no_vigentes = self._payloads(
                s, anio, mes, overrides or {}, trabajador_ide,
                self._filtro(empresa))
        self._designar_cierres(payloads)
        resultados = []
        for p in payloads:
            r = self._transfer.ejecutar({**p, "pisar_claves": pisar_claves,
                                         "usuario": usuario})
            resultados.append({"obra": p["obra"], **r})
            if r.get("ok"):
                self._trazar(r, usuario)
        return {"ok": all(x.get("ok") for x in resultados) if resultados
                else True, "obras": resultados, "no_vigentes": no_vigentes}

    def _trazar(self, r: dict, usuario: str) -> None:
        """Persiste en la asignación qué hizo Sigrid con ella.

        Las sentencias se construyen con el ORM (`update(AsignacionORM)`), no
        con SQL crudo: un nombre de columna mal escrito falla al importar, no
        en producción contra la base.
        """
        ahora = datetime.now(timezone.utc)
        quien = (usuario or "")[:_MAX_USUARIO]
        with self._sf() as s:
            for e in r.get("escritas", []):
                s.execute(
                    update(AsignacionORM)
                    .where(AsignacionORM.id == e["registro_id"])
                    .values(sigrid_estado="registrado",
                            sigrid_parte_cod=e.get("parte_cod"),
                            sigrid_hmores_ide=e.get("hmores_ide"),
                            sigrid_motivo=None,
                            sigrid_registrado_at_utc=ahora,
                            sigrid_registrado_by=quien))
            for rid in r.get("ya_registradas", []):
                # Solo asciende el estado, y solo si aún no era 'registrado':
                # no se pisa la marca de tiempo de quien lo registró de verdad.
                s.execute(
                    update(AsignacionORM)
                    .where(AsignacionORM.id == rid,
                           AsignacionORM.sigrid_estado.is_distinct_from(
                               "registrado"))
                    .values(sigrid_estado="registrado"))
            # F-051 (R16): el `hmores.ide` de cada ya registrada, también
            # de las registradas antes de F-051 (el JSON trae las claves
            # como texto).
            for rid, ide in (r.get("ya_registradas_ide") or {}).items():
                if ide:
                    s.execute(
                        update(AsignacionORM)
                        .where(AsignacionORM.id == int(rid))
                        .values(sigrid_hmores_ide=int(ide)))
            for o in r.get("omitidas", []):
                if "vinculado_ide" in o:
                    continue            # F-044 (R30): la de su subfila
                s.execute(
                    update(AsignacionORM)
                    .where(AsignacionORM.id == o["registro_id"])
                    .values(sigrid_estado="omitido",
                            sigrid_motivo=(o.get("motivo") or "")[:_MAX_MOTIVO]))
            trazar_vinculados(s, r)
            # F-030 (R31): la de cada incidencia, en la misma sesión.
            trazar_incidencias(s, r.get("incidencias") or [], ahora, quien,
                               cierres=r.get("cierres_racha") or [],
                               no_coincide=r.get("no_coincide") or [])
            s.commit()
