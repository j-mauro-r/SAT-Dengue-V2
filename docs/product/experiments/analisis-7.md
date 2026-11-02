# Análisis científico 7 — De EXP00 a EXP-BETA01 V2

Síntesis crítica del conocimiento acumulado, 2 de noviembre de 2026. Se examinan
resultados existentes; no se ejecutan modelos, simulaciones, recalibraciones ni
selecciones nuevas. El objeto es la anticipación retrospectiva del **inicio H5**,
no la predicción de cualquier exceso ni la eficacia sanitaria de una intervención.

Los [análisis 1](analisis-1.md), [2](analisis-2.md), [3](analisis-3.md),
[4](analisis-4.md), [5](analisis-5.md) y [6](analisis-6.md) son antecedentes
interpretativos de los mismos experimentos, no seis replicaciones adicionales.
Las cifras y disposiciones se contrastan con resultados, protocolos y artefactos
identificados, enlazados en cada capítulo. Los agregados BETA de cuatro años
incluyen 2024, estrés consumido; no constituyen confirmación independiente.

## Capítulo 1. Resumen ejecutivo

Cinco hallazgos delimitan el problema científico:

1. **Existe información predictiva aprovechable, pero su contribución es
   condicional.** En EXP03, añadir estado contemporáneo a la base rezagada mejora
   la sensibilidad T+1 entre 12,86 y 20,00 puntos porcentuales (pp); GAM y
   LightGBM además reducen falsas alertas agregadas. Los umbrales históricos del
   mes objetivo favorecen a boosting en ambos horizontes y en los tres años de
   desarrollo. Esto impide atribuir toda ganancia simplemente a emitir más
   alertas, pero no supera los controles conjuntos del experimento.
   [EXP03, contrastes P1/P4](EXP03_feature_ablation/CONCLUSIONS.md).
2. **El evento que se anticipa también requiere validación.** EXP01 demuestra
   identidad inicio/exceso T+1 dentro de la cohorte sin exceso en T; EXP02 muestra
   que H9 sustituye 40 inicios H5 por 47 distintos en 2024. Cambiar etiqueta puede
   cambiar la tarea sin mejorar la detección del mismo fenómeno. H5 se conserva
   por trazabilidad, sin acreditarlo como verdad epidemiológica externa.
   [EXP01](EXP01_direct_onset/CONCLUSIONS.md), [EXP02](EXP02_label_stability/CONCLUSIONS.md).
3. **Calidad probabilística y utilidad de alerta se separan empíricamente.**
   EXP04 mejora Brier de desarrollo con ventanas móviles, pero pierde 5,7–15,2 pp
   de sensibilidad. BETA03 mantiene las probabilidades R0 y reduce 95/81 falsas
   alertas T+1/T+2 sacrificando 46/29 detecciones. No basta corregir la escala de
   probabilidad o disminuir el volumen de alertas.
   [EXP04](EXP04_transporte_temporal_%20de_calibracion_y_umbrales_de%3Adecision/CONCLUSIONS.md),
   [BETA03](EXP-BETA03/RESULTS.md).
4. **La ampliación nacional no mejoró el par detección–carga del procedimiento
   probado.** Frente a G0 OFF, G1 pierde cinco detecciones y añade ocho falsas
   alertas en T+1; pierde una y añade 21 en T+2. Su contribución específica es
   convertir G1 de `NO_EVALUABLE` en V1 en una hipótesis efectivamente contrastada
   y `NO_RESPALDADA` en V2, manteniendo los controles históricos. No refuta toda
   transferencia nacional posible. [Resultados V2](EXP-BETA01-V2/RESULTS.md),
   [conclusiones V1](EXP-BETA01/CONCLUSIONS.md).
5. **El agregado puede ocultar incluso una inversión de la lectura probabilística.**
   G1 mejora AP agrupada T+1 de 0,309268 a 0,334520, pero su AP es menor que la
   de G0 en cada uno de los cuatro años. Además, incumple el criterio conjunto
   frente a R0 en 20/24 estratos anuales. Más municipios no aportaron años de
   confirmación ni estabilidad demostrada. Esta lectura surge de desagregar las
   [métricas originales V2](EXP-BETA01-V2/RESULTS_BY_STRATUM.csv), no de entrenar
   otra variante.

**Conclusión central:** se han mejorado componentes del pronóstico sin demostrar
que la información adicional mejore consistentemente la separación de inicios y
no inicios en la región de decisiones compatible con la carga permitida. Esa
separación debe mantenerse entre años y territorios. La evidencia delimita este
problema, pero no identifica una causa única: no se ha demostrado que arquitectura,
tamaño de muestra, calibración o H5 expliquen por sí solos todos los resultados. Siguen
abiertas la transportabilidad del punto de alerta, la representatividad del
entrenamiento, la validez del evento y la oportunidad real de los datos.

## Capítulo 2. Evolución del conocimiento científico

La matriz distingue resultados descriptivos favorables, disposiciones de protocolo
y preguntas no ejecutadas. Una contribución parcial de variables no reemplaza
un veredicto formal `inconclusive`.

