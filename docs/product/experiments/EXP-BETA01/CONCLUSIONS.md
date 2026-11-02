# EXP-BETA01 V1 — aprendizaje compartido y adaptación territorial

**Estado de ejecución: `COMPLETED_WITH_LIMITATIONS`.** Evidencia real retrospectiva
de Meta–Tolima, ejecutada el 1 de noviembre de 2026. Esta consolidación documental
no constituye otra ejecución. Adaptación local: **`NO_RESPALDADA`**; transferencia
nacional G1 y beneficio de introducir pooling: **`NO_EVALUABLE`**.

## Pregunta e hipótesis

¿Compartir información entre municipios y adaptar ligeramente el predictor por
territorio mejora la detección de inicios H5 sin exceder la carga de falsas alertas
ni perder más de 2 puntos porcentuales (pp) de sensibilidad respecto de R0?
El [diseño](../EXP-BETA/DESING.md) separa expansión nacional y adaptación local.
R0 ya agrupaba los 76 municipios: G0 no introduce por primera vez aprendizaje
compartido. Por ello, G0 frente a R0 compara procedimientos, no identifica un
efecto causal de pooling. [Implementación](../EXP-BETA/PHASE2_IMPLEMENTATION.md).

## Diseño efectivamente evaluado

El [protocolo congelado](protocol.phase2.json) fija XGBoost de 80 árboles,
profundidad 2, tasa de aprendizaje 0,05 y ninguna búsqueda. G0 agrupa Meta y
Tolima; L1 conserva ese predictor y añade un intercepto residual por departamento,
penalización 10, mínimo 24 filas y tres observaciones de cada clase, con retorno
al predictor global si falta soporte. No existen 76 modelos municipales.
Se evaluaron G0 y L1 con clima OFF/ON; OFF retira exactamente nueve variables
climáticas, conservando las mismas filas completas de ON y las mismas etiquetas.

Para el año objetivo Y: entrenamiento hasta Y−4, calibración global en Y−3,
adaptación en Y−2, selección de umbral en Y−1 y evaluación en Y, con embargos
por origen entre roles. Los años son 2020, 2021, 2022 y 2024; este último es
estrés ya consumido. No se evaluó 2025. Los cortes son comunes a todos los
municipios. R0 mantiene su entrenamiento, probabilidades y decisiones históricos.

La cohorte exige no exceso observado en T. En T+1, inicio y exceso coinciden;
en T+2, inicio exige la transición de no exceso en T+1 a exceso en T+2. Ese
estado futuro define la etiqueta, nunca un predictor ni un filtro por resultado.
Las claves, objetivos y periodos coinciden exactamente con R0: 2.653 filas y
313 inicios en T+1; 2.422 y 219 en T+2. La exposición es, respectivamente,
**2.653/12** y **2.422/12** municipio-años elegibles, no 76 multiplicado por cuatro.

