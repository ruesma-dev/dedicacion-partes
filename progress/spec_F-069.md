<!-- progress/spec_F-069.md -->
# F-069 · Informe del spec-author (2026-11-10)

Spec escrita en `specs/F-069-importe-caja-km/` (rama `feature/F-069-importe-caja-km`,
copia `porcentajes-f069`): `requirements.md` R1-R30 (136 líneas), `design.md`
(249), `tasks.md` T1-T15. Estado en `features.json`: `spec_ready`, a la espera
de que el humano apruebe y cierre las decisiones.

## Resumen

El importe del mes de los vinculados de importe (caja, km y viajes) se teclea
en el editor del trabajador, la api lo guarda en una tabla nueva
`importe_vinculado` (periodo × vinculado) y lo manda en el contrato
(`importe_mensual`, `importe`). El transfer lo usa como `pre` en vez de
`reshor.pre` y reparte con el `can` del titular (`tot = round(can × pre, 2)`);
lo demás (partida, cuenta, pisado, capacidad, idempotencia) es lo de F-044 y
F-068. Toca los tres servicios (design §1). Ninguna SQL nueva contra Sigrid.
Despliegue: transfer → api → front. Si el transfer es el viejo, los vinculados
de importe se siguen omitiendo como hoy.

## Decisiones abiertas (detalle en design §9)

- D1 · Tipos que van por importe: **A** `CAJA`, `VP`, `VIAJE` en una lista de `config.yaml` (B solo caja y VP; C todo `pre` 0).
- D2 · Unidad: **A** euros en todos (es lo que llevan hoy las `KM` a mano); sin negativos.
- D3 · Dónde se pide: **A** casillas en el editor del trabajador, tras las incidencias, con autoguardado; «falta importe» en la subfila.
- D4 · Sin importe / 0: **A** sin importe ⇒ ese vinculado se omite «falta el importe del mes» y lo demás se registra; 0 ⇒ no se escribe nada.
- D5 · Reparto: **A** `can` = % del titular, `pre` = importe, `tot = round(can × pre, 2)`; descuadre de céntimos aceptado (B, cuadrar el resto, obliga a calcular en la api).
- D6 · Líneas a mano ya en el parte (29 en octubre): **A** como F-044/F-064 (pisado a confirmar, marcado por defecto; otra partida ⇒ sobrecarga si pasa de 1).
- D7 · Persistencia: **A** tabla `importe_vinculado`; copiar el mes NO copia importes; el editor enseña el del mes anterior como referencia.
- D8 · Trabajador que no suma 100 %: **A** sin normalizar, como F-044.
- D9 · Importe cambiado tras registrar: **A** `ya_registrado`, como el % (corregir a mano o F-033).

## Notas para el líder

- `bash harness/init.sh` en la copia: la primera vez salió en ROJO por los venvs que faltaban (el líder los creó); tras escribir la spec, verde («ENTORNO LISTO»: raíz 418, api 1339, front 458, transfer 1737; tamaño 136/150 y 249/250).
- **No he hecho lecturas contra Sigrid.** Los datos salen de `progress/explore_F-044_sigrid.md`
  (§1 tipos y `pre`, §3: en las `KM` a mano `tot = can × pre` en 489 de 489) y del contexto del encargo.
  La forma de las líneas de caja a mano no está medida: si el humano quiere confirmarla antes de aprobar D5, hace falta una lectura vía `sigrid-api`.
- Cruce con **F-071** (`can` ajustado por alta o baja): hay que anotarlo en su spec al aprobar esta (design §10).
- T13 (MANUAL en local, modo pruebas, 0404) y T14 (despliegue y `azure-apps/dedicacion.md`) son del humano.
