# Análisis científico 6 — Síntesis EXP00–EXP04 y EXP-BETA V1

**Pregunta:** ¿qué aprendimos de los experimentos históricos y qué conocimiento
adicional aportó EXP-BETA V1 para mejorar la detección anticipada de brotes de dengue?

Consolidación documental al 2 de noviembre de 2026, sobre `main` en
`a2f89110c84969f2ca2fb635532383e1271ec8b6`. V1 designa aquí el programa EXP-BETA
entrenado en Meta–Tolima, no renombra SAT-Dengue V1 ni altera identidades de bundles.
Una posible V2 nacional no se ha ejecutado. Se analizan resultados guardados:
no hay entrenamiento, recalibración, reconstrucción de datos ni nueva evaluación.

## A. Resumen ejecutivo

Los experimentos muestran señal predictiva retrospectiva, pero no una mejora
que preserve simultáneamente sensibilidad de inicio, falsas alertas, estabilidad
anual y consistencia territorial. EXP00 documentó el desequilibrio; EXP01–EXP03.1
separaron efecto del objetivo, definición de episodio y representación de variables.
EXP04 mostró que una calibración con menor Brier puede acompañarse de demasiados
inicios perdidos. [Síntesis histórica](analisis-5.md).

BETA V1 añade tres resultados delimitados: G0 ofrece mejoras agregadas T+1,
sin ventaja estable de adaptación local; NB2 produce distribuciones de conteos,
pero no satisface el criterio conjunto T+1 ni identifica inicio T+2; una política
más restrictiva sobre R0 reduce falsas alertas sacrificando sensibilidad.
La contribución es delimitar qué funciona parcialmente y qué sigue sin respaldo,
no demostrar una mejora operativa general. [Cierre de las cuatro fases](EXP-BETA/CONCLUSIONS.md).

Las fuentes nacionales sí permanecen localmente disponibles. La restricción de
V1 procede de la tabla admitida de Meta–Tolima, no de una pérdida demostrada de
los originales. Esto mantiene abierta G1 como hipótesis, sin convertirla en un
experimento ejecutado. **G5 `NOT_APPROVED`; `champion: not_selected`.**

## B. Evolución de la investigación

La secuencia es una evolución de preguntas, no un ranking numérico común:

1. **Evento epidemiológico:** EXP01 demuestra equivalencia de inicio/exceso T+1
   cuando `Y(T)=0`, pero exige distinguirlos en T+2. EXP02 muestra que cambiar
   H5/H7/H9 altera identidad y fragmentación de episodios. Se mantiene H5 por
   comparabilidad, no como verdad epidemiológica externa.
   [Análisis 1](analisis-1.md), [análisis 2](analisis-2.md).
2. **Variables predictivas:** EXP03 encuentra señal en el estado actual para
   T+1 y en umbrales históricos del mes objetivo para boosting; el clima tiene
   efectos condicionados. EXP03.1 encuentra valor limitado de conteos gruesos
   de estados recientes y no respalda el cambio entre semestres.
   [Análisis 3](analisis-3.md), [análisis 4](analisis-4.md).
3. **Aprendizaje compartido y adaptación:** el histórico ya agrupaba municipios.
   BETA01 prueba otra representación/procedimiento G0 e interceptos L1, pero
   no expansión nacional G1. La hipótesis territorial se somete a controles
   conjuntos, sin suponer que toda heterogeneidad exige modelos separados.
   [Conclusiones BETA01](EXP-BETA01/CONCLUSIONS.md).
4. **Pronóstico probabilístico:** BETA02 cambia la representación de salida a
   conteos NB2 y separa distribución, exceso e inicio. La marginal T+2 no
   identifica una transición conjunta; ese límite matemático se conserva.
   [Conclusiones BETA02](EXP-BETA02/CONCLUSIONS.md).
5. **Calibración, alerta y estabilidad:** EXP04 no logra una política elegible;
   BETA03 prueba umbrales globales y territoriales sobre R0 congelado. El
   presupuesto de desarrollo no garantiza su cumplimiento futuro, y ahorrar
   alertas puede perder demasiados inicios. [EXP04](EXP04_transporte_temporal_%20de_calibracion_y_umbrales_de%3Adecision/CONCLUSIONS.md),
   [BETA03](EXP-BETA03/CONCLUSIONS.md).

