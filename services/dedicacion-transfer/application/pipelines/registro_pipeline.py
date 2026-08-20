# application/pipelines/registro_pipeline.py
"""Pipeline de registro de PORCENTAJES en los partes de trabajo de Sigrid.

Orquesta las reglas; no las enuncia. La fuente normativa es
`docs/ARCHITECTURE.md` § Semántica de dominio imprescindible.

Pasos (el preflight ejecuta 1-8; la escritura, 1-10):

  1. Resolver los DESTINOS: la obra normal (en pruebas, la de pruebas) y,
     si hay líneas de postventa, la obra de postventa con su PARTIDA
     (ARCHITECTURE.md#regla-p5).
  2. Resolver el RECURSO de cada empleado (res.conide) si no viene dado:
     se elige el recurso con código mensual M*; a igualdad, el más
     reciente (ide mayor).
  3. Cargar los tipos de hora de los recursos implicados (reshor).
  4. Aplicar las REGLAS de la línea (ARCHITECTURE.md#regla-p1 … #regla-p3,
     #regla-p5).
  5. Localizar el parte de cada DESTINO+MES; proponer código si no existe.
  6. Idempotencia por synckey ('porcentajes:{id}') -> ya_registrado.
  6 bis. CONFLICTOS de línea SIN PARTIDA, por línea
     (ARCHITECTURE.md#regla-sin-partida) -> confirmar la imputación sin
     partida. Van los PRIMEROS: los otros dos avisos dan por hecho que esa
     línea se escribe.
  7. CONFLICTOS de pisado, por identidad de la línea
     (ARCHITECTURE.md#regla-conflicto) -> confirmar pisado.
  7 bis. CONFLICTOS de sobrecarga, por jornada del recurso en el parte
     (ARCHITECTURE.md#regla-capacidad) -> confirmar escritura. Van DESPUÉS
     de los de pisado: su cifra ya presupone que el pisado ocurre.
  8. (fin del preflight)
  9. Crear los partes que falten (con + hmo, releer el ide).
 10. Borrar las pisadas confirmadas + insertar las nuevas (por lotes).
"""
from __future__ import annotations

import logging
import unicodedata
from datetime import datetime, timezone
from typing import Optional

from application.services.partida_resolver import (
    construir_catalogo, resolver_normal, resolver_postventa,
)
from application.services.reglas_porcentajes import (
    AVISO_SIN_PARTIDA, MOTIVO_PARTIDA_PV_NO_HOJA, MOTIVO_SIN_PARTIDA,
    MOTIVO_SOBRECARGA, ReglasPorcentajes, clave_conflicto, clave_sin_partida,
    clave_sobrecarga, criterio_choque, es_linea_mensual, evaluar_capacidad,
    sin_partida,
)
from domain.models.registro_models import (
    AccionLinea, Conflicto, LineaEntrada, ObraEntrada, ParteDestino,
    Preflight, ResultadoRegistro,
)
from infrastructure.sigrid.sigrid_write_client import synckey_de

logger = logging.getLogger(__name__)


