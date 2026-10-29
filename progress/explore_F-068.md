<!-- progress/explore_F-068.md -->
# F-068 · Exploración en Sigrid: historial y CI repetidas de los vinculados

Spec-author, 2026-10-28, rama `feature/F-068-propuesta-vinculado-como-titular`.
**Solo lectura**: `POST /api/sql/read` de `sigrid-api` con el
`SigridWriteClient._read` del transfer (lanza ante `truncated`), como en
`progress/explore_F-044_sigrid.md`; todo agregado en SQL. Ni una escritura.
**Sin nombres ni importes por persona**: solo tipos, códigos de obra y de
partida y recuentos. Los scripts viven en el scratchpad del agente.

Universo: recursos no persona con el campo «Recurso Asociado» (F-044 §6);
líneas de partes de trabajo (`con.tip` 35) con partida del presupuesto de la
obra del parte, en la ventana de la propuesta del trabajador
(`PROPUESTA_MESES_ATRAS` = 24: 2024-10 a 2026-10). Un **par** es (vinculado,
obra) con alguna línea en la ventana. Ninguna respuesta `truncated`.

## 1. El historial del vinculado en la obra decide casi siempre

Último mes con líneas del par; gana la partida con más `can` sumado.

| Tipo | Pares | Ganadora única | Empate | Única y hoja activa¹ | Única con su cuenta | Única `CI*` |
|---|---|---|---|---|---|---|
| `TF` | 720 | 716 | 4 | 648 | 619 | 661 |
| `CO` | 460 | 457 | 3 | 372 | 337 | 419 |
| `VE` | 248 | 246 | 2 | 219 | 209 | 224 |
| `CAJA` | 330 | 322 | 8 | 291 | 251 | 309 |
| `VIAJE` | 13 | 13 | 0 | 5 | 0 | 12 |

¹ Hoja activa **con cuenta** (la consulta solo miraba esas): cota inferior.
`VP` (no se vincula, D1b de F-044): 177 pares, 177 únicos.

- **Empates**: menos del 1 % (TF 4, CO 3, VE 2, CAJA 8).
- **Ganadora que no es `CI*`**: TF 55, CO 38, VE 22, CAJA 13 pares. Son meses
  en que el titular iba a otra partida (`CP*`, códigos sin `CI`, p. ej.
  `PC204.01` en la 0695): ver D2 del design.
- **Una sola hoja con su cuenta en la obra** (lo que F-044 propone hoy, R15):
  el historial da **la misma** en TF 543, CO 286, VE 197, CAJA 216 pares y
  **otra** hoja activa en TF 14, CO 21, VE 3, CAJA 29. La enmienda (historial
  antes que la cuenta) cambia esas pocas.
- **Varias hojas con su cuenta** (lo que F-044 deja «sin partida», R16): el
  historial da una única hoja activa en TF 77 de 82, CO 52 de 58, VE 13 de 13,
  CAJA 37 de 40.

## 2. Unidades: casi nunca hay dos horas del mismo vinculado en un mes y obra

Meses-obra con más de una hora del mismo vinculado: TF 0 de 4.978, CO 0 de
2.968, VE 2 de 1.424, CAJA 17 de 1.441, VIAJE 0 de 21. Sumar `can` de todas sus
horas (sin filtrar por la suya) no mezcla unidades en la práctica.

## 3. Las obras con la cuenta repetida (obras con vinculados en 2026)

Solo **cinco obras** tienen 2+ hojas activas con la misma subcuenta de un
vinculado. Por pareja, la descripción es **idéntica** salvo en dos grupos:
el nombre no desempata; lo hace el capítulo.

| Obra | Subcuentas repetidas | Códigos de cada pareja | ¿Misma descripción? |
|---|---|---|---|
| 0678 | `CICO01`, `CICO13`, `CICO15` | `CI.0.xx` / `CI.4.x` | sí |
| 0678 | `CIMP09` (vehículo) | `CI.0.06` / `CI.03P.9` | sí |
| 0692 | `CICO01`, `CICO13`, `CICO15` | `CI.04.xx` / `CI.4.x` | sí |
| 0692 | `CIIN10`, `CIMJ09`, `CIMP09` | `CI.02.10`/`CI.2.10`, `CI.03.02.09`/`CI.03A.9`, `CI.03.01.09`/`CI.03P.9` | sí |
| 0693 | `CICO01`, `CICO13`, `CICO15`, `CIIN10`, `CIMP09` | `CI_F1.…` / `CI_F2.…` (fases) | sí |
| 0694 | `CICO13`, `CICO15`, `CIIN10`, `CIMP09` | `CI.4.x`(`CI.2`, `CI.03P`) / `CI0.04.xx`(`CI0.…`) | sí |
| 0694 | `CICO01` | `CI.4.1`, `CI.4.19_1`, `CI0.04.01` | no |
| 0695 | `CICO01` | `CI.4.1` / `CI.4.1.1` | no |

El padre de cada hoja es el capítulo de su código (`CI.4.13` cuelga de `CI.4`):
código y árbol dicen lo mismo en todos los casos medidos.

## 4. Qué capítulo se usa de verdad en esas obras (líneas de vinculados)

- **0678**: `CI.4.1`, `CI.4.13`, `CI.4.15`, `CI.03P.9` de 2024-10 a 2026-09;
  ninguna línea en `CI.0.*`. El «CI.4 en empate» acierta en TF, CO y CAJA; el
  vehículo (`CI.0.06` / `CI.03P.9`) **no** lo resuelve el CI.4.
- **0692**: hasta 2025-07 en `CI.4.x` (después, solo 3 recursos siguen en
  `CI.4.15`); **desde 2026-02 en `CI.04.x`** (el capítulo nuevo, 14 recursos
  de teléfono). Un «CI.4» literal (`CI.4.`) elegiría el capítulo que se dejó
  de usar; uno numérico (`CI.04` = `CI.4`) deja el empate y la subfila
  «sin partida». Ver D1 del design. El historial resuelve los que ya tienen
  líneas.
- **0693**: las dos fases (`CI_F1`, `CI_F2`) se usan; `CI_F1` hasta 2026-09.
  Ningún «CI.4» las distingue: historial o «sin partida».
- **0694**: hasta 2025-05 en `CI0.04.*`; desde 2025-03 en `CI.4.*`.
- **0695**: `CI.4.1` hasta 2025-01; `CI.4.1.1` desde 2025-01 (ambas en `CI.4`).

## 5. Escala del casamiento por nombre sin cuenta

Las 50 obras con líneas de vinculados en 2026 tienen entre 53 y 182 hojas
activas `CI*` (media 72): el paso «por nombre entre las CI» casa contra ese
universo, no contra dos.

## 6. Consultas (resumen)

(1) por par: último mes, ganadora por `can`, empate, si es hoja activa con
cuenta, si su subcuenta es la del vinculado, si es `CI*`, y cuántas hojas
activas de la obra tienen su subcuenta; (2) meses-obra con más de una hora
por vinculado; (3) obras con 2+ hojas activas por subcuenta (códigos, padre y
si la descripción coincide, sin publicarla); (4) hojas `CI*` activas por
obra; (5) líneas de vinculados por obra y código de partida en las cinco
obras de §3.