## C. Comparación científica entre experimentos

Cada enlace conduce al propietario de conclusiones, protocolo e identidad de
resultados. Se preservan sus disposiciones: una síntesis favorable parcial no
reemplaza un veredicto `INCONCLUSIVE` del protocolo.

| Experimento | Pregunta científica | Enfoque evaluado | Hallazgo principal | Limitación | Contribución al conocimiento |
|---|---|---|---|---|---|
| [EXP00](EXP00_historical_baseline/CONCLUSIONS.md) | ¿La referencia histórica detecta inicios con carga admisible? | Registro/replay de XGBoost, LightGBM y GAM congelados, frente a persistencia | Los seis procedimientos detectan más y exceden el margen histórico de FAR | Bloque 2025 consumido; falsa alerta respecto a exceso; no es un experimento predictivo nuevo | Línea base negativa reproducible; sensibilidad aislada insuficiente |
| [EXP01](EXP01_direct_onset/CONCLUSIONS.md) | ¿Ayuda entrenar inicio directamente? | Inicio/exceso, familias y frentes de presupuestos emparejados | T+1 idéntico; ventajas T+2 mixtas, clasificación `INCONCLUSIVE` | Cortes 2020/2022 y estrés 2024; intervalos pareados no disponibles | Evita duplicar objetivos T+1 y conserva exceso como control distinto T+2 |
| [EXP02](EXP02_label_stability/CONCLUSIONS.md) | ¿Es estable el episodio al cambiar historia del canal? | H5/H7/H9 sobre población común, verdad propia y H5 fija | Sustitución de inicios y fragmentación; sin superioridad general de H7/H9 | Sin validación epidemiológica externa; mejor Brier propio puede cambiar la pregunta | Congelar identidad del evento durante comparaciones predictivas |
| [EXP03](EXP03_feature_ablation/CONCLUSIONS.md) | ¿Qué bloques aportan señal? | Ablación selectiva de estado T, historia, umbrales y clima | Estado T útil principalmente T+1; umbrales prometedores para boosting | Disposiciones primarias `inconclusive`; guardrails no superados y transporte 2024–2025 no evaluable | Mapa condicional de información, sin ganancia universal del clima |
| [EXP03.1](EXP03.1_add_pass_info/CONCLUSIONS.md) | ¿Ayuda la trayectoria reciente del canal? | M00, M01 memoria semestral, M02 cambio entre semestres | Q1 `PARCIALMENTE_RESPALDADA`; Q2/Q3 `NO_RESPALDADA` | Ganancia pequeña con mayor carga; variación por año/familia/horizonte | No promover memoria gruesa como solución general ni M02 como mejora |
| [EXP04](EXP04_transporte_temporal_%20de_calibracion_y_umbrales_de%3Adecision/CONCLUSIONS.md) | ¿Se transporta calibración/umbral preservando detección y carga? | A0 frente a A1–A3, ventanas móviles 12/24/36 meses | Menor carga y Brier, pero pérdida de sensibilidad fuera del margen | A4 sin origen expansivo; B/C y composición D no evaluables | Distingue calibración probabilística de utilidad de alertas |
| [EXP-BETA01](EXP-BETA01/CONCLUSIONS.md) | ¿Mejoran pooling/ampliación y adaptación territorial? | G0/L1 XGBoost, clima OFF/ON, R0 emparejado | Ganancias agregadas G0 T+1; adaptación `NO_RESPALDADA`, T+2 deteriorado | G1 y perfiles `NO_EVALUABLE`; R0 ya agrupaba los 76 municipios | Separar nueva representación de transferencia nacional y de ajuste local |
| [EXP-BETA02](EXP-BETA02/CONCLUSIONS.md) | ¿Conteos probabilísticos mejoran las alertas? | NB2 marginal por horizonte y clima | Ningún NB2 cumple ambos criterios T+1; distribución reproducible | Inicio T+2 no identificado; sin comparador R0 de conteos ni red entrenada | El riesgo marginal no sustituye trayectoria; error de conteos no acredita utilidad |
| [EXP-BETA03](EXP-BETA03/CONCLUSIONS.md) | ¿Puede reducirse carga conservando sensibilidad? | GLOBAL/DEPARTMENT sobre R0 congelado | Menos FA con pérdida excesiva de detección; `NO_RESPALDADA` | DEPARTMENT solo 2020; aprendizaje adicional no justificado | Aísla cambio de política y demuestra límites del control de carga en desarrollo |

