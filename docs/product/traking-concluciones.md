# Current scientific decision status — 2026-10-21

This is the active scientific decision register. The current summary below and the latest explicit decisions govern; dated snapshots and preserved source records that follow are historical, including superseded "pending" statements. [The master plan](../roadmap/master-plan.md) alone owns stage progress. This reconciliation records implemented facts without changing scientific rules or granting a freeze.

| Topic | Current rule / evidence / remaining limit |
|---|---|
| Population and geography | Residence in the 76 Tolima/Meta municipalities; symptom onset; supplied 2013 dates/records unchanged; all supplied notification classifications; no unsupported duplicate deletion (DEC-113/114/118). Unassignable records remain reconciled outside invented municipality-month keys. |
| Epidemiological streams | General dengue defines the initial Y and `zona_canal_t`; severe dengue is a separate count/predictor. Combined-stream Y is a later experiment, not the current target. |
| Covered no-case months | Count zero is valid within approved coverage (DEC-120). Missing climate, out-of-coverage months and insufficient history are not converted to zero. |
| Historical channel and future Y | DEC-122 supersedes whole-year closure wording: five same-month observations from the five years before the target year, with required historical months. November 2024 → January 2025 can include January 2024. Strict count > P75 defines excess; missing required history/result stays non-evaluable. Y T+1/T+2 are outcomes, never predictors. |
| Numerical and four-zone implementation | Notebook 03 and its local construction contract implement type-7 linear percentiles, evaluability and EXITO/SEGURIDAD/ALERTA/EXCESO at T with explicit tie rules. These are implemented candidate rules, not still absent specifications; the owning contract retains exact boundaries. |
| Field definitions | [The canonical 69-field matrix](stage-2/DATA-01-Priority%20Field%20Matrix.md) is ACTIVE following Mauricio's restoration. Six insufficient operational definitions remain explicit; this does not mean 59 fields are undefined or that all 69 are model inputs. The archive copy is a pointer. |
| Current outputs and analysis | Notebook 03 supplies the individual consolidated CSV, monthly climate panel, Y/current channel and bounded EDA. Only the older experimental notebooks 01/02 and their reports are retired. Candidate status does not negate their completed implementation or approve predictive utility. |
| January 2020 | Incorporated for the reviewed 76 municipalities: 2,356 municipality-days, nine climate variables. Historical claims of that scoped gap are superseded; no national completeness claim. |
| Preparation | [Notebook 04 and its modules](stage-3/README.md) add 16 deterministic candidates, preserve scientific inputs, separate X/Y, select eight temporal windows and fit reusable preparers on training only. The preparation contract owns exact roles and boundaries; subsequent Stage 4/5 training evidence is recorded separately. |
| Evaluation support | Preparation uses target eligibility 2012-01..2024-12, excludes reserved targets from 2025-01 and requires validation origins >= fit cutoff. Later validation origins represent successive predictions. These are implemented controls, not evidence of real-time data availability. |
| Remaining evidence | Historical as-of availability is unproven. The earlier 5/7/9-year sensitivity has no completed evidence recorded here; its freeze disposition needs an explicit human decision. Provenance reconstruction limits remain in the dated records below. Do not invent completion or restart retired EDA by default. |
| Gate decisions | Mauricio approved G2 and G3 on 2026-10-21 using the existing notebook 03/04 evidence and retaining the documented limitations (DEC-135). Mauricio accepted G4 and exact proposal/protocol `66d7208066476b027721182d185770d2522dfe5d891caf4b3b2759177dcc5e09` and authorized the frozen 2025 evaluation (DEC-132). Mauricio subsequently accepted G5 `NOT_APPROVED`; Stage 5 is closed and no champion is selected (DEC-134). |

---

# Historical snapshot — experimental EDA retirement on 2026-10-19

Mauricio explicitly retired **all experimental EDA** after using it to approach and refine the data. This file remains the single active **Stage 2 scientific decision register**. The [master plan](../roadmap/master-plan.md), governance and Stage 1 requirements keep their separate responsibilities. This section takes precedence over the historical entries below, including earlier references to pending January data or mandatory reruns of retired notebooks.

| Topic | Current status and limit |
|---|---|
| Experimental EDA | DEPRECATED: both exploratory notebooks, all eight Stage 2 experimental reports, PLAN_005 derivatives and subsequent experimental panel/association analyses are archived. See the [historical archive](../archive/experimental-eda/README.md) and its [path/hash manifest](../archive/experimental-eda/manifest.json). Archived outputs are not current feature selection, target validation or predictive evidence. |
| Approved decisions | Preserved: residence in Tolima/Meta and symptom onset; unchanged supplied 2013 dates/records (DEC-113); separate epidemiological streams and no unsupported duplicate deletion (DEC-114); all supplied notification classifications (DEC-118); approved initial Y and horizons (DEC-119/121); covered no-case months counted as zero (DEC-120). Retirement does not revoke an approved decision or approve an experimental choice. |
| January 2020 climate | Existing local recovery/incorporation evidence records 2,356 municipality-days = 76 municipalities × 31 days, with nine climate variables in the Tolima/Meta scope. The incorporated `google_earth_engine.csv`, epidemiological sources and backups are unchanged by this cleanup. This is not a claim of national completeness. The old January-gap statements below are historical and superseded for that scope. |
| Provenance limitations | Original manifest reconstruction was limited; the historical reconciliation records `prior_equals_baseline = false` and `all_passed = false`. The archive does not repair or conceal that mismatch or overwritten backup-metadata history. Source hashes and recovery evidence remain locally inspectable in `data/interim/stage2_manifest_traceability/` and `data/interim/stage2_january_2020_incorporation/`. |
| Field definitions | The former field matrix and source-provenance report are historical references in the archive; they do not constitute a newly approved or frozen Data Contract. |
| Candidate chapter-1 datasets | Constructed as bounded Stage 2 candidate artifacts with explicit contract and execution manifest (`data/interim/stage2_consolidated_dataset_pipeline/`). These outputs are for downstream analysis and reconciliation only; they do not assert final training suitability, target definition closure or Stage 2 gate closure. |
| Next analytical work | Do not rerun or maintain retired studies solely to refresh their outputs. Define any future EDA as a new bounded task using the refined sources and current approved decisions. Numerical target/evaluability specifications, future approved sensitivity work and monthly aggregation rules still need their own evidence; this cleanup supplies none. |
| Stage gate | Stage 2/G2 remain OPEN. No Data/Target Freeze, model training or stage closure is asserted. |

The earlier reconciliation and full decision history are retained below, with links relocated to archived evidence. Historical counts, dates, states, dictionaries and "pending" wording describe their original review, not the current work queue. Decision IDs remain stable and are not reused.

---

# Historical snapshot — reconciliation on 2026-10-18

This current-status section takes precedence over superseded open questions in the preserved historical sections below. The complete local register and complete PR #9 document are retained verbatim for traceability; earlier pending statements are not silently converted into current requirements.

