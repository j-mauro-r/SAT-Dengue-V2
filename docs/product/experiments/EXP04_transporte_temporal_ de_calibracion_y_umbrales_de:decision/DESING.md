# EXP04 — Transporte temporal de calibración y umbrales de decisión

**Documento:** `DESING.md` (nombre solicitado)  
**Proyecto:** SAT DENGUE V2 / investigación hacia V3  
**Estado:** diseño propuesto; **NO EJECUTADO / NO VALIDADO**  
**Propósito:** especificación científica para implementación posterior por Codex; no autoriza entrenamiento, evaluación sobre periodos reservados, selección de champion ni despliegue.

## 1. Pregunta científica e hipótesis falsable

**Pregunta principal.** Manteniendo constantes la definición de inicio, las cohortes, los predictores y el modelo base, ¿una estrategia preespecificada de calibración temporal y selección de umbral consigue **transportar mejor** entre años el presupuesto de falsas alertas de onset, **sin pérdida material de sensibilidad** en T+1 o T+2, frente al procedimiento fijo de referencia?

**H1 (hipótesis primaria).** Al menos una política temporal **preseleccionada exclusivamente con desarrollo cronológico** (combinación de ventana de calibración y política de umbral) reduce el exceso y la variación interanual de falsas alertas de onset por municipio-año frente a la referencia congelada, mantiene la sensibilidad dentro del margen de no inferioridad establecido *antes* de evaluar y no causa deterioros territoriales materiales. La política debe satisfacer las condiciones **conjuntamente**, no mediante selección retrospectiva del mejor año, familia u horizonte.

**H0 (hipótesis nula operacional).** Ninguna política candidata demuestra conjuntamente la mejora de transporte de carga y la preservación de detección bajo los criterios y el soporte disponibles; los resultados pueden quedar `NO_RESPALDADA` o `NO_EVALUABLE`, sin asumir equivalencia.

**Hipótesis secundarias, independientes:**
- **H1a — ventana:** una ventana móvil reciente transporta mejor que una expansiva, manteniendo fijo calibrador y selector de umbral.
- **H1b — método:** Platt/sigmoid o isotónica mejora calibración fuera de tiempo frente al calibrador de referencia, manteniendo ventana y selector fijos.
- **H1c — decisión:** una política de selección de umbral basada en presupuesto y robustez entre bloques de desarrollo transporta mejor que la selección puntual de referencia, manteniendo fija la calibración.

Las hipótesis secundarias explican mecanismos potenciales; **no constituyen evidencia de la hipótesis principal por sí solas**.

## 2. Justificación y evidencia de partida

- **EXP00:** las ganancias de sensibilidad coexistieron con exceso de falsas alertas; ninguno de los modelos fue aprobado.
- **EXP01:** la calibración en T+2 sobreestimó en unos años y subestimó en otros; en T+1, exceso e inicio son idénticos dentro de la cohorte `Y(T)=0`.
- **EXP02:** H5/H7/H9 cambian la identidad de eventos; H5 se conserva por comparabilidad, **no** por superioridad epidemiológica. Mejor Brier contra etiquetas diferentes no permite concluir mejor predicción.
- **EXP03:** se identificó señal en estado epidemiológico T para T+1 y P25/P75 históricos para boosting, pero un umbral escogido bajo una falsa alerta por municipio-año no mantuvo necesariamente esa carga fuera del corte usado para seleccionarlo; hubo heterogeneidad temporal y territorial.
- **Investigación V3 y plan actualizado:** priorizan ventanas móviles/expansivas, Platt/isotónica, un presupuesto de carga explícito, umbrales congelados y evaluación por año, horizonte y territorio. La restricción V1 (`+5 pp FAR` respecto al canal) **no es intercambiable** con el presupuesto V2 (falsas alertas de onset por municipio-año).