| Experimento | Hipótesis | Qué se evaluó | Resultado principal | Aprendizaje científico | Pregunta que permanece |
|---|---|---|---|---|---|
| [EXP00](EXP00_historical_baseline/CONCLUSIONS.md) | Reproducir la línea histórica y documentar su utilidad | Replay protegido de tres familias × dos horizontes; persistencia; 2025 | Reproducción respaldada; seis procedimientos `does_not_meet`, todos superan el margen de +5 pp de FAR | Detectar más no garantiza utilidad; persistencia T+1 tiene sensibilidad cero por construcción | ¿Qué información permite ganar detección sin carga excesiva? |
| [EXP01](EXP01_direct_onset/CONCLUSIONS.md) | Inicio directo mejora sobre exceso | Objetivos pareados y frente completo de presupuestos | T+1 idéntico en 1.902 pares; T+2 mixto; `INCONCLUSIVE` | La equivalencia T+1 es estructural; el cambio de target T+2 no es solución general | ¿Qué representación distingue transición de continuación? |
| [EXP02](EXP02_label_stability/CONCLUSIONS.md) | Estabilidad al variar H5/H7/H9 | Identidad de etiquetas/episodios y evaluación propia/común | `MATERIAL_INSTABILITY` descriptiva; sustitución de H5 `INCONCLUSIVE` | Un total parecido puede ocultar eventos distintos; mejor Brier propio no valida el evento | ¿Cómo validar externamente el inicio? |
| [EXP03](EXP03_feature_ablation/CONCLUSIONS.md) | Bloques de variables añaden señal | Ablación pareada con H5 fija | Estado T y P25/P75 prometedores; todas las disposiciones primarias `inconclusive` | Aporte depende de horizonte, familia y territorio; no es importancia causal | ¿Se transporta la señal útil bajo carga restringida? |
| [EXP03.1](EXP03.1_add_pass_info/CONCLUSIONS.md) | Memoria y cambio semestral mejoran M00 | M01−M00, M02−M01 y M02−M00 | Q1 `PARCIALMENTE_RESPALDADA`; Q2/Q3 `NO_RESPALDADA` | Cinco detecciones adicionales cuestan 58 FA; resumen temporal grueso insuficiente | ¿Hay dinámica anticipatoria que esa representación pierde? |
| [EXP04](EXP04_transporte_temporal_%20de_calibracion_y_umbrales_de%3Adecision/CONCLUSIONS.md) | Calibración/umbrales transportan detección y carga | A1–A3 móviles frente a A0, predictor fijo | Ninguna ventana elegible; evidencia `DESCRIPTIVE_ONLY`; A4/B/C/D no evaluables | Menor Brier y carga pueden acompañar pérdida inadmisible de detección | ¿Dónde falla la decisión si se conserva el orden de puntuaciones? |
| [EXP-BETA01 V1](EXP-BETA01/CONCLUSIONS.md) | Aprendizaje compartido y adaptación local | G0/L1 XGBoost, clima OFF/ON, R0 | Ganancias agregadas G0 T+1; L1 `NO_RESPALDADA`; G1 `NO_EVALUABLE` | R0 ya agrupaba municipios; G0 cambia procedimiento, L1 solo intercepto | ¿Qué aporta realmente ampliar entrenamiento? |
| [EXP-BETA02 V1](EXP-BETA02/CONCLUSIONS.md) | Conteos probabilísticos mejoran inicio | NB2 marginal, OFF/ON | Alertas T+1 `NO_RESPALDADA`; inicio T+2 `NO_EVALUABLE` | Distribución de casos y transición de inicio son objetos distintos | ¿Aporta una distribución conjunta identificable? |
| [EXP-BETA03 V1](EXP-BETA03/CONCLUSIONS.md) | Reducir FA conservando sensibilidad | GLOBAL y DEPARTMENT sobre R0 congelado | `NO_RESPALDADA`; política local solo evaluable en 2020 | Restringir carga en desarrollo no garantiza carga futura ni preservación de detección | ¿El problema es el orden local de riesgo, la selección o ambos? |
| [EXP-BETA01 V2](EXP-BETA01-V2/CONCLUSIONS.md) | Municipios nacionales mejoran G0 OFF regional | Ocho ajustes de la misma arquitectura; ampliación solo de entrenamiento | `NO_RESPALDADA`; AP/Brier agrupados mejores, alertas peores | Cantidad adicional no basta; geografía e historia añadidas deben separarse | ¿Qué parte de la mezcla nacional es transferible al objetivo regional? |

La secuencia reduce explicaciones simples sin eliminarlas universalmente. EXP01
acota el cambio de objetivo; EXP02 obliga a fijar el evento; EXP03 identifica
información útil; EXP03.1 limita una representación concreta de memoria; EXP04
separa calidad de probabilidad y decisión. BETA añade controles de adaptación,
conteos y política. V2 finalmente prueba expansión territorial sin confundirla
con cambiar de familia. **No son diez pruebas independientes de una misma
hipótesis:** comparten datos, decisiones previas y años inspeccionados.

Hay dos discrepancias interpretativas que deben conservarse visibles. Las frases
amplias de [análisis 3](analisis-3.md) y [análisis 5](analisis-5.md) sobre ausencia
de desempeño 2025 se restringen aquí al transporte posterior no evaluable:
[EXP00](EXP00_historical_baseline/CONCLUSIONS.md) sí conserva una evaluación
histórica 2025, consumida y negativa. Asimismo, el [diseño BETA](EXP-BETA/DESING.md)
y [análisis 6](analisis-6.md) describen G1 pendiente en su fecha; la publicación
V2 posterior acredita su ejecución, sin modificar el `NO_EVALUABLE` de V1.
Las expresiones previas «no basta con…» se interpretan como límites de las
formulaciones probadas, no como refutaciones de familias enteras.

## Capítulo 3. Qué añade realmente EXP-BETA01 V2

### A. Volumen, historia y alcance del contraste

La [validación canónica nacional](../../data/canonical-national-validation.md)
registra 182.886 filas, 1.122 territorios y orígenes 2011-06–2024-12. **Ese total
no es el entrenamiento G1.** Fuera de los 76 municipios originales, H5 actual
solo es elegible desde junio de 2016. El filtro de riesgo, la disponibilidad de
predictores/etiquetas y los cortes temporales reducen más el soporte.

| Horizonte / año evaluado | Filas regionales | Filas añadidas | Municipios añadidos / total G1 | Inicios añadidos | Orígenes añadidos / meses |
|---|---:|---:|---:|---:|---|
| T+1 / 2020 | 3.155 | 5.239 | 1.017 / 1.093 | 389 | 2016-06–2016-11 / 6 |
| T+1 / 2021 | 3.938 | 17.029 | 1.045 / 1.121 | 855 | 2016-06–2017-11 / 18 |
| T+1 / 2022 | 4.691 | 28.590 | 1.046 / 1.122 | 1.453 | 2016-06–2018-11 / 30 |
| T+1 / 2024 | 5.728 | 47.489 | 1.046 / 1.122 | 3.572 | 2016-06–2020-11 / 54 |
| T+2 / 2020 | 3.089 | 4.311 | 1.007 / 1.083 | 218 | 2016-06–2016-10 / 5 |
| T+2 / 2021 | 3.871 | 16.036 | 1.045 / 1.121 | 617 | 2016-06–2017-10 / 17 |
| T+2 / 2022 | 4.638 | 27.679 | 1.046 / 1.122 | 1.130 | 2016-06–2018-10 / 29 |
| T+2 / 2024 | 5.655 | 46.576 | 1.046 / 1.122 | 2.667 | 2016-06–2020-10 / 53 |

Fuente: [TRAINING_SUPPORT](EXP-BETA01-V2/TRAINING_SUPPORT.csv).
Son celdas con historias solapadas; no se suman sus filas/inicios como muestras
independientes. Tampoco 1.046 municipios nuevos equivalen a 1.046 regímenes
independientes: la diversidad epidemiológica efectiva no fue medida.

El [protocolo V2](EXP-BETA01-V2/protocol.json) conserva 24 predictores sin clima,
XGBoost de 80 árboles/profundidad 2 y roles de V1: entrenamiento hasta Y−4,
calibración global Y−3, adaptación Y−2 sin usar, selección Y−1 y evaluación Y,
con embargos por origen. Calibración, selección y evaluación siguen siendo
regionales. Se conserva el **método** de calibración y selección; los interceptos
y umbrales G1 se estiman en los roles permitidos, no se impone el valor numérico
G0. Los ocho modelos son dos horizontes por cuatro cortes, no ocho arquitecturas.

