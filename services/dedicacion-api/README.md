<!-- README.md -->
# dedicacion-api

Backend del registro mensual de **% de dedicación por trabajador y obra**
(sustituye a `Plantilla_Dedicacion_Ruesma_vXX.xlsx`). FastAPI + PostgreSQL,
arquitectura hexagonal, maestros sincronizados desde Sigrid vía `sigrid-api`.

## Arranque local

```
copy .env.example .env    (rellenar credenciales)
pip install -r requirements.txt
python main.py            (crea la BBDD "dedicacion" si no existe, puerto 8090)
```

**Arranca siempre por `python main.py`.** El esquema se pone al día ahí y solo
ahí: `main.py` crea las tablas que faltan y añade a las que ya existen las
columnas que declara `infrastructure/db/orm_models.py`, derivando el DDL con
`infrastructure/db/esquema.py` y registrando en el log cuántas sentencias
aplicó (contra una base al día, cero). Construir la app (`build_app`) **no
toca la base de datos**, así que apuntar `uvicorn` directamente a la app se
salta esa puesta al día. El mecanismo solo añade columnas: cualquier otro
cambio de esquema es una migración que escribe una persona.

## Endpoints (prefijo /api/v1)

| Método | Ruta | Uso |
|---|---|---|
| GET  | /health | Estado del servicio |
| GET  | /sync/preview | Ver qué devolverán las consultas de Sigrid (sin persistir) |
| POST | /sync | Sincronizar empleados activos y obras |
| GET/POST | /periodos | Listar / crear-obtener periodo (idempotente) |
| POST | /periodos/{a}/{m}/cerrar · /reabrir | Estado del periodo |
| POST | /periodos/{a}/{m}/copiar-anterior | Rellena SIN CARGA con el último periodo con datos |
| GET  | /periodos/{a}/{m}/cuadrante | Trabajadores + líneas + estados + resumen |
| PUT  | /periodos/{a}/{m}/trabajadores/{ide}/asignaciones | Sustitución atómica de las líneas |
| POST | /periodos/{a}/{m}/trabajadores/{ide}/deshacer | Deshacer (multi-nivel, con auditoría) |
| POST | /periodos/{a}/{m}/trabajadores/{ide}/copiar-anterior | Repetir mes anterior de un trabajador |
| GET  | /periodos/{a}/{m}/export.xlsx | Excel compatible (hoja Detalle + Resumen, convenio Postv-) |

## Pendiente de decidir con datos reales

- Filtro de obras "no cerradas": la consulta de `config/config.yaml` trae hoy
  todas las obras con su `con.est`; usar `GET /sync/preview` (campo
  `obras.por_estado`) para ver la codificación real y ajustar el `WHERE`.
- Consulta de empleados activos: basada en último `emphis.fecbaj = 0`;
  validar el total contra nóminas (~156) con el mismo preview.
