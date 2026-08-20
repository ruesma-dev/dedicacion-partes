<!-- progress/current.md -->
# Trabajo en curso

**F-013 · Una línea sin partida no se escribe en silencio**
Rama `feature/F-013-linea-sin-partida-confirma` · `sdd: false` · rigor `critico`
Estado: **lanzada el 2026-08-20.** No lleva spec: mandan sus `acceptance`.

## Qué se cambia y por qué

Hoy, cuando el casado de partida falla en obra normal,
`registro_pipeline.py` hace:

```python
a.paride = 0
a.aviso = "partida no localizada para la categoría/nombre: se imputa sin partida (editable)"
```

Es decir: **avisa, pero escribe igual**. En el preflight real de julio 2026
eso eran **2.132 € de una jefa de obra** (Arriaza, obra 0025) colgando de la
obra sin imputar a ninguna partida.

**Decisión del humano (2026-08-20):** debe **avisar y esperar confirmación**,
igual que la sobrecarga del 100 % que introdujo F-002.

**El mecanismo ya existe**: la Regla B de F-002 emite un `Conflicto` con
motivo propio que viaja al front. Esto es aplicar ese patrón a un tercer
caso, no inventar nada — y por eso **no toca `dedicacion-api` ni
`dedicacion-front`**.

## Por qué es feature aparte y no una tarea de F-002

F-002 está `blocked` por motivos ajenos (Administración) y sus fases 1 y 2
están **aprobadas y mergeadas a `dev`**. Meterle un cambio de comportamiento
nuevo la reabriría sin necesidad.

## Verificaciones `MANUAL (humano)` pendientes

**Ninguna de F-013 mientras no se escriba en Sigrid.** Los tests son offline
con las fixtures de `services/dedicacion-transfer/tests/conftest.py`. Si en
algún momento se quisiera comprobar contra Sigrid real, sería una acción
aparte y con autorización expresa.

## Otras features (ninguna avanza sin el humano)

- **F-002** · `blocked`. Falta avisar a Administración de las cuatro partidas
  duplicadas de POSTV2 (`656`, `664`, `680`, `693`) y decidir quién firma la
  procedencia de las reglas.
- **F-008** · `blocked`. Fases 1–6 **aprobadas** en su rama, sin mergear. La
  **fase 7 es del humano** (crear recursos, imágenes, Easy Auth), con sus
  comandos en `specs/F-008-infra-azure/tasks.md` e `infra/README_dedicacion.md`.
  Falta **D3**: la lista del grupo `dedicacion-portal-users`.
- **F-004** · `done` y aprobada en su rama `feature/F-004-readme-monorepo`,
  **sin mergear a `dev`**. (En ESTA rama `features.json` la muestra como
  `pending`: su `done` vive en su propia rama.)

## ⚠ ACCIÓN PENDIENTE EN PRODUCCIÓN (Sigrid)

Sigue viva la fila de prueba de T14: `hmores.ide = 403039`, parte
`PT26/00296`, obra `0404`, marca `PRUEBA-PORC`. El humano quiere verla en la
pantalla del ERP antes de borrarla. **Es precondición de la fase 7 de F-008.**

```bash
cd services/dedicacion-transfer
.venv/Scripts/python prueba_escritura_porcentajes.py limpiar --confirmar --ano 2026 --mes 7
```

## Hechos comprobados que no conviene volver a descubrir

- **La escritura en Sigrid funciona** (T14, 2026-08-20). Antes de esa fecha el
  sistema **nunca** había escrito en el ERP.
- El api expone su salud en **`/api/v1/health`**, no en `/health`.
- `ruff` **no está instalado** en el venv de `dedicacion-api`.
- **Dos defectos del arnés detectados el 2026-08-20** (anotados en
  `progress/history.md` para `arnes-base`): `init.sh` confunde «no hay tests»
  (pytest código 5) con «los tests fallan», y **la caché de suites cruza
  ramas**, de modo que el portero puede dar `[OK]` por una suite ejecutada en
  otra rama. Si aparece un rojo raro del front, mira si hay un `tests/` con
  solo `__pycache__` dentro.