La igualdad de claves, X y verdad regionales en los cinco roles hizo innecesario
G0_MATCHED. El contraste identifica el efecto del **procedimiento de añadir las
filas nacionales disponibles**; no separa cantidad, composición territorial,
prevalencia, estación y recencia. En 2020, muchos municipios aportan solo cinco
o seis meses de origen, sin ciclo anual completo. En 2024 hay más historia
nacional, pero el entrenamiento aún termina en 2020: no incorpora la dinámica
reciente de 2021–2023. Es una consecuencia del diseño conservado, no una causa
probada del resultado. [Soporte de roles](EXP-BETA01-V2/ROLE_SUPPORT.csv).

Además, **entrenamiento nacional no significa evaluación nacional**: la pregunta
es transferencia hacia Meta–Tolima. No se midió utilidad en los demás territorios.

### B. G1 frente al control regional G0

Los tres brazos comparten exactamente 2.653 filas/313 inicios T+1 y 2.422/219
T+2. Exposición: 221,083333 y 201,833333 municipio-años **elegibles** (filas/12),
no 76 × cuatro años. En 2024 contribuyen 72/70 municipios en T+1/T+2, como en
la cohorte original. Tasas agrupadas se calculan desde conteos, no como media
simple de tasas. [Resultados y soporte](EXP-BETA01-V2/RESULTS.md).

| Horizonte | Brazo | Detectados / inicios | Sensibilidad | FA | FA/municipio-año | Precisión | AP | Brier |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| T+1 | R0 | 142/313 | 45,37% | 231 | 1,044855 | 0,380697 | 0,260911 | 0,109712 |
| T+1 | G0 OFF | 146/313 | 46,65% | 179 | 0,809649 | 0,449231 | 0,309268 | 0,094352 |
| T+1 | G1 OFF | 141/313 | 45,05% | 187 | 0,845835 | 0,429878 | 0,334520 | 0,092204 |
| T+2 | R0 | 86/219 | 39,27% | 256 | 1,268373 | 0,251462 | 0,161573 | 0,088390 |
| T+2 | G0 OFF | 62/219 | 28,31% | 161 | 0,797688 | 0,278027 | 0,173767 | 0,079653 |
| T+2 | G1 OFF | 61/219 | 27,85% | 182 | 0,901734 | 0,251029 | 0,188141 | 0,078766 |

Fuente: [90 estratos originales](EXP-BETA01-V2/RESULTS_BY_STRATUM.csv).
G0 domina descriptivamente los **dos puntos operativos agrupados** G1: más
sensibilidad y menos FA. Esto no demuestra dominancia de todas sus curvas ni
significancia estadística. G1 pierde precisión en ambos horizontes.

El detalle anual permite distinguir constancia de compensación. Cada delta es
G1−G0 sobre el mismo soporte anual; AP se calcula dentro del año.

| Horizonte / año | Inicios | Δ detecciones | Δ FA | AP G0 → G1 | Brier G0 → G1 |
|---|---:|---:|---:|---:|---:|
| T+1 / 2020 | 69 | 0 | +9 | 0,342279 → 0,334466 | 0,0823 → 0,0815 |
| T+1 / 2021 | 52 | −2 | −3 | 0,199470 → 0,168520 | 0,0558 → 0,0568 |
| T+1 / 2022 | 89 | −1 | +2 | 0,454611 → 0,434186 | 0,1038 → 0,1016 |
| T+1 / 2024 | 103 | −2 | 0 | 0,525115 → 0,511911 | 0,1695 → 0,1596 |
| T+2 / 2020 | 51 | −2 | −20 | 0,277013 → 0,323986 | 0,0750 → 0,0738 |
| T+2 / 2021 | 45 | +3 | +5 | 0,226457 → 0,238690 | 0,0518 → 0,0506 |
| T+2 / 2022 | 62 | +5 | +29 | 0,210989 → 0,194883 | 0,0892 → 0,0879 |
| T+2 / 2024 | 61 | −7 | +7 | 0,360705 → 0,266693 | 0,1240 → 0,1247 |

Fuentes: [métricas](EXP-BETA01-V2/RESULTS_BY_STRATUM.csv) y
[contrastes pareados](EXP-BETA01-V2/COMPARISONS_BY_STRATUM.csv).
T+1 no gana detecciones en ningún año. T+2 gana en 2021/2022 con más FA,
ahorra FA perdiendo detecciones en 2020 y empeora ambas en 2024. Ningún total
anual de los ocho muestra más detecciones sin más FA. El estrés T+2 pierde
siete detecciones y añade siete FA pese al mayor soporte acumulado; el aumento
entre cortes no constituye una curva de aprendizaje controlada porque cambia
simultáneamente el año evaluado.

| Horizonte / departamento, cuatro años | Δ detecciones G1−G0 | Δ FA | Δ AP | Δ Brier |
|---|---:|---:|---:|---:|
| T+1 / Meta | 0 | 0 | +0,024886 | −0,002855 |
| T+1 / Tolima | −5 | +8 | +0,028331 | −0,001703 |
| T+2 / Meta | +2 | +4 | −0,003991 | +0,000590 |
| T+2 / Tolima | −3 | +17 | +0,025228 | −0,001829 |

El deterioro neto T+1 se concentra en Tolima; igualdad de conteos en Meta no
significa identidad de alertas individuales. En T+2, Meta gana sensibilidad
con más carga y peores métricas probabilísticas; Tolima mejora AP/Brier
agrupados mientras pierde detecciones y añade FA. **El efecto territorial
cambia según la propiedad evaluada**, sin identificar un territorio siempre
beneficiado o perjudicado. Fuente: [contrastes](EXP-BETA01-V2/COMPARISONS_BY_STRATUM.csv).

### C. G1 frente a R0 y criterios congelados

G1 T+1 pierde una detección frente a R0 (−0,32 pp) y reduce 44 FA; cumple
agrupadamente carga ≤1 y margen descriptivo ≥−2 pp. T+2 pierde 25 detecciones
(−11,42 pp) y reduce 74 FA: cumple carga, incumple sensibilidad. Incumple el
criterio conjunto en **20/24 estratos anuales** (año × horizonte × total/Meta/Tolima),
12/16 contando solo departamentos, y 24/30 al añadir agregados de cuatro años.
Son estratos solapados, no experimentos independientes.
[Resultados V2](EXP-BETA01-V2/RESULTS.md).

El dictamen `NO_RESPALDADA` tampoco depende exclusivamente de esos controles:
la regla predeclarada exige una ganancia de sensibilidad sin más carga frente
a G0 para siquiera sostener apoyo parcial agrupado. Ningún horizonte la logra.
El campo `joint_compliance` suplementario frente a G0 comprueba margen/carga;
no equivale a respaldo de transferencia ni reemplaza R0 como referencia formal.
[Protocolo](EXP-BETA01-V2/protocol.json),
[comparaciones](EXP-BETA01-V2/COMPARISONS_BY_STRATUM.csv).

