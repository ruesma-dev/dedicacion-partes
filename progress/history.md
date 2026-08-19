<!-- progress/history.md -->
# Histórico del arnés

Registro append-only. El líder mueve aquí el resumen de cada feature terminada.

---

## 2026-08-19 · F-001 · Primera suite de tests de `dedicacion-api`: la regla del 100 %

Rama `feature/F-001-tests-estados-api` · `sdd: false` · rigor `estandar` ·
**APROBADO** por el reviewer · 5 commits locales (`5a1b54d` … `12be01e`).

**Qué cambió.** Tres ficheros nuevos bajo `services/dedicacion-api/tests/`
(`__init__.py`, `conftest.py` con el `sys.path.insert` en un único sitio, y
`test_estados.py` con 21 tests). **Cero ficheros de producción modificados**:
`domain/estados.py` se leyó, no se tocó.

**Qué se verificó (salida real).** `bash harness/init.sh` → ENTORNO LISTO,
exit 0, con `[OK] servicio api (services/dedicacion-api): pytest en verde` —
antes de F-001 esa línea era un AVISO de «sin directorio de tests». Suite: 21
passed en 0,10 s; `domain/estados.py` al 100 % (26/26 sentencias). Fase RED:
7 roturas deliberadas de `estados.py` en copia aislada, 7 cazadas; el
reviewer la reprodujo con los mutantes del generador real (16 muertos de 17,
y el único superviviente es el mutante equivalente que el implementer ya
había identificado y justificado por escrito). ruff sigue en los mismos 164
avisos de deuda previa; los ficheros nuevos salen limpios.

**Las dos puertas nuevas, verificadas de forma independiente.** Era la
primera vez que se ejercían en este repositorio. La puerta de cobertura salió
`N/A (F-001 no cambia líneas Python de producción frente a dev)` y la campaña
de mutación generó 0 mutantes. El reviewer no se fio del informe: leyó
`harness/alcance.py` (`DIRECTORIOS_EXCLUIDOS` incluye `tests` **como segmento
de ruta a cualquier profundidad**, pensado para monorepos) y
`harness/cobertura.py` (el `N/A` es una rama declarada que imprime su motivo,
distinta de aprobar en silencio), recalculó el alcance y añadió una prueba de
control. Conclusión: comportamiento correcto por diseño, no una puerta
esquivada. **La puerta de cobertura sigue sin estrenarse con datos reales**:
lo hará la primera feature que toque producción (F-002 o F-003).

**Decisiones tomadas.** `conftest.py` en vez de repetir el `sys.path.insert`
en cada test como hace el transfer. Dos casos de épsilon de más (99,995 % y
100,005 %) además de los que pedía el criterio: son los únicos que distinguen
`<=` de `<`, y así quedó demostrado al romper el código. Se cubrió también
`calcular_desviacion`, que el criterio no nombraba. Los 11 avisos de ruff que
introdujeron los ficheros nuevos se corrigieron en el acto (`7760080`), para
que la deuda previa no creciera con esta feature.

**Deuda que deja apuntada (declarada por ambos subagentes, no corregida).**
F-001 amplía de 4 a 6 los ficheros de cobertura versionados: añade
`services/dedicacion-api/.coverage` y `coverage.json`, siguiendo el
precedente de la raíz y del transfer. Ninguno está en `.gitignore`, así que
el portero ensucia `git status` cada vez que se ejecuta. Lo correcto es lo
contrario: ignorarlos y sacarlos del índice con `git rm --cached`. Como el
`.gitignore` lo deja el instalador del arnés, por la regla de propagación el
arreglo va también a `arnes-base`. Convertido en **F-009**.

**Propuestas de automejora del reviewer, pendientes de decisión del humano.**
(1) `CHECKPOINTS.md` C4 bis no dice qué hacer cuando *toda* la feature cae en
`DIRECTORIOS_EXCLUIDOS` (cobertura N/A y mutación 0 a la vez): propone hacer
regla explícita la mutación sobre el fichero que los tests nuevos cubren.
(2) `.claude/agents/reviewer.md`: cuando el alcance salga vacío, añadir como
paso el control positivo (generar mutantes del fichero de producción cubierto
y ejecutarlos contra la suite). (3) La caché del portero puede enseñar un
`[OK]` de un servicio sin que la suite se haya ejecutado en esa sesión: el
protocolo del reviewer debería obligar a lanzarla a mano. Las tres valen para
cualquier proyecto ⇒ van a `arnes-base`. Convertidas en **F-010**.

**Corrección menor anotada.** El «Cómo reproducirlo» del informe del
implementer manda `ruff` con el intérprete del venv del api, donde ruff no
está instalado. Con el de la raíz funciona.

Informes: `progress/impl_F-001.md`, `progress/review_F-001.md`,
`progress/mutacion_F-001.md`.
