<!-- progress/review_F-015.md -->
# F-015 · Review de cierre — Alta en el Portal Ruesma: tarjeta y usuarios del grupo

**Fecha:** 2026-08-21 · **Rama revisada:** `dev` · **Commits:** `96cf169`,
`682bdef`, `c03240d`, `142676e`, `d14a5b2`

## Veredicto

**APPROVED** (segunda pasada, 2026-08-21 — ver la sección final)

> **Primera pasada: CHANGES_REQUESTED.** Cuatro remates de cierre, ninguno de
> fondo. El líder los cerró en `8c3ce95` y los he verificado uno a uno: el
> detalle está en **«Segunda pasada»**, al final de este informe. Todo lo que
> sigue es la primera pasada, que se conserva íntegra —incluidos los cambios
> requeridos— porque es el rastro de por qué esta feature se cerró como se
> cerró.

Conviene decirlo sin ambigüedad, porque el veredicto binario no lo distingue:
**el trabajo sustantivo de F-015 está hecho y lo he verificado de forma
independiente.** La tarjeta existe, apunta al sitio correcto, está desplegada
y restringida por el grupo; hay 8 personas dentro; no hay ni un identificador
de Entra en este repositorio. Los cinco requisitos R1–R5 se cumplen en lo
esencial.

Lo que falla es el **cierre**: cuatro checkboxes de C1–C5 quedan vacíos, y uno
de ellos —el documento del ecosistema diciendo que esto está «pendiente»
cuando lleva un día en producción— es exactamente el daño que el `CLAUDE.md`
global describe («un documento desactualizado que parece vigente hace más daño
que no tenerlo»). Los cuatro se arreglan en minutos y ninguno obliga a
rehacer nada.

## Nivel de rigor

Declarado en `harness/features.json`: **`documental`**. Verificado contra
`harness/rigor.json` y la tabla de `CHECKPOINTS.md`.

Exige **C1–C3, C3 bis y C5**. **No** exige fase RED, **ni** cobertura, **ni**
campaña de mutación — y no se han reclamado. El diff no toca una sola línea de
código de producción ni de test (ver C3), así que el nivel está bien elegido:
no es una etiqueta usada para esquivar puertas.

Las tres puertas de C4 bis se declaran **N/A por el nivel `documental`**, que
es el motivo escrito que `CHECKPOINTS.md` exige. Tampoco existe
`progress/mutacion_F-015.md`, y es correcto que no exista.

## Checkpoints

### C1 — El arnés está completo y en verde · **[x]**

- [x] `bash harness/init.sh` termina con **exit code 0**. Ejecutado por mí dos
      veces (la segunda comprobando el código de salida explícitamente, por el
      aviso de que hay otro reviewer en el mismo árbol): verde las dos, sin
      rojos transitorios. `102 passed in 2.41s` en la suite raíz, los tres
      servicios en verde por caché, `PUERTA COBERTURA: N/A (rama dev: solo
      aplica en ramas de feature)`.
- [x] Existen los nueve ficheros obligatorios (los lista el propio portero).

Avisos no bloqueantes que el portero ya declara como deuda previa: `ruff` con
179 avisos y `[AVISO] Hay features en estado blocked` (F-008, que está en
review por otro agente).

### C2 — El estado es coherente · **[ ]**

- [x] Una sola feature `in_progress`: F-015.
- [ ] **La rama actual NO es `feature/F-015-portal-tarjeta-y-usuarios`.** Es
      `dev`, y los cinco commits de la feature están directamente en `dev`
      (`git branch --contains d14a5b2` → `dev`). La rama que declara
      `features.json` **no existe** (`git branch -a` lista F-001, F-002,
      F-003, F-004, F-008, F-009 y F-013; ninguna F-015). Ver cambio 3.
- [ ] **`progress/current.md` no describe la sesión activa.** Ver cambio 2.
- [x] Las features `done` tienen su resumen en `progress/history.md`.

