# Conclusiones científicas de EXP03.1

## 1. Estado y disposición científica

Este documento describe los resultados del bundle científico verificado de EXP03.1. No representa una nueva ejecución ni una aprobación de uso. La evidencia es retrospectiva y descriptiva; las conclusiones no autorizan despliegue ni selección de modelo.

G5: NOT_APPROVED

champion: not_selected

## 2. Resumen ejecutivo

La comparación de memoria reciente (Q1) muestra un incremento agregado pequeño de detecciones, acompañado por más falsas alertas y más alertas totales. La clasificación es `PARCIALMENTE_RESPALDADA`, no una demostración de ganancia robusta bajo el presupuesto congelado. La adición del cambio semestral (Q2) reduce la carga de alertas, pero también reduce detecciones y sensibilidad; Q2 queda `NO_RESPALDADA`. La trayectoria completa frente a la referencia (Q3) reduce detecciones y aumenta falsas alertas y alertas totales para onset; Q3 queda `NO_RESPALDADA`.

Los resultados varían por año, familia, horizonte y territorio. La cobertura evaluada es completa en las filas del bundle, pero no se dispone de intervalos de incertidumbre ni de evidencia de robustez a disponibilidad retrasada. 2024 es estrés retrospectivo; no hay resultado de desempeño para 2025.

## 3. Identidad del análisis

| Campo | Valor verificado |
|---|---|
| Identificador científico | `EXP03.1` |
| Bundle ID | `afcb8b4a6cb512c1247fc52c5d9786a3f0d245663981a29f8f23ac76873a3e04` |
| SHA-256 de `bundle.json` | `5b3f20a266c5e6aae7d2727a00a2213ea9cc3bc691bac5f02267a3e44edc5619` |
| Esquema | `exp03-1-real-scientific-bundle-v1` |
| Celdas / hijos vinculados | 96 / 96 |
| Ejecución padre | `a37877c20dbd4b1382567e79e8d89e7b` |

El validador oficial registró `status=verified`; el mapeo de 96 celdas coincide uno a uno con 96 ejecuciones hijas finalizadas bajo el padre indicado. Evidencia: [identidad y procedencia verificadas](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/identity.md).

## 4. Procedencia y contadores

Los contrastes proceden de `bundle.cells[].metrics` y de las filas emparejadas de `bundle.contrasts.paired_effects`; el seguimiento se consultó en modo solo lectura. El bundle registra 96 ajustes de modelo, 96 ajustes de calibrador, una reserva y 96 selecciones de umbral; `permanent_mlflow_writes=0`.

Permanece sin resolver la diferencia entre `execution_counters.real_private_reads=8` y `provenance.real_private_reads=1`. El recibo de admisión enumera ocho registros de archivo, pero el protocolo no define el alcance de ambos contadores. No se normaliza ni se propone una explicación. Evidencia: [inventario](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/inventory/inventory.md) e [identidad](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/identity.md).

## 5. Pregunta científica

La pregunta congelada es si la representación de la trayectoria reciente de estados de canal mejora la detección de onsets futuros frente a la referencia M00, bajo el mismo presupuesto primario de falsas alertas. El objetivo primario es onset; el control de exceso es un objetivo distinto y no se combina con onset.

## 6. Hipótesis y criterio de interpretación

La hipótesis EXP03.1-H1 propone que la frecuencia reciente de estados y su cambio respecto del semestre previo agregan detección de onset. Un aumento aislado no basta para sostenerla si coincide con mayor carga de alertas, deterioro de calibración o direcciones inestables por año, territorio o perfil. Las categorías de este informe son descriptivas y aplican los criterios congelados; no se añadió un umbral numérico posterior.

## 7. Diseño y contrastes

La matriz congelada compara M00 (referencia), M01 (M00 más memoria reciente) y M02 (M01 más cambio semestral). Q1=M01−M00, Q2=M02−M01 y Q3=M02−M00. Se evaluaron las familias GAM, LightGBM y XGBoost, con horizontes T+1 y T+2, cortes `development_2020`, `development_2021`, `development_2022` y `stress_2024`.

