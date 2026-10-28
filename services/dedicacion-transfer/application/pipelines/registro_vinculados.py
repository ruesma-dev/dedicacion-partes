# application/pipelines/registro_vinculados.py
"""F-044 · `PasoVinculados`: los recursos vinculados dentro del pipeline de
registro (design §6.3; ARCHITECTURE.md#regla-vinculado).

Aparte de `registro_pipeline.py` para no engordarlo:

- `proponer` (R9, R29): la propuesta de partida de cada subfila con la
  misma regla que el preflight (`reglas_vinculados.partida_del_vinculado`):
  la partida del titular en postventa, VAR o partida no `CI*`; si no
  (F-068), su historial en la obra y, sin él, su cuenta (la subcuenta de la
  cuenta de su hora por defecto, `reshor.caaide`, entre las cuentas del
  presupuesto de la obra) y su nombre.
- El preflight (R12-R26), en los puntos del pipeline donde sus lecturas
  van JUNTO a las de los titulares (R27): `decidir` tras la partida del
  titular (paso 4), la cuenta en el paso 4 bis, el parte en el 5,
  `idempotencia` con la lectura del paso 6, `sin_partida` en el 6 bis,
  `conflictos_del_parte` con las líneas del paso 7 y `cerrar` al final
  (titular omitido ⇒ sus vinculados también, sin sus avisos).

Lecturas (R27): las horas de los vinculados y sus líneas, en las mismas
lecturas que las de los trabajadores; las cuentas del presupuesto, UNA vez
por petición y solo si alguna subfila las necesita. Sin vinculados no se
lee nada más que antes. F-068 (R11, R12, R14): el historial de los
vinculados en la obra, también UNA vez por petición (con los recursos de
todos) y solo si alguna subfila llega a ese paso.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from domain.models.registro_models import (
    AccionLinea,
    AccionVinculado,
    Conflicto,
    HoraRecurso,
    LineaEntrada,
    ObraEntrada,
    ParteDestino,
    ResultadoRegistro,
    VinculadoEntrada,
)

from application.services.cuenta_analitica import subcuenta_de_linea
from application.services.estado_parte import motivo_choque
from application.services.partida_catalog import PartidaNodo
from application.services.propuesta_partida import Propuesta
from application.services.reglas_porcentajes import (
    AVISO_LINEA_CERO,
    AVISO_QUEDAN_A_CERO,
    MOTIVO_LINEA_CAMBIADA,
    clave_conflicto,
    clave_sobrecarga,
    criterio_choque,
    emparejar_ceros,
    es_de_la_hora,
    es_nuestra_de_otra,
    evaluar_capacidad,
    pisables_al_cero,
    repartir_choques,
    synckey_tras_editar,
)
from application.services.reglas_vinculados import (
    AVISO_SIN_PARTIDA_VINCULADO,
    METODO_MANUAL,
    METODOS_PROPUESTA_PROPIA,
    MOTIVO_PISADO_PENDIENTE,
    MOTIVO_SIGUE_AL_TRABAJADOR,
    MOTIVO_SIN_PARTIDA_VINCULADO,
    MOTIVO_SOBRECARGA_VINCULADO,
    MOTIVO_TITULAR_SIN_ESCRIBIR,
    PartidaElegida,
    PartidaTitular,
    clave_sin_partida_vinculado,
    decidir_vinculados,
    es_linea_de,
    partida_del_vinculado,
    partida_por_cuenta_o_nombre,
    partida_por_historial,
    por_que_sin_ci,
    synckey_vinculado,
    va_con_el_titular,
)

logger = logging.getLogger(__name__)


class _UnaVez:
    """El resultado de `leer`, leído la primera vez que se pide."""

    def __init__(self, leer: Callable[[], Any]) -> None:
        self._leer = leer
        self._leido = False
        self._valor: Any = None

    def __call__(self) -> Any:
        if not self._leido:
            self._valor = self._leer()
            self._leido = True
        return self._valor


def _titular_de_propuesta(linea: dict, catalogo: dict[int, PartidaNodo],
                          propuesta: Propuesta | None
                          ) -> PartidaTitular | None:
    """La partida del titular de una línea del selector: la elegida si es
    hoja activa de su catálogo (si no, None: en el preflight se omitiría y
    sus vinculados con él); sin elegida, su propuesta (o sin partida)."""
    destino = "postventa" if linea["es_postventa"] else "obra"
    elegida = linea.get("paride")
    if elegida:
        nodo = catalogo.get(int(elegida))
        if nodo is None or not (nodo.es_hoja and nodo.activa):
            return None
        return PartidaTitular(destino=destino, paride=int(nodo.ide),
                              cod=nodo.cod, res=nodo.res,
                              metodo=METODO_MANUAL)
    if propuesta is None:
        return PartidaTitular(destino=destino, paride=0)
    return PartidaTitular(destino=destino, paride=int(propuesta.paride),
                          cod=propuesta.cod, res=propuesta.res,
                          metodo=propuesta.metodo)


def clave_de(av: AccionVinculado) -> tuple[int, int]:
    """Un vinculado de una línea: (titular, recurso)."""
    return int(av.registro_id), int(av.recurso_ide)


def nueva_de(av: AccionVinculado) -> dict:
    """Lo que se escribiría, dentro de un `Conflicto`: las claves de las de
    un trabajador (`_nueva` del pipeline) más su recurso."""
    return {"registro_id": av.registro_id, "recurso_ide": av.recurso_ide,
            "can": av.can, "tot": av.tot, "hora_codigo": av.hora_codigo,
            "fecha_int": av.fecha_int, "partida_cod": av.partida_cod}


def _sumar_aviso(av: AccionVinculado, *textos: str | None) -> None:
    partes = [x for x in (av.aviso, *textos) if x]
    av.aviso = " · ".join(partes) if partes else None


def _sin_cuenta(av: AccionVinculado) -> None:
    """Una acción que ya no se escribe no lleva cuenta (como el titular)."""
    av.caa_ide, av.caa_cod, av.caa_motivo = 0, None, None
    av.caa_aviso, av.caa_origen, av.caa_nota = None, None, None


class PasoVinculados:
    """Los vinculados de una petición sobre el mismo cliente (o la memoria
    del lote) que el pipeline. Uno por petición: guarda las entradas de la
    api (`hmores_ide` y la partida guardada de cada vinculado)."""

    def __init__(self, cliente) -> None:
        self._cli = cliente
        self._entradas: dict[tuple[int, int], VinculadoEntrada] = {}

    # ------------------------------------------------------------- #
    def proponer(self, *, origen_ide: int, nodos: dict[int, PartidaNodo],
                 nodos_pv: dict[int, PartidaNodo], lineas: list[dict],
                 propuestas: dict[str, Propuesta | None], desde: int,
                 hasta: int) -> dict[str, dict[str, dict | None]]:
        """R9: por línea con `vinculados`, la propuesta de cada uno
        (`{paride, cod, res, metodo, origen}`, como la del titular) o None
        (sin partida). Vacío si ninguna línea trae vinculados. F-068 (R15):
        la misma regla que `_partida`, con el historial en la ventana
        `desde`-`hasta` y las cuentas, una vez y solo si hacen falta."""
        con = [l for l in lineas if l.get("vinculados")]
        if not con:
            return {}
        recursos = sorted({int(v["recurso_ide"]) for l in con
                           for v in l["vinculados"]})
        horas = _UnaVez(lambda: self._cli.horas_de_recursos(recursos))
        historial = _UnaVez(lambda: self._cli.historial_de_vinculados(
            recursos, int(origen_ide), int(desde), int(hasta)))
        cuentas = _UnaVez(
            lambda: self._cli.cuentas_del_presupuesto(int(origen_ide)))
        out: dict[str, dict[str, dict | None]] = {}
        for l in con:
            titular = _titular_de_propuesta(
                l, nodos_pv if l["es_postventa"] else nodos,
                propuestas.get(l["clave"]))
            por_recurso: dict[str, dict | None] = {}
            for v in l["vinculados"]:
                rid = int(v["recurso_ide"])
                if titular is None:
                    por_recurso[str(rid)] = None
                    continue

                def previa(rid: int = rid):
                    return partida_por_historial(historial(), rid,
                                                 int(origen_ide), nodos)

                def ci(rid: int = rid, v: dict = v):
                    sub = subcuenta_de_linea(horas().get(rid, []), None)
                    return partida_por_cuenta_o_nombre(
                        nodos, cuentas(), sub, v.get("tipo_res"),
                        v.get("descripcion"))

                p = partida_del_vinculado(titular, None, True, ci, previa)
                por_recurso[str(rid)] = (
                    asdict(Propuesta(p.paride, p.cod, p.res, p.metodo,
                                     p.origen))
                    if p.paride else None)
            out[l["clave"]] = por_recurso
        return out

    # ------------------------------------------------------------- #
    #  Preflight
    # ------------------------------------------------------------- #
    def decidir(self, acciones: list[AccionLinea], lineas: list[LineaEntrada],
                horas: dict[int, list[HoraRecurso]], *, origen_ide: int,
                validas: dict, nodos_pv: dict[int, PartidaNodo],
                nodos: Callable[[], dict[int, PartidaNodo]],
                ventana: Callable[[], tuple[int, int]]
                ) -> list[AccionVinculado]:
        """Tras la partida de los titulares (paso 4): la línea de cada
        vinculado (`decidir_vinculados`, R12, R14, R18) y su partida (R15-R17
        y F-068 R1) con la elegida (validada en `validas`, la lectura del
        pipeline, o en el presupuesto de la postventa), la propuesta guardada
        con un método propio o la regla. El historial de los vinculados en la
        obra (en `ventana()`, `(desde, hasta)`: la del trabajador) y las
        cuentas del presupuesto, una vez y solo si alguna subfila llega a su
        paso; el presupuesto, el del pipeline si ya se leyó."""
        por_id = {l.registro_id: l for l in lineas}
        recursos = sorted({int(v.recurso_ide) for l in lineas
                           for v in l.vinculados})

        def leer_historial() -> list:
            desde, hasta = ventana()
            return self._cli.historial_de_vinculados(
                recursos, int(origen_ide), int(desde), int(hasta))

        historial = _UnaVez(leer_historial)
        cuentas = _UnaVez(
            lambda: self._cli.cuentas_del_presupuesto(int(origen_ide)))
        presupuesto = _UnaVez(nodos)
        out: list[AccionVinculado] = []
        for a in acciones:
            linea = por_id[a.registro_id]
            if not linea.vinculados:
                continue
            titular = PartidaTitular(
                destino=a.destino, paride=int(a.paride or 0),
                cod=a.partida_cod, res=a.partida_res, metodo=a.partida_metodo)
            for v, av in zip(linea.vinculados,
                             decidir_vinculados(a, linea, horas),
                             strict=True):
                self._entradas[clave_de(av)] = v
                if av.accion == "escribir":
                    self._partida(av, v, titular, horas, int(origen_ide),
                                  validas, nodos_pv, presupuesto, cuentas,
                                  historial)
                out.append(av)
        return out

    @staticmethod
    def _valida(paride: int, destino: str, origen_ide: int, validas: dict,
                nodos_pv: dict[int, PartidaNodo]) -> tuple[bool, str | None]:
        """¿`paride` es hoja activa del presupuesto de su destino? Con su
        descripción. La de la obra, por `validar_partidas` (F-055); la de la
        postventa, en su presupuesto (`#regla-p5`)."""
        if destino == "postventa":
            nodo = nodos_pv.get(int(paride))
            return (bool(nodo and nodo.es_hoja and nodo.activa),
                    nodo.res if nodo else None)
        v = validas.get(int(paride))
        return (v is not None and v.vale_en(origen_ide),
                v.res if v else None)

    def _partida(self, av: AccionVinculado, v: VinculadoEntrada,
                 titular: PartidaTitular, horas: dict, origen_ide: int,
                 validas: dict, nodos_pv: dict, presupuesto: Callable,
                 cuentas: Callable, historial: Callable) -> None:
        """R15-R17 sobre `av`: elegida (si no vale, omitida); sin ella, si
        no va con el titular, la propuesta guardada con un método propio que
        vale (F-055: se escribe lo que enseña el cuadrante; F-068 R16); si
        no, la regla: historial en la obra, cuenta y nombre (F-068 R1)."""
        elegida, valida = None, True
        if v.paride:
            valida, res = self._valida(int(v.paride), av.destino, origen_ide,
                                       validas, nodos_pv)
            elegida = PartidaElegida(int(v.paride), v.partida_cod, res)
        elif (v.propuesta_paride
              and v.propuesta_metodo in METODOS_PROPUESTA_PROPIA
              and not va_con_el_titular(titular)):
            vale, res = self._valida(int(v.propuesta_paride), av.destino,
                                     origen_ide, validas, nodos_pv)
            if vale:
                av.paride = int(v.propuesta_paride)
                av.partida_cod = v.propuesta_cod
                av.partida_res = v.propuesta_res or res
                av.partida_metodo = v.propuesta_metodo
                av.partida_origen = v.propuesta_origen
                return

        def previa():
            return partida_por_historial(historial(), int(av.recurso_ide),
                                         origen_ide, presupuesto())

        def ci():
            sub = subcuenta_de_linea(horas.get(int(av.recurso_ide), []),
                                     av.hora_ide)
            return partida_por_cuenta_o_nombre(presupuesto(), cuentas(), sub,
                                               v.tipo_res, v.descripcion)

        p = partida_del_vinculado(titular, elegida, valida, ci, previa)
        if p.omitir:
            av.accion, av.motivo = "omitir", p.motivo
            return
        av.paride, av.partida_cod, av.partida_res = p.paride, p.cod, p.res
        av.partida_metodo, av.partida_origen = p.metodo, p.origen
        if p.sin_partida:
            _sumar_aviso(av, AVISO_SIN_PARTIDA_VINCULADO.format(
                tipo=av.tipo, cod=av.cod, por_que=por_que_sin_ci(p.motivo)))

    # ------------------------------------------------------------- #
    def registradas(self, vinculados: list[AccionVinculado]
                    ) -> tuple[list[str], list[int]]:
        """Paso 6 (R13, R30): las `synckey` y los `hmores.ide` de los
        vinculados que se escriben, para la MISMA lectura de los titulares."""
        escribir = [av for av in vinculados if av.accion == "escribir"]
        return ([synckey_vinculado(*clave_de(av)) for av in escribir],
                [self._entradas[clave_de(av)].hmores_ide for av in escribir])

    def idempotencia(self, vinculados: list[AccionVinculado], por_sk: dict,
                     por_ide: dict) -> None:
        """Paso 6 (R13, R30): ya registrado si la línea de su `hmores_ide`
        es de su recurso, de su hora y no es nuestra de otra; si no, la de
        su `synckey`. Cada vinculado se decide solo (R18)."""
        for av in vinculados:
            if av.accion != "escribir":
                continue
            propia = synckey_vinculado(*clave_de(av))
            hit = por_ide.get(int(self._entradas[clave_de(av)].hmores_ide
                                  or 0))
            if (hit is None or hit.reside != av.recurso_ide
                    or not es_de_la_hora(hit, av.hora_codigo)
                    or es_nuestra_de_otra(hit.synckey, propia)):
                hit = por_sk.get(propia)
            if hit is not None:
                av.accion, av.hmores_ide = "ya_registrado", hit.ide
                av.motivo = (f"ya registrada en Sigrid (línea {hit.ide}); "
                             f"no se duplica")

    @staticmethod
    def sin_partida(vinculados: list[AccionVinculado]) -> list[Conflicto]:
        """Paso 6 bis (R16): un aviso por vinculado sin partida, con su
        clave (no la del titular, R26)."""
        return [Conflicto(
            clave=clave_sin_partida_vinculado(*clave_de(av)),
            recurso_ide=int(av.recurso_ide), nombre=av.nombre, ano=av.ano,
            mes=av.mes, parte_cod=av.parte_cod, horide=av.hora_ide,
            hora_codigo=av.hora_codigo, lineas=[], nuevas=[nueva_de(av)],
            registros=[av.registro_id], motivo="sin_partida",
            vinculado={"tipo": av.tipo, "cod": av.cod})
            for av in vinculados
            if av.accion == "escribir" and not int(av.paride or 0)]

    def conflictos_del_parte(
        self, grupo: list[AccionVinculado], existentes: list, donde: dict,
        parte: ParteDestino, lineas_cerradas: set[int],
        estado_de: Callable[[int | None], str],
    ) -> list[Conflicto]:
        """Paso 7 (R19-R23) para los vinculados de un parte, con las líneas
        que el pipeline ya leyó de todos los partes del periodo: choque en
        un cerrado ⇒ omitido (R22); choque En registro ⇒ pisado a confirmar
        por vinculado (R20); línea suya al 0 % ⇒ se edita (R21); y la
        capacidad de su hora (R23), con los pisados dados por confirmados."""
        mias = {synckey_vinculado(*clave_de(av)) for av in grupo}
        pisables: dict[int, set[int]] = {}
        for av in grupo:
            pisables.setdefault(int(av.recurso_ide), set()).update(
                ls.ide for ls in pisables_al_cero(
                    existentes, av, en_cerrado=lineas_cerradas, mias=mias,
                    hora=av.hora_codigo))
        por_clave: dict[str, Conflicto] = {}
        for av in grupo:
            suyas = pisables[int(av.recurso_ide)]
            choques = [ls for ls in existentes
                       if criterio_choque(ls, av, mias=mias)
                       and ls.ide not in suyas]
            if not choques:
                continue
            cerrado = next((donde[ls.ide] for ls in choques
                            if donde[ls.ide].cod in parte.cerrados), None)
            if cerrado is not None:
                av.accion = "omitir"
                av.motivo = motivo_choque(cerrado.cod, estado_de(cerrado.est))
                _sin_cuenta(av)
                continue
            k = clave_conflicto(av)
            c = por_clave.get(k)
            if c is None:
                c = Conflicto(
                    clave=k, recurso_ide=int(av.recurso_ide),
                    ano=parte.ano, mes=parte.mes,
                    parte_cod=donde[choques[0].ide].cod, nombre=av.nombre,
                    horide=av.hora_ide, hora_codigo=av.hora_codigo,
                    lineas=choques,
                    contexto=[ls for ls in existentes
                              if ls.reside == av.recurso_ide
                              and ls not in choques
                              and es_de_la_hora(ls, av.hora_codigo)
                              and ls.ide not in suyas],
                    vinculado={"tipo": av.tipo, "cod": av.cod})
                por_clave[k] = c
            c.registros.append(av.registro_id)
            c.nuevas.append(nueva_de(av))
        for c in por_clave.values():
            edita, c.a_cero_ides = repartir_choques(c.registros, c.lineas)
            c.edita_ide = min(edita.values())
        conflictos = list(por_clave.values())
        en_pisado = {(r, c.recurso_ide) for c in conflictos
                     for r in c.registros}
        self._emparejar_ceros(
            [av for av in grupo if av.accion == "escribir"
             and clave_de(av) not in en_pisado],
            existentes, donde, lineas_cerradas, mias)

        vivos = [av for av in grupo if av.accion == "escribir"]
        pisadas: dict[int, set[int]] = {}
        for c in conflictos:
            pisadas.setdefault(c.recurso_ide, set()).update(
                ls.ide for ls in c.lineas)
        for recurso, ides in pisables.items():
            pisadas.setdefault(recurso, set()).update(ides)
        for recurso in sorted({int(av.recurso_ide) for av in vivos}):
            suyas_ = [av for av in vivos if int(av.recurso_ide) == recurso]
            cabeza = suyas_[0]
            cap = evaluar_capacidad(
                [ls for ls in existentes if int(ls.reside) == recurso],
                suyas_, mias=mias, pisadas=pisadas.get(recurso, set()),
                es_jornada=es_linea_de(cabeza.hora_codigo))
            if not cap.sobrecarga:
                continue
            conflictos.append(Conflicto(
                clave=clave_sobrecarga(cabeza), recurso_ide=recurso,
                ano=parte.ano, mes=parte.mes, parte_cod=parte.cod,
                nombre=cabeza.nombre, horide=cabeza.hora_ide,
                hora_codigo=cabeza.hora_codigo, lineas=[],
                contexto=list(cap.contadas),
                nuevas=[nueva_de(av) for av in suyas_],
                registros=[av.registro_id for av in suyas_],
                motivo="sobrecarga", suma_existente=round(cap.existente, 4),
                suma_total=round(cap.total, 4), exceso=round(cap.exceso, 4),
                vinculado={"tipo": cabeza.tipo, "cod": cabeza.cod}))
        return conflictos

    @staticmethod
    def _emparejar_ceros(libres: list[AccionVinculado], existentes: list,
                         donde: dict, en_cerrado: set[int],
                         mias: set[str]) -> None:
        """R21 (`#regla-cero`): cada vinculado sin choque edita como mucho
        una línea suya al 0 % de su hora, con su aviso."""
        pares, sobran = emparejar_ceros(
            libres, existentes, en_cerrado=en_cerrado, mias=mias,
            clave=clave_de, hora=lambda av: av.hora_codigo)
        for av in libres:
            ls = pares.get(clave_de(av))
            if ls is None:
                continue
            ps = donde[ls.ide]
            av.linea_cero = {
                "ide": ls.ide, "hmoide": int(ps.ide), "parte_cod": ps.cod,
                "horide": ls.horide, "hora_codigo": ls.hora_codigo,
                "paride": ls.paride, "can": ls.can,
                "fecha_int": ls.fecha_int, "synckey": ls.synckey}
            partida = (av.partida_cod if ls.paride == av.paride
                       else ls.paride)
            n = sobran[int(av.recurso_ide)]
            _sumar_aviso(av, AVISO_LINEA_CERO.format(
                ide=ls.ide, parte=ps.cod, hora=ls.hora_codigo,
                partida=partida),
                AVISO_QUEDAN_A_CERO.format(n=n) if n else None)

    @staticmethod
    def cerrar(acciones: list[AccionLinea], vinculados: list[AccionVinculado],
               conflictos: list[Conflicto]) -> list[Conflicto]:
        """Fin del preflight (R18): el vinculado de un titular que acabó
        omitido (p. ej. por un choque en un parte cerrado) se omite con su
        motivo; los avisos de los vinculados omitidos se retiran."""
        titulares = {a.registro_id: a for a in acciones}
        for av in vinculados:
            t = titulares[av.registro_id]
            if av.accion != "omitir" and t.accion == "omitir":
                av.accion = "omitir"
                av.motivo = MOTIVO_SIGUE_AL_TRABAJADOR.format(
                    motivo=t.motivo)
                av.linea_cero = None
                _sin_cuenta(av)
        omitidos = {clave_de(av) for av in vinculados
                    if av.accion == "omitir"}
        return [c for c in conflictos
                if not (c.vinculado and all(
                    (r, c.recurso_ide) in omitidos for r in c.registros))]


def motivo_de_conflicto(c: Conflicto) -> tuple[str, bool]:
    """R26, R28: por qué no se escribe un vinculado retenido por su aviso
    sin confirmar y si deja rastro en `omitidas` (todos menos el pisado,
    como el titular)."""
    tipo, cod = (c.vinculado or {}).get("tipo"), (c.vinculado or {}).get(
        "cod")
    if c.motivo == "pisado":
        return MOTIVO_PISADO_PENDIENTE.format(clave=c.clave), False
    if c.motivo == "sobrecarga":
        return MOTIVO_SOBRECARGA_VINCULADO.format(
            tipo=tipo, cod=cod, hora=c.hora_codigo, total=c.suma_total,
            existente=c.suma_existente, nueva=c.nueva_can), True
    return MOTIVO_SIN_PARTIDA_VINCULADO.format(tipo=tipo, cod=cod), True


def _omitir(res: ResultadoRegistro, av: AccionVinculado, motivo: str,
            a_omitidas: bool = True) -> None:
    """R28: el vinculado no se escribe; en `omitidas` lleva su recurso
    (`vinculado_ide`): la api no lo confunde con su asignación."""
    av.accion, av.motivo, av.linea_cero = "omitir", motivo, None
    _sin_cuenta(av)
    if a_omitidas:
        res.omitidas.append({"registro_id": av.registro_id,
                             "vinculado_ide": av.recurso_ide,
                             "motivo": motivo})


class EscrituraVinculados:
    """R24, R28 (design §6.3): `ejecutar` de los vinculados, DESPUÉS de los
    titulares y de su relectura: solo los de un titular que quedó escrito
    (o ya registrado) y sin aviso propio sin confirmar. Edita en su sitio
    su línea al 0 % y el choque de su pisado confirmado (con la guarda de
    SU hora), pone a 0 los choques que sobran e inserta el resto en el
    parte del titular (lo crea si falta), en lotes del cliente y sin
    `DELETE`; luego relee."""

    def __init__(self, cliente, *, est: int, paso_pos: int,
                 tex: str | None, obra_de: Callable,
                 crear_parte: Callable, traza: Callable) -> None:
        self._cli = cliente
        self._est = int(est)
        self._paso = int(paso_pos)
        self._tex = tex
        self._obra_de = obra_de
        self._crear_parte = crear_parte
        self._traza = traza

    def ejecutar(self, res: ResultadoRegistro, partes: list[ParteDestino],
                 vinculados: list[AccionVinculado], conflictos: list,
                 pisar: set[str],
                 bloqueados: dict[tuple[int, int], tuple[str, bool]]) -> None:
        res.vinculados = vinculados
        escritos = ({e["registro_id"] for e in res.escritas}
                    | set(res.ya_registradas))
        motivo_titular: dict[int, str] = {}
        for o in res.omitidas:
            if "vinculado_ide" not in o:
                motivo_titular.setdefault(o["registro_id"], o["motivo"])
        a_escribir = []
        for av in vinculados:
            if av.accion != "escribir":
                continue
            if av.registro_id not in escritos:
                _omitir(res, av, MOTIVO_SIGUE_AL_TRABAJADOR.format(
                    motivo=motivo_titular.get(av.registro_id,
                                              MOTIVO_TITULAR_SIN_ESCRIBIR)))
            elif clave_de(av) in bloqueados:
                _omitir(res, av, *bloqueados[clave_de(av)])
            else:
                a_escribir.append(av)
        if not a_escribir:
            return
        mias = {synckey_vinculado(*clave_de(av)) for av in vinculados}
        edita, ceros, cambiadas = self._planear(a_escribir, conflictos,
                                                pisar, mias)
        for av in a_escribir:
            if clave_de(av) in cambiadas:
                _omitir(res, av, MOTIVO_LINEA_CAMBIADA.format(
                    ide=cambiadas[clave_de(av)]))
        a_escribir = [av for av in a_escribir if av.accion == "escribir"]
        orden = sorted(a_escribir, key=lambda x: (x.ano, x.mes,
                                                  *clave_de(x)))
        statements: list[dict] = []
        editadas: list[tuple[AccionVinculado, dict]] = []
        for av in orden:
            ls = edita.get(clave_de(av))
            if ls is None:
                continue
            sk = synckey_tras_editar(ls.synckey,
                                     synckey_vinculado(*clave_de(av)))
            despues = {
                "can": float(av.can), "pre": float(av.pre),
                "tot": float(av.tot), "horide": int(av.hora_ide),
                "hora_codigo": av.hora_codigo, "paride": int(av.paride or 0),
                "caaide": int(av.caa_ide or 0), "fecha_int": av.fecha_int,
                "synckey": sk, "tex": ls.tex if self._tex is None
                else self._tex}
            statements.append(self._cli.stmt_editar_linea(
                ide=ls.ide, reside=int(ls.reside), can_leido=ls.can,
                synckey_leida=ls.synckey, horide=int(av.hora_ide),
                can=float(av.can), pre=float(av.pre),
                paride=int(av.paride or 0), caaide=int(av.caa_ide or 0),
                fecha_int=av.fecha_int, synckey=sk, tex=self._tex,
                hora=av.hora_codigo))
            t = self._traza("edita vinculado", av.registro_id, ls, despues)
            t["vinculado_ide"] = av.recurso_ide
            res.editadas.append(t)
            editadas.append((av, t))
        trazas_cero = []
        for k, ls in ceros:
            av = next(x for x in a_escribir if clave_de(x) == k)
            statements.append(self._cli.stmt_poner_a_cero(
                ide=ls.ide, reside=int(ls.reside), can_leido=ls.can,
                synckey_leida=ls.synckey, hora=av.hora_codigo))
            t = self._traza("pone a 0 vinculado", av.registro_id, ls, {
                **t_fila(ls), "can": 0.0, "tot": 0.0})
            t["vinculado_ide"] = av.recurso_ide
            res.a_cero.append(t)
            trazas_cero.append(t)
        insertadas = self._insertar(
            [av for av in orden if clave_de(av) not in edita], partes,
            statements)
        afectadas = self._cli.escribir(statements)
        logger.info("[registro] vinculados escritos=%s editados=%s a_cero=%s "
                    "filas=%s", len(insertadas), len(editadas),
                    len(trazas_cero), afectadas)
        self._comprobar(res, insertadas, editadas, trazas_cero)

    def _insertar(self, nuevas: list[AccionVinculado],
                  partes: list[ParteDestino],
                  statements: list[dict]) -> list[AccionVinculado]:
        """Los `INSERT` en el parte de su titular (el del preflight), que se
        crea si aún no existe; `pos` tras el máximo del parte."""
        pos: dict[int, int] = {}
        for av in nuevas:
            d: ObraEntrada = self._obra_de(av)
            p = next(x for x in partes if x.obra_cod == d.codigo
                     and (x.ano, x.mes) == (av.ano, av.mes))
            if not (p.existe and p.ide):
                self._crear_parte(p, d)
            hmoide = int(p.ide)
            if hmoide not in pos:
                pos[hmoide] = self._cli.max_pos(hmoide)
            pos[hmoide] += self._paso
            statements.append(self._cli.stmt_insert_linea(
                hmoide=hmoide, obra=d, reside=int(av.recurso_ide),
                pos=pos[hmoide], fecha_int=av.fecha_int,
                horide=int(av.hora_ide), can=float(av.can),
                pre=float(av.pre), ano=av.ano, mes=av.mes,
                synckey=synckey_vinculado(*clave_de(av)), tex=self._tex,
                paride=int(av.paride or 0), caaide=int(av.caa_ide or 0)))
            av.parte_cod = p.cod
        return nuevas

    def _planear(self, a_escribir: list[AccionVinculado], conflictos: list,
                 pisar: set[str], mias: set[str]
                 ) -> tuple[dict, list, dict]:
        """Como `_planear_ediciones` del titular (F-051 R12): qué edita cada
        vinculado y qué se pone a 0, releído justo antes de escribir; si la
        línea ya no vale, cae (con todo su pisado)."""
        escribibles = {clave_de(av): av for av in a_escribir}
        piezas: list[tuple] = [
            ("edita", int(av.linea_cero["ide"]), clave_de(av), av, "cero",
             (clave_de(av),))
            for av in a_escribir if av.linea_cero]
        usadas: set[int] = set()
        for c in conflictos:
            regs = sorted(k for k in ((r, c.recurso_ide)
                                      for r in c.registros)
                          if k in escribibles)
            if not c.vinculado or c.clave not in pisar or not regs:
                continue
            libres = [ls for ls in c.lineas if ls.ide not in usadas]
            usadas.update(ls.ide for ls in libres)
            por_reg, a_cero = repartir_choques(regs, libres)
            piezas += [("edita", ide, k, escribibles[k], "choque",
                        tuple(regs)) for k, ide in por_reg.items()]
            piezas += [("a_cero", ide, regs[0], escribibles[regs[0]],
                        "choque", tuple(regs)) for ide in a_cero]
        if not piezas:
            return {}, [], {}
        leidas = self._cli.lineas_para_editar([pz[1] for pz in piezas])
        cambiadas: dict[tuple[int, int], int] = {}
        for _, ide, _, av, criterio, caen in piezas:
            if not self._sigue_valiendo(leidas.get(ide), av, criterio, mias):
                for k in caen:
                    cambiadas.setdefault(k, ide)
        edita = {k: leidas[ide] for que, ide, k, *_ in piezas
                 if que == "edita" and k not in cambiadas}
        ceros = [(k, leidas[ide]) for que, ide, k, *_ in piezas
                 if que == "a_cero" and k not in cambiadas]
        return edita, ceros, cambiadas

    def _sigue_valiendo(self, ls, av: AccionVinculado, criterio: str,
                        mias: set[str]) -> bool:
        """R24: sigue existiendo, de SU hora, sin enlaces, en un parte En
        registro y, según a qué iba, al 0 % y pisable o con su identidad."""
        if (ls is None or ls.enlazada
                or not es_de_la_hora(ls, av.hora_codigo)
                or ls.parte_est != self._est):
            return False
        if criterio == "cero":
            return bool(pisables_al_cero([ls], av, en_cerrado=set(),
                                         mias=mias, hora=av.hora_codigo))
        return criterio_choque(ls, av, mias=mias)

    def _comprobar(self, res: ResultadoRegistro,
                   insertadas: list[AccionVinculado],
                   editadas: list[tuple[AccionVinculado, dict]],
                   trazas_cero: list[dict]) -> None:
        """Relectura (como la del titular, F-051 R13): el `hmores_ide` de
        cada insertada por su `synckey`; la editada que no tiene lo escrito
        se omite; la puesta a 0 que no quedó, al log."""
        por_sk, por_ide = self._cli.lineas_registradas(
            [synckey_vinculado(*clave_de(av)) for av in insertadas],
            [t["ide"] for _, t in editadas] + [t["ide"] for t in trazas_cero])
        for av in insertadas:
            hit = por_sk.get(synckey_vinculado(*clave_de(av)))
            if hit is not None:
                av.hmores_ide = hit.ide
        for av, t in editadas:
            hit = por_ide.get(t["ide"])
            if hit is None or abs(float(hit.can or 0.0)
                                  - t["despues"]["can"]) >= 0.000001 \
                    or (hit.synckey or "").strip() != t["despues"]["synckey"]:
                logger.warning("[registro] la guarda no dejo editar la "
                               "linea %s (vinculado %s)", t["ide"],
                               av.recurso_ide)
                res.editadas.remove(t)
                _omitir(res, av, MOTIVO_LINEA_CAMBIADA.format(ide=t["ide"]))
                continue
            av.hmores_ide, av.parte_cod = t["ide"], t["parte_cod"]
        for t in trazas_cero:
            hit = por_ide.get(t["ide"])
            if hit is None or float(hit.can or 0.0) != 0.0:
                logger.warning("[registro] no quedo a 0 la linea %s "
                               "(parte %s, vinculado %s)", t["ide"],
                               t["parte_cod"], t["vinculado_ide"])
                res.a_cero.remove(t)


def t_fila(ls) -> dict:
    """Lo que tenía una línea que se pone a 0 (las claves de `_fila` del
    pipeline, F-051 R18)."""
    return {"can": ls.can, "pre": ls.pre, "tot": ls.tot,
            "horide": ls.horide, "hora_codigo": ls.hora_codigo,
            "paride": ls.paride, "caaide": ls.caaide,
            "fecha_int": ls.fecha_int, "synckey": ls.synckey, "tex": ls.tex}
