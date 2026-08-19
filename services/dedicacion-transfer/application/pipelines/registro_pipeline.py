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
    ReglasPorcentajes, clave_conflicto, criterio_choque,
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
        """Paso 1b. Obra de postventa + capítulo de la obra original.

        Devuelve (obra_destino_pv, capitulo, motivo_si_falla). En modo
        pruebas el parte se escribe en la obra de pruebas, pero el
        capítulo se resuelve igualmente contra la obra de postventa real
        (para validar el casado).
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
        capitulo = ({"ide": nodo.ide, "cod": nodo.cod, "res": nodo.res}
                    if nodo else None)
        if capitulo is None:
            return (None, None,
                    f"la obra {obra_origen.codigo or obra_origen.nombre} "
                    f"no casa con ningún capítulo de "
                    f"{self._st.postventa_obra_cod}")
        destino = destino_pruebas if forzada else obra_pv
        return destino, capitulo, None

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
        capitulo: Optional[dict] = None
        motivo_pv: Optional[str] = None
        if any(l.es_postventa for l in lineas) \
                and self._st.postventa_registrar:
            destino_pv, capitulo, motivo_pv = self._destino_postventa(
                obra, forzada, destino_normal)

        # Pasos 2-4: recursos + reglas.
        horas = self._resolver_recursos(lineas)
        reglas = ReglasPorcentajes(
            horas, postventa_registrar=self._st.postventa_registrar,
            capitulo_postventa=capitulo, motivo_postventa=motivo_pv)
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
                a.paride = 0
                a.aviso = ("partida no localizada para la categoría/"
                           "nombre: se imputa sin partida (editable)")
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

        # Paso 7: conflictos (ver ARCHITECTURE `#regla-conflicto`).
        conflictos: list[Conflicto] = []
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
                        and (ls.hora_codigo or "").upper().startswith("M")
                    ]
                    c = Conflicto(
                        clave=k, recurso_ide=int(a.recurso_ide or 0),
                        ano=parte.ano, mes=parte.mes, parte_cod=parte.cod,
                        nombre=a.nombre, horide=a.hora_ide,
                        hora_codigo=a.hora_codigo,
                        lineas=choques, contexto=contexto)
                    por_clave[k] = c
                c.registros.append(a.registro_id)
                c.nuevas.append({
                    "registro_id": a.registro_id, "can": a.can,
                    "tot": a.tot, "hora_codigo": a.hora_codigo,
                    "fecha_int": a.fecha_int, "partida_cod": a.partida_cod,
                })
            conflictos.extend(por_clave.values())

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
        setattr(pf, "capitulo_postventa", capitulo)

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
        for c in pf.conflictos:
            if c.clave in pisar:
                res.pisadas.append(c.clave)
            else:
                res.pendientes_confirmacion.append(c)
                bloqueadas.update(c.registros)

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
        for c in pf.conflictos:
            if c.clave not in pisar:
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
