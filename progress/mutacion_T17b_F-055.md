<!-- progress/mutacion_T17b_F-055.md -->
# F-055 · T17b · Mutación de las líneas nuevas

Sobre `c997385`. Mutantes del **generador del arnés**
(`harness.mutacion.generar_mutantes`) en las líneas de producción de
`b3e5373..c997385` (`propuestas_mes.py`, `app.py`, `sigrid_write_client.py`),
más 4 **manuales** donde el arnés no genera (`lifespan`, la marca de parada).
Cada uno se aplica al fichero, corre los tests (api: `test_f055_propuestas_mes`,
`test_f055_propuestas_tras_escribir`, `test_f024_rutas_empresa`; transfer:
`test_f055_cliente_agrupado`, `test_f055_lecturas_lote`, `test_f055_lote`) y se
restaura. Script: `mut_t17b_arnes.py` (scratchpad de la sesión).

**9 mutantes, 9 muertos, 0 vivos.**

| Fichero:línea | Origen | Original → mutado (texto exacto de la línea) | Fallos |
|---|---|---|---|
| `propuestas_mes.py:72` | arnés | `self._ejecutor.shutdown(wait=False, cancel_futures=True)` → `self._ejecutor.shutdown(wait=True, cancel_futures=True)` | 1 |
| `propuestas_mes.py:72` | arnés | `self._ejecutor.shutdown(wait=False, cancel_futures=True)` → `self._ejecutor.shutdown(wait=False, cancel_futures=False)` | 1 |
| `sigrid_write_client.py:623` | arnés | `(int(f["pos"] or 0), self._linea_del_parte(f)))` → `(int(f["pos"] and 0), self._linea_del_parte(f)))` | 2 |
| `sigrid_write_client.py:623` | arnés | `(int(f["pos"] or 0), self._linea_del_parte(f)))` → `(int(f["pos"] or 1), self._linea_del_parte(f)))` | 1 |
| `sigrid_write_client.py:625` | arnés | `return {h: [ls for _, ls in sorted(v, key=lambda x: x[0])]` → `return {h: [ls for _, ls in sorted(v, key=lambda x: x[1])]` | 3 |
| `app.py:57` | manual | `app.state.contenedor.propuestas_mes.cerrar()` → `pass` | 1 |
| `app.py:70` | manual | `lifespan=_ciclo_de_vida,` → `lifespan=None,` | 1 |
| `propuestas_mes.py:71` | manual | `self._parada.set()` → `pass` | 1 |
| `propuestas_mes.py:159` | manual | `break` → `pass` | 1 |
