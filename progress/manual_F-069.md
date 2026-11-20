<!-- progress/manual_F-069.md -->
# F-069 · Verificaciones MANUAL

## T16 · HECHA el 2026-11-20 (líder, modo pruebas, a petición del humano)

Petición del humano en la PARADA 2: «2 mes sin uso y hazlo tu». Meses usados: **2032-03** y **2032-04** (sin partes en la 0404 antes de empezar; 2032-01 ya tenía el parte de F-054). Todo por la api, como lo manda el front (`elementoImporte`: cantidad y comentario juntos). El modal del navegador no se ha mirado: lo que pinta sale de estos mismos datos y lo cubre `test_f069_importes_front.py`.

- **Entorno.** Transfer y api de la rama (`porcentajes-f069`, `57b5518`). La copia no tiene `.env`: cada servicio se arrancó cargando en memoria el `.env` de la copia principal (nada copiado ni escrito). `/health` del transfer: `modo_pruebas` true, obra de pruebas `0404`, base `ruesma`; `transfer_base_url` de la api, `http://127.0.0.1:8006`. La BBDD local ya tenía `importe_vinculado.cantidad` nulable: el `ALTER` no hizo falta.
- **Trabajador.** 2299582, MORALES LOPEZ, ALEJANDRO JOSE (MO/0649), con `CAJA` CA0173, `VP` VP0131 y `TF` TF0287. Cuadrante 2032-03: 0696 al 60 % (comentario del titular «titular t16») y 0722 al 40 %.
- **D19.** Comentario «visita a proveedor» en el km sin cantidad y releer el cuadrante: sigue (`cantidad` None). **Cumple.**
- **Preflight** con km 100 y caja 80 € en la 0696 y 0 en la 0722: km `pre` 20,00 € (100 × 0,20), `tot` 12,00 € y 8,00 €; caja `can` 1, `pre` 80 solo en la 0696; en la 0722, omitida «caja 0 … no se registra nada en esta obra». **Cumple.**
- **Registrar** (parte nuevo **PT32/00002**): 7 líneas. Km 416122 y 416125 con `tex` «PRUEBA-PORC visita a proveedor»; caja 416121 `can` 1, `pre` 80, `tot` 80; titular 416119 «PRUEBA-PORC titular t16». **Cumple.**
- **Registrar otra vez:** todo «ya registrada … no se duplica». **Cumple.**
- **D20.** Comentario del km a «visita a proveedor y obra». El preflight dice «ya registrada … se actualiza el comentario» con `tex_nuevo`; `ejecutar` trae `tex_actualizadas` con 416122 y 416125. En `estado`: `tex` nuevo, mismo `ide` y `pos`, `can`, `pre` y `tot` iguales. Log del transfer: dos `UPDATE hmores SET tex = ? WHERE ide = ? AND reside = ? …` y **0 `DELETE`**. **Cumple.**
- **Copiar a 2032-04.** Km y caja «copiado» y los dos omitidos: «copiado del mes anterior sin revisar … tecléalo o pulsa «Revisado»». **Cumple** (D11).
  - «Revisado» **solo en el km**: el km pasa a `escribir` (12 € y 8 €) y la caja sigue omitida, copiada. **Cumple** (review 1, cambio 4).
  - **D18.** Cambiar solo el comentario de la caja (con su cantidad, como el front): sigue `copiado` y omitida. **Cumple.** Un `PUT` a mano sin la clave `cantidad` la deja vacía: es la regla de un vinculado por obra (decisión 4 del informe); el front siempre manda la cantidad.
  - Al copiar por segunda vez, el km no volvió a marcarse: ya existía en el mes y la copia no lo pisa (R8); la caja sí se sustituyó (O3 de la review 1).
  - «Revisado» en la caja: pasa a `escribir`. Registrar 2032-04 (parte **PT32/00003**): caja 416128 con «PRUEBA-PORC caja solo comentario», km 416129 y 416132. **Cumple.**
- **D17.** Borrar en la app el comentario del km de 2032-03 y traer de Sigrid (`traer-sigrid`): vuelve «visita a proveedor y obra», **sin la marca**. El del titular no vuelve: `excluidas_pruebas` 2 (decisión 6 del informe, aceptada). **Cumple.**
- **Limpieza y sorpresa.** `limpiar --ano 2032 --mes 3 --confirmar` **no se limita al mes**: borra todas las líneas `PRUEBA-PORC` de la 0404. Se llevó las de 2032-03 y 2032-04 y también las tres de la T19 de F-054 (414543-414545, PT32/00001), cuya limpieza estaba pendiente de decisión del humano. Quedan, sin la marca, 415966 y 415967 a 0 en PT32/00001, y los partes PT32/00002 y PT32/00003 vacíos. En la BBDD local quedan los periodos 2032-03 y 2032-04.

Ficheros de la prueba en el scratchpad de la sesión (no versionados): `t16_*.json` y `t16_*.log`.