**Nota de procedencia:** los documentos fuente describen EXP04 como propuesta, no como resultado validado. Los márgenes, rejillas y reglas numéricas de este diseño son **decisiones metodológicas propuestas aquí**, pendientes de congelación y revisión científica antes de ejecutar; no son hallazgos de las fuentes.

## 3. Alcance, estimando y no objetivos

**Estimando principal:** diferencia pareada entre políticas en la **tasa realizada de falsas alertas de onset por municipio-año monitoreado** y en la **sensibilidad de onset**, en el mismo conjunto elegible de municipios-meses y para el mismo corte temporal, horizonte y familia. Complementos: error de calibración y dispersión temporal de la carga.

**Incluye:** T+1, T+2; GAM, LightGBM y XGBoost como familias de referencia si sus artefactos son recuperables y comparables; municipios de Tolima y Meta; calibración global (sin parámetros específicos por territorio); selección temporal de umbrales; evaluación retrospectiva cronológica y controles de calibración/seguridad temporal.

**Excluye:** nuevas variables, nuevas arquitecturas, tuning de hiperparámetros predictivos, reetiquetado H7/H9, entrenamiento territorial, nowcasting, reglas de alertas por episodio, cambio de definición del objetivo, experimentación con clima o selección de un champion. **EXP05** resolverá calibración diferenciada territorial; **EXP06** abordará disponibilidad real.

**Referencia primaria de EXP04:** **M00/EXP03 V09 completo**, tal como se identifica en EXP03.1; H5 y población/objetivo por familia y horizonte permanecen congelados. M01/M02 **no** ingresan automáticamente: EXP03.1 no demostró ganancia general de onset suficiente para promoverlos. La implementación debe identificar inequívocamente versión, artefactos y política de calibración/umbral de la referencia. Si no se puede reconstruir exactamente, registrar `BLOCKED_BASELINE` en lugar de sustituirla silenciosamente.

**Política de evolución:** la referencia de un experimento **no es necesariamente el último modelo ejecutado**. Cada EXP debe registrar por separado (a) su **referencia científica congelada** para comparaciones válidas, (b) sus **variantes investigadas** y (c) cualquier **candidato promovible** sustentado en evidencia. Un resultado prometedor no equivale a aprobación ni a actualización silenciosa de la base. Véase la sección 3.1.

### 3.1. Contrato explícito del modelo base y su evolución (obligatorio)

El término **modelo base** tiene dos usos que deben permanecer diferenciados:

- **Base científica de comparación (baseline congelada):** configuración que permite atribuir al tratamiento EXP04 los cambios observados. Se conserva idéntica **dentro de cada contraste emparejado**.
- **Base candidata acumulativa del programa SAT DENGUE:** versión compuesta únicamente por mejoras que superaron los criterios científicos acordados. Puede evolucionar **entre** experimentos, mediante una decisión documentada y versionada; **no** cambia durante un experimento.

**Estado heredado de EXP00–EXP03.1, según las fuentes aportadas:**