La memoria cubre T−1 a T−6; los cambios comparan ese semestre con T−7 a T−12. Las cohortes emparejadas y las definiciones de etiquetas, umbrales y presupuesto permanecen comunes. Referencias metodológicas: [protocolo congelado](./protocol.json), [matriz congelada](./ablation-matrix.frozen.yml) y [diseño](./DESIGN.md).

## 8. Inventario y cobertura temporal

El bundle contiene 96 celdas evaluables, 60.207 filas de predicción y 52.941 pares emparejados de Q1–Q3. Hay 96 umbrales no nulos. Los años de destino son 2020 (14.769 filas), 2021 (19.299), 2022 (15.852) y 2024 (10.287); el mes máximo es `2024-12`. No hay predicciones posteriores a 2024.

La cobertura por celda es 1,0 y las abstenciones son cero. Esto describe las filas de evaluación contenidas en el bundle; no demuestra por sí solo cobertura operativa ni disponibilidad activa del reporte en cada periodo. Evidencia: [inventario reproducible](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/inventory/inventory.md).

## 9. Denominadores y convenciones de métricas

Los contrastes de onset Q1, Q2 y Q3 tienen cada uno 24 pares de celdas, 15.225 pares de predicciones y 1.596 onsets positivos. Los totales de detecciones, falsas alertas y alertas suman evaluaciones repetidas de celdas, no eventos únicos ni municipios únicos. La sensibilidad macro da el mismo peso a cada par de celdas; se distingue de las tasas agrupadas.

El presupuesto congelado `B_primary=1.0` representa falsas alertas de onset por municipio-año monitoreado y es un objetivo de selección, no una garantía de la tasa observada en evaluación. FAR y FPR no son intercambiables. Las exposiciones implícitas en tasas almacenadas se identifican como tales en los análisis de carga.

## 10. Tabla de decisión Q1–Q3

| Contraste | Clasificación | Pares / predicciones | Onsets positivos | Detecciones ref.→cand. (Δ) | Falsas alertas ref.→cand. (Δ) | Alertas ref.→cand. (Δ) | Sensibilidad macro ref.→cand. (Δ) |
|---|---|---:|---:|---:|---:|---:|---:|
| Q1: M01−M00 | `PARCIALMENTE_RESPALDADA` | 24 / 15.225 | 1.596 | 662→667 (+5) | 1.684→1.742 (+58) | 2.346→2.409 (+63) | 0,388014→0,388783 (+0,000769) |
| Q2: M02−M01 | `NO_RESPALDADA` | 24 / 15.225 | 1.596 | 667→652 (−15) | 1.742→1.714 (−28) | 2.409→2.366 (−43) | 0,388783→0,379860 (−0,008923) |
| Q3: M02−M00 | `NO_RESPALDADA` | 24 / 15.225 | 1.596 | 662→652 (−10) | 1.684→1.714 (+30) | 2.346→2.366 (+20) | 0,388014→0,379860 (−0,008154) |

Los totales son sumas sobre evaluaciones de celdas emparejadas; no son conteos únicos. Sensibilidad es el promedio macro de celdas. Evidencia: [síntesis](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/synthesis/synthesis.md) y [clasificaciones Q](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/synthesis/q_classifications.csv).

## 11. Q1: memoria reciente

Q1 detecta cinco onsets adicionales en 1.596 positivos y 15.225 pares de predicciones, pero añade 58 falsas alertas y 63 alertas totales. La sensibilidad macro aumenta 0,000769; la precisión macro pasa de 0,268815 a 0,263886 (Δ −0,004929). La tasa macro de falsas alertas por municipio-año pasa de 0,967105 a 0,999900. La dirección positiva agregada es pequeña y coexiste con carga mayor, estratos mixtos y discordancia de métricas de calibración; por ello la evidencia es parcial, no robusta. Evidencia: [resultado Q1](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/q1/q1.md).

El agregado Q1 cubre onset en T+1 y T+2. La evaluación de exceso no aplica a Q1 en la matriz congelada. Los soportes por horizonte están en [Q1 por par de celdas](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/q1/q1_by_cell_pair.csv) y en [carga por estrato](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/detection_load/load_by_stratum.csv).

## 12. Q2: cambio semestral incremental