**Comparabilidad:** EXP00 usa 2025 y FAR de exceso; EXP01/02 usan otras cohortes
históricas; EXP03/03.1 emplean exposición monitoreada, mientras BETA evalúa carga
sobre filas elegibles/12. EXP04 separa desarrollo 2020–2022 del estrés 2024.
No se mezclan sus métricas como si estimaran un mismo efecto. En BETA se verifica
igualdad completa de claves/verdad con R0; aun así, BETA01/02 cambian roles de
ajuste y representación. Solo BETA03 mantiene también las probabilidades.

Sensibilidad = TP/inicios; precisión = TP/(TP+FP); FAR = FP/(TP+FP), con el evento
propio de cada protocolo; FPR = FP/negativos. FA por municipio-año = FP/exposición.
FAR no es la tasa anual ni la probabilidad de detectar un inicio. Tasas agrupadas
se recomputan desde sumas; tasas macro promedian celdas y no son intercambiables.
[Convenciones históricas EXP03.1](EXP03.1_add_pass_info/CONCLUSIONS.md#9-denominadores-y-convenciones-de-métricas),
[convenciones BETA01](EXP-BETA01/CONCLUSIONS.md#resultados-reales-y-comparación-con-r0).

## D. Hallazgos transversales

**Dónde aparece señal y qué mejora detecciones.** EXP03 atribuye contribuciones
condicionales al estado contemporáneo y a P25/P75 históricos del mes objetivo;
parte de estos últimos puede representar la frontera matemática que define H5,
sin probar un mecanismo biológico. En BETA01, G0 OFF/ON obtiene 146/152 detecciones
T+1 frente a 142 de R0, con 179/204 FA frente a 231. Es evidencia favorable de
procedimientos sobre la misma cohorte, no de transferencia nacional ni efecto
causal aislado de nuevas variables. [EXP03](EXP03_feature_ablation/CONCLUSIONS.md),
[BETA01](EXP-BETA01/CONCLUSIONS.md).

**Qué reduce carga y a qué costo.** EXP04 reduce sensibilidad de desarrollo
entre 5,7 y 15,2 pp con ventanas móviles. BETA03 reduce 95 FA T+1 y 81 T+2,
pero pierde 46 y 29 detecciones adicionales. BETA02 OFF pierde 2,2364 pp; ON
supera el límite con 1,004146 FA/municipio-año. Una mejor precisión, Brier o
menor número de alertas no acredita el criterio conjunto. [EXP04](EXP04_transporte_temporal_%20de_calibracion_y_umbrales_de%3Adecision/CONCLUSIONS.md),
[BETA02](EXP-BETA02/CONCLUSIONS.md), [BETA03](EXP-BETA03/CONCLUSIONS.md).

**Territorio y tiempo.** EXP02 registra deterioro departamental en 91 de 176
puntos favorables agregados; son puntos correlacionados del frente, no réplicas.
BETA01 L1 falla 43/48 estratos conjuntos y BETA03 GLOBAL solo cumple 8/24.
Agrupar oculta fallos; separar por departamento tampoco asegura mejora, como
muestra DEPARTMENT en 2020. Más municipios no sustituyen años independientes.
[EXP02](EXP02_label_stability/CONCLUSIONS.md), [BETA01](EXP-BETA01/CONCLUSIONS.md),
[BETA03](EXP-BETA03/CONCLUSIONS.md).

**Aporte del clima.** EXP03 no respalda un efecto general y algunas ganancias
T+2 de boosting aumentan mucho las FA. BETA01 G0 ON frente a OFF añade seis
inicios y 25 FA en T+1; añade cinco y reduce nueve FA en T+2. NB2 ON mejora
MAE/log score agregados, pero empeora RMSE T+2. Son contrastes específicos de
representación, cohorte y protocolo; no demuestran inutilidad ni ventaja universal
del clima. [EXP03](EXP03_feature_ablation/CONCLUSIONS.md),
[BETA01](EXP-BETA01/CONCLUSIONS.md), [BETA02](EXP-BETA02/CONCLUSIONS.md).

**Modelar conteos.** NB2 permite describir sobredispersión y cuantiles predictivos;
la cobertura 97,3–97,8% de intervalos nominales del 90% va acompañada de amplitud
considerable. No prueba precisión útil, mejor alerta ni superioridad frente a
un R0 sin distribución de conteos. Inicio T+2 requiere dependencia entre meses:
dos marginales no bastan. [BETA02](EXP-BETA02/CONCLUSIONS.md).

**Valor limitado y resultados negativos.** EXP03.1 Q1 suma cinco detecciones
con 58 FA adicionales y Q3 pierde diez con 30 FA adicionales; son sumas de
24 pares de celdas, con eventos repetidos entre familias/horizontes, no individuos
únicos. Ni memoria gruesa, ni adaptación L1, ni recalibración o restricción de
umbrales resolvieron el frente conjunto. Esto acota esas formulaciones sin
refutar toda adaptación, toda red neuronal ni los componentes no ejecutados.
[EXP03.1](EXP03.1_add_pass_info/CONCLUSIONS.md), [cierre BETA](EXP-BETA/CONCLUSIONS.md).

## E. Arquitectura realmente implementada

La tabla canónica V1 es una proyección identificada del panel Stage 2: 17.936
filas × 70 columnas, 76 municipios, nueve agregados climáticos y roles separados
para claves, predictores, targets, controles y metadatos. Las allowlists mantienen
los resultados futuros fuera de X; preservar campos no autoriza usarlos como
predictores. Es la base común de experimentos alternativos.
[Contrato canónico](EXP-BETA01/canonical_model_table_v1.json),
[aceptación local](EXP-BETA/PHASE2_IMPLEMENTATION.md).

- **BETA01:** XGBoost tabular G0 y su ajuste departamental L1; clima OFF/ON.
  L1 comparte el estimador G0 y modifica un intercepto, sin modelos municipales.
- **BETA02:** regresiones NB2 con enlace log y dispersión, ajustadas directamente
  desde la tabla; no consumen la salida G0/L1 como una etapa predictora obligatoria.
  Sus probabilidades guardadas solo aportan contexto secundario de comparación.
- **BETA03:** lectura de probabilidades nativas R0 y evaluación posterior de
  umbrales; no entrena otro predictor ni exige usar NB2 como entrada.
- **R0:** referencia histórica M00/XGBoost/onset, con modelos y decisiones
  congelados; se conserva, sin convertirlo en champion.

Son **experimentos predictivos alternativos y una evaluación posterior de políticas**,
no una cadena obligatoria de tres modelos. **No se implementó un backbone neuronal
nacional, una arquitectura de dos clasificadores en cascada ni hard-negative mining.**
Fuentes: [implementación BETA01](EXP-BETA/PHASE2_IMPLEMENTATION.md),
[BETA02](EXP-BETA02/README.md), [BETA03](EXP-BETA03/README.md).

## F. Limitaciones de EXP-BETA V1

V1 entrenó exclusivamente con Meta y Tolima. G1 nacional, perfiles de transmisión,
inicio NB2 T+2 y confirmación temporal independiente son no evaluables.
DeepAR/GRU no contó con justificación secuencial independiente; el aprendizaje
adicional BETA03 carecía de falsos positivos con puntuación ≥0,8 y de bloques
independientes suficientes.
No se infieren resultados para esos componentes. No inferioridad estadística
`UNAVAILABLE`; superioridad `NOT_ESTABLISHED`. [Matriz de las cuatro fases](EXP-BETA/CONCLUSIONS.md#matriz-de-cumplimiento-de-las-cuatro-fases).

2024 fue estrés reutilizado, nunca confirmación independiente. BETA no evaluó
2025; esto no borra el bloque histórico 2025 consumido por EXP00 ni lo convierte
en reserva intacta. Los datos consolidados no reconstruyen qué se sabía en cada
fecha de emisión; H5 no es un desenlace clínico validado externamente. Cohortes
completas y pocos periodos limitan la generalización y el soporte inferencial.
[EXP00](EXP00_historical_baseline/CONCLUSIONS.md), [límites BETA](EXP-BETA/CONCLUSIONS.md#estado-final-de-v1-y-límites-para-una-posible-v2).

### Hallazgo de la auditoría local de fuentes

La auditoría de conservación del 2 de noviembre de 2026 localizó fuentes
nacionales legibles, con identidad local contrastada, y clasificó la disponibilidad
como **`PARTIALLY_AVAILABLE` / `DISPONIBLE CON LIMITACIONES`**. No encontró evidencia
de pérdida definitiva. Se incorporan sus hallazgos aquí como diagnóstico de
fuentes, separado del resultado predictivo y sin una nueva ejecución experimental:

| Fuente local, relativa a la raíz | Evidencia de conservación/cobertura | Identidad SHA-256 |
|---|---|---|
| `data/raw/dengue.csv` | 1.705.604 notificaciones, evento 210; años ANO 2007–2025; 32 departamentos y Bogotá en cada año | `58d277cfef7a60c28d488eefe4e7a1a7bf0f7b0df3dd88245971cd7b3d32c84b` |
| `data/raw/dengue_grave.csv` | 50.101 notificaciones, evento 220; ANO 2007–2025; 32 departamentos y Bogotá en el conjunto, presencia variable por año | `3d60e96ccbedc35a19a8f5f54be8d786aa599813259c914f131522bf17dd1d70` |
| `data/sources/Dengue_Datos_2012_210.xlsx`, `Dengue_Datos_2013_210.xlsx`, `Dengue_Datos_2014_210.xlsx` | 52.467 / 122.441 / 105.356 filas nacionales de evento 210; identidad byte a byte con blobs históricos de Git `1d7450c` comprobada en la auditoría | Correspondencia histórica local; no se publican los archivos privados |

Los hashes de ambos CSV se volvieron a contrastar en esta consolidación con
`data/interim/stage2_consolidated_dataset_pipeline/execution_manifest.json`, campos
`input_fingerprints_before/after`; `reconciliation.source_rows` confirma sus
conteos. La identidad local no certifica exhaustividad epidemiológica frente
al proveedor ni ausencia de duplicados. La auditoría identificó 8.091 filas
sin correspondencia con el catálogo municipal actual y 136 sin fecha de inicio;
las primeras pueden incluir códigos históricos/extranjeros o faltantes y no son
automáticamente registros inválidos. ANO no equivale a extremos de fecha:
existen fechas de notificación hasta 2026 y de inicio desde 2006.

La fuente climática `data/raw/google_earth_engine.csv` cubre municipios nacionales,
pero enero de 2020 solo tiene filas para los 76 de Meta–Tolima: faltan 1.046
municipios/32.426 municipio-días respecto al catálogo actual. La auditoría no
establece completitud de todas las demás variables/fechas ni autoriza imputación.
El respaldo climático anterior verificado tampoco contenía enero de 2020 nacional;
restaurarlo no resuelve esa brecha. No se restauró ni alteró ninguna fuente.
Identidad climática registrada: `dfe20fa02b6d6068c04744b5c86f44112048400a7fde637368c0d4effc88cb3f`;
localizadores de procedencia: el manifiesto Stage 2 anterior y
`data/interim/stage2_january_2020_incorporation_precheck/january_raw_audit.json`
para el diagnóstico previo a la incorporación limitada a Meta–Tolima.

El flujo existente conserva todas las 1.755.705 filas epidemiológicas en
`data/processed/dengue_y_dengue_grave.csv`; 1.515.860 se clasifican fuera del
alcance. La selección `SCOPE_DEPARTMENTS = {"50", "73"}` en
[consolidation.py](../../../src/sat_dengue/data/consolidation.py), su catálogo
normalizado y la agregación de registros asignables restringen el panel mensual;
[workflow.py](../../../src/sat_dengue/data/workflow.py) conserva la consolidación
por filas. La tabla canónica hereda el panel limitado, no todos los CSV nacionales.
Los originales Excel dejaron de estar indexados en Git, pero permanecen locales;
para los CSV no se localizó historial versionado alcanzable, no prueba universal
de que nunca se almacenaran en otro lugar. [.gitignore](../../../.gitignore) y
[reconciliación histórica Stage 2](../../operations/stage2-pr-reconciliation.md)
explican la separación entre fuentes privadas e historial público.

**Fuentes nacionales disponibles no equivale a entrenamiento nacional ejecutado.**
En la V1 no se construyó ni admitió con ellas un panel canónico nacional elegible
para G1. Los documentos congelados que dicen «fuente nacional no disponible» se
refieren al insumo compatible autorizado de aquella ejecución; esta auditoría
posterior no modifica su identidad ni demuestra el resultado de G1. Una tabla
nacional futura podría derivarse por separado, previa validación, preservando
la original; esta viabilidad no es un nuevo dataset ni autorización de implementación.

## G. Conocimiento reutilizable para una V2

**Conclusiones que deben conservarse:** equivalencia T+1 bajo la cohorte vigente,
distinción T+2 entre exceso e inicio, sensibilidad de etiquetas a H y separación
entre calibración, conteos y utilidad de alertas. R0, V1 y sus identidades deben
mantenerse como referencias. No promover L1, NB2 o GLOBAL por una métrica aislada.
[EXP01](EXP01_direct_onset/CONCLUSIONS.md), [EXP02](EXP02_label_stability/CONCLUSIONS.md),
[cierre V1](EXP-BETA/CONCLUSIONS.md).

**Hipótesis futuras, todavía no confirmadas:** ampliar municipios podría aportar
soporte y diversidad útiles para G1, o introducir heterogeneidad perjudicial;
el contraste debe mantener familia, variables, cohortes de evaluación y política.
Perfiles validados podrían ayudar a estudiar heterogeneidad; una distribución
conjunta podría permitir inicio T+2. Ninguna de esas posibilidades se demuestra
por la conservación de fuentes ni por los resultados negativos de V1.
[Diseño original](EXP-BETA/DESING.md), [límites BETA02](EXP-BETA02/CONCLUSIONS.md).

**Controles reutilizables:** H5 y claves emparejadas, mismas fechas de corte para
todos los territorios, roles temporales separados, allowlists, clima OFF/ON sobre
las mismas observaciones, exposición explícita, guardrails por año/departamento,
criterios congelados antes de resultados y artefactos sin sobrescritura. Una
ampliación nacional ayudaría a investigar transferencia y soporte territorial;
no resuelve por sí misma retrasos de reporte, clima faltante, geografía histórica,
validez externa de H5 ni falta de confirmación temporal.

Las preguntas sobre oportunidad real requieren versiones históricas de
notificación u otras fuentes de disponibilidad; la confirmación exige periodos
maduros no consumidos y autorizados. EXP05, EXP06 y futuras propuestas conservan
literalmente su estado y contenido en el [registro activo](../experimentos.md).
Este apartado no crea un plan V2 ni autoriza entrenamiento.

## H. Conclusión científica final

Se demostró que algunas representaciones contienen señal retrospectiva y que
el resultado de alerta depende de objetivo, cohorte, horizonte, territorio y
política. BETA V1 convirtió tres hipótesis en comparaciones identificadas: encontró
ganancias parciales T+1, una limitación explícita de las marginales de conteos y
el costo en sensibilidad de reducir falsas alertas sobre un predictor fijo.

No se demostró mejora general estable, transferencia nacional, no inferioridad
estadística ni anticipación operativa prospectiva. Los resultados negativos son
conocimiento porque descartan la aprobación de procedimientos concretos bajo
criterios congelados, preservan comparadores y evitan confundir métricas favorables
con una solución. Lo no evaluable conserva su incertidumbre; no se convierte en
fracaso o éxito inventado.

Sigue abierto cómo transportar el equilibrio detección–carga entre periodos y
territorios con información disponible a tiempo. V1 aporta una referencia
verificable para investigar esa pregunta; una eventual V2 deberá aportar evidencia
nueva. **G5 `NOT_APPROVED`; `champion: not_selected`.**