| Elemento | Estado de evidencia | Decisión para la base de EXP04 |
|---|---|---|
| Definición de inicio H5 y cohorte elegible | H5 mantiene comparabilidad; EXP02 no probó superioridad epidemiológica | **Congelar H5** y las reglas de elegibilidad/episodio del contrato M00 |
| T+1, objetivo de inicio/exceso en cohorte `Y(T)=0` | EXP01 demostró equivalencia bajo esa cohorte | **Un único brazo predictivo T+1** |
| T+2, onset versus exceso | EXP01/EXP03 aconsejan separación | **Onset primario** y **exceso control separado**, sin fusionar métricas |
| GAM, LightGBM, XGBoost | Ninguna familia obtuvo aprobación general | Mantener **las tres familias como comparadores**, sin elegir champion |
| Vector predictor **EXP03 V09 completo (M00)** | Referencia que EXP03.1 comparó; incorpora los bloques definidos en el contrato V09 | **Conservar exactamente el vector M00**; no reconstruir su lista de columnas a partir de resúmenes |
| Estado epidemiológico contemporáneo T | EXP03 encontró señal especialmente para T+1, condicionada a disponibilidad | **Mantenerlo solo en la medida exacta en que esté en M00**; no añadir un segundo bloque ni inferir disponibilidad operativa |
| Umbrales históricos P25/P75 del mes objetivo | EXP03 los encontró prometedores para boosting, no causales ni aprobados por sí solos | **Mantenerlos solo como estén configurados en M00**; no reoptimizar ni duplicar features |
| Clima y demás componentes de canal | EXP03 no respaldó incorporar clima como mejora universal; tampoco demostró que retirar el canal fuera equivalente | **No modificar** su inclusión/exclusión heredada de M00 durante EXP04 |
| EXP03.1 M01 (conteos T−1…T−6) | Ganancia de onset marginal con más falsas alertas; no champion | **Excluir del contraste primario**; documentar como variante histórica investigada |
| EXP03.1 M02 (cambio contra T−7…T−12) | Hipótesis de mejora general no respaldada | **Excluir del contraste primario** |
| Predictor entrenado, hiperparámetros, semillas y scores OOF | Deben verificarse con artefactos reales; los resúmenes no contienen contrato exacto | **Fijar y registrar por familia/horizonte**. Preferir scores verificados idénticos; regenerar solo con protocolo expreso y nueva identidad de ejecución |
| Calibrador y umbral de EXP03/EXP03.1 M00 | Constituyen el **control** que EXP04 propone contrastar | **Reproducir y congelar como brazo A0**; no confundir con nueva calibración candidata |

**Inventario obligatorio antes de implementar EXP04:** Codex debe obtener del sistema de registro autorizado una ficha `BASELINE_MANIFEST` con `base_id`, `source_experiment`, `source_variant=M00`, commit/versión, identificadores y hashes de artefactos, configuración de columnas (orden, transformaciones y fechas de conocimiento), H5/etiquetas, cohortes, municipio/horizonte/objetivo, particiones cronológicas, predicciones sin redondeo, parámetros predictor, calibrador, threshold y política de selección, métricas de referencia y denominadores. **Ninguno de esos detalles desconocidos se puede completar suponiendo su valor.** Si falta material crítico, declarar `BLOCKED_BASELINE`.

**Qué se reutiliza técnicamente de EXP03.1:** cuando se verifique compatibilidad, reutilizar contratos y utilidades de cohortes, OOF, claves emparejadas, métricas, estratificación, manifests y trazabilidad de ejecuciones; reutilizar **M00**, no incorporar sus features de M01/M02. Entregar un mapa de componentes `REUSE_UNCHANGED / ADAPT / NEW` con justificación, rutas, interfaces afectadas y evidencia de que no cambian los resultados del control. Evitar duplicación, reescritura innecesaria y modificaciones a bundles históricos.

**Regla reproducible de promoción de mejoras entre experimentos:**

1. **Propuesta:** declarar la variante candidata y qué cambió frente a la base anterior; conservar inmutable la comparación original.
2. **Evidencia:** contrastes emparejados, soporte, estabilidad temporal/territorial, sensibilidad, carga, calibración, incertidumbre y límites, todos con criterios predefinidos. Mejoras parciales o en métricas aisladas **no habilitan promoción automática**.
3. **Decisión:** revisión científica independiente y aprobación explícita del cambio de baseline según el gobierno del proyecto; registrar `PROMOTED`, `REJECTED` o `DEFERRED`, con razonamiento. `PROMOTED` **no** equivale por sí mismo a `champion_selected` ni a autorización de uso operacional.
4. **Versionado:** nueva `base_id` inmutable (p. ej., `SAT_BASE_vNext` como identificador ilustrativo, no versión existente), vínculo a `parent_base_id`, evidencia y lista de modificaciones. Preservar referencia anterior y comparabilidad.
5. **Inicio del siguiente experimento:** consumir únicamente la última base **aprobada**, y además conservar una referencia histórica cuando sea necesaria para evaluar mejoras acumuladas. No reescribir resultados previos con la nueva base.