### C3 — El código respeta arquitectura y convenciones · **N/A justificado**

**N/A porque la feature no toca código.** No es una exención por conveniencia:
lo he comprobado sobre el diff real, no sobre el informe.
`git diff --stat 96cf169^..d14a5b2` da 8 ficheros, **todos** Markdown o JSON
del arnés:

```
BACKLOG.md | docs/INTEGRACION.md | harness/features.json
progress/spec_F-015.md | specs/F-008-infra-azure/tasks.md
specs/F-015-portal-tarjeta-y-usuarios/{design,requirements,tasks}.md
```

Ni un `.py`, ni un `.js`, ni SQL. Por tanto no hay arquitectura hexagonal que
violar, ni `print()` de debug, ni dependencias nuevas, ni ocasión de tropezar
con las tres trampas del proyecto (escala del porcentaje, postventa, la pluma
única del transfer): ninguna de las tres se roza.

Lo que **sí** aplica de C3 y **sí** se cumple:

- [x] Primera línea con la ruta relativa en los cuatro Markdown nuevos o
      tocados (`docs/INTEGRACION.md`, los tres de `specs/F-015-.../`).
- [x] Sin secretos hardcodeados (barrido completo en la sección R4).

### C3 bis — Documentos que entran de fuera · **N/A justificado**

**N/A porque la feature no añade ni modifica nada en `docs/referencia/`** (el
diff de arriba lo confirma). No hay original ofimático que pudiera haberse
colado.

Aun así **he ejecutado el barrido de datos sensibles** por mi cuenta, porque
es el corazón de esta feature (R4) y no basta con fiarse del informe ajeno.
Patrones y resultado, en la sección R4.

### C4 — La verificación es real · **N/A parcial, justificado**

- [x] **N/A justificado el requisito de tests trazables**: nivel `documental`,
      cero código, y las cinco tareas son verificaciones `MANUAL (humano)` por
      diseño (T1–T5 lo dicen literalmente). No hay comportamiento nuevo que un
      test unitario pudiera fijar: lo que hay que comprobar vive en Entra, en
      otro repositorio y en un navegador.
- [x] Los unit tests del repositorio no tocan red ni BBDD (sin cambios aquí;
      `tests/test_f008_infra_sin_secretos.py`, el único relevante, es lectura
      de ficheros).
- [ ] **Las verificaciones MANUAL no están listadas en
      `progress/current.md`.** Sí están —con su comando exacto y su resultado—
      en `specs/F-015-portal-tarjeta-y-usuarios/tasks.md`, que es donde de
      verdad se leen. Lo cuento dentro del cambio 2 y no como reproche
      aparte: el problema es que `current.md` está congelado en una sesión
      anterior, no que falte la trazabilidad.

### C4 bis — El rigor declarado se cumple · **[x]**

- [x] La feature declara `rigor: "documental"`, valor válido según
      `harness/rigor.json`.
- [x] **Fase RED: N/A** — el nivel `documental` no la exige y no hay código
      cuyo fallo previo pudiera enseñarse.
- [x] **Cobertura: N/A** — el nivel no la exige; además `init.sh` la declaró
      N/A con su motivo impreso (`rama dev: solo aplica en ramas de feature`).
- [x] **Mutación: N/A** — el nivel no la exige; no existe
      `progress/mutacion_F-015.md` y es correcto que no exista. No procede el
      recálculo independiente de alcance y mutantes ni la prueba de control
      del «cero mutantes»: no hay campaña que verificar porque no hay una sola
      línea de Python en el diff.
- [x] **Evidencias:** no hay `progress/impl_F-015.md` porque no hubo
      implementer — el trabajo lo ejecutó el humano y el líder. La evidencia
      equivalente (qué se hizo, quién y con qué comprobación) está en
      `progress/spec_F-015.md` y en los `tasks.md` fechados. Para una feature
      `documental` sin código lo doy por suficiente; los cuatro números de la
      sección «Evidencias» (tests, cobertura, mutantes, tiempo) no tienen
      contenido posible aquí.
