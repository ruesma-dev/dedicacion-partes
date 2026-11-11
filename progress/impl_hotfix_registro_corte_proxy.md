<!-- progress/impl_hotfix_registro_corte_proxy.md -->
# Hotfix 2026-11-11 · `hotfix/registro-corte-proxy` · informe del implementer

Copia `porcentajes-hotfix`, rama `hotfix/registro-corte-proxy` (desde `dev`
`85a6a70`). Sin spec SDD: plan aprobado por el humano («vamos con el hotfix»).
Solo toca `dedicacion-front` (y la doc). Commit del arreglo: `16a720d`.

## Problema

10/11/2026, registro de octubre (56 obras, ~3,5 min): el proxy del front cortó
a los 200 s con 502 `{"error": "Backend dedicacion-api inaccesible"}`;
`registroEjecutar()` solo hacía `toast(err.message, true)` aunque el servidor
terminó. El usuario cree que falló y puede relanzarlo.

## Qué cambió

| Fichero | Cambio |
|---|---|
| `services/dedicacion-front/static/js/app.js` | `api()`: el `Error` lleva `status` (código HTTP; `0` si `fetch` rechaza). Mismo mensaje que antes (`cuerpo.error`, `Error HTTP N`, o el del fallo de red). |
| ídem | `toast(mensaje, esError, fijo=false)`: con `fijo` no se va solo; devuelve la caja (los llamadores de siempre no cambian). |
| ídem | `registro.cortado` y `const ESPERA_RECARGA_TRAS_CORTE = 60000`. |
| ídem | `esCorteDelProxy(err)`: `status` en `[0, 502, 504]`. |
| ídem | `esperarRegistroCortado(err)`: cierra el modal, aviso fijo «El registro sigue en curso en el servidor (<mensaje>). Recargo el cuadrante en 60 s; no lo relances.», `#btn-registro` deshabilitado («Registro en curso…»), y a los 60 s `cargarPeriodo(anio, mes)` del mes registrado, quita el aviso, desbloquea y avisa «Cuadrante recargado; revisa el resultado del registro.». |
| ídem | `registroEjecutar()`: en el `catch`, corte ⇒ `esperarRegistroCortado`; otro error ⇒ `toast(err.message, true)` como siempre **y** el botón vuelve a «Registrar» habilitado. |
| ídem | `registroPreflight()`: con `registro.cortado`, aviso «El registro anterior sigue en curso; espera a que se recargue el cuadrante.» y no pide nada. |
| `services/dedicacion-front/tests/test_hotfix_registro_corte_proxy.py` | 15 tests nuevos (node). |
| `docs/ARCHITECTURE.md` | «Timeouts encadenados»: párrafo del corte del registro y su trato en pantalla. |

### Decisiones (dentro del plan, para el líder)

1. **Botón atascado (lo pedía comprobar el plan): sí se quedaba.** Antes, en
   cualquier error de `ejecutar`, `#btn-ejecutar-registro` seguía
   `disabled` con «Registrando…» y el modal abierto: no se podía reintentar
   sin cerrarlo y repetir el preflight. Arreglado en el mismo cambio (test
   `…otro_error_como_siempre_y_el_boton_vuelve`, RED abajo).
2. **«El botón de registrar» bloqueado** = `#btn-registro` («Registrar en
   Sigrid»): el del modal desaparece al cerrarlo. Pero hay **otras dos
   entradas** al registro (botón «⇪ Sigrid» de cada fila, l. ~1543, y
   «⇪ Registrar en Sigrid» del editor, l. ~1724) y `registroPreflight`
   re-habilitaba `#btn-registro` en su `finally`. Por eso el bloqueo real
   está en `registroPreflight` (`registro.cortado`): sin ello, el plan
   («no lo relances», botón bloqueado) no se cumplía.
3. **Se recarga el mes registrado**, capturado al cortar, no el que se esté
   viendo a los 60 s (si el usuario cambia de mes, vuelve al registrado,
   que es el que tiene que revisar). Test
   `…recarga_el_mes_registrado_aunque_se_cambie`.
4. **El aviso lleva el mensaje original** entre paréntesis. Motivo: la api
   también puede devolver 502 por su cuenta (`SigridError` →
   `_HTTP_POR_ERROR` de `dedicacion-api/interface_adapters/api/app.py`), y
   ahí el registro sí pudo fallar antes de escribir. No se distingue (eso
   pediría mirar el texto del proxy); el trato (esperar, recargar, revisar)
   es inocuo también en ese caso y el mensaje queda a la vista. Un fallo del
   transfer NO llega como 502: el cliente de la api lo devuelve como
   `ok:false` en un 200 (`transfer_client.py`), que sigue el camino normal.
5. Si `cargarPeriodo` falla al recargar, ella misma avisa (como siempre) y
   después sale igualmente «Cuadrante recargado…»; no se ha complicado más.

## Fase RED

Comando (desde `services/dedicacion-front`):
`.venv/Scripts/python -m pytest tests/test_hotfix_registro_corte_proxy.py -q -p no:cacheprovider`

Primera ejecución: 15 failed, todas por `AssertionError: no existe la
constante ESPERA_RECARGA_TRAS_CORTE en app.js` (RED de arnés, no de
comportamiento). Se hizo el arnés tolerante (`_si_existe`: incluye la
función o constante solo si existe; su existencia la exigen otros asserts)
para ver el RED **de comportamiento**. Salida real, antes del arreglo:

```
E       AssertionError: assert {'mensaje': '...sError': True} == {'mensaje': '...sError': True}
E         Right contains 1 more item:
E         {'status': 502}
   (igual con {'status': 504}, {'status': 422}, {'status': 0})
E       AssertionError: no existe la función esperarRegistroCortado en app.js
E               subprocess.CalledProcessError: Command '['C:\\Program Files\\nodejs\\node.EXE', '-']' returned non-zero exit status 1.
   (x4: los casos de corte 502/504/red y «mes registrado»; stderr de node:
    TypeError: Cannot read properties of undefined (reading 'f')
    = no se programa ningún temporizador de recarga)
E       AssertionError: assert {'disabled': ...Registrando…'} == {'disabled': ...: 'Registrar'}
E         Differing items:
E         {'textContent': 'Registrando…'} != {'textContent': 'Registrar'}
E         {'disabled': True} != {'disabled': False}
   (x4: 409, 422, 500, 503 — el botón atascado de la decisión 1)
FAILED ...::test_hotfix_corte_api_lanza_el_error_con_su_status[...-502]  (y 504, 422, red)
FAILED ...::test_hotfix_corte_la_espera_es_de_60_s
FAILED ...::test_hotfix_corte_avisa_bloquea_y_programa_la_recarga[502-proxy]  (y 504-balanceador, red)
FAILED ...::test_hotfix_corte_recarga_el_mes_registrado_aunque_se_cambie
FAILED ...::test_hotfix_corte_otro_error_como_siempre_y_el_boton_vuelve[409]  (y 422, 500, 503)
13 failed, 2 passed in 2.65s
```

Los 2 que pasaban ya: `api()` con éxito devuelve el cuerpo y el preflight sin
corte pide lo de siempre (son de no regresión).

GREEN, mismo comando, tras el arreglo: `15 passed in 1.82s`. Suite completa
del front: `473 passed, 19 warnings in 56.77s`.

## Qué cubren los tests

- `api()`: 502 (cuerpo del proxy), 504 (cuerpo no JSON, como el HTML del
  balanceador ⇒ «Error HTTP 504»), 422 y fallo de red ⇒ mismo mensaje de
  siempre + `status` (502/504/422/0); éxito ⇒ el cuerpo.
- Corte (502, 504, red), con el `api()` REAL y un `fetch` doble: modal
  cerrado, un único aviso fijo con el texto, `#btn-registro` deshabilitado,
  un temporizador de 60000 ms y ninguna recarga todavía; durante la espera,
  `registroPreflight(null)` y `registroPreflight(77)` no piden nada y avisan;
  al vencer: `cargarPeriodo(2026, 10)`, aviso quitado, botón desbloqueado y
  aviso final.
- Error normal (409/422/500/503): un `toast(mensaje, true)` no fijo, modal
  abierto, sin temporizador ni recarga, «Registrar» habilitado.
- La constante vale 60000 y es la que usa `esperarRegistroCortado`.
- Los tests previos de `registroEjecutar` (F-049, el cuerpo del POST) siguen
  verdes.

## Resultado de `bash harness/init.sh`

Al empezar (tras `rm -f .arnes_cache/suite_*.ok`): `ENTORNO LISTO`, sin
`[KO]` (raíz 418 passed/1 skipped; api 1339; front 458; transfer 1737).

Al terminar (tras `rm -f .arnes_cache/suite_*.ok`, con el arreglo ya
commiteado): `ENTORNO LISTO. Puedes trabajar.`, código de salida 0, sin
`[KO]`: raíz 418 passed/1 skipped (48.50 s); api 1339 passed (89.42 s);
front 473 passed (62.86 s); transfer 1737 passed (21.77 s).

## Fuera de alcance / qué queda

- No se tocan timeouts, proxy, api ni transfer. Registrar en segundo plano con
  progreso queda fuera. Nota para el líder: en `BACKLOG.md`, **F-073** es hoy
  el «Informe Excel de cada registro»; si el registro en segundo plano debe ir
  ahí, su descripción no lo dice todavía.
- **`azure-apps` no se toca**: no cambia ningún contrato con la api ni con
  Azure (mismos endpoints, mismos códigos; solo el trato en pantalla).
- **Pendiente del humano (MANUAL):** probar en el navegador (en local, con la
  api parada o un `API_TIMEOUT_S` bajo en el `.env` del front, para forzar el
  502 en `registro/ejecutar` — ojo: el transfer local va en modo pruebas,
  obra `0404`) y **desplegar SOLO el front**.
- Merge a `dev`: lo hace el líder.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests nuevos | 15 (RED: 13 failed / 2 passed → GREEN: 15 passed) |
| Suite del front | 473 passed (antes 458) |
| Cobertura de líneas cambiadas | N/A: `PUERTA COBERTURA: N/A (la rama … no corresponde a ninguna feature declarada)`; además el cambio es JS, que la cobertura de Python no mide |
| Mutación | N/A: hotfix sin feature en `features.json` y código JS (`harness.mutacion` es de Python) |
| Tiempo de la suite del front | 56.77 s (los 15 nuevos, 1.82 s) |
