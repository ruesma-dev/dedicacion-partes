<!-- progress/current.md -->
# Trabajo en curso

**Ninguna feature en ejecución.** Rama `dev`, con F-001, F-003 y F-009
mergeadas y cerradas. Queda **F-002 en `blocked`**, esperando tres
verificaciones que solo puede hacer el humano.

## El sistema se levantó en local y funciona (2026-08-20)

Primera vez que los tres servicios corren juntos desde el monorepo. Orden de
arranque, que importa porque cada uno llama al anterior:

```bash
cd services/dedicacion-transfer && .venv/Scripts/python main.py   # 8006
cd services/dedicacion-api      && .venv/Scripts/python main.py   # 8090
cd services/dedicacion-front    && .venv/Scripts/python main.py   # 8080
```

Comprobado con salida real:

- **transfer** `http://127.0.0.1:8006/health` → **200**.
- **api** `http://127.0.0.1:8090/api/v1/health` → **200**,
  `{"ok":true,"service":"dedicacion-api","sigrid_configurado":true}`.
  Ojo: el api **no** expone `/health` a secas, sino bajo `/api/v1`.
- **front** `http://localhost:8080` → **200**, y su proxy `/api/*` devuelve el
  cuadrante real leído de PostgreSQL.
- La pantalla carga con **176 trabajadores** en agosto 2026: 0 OK, 175 sin
  carga, 1 falta, 0 exceso.

Requisitos que ya estaban en su sitio: PostgreSQL escuchando en 5432, los tres
`.env` presentes, y el api apuntando al transfer en `127.0.0.1:8006` por
defecto (`config/settings.py:59`).

## F-002 · BLOQUEADA esperando al humano

Fases 1 y 2 **implementadas y aprobadas**. El código está en `dev`. Lo que
falta es la Fase 3, y ninguna de sus tareas la puede hacer un agente:

| Tarea | Qué es | Cómo se hace |
|---|---|---|
| **T6.1** | avisar a Administración de las **cuatro partidas duplicadas** de POSTV2 (`656`, `664`, `680`, `693`, colgando de la raíz en vez de `CD`) | es un aviso, no una acción técnica |
| **T6.2** | decidir **quién firma** la procedencia de las reglas | hoy dice `Confirmado por Pablo Gris (responsable del proyecto) el 2026-08-19 · verificado contra Sigrid`. El test no clava el interlocutor: cambiarlo no rompe nada |
| **T13** | casado real contra Sigrid **sin escribir** | `python prueba_escritura_porcentajes.py capitulos` / `estado` / `preflight` |
| **T14** | **escritura real** en la obra de pruebas `0404` | `ejecutar --confirmar` → `verificar` → `limpiar --confirmar`. **Exige autorización expresa del humano para esa acción concreta**; ningún agente la lanza |

> **T14 sería la primera escritura de este sistema en Sigrid.** Lo demuestra
> la consulta C6 del 2026-08-19: cero filas con `synckey LIKE 'porcentajes:%'`
> o marca `PRUEBA-PORC`. `OBRA_PRUEBAS_FORZAR` sigue en `true`.

## Por qué F-002 está `blocked` y no `in_progress`

Al mergear F-002 y F-003 quedaron **dos features `in_progress`** y
`harness/init.sh` solo admite una. El estado real de F-002 es que no puede
avanzar sin acción humana, que es justo lo que `blocked` describe. No es una
avería.

**Deuda de protocolo detectada aquí:** el arnés no tiene un estado para «hecho
y aprobado, esperando una verificación del humano». O se miente con
`in_progress` o se usa `blocked`, que suena a problema. Candidato a sumarse a
**F-010**.

## Estado del backlog

- **F-001** · `done` · primera suite de tests (`domain/estados.py` al 100 %).
- **F-002** · **`blocked`** · ver arriba.
- **F-003** · `done` · el ORM es la única fuente de verdad del esquema. **T8
  ejecutada el 2026-08-20**: dos arranques con `0 sentencias DDL aplicadas`,
  14 columnas y 30 filas antes y después, idénticas.
- **F-009** · `done` · los artefactos de cobertura ya no se versionan, y el
  arreglo está portado a `arnes-base` (`c5b258d`).
- **F-004 a F-008, F-010 a F-012** · `pending`.

## Hechos comprobados que no conviene volver a descubrir

- **Este sistema NUNCA ha escrito en Sigrid** (consulta C6). Lo de julio de
  2026 fueron cinco **preflights** en modo pruebas.
- El original `porcentajes-transfer` y el código migrado eran **byte a byte
  idénticos**: no se perdió lógica en la migración.
- `ruff` **no está instalado** en el venv de `dedicacion-api`: para lintar ese
  servicio hay que usar el intérprete de la raíz.
- El api expone su salud en **`/api/v1/health`**, no en `/health`.