- [x] Ningún punto marcado N/A sin justificación escrita.

### C4 ter — Rutas sensibles · **N/A justificado**

**N/A por ausencia de declaración**: no existe `harness/rutas_sensibles.json`
(solo el `.ejemplo.json` y el módulo `.py`). Es el caso mayoritario que
`CHECKPOINTS.md` declara N/A sin nada que justificar. Además `init.sh` no
señaló ninguna ruta tocada.

### C5 — La sesión se cerró bien · **[ ]**

- [ ] **`tasks.md` tiene T7 sin marcar** (`- [ ] T7: Ejecutar bash
      harness/init.sh en verde`). Ver cambio 4.
- [x] Sin ficheros temporales ni artefactos sin trackear: `git status` limpio.
- [ ] **`features.json` no refleja el estado real**: declara
      `"branch": "feature/F-015-portal-tarjeta-y-usuarios"`, que no existe.
      Ver cambio 3.

**Observación sobre el formato de commit** (no la cuento como cambio
requerido): los cinco commits son `F-015: <descripción>`, no
`F-015 Tn: ...`. `CHECKPOINTS.md` reserva el formato corto para features
`sdd=false` y F-015 es `sdd=true`. Dicho esto, aquí una tarea no equivale a un
commit —T1 a T5 son actos manuales del humano en Azure y en otro repositorio,
no cambios en este árbol—, así que el formato prescrito no tenía dónde
aplicarse. Lo señalo para que conste, no para bloquear. Ver la sección de
automejora.

## Cobertura: requisito → evidencia

No hay tests que mapear (nivel `documental`). Lo que sigue es lo que **he
verificado yo**, con el comando o el fichero exacto.

| Req | Qué exige | Cómo lo he verificado | Resultado |
|---|---|---|---|
| **R1** | Tarjeta en el Portal, al FQDN del front, desbloqueada por `dedicacion-portal-users` | Lectura de `front-portal/public/assets/js/catalog.js` (commit `4d7cfa8`) + `curl` al FQDN | **CUMPLE** |
| **R2** | Alta con `setup_front_easyauth.ps1 -Miembros`; la persona entra | `az ad group member list --group 'dedicacion-portal-users' --query "length(@)"` → **8** | **CUMPLE** |
| **R3** | Quien no esté en el grupo no obtiene token | `appRoleAssignmentRequired = True` (evidencia en `spec_F-015.md`) + `curl` → **HTTP 401** | **CUMPLE** |
| **R4** | Ni un objectId, GUID ni tenant en el repositorio | `git grep` con dos patrones + `pytest tests/test_f008_infra_sin_secretos.py` → **53 passed** | **CUMPLE** |
| **R5** | El documento del ecosistema dice quién entra y cómo se da acceso | Lectura de `azure-apps/dedicacion.md` | **CUMPLE en el cuerpo, se contradice en la cabecera** → cambio 1 |

### R1 · La entrada del catálogo, leída (solo lectura, no se ha tocado nada)

`front-portal/public/assets/js/catalog.js`, líneas 132-143, dentro de la
categoría *Obra* y justo detrás de «Partes de Trabajo»:

```js
id: 'dedicacion',  title: 'Dedicación',  category: 'Obra',  icon: 'chart',
url: 'https://ca-dedicacion-front.ashypebble-3c89c6d6.spaincentral.azurecontainerapps.io',
requiredGroupName: 'dedicacion-portal-users',
requiredGroupId: ['<GUID real, correctamente fuera de este repositorio>'],
comingSoon: false,
```

Cuatro comprobaciones, las cuatro pasan:

1. **El FQDN coincide** carácter a carácter con el que documentan
   `docs/INTEGRACION.md` §6 y `progress/current.md` para
   `ca-dedicacion-front`. Y no me he quedado en comparar cadenas: **el FQDN
   responde**. `curl` devuelve **HTTP 401** sin cabeceras de sesión, que es
   justo lo que debe pasar —Easy Auth activo rechazando al anónimo—, no un
   404 ni un DNS que no resuelve. Corrobora R1 y R3 a la vez.
