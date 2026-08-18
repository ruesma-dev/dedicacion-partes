<!-- README.md -->
# dedicacion-front

Interfaz web de captura rápida de dedicación. Sirve la SPA (Jinja2 + JS
vanilla) y hace proxy de `/api/*` hacia `dedicacion-api`, inyectando el
usuario de Easy Auth (`X-MS-CLIENT-PRINCIPAL-NAME` → `X-Usuario`).

## Arranque local

```
copy .env.example .env
pip install -r requirements.txt
python main.py            (puerto 8080; requiere dedicacion-api en 8090)
```

## Atajos de teclado

| Tecla | Acción |
|---|---|
| ↑ / ↓ | Moverse por la lista |
| Enter | Abrir el editor del trabajador |
| escribir + Enter | Autocompletar obra y añadir línea (el % se precarga con el restante) |
| R | Repetir las asignaciones del mes anterior del trabajador |
| Ctrl+Z | Deshacer última modificación |
| Esc | Cerrar editor (autoguardado) |
| / | Ir al buscador |

Autoguardado con debounce (700 ms) en cada cambio; los chips del resumen
superior filtran por estado (OK / sin carga / falta / exceso).
