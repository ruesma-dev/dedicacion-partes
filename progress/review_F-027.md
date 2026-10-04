<!-- progress/review_F-027.md -->
Revisión completa (pasada 1), diff `1f10ab0..f12d992` (alcance de la herramienta: `68e884e..HEAD`, misma producción)

# F-027 · Review — Deshacer solo lo propio

- **Veredicto: APPROVED**
- **Nivel de rigor:** `estandar`, declarado. Exige fase RED, cobertura ≥ 80 %
  de lo cambiado y mutación con supervivientes analizados. `sdd=false`: se
  valida contra los 7 `acceptance`.
- `bash harness/init.sh` (ejecutado por mí): **ENTORNO LISTO**, raíz 418
  passed / 1 skipped, servicios en verde, `PUERTA COBERTURA 100.0 % (33/33)`,
  `PUERTA TAMAÑO impl 211/220`, ruff 198 avisos (deuda previa, sin cambio).

## Lo pedido por el líder, punto a punto

1. **Regla A** (`use_cases.py:177-193`): solo se lee `ultimo_pendiente` (mayor
   id del trabajador en el periodo, de quien sea); si no es del usuario →
   `DeshacerAjeno` **antes** de validar, reemplazar, marcar o hacer commit.
   Nunca se deshace otro evento. El motivo nombra al autor y sale como
   `{"error": …}` con 409, igual que `NadaQueDeshacer` (`app.py:35`).
2. **`puede_deshacer`**: cuadrante (`autores_ultimo_pendiente`) y fila
   (`ObtenerFilaTrabajador`, que usan guardar, deshacer y las dos ramas de
   copiar) con la misma `deshacer_permitido`; `usuario` keyword obligatorio.
   **SQL** `… WHERE id IN (SELECT max(id) … WHERE periodo_id=:p AND deshecho
   IS false GROUP BY trabajador_ide)`: correcto (el `IN` por PK no necesita
   repetir el periodo; mismo orden que `ultimo_pendiente`, `ORDER BY id DESC`).
   **Reproducido por mí en SQLite en memoria** con el repositorio real y
   eventos intercalados: 10 `ana, pablo, eva(desh.), zoe(desh.)` → `pablo`;
   14 `pablo, ana(desh.)` → `pablo`; 16 solo deshecho → sin entrada; otro
   periodo con id mayor no contamina; `ultimo_pendiente` coincide en los tres.
3. **Normalización única**: `domain/deshacer.clave_usuario`
   (`strip().casefold()`), la única comparación de usuarios (grep). No usar
   `normalizar` es correcto: quita acentos y colapsa espacios interiores, y
   podría fundir dos UPN distintos. `obtener_usuario` (previo) solo transporta.
4. **Front**: botón (`app.js` ≈627) solo con `puede_deshacer` y periodo
   ABIERTO; Ctrl+Z (≈1279, ≈1300) llama a `deshacer()`, que pinta
   `toast(cuerpo.error)`; el proxy del front reenvía código y cuerpo. **El
   criterio 5 reescrito es correcto y mejor**: el original decía que Ctrl+Z
   dependía de `puede_deshacer`, falso ya antes de F-027; filtrarlo en el
   front lo dejaría mudo justo cuando hace falta el motivo. Ver O1.
5. **Tests anteriores**: `git diff 1f10ab0..HEAD -- '*tests*'` toca solo
   `test_f024_cuadrante_empresa`, `test_f025_cuadrante_postventa` y
   `test_f034_obras_siempre_ruesma` (+ el nuevo). Cotejado fila a fila con la
   tabla del informe: todo declarado, **ninguna aserción cambia**. El doble de
   F-024 queda más fiel (lista de eventos, deshace uno a uno, el dict de
   autores se queda con el último). Sin restos de `trabajadores_con_pendientes`.
6. **Mutación**: ver C4 bis. Además, 8 mutantes **a mano** sobre una copia en
   mi scratchpad (RM4, árbol real intacto), suite entera del api (535 tests):

   | Mutante (original → mutado) | Resultado |
   |---|---|
   | `deshacer.py` `usuario.strip().casefold()` → `usuario.casefold()` | muerto, 4 fallos |
   | `deshacer.py` `usuario.strip().casefold()` → `usuario.strip()` | muerto, 7 fallos |
   | `repositories.py` `func.max(EventoORM.id)` → `func.min(EventoORM.id)` | muerto, 1 fallo |
   | `repositories.py` quitar `.group_by(EventoORM.trabajador_ide)` | muerto, 1 fallo |
   | `use_cases.py` cuadrante `…ide), usuario` → `…ide), autores.get(…) or ''` | muerto, 5 fallos |
   | `use_cases.py` fila final de deshacer `usuario=usuario` → `usuario='x'` | muerto, 2 fallos |
   | `use_cases.py` motivo `{pendiente.usuario}` → `otro usuario` | muerto, 4 fallos |
   | `use_cases.py` comprobación de autor movida tras `reemplazar`+`marcar_deshecho` | muerto, 4 fallos (r1, r2 y HTTP) |

   Los de SQL solo los caza el test de la sentencia compilada; la semántica
   la cubre mi reproducción en SQLite (punto 2). Suficiente para `estandar`.