**Estado actual para este diseño:** **M00 es referencia científica provisional de EXP04, no un champion acreditado**. Ninguno de EXP00–EXP03.1 justifica por los documentos proporcionados una promoción global inequívoca de modelo a despliegue. Los componentes útiles de EXP03 aportan la justificación científica para investigarlos, pero se conservan en EXP04 tal y como estén realmente definidos en M00. Si existe una decisión formal de promoción posterior no aportada en las fuentes, requiere identificarse y reconciliarse antes de congelar EXP04; no se presume.

**Después de EXP04:** si una política de calibración/umbral satisface los gates científicos, puede proponerse como **nueva base de decisión** para EXP05, manteniendo idéntico predictor M00. De aprobarse, se versionará como `predictor_base_id` + `calibration_policy_id` + `threshold_policy_id` + `baseline_version`; si no, EXP05 hereda la base anterior aprobada. Una mejora de Brier/ECE por sí sola no promueve la política para un sistema cuyo objetivo primario es onset con falsas alertas controladas.

## 4. Definiciones y unidades de comparación

1. **Onset**: inicio del episodio definido por el protocolo H5 congelado. No redefinir para facilitar el éxito de EXP04.
2. **T+1**: evaluar una sola tarea onset/exceso en la cohorte vigente `Y(T)=0`. No crear dos modelos redundantes.
3. **T+2**: onset es **objetivo primario**; exceso mensual es **control secundario emparejado**, con métricas separadas. No combinar denominadores ni interpretar una mejora de exceso como mejora de onset.
4. **Falsa alerta de onset**: alerta positiva de la política en una fila elegible sin onset en el horizonte; distinguir de alertas durante continuación y de no-exceso al reportar clases de error.
5. **Exposición**: municipio-año monitoreado = suma de meses elegibles y observables por municipio / 12. Documentar meses, municipios y cobertura; no usar 76 como denominador fijo si el soporte efectivo difiere.
6. **FA_rate** = falsas alertas de onset / exposición municipio-año. **Sensibilidad** = verdaderos inicios alertados / inicios evaluables. **Precisión** = verdaderos inicios alertados / alertas de onset emitidas. Unidades y ceros del denominador deben estar explícitos.
7. **B_primary = 1,0** falsa alerta de onset por municipio-año: presupuesto **de selección**, no garantía automática del resultado fuera de tiempo. Registrar también FAR de EXP00/V1 por separado cuando su definición sea reconstruible; nunca tratar FAR y FA_rate como sinónimos.
8. Las comparaciones se hacen sobre **identificadores de predicción emparejados**, manteniendo los mismos positivos, negativos y cobertura; si cambia la elegibilidad, mostrar contraste sobre la intersección y registrar exclusiones, sin adjudicarlo como efecto del calibrador.

## 5. Diseño cronológico y prevención de fuga

### 5.1 Orden temporal innegociable

Para cada corte de evaluación `E`:

`entrenamiento del predictor -> predicciones fuera de muestra para calibración -> ajuste de calibrador -> selección de umbral -> congelación -> evaluación de E`.

Cada paso utilizará únicamente observaciones y **etiquetas cuyo horizonte ya habría madurado antes de la fecha de decisión**. En T+2, la purga/embargo debe considerar el horizonte completo, no solo la fecha de emisión. Evitar que un mismo evento objetivo o información futura participe simultáneamente en ajuste y evaluación. Registrar `forecast_issue_date`, `target_date`, `label_available_date` (o supuesto explícito de madurez), `calibration_cutoff` y `evaluation_start`.

Usar predicciones OOF/rolling-origin **verdaderamente fuera de muestra** para ajustar calibradores; no calibrar con predicciones in-sample del propio predictor. Si se deben regenerar predicciones, congelar características y parámetros del predictor, y usar entrenamiento cronológico exclusivo; documentar ese hecho como **nueva ejecución**, no idéntico al bundle previo.

