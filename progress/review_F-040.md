<!-- progress/review_F-040.md -->
Revisión incremental desde `efed4a6` (pasada 2), delta `efed4a6..f69e697`

# F-040 · Review (reviewer, 2026-10-06)

**Veredicto: APPROVED.**

**Nivel de rigor:** `estandar`, declarado en `features.json`. Exige fase RED,
cobertura ≥ 80 % y campaña de mutación con supervivientes analizados.

## Alcance de esta pasada

- **Pasada 1** (completa, `31132a4..431ca39`): CHANGES_REQUESTED con un solo
  cambio. El detalle está en `git show efed4a6:progress/review_F-040.md`.
  Lo que quedó dado por bueno:
  - las cifras salen de la regla del 100 % (`domain/estados.py`) y el
    exportador no decide ninguna;
  - las combinadas se hacen con `merged_cells.add` y llevan el valor en todo
    el grupo (comprobado en el XML);
  - formato, bandas, línea gruesa, cabecera en la fila 2, sin «Obra(código)»,
    y las dos hojas;
  - el Resumen «código descripción = NN%», con Postv- y VAR-29;
  - sin notación científica;
  - ningún test anterior cambiado;
  - la muestra, regenerada byte a byte;
  - los docs, y `azure-apps` sin cambios;
  - la mutación recalculada: 250 líneas y 77 mutantes, con 3 reproducidos a
    mano.
- **Delta de la pasada 2**: `f82e0b9` (ciclo 2) y `f69e697` (rastro). Toca
  `tests/test_f040_excel.py` (+13/-2), `progress/impl_F-040.md` y
  `progress/current.md`. **No cambia ningún fichero de producción**:
  `contenido.py` y `exporter.py` son los de `2b14802`/HEAD de la pasada 1. Por
  eso la campaña medida sigue valiendo y no hay que repetirla (RM1).

## Verificación del delta

- **`bash harness/init.sh`**: `ENTORNO LISTO`.
  - Raíz: 418 passed, 1 skipped.
  - api, front y transfer en verde.
  - `PUERTA COBERTURA` 100 % (132/132); `PUERTA TAMAÑO` dentro.
  - La línea de la api decía «caché», así que la he ejecutado aparte, sin
    caché: `python -m pytest tests -q -p no:cacheprovider` desde
    `services/dedicacion-api` da **619 passed**.
- **Cambio 1: corregido.** `test_f040_r16_99996_…` comprueba ahora también
  `_xml_hoja(contenido, 1)[0]["G3"]["v"] == "0"`.
  - **Reproducido por mí** en la copia del scratchpad, con el test nuevo y el
    mutante `float(valor) / 100 + 0.0` → `float(valor) / 100 - 0.0`: cae con
    `AssertionError: assert '-0' == '0'`, 1 failed y 32 passed. Sin el
    mutante, 33 passed.
  - He restaurado la copia y comprobado con `diff` que es idéntica al árbol.
- **Informe del implementer.** §2.3 dice ahora lo que pasa de verdad y trae la
  traza. Coincide con la mía. Para hacer sitio, el resto se ha resumido sin
  perder contenido: la muestra, los 7 puntos de la M1 y lo que queda fuera
  siguen ahí. Está a 219/220.
- **Observación 1 (`obra_ide`): recogida.** `_linea` usa ahora
  `itertools.count(1)`. El exportador no lee `obra_ide`, así que es
  determinista para un mismo orden de ejecución, y basta.
- **Observación 2 (M1): recogida** en `current.md` (sección F-040).
- **Rastro.**
  - `grep -n "Ninguna feature" progress/current.md`: vacío (exit 1).
  - La sección F-040 refleja la review 1 rechazada, el ciclo 2 hecho y la
    review 2 lanzada.
  - La M1 conserva el arranque, el `curl.exe` y los 7 puntos.
- La automejora de la pasada 1 está anotada en `arnes-base`, según el
  coordinador. No lo he comprobado: no entra en el alcance de esta copia.

## Checkpoints

- **C1** [x] `init.sh` con exit 0 · [x] están los ficheros base.
- **C2**
  - [x] Una sola `in_progress` (F-040).
  - [x] La rama es `feature/F-040-excel-modelo-juan`.
  - [x] `current.md` es coherente, con el paralelo de F-039 y F-041 decidido
    por el humano.
  - [x] Las `done` tienen resumen en `history.md`.
- **C3**
  - [x] Hexagonal: `contenido.py` y `exporter.py` en `infrastructure/`, el
    dominio sin tocar.
  - [x] Primera línea con la ruta.
  - [x] Sin prints, sin secretos y sin dependencias nuevas (`itertools` es de
    la biblioteca estándar).
  - [x] Trampas: la escala 0-100 se pasa a fracción solo en la celda; la
    postventa lleva su prefijo y no se mezcla; nada en Sigrid.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4**
  - [x] Cada requisito tiene su test. R16, el «-0» incluido, ya está vigilado.
    La tabla R → test de la pasada 1 sigue igual.
  - [x] Sin red ni BBDD.
  - [x] La M1 está en `current.md` con su comando exacto; `AAAA/MM` es el
    periodo con carga, y lo elige el humano.
- **C4 bis**
  - [x] Rigor declarado · [x] RED real (T1 y T3, y la del ciclo 2) ·
    [x] cobertura OK.
  - [x] Informe de mutación generado por la herramienta, con totales
    recalculados (250 y 77).
  - [x] Campaña no reejecutada: 439,9 s según el informe (> 60 s). Basta el
    recálculo puro más RM1-RM6.
  - [x] Coste: 22 s por mutante, con 1 worker · [x] sin «CAMPAÑA NO VÁLIDA»
    ni base rota.
  - [x] RM1: el delta no toca producción · [x] RM2: 20 × 22,0 ≈ 439,9 s.
  - N/A RM5, por nivel `estandar` · N/A RM6, no se quitó ninguna guarda ·
    N/A campaña manual, porque hubo automática.
  - [x] Sin supervivientes en la muestra. El aritmético de la línea 149, fuera
    de la muestra, ya muere (comprobado arriba).
  - [x] La sección «Evidencias» tiene los cuatro números y los workers, y ya
    no afirma nada falso.
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5**
  - [x] T1-T5 y T7 en `[x]`, con su commit `F-040 Tn:`. T6 es la MANUAL M1 del
    humano, listada en `current.md`, igual que en F-039.
  - [x] Sin temporales: `git status` limpio.
  - [x] `features.json` dice `in_progress`, que es lo real.

## Cobertura requisito → test

Sin cambios respecto a la pasada 1 (`git show efed4a6:progress/review_F-040.md`,
sección «Cobertura»). Los 33 tests están en
`services/dedicacion-api/tests/test_f040_excel.py`. R20 lo cubre
`test_f024_rutas_empresa.py`, que no se ha tocado. R21 se verificó sobre el
diff de los docs. La **M1 sigue pendiente del humano**: antes del `done` hacen
falta su resultado y su visto bueno al aspecto (criterio de aceptación
«se enseña el resultado real… y lo revisa el humano»).

## Cambios requeridos

Ninguno.

## Para cerrar

1. La M1, con la muestra o con datos reales de la BBDD local, y su resultado
   anotado en `progress/`.
2. El `done` del líder después de la M1, con `init.sh` en verde.
