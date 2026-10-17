# prueba_escritura_porcentajes.py
"""Pruebas de escritura de PORCENTAJES en Sigrid — script de fases.

Sigue la receta validada con los partes diarios: dry-run por defecto,
inspección primero, y limpieza por marca. Usa el .env del proyecto.

Fases:
  python prueba_escritura_porcentajes.py inspeccionar
      Vuelca las últimas líneas M* reales (can/canres/pre/tot/paride/caaide)
      y una muestra de hderes: fija el mapeo ANTES de escribir nada.
  python prueba_escritura_porcentajes.py estado
      Parte(s) de la obra de pruebas del mes actual y sus líneas.
  python prueba_escritura_porcentajes.py preflight
      Preflight de las líneas de ejemplo (no escribe).
  python prueba_escritura_porcentajes.py ejecutar --confirmar
      Escribe las líneas de ejemplo en la obra de pruebas.
  python prueba_escritura_porcentajes.py verificar
      Relee por synckey lo escrito por este script.
  python prueba_escritura_porcentajes.py limpiar --confirmar
      Borra SOLO las líneas con la marca de pruebas de este hilo.
  python prueba_escritura_porcentajes.py propuesta --obra 0694 --recurso N
      [--ano A --mes M --categoria C --nombre "N"]
      SOLO LECTURA (F-050): catálogo de la obra con su mayor, partida
      propuesta del recurso (método, origen, botón preelegido) y los
      segundos de cada lectura. No llama a escribir ni a ejecutar.
  python prueba_escritura_porcentajes.py medir --ano A --mes M --obra 0694
      --obra 0696 --recurso N [--recurso N2] [--partida OBRA:PARIDE] [--lote]
      SOLO LECTURA (F-055): el preflight de cada obra con esos recursos (y
      la partida elegida de --partida), con los segundos de cada lectura,
      de cada obra y del total. No llama a escribir ni a ejecutar. Con
      --lote, todas las obras a la vez, como el preflight en lote (T18).

Sin --confirmar, las fases de escritura solo muestran lo que harían.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from datetime import date

from config.settings import get_settings
from application.pipelines.registro_lote import RegistroLote
from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import LineaEntrada, ObraEntrada
from infrastructure.sigrid.sigrid_write_client import (
    PREFIJO_SYNCKEY, SigridWriteClient, medir_lecturas,
)

# --- Líneas de ejemplo (EDITAR con RECURSOS reales con código M*) --- #
# `recurso_ide` es el `res.ide` del recurso persona (F-026,
# ARCHITECTURE.md#regla-recurso): el transfer lo usa tal cual.
# Empresa (`con.emp`) de las líneas y de las obras que busca este script:
# la obra se busca por código Y empresa (ARCHITECTURE.md#regla-empresa).
EMPRESA_PRUEBA = 1

# registro_id arbitrario para pruebas (synckey 'porcentajes:9000xx').
LINEAS_PRUEBA = [
    {"registro_id": 900001, "recurso_ide": 0, "dni": None,
     "nombre": "EDITAR: encargado con MENC", "porcentaje": 0.40,
     "empresa": EMPRESA_PRUEBA},
    {"registro_id": 900002, "recurso_ide": 0, "dni": None,
     "nombre": "EDITAR: jefe de obra con MJEFO", "porcentaje": 0.60,
     "empresa": EMPRESA_PRUEBA},
    {"registro_id": 900003, "recurso_ide": 0, "dni": None,
     "nombre": "EDITAR: postventa del mismo encargado",
     "porcentaje": 0.10, "es_postventa": True, "empresa": EMPRESA_PRUEBA},
]

#: F-055 (R2): primer `registro_id` de las líneas de la fase `medir`, tan
#: arbitrario como los de arriba (synckey 'porcentajes:9900xx').
REGISTRO_MEDIR = 990000

# La obra "original" de estas líneas de prueba: su capítulo debe existir
# en la obra de postventa (fase capitulos para verlos).
OBRA_ORIGEN_PRUEBA = {"codigo": "0678"}


def _no_vacio(d: dict) -> dict:
    return {k: v for k, v in d.items() if v not in (None, 0, 0.0, "", " ")}


def _cliente(st) -> SigridWriteClient:
    return SigridWriteClient(
        base_url=st.sigrid_api_base_url,
        function_key=st.sigrid_api_function_key,
        database=st.sigrid_api_database,
        timeout_s=st.sigrid_api_timeout_s,
        max_statements=st.sigrid_max_statements,
        max_rows=st.sigrid_max_rows,
        tip_parte=st.tip_parte_trabajo, est_parte=st.est_parte_activo)


def _lineas(ano: int, mes: int) -> list[LineaEntrada]:
    return [LineaEntrada(ano=ano, mes=mes, **d) for d in LINEAS_PRUEBA]


def _obra_origen() -> ObraEntrada:
    return ObraEntrada(**OBRA_ORIGEN_PRUEBA)


def fase_inspeccionar(cli: SigridWriteClient) -> None:
    print("== Últimas líneas M* reales (fijar el mapeo con esto) ==")
    for f in cli.inspeccionar_mensuales(20):
        print(json.dumps(_no_vacio(f), ensure_ascii=False, default=str))
    print("\n== Muestra de hderes (Dedicación de recursos) ==")
    try:
        filas = cli._read(
            "SELECT TOP 10 * FROM hderes ORDER BY ide DESC", [])
        for f in filas:
            print(json.dumps(_no_vacio(f), ensure_ascii=False, default=str))
    except Exception as exc:                    # noqa: BLE001
        print(f"(hderes no disponible: {exc})")


def fase_capitulos(cli: SigridWriteClient, st) -> None:
    """Capítulos de la obra de postventa (para verificar el casado)."""
    obra = cli.obra_por_codigo(st.postventa_obra_cod, EMPRESA_PRUEBA)
    if obra is None:
        print(f"Obra de postventa '{st.postventa_obra_cod}' NO encontrada. "
              f"Ajusta POSTVENTA_OBRA_COD en el .env.")
        return
    print(f"Obra postventa: {obra.codigo} · {obra.nombre} (ide={obra.ide})")
    for c in cli.capitulos_de_obra(int(obra.ide)):
        print(f"  ide={c['ide']:>8}  padide={c.get('padide') or 0:>8}  "
              f"cod={c.get('cod') or '':<20} {c.get('res') or ''}")


def fase_estado(cli: SigridWriteClient, st, ano: int, mes: int) -> None:
    obra = cli.obra_por_codigo(st.obra_pruebas_cod, EMPRESA_PRUEBA)
    if obra is None:
        print(f"Obra de pruebas {st.obra_pruebas_cod} no encontrada")
        return
    print(f"Obra pruebas: {obra.codigo} · {obra.nombre} (ide={obra.ide}, "
          f"cenide={getattr(obra, 'cenide', 0)})")
    partes = cli.partes_existentes(int(obra.ide), [(ano, mes)])
    p = partes[(ano, mes)]
    print(f"Parte {ano}/{mes:02d}: existe={p.existe} ide={p.ide} "
          f"cod={p.cod}")
    if p.existe and p.ide:
        filas = cli._read(
            "SELECT hmores.ide AS ide, hmores.reside AS reside, hmores.fec "
            "AS fec, auxhor.cod AS hora, hmores.can AS can, hmores.pre AS "
            "pre, hmores.tot AS tot, hmores.synckey AS synckey FROM hmores "
            "LEFT JOIN auxhor ON auxhor.ide = hmores.horide "
            "WHERE hmores.hmoide = ? ORDER BY hmores.pos", [int(p.ide)])
        print(f"Líneas del parte: {len(filas)}")
        for f in filas:
            print("  ", json.dumps(_no_vacio(f), ensure_ascii=False,
                                   default=str))


def fase_preflight(pipeline: RegistroPipeline, st, ano: int, mes: int):
    pf = pipeline.preflight(
        obra=_obra_origen(), lineas=_lineas(ano, mes))
    print(f"Obra destino: {pf.obra_destino.codigo} "
          f"(pruebas={pf.forzada_pruebas})")
    for p in pf.partes:
        print(f"Parte {p.ano}/{p.mes:02d}: existe={p.existe} cod={p.cod}")
    obra_pv = getattr(pf, "obra_postventa", None)
    cap = getattr(pf, "capitulo_postventa", None)
    if obra_pv:
        print(f"Destino postventa: {obra_pv.codigo} · capítulo "
              f"{cap['cod'] if cap else '?'} (paride="
              f"{cap['ide'] if cap else '?'})")
    for a in pf.acciones:
        print(f"  [{a.accion:13s}] reg={a.registro_id} {a.nombre} "
              f"dest={a.destino} paride={a.paride} cod={a.hora_codigo} "
              f"can={a.can} pre={a.pre} tot={a.tot} motivo={a.motivo}")
    for c in pf.conflictos:
        print(f"  CONFLICTO {c.clave} ({c.hora_codigo}): "
              f"{len(c.lineas)} existentes -> nuevas {c.nueva_can}")
    return pf


def fase_ejecutar(pipeline: RegistroPipeline, st, ano: int, mes: int,
                  confirmar: bool, pisar: list[str]) -> None:
    pf = fase_preflight(pipeline, st, ano, mes)
    if not confirmar:
        print("\nDRY-RUN: añade --confirmar para escribir de verdad.")
        return
    if not st.obra_pruebas_forzar:
        print("ATENCIÓN: OBRA_PRUEBAS_FORZAR=false (¡producción!). Aborta "
              "si no era la intención.")
    r = pipeline.ejecutar(
        obra=_obra_origen(), lineas=_lineas(ano, mes),
        pisar_claves=set(pisar), usuario="prueba_escritura_porcentajes")
    print(f"escritas={len(r.escritas)} borradas={r.borradas} "
          f"ya={len(r.ya_registradas)} omitidas={len(r.omitidas)} "
          f"pendientes={len(r.pendientes_confirmacion)}")
    for e in r.escritas:
        print("  ", e)
    for c in r.pendientes_confirmacion:
        print(f"  PENDIENTE {c.clave}: relanza con --pisar {c.clave}")


def fase_verificar(cli: SigridWriteClient) -> None:
    claves = [f"{PREFIJO_SYNCKEY}{d['registro_id']}" for d in LINEAS_PRUEBA]
    mapa = cli.lineas_por_synckey(claves)
    if not mapa:
        print("No hay líneas nuestras (synckey) en Sigrid.")
    for k, ls in sorted(mapa.items()):
        print(f"{k}: hmores.ide={ls.ide} reside={ls.reside} "
              f"fec={ls.fecha_int} cod={ls.hora_codigo} can={ls.can} "
              f"tot={ls.tot}")


def fase_limpiar(cli: SigridWriteClient, st, confirmar: bool) -> None:
    filas = cli._read(
        "SELECT ide, hmoide, reside, fec, can, synckey FROM hmores "
        "WHERE CAST(tex AS NVARCHAR(200)) = ? "
        "AND synckey LIKE ?", [st.marca_pruebas, f"{PREFIJO_SYNCKEY}%"])
    print(f"Líneas marcadas '{st.marca_pruebas}' de este hilo: {len(filas)}")
    for f in filas:
        print("  ", _no_vacio(f))
    if not filas:
        return
    if not confirmar:
        print("DRY-RUN: añade --confirmar para borrarlas.")
        return
    cli.escribir([cli.stmt_borrar_linea(int(f["ide"])) for f in filas])
    print("Borradas.")


def _cronometrar(cli, tiempos: list) -> None:
    """Envuelve las lecturas de la propuesta para medir cada una."""
    def medir(nombre: str, lectura):
        def medida(*a, **kw):
            t0 = time.perf_counter()
            try:
                return lectura(*a, **kw)
            finally:
                tiempos.append((nombre, time.perf_counter() - t0))
        return medida

    for nombre in ("obra_por_codigo", "capitulos_de_obra",
                   "historial_partidas"):
        setattr(cli, nombre, medir(nombre, getattr(cli, nombre)))


def fase_propuesta(cli, pipeline: RegistroPipeline, obra_cod: str,
                   recurso: int, ano: int, mes: int,
                   categoria: str | None = None,
                   nombre: str | None = None) -> dict:
    """F-050 (T16, M1): la propuesta de UN recurso en UNA obra, solo
    lectura: la misma `RegistroPipeline.proponer` que el endpoint."""
    tiempos: list[tuple[str, float]] = []
    _cronometrar(cli, tiempos)
    r = pipeline.proponer(
        empresa=EMPRESA_PRUEBA, obra=ObraEntrada(codigo=obra_cod), ano=ano,
        mes=mes, lineas=[{"clave": "linea", "recurso_ide": recurso,
                          "nombre": nombre, "categoria": categoria,
                          "es_postventa": False}])
    if not r["ok"]:
        print(f"NO se propone: {r['error']}")
        return r
    cat = r["partidas_obra"]
    for p in cat:
        print(f"  {p['mayor']:4s} {p['cod'] or '':<16} {p['res'] or ''}")
    por_mayor = Counter(p["mayor"] for p in cat)
    print(f"Catálogo de {obra_cod}: {len(cat)} partidas hoja activas")
    print("Por mayor: " + " · ".join(
        f"{m} {por_mayor[m]}" for m in ("CD", "CI", "CP", "OTRO")))
    prop = r["propuestas"]["linea"]
    if prop is None:
        print("Propuesta: ninguna (sin partida)")
    else:
        print(f"Propuesta: {prop['cod']} · {prop['res']} "
              f"(paride {prop['paride']})")
        print(f"  método {prop['metodo']} · origen {prop['origen'] or '—'}")
    print(f"Botón preelegido (mayor_inicial): "
          f"{r['mayor_inicial']['linea'] or 'Todas'}")
    for n, s in tiempos:
        print(f"  lectura {n}: {s:.2f} s")
    return r


def _partidas_por_obra(parser, valores: list[str],
                       obras: list[str]) -> dict[str, int]:
    """`--partida OBRA:PARIDE` -> {obra: paride}; la obra, de las --obra."""
    out: dict[str, int] = {}
    for v in valores:
        obra, sep, paride = v.partition(":")
        if not sep or not paride.isdigit() or obra not in obras:
            parser.error(f"--partida {v}: se espera OBRA:PARIDE, con OBRA "
                         f"entre las --obra")
        out[obra] = int(paride)
    return out


def _imprimir_lecturas(m) -> None:
    for x in m.lecturas:
        filas = "error" if x.filas is None else f"{x.filas} filas"
        print(f"  lectura {x.nombre}: {filas} · {x.segundos:.2f} s")


def _imprimir_acciones(pf) -> None:
    for a in (pf.acciones if pf is not None else []):
        print(f"  [{a.accion}] recurso={a.recurso_ide} "
              f"paride={a.paride} {a.partida_metodo or '—'}")


def fase_medir(pipeline: RegistroPipeline, ano: int, mes: int,
               obras: list[str], recursos: list[int],
               partidas: dict[str, int], lote=None) -> None:
    """F-055 (R2, T2 y T18): SOLO LECTURA. El preflight de cada obra con
    esos recursos (y su partida elegida, si se da), midiendo cada lectura:
    segundos por lectura, por obra y en total. Sin `lote`, obra a obra con el
    mismo `RegistroPipeline.preflight` que el endpoint suelto; con `lote` (un
    `RegistroLote`), todas a la vez como `POST /api/registro/preflight-lote`
    (T18). Nunca `ejecutar`."""
    porcentaje = round(1 / len(obras), 4)

    def lineas_de(i: int, cod: str) -> list[LineaEntrada]:
        return [LineaEntrada(
            registro_id=REGISTRO_MEDIR + 100 * i + j, ano=ano, mes=mes,
            porcentaje=porcentaje, recurso_ide=r, empresa=EMPRESA_PRUEBA,
            paride=partidas.get(cod)) for j, r in enumerate(recursos)]

    t0 = time.perf_counter()
    if lote is not None:
        print(f"== Lote de {len(obras)} obras ==")
        resultados: list = []
        with medir_lecturas() as total:
            try:
                resultados = lote.preflight(
                    [(ObraEntrada(codigo=cod), lineas_de(i, cod))
                     for i, cod in enumerate(obras)])
            except Exception as exc:            # noqa: BLE001
                print(f"NO se pudo: {exc}")
        _imprimir_lecturas(total)
        for cod, pf in zip(obras, resultados):
            print(f"  Obra {cod}:" + (f" NO se pudo: {pf}"
                                      if isinstance(pf, Exception) else ""))
            if not isinstance(pf, Exception):
                _imprimir_acciones(pf)
    else:
        with medir_lecturas() as total:
            for i, cod in enumerate(obras):
                print(f"== Obra {cod} ==")
                t_obra = time.perf_counter()
                pf = None
                with medir_lecturas() as m:
                    try:
                        pf = pipeline.preflight(obra=ObraEntrada(codigo=cod),
                                                lineas=lineas_de(i, cod))
                    except Exception as exc:    # noqa: BLE001
                        print(f"NO se pudo: {exc}")
                segundos = time.perf_counter() - t_obra
                _imprimir_lecturas(m)
                _imprimir_acciones(pf)
                print(f"Obra {cod}: {m.n} lecturas · {m.segundos:.2f} s "
                      f"leyendo · {segundos:.2f} s en total")
    print(f"TOTAL: {len(obras)} obras · {total.n} lecturas · "
          f"{total.segundos:.2f} s leyendo · "
          f"{time.perf_counter() - t0:.2f} s en total")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fase", choices=["inspeccionar", "capitulos",
                                         "estado", "preflight", "ejecutar",
                                         "verificar", "limpiar",
                                         "propuesta", "medir"])
    parser.add_argument("--confirmar", action="store_true")
    parser.add_argument("--ano", type=int, default=date.today().year)
    parser.add_argument("--mes", type=int, default=date.today().month)
    parser.add_argument("--pisar", nargs="*", default=[])
    # F-050, fase `propuesta` (solo lectura); F-055, fase `medir` (solo
    # lectura), con --obra y --recurso repetibles.
    parser.add_argument("--obra", action="append", default=[])
    parser.add_argument("--recurso", type=int, action="append", default=[])
    parser.add_argument("--categoria")
    parser.add_argument("--nombre")
    parser.add_argument("--partida", action="append", default=[])
    parser.add_argument("--lote", action="store_true")
    args = parser.parse_args()
    if args.fase == "propuesta" and (len(args.obra) != 1
                                     or len(args.recurso) != 1):
        parser.error("la fase propuesta exige un --obra y un --recurso")
    if args.fase == "medir" and (not args.obra or not args.recurso):
        parser.error("la fase medir exige --obra y --recurso")
    partidas = _partidas_por_obra(parser, args.partida, args.obra)

    st = get_settings()
    cli = _cliente(st)
    pipeline = RegistroPipeline(cliente=cli, settings=st)

    if args.fase == "inspeccionar":
        fase_inspeccionar(cli)
    elif args.fase == "capitulos":
        fase_capitulos(cli, st)
    elif args.fase == "estado":
        fase_estado(cli, st, args.ano, args.mes)
    elif args.fase == "preflight":
        fase_preflight(pipeline, st, args.ano, args.mes)
    elif args.fase == "ejecutar":
        fase_ejecutar(pipeline, st, args.ano, args.mes, args.confirmar,
                      args.pisar)
    elif args.fase == "verificar":
        fase_verificar(cli)
    elif args.fase == "limpiar":
        fase_limpiar(cli, st, args.confirmar)
    elif args.fase == "propuesta":
        fase_propuesta(cli, pipeline, args.obra[0], args.recurso[0],
                       args.ano, args.mes, args.categoria, args.nombre)
    elif args.fase == "medir":
        fase_medir(pipeline, args.ano, args.mes, args.obra, args.recurso,
                   partidas, RegistroLote(cliente=cli, settings=st)
                   if args.lote else None)


if __name__ == "__main__":
    sys.exit(main())
