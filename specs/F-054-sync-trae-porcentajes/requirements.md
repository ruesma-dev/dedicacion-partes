<!-- specs/F-054-sync-trae-porcentajes/requirements.md -->
# F-054 · Al sincronizar, traer al cuadrante los % que ya están en Sigrid

Rigor **`critico`**. Los tres servicios (design §1): el transfer **lee**
Sigrid y traduce, la api **escribe** en `dedicacion` y el front lanza y
enseña. **En Sigrid, solo lectura.** Pedida el 2026-10-08 («al sincronizar
debería traer los % ya existentes en Sigrid»); ejemplo: el caso de la 0694,
2026-09 (una `MADM` al 95 % a mano, sin `synckey`, que salió como sobrecarga).
**D1-D11 ABIERTAS** (§9); los R con `[Dn]` van con la recomendada. Fuera:
incidencias de Sigrid (D9, F-062), vinculados (F-044), escribir y `partes`.

## 0. Lo que hay en Sigrid y glosario

Lecturas agregadas del líder (2026-10-23, mensuales desde 2025): las `M*`
suman el 100 % por recurso y mes «en 730 de 756 meses con incidencia»; la
`M*` lleva `fec` = último día del mes en el 94 %; las `CI*`/`CIZ` tienen
`can = tot = 0` y no cuentan para el %. **Línea mensual**: `hmores` con hora
`M*` y `can` ≠ 0 en un parte de trabajo de obra. **Entrada**: obra + modo del
cuadrante (obra normal, `Postv-X` o `VAR-NN`).

## 1. Disparador y periodo `[D1, D7]`

- **R1.** CUANDO el sync de maestros termina con éxito, el front debe pedir
  `POST /api/v1/periodos/{anio}/{mes}/traer-sigrid` del periodo abierto en el
  cuadrante, con la empresa elegida. SI el sync falla, no se pide.
- **R2.** Periodo inexistente ⇒ 404; `CERRADO` ⇒ 409; sin llamar al transfer.
- **R3.** SI una lectura de Sigrid falla o viene `truncated`, ENTONCES el
  transfer responde 502 y la api 502 con el motivo, sin tocar la base; el
  front lo avisa y el sync de maestros ya hecho se queda.

## 2. Qué se lee (transfer) `[D2, D6]`

- **R4.** El transfer lee en **una** lectura las líneas mensuales de los
  partes de trabajo de obra (`con.tip` del ajuste, `hmo.reside` 0) del
  periodo pedido (`hmo.ano`, `hmo.mes`) en obras de la empresa pedida, con
  cualquier `fec`, `synckey` y estado del parte.
- **R5.** Las de la obra de pruebas (`OBRA_PRUEBAS_COD`) solo se cuentan.
- **R6.** Cada línea publica `hmores_ide`, recurso, obra del parte, parte
  (`ide`, código, estado, `en_registro`), hora, `can`, `fec`, partida (`ide`,
  `cod`, `res`) y `synckey`.
- **R7.** El endpoint nunca escribe en Sigrid, esté o no en modo pruebas.

## 3. Traducción a una entrada (transfer) `[D3]`

- **R8.** Línea de una obra normal: `destino = normal`, con su obra.
- **R9.** Línea de la obra de postventa (`POSTVENTA_OBRA_COD`): `destino =
  postventa` y `obra_origen_ide` = la **única** obra, de las que manda la
  api, cuyo casado (`casar_postventa`, `#regla-p5`) da su partida; ninguna ⇒
  motivo «no casa»; varias ⇒ «ambigua», con sus códigos.
- **R10.** Línea de la obra VAR (`VAR_OBRA_COD`): `destino = var` con
  `var_paride` si `partida_var_de` (`#regla-var`) la acepta; si no, su motivo.
- **R11.** Los catálogos de postventa y VAR se leen solo si alguna línea es
  de esa obra. **R12.** Son las funciones del preflight: un `Postv-X` o
  `VAR-NN` traído se registra en la partida de la que vino.

## 4. Qué se trae al cuadrante (api) `[D3, D10, D11]`

- **R13.** La api agrupa por trabajador (`recurso_ide` = `trabajador.ide`) y
  entrada: normal = la obra; postventa = (`obra_origen_ide`, postventa); VAR
  = la fila de `obra` con `ide` = −`var_paride`.
- **R14.** Una línea no se trae y sale en `no_traidas` con su motivo si el
  trabajador no es visible en la empresa elegida o no está vigente en el mes;
  si su entrada no está en la base, es de otra empresa o no es ofrecible
  (`Linea.ofrecible`); o si el transfer la devolvió con motivo. Las de
  recursos que no están en el maestro (p. ej. vinculados) solo se cuentan,
  en `fuera_maestro`.
- **R15.** Las líneas de un trabajador en la misma entrada (varios partes,
  días o partidas) se suman. SI en una normal tienen partidas distintas,
  ENTONCES esa entrada no se trae.
- **R16.** % = suma de `can` × 100 a centésimas; ≤ 0 o > 100 ⇒ no se trae.
- **R17.** Partida: en la normal, la de sus líneas como **elegida** (0 ⇒
  automática); en postventa, automática (el casado da la misma); en VAR, la
  fija de la entrada. Sin propuesta guardada.
- **R18.** Las entradas buenas se traen aunque otras del trabajador no.

