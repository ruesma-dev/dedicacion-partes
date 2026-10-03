<!-- progress/review_despliegue_20261001.md -->
Revisión completa (pasada 1) de `ffed068..39b88c5` (`d449a58` hotfix, `fb240be` despliegue, `39b88c5` merge)

# Review · despliegue del 2026-10-01 (sin feature propia)

**Veredicto: CHANGES_REQUESTED**

**Rigor:** sin feature; por analogía `documental` (infra y docs, sin código
de producción): sin fase RED, cobertura ni mutación. Consta a propósito.

## 1 · El hotfix `d449a58`: correcto, causa raíz demostrada

- **La causa raíz es cierta.** Reproducido en PowerShell 5.1.26100.9549:
  asignar `$inventario = … | ConvertFrom-Json` deja `$INVENTARIO` como
  `PSCustomObject`. Sin cast, `WriteAllText` da literalmente «No se encuentra
  ninguna sobrecarga para "WriteAllText" y el número de argumentos "3"» (el
  error del 2026-08-20); con `[string]` y el `imagenes.json` real, el objeto
  pasa a un texto de 418 caracteres y da `PathTooLongException` (el de hoy).
- **El arreglo es mínimo y suficiente**: `$datosInventario` en las tres
  líneas que la usaban.
- **Otras colisiones por mayúsculas en `infra/*.ps1`** (barrido de todos los
  `$nombre`, por fichero y entre ficheros que comparten sesión):
  - `redeploy_dedicacion.ps1:102` `$img` frente a `$IMG` (mapa de `00_vars`).
    **Latente, no activa**: se asigna después del último uso de `$IMG`,
    incluido el indirecto vía `Imagen`/`Tag-Publicado` (ámbito dinámico).
    Mover ese bucle o añadir un `Imagen` detrás la activaría (O1).
  - `$inventario`, `$app`, `$fqdn` de `00_capps_vars:65,82-83` frente a
    `$INVENTARIO`/`$APP`/`$FQDN`: **inocuas**, son locales de función.
- **Comentario**: veraz en la causa. «Los casts se quedan: no estorban» es
  inexacto (O2): con un objeto que dé un texto corto, el cast **escribe un
  fichero basura en el directorio actual en vez de fallar**. Lo comprobé sin
  querer: mi reproducción creó `@{a=1; servicios=}` en la raíz del repo
  (borrado; árbol limpio después).

## 2 · `infra/imagenes.json`: los digests son FALSOS (bloqueante)

Leído del ACR y de los Container Apps (solo lectura):

| Servicio | Tag (JSON = desplegado) | Digest en el JSON | Digest real del tag |
|---|---|---|---|
| transfer | r20261001-1805 ✔ | `cf872c89…13e3f` | `019ef7ea…2774a` |
| api | r20261001-1807 ✔ | `d5b4a18a…b84e` | `ef7de7a1…5a12b` |
| front | r20261001-1808 ✔ | `abd1b6f4…cec8f3` | `69a16432…aff9` |

Los tres digests del JSON son los de `r20260820-1625` (comprobado en el ACR).
El script actualiza `tag`, `publicado` y `nota`, **nunca `digest`**
(`build_images:126-133`); como el inventario no se había escrito nunca por
script, nadie lo vio. El fichero cuya razón de ser (R24) es decir «qué código
corre» afirma un digest que no es el de ese código. Revisiones
`…--r20261001180529` y `OBRA_PRUEBAS_FORZAR=false` confirmados en caliente.
JSON válido, `eol=lf`, sin secretos. Quedan en el ACR dos tags huérfanos del
transfer, `r20261001-1734` y `-1744` (intentos fallidos), sin rastro (O3).

## 3 · Documentación del modo real: quedan sitios que dicen «pruebas»

Bien: `CLAUDE.md`, `README.md` («Qué NO hacer»), `docs/ARCHITECTURE.md`,
`docs/INTEGRACION.md` (cabecera y §8 con el comando para volver) y
`azure-apps/dedicacion.md` (`6cfb59d`). `services/*/README.md`,
`CHECKPOINTS.md`, `.env.example` y `app.js` hablan del modo como regla o del
alta, no del estado: correctos.

**Siguen afirmando, en presente, que el desplegado está en pruebas:**
- `progress/current.md:71-73` — «**El transfer sigue en modo pruebas.**», en
  «Lo que el sistema sabe hacer, comprobado». Es lo primero que lee cualquier
  agente: el riesgo principal que señalaba el líder, literal.
- `progress/current.md:38-39` — F-017 «probar … sobre la obra 0404» (hoy
  exige volver antes a pruebas) y F-018 «pasar a escritura real. Requiere…»
  (ya hecho).
- `infra/README_dedicacion.md:144-145` — «El transfer está en MODO PRUEBAS y
  esta feature termina así», en el runbook de despliegue.