R0 es M00/XGBoost/onset histórico, ya compartido entre municipios. Sus variables,
preparación y roles de ajuste/calibración difieren de BETA; su política original
usó exposición monitoreada más amplia. Sus alertas se conservan y las tasas se
reexpresan sobre la exposición elegible común. G1−R0 compara procedimientos
completos: **solo G1−G0 OFF aísla la ampliación de entrenamiento dentro del
procedimiento BETA**. No sería correcto atribuir a Colombia la pérdida completa
T+2 frente a R0, pues G0 ya perdía 24 detecciones antes de ampliar.
[Protocolo V1](EXP-BETA01/protocol.phase2.json), [BETA03](EXP-BETA03/CONCLUSIONS.md).

### D. Por qué AP/Brier mejores no rescatan el resultado

La aparente paradoja tiene una parte demostrable y otra pendiente de diagnóstico.

**Demostrable:** AP resume ordenación a lo largo de distintos niveles de
recuperación; no mide solo la zona del umbral finalmente utilizado. Brier
promedia error cuadrático de probabilidad en todas las filas; no es una medida
pura de calibración ni pondera exclusivamente el costo de una alerta. Un cambio
favorable fuera de la región de decisión puede coexistir con errores adicionales
en ella. Los conteos publicados prueban esa coexistencia, pero no localizan por
sí solos qué filas explican cada mejora. EXP04 ya ofrece el control complementario:
A1/A2/A3 cambian escala/Brier y conservan decisiones; BETA03 cambia decisiones
sin cambiar AP/Brier. [EXP04](EXP04_transporte_temporal_%20de_calibracion_y_umbrales_de%3Adecision/CONCLUSIONS.md),
[BETA03](EXP-BETA03/RESULTS.md).

**Hallazgo de agregación:** AP agrupada no es el promedio de AP anuales. Mezcla
puntuaciones de cuatro modelos ajustados/calibrados en historias distintas y
compara también el orden entre años. G1 mejora AP agrupada T+1 aun empeorando
las cuatro AP anuales; por tanto, no demuestra mejor ordenación dentro de cada
año de emisión. La diferencia reside en cómo la combinación de escalas y
ordenaciones entre periodos afecta la AP agrupada; no se ha identificado su
mecanismo. No es un error aritmético: se reprodujeron las AP desde las predicciones
persistidas. En T+2 hay mejora anual solo en 2020/2021, deterioro en 2022/2024.
Brier sí se agrega ponderando por filas: mejora en tres años de cada horizonte,
con excepción de 2021 T+1 y 2024 T+2.
[Tabla original](EXP-BETA01-V2/RESULTS_BY_STRATUM.csv).

**Explicaciones abiertas:** la mezcla territorial puede modificar relaciones
predictor–evento; la historia nacional corta cambia estaciones y prevalencia
representadas; una gran cantidad de negativos puede mejorar error promedio sin
mejorar la región de alerta; calibración y selección regionales pueden no
transportar el punto útil al año siguiente. La prevalencia evaluada T+1 pasa de
52/846 en 2021 (6,15%) a 103/453 en 2024 (22,74%). Es evidencia de composición
temporal distinta dentro de la cohorte, no prueba de que ese cambio cause los
errores. Transferencia negativa es una hipótesis compatible con el deterioro
operativo frente a G0, pero su explicación territorial no está aislada de la
historia añadida ni de la decisión. [Soporte](EXP-BETA01-V2/TRAINING_SUPPORT.csv),
[métricas](EXP-BETA01-V2/RESULTS_BY_STRATUM.csv).

## Capítulo 4. Hallazgos transversales

### 1. Señal útil, con alcance delimitado

EXP00 discrimina exceso y gana detección frente a persistencia, pero este control
T+1 detecta cero por construcción. EXP03 aporta evidencia más informativa:
contrastes de variables con más detección y menos FA dentro de una comparación
controlada. BETA01 G0 OFF gana cuatro detecciones T+1 y reduce 52 FA frente a
R0 sobre claves iguales, aunque cambie el procedimiento completo. Existe señal
retrospectiva útil; no se ha demostrado anticipación operativa estable.
[EXP00](EXP00_historical_baseline/CONCLUSIONS.md), [EXP03](EXP03_feature_ablation/CONCLUSIONS.md),
[BETA01](EXP-BETA01/CONCLUSIONS.md).

### 2–4. Estado T, variables consistentes y umbrales históricos

Estado actual y contexto estacional del mes objetivo son los aportes relativamente
más consistentes dentro de EXP03. P4 mejora sensibilidad de LightGBM/XGBoost
entre 20,89 y 27,62 pp según horizonte/familia; no es un efecto universal, pues
GAM no reproduce esa dirección en T+1. Los P25/P75 pueden facilitar representar
la frontera H5 que define la etiqueta; eso no prueba mecanismo biológico ni
fuga futura si se calculan solo desde historia admisible. Retirar todo el canal
pierde detecciones en las seis combinaciones, pero componentes individuales
tienen redundancias y efectos distintos. No se deben sumar efectos de ablaciones.
[EXP03](EXP03_feature_ablation/CONCLUSIONS.md).

La conexión con EXP03.1 es que **nivel, contexto estacional y trayectoria no son
intercambiables**: añadir conteos semestrales de estados sobre M00 casi no mejora
onset y aumenta carga. No demuestra que toda memoria sea inútil. Además, la
cohorte exige conocer Y(T)=0 incluso con predictores rezagados. El diagnóstico
estricto de EXP03 queda `unable_to_issue` cuando ese estado no está disponible;
no se obtiene anticipación real simplemente retrasando columnas.
[EXP03.1](EXP03.1_add_pass_info/CONCLUSIONS.md), [EXP03](EXP03_feature_ablation/CONCLUSIONS.md).

### 5. Clima: señal condicionada, pregunta nacional abierta

EXP03 encuentra ganancias climáticas T+2 de boosting con 138/153 FA adicionales,
revertidas en el estrés 2024. BETA01 G0 ON−OFF añade seis detecciones y 25 FA
T+1; añade cinco y reduce nueve FA T+2. NB2 ON mejora MAE y log score agrupados,
pero empeora RMSE T+2. Estos resultados no prueban ni inutilidad ni ventaja
general del clima. V2 es exclusivamente OFF: no evalúa si clima modifica la
transferencia nacional. La mejora de cobertura de una fuente tampoco constituye
una mejora predictiva. [EXP03](EXP03_feature_ablation/CONCLUSIONS.md),
[BETA01](EXP-BETA/RESULTS.md), [NB2](EXP-BETA02/RESULTS.md),
[validación nacional](../../data/canonical-national-validation.md).

