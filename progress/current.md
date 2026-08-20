<!-- progress/current.md -->
# Trabajo en curso

**F-004 · README del monorepo y arranque local en orden**
Rama `feature/F-004-readme-monorepo` · `sdd: false` · rigor `documental`
Estado: **lanzada el 2026-08-20.** No lleva spec: mandan sus `acceptance`.

> Se lanza ahora a propósito: el 2026-08-20 se levantó el sistema entero en
> local por primera vez y se verificó cada paso, así que el README se escribe
> con hechos comprobados y no con suposiciones.

## Lo que ya está verificado y debe acabar en el README

```bash
cd services/dedicacion-transfer && .venv/Scripts/python main.py   # 8006
cd services/dedicacion-api      && .venv/Scripts/python main.py   # 8090
cd services/dedicacion-front    && .venv/Scripts/python main.py   # 8080
```

- El orden importa: cada servicio llama al anterior.
- Cada servicio arranca **desde su propia carpeta**, con **su** venv. No hay
  `.env` en la raíz.
- Requisitos previos: PostgreSQL escuchando en 5432 y los tres `.env`
  copiados de sus `.env.example`.
- El api apunta al transfer en `127.0.0.1:8006` por defecto
  (`config/settings.py:59`).
- Comprobaciones de salud: transfer `http://127.0.0.1:8006/health`;
  api **`http://127.0.0.1:8090/api/v1/health`** (¡no `/health`!);
  front `http://localhost:8080`.

## Otras features vivas (ninguna avanza sin el humano)

- **F-002** · `blocked`. Reglas implementadas y aprobadas, en `dev`. Falta:
  avisar a Administración de las cuatro partidas duplicadas de POSTV2
  (`656`, `664`, `680`, `693`); decidir quién firma la procedencia; e
  **implementar la regla nueva** que decidió el humano el 2026-08-20 — una
  línea sin partida (`paride = 0`) debe **avisar y esperar confirmación** en
  vez de escribirse en silencio.
- **F-008** · `blocked`. Fases 1–6 implementadas y **APROBADAS** en la rama
  `feature/F-008-infra-azure` (**sin mergear a `dev`**). La **fase 7 es del
  humano**: crear recursos, imágenes, Easy Auth y comprobaciones. Sus
  comandos están en `specs/F-008-infra-azure/tasks.md` fase 7 y en
  `infra/README_dedicacion.md`. Falta también **D3** (lista de personas del
  grupo `dedicacion-portal-users`).

## ⚠ ACCIÓN PENDIENTE EN PRODUCCIÓN (Sigrid)

**Hay una fila de prueba viva en Sigrid** desde el 2026-08-20 (T14 de F-002).
El humano quiere verla en la pantalla de partes del ERP antes de borrarla.

| Qué | Dónde |
|---|---|
| Línea | `hmores.ide = 403039`, `synckey = 'porcentajes:77'`, `tex = 'PRUEBA-PORC'` |
| Parte | `PT26/00296` (`hmo.ide = 2820419`), **creado por nosotros** |
| Obra | `0404 · CUBIERTA NAVE 14 - JOHN DEERE` (obra de pruebas) |

Borrado, cuando el humano dé el visto bueno:

```bash
cd services/dedicacion-transfer
.venv/Scripts/python prueba_escritura_porcentajes.py limpiar --confirmar --ano 2026 --mes 7
```

Borra **solo** lo marcado `PRUEBA-PORC`; la cabecera del parte quedaría creada
y vacía. **Es precondición de la fase 7 de F-008**: desplegar y probar
escribirá más líneas `PRUEBA-PORC` en la misma obra y mes, indistinguibles.

## Verificaciones `MANUAL (humano)` pendientes

**Ninguna de F-004**: es documentación y no toca Sigrid, ni la BBDD, ni
`.env`. Las de F-002 y F-008 están descritas arriba.

## Hechos comprobados que no conviene volver a descubrir

- **La escritura en Sigrid funciona** (T14, 2026-08-20). Antes de esa fecha
  el sistema **nunca** había escrito en el ERP.
- `ruff` **no está instalado** en el venv de `dedicacion-api`: usar el
  intérprete de la raíz para lintar ese servicio.
- El guardián de secretos vigila `infra/`, `specs/`, `docs/` **y
  `progress/`**. Verificado colando un `clientSecret` falso: el test falla.
- La fase `verificar` de `prueba_escritura_porcentajes.py` busca **sus
  propias** líneas de plantilla, no lo que escriba el sistema por su camino
  normal. Para comprobar una escritura real hay que leer por `synckey`.
