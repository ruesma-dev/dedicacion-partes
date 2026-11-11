<!-- progress/spec_F-069.md -->
# F-069 · Informe del spec-author (2026-11-10, revisado el 2026-11-11)

Spec en `specs/F-069-importe-caja-km/` (rama `feature/F-069-importe-caja-km`,
copia `porcentajes-f069`): `requirements.md` R1-R32 (143 líneas), `design.md`
(247), `tasks.md` T1-T16. Estado en `features.json`: `spec_ready`, todavía sin
aprobar porque quedan **D10 y D11 abiertas**.

## Resumen

La cantidad del mes de los vinculados de cantidad se teclea en el editor del
trabajador: € para caja y viaje, km para el VP. La api la guarda en la tabla
nueva `importe_vinculado` (periodo × vinculado, con la marca `copiado`). Copiar
el mes la copia, marcada como copiada, y la manda en el contrato (`importe_mensual`,
`unidad`, `cantidad`, `copiado`). El transfer calcula el importe del mes (en
€ tal cual; los km × el precio por km, que lee de Sigrid según D10). Ese
importe va a `pre` y se reparte con el `can` del titular (`tot = round(can × pre, 2)`).
Partida, cuenta, pisado, capacidad e idempotencia, como en F-044 y F-068.
Despliegue: transfer → api → front.

## Decisiones cerradas por el humano (2026-11-11: «d2, caja en euros, km en km y viaje en wuros. d7, copia importes. A a lo demas»)

- D1 = A: `CAJA`, `VP` y `VIAJE`, en `config.yaml` (`tipos_importe`, ahora con su unidad).
- D2: caja y viaje en €; VP en km × precio unitario («esta en sigrid como unitario de ese recurso» → D10).
- D3 = A: casillas en el editor. D4 = A: sin cantidad se omite ese vinculado; con 0 no se escribe nada.
- D5 = A: `can` = %, `pre` = importe del mes, `tot = round(can × pre, 2)`. D6 = A: las líneas a mano, como F-044/F-064.
- D7 = B: copiar el mes copia las cantidades como valor ya puesto y editable, con `copiado = true` y la marca «copiado del mes anterior, sin revisar» en el editor y en la subfila. La marca se quita al teclear o al pulsar «Revisado». Nunca pisa una cantidad que ya esté puesta y deja su propio evento `IMPORTES`.
- D8 = A: sin normalizar. D9 = A: lo ya registrado no se edita.

## Decisiones abiertas

- **D10 · Dónde está el precio por km de cada VP.** No lo he encontrado (detalle en design §9.2). Recomiendo A: que el humano diga la pantalla y el campo de Sigrid, con un VP de ejemplo. Si el precio no existe por recurso, B: un precio único en `config.yaml`, 0,20, el que llevan las líneas a mano. **Bloquea T3 y la aprobación.**
- **D11 · Cantidad copiada sin revisar al registrar.** Recomiendo A: se omite «importe copiado del mes anterior sin revisar» hasta que se revise. B: se registra tal cual.

## Lecturas contra Sigrid (2026-11-11, solo `SELECT` vía `sigrid-api` `POST /api/sql/read`, base `ruesma`)

Las hice con el cliente de la api (`SigridApiClient`) y un script del scratchpad. Usé el `.env` de la copia principal solo para leerlo; no cambié nada.
- `reshor` (hora 46 `KM`) de los VP: `pre`, `prenom`, `preven` a 0, salvo tres con un importe mensual (VP0016 160, VP0046 600, VP0115 175). `candef` vale 1 en 43; `proide` 0.
- `auxhor` 46: `KM`, `pre`, `prenom` y `preven` a 0, `unipre` 0, `medide` 19 («ud»). `tarmob` de la hora 46: ninguna fila. `rescen` de VP0049, VP0076 y VP0104: ninguna. `conext`: solo «Recurso Asociado» (`defext` 46).
- `auxgas` con precio: solo el 8, «Kilometros», 0,1923 (global). `hgvres` del gasto 8 desde 2025: ninguna línea.
- Líneas `hmores` con hora `KM` de 2026 (602): 563 con `pre` en € (de 6 a 1.069,20) y `can` ≤ 1; 31 a 0; 8 con `can` = km y `pre` 0,20 (VP0111, VP0117, VP0137…). Entre 2024 y 2025 hay más con 0,20 (VP0050, VP0078…).

## Notas para el líder

- `bash harness/init.sh` en verde tras la revisión (ver el commit).
- Cruce con F-071 (`can` ajustado): hay que anotarlo en su spec. T13 (MANUAL en modo pruebas, 0404) y T15 (despliegue y `azure-apps`) son del humano.