2. **El grupo es el correcto** (`dedicacion-portal-users`) y lleva su GUID
   real puesto, no un marcador.
3. **Sigue el patrón de las demás entradas**: misma forma exacta que
   `partes-trabajo` (líneas 120-131), con `requiredGroupName` +
   `requiredGroupId` como array y `comingSoon: false`.
4. **El icono `chart` existe** en el diccionario `ICONS` de
   `public/assets/js/app.js` (línea 21). No es un detalle menor: un icono
   inventado habría dejado la tarjeta muda en la parrilla. La decisión de
   `chart` sobre `compare` está razonada en `spec_F-015.md` y la comparto —
   `compare` ya lo usa «Comparativos».

### R4 · El barrido de identificadores, ejecutado por mí

Patrones usados sobre **todo el árbol versionado** (`git grep -I`):

1. GUID canónico: `[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-...-[0-9a-fA-F]{12}`
2. Por nombre: `tenant[-_ ]?id|object[-_ ]?id|client[-_ ]?id|subscription[-_ ]?id|principal[-_ ]?id`
3. Correos: `[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}`

**Resultado: ningún identificador real.** Los únicos GUID que aparecen son:

- `00000000-0000-0000-0000-000000000000` en `infra/setup_front_easyauth.ps1:157`
  — la constante de «acceso por defecto» de Entra, igual para todo el tenant
  del mundo, ya analizada y admitida en la review de F-008 y whitelisteada
  explícitamente en `tests/test_f008_infra_sin_secretos.py:72`.
- GUID sintéticos dentro del propio test guardián (líneas 269-270), que son
  precisamente los casos negativos con los que se comprueba que el guardián
  muerde.

Las coincidencias del patrón 2 son **todas** el nombre de la variable o del
parámetro (`--assignee-object-id`, `principalId = $GROUP_ID`, «el objectId NO
se escribe en el repositorio»), nunca un valor. Los dos correos que aparecen
son de ejemplo en comentarios de uso (`persona@ruesma.es` en
`docs/INTEGRACION.md:198`, `ana@`/`luis@` en `setup_front_easyauth.ps1:7`),
heredados de F-008 y sin correspondencia con nadie real.

El GUID del grupo vive **solo** en `catalog.js` de `front-portal`, que es
donde el mecanismo del portal lo exige y donde lo llevan también las otras
seis entradas activas. Es el diseño correcto y se ha respetado.

**R4, el criterio más importante de la feature, está limpio.**

### R3 · La duda de la licencia P1, bien cerrada

Merece un apunte porque es el tipo de cosa que se cierra mal a menudo. La
duda era legítima: sin Entra ID P1, la «asignación requerida» se ignora **en
silencio** y entraría cualquiera del tenant, sin ningún error visible. No se
cerró suponiendo, ni leyendo la SKU: se cerró preguntándole al objeto
concreto (`appRoleAssignmentRequired` → `True`). Eso es evidencia, y mi
`curl` con 401 la corrobora desde fuera.

## Cambios requeridos

Cuatro, todos de cierre, ninguno de fondo.

### 1 · `azure-apps/dedicacion.md` se contradice a sí mismo: la cabecera dice que esto está pendiente

Es el más importante de los cuatro, y el único que toca a un requisito (R5).

El cuerpo del documento (§5, líneas 168-178) está bien: dice que se llega por
la tarjeta, que la dio de alta `front-portal`, quién puede entrar y cómo se
da acceso a alguien nuevo, sin listar a nadie. Perfecto.

Pero el **recuadro de resumen de la cabecera**, líneas 26-27 —que es
exactamente lo que lee alguien de otro proyecto que abre el documento— sigue
diciendo:

> **Acceso:** [...] La tarjeta en el Portal Ruesma y el alta de usuarios
> **están pendientes** (F-015 en el repositorio de origen).