### 6–7. Probabilidades, alertas y explicaciones parcialmente descartadas

EXP04 y BETA03 muestran que el control de decisión puede ahorrar carga sin
preservar detección; V2 añade que incluso cambiar el entrenamiento y mejorar
métricas agrupadas no asegura una mejor alerta. Se debilitan las explicaciones
suficientes «solo falta calibrar», «solo falta memoria semestral», «solo falta
adaptación departamental por intercepto» y «solo faltan municipios». No se
elimina la contribución posible de ninguno de esos mecanismos bajo otro diseño.
No se ha probado imposibilidad del objetivo conjunto ni falta de capacidad de
todas las arquitecturas. [EXP04](EXP04_transporte_temporal_%20de_calibracion_y_umbrales_de%3Adecision/CONCLUSIONS.md),
[cierre BETA V1](EXP-BETA/CONCLUSIONS.md), [V2](EXP-BETA01-V2/CONCLUSIONS.md).

### 8–9. Heterogeneidad territorial y generalización nacional

EXP02 registra deterioro departamental en 91 de 176 puntos favorables agregados;
EXP03 tiene fallos de controles por perfil; BETA01 L1 falla 43/48 estratos; V2
muestra compensaciones distintas en Meta/Tolima. Son observaciones relacionadas,
no replicaciones que puedan contarse como votos independientes. El departamento
es una agrupación administrativa, no un mecanismo epidemiológico identificado:
que exista heterogeneidad no garantiza que separar interceptos o umbrales por
esa agrupación la resuelva. V2 no resuelve generalización hacia Meta–Tolima y
no mide generalización a territorios nacionales no evaluados.
[EXP02](EXP02_label_stability/CONCLUSIONS.md), [EXP03](EXP03_feature_ablation/CONCLUSIONS.md),
[BETA01](EXP-BETA01/CONCLUSIONS.md), [V2](EXP-BETA01-V2/COMPARISONS_BY_STRATUM.csv).

### 10. La dificultad específica de T+2

En la cohorte Y(T)=0, T+1 requiere exceso al mes siguiente. T+2 requiere además
que T+1 siga sin exceso: una alerta de continuación es un error para inicio.
EXP01 muestra que objetivos distintos no producen ventaja estable; EXP03 encuentra
menor aporte del estado actual; EXP03.1 no lo compensa con memoria gruesa.
NB2 añade un límite matemático: dos distribuciones marginales no identifican
la probabilidad conjunta de esa transición. V2 mantiene solo 219 inicios
elegibles frente a 313 T+1, con distinto soporte y embargo; no es una comparación
del mismo conjunto de eventos a mayor distancia. La menor información sobre la
transición, el soporte y su variación temporal son explicaciones abiertas, no
una demostración de que anticipar T+2 sea imposible.
[EXP01](EXP01_direct_onset/CONCLUSIONS.md), [EXP03](EXP03_feature_ablation/CONCLUSIONS.md),
[NB2](EXP-BETA02/CONCLUSIONS.md), [V2](EXP-BETA01-V2/RESULTS.md).

## Capítulo 5. Arquitecturas y enfoques realmente evaluados

| Enfoque y fuente | Componente cambiado / pregunta | Ventaja observada | Limitación | Aporte científico |
|---|---|---|---|---|
| [R0 histórico](EXP-BETA03/CONCLUSIONS.md) | Referencia M00/XGBoost/onset congelada, ya compartida | Control trazable, mayor detección T+2 que G0/G1 | Carga BETA agrupada >1; no champion | Separa reproducibilidad de aceptabilidad |
| [G0 tabular](EXP-BETA01/CONCLUSIONS.md) | Representación canónica y roles BETA regionales | Más detección y menos FA T+1 que R0 | Pérdida T+2; no aísla innovación por pooling | Un procedimiento puede mejorar un horizonte y empeorar otro |
| [L1 departamental](EXP-BETA01/CONCLUSIONS.md) | Intercepto residual regularizado sobre G0 | Ganancia puntual T+2 OFF | Efectos mixtos, 43/48 fallos conjuntos | Heterogeneidad no garantiza beneficio de adaptación ligera |
| [G1 nacional](EXP-BETA01-V2/protocol.json) | Añadir filas nacionales con familia/variables/roles regionales fijos | Mayor AP y menor Brier agrupados | Peores pares detección/FA; AP T+1 anual peor | Ampliación geográfica y utilidad regional no son equivalentes |
| [NB2 marginal](EXP-BETA02/CONCLUSIONS.md) | Pronosticar conteos sobredispersos y derivar riesgo H5 | Distribuciones y cuantiles reproducibles | No cumple criterio T+1 ni identifica inicio T+2 | Pronosticar nivel no identifica transición conjunta |
| [GLOBAL/DEPARTMENT](EXP-BETA03/CONCLUSIONS.md) | Cambiar política sobre probabilidades R0 fijas | Menos FA sin reajustar predictor | Pérdida excesiva de detección; local solo 2020 | Aísla el costo de la restricción y del denominador de selección |

Son comparaciones alternativas y controles de componentes, no una cadena
obligatoria G0→NB2→filtro. **No se implementaron ni evaluaron** un backbone
neuronal nacional, DeepAR/GRU, detector seguido de segundo clasificador de falsas
alarmas, hard-negative mining ni entrenamiento cost-sensitive explícito en estos
brazos BETA. El presupuesto de selección no equivale a una función de pérdida
asimétrica durante el entrenamiento. BETA03 no encontró FP ≥0,8 en sus ocho
roles de selección y carecía de bloques independientes suficientes para activar
aprendizaje adicional; eso no demuestra ausencia de errores difíciles a otros
niveles ni fracaso de esos métodos. [Diseño](EXP-BETA/DESING.md),
[cierre ejecutado](EXP-BETA/CONCLUSIONS.md), [diagnóstico BETA03](EXP-BETA03/RESULTS.md).

## Capítulo 6. Desempeño conjunto y compensaciones

### Qué comparaciones numéricas son válidas

| Serie | Evento, población y periodo | Uso permitido en esta síntesis |
|---|---|---|
| EXP00 | Exceso mensual, 912 filas/86 inicios, 2025; FAR de exceso | Contexto histórico; no restar sus tasas a las de BETA |
| EXP01/02 | Cohortes propias; 2020/2022/2024; EXP02 intersecta historia H5/H7/H9 | Contrastes internos; no atribuir diferencias entre experimentos a un solo componente |
| EXP03/03.1 | Inicio, tres cortes de desarrollo y estrés; carga sobre exposición monitoreada | Aportes internos de variables; separar sumas de celdas repetidas y medias macro |
| EXP04 | Inicio y exposición elegible común; desarrollo separado de estrés | Contraste interno A0/A; no trasladar automáticamente tasas históricas R0 |
| BETA01/02/03/V2 | Claves y verdad emparejadas con R0; exposición elegible/12 | Comparación descriptiva de procedimientos en mismo horizonte/periodo; T+2 NB2 excluido |

