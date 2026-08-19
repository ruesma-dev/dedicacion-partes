<!-- progress/current.md -->
# Trabajo en curso

**F-001 · Primera suite de tests de `dedicacion-api`: la regla del 100 %**
Rama `feature/F-001-tests-estados-api` · `sdd: false` · rigor `estandar`
Estado: **implementación terminada, pendiente de review.**

## Tarea en curso

Ninguna: las cuatro tareas derivadas de los `acceptance` están hechas y
commiteadas. Lo siguiente es el **reviewer** contra `CHECKPOINTS.md`.

| Tarea | Estado | Commit |
|---|---|---|
| T1 · `tests/`, `conftest.py` y test de suite offline | [x] | `5a1b54d` |
| T2 · Cuatro estados, borde de la épsilon y desviación | [x] | `fddef04` |
| T3 · `resumir()` y descarte de la baja sin líneas | [x] | `a2f58aa` |
| — · Tests nuevos sin avisos de ruff | [x] | `7760080` |
| T4 · Portero, fase RED, mutación e informe | [x] | commit de cierre |

**Informe completo: `progress/impl_F-001.md`.**
**Campaña de mutación: `progress/mutacion_F-001.md`.**

## Estado verificado (salida real, no «debería funcionar»)

- `bash harness/init.sh` → **ENTORNO LISTO**, exit 0, con la línea
  `[OK] servicio api (services/dedicacion-api): pytest en verde`.
- Suite del api: **21 passed** en 0,10 s. `domain/estados.py` al **100 %**.
- Fase RED: **7 roturas deliberadas de `estados.py` en una copia aislada,
  7 cazadas** por la suite. Trazas pegadas en el informe.
- ruff: **164 avisos, los mismos de antes**; los ficheros nuevos salen
  limpios.

## Decisiones tomadas en esta sesión

1. **`conftest.py` con el `sys.path.insert` en un único sitio**, en vez de
   repetirlo en la cabecera de cada test como hace el transfer.
2. **Dos casos de épsilon de más** (99,995 % y 100,005 %) además de los dos
   que pide el `acceptance`: son los únicos que distinguen `<=` de `<`, y así
   quedó demostrado al romper el código.
3. **Se cubre también `calcular_desviacion`**, que el `acceptance` no nombra
   pero comparte la guarda de «0 líneas» con `calcular_estado`.
4. Los 11 avisos de ruff que introdujeron los ficheros nuevos se corrigieron
   en el acto: la deuda previa no crece con esta feature.

## Desviaciones respecto al alcance aprobado

Ninguna sobre producción: **cero ficheros de producción modificados**
(`git diff dev..HEAD --name-only` devuelve solo los tres ficheros de
`tests/`). El único commit no previsto es el de lint, que toca únicamente los
ficheros de test recién creados.

## Puntos que el reviewer debe mirar con calma

1. **La puerta de cobertura salió `N/A`** con su motivo impreso: «F-001 no
   cambia líneas Python de producción frente a dev». Es correcto por diseño
   —`harness/alcance.py` excluye el segmento de ruta `tests`— y **no** un
   fallo de la herramienta, así que no se marcó `blocked`. Igual pasa con la
   campaña de mutación: **0 mutantes generados**. Ambas cosas están razonadas
   en `progress/impl_F-001.md` § 5, con la mutación manual como sustituto
   real.
2. **Primera vez que se ejerce la puerta de cobertura en este repositorio.**
   Conviene que quede validado que el `N/A` es el comportamiento esperado.

## Verificaciones MANUAL (humano) pendientes

**Ninguna para F-001.** No toca producción, no escribe en Sigrid, no toca la
BBDD y no cambia comportamiento alguno.

## Pendiente de decisión del humano (viene de la sesión anterior, sigue vivo)

- Validar la sección «Semántica de dominio imprescindible» de
  `docs/ARCHITECTURE.md`, escrita leyendo el código y no hablando con
  Administración.
- Las dos contradicciones marcadas ⚠ en ese documento (destino e imputación
  de postventa, y qué cuenta como conflicto en obra normal) siguen abiertas y
  son **F-002**. Hasta resolverlas no se escribe en producción.
- **Higiene sugerida, no hecha** (fuera del alcance de F-001): el repositorio
  versiona `.coverage` y `coverage.json` de la raíz y del transfer sin
  tenerlos en `.gitignore`. F-001 añade los del api por consistencia con ese
  precedente; lo correcto sería ignorarlos y sacarlos del índice. Candidato a
  feature de higiene.