Es falso desde ayer. La tarjeta está desplegada y hay 8 personas dentro. Un
lector que se quede en el recuadro concluye que el sistema es inalcanzable y
que nadie tiene acceso, que es la conclusión contraria a la verdad. El
`CLAUDE.md` global nombra este daño concreto: «un documento desactualizado
que parece vigente hace más daño que no tenerlo».

**Arreglo:** sustituir esas dos líneas por el estado real (tarjeta activa
desde el 2026-08-21, acceso por pertenencia al grupo). **No lo he hecho yo:**
es otro repositorio y tenía instrucción de no tocarlo, y además el reviewer no
corrige.

**Y un dato que corrige lo que se me dijo al encargar la review.** Se me
indicó que la copia «se refrescó igual» y que «ese commit es del humano».
El refresco del contenido sí está; **el commit no existe**. En
`C:\Users\pgris\PycharmProjects\azure-apps`, `git status` devuelve:

```
?? dedicacion.md
```

El fichero está **sin trackear**: nunca se ha commiteado, y `git log --
dedicacion.md` sale vacío. Mientras siga así, el documento del ecosistema
**no existe para nadie más**: no está en el repositorio que los demás
proyectos clonan, y un `git clean` se lo lleva por delante. El commit es del
humano —es su repositorio y así lo fija `design.md`—, pero conviene que sepa
que está pendiente, porque R5 se apoya en ese fichero.

### 2 · `progress/current.md` describe una sesión que ya pasó (C2, C4)

Contradice a `features.json` en su primera línea. Dice **«Ninguna feature en
ejecución»** cuando F-015 está `in_progress` —lo canta el propio portero:
`en curso: ['F-015']`—. Además:

- Habla de **12 features**; `features.json` tiene **13**.
- **No menciona F-015** en ninguna parte, ni en la tabla de estado.
- Sigue diciendo **«Falta decidir D3»**, decisión que se cerró el 2026-08-20
  (el humano da de alta a mano; consta en `spec_F-015.md`).
- Sigue presentando la fase 7 de F-008 como pendiente, cuando se ejecutó.

De aquí sale también el checkbox vacío de C4: las verificaciones MANUAL de
F-015 no están listadas en `current.md`. No pido duplicarlas —están completas
y fechadas en `tasks.md`—, solo que el fichero deje de describir otra sesión.

**No lo he tocado**: es del líder, y así se me indicó.

### 3 · `features.json` declara una rama que no existe (C2, C5)

`"branch": "feature/F-015-portal-tarjeta-y-usuarios"`, pero esa rama no
existe y los cinco commits están en `dev`. El `CLAUDE.md` de este repositorio
lo pone entre las reglas duras: «Cada feature se desarrolla en su rama
`feature/F-XXX-slug`. Nunca commits directos a `dev`».

Dos apuntes para que la decisión sea informada y no un reflejo:

- **No es exclusivo de F-015.** `a59b1b5` («F-008 T31») también está en `dev`
  pese a que `feature/F-008-infra-azure` sí existe. Hay deriva de método, no
  un descuido puntual de esta feature.
- **Rehacerlo ahora no tiene sentido.** Los commits ya están en `dev` y hay
  `origin/dev`; reescribir historia compartida por una feature que no toca
  código sería peor que el problema.

**Arreglo que pido:** que `features.json` diga la verdad (`"branch": "dev"`)
**o** que quede escrito por qué esta feature se trabajó en `dev`. Lo que no
puede quedarse es un campo que apunta a una rama inexistente. La decisión es
del líder o del humano; yo no toco `features.json`.

### 4 · T7 sin marcar en `tasks.md` (C5)

`- [ ] T7: Ejecutar bash harness/init.sh en verde` es la única casilla
pendiente. **La verificación está hecha**: lo he ejecutado yo dos veces, exit
code 0, con `tests/test_f008_infra_sin_secretos.py` incluido y en verde (53
passed). Solo falta marcarla, con la fecha, como se hizo con T1–T6.