Fuentes: [EXP00](EXP00_historical_baseline/CONCLUSIONS.md),
[EXP01](EXP01_direct_onset/CONCLUSIONS.md), [EXP02](EXP02_label_stability/CONCLUSIONS.md),
[EXP03](EXP03_feature_ablation/CONCLUSIONS.md), [EXP03.1](EXP03.1_add_pass_info/CONCLUSIONS.md),
[EXP04](EXP04_transporte_temporal_%20de_calibracion_y_umbrales_de%3Adecision/CONCLUSIONS.md),
[comparabilidad BETA](EXP-BETA/CONCLUSIONS.md).

Sensibilidad = TP/inicios; precisión = TP/(TP+FP); carga = FP/exposición.
FAR es FP/alertas, no FPR ni carga anual. Brier compara probabilidades con su
verdad declarada; AP no es precisión del umbral. Los horizontes no se suman como
episodios únicos. No se promedian AP anuales para representar AP agrupada, ni
se transforma ausencia de intervalos en evidencia de equivalencia.

### Comparaciones comunes que ayudan a interpretar V2

Los siguientes contrastes de procedimientos comparten soporte BETA: 313 inicios
T+1 o 219 T+2 en los cuatro años. Son diferencias pareadas descriptivas de
conteos, no estimaciones causales de una arquitectura ni selección posterior.

| Candidato − control | Horizonte | Δ detecciones | Δ FA | Lectura conjunta |
|---|---|---:|---:|---|
| G0 OFF − R0 | T+1 | +4 | −52 | Ganancia agrupada posible antes de expansión nacional |
| G0 ON − G0 OFF | T+1 | +6 | +25 | Clima añade detección con carga |
| G0 ON − G0 OFF | T+2 | +5 | −9 | Ganancia conjunta de este contraste, sin rescatar margen frente a R0 |
| NB2 ON − G0 ON | T+1 | 0 | +18 | Igual detección agrupada no implica iguales inicios identificados |
| GLOBAL − R0 | T+1 | −46 | −95 | Menor carga con pérdida inadmisible |
| GLOBAL − R0 | T+2 | −29 | −81 | Mismo patrón bajo probabilidades idénticas |
| G1 OFF − G0 OFF | T+1 | −5 | +8 | Deterioro conjunto |
| G1 OFF − G0 OFF | T+2 | −1 | +21 | Deterioro conjunto |

Fuentes: [BETA01](EXP-BETA/RESULTS.md), [BETA02](EXP-BETA02/RESULTS.md),
[BETA03](EXP-BETA03/RESULTS.md), [V2](EXP-BETA01-V2/COMPARISONS_BY_STRATUM.csv).
DEPARTMENT se omite de esta tabla porque solo tiene 2020; en ese soporte pierde
21/14 detecciones T+1/T+2 frente a R0. No se compara con R0 de cuatro años.
NB2 OFF falla el margen T+1 con −2,2364 pp; ON falla carga con 1,004146, aunque
un redondeo a 1,00 parezca admisible. [BETA02](EXP-BETA02/RESULTS.md),
[BETA03](EXP-BETA03/RESULTS.md).

La precisión tampoco resuelve sola la decisión: en EXP04 aumenta en los seis
agregados móviles de desarrollo mientras cae la sensibilidad. En V2 disminuye
en ambos horizontes frente a G0, pese a mejores AP/Brier agrupados. La incertidumbre
NB2 ilustra otra compensación: cobertura 97,32–97,81% de intervalos nominales
90% acompaña anchos medios de aproximadamente 22–31 notificaciones; cubrir más
no demuestra precisión ni calibración completa. [EXP04](EXP04_transporte_temporal_%20de_calibracion_y_umbrales_de%3Adecision/CONCLUSIONS.md),
[V2](EXP-BETA01-V2/RESULTS.md), [NB2](EXP-BETA02/RESULTS.md).

El patrón temporal no se reduce a «2024 fue difícil»: en G1 T+1 la carga supera
1 en 2020, 2022 y 2024, pero es 0,340426 en 2021, cuando detecta solo 8/52
inicios. En T+2 supera 1 en 2022/2024 (1,609984/1,217391). La carga agrupada
inferior a uno combina regímenes con comportamiento distinto. Por territorio,
los totales Meta/Tolima tampoco garantizan cumplimiento año por año. El punto
pendiente es conservar ambos objetivos en cada contexto con soporte suficiente,
no escoger el promedio menos desfavorable. [V2](EXP-BETA01-V2/RESULTS_BY_STRATUM.csv).

## Capítulo 7. Cinco hipótesis explicativas, todavía abiertas

Estas hipótesis organizan incertidumbre; no cambian los dictámenes congelados.
La última columna describe contrastes que podrían aportar evidencia bajo otra
autorización, no experimentos ejecutados ni un plan de implementación.

| Hipótesis | Observación y evidencia favorable | Evidencia contraria o límite | Información faltante | Comprobación acotada posible |
|---|---|---|---|---|
| **H1. La mezcla nacional introduce transferencia desigual por composición territorial e histórica.** | G1 empeora los puntos operativos y el efecto neto T+1 recae en Tolima; soporte nacional inicia en 2016. [V2](EXP-BETA01-V2/COMPARISONS_BY_STRATUM.csv) | Mejora Brier en seis de ocho cortes; Meta T+2 gana detecciones. No hay deterioro universal | Efecto geográfico separado de meses, volumen y proporción de clases | Comparar expansión sobre una historia común y composición predeclarada, manteniendo algoritmo/roles y un control regional con ese mismo soporte; no escoger territorios por resultados de evaluación |
| **H2. La variación temporal altera el transporte del punto de alerta.** | Cambian prevalencias y carga; G1 T+1 invierte la lectura AP anual/agrupada; EXP04 muestra desviación selección→evaluación. [EXP04](EXP04_transporte_temporal_%20de_calibracion_y_umbrales_de%3Adecision/CONCLUSIONS.md), [V2](EXP-BETA01-V2/RESULTS_BY_STRATUM.csv) | EXP04 no arregla detección al recalibrar; aumentar historia tampoco garantiza mejora | Separación de cambio de prevalencia, distribución de X y relación X–Y | Contraste temporal predeclarado con predictor fijo y política seleccionada en bloques anteriores; estudiar escala y orden por bloque, con evaluación externa intacta |
| **H3. H5 y el soporte limitado de transiciones dificultan aprender el evento relevante, especialmente T+2.** | EXP02 sustituye identidades; NB2 marginal no identifica transición; 219 inicios elegibles T+2. [EXP02](EXP02_label_stability/CONCLUSIONS.md), [NB2](EXP-BETA02/CONCLUSIONS.md) | H5 fija sí admite aportes útiles de variables; inestabilidad entre definiciones no demuestra error de H5 | Correspondencia con episodios epidemiológicos externos y soporte efectivo independiente | Adjudicación externa ciega de un conjunto acotado de episodios; mantener H5 como referencia. Para conteos, estudiar identificabilidad conjunta antes de elegir arquitectura |
| **H4. La mejora de riesgo promedio no mejora el orden y la decisión en la región de baja carga.** | V2 mejora métricas agrupadas con peores alertas; EXP04 cambia Brier sin cambiar decisiones entre ventanas. [V2](EXP-BETA01-V2/RESULTS.md), [EXP04](EXP04_transporte_temporal_%20de_calibracion_y_umbrales_de%3Adecision/CONCLUSIONS.md) | G1 T+1 pierde AP en todos los años: el problema no tiene por qué ser solo el umbral. BETA03 ya muestra límites de restringirlo | Qué diferencias provienen de ordenación cerca del umbral y cuáles del transporte de su selección | Diagnóstico pareado de puntuaciones y políticas guardadas por corte, sin elegir otro umbral en evaluación; una intervención posterior requeriría selección y prueba separadas |
| **H5. La representatividad y disponibilidad de las notificaciones limitan la señal transportable.** | Datos consolidados, ceros asumidos bajo cobertura, registros territoriales sin asignar y desigual historia. [Validación nacional](../../data/canonical-national-validation.md) | Paridad exacta regional y reproducción técnica; no hay evidencia que atribuya los errores a corrupción o pérdida de fuentes | Completitud oficial, versiones por fecha de reporte, equivalencia geográfica histórica | Auditoría acotada frente a una extracción oficial/versiones de disponibilidad, sin alterar los históricos; contraste futuro con información realmente conocida al origen |