7. **Docs**: `ARCHITECTURE.md` regla 14 `#regla-deshacer` dice lo
   implementado y entra en las anclas de fuente única (`test_f002` en verde).
   `INTEGRACION.md` §5 y sus dos consecuencias (`local`/`desconocido`
   comparten identidad; lo guardado así no lo deshace nadie con Easy Auth)
   cuadran con `deps.obtener_usuario`, `.env.example` del front e
   `infra/create_front_dedicacion.ps1`. `azure-apps` `e4a304c`: copia literal,
   cabecera «sin desplegar», la anterior como «Versión anterior». Ver O2.
8. **Rastro**: `grep -n "Ninguna feature" progress/current.md` → vacío
   (exit 1); la sección F-027 es coherente con el estado.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros base presentes.
- **C2** [x] una sola `in_progress` · [x] rama `feature/F-027-…` · [x]
  `current.md` solo la sesión activa · [x] toda `done` en `history.md` (script).
- **C3** [x] hexagonal: `domain/deshacer.py` y `EventoPendiente` sin
  infraestructura, SQL solo en `infrastructure/db`, el 409 en el adaptador ·
  [x] primera línea con ruta · [x] sin prints, TODOs, secretos ni
  dependencias nuevas · [x] tres trampas: ni escala del porcentaje, ni
  postventa (el snapshot restaurado conserva `es_postventa`), ni Sigrid.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] cada `acceptance` con test, en verde (tabla abajo) · [x] sin red
  ni BBDD (sesión falsa, UoW en memoria, `TestClient`) · N/A MANUAL: nivel
  `estandar` no las exige y los criterios están cubiertos por tests (ver O3).
- **C4 bis** [x] `rigor` declarado · [x] **RED** con salida real T1-T4 y T8,
  más el RED semántico de `puede_deshacer` (firma nueva, semántica vieja) ·
  [x] **cobertura** `[OK] 100.0 %` · [x] **mutación recalculada**:
  `alcance_de_feature` → 8 ficheros, **117** líneas; `generar_mutantes` →
  **8** (2+3+0+1+0+1+1+0), como el informe · [x] **muertos comprobados**:
  «Tiempo total» 58.2 s < 60 s ⇒ **campaña reejecutada entera** (`--workers
  1`, salida en mi scratchpad): **8/8 muertos, 0 supervivientes, 0 timeouts,
  0 sin veredicto, 52.3 s**, mismos 8 mutantes y textos; `git status` limpio
  después · [x] coste por mutante 58.2×1/8 = 7.3 s · [x] sin «⚠ CAMPAÑA NO
  VÁLIDA», base en verde · [x] **RM1** SHA `ea95a29`; después solo cambian
  `features.json` y `progress/`: mismo alcance · [x] **RM2** base 8.5 s,
  media 7.3 s, 8×7.3≈58.2, W=1 · N/A **RM5**: nivel `estandar` y sin
  equivalentes declarados · [x] **RM6**: ninguna guarda quitada; los dos
  supervivientes previos se mataron **añadiendo** tests · N/A campaña manual
  (la automática dio 8) · [x] nada `PENDIENTE` · [x] «Evidencias» completa con
  W=1 · [x] ningún N/A sin motivo. **RM3**: ninguno de los 8 es equivalente.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** N/A `tasks.md` (`sdd=false`); commits `F-027 T1`…`T8` presentes ·
  [x] sin temporales ni sin trackear · [x] `features.json` en `in_progress`.

## Cobertura · criterio → test (`tests/test_f027_deshacer_propio.py`)

| Criterio | Tests |
|---|---|
| 1 · 409 que nombra al otro | `r1_no_deshago_lo_del_otro`, `r1_por_http_lo_del_otro_es_409…`, `r1_el_error_es_de_dominio…`, `r1_nada_que_deshacer…` |
| 2 · decisión A | `r2_el_otro_cambia_despues_y_ya_no_puedo`, `r2_por_http_el_otro_cambia_despues` |
| 3 · `puede_deshacer` | `r3_…_en_el_cuadrante` (4 usuarios), `r3_…_en_la_fila`, `r3_por_http_…`, `r3_autores_del_ultimo_pendiente…`, `r3_ultimo_pendiente_trae_su_autor` |
| 4 · mayúsculas y extremos | `r4_mismo_usuario…`, `r4_otro_usuario_o_nada_pendiente`, `r4_clave_usuario…`, `r4_deshago_lo_mio_con_otras_mayusculas…` |
| 5 · front no decide | verificación de código (punto 4) + `r1_por_http_…` (`{"error"}`) |
| 6 · dos usuarios + tabla | los anteriores (Ana/Pablo) + tabla cotejada (punto 5) |
| 7 · review + init.sh | este informe; init.sh en verde |

## Observaciones (no bloquean; acción concreta para el líder)

- **O1 · El criterio 5 cambió después de la PARADA 1.** Correcto en el fondo,
  pero el humano aprobó otro texto: citarlo en el resumen de la PARADA 2.
- **O2 · Enlace roto en `azure-apps/dedicacion.md:287`**: único enlace
  Markdown del documento, apunta a `ARCHITECTURE.md#regla-deshacer`, que en
  `azure-apps` no existe. Las demás reglas se citan como texto (líneas 246,
  439, 450). Pasarlo a texto en `azure-apps` (fuera de esta rama).
- **O3 · Comprobación tras desplegar**: los pasos están en `impl_F-027.md`
  § «Pendiente para el líder»; `current.md` solo dice «se puede mirar con dos
  personas». Al cerrar, llevar esos pasos a `history.md` o al despliegue.
- Previo a F-027 y fuera de alcance: sin bloqueo de fila entre leer el último
  pendiente y restaurar; dos peticiones simultáneas siguen siendo posibles.

## Cambios requeridos

Ninguno.
