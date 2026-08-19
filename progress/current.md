<!-- progress/current.md -->
# Trabajo en curso

**Ninguna feature en ejecución.** F-001 se cerró el 2026-08-19 con veredicto
APROBADO; su resumen está en `progress/history.md`. La siguiente tarea por
prioridad es **F-002** (`critico`, `sdd: true`): fijar las reglas P4 y P5.

## Estado del repositorio

- `bash harness/init.sh` → ENTORNO LISTO. Avisos vivos: 164 de ruff (deuda
  previa) y `dedicacion-front` sin directorio de tests. El api ya no aparece
  en esa lista: F-001 le dio su primera suite (21 tests).
- Remoto `origin` → `ruesma-dev/dedicacion-partes` (GitHub). Publicados
  `main` y `dev`, ambos con upstream. La rama
  `feature/F-001-tests-estados-api` **no está subida** y **no está mergeada a
  `dev`**: pendiente de decisión del humano.

## Pendiente de decisión del humano

1. **Qué se hace con la rama de F-001**: merge a `dev` y/o push. Los agentes
   no hacen merge ni push por su cuenta.
2. **Validar la sección «Semántica de dominio imprescindible» de
   `docs/ARCHITECTURE.md`** (viene de la sesión de instalación): está escrita
   leyendo el código, no hablando con Administración.
3. **Las dos contradicciones ⚠ de ese documento** —destino e imputación de
   postventa, y qué cuenta como conflicto en obra normal— siguen abiertas y
   son **F-002**. Hasta resolverlas no se escribe en producción.
4. **Las tres automejoras del arnés** que propuso el reviewer de F-001 quedan
   registradas como **F-010**; la higiene de los artefactos de cobertura,
   como **F-009**. Ambas al final de la cola: confírmalas o reordénalas.

## Lo que sabemos y no conviene volver a descubrir

- **La puerta de cobertura sigue sin estrenarse con datos reales.** En F-001
  salió `N/A` legítimo porque la feature solo añadía ficheros bajo `tests/`,
  que `harness/alcance.py` excluye a propósito. La primera feature que toque
  producción (F-002 o F-003) será la que la pruebe de verdad.
- **`ruff` no está instalado en el venv de `dedicacion-api`**: para lintar
  ese servicio hay que usar el intérprete de la raíz.
- El portero ensucia `git status` en cada ejecución porque los ficheros de
  cobertura están versionados. Es F-009.
