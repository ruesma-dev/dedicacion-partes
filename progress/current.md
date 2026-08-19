<!-- progress/current.md -->
# Trabajo en curso

**F-009 · Higiene: los artefactos de cobertura no se versionan**
Rama `feature/F-009-higiene-coverage-gitignore` · `sdd: false` · rigor `estandar`
Estado: **lanzada el 2026-08-19. Implementer en marcha.**

> Esta rama contiene únicamente F-009. **F-002** y **F-003** viven en sus
> propias ramas y su estado se describe en el `progress/current.md` de cada
> una.

## Por qué se hace ahora

Seis ficheros generados están versionados: `.coverage` y `coverage.json` de la
raíz, de `dedicacion-api` y de `dedicacion-transfer`. `bash harness/init.sh`
los reescribe **en cada ejecución**, así que el árbol se ensucia solo.

No es cosmético. En una sola tarde ha estorbado **tres veces**:

1. En F-001 hubo que decidir si commitearlos o no, y se acabaron añadiendo dos
   más (los del api) «por seguir el precedente».
2. En F-002, la campaña de mutación paralela —que exige árbol limpio— tuvo que
   lanzarse con `--workers 1`.
3. En F-003, lo mismo, y además el reviewer interpretó el árbol sucio como un
   posible rojo del portero.

El reviewer de F-002 lo dejó escrito en `progress/review_F-002_fase1.md` §10:
`bash harness/init.sh` es obligatorio para el reviewer **y** ensucia el árbol,
así que `harness/mutacion_paralela.py` nunca puede usarse. Cerrar F-009 mata
el problema de raíz.

## Alcance

- `.coverage` y `coverage.json` (raíz y los tres servicios) al `.gitignore` y
  **fuera del índice** con `git rm --cached`.
- **Propagación obligatoria a `arnes-base`**: el `.gitignore` que produce este
  comportamiento lo instala el arnés, así que el mismo arreglo vale para
  cualquier repositorio. Va en el mismo trabajo, no después
  (`CLAUDE.md`, regla de propagación).
- Lo que **no** cambia: la puerta de cobertura y la caché de suites de
  `init.sh` leen esos ficheros **del disco**, no de git. Deben seguir
  funcionando igual.

## Verificaciones `MANUAL (humano)` pendientes

**Ninguna.** F-009 no toca Sigrid, ni la BBDD, ni ningún `.env`. Todo lo que
hay que comprobar lo comprueba el portero y los comandos de git.

## ⚠ Aviso para el merge

Las ramas de **F-002** y **F-003** todavía tienen esos seis ficheros
trackeados y los modifican. Al mergear F-009 a `dev` y luego mergear esas dos,
git puede **reintroducirlos**. Tras cada merge hay que comprobar
`git ls-files | grep coverage` y que siga sin devolver nada.

## Estado de las demás features

- **F-001** · `done`, mergeada a `dev` y publicada en GitHub.
- **F-002** · `in_progress` en su rama. Fase 1 (T1–T5) **aprobada**; spec v2
  escrita con D1 y D2 cerradas. Pendiente la Fase 2: la **regla de capacidad
  del 100 %**. Es lo siguiente que se implementa cuando F-009 cierre.
- **F-003** · `in_progress` en su rama, implementada y **APROBADA** por el
  reviewer. **No pasa a `done` hasta que el humano ejecute T8** contra su base
  real (los comandos están en el `current.md` de esa rama).
- **F-010** y **F-011** · `pending`.

## Hechos comprobados que no conviene volver a descubrir

- **Este sistema NUNCA ha escrito en Sigrid** (consulta C6, 2026-08-19: 0
  filas). Lo de julio fueron cinco preflights en modo pruebas.
- `ruff` **no está instalado** en el venv de `dedicacion-api`: para lintar ese
  servicio hay que usar el intérprete de la raíz.
