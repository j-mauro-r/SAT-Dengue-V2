# EXP-BETA02 V1 — pronóstico probabilístico de conteos

**Ejecución: `COMPLETED_WITH_LIMITATIONS`; hipótesis del enfoque NB2 marginal:
`NO_RESPALDADA`.** Inicio T+2: **`NO_EVALUABLE`**. Evidencia real del 2 de
noviembre de 2026; esta síntesis no reejecuta el experimento.

## Pregunta e hipótesis

¿Pronosticar una distribución mensual de casos permite alertar mejor sobre
inicios H5 que la referencia binaria R0, preservando sensibilidad y controlando
falsas alertas? La hipótesis se evalúa por utilidad de alertas; menor error de
conteos o Brier no basta. [Diseño de Fase 3](../EXP-BETA/DESING.md) y
[protocolo congelado](protocol.json).

## Diseño experimental real

Se ajustó una regresión binomial negativa NB2 conjunta para Meta y Tolima por
horizonte, año y clima OFF/ON: 16 modelos únicos, sin búsqueda. Enlace log,
varianza `mu + alpha * mu^2`, penalización ridge fija 1 y transformación/
estandarización ajustada solo en entrenamiento. No se entrenó DeepAR ni GRU.
La respuesta son notificaciones, no incidencia estandarizada por población.
[Implementación y roles temporales](README.md).

Para evaluar Y se entrenó hasta Y−2 y se seleccionó política en Y−1, con embargo
de orígenes y corte temporal común entre territorios. Las cohortes OFF/ON exigen
predictores ON completos, no exceso observado en T y conteos/etiquetas conocidos;
coinciden exactamente con R0 en claves, periodos y verdad. Años 2020/2021/2022/2024,
sin evaluar 2025: 2.653 filas/313 inicios T+1 y 2.422/219 T+2. Los 219 inicios
conocidos verifican la cohorte; no producen una probabilidad NB2 de inicio T+2.

Se obtiene riesgo de exceso mediante la cola NB2 estrictamente por encima del
P75 H5 del mes objetivo, calculado desde el origen sin futuro. En T+1 equivale a
inicio dentro de la cohorte. En T+2, las marginales no identifican la probabilidad
conjunta de no exceso T+1 seguido de exceso T+2. No se usa el estado futuro real,
un producto de independencia ni exceso T+2 como sustituto de inicio.