Q2 compara M02 con M01 en 24 pares, 15.225 predicciones emparejadas y 1.596 onsets. Las detecciones bajan de 667 a 652 (−15), las falsas alertas de 1.742 a 1.714 (−28) y las alertas de 2.409 a 2.366 (−43); la sensibilidad macro baja 0,008923. La reducción de carga no respalda la hipótesis de mejora de detección de onset. La tasa macro de falsas alertas pasa de 0,999900 a 0,983702. Evidencia: [resultado Q2](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/q2/q2.md).

Q2 no tiene un contraste de exceso-control: M01 carece de celdas para ese objetivo. No se sustituye por Q3. Evidencia desagregada: [Q2 por par de celdas](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/q2/q2_by_cell_pair.csv).

## 13. Q3: trayectoria completa frente a referencia

Q3 compara M02 con M00 en 24 pares de onset, 15.225 predicciones emparejadas y 1.596 onsets. Las detecciones bajan 10; las falsas alertas aumentan 30 y las alertas totales aumentan 20. La sensibilidad macro cae 0,008154. Este resultado no respalda una mejora de onset; el resultado de exceso-control se informa por separado en la sección 16. Evidencia: [resultado Q3](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/q3/q3.md) y [Q3 por par de celdas](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/q3/q3_by_cell_pair.csv).

## 14. Onset en T+1

| Contraste | Pares / predicciones | Onsets | Detecciones ref.→cand. (Δ) | Falsas alertas ref.→cand. (Δ) | Alertas ref.→cand. (Δ) | Sensibilidad macro ref.→cand. |
|---|---:|---:|---:|---:|---:|---:|
| Q1: M00→M01 | 12 / 7.959 | 939 | 427→429 (+2) | 804→842 (+38) | 1.231→1.271 (+40) | 0,426969→0,426185 |
| Q2: M01→M02 | 12 / 7.959 | 939 | 429→426 (−3) | 842→831 (−11) | 1.271→1.257 (−14) | 0,426185→0,424297 |
| Q3: M00→M02 | 12 / 7.959 | 939 | 427→426 (−1) | 804→831 (+27) | 1.231→1.257 (+26) | 0,426969→0,424297 |

En T+1, Q1 suma dos detecciones agrupadas, pero su sensibilidad macro disminuye 0,000784 y la carga aumenta. Q2 y Q3 también reducen la sensibilidad macro. Evidencia: [Q1 por celda](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/q1/q1_by_cell_pair.csv), [Q2](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/q2/q2.md), [Q3](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/q3/q3.md) y [carga por estrato](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/detection_load/load_by_stratum.csv).

## 15. Onset en T+2

| Contraste | Pares / predicciones | Onsets | Detecciones ref.→cand. (Δ) | Falsas alertas ref.→cand. (Δ) | Alertas ref.→cand. (Δ) | Sensibilidad macro ref.→cand. |
|---|---:|---:|---:|---:|---:|---:|
| Q1: M00→M01 | 12 / 7.266 | 657 | 235→238 (+3) | 880→900 (+20) | 1.115→1.138 (+23) | 0,349058→0,351381 |
| Q2: M01→M02 | 12 / 7.266 | 657 | 238→226 (−12) | 900→883 (−17) | 1.138→1.109 (−29) | 0,351381→0,335424 |
| Q3: M00→M02 | 12 / 7.266 | 657 | 235→226 (−9) | 880→883 (+3) | 1.115→1.109 (−6) | 0,349058→0,335424 |

En T+2, Q1 mejora tres detecciones agrupadas y 0,002323 de sensibilidad macro, de nuevo con más carga; Q2 y Q3 pierden 12 y 9 detecciones, respectivamente. Estas cifras usan denominadores y soportes emparejados de onset y no se combinan con el objetivo de exceso-control. Evidencia: [Q1 por celda](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/q1/q1_by_cell_pair.csv), [Q2](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/q2/q2.md), [Q3](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/q3/q3.md) y [carga por estrato](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/detection_load/load_by_stratum.csv).

## 16. Exceso-control en T+2