Estas explicaciones pueden coexistir. Ninguna queda demostrada por una correlación
entre año, territorio y error. En particular, la ausencia de mejora no distingue
por sí sola falta de información, mala representación, muestra no comparable o
selección de política inestable.

## Capítulo 8. Oportunidades de investigación, en orden de valor informativo

El orden prioriza discriminación entre explicaciones y viabilidad, no una promesa
de desempeño. Ninguna oportunidad autoriza entrenamiento o cambia criterios.

| Prioridad / oportunidad | Respaldo disponible | Potencial detección–carga | Datos realmente disponibles | Evaluación rigurosa y condición | Complejidad |
|---|---|---|---|---|---|
| **1. Localizar la discrepancia entre ranking, escala y punto de alerta G1/G0 por año.** | Inversión AP T+1 y contrastes adversos verificables | Identificar si existe margen útil antes de cambiar predictor/política; mejora no garantizada | Puntuaciones, alertas y roles congelados de G0/G1 | Diagnóstico pareado sin optimizar sobre evaluación; cualquier política nueva requerirá prueba independiente | Baja para diagnóstico |
| **2. Separar composición geográfica de historia/recencia en la transferencia.** | Soporte nacional corto y efectos territoriales mixtos | Evitar mezclar fuentes poco transferibles, si se demuestra ese mecanismo | Tabla nacional identificada y controles regionales; falta historia nacional H5 previa a 2016 | Historia común y composición fijadas antes del contraste; años reutilizados solo exploratorios | Media |
| **3. Obtener evidencia temporal y de disponibilidad independiente.** | Transporte inestable repetido; no hay anticipación real acreditada | Determinar si la señal es utilizable y si persiste; prerrequisito de aprobación, no ajuste de métricas | Fuentes consolidadas existentes; no se acreditan vintages ni un bloque nuevo maduro/intacto | Verificar acceso, madurez y ausencia de consumo antes de reservar; no convertir 2025 en reserva virgen | Alta por acceso/tiempo |
| **4. Validar externamente la identidad de los episodios H5.** | Cambios H5/H7/H9 documentados | Evitar optimizar una definición desconectada de la decisión sanitaria | Etiquetas históricas; referencia epidemiológica independiente aún no verificada | Adjudicación ciega y acuerdo de criterios antes de examinar errores; sin reemplazar H5 retrospectivamente | Media–alta |
| **5. Estudiar una representación conjunta parsimoniosa para inicio T+2.** | Límite explícito NB2 y débil aporte del estado T a dos meses | Separar nuevo inicio de continuación sin usar futuro observado | Trayectorias mensuales canónicas, con límites de soporte/historia | Comparador directo de inicio y misma cohorte; justificar soporte antes de ajustar una distribución conjunta | Media–alta |

La prioridad 3 es un requisito para cualquier confirmación aunque no sea el primer
diagnóstico ejecutable. Las prioridades 1/2 pueden refinar qué contrastar; no crean
independencia a partir de años consumidos. No se recomienda pasar automáticamente
a L1 nacional, NB2 nacional, BETA03 V2 o redes mayores: el resultado G1 no acredita
una base operativa mejor. [Continuidad V2](EXP-BETA01-V2/CONCLUSIONS.md).

## Capítulo 9. Limitaciones científicas y de reproducibilidad

**Validez científica.** La evaluación retrospectiva usa notificaciones consolidadas;
no reconstruye disponibilidad al cierre de T. H5 es una definición experimental,
no inicio clínico validado externamente. Se reutilizan años y territorios durante
la secuencia de hipótesis; 2024 fue estrés previamente consumido. BETA no evaluó
2025 y EXP00 ya lo consumió para su comparación histórica. No existe confirmación
temporal independiente, validación prospectiva u operativa ni evidencia de impacto
sanitario. Los criterios ≤1 y −2 pp son reglas experimentales adoptadas, no
capacidad de respuesta medida. [EXP00](EXP00_historical_baseline/CONCLUSIONS.md),
[límites BETA](EXP-BETA/CONCLUSIONS.md).

La historia regional/nacional difiere; el entrenamiento añadido no incluye todas
las filas canónicas. El universo nacional usa 1.122 territorios del catálogo,
sin demostrar equivalencia histórica de límites/geometrías. Hay 5.663 registros
territoriales no asignados dentro de la ventana, posibles duplicados conservados
y completitud de extracción oficial no certificada. La tabla mantiene faltantes
climáticos en dos territorios insulares; clima completo alcanza 182.560 de
182.886 filas, sin convertir eso en prueba de utilidad. V2 OFF no cubre la
interacción clima–transferencia. La evaluación principal sigue limitada a
Meta–Tolima y los perfiles validados de BETA siguen ausentes.
[Validación nacional](../../data/canonical-national-validation.md),
[límites V2](EXP-BETA01-V2/CONCLUSIONS.md).

