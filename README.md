<!-- README.md -->
# dedicación · monorepo `porcentajes`

Registra el **porcentaje de dedicación mensual de cada trabajador a cada
obra** y lo lleva a los partes de trabajo de Sigrid. Sustituye a la hoja
`Plantilla_Dedicacion_Ruesma_vXX.xlsx` que Administración mantenía a mano.
Solo entra el personal que en Sigrid cobra **por mes** (código de hora `M*`);
el que va por horas se registra en el otro sistema, `partes`, contra las
mismas tablas de Sigrid pero con su propio espacio de `synckey`.

El dato viaja siempre en la misma dirección: alguien captura el cuadrante del
mes en el **front**, la **api** lo persiste en PostgreSQL y es la dueña del
dato, y cuando se decide registrar, la api llama al **transfer**, que es el
único componente del sistema con credencial de escritura contra Sigrid. Los
maestros (empleados y obras) van al revés y en solo lectura: la api los
sincroniza desde Sigrid a través de la pasarela `sigrid-api`.

```
navegador
    │
    ▼
services/dedicacion-front    (8080)   SPA Jinja2 + JS vanilla, sin lógica de negocio
    │  proxy /api/*  (+ cabecera X-Usuario desde Easy Auth)
    ▼
services/dedicacion-api      (8090)   FastAPI + PostgreSQL `dedicacion`
    │                                   │
    │  HTTP preflight / ejecutar        └──▶ sigrid-api   (LECTURA de maestros)
    ▼
services/dedicacion-transfer (8006) ───────▶ sigrid-api   (ESCRITURA, base `ruesma`)
                                                  └──▶ Sigrid (SQL Server on-prem)
```

| Servicio | Puerto | Qué hace | Detalle |
|---|---|---|---|
| `dedicacion-front` | 8080 | Captura rápida del cuadrante y proxy hacia la api. **No decide nada de negocio.** | [README](services/dedicacion-front/README.md) |
| `dedicacion-api` | 8090 | Dueño del dato: maestros sincronizados, cuadrante por periodo, regla del 100 %, export a Excel y orquestación del registro. | [README](services/dedicacion-api/README.md) |
| `dedicacion-transfer` | 8006 | La única pluma: contrato `preflight` / `ejecutar`, idempotencia por `synckey`, reglas P1-P5 y modo pruebas. | [README](services/dedicacion-transfer/README.md) |