El único contraste aplicable es Q3, M00→M02: 12 pares de celdas, 7.266 pares de predicciones y 1.044 positivos del objetivo de exceso-control. Las detecciones de exceso bajan de 341 a 317 (−24), las falsas alertas de 589 a 556 (−33) y las alertas totales de 930 a 873 (−57). La tasa de detección de ese objetivo pasa de 0,326628 a 0,303640.

Este resultado no es onset, no se usa para compensar Q3 onset y no se evalúa contra `B_primary`, que corresponde a falsas alertas de onset. T+1 exceso-control no está definido por la matriz congelada. Evidencia: [resultado Q3](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/q3/q3.md), grupo `excess_control/T+2`.

## 17. Desarrollo retrospectivo 2020–2022

Los cortes 2020, 2021 y 2022 son historia retrospectiva OOF solapada, no validación prospectiva. Entre los cortes, familias y horizontes, las direcciones de sensibilidad fueron 21 favorables, 15 neutras y 27 adversas. Estas son comparaciones repetidas descriptivas, no probabilidades independientes.

Por contraste, las direcciones favorable/neutra/adversa fueron Q1 7/1/10, Q2 3/11/4 y Q3 7/3/8. El promedio global favorable no elimina resultados adversos ni constituye inferencia. Evidencia: [estratos](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/strata/strata.md) y [síntesis](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/synthesis/synthesis.md).

## 18. Estrés retrospectivo 2024

2024 se conserva aparte del desarrollo y no se usa para seleccionar configuración. En las comparaciones de onset, los deltas agregados detecciones/falsas alertas/alertas fueron Q1 +6/+21/+27, Q2 −14/−42/−56 y Q3 −8/−21/−29. Son sumas de evaluaciones repetidas y descriptivas; no reemplazan la evaluación de desarrollo ni prueban desempeño futuro.

No existe evidencia de desempeño de 2025: el bundle termina en `2024-12`, contiene cero predicciones posteriores a 2024 y la frontera 2025 está rechazada. Evidencia: [resumen de síntesis](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/synthesis/synthesis_summary.json) y [estratos](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/strata/strata.md).

## 19. Consistencia por familia y horizonte

En las 21 combinaciones Q/objetivo/familia/horizonte con soporte de desarrollo, 14 cruzan cero entre años y se registraron 21 cambios de signo no neutros entre cortes adyacentes. La dirección también varía dentro de GAM, LightGBM y XGBoost; no se observa una dirección uniforme que justifique elegir una familia. Estos conteos dependen de los mismos municipios y periodos y no son pruebas de estabilidad inferencial.

El detalle de cada estrato, soporte y delta está en [estratos por grupo](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/strata/strata_by_group.csv) y [resumen de estratos](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/strata/strata.md). Las combinaciones sin soporte se mantienen como no evaluables, no como efectos nulos.

## 20. Detección y carga de alertas

La lectura conjunta separa detecciones positivas de alertas emitidas. En Q1 onset hubo 44 alertas verdaderas solo en el candidato frente a 39 solo en la referencia; aun así, se emitieron 63 alertas más y 58 falsas alertas netas más. En Q2 hubo 14 alertas verdaderas solo en M02 frente a 29 solo en M01, con 43 alertas totales menos y 28 falsas alertas menos. En Q3 onset fueron 37 frente a 47 alertas verdaderas exclusivas, junto con 20 alertas totales más y 30 falsas alertas más.

Las cuentas por clase, transiciones y exposiciones están en [transiciones por clase](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/detection_load/alert_transitions_by_class.csv) y [carga por estrato](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/detection_load/load_by_stratum.csv). Una alerta candidata no equivale automáticamente a una detección nueva.

## 21. Persistencia y clases de error

Onset, continuación y no-exceso se conservan como clases distintas. Para Q1, las alertas exclusivas sobre onsets fueron 44 en M01 y 39 en M00 (ganancia neta de 5); sobre continuaciones fueron 16 y 13 (diferencia neta de 3), mientras que sobre no-exceso fueron 207 y 152 (55 de las 58 falsas alertas netas adicionales). Por tanto, EXP03.1 observa una señal incremental mínima sobre inicios, pero no demuestra anticipación robusta: la ganancia cambia de dirección según la métrica macro y los estratos, y está dominada operativamente por carga sobre no-exceso. Tampoco demuestra que el mecanismo sea principalmente persistencia; los campos de persistencia, incluido el historial de alerta T+1 para la evaluación T+2, están separados del endpoint y no identifican causalidad. Evidencia: [detección y carga](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/detection_load/detection_load.md) y [transiciones por clase](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/detection_load/alert_transitions_by_class.csv).