def _norm(texto: Optional[str]) -> str:
    plano = unicodedata.normalize("NFD", texto or "")
    sin = "".join(c for c in plano if unicodedata.category(c) != "Mn")
    return " ".join(sin.lower().split())


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
    def _obra_destino(self, obra: ObraEntrada) -> tuple[ObraEntrada, bool]:
        """Paso 1a. En pruebas, TODO va a la obra de pruebas."""
        if self._st.obra_pruebas_forzar:
            destino = self._cli.obra_por_codigo(self._st.obra_pruebas_cod)
            if destino is None:
                raise RuntimeError(
                    f"obra de pruebas {self._st.obra_pruebas_cod} "
                    f"no encontrada")
            logger.warning(
                "[registro] MODO PRUEBAS: la obra %s se ignora; se escribe "
                "en %s (%s)", obra.codigo, destino.codigo, destino.nombre)
            return destino, True
        if obra.ide:
            real = self._cli.obra_por_ide(int(obra.ide))
        elif obra.codigo:
            real = self._cli.obra_por_codigo(obra.codigo)
        else:
            real = None
        if real is None:
            raise RuntimeError(
                f"obra no encontrada en Sigrid (ide={obra.ide} "
                f"cod={obra.codigo})")
        return real, False

    # ------------------------------------------------------------- #
    def _destino_postventa(
        self, obra_origen: ObraEntrada, forzada: bool,
        destino_pruebas: ObraEntrada,
    ) -> tuple[Optional[ObraEntrada], Optional[dict], Optional[str]]:
        """Paso 1b. Obra de postventa + partida de la obra original.

        Devuelve (obra_destino_pv, partida, motivo_si_falla). En modo
        pruebas el parte se escribe en la obra de pruebas, pero la partida
        se resuelve igualmente contra la obra de postventa real (para
        validar el casado). Ver `ARCHITECTURE.md#regla-p5`.
        """
        obra_pv = self._cli.obra_por_codigo(self._st.postventa_obra_cod)
        if obra_pv is None:
            return None, None, (f"obra de postventa "
                                f"'{self._st.postventa_obra_cod}' "
                                f"no encontrada en Sigrid")
        filas = self._cli.capitulos_de_obra(int(obra_pv.ide))
        nodos = construir_catalogo(filas)
        self._nodos_pv = nodos
        nodo = resolver_postventa(nodos, obra_origen.codigo,
                                  obra_origen.nombre)
        partida = ({"ide": nodo.ide, "cod": nodo.cod, "res": nodo.res}
                   if nodo else None)
        if partida is None:
            return (None, None,
                    f"la obra {obra_origen.codigo or obra_origen.nombre} "
                    f"no casa con ninguna partida de "
                    f"{self._st.postventa_obra_cod}")
        destino = destino_pruebas if forzada else obra_pv
        return destino, partida, None

    # ------------------------------------------------------------- #
    def _es_hoja_activa_pv(self, paride: int) -> bool:
        """¿`paride` es una partida hoja activa del presupuesto de la obra
        de postventa? Es el universo de `ARCHITECTURE.md#regla-p5`, el mismo
        que se publica en `partidas_postventa`."""
        nodos = getattr(self, "_nodos_pv", None) or {}
        nodo = nodos.get(int(paride))
        return bool(nodo and nodo.es_hoja and nodo.activa)

    # ------------------------------------------------------------- #
    def _resolver_recursos(self, lineas: list[LineaEntrada]) -> dict:
        """Pasos 2-3: recurso de cada empleado + horas de cada recurso."""
        pendientes = sorted({
            int(l.empleado_ide) for l in lineas
            if not l.recurso_ide and l.empleado_ide
        })
        candidatos = self._cli.recursos_de_empleados(pendientes) \
            if pendientes else {}
        todos = {int(l.recurso_ide) for l in lineas if l.recurso_ide}
        for resides in candidatos.values():
            todos.update(int(r) for r in resides)
        horas = self._cli.horas_de_recursos(sorted(todos)) if todos else {}

        for linea in lineas:
            if linea.recurso_ide or not linea.empleado_ide:
                continue
            resides = candidatos.get(int(linea.empleado_ide), [])
            if not resides:
                continue                      # la regla lo omitirá
            con_mensual = [
                r for r in resides
                if any(h.es_mensual for h in horas.get(int(r), []))
            ]
            linea.recurso_ide = max(con_mensual) if con_mensual \
                else max(resides)
        return horas

    # ------------------------------------------------------------- #
    def preflight(self, *, obra: ObraEntrada,
                  lineas: list[LineaEntrada]) -> Preflight:
        destino_normal, forzada = self._obra_destino(obra)

        # Paso 1b: destino de postventa (solo si hace falta).
        destino_pv: Optional[ObraEntrada] = None
        partida_pv: Optional[dict] = None
        motivo_pv: Optional[str] = None
        if any(l.es_postventa for l in lineas) \
                and self._st.postventa_registrar:
            destino_pv, partida_pv, motivo_pv = self._destino_postventa(
                obra, forzada, destino_normal)

        # Pasos 2-4: recursos + reglas.
        horas = self._resolver_recursos(lineas)
        reglas = ReglasPorcentajes(
            horas, postventa_registrar=self._st.postventa_registrar,
            partida_postventa=partida_pv, motivo_postventa=motivo_pv)
        acciones: list[AccionLinea] = [reglas.decidir(l) for l in lineas]

        # Partida de imputación por línea: el override manual del front
        # manda; si no, la NORMAL se casa con la partida del recurso en el
        # presupuesto de la obra ORIGEN (patrón de partes: rol/categoría y
        # nombre), y la POSTVENTA ya trae el suyo de la obra de postventa
        # (`POSTVENTA_OBRA_COD`).
        nodos_origen = None
        por_id = {l.registro_id: l for l in lineas}
        for a in acciones:
            if a.accion != "escribir":
                continue
            linea = por_id.get(a.registro_id)
            if linea is not None and linea.paride:
                # El override del front manda… salvo que apunte fuera del
                # universo válido de la postventa (un capítulo, una partida
                # de baja). Ahí no se escribe: ver ARCHITECTURE #regla-p5.
                if a.destino == "postventa" \
                        and not self._es_hoja_activa_pv(linea.paride):
                    a.accion = "omitir"
                    a.motivo = MOTIVO_PARTIDA_PV_NO_HOJA.format(
                        paride=int(linea.paride))
                    continue
                a.paride = int(linea.paride)
                a.partida_cod = linea.partida_cod
                a.partida_metodo = "manual"
                continue
            if a.destino == "postventa":
                a.partida_metodo = "postventa"
                continue
            if nodos_origen is None:
                origen_real = None
                if obra.ide:
                    origen_real = self._cli.obra_por_ide(int(obra.ide))
                elif obra.codigo:
                    origen_real = self._cli.obra_por_codigo(obra.codigo)
                filas_o = self._cli.capitulos_de_obra(
                    int(origen_real.ide)) if origen_real else []
                nodos_origen = construir_catalogo(filas_o)
            m = resolver_normal(
                nodos_origen,
                linea.categoria if linea else None,
                linea.nombre if linea else a.nombre)
            if m is None:
                # Hasta F-013 esto se escribía igual, con un aviso que nadie
                # tenía que atender. Ahora el paso 6 bis lo convierte en un
                # conflicto: ver ARCHITECTURE.md#regla-sin-partida.
                a.paride = 0
                a.aviso = AVISO_SIN_PARTIDA
            else:
                a.paride, a.partida_cod, a.partida_metodo = m

        escribir = [a for a in acciones if a.accion == "escribir"]

        def obra_de(a: AccionLinea) -> ObraEntrada:
            return destino_pv if a.destino == "postventa" else destino_normal

        # Paso 5: parte por DESTINO + periodo.
        partes: dict[tuple[int, int, int], ParteDestino] = {}
        for a in escribir:
            d = obra_de(a)
            clave = (int(d.ide), a.ano, a.mes)
            if clave in partes:
                continue
            encontrado = self._cli.partes_existentes(
                int(d.ide), [(a.ano, a.mes)])[(a.ano, a.mes)]
            encontrado.obra_cod = d.codigo
            if not encontrado.existe and not encontrado.cod:
                encontrado.cod = self._cli.siguiente_cod_pt(a.ano)
            partes[clave] = encontrado

        # Paso 6: idempotencia por synckey.
        ya = self._cli.lineas_por_synckey(
            [synckey_de(a.registro_id) for a in escribir])
        for a in acciones:
            hit = ya.get(synckey_de(a.registro_id))
            if a.accion == "escribir" and hit is not None:
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
            parte_a = partes.get((int(obra_de(a).ide), a.ano, a.mes))
            conflictos.append(Conflicto(
                clave=clave_sin_partida(a),
                recurso_ide=int(a.recurso_ide), nombre=a.nombre,
                ano=a.ano, mes=a.mes,
                parte_cod=parte_a.cod if parte_a else None,
                horide=a.hora_ide, hora_codigo=a.hora_codigo,
                lineas=[],          # no sustituye a nadie: no borra nada
                nuevas=[_nueva(a)], registros=[a.registro_id],
                motivo="sin_partida"))
            logger.warning(
                "[registro] sin partida recurso=%s registro=%s %s/%s: "
                "no se escribe sin confirmar", a.recurso_ide, a.registro_id,
                a.ano, a.mes)

        # Paso 7: conflictos (ver ARCHITECTURE `#regla-conflicto`).
        pendientes = [a for a in acciones if a.accion == "escribir"]
        for clave_p, parte in sorted(partes.items()):
            if not parte.existe or not parte.ide:
                continue            # parte nuevo: no puede haber conflicto
            grupo = [a for a in pendientes
                     if (int(obra_de(a).ide), a.ano, a.mes) == clave_p]
            if not grupo:
                continue
            existentes = self._cli.lineas_del_parte(
                int(parte.ide), [a.recurso_ide for a in grupo])
            mias = {synckey_de(a.registro_id) for a in grupo}
            por_clave: dict[str, Conflicto] = {}
            for a in grupo:
                k = clave_conflicto(a)
                choques = [ls for ls in existentes
                           if criterio_choque(ls, a, mias=mias)]
                if not choques:
                    continue        # nada previo con esa identidad
                c = por_clave.get(k)
                if c is None:
                    contexto = [
                        ls for ls in existentes
                        if ls.reside == a.recurso_ide and ls not in choques
                        and es_linea_mensual(ls)
                    ]
                    c = Conflicto(
                        clave=k, recurso_ide=int(a.recurso_ide or 0),
                        ano=parte.ano, mes=parte.mes, parte_cod=parte.cod,
                        nombre=a.nombre, horide=a.hora_ide,
                        hora_codigo=a.hora_codigo,
                        lineas=choques, contexto=contexto)
                    por_clave[k] = c
                c.registros.append(a.registro_id)
                c.nuevas.append(_nueva(a))
            conflictos.extend(por_clave.values())

            # Paso 7 bis: capacidad (ver ARCHITECTURE `#regla-capacidad`).
            # Va DESPUÉS de los pisados del mismo parte, y no antes: su
            # cifra ya presupone que todos ellos se confirman.
            pisadas: dict[int, set[int]] = {}
            for c in por_clave.values():
                pisadas.setdefault(c.recurso_ide, set()).update(
                    ls.ide for ls in c.lineas)
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

        pf = Preflight(
            obra_destino=destino_normal, obra_origen=obra,
            forzada_pruebas=forzada,
            partes=[partes[k] for k in sorted(partes)], acciones=acciones,
            conflictos=conflictos)
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
            if not nodos:
                return []
            return [{"ide": n.ide, "cod": n.cod, "res": n.res,
                     "categoria": n.categoria}
                    for n in nodos.values() if n.es_hoja and n.activa]

        setattr(pf, "partidas_obra", _cat(nodos_origen))
        setattr(pf, "partidas_postventa",
                _cat(getattr(self, "_nodos_pv", None)))
        return pf

    # ------------------------------------------------------------- #
    def ejecutar(self, *, obra: ObraEntrada, lineas: list[LineaEntrada],
                 pisar_claves: set[str] | None = None,
                 usuario: str | None = None) -> ResultadoRegistro:
        pisar = {str(k) for k in (pisar_claves or set())}
        pf = self.preflight(obra=obra, lineas=lineas)
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
        )

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
        if not a_escribir:
            logger.info("[registro] nada que escribir (bloqueadas=%s)",
                        len(bloqueadas))
            return res

        # Paso 9: crear los partes que falten (por destino).
        por_parte = {(int(o.ide), p.ano, p.mes): p
                     for p in pf.partes
                     for o in [destino_normal, destino_pv] if o
                     and p.obra_cod == o.codigo}
        # (clave robusta: si ambos destinos coinciden —modo pruebas— es la
        #  misma entrada)
        for a in sorted(a_escribir, key=lambda x: (x.ano, x.mes)):
            d = obra_de(a)
            clave = (int(d.ide), a.ano, a.mes)
            p = por_parte.get(clave)
            if p is None or (p.existe and p.ide):
                continue
            marca = (f" ({self._st.marca_pruebas})" if pf.forzada_pruebas
                     else "")
            desc = f"Parte {d.nombre or d.codigo}{marca}"
            cod = p.cod or self._cli.siguiente_cod_pt(a.ano)
            self._cli.escribir(self._cli.stmts_crear_parte(
                obra=d, ano=a.ano, mes=a.mes, cod=cod, desc=desc))
            nuevos = self._cli.partes_existentes(int(d.ide),
                                                 [(a.ano, a.mes)])
            creado = nuevos.get((a.ano, a.mes))
            if creado is None or not creado.ide:
                raise RuntimeError(f"no se pudo crear el parte {cod}")
            p.existe, p.ide, p.cod, p.creado = (True, creado.ide,
                                                creado.cod, True)
            logger.info("[registro] parte creado %s (ide=%s) obra=%s %s/%s",
                        p.cod, p.ide, d.codigo, a.ano, a.mes)

        # Paso 10: borrar pisadas + insertar.
        statements: list[dict] = []
        # Una misma línea de Sigrid puede aparecer en más de un conflicto
        # (dos pendientes del mismo recurso con partidas distintas chocan
        # con ella). Se borra UNA vez: el segundo DELETE no borraría nada y
        # dejaría `borradas` contando de más.
        ides_borrados: set[int] = set()
        escribibles = {a.registro_id for a in a_escribir}
        for c in pf.conflictos:
            if c.clave not in pisar:
                continue
            # R32: un conflicto confirmado solo emite sus borrados si al
            # menos uno de sus registros llega a escribirse. Si no —porque
            # los bloquea otro conflicto sin confirmar—, borrar dejaría el
            # parte SIN la línea vieja y SIN la nueva: pérdida neta de un
            # apunte de Administración, y encima silenciosa.
            if not (set(c.registros) & escribibles):
                continue
            for ls in c.lineas:
                if ls.ide in ides_borrados:
                    continue
                ides_borrados.add(ls.ide)
                statements.append(self._cli.stmt_borrar_linea(ls.ide))
                res.borradas += 1

        pos_por_parte: dict[int, int] = {}
        tex = self._st.marca_pruebas if pf.forzada_pruebas else None
        for a in sorted(a_escribir, key=lambda x: (x.ano, x.mes,
                                                   x.registro_id)):
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
                tex=tex, paride=int(a.paride or 0)))
            res.escritas.append({"registro_id": a.registro_id,
                                 "hmoide": hmoide, "parte_cod": p.cod,
                                 "obra_cod": d.codigo,
                                 "destino": a.destino,
                                 "hora_codigo": a.hora_codigo,
                                 "partida_cod": a.partida_cod,
                                 "can": a.can, "pre": a.pre, "tot": a.tot})

        afectadas = self._cli.escribir(statements)
        logger.info("[registro] escritas=%s borradas=%s filas=%s usuario=%s "
                    "ts=%s", len(res.escritas), res.borradas, afectadas,
                    usuario, datetime.now(timezone.utc).isoformat())

        mapa = self._cli.lineas_por_synckey(
            [synckey_de(e["registro_id"]) for e in res.escritas])
        for e in res.escritas:
            hit = mapa.get(synckey_de(e["registro_id"]))
            if hit is not None:
                e["hmores_ide"] = hit.ide
        return res