Las observaciones municipio-mes, años, cortes, familias y estratos no son
replicaciones independientes. Las tasas agrupadas pueden ocultar daños anuales,
y AP agrupada depende de mezclar escalas temporales. EXP00/EXP03 contienen
intervalos históricos bajo sus reglas, pero no se transfieren a BETA ni prueban
superioridad de G1. No hay soporte para declarar no inferioridad estadística o
superioridad de V2: `UNAVAILABLE` / `NOT_ESTABLISHED`. No se inventan intervalos,
pruebas ni nuevas métricas en esta síntesis.
[EXP03](EXP03_feature_ablation/CONCLUSIONS.md), [V2](EXP-BETA01-V2/protocol.json).

**Reproducibilidad técnica.** La publicación V2 identifica ocho modelos y reproduce
sus predicciones sin ajustes; eso no subsana los límites de validez anteriores.
La presente revisión verificó hashes de los 25/27/8/40 payloads de BETA01 V1,
BETA02 V1, BETA03 V1 y BETA01 V2, respectivamente; cotejó las dos tablas públicas
V2 con los CSV nativos y recalculó conteos, AP y Brier de sus 90 estratos a partir
de predicciones ya guardadas. No ejecutó inferencia ni reentrenamiento. Para
EXP00–EXP04 se utilizaron conclusiones originales auditadas, protocolos y
localizadores de resultados; no se afirma repetir sus auditorías exhaustivas.
[Identidades V1](EXP-BETA/CONCLUSIONS.md), [identidad V2](EXP-BETA01-V2/RESULTS.md).

Persisten límites técnicos históricos específicos: EXP01 no guardó probabilidades
individuales para reconstrucción completa; EXP02 documenta redondeo que altera
la reaplicación literal de ciertos umbrales; EXP03.1 distingue replay observable
de estados intermedios originales y conserva una discrepancia de contadores de
lectura. No se «corrigen» resultados originales en esta síntesis. Los hallazgos
heredados de CI/inventario privado descritos en V2 tampoco son evidencia de
mecanismo epidemiológico ni quedan resueltos por añadir documentación.
[EXP01](EXP01_direct_onset/CONCLUSIONS.md), [EXP02](EXP02_label_stability/CONCLUSIONS.md),
[EXP03.1](EXP03.1_add_pass_info/CONCLUSIONS.md), [estado técnico V2](EXP-BETA01-V2/README.md).

## Capítulo 10. Conclusiones finales

1. **¿Qué hemos demostrado?** Equivalencia inicio/exceso T+1 bajo Y(T)=0,
   sensibilidad de la identidad de episodios a H, contribuciones predictivas
   condicionales del estado T y umbrales históricos, y separación empírica entre
   error probabilístico y utilidad de alerta. Se demostraron resultados
   reproducibles de procedimientos concretos, no eficacia operativa general.
   [EXP01](EXP01_direct_onset/CONCLUSIONS.md), [EXP02](EXP02_label_stability/CONCLUSIONS.md),
   [EXP03](EXP03_feature_ablation/CONCLUSIONS.md), [EXP04](EXP04_transporte_temporal_%20de_calibracion_y_umbrales_de%3Adecision/CONCLUSIONS.md).
2. **¿Qué hipótesis no recibieron respaldo?** La mejora general por cambio
   semestral M02, la adaptación L1 fijada, NB2 marginal como mejora conjunta de
   alertas, las políticas BETA03 y la ampliación G1 V2 bajo sus reglas.
   EXP01/EXP03 conservan sus disposiciones inconclusas; componentes no ejecutados
   conservan ausencia de evaluación. No se refutan todas las alternativas de esas
   familias. [EXP03.1](EXP03.1_add_pass_info/CONCLUSIONS.md),
   [cierre V1](EXP-BETA/CONCLUSIONS.md), [V2](EXP-BETA01-V2/CONCLUSIONS.md).
3. **¿Qué mejoró sin producir mejores alertas?** Brier de ciertas calibraciones,
   distribuciones reproducibles de conteos, reducción de FA por restricción de
   umbrales y AP/Brier agrupados nacionales. La AP T+1 nacional favorable no
   se sostiene dentro de ningún año; la mejora agregada no acredita una
   discriminación anual superior. [EXP04](EXP04_transporte_temporal_%20de_calibracion_y_umbrales_de%3Adecision/CONCLUSIONS.md),
   [NB2](EXP-BETA02/RESULTS.md), [BETA03](EXP-BETA03/RESULTS.md),
   [V2](EXP-BETA01-V2/RESULTS_BY_STRATUM.csv).
4. **¿Qué conocimiento nuevo aportó entrenar nacionalmente?** Existe una prueba
   identificada de transferencia con evaluación regional exactamente conservada:
   añadir muchos municipios elegibles no mejoró sus puntos operativos. La mezcla
   aporta historia desigual y modifica de manera distinta probabilidades y
   decisiones; ya no basta invocar escasez de municipios como explicación
   suficiente. Su efecto geográfico separado de la composición temporal sigue
   sin identificarse. [Protocolo](EXP-BETA01-V2/protocol.json),
   [soporte](EXP-BETA01-V2/TRAINING_SUPPORT.csv).
5. **¿Cuál es el principal problema pendiente?** Determinar qué información y
   regla de decisión separan de forma transportable los inicios relevantes de
   los no inicios bajo una carga admisible, con evento válido y datos disponibles
   a tiempo. La evidencia ubica el problema en esa relación conjunta; no permite
   reducirlo exclusivamente a calibración, arquitectura o definición H5.
   [EXP03](EXP03_feature_ablation/CONCLUSIONS.md), [cierre V1](EXP-BETA/CONCLUSIONS.md),
   [V2](EXP-BETA01-V2/CONCLUSIONS.md).
6. **¿Qué conviene preguntar después?** «¿La discrepancia G1/G0 procede de
   ordenación dentro del corte, de la escala entre cortes o del transporte del
   umbral seleccionado?» Es la pregunta más inmediata porque las puntuaciones
   guardadas permiten diagnosticarla sin aumentar complejidad y porque la
   inversión AP agrupada/anual impide presuponer una mejora discriminativa.
   Su respuesta podría justificar un contraste de composición o política;
   no autoriza escoger otro umbral sobre estos años ni declarar confirmación.
   [Métricas y contrastes V2](EXP-BETA01-V2/COMPARISONS_BY_STRATUM.csv).

**Conclusión de tesis:** SAT-Dengue demuestra que aprender más información,
representar mejor algunos aspectos del riesgo y reducir alertas son capacidades
distintas de anticipar inicios con carga estable. La expansión nacional fortalece
esta conclusión al conservar el control regional y obtener resultados operativos
adversos pese a métricas probabilísticas agrupadas favorables. La contribución
acumulada es delimitar con controles reproducibles qué mejoras parciales no
resuelven aún la decisión, y qué evidencia falta para distinguir las explicaciones.
No prueba imposibilidad predictiva ni autoriza una arquitectura mayor por defecto.
**G5 `NOT_APPROVED`; `champion: not_selected`.**