El criterio adoptado antes del ajuste exige ≤1 falsa alerta por municipio-año
y diferencia de sensibilidad ≥−2 pp frente a R0, con controles por año y
departamento. Los umbrales se eligen exclusivamente en selección, conservando
empates de puntuación completos. Cumplimiento descriptivo no equivale a no
inferioridad estadística. [DEC-137](../../traking-concluciones.md#dec-137-adopt-exp-beta01-sensitivityload-criteria-before-fitting).

## Resultados reales y comparación con R0

Se suman conteos y exposición de los cuatro años, sin promediar tasas anuales.
Sensibilidad = detecciones/inicios; FA = falsas alertas de inicio; carga =
FA/(filas elegibles/12). Los decimales son de presentación; los criterios usan
los valores sin redondear. Fuente: [resultados originales](../EXP-BETA/RESULTS.md)
y [120 estratos persistidos](../EXP-BETA/RESULTS_BY_STRATUM.csv).

| Horizonte | Brazo | Clima | Detecciones / inicios | Sensibilidad | FA | FA / municipio-año | Brier |
|---|---|---|---:|---:|---:|---:|---:|
| T+1 | R0 | histórico | 142 / 313 | 45,37% | 231 | 1,044855 | 0,109712 |
| T+1 | G0 | OFF | 146 / 313 | 46,65% | 179 | 0,809649 | 0,094352 |
| T+1 | G0 | ON | 152 / 313 | 48,56% | 204 | 0,922729 | 0,094855 |
| T+1 | L1 | OFF | 138 / 313 | 44,09% | 175 | 0,791557 | 0,093816 |
| T+1 | L1 | ON | 152 / 313 | 48,56% | 210 | 0,949868 | 0,094386 |
| T+2 | R0 | histórico | 86 / 219 | 39,27% | 256 | 1,268373 | 0,088390 |
| T+2 | G0 | OFF | 62 / 219 | 28,31% | 161 | 0,797688 | 0,079653 |
| T+2 | G0 | ON | 67 / 219 | 30,59% | 152 | 0,753097 | 0,080261 |
| T+2 | L1 | OFF | 67 / 219 | 30,59% | 164 | 0,812552 | 0,079350 |
| T+2 | L1 | ON | 64 / 219 | 29,22% | 167 | 0,827415 | 0,079776 |

**Observación favorable:** G0 OFF/ON detecta cuatro/diez inicios adicionales en
T+1 con 52/27 falsas alertas menos que R0. Es un resultado agregado de los
procedimientos completos, compatible con señal útil y sin selección de ganador.
El contraste climático G0 ON−OFF añade seis detecciones y 25 FA en T+1; en T+2
añade cinco detecciones y reduce nueve FA. El clima aporta información condicional,
sin demostrar una ventaja general ni rescatar T+2 frente a R0.

**Resultado negativo:** todas las variantes pierden 8,68–10,96 pp de sensibilidad
en T+2 respecto de R0, aunque cumplan el presupuesto agregado. L1 incumple los
criterios conjuntos en **43/48** estratos horizonte/año/departamento-o-total/clima.
Con clima ON, L1 frente a G0 mantiene 152 detecciones T+1 con seis FA más;
en T+2 pierde tres detecciones y añade 15 FA. Sin clima, las direcciones también
son mixtas. Brier menor no subsana ese deterioro decisional. Los estratos agregados
y departamentales se solapan; 48 no representa 48 experimentos independientes.

## Conclusión, limitaciones e implicaciones

La adaptación departamental fija queda **`NO_RESPALDADA`** para el objetivo
conjunto. Los beneficios descriptivos de G0 T+1 no autorizan sustituir R0 ni
declarar una mejora estable. La hipótesis global permanece **`NO_EVALUABLE`**:
el histórico ya hacía pooling y G1 no tuvo una tabla nacional compatible admitida.
Los perfiles de transmisión tampoco tienen una fuente validada en este contrato.

La [auditoría de fuentes incorporada a la síntesis](../analisis-6.md#f-limitaciones-de-exp-beta-v1)
aclara el alcance: los originales nacionales siguen disponibles localmente;
**fuentes nacionales disponibles no equivale a entrenamiento nacional ejecutado**.
No se reinterpreta G1 como fracaso predictivo ni se modifica su protocolo.

Los cuatro años reutilizados, los datos consolidados y H5 como proxy impiden
afirmar confirmación temporal independiente, anticipación operativa o superioridad.
No inferioridad estadística: `UNAVAILABLE`; superioridad: `NOT_ESTABLISHED`.
Mantener R0, H5, contrastes climáticos emparejados y controles territoriales;
una ampliación nacional necesita su propia elegibilidad y evaluación independiente.
No promover L1 como mejora general ni escalar automáticamente a otra arquitectura.
**G5 `NOT_APPROVED`; `champion: not_selected`.**

## Trazabilidad

- Publicación local: `tmp/kedro-migration/exp-beta01-runs/37a0cae62f4d3fa59cede281e032c9abd1b568a90933855b9eebd3b3d3fb5f4a/`.
  Manifiesto SHA-256: `4f6b86fcfcf46dbb47123b33ac29ecc9c23b62e65ac1c83ec460231f04816d7e`.
  `metrics.csv`, `comparisons_r0.json`, `contrasts.csv` y `conclusions.json`
  sustentan los conteos, comparaciones y disposiciones; no son fixtures.
- [Contrato canónico](canonical_model_table_v1.json) y
  [protocolo](protocol.phase2.json) conservan las rutas de identidad originales.
  La [integración del programa](../EXP-BETA/CONCLUSIONS.md) identifica la tabla
  canónica compartida y la preservación histórica.
- [PHASE1](../EXP-BETA/PHASE1.md) y [PHASE2](../EXP-BETA/PHASE2.md) son registros
  históricos de bloqueo en Cloud, superados por la aceptación local descrita en
  [PHASE2_IMPLEMENTATION](../EXP-BETA/PHASE2_IMPLEMENTATION.md), no resultados negativos.
  Esta última registra 64 ajustes reales entre publicaciones y reproducciones,
  con 16 identidades únicas por publicación; L1 comparte los modelos G0.
- En esta consolidación se verificaron hashes de los 25 payloads del manifiesto
  y correspondencia numérica de los 120 estratos públicos con `metrics.csv`.
  No se repitieron ajustes ni inferencia; los tests sintéticos históricos solo
  acreditan comportamiento técnico, no estas métricas científicas.