## 5. Lo que ya tiene el cuadrante `[D4]`

- **R19.** MIENTRAS no tiene líneas en el periodo, se le crean las traídas.
- **R20.** SI ya tiene líneas y coinciden con las traducibles de Sigrid
  (mismas entradas y %, con la épsilon 0,005 de `domain/estados.py`; la
  partida no cuenta), ENTONCES no se toca y suma en `coinciden`.
- **R21.** SI difieren, ENTONCES no se toca: sale en `diferencias`.
- **R22.** CUANDO la petición trae `sustituir: [ide]`, a esos trabajadores se
  les **sustituyen** las líneas por las traducibles de Sigrid; uno sin
  ninguna no se toca y sale con su motivo.
- **R23.** Una transacción; repetir sin cambios en Sigrid no cambia nada.

## 6. Marcar «ya registradas» `[D5]`

- **R24.** Cada entrada traída guarda en su asignación `sigrid_hmores_ide`
  (el menor `ide` de las líneas que suma), `sigrid_parte_cod`,
  `sigrid_estado = registrado` y el motivo «traída de Sigrid»: al registrar
  viaja como `hmores_ide` y el transfer la da por **ya registrada**
  (`#regla-cero`). **R25.** Las que ya tenía el cuadrante no se marcan.
- **R26.** Lo que se cambie después sigue la regla de hoy: la fila guardada
  pierde la traza y la línea de Sigrid es un pisado a confirmar, que se
  **edita** en su sitio. Nunca un duplicado.

## 7. Deshacer y propuestas `[D8]`

- **R27.** Cada trabajador traído o sustituido deja **un** evento `SIGRID`
  con su `X-Usuario` y los snapshots, deshacible (`#regla-deshacer`).
- **R28.** Tras traer, se encolan las propuestas de los escritos (Copiar mes).

## 8. Resultado, front y lo que no cambia

- **R29.** La respuesta publica `traidos` y `sustituidos` (trabajador y
  entradas), `coinciden`, `diferencias` (las dos versiones), `no_traidas`
  (trabajador, obra, parte, %, motivo), `fuera_maestro`, `lineas_leidas`,
  `excluidas_pruebas` y los motivos de postventa y VAR.
- **R30.** El front enseña un aviso con el resumen y, si hay diferencias o no
  traídas, una ventana con las listas; cada diferencia con «Usar lo de
  Sigrid», que repite la petición con `sustituir: [ide]` y recarga el
  cuadrante. El front no compara ni decide.
- **R31.** Preflight, `ejecutar`, sync de maestros y propuestas hacen las
  mismas lecturas que hoy (F-055): ninguno usa la lectura nueva.
- **R32.** `ARCHITECTURE.md` gana `#regla-traer-sigrid` y la fila de lectura;
  `INTEGRACION.md`, §1, §5 y §7 (despliegue transfer → api → front);
  `azure-apps/dedicacion.md`, al desplegar y dentro de F-054;
  `test_f002_fuente_unica` vigila la ancla.
- **R33.** MANUAL (humano, local, septiembre 2026): tras sincronizar, el caso
  de la 0694 sale en el cuadrante o en `diferencias`, y el preflight da lo
  traído por ya registrado (tasks T13).

## 9. Preguntas abiertas para el humano (recomendada: **A** en todas)

1. **D1 · Disparador.** (A) al pulsar «Sincronizar Sigrid», tras el sync con
   éxito, el periodo abierto en el cuadrante; (B) botón aparte; (C) dentro
   de `POST /sync`, todos los abiertos y sin ver el resultado.
2. **D2 · Qué líneas.** (A) todas las mensuales, nuestras y manuales; (B)
   solo las sin `synckey` nuestra. A: Sigrid es lo registrado.
3. **D3 · Traducción.** (A) R8-R17: la partida del parte como **elegida**, y
   sin entrada ofrecible no se trae; (B) como propuesta guardada (el
   selector la reescribe); (C) traer también a no ofrecibles, marcadas.
4. **D4 · Lo que ya hay.** (A) R19-R22: solo los trabajadores sin líneas; con
   líneas, coincide o se lista con «Usar lo de Sigrid»; (B) Sigrid manda
   siempre; (C) mezclar línea a línea. A: como Copiar mes.
5. **D5 · Ya registradas.** (A) R24, guardar el `hmores.ide`; (B) no marcar:
   cada traída pediría confirmar un pisado al registrar.
6. **D6 · Partes cerrados.** (A) cuentan igual, con su estado en la
   respuesta; (B) solo los En registro. A: son % del mes.
7. **D7 · Mes cerrado en la app.** (A) 409 sin leer; (B) traer igual.
8. **D8 · Deshacer.** (A) un evento por trabajador; (B) el lote de una vez.
9. **D9 · Incidencias.** (A) solo %, las `CI*`/`CIZ` a F-062; (B) también.
10. **D10 · Varias líneas en una entrada.** (A) R15: sumar, y con partidas
    distintas no se trae; (B) sumar y elegir la de más %; (C) no traer
    nunca. A: elegir una dejaría otra sumando de más al registrar.
11. **D11 · Qué trabajadores.** (A) los visibles en la empresa elegida y
    vigentes, como Copiar mes y Registrar; (B) todos los del maestro.