- `infra/redeploy_dedicacion.ps1:114` — tras cada redeploy imprime «Y que
  SIGUE en modo pruebas (R9)»: quien vea `false` no sabrá si es lo esperado.
- `harness/features.json`/`BACKLOG.md`: F-018 conserva «**Hoy**
  OBRA_PRUEBAS_FORZAR=true desvia toda escritura» y luego dice lo contrario;
  F-017 dice «TODO se desvia a la obra de pruebas» y su primer `acceptance`
  exige comprobar en caliente que sigue en pruebas.

## 4 · `features.json` y `current.md` frente a la decisión del humano

La decisión está bien recogida (F-018, `current.md` §«DESPLEGADO EN MODO
REAL»): orden expresa, F-017/F-026/F-011 nombrados, incidente del transfer
viejo en real con la comprobación de que solo hubo preflights. Pero, además
de lo del punto 3, los `acceptance` de F-018 que la decisión dejó atrás
(«F-026 cerrada antes de quitar», «NO arranca hasta F-017», «camino previsto
-ModoProduccion -Confirmar», «Plan de reversión ANTES») siguen como si nada:
F-018 es inaprobable por criterios que ya no pueden cumplirse.

## 5 · `bash harness/init.sh`

Verde: 355 passed, 1 skipped; `ENTORNO LISTO`. Ejecutado en la rama actual
`feature/F-025-…`, que contiene `39b88c5` (solo difiere `progress/current.md`).

## Checkpoints

- C1 [x] init.sh en verde · [x] ficheros del arnés presentes.
- C2 [x] ninguna `in_progress` · N/A rama `feature/F-XXX`: trabajo `chore/`
  sin feature, ya mergeado · [ ] **`current.md` coherente**: afirma modo
  pruebas (`:71`) y planifica F-017/F-018 como antes del cambio.
- C3 N/A hexagonal: sin código de servicio · [x] ruta en primera línea · [x]
  sin secretos ni debug (barrido del diff: sin GUID, IP ni claves) · [x] el
  cambio de `OBRA_PRUEBAS_FORZAR` tiene decisión escrita del humano (F-018).
- C3 bis N/A: no entra documento externo. C4 ter N/A: no existe
  `harness/rutas_sensibles.json`.
- C4 N/A trazabilidad EARS: sin spec; infra solo verificable contra Azure, y
  verificado así (tags, revisiones, modo) · [ ] **el registro de lo
  desplegado es veraz**: digests falsos.
- C4 bis N/A: sin feature ni código de producción (rigor `documental`).
- C5 N/A `tasks.md`: sin spec · [x] árbol limpio · [ ] `features.json`
  refleja el estado real: F-017/F-018 contradictorias.

## Cambios requeridos

1. `infra/imagenes.json`: digests reales de la tabla del punto 2
   (`az acr repository show -n acralbaranesdev --image <repo>:<tag> --query
   digest -o tsv`).
2. `infra/build_images_dedicacion.ps1:126-133`: escribir también `digest`
   (leído del ACR tras el build) o, como mínimo, ponerlo a `null`; si no, cada
   build repite el defecto del punto 1.
3. `progress/current.md:71-73`: estado real (modo real desde el 2026-10-01;
   volver: `INTEGRACION.md` §8). `:38-39`: F-017 exige volver a pruebas antes
   (o decisión del humano); F-018, solo lo que queda.
4. `infra/README_dedicacion.md:144-145`: estado de hoy (real) frente a cómo
   termina un alta nueva (pruebas).
5. `infra/redeploy_dedicacion.ps1:114`: no afirmar «SIGUE en modo pruebas»;
   decir qué valor esperar (hoy `false`, ver §8).
6. `harness/features.json`: F-018 «Hoy …=true» → «Hasta el 2026-10-01…» y
   anotar (sin borrar) como superados por la decisión los `acceptance` 1-3, 5
   y 6. F-017: corregir la descripción y anotar que su primer `acceptance` hoy
   obliga a volver a pruebas (decide el humano). Regenerar `BACKLOG.md`.

## Observaciones no bloqueantes

- O1 `redeploy_dedicacion.ps1:102`: renombrar `$img` (p. ej. `$imagenActual`).
- O2 Los casts de `build_images:146` enmascaran el fallo: mejor una guarda
  `if ($INVENTARIO -isnot [string]) { throw … }` y corregir «no estorban».
- O3 Anotar los tags huérfanos `dedicacion-transfer:r20261001-1734` y `-1744`.
- O4 `README.md` §«Al 2026-08-20» mezcla «No hay nada desplegado en Azure»
  (ya falso) con la frase nueva del 2026-10-01.
- Automejora (propuesta, no aplicada) para `CHECKPOINTS.md` C2: «si el trabajo
  cambia un estado de producción, `grep` del estado anterior en todo el repo».