## 22. Calibración y discriminación

| Q | Δ AP | Δ Brier | Δ ECE | Cobertura ref.→cand. | Grupos de onset con métricas en dirección opuesta a sensibilidad |
|---|---:|---:|---:|---:|---:|
| Q1 | +0,000201 | +0,000287 | +0,000454 | 1,000→1,000 | 7/8 |
| Q2 | −0,001179 | −0,000022 | +0,000213 | 1,000→1,000 | 5/8 |
| Q3 | −0,000978 | +0,000265 | +0,000667 | 1,000→1,000 | 5/8 |

AP es average precision; Brier y ECE son errores donde valores menores son favorables. En 19 de 28 grupos emparejados Q/objetivo/horizonte/corte, alguna métrica disponible se movió en dirección opuesta a la sensibilidad. Las direcciones son descriptivas; no se combinan en un ranking. Evidencia: [calibración](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/calibration/calibration.md).

## 23. Cobertura, confiabilidad e incertidumbre

Las 96 celdas tienen cobertura 1,0 y cero abstenciones. Hay 225 bins de confiabilidad no vacíos; sus 60.207 filas sumadas reconcilian con el soporte del bundle, con evaluaciones repetidas. La completitud de esas filas no prueba disponibilidad activa del reporte ni extrapolación a otros periodos.

No hay intervalos de confianza, errores estándar ni valores p en el bundle o resúmenes autorizados. No se estimó incertidumbre mediante remuestreo posterior. Tampoco hay resultado de robustez a disponibilidad retrasada; el reconocimiento retrospectivo de disponibilidad no es evidencia de tal robustez. Evidencia: [calibración, cobertura e incertidumbre](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/calibration/calibration.md).

## 24. Evidencia territorial: Meta y Tolima

El análisis agregado cubre 76 municipios del bundle: 29 en Meta y 47 en Tolima. No se publican identificadores municipales ni filas municipio-mes. En las ocho agrupaciones de onset reportadas, las direcciones de sensibilidad municipio-grupo fueron:

| Q | Meta: mayor/menor/empate | Tolima: mayor/menor/empate |
|---|---:|---:|
| Q1 | 14/17/127 | 22/12/172 |
| Q2 | 4/15/139 | 8/11/187 |
| Q3 | 10/22/126 | 21/17/168 |

Los conteos repiten comparaciones por grupo y no representan municipios únicos. El soporte territorial varía por periodo; las tasas regionales basadas en exposición de filas se mantienen separadas de las métricas globales por celda. La evidencia es heterogénea y descriptiva. Evidencia: [análisis territorial](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/territory/territory.md).

## 25. Perfiles históricos de transmisión

No evaluable con el bundle de EXP03.1; no se infirió retrospectivamente.

La membresía histórica requerida no está disponible en la evidencia verificada. No se reconstruyó ni se infirió retrospectivamente.

## 26. Hallazgos, interpretación, hipótesis abiertas y limitaciones

**Hallazgos confirmados.** Q1 añade cinco detecciones de onset, pero con 58 falsas alertas y 63 alertas totales adicionales. Q2 reduce carga y también detecciones. Q3 onset reduce detecciones y aumenta carga; su exceso-control reduce detecciones y alertas en un estimando separado. Los resultados cambian por año, familia, horizonte y territorio.

**Interpretación.** La evidencia permite una señal agregada limitada para memoria reciente, no una mejora uniforme bajo el presupuesto congelado. La reducción de carga de Q2 no satisface la hipótesis de mejora de detección. El resultado de exceso-control de Q3 no contrarresta el de onset. La hipótesis principal completa —que memoria reciente y cambio semestral mejoran la detección— no queda comprobada: solo Q1 recibe apoyo parcial; Q2 y Q3 no reciben apoyo.

