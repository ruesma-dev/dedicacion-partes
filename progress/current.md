<!-- progress/current.md -->
# Trabajo en curso

**Ninguna feature en ejecución.** El repositorio está recién montado: arnés
instalado, código migrado y proyecto definido. La siguiente sesión arranca el
circuito con **F-001**.

## Qué se hizo el 2026-08-19 (sesión de instalación)

Cuatro commits en `dev`, ninguno en `main`, sin `push` ni PR.

1. **Arnés base v1.5.2 instalado** con `instalar_arnes.ps1` desde
   `arnes-base`. Se borraron a mano las cachés que el instalador arrastra
   (`.pytest_cache/`, `__pycache__/`) y se copió su `.gitattributes`, que el
   instalador no copia. Los dos defectos son de `arnes-base` y están
   apuntados como **F-007**.
2. **Entorno**: `git init` con `main` y `dev`, `.gitignore` ampliado
   (`.venv/`, `.idea/`, `__pycache__/`), `requirements-dev.txt` con pytest,
   ruff, coverage y PyYAML instalados en el `.venv` de la raíz.
3. **Migración del código al monorepo.** Las tres carpetas sueltas
   `PycharmProjects/porcentajes-{api,front,transfer}` —con código
   funcionando y **sin git**— entraron como
   `services/dedicacion-{api,front,transfer}`. No entraron `.env`, `.venv`,
   `.idea`, `logs` ni cachés; cada servicio lleva su `.env.example` con los
   valores sensibles vaciados, y los `.env` reales están copiados en local
   (ignorados por git, comprobado con `git check-ignore`). Las carpetas de
   origen quedaron con `ARCHIVADO.md`: **no se trabaja en ellas**.
4. **Arnés adaptado**: todas las marcas `[ADAPTAR]` resueltas —`CLAUDE.md`,
   `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`, `docs/referencia/`,
   `CHECKPOINTS.md` C3, `harness/init.sh`, `harness/features.json`,
   `.claude/settings.json`— y backlog de 8 features escrito.

### Entorno de ejecución (importante para la próxima sesión)

- **Un venv por servicio**, creado en esta sesión con sus `requirements.txt`
  más pytest y coverage: `services/dedicacion-*/.venv`. Sin ellos, los tests
  del transfer no corren en el monorepo (`ModuleNotFoundError: httpx`) y el
  portero daba verde sin ejecutarlos.
- `harness/servicios.json` declara los tres servicios con su venv, así que
  `harness/init.sh` ejecuta la suite de cada uno con su intérprete. Hoy solo
  el transfer tiene tests (4, en verde); api y front salen como «NADIE está
  comprobando los tests», que es la verdad y lo que ataca F-001.
- `harness/init.sh` trae comprobaciones propias en la sección 9: ningún
  `.env` versionado, `config.yaml` de la API parseable y los tres
  `.env.example` presentes.
- Estado del portero al cerrar la sesión: **ENTORNO LISTO**. Avisos vivos:
  164 de ruff (deuda previa, no bloquea) y los dos servicios sin tests.

## Decisiones del humano en esta sesión

- Nombre de dominio: **«dedicación»**. Carpeta del monorepo: se queda
  **`porcentajes`**. `synckey`: **se congela** en `porcentajes:{id}`.
  Las tres constan en `docs/ARCHITECTURE.md` § «Decisiones tomadas».
- Nada desplegado en Azure: el sistema solo corre en local.

## Lo que queda pendiente de validar (no es trabajo, es confirmación)

- **La sección «Semántica de dominio imprescindible» de
  `docs/ARCHITECTURE.md`** está escrita leyendo el código y los README, no
  hablando con Administración. El humano debe validarla antes de que se use
  como norma para diseñar.
- **Dos contradicciones reales del repositorio**, marcadas ⚠ en ese
  documento y convertidas en **F-002**: el destino y la imputación de
  postventa (P5) y qué cuenta como conflicto en obra normal (P4). Hasta
  resolverlas no se escribe en producción.
- El orden fino del backlog es una propuesta.

## Corrección hecha en la propia sesión

La propuesta inicial traía una feature de paginación contra `sigrid-api`
partiendo de que el tope eran 1.000 filas por petición. **Es falso**: ese es
el defecto del código; la instancia `dev` tiene `MAX_ALLOWED_ROWS = 500.000`
(`azure-apps/sigrid_api.md` §4.1, comprobado el 2026-08-18). Con
`SIGRID_MAX_ROWS=5000` no hay problema, y el cliente ya lanza `SigridError`
si la respuesta viene `truncated`. La feature se retiró y lo que manda —el
corte del balanceador a los 230 s— quedó escrito en `ARCHITECTURE.md`.

> Ojo, no corregido: `PycharmProjects/CLAUDE.md` (el global, fuera de este
> repositorio) sigue diciendo que `sigrid-api` «sirve como máximo 1.000 filas
> por petición». Es el mismo error y no se tocó porque está fuera del
> proyecto.
