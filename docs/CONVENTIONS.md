<!-- docs/CONVENTIONS.md -->
# Convenciones de código

> Documento normativo: el reviewer valida contra él. Las secciones que no
> apliquen al lenguaje del proyecto se borran; no se dejan «por si acaso».

## Estructura y estilo

- Primera línea de CADA fichero de código: comentario con su ruta relativa.
  Ej.: `# application/steps/mi_step.py`
- Arquitectura hexagonal (Ports & Adapters): domain sin dependencias,
  application orquesta, infrastructure adapta. Patrón pipeline + steps con
  objeto contexto para procesos encadenados; la composición del pipeline se
  hace en el punto de entrada, no dentro de los steps.
- Configuración leída del entorno (`.env` en local), parametrizaciones en
  ficheros de datos versionados. **Ningún secreto en código.**
- Logging estructurado. Prohibido `print()` (o equivalente) en código de
  producción; permitido en scripts puntuales.
- Errores transitorios de red: reintentos con backoff, nunca bucle desnudo.

### Python

- Python 3.12, PEP8, type hints en firmas públicas.
- Pydantic v2. `default=` solo en la firma, nunca duplicado dentro de
  `Field()`.
- Configuración: `config/settings.py` (pydantic-settings) leyendo `.env`.
- Logging con structlog. Reintentos con tenacity.
- PDF en servidor: ReportLab (no HTML/CSS print).

### JavaScript (solo `dedicacion-front`)

- JS vanilla, sin framework ni bundler: todo en `static/js/app.js`, servido
  tal cual. Nada de añadir dependencias de front sin decisión del humano.
- El front no calcula reglas de negocio: pinta lo que devuelve la API y le
  manda lo que el usuario teclea.

## SQL

- **Las consultas contra Sigrid van en YAML versionado**
  (`services/dedicacion-api/config/config.yaml`), no incrustadas en el
  código, y devuelven los alias exactos que espera el mapeo (por nombre de
  columna, nunca por posición).
- Parámetros SIEMPRE parametrizados: prohibido concatenar valores en la
  cadena SQL.
- El esquema de PostgreSQL se declara en `orm_models.py`. Si una feature
  necesita una columna nueva, entra en el ORM; el `ALTER TABLE ... IF NOT
  EXISTS` complementario, si hace falta, se deriva de ahí y no se escribe a
  mano en paralelo (ver el `_ALTERS` de `application/registro_sigrid.py`,
  que hoy es justo lo contrario y está en el backlog).

## Tests

- Los unit tests no tocan red ni BBDD: mocks y fixtures.
- Un requisito EARS (o criterio `acceptance`) => al menos un test con nombre
  trazable (`test_fXXX_rN_...`).
- Nada de credenciales en los tests, ni siquiera de entornos de desarrollo.

## Git

- Ramas: `main` (estable) ← `dev` (integración) ← `feature/F-XXX-slug`.
- Commits: `F-XXX Tn: descripción` (tareas) o `F-XXX: descripción` (ajustes).
- Los agentes solo hacen commit local en ramas feature. Push, merge a dev y
  PRs: siempre el humano.
- Los originales en PDF u ofimática no se versionan (ver `.gitignore`).

<!-- ==================== INICIO · ENTORNO DE RUESMA ==================== -->
<!-- Convenios de la organización, no del arnés. Fuera de ese entorno,     -->
<!-- borra el bloque entero hasta el comentario de cierre.                 -->

## Convenios del entorno de Ruesma

- **Todo en español**, incluidos comentarios de código y mensajes de commit.
- CSV de salida: UTF-8 BOM, `;` como separador, coma decimal (Excel ES).
- PowerShell: UTF-8 con BOM y CRLF (salvo excepciones documentadas).
- Medidas DAX sin tildes.
- Azure: imágenes con tags fechados (`rYYYYMMDD-HHmm`), nunca reescribir
  tags; secretos como secrets del recurso, jamás desplegar `.env`.

<!-- ===================== FIN · ENTORNO DE RUESMA ====================== -->
