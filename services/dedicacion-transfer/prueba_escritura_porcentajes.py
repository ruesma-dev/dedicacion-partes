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

Sin --confirmar, las fases de escritura solo muestran lo que harían.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date

from config.settings import get_settings
from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import LineaEntrada, ObraEntrada
from infrastructure.sigrid.sigrid_write_client import (
    PREFIJO_SYNCKEY, SigridWriteClient,
)

# --- Líneas de ejemplo (EDITAR con empleados reales con código M*) --- #
# registro_id arbitrario para pruebas (synckey 'porcentajes:9000xx').
LINEAS_PRUEBA = [
    {"registro_id": 900001, "empleado_ide": 0, "dni": None,
     "nombre": "EDITAR: encargado con MENC", "porcentaje": 0.40},
    {"registro_id": 900002, "empleado_ide": 0, "dni": None,
     "nombre": "EDITAR: jefe de obra con MJEFO", "porcentaje": 0.60},
    {"registro_id": 900003, "empleado_ide": 0, "dni": None,
     "nombre": "EDITAR: postventa del mismo encargado",
     "porcentaje": 0.10, "es_postventa": True},
]

# La obra "original" de estas líneas de prueba: su capítulo debe existir
# en la obra de postventa (fase capitulos para verlos).
OBRA_ORIGEN_PRUEBA = {"codigo": "0678"}


def _no_vacio(d: dict) -> dict:
    return {k: v for k, v in d.items() if v not in (None, 0, 0.0, "", " ")}


def _cliente(st) -> SigridWriteClient:
    return SigridWriteClient(
        base_url=st.sigrid_api_base_url,
        function_key=st.sigrid_api_function_key,
        database=st.sigrid_api_database, empresa=st.sigrid_empresa,
        timeout_s=st.sigrid_api_timeout_s,
        max_statements=st.sigrid_max_statements,
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
    obra = cli.obra_por_codigo(st.postventa_obra_cod)
    if obra is None:
        print(f"Obra de postventa '{st.postventa_obra_cod}' NO encontrada. "
              f"Ajusta POSTVENTA_OBRA_COD en el .env.")
        return
    print(f"Obra postventa: {obra.codigo} · {obra.nombre} (ide={obra.ide})")
    for c in cli.capitulos_de_obra(int(obra.ide)):
        print(f"  ide={c['ide']:>8}  padide={c.get('padide') or 0:>8}  "
              f"cod={c.get('cod') or '':<20} {c.get('res') or ''}")


def fase_estado(cli: SigridWriteClient, st, ano: int, mes: int) -> None:
    obra = cli.obra_por_codigo(st.obra_pruebas_cod)
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fase", choices=["inspeccionar", "capitulos",
                                         "estado", "preflight", "ejecutar",
                                         "verificar", "limpiar"])
    parser.add_argument("--confirmar", action="store_true")
    parser.add_argument("--ano", type=int, default=date.today().year)
    parser.add_argument("--mes", type=int, default=date.today().month)
    parser.add_argument("--pisar", nargs="*", default=[])
    args = parser.parse_args()

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


if __name__ == "__main__":
    sys.exit(main())