Las **reglas de negocio no se enuncian aquí ni en los README de servicio**: su
única fuente normativa es [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
§ Semántica de dominio imprescindible.

## Arranque local

### Requisitos previos

- **Python 3.12** y, para cada servicio, **su propio `.venv`** en
  `services/<servicio>/.venv` (`pip install -r requirements.txt` desde la
  carpeta del servicio).
- **PostgreSQL escuchando en el 5432.** La api crea la base `dedicacion` al
  arrancar si no existe, pero el servidor tiene que estar levantado.
- Los **tres `.env`**, copiados cada uno de su `.env.example` y rellenados.
  **No hay `.env` en la raíz**: cada servicio lee el de su propia carpeta.

```bash
cp services/dedicacion-transfer/.env.example services/dedicacion-transfer/.env
cp services/dedicacion-api/.env.example       services/dedicacion-api/.env
cp services/dedicacion-front/.env.example     services/dedicacion-front/.env
```

Qué hay que rellenar (los `.env.example` traen el resto ya puesto):

- `dedicacion-transfer` y `dedicacion-api`: `SIGRID_API_BASE_URL` y
  `SIGRID_API_FUNCTION_KEY` de la pasarela `sigrid-api`.
- `dedicacion-api`: `PG_PASSWORD` y `PG_ADMIN_PASSWORD` de PostgreSQL.
- `dedicacion-front`: nada obligatorio en local.

Los valores no se piden por chat ni se escriben en ningún fichero del
repositorio: se copian del gestor de secretos.

### El orden importa

Cada servicio llama al anterior, así que se levantan de abajo arriba, **cada
uno desde su propia carpeta y con su propio intérprete**, en tres terminales:

```bash
cd services/dedicacion-transfer && .venv/Scripts/python main.py   # 8006
cd services/dedicacion-api      && .venv/Scripts/python main.py   # 8090
cd services/dedicacion-front    && .venv/Scripts/python main.py   # 8080
```

La api busca al transfer en `http://127.0.0.1:8006` por defecto
(`transfer_base_url`, `services/dedicacion-api/config/settings.py:59`) y el
front busca a la api en `http://127.0.0.1:8090` (`API_BASE_URL`). Si el
transfer no está arriba, la api arranca igual, pero el registro en Sigrid
falla al ejecutarse.

**En la api se arranca siempre por `main.py`**, nunca apuntando `uvicorn` a la
app: la puesta al día del esquema ocurre en `main.py` y solo ahí. El porqué
está en el [README de la api](services/dedicacion-api/README.md).

### Comprobar que funciona

| Qué | Dónde |
|---|---|
| transfer | `http://127.0.0.1:8006/health` |
| api | `http://127.0.0.1:8090/api/v1/health` |
| front | `http://localhost:8080/health` |

Ojo con la de la api: es **`/api/v1/health`**, no `/health` — todas sus rutas
cuelgan del prefijo `/api/v1`. Confundirlas devuelve un 404 que parece un
servicio caído y no lo es.

La prueba de verdad es abrir **`http://localhost:8080`**: con el sistema
entero arriba, el front sirve el cuadrante real leído de PostgreSQL, con sus
trabajadores, sus líneas y los chips de estado. Si la página carga pero sale
vacía o con error, el que falla es el eslabón siguiente, no el front.

## Qué NO hacer

- **El transfer arranca en modo pruebas y ahí se queda.**
  `OBRA_PRUEBAS_FORZAR=true` desvía TODA escritura a la obra de pruebas
  `0404`, marcada `PRUEBA-PORC`. Salir de ese modo —o lanzar
  `prueba_escritura_porcentajes.py ejecutar --confirmar` fuera de él— exige
  **autorización expresa del humano para esa acción concreta**. Ningún agente
  lo hace por su cuenta.
- **Contra Sigrid, solo lectura**, salvo `dedicacion-transfer`. La api no
  tiene credencial de escritura y no debe tenerla. La escritura va **siempre**
  contra la base `ruesma`; `ruesma_rep` es una réplica que no admite escritura.
- **Nunca commitear un `.env`.** Ni claves, ni cadenas de conexión, ni IDs de
  suscripción o tenant, ni IPs internas, en ningún fichero del repositorio
  —tampoco en `specs/`, `docs/` o `progress/`—. El historial de git no suelta
  lo que entra, y da igual que el repositorio sea privado.
- **La lógica no se copia entre servicios.** Si dos la necesitan, se decide
  dónde vive antes de escribirla. El front, en particular, no calcula nada que
  decida qué se registra en Sigrid.

## Dónde está cada cosa

| Carpeta | Qué contiene |
|---|---|
| `services/` | Los tres servicios, independientes: cada uno con su `main.py`, su `config/`, su `requirements.txt` y su `.venv`. |
| `docs/` | [`ARCHITECTURE.md`](docs/ARCHITECTURE.md) (normativo: capas, reglas P1-P5, accesos externos) y [`CONVENTIONS.md`](docs/CONVENTIONS.md) (estilo, SQL, tests, git). |
| `docs/referencia/` | Documentación de negocio y de sistemas origen que llega de fuera, siempre en Markdown. Punteros a `azure-apps/`, no copias. |
| `specs/` | Especificaciones SDD, una carpeta por feature. |
| `progress/` | Memoria del arnés: `current.md` (trabajo en curso), `history.md` e informes por subagente. |
| `harness/` | El arnés de agentes: `init.sh` (portero), `features.json`, `rigor.json`. |
| `scripts/` | Utilidades sueltas de entorno. |
| `tests/` | Suite de la raíz (la del arnés). Los tests de cada servicio viven en su carpeta. |

Qué leer según lo que busques:

- **«¿por qué el código hace esto?»** → [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
  Es la única fuente normativa de las reglas de dominio.
- **«¿cómo se escribe aquí?»** → [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md).
- **«¿qué falta por hacer?»** → [`BACKLOG.md`](BACKLOG.md), generado desde
  `harness/features.json` por `harness/backlog.py`. No se edita a mano.
- **«¿cómo trabajan los agentes?»** → [`CLAUDE.md`](CLAUDE.md) y
  [`CHECKPOINTS.md`](CHECKPOINTS.md).
- **«¿qué hay en Sigrid?»** → el repositorio vecino `azure-apps`:
  `sigrid_api.md` (la pasarela, sus topes reales) y `sigrid_tablas.md` (el
  diccionario de tablas). No se duplican aquí, se enlazan.

Antes de empezar cualquier trabajo: `bash harness/init.sh`. Si no termina en
verde, no se trabaja.

## Estado del proyecto

Al **2026-08-20**, sin adornos:

- **Funciona en local, entero.** El 2026-08-20 se levantaron los tres
  servicios a la vez por primera vez y el front sirvió el cuadrante real
  leído de PostgreSQL. Los comandos de arriba son los que se usaron.
- **La escritura en Sigrid está probada de verdad**, una sola vez: una línea
  real escrita en la **obra de pruebas** `0404`, marcada `PRUEBA-PORC`, con su
  parte creado por el sistema. Antes de esa fecha el sistema nunca había
  escrito en el ERP. Sigue en modo pruebas.
- **No hay nada desplegado en Azure.** El trabajo de infraestructura está en
  curso en su propia rama, sin integrar: en esta rama no existen ni `infra/`
  ni los documentos de despliegue. Cuando exista despliegue, tendrá su
  documento en `azure-apps/`.
- **La base PostgreSQL es hoy local** (`PG_HOST=localhost`). El servidor de
  destino al desplegar está sin decidir por escrito.

Lo que queda abierto, con su estado y su prioridad, está en
[`BACKLOG.md`](BACKLOG.md); lo que está a medias ahora mismo, en
`progress/current.md`.