### 5.2 Cortes autorizables

- **Desarrollo exploratorio/selección interna:** cortes conocidos 2020, 2021 y 2022, solamente si el historial previo disponible permite un backtest honesto para cada uno. No asumir que un esquema expansivo o ventana de 36 meses cabe en todos.
- **Estrés retrospectivo:** 2024 se analiza **después de congelar** configuración, nunca se usa para elegir ventana, método, umbral o familia.
- **2025:** no hay resultado científico válido reportado; **no** inventar cobertura, no declarar backtest 2025 realizado ni usar predicciones de EXP00 como confirmación directamente comparable. Mantener `NOT_EVALUABLE` hasta que exista frontera de datos y autorización documentadas.
- Cualquier corte sin historial de calibración, etiquetas maduras o predictor válido es `NOT_EVALUABLE`; no reemplazarlo por otro año oportunista.

La validación interna debe ser **anidada y cronológica**: para elegir entre políticas se comparan decisiones obtenidas solo con cortes anteriores al bloque validado. Los cortes de 2020–2022 son retrospectivos y pueden compartir entrenamiento; **no** tratarlos como muestras anuales independientes. Cuando no haya suficientes bloques para selección y validación anidadas, detener la conclusión confirmatoria: emitir solo resultado descriptivo.

## 6. Matriz de intervenciones controladas

### Fase A — Ventana (un solo factor)

Con predictor, método de calibración y política de umbral idénticos a la referencia:

| Brazo | Ventana candidata | Condición |
|---|---|---|
| A0 | Referencia EXP03 reproducida | Comparador congelado |
| A1 | Móvil de 12 meses maduros | Si soporte suficiente |
| A2 | Móvil de 24 meses maduros | Si soporte suficiente |
| A3 | Móvil de 36 meses maduros | Si soporte suficiente |
| A4 | Expansiva desde primer bloque OOF elegible | Sin incorporar bloques futuros |

Las duraciones son **rejilla propuesta**, no tamaños validados. No completar meses faltantes con datos posteriores. Registrar tamaños de muestra, positivos, negativos y disponibilidad real por brazo.

### Fase B — Calibrador (un solo factor)

Mantener la **misma ventana elegida por protocolo interno**, el mismo predictor y el mismo selector de umbral:

| Brazo | Método | Condición |
|---|---|---|
| B0 | Método de referencia reconstruido | Control |
| B1 | Platt/sigmoid (regresión logística sobre score) | Regularización y ajuste predefinidos |
| B2 | Isotónica monótona | Requiere soporte positivo/negativo suficiente, regla de fallback predefinida |

Registrar calibrador identidad/no recalibración como control diagnóstico **solo si es matemáticamente pertinente al score base**; no comparar probabilidades no equivalentes. Si isotónica falla por soporte, declarar `NOT_EVALUABLE` para ese brazo/corte, sin sustituirlo después de ver el resultado. Evitar que el ajuste de hiperparámetros del calibrador utilice E o 2024.

### Fase C — Política de umbral (un solo factor)

Mantener fijos predictor, ventana y calibrador:

| Brazo | Regla |
|---|---|
| C0 | Selector vigente de EXP03, reconstruido exactamente |
| C1 | Seleccionar el umbral con **máxima sensibilidad interna** entre candidatos cuya FA_rate de selección sea <= 1,0; desempate determinista y documentado |
| C2 | Entre umbrales elegibles, exigir adicionalmente que el **máximo FA_rate entre bloques cronológicos de selección** sea <= 1,0; después maximizar sensibilidad conjunta |

C2 requiere >=2 bloques internos con soporte; de lo contrario `NOT_EVALUABLE`. El umbral se selecciona **solo** sobre el bloque de selección disponible, y permanece fijo durante todo E. Establecer en el protocolo el sentido del comparador (`score >= threshold`), la rejilla completa de umbrales (incluidos extremos), empates y casos sin umbral viable. Una política que no emite alertas puede ser factible para la carga, pero **no gana** si pierde sensibilidad más allá del margen.

