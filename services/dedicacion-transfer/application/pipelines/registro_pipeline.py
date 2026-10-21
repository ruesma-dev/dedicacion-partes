# application/pipelines/registro_pipeline.py
"""Pipeline de registro de PORCENTAJES en los partes de trabajo de Sigrid.

Orquesta las reglas; no las enuncia. La fuente normativa es
`docs/ARCHITECTURE.md` § Semántica de dominio imprescindible.

Pasos (el preflight ejecuta 0-8; la escritura, 0-10):

  0. EMPRESA de la petición y OBRA DE ORIGEN, en los dos modos
     (ARCHITECTURE.md#regla-empresa). Sin empresa, o con la obra en otra
     empresa, todas las líneas salen omitidas aquí, sin seguir.
  1. Resolver los DESTINOS: la obra normal (en pruebas, la de pruebas) y,
     si hay líneas de postventa, la obra de postventa con su PARTIDA
     (ARCHITECTURE.md#regla-p5), todas en la empresa de la petición.
  2. El RECURSO de cada línea es el que manda la API (`recurso_ide`); el
     transfer no lo elige ni lee `res.conide`
     (ARCHITECTURE.md#regla-recurso). Sin él, la regla omite la línea.
  3. Cargar los tipos de hora de los recursos implicados (reshor).
  4. Aplicar las REGLAS de la línea (ARCHITECTURE.md#regla-p1 … #regla-p3,
     #regla-p5). La línea que trae `var_paride` (una entrada VAR del
     cuadrante) va a esa partida o se omite, antes del override manual
     (ARCHITECTURE.md#regla-var). La partida elegida de una línea de obra
     tiene que ser hoja activa del presupuesto de origen o se omite; la que
     no trae partida lleva la PROPUESTA, con una sola lectura del historial
     por petición (ARCHITECTURE.md#regla-partida, F-050).
  4 bis. CUENTA ANALÍTICA de cada acción `escribir` en el centro de su obra
     destino (ARCHITECTURE.md#regla-analitica): la del recurso y, si no da,
     la de la partida de coste. Una lectura de partidas por petición y una
     de cuentas por centro, sin `try`: si fallan, la petición falla.
  5. Elegir el parte de cada DESTINO+MES entre TODOS los del periodo
     (ARCHITECTURE.md#regla-analitica): el En registro de mayor `ide`; si
     no hay ninguno, uno nuevo (complementario si hay cerrados) con el
     código de la empresa de la obra.
  6. Idempotencia por synckey ('porcentajes:{id}') -> ya_registrado, en
     cualquier parte, también cerrado.
  6 bis. CONFLICTOS de línea SIN PARTIDA, por línea
     (ARCHITECTURE.md#regla-sin-partida) -> confirmar la imputación sin
     partida. Van los PRIMEROS: los otros dos avisos dan por hecho que esa
     línea se escribe.
  7. CONFLICTOS de pisado, por identidad de la línea
     (ARCHITECTURE.md#regla-conflicto), contra las líneas de TODOS los
     partes del periodo -> confirmar pisado; si choca con un parte
     CERRADO, la acción se omite (`parte_cerrado`).
  7 bis. CONFLICTOS de sobrecarga, por jornada del recurso en el parte
     (ARCHITECTURE.md#regla-capacidad) -> confirmar escritura. Van DESPUÉS
     de los de pisado: su cifra ya presupone que el pisado ocurre.
  8. (fin del preflight)

  Las INCIDENCIAS de la petición (F-030, ARCHITECTURE.md#regla-incidencia)
  se deciden tras el paso 4 con `reglas_incidencias` y comparten con las
  líneas la empresa (paso 0), las horas (paso 3), la validación de la
  partida, la cuenta analítica (4 bis), el parte (5), el modo pruebas y el
  alta (9); NO entran en los pasos 6 bis, 7 ni 7 bis (R28). Tras el paso 5,
  R27: UNA lectura de las líneas de incidencia del mes (`incidencias_del_mes`)
  solo si alguna se va a escribir. Sin incidencias, todo es como antes.
  9. Crear los partes que falten (alta protegida, releer el periodo y,
     si no aparece uno En registro, UN reintento con otro código).
 10. EDITAR en su sitio la línea al 0 % de cada acción (`linea_cero`) y
     el choque de cada pisado confirmado, poner a 0 los choques que sobran
     e insertar el resto (por lotes), tras releer lo que se va a tocar;
     nunca un DELETE (ARCHITECTURE.md#regla-cero, F-051).
"""
from __future__ import annotations

import logging
import time
import unicodedata
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Optional

from application.services.cuenta_analitica import (
    origen_subcuenta, resolver_cuenta, subcuenta_de_linea,
)
from application.services.estado_parte import (
    aviso_de_parte, elegir_parte, motivo_choque, nombre_estado,
)
from application.services.partida_resolver import construir_catalogo
from application.services.propuesta_partida import (
    MOTIVO_PARTIDA_NO_HOJA, Propuesta, catalogo, mayor_inicial,
    proponer_partida, ventana,
)
from application.services.reglas_incidencias import (
    decidir_incidencia, reconciliar, synckey_incidencia,
)
from application.services.reglas_porcentajes import (
    AVISO_LINEA_CERO, AVISO_QUEDAN_A_CERO, AVISO_SIN_PARTIDA,
    MOTIVO_EMPRESA_OBRA, MOTIVO_LINEA_CAMBIADA, MOTIVO_PARTIDA_PV_NO_HOJA,
    MOTIVO_SIN_PARTIDA, MOTIVO_SOBRECARGA, ReglasPorcentajes, clave_conflicto, clave_sin_partida,
    clave_sobrecarga, criterio_choque, emparejar_ceros, empresa_de_peticion,
    es_linea_mensual, es_nuestra_de_otra, evaluar_capacidad,
    pisables_al_cero, repartir_choques, sin_partida, synckey_tras_editar,
)
from application.services.universo_postventa import (
    cargar_catalogo_postventa, casar_postventa,
)
from application.services.universo_var import (
    MOTIVO_VAR_POSTVENTA, cargar_catalogo_var, partida_var_de,
)
from domain.models.registro_models import (
    AccionIncidencia, AccionLinea, Conflicto, IncidenciaEntrada, LineaEntrada,
    ObraEntrada, ParteDestino, Preflight, ResultadoRegistro,
)
from infrastructure.sigrid.sigrid_write_client import (
    medir_lecturas, synckey_de,
)

logger = logging.getLogger(__name__)

#: Reloj del resumen del preflight (aparte para poder fijarlo en los tests).
_ahora = time.perf_counter


def _norm(texto: Optional[str]) -> str:
    plano = unicodedata.normalize("NFD", texto or "")
    sin = "".join(c for c in plano if unicodedata.category(c) != "Mn")
    return " ".join(sin.lower().split())


def _sumar_aviso(a: AccionLinea, *textos: str | None) -> None:
    """Suma textos al `aviso` de la acción, que es lo que pinta el front
    (F-037 R6): nunca sustituye al que ya traía."""
    partes = [x for x in (a.aviso, *textos) if x]
    a.aviso = " · ".join(partes) if partes else None


def _fila(ls) -> dict:
    """F-051 (R18): todo lo que tiene una línea que se va a tocar."""
    return {"can": ls.can, "pre": ls.pre, "tot": ls.tot,
            "horide": ls.horide, "hora_codigo": ls.hora_codigo,
            "paride": ls.paride, "caaide": ls.caaide,
            "fecha_int": ls.fecha_int, "synckey": ls.synckey, "tex": ls.tex}


def _traza(que: str, registro_id: int, ls, despues: dict) -> dict:
    """F-051 (R18): el log y la entrada de `editadas`/`a_cero` de una
    línea, con lo que tenía y lo que queda (para que F-033 la deshaga). Se
    escribe ANTES de enviar la sentencia: si la escritura falla a medias,
    el log ya dice qué se iba a tocar."""
    t = {"registro_id": registro_id, "ide": ls.ide, "hmoide": ls.hmoide,
         "parte_cod": ls.parte_cod, "antes": _fila(ls), "despues": despues}
    logger.info("[registro] %s ide=%s parte=%s registro=%s antes=%s "
                "despues=%s", que, ls.ide, ls.parte_cod, registro_id,
                t["antes"], despues)
    return t


