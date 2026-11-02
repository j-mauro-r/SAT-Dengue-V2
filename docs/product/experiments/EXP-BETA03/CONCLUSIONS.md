# EXP-BETA03 V1 — políticas de alerta sobre puntuaciones congeladas

**Ejecución: `COMPLETED_WITH_LIMITATIONS`; hipótesis: `NO_RESPALDADA`.**
Comparación retrospectiva real del 2 de noviembre de 2026. Reducir falsas
alertas no produjo una mejora conjunta aceptable de detección y carga.

## Pregunta e hipótesis

¿Puede una regla restringida de umbral, global o departamental regularizada,
reducir falsas alertas sin perder más de 2 pp de sensibilidad frente a R0 ni
trasladar el deterioro entre territorios? La alternativa de aprendizaje sobre
negativos difíciles era condicional, no un componente obligatorio.
[Diseño de Fase 4](../EXP-BETA/DESING.md), [protocolo](protocol.json).

## Diseño efectivamente evaluado

R0 es M00/XGBoost/onset, elegido por prioridad de referencia y disponibilidad
verificada de sus puntuaciones nativas, no por un ranking de evaluación de
BETA01/02. Se conservan predictor, calibrador y roles históricos; selección de
política en julio–diciembre de Y−1 y evaluación en Y, con embargo temporal.
**Cero ajustes de estimador o calibrador.** [Implementación](README.md).

GLOBAL usa el selector existente que maximiza detecciones bajo el presupuesto
de ≤1 FA por municipio-año elegible, respetando empates completos; en empate
prefiere menos FA y después mayor umbral. La política sin alertas es admisible.
R0 conserva sus alertas históricas y se recalcula su tasa con el mismo denominador
elegible de BETA. Su selección original usaba exposición monitoreada más amplia:
esta es una comparación de política/denominador, no un algoritmo nuevo ni un
incumplimiento retroactivo del contrato histórico de R0.

