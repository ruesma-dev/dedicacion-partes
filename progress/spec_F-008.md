<!-- progress/spec_F-008.md -->
# F-008 · Infraestructura y despliegue en Azure — spec escrita

**Fecha:** 2026-08-20 · **Rama:** `feature/F-008-infra-azure` ·
**Autor:** subagente `spec-author`.

Entregado: `specs/F-008-infra-azure/` con `requirements.md` (36 requisitos
EARS), `design.md` (11 secciones) y `tasks.md` (33 tareas en 8 fases).
**No se ha tocado código, ni ejecutado ningún comando de Azure, ni
desplegado nada.**

---

## 1 · Decisiones que necesita cerrar el humano

Las fases 1–4 de `tasks.md` no dependen de ninguna de ellas y pueden
arrancar ya. De la fase 5 en adelante, sí.

### D1 · Dónde vive la BBDD `dedicacion` — **la decisión grande**

Hoy `PG_HOST=localhost` y no hay decisión escrita. Tres opciones en
`design.md` §3:

- **A · Base propia `dedicacion` en `psql-albaranes-rs9k2`** (seríamos el
  quinto inquilino, tras albaranes, partes, datamart y postventa).
  A favor: coste marginal cero, mismo patrón y vocabulario que el resto del
  ecosistema, precedente documentado del 2026-08-19.
  En contra: disco de **32 GB compartido que solo crece** —el 2026-08-09
  llegó al 93,4 % y el servidor quedó en solo-lectura diez minutos por el
  build de otro proyecto—, **punto de restauración del servidor entero** y
  cupo de conexiones repartido entre cinco proyectos.
- **B · Servidor PostgreSQL propio.** Aislamiento total, coste mensual nuevo
  por una base de kilobytes y otro servidor que mantener.
- **C · No persistir en Azure.** Descartada: un Container App no tiene disco
  persistente y el objetivo declarado es probar fuera del portátil.

**Lo que recomienda la spec: A**, con las cuatro salvaguardas que
`postventa-incidencias` dejó escritas (base y rol creados **una vez por una
persona**, rol de aplicación propio y no el admin del servidor, nada a nivel
de servidor, `PG_SSLMODE=require`). La spec **no decide**: hace falta el
visto bueno.

### D1b · Esquema `public` o esquema nominado

`postventa` usa esquema propio con `search_path` sin `public`. La spec
recomienda **`public` dentro de nuestra base**, porque la base es propia y es
lo que hacen `albaranes` y `partes`.

**Hay que decidirlo AHORA, no después:** cambiar a esquema nominado obliga a
tocar `orm_models.py` y el `search_path` de todas las sesiones, y eso no es
barato una vez hay datos.

### D2 · Qué se expone públicamente

La spec propone: **solo el front** con ingress externo; api y transfer
**internos**.

El caso de la api no es de comodidad. `deps.py:92` (`obtener_usuario`) se
limita a leer la cabecera `X-Usuario` y creérsela: **la api no tiene
autenticación propia**. Con ingress externo, cualquiera en Internet podría
llamar a `registro/ejecutar`, que llama al transfer, que es la única pluma
sobre el ERP. El ingress interno **es** el control de acceso de la api.

Lo que hay que aceptar si se confirma: para probar la api sin navegador hay
que entrar por el front autenticado (`https://<fqdn-front>/api/v1/health`).
No se abre un atajo «temporal».

### D3 · Quién entra en el grupo `dedicacion-portal-users`

Easy Auth con Enterprise App de asignación requerida: solo los miembros del
grupo obtienen token. Hace falta la lista inicial de personas.

### D4 · Réplicas mínimas (coste frente a arranque en frío)

La spec propone `min-replicas 1` en los tres servicios: tres contenedores
siempre encendidos, comportamiento predecible mientras se valida. La palanca
de coste es bajar api y transfer a `min-replicas 0` (`max` sigue siendo 1 en
los dos); a cambio, la primera petición de cada rato se hace esperar, y en el
caso del transfer eso cae dentro del preflight, que es donde el usuario está
mirando.

### D5 · Una clave de `sigrid-api` que no pueda escribir