| Topic | Current authority and status |
|---|---|
| Baseline records | All supplied notification classifications included; streams separate; no unsupported duplicate deletion (DEC-114/118). Unassignable geography/onset retained in reconciliation. |
| 2013 | Keep original records/dates unchanged for the baseline (DEC-113). |
| Baseline no-case months | Within supplied coverage, no case records means aggregate count zero under the approved dataset assumption (DEC-120). Such zeros are valid P75 observations. Climate gaps and outside-coverage history are distinct. |
| Coverage-backed eligibility baseline | Source notification-year metadata supports a conservative model-eligibility interval but does not by itself certify full symptom-onset surveillance completeness at temporal edges. Boundary symptom periods remain preserved for lineage and diagnostics; unsupported edge periods can be excluded from model eligibility without deleting source rows or redefining existing Y/P75 fields. |
| Current endemic-channel at reference month T | Candidate feature convention for Stage 2 closeout: compute `p25_canal_t`, `p50_canal_t`, `p75_canal_t` from the same calendar month in the five prior years per municipality (type-7 percentiles), then classify `zona_canal_t` as EXITO/SEGURIDAD/ALERTA/EXCESO with explicit tie rules. Missing current count or insufficient history yields null thresholds and null zone; this does not redefine future `y_t1`/`y_t2`. |
| Category profiling scope | Chapter-5 category/cardinality profiling is partial evidence from the first 150,000 rows of `dengue.csv` (general dengue stream). It is not severe-dengue representative and does not claim exhaustive production profiling of all 69 source columns. |
| Correlation adjustment interpretation | Month-adjusted correlation diagnostics are computed with global calendar-month mean centering for descriptive context only; they are not causal proof and do not by themselves authorize automatic predictor exclusion. |
| Initial Y | Approved: municipality-month, median/percentile channel, strict count > P75; five same-month historical observations from the five years prior to target year, available under retrospective consolidated data constraints; epidemic years included; horizons T+1/T+2 (PR #9 and DEC-119/121/122). |
| Onset/continuation | For T+1 compare T with T+1; for T+2 compare T+1 with T+2. Future states are evaluation outcomes, never predictors at T (approved PR #9 configuration). |
| Evidence not yet earned | Exact numerical percentile convention, evaluability of genuinely unavailable history and consistent consecutive-state references need implementation specifications; 5/7/9-year target sensitivity has not run. |
| Deferred operation | User-requested forecast re-execution belongs to product behavior, not a Stage 2 closing condition. Historical availability remains a limitation of the consolidated retrospective data, not a demand to reconstruct unavailable snapshots before this bounded closure. |
| Stage gate | Stage 2/G2 remain OPEN. No model training, target validation or freeze is asserted by documentation reconciliation. |

See the [reconciliation and recovery report](../operations/stage2-pr-reconciliation.md). The sections that follow preserve each source document; their original dates and states are historical evidence. The latest explicit human decisions above govern current preparation.

---

# SAT-Dengue V2 Registro de decisiones de datos y modelo

Archivo: `traking-concluciones.md`. Auditoría y actualización: **2026-10-17**, America/Bogota. Rama activa: **Stage2/Data-Understanding**. Referencia de Git inspeccionada: `1d7450ca9a15d376f404af13ff472a6d39bcde04`.

## Alcance de esta revisión

Este registro contiene exclusivamente decisiones y asuntos pendientes directamente relacionados con **análisis, interpretación y tratamiento de datos, construcción de variables y Y, diseño, entrenamiento, calibración y evaluación del modelo**. Se excluyen marcos de metodología de gestión, planificación por etapas, gobierno de agentes, interfaz, API, despliegue e infraestructura. Se conserva la validación estadística y temporal porque afecta directamente el desarrollo del modelo; no se confunde con una metodología de gestión del proyecto.

La auditoría revisó el texto extraíble de las **seis fuentes del proyecto**, hizo inventario y cribado de **77 documentos narrativos locales** (29 en `docs/`, 44 registros y planes locales en `.dwp/`, dos entradas raíz y dos documentos de revisión/plantilla), revisó el código y resultados guardados del cuaderno de **17 celdas**, e inventarió siete archivos de referencia en `data/sources/`. Entre los 77 se incluye la versión previa de este registro, utilizada solo para conservar su historia, no como corroboración independiente. Los catálogos y archivos anuales son datos, no documentos narrativos: se consultaron sus metadatos y evidencia agregada ya existente, sin un nuevo perfilado de pacientes. Las dependencias y manuales de herramientas de `.agents/`, entornos virtuales y cachés no se consideran decisiones científicas del proyecto.

Es una **auditoría documental**, no una nueva ejecución del análisis, revisión del código remoto de V1 ni comprobación independiente de sus resultados publicados. La bibliografía citada en los documentos se conserva como contexto, no se convierte automáticamente en decisiones adoptadas. No se modificaron fuentes sincronizadas, datos, cuaderno, diccionario ni otros documentos.

Resultado del alcance: **46 entradas anteriores conservadas y 38 incorporadas = 84 entradas científicas**, de las cuales 29 aceptadas, 16 abiertas, 13 propuestas, 12 históricas no adoptadas, 10 aplicadas en diagnóstico, tres reemplazadas y una documentada en fuente. Los estados no equivalen entre sí.

El [diccionario canónico](stage-2/DATA-01-Priority%20Field%20Matrix.md) conserva la única definición de campos. El [registro de procedencia](../archive/experimental-eda/stage-2/DATA-01-Source%20Provenance.md) identifica insumos; el [informe de reconocimiento](../archive/experimental-eda/stage-2/DATA-01-Initial%20Recognition%20Report.md) y la [investigación de 2013](../archive/experimental-eda/stage-2/DATA-01-2013-date-inconsistency-investigation.md) documentan resultados. Este archivo registra decisiones y sus límites; no duplica el diccionario ni convierte observaciones en aprobaciones.

## Consecutivos, estados y fechas

Los códigos DEC existentes conservan su identidad. Por reducción explícita del alcance se retiraron del registro vigente 18 entradas ajenas a datos/modelo o redundantes con la conservación de fuentes. Sus códigos quedan **reservados y no se reutilizan**: DEC-001, DEC-003, DEC-004, DEC-005, DEC-006, DEC-007, DEC-008, DEC-011, DEC-049, DEC-052, DEC-053, DEC-054, DEC-055, DEC-056, DEC-057, DEC-058, DEC-063, DEC-064. Esta salida por alcance no es deprecación de una decisión científica. Su contenido anterior se preserva en el historial de la conversación; no se crea otro documento competidor. Los nuevos códigos llegan hasta DEC-107 y continúan la numeración anterior; los huecos en el índice son intencionales.

- **ACEPTADA:** existe instrucción explícita o acuerdo/documento vigente que la respalda, limitado a su alcance. No implica implementación completa ni evidencia predictiva favorable.
- **PROPUESTA:** recomendación del usuario, experto, propuesta de grado o asistente sin adopción final documentada. Proponer escenarios no selecciona uno como política de limpieza.
- **ABIERTA:** decisión o evidencia aún por resolver; no se inventa una regla para completarla.
- **REEMPLAZADA:** convención o interpretación anterior sustituida, con motivo y código sucesor. Se declara cuando era una interpretación del asistente y no una política aprobada.
- **HISTÓRICA_NO_ADOPTADA:** antecedente o sugerencia de V1/fuentes no adoptada automáticamente en V2; no se finge una aprobación o revocación de V2.
- **APLICADA_EN_DIAGNÓSTICO:** opción identificada en el cuaderno o diagnóstico guardado. Acredita uso acotado, **no aprobación de producción** ni autorización para extenderla a todo el tratamiento.
- **DOCUMENTADA_EN_FUENTE:** atribución o especificación que consta en la fuente, sin confirmar el procedimiento que generó los datos locales.

Por autorización del usuario, las incorporaciones se registran con fecha **2026-10-17**. Esa fecha identifica la auditoría documental; no se presenta como aprobación histórica. Las fechas anteriores se conservan; DESCONOCIDA o No aplica evita inventar fechas. **Revisada el** es siempre la fecha de esta auditoría. La fecha de deprecación solo se completa si hay evidencia; una entrada histórica nunca adoptada no necesita una falsa fecha de retiro. La actualización documental no modifica el corte analítico 2026-10-15 del cuaderno existente.

Para cambiar una decisión: conservar el código y evidencia, registrar el evento y autoridad; si hay reemplazo, agregar sucesora, fecha y justificación y actualizar referencias recíprocas. Nunca reutilizar códigos, borrar incertidumbre, crear ciclos de reemplazo o aprobar propuestas por silencio. Un cambio de datos o Y debe indicar qué conteos, variables, particiones y resultados requieren regeneración.

## Fuentes examinadas

### Fuentes completas del proyecto

| Archivo | Tratamiento en la auditoría | SHA-256 de la copia revisada |
|---|---|---|
| `AI-DEVELOPER-FIRST-FRAMEWORK.md` | Excluida: marco de gestión de otro producto; no contiene decisiones adoptadas de datos/modelo de SAT-Dengue. | `cccf970fed3c25bfdf72c3b135ef9ab187909f71f9923a5e310867800769955a` |
| `Avance entrega 3 microproyecto.pdf` | Excluida como autoridad de dengue: trata PulmoIA e imágenes; no se transfieren sus decisiones de modelos ni entrenamiento. | `83ca481185db394decd7650e38b89415a97e63b3874321cee4f5716267281001` |
| `Formato-propuesta_Proyecto-de-grado-Mauricio.pdf` | Fuente científica principal: objetivos, fuentes, panel, modelos, validación y métricas; distinguir propuesta y aprobación. | `2d9ca5c0786858e7f5dd50dacd1db20dbd5027c2eba077792651f39028f045ce` |
| `Reporte_Entrega3_final-2.docx` | Antecedente V1: preparación, variables, particiones, calibración y limitaciones; no validación del modelo V2. | `fe06c42fa21bcac7a76590cfee76b2176fdc7892478f0a080644c64644fb7d49` |
| `Sesion_1_con_Experto_Notas.docx` | Recomendaciones y acuerdo conceptual del experto; notas consolidadas, no transcripción literal. | `8b5f899930c0ed94e8adc970f9bf790ea95ec191ff28257a91100debf6b84c72` |
| `prueba-dashboard.md` | Solo evidencia de entradas y probabilidades del modelo V1; las pruebas visuales no validan inferencia ni exactitud predictiva. | `11b5df5fbace62efe601b1d4d14f171e4ee48f9e2c7b2ff4a8a22d2b0ee93d9e` |

Códigos de las fuentes privadas: **SRC-E** = notas del experto; **SRC-R** = reporte de Entrega 3; **SRC-P** = propuesta de grado. Se mantienen nombre, sección/página y huella; no se copian los documentos al repositorio.

### Documentos y evidencia locales

| Código | Fuente / ubicación | Uso y límite |
|---|---|---|
| PRODUCT | [Definición del producto](product-definition.md) | Solo objetivo, horizontes, familias de modelos y referencias predictivas. |
| NOTE | [Nota de decisiones y fuentes](../archive/experimental-eda/stage-2/nota-metodologica.md) | Solo contenidos de datos/modelo y alternativas; no se registran marcos de gestión. |
| MATRIX | [Diccionario de campos](stage-2/DATA-01-Priority%20Field%20Matrix.md) | Significados, códigos, fechas, prioridades y limitaciones del export. |
| RECOG | [Reconocimiento y cobertura](../archive/experimental-eda/stage-2/DATA-01-Initial%20Recognition%20Report.md) | Resultados agregados guardados; algunas secciones de próximos pasos están desactualizadas. |
| PROV | [Registro de procedencia](../archive/experimental-eda/stage-2/DATA-01-Source%20Provenance.md) | Identidad y límites de fuentes, versiones y ventanas. |
| INVEST | [Investigación de 2013](../archive/experimental-eda/stage-2/DATA-01-2013-date-inconsistency-investigation.md) | Comparación anual y escenarios diagnósticos ejecutados; no corrección aprobada. |
| DATA | [Política de datos](../data/data-policy.md) | Solo preservación de insumos y tratamiento restringido de registros individuales; no infraestructura. |
| PROD4 / PROD5 / PROD6 | [Cobertura](stage-1/PROD-04-dashboard-master-user-story.md), [validación de insumos](stage-1/PROD-05-new-period-flow.md), [semántica analítica](stage-1/PROD-06-ui-information.md) | Solo cláusulas de cobertura, calidad, datos o explicabilidad; excluir diseño de interfaz y operación del producto. |
| ML | [Estándares científicos del modelo](../standards/ml-scientific-standards.md) | Validación temporal, prevención de fuga y evidencia comparable. |
| PROD1 / PROD7 / PROD8 | [Pregunta científica](stage-1/PROD-01-business-question.md), [semántica de predicción](stage-1/PROD-07-draft-prediction-contract.md), [variables de entrada](stage-1/PROD-08-draft-input-contract.md) | Extraer solo población, horizonte, disponibilidad y variables; ignorar interfaz/API. |
| Cuaderno | [01_stage2_residence_onset_eda.ipynb](../archive/experimental-eda/notebooks/01_stage2_residence_onset_eda.ipynb) | Código, parámetros y resultados guardados; celdas numeradas desde 0 para localizar evidencia. No reejecutado en esta auditoría. |
| PLAN003 | `.dwp/plans/PLAN_003_validate_divipola_municipal_coverage/` | Solo tareas 1–3 y evidencia de catálogo, cobertura y continuidad; no decisiones de gestión del plan. |
| PLAN004 / CONCLUSIONES004 | `.dwp/plans/PLAN_004_dengue_date_inconsistency_investigation/`, tareas 1–5 y `analysis_results/CONCLUSIONS.md` | Comparabilidad, llaves, fechas y escenarios; sus archivos locales ignorados pueden no existir en un checkout limpio. |
| Datos de referencia | `data/sources/` | Tres fuentes anuales 2012/2013/2014, dos catálogos DIVIPOLA, `Listados_DIVIPOLA.xlsx` y `divipola-provenance.json`; no nuevas muestras de pacientes. |
| Artefactos agregados | `data/interim/stage2_dengue_date_investigation/` y `data/interim/stage2_divipola_validation/` | Metadatos, llaves, correspondencias, fechas, escenarios y controles guardados; no se recalcularon en esta tarea. |

El cribado también incluyó los demás documentos locales (índices, seguridad, producto, contratos, operaciones y planes): se extrajeron solo cláusulas con efecto directo sobre datos o modelo; el resto se excluyó. El registro anterior no se usa como fuente independiente de aprobación. Para las entradas retenidas que citan PROD4/PROD5/PROD6/DATA, esas referencias identifican únicamente la cláusula científica o de insumos ya documentada, no incorporan decisiones ajenas al alcance.

### Acuerdos de esta conversación

| Código | Evidencia de 2026-10-17 | Límite |
|---|---|---|
| CHAT-01 | Auditoría de las 69 columnas reales. | No aprobación de limpieza. |
| CHAT-02 | Solicitud de un único diccionario completo como fuente de verdad. | No cierre de definiciones operativas insuficientes. |
| CHAT-03 | Propuesta mensual y tolerancia de siete días; análisis con consulta como corroboración. | Recomendaciones y cálculos exploratorios no incorporados al cuaderno. |
| CHAT-04 | Propuesta de correlación mensual y escenarios 1–3. | No escenario elegido ni estudio nuevo ejecutado. |
| CHAT-05 | Identificación de Y ya acordada por el grupo y revisión de las fuentes. | Concepto respaldado; parametrización definitiva pendiente. |
| AUD-2026-10-17 | Solicitud actual de auditoría de fuentes y documentos, limitada a datos y modelo. | Autoriza esta actualización; no aprueba automáticamente las alternativas encontradas. |

## Índice de decisiones de datos y modelo

| Código | Decisión | Estado | Reemplazada por |
|---|---|---|---|
| [DEC-002](#dec-002) | Validar modelos y resultados de V2 sin transferir evidencia de V1 | ACEPTADA | No aplica |
| [DEC-009](#dec-009) | Planteamiento nacional y piloto municipal de V1 | HISTÓRICA_NO_ADOPTADA | DEC-010 |
| [DEC-010](#dec-010) | Definir el dominio analítico en municipios de Tolima y Meta | ACEPTADA | No aplica |
| [DEC-012](#dec-012) | Usar granularidad municipal y de año-mes calendario | ACEPTADA | No aplica |
| [DEC-013](#dec-013) | Producir pronósticos distintos para T+1 y T+2 | ACEPTADA | No aplica |
| [DEC-014](#dec-014) | Respetar la cronología y la disponibilidad de información | ACEPTADA | No aplica |
| [DEC-015](#dec-015) | Agrupar por ocurrencia en el reconocimiento inicial | REEMPLAZADA | DEC-016 |
| [DEC-016](#dec-016) | Atribuir los casos por residencia | ACEPTADA | No aplica |
| [DEC-017](#dec-017) | Usar el inicio de síntomas como fecha epidemiológica | ACEPTADA | No aplica |
| [DEC-018](#dec-018) | No reemplazar silenciosamente un inicio ausente o inconsistente | ACEPTADA | No aplica |
| [DEC-019](#dec-019) | Conservar los archivos originales y señalar anomalías | ACEPTADA | No aplica |
| [DEC-020](#dec-020) | Identificar municipios con códigos validados | ACEPTADA | No aplica |
| [DEC-021](#dec-021) | Definir la inclusión de casos y la identidad de episodios | ABIERTA | No aplica |
| [DEC-022](#dec-022) | Mantener separados 210 y 220 durante el análisis exploratorio actual | ACEPTADA | No aplica |
| [DEC-023](#dec-023) | Serie principal de dengue y serie auxiliar de dengue grave en V1 | HISTÓRICA_NO_ADOPTADA | DEC-021, DEC-022 |
| [DEC-024](#dec-024) | Elegir el entrenamiento compartido, departamental o municipal | ABIERTA | No aplica |
| [DEC-025](#dec-025) | Comparar el ajuste compartido con el departamental | PROPUESTA | No aplica |
| [DEC-026](#dec-026) | Comparar las familias de modelos candidatas | ACEPTADA | No aplica |
| [DEC-027](#dec-027) | Usar modelos de referencia epidemiológicos | ACEPTADA | No aplica |
| [DEC-028](#dec-028) | Aplicar validación temporal y evidencia comparable | ACEPTADA | No aplica |
| [DEC-029](#dec-029) | Separar la autoridad semántica oficial de la procedencia del CSV | ACEPTADA | No aplica |
| [DEC-030](#dec-030) | Registrar identidades inmutables y límites de las fuentes | ACEPTADA | No aplica |
| [DEC-031](#dec-031) | Usar una matriz limitada a campos prioritarios | REEMPLAZADA | DEC-032 |
| [DEC-032](#dec-032) | Usar un único diccionario canónico completo | ACEPTADA | No aplica |
| [DEC-033](#dec-033) | Mantener explícitas las definiciones insuficientes | ACEPTADA | No aplica |
| [DEC-034](#dec-034) | Tratar Y como completamente indefinida | REEMPLAZADA | DEC-035, DEC-037 |
| [DEC-035](#dec-035) | Definir conceptualmente Y como exceso futuro de dengue | ACEPTADA | No aplica |
| [DEC-036](#dec-036) | Usar P75 y umbrales numéricos anteriores en V1 | HISTÓRICA_NO_ADOPTADA | DEC-037, DEC-040 |
| [DEC-037](#dec-037) | Aprobar definitivamente la construcción del canal y las etiquetas | ABIERTA | No aplica |
| [DEC-038](#dec-038) | Priorizar la detección de nuevos inicios de brote | ACEPTADA | No aplica |
| [DEC-039](#dec-039) | Formalizar el inicio del mes objetivo frente al mes anterior | PROPUESTA | No aplica |
| [DEC-040](#dec-040) | Seleccionar posteriormente los umbrales operativos de probabilidad | ABIERTA | No aplica |
| [DEC-041](#dec-041) | No corregir ni descartar automáticamente las 8.556 anomalías | ACEPTADA | No aplica |
| [DEC-042](#dec-042) | Política de coincidencia mensual y reasignación de hasta siete días | PROPUESTA | No aplica |
| [DEC-043](#dec-043) | Comparar los tres escenarios solicitados para las anomalías | PROPUESTA | No aplica |
| [DEC-044](#dec-044) | Explorar asociaciones cronológicas antes de seleccionar variables | PROPUESTA | No aplica |
| [DEC-045](#dec-045) | Separar asociación de influencia predictiva o causal | ACEPTADA | No aplica |
| [DEC-046](#dec-046) | Usar la consulta como corroboración o candidata a imputación validada | PROPUESTA | No aplica |
| [DEC-047](#dec-047) | Resolver la procedencia climática y la ausencia de enero de 2020 | ABIERTA | No aplica |
| [DEC-048](#dec-048) | Definir elegibilidad predictiva sin reducir el alcance geográfico | ABIERTA | No aplica |
| [DEC-050](#dec-050) | Definir el contexto de datos de cada inferencia mensual | ACEPTADA | No aplica |
| [DEC-051](#dec-051) | Validar los datos de entrada antes de inferir | ACEPTADA | No aplica |
| [DEC-059](#dec-059) | Definir el conjunto final de variables y sus esquemas analíticos | ABIERTA | No aplica |
| [DEC-060](#dec-060) | Validar explicaciones e importancia del modelo | ACEPTADA | No aplica |
| [DEC-061](#dec-061) | Preferencias de evaluación científica de la propuesta de grado | PROPUESTA | No aplica |
| [DEC-062](#dec-062) | Seleccionar el modelo y calibrador de V2 únicamente con evidencia comparable | ABIERTA | No aplica |
| [DEC-065](#dec-065) | Distinguir periodos ausentes, datos vacíos y ceros observados | ACEPTADA | No aplica |
| [DEC-066](#dec-066) | Panel con ceros explícitos usado en V1 | HISTÓRICA_NO_ADOPTADA | DEC-065 |
| [DEC-067](#dec-067) | Sustitución de inicio por notificación usada en V1 | HISTÓRICA_NO_ADOPTADA | DEC-018 |
| [DEC-068](#dec-068) | Conjunto de 39 variables y exclusiones de V1 | HISTÓRICA_NO_ADOPTADA | DEC-059 |
| [DEC-069](#dec-069) | Rezagos epidemiológicos concretos del antecedente | HISTÓRICA_NO_ADOPTADA | No aplica |
| [DEC-070](#dec-070) | Rezagos climáticos y estacionalidad usados en V1 | HISTÓRICA_NO_ADOPTADA | No aplica |
| [DEC-071](#dec-071) | Familias de variables temporales sugeridas por el experto | PROPUESTA | No aplica |
| [DEC-072](#dec-072) | Densidad poblacional como covariable condicionada | PROPUESTA | No aplica |
| [DEC-073](#dec-073) | TerraClimate como fuente climática sugerida | HISTÓRICA_NO_ADOPTADA | No aplica |
| [DEC-074](#dec-074) | Agregación espacial del clima a límites municipales | PROPUESTA | No aplica |
| [DEC-075](#dec-075) | Definir agregaciones climáticas mensuales y unidades | ABIERTA | No aplica |
| [DEC-076](#dec-076) | CHIRPS y ERA5-Land como referencias del esquema climático actual | DOCUMENTADA_EN_FUENTE | No aplica |
| [DEC-077](#dec-077) | SARIMAX y LSTM como alternativas sugeridas por el experto | HISTÓRICA_NO_ADOPTADA | No aplica |
| [DEC-078](#dec-078) | Partición y calibración cronológicas descritas en V1 | HISTÓRICA_NO_ADOPTADA | No aplica |
| [DEC-079](#dec-079) | Ventanas expansivas y bloque temporal final reservado | PROPUESTA | No aplica |
| [DEC-080](#dec-080) | Calibración de Platt y umbrales por horizonte del antecedente | HISTÓRICA_NO_ADOPTADA | No aplica |
| [DEC-081](#dec-081) | Independencia de calibración y selección de umbrales | ABIERTA | No aplica |
| [DEC-082](#dec-082) | Ablación de variables próximas al canal y al estado actual | PROPUESTA | No aplica |
| [DEC-083](#dec-083) | Auditar las variables del periodo objetivo y su disponibilidad | ABIERTA | No aplica |
| [DEC-084](#dec-084) | Regenerar importancia y SHAP para el modelo realmente evaluado | ABIERTA | No aplica |
| [DEC-085](#dec-085) | Interpretar métricas por horizonte, municipio y número de inicios | PROPUESTA | No aplica |
| [DEC-086](#dec-086) | Definir el universo territorial independientemente de las filas observadas | APLICADA_EN_DIAGNÓSTICO | No aplica |
| [DEC-087](#dec-087) | Separar formato del código de pertenencia al catálogo | APLICADA_EN_DIAGNÓSTICO | No aplica |
| [DEC-088](#dec-088) | Sustitución de código territorial por nombre cuando falta el código | ABIERTA | No aplica |
| [DEC-089](#dec-089) | No fragmentar un municipio por variantes de nombre | ACEPTADA | No aplica |
| [DEC-090](#dec-090) | Conservar el corte analítico de la ejecución existente | APLICADA_EN_DIAGNÓSTICO | No aplica |
| [DEC-091](#dec-091) | Separar presencia territorial de continuidad temporal | APLICADA_EN_DIAGNÓSTICO | No aplica |
| [DEC-092](#dec-092) | Definir ventanas de intersección epidemiológica y climática | APLICADA_EN_DIAGNÓSTICO | No aplica |
| [DEC-093](#dec-093) | Clasificar fechas interpretables, ausentes e inconsistentes | APLICADA_EN_DIAGNÓSTICO | No aplica |
| [DEC-094](#dec-094) | No validar ANO y SEMANA únicamente con calendario ISO | ACEPTADA | No aplica |
| [DEC-095](#dec-095) | Controlar las llaves y la cardinalidad al comparar fuentes | APLICADA_EN_DIAGNÓSTICO | No aplica |
| [DEC-096](#dec-096) | Conservar separados los escenarios A–D ya ejecutados y los 1–3 propuestos | APLICADA_EN_DIAGNÓSTICO | No aplica |
| [DEC-097](#dec-097) | Verificar año y comparabilidad de las descargas anuales por contenido | APLICADA_EN_DIAGNÓSTICO | No aplica |
| [DEC-098](#dec-098) | Separar confirmación, gravedad, hospitalización y condición vital | ACEPTADA | No aplica |
| [DEC-099](#dec-099) | Definir representación y agregación mensual por tipo de variable | ABIERTA | No aplica |
| [DEC-100](#dec-100) | Resolver ponderación y heterogeneidad del panel municipal | ABIERTA | No aplica |
| [DEC-101](#dec-101) | Verificar que una coincidencia de fechas no se interprete como intercambio | ABIERTA | No aplica |
| [DEC-102](#dec-102) | Comprobar duplicados climáticos sin confundirlos con repeticiones de casos | APLICADA_EN_DIAGNÓSTICO | No aplica |
| [DEC-124](#dec-124) | Freeze Stage 5 research scope and alert meaning | ACCEPTED_RESEARCH_PROTOCOL | No aplica |
| [DEC-125](#dec-125) | Set provisional research utility criteria | ACCEPTED_RESEARCH_PROTOCOL | No aplica |
| [DEC-126](#dec-126) | Evaluate original and sigmoid-calibrated probabilities | ACCEPTED_RESEARCH_PROTOCOL | No aplica |
| [DEC-127](#dec-127) | Select alert thresholds within temporal development | ACCEPTED_RESEARCH_PROTOCOL | No aplica |
| [DEC-128](#dec-128) | Compare candidates with existing metrics and support | ACCEPTED_RESEARCH_PROTOCOL | No aplica |
| [DEC-129](#dec-129) | Freeze the selected protocol before reserved evaluation | ACCEPTED_RESEARCH_PROTOCOL | No aplica |
| [DEC-130](#dec-130) | Compare all six procedures and add complementary development AUROC | ACCEPTED_IMPLEMENTATION_SCOPE | No aplica |
| [DEC-131](#dec-131) | Implement the frozen final route before scientific authorization | ACCEPTED_IMPLEMENTATION_SCOPE | No aplica |
| [DEC-132](#dec-132) | Accept G4 and execute the exact frozen 2025 protocol | ACCEPTED_AND_EXECUTED | No aplica |
| [DEC-133](#dec-133) | Recommend G5 NOT_APPROVED after the frozen 2025 evaluation | PROPOSED_FOR_HUMAN_G5_DECISION | No aplica |
| [DEC-134](#dec-134) | Accept G5 NOT_APPROVED and centralize champion-decision policy | ACCEPTED_AND_CLOSED | No aplica |
| [DEC-135](#dec-135) | Approve G2 data/target and G3 training preparation baselines | ACCEPTED_WITH_DOCUMENTED_LIMITS | No aplica |
| [DEC-136](#dec-136) | Register EXP03.1 recent endemic-channel trajectory infrastructure | ACCEPTED_IMPLEMENTATION_SCOPE | No aplica |

## Registros detallados

<a id="dec-002"></a>
### DEC-002 Validar modelos y resultados de V2 sin transferir evidencia de V1

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** 2026-10-14 (ADR aceptado y fechado). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** No transferir los modelos ajustados, resultados, contrato de variables o desempeño de V1 como evidencia de validez del modelo V2.
- **Justificación:** Los datos, alcance geográfico y objetivos evaluados son diferentes; la generalización debe comprobarse con el conjunto y protocolo de V2.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** SRC-R, secciones 1–2; PRODUCT; NOTE.
- **Límites y validación pendiente:** V1 conserva valor como antecedente de variables, calibración y riesgos; no demuestra desempeño científico de V2.

<a id="dec-009"></a>
### DEC-009 Planteamiento nacional y piloto municipal de V1

- **Estado:** HISTÓRICA_NO_ADOPTADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; propuesta original, notas del experto y reporte de V1. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica; no adoptada como alcance actual del producto V2. **Reemplaza a:** No aplica. **Reemplazada por:** DEC-010.
- **Decisión, propuesta o práctica documentada:** Los materiales anteriores plantean Colombia, un piloto municipal acotado o Cali/Bucaramanga.
- **Justificación:** Explican la historia de la investigación, pero no autorizan una implementación nacional de V2 ni la restringen a las ciudades de V1.
- **Motivo de deprecación o no adopción:** La orientación explícita hacia Tolima/Meta rige V2; los documentos fuente siguen siendo evidencia histórica.
- **Evidencia y autoridad:** SRC-P, secciones 4–5; SRC-E, sección 3; SRC-R, sección 1; PROD1.
- **Límites y validación pendiente:** No se estableció una fecha de adopción o reversión de esos alcances en V2.

<a id="dec-010"></a>
### DEC-010 Definir el dominio analítico en municipios de Tolima y Meta

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; referencia de producto aceptada documentada a más tardar el 2026-10-15. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** DEC-009. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** El dominio de los datos y las predicciones de V2 comprende todos los municipios de Tolima y Meta; los resultados siguen siendo municipales.
- **Justificación:** Delimita la población y unidad de análisis sin confundir la inclusión geográfica con la suficiencia de datos.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** PROD1; NOTE.
- **Límites y validación pendiente:** La elegibilidad por historia o calidad se resuelve en DEC-048; no se documentan aquí pestañas, usuarios o interfaz.

<a id="dec-012"></a>
### DEC-012 Usar granularidad municipal y de año-mes calendario

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; documentado a más tardar el 2026-10-15; reafirmada explícitamente el 2026-10-17. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Construir el panel analítico a nivel municipio-mes. Interpretar mismo mes como coincidencia tanto de año como de mes.
- **Justificación:** Corresponde a los horizontes del producto y a las comparaciones endémicas estacionales, conservando la heterogeneidad territorial.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** SRC-P, secciones 7–8; NOTE; CHAT-04.
- **Límites y validación pendiente:** Conservar las fechas diarias originales para comprobar procedencia, consistencia y disponibilidad; el análisis mensual no autoriza borrarlas.

<a id="dec-013"></a>
### DEC-013 Producir pronósticos distintos para T+1 y T+2

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; referencia de producto aceptada documentada a más tardar el 2026-10-15. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** T es el último mes de referencia cargado; T+1 y T+2 son el mes calendario inmediatamente siguiente y el segundo siguiente.
- **Justificación:** Permite la preparación inmediata y las acciones que requieren mayor anticipación.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** PROD1; PROD7; SRC-P, objectives.
- **Límites y validación pendiente:** Dos salidas distintas no implican modelos ajustados por separado ni umbrales de probabilidad iguales.

<a id="dec-014"></a>
### DEC-014 Respetar la cronología y la disponibilidad de información

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (revisión y registro; fecha original de aprobación específica no acreditada). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Predecir con información disponible al corte de referencia; separar el mes de ocurrencia o inicio de síntomas del momento en que se conoció o revisó la información.
- **Justificación:** Evita que información futura y revisiones retrospectivas inflen el desempeño predictivo aparente.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** ML; PROD1; NOTE; CHAT-03.
- **Límites y validación pendiente:** La notificación por sí sola no reconstruye todas las revisiones históricas. Una fecha de notificación imposible no demuestra disponibilidad previa confiable.

<a id="dec-015"></a>
### DEC-015 Agrupar por ocurrencia en el reconocimiento inicial

- **Estado:** REEMPLAZADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; diagnóstico histórico registrado a más tardar el 2026-10-15. **Revisada el:** 2026-10-17.
- **Deprecada el:** DESCONOCIDA; reemplazo documentado a más tardar el 2026-10-16. **Reemplaza a:** No aplica. **Reemplazada por:** DEC-016.
- **Decisión, propuesta o práctica documentada:** El reconocimiento inicial utilizó campos de ocurrencia y ANO + SEMANA + COD_MUN_O para agrupaciones exploratorias.
- **Justificación:** Conservar los conteos históricos como evidencia de ejecución; la agrupación omitía departamento y no demostraba unicidad municipal nacional ni duplicación de casos.
- **Motivo de deprecación o no adopción:** Se seleccionó explícitamente residencia; ocurrencia y notificación no pueden ser filtros alternativos de alcance y un código municipal local no es único nacionalmente.
- **Evidencia y autoridad:** RECOG; NOTE; MATRIX.
- **Límites y validación pendiente:** Era una convención diagnóstica, no prueba de una decisión previa aprobada de atribución territorial del producto.

<a id="dec-016"></a>
### DEC-016 Atribuir los casos por residencia

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; documentada como vigente a más tardar el 2026-10-16. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** DEC-015. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Usar COD_DPTO_R y COD_MUN_R para la atribución municipal y el alcance de Tolima/Meta.
- **Justificación:** Define una ubicación analítica poblacional estable, distinta del prestador que notifica o del lugar de ocurrencia.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** NOTE; MATRIX.
- **Límites y validación pendiente:** El clima de residencia no prueba dónde se adquirió la infección; la aplicabilidad histórica del catálogo continúa pendiente.

<a id="dec-017"></a>
### DEC-017 Usar el inicio de síntomas como fecha epidemiológica

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** 2026-10-15 (decisión humana explícita registrada en el informe de reconocimiento). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Asignar el periodo epidemiológico a partir de INI_SIN.
- **Justificación:** El inicio de síntomas describe el momento de la enfermedad, en lugar del reporte administrativo, y es la referencia temporal del evento documentada.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** RECOG, sección 0.1; NOTE; MATRIX.
- **Límites y validación pendiente:** La validez cronológica y las políticas para anomalías son distintas del significado del campo.

<a id="dec-018"></a>
### DEC-018 No reemplazar silenciosamente un inicio ausente o inconsistente

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; documentada como vigente a más tardar el 2026-10-16. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** DEC-067. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** No sustituir automáticamente por FEC_NOT, intercambiar fechas ni convertir un inicio ausente en una fecha inventada.
- **Justificación:** Los campos representan procesos diferentes; el orden invertido por sí solo no identifica el campo erróneo ni demuestra un intercambio.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** NOTE; INVEST; MATRIX.
- **Límites y validación pendiente:** No impide adoptar después una política de imputación o corrección explícitamente validada.

<a id="dec-019"></a>
### DEC-019 Conservar los archivos originales y señalar anomalías

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; documentada como vigente a más tardar el 2026-10-16. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Conservar los insumos originales; realizar los diagnósticos y tratamientos por escenario en análisis derivados, preservando valores originales e indicadores de calidad.
- **Justificación:** Favorece la reversibilidad, la trazabilidad y la separación entre incertidumbre de medición e información corregida.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** DATA; NOTE; INVEST; MATRIX; CHAT-03.
- **Límites y validación pendiente:** Conservar el volumen o suavizar una curva no valida su exactitud temporal Los resultados comunicados se mantienen agregados, sin ejemplos identificables de pacientes.

<a id="dec-020"></a>
### DEC-020 Identificar municipios con códigos validados

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; documentada como vigente a más tardar el 2026-10-16. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Usar identificadores territoriales completos y referencias DIVIPOLA aplicables, en lugar de unir por nombre.
- **Justificación:** Los nombres municipales pueden variar y los códigos locales de tres caracteres se repiten entre departamentos.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** NOTE; PROV; MATRIX.
- **Límites y validación pendiente:** La pertenencia al catálogo actual y la procedencia reportada no certifican los límites históricos; el código de notificación tiene cinco posiciones en los CSV actuales.

<a id="dec-021"></a>
### DEC-021 Definir la inclusión de casos y la identidad de episodios

- **Estado:** ABIERTA.
- **Fecha de decisión o incorporación:** No aplica; asunto documentado a más tardar el 2026-10-16. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Resolver la inclusión de probables, confirmados y descartados, el ámbito de los identificadores, la precedencia de revisiones y la eliminación de duplicados antes de fijar conteos definitivos.
- **Justificación:** Las notificaciones no son automáticamente casos confirmados ni episodios únicos. CONSECUTIVE no es un identificador de paciente verificado.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** MATRIX; NOTE; CHAT-01.
- **Límites y validación pendiente:** Este registro no adopta una nueva regla de inclusión o exclusión.

<a id="dec-022"></a>
### DEC-022 Mantener separados 210 y 220 durante el análisis exploratorio actual

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; documentada como vigente a más tardar el 2026-10-16. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Describir por separado dengue y dengue grave hasta establecer su relación, inclusión y eliminación de duplicados.
- **Justificación:** Los códigos de evento distintos no demuestran conjuntos de casos disjuntos; una unión sin validar puede duplicar conteos.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** NOTE; MATRIX; objetivo del cuaderno.
- **Límites y validación pendiente:** Es la convención del análisis exploratorio acotado, no una regla definitiva que obligue a usar dengue grave como objetivo separado.

<a id="dec-023"></a>
### DEC-023 Serie principal de dengue y serie auxiliar de dengue grave en V1

- **Estado:** HISTÓRICA_NO_ADOPTADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; SRC-R secciones 1.3 y 2.1. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica; sin adopción automática en V2. **Reemplaza a:** No aplica. **Reemplazada por:** DEC-021, DEC-022.
- **Decisión, propuesta o práctica documentada:** V1 usó el evento 210 como serie principal y el 220 para historia y variables auxiliares rezagadas.
- **Justificación:** Explica la construcción previa de etiquetas sin decidir la unión o inclusión de eventos en V2.
- **Motivo de deprecación o no adopción:** Las exportaciones actuales requieren verificar inclusión y relaciones entre eventos o episodios antes de seleccionar la definición definitiva del conteo.
- **Evidencia y autoridad:** SRC-R, secciones 1.3 y 2.1.
- **Límites y validación pendiente:** El reporte llama dengue total a su serie; ese nombre por sí solo no resuelve cómo contar 210/220.

<a id="dec-024"></a>
### DEC-024 Elegir el entrenamiento compartido, departamental o municipal

- **Estado:** ABIERTA.
- **Fecha de decisión o incorporación:** No aplica; alternativas registradas el 2026-10-15. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** La granularidad del entrenamiento sigue sin decidirse.
- **Justificación:** La salida municipal no determina cuántos modelos se ajustan; la historia local y la escasez de inicios pueden limitar el entrenamiento independiente.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** NOTE; PROD1.
- **Límites y validación pendiente:** El volumen de notificaciones no equivale al número de observaciones municipio-mes ni decide la arquitectura.

<a id="dec-025"></a>
### DEC-025 Comparar el ajuste compartido con el departamental

- **Estado:** PROPUESTA.
- **Fecha de decisión o incorporación:** 2026-10-15 (recomendación documentada). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Considerar una comparación controlada con el mismo panel, etiquetas, variables, horizontes y particiones temporales; evaluar ajustes municipales solo donde la evidencia lo sustente.
- **Justificación:** Mide si la especialización geográfica aporta valor sin introducir factores de confusión en la comparación.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** NOTE, secciones 4–5.
- **Límites y validación pendiente:** Este registro no autoriza ni ejecuta experimentos ni selecciona una arquitectura ganadora.

<a id="dec-026"></a>
### DEC-026 Comparar las familias de modelos candidatas

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; presente en los fundamentos o referencia del producto a más tardar el 2026-10-15. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Mantener XGBoost, LightGBM y GAM como familias candidatas; la selección final depende de la evidencia.
- **Justificación:** Compara modelos no lineales y con interacciones con una alternativa más interpretable bajo un protocolo común.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** PRODUCT; SRC-P, sección 7.
- **Límites y validación pendiente:** No ordena reutilizar el modelo seleccionado de V1 ni declarar superioridad sin evidencia de V2.

<a id="dec-027"></a>
### DEC-027 Usar modelos de referencia epidemiológicos

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; referencia del producto documentada a más tardar el 2026-10-15. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Comparar con el canal endémico y la persistencia; usar Poisson únicamente cuando corresponda metodológicamente.
- **Justificación:** Permite evaluar si el aprendizaje automático agrega anticipación útil frente al estado epidemiológico actual y la historia simple.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** PRODUCT; SRC-P, secciones 7 y 10.
- **Límites y validación pendiente:** Son necesarios periodos de evaluación idénticos; un canal del estado observado no constituye automáticamente un pronóstico futuro desplegable.

<a id="dec-028"></a>
### DEC-028 Aplicar validación temporal y evidencia comparable

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (revisión y registro; fecha original de aprobación específica no acreditada). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Usar evaluación temporal estricta, ajustar transformaciones solo con entrenamiento y aplicar un protocolo común; no seleccionar modelos únicamente por resultados de entrenamiento.
- **Justificación:** Controla la fuga temporal, el sobreajuste y las afirmaciones basadas en comparaciones incompatibles.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** ML; SRC-P, sección 10.
- **Límites y validación pendiente:** La propuesta especifica ventanas expansivas y un bloque posterior sin usar; las fechas exactas de V2 siguen pendientes de aprobación definitiva.

<a id="dec-029"></a>
### DEC-029 Separar la autoridad semántica oficial de la procedencia del CSV

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (adoptada mediante el diccionario canónico solicitado). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Usar las definiciones técnicas del INS como autoridad semántica e identificar por separado las correspondencias empíricas de los archivos exportados.
- **Justificación:** Es posible establecer significados oficiales sin demostrar el procedimiento que generó un archivo local; nombres y huellas digitales no prueban por sí solos su procedencia.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** CHAT-01; CHAT-02; MATRIX; PROV.
- **Límites y validación pendiente:** No se aprueba un nuevo flujo de descarga desde el origen ni se reescribe silenciosamente la estrategia Kaggle/local.

<a id="dec-030"></a>
### DEC-030 Registrar identidades inmutables y límites de las fuentes

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; documentada como vigente a más tardar el 2026-10-16. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Registrar fuente, versión, evidencia de recuperación y huellas digitales cuando estén disponibles; separar modificación y ejecución local de publicación de la fuente y cortes analíticos.
- **Justificación:** Permite la replicación y evita presentar huellas posteriores como prueba de una ejecución anterior que no las registró.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** PROV; NOTE.
- **Límites y validación pendiente:** La procedencia DANE suministrada por una persona es atribución, no autenticación independiente; sigue pendiente la procedencia de la extracción climática.

<a id="dec-031"></a>
### DEC-031 Usar una matriz limitada a campos prioritarios

- **Estado:** REEMPLAZADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; alcance documental registrado el 2026-10-16. **Revisada el:** 2026-10-17.
- **Deprecada el:** 2026-10-17. **Reemplaza a:** No aplica. **Reemplazada por:** DEC-032.
- **Decisión, propuesta o práctica documentada:** La matriz canónica anterior interpretaba campos seleccionados e inventariaba los restantes mediante su cantidad.
- **Justificación:** Era adecuada para el análisis exploratorio inicial acotado, pero insuficiente para interpretar todas las columnas de los CSV.
- **Motivo de deprecación o no adopción:** Mauricio solicitó un diccionario de campos completo para ambas exportaciones de dengue en el mismo archivo canónico.
- **Evidencia y autoridad:** Revisión anterior de la matriz conservada en Git; CHAT-02.
- **Límites y validación pendiente:** Se retira ese alcance limitado, no las definiciones correctamente sustentadas.

<a id="dec-032"></a>
### DEC-032 Usar un único diccionario canónico completo

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (solicitud explícita en esta conversación). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** DEC-031. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** DATA-01-Priority Field Matrix.md es la única referencia de definición de los 69 campos compartidos; no mantener otro diccionario competidor.
- **Justificación:** Centraliza nombres, significados, codificaciones, prioridades, fuentes y aspectos semánticos pendientes de la exportación.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** CHAT-02; MATRIX.
- **Límites y validación pendiente:** Hay 63 conceptos con respaldo oficial y seis definiciones operativas insuficientes; la cobertura no es certificación científica. El diccionario conserva las definiciones, este registro solo su decisión de uso.
- **Documentation restoration:** Mauricio explicitly restored the canonical matrix to `docs/product/stage-2/DATA-01-Priority Field Matrix.md`. All 69 fields are inventoried; the report must not interpret the notebook's 59 default classification labels as missing field definitions. DEC-033 still governs the six insufficient operational definitions.

<a id="dec-033"></a>
### DEC-033 Mantener explícitas las definiciones insuficientes

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (parte de la solicitud del diccionario canónico). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Mantener explícitamente sin resolver el significado operativo de CONSECUTIVE, GRU_POB, confirmados, va_sispro, Estado_final_de_caso y nom_est_f_caso.
- **Justificación:** Las menciones institucionales o relaciones observadas no establecen algoritmos oficiales, versiones de catálogo ni ámbitos de identidad.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** MATRIX; CHAT-01.
- **Límites y validación pendiente:** La correspondencia observada entre estado final y confirmación es empírica; nunca equipararla con la gravedad clínica CLASFINAL.

<a id="dec-034"></a>
### DEC-034 Tratar Y como completamente indefinida

- **Estado:** REEMPLAZADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (interpretación anterior del asistente, no un método aprobado por una persona). **Revisada el:** 2026-10-17.
- **Deprecada el:** 2026-10-17. **Reemplaza a:** No aplica. **Reemplazada por:** DEC-035, DEC-037.
- **Decisión, propuesta o práctica documentada:** Una respuesta anterior planteó decidir si Y significaba conteos o inicio de brote sin revisar primero las fuentes conservadas del grupo.
- **Justificación:** Conservar el error interpretativo para que su corrección sea visible, en lugar de reescribir silenciosamente el historial.
- **Motivo de deprecación o no adopción:** El usuario señaló los acuerdos existentes del grupo; revisar las fuentes estableció exceso binario y un objetivo científico centrado en inicios. Los detalles operativos siguen abiertos.
- **Evidencia y autoridad:** CHAT-05; SRC-E; SRC-R; SRC-P.
- **Límites y validación pendiente:** Este registro documenta una interpretación corregida, no una elección científica previamente aprobada.

<a id="dec-035"></a>
### DEC-035 Definir conceptualmente Y como exceso futuro de dengue

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA para el acuerdo original del grupo; reconocimiento respaldado por fuentes el 2026-10-17. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** DEC-034. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Para el municipio m y h en {1,2}, Y(m,t,h)=1 cuando los casos en t+h superan el límite histórico de exceso aplicable, y 0 en caso contrario; estimar su probabilidad.
- **Justificación:** Las notas del experto definen explícitamente exceso/no exceso; la propuesta de grado se centra en anticipar transiciones y no en pronosticar conteos como único resultado.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** CHAT-05; SRC-E, sección 5; SRC-R, sección 2.1; SRC-P, secciones 5 y 10.
- **Límites y validación pendiente:** El acuerdo conceptual no fija la definición del conteo ni el procedimiento para generar el límite. Este registro no convierte P75 o una regla nueva en parámetros aprobados.

<a id="dec-036"></a>
### DEC-036 Usar P75 y umbrales numéricos anteriores en V1

- **Estado:** HISTÓRICA_NO_ADOPTADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; documentado en SRC-R. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica; no adoptada automáticamente en V2. **Reemplaza a:** No aplica. **Reemplazada por:** DEC-037, DEC-040.
- **Decisión, propuesta o práctica documentada:** V1 usó conteos futuros superiores a P75 para definir exceso y umbrales de integración 0.34/0.27 para las probabilidades de T+1/T+2.
- **Justificación:** Registra un antecedente real y distingue el límite del conteo de casos del umbral de probabilidad del modelo.
- **Motivo de deprecación o no adopción:** V2 requiere validar método, ventana, casos y calibración; las constantes históricas no se transfieren como reglas definitivamente aprobadas.
- **Evidencia y autoridad:** SRC-R, secciones 2.1 y 3.2; PROD7.
- **Límites y validación pendiente:** La implementación anterior no establece una justificación epidemiológica universal ni una aprobación para V2.

<a id="dec-037"></a>
### DEC-037 Aprobar definitivamente la construcción del canal y las etiquetas

- **Estado:** ABIERTA.
- **Fecha de decisión o incorporación:** No aplica; dependencia de la etapa 2; aclarada el 2026-10-17. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** DEC-036, DEC-034. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Elegir método, ventana histórica, referencia estacional, tratamiento de brotes previos y periodos sin casos, y si se conserva P75; ajustar solo con la historia permitida.
- **Justificación:** Estas elecciones cambian materialmente Y y pueden incorporar información futura si se estiman con toda la serie.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** NOTE; PROD1; CHAT-05.
- **Límites y validación pendiente:** El exceso binario está definido conceptualmente; la construcción definitiva del conteo y umbral de V2 no lo está.

<a id="dec-038"></a>
### DEC-038 Priorizar la detección de nuevos inicios de brote

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; propuesta de grado; reconocida el 2026-10-17. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Evaluar por separado la anticipación de inicios y la continuidad del exceso; reportar sensibilidad y cantidades absolutas de inicios.
- **Justificación:** Un buen desempeño durante brotes persistentes puede ocultar fallas para anticipar episodios nuevos.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** SRC-P, secciones 2, 5 y 10; SRC-R, secciones 2.3 y 4; CHAT-05.
- **Límites y validación pendiente:** El desempeño con tres transiciones de V1 no demuestra superioridad de V2 ni fija criterios numéricos de aceptación.

<a id="dec-039"></a>
### DEC-039 Formalizar el inicio del mes objetivo frente al mes anterior

- **Estado:** PROPUESTA.
- **Fecha de decisión o incorporación:** 2026-10-17 (formalización del asistente basada en fuentes). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** El indicador candidato de inicio en s es exceso(s)=1 y exceso(s-1)=0; para T+2, el mes anterior es t+1.
- **Justificación:** Separa una transición nueva de la persistencia y evita evaluar T+2 contra el mes incorrecto.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** CHAT-05; SRC-R, secciones 2.1 y 3.3.
- **Límites y validación pendiente:** La expresión mensual es una formalización explícita; las reglas de persistencia, reingreso y estados no disponibles aún requieren aprobación de la etapa 2.

<a id="dec-040"></a>
### DEC-040 Seleccionar posteriormente los umbrales operativos de probabilidad

- **Estado:** ABIERTA.
- **Fecha de decisión o incorporación:** No aplica; conservada desde la etapa 1. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** DEC-036. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Seleccionar calibración, umbrales por horizonte y niveles de alerta mediante validación temporal y un equilibrio explícito entre eventos omitidos y falsas alarmas.
- **Justificación:** El umbral de probabilidad es distinto del límite epidemiológico del conteo; un color no constituye validación científica.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** PROD6; PROD7; SRC-P, secciones 9–10.
- **Límites y validación pendiente:** No se adoptan 0.34, 0.27, 50%, colores fijos ni un umbral común para ambos horizontes.

<a id="dec-041"></a>
### DEC-041 No corregir ni descartar automáticamente las 8.556 anomalías

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; límite de investigación documentado el 2026-10-17. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Mantener visible el inicio posterior a la notificación; no se aprueba un intercambio, reemplazo, exclusión general ni descarte de un año en producción.
- **Justificación:** Las fechas afectadas pueden diferir por meses; su orden no identifica la columna errónea y perder registros puede distorsionar los picos epidémicos.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** INVEST; MATRIX; CHAT-03.
- **Límites y validación pendiente:** Esta restricción permanece hasta decidir un tratamiento y es compatible con escenarios de sensibilidad controlados.

<a id="dec-042"></a>
### DEC-042 Política de coincidencia mensual y reasignación de hasta siete días

- **Estado:** PROPUESTA.
- **Fecha de decisión o incorporación:** 2026-10-17 (propuesta del usuario). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Considerar conservar el inicio cuando coincidan año y mes y una regla de asignación mensual cuando las fechas crucen un límite de mes por hasta siete días.
- **Justificación:** Busca conservar la cronología mensual; la coincidencia de año-mes elimina la ambigüedad entre esas dos asignaciones mensuales.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** CHAT-03.
- **Límites y validación pendiente:** Hay 784 registros con igual año-mes, 42 con cambio de mes dentro de siete días y 7.730 con diferencias mayores; siete días no es una regla correctiva establecida por el INS. No se aprueba un mes de destino ni una política general.

<a id="dec-043"></a>
### DEC-043 Comparar los tres escenarios solicitados para las anomalías

- **Estado:** PROPUESTA.
- **Fecha de decisión o incorporación:** 2026-10-17 (propuesta explícita del usuario; ejecución pausada para documentar). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** El escenario 1 conserva los 8.556 registros en su mes original de inicio; el 2 conserva solo los 784 con igual año-mes de inicio y notificación y excluye 7.772; el 3 excluye los 8.556.
- **Justificación:** Mide cómo la incertidumbre temporal cambia conteos municipio-mes, picos, estacionalidad, asociaciones y etiquetas posteriores.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** CHAT-04; CHAT-03.
- **Límites y validación pendiente:** Aplicar la selección solo al grupo anómalo; los demás registros reciben idéntico tratamiento. No filtrar toda la base por coincidencia mensual. No se elige ningún escenario como verdad de producción.

<a id="dec-044"></a>
### DEC-044 Explorar asociaciones cronológicas antes de seleccionar variables

- **Estado:** PROPUESTA.
- **Fecha de decisión o incorporación:** 2026-10-17 (propuesta explícita del usuario; ejecución pausada para documentar). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Estudiar relaciones temporales mensuales dentro de dengue y dengue grave, entre ambos y con las covariables, incluidos rezagos pertinentes y sensibilidad por escenario.
- **Justificación:** La exploración puede identificar relaciones candidatas mientras se completa la construcción operativa de Y.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** CHAT-04.
- **Límites y validación pendiente:** Este registro no inicia el estudio de correlación, autoriza agregaciones arbitrarias de códigos nominales ni certifica un conjunto definitivo de variables.

<a id="dec-045"></a>
### DEC-045 Separar asociación de influencia predictiva o causal

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (revisión y registro; fecha original de aprobación específica no acreditada). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Tratar las correlaciones como exploratorias; evaluar su aporte predictivo adicional frente a Y futura mediante validación temporal y controles de estacionalidad, tendencia y disponibilidad.
- **Justificación:** La estacionalidad compartida, la autocorrelación y la fuga de información pueden crear importancia aparente engañosa; la asociación predictiva no establece causalidad.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** ML; CHAT-04.
- **Límites y validación pendiente:** En esta sesión no se declaran variables como las más influyentes ni se eliminan del modelo.

<a id="dec-046"></a>
### DEC-046 Usar la consulta como corroboración o candidata a imputación validada

- **Estado:** PROPUESTA.
- **Fecha de decisión o incorporación:** 2026-10-17 (recomendación del asistente). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Usar FEC_CON para evaluar plausibilidad; si fuera necesario estimar, evaluar un modelo de retraso desde el inicio con registros confiables e incertidumbre.
- **Justificación:** En el diagnóstico focalizado, las 8.556 consultas fueron simultáneas o posteriores al inicio y 7.832 compartían su mes, lo que respalda investigar antes que sustituir automáticamente por notificación.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** CHAT-03; MATRIX.
- **Límites y validación pendiente:** Son observaciones internas, no prueba independiente de fechas correctas; no se adopta sustitución por FEC_CON ni imputación.

<a id="dec-047"></a>
### DEC-047 Resolver la procedencia climática y la ausencia de enero de 2020

- **Estado:** ABIERTA.
- **Fecha de decisión o incorporación:** No aplica; documentado a más tardar el 2026-10-16. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Resolver cobertura ausente de enero de 2020, procedencia de extracción, agregación diaria a mensual y convenciones de unidades y signos antes de fijar las variables climáticas.
- **Justificación:** Fechas ausentes, celdas vacías y precipitación cero son distintas; acumulaciones y promedios diarios requieren agregaciones diferentes.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** MATRIX; PROV; NOTE.
- **Límites y validación pendiente:** No se aprueban interpolación, llenado con ceros, inversión de signos ni un método de recuperación climática.

<a id="dec-048"></a>
### DEC-048 Definir elegibilidad predictiva sin reducir el alcance geográfico

- **Estado:** ABIERTA.
- **Fecha de decisión o incorporación:** No aplica; dependencia de la etapa 2. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Determinar historia mínima, completitud, validez del catálogo y evidencia de eventos necesarias para emitir una predicción municipal.
- **Justificación:** Todos los municipios permanecen en el alcance, pero evidencia insuficiente no puede transformarse en una predicción de bajo riesgo.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** PROD1; PROD4; NOTE.
- **Límites y validación pendiente:** No se aprueba excluir municipios específicos ni convertir periodos ausentes en cero.

<a id="dec-050"></a>
### DEC-050 Definir el contexto de datos de cada inferencia mensual

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; referencia de producto aceptada documentada a más tardar el 2026-10-15. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** El insumo para inferencia corresponde a un departamento Tolima/Meta y a un mes de referencia cerrado, con registros de varios municipios.
- **Justificación:** Establece la población, el periodo y el conjunto de información permitido al modelo.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** PROD1; PROD5; PROD8.
- **Límites y validación pendiente:** Es una dirección documentada de los insumos; formato exacto, variables requeridas, omisiones admisibles y disponibilidad real siguen pendientes. Se excluye el mecanismo de carga en interfaz.

<a id="dec-051"></a>
### DEC-051 Validar los datos de entrada antes de inferir

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; referencia de producto aceptada documentada a más tardar el 2026-10-15. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Comprobar departamento, periodo, identidad municipal e información requerida antes de aplicar el modelo; impedir la inferencia con datos que incumplan las condiciones bloqueantes.
- **Justificación:** Evita aplicar el modelo a observaciones territorial o temporalmente inconsistentes o a variables incompatibles.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** PROD5.
- **Límites y validación pendiente:** Las reglas exactas de validación y tratamiento de casos parciales siguen abiertas. No se registran aquí flujos de interfaz ni persistencia del producto.

<a id="dec-059"></a>
### DEC-059 Definir el conjunto final de variables y sus esquemas analíticos

- **Estado:** ABIERTA.
- **Fecha de decisión o incorporación:** No aplica; pospuestos explícitamente en la etapa 1. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** DEC-068. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Resolver variables de entrada y derivadas, representación, tipos, ventanas históricas y compatibilidad entre entrenamiento e inferencia antes de fijar el conjunto final del modelo.
- **Justificación:** Sin un esquema analítico estable no se pueden reproducir las predicciones ni distinguir diferencias de datos de diferencias entre modelos.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** MATRIX; NOTE; PROD7; PROD8.
- **Límites y validación pendiente:** Las 39 variables de V1 no se transfieren automáticamente. Se excluyen contratos de API, transporte y detalles de infraestructura.

<a id="dec-060"></a>
### DEC-060 Validar explicaciones e importancia del modelo

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; referencia de producto aceptada documentada a más tardar el 2026-10-15. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Usar explicaciones e importancia de variables solo cuando correspondan al modelo evaluado y a los datos y particiones declarados; no inventar atribuciones.
- **Justificación:** Una explicación de la salida del modelo no demuestra causalidad y puede quedar obsoleta después de reentrenar.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** PROD6; PROD7; SRC-P, sección 9.
- **Límites y validación pendiente:** No se aprueba aún un método específico de explicabilidad para V2. Su presentación en interfaz está fuera de este registro.

<a id="dec-061"></a>
### DEC-061 Preferencias de evaluación científica de la propuesta de grado

- **Estado:** PROPUESTA.
- **Fecha de decisión o incorporación:** DESCONOCIDA; especificación de la fuente; revisada el 2026-10-17. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Priorizar sensibilidad sobre inicios y cantidades absolutas detectadas/total; revisar también falsas alarmas, precisión, F1, PR-AUC, puntuación de Brier y calibración por horizonte y municipio.
- **Justificación:** Las transiciones escasas y el desbalance de clases hacen insuficientes la exactitud general o el F1 de estados persistentes.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** SRC-P, sección 10; SRC-R, secciones 2.3 y 4; NOTE.
- **Límites y validación pendiente:** La propuesta sugiere igualar la sensibilidad del canal, superar la persistencia y aumentar como máximo cinco puntos porcentuales las falsas alarmas; son criterios propuestos, no umbrales aprobados para V2.
- **Current disposition (2026-10-20):** [DEC-125](#dec-125) now governs the accepted Stage 5 research utility criteria, with an explicit persistence reference and false-alert-ratio denominator. The source proposal and its broader metric list remain historical; no operational threshold is approved here.

<a id="dec-062"></a>
### DEC-062 Seleccionar el modelo y calibrador de V2 únicamente con evidencia comparable

- **Estado:** ABIERTA.
- **Fecha de decisión o incorporación:** No aplica; etapas posteriores de modelado y evaluación. **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Evaluar modelos, calibración, umbrales operativos y desempeño local antes de declarar un modelo seleccionado para V2.
- **Justificación:** La integración de V1 y sus resultados SHAP no prueban superioridad predictiva, calibración ni anticipación confiable de V2.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** PRODUCT; NOTE; SRC-R, secciones 2.2–2.5.
- **Límites y validación pendiente:** Esta tarea documental no ejecuta entrenamiento de V2 ni experimentos de selección de variables.

<a id="dec-065"></a>
### DEC-065 Distinguir periodos ausentes, datos vacíos y ceros observados

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** DEC-066. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** No convertir automáticamente meses sin registros, celdas vacías o municipios ausentes en cero casos o cero precipitación.
- **Justificación:** El cero describe una observación; la ausencia puede deberse a falta de reporte, cobertura o extracción y sesgar tanto Y como los rezagos.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** RECOG, secciones de continuidad; MATRIX, sección ambiental; NOTE.
- **Límites y validación pendiente:** La imputación, las condiciones que permiten afirmar cero y el tratamiento de periodos incompletos siguen abiertos.

<a id="dec-066"></a>
### DEC-066 Panel con ceros explícitos usado en V1

- **Estado:** HISTÓRICA_NO_ADOPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** DEC-065.
- **Decisión, propuesta o práctica documentada:** El reporte de V1 describe un panel de 1.114 municipios con ceros explícitos.
- **Justificación:** Es un antecedente de preparación que afecta la distribución de conteos y la etiqueta; debe distinguirse de la evidencia actual sobre cobertura.
- **Motivo de deprecación o no adopción:** La convención de V1 no se adopta automáticamente; V2 exige distinguir ausencia y cero.
- **Evidencia y autoridad:** SRC-R, sección 1.3, párrafos 34–36.
- **Límites y validación pendiente:** No establece que toda ausencia de V2 sea un cero real. No se ha auditado el código generador de V1 en esta tarea.

<a id="dec-067"></a>
### DEC-067 Sustitución de inicio por notificación usada en V1

- **Estado:** HISTÓRICA_NO_ADOPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** DEC-018.
- **Decisión, propuesta o práctica documentada:** V1 usaba INI_SIN con notificación como respaldo cuando correspondía según su flujo previo.
- **Justificación:** Permite rastrear el antecedente de la discusión sobre continuidad temporal.
- **Motivo de deprecación o no adopción:** La decisión vigente de V2 prohíbe sustituir fechas automáticamente; el antecedente se conserva sin fingir una revocación histórica en V2.
- **Evidencia y autoridad:** SRC-R, sección 1.3, párrafo 35; NOTE, referencia al microproyecto.
- **Límites y validación pendiente:** No demuestra que ese respaldo sea adecuado para las 8.556 inconsistencias de V2.

<a id="dec-068"></a>
### DEC-068 Conjunto de 39 variables y exclusiones de V1

- **Estado:** HISTÓRICA_NO_ADOPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** DEC-059.
- **Decisión, propuesta o práctica documentada:** V1 construía 41 variables numéricas y usaba 39; excluía los conteos contemporáneos crudos casos_clasico y casos_grave, manteniendo historia por rezagos y ventanas móviles.
- **Justificación:** Es una decisión concreta de selección de variables del antecedente que faltaba en el registro.
- **Motivo de deprecación o no adopción:** No se transfiere el conjunto fijo de V1 a V2 sin evaluar datos, Y y contribución predictiva.
- **Evidencia y autoridad:** SRC-R, secciones 1.4 y 2.2, párrafos 40 y 50–68.
- **Límites y validación pendiente:** No prueba que los conteos actuales sean inválidos o indisponibles al cierre de t; su inclusión en V2 se decide con disponibilidad y validación, no copiando V1.

<a id="dec-069"></a>
### DEC-069 Rezagos epidemiológicos concretos del antecedente

- **Estado:** HISTÓRICA_NO_ADOPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** V1 incluía casos_clasico y casos_grave con rezagos 1, 2, 3, 4 y 6 meses y promedios móviles de tres meses.
- **Justificación:** Documenta la memoria temporal efectivamente descrita en el reporte, en lugar de una referencia vaga a historia.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** SRC-R, sección 2.2, párrafos 57–59.
- **Límites y validación pendiente:** Son 12 variables históricas reportadas; longitud de memoria, cierre de la ventana y tratamiento de huecos de V2 no están seleccionados.

<a id="dec-070"></a>
### DEC-070 Rezagos climáticos y estacionalidad usados en V1

- **Estado:** HISTÓRICA_NO_ADOPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** V1 incluía temperatura y lluvia rezagadas 1, 2 y 3 meses, además de mes_sin y mes_cos como representación cíclica del mes.
- **Justificación:** Aporta antecedentes concretos de ingeniería temporal y estacionalidad.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** SRC-R, sección 2.2, párrafos 60–65.
- **Límites y validación pendiente:** No se adopta automáticamente ese conjunto ni se considera la estacionalidad una prueba causal del aporte climático.

<a id="dec-071"></a>
### DEC-071 Familias de variables temporales sugeridas por el experto

- **Estado:** PROPUESTA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Evaluar casos históricos, rezagos, tendencias recientes, ventanas móviles, estacionalidad y autocorrelación, usando únicamente información anterior al horizonte predicho.
- **Justificación:** Permite estudiar cuánta señal predictiva aporta el pasado y separar persistencia de anticipación.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** SRC-E, sección 6, párrafos 31–41.
- **Límites y validación pendiente:** La selección final, rezagos máximos y ventanas dependen de Y, historia válida y validación temporal; la recomendación no congela variables.

<a id="dec-072"></a>
### DEC-072 Densidad poblacional como covariable condicionada

- **Estado:** PROPUESTA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Considerar densidad poblacional solo si su fuente, cobertura espacial, vigencia y frecuencia permiten alinearla de forma defendible con el panel mensual.
- **Justificación:** El experto identificó su posible valor y la limitación de no disponer necesariamente de variación mensual adecuada.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** SRC-E, sección 6, párrafo 42.
- **Límites y validación pendiente:** No se inventan valores mensuales ni se aprueba interpolar población. No está seleccionada como variable final.

<a id="dec-073"></a>
### DEC-073 TerraClimate como fuente climática sugerida

- **Estado:** HISTÓRICA_NO_ADOPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Las notas del experto mencionan TerraClimate entre los conjuntos por evaluar en Google Earth Engine.
- **Justificación:** Conserva una sugerencia de fuente distinta de CHIRPS y ERA5-Land para no borrar la historia de alternativas.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** SRC-E, sección 7, párrafos 43–48.
- **Límites y validación pendiente:** No identifica el origen del CSV actual ni autoriza sustituir productos o mezclar sus unidades sin validación.

<a id="dec-074"></a>
### DEC-074 Agregación espacial del clima a límites municipales

- **Estado:** PROPUESTA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Obtener variables climáticas municipales a partir de píxeles dentro de los límites municipales y una agregación espacial explícita.
- **Justificación:** La geometría, resolución, ponderación y producto condicionan qué exposición climática representa cada fila municipal.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** SRC-E, sección 7; SRC-P, sección 8; MATRIX, sección ambiental; PROV, E1–E3.
- **Límites y validación pendiente:** La referencia ambiental describe promedios espaciales; no prueba que ese procedimiento generara el CSV actual ni dónde se adquirió cada infección.

<a id="dec-075"></a>
### DEC-075 Definir agregaciones climáticas mensuales y unidades

- **Estado:** ABIERTA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Especificar por variable si corresponde promedio, suma u otra agregación del dato diario; conservar unidades y convención de signos, incluida evaporación ECMWF.
- **Justificación:** Un acumulado diario y una media diaria no admiten automáticamente la misma operación mensual.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** MATRIX, sección ambiental; PROV, referencias E1–E3.
- **Límites y validación pendiente:** No se aprueba aquí una suma de precipitación, promedio térmico, cambio de signo o conversión nueva; esas reglas requieren evidencia del producto y extracción.

<a id="dec-076"></a>
### DEC-076 CHIRPS y ERA5-Land como referencias del esquema climático actual

- **Estado:** DOCUMENTADA_EN_FUENTE.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** El diccionario ambiental de referencia atribuye lluvia a CHIRPS y temperatura, rocío, suelo, escorrentía, evaporación, viento y radiación a ERA5-Land.
- **Justificación:** Permite interpretar las nueve covariables sin confundir compatibilidad de nombres con trazabilidad de extracción.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** MATRIX, sección ambiental; PROV, E1–E3; SRC-P, sección 8; SRC-R, sección 2.2.
- **Límites y validación pendiente:** La configuración 2018–2024 del script y el intervalo 2007–2025 del CSV difieren; la versión y el trabajo generador real permanecen pendientes.

<a id="dec-077"></a>
### DEC-077 SARIMAX y LSTM como alternativas sugeridas por el experto

- **Estado:** HISTÓRICA_NO_ADOPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** El experto sugirió inicialmente SARIMAX, LSTM y XGBoost; la propuesta y referencia actuales de V2 priorizan XGBoost, LightGBM y GAM.
- **Justificación:** Explicita la diferencia entre sugerencias exploratorias y familias actualmente previstas.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** SRC-E, sección 8, párrafos 49–54; SRC-P, sección 7; PRODUCT.
- **Límites y validación pendiente:** No se declara que SARIMAX/LSTM hayan sido rechazados experimentalmente, evaluados o aprobados para V2.

<a id="dec-078"></a>
### DEC-078 Partición y calibración cronológicas descritas en V1

- **Estado:** HISTÓRICA_NO_ADOPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** El reporte de V1 describe entrenamiento hasta 2022, prueba 2023–2025, validación temporal interna y calibración posterior con datos 2021–2022.
- **Justificación:** Son decisiones concretas del antecedente que afectan la comparación de resultados y requieren trazabilidad.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** SRC-R, sección 1.3, párrafo 36; sección 2.1.
- **Límites y validación pendiente:** No se transfieren estas fechas a V2 ni se certifica independencia de la calibración: el periodo descrito coincide temporalmente con parte del entrenamiento.

<a id="dec-079"></a>
### DEC-079 Ventanas expansivas y bloque temporal final reservado

- **Estado:** PROPUESTA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Aplicar validación cruzada temporal con ventana expansiva durante el entrenamiento y reservar un bloque posterior para evaluación final; recalcular el canal dentro de cada partición con historia permitida.
- **Justificación:** Evita que el límite de exceso y las transformaciones aprendan de los periodos que se pretende evaluar.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** SRC-P, secciones 7 y 10; ML; NOTE.
- **Límites y validación pendiente:** El principio de validación temporal está aceptado en DEC-028; las fechas, tamaños, separación y maduración de reportes de V2 siguen pendientes.

<a id="dec-080"></a>
### DEC-080 Calibración de Platt y umbrales por horizonte del antecedente

- **Estado:** HISTÓRICA_NO_ADOPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** V1 reporta calibración de probabilidades de XGBoost mediante Platt y umbrales 0.34 para T+1 y 0.27 para T+2.
- **Justificación:** Separa el método para ajustar probabilidades del umbral operativo y del límite epidemiológico P75.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** SRC-R, secciones 2.1 y 3.2; prueba-dashboard.md, sección 5.
- **Límites y validación pendiente:** El documento no demuestra que ese método sea óptimo o válido en V2; comparar calibración con datos independientes y no copiar umbrales.

<a id="dec-081"></a>
### DEC-081 Independencia de calibración y selección de umbrales

- **Estado:** ABIERTA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Definir qué datos se usarán para ajustar calibración y umbrales sin usar la prueba final ni generar predicciones de calibración sobre datos de ajuste del modelo.
- **Justificación:** La descripción V1 de calibración 2021–2022 y entrenamiento hasta 2022 no basta para demostrar independencia; se requiere revisar cómo se produjeron esas predicciones.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** SRC-R, secciones 1.3 y 2.1; ML; NOTE.
- **Límites y validación pendiente:** Se registra un vacío de evidencia, no una afirmación de fuga demostrada. No se selecciona un procedimiento nuevo para V2.

<a id="dec-082"></a>
### DEC-082 Ablación de variables próximas al canal y al estado actual

- **Estado:** PROPUESTA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Comparar el modelo completo con una variante sin brote, brote_lag_1, zona_canal y sir; declarar si también se retiran percentiles y variables del canal del periodo objetivo.
- **Justificación:** El profesor solicitó distinguir aporte adicional de la persistencia; el reporte señala importancia previa aproximada de 0.41 para brote_lag_1.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** SRC-R, sección 2.2.1, párrafos 69 y 73.
- **Límites y validación pendiente:** No existe en la fuente una corrida de ablación reproducible ni una mejora medida. La propuesta no elimina variables de V2 ni acredita importancia vigente.

<a id="dec-083"></a>
### DEC-083 Auditar las variables del periodo objetivo y su disponibilidad

- **Estado:** ABIERTA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Verificar cómo se construyen p25_objetivo, p75_objetivo y zona_objetivo y si cada valor puede obtenerse al cierre de t sin observar el futuro.
- **Justificación:** Una referencia estacional calculada con historia puede estar disponible; una zona basada en casos futuros sería fuga. El nombre no permite resolverlo.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** SRC-R, sección 2.2, párrafo 67; SRC-E, sección 2; MATRIX; NOTE.
- **Límites y validación pendiente:** No se etiqueta automáticamente toda variable con sufijo objetivo como inválida ni se certifica su seguridad sin inspeccionar la construcción.

<a id="dec-084"></a>
### DEC-084 Regenerar importancia y SHAP para el modelo realmente evaluado

- **Estado:** ABIERTA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Vincular importancia y explicaciones a la versión ajustada, corte, variables y conjunto evaluado; regenerar análisis cuando cambie el modelo.
- **Justificación:** El reporte advierte que los SHAP guardados antecedían al reentrenamiento con corte 2022 y no se reutilizaron como evidencia del modelo vigente.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** SRC-R, sección 2.2, párrafos 69–70; DEC-060.
- **Límites y validación pendiente:** Es un problema de evidencia analítica, no un requisito de interfaz; no se afirma disponer ya de SHAP válidos para V2.

<a id="dec-085"></a>
### DEC-085 Interpretar métricas por horizonte, municipio y número de inicios

- **Estado:** PROPUESTA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Reportar resultados por horizonte y municipio, con número absoluto de inicios detectados y totales; controlar si los agregados ocultan fallas locales.
- **Justificación:** Con pocos inicios, una transición modifica fuertemente la sensibilidad; V1 reporta tres y la evidencia T+2 no incluye todos los modelos de referencia bajo el mismo protocolo.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** SRC-P, sección 10; SRC-R, secciones 2.3 y 4; NOTE, sección 5.
- **Límites y validación pendiente:** Las cifras V1 no se convierten en desempeño de V2. PR-AUC, Brier y falsas alarmas se complementan, no sustituyen la evaluación de inicios.

<a id="dec-086"></a>
### DEC-086 Definir el universo territorial independientemente de las filas observadas

- **Estado:** APLICADA_EN_DIAGNÓSTICO.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Construir el universo esperado de municipios desde DIVIPOLA y comparar por separado presencia en dengue, dengue grave y clima.
- **Justificación:** Evita excluir del análisis de cobertura los municipios que no aparecen en un archivo.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** RECOG, sección DIVIPOLA; cuaderno, celdas 8 y 11; PLAN003, tarea 2.
- **Límites y validación pendiente:** El diagnóstico encuentra 29 municipios de Meta y 47 de Tolima; no demuestra que toda ausencia sea cero ni aprueba elegibilidad predictiva.

<a id="dec-087"></a>
### DEC-087 Separar formato del código de pertenencia al catálogo

- **Estado:** APLICADA_EN_DIAGNÓSTICO.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Evaluar por separado longitud, caracteres y relleno explícito de ceros, coherencia entre código completo y departamento, y pertenencia al catálogo.
- **Justificación:** Un código de cinco dígitos puede tener formato válido sin corresponder a un municipio de la referencia.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** Cuaderno, celdas 5, 8 y 11; PLAN003, tareas 1–2; MATRIX.
- **Límites y validación pendiente:** El relleno se realiza en variables derivadas; no se truncan códigos largos ni se sobrescriben los originales. El catálogo actual no acredita validez histórica.

<a id="dec-088"></a>
### DEC-088 Sustitución de código territorial por nombre cuando falta el código

- **Estado:** ABIERTA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Resolver si alguna vez se permite atribución por nombre y cómo bloquear contradicciones entre nombre y código.
- **Justificación:** El cuaderno conserva una rama de respaldo por nombre; el resultado guardado informa cero usos y cero conflictos, lo que no valida la política futura.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** Cuaderno, celda 5; MATRIX, geografía; NOTE.
- **Límites y validación pendiente:** No se convierte la presencia de esa rama en una decisión científica aprobada; la regla vigente prioriza códigos validados.

<a id="dec-089"></a>
### DEC-089 No fragmentar un municipio por variantes de nombre

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Usar el código municipal completo validado como identidad de agrupación; tratar el nombre como atributo de conciliación.
- **Justificación:** Agrupar por código y nombre puede partir una misma serie en varias y alterar correlaciones, continuidad y tamaño del panel.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** MATRIX; PLAN003, tarea 2; cuaderno, celda 5.
- **Límites y validación pendiente:** El resumen municipal inicial todavía agrupa por departamento, código y nombre. La regla documental no prueba cumplimiento integral; no se modifica el cuaderno en esta auditoría.

<a id="dec-090"></a>
### DEC-090 Conservar el corte analítico de la ejecución existente

- **Estado:** APLICADA_EN_DIAGNÓSTICO.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** La ejecución existente fija ANALYSIS_CUTOFF_DATE y PREVIOUS_EXECUTION_CUTOFF_DATE en 2026-10-15 y registra aparte el momento de ejecución.
- **Justificación:** Permite repetir diagnósticos sin desplazar silenciosamente la referencia temporal al día de auditoría.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** Cuaderno, celdas 2–3; PROV, sección 3; RECOG.
- **Límites y validación pendiente:** La fecha 2026-10-17 de este registro no cambia el corte de datos ni define las futuras particiones de entrenamiento.

<a id="dec-091"></a>
### DEC-091 Separar presencia territorial de continuidad temporal

- **Estado:** APLICADA_EN_DIAGNÓSTICO.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Medir presencia de municipios y continuidad por municipio y fuente con ventanas explícitas, distinguiendo periodos previos, huecos internos y periodos posteriores.
- **Justificación:** Estar presente alguna vez no implica una serie mensual completa.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** RECOG, secciones territorial y temporal; cuaderno, celda 11; PLAN003, tarea 3.
- **Límites y validación pendiente:** La ausencia de meses no se rellena con cero y no se descartan municipios automáticamente.

<a id="dec-092"></a>
### DEC-092 Definir ventanas de intersección epidemiológica y climática

- **Estado:** APLICADA_EN_DIAGNÓSTICO.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Distinguir ventanas de unión e intersección entre fuentes; calcular la cobertura climática sobre el periodo común explícito.
- **Justificación:** Evita interpretar como faltantes internos los periodos fuera de la cobertura disponible de otra fuente.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** Cuaderno, celdas 6, 9 y 11; RECOG; PROV.
- **Límites y validación pendiente:** La ventana común guardada es 2007-01-01 a 2025-12-31; no es una partición definitiva del modelo ni una autorización para eliminar observaciones externas.

<a id="dec-093"></a>
### DEC-093 Clasificar fechas interpretables, ausentes e inconsistentes

- **Estado:** APLICADA_EN_DIAGNÓSTICO.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Interpretar fechas epidemiológicas con día/mes/año y clima con año-mes-día en variables derivadas; separar ausencia, error de conversión, futuro respecto al corte y contradicción cronológica.
- **Justificación:** Una fecha convertible puede ser cronológicamente imposible; una cadena vacía no es equivalente a un valor inválido.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** Cuaderno, celdas 5, 9 y 11; INVEST; MATRIX.
- **Límites y validación pendiente:** Los sufijos horarios se ignoran en el diagnóstico por fecha; no se certifica precisión intradiaria ni se corrigen fechas originales.

<a id="dec-094"></a>
### DEC-094 No validar ANO y SEMANA únicamente con calendario ISO

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Usar el año y semana epidemiológicos del evento y verificar la edición y calendario colombiano; la comparación ISO del cuaderno es descriptiva.
- **Justificación:** Los límites de semana y año pueden diferir, generando discrepancias legítimas o errores que requieren revisión diferenciada.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** MATRIX, sección de fechas; RECOG; cuaderno, celda 5.
- **Límites y validación pendiente:** Para 210/220 las ediciones oficiales consultadas vinculan semana con inicio de síntomas; sigue pendiente demostrar la regla aplicada en el export concreto.

<a id="dec-095"></a>
### DEC-095 Controlar las llaves y la cardinalidad al comparar fuentes

- **Estado:** APLICADA_EN_DIAGNÓSTICO.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Evaluar completitud y unicidad de CONSECUTIVE en cada subconjunto comparable y realizar correspondencia uno a uno solo donde sea defendible; contar no correspondidos en ambos sentidos.
- **Justificación:** Evita que una unión muchos-a-muchos multiplique registros y que la unicidad local se confunda con identidad global del paciente.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** INVEST, sección 3; PLAN004, tarea 4; comparison_key_stability.csv; comparison_match_outcomes.csv.
- **Límites y validación pendiente:** Los subconjuntos anuales muestran unicidad local; no prueba estabilidad universal, equivalencia clínica, autenticidad de la fuente o un identificador de paciente.

<a id="dec-096"></a>
### DEC-096 Conservar separados los escenarios A–D ya ejecutados y los 1–3 propuestos

- **Estado:** APLICADA_EN_DIAGNÓSTICO.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** La investigación ejecutó A conservar, B intercambiar fechas afectadas, C excluir y D usar referencia 2013 con respaldo a A; son distintos de los escenarios 1–3 propuestos en DEC-043.
- **Justificación:** Evita atribuir ejecución al escenario nuevo de coincidencia año-mes solo porque existe un escenario B anterior.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** INVEST, secciones 3–4; PLAN004, tarea 5; cuaderno, celdas 14–16; CHAT-04.
- **Límites y validación pendiente:** El intercambio elimina retrasos negativos por construcción; conservar volumen o coincidir con la referencia anual no prueba fechas verdaderas. Ningún escenario se adopta como limpieza definitiva.

<a id="dec-097"></a>
### DEC-097 Verificar año y comparabilidad de las descargas anuales por contenido

- **Estado:** APLICADA_EN_DIAGNÓSTICO.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Inventariar fuentes de 2012–2014 por contenido y cobertura de fechas, no solo nombre; distinguir año de síntomas, notificación y ANO y conservar denominadores comparables.
- **Justificación:** Los subconjuntos anuales, poblaciones y años de fecha pueden no coincidir; un nombre de archivo no define el periodo clínico real.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** PLAN004, tareas 1–3; INVEST; source_inventory.csv; baseline_anomaly_by_year_dimensions.csv.
- **Límites y validación pendiente:** La reproducción de las 8.556 alertas no identifica por sí sola el origen causal de la inconsistencia.

<a id="dec-098"></a>
### DEC-098 Separar confirmación, gravedad, hospitalización y condición vital

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Interpretar TIP_CAS/AJUSTE y estados derivados como clasificación de confirmación, CLASFINAL como gravedad, PAC_HOS como hospitalización y CON_FIN como condición vital, sin equivalencias automáticas.
- **Justificación:** Confundir estos ejes cambia el conteo de casos y la población de Y.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** MATRIX, secciones de codificación y estados derivados.
- **Límites y validación pendiente:** CLASFINAL no está en los encabezados; la correspondencia empírica de confirmados con estados 3/5 no constituye una fórmula oficial para cualquier export.

<a id="dec-099"></a>
### DEC-099 Definir representación y agregación mensual por tipo de variable

- **Estado:** ABIERTA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Elegir para cada campo si procede conteo, proporción, distribución, indicador u otra representación; no correlacionar como magnitudes códigos nominales por ser numéricos.
- **Justificación:** La correlación y la selección de variables requieren semántica compatible, denominadores y granularidad; el número asignado a un municipio o categoría no es una medida continua.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** MATRIX, tipos y códigos; CHAT-04; NOTE.
- **Límites y validación pendiente:** Se registra una necesidad de diseño derivada del diccionario, no una codificación final ni nuevas variables aprobadas. Fechas de hospitalización o ajustes posteriores deben superar el control de disponibilidad.

<a id="dec-100"></a>
### DEC-100 Resolver ponderación y heterogeneidad del panel municipal

- **Estado:** ABIERTA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Definir si el ajuste compartido o departamental necesita ponderación o controles por municipio y cómo medir estabilidad local bajo el mismo protocolo.
- **Justificación:** Una ciudad con muchas notificaciones no aporta automáticamente más filas mensuales, pero escala del conteo, brotes y heterogeneidad pueden dominar el ajuste o las métricas.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** NOTE, secciones 4–5; RECOG, hallazgos epidemiológicos.
- **Límites y validación pendiente:** No se aprueban pesos, exclusiones de ciudades, normalización de incidencia ni modelos municipales separados.

<a id="dec-101"></a>
### DEC-101 Verificar que una coincidencia de fechas no se interprete como intercambio

- **Estado:** ABIERTA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Antes de usar exact_swapped_pairs como evidencia de fechas intercambiadas, verificar que la métrica excluya pares donde inicio y notificación ya son iguales.
- **Justificación:** Si dos fechas son iguales, también satisfacen la igualdad invertida; la métrica por sí sola no identifica una inversión.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** comparison_date_pairs.csv; INVEST, sección 4.3; CONCLUSIONES004, sección 3.
- **Límites y validación pendiente:** Es una limitación lógica de interpretación detectada en auditoría; no se recalculó la métrica ni se afirma que todos sus pares sean iguales. No se adopta corrección de fechas.

<a id="dec-102"></a>
### DEC-102 Comprobar duplicados climáticos sin confundirlos con repeticiones de casos

- **Estado:** APLICADA_EN_DIAGNÓSTICO.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en esta auditoría; no implica aprobación original en esta fecha). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Evaluar duplicados por municipio-fecha en el clima y tratar por separado la identidad de casos epidemiológicos; muchos casos pueden compartir municipio y periodo.
- **Justificación:** La unidad de observación difiere entre una medición climática municipal diaria y una notificación individual. Aplicar la misma regla de unicidad eliminaría casos válidos.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** RECOG, secciones de clima e interpretación; cuaderno, celdas 9 y 11; MATRIX.
- **Límites y validación pendiente:** El diagnóstico climático acotado reporta cero duplicados municipio-fecha; no prueba ausencia de duplicados de pacientes ni autoriza borrar notificaciones por una llave mensual repetida.

## Hallazgos de coherencia que afectan datos y modelo

1. **Comparación de 2013 ya ejecutada frente a textos antiguos.** INVEST, las celdas 14–16 y los artefactos anuales documentan la comparación. RECOG, PROV y NOTE conservan frases que aún la anuncian como futura. Se usa la evidencia ejecutada para describir el diagnóstico, sin afirmar que la causa o el tratamiento estén resueltos. Los otros documentos no se modifican en esta auditoría.
2. **Unicidad local frente a identidad global.** Los controles guardados permiten correspondencia por CONSECUTIVE en ciertos subconjuntos anuales; esto no resuelve su ámbito global ni prueba identidad de paciente. No es una contradicción que el diccionario mantenga esa semántica abierta.
3. **Escenarios distintos.** Los A–D ejecutados incluyen intercambio y referencia anual. Los 1–3 propuestos incluyen coincidencia año-mes. No se atribuye al nuevo escenario 2 evidencia producida para B. Los cálculos exploratorios de 784/42/7.730 requieren incorporación reproducible antes de usarse como resultados de tesis.
4. **Calibración descrita sin independencia demostrada.** V1 reporta calibración 2021–2022 y entrenamiento hasta 2022. Sin inspeccionar cómo se generaron las predicciones no se acredita independencia ni se declara fuga demostrada. La elección para V2 permanece abierta.
5. **Variables del periodo objetivo.** El reporte enumera `zona_objetivo` y percentiles del objetivo. Se debe revisar su construcción y disponibilidad; no se deduce seguridad ni fuga únicamente del nombre.
6. **Importancia y explicabilidad desactualizadas.** Los SHAP anteriores al reentrenamiento no describen necesariamente el modelo vigente; la importancia previa y la integración técnica no demuestran superioridad predictiva ni causalidad.
7. **Meses de exceso frente a inicios.** Y conceptual está respaldada. El comparador de inicio T+2 debe revisarse contra t+1 y no solo t; eso no convierte la regla propuesta en una aprobación de duración o reingreso de episodios.
8. **Agrupación por nombre y convención por código.** La norma científica exige identidad municipal por código; el resumen inicial del cuaderno todavía agrupa también por nombre. No se confunde la regla escrita con implementación integral.
9. **Coincidencia invertida no prueba intercambio.** El indicador de pares invertidos debe distinguir fechas iguales. Se registra el vacío de interpretación sin recalcular ni reinterpretar automáticamente todas sus observaciones.
10. **Privacidad y granularidad de origen.** La propuesta describe trabajo con datos agregados; el cuaderno parte de CSV individuales. No se presenta la unidad final municipio-mes como prueba de que el origen no contenga datos sensibles. Los resultados analíticos comunicados deben seguir agregados y sin ejemplos identificables.

## Cambios de esta auditoría

| Fecha | Cambio | Consecuencia científica |
|---|---|---|
| 2026-10-17 | Reducción del registro al análisis/tratamiento de datos y al diseño, desarrollo y evaluación del modelo. | Se reservan 18 códigos retirados por alcance; no se renumeran las decisiones científicas ni se presenta su salida como deprecación científica. |
| 2026-10-17 | Conservación de 46 entradas y ampliación con DEC-065–DEC-102. | Se incorporan antecedentes de variables, ceros, sustitución de fechas, particiones, calibración, ablación, alternativas y controles del diagnóstico. |
| 2026-10-17 | Separación entre decisiones aceptadas, propuestas, asuntos abiertos y prácticas implementadas solo en diagnóstico. | Una fuente, una ejecución o una solicitud de auditar no se convierten en aprobación de producción. |
| 2026-10-17 | Conservación del español, las fechas históricas conocidas y los vínculos de reemplazo. | La fecha de hoy se aplica al registro/auditoría sin fabricar aprobación original; en DEC-014/028/045 se corrige la atribución previa a una fecha general de fundamentos, que no acreditaba una aprobación estadística específica. |

Para un cambio posterior registrar: fecha, código, estado anterior/nuevo, evidencia de autoridad, razón, deprecación y sucesora cuando apliquen, e impacto sobre conteos, Y, variables, particiones, calibración y resultados que deban regenerarse. No se elige hoy un tratamiento de 2013, conjunto definitivo de variables, arquitectura ganadora o método de calibración.

## Actualización incremental PLAN_005 (2026-10-17)

Esta actualización agrega decisiones y estados específicos del estudio reproducible de sensibilidad mensual S1/S2/S3 y asociaciones temporales exploratorias del PLAN_005. No reabre decisiones cerradas previas ni convierte correlaciones en evidencia causal o predictiva concluyente.

| Código | Decisión | Estado | Reemplazada por |
|---|---|---|---|
| [DEC-103](#dec-103) | Reproducir y bloquear interpretación sin ajuste de cardinalidad anómala 2013 | ACEPTADA | No aplica |
| [DEC-104](#dec-104) | Escenarios S1/S2/S3 como análisis de sensibilidad exploratoria acotada | APLICADA_EN_DIAGNÓSTICO | No aplica |
| [DEC-105](#dec-105) | Controlar estacionalidad, tendencia y autocorrelación al contrastar asociaciones | APLICADA_EN_DIAGNÓSTICO | No aplica |
| [DEC-106](#dec-106) | Tratar asociaciones como candidatas y no como utilidad predictiva demostrada | ACEPTADA | No aplica |
| [DEC-107](#dec-107) | Mantener pendiente la reconstrucción as-of para evaluación operativa real | ABIERTA | No aplica |

<a id="dec-103"></a>
### DEC-103 Reproducir y bloquear interpretación sin ajuste de cardinalidad anómala 2013

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en ejecución de PLAN_005). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Toda comparación de sensibilidad debe iniciar con reproducción de 8.556 anomalías, 784 coincidencias año-mes y 7.772 diferencias año-mes; si falla, se documenta discrepancia antes de interpretar.
- **Justificación:** Evita interpretar sensibilidad con base en un conjunto mal definido o no reproducible.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** `data/interim/stage2_monthly_sensitivity_associations/anomaly_cardinality_summary.csv`; `anomaly_discrepancy_log.md`; notebook 02 sección 3.
- **Límites y validación pendiente:** Confirmar cardinalidad no resuelve por sí sola la causa de la inconsistencia ni autoriza correcciones automáticas.

<a id="dec-104"></a>
### DEC-104 Escenarios S1/S2/S3 como análisis de sensibilidad exploratoria acotada

- **Estado:** APLICADA_EN_DIAGNÓSTICO.
- **Fecha de decisión o incorporación:** 2026-10-17 (ejecución acotada en PLAN_005). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Ejecutar exactamente S1/S2/S3 y aplicar diferencias únicamente al grupo anómalo, manteniendo base municipio-mes comparable entre escenarios.
- **Justificación:** Permite cuantificar sensibilidad sin mezclar con tratamientos A-D anteriores ni alterar reglas del resto de registros.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** `monthly_panel_s1.csv`, `monthly_panel_s2.csv`, `monthly_panel_s3.csv`; `sensitivity_summary_by_geo.csv`; notebook 02 secciones 4-6.
- **Límites y validación pendiente:** Es evidencia exploratoria de sensibilidad; no selecciona una política definitiva de limpieza para producción.

<a id="dec-105"></a>
### DEC-105 Controlar estacionalidad, tendencia y autocorrelación al contrastar asociaciones

- **Estado:** APLICADA_EN_DIAGNÓSTICO.
- **Fecha de decisión o incorporación:** 2026-10-17 (ejecución acotada en PLAN_005). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Reportar asociaciones crudas y controladas, y acompañar inferencia exploratoria con multiplicidad y pruebas de permutación compatibles con dependencia temporal.
- **Justificación:** Reduce sobreinterpretación de correlaciones dominadas por estacionalidad/autocorrelación y explicita incertidumbre.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** `associations_raw.csv`; `associations_controlled.csv`; `associations_method_notes.md`; notebook 02 secciones 9-10.
- **Límites y validación pendiente:** No equivale a validación predictiva fuera de muestra ni a prueba causal.

<a id="dec-106"></a>
### DEC-106 Tratar asociaciones como candidatas y no como utilidad predictiva demostrada

- **Estado:** ACEPTADA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en PLAN_005). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Las asociaciones estables identificadas se usan solo para priorización de candidatos a evaluación posterior, sin declararlas utilidad predictiva probada.
- **Justificación:** Mantiene coherencia con el estado abierto de Y final, validación temporal y disponibilidad as-of.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** `associations_stability_summary.csv`; `DATA-02-monthly-sensitivity-associations.md`; notebook 02 sección 11.
- **Límites y validación pendiente:** Requiere protocolo de entrenamiento/validación temporal estricto antes de cualquier afirmación operativa.

<a id="dec-107"></a>
### DEC-107 Mantener pendiente la reconstrucción as-of para evaluación operativa real

- **Estado:** ABIERTA.
- **Fecha de decisión o incorporación:** 2026-10-17 (incorporación documental en PLAN_005). **Revisada el:** 2026-10-17.
- **Deprecada el:** No aplica. **Reemplaza a:** No aplica. **Reemplazada por:** No aplica.
- **Decisión, propuesta o práctica documentada:** Antes de evaluar desempeño operativo se debe reconstruir qué información estaba disponible en cada corte temporal, incluyendo maduración de reportes.
- **Justificación:** Los exportes retrospectivos consolidados pueden inducir optimismo si se usan como sustituto de disponibilidad histórica real.
- **Motivo de deprecación o no adopción:** No aplica.
- **Evidencia y autoridad:** `preflight_protocol.json`; notebook 02 secciones 12-13; `DATA-02-monthly-sensitivity-associations.md`.
- **Límites y validación pendiente:** Sin reconstrucción as-of, la evidencia actual permanece exploratoria y no operacional.

## Incremental PLAN_006 review (2026-10-18)

These entries update current evidence without rewriting historical approvals. See [DATA-03](../archive/experimental-eda/stage-2/DATA-03-panel-review.md) and [DATA-04](../archive/experimental-eda/stage-2/DATA-04-retrospective-use-rules.md). Stage 2/G2 remain open.

### DEC-108 Independent source joins and explicit territorial exceptions

Status: APPLIED_IN_DIAGNOSTIC. The 76-code grid independently retains dengue, severe and climate. Unknown 50000/73000 rows stay outside municipal analysis but inside reconciliation. All 4,598 identified severe rows are conserved, with 21 unknown-code rows reported separately. This supersedes the PLAN_005 panel as current analytical evidence; old outputs remain unchanged.

### DEC-109 Absence is not a certified zero

Status: APPLIED_IN_DIAGNOSTIC. Mauricio confirmed no further evidence of reporting interruptions or incomplete downloads. Numerical retained-row counts and nullable disease-count proxies are separate. No confirmed disease zeros or operational completeness are asserted. Scenario removal has its own state.

### DEC-110 Equal-date pairs do not demonstrate exchanged dates

Status: VERIFIED_DIAGNOSTIC; resolves the metric question in DEC-101. Original annual references were re-read: the 481/66/540 naive inverted pairs are all equal dates, with zero genuine unequal-date inversions. This supersedes the earlier swap-signal interpretation, not the unresolved cause of 2013 anomalies.

### DEC-111 Preserve 2013 scenarios and selected-sample association limits

Status: APPLIED_IN_DIAGNOSTIC; baseline policy subsequently selected by DEC-113 (2026-10-18). S1/S2/S3 remain historical sensitivity evidence; S1 is now the approved baseline treatment. The descriptive prior-year maximum comparison is not an endemic channel. Repeated associations use common observed support, explicit municipal/time controls and no self-conditioning. Prior inferential p-values and candidate rankings are not carried forward; no predictive utility or causality is established.

### DEC-112 Reproducible retrospective population and availability rules

Status: APPLIED_IN_DIAGNOSTIC; operational policy OPEN. Count source notification rows, keep streams separate, preserve original onset and do not infer patient identity or deduplicate. Historical as-of snapshots cannot be reconstructed from the available consolidated files. DATA-04 and `retrospective_rules.json` govern this review only; final population, maturation, eligibility, channel, Y and Data Contract remain open.


## Baseline decision and target clarification (2026-10-18)

<a id="dec-113"></a>
### DEC-113 Keep the supplied 2013 records unchanged for the baseline

- **Status:** ACCEPTED by Mauricio in the project conversation on 2026-10-18.
- **Decision:** Build the baseline with the 2013 records exactly as supplied. Do not delete, replace, exchange or reassign dates because of the 8,556 onset-after-notification anomalies. This selects S1 for the baseline.
- **Sequence:** Only after the baseline has been established may replacement or removal of those anomaly records be evaluated as separate experiments. The existing S2/S3 diagnostics remain historical evidence, not a modified baseline or authorization to run new experiments now.
- **Relationship:** Resolves the baseline-treatment question left open in DEC-111 and strengthens DEC-041. It does not establish which historical date is true. DEC-042's proposed reassignment is not adopted for the baseline.
- **Scope accounting:** The 8,556 anomalies refer to the original departmental audit. Of these, 8,524 have valid municipal geography in the reviewed panel; the other 32 remain in geographic exceptions. No record is newly excluded because its dates are anomalous; existing geographic/missing-date reconciliation remains explicit.
- **Effect:** Future baseline construction must use original supplied dates and no anomaly-based exclusion. Previous diagnostic outputs and input snapshots are preserved. No baseline model, new experiment or G2 approval is claimed by this documentation update.

### Existing target agreement — clarification, not a new definition

DEC-013 already accepts distinct T+1/T+2 forecasts; DEC-035 accepts binary future excess above the applicable historical limit; DEC-038 accepts special evaluation of new outbreak onsets. These agreements remain authoritative. The assistant's subsequent checklist described Y too broadly as undefined. DEC-037 still records the operational channel method/window/seasonal reference and count construction as open; DEC-039 records the exact onset-transition rule as proposed. Historical P75 in DEC-036 is not automatically an approved V2 parameter. No existing target decision is revoked or silently promoted by this clarification.


## User observations and operational proposals (2026-10-18)

<a id="dec-114"></a>
### DEC-114 No duplicate-case removal without precise evidence

Status: ACCEPTED working assumption, explicit human instruction on 2026-10-18. For the baseline, assume no demonstrated duplicate cases and preserve supplied notification rows. Do not eliminate cases based on suspected identity or repeated export identifiers alone. This is a preparation rule, not an empirical proof of patient/episode uniqueness. Revisit only if precise evidence becomes available. No current row is removed by this decision.

<a id="dec-115"></a>
### DEC-115 Rely on supplied observations without inventing reporting interruptions

Status: ACCEPTED, explicit human instruction on 2026-10-18. Use available records; do not infer municipal reporting cessation or exclude municipalities on that unsupported assumption. Do not estimate or fabricate unreported cases. Completeness is unverified, not a demonstrated reporting failure. A zero retained-row count describes the export; it does not certify that no disease occurred. Existing geographic/date exceptions remain separately reconciled. This decision alone does not supply a disease-zero rule, final modeling eligibility threshold or an imputation policy.

<a id="dec-116"></a>
### DEC-116 User-reported climate construction and reconstruction option

Status: SOURCE_ACCOUNT_RECORDED. Mauricio states that the climate file was constructed by downloading Google Earth Engine information and linking municipalities through DIVIPOLA codes. This supplies human provenance evidence, not independent verification of the exact generating run, products/versions, spatial aggregation, conversions or missing January 2020. Rebuilding/enriching the climate dataset is an available option if necessary; no new download, source replacement or expanded climate experiment is initiated by this entry.

### Target specification clarification from the supplied screenshot

The screenshot reiterates the existing agreement: for municipality m and horizon h in {1,2}, Y(m,t,h)=1[C(m,t+h)>U(m,t+h)]. C is the monthly count under an agreed case-population rule; U is the applicable historical excess limit. Y=0 applies when both quantities are defined and C does not exceed U; an unknown count/limit is not automatically Y=0. The model estimates the probability of excess, rather than directly producing the historical label.

The documented candidate new-onset evaluation is Inicio(m,s)=1[Exceso(m,s)=1 and Exceso(m,s-1)=0]. Thus T+2 onset compares t+2 with t+1. Preserve DEC-039's proposed operational status: the screenshot is a prior assistant explanation, not independent human approval of every persistence/re-entry/unknown-state rule. DEC-035/038 remain accepted. The notification-classification population for C is now resolved by DEC-118: include all supplied classifications. Remaining construction choices are the method and seasonal/history window for U (P75 is a V1 precedent), and allowed history at each temporal evaluation cutoff. The 2013 baseline treatment is now resolved by DEC-113. The case-count limit U is separate from the probability threshold used to issue an alert.

<a id="dec-117"></a>
### DEC-117 Re-run forecasts when uploaded historical data change

Status: USER_PROPOSAL_RECORDED; detailed product behavior not yet frozen. Mauricio proposes an initial run on the morning of the first day of the month and re-execution when prior-month records change, conditional on minimum input quality. Re-running should apply whether the preceding result showed an alert or not. No monotonicity guarantee exists: additional rows, corrections, changed features or a revised reference can increase, decrease or preserve predicted risk. A recommendation is to retain each input version, execution time and horizon-specific output so revisions remain inspectable. No new alert-latching policy, retraining schedule or operating cutoff is approved here.

Re-execution addresses updates after deployment; it does not reconstruct the incomplete files that a historical user would have possessed. Consolidated retrospective evaluation remains distinct from a real-time simulation. Future saved input snapshots could provide evidence for that later evaluation. These limitations do not require estimating the unknowable number of unreported cases now.


<a id="dec-118"></a>
### DEC-118 Include all supplied records in the baseline population

- **Status:** ACCEPTED. Explicit instruction from Mauricio on 2026-10-18: use ALL records; omit none based on case classification.
- **Rule:** Include probable, laboratory-confirmed and epidemiological-link-confirmed notification rows. Do not apply a confirmed-only filter, nor discard records because TIP_CAS, AJUSTE, Estado_final_de_caso, nom_est_f_caso or confirmados indicates a non-confirmed classification. Preserve supplied records and their original values. Keep dengue and severe-dengue streams separate; this does not authorize summing them as unique patients.
- **Relationship:** Resolves the probable-versus-confirmed baseline population choice. Complements DEC-113 (unchanged 2013), DEC-114 (no unsupported duplicate removal) and DEC-115 (rely on supplied observations). Earlier statements that this classification choice remains open are superseded.
- **Accounting:** All supplied rows remain preserved and reconciled. The established Tolima/Meta residence scope remains in effect; rows outside it are not silently attributed to the study municipalities. Rows without usable geography or onset remain visible in separate reconciliation, rather than being deleted or assigned invented municipality/month values. Therefore inclusion of all source records does not imply that every record can contribute to a valid municipality-month count.
- **Implementation status:** The reviewed S1 panel already counts both probable and confirmed rows without a confirmation filter. This update records the approved population; it does not rerun a model or alter the source snapshots. No new assumptions are made about codes absent from these supplied snapshots. Channel construction and G2 remain open.


<a id="dec-119"></a>
### DEC-119 Adopt the INS median-and-percentile channel family for excess

- **Status:** ACCEPTED. Explicit instruction from Mauricio on 2026-10-18 selects the official median-and-percentile endemic-channel method documented by INS, with excess strictly above P75. This resolves method-family selection; do not substitute Bortman or its upper 95% confidence limit.
- **Primary evidence verified:** INS, Dengue event report, epidemiological period IV of 2023, page 3, technical epidemiological component, paragraph “Canales endémicos”: [official report](https://www.ins.gov.co/buscador-eventos/Informesdeevento/DENGUE%20PE%20IV%202023.pdf). The report distinguishes the median/percentile P75 boundary from the Bortman upper confidence boundary.
- **Relationship to prior approval:** Retain the initial project configuration approved in the “Plan SAT-Dengue V2” conversation and recorded in draft PR #9: municipality-month counts, same calendar month from five complete historical calendar years available at cutoff T, epidemic years included, T+1/T+2, and 5/7/9-year sensitivity. All supplied case classifications remain included under DEC-118; 2013 remains unchanged under DEC-113. The detailed PR #9 record still requires reconciliation with this local register; no merge is performed here.
- **Scope precision:** The cited INS report uses weekly historical observations from 2015–2022 excluding 2016 and 2019. The project's monthly five-year history including epidemic years is an explicitly approved adaptation of the percentile-channel approach, not an exact reproduction of that report's configuration and not an INS-prescribed monthly five-year standard.
- **Numerical precision:** This report identifies the P25/median/P75 reference boundaries but supplies no explicit sample-percentile rank/interpolation formula or software setting. The selected epidemiological method is approved; an implementation convention must not be described as an official INS numerical algorithm without further supporting specification. No competing method is selected by this note.
- **Validation status:** Documentary method/threshold verified. No channel computation, target sensitivity, source modification, new input-data policy or G2 approval is claimed. Insufficient-history handling remains governed by the approved non-evaluable principle and must be specified consistently for implementation.


<a id="dec-120"></a>
### DEC-120 Represent no-case months as zero in the baseline

- **Status:** ACCEPTED. Explicit human decision from Mauricio on 2026-10-18: a month with no cases is filled with zero (“no hubo casos”).
- **Operational baseline rule:** Within the supplied epidemiological coverage and established municipal study scope, represent a municipality-month with no source case records as count 0, relying on the supplied dataset under DEC-115. Apply separately to dengue and severe-dengue counts; preserve all original records under DEC-118. Create zero aggregate counts, not fabricated individual patient records.
- **Interpretation:** This is the project's approved counting assumption for the supplied baseline, not independent certification of complete surveillance or absence of unreported disease. Keep the no-source-rows provenance identifiable; no additional completeness evidence is required to apply the approved baseline convention.
- **Historical reference:** In a five-year same-month reference, a covered no-case month contributes a valid numeric zero. It does not make the five-value history incomplete. Months outside the supplied coverage, genuinely unavailable inputs and records without assignable municipality/onset are not made observable by this rule. Retain the non-evaluable principle if the required historical reference cannot be constructed.
- **Boundaries:** Do not zero-fill missing climate; January 2020 remains a climate gap pending recovery. Do not confuse records removed by a sensitivity experiment with months that originally had no cases. Preserve the separate records/accounting for unassignable geography/onset. Do not infer the coverage start of a municipality solely from its first positive case.
- **Relationship:** Supersedes the baseline prohibition on converting no-record covered epidemiological months to zeros in DEC-109 and the corresponding unresolved baseline choice in DEC-115. The earlier PLAN_006 unknown-state outputs remain historical evidence of the prior policy.
- **Implementation/evidence:** This entry records the approved rule. Existing PLAN_006 panels and association results have not been regenerated. Future baseline/target construction must implement the zero counts, preserve source reconciliation and validate eligibility/labels anew; prior observed-positive association results must not be presented as covering the new zero-inclusive population. No G2 approval is claimed.


---

## PR #9 source document — preserved original

The following complete upstream document is retained as source evidence. Its original integration warning and pending-classification/zero assumptions describe the pre-reconciliation state. The current-status table above and DEC-121 below state their present disposition; the original text is not a competing current policy.

# Seguimiento de conclusiones y decisiones — SAT-Dengue V2

> **Nota de integración (18-10-2026):** este archivo se crea como propuesta versionada porque `docs/product/traking-concluciones.md` **no existe en la rama `main` consultada**. Se ha informado de una versión de trabajo local del mismo nombre. **Antes de integrar el PR, reconciliar este contenido con el archivo local y preservar todas sus conclusiones previas.** Este documento no pretende reemplazar ni invalidar el historial local.

## Decisión DEC-Y-2026-10-18-01 — Configuración inicial aprobada de la variable objetivo Y

- **Fecha de aprobación:** 18 de octubre de 2026.
- **Aprobación:** expresa del responsable del proyecto en conversación de seguimiento.
- **Etapa:** Stage 2 — Data Understanding.
- **Estado de la decisión:** **APROBADA como configuración inicial de referencia**; la sensibilidad, los criterios de evaluabilidad y la formalización computacional permanecen pendientes.
- **Alcance:** clasificación binaria de exceso epidemiológico de dengue por **municipio × mes**, con predicción **T+1 y T+2**.
- **No implica:** aprobación del Gate G2, entrenamiento de modelos, selección de umbrales de alerta operativa ni declaración oficial de brote.

### 1. Configuración aprobada

| Parámetro | Decisión aprobada | Precisión |
|---|---|---|
| Unidad geográfica | **Municipio**, identificado mediante código DIVIPOLA | Ámbito del proyecto: Tolima y Meta. |
| Unidad temporal | **Mes calendario** | El panel objetivo se define a escala municipio-mes. |
| Resultado observado | **Conteo mensual de casos de dengue**, según la regla de inclusión de registros del proyecto | Se conserva **2013** y no se excluyen registros/años epidémicos por defecto. La validación de duplicados y la calidad de datos siguen siendo requisitos independientes. |
| Variable objetivo | **Binaria**: `Y=1` exceso; `Y=0` sin exceso | Si la etiqueta no puede evaluarse con datos válidos, **no** se codifica como cero. |
| Canal de referencia | **Percentil 75 (P75)** del histórico | Se utiliza el método de percentiles, **no** el límite superior de Bortman. |
| Regla de decisión | **Exceso si y solo si casos observados > P75** | La igualdad al umbral se clasifica `Y=0`. |
| Ventana histórica inicial | **Cinco (5) años calendario completos**, históricos y disponibles al corte de predicción | La ventana se determina retrospectivamente para cada corte `T`, sin incluir periodos futuros. |
| Agrupación estacional | **Mismo mes calendario** de cada uno de los cinco años de referencia | Enero contra eneros, abril contra abriles, etc.; no agrupar los 12 meses indiscriminadamente. |
| Años epidémicos | **Se incluyen**; no excluir 2013, 2016, 2019, 2023 ni otros años por su condición epidémica | Las exclusiones solo podrían justificarse posteriormente por un problema de calidad demostrado y documentado, no por el resultado de la etiqueta. |
| Actualización | **Recalcular el canal en cada corte temporal** usando exclusivamente historia disponible en ese momento | Obligatorio para evaluación retrospectiva con ventana expansiva y uso prospectivo. |
| Horizontes | **T+1** y **T+2** meses | Ambos se predicen desde el mismo corte `T`. |
| Sensibilidad prevista | **5 años (referencia aprobada) frente a 7 y 9 años** | No cambia la configuración de referencia por sí sola; cualquier revisión requerirá nueva decisión explícita. |

**Alcance de la aprobación:** se aprueba **5 años + mismo mes + P75 + inclusión de años epidémicos** como configuración **inicial**. No se afirma que sea el óptimo empírico para todos los municipios.

### 2. Definición formal de Y y restricción anti-leakage

Sean:
- `m`: municipio DIVIPOLA.
- `T`: mes de corte desde el que se emite la predicción.
- `h ∈ {1, 2}`: horizonte de meses futuros.
- `C(m,T+h)`: conteo observado y validado de casos del municipio `m` en el mes objetivo.
- `H5(m,T+h | T)`: conjunto de **cinco conteos históricos** del **mismo mes calendario** que `T+h`, correspondientes a los **cinco años calendario completos** elegibles según información disponible al corte `T`.
- `P75(H5)`: percentil 75 de esos cinco conteos.

Entonces, para periodos **evaluables**:

```text
Y(m,T+h | T) = 1  si C(m,T+h) > P75(H5(m,T+h | T))
Y(m,T+h | T) = 0  si C(m,T+h) <= P75(H5(m,T+h | T))
Y(m,T+h | T) = NA si no existe observación válida o histórico suficiente
```

**Ejemplo estacional:** para un corte en marzo de 2024 y objetivo abril de 2024, los cinco abriles de referencia son **abril de 2019, 2020, 2021, 2022 y 2023**, siempre que esos datos fueran válidos y estuvieran disponibles en marzo de 2024. No utilizar abril de 2024 para calcular su propio umbral.

**Regla temporal vinculante:** la construcción del umbral de T+1 y T+2 **no puede usar casos de T+1/T+2 ni datos publicados o corregidos después de T como si hubieran estado disponibles en T**. El conteo observado del mes objetivo se consulta **solo después**, para asignar la etiqueta de evaluación; nunca se introduce como predictor en T.

**Interpretación de «años completos»:** usar cinco años calendario **cerrados y disponibles al corte T**, no una ventana móvil de 60 meses indiferenciada. La regla de corte, cierres anuales y rezagos de publicación debe codificarse de forma determinista en el contrato de datos. No asumir disponibilidad instantánea de SIVIGILA.

### 3. Inicio frente a continuación: clasificación retrospectiva

La etiqueta principal es exceso `Y`; **inicio/continuación** es una clasificación secundaria del episodio, no una segunda definición de P75.

| Horizonte evaluado desde T | Inicio | Continuación |
|---|---|---|
| T+1 | `Y(T)=0` y `Y(T+1)=1` | `Y(T)=1` y `Y(T+1)=1` |
| T+2 | `Y(T+1)=0` y `Y(T+2)=1` | `Y(T+1)=1` y `Y(T+2)=1` |

La evaluación retrospectiva de inicio en **T+2** requiere el estado observado de **T+1**. Ese estado es futuro respecto a T y **no debe utilizarse como predictor** en T. Los umbrales usados para estados de meses consecutivos deberán aplicar una política temporal consistente, que se documentará en el contrato.

### 4. Evidencia documental y alcance de cada fuente

| Fuente | Qué respalda | Qué **no** demuestra |
|---|---|---|
| **Notas de sesión con experto**, sección 5, `Sesion_1_con_Experto_Notas.docx` | Objetivo binario exceso / no exceso y comparación con canal endémico. | No fija cinco años ni una agrupación mensual exacta. |
| **Reporte de Entrega 3**, sección 2.1, `Reporte_Entrega3_final-2.docx` | Criterio `casos > P75` para horizonte futuro; T+1/T+2. | No determina la ventana histórica del P75. |
| **Propuesta de grado**, sección 10, `Formato-propuesta_Proyecto-de-grado-Mauricio.pdf` | Validación temporal con ventana expansiva y parámetros recalculados solo con historia permitida; distinción inicio/continuación. | Ventana expansiva **no equivale** a cinco años del canal. |
| **INS (2023), Informe de evento: Dengue, periodo epidemiológico IV**, [PDF oficial](https://www.ins.gov.co/buscador-eventos/Informesdeevento/DENGUE%20PE%20IV%202023.pdf) | Antecedente institucional de canal por medianas/percentiles con límite P75; referencia **semanal** y selección histórica 2015–2022 con exclusión de 2016 y 2019 en ese informe. | **No prescribe** para este proyecto un canal P75 **mensual de cinco años**; otros métodos del INS usan límites distintos. |
| **Umaña y colaboradores (2026)**, *Endemic Channel Parametrization in Dengue Surveillance: Methodological Assessment of Retrospective Windows, Outbreak Trends, and Zero-Case Periods in Colombia*, [artículo](https://publichealth.jmir.org/2026/1/e79914), [DOI](https://doi.org/10.2196/79914) | Relevancia metodológica de la ventana retrospectiva, años epidémicos y periodos de cero casos; se estudiaron ventanas de 5–9 años. | Sus resultados se centran en **Bortman**; **no prueban** que cinco años sea óptimo para P75 mensual municipio-mes. |
| **Registro documental de brotes** (PR #8), [documento](https://github.com/j-mauro-r/SAT-Dengue-V2/pull/8) | Casos externos para contextualización y validación cualitativa. | La fecha de una noticia, alerta o decreto **no es** automáticamente el primer mes con `Y=1`. |

**Fundamento de la selección:** el uso de **P75** proviene de la documentación del proyecto y tiene antecedente oficial; **cinco años y agrupación por mismo mes** son **decisiones metodológicas explícitas del proyecto**, compatibles con las referencias, no una regla nacional obligatoria. La elección inicial se aprueba por criterio del responsable y deberá someterse a sensibilidad.

### 5. Condiciones aún no cerradas (no suponer resueltas)

1. **Convención exacta del percentil:** método de interpolación, manejo de empates y resultado con solo cinco observaciones. Debe quedar fijado y probado para reproducibilidad.
2. **Meses sin registros:** ausencia de notificaciones **no equivale automáticamente a cero**. Resolver continuidad y elegibilidad municipal antes de asignar `Y=0`.
3. **Histórico incompleto:** establecer mínimo de años válidos, qué hacer si falta uno o más de los cinco valores, y desde qué fecha un municipio es evaluable. No imputar ni rellenar silenciosamente.
4. **Baja transmisión:** cuantificar la frecuencia de `P75=0` y el caso de un solo registro que activa exceso; documentar comportamiento por municipio.
5. **Disponibilidad as-of:** definir la fuente y fecha efectiva de disponibilidad, revisiones de datos y criterio de cierre del mes. La ausencia de instantáneas históricas de notificación limita lo que puede probarse sobre disponibilidad real.
6. **Conteo y trazabilidad:** documentar inclusión de tipos de dengue, duplicados, municipios desconocidos, fechas `INI_SIN`/`FEC_NOT`, y calidad de registros, incluyendo la investigación de inconsistencias de 2013.
7. **Coherencia de estados consecutivos:** formalizar cómo se calculan `Y(T)`, `Y(T+1)` y `Y(T+2)` para clasificar inicio/continuación sin introducir referencias futuras.

### 6. Validación de sensibilidad acotada, antes del Target Freeze

**Objetivo:** evaluar estabilidad de la configuración aprobada sin entrenar modelos ni alterar el umbral P75.

| Variante | Ventana histórica | Agrupación | Umbral | Uso |
|---|---:|---|---|---|
| **A — referencia aprobada** | **5 años** | Mismo mes | **P75** | Base de comparación. |
| B | 7 años | Mismo mes | P75 | Sensibilidad. |
| C | 9 años | Mismo mes | P75 | Sensibilidad. |

**Salidas mínimas:** cobertura de municipio-mes evaluables y no evaluables; proporción de meses `Y=1`; cambios de etiqueta respecto a A; número y distribución de inicios/continuaciones; casos `P75=0`; análisis por municipio y nivel de transmisión. Mantener constantes fuente, conteo, criterios de calidad y política temporal. **No entrenar modelos** en esta actividad.

**Regla de gobernanza:** A es la configuración inicial **aprobada**. Los resultados de B/C no la sustituyen automáticamente; cualquier cambio requiere justificación y nueva aprobación explícita.

### 7. Estado de cierre de Stage 2

- **Definición conceptual de Y:** **APROBADA**.
- **Regla estricta `conteo > P75`:** **APROBADA**.
- **Configuración inicial `5 años / mismo mes / sin excluir años epidémicos`:** **APROBADA**.
- **Horizontes T+1 y T+2:** **APROBADOS**.
- **Validación de sensibilidad y condiciones de evaluabilidad:** **PENDIENTES**.
- **Contrato de datos/objetivo, controles anti-leakage y evidencia del Gate G2:** **PENDIENTES**.
- **Gate G2 — Data & Target Freeze:** **NO APROBADO**.

**Próxima acción mínima:** documentar la convención exacta de P75 y las reglas de meses no observados/histórico insuficiente; luego ejecutar una única sensibilidad controlada 5/7/9 años y revisar los resultados antes del freeze.

---

*Registro de decisión: la aprobación se refiere a la **configuración inicial** y no constituye certificación de desempeño ni clasificación epidemiológica oficial del INS.*


---

<a id="dec-121"></a>
### DEC-121 Reconcile approved Y configuration and preserve all decision histories

- **Status:** APPROVED_CONFIGURATION_RECONCILED on 2026-10-18. The explicit approval by Mauricio in “Plan SAT-Dengue V2” is recorded in PR #9 under DEC-Y-2026-10-18-01. This reconciliation preserves its full text and the existing local register, including DEC-119/120. No new scientific parameter is selected here.
- **Imported approved choices:** Binary future excess; P75; same calendar month; all epidemic years including 2013; strict greater-than rule; T+1/T+2; sensitivity against seven and nine years. Historical reference interpretation is clarified in DEC-122 as five same-month observations from the five years prior to target year.
- **Supersession:** Resolves method/window/seasonal uncertainty in DEC-037/111/112 and earlier explanatory notes to the extent covered by this approval. DEC-119 selects the INS percentile-channel family. DEC-118 resolves case classifications. DEC-114 prohibits unsupported duplicate removal. DEC-120 supersedes the baseline unknown-versus-zero question for covered no-case months. Missing climate and genuinely unavailable historical observations are not filled by DEC-120.
- **Outstanding implementation/evidence:** Document a deterministic numerical percentile convention, coverage/insufficient-history handling and consistent reference for consecutive states. Implement the approved policy and perform the 5/7/9 comparison; it is approved work, not completed evidence. Prior PLAN_006 artifacts preserve their original unknown-state population and are not evidence for an unexecuted zero-inclusive target.
- **External research:** PR #8's full source-linked outbreak inventory is preserved unchanged in docs/research/colombia-dengue-outbreak-events.md. It supplies context/qualitative checks, not automatic training labels or first-onset dates.
- **Git disposition:** Main, PR #8 and PR #9 histories are integrated into Stage2/Data-Understanding for PR #10. Original refs and all source-file bytes are privately backed up. The PRs are not closed or merged into main by this work. This is documentary reconciliation, not approval of G2 or predictive performance.


<a id="dec-122"></a>
### DEC-122 Clarify same-month historical reference without whole-year closure requirement

- **Status:** ACCEPTED_CLARIFICATION on 2026-10-19 by explicit instruction from Mauricio during Stage 2 follow-up.
- **Clarified rule:** For a target period `T+h` (YYYY-MM), build the historical reference with the same month `MM` from the five years immediately prior to target year (`YYYY-5` .. `YYYY-1`).
- **Interpretation boundary:** This clarification supersedes wording that could be read as requiring each full historical calendar year to be fully completed before using that year's same-month observation. Month-level closure of each referenced period is sufficient under this retrospective consolidated dataset context.
- **Example:** Cutoff November 2024, horizon `T+2`, target January 2025 -> reference months January 2020, 2021, 2022, 2023 and 2024.
- **Non-substitution rule:** If one required same-month historical observation is genuinely missing, keep the label non-evaluable; do not silently backfill with an older year.
- **Retrospective limitation:** This project uses consolidated retrospective data. Temporal ordering of the computation does not prove historical operational availability of each value version at real-time cutoff.
- **Relationship:** Refines DEC-121 wording and keeps DEC-119 method-family, DEC-120 zero-in-coverage rule and DEC-118 inclusion policy unchanged.


### DEC-123 Approve Stage 4 selection and corrective evaluation policy

- **Status:** ACCEPTED by Mauricio's explicit corrective instruction on 2026-10-20.
- **Decision:** Correct non-interpolated AP by distinct score thresholds and evaluate onset from observed excess at exactly S/S−1, including context before the validation boundary. Unknown scientific context remains explicit; prediction failures cannot improve sensitivity by shrinking true-event denominators. Retrospective states are evaluation-only.
- **Selection:** Technical eligibility first; inner-training mean AP, then Brier, then predeclared within-family simplicity. Fixed external candidates use equally weighted mean AP across four windows, with separate horizon rankings and accompanying Brier/temporal/territorial evidence. No arbitrary event-metric composite, repeated external tuning or final-block use. Stage 4 ranking is not an approved champion.
- **Owner:** Executable numerical tie tolerance, family-specific simplicity rules and boundary details live in `docs/product/stage-4/model_engineering_contract_v1.json` and its existing README; do not maintain a second implementation here.
- **Scope:** Authorizes correction, reference regeneration, meaningful tests, independent review and same branch/PR #15 update. No candidate training, Y/channel/population/window/source changes, EDA, merge or automatic G2/G3/G4 approval. PLAN_020 approval and old metric artifacts remain historical; this correction supersedes affected evaluation results.


---

## Stage 5 research protocol — approved for implementation, 2026-10-20

**Authority and execution state:** Mauricio explicitly requested creation of the Stage 5 branch and registration of DEC-124–129 on 2026-10-20. Those decisions record the research protocol; they are not assistant suggestions treated as approval by silence. PLAN_027 completed the corrected development pipeline at commit 85a315c. DEC-130/131 record the later six-procedure proposal and gated implementation. On 2026-10-21, DEC-132 records Mauricio's explicit G4, exact-protocol and final-execution authorization and the resulting reserved evaluation. The working branch is `Stage5/Model-Evaluation`, created from the clean `Stage4/Model-Engineering` HEAD `c8daf08f613340e86170f0fbbbbb6ce60a20c4b4`. G2/G3/G5 remain unapproved; no champion, deployment or merge is authorized.

<a id="dec-124"></a>
### DEC-124 Freeze Stage 5 research scope and alert meaning

- **Status:** ACCEPTED_RESEARCH_PROTOCOL on 2026-10-20 by the explicit registration instruction above.
- **Decision:** Preserve approved Y/channel rules (DEC-118–122), features, three candidate families (XGBoost, LightGBM, GAM), references and scientific population from Stage 4. Evaluate T+1 and T+2 separately. Do not reopen EDA, add model families or change labels to improve scores.
- **Alert meaning:** A thresholded prediction is a warning of excess in its exact target month, supporting review/preparedness. It is not an official outbreak declaration or an automatic intervention. Future excess may be a continuation; reporting a correct excess alert does not prove detection of a new onset.
- **Onset boundary:** Keep the approved observed-state transition at target S and exactly S−1, separately from the excess label. Do not train an onset target or inject those future states into X.
- **Limitation:** Consolidated retrospective data and correct calendar ordering do not establish historical real-time publication/revision availability. G4 acceptance remains separate from technical completion.

<a id="dec-125"></a>
### DEC-125 Set provisional research utility criteria

- **Status:** ACCEPTED_RESEARCH_PROTOCOL on 2026-10-20; pilot research criteria, not deployment requirements.
- **Decision:** For each horizon, require an absolute improvement of at least **0.10 (10 percentage points)** in onset sensitivity over persistence, while allowing at most **0.05 (5 percentage points)** additional false-alert ratio relative to persistence on the same evaluation cohorts. These are differences in proportions, not relative percentage increases. Preserve predeclared window weighting and evaluability rules; do not change aggregation after viewing results.
- **Definitions:** Onset sensitivity is detected evaluable new onsets / all evaluable real new onsets, with DEC-123 missing-prediction safeguards. False-alert ratio is alerts whose target Y is 0 / all emitted alerts. A correctly predicted continuation is not a false excess alert, but is not a detected onset. Unknown outcomes are not negatives. No emitted alerts makes the false-alert ratio unavailable, not zero; such a policy cannot pass by avoiding all warnings. An absent onset denominator remains unavailable.
- **Rationale and authority:** Ten percentage points is an explicitly proposed project-level minimum research gain, not a literature/INS standard or proof of health-service adequacy. The five-point allowance adapts SRC-P section 10's pending proposal, now explicitly using persistence and the false-alert-ratio denominator. It does not copy a false-positive-rate bound or promise the Colombian EWARS results.
- **Relationship:** Supersedes DEC-061's pending utility-criterion wording only for this Stage 5 research protocol. It does not adopt every metric in DEC-061, silently substitute a separately defined channel forecast, or alter the Stage 4 selection policy. No independent channel comparator is presumed to exist merely because persistence uses the current channel state.
- **Acceptance boundary:** A ten-point gain can still be operationally insufficient, particularly against a weak baseline. Report event counts and uncertainty. Insufficient evidence is an allowed conclusion; deployment needs separate agreement with the health-service user on missed events and unnecessary actions.

<a id="dec-126"></a>
### DEC-126 Evaluate original and sigmoid-calibrated probabilities

- **Status:** ACCEPTED_RESEARCH_PROTOCOL on 2026-10-20; no calibrator fitted by this registration.
- **Decision:** Compare unchanged probabilities against a sigmoid (Platt-style) correction by candidate/horizon. Use Brier and reliability curves with sample/event support; retain a correction only when independently evaluated development evidence supports it. No automatic calibration or flexible-method search is authorized.
- **Interpretation:** Brier measures overall probabilistic error, not calibration alone. Curves compare predicted probabilities with observed excess frequencies; small municipal samples cannot establish precise calibration. Maintain original probabilities and provenance alongside any corrected version.
- **Temporal control:** Calibrator fitting must use out-of-time predictions from models that did not fit those outcomes. Selection and evaluation of calibration remain separated under DEC-127. Do not reuse V1 thresholds or confuse EWARS configuration tuning with probability calibration.
- **Relationship:** Resolves DEC-081's conceptual independence requirement for this protocol; the executable split schedule and calibration acceptance/tie details must be fixed in the future Stage 5 contract before execution. DEC-062's empirical model/calibrator choice remains open until evidence exists.

<a id="dec-127"></a>
### DEC-127 Select alert thresholds within temporal development

- **Status:** ACCEPTED_RESEARCH_PROTOCOL on 2026-10-20; no numerical probability threshold selected.
- **Decision:** Select one probability threshold per candidate/horizon, initially shared across municipalities. Maximize onset sensitivity subject to the DEC-125 false-alert constraint in permitted development data. Break equal-sensitivity choices by fewer false alerts; declare no feasible policy when none meets the constraint. Do not impose 0.5 or copy published EWARS/V1 thresholds.
- **Chronology:** Predeclare temporal roles for base-model training, calibration fitting, threshold selection and subsequent evaluation. Labels used in any adjustment must be observable by its adjustment cutoff; prediction origins must not precede the fitted system's availability. Fit all learned preprocessing within the corresponding training subset. Do not use random folds.
- **Evaluation boundary:** Existing Stage 4 external windows and their `evaluation_context.csv` remain evaluation-only and must not become threshold/calibrator fitting inputs. A future Stage 5 contract must explicitly define permitted historical development context for onset-based threshold selection, separate from external evaluation context and X. Do not reinterpret this decision as permission to tune on prior external results.
- **Remaining implementation detail:** Specify exact split dates, threshold candidate/tie conventions and artifact identity/reuse before running the bounded DWP implementation. This is implementation preparation, not permission to alter existing scientific cohorts.

<a id="dec-128"></a>
### DEC-128 Compare candidates with existing metrics and support

- **Status:** ACCEPTED_RESEARCH_PROTOCOL on 2026-10-20.
- **Decision:** Retain four core metrics: grouped-tie non-interpolated AP, Brier, onset sensitivity and false-alert ratio. Preserve DEC-123's separate-horizon, equal-window AP ranking, with utility qualification reported separately under DEC-125; the highest-AP candidate need not be operationally eligible. Do not create a weighted composite or an arbitrary cross-family complexity score.
- **Evidence:** Report all declared periods, departments and municipalities with selected population, emitted alerts, evaluable outcomes and real/detected onset counts. Report unavailable metrics explicitly, including one-class AP and missing-context cases; never improve a ranking by silently dropping difficult windows or territories. Quantify uncertainty with dependence-aware methods specified before execution, rather than treating all municipality-month rows as independent.
- **Stability:** Examine period and territorial variability without fitting 76 local thresholds/calibrators on small samples. Previously inspected Stage 4 development results are not a newly untouched test. This decision does not expand the scientific population or permit repeated external hyperparameter tuning.

<a id="dec-129"></a>
### DEC-129 Freeze the selected protocol before reserved evaluation

- **Status:** ACCEPTED_RESEARCH_PROTOCOL on 2026-10-20; the separately authorized execution is recorded in DEC-132.
- **Decision:** Freeze selected candidate, preparation, calibration, alert threshold, temporal evaluation/update policy and acceptance rules before opening the final target-period block starting **2025-01**. Maintain separation by target period for both horizons, including rows originating before 2025 whose targets fall in the reserved block.
- **Outcome:** Evaluate the frozen procedure and classify the evidence as meets criteria, does not meet criteria, or insufficient evidence. Do not adjust/reselect on the reserved outcomes or call the same block untouched again after inspecting it. Research closure may conclude that no candidate qualifies; it need not produce a champion.
- **Human boundary:** Research utility is distinct from operational authorization. Record unresolved real-time availability limitations and any required prospective pilot. Acceptance/approval of G4/G5, deployment and merge remain human decisions, not consequences of this branch or passing tests.

### Evidence supporting DEC-124–129

The sources below support the evaluation design and contextual limitations. None establishes our 10-point improvement or 5-point allowance as a universal standard; the numeric research criteria derive from the explicit project decision in DEC-125.

| Source | Contribution and transfer limit |
|---|---|
| SRC-P, proposal section 10; historical DEC-061 | Temporal reserved evaluation, onset counts, probability calibration, and a proposed five-percentage-point false-alarm allowance. The reference and denominator are made explicit by DEC-125 rather than assumed interchangeable. |
| [Schlesinger et al. (2024), Colombia EWARS-csd](https://www.frontiersin.org/journals/public-health/articles/10.3389/fpubh.2024.1323618/full) | Municipality-dependent sensitivity/PPV trade-offs; weekly hospitalization outcomes and optimal retrospective configurations are not directly transferable to our monthly onset assessment. |
| [Hussain-Alkhateeb et al. (2018), EWARS including Brazil](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0196811) | Local alarm settings and joint sensitivity/PPV assessment; published probability cutoffs are not defaults for V2. |
| [Infodengue-Mosqlimate 2025 protocol, Brazil](https://sprint.mosqlimate.org/sprint/2025/) | Explicit historical cutoffs, season-specific validation and a separate true forecast; case-curve forecasting differs from our binary target. |
| [Van Calster et al. (2019), probability calibration](https://link.springer.com/article/10.1186/s12916-019-1466-7) | Reliability assessment, adequate sample support and limitations of apparent discrimination; clinical-model guidance is methodological evidence, not a dengue alert threshold. |
| [scikit-learn 1.7 calibration documentation](https://scikit-learn.org/1.7/modules/calibration.html) | Disjoint calibration fitting, sigmoid/isotonic trade-offs, and distinction between Brier and calibration alone. |
| [Campbell et al. (2026), operational D-MOSS evaluation](https://journals.plos.org/globalpublichealth/article?id=10.1371/journal.pgph.0005867) | Alert thresholds trade off missed episodes and false alarms by action/territory; Vietnamese operational results do not certify V2 or retrospective as-of availability. |


### Historical delivery2 two-procedure proposal — 2026-10-21 (superseded by DEC-130)

The [assessment contract](stage-5/model_evaluation_contract_v1.json) records a
concrete proposal under PLAN_028. It preserves DEC-123–129 and the 5pp/10pp/42
knobs. Highest AP among point-utility-qualified candidates is a proposed family
choice, not an already-approved champion. The proposed final calendar retains
2024-06 internal decisions, with outer training through 2024-12 for T+1 and
2024-11 for T+2. Final targets January–December2025, temporal-block uncertainty,
acceptance rules and calibration transfer require explicit human acceptance tied
to the immutable proposal identity. No reserved results have informed this design.
G4/G5 are not approved by implementation or by this registration.


<a id="dec-130"></a>
### DEC-130 Compare all six procedures and add complementary development AUROC

- **Status:** ACCEPTED_IMPLEMENTATION_SCOPE on2026-10-21 by Mauricio's explicit
  first-of-three Stage5 closure prompt. This is not G4/G5 or reserved-access approval.
- **Decision:** Include XGBoost, LightGBM and GAM at both T+1/T+2, with persistence
  on the same horizon cohorts. This replaces the prior proposed two-family screen;
  development utility does not remove procedures. No winner is declared.
- **Metrics:** Add complementary AUROC on continuous candidate scores and the
  documented deterministic persistence score. Keep four-window equal weighting,
  explicit single-class/missing non-evaluability and strict alignment/invalid-value
  controls. Brier is still N/A for persistence. Do not add F1, change AP selection
  or change DEC-125 utility/denominators. Existing scientific metrics remain intact.
- **Preserved science:** Y, population, features, preparation, model families,
  approved hyperparameters, per-family/horizon June2024 calibration/threshold
  decisions and retrospective limitations are unchanged.
- **Future proposal:** Six models and six train-only preparers; no new searches,
  calibrator fits or threshold selections. T+1 training labels endDecember2024;
  T+2 endNovember2024. Final targetsJanuary–December2025, origins target−h,
  common76 municipalities, explicit missing evidence, no reserved-label updates.
  None of those fits or reserved reads is authorized in this delivery.
- **Recommendation boundary:** The [owning evaluation contract](stage-5/model_evaluation_contract_v1.json)
  proposes complete/evaluable technical and existing utility/uncertainty eligibility,
  then annual reserved-cohort AP separately by horizon; exact ties require human
  choice and insufficient evidence permits no recommendation. AUROC is complementary.
  This proposed recommendation/acceptance protocol still requires explicit human
  acceptance before2025 access; the present instruction does not supply it.
- **Uncertainty and consumption:** Retain the existing proposed temporal-block
  method with common paired draws across families and marginal candidate-wise
  intervals. No simultaneous/post-selection confidence claim or new correction.
  Using2025 to compare and recommend consumes it for that decision; it cannot be
  an additional independent test of the subsequently selected model.


<a id="dec-131"></a>
### DEC-131 Implement the frozen final route before scientific authorization

- **Status:** ACCEPTED_IMPLEMENTATION_SCOPE by Mauricio's second-of-three closure
  prompt. G4, exact protocol acceptance and reserved scientific execution remain
  separate human decisions; no G5 or champion approval is inferred.
- **Identity:** Retain proposal SHA256
  `66d7208066476b027721182d185770d2522dfe5d891caf4b3b2759177dcc5e09`.
  Preserve its scientific contract, component decisions and code; explicitly migrate
  only notebook08 orchestration with separate original/new fingerprints.
- **Implementation:** All six procedures, exact temporal cohorts and train-only
  preparation, annual shared metrics, frozen common circular3-month/2000/42
  uncertainty, immutable native inference and fail-closed reuse. Retain DEC-125 and
  DEC-130 scientific rules without new searches, recalibration, threshold changes,
  data/feature changes or reserved-driven tuning.
- **Execution boundary:** Implement and validate with synthetic and development
  evidence now. Do not load reserved values or fit final scientific components
  until an actual human decision accepts G4, the exact protocol and execution.
  Synthetic model fits do not consume or establish the scientific six-fit delivery.
- **Pending:** Actual final coverage/performance, scientific execution and final
  recommendation/Stage6 handoff remain unaccredited. Tests and implementation do
  not satisfy those human/scientific gates.


<a id="dec-132"></a>
### DEC-132 Accept G4 and execute the exact frozen 2025 protocol

- **Status:** ACCEPTED_AND_EXECUTED on 2026-10-21 by Mauricio's explicit decision.
- **Authority:** Accept G4 and exact proposal SHA-256
  `66d7208066476b027721182d185770d2522dfe5d891caf4b3b2759177dcc5e09`;
  authorize exactly six final model fits and consultation/evaluation of the 2025
  reserved block. Do not run new searches, calibration fits or threshold selections.
  This authority does not approve G5 or automatically select a winner.
- **Execution:** PLAN_028 executed six models and six train-only preparers, zero
  hyperparameter searches, zero calibrator fits and zero threshold selections.
  The final bundle identity is
  `768406f872f4b859756b4603d684b965841e8c37a0f00c7f34618786dfa76e35`.
  Each horizon has the complete 76-municipality × 12-target cohort (912 rows),
  with no missing labels, predictors or onset context. T+2 training ends in
  November 2024 and retains the November 2024 origin for January 2025.
- **Scientific result:** All six family/horizon procedures are classified
  `does_not_meet`. They improve onset sensitivity relative to persistence, but all
  exceed the predeclared five-percentage-point maximum increase in false-alert
  ratio. No rule was changed after observing the results.
- **Boundary:** The 2025 block is consumed for this comparison and cannot be called
  an independent post-selection test. Historical real-time availability remains
  unproven. G5 is `NOT_APPROVED`; `champion` is `not_selected`. Final interpretation,
  recommendation and the Stage 6 handoff belong to the third delivery.

<a id="dec-133"></a>
### DEC-133 Recommend G5 NOT_APPROVED after the frozen 2025 evaluation

- **Status:** PROPOSED_FOR_HUMAN_G5_DECISION on 2026-10-21. This is a scientific
  recommendation and technical handoff, not Mauricio's acceptance or rejection of G5.
- **Evidence:** Proposal SHA-256
  `66d7208066476b027721182d185770d2522dfe5d891caf4b3b2759177dcc5e09`,
  final bundle
  `768406f872f4b859756b4603d684b965841e8c37a0f00c7f34618786dfa76e35`
  and fresh-kernel notebook receipt
  `6eb390d18a7ce1300e7664da560694f1afd7f56511d31b3cbcf99510eb043564`.
- **Recommendation:** Keep `G5 = NOT_APPROVED` and `champion = not_selected`.
  Every model/horizon candidate improves AP, AUROC and onset sensitivity relative
  to persistence, but all six exceed the frozen maximum five-percentage-point
  increase in false-alert ratio. Do not select a family from discrimination,
  Brier or sensitivity alone, and do not revise thresholds after seeing 2025.
- **Technical/scientific distinction:** The final route, native model restoration,
  complete 76-by-12 cohorts, manifest and metrics reproduce without a new fit.
  That closes Stage 5 technical work with an unsatisfactory scientific outcome;
  it does not demonstrate the required operational utility.
- **Product boundary:** Stage 6 model integration remains blocked until a future
  explicit G5 approval. Draft product/inference contracts may be prepared when
  clearly marked pending G5; no champion may be connected to API or dashboard.
- **Next proposed experiment:** Under a separate plan and protocol, change only
  the alert-threshold policy. Use nested rolling temporal development to select a
  more conservative shared threshold per family/horizon, require the false-alert
  increase to remain within five points in each inner evaluation period, and then
  maximize onset sensitivity among feasible thresholds. Preserve the three current
  model families as historical evidence. Do not optimize on 2025; use a later
  independent block or a predeclared nested outer assessment.
- **Limits:** Consolidated retrospective data do not prove historical operational
  availability. Calibration transfer remains uncertain. The 2025 block is consumed
  for the completed comparison and cannot become an untouched test again. Period
  and territory concentrations are descriptive and support no causal attribution.

<a id="dec-134"></a>
### DEC-134 Accept G5 NOT_APPROVED and centralize champion-decision policy

- **Status:** ACCEPTED_AND_CLOSED by Mauricio on 2026-10-21.
- **Decision:** Accept `G5 = NOT_APPROVED`, keep `champion = not_selected`, and close
  Stage 5 without relaxing scientific criteria or selecting a provisional winner.
- **Single configuration owner:**
  [`champion_decision_policy_v1.json`](stage-5/champion_decision_policy_v1.json)
  owns the editable utility tolerances, ranking rule, retained alert-threshold
  authority, human disposition and read-only MVP boundary. Stage 5 contracts point
  to it instead of repeating those decision values.
- **Interpretation:** Utility tolerances determine whether evidence meets the agreed
  research rule. Retained probability thresholds determine whether a score emits an
  alert. Neither setting retrains the fitted estimators, and changing either after
  seeing 2025 cannot turn the consumed evaluation into new independent evidence.
- **Product boundary:** The read-only MVP may present persisted historical/evaluation
  results, probabilities, alerts and performance context with visible
  `NOT_APPROVED` status. It may not claim operational approval or connect a champion.
- **Future work:** Any renewed champion search or threshold experiment requires a
  separate predeclared scientific protocol and evidence independent of consumed 2025.

<a id="dec-135"></a>
### DEC-135 Approve G2 data/target and G3 training preparation baselines

- **Status:** ACCEPTED_WITH_DOCUMENTED_LIMITS by Mauricio on 2026-10-21.
- **G2 decision:** Approve the current Data & Target Freeze represented by notebook
  03 and its owning contracts: 76 Tolima/Meta municipalities, residence geography,
  symptom-onset time, general-dengue Y, separate severe-dengue count, five prior
  same-month channel observations, current four-zone channel, and T+1/T+2 outcomes.
- **G3 decision:** Approve the notebook 04 preparation baseline: monthly panel,
  approved climate inputs, deterministic antecedents, `zona_canal_t`, temporal
  partitions, train-only transformations, explicit X/Y separation and controls
  against future information.
- **Preserved limits:** Historical as-of operational availability remains unproven;
  six source fields retain insufficient operational definitions; the 5/7/9-year
  target sensitivity is unexecuted; retrospective data do not establish prospective
  performance. These limits remain visible and do not invalidate the accepted MVP
  baseline.
- **Boundary:** This decision does not rerun EDA, change datasets or labels, approve
  predictive performance, reverse G5 `NOT_APPROVED`, or authorize model integration.


### EXP03 revised implementation boundary — no scientific execution

The current [EXP03 scope](experiments/EXP03_feature_ablation/alcance.md) owns the
sixteen-set information-value design. [Implementation traceability](experiments/EXP03_feature_ablation/IMPLEMENTATION.md)
records the code, generated acceptance and independent-review evidence. The new
executable protocol invalidates legacy EXP03 approvals without changing EXP00/EXP01
scientific identities or EXP02 label-sensitivity ownership. Mauricio fixed B_primary=1.0 before execution in protocol 2.0.1 on 2026-10-27;
see the [decision and rationale](experiments/EXP03_feature_ablation/DESIGN.md#primary-budget-decision--2026-10-27).
This is an experimental comparison budget, not validated operational capacity.
Private-input coverage/maturity and scientific authorization remain pending.
Synthetic fits and consumed-year fixtures are engineering evidence only;
G5 remains NOT_APPROVED and champion not_selected.
<a id="dec-136"></a>
### DEC-136 Register EXP03.1 recent endemic-channel trajectory infrastructure

- **Status:** ACCEPTED_IMPLEMENTATION_SCOPE.
- **Decision date:** 2026-10-27, explicit instruction from Mauricio.
- **Decision:** Implement source-free scientific, contractual, Kedro, persistence, reporting, tracking and synthetic-test infrastructure for visible experiment `EXP03.1` (technical registry ID `EXP031`, Python ID `exp03_1`). Compare complete EXP03 V09 (M00), V09 plus six-month recent channel memory (M01), and M01 plus change from the preceding six months (M02) under the inherited fixed false-onset-alert budget.
- **Scientific boundary:** H5, families, fixed configurations, temporal roles and budget remain inherited from EXP03. The primary cohort requires twelve known historical zones. V09 reuse is fail-closed on all applicable identities and otherwise refits on the paired intersection. No real execution, private-data read, permanent MLflow write, 2025 evaluation, champion selection, G5 approval or reinterpretation of EXP03 is authorized.
- **Evidence owner:** `docs/product/experiments/EXP03.1_add_pass_info/`.