DEPARTMENT solo se evalúa si ambos departamentos tienen ≥24 filas y ≥3 ejemplos
de cada clase en desarrollo y una brecha de carga GLOBAL ≥0,5 FA/municipio-año.
Regulariza hacia GLOBAL con 24 pseudofilas y conserva el umbral que respete
el límite local de desarrollo; sin soporte retorna a GLOBAL. No hay umbrales
municipales libres. Los criterios de carga y margen descriptivo ≥−2 pp fueron
ratificados antes de evaluar. [DEC-139](../../traking-concluciones.md#dec-139-freeze-exp-beta03-before-policy-evaluation).

Claves, etiquetas H5, fechas y probabilidades son idénticas en cada par R0/política:
2020/2021/2022/2024; T+1 = 2.653 filas/313 inicios y T+2 = 2.422/219.
Ambos requieren no exceso en T; T+2 conserva la transición de inicio, distinta
del exceso marginal NB2. Exposición = filas elegibles/12. El año 2024 es estrés
consumido; no se evaluó 2025 ni se usaron errores de evaluación para entrenar.

## Resultados reales y comparación con R0

Fuente: [RESULTS](RESULTS.md), [54 estratos](METRICS_BY_STRATUM.csv).
Las tasas agrupadas usan sumas de eventos y exposición, no medias de tasas.

| Horizonte | Política | Detecciones / inicios | Sensibilidad | FA | FA / municipio-año | Δ sensibilidad vs R0 |
|---|---|---:|---:|---:|---:|---:|
| T+1 | R0 | 142 / 313 | 45,37% | 231 | 1,044855 | referencia |
| T+1 | GLOBAL | 96 / 313 | 30,67% | 136 | 0,615153 | −14,70 pp |
| T+2 | R0 | 86 / 219 | 39,27% | 256 | 1,268373 | referencia |
| T+2 | GLOBAL | 57 / 219 | 26,03% | 175 | 0,867052 | −13,24 pp |

**Hallazgo positivo acotado:** GLOBAL reduce 95 FA en T+1 y 81 en T+2; logra el
presupuesto agregado sin modificar probabilidades. **Resultado negativo decisivo:**
omite 46 y 29 inicios adicionales, respectivamente, excediendo ampliamente el
margen. Solo **8/24** estratos GLOBAL horizonte/año/departamento-o-total cumplen
ambos criterios. No son 24 replicaciones independientes.

En 2021/2022 las decisiones GLOBAL coinciden con R0. La pérdida se concentra
en 2020 y el estrés 2024. Aunque el promedio cumpla el presupuesto, GLOBAL
excede 1 en Meta T+1/2022 (1,028571), Tolima T+1/2024 (1,210084) y ambos
departamentos T+2/2022 (Meta 2,597938; Tolima 1,395973). Factibilidad en
desarrollo no garantiza carga futura. Brier/AP permanecen iguales porque
las probabilidades no cambian: T+1 0,109712/0,260911; T+2 0,088390/0,161573.

## Adaptación territorial y componentes condicionales

El soporte predeclarado solo habilitó DEPARTMENT en 2020, ambos horizontes.
Estas filas se comparan **solo con R0 de 2020**, no con sus totales de cuatro años.

| Horizonte, cohorte 2020 | R0 detecciones / FA | DEPARTMENT detecciones / inicios | Sensibilidad DEPARTMENT | FA | FA / municipio-año | Δ sensibilidad |
|---|---:|---:|---:|---:|---:|---:|
| T+1, 661 filas | 31 / 74 | 10 / 69 | 14,49% | 14 | 0,254160 | −30,43 pp |
| T+2, 588 filas | 25 / 75 | 11 / 51 | 21,57% | 31 | 0,632653 | −27,45 pp |

Ninguno de sus **6** estratos emparejados cumple conjuntamente. En los otros
seis cortes horizonte/año el contraste territorial incremental es `NO_EVALUABLE`
y se retorna a GLOBAL; no se inventa otro brazo duplicando el retorno.

Los ocho cortes de selección nativa tienen **cero falsos positivos con puntuación
≥0,8**. Además, cada predictor congelado dispone de un único bloque semestral
de selección, insuficiente para demostrar recurrencia independiente y reservar
otro bloque intacto. Aprendizaje asimétrico y hard-negative mining:
**`CONDICIONAL_NO_JUSTIFICADO`**, sin ejecución ni métricas atribuibles.
No se implementó un segundo clasificador en cascada ni aprendizaje por refuerzo.
[Diagnóstico y resultados](RESULTS.md).

## Conclusión, límites e implicaciones

La hipótesis de la política congelada queda **`NO_RESPALDADA`**: menor carga
coexiste con pérdidas inadmisibles de detección y fallos territoriales. Esto
no refuta toda posible política local ni los métodos de negativos difíciles
que no se evaluaron. Mantener R0 como referencia, separar calidad probabilística
de decisión y conservar controles por año/departamento; no promover GLOBAL o
DEPARTMENT por su menor volumen de alertas.

Los perfiles carecen de fuente validada; no hubo entrenamiento nacional.
Los datos consolidados y H5 no acreditan inicio clínico ni oportunidad de reporte.
Cuatro años reutilizados, con 2024 consumido, no ofrecen confirmación independiente.
No inferioridad estadística `UNAVAILABLE`; superioridad `NOT_ESTABLISHED`.
**G5 `NOT_APPROVED`; `champion: not_selected`.** Cualquier investigación adicional
necesita una hipótesis propia y evidencia temporal no reutilizada como confirmación.

## Trazabilidad y preservación

- Protocolo congelado en `8fc0a8e`, SHA-256
  `0b8b5f22ef678039147fd55dafd7938d70de6333c85afe631a31c3e8386ee386`;
  ejecución desde `04a2716934d89a53e635fbcb2c28120489c3599a`.
- Publicación: `tmp/kedro-migration/exp-beta03-runs/9f25fb41dc069f8c2680381bc6d02b1a032d7d1e6152d457ecd94827481c76fe/`.
  Manifiesto SHA-256: `f95c1d27e89e7fd04a8f1a5d7d62c2049de08ef5c0b19c196be3d49c9c770cfc`.
  Ocho payloads más manifiesto, 11.399 filas, 54 estratos y 30 comparaciones.
- `metrics.csv`, `pooled.json`, `comparisons_r0.json` y `policies.json` sustentan
  efectos y soporte. Esta consolidación verificó hashes de los ocho payloads y
  correspondencia de la tabla pública; no repitió el grafo ni los 70 tests técnicos
  históricos. [RESULTS](RESULTS.md) registra la reproducción anterior de los nueve
  archivos y la preservación de 437 archivos históricos y 27 payloads BETA02.
- [Conclusión integradora](../EXP-BETA/CONCLUSIONS.md) conserva el cierre del
  programa y sus identidades; los artefactos privados siguen fuera de Git.