**Fase D — Composición restringida:** una vez fijadas las elecciones mediante evaluación anidada solo de desarrollo, comparar la **única combinación preseleccionada** A+B+C con A0/B0/C0. No buscar todas las combinaciones ni seleccionar retrospectivamente usando 2024. Si no existe capacidad de selección interna independiente, omitir D confirmatoria y reportar únicamente efectos de factores aislados.

**Dimensiones:** familia × horizonte × corte × brazo. El control de exceso T+2 se informa aparte; las celdas no se multiplican para simular observaciones independientes.

## 7. Regla primaria de éxito, no inferioridad e interpretación

**Propuesta para congelar antes de la ejecución** (no inferida de las fuentes):

- **Carga operativa:** `FA_rate_E <= 1,0` en cada **año evaluable** del conjunto de evaluación principal. Reportar también exceso positivo `max(0, FA_rate_E - 1)` y dispersión entre años. Si la referencia ya cumple en un año, la candidata no puede aumentar materialmente esa tasa.
- **Preservación de sensibilidad:** diferencia pareada de sensibilidad `S_cand - S_ref >= -0,02` (margen propuesto: **−2 puntos porcentuales**) por horizonte, en agregado de cortes evaluables, con inspección de pérdidas por año. Si no se acepta este margen antes de ejecutar, **no usarlo para declarar éxito** y mantener el resultado sin clasificación confirmatoria.
- **Mejora respecto a referencia:** exigir reducción estricta del exceso agregado de FA_rate frente a A0 y **sin pérdida de detección material**; un método que solo reduce alertas apagando el sistema no cumple H1.
- **Estabilidad temporal:** no permitir que un promedio favorable oculte años con carga por encima del presupuesto. Si un año no cumple, clasificar `NO_RESPALDADA` para el criterio fuerte, aunque informar el progreso descriptivo.
- **Territorio:** presentar Meta y Tolima y, si hay membresía previa verificada, perfiles históricos. No seleccionar por promedio si existe deterioro territorial material; el margen territorial debe congelarse por comité/protocolo antes de declarar éxito. A falta de margen aceptado, informar `PARCIAL / SIN APROBACIÓN`, nunca presuponer que la heterogeneidad es inocua.
- **Incertidumbre:** preferir diferencias pareadas con intervalos de confianza por remuestreo en bloques municipio y tiempo (respetando dependencias). Definir nivel (propuesto 95 %), unidad de bloque, número de réplicas y semillas **antes** de ejecutar. Si el soporte no permite inferencia defendible, publicar `UNAVAILABLE` y restringir conclusiones a descriptivas; no usar valores p de filas independientes.

**Clasificaciones de H1:** `RESPALDADA` solo si se cumplen todos los criterios precongelados, controles temporales y soporte; `PARCIALMENTE_RESPALDADA` para mejoras descriptivas sin soporte suficiente/guardrails; `NO_RESPALDADA` para incumplimiento de sensibilidad o carga; `NO_EVALUABLE` si faltan artefactos, madurez, cohortes pareadas o cortes suficientes. Ninguna clasificación implica automáticamente G5 aprobado.

**Advertencia técnica:** un recalibrador estrictamente monótono preserva el orden de las puntuaciones; si el selector examina todos los umbrales y no hay diferencias de empates, **puede producir exactamente la misma frontera sensibilidad–falsas alertas** sobre los mismos datos. En ese caso una mejora de Brier/ECE **no prueba** mejora de detección bajo presupuesto. EXP04 debe separar explícitamente calibración probabilística, selección de umbral y estabilidad de transporte, sin atribuir un efecto de umbral a un cambio de ranking inexistente.

## 8. Indicadores y reportes obligatorios

**Por familia × horizonte × año × política y también en comparaciones pareadas:**