## Lo que queda vivo, y de quién es

Se me pidió expresamente mirarlo.

| Cabo suelto | ¿Afecta a F-015? | Dueño |
|---|---|---|
| 4 entradas con `REEMPLAZAR_OBJECT_ID_*` (`bc3`, `contratos`, `facturas`, `residuos`) en `catalog.js` | **No** | `front-portal` / humano |
| `azure-apps/dedicacion.md` sin commitear y con la cabecera obsoleta | **Sí** (R5) | Humano (commit) + líder (texto) — cambio 1 |
| F-008 en `blocked`, en review por otro agente | No | El otro reviewer |

**Sobre los cuatro marcadores: confirmado que no afectan a nuestra tarjeta.**
Los he comprobado uno a uno y los cuatro son `comingSoon: true` con `url: ''`,
es decir, apps que aún no existen y cuyas tarjetas no llevan a ninguna parte
por diseño. El marcador sin sustituir no puede hacer daño porque no hay nada
detrás. Y sobre todo: **son entradas independientes**; el `requiredGroupId` de
una entrada no influye en el de otra. La nuestra tiene su GUID real. No cuenta
contra F-015 y no es trabajo de este proyecto.

**Un cabo que sí se ha cerrado y conviene anotar.** `progress/spec_F-015.md`
avisaba de que la entrada de **Comparativos** tenía
`requiredGroupId: ['REEMPLAZAR_OBJECT_ID_compras_usuarios']` **con
`comingSoon: false`**, lo que sí era peligroso: esa tarjeta se habría
desplegado sin dejar entrar a nadie. Ya no está: hoy Comparativos lleva un
GUID real y `comingSoon: false` (líneas 100-104). El humano lo resolvió antes
de desplegar. El aviso funcionó.

## Automejora del protocolo (propuesta, no aplicada)

Dos cosas que este cierre ha dejado a la vista. **No las he aplicado**, van a
decisión del humano y, si se aceptan, deberían portarse a `arnes-base` según
la regla de propagación.

1. **`CHECKPOINTS.md` C5 no contempla las features sin commits por tarea.**
   Exige «un commit `F-XXX Tn: ...` por tarea», pero en una feature
   `documental` como esta las tareas son actos del humano en Azure y en otro
   repositorio: no producen commits en este árbol, y forzar el formato sería
   teatro. Propongo que C5 admita explícitamente que, cuando una tarea sea
   `MANUAL (humano)` y no genere cambios en el árbol, baste con que quede
   fechada y firmada en `tasks.md`, que es lo que aquí se ha hecho y está
   bien hecho.

2. **El protocolo del reviewer no dice qué hacer cuando el entregable vive en
   otro repositorio.** F-015 tiene su producto principal —la tarjeta— en
   `front-portal`, y su documento de R5 en `azure-apps`. He podido leerlos
   porque están en el mismo disco, pero el protocolo no lo prevé ni obliga a
   comprobar si el cambio está **commiteado** allí. Es justo el agujero por el
   que se ha colado el cambio 1: el contenido estaba, el commit no, y sin
   mirar `git status` del otro repositorio habría dado R5 por bueno.
   Propongo añadir al protocolo: *si la spec sitúa un entregable en otro
   repositorio, el reviewer comprueba su contenido **y** su estado en git
   (trackeado y commiteado), y lo hace constar; nunca escribe en él.*

---

**Resumen para el líder.** F-015 está sustancialmente terminada y bien hecha:
la tarjeta funciona, el acceso está restringido de verdad —comprobado con un
401 real, no de palabra—, hay 8 personas dentro y el repositorio está limpio
de identificadores. Faltan cuatro remates de cierre: la cabecera del documento
del ecosistema (que además sigue sin commitear en `azure-apps`), `current.md`
congelado en la sesión anterior, la rama declarada que no existe, y T7 sin
marcar. Ninguno obliga a rehacer nada; con eso resuelto, esta feature se cierra
sin reservas.

