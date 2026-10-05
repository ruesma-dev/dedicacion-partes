<!-- specs/F-034-obras-siempre-ruesma/requirements.md -->
# F-034 · Las obras son siempre de Construcciones Ruesma; el selector filtra solo trabajadores

Rigor **`critico`**: corrige una regla desplegada que hoy impide registrar a
los trabajadores de la 18 y la 31 con el transfer en **modo real**
(`docs/INTEGRACION.md` §8). Es una corrección de F-024, no una feature nueva.

Servicios: **`dedicacion-api`** (obras ofrecidas, visibilidad, marca y
empresa de cada línea) y **`dedicacion-front`** (solo dos textos). El
**transfer no se toca**: su contrato y su código siguen igual (R9). Regla de
dominio: [`docs/ARCHITECTURE.md#regla-empresa`](../../docs/ARCHITECTURE.md#regla-empresa).

Regla nueva del humano (2026-10-01): los **trabajadores** son de varias
empresas; las **obras**, incluida la postventa, son **siempre** de
Construcciones Ruesma (empresa 1).

Glosario: **E** = empresa elegida en el selector (parámetro `empresa`, F-024).
**Empresa de las obras** = el ajuste `EMPRESA_IMPUTACION` (1), que sigue
siendo además la **por defecto** del selector (D1). Empresa de un trabajador
u obra = su `empresa` (`con.emp`, F-023), NULL en filas desactivadas antes
de F-023.

## 1. Obras ofrecidas

- **R1.** CUANDO se pide el cuadrante con cualquier E, la lista `obras` debe
  contener solo las obras cuya empresa es la empresa de las obras (activas, o
  inactivas con líneas en el periodo), nunca las fichas de esas obras en otras
  empresas. Una obra con empresa NULL no se ofrece.

## 2. Qué trabajadores se ven con E

- **R2.** Un trabajador con empresa debe ser visible solo en la suya (sin
  cambio respecto a F-024).
- **R3.** Un trabajador con empresa NULL debe ser visible **solo en la por
  defecto**, tenga o no líneas y sean de la obra que sean. (Ver D2; sustituye
  a R8 de F-024 para el caso NULL.)
- **R4.** El resumen, las respuestas por fila, la copia del mes y el export
  deben seguir contando solo los trabajadores visibles en E, ahora con R2-R3
  (R10 y R13-R15 de F-024 siguen vigentes).

## 3. Marca de la línea

- **R5.** `otra_empresa` de cada línea debe valer `true` solo si
  `obra_empresa` no es null y es distinta de la **empresa de las obras**, sea
  cual sea E. (Ver D3.)
- **R6.** El front debe avisar en la línea con `otra_empresa` de que la obra
  no es de la empresa de las obras y no se registrará, sin la coletilla «en
  esta empresa»; y el `title` del selector debe decir que es la empresa de
  los trabajadores. Presentación pura: el front no compara empresas.

## 4. Registro en Sigrid

- **R7.** CUANDO se pide preflight o ejecutar con E, la API debe mandar al
  transfer solo las líneas de los trabajadores visibles en E (R2-R3), **todas
  con `empresa` = empresa de las obras**, sea cual sea E. (Sustituye a R16 de
  F-024.)
- **R8.** SI una línea va a una obra cuya empresa no es la de las obras,
  ENTONCES la API debe mandarla igual, con `empresa` = empresa de las obras, y
  la omisión con motivo que decide el transfer debe quedar trazada
  (`sigrid_estado = omitido`), como en R17 de F-024.
- **R9.** El contrato API ↔ transfer no debe cambiar (mismos campos, mismos
  códigos HTTP) y el código de `services/dedicacion-transfer/` no debe
  cambiar.
- **R10.** `EMPRESA_IMPUTACION` debe seguir siendo un entero > 0 (si no, la
  API no arranca), la por defecto del selector y de las peticiones sin
  `empresa`, y la fuente única de la empresa de las obras.

## 5. Tests que fijaban la regla anterior

- **R11.** Cada test de F-022 o F-024 que fijaba la regla anterior debe
  adaptarse **declarándolo** en `progress/impl_F-034.md` (test, assert viejo,
  assert nuevo, requisito que lo justifica). Ningún caso se borra sin
  sustituirlo por su equivalente con la regla nueva; la lista cerrada está en
  [`design.md` §6](design.md#6-tests-existentes-que-cambian).

## 6. Documentación

- **R12.** `docs/ARCHITECTURE.md#regla-empresa`, `docs/INTEGRACION.md`
  (cabecera, fila de `EMPRESA_IMPUTACION` en §3, párrafo de §9), el
  comentario de `settings.py` y el `.env.example` de la API deben decir la
  regla nueva. La copia de esas piezas a `azure-apps/dedicacion.md` la hace el
  líder (commit en `azure-apps`).

## 7. Verificación con datos reales

- **R13.** Un preflight real, **de solo lectura**, con la 18 elegida debe
  devolver las líneas de sus trabajadores en obras de Construcciones Ruesma
  con `accion = escribir` y `obra_origen.empresa = 1`, no omitidas por
  empresa. **Nadie lanza `registro/ejecutar`** (MANUAL del humano, T9).

Fuera de alcance: ver [`design.md` §8](design.md#8-fuera-de-alcance).

## 8. Decisiones abiertas (las valida el humano antes de implementar)

- **D1 · De dónde sale la empresa de las obras.** **Propuesta:**
  `EMPRESA_IMPUTACION` recupera su sentido literal —la empresa a la que se
  imputa, la de las obras— y sigue siendo la por defecto del selector. Hoy
  las dos son la 1; no toca `infra/`, ni el `.env` desplegado, ni
  `azure-apps` más allá del texto. En el dominio van como **dos campos**
  (`FiltroEmpresa.empresa_obras` y `por_defecto`) para que separarlas mañana
  sea solo un ajuste. **Alternativa:** un ajuste nuevo (`EMPRESA_OBRAS`) y
  `EMPRESA_IMPUTACION` renombrada a por defecto: más explícito, pero toca
  infra, el `.env` de Azure y un redespliegue de configuración.
- **D2 · Trabajadores sin empresa.** F-024 los hacía visibles en la empresa
  de las obras de sus líneas: con las obras siempre de la 1, esa deducción ya
  no dice nada del trabajador. **Propuesta:** solo en la por defecto (R3); la
  marca «sin empresa» se queda. **Alternativa:** no tocar la regla (en la
  práctica da lo mismo, salvo líneas viejas en obras de otra empresa, como la
  0009 y la 0025 de Porsan del maestro local, que harían aparecer al
  trabajador en la 28).
- **D3 · `otra_empresa` y «sin empresa».** **Propuesta:** `otra_empresa`
  pasa a significar «obra que no es de la empresa de las obras» (R5); esas
  líneas se ven, cuentan para el 100 % y el transfer las omite con motivo
  (D5 de F-024, con la referencia nueva). «Sin empresa» del trabajador no
  cambia. **Alternativa:** retirar `otra_empresa` del esquema (rompe el
  contrato API ↔ front y esconde por qué una línea no se registra).
- **D4 · Modo pruebas.** La D3 de F-024 (error con otra empresa elegida)
  **queda sin objeto**: la obra de pruebas se busca en la empresa de la
  línea, que ahora es siempre la de las obras. No exige código; el test R19
  de F-024 se conserva como prueba de que un error por obra del transfer se
  propaga y no se traza. Solo se pide confirmarlo.
- **D5 · Dónde se verifica R13.** **Propuesta:** api de la rama y transfer
  **locales**, el transfer con `OBRA_PRUEBAS_FORZAR=true` (la comprobación de
  empresa de la obra de origen corre igual en pruebas), leyendo Sigrid real
  vía `sigrid-api`; tras desplegar, en producción solo la comprobación visual
  del cuadrante con la 18, **sin pulsar Registrar**. **Alternativa:**
  preflight en producción con la api desplegada: es de solo lectura, pero el
  transfer de producción está en real y el botón del front lleva a ejecutar
  tras confirmar; si se hace, lo hace el humano.