**Hipótesis abiertas.** La contribución condicionada a horizonte, familia, territorio y disponibilidad temporal requiere evaluación futura preespecificada; este bundle no permite resolverla más allá de las clasificaciones descriptivas reportadas.

**Limitaciones decisivas.** Los totales repiten evaluaciones; los cortes de desarrollo son retrospectivos y solapados; 2024 es estrés; no hay desempeño 2025, intervalos ni prueba de retraso de disponibilidad. La discrepancia `real_private_reads=8` frente a `1` sigue sin reconciliarse. La membresía de perfiles históricos no es evaluable. Las tasas de exposición regionales y globales usan bases distintas.

## 27. Decisiones recomendadas para experimentos futuros

1. Mantener M00 como referencia científica; no promover M01 ni M02 y no seleccionar champion con EXP03.1.
2. Si se vuelve a estudiar M01, preespecificar por separado T+1 y T+2, el coste de falsas alertas y un criterio de consistencia temporal/territorial antes de observar resultados.
3. No continuar M02 como mejora general de onset con esta formulación. Cualquier variante futura del cambio semestral debe plantearse como una hipótesis nueva y acotada, no como confirmación de EXP03.1.
4. Incorporar incertidumbre preespecificada y una prueba válida de disponibilidad retrasada en una ejecución futura autorizada; EXP03.1 no permite añadirlas retrospectivamente.
5. Resolver semánticamente la discrepancia de `real_private_reads` antes de reutilizar esos contadores como evidencia de procedencia.

Estas son decisiones de diseño futuro, no nuevos criterios aplicados a los resultados actuales. No autorizan otra ejecución ni infraestructura adicional.

## 28. Reproducibilidad y disposición final

Se permite conservar estas conclusiones como descripción del bundle y como evidencia para diseñar preguntas futuras. No se permite inferir causalidad, prospectividad, preparación operativa, desempeño en 2025, robustez a retrasos, equivalencia, significancia, selección de champion ni aprobación de G5. No se comparan otros experimentos.

La trazabilidad reproducible está en el bundle identificado en la sección 3 y en los registros ya generados bajo `.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/`. La siguiente tabla vincula cada resultado sustantivo con sus artefactos y cálculos reproducibles.

| Evidencia | Registros |
|---|---|
| Identidad y procedencia | [identity.md](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/identity.md) |
| Inventario y denominadores | [inventory.md](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/inventory/inventory.md) |
| Q1: memoria reciente | [q1.md](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/q1/q1.md), [q1_by_cell_pair.csv](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/q1/q1_by_cell_pair.csv) |
| Q2: cambio semestral | [q2.md](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/q2/q2.md), [q2_by_cell_pair.csv](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/q2/q2_by_cell_pair.csv) |
| Q3: trayectoria completa | [q3.md](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/q3/q3.md), [q3_by_cell_pair.csv](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/q3/q3_by_cell_pair.csv) |
| Estratos temporales y por familia | [strata.md](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/strata/strata.md), [strata_by_group.csv](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/strata/strata_by_group.csv) |
| Carga y transiciones de alertas | [detection_load.md](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/detection_load/detection_load.md), [alert_transitions_by_class.csv](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/detection_load/alert_transitions_by_class.csv), [load_by_stratum.csv](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/detection_load/load_by_stratum.csv) |
| Calibración, cobertura e incertidumbre | [calibration.md](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/calibration/calibration.md) |
| Evidencia territorial agregada | [territory.md](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/territory/territory.md) |
| Clasificación y síntesis | [synthesis.md](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/synthesis/synthesis.md), [q_classifications.csv](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/synthesis/q_classifications.csv), [synthesis_summary.json](../../../../.dwp/plans/PLAN_051_exp03_1_scientific_analysis/analysis_results/synthesis/synthesis_summary.json) |

La metodología congelada está enlazada en la sección 7. Este cierre no volvió a ejecutar EXP03.1, no recalibró ni reentrenó y no escribió en MLflow.

Disposición: análisis descriptivo terminado; no se deriva aprobación científica ni selección de modelo.

G5: NOT_APPROVED

champion: not_selected