---

# Segunda pasada · 2026-08-21 — **APPROVED**

El líder cerró los cuatro cambios requeridos en `8c3ce95` («F-015: cierra los
cuatro remates de la review de cierre»). **No me he fiado del resumen: he
comprobado los cuatro contra el árbol.** Los cuatro están.

## Los cuatro cambios, verificados

### 1 · La cabecera de `azure-apps/dedicacion.md` · **RESUELTO**

Leído el fichero. El recuadro ya no miente:

> **Acceso: en uso desde el 2026-08-21.** Se entra por la tarjeta
> **«Dedicación»** del Portal Ruesma (categoría *Obra*), y el permiso lo da la
> pertenencia al grupo `dedicacion-portal-users`, con **asignación requerida**
> en la Enterprise App: tener cuenta de Ruesma **no** basta. Para dar acceso a
> alguien nuevo, ver §5.

`grep -n "pendient" dedicacion.md` no devuelve **nada**: la afirmación falsa no
sobrevive en ningún otro punto del documento. El texto nuevo dice las tres
cosas que hacían falta —que está en uso, cómo se llega y quién puede entrar— y
remite a §5 para el alta, sin duplicar el procedimiento ni nombrar a nadie.
**R5 queda cumplido también en la cabecera**, no solo en el cuerpo.

**El fichero sigue sin trackear en `azure-apps` (`?? dedicacion.md`), y me
parece bien que se quede así**: es otro repositorio y el commit es del humano,
como fija `design.md`. Lo que pedía no era el commit, sino que el pendiente
estuviera anotado en vez de olvidado. Lo está: `progress/current.md` líneas
45-47 lo pone como primer punto de lo que espera al humano, **con el motivo**
(«mientras no se commitee, el documento del ecosistema no existe para los
demás proyectos» y un `git clean` se lo lleva). Eso es exactamente lo que
convierte un cabo suelto en un pendiente con dueño.

### 2 · `progress/current.md` · **RESUELTO**

Reescrito entero (183 líneas tocadas). Comprobado punto por punto:

| Lo que fallaba | Ahora |
|---|---|
| «Ninguna feature en ejecución» | línea 4: **F-015 · `in_progress`, en review de cierre** |
| «12 features» | línea 9: **«Estado del backlog (13 features)»** |
| F-015 sin mencionar | 5 apariciones, incluida la tabla de estado (línea 14) |
| «Falta decidir D3» | `grep "D3"` no devuelve **nada** |
| Fase 7 como pendiente | dada por ejecutada |

Añade además la tabla única con **todas** las verificaciones MANUAL fechadas.
Con eso cae también el checkbox pendiente de **C4**: las verificaciones
`MANUAL (humano)` de F-015 ya están listadas en `current.md`, que era el
requisito literal del checkpoint.

### 3 · La rama · **RESUELTO**

`features.json` ya dice `"branch": "dev"` (verificado leyendo el JSON, no el
diff). Se acabó el campo que apuntaba a una rama inexistente.

Y está lo que de verdad pedía, que era el **porqué escrito**:
`current.md` §«Nota de método: por qué hay commits directos en `dev`»
(líneas 54-62) explica que F-015 no toca una línea de código de este
repositorio —su único cambio real vive en `front-portal`— y que se hizo
intercalada con el despliegue en vivo, con el árbol en `dev` para corregir los
scripts sobre la marcha. Recoge la deriva de F-008 que señalé y **cierra
diciendo: «No es la norma y no debe volverse costumbre.»**

Eso es lo que distingue una excepción de una erosión: queda por escrito, con
su motivo y con su fecha de caducidad moral. La acepto.

### 4 · T7 · **RESUELTO**

`tasks.md:25` → `- [x] T7 · HECHA (2026-08-21)`. Y **cero** casillas sin marcar
en el fichero (`grep -c "^- \[ \]"` → `0`).

