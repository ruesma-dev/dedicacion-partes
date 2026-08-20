<!-- progress/current.md -->
# Trabajo en curso

**F-002 · en review de cierre.** Ninguna otra feature en ejecución. Rama
`dev`, con **todo el trabajo aprobado ya integrado**: F-001, F-003, F-004,
F-009, F-013 y las fases 1–6 de F-008.

## Estado del backlog (12 features)

| Estado | Features |
|---|---|
| `done` | F-001, F-003, F-004, F-009, F-013 |
| `in_progress` | **F-002** — review de cierre en curso |
| `blocked` | **F-008** — esperando la fase 7, que es del humano |
| `pending` | F-005, F-006, F-011, F-012, F-014 |

Retiradas el 2026-08-20 por decisión del humano: **F-007** y **F-010**, que se
hacen en `arnes-base`. Su razonamiento está en `progress/history.md`.

## ⚠ Lo que espera al humano

### 1 · La fase 7 de F-008 — crear la infraestructura en Azure

Fases 1–6 **implementadas y aprobadas**. Lo que queda **crea recursos, gasta
dinero y toca la suscripción**: ningún agente lo ejecuta. Comandos con su
resultado esperado en `specs/F-008-infra-azure/tasks.md` fase 7 y en
`infra/README_dedicacion.md`.

Orden: `fase1_infra_dedicacion.ps1` → `crear_base_dedicacion.ps1` →
`add_secrets_dedicacion.ps1` → `build_images_dedicacion.ps1` → los tres
`create_*_dedicacion.ps1` → `setup_front_easyauth.ps1`.

**Falta decidir D3**: la lista de personas del grupo
`dedicacion-portal-users`, necesaria para Easy Auth (T26).

**Y D5, que no bloquea pero conviene antes de que el entorno esté vivo**:
pedir a `sigrid-api` una function key de **solo lectura** para la api. Hoy api
y transfer comparten la misma, y lo único que impide que la api escriba es que
su código no tiene rutas de escritura.

> Al pegar la salida real de `az` en `progress/`: usa marcadores
> (`<SUSCRIPCION>`, `<OBJECT-ID>`). El guardián de secretos ya vigila ese
> directorio, pero es la red, no la primera línea.

### 2 · F-014, cuando toque (prioridad 20)

Sigue viva en Sigrid la fila de la primera escritura real:
`hmores.ide = 403039`, `synckey 'porcentajes:77'`, marca `PRUEBA-PORC`, en el
parte `PT26/00296` (`hmo.ide = 2820419`) de la obra de pruebas `0404`.

```bash
cd services/dedicacion-transfer
.venv/Scripts/python prueba_escritura_porcentajes.py limpiar --confirmar --ano 2026 --mes 7
```

**Ojo con el orden**: probar el registro desde Azure escribirá **más** líneas
`PRUEBA-PORC` en la misma obra y mes, indistinguibles de esa salvo por su
`ide`. Si se va a desplegar antes, conviene limpiar primero o asumir que habrá
que distinguirlas a mano.

F-014 recoge también el aviso a Administración de las cuatro partidas
duplicadas de POSTV2 (`656`, `664`, `680`, `693`) y quién firma la procedencia
de las reglas P4/P5.

## Lo que el sistema sabe hacer hoy, comprobado

- **Corre entero en local**: transfer 8006 → api 8090 → front 8080, cada uno
  desde su carpeta con su venv. El README de la raíz lo documenta.
- **Escribe en Sigrid de verdad** (T14, 2026-08-20): crea el parte si no
  existe e inserta la línea con su `synckey`. Antes de esa fecha **nunca**
  había escrito en el ERP.
- **Avisa y espera confirmación** en tres casos distintos, cada uno con su
  clave: pisado de una línea existente, sobrecarga del 100 % del trabajador
  (F-002) y línea sin partida casada (F-013).

## Hechos que no conviene volver a descubrir

- El api expone su salud en **`/api/v1/health`**, no en `/health`.
- `ruff` **no está instalado** en el venv de `dedicacion-api`: usar el
  intérprete de la raíz.
- **Dos defectos del arnés**, anotados en `history.md` para `arnes-base`:
  `init.sh` confunde «no hay tests» (pytest código 5) con «los tests fallan»,
  y **la caché de suites cruza ramas**, así que el portero puede dar `[OK]`
  por una suite ejecutada en otra rama. Si aparece un rojo raro del front,
  mira si hay un `services/dedicacion-front/tests/` con solo `__pycache__`.
- La fase `verificar` de `prueba_escritura_porcentajes.py` busca **sus
  propias** líneas de plantilla, no lo que escriba el sistema por su camino
  normal. Para comprobar una escritura real hay que leer por `synckey`.