- Soporte: municipios, meses, exposición municipio-año, positivos onset, negativos, exclusiones y abstenciones.
- Detección: TP, FN, sensibilidad por año, sensibilidad macro municipal y global (sin mezclarlas).
- Carga: FP de onset, alertas totales, FA_rate, exceso sobre presupuesto, FAR/FPR si se pueden reconstruir bajo definición explícita, precisión y falsas alertas por clase (continuación/no-exceso).
- Probabilidades: Brier, ECE con bins predefinidos, curva de confiabilidad, AP y distribución de puntuaciones/prevalencia. **AP no sustituye calibración.**
- Transporte: umbral elegido antes de cada E, deriva de FA_rate entre selección/E, diferencias de sensibilidad y dispersión entre años.
- Territorio: Meta, Tolima, municipios con soporte; perfiles solo con membresía histórica válida (si no, `NOT_EVALUABLE`).
- T+2: repetir controles de exceso en tabla **separada**; nunca sumar onset y exceso ni compartir el presupuesto de onset.
- Diferencias: resultados pareados de cada brazo contra su control y de composición final vs referencia, con intervalos o razón explícita de imposibilidad.

Visualizaciones propuestas: frontera detección–carga en **mismo soporte**, tasas por año y departamento, reliability plots, distribuciones de probabilidades y umbrales por corte. Incluir también el desempeño de umbral fijo sin recalibrar para comprobar cuánto aporta actualizar la política.

## 9. Reglas de implementación para Codex

1. **Reconocimiento en solo lectura previo:** localizar en repo el contrato científico de EXP03/EXP03.1, artefactos de M00, definiciones de cohortes, soporte de OOF, procedencia y política de umbral; registrar diferencias respecto a este documento. **No reinterpretar** convenciones desconocidas sin una decisión científica explícita.
2. Congelar un protocolo versionado antes de ejecutar: hipótesis, prioridades primarias/secundarias, márgenes, matriz factible, cortes, fechas de madurez, seed, política de fallback y multiplicidad. No ampliar rejilla al ver resultados.
3. Reutilizar componentes existentes para generar **scores base idénticos** en pares de comparación; elaborar `BASELINE_MANIFEST` y mapa `REUSE_UNCHANGED / ADAPT / NEW` de EXP03.1 antes de agregar componentes. SOLID/DRY y configuración centralizada para periodos, ventanas y presupuestos.
4. Mantener separados `fit_predictor`, `predict_out_of_fold`, `fit_calibrator`, `select_threshold`, `evaluate_frozen`, `report_strata`, sin mezclar conjuntos temporales.
5. Implementar verificaciones de **no fuga temporal**, unicidad de clave municipio–mes–horizonte–objetivo, soporte pareado, equivalencia de etiquetas, reconstrucción del umbral y conservación de precisión numérica.
6. Preservar predicciones y probabilidades completas (no redondear antes de reproducir alertas); registrar corte de entrenamiento, calibración, umbral y evaluación por fila de resultado.
7. Registrar experimentos/artefactos con nombres y versiones distinguibles sin sobrescribir EXP00–EXP03.1. No ejecutar ni escribir MLflow, tocar datos privados, aprobar gates o iniciar despliegue **como consecuencia de la sola creación de este diseño**.
8. Implementar un modo `dry-run`/validación de precondiciones que reporte qué cortes y brazos son evaluables sin entrenamiento ni modificar evidencias existentes.
9. Separar **evidencia observada** de interpretación e hipótesis en el informe final. Si hay falta de soporte, mostrar `BLOCKED`/`NOT_EVALUABLE`, no resultados sintéticos ni métricas prestadas.

### Entregables de la implementación futura