## Comprobaciones propias de esta segunda pasada

No basta con que los cuatro arreglos estén: hay que comprobar que no rompieron
nada al pasar.

- **`bash harness/init.sh`: ENTORNO LISTO, `exit=0`**, ejecutado por mí.
  `102 passed`, los tres servicios en verde, `PUERTA COBERTURA: N/A (rama dev)`
  con su motivo impreso, ningún `.env` versionado.
- **R4 revalidado**, porque `8c3ce95` tocó `features.json` y `current.md`, que
  son justo donde podría colarse un identificador al reescribir:
  `tests/test_f008_infra_sin_secretos.py` → **53 passed**, y el barrido de GUID
  sobre `progress/current.md`, `harness/features.json` y `specs/` no devuelve
  **ninguna** coincidencia. **Sigue sin entrar ni un objectId en este
  repositorio.**
- **Alcance del commit**: 5 ficheros, todos previstos —`BACKLOG.md` (regenerado
  por el portero), `harness/features.json`, `progress/current.md`,
  `specs/F-015-.../tasks.md`— más `progress/review_F-015.md`, que es este
  informe. **Ni una línea de código.** El nivel `documental` sigue siendo el
  correcto de principio a fin.
- **`git status` limpio**, y `front-portal` intacto (`git status --short` vacío
  allí). Nada del otro reviewer tocado.

## Checkpoints, recorrido final

| | Estado | Nota |
|---|---|---|
| **C1** | **[x]** | `init.sh` exit 0, verificado tres veces en total |
| **C2** | **[x]** | Una sola `in_progress`; rama declarada = rama real, con la excepción escrita; `current.md` describe la sesión activa |
| **C3** | **N/A justificado** | Cero código en el diff, comprobado sobre `git diff --stat` |
| **C3 bis** | **N/A justificado** | No toca `docs/referencia/`; barrido de sensibles ejecutado igualmente |
| **C4** | **[x]** | Tests trazables N/A por nivel `documental` y por ser todo verificación manual; las MANUAL ya listadas en `current.md` |
| **C4 bis** | **[x]** | `rigor: documental` declarado; RED, cobertura y mutación N/A **por el nivel**, justificado por escrito |
| **C4 ter** | **N/A justificado** | No existe `harness/rutas_sensibles.json` |
| **C5** | **[x]** | `tasks.md` sin casillas vacías; árbol limpio; `features.json` refleja el estado real |

**Ningún checkbox vacío en C1–C5. Ningún N/A sin motivo escrito.**

## Veredicto final

**APPROVED.**

Los cinco requisitos se cumplen y los he verificado de forma independiente, no
por informe: la tarjeta existe y es correcta (FQDN que coincide y **responde**,
grupo correcto, icono `chart` que sí está en `ICONS`, mismo patrón que
`partes-trabajo`); el acceso está restringido de verdad (**HTTP 401** al
anónimo y `appRoleAssignmentRequired = True`); hay **8** personas en el grupo
(`az ad group member list`); **no hay ni un identificador de Entra en este
repositorio**, que era el criterio más importante de la feature; y los dos
documentos —`docs/INTEGRACION.md` y la copia del ecosistema— dicen quién puede
entrar y cómo se da acceso, sin listar a nadie por su nombre o su correo.

Queda **un pendiente con dueño y sin plazo del arnés**: commitear
`azure-apps/dedicacion.md`, que es del humano y está anotado con su motivo en
`current.md`. No bloquea el cierre —R5 se cumple en el contenido, y el commit
en otro repositorio nunca fue trabajo de esta feature—, pero **conviene que se
haga pronto**: hasta entonces ese documento no existe para los demás
proyectos.

Los cuatro marcadores `REEMPLAZAR_OBJECT_ID_*` del catálogo del portal siguen
sin ser trabajo de este proyecto y confirmado que no afectan a nuestra tarjeta.

Las dos propuestas de automejora del protocolo siguen en pie, a decisión del
humano y sin aplicar.