La política selecciona detecciones máximas bajo ≤1 FA por municipio-año elegible
y conserva empates completos. Se exige diferencia de sensibilidad ≥−2 pp frente
a R0, con controles anuales/departamentales, adoptados antes de ajustar.
La exposición es filas elegibles/12. Los ajustes históricos de R0 difieren:
la comparación evalúa procedimientos completos, no el efecto causal aislado
de sustituir etiquetas por conteos. [DEC-138](../../traking-concluciones.md#dec-138-freeze-the-bounded-exp-beta02-count-forecasting-protocol).

## Resultados reales frente a R0

Agregación de conteos y exposición de los cuatro años; denominador T+1 =
2.653/12 municipio-años. Fuente: [RESULTS](RESULTS.md) y
[estratos de inicio](ONSET_BY_STRATUM.csv). Ninguna cifra procede de tests sintéticos.

| T+1 | Detecciones / inicios | Sensibilidad | FA | FA / municipio-año | Brier |
|---|---:|---:|---:|---:|---:|
| R0 | 142 / 313 | 45,37% | 231 | 1,044855 | 0,109712 |
| NB2 OFF | 135 / 313 | 43,13% | 212 | 0,958914 | 0,095385 |
| NB2 ON | 152 / 313 | 48,56% | 222 | **1,004146** | 0,091055 |

OFF reduce 19 FA, pero pierde siete detecciones: **−2,2364 pp**, fuera del margen.
ON gana diez detecciones (**+3,1949 pp**) con nueve FA menos, pero su carga
**222×12/2.653 > 1** incumple el presupuesto. No se redondea a 1,00 para aprobarlo.
Ninguna configuración cumple ambos criterios agregados; **19/24** estratos
T+1 año/departamento-o-total/clima fallan conjuntamente. Los estratos se solapan
y no son réplicas independientes. **T+2 inicio: sin sensibilidad ni FA NB2
evaluables**, aun cuando existan pronósticos marginales de conteos/exceso.

Como contexto secundario emparejado, BETA01 G0 ON detecta también 152 inicios
T+1 con 204 FA, frente a 222 de NB2 ON. Esto no cambia R0 como comparador primario
ni selecciona retrospectivamente otro ganador. [Resultados originales](RESULTS.md).

## Conteos e incertidumbre predictiva: resultados secundarios

Agregados ponderados por filas, con RMSE calculado desde errores cuadrados;
intervalos predictivos discretos del 90%, condicionales a parámetros ajustados.
Fuente: [48 estratos de conteos](COUNT_BY_STRATUM.csv).

| Horizonte | Clima | MAE | RMSE | Log score negativo medio | Cobertura 90% | Ancho medio |
|---|---|---:|---:|---:|---:|---:|
| T+1 | OFF | 4,3020 | 16,2728 | 1,9312 | 97,32% | 23,2107 |
| T+1 | ON | 3,8821 | 14,5866 | 1,9114 | 97,36% | 21,9932 |
| T+2 | OFF | 5,4989 | 18,8961 | 2,0728 | 97,65% | 30,7816 |
| T+2 | ON | 5,1251 | 20,8550 | 2,0444 | 97,81% | 28,8476 |

**Hallazgo positivo:** NB2 proporciona distribuciones reproducibles de conteos
sobredispersos; los 16 ajustes convergieron. ON mejora MAE y log score agregados,
pero empeora RMSE T+2. La cobertura superior al 90% con intervalos amplios no
demuestra incertidumbre bien calibrada y precisa; excluye incertidumbre de
parámetros y disponibilidad de fuentes. R0 no tiene distribución de conteos:
no existe una comparación directa de estos errores con R0.

## Conclusión, limitaciones e implicaciones

**`NO_RESPALDADA`** para esta familia marginal congelada como mejora conjunta de
alertas: T+1 falla los controles y T+2 inicio queda **`NO_EVALUABLE`**. No es una
refutación de todos los modelos de conteos. Un Brier menor y mayor detección ON
son hallazgos parciales, no aprobación de la hipótesis operacional completa.

Conservar la distinción entre distribución de casos, exceso e inicio y la
comparación con R0. Una trayectoria conjunta coherente es una pregunta futura,
no una solución implementada. DeepAR/GRU permaneció sin ejecutar por falta de
justificación independiente y soporte para una escalada secuencial; su estado
de ejecución es `CONDICIONAL_NO_JUSTIFICADO`, sin resultado científico evaluable.
Los perfiles de transmisión y G1 nacional no fueron evaluados en V1.

Meta–Tolima, selección de cohortes completas, datos retrospectivos consolidados
y reutilización temporal limitan generalización. 2024 es estrés consumido, no
confirmación. No inferioridad estadística `UNAVAILABLE`; superioridad
`NOT_ESTABLISHED`. **G5 `NOT_APPROVED`; `champion: not_selected`.**

## Trazabilidad y preservación

- Protocolo SHA-256: `6a7697f0011680e59b697422b35a3f928fbe5a8a9dc6e74431548ad2581baef1`,
  congelado en `61bd1e3`; ejecución desde `037ad01`.
- Publicación: `tmp/kedro-migration/exp-beta02-runs/1f0fffc450476c587ed109cb16d552933f832bd8a58d441a5265ee77f12e1468/`.
  Manifiesto SHA-256: `5d8cf7b366d366e6444f7712021914df60c32bff7efa170a3264b42d968ce327`.
  Contiene 27 payloads, 10.150 pronósticos y 18.571 filas de inicio/referencia T+1.
- `count_metrics.csv`, `onset_metrics.csv`, `comparisons_r0.json` y
  `conclusions.json` sustentan estas conclusiones. La consolidación verificó
  todos los hashes y la correspondencia de los 48/84 estratos públicos;
  los agregados se calcularon sobre los resultados existentes, sin ajustar modelos.
- [RESULTS](RESULTS.md) distingue 16 ajustes iniciales y 16 de reproducción,
  28 archivos idénticos y replay nativo sin ajustes. Los 63 tests allí reportados
  son evidencia técnica histórica, no una ejecución repetida en esta tarea.
  La discrepancia heredada del inventario privado de migración sigue documentada
  en [README](README.md), sin reescribir su identidad.
- [Conclusión integradora de V1](../EXP-BETA/CONCLUSIONS.md).