- Protocolo congelado, matriz factible y manifiesto de cortes/fechas/soporte.
- Especificación y trazabilidad de la referencia reproducida, `BASELINE_MANIFEST`, mapa de reutilización EXP03.1 y registro de decisiones de evolución/promoción de base.
- Predicciones y resultados pareados, umbrales congelados y metadatos de calibradores.
- Tablas de métricas primarias, controles, estratos, cobertura e incertidumbre.
- Informe `CONCLUSIONS.md` con H1/H1a/H1b/H1c, límites, decisiones y estado G5; evidencias de reproducibilidad.
- Inventario de bloqueos que impiden afirmar evaluación prospectiva u operativa.

## 10. Gates y decisiones posteriores

**G0 — Diseño congelado:** aceptados presupuesto, margen de no inferioridad, criterio territorial, cortes y reglas de selección; si no, `BLOCKED_DESIGN`.

**G1 — Integridad de referencia:** M00 reproducible con manifiesto versionado, mismas etiquetas/cohortes, scores íntegros y control sin cambios; de lo contrario `BLOCKED_BASELINE`. Prohibido promover o sustituir la base implícitamente.

**G2 — Causalidad temporal:** OOF y madurez documentadas; sin fuga de E a calibración o selección; si no, `BLOCKED_TEMPORAL`.

**G3 — Evaluabilidad:** soporte positivo/negativo, ventanas factibles, cortes múltiples y controles pareados; declarar explícitamente brazos `NOT_EVALUABLE`.

**G4 — Evidencia científica:** métricas conjuntas, intervalos apropiados o limitación explícita, estratos y estrés 2024 solo después de congelación.

**G5 — Decisión:** por defecto **`NOT_APPROVED` / `champion: not_selected`** hasta revisión científica independiente. Un resultado favorable de EXP04 solamente habilita consideración de validación futura, no despliegue o equivalencia clínica/epidemiológica.

## 11. Riesgos y decisiones abiertas que deben resolverse antes de ejecutar

1. **Disponibilidad de scores OOF anteriores y etiqueta madura:** los archivos fuente no acreditan que exista historia suficiente para ventanas de 12/24/36 meses en todos los cortes.
2. **Reproducibilidad de M00 y del umbral:** no se suministraron aquí sus contratos/bundles operativos; Codex debe verificar antes de comparar.
3. **Margen de −2 pp, umbral territorial y reglas de incertidumbre:** propuestas para aprobación, no inferencias respaldadas por los análisis históricos.
4. **Cortes insuficientes para confirmación:** tres años solapados de desarrollo y 2024 previamente conocido pueden permitir comparación descriptiva, pero no una demostración independiente de generalización. Evaluación nueva requerirá un periodo realmente no utilizado, maduro y autorizado.
5. **Disponibilidad real de información T:** los resultados basados en T consolidado no prueban anticipación efectiva en operación; diferir la validación de notificación a EXP06.
6. **Calibración vs clasificación:** una mejora en Brier/ECE sin mejora conjunta de carga y detección no satisface la hipótesis primaria.
7. **Riesgo de multiplicidad:** varias ventanas, calibradores, familias y horizontes pueden producir falsos ganadores; anidar selección y congelar política antes del estrés.

## 12. Fuentes autorizadas de este diseño

- `SAT_DENGUE_V3_Investigacion_y_Propuestas_de_Mejora.pdf`: diagnóstico, priorización de EXP04, indicadores y restricciones metodológicas (pp. 2–6).
- `analisis-1.md`: EXP00/EXP01, equivalencia T+1, discrepancias de calibración y necesidad de presupuestos.
- `analisis-2.md`: EXP02, sensibilidad de etiquetas, necesidad de H5 estable y evaluación de mismo evento.
- `analisis-3.md`: EXP03, señal en variables, falta de transporte temporal y heterogeneidad.
- `experimentos_actualizado.md`: objetivo y matriz original de EXP04, secuencia EXP04→EXP05 y criterios acumulados.

**Regla de autoridad:** este archivo especifica **el experimento propuesto**; sus parámetros nuevos necesitan aprobación y congelación antes de la ejecución. No sustituye el protocolo científico vigente, los contratos reales del repositorio ni la evidencia empírica aún no producida.
