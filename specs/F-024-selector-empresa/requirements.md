<!-- specs/F-024-selector-empresa/requirements.md -->
# F-024 · Selector de empresa arriba a la derecha, Construcciones Ruesma por defecto

Rigor `estandar`. Servicios: **`dedicacion-api`** (filtra y decide la empresa
de cada línea), **`dedicacion-front`** (selector y paso del parámetro, sin
lógica) y **`dedicacion-transfer`** (solo el valor de `obra_destino` en el
corte por obra de otra empresa; el contrato no cambia). Regla de dominio:
[`docs/ARCHITECTURE.md#regla-empresa`](../../docs/ARCHITECTURE.md#regla-empresa).

Ya decidido por el humano: selector arriba a la derecha; empresa 1 por
defecto; filtra obras y recursos; **se imputa a la empresa filtrada**.

Glosario: **E** = empresa elegida en la petición. **Por defecto** = el ajuste
`EMPRESA_IMPUTACION` (1). Empresa de un trabajador u obra = su `empresa`
(`con.emp`, F-023), que puede ser NULL en filas desactivadas antes de F-023.

## 1. Lista de empresas y selector

- **R1.** CUANDO se pide `GET /api/v1/empresas`, la API debe devolver
  `por_defecto` y `empresas`: las que tienen al menos un trabajador **activo**
  en el maestro, más la por defecto aunque no tenga ninguno, ordenadas por
  número, cada una con `empresa` y `nombre`.
- **R2.** El nombre de cada empresa debe salir de `config.yaml`
  (`empresas.nombres`). SI una empresa no tiene nombre configurado, ENTONCES
  la API debe devolver `"Empresa N"`. (Ver D1.)
- **R3.** CUANDO el usuario entra sin empresa en la URL, el front debe
  enseñar el selector en la esquina superior derecha con `por_defecto`
  seleccionada (Construcciones Ruesma).
- **R4.** CUANDO el usuario cambia de empresa, el front debe recargar el
  cuadrante del periodo en curso con ella y dejarla en la URL
  (`?empresa=N`). SI la URL trae una empresa que no está en la lista,
  ENTONCES el front debe usar `por_defecto`. (Ver D2.)
- **R5.** El front debe mandar la empresa elegida como parámetro `empresa`
  en todas las llamadas a `/api/v1/periodos/...` (cuadrante, asignaciones,
  deshacer, copias, export y registro) y no debe filtrar trabajadores, obras
  ni líneas por empresa por su cuenta.

## 2. El parámetro `empresa` en la API

- **R6.** Todo endpoint de `/api/v1/periodos/{anio}/{mes}/...` que lea,
  resuma, copie, exporte o registre debe aceptar `empresa` por query. SI
  falta, ENTONCES la API debe usar la por defecto. SI no es un entero > 0,
  ENTONCES debe responder 422 sin tocar nada.

## 3. Qué se ve con la empresa E

- **R7.** CUANDO se pide el cuadrante con E, la API debe devolver solo los
  trabajadores **visibles en E** (R8) y `empresa: E` en la respuesta.
- **R8.** Un trabajador con empresa es visible solo en la suya. Un
  trabajador con empresa NULL debe ser visible en cada empresa de las obras
  de sus líneas del periodo; y si ninguna de esas obras tiene empresa, o no
  tiene líneas, solo en la por defecto. (Ver D4.)
- **R9.** La lista `obras` del cuadrante con E debe contener solo obras cuya
  empresa es E (activas, o inactivas con líneas en el periodo). Una obra con
  empresa NULL no se ofrece en ninguna empresa.
- **R10.** Cada trabajador visible debe llevar **todas** sus líneas del
  periodo, también las de obras de otra empresa, y su total y su estado
  (`OK`/`FALTA`/`EXCESO`/`SIN_CARGA`) se calculan sobre todas. (Ver D5.)
- **R11.** Cada línea debe llevar `obra_empresa` (puede ser null) y
  `otra_empresa`, que vale `true` solo si `obra_empresa` no es null y es
  distinta de E. Cada trabajador debe llevar su `empresa` (puede ser null).
- **R12.** El front debe marcar «sin empresa» al trabajador con `empresa`
  null y avisar en cada línea con `otra_empresa` de que no se registrará en
  esta empresa. Es presentación de los campos de R11, sin cálculo.
- **R13.** El resumen del cuadrante y el de las respuestas por fila
  (guardar, deshacer, copiar trabajador) deben contar solo los trabajadores
  visibles en E.

## 4. Copia y export

- **R14.** CUANDO se copia el mes anterior con E, la API solo debe rellenar
  trabajadores activos visibles en E; los contadores de la respuesta se
  refieren solo a ellos.
- **R15.** CUANDO se exporta con E, el Excel debe contener solo los
  trabajadores visibles en E, y el nombre del fichero debe incluir E.

## 5. Registro en Sigrid

- **R16.** CUANDO se pide preflight o ejecutar con E, la API debe mandar al
  transfer solo las líneas de los trabajadores visibles en E, **todas con
  `empresa = E`**. `EMPRESA_IMPUTACION` deja de ser la fuente de la empresa
  de la línea y pasa a ser solo la por defecto de R6. (Ver D6.)
- **R17.** SI una línea de un trabajador visible va a una obra de otra
  empresa, ENTONCES la API debe mandarla igual con `empresa = E`, y la omisión
  con motivo que decide el transfer debe quedar trazada en la asignación
  (`sigrid_estado = omitido`), como cualquier otra omitida.
- **R18.** CUANDO se pide con `trabajador_ide` de un trabajador no visible
  en E, la API no debe llamar al transfer y debe responder `ok: true` con
  `obras: []`.
- **R19.** MIENTRAS el transfer esté en modo pruebas y E no tenga obra de
  pruebas, la API debe devolver en cada obra el `ok: false` y el `error` del
  transfer («obra de pruebas … no encontrada en la empresa E»), y ejecutar no
  debe trazar nada. (Ver D3.)
- **R20.** CUANDO el transfer omite todas las líneas porque la obra de
  origen es de otra empresa que sus líneas, `obra_destino` y `obra_origen`
  del preflight y de ejecutar deben ser la obra de origen **resuelta en
  Sigrid, con su empresa**, no la de entrada con `empresa: null`. En el corte
  por línea sin empresa (no hay obra resuelta) siguen siendo la de entrada.
- **R21.** El contrato API ↔ transfer no debe cambiar: mismos campos de
  entrada y de salida, mismos códigos HTTP.

## 6. Documentación

- **R22.** `docs/ARCHITECTURE.md#regla-empresa`, `docs/INTEGRACION.md`
  (variable `EMPRESA_IMPUTACION`, endpoint `GET /api/v1/empresas`, §9), el
  comentario de `settings.py` y el `.env.example` de la API deben decir que la
  empresa de la línea es la elegida en el selector y que `EMPRESA_IMPUTACION`
  es la por defecto. `azure-apps/dedicacion.md` recibe las mismas piezas
  literales (commit en `azure-apps` del humano).

Fuera de alcance: ver [`design.md` §10](design.md#10-fuera-de-alcance).

## 7. Decisiones abiertas (las valida el humano antes de implementar)

- **D1 · Nombres de las empresas.** Hoy hay trabajadores activos en las
  empresas 1, 18 y 31 (T11 de F-023); obras en 19. **Propuesta:** nombres en
  `config.yaml` (`empresas.nombres`) con `1: Construcciones Ruesma` y
  `28: Porsan`, y «Empresa N» para el resto hasta que alguien los rellene
  (T12, lectura de `auxemp.res` por `auxemp.numemp = con.emp`, la unión que
  usa el data mart). **Alternativa:** sincronizar `auxemp` a una tabla
  `empresa` con el resto de maestros: sin lista a mano, pero con tabla, paso
  de sync y consulta nuevos. Se descarta para F-024 por tamaño.
- **D2 · Dónde vive la empresa elegida.** **Propuesta:** en la URL
  (`?empresa=N`), sin guardarla en servidor ni en `localStorage`: al entrar
  sale la por defecto y un recargo o un enlace conservan la elegida.
  **Alternativas:** por usuario en BBDD (contradice «al entrar, Ruesma») o
  solo en memoria (se pierde al recargar).
- **D3 · Modo pruebas con otra empresa.** La obra `0404` solo existe en la
  empresa 1 (D3 de F-022). **Propuesta:** no cambiar nada: el preflight
  enseña por obra el error del transfer, que nombra la obra de pruebas y la
  empresa, y no se escribe nada (R19). **Alternativas:** dar de alta la
  obra de pruebas en cada empresa (acción de Administración en Sigrid), o
  desviar a la `0404` de la empresa 1 (rompe `#regla-pruebas`: se descarta).
- **D4 · Desactivados con empresa NULL y líneas en el periodo.**
  **Propuesta:** R8, «se ven donde tienen carga»; si no se puede saber, en
  la por defecto; marcados «sin empresa» (R12). **Alternativas:** en todas
  las empresas (cuentan en varios resúmenes) u ocultos (esconden carga: se
  descarta). Las obras NULL no se ofrecen (R9); sus líneas sí se ven.
- **D5 · Líneas del periodo en obras de otra empresa** (p. ej. las 0009 y
  0025 de Porsan del maestro local). **Propuesta:** se ven en la fila, cuentan
  en el 100 %, salen marcadas y, al registrar, el transfer las omite con
  motivo (R10, R17). **Alternativas:** ocultarlas (esconde carga) o que la
  API no las mande (pierde la traza de la omisión).
- **D6 · `EMPRESA_IMPUTACION`.** **Propuesta:** conserva el nombre y pasa a
  ser la «empresa por defecto» (R6, R16): no toca `infra/` y los scripts sin
  empresa siguen funcionando. **Alternativa:** renombrarla a
  `EMPRESA_POR_DEFECTO` (más claro; toca infra, `.env` y `azure-apps`).
- **D7 · Persona con fichas en dos empresas** (D4 de F-023): una fila en
  cada empresa y **cada ficha con su propio 100 %**, como hoy. Un 100 % por
  persona entre empresas sería otra feature. Solo se pide confirmarlo.