Hoy la api y el transfer referencian **la misma** function key. Lo que impide
que la api escriba es que su código no tiene rutas de escritura, no la
credencial. Si `sigrid-api` admite claves distintas por consumidor, la api
debería llevar una de solo lectura. Es una pregunta para el dueño de ese
proyecto; no bloquea el despliegue, pero conviene preguntarlo antes de que el
entorno esté vivo.

---

## 2 · Hallazgos del estudio que el humano debería conocer

Salieron leyendo el código para escribir la spec. Los tres primeros están ya
convertidos en requisitos con test.

1. **`dedicacion-api` crea la base de datos y el rol en cada arranque.**
   `infrastructure/db/database.py::asegurar_base_datos` conecta como
   **administrador del servidor** y ejecuta `CREATE ROLE` / `CREATE DATABASE`.
   Contra `localhost` es una comodidad; contra `psql-albaranes-rs9k2` es justo
   lo que el ecosistema prohíbe por escrito. Se resuelve con
   `AUTO_CREATE_DATABASE` (por defecto `false`, seguro por defecto) y un
   cortocircuito que **ni siquiera abre la conexión** (R13–R16, T1–T4).
2. **Los timeouts encadenados están al revés.** El front espera 120 s y la
   api espera 180 s al transfer: el front se rinde **antes**, y el usuario
   vería un error de un registro que sí se estaba haciendo. Se corrige
   subiendo el front a 200 s, por debajo del corte de **230 s** del
   balanceador de Azure (R28).
3. **El transfer no tiene `Dockerfile`.** Es el único de los tres. Sin él no
   hay imagen que desplegar (R26, T7).
4. **`DEFAULT_USER=local` en el front.** Si llegara una petición sin cabecera
   de Easy Auth, la auditoría registraría `local`, que parece un nombre
   legítimo. En Azure se despliega `desconocido` (R12).
5. **`/health` del front no será alcanzable anónimamente.** Con Easy Auth y
   login obligatorio, un `curl` anónimo recibe una redirección al login. No es
   un fallo; hay que saberlo antes de perder una tarde creyendo que el
   servicio está caído (R35).
6. **La api y el front sí tienen `Dockerfile`, pero `partes` usa `latest`.**
   `docs/CONVENTIONS.md` exige tag fechado `rAAAAMMDD-HHmm` sin reescribir.
   La spec se separa aquí del patrón de `partes` a propósito, y añade
   `infra/imagenes.json` versionado para que «qué código está desplegado» se
   responda desde git (R23, R24).

---

## 3 · Aviso de coordinación con F-002

**Hay una fila de prueba viva en Sigrid** (`hmores.ide=403039`, parte
`PT26/00296`, obra `0404`, marca `PRUEBA-PORC`) que el humano quiere ver en
la pantalla de partes del ERP antes de borrarla (`progress/current.md`).

Probar el registro desde el entorno desplegado escribirá **más** líneas
`PRUEBA-PORC` en la misma obra y el mismo mes, y ya no se distinguirán de esa.
Por eso toda la fase 7 de `tasks.md` lleva como **precondición** cerrar esa
comprobación, y T29 se detiene en `registro/preflight` sin ejecutar
`registro/ejecutar`.

---

## 4 · Nota de rigor (`critico`)

Esta feature es **mayoritariamente scripts de infraestructura y acciones
sobre una suscripción de Azure**, y así está dicho en `design.md` §8 en vez
de disimulado.

- **Con test automático** (donde se aplican fase RED, cobertura ≥ 80 % de
  líneas cambiadas y mutación con cero supervivientes): el bootstrap de la
  base de datos de `dedicacion-api`, el guardián de secretos sobre `infra/`,
  el inventario de imágenes y `.dockerignore`, la propagación de la identidad
  de Easy Auth en el front, y el test que documenta que la api no valida nada.
- **Por revisión del reviewer contra criterios escritos**: los `.ps1`.
- **MANUAL (humano)**: todo lo que crea recursos, gasta dinero o toca la
  suscripción. Ocho tareas (T24–T31), cada una con su comando `az` exacto y
  su resultado esperado.

No se han inventado tests de adorno para cuadrar el expediente.
`harness/alcance.py` solo mide ficheros `.py` fuera de `tests/`, `specs/`,
`progress/` y `docs/`, así que el alcance de mutación será el bootstrap de la
base de datos y poco más — que es exactamente donde se quiere la vigilancia.