def _nueva(a: AccionLinea) -> dict:
    """Lo que se escribiría, tal y como viaja dentro de un `Conflicto`.

    Los dos tipos de conflicto lo publican igual: si divergieran, el front
    tendría que saber de cuál viene para leerlo.
    """
    return {"registro_id": a.registro_id, "can": a.can, "tot": a.tot,
            "hora_codigo": a.hora_codigo, "fecha_int": a.fecha_int,
            "partida_cod": a.partida_cod}


class RegistroPipeline:
    def __init__(self, *, cliente, settings) -> None:
        self._cli = cliente
        self._st = settings

    # ------------------------------------------------------------- #
    def _obra_origen(self, obra: ObraEntrada, empresa: int) -> ObraEntrada:
        """Paso 0. La obra de origen en Sigrid, en los DOS modos: por `ide`
        si viene y, si no, por código Y empresa
        (ARCHITECTURE.md#regla-empresa)."""
        if obra.ide:
            real = self._cli.obra_por_ide(int(obra.ide))
        elif obra.codigo:
            real = self._cli.obra_por_codigo(obra.codigo, empresa)
        else:
            real = None
        if real is None:
            raise RuntimeError(
                f"obra no encontrada en Sigrid (ide={obra.ide} "
                f"cod={obra.codigo} empresa={empresa})")
        return real

    # ------------------------------------------------------------- #
    def _obra_destino(self, origen: ObraEntrada,
                      empresa: int) -> tuple[ObraEntrada, bool]:
        """Paso 1a. En pruebas, TODO va a la obra de pruebas DE LA EMPRESA
        de la petición; si no existe en ella, no se escribe nada."""
        if self._st.obra_pruebas_forzar:
            destino = self._cli.obra_por_codigo(self._st.obra_pruebas_cod,
                                                empresa)
            if destino is None:
                raise RuntimeError(
                    f"obra de pruebas {self._st.obra_pruebas_cod} "
                    f"no encontrada en la empresa {empresa}")
            logger.warning(
                "[registro] MODO PRUEBAS: la obra %s se ignora; se escribe "
                "en %s (%s)", origen.codigo, destino.codigo, destino.nombre)
            return destino, True
        return origen, False

    # ------------------------------------------------------------- #
    def _todas_omitidas(self, obra: ObraEntrada, lineas: list[LineaEntrada],
                        motivo_empresa: Optional[str],
                        incidencias: list[IncidenciaEntrada]) -> Preflight:
        """Fin anticipado del paso 0: ninguna línea se puede escribir.

        Las acciones salen del MISMO `decidir` que el resto, que omite cada
        línea por su empresa antes de mirar horas o recursos; las de las
        incidencias, del mismo `decidir_incidencia` (F-030)."""
        reglas = ReglasPorcentajes({}, motivo_empresa=motivo_empresa)
        return Preflight(
            obra_destino=obra, obra_origen=obra,
            forzada_pruebas=self._st.obra_pruebas_forzar,
            acciones=[reglas.decidir(l) for l in lineas],
            incidencias=[a for i in incidencias for a in decidir_incidencia(
                i, {}, motivo_empresa=motivo_empresa)])

    # ------------------------------------------------------------- #
    def _destino_postventa(
        self, obra_origen: ObraEntrada, forzada: bool,
        destino_pruebas: ObraEntrada, empresa: int,
    ) -> tuple[Optional[ObraEntrada], Optional[dict], Optional[str], dict]:
        """Paso 1b. Obra de postventa + partida de la obra original.

        Devuelve (obra_destino_pv, partida, motivo_si_falla, catálogo). El
        catálogo es el de ESTA petición: no se guarda en la instancia (F-025
        R9). Carga y casado son las mismas funciones que el universo de
        postventa (`universo_postventa`). En modo pruebas el parte se
        escribe en la obra de pruebas, pero la partida se resuelve
        igualmente contra la obra de postventa real (para validar el
        casado). Ver `ARCHITECTURE.md#regla-p5`.
        """
        catalogo = cargar_catalogo_postventa(self._cli, self._st, empresa)
        partida, motivo = casar_postventa(catalogo, obra_origen.codigo,
                                          obra_origen.nombre)
        if partida is None:
            return None, None, motivo, catalogo.nodos
        destino = destino_pruebas if forzada else catalogo.obra
        return destino, partida, None, catalogo.nodos

    # ------------------------------------------------------------- #
    @staticmethod
    def _es_hoja_activa_pv(nodos: dict, paride: int) -> bool:
        """¿`paride` es una partida hoja activa del presupuesto de la obra
        de postventa leído en esta petición? Es el universo de
        `ARCHITECTURE.md#regla-p5`, el mismo que se publica en
        `partidas_postventa`."""
        nodo = nodos.get(int(paride))
        return bool(nodo and nodo.es_hoja and nodo.activa)

    # ------------------------------------------------------------- #
    def _historial(self, lineas: list[LineaEntrada]) -> list:
        """F-050 (R7): UNA lectura del historial de partidas de los recursos
        de las líneas automáticas, en la ventana que acaba en su periodo.
        Sin `try`: si falla, la petición falla sin proponer ni escribir."""
        ano, mes = max((l.ano, l.mes) for l in lineas)
        desde, hasta = ventana(ano, mes, self._st.propuesta_meses_atras)
        return self._cli.historial_partidas(
            sorted({l.recurso_ide for l in lineas}), desde, hasta)

    # ------------------------------------------------------------- #
    def _validas(self, normales: list[LineaEntrada],
                 incidencias: list[AccionIncidencia]) -> dict:
        """F-055 (R3): UNA lectura de `validar_partidas` con la elegida de
        cada línea de obra normal o, sin ella, su propuesta guardada, y la
        partida de cada incidencia que se escribe (F-030 R25). Sin ninguna
        no se lee. Sin `try`: si falla, la petición falla."""
        parides = ({int(l.paride or l.propuesta_paride or 0)
                    for l in normales}
                   | {a.paride for a in incidencias}) - {0}
        return self._cli.validar_partidas(sorted(parides)) if parides else {}

    # ------------------------------------------------------------- #
    def _horas_de_lineas(self, lineas: list[LineaEntrada]) -> dict:
        """Pasos 2-3: horas de los recursos que traen las líneas, sin tocar
        las líneas ni leer `res` (F-026 R19)."""
        todos = {int(l.recurso_ide) for l in lineas if l.recurso_ide}
        return self._cli.horas_de_recursos(sorted(todos)) if todos else {}

    # ------------------------------------------------------------- #
    def _cuentas(self, escribir: list[AccionLinea], horas: dict,
                 obra_de) -> None:
        """Paso 4 bis (ARCHITECTURE.md#regla-analitica): `caa_*` de cada
        acción `escribir` en el centro de SU obra destino.

        Las partidas se leen UNA vez por petición y solo las de las líneas
        cuyo recurso no da subcuenta; las cuentas, una vez por centro con
        las subcuentas de los dos orígenes. Sin `try` (R7): escribir 0 en
        silencio porque una lectura falló es el defecto que se corrige."""
        def horas_de(a: AccionLinea) -> list:
            return horas.get(int(a.recurso_ide), [])

        parides = {int(a.paride) for a in escribir
                   if a.paride and not subcuenta_de_linea(horas_de(a),
                                                          a.hora_ide)}
        partidas = self._cli.partidas_de_lineas(parides) if parides else {}
        por_obra: dict[int, tuple[ObraEntrada, list[AccionLinea]]] = {}
        for a in escribir:
            d = obra_de(a)
            por_obra.setdefault(int(d.ide), (d, []))[1].append(a)
        for d, grupo in por_obra.values():
            origenes = {id(a): origen_subcuenta(
                            horas_de(a), a.hora_ide,
                            partidas.get(int(a.paride or 0)))
                        for a in grupo}
            cenide = int(getattr(d, "cenide", 0) or 0)
            pedidas = {o.sub for o in origenes.values() if o.sub}
            cuentas = (self._cli.cuentas_de_centro(cenide, int(d.empresa),
                                                   pedidas)
                       if pedidas and cenide else {})
            por_origen = {"recurso": 0, "partida": 0, None: 0}
            for a in grupo:
                o = origenes[id(a)]
                c = resolver_cuenta(o.sub, cuentas, d.codigo)
                a.caa_ide, a.caa_cod = c.caa_ide, c.caa_cod
                a.caa_motivo, a.caa_aviso = c.motivo, c.aviso
                a.caa_origen, a.caa_nota = o.origen, o.nota
                _sumar_aviso(a, c.aviso, o.nota)
                por_origen[o.origen] += 1
            logger.info(
                "[registro] cuenta analitica obra=%s recurso=%s partida=%s "
                "ninguna=%s", d.codigo, por_origen["recurso"],
                por_origen["partida"], por_origen[None])

    # ------------------------------------------------------------- #
    def _nombre_estado(self, est: int | None) -> str:
        return nombre_estado(est, est_cerrado=self._st.est_parte_cerrado,
                             est_imputado=self._st.est_parte_imputado)

    # ------------------------------------------------------------- #
    def _parte_del_periodo(self, d: ObraEntrada, ano: int,
                           mes: int) -> ParteDestino:
        """El parte que recibe las líneas de la obra `d` en el periodo
        (`estado_parte.elegir_parte`, la regla de `partes`)."""
        return elegir_parte(
            ano, mes, self._cli.partes_del_periodo(int(d.ide), ano, mes),
            est_registro=self._st.est_parte_activo)

    # ------------------------------------------------------------- #
    def _parte_nuevo_o_del_periodo(self, d: ObraEntrada, ano: int,
                                   mes: int,
                                   leido: ParteDestino | None = None
                                   ) -> ParteDestino:
        """Paso 5 para un destino y periodo: el parte elegido o, si no
        hay ninguno En registro, el código del nuevo, con su aviso.
        `leido`: el de `_parte_del_periodo` si ya se leyó (anexo R30, R33
        en pruebas), para no leerlo dos veces."""
        p = leido if leido is not None else self._parte_del_periodo(d, ano,
                                                                    mes)
        p.obra_cod = d.codigo
        if not p.existe:
            p.cod = self._cli.siguiente_cod_pt(ano, int(d.empresa))
        p.aviso = aviso_de_parte(p, {
            ps.cod: self._nombre_estado(ps.est)
            for ps in p.del_periodo if ps.cod in p.cerrados})
        return p

    # ------------------------------------------------------------- #
    def _reconciliar_incidencias(
        self, inc_escribir: list[AccionIncidencia],
        entradas: list[IncidenciaEntrada], destino: ObraEntrada,
        forzada: bool, leidos: dict[tuple[int, int, int], ParteDestino],
    ) -> None:
        """R27, R33 y anexo R30 (R40-R44): las líneas de incidencia del mes
        de esos recursos y las de la traza de la api (sus `hmores.ide`), en
        UNA lectura por mes; en pruebas, solo en los partes del periodo de
        la obra de pruebas (ese parte queda en `leidos` para el paso 5).
        Luego `reconciliar`. Sin `try`: si falla o viene `truncated`, la
        petición falla sin escribir nada."""
        for ano, mes in sorted({(a.ano, a.mes) for a in inc_escribir}):
            del_mes = [a for a in inc_escribir if (a.ano, a.mes) == (ano, mes)]
            hmoides = None
            if forzada:
                clave = (int(destino.ide), ano, mes)
                leidos[clave] = self._parte_del_periodo(destino, ano, mes)
                hmoides = [int(ps.ide) for ps in leidos[clave].del_periodo]
            ids = {a.id for a in del_mes}
            propias = [e for e in entradas if int(e.id) in ids]
            reconciliar(del_mes, propias, self._cli.incidencias_del_mes(
                sorted({int(a.recurso_ide) for a in del_mes}), ano, mes,
                hmoides=hmoides, ides=sorted({
                    int(i) for e in propias
                    for i in (e.hmores_ide_ini, e.hmores_ide_fin) if i})),
                est=int(self._st.est_parte_activo))

    # ------------------------------------------------------------- #
    def _crear_parte(self, p: ParteDestino, d: ObraEntrada,
                     desc: str) -> None:
        """Paso 9 (F-037 R11, D17): alta protegida y relectura del periodo.

        El alta no inserta si el código ya está ocupado en la empresa o si
        el periodo ya tiene un parte En registro (el que haya creado
        `partes` en ese instante). Tras el alta se relee: si hay uno En
        registro, se usa, sea el nuestro o no; si no, se pide otro código y
        se reintenta UNA vez. Si tampoco, falla antes de insertar líneas."""
        cod = p.cod
        for intento in range(2):
            self._cli.escribir(self._cli.stmts_crear_parte(
                obra=d, ano=p.ano, mes=p.mes, cod=cod, desc=desc))
            leido = self._parte_del_periodo(d, p.ano, p.mes)
            if leido.existe:
                p.existe, p.ide, p.cod = True, leido.ide, leido.cod
                p.estado, p.creado = leido.estado, leido.cod == cod
                logger.info(
                    "[registro] parte %s %s (ide=%s) obra=%s %s/%s",
                    "creado" if p.creado else "de otro servicio, se usa",
                    p.cod, p.ide, d.codigo, p.ano, p.mes)
                return
            if intento == 0:
                cod = self._cli.siguiente_cod_pt(p.ano, int(d.empresa))
        raise RuntimeError(
            f"no se pudo crear el parte {cod} de la obra {d.codigo} "
            f"{p.mes:02d}/{p.ano}: no hay ninguno En registro tras el alta")

    # ------------------------------------------------------------- #
    @staticmethod
    def _emparejar_ceros(libres: list[AccionLinea], existentes: list,
                         donde: dict, en_cerrado: set[int],
                         mias: set[str]) -> None:
        """Paso 7, F-051 (R2, R3): cada acción sin choque edita como mucho
        una línea al 0 % de su recurso (`linea_cero`), con su aviso y el
        de las que se quedan a 0. Sin confirmar (D2 = A)."""
        pares, sobran = emparejar_ceros(libres, existentes,
                                        en_cerrado=en_cerrado, mias=mias)
        for a in libres:
            ls = pares.get(a.registro_id)
            if ls is None:
                continue
            ps = donde[ls.ide]
            a.linea_cero = {
                "ide": ls.ide, "hmoide": int(ps.ide), "parte_cod": ps.cod,
                "horide": ls.horide, "hora_codigo": ls.hora_codigo,
                "paride": ls.paride, "can": ls.can,
                "fecha_int": ls.fecha_int, "synckey": ls.synckey}
            partida = (a.partida_cod if ls.paride == a.paride
                       else ls.paride)
            n = sobran[int(a.recurso_ide)]
            _sumar_aviso(a, AVISO_LINEA_CERO.format(
                ide=ls.ide, parte=ps.cod, hora=ls.hora_codigo,
                partida=partida),
                AVISO_QUEDAN_A_CERO.format(n=n) if n else None)

    # ------------------------------------------------------------- #
    def preflight(self, *, obra: ObraEntrada,
                  lineas: list[LineaEntrada],
                  incidencias: list[IncidenciaEntrada] | None = None,
                  ) -> Preflight:
        """Pasos 0-8, con el resumen de sus lecturas en el log (F-055 R1:
        obra, lecturas, segundos leyendo y totales), también si falla.
        `incidencias` (F-030): las de la obra; sin ellas, como siempre."""
        t0 = _ahora()
        with medir_lecturas() as m:
            try:
                return self._preflight(obra=obra, lineas=lineas,
                                       incidencias=list(incidencias or []))
            finally:
                logger.info(
                    "[registro] lecturas preflight obra=%s lecturas=%s "
                    "segundos_leyendo=%.2f segundos_totales=%.2f",
                    obra.codigo or obra.ide, m.n, m.segundos,
                    _ahora() - t0)

    # ------------------------------------------------------------- #
    def _preflight(self, *, obra: ObraEntrada, lineas: list[LineaEntrada],
                   incidencias: list[IncidenciaEntrada]) -> Preflight:
        # Paso 0: empresa y obra de origen (ARCHITECTURE.md#regla-empresa).
        # Las incidencias cuentan: una obra solo con ellas también va (R23).
        empresa = empresa_de_peticion([*lineas, *incidencias])
        if empresa is None:
            return self._todas_omitidas(obra, lineas, None, incidencias)
        origen = self._obra_origen(obra, empresa)
        if origen.empresa != empresa:
            motivo = MOTIVO_EMPRESA_OBRA.format(
                cod=origen.codigo, emp_obra=origen.empresa, emp_linea=empresa)
            # Se publica la obra de origen RESUELTA, con su empresa, no la
            # de entrada (F-024, R20). Sin empresa, arriba, no hay obra
            # resuelta y sigue saliendo la de entrada.
            return self._todas_omitidas(origen, lineas, motivo,
                                        incidencias)
        destino_normal, forzada = self._obra_destino(origen, empresa)

        # Paso 1b: destino de postventa (solo si hace falta).
        # Sin líneas de postventa no se lee ni se publica catálogo (R8).
        destino_pv: Optional[ObraEntrada] = None
        partida_pv: Optional[dict] = None
        motivo_pv: Optional[str] = None
        nodos_pv: dict = {}
        if any(l.es_postventa for l in lineas):
            destino_pv, partida_pv, motivo_pv, nodos_pv = \
                self._destino_postventa(obra, forzada, destino_normal,
                                        empresa)

        # Pasos 2-4: horas de los recursos dados + reglas.
        # Las horas, en UNA lectura con los recursos de las incidencias.
        horas = self._horas_de_lineas([*lineas, *incidencias])
        reglas = ReglasPorcentajes(
            horas, postventa_registrar=self._st.postventa_registrar,
            partida_postventa=partida_pv, motivo_postventa=motivo_pv)
        acciones: list[AccionLinea] = [reglas.decidir(l) for l in lineas]
        # F-030 (R24, R26): las dos líneas de cada incidencia.
        acciones_inc: list[AccionIncidencia] = [
            a for i in incidencias for a in decidir_incidencia(i, horas)]
        inc_escribir = [a for a in acciones_inc if a.accion == "escribir"]

        # Partida de imputación por línea (ARCHITECTURE.md#regla-partida): la
        # elegida (override) manda si es hoja activa del presupuesto de la
        # obra ORIGEN; si no viene, la NORMAL lleva la propuesta GUARDADA si
        # vale y, si no, es PENDIENTE y lleva la PROPUESTA (parte anterior,
        # casamiento por rol y nombre o último parte, R38); la POSTVENTA ya
        # trae la suya de la obra de postventa (`POSTVENTA_OBRA_COD`).
        # F-055 (R3): elegidas y guardadas se validan por `ide` en UNA
        # lectura; presupuesto e historial, solo si hay pendientes (R7).
        nodos_origen = None
        catalogo_var = None
        historial = None
        por_id = {l.registro_id: l for l in lineas}
        normales = [
            l for a in acciones
            if a.accion == "escribir" and a.destino != "postventa"
            for l in [por_id[a.registro_id]] if l.var_paride is None]
        validas = self._validas(normales, inc_escribir)

        def vale(paride) -> bool:
            v = validas.get(int(paride or 0))
            return v is not None and v.vale_en(origen.ide)

        por_proponer = [l for l in normales
                        if not l.paride and not vale(l.propuesta_paride)]
        for a in inc_escribir:
            # R25: la partida de la línea de % que vale por `ide` o 0, sin
            # aviso ni confirmación.
            if not vale(a.paride):
                a.paride = 0
        for a in acciones:
            if a.accion != "escribir":
                continue
            linea = por_id[a.registro_id]
            if linea.var_paride is not None:
                # Entrada VAR (ARCHITECTURE.md#regla-var): su partida o nada,
                # sin casado ni override. El catálogo, una vez por petición.
                if a.destino == "postventa":
                    a.accion = "omitir"
                    a.motivo = MOTIVO_VAR_POSTVENTA.format(
                        paride=linea.var_paride)
                    continue
                if catalogo_var is None:
                    catalogo_var = cargar_catalogo_var(self._cli, self._st,
                                                       empresa)
                nodo, motivo = partida_var_de(
                    catalogo_var, origen.ide, int(linea.var_paride),
                    int(self._st.var_partida_desde))
                if nodo is None:
                    a.accion, a.motivo = "omitir", motivo
                    continue
                a.paride, a.partida_cod = int(nodo.ide), nodo.cod
                a.partida_res, a.partida_metodo = nodo.res, "var"
                continue
            if linea.paride:
                # El override del front manda… salvo que apunte fuera del
                # universo válido de la postventa (un capítulo, una partida
                # de baja). Ahí no se escribe: ver ARCHITECTURE #regla-p5.
                if a.destino == "postventa":
                    if not self._es_hoja_activa_pv(nodos_pv, linea.paride):
                        a.accion = "omitir"
                        a.motivo = MOTIVO_PARTIDA_PV_NO_HOJA.format(
                            paride=int(linea.paride))
                        continue
                    a.partida_res = nodos_pv[int(linea.paride)].res
                elif not vale(linea.paride):
                    # R20 de F-050 (D9) y F-055 R5: una elegida que ya no
                    # vale no se escribe: se omite y se elige otra.
                    a.accion = "omitir"
                    a.motivo = MOTIVO_PARTIDA_NO_HOJA.format(
                        cod=linea.partida_cod or int(linea.paride),
                        obra=origen.codigo)
                    continue
                else:
                    a.partida_res = validas[int(linea.paride)].res
                a.paride = int(linea.paride)
                a.partida_cod = linea.partida_cod
                a.partida_metodo = "manual"
                continue
            if a.destino == "postventa":
                a.partida_metodo = "postventa"
                a.partida_res = partida_pv["res"]
                continue
            if vale(linea.propuesta_paride):
                # F-055 R8: la propuesta guardada que vale se escribe con lo
                # que enseña el cuadrante (design §10).
                a.paride = int(linea.propuesta_paride)
                a.partida_cod, a.partida_res = (linea.propuesta_cod,
                                                linea.propuesta_res)
                a.partida_metodo = linea.propuesta_metodo
                a.partida_origen = linea.propuesta_origen
                continue
            if nodos_origen is None:
                # La obra de origen ya está resuelta en el paso 0: no se
                # vuelve a buscar (R14 de F-022).
                nodos_origen = construir_catalogo(
                    self._cli.capitulos_de_obra(int(origen.ide)))
            if historial is None:
                historial = self._historial(por_proponer)
            p = proponer_partida(nodos_origen, historial, a.recurso_ide,
                                 int(origen.ide), linea.categoria,
                                 linea.nombre)
            if p is None:
                # Hasta F-013 esto se escribía igual, con un aviso que nadie
                # tenía que atender. Ahora el paso 6 bis lo convierte en un
                # conflicto: ver ARCHITECTURE.md#regla-sin-partida.
                a.paride = 0
                a.aviso = AVISO_SIN_PARTIDA
            else:
                a.paride, a.partida_cod, a.partida_res = p.paride, p.cod, p.res
                a.partida_metodo, a.partida_origen = p.metodo, p.origen

        escribir = [a for a in acciones if a.accion == "escribir"]

        def obra_de(a: AccionLinea) -> ObraEntrada:
            return destino_pv if a.destino == "postventa" else destino_normal

        # Paso 4 bis: cuenta analítica (ARCHITECTURE.md#regla-analitica),
        # con las incidencias (van a la obra normal) en las mismas lecturas.
        if escribir or inc_escribir:
            self._cuentas([*escribir, *inc_escribir], horas, obra_de)

        # R27 y anexo R30 (F-030): una línea de incidencia que ya está en
        # un parte del mes no se escribe: la nuestra con otra `fec` se
        # edita (R41) y la de otro se omite. UNA lectura por mes (R33) y
        # solo si alguna se escribiría; en pruebas, solo los partes de la
        # obra de pruebas. ANTES del paso 5 (obs. 7): solo las que siguen
        # `escribir` piden parte; `editar` va en el de su línea.
        leidos: dict[tuple[int, int, int], ParteDestino] = {}
        if inc_escribir:
            self._reconciliar_incidencias(inc_escribir, incidencias,
                                          destino_normal, forzada, leidos)
        inc_escribir = [a for a in inc_escribir if a.accion == "escribir"]

        # Paso 5: parte por DESTINO + periodo, entre TODOS los del periodo
        # (F-037 R9-R11, R15; ARCHITECTURE.md#regla-analitica).
        partes: dict[tuple[int, int, int], ParteDestino] = {}
        for a in escribir:
            d = obra_de(a)
            clave = (int(d.ide), a.ano, a.mes)
            if clave not in partes:
                partes[clave] = self._parte_nuevo_o_del_periodo(
                    d, a.ano, a.mes, leidos.get(clave))
            _sumar_aviso(a, partes[clave].aviso)
        for a in inc_escribir:
            clave = (int(destino_normal.ide), a.ano, a.mes)
            if clave not in partes:
                partes[clave] = self._parte_nuevo_o_del_periodo(
                    destino_normal, a.ano, a.mes, leidos.get(clave))
            a.parte_cod = partes[clave].cod

        # Paso 6: idempotencia (F-051 R15): la fila de su `hmores_ide` si es
        # de su recurso, es `M*` (T18: un `ide` reutilizado puede caer en
        # una `H*`/`C*` de `partes`) y no es nuestra de otra asignación; si
        # no, la de su `synckey`, como siempre. Las dos en UNA lectura.
        por_sk, por_ide = self._cli.lineas_registradas(
            [synckey_de(a.registro_id) for a in escribir],
            [por_id[a.registro_id].hmores_ide for a in escribir])
        for a in escribir:
            propia = synckey_de(a.registro_id)
            hit = por_ide.get(int(por_id[a.registro_id].hmores_ide or 0))
            if (hit is None or hit.reside != a.recurso_ide
                    or not es_linea_mensual(hit)
                    or es_nuestra_de_otra(hit.synckey, propia)):
                hit = por_sk.get(propia)
            if hit is not None:
                a.accion = "ya_registrado"
                a.hmores_ide = hit.ide
                a.motivo = (f"ya registrada en Sigrid (línea {hit.ide}); "
                            f"no se duplica")

        # Paso 6 bis: líneas SIN PARTIDA (ver ARCHITECTURE
        # `#regla-sin-partida`). Se emiten ANTES que los pisados y las
        # sobrecargas por la misma razón por la que el pisado va antes que
        # la sobrecarga: el aviso de después DA POR HECHO el de antes. La
        # identidad del pisado usa el `paride` a 0 de esta línea y la suma
        # de la sobrecarga incluye su `can`, así que la decisión que los
        # sostiene se lee primero.
        #
        # Y NO va dentro del bucle de partes de abajo: ese se salta los
        # partes que aún no existen porque contra un parte nuevo no puede
        # haber pisado. Aquí eso no vale: este aviso no habla de lo que ya
        # hay en Sigrid, sino de dónde se imputa lo que vamos a escribir.
        conflictos: list[Conflicto] = []
        for a in acciones:
            if not sin_partida(a):
                continue
            # Sin `.get` a propósito: el paso 5 dejó una entrada por cada
            # acción `escribir`, y de aquí a allí ninguna acción PASA a
            # serlo (el paso 6 solo las saca). Un `.get` con rama de
            # respaldo sería una guarda que ningún test puede ejercitar, y
            # que por tanto nadie mantiene. Lo mismo con `recurso_ide`: P1
            # omite toda línea que no lo tenga.
            parte_a = partes[(int(obra_de(a).ide), a.ano, a.mes)]
            conflictos.append(Conflicto(
                clave=clave_sin_partida(a),
                recurso_ide=int(a.recurso_ide), nombre=a.nombre,
                ano=a.ano, mes=a.mes, parte_cod=parte_a.cod,
                horide=a.hora_ide, hora_codigo=a.hora_codigo,
                lineas=[],          # no sustituye a nadie: no borra nada
                nuevas=[_nueva(a)], registros=[a.registro_id],
                motivo="sin_partida"))
            logger.warning(
                "[registro] sin partida recurso=%s registro=%s %s/%s: "
                "no se escribe sin confirmar", a.recurso_ide, a.registro_id,
                a.ano, a.mes)

        # Paso 7: conflictos (ver ARCHITECTURE `#regla-conflicto`) contra
        # las líneas de TODOS los partes del periodo, aunque el elegido sea
        # nuevo (F-037 R13): un choque con un parte CERRADO omite la acción
        # (en un cerrado no se escribe ni se borra) y prevalece; con uno En
        # registro es el conflicto de siempre, con el parte donde vive.
        pendientes = [a for a in acciones if a.accion == "escribir"]
        en_cerrado: set[int] = set()
        for clave_p, parte in sorted(partes.items()):
            grupo = [a for a in pendientes
                     if (int(obra_de(a).ide), a.ano, a.mes) == clave_p]
            if not grupo or not parte.del_periodo:
                continue            # sin partes en el periodo: nada choca
            existentes = []
            donde = {}
            for ps in parte.del_periodo:
                for ls in self._cli.lineas_del_parte(
                        int(ps.ide), [a.recurso_ide for a in grupo]):
                    existentes.append(ls)
                    donde[ls.ide] = ps
            mias = {synckey_de(a.registro_id) for a in grupo}
            # F-051 (R1, R3): las líneas al 0 % que se pueden editar, por
            # recurso. No son choque, no salen en ningún contexto y no
            # cuentan en la capacidad (ARCHITECTURE.md#regla-cero).
            lineas_cerradas = {ls.ide for ls in existentes
                               if donde[ls.ide].cod in parte.cerrados}
            pisables: dict[int, set[int]] = {}
            for a in grupo:
                pisables.setdefault(int(a.recurso_ide), set()).update(
                    ls.ide for ls in pisables_al_cero(
                        existentes, a, en_cerrado=lineas_cerradas,
                        mias=mias))
            por_clave: dict[str, Conflicto] = {}
            for a in grupo:
                k = clave_conflicto(a)
                suyas = pisables[int(a.recurso_ide)]
                choques = [ls for ls in existentes
                           if criterio_choque(ls, a, mias=mias)
                           and ls.ide not in suyas]
                if not choques:
                    continue        # nada previo con esa identidad
                cerrado = next((donde[ls.ide] for ls in choques
                                if donde[ls.ide].cod in parte.cerrados),
                               None)
                if cerrado is not None:
                    a.accion = "omitir"
                    a.motivo = motivo_choque(
                        cerrado.cod, self._nombre_estado(cerrado.est))
                    a.caa_ide, a.caa_cod, a.caa_motivo = 0, None, None
                    a.caa_aviso, a.caa_origen, a.caa_nota = None, None, None
                    en_cerrado.add(a.registro_id)
                    continue
                c = por_clave.get(k)
                if c is None:
                    contexto = [
                        ls for ls in existentes
                        if ls.reside == a.recurso_ide and ls not in choques
                        and es_linea_mensual(ls) and ls.ide not in suyas
                    ]
                    c = Conflicto(
                        clave=k, recurso_ide=int(a.recurso_ide or 0),
                        ano=parte.ano, mes=parte.mes,
                        parte_cod=donde[choques[0].ide].cod,
                        nombre=a.nombre, horide=a.hora_ide,
                        hora_codigo=a.hora_codigo,
                        lineas=choques, contexto=contexto)
                    por_clave[k] = c
                c.registros.append(a.registro_id)
                c.nuevas.append(_nueva(a))
            for c in por_clave.values():
                # F-051 (R4, R5): confirmado, edita (por `registro_id`) los
                # de menor `ide` y pone a 0 los que sobran; nunca borra.
                edita, c.a_cero_ides = repartir_choques(c.registros, c.lineas)
                c.edita_ide = min(edita.values())
            conflictos.extend(por_clave.values())
            self._emparejar_ceros(
                [a for a in grupo if a.accion == "escribir"
                 and not any(a.registro_id in c.registros
                             for c in por_clave.values())],
                existentes, donde, lineas_cerradas, mias)

            # Paso 7 bis: capacidad (ver ARCHITECTURE `#regla-capacidad`).
            # Va DESPUÉS de los pisados del mismo parte, y no antes: su
            # cifra ya presupone que todos ellos se confirman. Suma las
            # líneas de todos los partes del periodo y solo las acciones que
            # siguen siendo `escribir`.
            grupo = [a for a in grupo if a.accion == "escribir"]
            pisadas: dict[int, set[int]] = {}
            for c in por_clave.values():
                pisadas.setdefault(c.recurso_ide, set()).update(
                    ls.ide for ls in c.lineas)
            for recurso, ides in pisables.items():
                pisadas.setdefault(recurso, set()).update(ides)
            # Sin `or 0` a propósito: `grupo` solo tiene acciones «escribir»,
            # y P1 omite toda línea sin recurso, así que aquí `recurso_ide`
            # no puede ser nulo. Normalizarlo otra vez sería una guarda que
            # ningún test puede ejercitar, y que por tanto nadie mantiene.
            for recurso in sorted({int(a.recurso_ide) for a in grupo}):
                suyas = [a for a in grupo if int(a.recurso_ide) == recurso]
                cap = evaluar_capacidad(
                    [ls for ls in existentes if int(ls.reside) == recurso],
                    suyas, mias=mias, pisadas=pisadas.get(recurso, set()))
                if not cap.sobrecarga:
                    continue
                cabeza = suyas[0]
                conflictos.append(Conflicto(
                    clave=clave_sobrecarga(cabeza), recurso_ide=recurso,
                    ano=parte.ano, mes=parte.mes, parte_cod=parte.cod,
                    nombre=cabeza.nombre, horide=cabeza.hora_ide,
                    hora_codigo=cabeza.hora_codigo,
                    lineas=[],          # una sobrecarga NO borra nada
                    contexto=list(cap.contadas),
                    nuevas=[_nueva(a) for a in suyas],
                    registros=[a.registro_id for a in suyas],
                    motivo="sobrecarga",
                    suma_existente=round(cap.existente, 4),
                    suma_total=round(cap.total, 4),
                    exceso=round(cap.exceso, 4)))
                logger.warning(
                    "[registro] sobrecarga recurso=%s parte=%s existente=%s "
                    "nueva=%s total=%s", recurso, parte.cod,
                    cap.existente, cap.nueva, cap.total)

        # Una línea omitida por un parte cerrado ya no se escribe: su aviso
        # de «sin partida» del paso 6 bis no tiene nada que confirmar.
        conflictos = [c for c in conflictos
                      if not (c.motivo == "sin_partida"
                              and set(c.registros) <= en_cerrado)]

        pf = Preflight(
            obra_destino=destino_normal, obra_origen=obra,
            forzada_pruebas=forzada,
            partes=[partes[k] for k in sorted(partes)], acciones=acciones,
            conflictos=conflictos, incidencias=acciones_inc)
        if acciones_inc:
            logger.info(
                "[registro] incidencias obra=%s lineas=%s escribir=%s",
                destino_normal.codigo, len(acciones_inc),
                sum(a.accion == "escribir" for a in acciones_inc))
        logger.info(
            "[registro] preflight obra=%s partes=%s escribir=%s omitir=%s "
            "ya=%s conflictos=%s", destino_normal.codigo, len(pf.partes),
            pf.n_escribir, pf.n_omitir, pf.n_ya, len(conflictos))
        # El destino de postventa se adjunta para trazabilidad de la API.
        setattr(pf, "obra_postventa", destino_pv)
        # OJO con el nombre: lo que viaja es una PARTIDA, no un capítulo
        # (ARCHITECTURE.md#regla-p5). El atributo conserva el nombre viejo
        # porque es contrato HTTP y el front lo lee como `capitulo_postventa`
        # en la respuesta de /api/registro/preflight. Renombrarlo obliga a
        # tocar los tres servicios a la vez: es una feature aparte.
        setattr(pf, "capitulo_postventa", partida_pv)

        def _cat(nodos):
            # F-050 (R10): en orden natural del código; sin `mayor`, que solo
            # publica `/api/partidas/propuesta` (el front ya no lee estos).
            # F-055 (R10): solo si se leyó el presupuesto (hay pendientes);
            # si no, `[]` sin leer (sale la lectura forzada de F-049 d).
            return [{k: p[k] for k in ("ide", "cod", "res", "categoria")}
                    for p in catalogo(nodos or {})]

        setattr(pf, "partidas_obra", _cat(nodos_origen))
        setattr(pf, "partidas_postventa", _cat(nodos_pv))
        return pf

    # ------------------------------------------------------------- #
    def proponer(self, *, empresa: int, obra: ObraEntrada, ano: int,
                 mes: int, lineas: list[dict]) -> dict:
        """F-050 (R8, R11): catálogo y propuesta de cada línea, SOLO
        LECTURA, con la misma `proponer_partida` que el preflight (R9).

        `lineas`: `{clave, recurso_ide, nombre, categoria, es_postventa}`.
        La obra de otra empresa devuelve `ok` falso con el motivo (422 en
        la API); un fallo de lectura sube tal cual (502)."""
        origen = self._obra_origen(obra, empresa)
        if origen.empresa != empresa:
            return {"ok": False, "error": MOTIVO_EMPRESA_OBRA.format(
                cod=origen.codigo, emp_obra=origen.empresa,
                emp_linea=empresa)}
        nodos = construir_catalogo(
            self._cli.capitulos_de_obra(int(origen.ide)))
        normales = [l for l in lineas if not l["es_postventa"]]
        historial = []
        if normales:
            desde, hasta = ventana(ano, mes, self._st.propuesta_meses_atras)
            historial = self._cli.historial_partidas(
                sorted({l["recurso_ide"] for l in normales
                        if l["recurso_ide"]}), desde, hasta)
        nodos_pv: dict = {}
        partida_pv = None
        if len(normales) < len(lineas):
            # Postventa (R11): su propuesta es el casado de `#regla-p5`.
            catalogo_pv = cargar_catalogo_postventa(self._cli, self._st,
                                                    empresa)
            partida_pv, _ = casar_postventa(catalogo_pv, origen.codigo,
                                            origen.nombre)
            nodos_pv = catalogo_pv.nodos
        propuestas: dict = {}
        mayores: dict = {}
        for l in lineas:
            if l["es_postventa"]:
                p = (Propuesta(partida_pv["ide"], partida_pv["cod"],
                               partida_pv["res"], "postventa")
                     if partida_pv else None)
                de = nodos_pv
            else:
                p = proponer_partida(nodos, historial, l["recurso_ide"],
                                     int(origen.ide), l["categoria"],
                                     l["nombre"])
                de = nodos
            propuestas[l["clave"]] = asdict(p) if p else None
            mayores[l["clave"]] = mayor_inicial(p, de, l["categoria"])
        return {"ok": True, "partidas_obra": catalogo(nodos),
                "partidas_postventa": catalogo(nodos_pv),
                "propuestas": propuestas, "mayor_inicial": mayores}

    # ------------------------------------------------------------- #
    def ejecutar(self, *, obra: ObraEntrada, lineas: list[LineaEntrada],
                 pisar_claves: set[str] | None = None,
                 usuario: str | None = None,
                 incidencias: list[IncidenciaEntrada] | None = None,
                 ) -> ResultadoRegistro:
        """Pasos 0-10. Las incidencias (F-030) se escriben tras las líneas,
        en el mismo lote de sentencias; ningún conflicto las retiene (R28)
        y no salen en `escritas` (que es de las asignaciones), sino en
        `incidencias`, con el `hmores_ide` de cada línea escrita."""
        pisar = {str(k) for k in (pisar_claves or set())}
        # Sin incidencias, la llamada de siempre (R2): ni un argumento más.
        pf = self.preflight(obra=obra, lineas=lineas, **(
            {"incidencias": incidencias} if incidencias else {}))
        destino_normal = pf.obra_destino
        destino_pv = getattr(pf, "obra_postventa", None)

        def obra_de(a: AccionLinea) -> ObraEntrada:
            return destino_pv if a.destino == "postventa" else destino_normal

        res = ResultadoRegistro(
            ok=True, obra_destino=destino_normal,
            forzada_pruebas=pf.forzada_pruebas, partes=pf.partes,
            omitidas=[{"registro_id": a.registro_id, "motivo": a.motivo}
                      for a in pf.acciones if a.accion == "omitir"],
            ya_registradas=[a.registro_id for a in pf.acciones
                            if a.accion == "ya_registrado"],
            ya_registradas_ide={a.registro_id: a.hmores_ide
                                for a in pf.acciones
                                if a.accion == "ya_registrado"},
            incidencias=pf.incidencias,
        )
        inc_escribir = [a for a in pf.incidencias if a.accion == "escribir"]

        bloqueadas: set[int] = set()
        # Registros ya listados en `omitidas` por un aviso anterior. Empieza
        # vacío y no sembrado con las omisiones de las reglas: una acción
        # `omitir` no llega a ser conflicto (los conflictos solo agrupan
        # acciones `escribir`), así que los dos conjuntos son disjuntos por
        # construcción y sembrarlo sería una guarda que ningún test podría
        # ejercitar.
        omitidas_ya: set[int] = set()
        for c in pf.conflictos:
            if c.clave in pisar:
                res.pisadas.append(c.clave)
                continue
            res.pendientes_confirmacion.append(c)
            bloqueadas.update(c.registros)
            # Un conflicto sin confirmar deja rastro en `omitidas`, salvo el
            # pisado: un pisado sin confirmar es un paso normal del flujo
            # («repite y marca pisar»), mientras que una sobrecarga (R28) o
            # una línea sin partida (F-013) son anomalías que tienen que
            # verse aunque nadie vuelva a ejecutar. `dedicacion-api` solo
            # mira este campo para escribir `asignacion.sigrid_estado`.
            #
            # La condición se escribe por lo que se EXCLUYE y no por lo que
            # se incluye: así un motivo nuevo deja rastro por defecto, que
            # es el lado seguro del error.
            if c.motivo == "pisado":
                continue
            motivo = (
                MOTIVO_SOBRECARGA.format(
                    total=c.suma_total, existente=c.suma_existente,
                    n=len(c.contexto), nueva=c.nueva_can)
                if c.motivo == "sobrecarga" else MOTIVO_SIN_PARTIDA)
            # Una misma línea puede estar retenida por MÁS DE UN aviso (sin
            # partida y sobrecarga a la vez). En `omitidas` sale UNA vez,
            # con el motivo del primero que la retuvo, que por el orden en
            # que se emiten es el que los demás presuponen. `dedicacion-api`
            # hace un UPDATE por entrada sobre la MISMA asignación: dos
            # entradas serían dos escrituras de las que solo sobrevive la
            # última, y un recuento de omitidas inflado en el front. Los
            # avisos completos siguen viéndose donde se decide, que es
            # `pendientes_confirmacion`.
            for r in c.registros:
                if r in omitidas_ya:
                    continue
                omitidas_ya.add(r)
                res.omitidas.append({"registro_id": r, "motivo": motivo})

        a_escribir = [a for a in pf.acciones
                      if a.accion == "escribir"
                      and a.registro_id not in bloqueadas]
        if not a_escribir and not inc_escribir:
            logger.info("[registro] nada que escribir (bloqueadas=%s)",
                        len(bloqueadas))
            return res

        # Paso 9 bis (F-051 R4, R5, R12): qué edita cada acción y qué se
        # pone a 0, comprobado contra Sigrid justo antes de escribir. Va
        # ANTES del alta de partes: la acción que edita no necesita parte
        # nuevo, y la que cae no tiene que dejar uno vacío.
        edita, ceros, cambiadas = self._planear_ediciones(
            pf, a_escribir, pisar)
        for a in a_escribir:
            if a.registro_id in cambiadas:
                res.omitidas.append({
                    "registro_id": a.registro_id,
                    "motivo": MOTIVO_LINEA_CAMBIADA.format(
                        ide=cambiadas[a.registro_id])})
        a_escribir = [a for a in a_escribir
                      if a.registro_id not in cambiadas]
        if not a_escribir and not inc_escribir:
            logger.info("[registro] nada que escribir (cambiadas=%s)",
                        len(cambiadas))
            return res
        a_insertar = [a for a in a_escribir if a.registro_id not in edita]

        # Paso 9: crear los partes que falten (por destino), solo para lo
        # que se inserta.
        por_parte = {(int(o.ide), p.ano, p.mes): p
                     for p in pf.partes
                     for o in [destino_normal, destino_pv] if o
                     and p.obra_cod == o.codigo}
        # (clave robusta: si ambos destinos coinciden —modo pruebas— es la
        #  misma entrada)
        for a in sorted([*a_insertar, *inc_escribir],
                        key=lambda x: (x.ano, x.mes)):
            d = obra_de(a)
            clave = (int(d.ide), a.ano, a.mes)
            p = por_parte.get(clave)
            if p is None or (p.existe and p.ide):
                continue
            marca = (f" ({self._st.marca_pruebas})" if pf.forzada_pruebas
                     else "")
            # D13: `Parte <obra>`, como `partes` y Administración: el
            # complementario es «un parte más» del periodo.
            self._crear_parte(p, d, f"Parte {d.nombre or d.codigo}{marca}")

        # Paso 10: editar en su sitio, poner a 0 y, lo que no edita nada,
        # insertar. Ningún DELETE (F-051 R6, ARCHITECTURE.md#regla-cero).
        statements: list[dict] = []
        tex = self._st.marca_pruebas if pf.forzada_pruebas else None
        orden = sorted(a_escribir, key=lambda x: (x.ano, x.mes,
                                                  x.registro_id))
        for a in orden:
            ls = edita.get(a.registro_id)
            if ls is None:
                continue
            synckey = synckey_tras_editar(ls.synckey,
                                          synckey_de(a.registro_id))
            despues = {
                # `can` y `tot` ya vienen redondeados de las reglas, como
                # los de una inserción (`stmt_editar_linea` los recalcula
                # igual).
                "can": float(a.can), "pre": float(a.pre),
                "tot": float(a.tot),
                "horide": int(a.hora_ide), "hora_codigo": a.hora_codigo,
                "paride": int(a.paride or 0), "caaide": int(a.caa_ide or 0),
                "fecha_int": a.fecha_int, "synckey": synckey,
                "tex": ls.tex if tex is None else tex}
            statements.append(self._cli.stmt_editar_linea(
                ide=ls.ide, reside=int(ls.reside), can_leido=ls.can,
                synckey_leida=ls.synckey, horide=int(a.hora_ide),
                can=float(a.can), pre=float(a.pre),
                paride=int(a.paride or 0), caaide=int(a.caa_ide or 0),
                fecha_int=a.fecha_int, synckey=synckey, tex=tex))
            res.editadas.append(_traza("edita", a.registro_id, ls, despues))
            res.escritas.append(self._escrita(
                a, obra_de(a), ls.hmoide, ls.parte_cod, editada=True,
                hmores_ide=ls.ide))
        for registro_id, ls in ceros:
            statements.append(self._cli.stmt_poner_a_cero(
                ide=ls.ide, reside=int(ls.reside), can_leido=ls.can,
                synckey_leida=ls.synckey))
            res.a_cero.append(_traza("pone a 0", registro_id, ls, {
                **_fila(ls), "can": 0.0, "tot": 0.0}))

        pos_por_parte: dict[int, int] = {}
        for a in orden:
            if a.registro_id in edita:
                continue
            d = obra_de(a)
            p = por_parte[(int(d.ide), a.ano, a.mes)]
            hmoide = int(p.ide)
            if hmoide not in pos_por_parte:
                pos_por_parte[hmoide] = self._cli.max_pos(hmoide)
            pos_por_parte[hmoide] += int(self._st.paso_pos)
            statements.append(self._cli.stmt_insert_linea(
                hmoide=hmoide, obra=d, reside=int(a.recurso_ide),
                pos=pos_por_parte[hmoide], fecha_int=a.fecha_int,
                horide=int(a.hora_ide), can=float(a.can), pre=float(a.pre),
                ano=a.ano, mes=a.mes, synckey=synckey_de(a.registro_id),
                tex=tex, paride=int(a.paride or 0),
                caaide=int(a.caa_ide or 0)))
            res.escritas.append(self._escrita(a, d, hmoide, p.cod,
                                              editada=False))

        # F-030 (R24): las dos líneas de cada incidencia, `can = 0` (así
        # `tot = 0`) y su propia `synckey`.
        for a in sorted(inc_escribir, key=lambda x: (x.ano, x.mes, x.id)):
            d = destino_normal
            p = por_parte[(int(d.ide), a.ano, a.mes)]
            hmoide = int(p.ide)
            if hmoide not in pos_por_parte:
                pos_por_parte[hmoide] = self._cli.max_pos(hmoide)
            pos_por_parte[hmoide] += int(self._st.paso_pos)
            a.parte_cod = p.cod
            statements.append(self._cli.stmt_insert_linea(
                hmoide=hmoide, obra=d, reside=int(a.recurso_ide),
                pos=pos_por_parte[hmoide], fecha_int=a.fecha_int,
                horide=int(a.hora_ide), can=0.0, pre=float(a.pre),
                ano=a.ano, mes=a.mes, synckey=synckey_incidencia(a.id, a.rol),
                tex=tex, paride=int(a.paride or 0),
                caaide=int(a.caa_ide or 0)))

        afectadas = self._cli.escribir(statements)
        logger.info("[registro] escritas=%s editadas=%s a_cero=%s "
                    "borradas=%s filas=%s usuario=%s ts=%s",
                    len(res.escritas), len(res.editadas), len(res.a_cero),
                    res.borradas, afectadas, usuario,
                    datetime.now(timezone.utc).isoformat())
        self._comprobar_escrito(res, inc_escribir)
        return res

    # ------------------------------------------------------------- #
    def _planear_ediciones(self, pf: Preflight, a_escribir: list,
                           pisar: set[str]) -> tuple[dict, list, dict]:
        """Paso 9 bis, F-051 (design §6.4, 1-2): `({registro_id: línea a
        editar}, [(registro_id, línea a poner a 0)], {registro_id: ide que
        ha cambiado})`, con las líneas tal y como están AHORA en Sigrid
        (una lectura, R12). Si la línea al 0 % ya no es pisable, cae su
        acción; si un choque ya no lo es, cae el pisado entero."""
        escribibles = {a.registro_id: a for a in a_escribir}
        mias = {synckey_de(a.registro_id) for a in pf.acciones}
        # (qué, ide, registro_id, acción de referencia, criterio, caen)
        piezas: list[tuple] = [
            ("edita", int(a.linea_cero["ide"]), a.registro_id, a, "cero",
             (a.registro_id,))
            for a in a_escribir if a.linea_cero]
        # Las líneas al 0 % nunca son choque (paso 7), así que solo los
        # pisados pueden compartir línea: se reparte una vez.
        usadas: set[int] = set()
        for c in pf.conflictos:
            regs = sorted(r for r in c.registros if r in escribibles)
            # R32 de hoy: un pisado confirmado solo toca algo si al menos
            # uno de sus registros llega a escribirse.
            if c.clave not in pisar or not regs:
                continue
            libres = [ls for ls in c.lineas if ls.ide not in usadas]
            usadas.update(ls.ide for ls in libres)
            por_reg, a_cero = repartir_choques(regs, libres)
            piezas += [("edita", ide, r, escribibles[r], "choque",
                        tuple(regs)) for r, ide in por_reg.items()]
            piezas += [("a_cero", ide, regs[0], escribibles[regs[0]],
                        "choque", tuple(regs)) for ide in a_cero]
        if not piezas:
            return {}, [], {}
        leidas = self._cli.lineas_para_editar([pz[1] for pz in piezas])
        cambiadas: dict[int, int] = {}
        for _, ide, _, a, criterio, caen in piezas:
            if not self._sigue_valiendo(leidas.get(ide), a, criterio, mias):
                for r in caen:
                    cambiadas.setdefault(r, ide)
        edita = {r: leidas[ide] for que, ide, r, *_ in piezas
                 if que == "edita" and r not in cambiadas}
        ceros = [(r, leidas[ide]) for que, ide, r, *_ in piezas
                 if que == "a_cero" and r not in cambiadas]
        return edita, ceros, cambiadas

    def _sigue_valiendo(self, ls, a: AccionLinea, criterio: str,
                        mias: set[str]) -> bool:
        """R12: la línea sigue existiendo, es `M*`, sin enlaces, en un
        parte En registro y, según a qué iba, al 0 % y pisable por la
        acción (R1) o con la misma identidad que ella (choque)."""
        if (ls is None or ls.enlazada or not es_linea_mensual(ls)
                or ls.parte_est != int(self._st.est_parte_activo)):
            return False
        if criterio == "cero":
            return bool(pisables_al_cero([ls], a, en_cerrado=set(),
                                         mias=mias))
        return criterio_choque(ls, a, mias=mias)

    @staticmethod
    def _escrita(a: AccionLinea, d: ObraEntrada, hmoide, parte_cod,
                 *, editada: bool, hmores_ide: int | None = None) -> dict:
        e = {"registro_id": a.registro_id, "hmoide": hmoide,
             "parte_cod": parte_cod, "obra_cod": d.codigo,
             "destino": a.destino, "hora_codigo": a.hora_codigo,
             "partida_cod": a.partida_cod, "caa_cod": a.caa_cod,
             "can": a.can, "pre": a.pre, "tot": a.tot, "editada": editada}
        if hmores_ide is not None:
            e["hmores_ide"] = hmores_ide
        return e

    def _comprobar_escrito(self, res: ResultadoRegistro,
                           inc_escritas: list[AccionIncidencia]) -> None:
        """Paso 10, relectura (R13, R16): el `hmores_ide` de cada insertada
        por su `synckey`; una editada que no tiene lo escrito (la guarda no
        la cambió) sale de `escritas` y va a `omitidas`; una puesta a 0 que
        no quedó a 0, al log. UNA lectura, la de siempre, que también trae
        el `hmores_ide` de las líneas de incidencia escritas (F-030)."""
        por_sk, por_ide = self._cli.lineas_registradas(
            [synckey_de(e["registro_id"]) for e in res.escritas]
            + [synckey_incidencia(a.id, a.rol) for a in inc_escritas],
            [t["ide"] for t in res.editadas + res.a_cero])
        for a in inc_escritas:
            hit = por_sk.get(synckey_incidencia(a.id, a.rol))
            if hit is not None:
                a.hmores_ide = hit.ide
        trazas = {t["registro_id"]: t for t in res.editadas}
        for e in list(res.escritas):
            if not e["editada"]:
                hit = por_sk.get(synckey_de(e["registro_id"]))
                if hit is not None:
                    e["hmores_ide"] = hit.ide
                continue
            t = trazas[e["registro_id"]]
            hit = por_ide.get(t["ide"])
            if hit is None or abs(float(hit.can or 0.0)
                                  - t["despues"]["can"]) >= 0.000001 \
                    or (hit.synckey or "").strip() != t["despues"]["synckey"]:
                logger.warning("[registro] la guarda no dejo editar la "
                               "linea %s (registro %s)", t["ide"],
                               e["registro_id"])
                res.escritas.remove(e)
                res.editadas.remove(t)
                res.omitidas.append({
                    "registro_id": e["registro_id"],
                    "motivo": MOTIVO_LINEA_CAMBIADA.format(ide=t["ide"])})
        for t in list(res.a_cero):
            hit = por_ide.get(t["ide"])
            if hit is None or float(hit.can or 0.0) != 0.0:
                logger.warning("[registro] no quedo a 0 la linea %s "
                               "(parte %s, registro %s)", t["ide"],
                               t["parte_cod"], t["registro_id"])
                res.a_cero.remove(t)
