# Diseño científico y técnico — Evolución global–local de SAT-Dengue

**Documento:** `DESING.md` (nombre solicitado)  
**Fecha:** 1 de noviembre de 2026  
**Versión:** 1.1 — alineada con la auditoría Kedro del 1 de noviembre de 2026.  
**Estado:** hoja de ruta de diseño **pendiente de aprobación para implementar**; no se ha ejecutado ninguna fase.  
**Ámbito:** investigación retrospectiva de inicios de brote de dengue en **T+1 y T+2**, con evaluación principal en Meta y Tolima.  
**Base arquitectónica observada:** auditoría estática `KEDRO_ARCHITECTURE_AUDIT.md` sobre `main`, commit `808cdab17d4bafa46f22bf48d1a9f4b849874e8e`. Los archivos, interfaces y restricciones Kedro citados proceden de esa auditoría; la ejecución y presencia física de todos los datos siguen **UNVERIFIED**.

## 1. Resumen ejecutivo y decisión que buscamos

El problema no se resuelve necesariamente con otro algoritmo. EXP00–EXP04 muestran que existe señal predictiva retrospectiva, pero no una política que conserve simultáneamente **detección, falsas alertas, estabilidad temporal y consistencia territorial**. En EXP04, reducir falsas alertas y mejorar Brier implicó pérdidas de sensibilidad de **5,7 a 15,2 puntos porcentuales**; ninguna política superó el criterio conjunto. La pregunta ya no es solamente «¿qué modelo predice mejor?», sino **«¿compartir información entre municipios, predecir distribuciones de casos y controlar errores de decisión permite mejorar ese frente conjunto?»**.

**Hipótesis centrales, separadas para poder atribuir resultados:**

1. **Transferencia de información:** entrenar sobre una población más amplia de municipios epidemiológicamente elegibles puede mejorar la generalización en Meta y Tolima frente a aprender únicamente con las observaciones actuales.
2. **Pronóstico de conteos:** modelar una distribución de casos en lugar de una etiqueta binaria puede proporcionar probabilidades más útiles para distinguir inicio de brote y continuación, especialmente en T+2.
3. **Decisión consciente de falsos positivos:** ajustar la política de alerta y, solo si es necesario, el aprendizaje de ejemplos negativos difíciles puede reducir falsas alertas **sin perder detecciones por encima del margen permitido**.

La propuesta se desarrolla en **cuatro fases secuenciales** con criterios de avance. No supone que las tres hipótesis funcionen ni exige encadenar todos los modelos. **Un resultado negativo bien evaluado también permite cerrar científicamente.**

**Alcance por fases y por experimentos:** la **Fase 1** habilita una nueva ruta Kedro de datos; la **Fase 2 ejecuta EXP-BETA01** (aprendizaje global/local). **Fases 3 y 4** son extensiones científicas futuras y **no forman parte de la autorización ni del criterio de finalización de EXP-BETA01**: corresponden a **EXP-BETA02** (pronóstico probabilístico) y **EXP-BETA03** (reducción de falsas alertas). Cada fase tendrá un prompt Codex independiente, con aprobación humana entre fases. Ninguna se inicia por el solo hecho de estar descrita aquí.


### Decisiones ya aprobadas para esta propuesta

- Conservar **clima dentro de la Canonical Model Table** y probar explícitamente su aporte; conservarlo no implica activarlo en todos los modelos.
- Usar **información retrospectiva consolidada**. No reconstruir la disponibilidad real al día de emisión ni implementar nowcasting en estas cuatro fases. Esto **no autoriza usar información posterior al origen T** para construir predictores: datos disponibles retrospectivamente y ausencia de fuga hacia el futuro son asuntos distintos.
- **Compatibilidad hacia atrás obligatoria:** ningún nuevo dataset, nodo o parámetro puede modificar la representación o el contrato que consumen los experimentos históricos. La ampliación de Kedro debe ser **aditiva**, desde el panel mensual identificado de Stage 2 y **fuera de `replay`**.
- **Contrato y catálogo estrictos:** Kedro ya valida nombres y perfiles en código. Los nuevos datasets necesitan alta explícita tanto en `conf/base/catalog.yml` como en `config_loader.CATALOG`, y el perfil correspondiente en `validate_parameters`; **no desactivar ni flexibilizar esas validaciones**.
- **Línea base histórica inmutable:** añadir código/configuración puede originar una nueva identidad de replay; no significa que se autorice sobrescribir bundles, alterar hashes anteriores o prometer reutilizar los checkpoints previos.
- Mantener **H5** como definición comparativa de referencia, sin presentar H5 como verdad epidemiológica definitiva; conservar `M00/A0` como referencia científica, sin seleccionar champion.
- La evaluación principal seguirá siendo **Meta y Tolima**. La expansión nacional es una hipótesis **sujeta a disponibilidad, calidad y elegibilidad**; no está comprobado que el proyecto disponga actualmente de todos los municipios del país con el mismo esquema de datos.

## 2. Lo que la evidencia permite y lo que no permite concluir

| Evidencia interna | Decisión de diseño | Límite de interpretación |
|---|---|---|
| EXP00: más inicios detectados acompañados de carga excesiva | Evaluar siempre detección **junto** a falsas alertas | Más sensibilidad no prueba utilidad operativa |
| EXP01: en la cohorte `Y(T)=0`, exceso e inicio son equivalentes en T+1; no en T+2 | Un objetivo para T+1; mantener inicio y exceso como controles separados para T+2 | El exceso en T+2 **no equivale** a un inicio nuevo |
| EXP02: H5/H7/H9 cambian la identidad y fragmentación de los episodios | Congelar H5 y la cohorte durante las comparaciones | H5 no es ground truth externo validado |
| EXP03: estado de T aporta principalmente en T+1; P25/P75 históricos del mes objetivo ayudan a boosting | Conservar ambos como bloques candidatos, sin reescribir las entradas anteriores | Parte del valor de P25/P75 puede venir de representar el umbral usado para definir `Y` |
| EXP03: el clima no mejora de forma general y a veces dispara falsas alertas | Mantener clima en la tabla y contrastar **con/sin clima** sobre el mismo protocolo | No declarar el clima inútil ni asumir que ayuda |
| EXP03.1: memoria de estados reciente aporta poco; M02 no mejora | No promover M01/M02 al baseline por defecto | No excluye otras representaciones temporales |
| EXP04: mejor calibración no garantiza mejor política de alertas | Separar predictor, calibración y regla de decisión | B/C de EXP04 no evaluados: no atribuirles resultado negativo |

**Control de evidencia:** no deben compararse porcentajes absolutos de EXP00, EXP01 y EXP04 como si compartieran población, definición de falsa alerta o años. Una comparación nueva debe realizarse **sobre las mismas observaciones, etiqueta y periodos**, o describirse exclusivamente como contextual.

### Respaldo externo que motiva, sin garantizar, la propuesta

- En **Colombia**, una comparación publicada en 2020 encontró que un modelo agregado nacional aplicado a escala local pronosticó conteos de dengue mejor que algunos modelos departamentales; el trabajo también muestra que una red neuronal no es automáticamente superior a Random Forest [E1].
- Los modelos **globales de series** pueden compartir señal entre series heterogéneas, aunque su rendimiento depende de la relación real entre dominios y de la evaluación [E2].
- Un estudio brasileño de 2026 ensayó **preentrenamiento global y fine-tuning municipal** de CNN-LSTM con resultados favorables en sus propias métricas y **horizontes semanales** [E3]. Su ganancia **no se puede trasladar directamente** al objetivo mensual de inicio ni a las falsas alertas de SAT-Dengue.
- **DeepAR** aprende conjuntamente series relacionadas y permite distribuciones binomiales negativas para conteos [E4]. No implica que nuestra muestra alcance para entrenarlo con ventaja.
- En dengue mensual, un estudio de 2026 encontró que modelos **parsimoniosos de conteos** podían superar a una BiLSTM-Negative Binomial en horizontes de 1–2 meses; por ello el comparador estadístico sencillo debe preceder a una red más compleja [E5].
- Un modelo **jerárquico binomial negativo municipal** ya se ha utilizado en Valle del Cauca, Colombia [E6], lo que respalda estudiar el reparto parcial de información entre municipios, no necesariamente implementar una arquitectura bayesiana pesada.

**Síntesis:** la justificación científica más sólida es probar **aprendizaje compartido antes que mayor complejidad**; después evaluar pronóstico probabilístico y, por último, una política de alerta restringida.

## 3. Contrato científico y arquitectura lógica mínima

### 3.1 Pregunta, unidad de análisis y límites

- **Unidad base:** municipio DANE × mes de origen `T`. Para cada fila se pueden derivar resultados de los horizontes `T+1` y `T+2`, siempre con disponibilidad suficiente de etiquetas.
- **Variable epidemiológica:** exceso mensual según canal **H5**, calculado de forma cronológica usando únicamente historia anterior al mes evaluado. Definir `Y(m,t) = 1` si el municipio `m` está en exceso en `t`, según la regla H5 vigente.
- **Inicio T+1:** en la cohorte en riesgo `Y(m,T)=0`, evento `Y(m,T+1)=1`.
- **Inicio T+2:** respetar **exactamente** la definición de inicio/episodio ya congelada en el código histórico. Conceptualmente, un brote que comenzó en T+1 y continúa en T+2 **no es un nuevo inicio en T+2**. Si se pronostican conteos, hará falta evaluar la **trayectoria conjunta T+1, T+2** (o un modelo directo de inicio), no simplemente `P(exceso en T+2)`.
- **Horizonte:** mensual, sin convertir resultados semanales de literatura en evidencia de anticipación mensual.
- **Finalidad:** capacidad predictiva **retrospectiva**; no afirmar anticipación operativa efectiva, impacto sanitario o preparación para producción.

### 3.2 Canonical Model Table V1: propuesta conceptual

**Una fila por `municipio_dane, periodo_T`** y columnas agrupadas por función. La tabla es fuente de nuevas **vistas**; no sustituye entradas legacy.

| Bloque | Campos mínimos o derivados | Reglas |
|---|---|---|
| Identidad | `municipio_dane`, `departamento`, `periodo_T` | Clave única, municipio por código DANE |
| Contexto territorial | `perfil_transmision`, población/incidencia si existe fuente validada | El perfil de cada corte no debe usar años futuros; no crear variables artificiales si no hay datos fiables |
| Historia de casos | `casos_T`, rezagos `casos_T_1...T_k`, estacionalidad, estadísticas móviles | Ventanas y `k` parametrizados; cifras hasta T, no posteriores |
| Canal endémico | `Y_T`, `zona_T`, razón observado/esperado T, `P25/P75` históricos del mes objetivo, versión `H5` | Para T+1/T+2 los umbrales del objetivo deben calcularse **solo con historia que preceda a T**, no con observaciones futuras |
| Clima | temperatura/precipitación/humedad histórica, agregados y rezagos existentes | Mantener los mismos significados, unidades y ventanas que permita la fuente; no introducir clima observado en T+1/T+2 como predictor |
| Proveniencia | versión lógica del esquema, corte de datos y definición de construcción | Registrar origen/versión, sin imponer nuevo framework de metadatos |

**Separación obligatoria:** etiquetas `onset_T1`, `onset_T2`, `excess_T1`, `excess_T2` pueden vincularse mediante una *vista supervisada* o tabla de targets independiente; **jamás incluirse en `X`**. También deben excluirse variables que filtren directamente el futuro (por ejemplo, resultados reales de `casos_T1` o `casos_T2`).

**Vistas con creación diferida — sin sobredimensionar Fase 1:**

1. **Fase 1:** publicar solo `canonical_model_table_v1`, con columnas y **roles** (`feature`, `target`, `key`, `control`, `metadata`) definidos en un contrato propio. Los targets pueden estar físicamente en esta tabla, pero deben permanecer excluidos de los predictores por una allowlist explícita. No se exige publicar múltiples archivos adicionales.
2. **Fase 2 / EXP-BETA01:** proyectar desde la tabla una vista tabular `X/Y/claves/controles` en el propio consumidor, con selección de variables y cohortes congeladas.
3. **Fase 3 / EXP-BETA02 (condicional):** formar secuencias históricas a partir de la misma fuente identificada. Crear un dataset persistido de secuencias solo si existe una necesidad reproducible demostrada; no hacerlo anticipadamente.

`canonical_tabular_v1`, `canonical_sequences_v1` y `canonical_targets_v1` describen **vistas lógicas**, no nuevas entradas obligatorias del catálogo. Los nombres definitivos dependerán de la implementación acotada.

### 3.3 Compatibilidad Kedro: contrato de arquitectura contrastado con auditoría

**Punto de derivación confirmado en código (no en ejecución):** partir de `data/processed/panel_mensual_dengue_clima.csv` y su contrato/manifiesto identificados. Alternativamente puede leerse el `panel.csv` de un `stage2_bundle` **explícitamente identificado y verificado**. **No** alternar fuentes automáticamente ni buscar el «último bundle». El `stage2_unlabeled_panel` es solo un intermedio **en memoria**; no requiere persistirlo para esta solución.

```text
Stage 2 — panel mensual curado e identificado (lectura; NO modificar)
                     ├── lectores históricos → preparación/EXP00–EXP04, replay (sin cambios)
                     └── NUEVO pipeline Kedro de proyección → canonical_model_table_v1
                                  │                            (contrato, manifiesto, destino propios)
                                  └── EXP-BETA01 → global/local → riesgo → decisión → evaluación
                                       └── (futuro) EXP-BETA02 / EXP-BETA03, sin alterar EXP-BETA01
```

**Superficies concretas observadas en el repositorio:**

| Superficie Kedro | Regla mínima para nuevas rutas | Qué debe conservarse |
|---|---|---|
| `src/sat_dengue/pipeline_registry.py` | Registrar un nuevo pipeline independiente con nombre inequívoco. | `__default__` permanece apuntando a `foundation`; no insertar la ruta en `replay`. |
| `conf/base/catalog.yml` y `src/sat_dengue/config_loader.py` (`CATALOG`) | Añadir de manera consistente las nuevas entradas explícitas, sin catálogo abierto. | Entradas y nombres legacy completos, sin renombrar ni redirigir. |
| `src/sat_dengue/configuration.py` (`validate_parameters`, autoridades) | Admitir **solo** el nuevo perfil/configuración requerido, sin overrides globales ni cambios en contratos anteriores. | Validación estricta y perfiles históricos. |
| `src/sat_dengue/datasets/` | Incorporar un lector verificador y una salida identificada solo si los adaptadores existentes no sirven sin alterar su semántica. | Destinos, firmas, manifiestos, huellas y lectores históricos. |
| `src/sat_dengue/pipelines/data/` y `training_preparation/` | Reutilizar funciones deterministas de dominio **si su semántica coincide**; derivar en un módulo nuevo sin editar recetas legacy. | El esquema exacto de `read_panel`, las **16 features** históricas de `derive_features`, preparadores guardados y rutas de entrenamiento/evaluación. |
| `src/sat_dengue/hooks.py` | No modificarlo en Fase 1: usar `tracking: disabled`, si corresponde al perfil existente. | Tracking y publicaciones históricas. |

El panel Stage 2 ya tiene nueve agregados climáticos: `rain_mm_month_sum`, `temp_mean_c_month_mean`, `dewpoint_mean_c_month_mean`, `surface_runoff_mm_month_sum`, `total_evaporation_mm_month_sum_ecmwf`, `solar_radiation_mj_m2_month_sum`, `soil_water_l1_month_mean`, `wind_u_ms_month_mean` y `wind_v_ms_month_mean`. **Conservar nombres, valores, unidades, reglas de cobertura y contadores de días válidos cuando la fuente los incluya**; no recalcularlos ni imputar silenciosamente ceros. No asumir variables adicionales que la auditoría no acreditó.

**Riesgos específicos que la nueva ruta debe prevenir:**

- **Esquemas históricos exactos:** `read_panel` y lectores experimentales rechazan columnas inesperadas; **nunca ampliar físicamente** el panel histórico ni su contrato para alojar la tabla nueva.
- **Fugas por roles:** el panel Stage 2 mezcla epidemiología, etiquetas, cobertura y controles. Proyectar con **allowlists positivas**, no `select all` ni la matriz `X` ya imputada/codificada por Stage 3.
- **Fugas por filtros:** no utilizar `prepare_exp01_inputs`, `prepare_benchmark_inputs`, ni lectores EXP03/EXP03.1 para la nueva ruta sin aislar su política; podrían introducir cortes como `2024-12`, `2025-12` y reglas de elegibilidad históricas.
- **Acoplamiento entre experimentos:** EXP03 → EXP03.1 → EXP04 reutiliza funciones, algunas internas. No extender esa cadena para EXP-BETA01 ni refactorizarla «de paso».
- **Versionado real:** el repositorio usa **manifiestos, SHA-256, identidades y publicación atómica sin sobrescritura**, no el mecanismo genérico `versioned: true` de Kedro. Aprovechar el patrón existente con **nueva identidad**; el sufijo `v1` no sustituye procedencia ni hash.
- **Identidades de replay:** las huellas globales incorporan código/configuración. Un cambio aditivo puede dar lugar a un nuevo ID de ejecución, aunque los datasets y resultados históricos permanezcan intactos. Preservar artefactos anteriores y verificar compatibilidad, sin exigir IDs idénticos.

**Límites de evidencia:** la auditoría inspeccionó código estático en el commit citado, **sin abrir payloads privados ni ejecutar pipelines**. Antes de diseñar comparaciones se debe verificar la disponibilidad física, periodo de cobertura y contenido del panel y del `M00/A0` histórico. La auditoría **no prueba** disponibilidad de datos nacionales ni reproducción efectiva de checkpoints.

### 3.4 Diseño de evaluación congelado antes de entrenar

1. **Mismas cohortes y objetivos** para comparar candidatos: H5, pares `(municipio, T)`, fechas, tratamiento de meses sin notificación, denominador de falsas alertas y horizontes.
2. **Validación temporal ordenada:** ajuste, selección, calibración y evaluación en ventanas cronológicas; un año objetivo no puede alimentar entrenamiento de ningún municipio que se evalúe en ese año. Evitar mezcla de cortes por territorio.
3. **Separar desarrollo/estrés/confirmación:** 2024 ya se consumió como estrés retrospectivo; **no** utilizarlo para escoger un ganador y llamarlo confirmación independiente. En la síntesis actual **2025 figura no evaluable**. Si no aparece un corte nuevo, maduro y nunca usado, limitar las conclusiones a evidencia retrospectiva y describir incertidumbre.
4. **Comparador fijo:** `M00/A0` y las líneas pertinentes de la secuencia anterior, reusando predicciones congeladas cuando compartan exactamente cohorte/target; si se reconstruye un control, registrar su nueva versión y evitar fingir identidad con el histórico.
5. **Resultado primario conjunto:** sensibilidad de inicios y carga de falsas alertas por municipio-año. Como referencia experimental, conservar el presupuesto **≤1 falsa alerta/municipio-año** y el margen **−2 pp** de no inferioridad de EXP04 **cuando se esté replicando ese protocolo**. Su adopción formal para nuevas hipótesis deberá congelarse antes de ejecutarlas; **no ajustar límites después de ver resultados**.
6. **Guardrails:** reportar por horizonte, año, Meta, Tolima y perfiles con soporte suficiente. Mostrar detecciones y falsas alertas absolutas, número de inicios y exposición que sirve de denominador. Un promedio agregado **no** habilita selección si hay deterioros territoriales relevantes.
7. **Métricas secundarias:** AP/AUROC (discriminación), Brier/calibración (riesgo), precisión/PPV, cobertura y scoring probabilístico de conteos si aplica. Ninguna métrica secundaria sustituye la decisión conjunta.
8. **Incertidumbre:** usar intervalos pareados por bloques territoriales/temporales cuando el soporte lo permita; si los años o eventos independientes son insuficientes, marcar `UNAVAILABLE` y mantener inferencias descriptivas.

---

## 4. Plan de implementación — exactamente cuatro fases

Las fases delimitan **cuatro futuros prompts independientes para Codex**. Cada una exige autorización previa, alcance congelado y revisión del resultado antes de la siguiente. **Este documento no ordena implementar nada.**

### Fase 1 — Base canónica y compatibilidad Kedro (habilitadora de EXP-BETA01)

**Pregunta:** ¿podemos publicar una fuente nueva, verificable y reutilizable sin cambiar ninguna entrada ni ejecución histórica?

**Alcance mínimo de datos**

- Inspeccionar el **panel Stage 2 persistido e identificado** (`data/processed/panel_mensual_dengue_clima.csv` + contrato/manifiesto), antes de la selección supervisada o del preprocesamiento de Stage 3. Si se prefiere `stage2_bundle/panel.csv`, fijar **esa única fuente identificada** antes de ejecutar; no alternar implícitamente.
- Proyectar por lectura una fila `municipio_dane × periodo_T`, conservando epidemiología, H5/estado T, contexto histórico, los **nueve agregados climáticos del panel** y controles de cobertura; crear únicamente rezagos o P25/P75 necesarios cuyo cálculo cronológico sea inequívoco, sin rellenar huecos automáticamente.
- Congelar un contrato compacto con clave, tipo, papel (`feature`, `target`, `key`, `control`, `metadata`), procedencia, regla de construcción y disponibilidad cronológica. Mantener `X` libre de `Y(T+1)`, `Y(T+2)`, conteos futuros, estados futuros y etiquetas de episodio. Los campos climáticos quedan en la tabla aunque la vista de entrenamiento pueda desactivarlos.
- Verificar el contenido físico y la cobertura del alcance Meta/Tolima. Registrar por separado la **factibilidad de datos nacionales**; no incorporarlos como dependencia obligatoria de esta fase si aún no existen fuentes comparables.

**Implementación Kedro mínima — requerida en esta fase**

1. Crear un **pipeline autónomo de lectura y proyección** (nombre definitivo coherente con el registro vigente), sin editar `pipelines/data` ni `pipelines/preparation` para cambiar sus salidas. No añadirlo a `replay` ni a `__default__`.
2. Crear entrada de lectura verificada del panel y destino nuevo de publicación para **`canonical_model_table_v1`**. No depender del intermedio en memoria `stage2_unlabeled_panel`, de la matriz `X` de Stage 3 ni del «último bundle».
3. Dar de alta entradas correspondientes **en ambos** `conf/base/catalog.yml` y `src/sat_dengue/config_loader.py` (`CATALOG`), y registrar únicamente el perfil autorizado en `configuration.py` (`validate_parameters`/autoridades), sin relajar validaciones.
4. Publicar la tabla en **destino nuevo**, con contrato, identidad de fuente, versión de transformación, manifiesto/SHA y escritura atómica **sin sobrescribir**. Aprovechar patrones de `datasets/`; no introducir un sistema nuevo de versionado.
5. Permitir ejecución de esta ruta sin tracking de modelos cuando proceda (`tracking: disabled`); no modificar hooks ni MLflow para producir una tabla.

**Superficies de referencia para Codex:** `src/sat_dengue/pipeline_registry.py`, `src/sat_dengue/config_loader.py`, `src/sat_dengue/configuration.py`, `conf/base/catalog.yml`, `src/sat_dengue/datasets/`, `src/sat_dengue/pipelines/data/` **solo en lectura para estudiar semántica**, `src/sat_dengue/training_preparation/` **solo como referencia**. Los nombres precisos de nuevos módulos se deciden siguiendo el patrón existente, no se imponen aquí.

**Fuera de alcance:** entrenar modelos, migrar Stage 2/3, recodificar todos los históricos, modificar contratos antiguos, reparar toda la cadena EXP03–EXP04, persistir todas las vistas posibles, reconstruir casos individuales o añadir MLOps nuevos.

**Entregables:** `canonical_model_table_v1` identificada y persistida; contrato/diccionario; resumen de cobertura y elegibilidad; mapa conciso de qué entradas legacy se preservaron; evidencia de lectura, integridad, reglas cronológicas y no sobrescritura.

**Criterio de aceptación y pase:** la ruta nueva se ejecuta de forma independiente; el catálogo/perfil la admiten sin desactivar controles; conserva clima y diferencia **cero de ausencia**; no introduce `Y` en `X`; mantiene **idénticos bytes/esquemas/destinos** de fuentes y contratos legacy afectados, según verificaciones aplicables. Si el panel físico no tiene una columna necesaria, registrar `UNVERIFIED`/brecha y decidir una nueva fuente identificada: **no mutar la fuente histórica**.

### Fase 2 — Aprendizaje compartido y adaptación territorial mínima

**Pregunta:** ¿la mejora proviene de compartir más información entre municipios, o de personalizar un modelo ya entrenado?

**Diseño pareado mínimo**

| Brazo | Qué cambia | Qué revela |
|---|---|---|
| `R0` | Referencia retrospectiva `M00/A0` reproducible en la misma cohorte | Punto de partida, **no champion** |
| `G0` | Mismo enfoque tabular seleccionado, entrenado conjuntamente con Meta + Tolima | Beneficio de nueva representación/entrenamiento conjunto, sin datos nacionales |
| `G1` | Igual familia y features, expandiendo entrenamiento a municipios nacionales **elegibles**, si existen | Beneficio atribuible al volumen/diversidad adicional |
| `L1` | Mejor `G0/G1` con **ajuste territorial ligero** sobre datos anteriores al corte (por ejemplo, intercepto/calibración por departamento o perfil con regularización) | Beneficio de adaptación; evita 76 modelos independientes |

**Control de variables:** no cambiar al tiempo familia, dataset, features y regla de decisión. Una primera comparación `G0 ↔ G1` debe conservar la misma familia e hiperparámetros esenciales; `L1` conserva el predictor y prueba la adaptación por separado. Evaluar **clima OFF/ON como contraste emparejado acotado**, no como combinación exhaustiva de muchos hiperparámetros.

**Preflight científico obligatorio:** antes de afirmar que `G0` aporta «aprendizaje global», comprobar si `M00/A0` o el entrenamiento histórico ya agrupa los **76 municipios** en un único predictor. Si lo hace, `G0` no es una innovación por *pooling* por sí sola: debe distinguirse una **reimplementación de control** de la ampliación nacional y de la adaptación territorial. Si `G1` no dispone de datos elegibles, cerrar ese brazo como `NO_EVALUABLE` sin inventar una fuente nacional.

**Elección prudente:** usar primero **una familia tabular existente** (por ejemplo LightGBM o XGBoost, según reproducibilidad y señal histórica) para separar el efecto de **compartir datos** del efecto de **introducir una red neuronal**. Si la evidencia de globalización o el soporte de secuencias justifica una red, reservar un único candidato temporal pequeño para la fase siguiente. No abrir búsqueda masiva de arquitecturas.

**Adaptación local:** priorizar un ajuste ligero (intercepto/calibración con regularización y fallback global); no hacer fine-tuning de cientos de parámetros en territorios con pocos inicios. La comparación `global vs local` debe responder si el ajuste territorial añade valor por encima del modelo global **sin sobreajustar**.

**Implementación Kedro mínima — requerida para EXP-BETA01 (solo tras aprobar Fase 1)**

1. Registrar una **ruta experimental independiente** para `EXP-BETA01`, consumidora **explícita** de `canonical_model_table_v1` y de su identidad/manifiesto. No conectar el experimento a `replay` ni utilizar automáticamente `preparation_sources`/`exp*_sources` históricos.
2. Construir dentro de esa ruta una **proyección tabular supervisada** (`X`, `Y`, claves, cobertura/controles) con allowlists y parámetros/contrato del experimento. Los cortes temporales, elegibilidad, H5, horizontes y clima ON/OFF deben quedar congelados **en el protocolo Beta**, no heredados por conveniencia de EXP01/EXP03.
3. Separar lógicamente **entrenamiento**, **adaptación ligera**, **predicción**, **calibración/política de comparación** y **evaluación**, reutilizando funciones existentes solo cuando sean compatibles. No extender la cadena de imports entre EXP03, EXP03.1 y EXP04, ni transformar Kedro en un framework nuevo.
4. Persistir **predicciones y métricas identificadas** por brazo/horizonte/corte, modelo, dataset y política aplicada; destino nuevo de resultados, manifiesto y publicación sin sobrescritura. Integrar MLflow **solo si la capacidad existente puede hacerlo sin cambio transversal**, sin hacerlo requisito para el aprendizaje global.
5. Registrar las nuevas entradas de catálogo y perfil **en los mismos puntos de validación estricta** identificados en Fase 1. No abrir parámetros arbitrarios ni alterar `__default__`, `replay`, contratos Stage 3–5 o preparadores guardados.

**Verificación de compatibilidad y evidencia:** el grafo Beta depende de la nueva tabla, no de outputs legacy mutados; conserva predicciones para comparaciones pareadas, y demuestra que clima OFF/ON selecciona columnas sin modificar la tabla fuente. Verificar el comportamiento histórico afectado según alcance; no hace falta reejecutar todos los experimentos ni reentrenar sus modelos.

**Entregables de la fase:** tabla pareada de brazos; predicciones persistidas por municipio/mes/horizonte; métricas por año/departamento; contribución marginal de clima; conclusión `RESPALDADA`, `NO_RESPALDADA` o `NO_EVALUABLE` para aprendizaje global y adaptación local.

**Criterio de avance:** seleccionar **a lo sumo un predictor global** como candidato de investigación si preserva detección y carga con mejores resultados consistentes; si ninguno supera la referencia, mantener R0 y registrar el resultado. **No forzar la fase 3 a utilizar G1/L1 si son peores.**

### Fase 3 — Pronóstico probabilístico de casos e inicio de episodios

**Pregunta:** ¿modelar el número de casos y su incertidumbre es más útil que clasificar directamente un inicio H5?

**Comparación contenida**

1. **Comparador obligatorio y simple:** un modelo **binomial negativo** de conteos (posiblemente con términos departamentales/perfil suavizados) para predecir casos mensuales. No se exige un modelo bayesiano complejo.
2. **Candidato adicional condicional:** **DeepAR o una GRU pequeña con salida binomial negativa** entrenada globalmente, **solo si** hay suficientes series/eventos, y si el modelo sencillo deja una limitación identificada que una secuencia podría resolver. Elegir **uno**, no ambos ni una búsqueda de Transformers.
3. Conservar exactamente los mismos **orígenes T, municipios, horizontes, H5 y bloques climáticos** que el comparador de clasificación para atribuir resultados.
4. Generar `P(exceso_T1)` y `P(exceso_T2)` utilizando umbrales H5 del mes correspondiente calculados sin información futura.
5. Para **inicio T+2**, obtener la probabilidad de la **secuencia que define un nuevo inicio**. Si la regla de episodios usa la transición `Y(T+1)=0, Y(T+2)=1`, estimarla mediante muestras conjuntas de trayectorias `(casos_T1, casos_T2)`. **No** usar como sustituto `P(exceso_T2)` ni usar `Y(T+1)` real como feature. Si el método propuesto no produce una distribución conjunta coherente, **dejar T+2 onset no evaluable para ese brazo**, en lugar de simular una equivalencia.
6. Convertir el riesgo probabilístico en alertas usando una **política fija comparable**, no elegir simultáneamente nuevo modelo y un threshold favorable.

**Implementación Kedro mínima — solo para EXP-BETA02, no para cerrar EXP-BETA01**

- Crear un **pipeline propio** que consuma por identidad la tabla canónica y, si es pertinente, las predicciones congeladas de EXP-BETA01; no reemplazar datasets/modelos de ese experimento.
- Proyectar casos y secuencias desde la **fuente canónica existente** mediante nodos específicos. Materializar secuencias como nuevo dataset solo si lo requiere el entrenamiento o la reproducibilidad; nunca introducir ahora un catálogo genérico de tensores.
- Separar entrenamiento de conteos, pronóstico de trayectoria conjunta, conversión a riesgo H5, política fija y evaluación, conservando sus outputs independientes y auditables.
- Registrar nombres/destinos/perfil en las validaciones Kedro existentes; los nuevos modelos y dependencias se incorporan **únicamente** si el candidato secuencial es científicamente autorizado.

**Métricas:** errores y cobertura del pronóstico de conteos; Brier/AP del riesgo de inicio; sensibilidad, falsas alertas e intervalos/soporte por territorio y año. La evaluación de conteos es **secundaria**: un mejor RMSE no acredita mejor detección de inicios.

**Entregables:** una referencia simple de conteos, como máximo un candidato temporal adicional, pronósticos por trayectoria si corresponde, probabilidades H5 y evaluación pareada contra el clasificador seleccionado.

**Criterio de avance:** conservar como candidato solo un pronóstico que tenga **valor demostrado en la decisión de alertar**, no solamente una mejor distribución de casos. Si el pronóstico probabilístico falla, **cerrar la hipótesis** sin entrenar una sucesión de modelos.

### Fase 4 — Política FP-aware y cierre científico

**Pregunta:** ¿puede reducirse la carga de falsas alarmas sin perder detección de inicios ni trasladar el deterioro a otros territorios?

**Orden de complejidad creciente — no ejecutar todo automáticamente**

1. **Punto de control:** aplicar al predictor congelado la política de decisión de referencia, con métricas por horizonte/año/territorio.
2. **Primera intervención:** seleccionar sobre desarrollo un **umbral restringido** por presupuesto de falsas alertas (global); congelarlo antes de evaluar cada corte posterior. Si existe evidencia suficiente, comparar una **regla por departamento/perfil con regularización y retorno al umbral global**. Evitar umbrales municipales libres.
3. **Intervención opcional:** si el ranking deja falsas alarmas recurrentes con alta confianza, probar **una sola** alternativa de aprendizaje consciente del costo (ponderación asimétrica **o** minería de negativos difíciles); no añadir ambas junto con un segundo clasificador salvo justificación independiente. Los ejemplos difíciles se extraen de predicciones **fuera de muestra dentro del desarrollo**; nunca de los años reservados para evaluación.
4. **Filtro de segunda etapa:** mantenerlo como **trabajo futuro** a menos que el paso 3 demuestre un patrón reproducible y soporte suficiente. No usar aprendizaje por refuerzo: no tenemos acciones, recompensas ni efectos de intervención observados para identificar una política causal.

**Regla de decisión:** optimizar sensibilidad de inicios **sujeta** a un límite de falsas alertas por municipio-año y guardrails territoriales. Un umbral que elimina alertas a costa de omitir demasiados inicios **no mejora** SAT-Dengue. No se cambiará el margen de no inferioridad ex post.

**Implementación Kedro mínima — solo para EXP-BETA03, no para cerrar EXP-BETA01**

- Añadir una **ruta experimental de política de decisión** que consuma predicciones **congeladas e identificadas** de un candidato aprobado para estudio (EXP-BETA01 o EXP-BETA02, o referencia R0), sin reentrenarlo por defecto.
- Mantener selección de umbrales/ajuste FP-aware **separados del predictor** y calcular métricas por año y territorio; almacenar decisiones, presupuestos y resultados bajo un destino nuevo de `EXP-BETA03`.
- Registrar entradas y perfil explícitos si son nuevos; reutilizar publicación/manifiestos y el tracking existente solo cuando encaje. No incorporar la política Beta en la evaluación histórica ni modificar los umbrales guardados.

**Evaluación final:** comparar predictor+política con `R0`, con el mismo target, cohortes y cortes; informar detecciones y falsas alertas por municipio-año, PPV, Brier, AP, estabilidad por año y Meta/Tolima/perfil. Distinguir selección en desarrollo, estrés ya consumido (2024) y confirmación independiente (si existe).

**Entregables:** política seleccionada **o rechazo explícito**, cuadro de ablations mínimo (predictor / adaptación / conteos / política), predicciones congeladas y una conclusión de tesis que describa resultados positivos, negativos y no evaluables.

**Criterio de cierre:** declarar `G5 APPROVED`/champion **únicamente** si se satisfacen los criterios científicos y de gobernanza vigentes con evidencia independiente suficiente. En ausencia de ello, mantener **`G5 NOT_APPROVED` y `champion: not_selected`**, pero **cerrar este programa experimental** con hallazgos documentados. Ningún resultado debe disparar indefinidamente «un modelo más».

---

## 5. Decisiones clave para evitar sobreingeniería

| Alternativa | Decisión en este diseño | Razón |
|---|---|---|
| 76 modelos por municipio | **No** | Poco soporte independiente, varianza alta y mantenimiento excesivo |
| Modelo nacional obligatorio | **No; condicionado** | La cobertura y homogeneidad nacional deben demostrarse en fase 1 |
| Nueva red profunda desde cero como primer intento | **No** | Confundiría efecto del algoritmo con efecto de compartir datos |
| Global tabular + adaptación ligera | **Sí, primero** | Menor complejidad y permite atribuir el cambio |
| Negative Binomial sencilla | **Sí, control de fase 3** | Buena referencia para conteos con sobredispersión |
| DeepAR/GRU probabilística | **Una sola, condicional** | Puede aprender secuencias globales, pero exige muestra y validación |
| Foundation models/Transformers/TFT/GNN | **Fuera de alcance inicial** | Coste y complejidad sin evidencia de que resuelvan el frente detección–carga |
| DRL (DQN/PPO/SAC) para falsos positivos | **Descartar en este alcance** | Falta entorno de acciones, recompensas e intervenciones observadas |
| Hard-negative mining | **Opcional al final** | Riesgo de sobreajuste/reutilización de errores de validación |
| Nuevo despliegue y dashboard | **No** | No aporta a decidir estas hipótesis; se reutiliza lo existente cuando corresponda |
| Actualizar/reentrenar EXP00–EXP04 | **No** | Mantener sus artefactos y contratos; reusar controles de manera trazable |

## 6. Riesgos transversales y mitigaciones mínimas

| Riesgo | Severidad | Mitigación concreta |
|---|---|---|
| Fuga temporal al calcular P25/P75 o clima del mes futuro | Alta | Computar por origen T; no usar datos posteriores a T en features |
| Usar años de prueba de otros municipios para entrenar global | Alta | Cortes cronológicos globales: misma fecha límite para todos los municipios |
| Confundir ausencia de notificación con cero casos | Alta | Conservar estado de dato faltante y reglas de elegibilidad por fuente |
| Perfil de transmisión calculado con datos futuros | Alta | Congelar perfil con información del corte o usar definición externa histórica válida |
| Contar exceso T+2 como inicio T+2 | Alta | Calcular evento de episodio según regla H5; predicción conjunta o onset directo |
| Falsos positivos usados para reentrenar y reevaluar en los mismos periodos | Alta | Hard negatives exclusivamente a partir de predicciones de desarrollo fuera de muestra |
| Desplazamiento de errores entre Meta y Tolima | Alta | Guardrails por territorio, no solamente métricas agregadas |
| Sobreajuste de calibración local con pocos inicios | Media-alta | Regularización, mínimo soporte y fallback al global |
| Clima aumenta carga de alertas | Media | Comparación pareada ON/OFF manteniendo todo lo demás fijo |
| Sobrescritura de pipelines/outputs históricos | Alta | Nuevos nombres y rutas; compatibilidad verificada antes de entrenar |
| Interpretar resultados retrospectivos como alarma real operativa | Alta | Declarar explícitamente el supuesto de datos consolidados y la limitación de tiempo real |

## 7. Cómo convertir posteriormente el diseño en cuatro prompts de Codex

Cada prompt futuro tendrá un **único objetivo**, una superficie de código conocida después de la auditoría y los mismos encabezados compactos:

- **Objetivo y pregunta que resuelve.**
- **Fuentes de autoridad** (esta propuesta, auditoría Kedro aprobada y contrato científico congelado).
- **Alcance y exclusiones**, incluyendo preservación de legacy.
- **Cambios esperados**, solo de la fase autorizada.
- **Criterios de aceptación observables y evidencia**, sin imponer detalles de implementación innecesarios.
- **Punto de decisión para Mauricio** antes de pasar a la siguiente fase.

La auditoría Kedro **ya fue recibida e integrada**. Los cuatro prompts pueden redactarse posteriormente desde las secciones de cada fase, **una vez autorizada la fase concreta**. **Para EXP-BETA01 solo corresponden Fase 1 y Fase 2**; Fases 3 y 4 se reservan a EXP-BETA02/03 y requieren decisiones científicas adicionales. No anticipar implementaciones ni nuevas dependencias «por si acaso».

## 8. Decisiones cerradas por auditoría y verificaciones pendientes

**Cerradas para el diseño (sujetas a confirmar en ejecución):**

- **Fuente:** panel mensual persistido e identificado Stage 2 (`data/processed/panel_mensual_dengue_clima.csv`); `stage2_unlabeled_panel` no requiere publicación, y `stage2_bundle/panel.csv` solo es alternativa con identidad y contrato explícitos.
- **Ruta:** bifurcación Kedro independiente y aditiva; no cambiar `replay`, `__default__`, `preparation_sources`, esquemas previos ni preparadores guardados.
- **Catálogo:** declaración doble `catalog.yml`/`config_loader.CATALOG` y validación estricta de perfiles en `configuration.py`.
- **Persistencia:** usar patrón de manifiestos/hashes/identidad/publicación sin sobrescritura, sin crear otra plataforma de versionado.
- **Clima:** nueve agregados existentes en Stage 2 con semántica de cobertura, más derivaciones justificadas si el protocolo las necesita.

**Pendiente de verificar antes de entrenar o declarar avance:**

1. ¿El panel físico identificado y los bundles `M00/A0` **existen, son legibles y tienen cobertura suficiente**? La auditoría estática los dejó `UNVERIFIED`.
2. ¿Los modelos históricos ya realizan **pooling de los 76 municipios**? Si es así, precisar el valor incremental de `G0` frente a `R0`.
3. ¿Existen **datos nacionales** realmente disponibles, homologados y elegibles por periodo? Si no, registrar `G1 = NO_EVALUABLE` y continuar con el alcance Meta/Tolima.
4. ¿Cuál es la definición programática exacta de **inicio T+2** del contrato congelado, necesaria para futuras probabilidades de trayectoria?
5. ¿El presupuesto **≤1 falsa alerta/municipio-año** y el margen **−2 pp** se ratifican para EXP-BETA01 y sucesivos? Congelar el protocolo antes de entrenar.
6. ¿Qué periodos son verdaderamente independientes y maduros? **2024 ya fue usado como estrés** y **2025 no se considera evidencia válida** bajo el estado científico actual.

Las preguntas 4–6 limitan selección o interpretación científica, no son motivo para rediseñar Kedro. Un resultado `NO_EVALUABLE` puede ser una salida válida del brazo correspondiente.

## 9. Conclusión

La evolución recomendada es **aditiva, escalonada y falsable**: **Fase 1** crea una única bifurcación Kedro desde Stage 2; **Fase 2 = EXP-BETA01** mide aprendizaje global y adaptación territorial; **Fase 3 = EXP-BETA02** estudia conteos probabilísticos; **Fase 4 = EXP-BETA03** estudia falsas alertas. Las últimas dos **no son dependencias de implementación de EXP-BETA01**. Cada fase incorpora únicamente su ruta, sus datasets y sus contratos propios, preservando las interfaces de los consumidores históricos. El enfoque conserva clima, aprovecha la información retrospectiva consolidada acordada y protege todos los experimentos previos.

El objetivo de las cuatro fases **no es obligar a encontrar un champion**. Es responder tres hipótesis nuevas con la menor complejidad que permita una conclusión científicamente defendible.

## 10. Referencias

### Fuentes internas proporcionadas

- `analisis-1.md`: EXP00–EXP01, equivalencia de target T+1 y limitaciones de T+2.
- `analisis-2.md`: EXP02, sensibilidad de definiciones H5/H7/H9.
- `analisis-3.md`: EXP03, estado actual, umbrales históricos y clima.
- `analisis-4.md`: EXP03.1, memoria temporal gruesa.
- `analisis-5.md`: síntesis científica EXP00–EXP04, referencia `M00/A0`, resultados y límites.
- `experimentos.md`: catálogo de hipótesis original; **sus estados de EXP03.1 y EXP04 están desactualizados** frente a `analisis-5.md`.
- `KEDRO_ARCHITECTURE_AUDIT.md`: auditoría **recibida y utilizada**; inspección estática de Kedro en `main` / `808cdab17d4bafa46f22bf48d1a9f4b849874e8e` (2026-11-01); recomendaciones de bifurcación desde Stage 2, catálogo cerrado, preservación de legacy y publicación identificada. **No acredita ejecución ni disponibilidad física de datos.**
- `experimentos_actualizado.md`: registro de la serie **EXP-BETA01/02/03**; la Fase 1 es habilitadora, no un experimento científico adicional.

### Evidencia científica y documentación externa consultada

- **[E1]** Zhao et al. (2020), *Machine learning and dengue forecasting: Comparing random forests and artificial neural networks for predicting dengue burden at national and sub-national scales in Colombia*. [Texto](https://pmc.ncbi.nlm.nih.gov/articles/PMC7537891/). **Transferibilidad:** pertinente para pooling colombiano, pero pronóstico de casos, no el endpoint onset/carga de SAT-Dengue.
- **[E2]** Montero-Manso y Hyndman (2021), *Principles and algorithms for forecasting groups of time series: locality and globality*. [Texto](https://p5g.robjhyndman.com/publications/global-forecasting/). **Transferibilidad:** fundamenta global vs local en series, no demuestra éxito en dengue.
- **[E3]** *From global to local: A transfer learning framework for municipal dengue prediction in Brazil* (2026). [Artículo](https://www.sciencedirect.com/science/article/abs/pii/S0378437126001111). **Transferibilidad:** estudio municipal relevante; horizontes semanales y métricas de conteos distintas a nuestro criterio de alertas.
- **[E4]** Salinas et al. (2020), *DeepAR: Probabilistic forecasting with autoregressive recurrent networks*. [Artículo](https://doi.org/10.1016/j.ijforecast.2019.07.001). **Transferibilidad:** metodología de redes globales y binomial negativa, no evidencia específica de que DeepAR supere baselines de dengue.
- **[E5]** Sesay et al. (2026), *Probabilistic forecasting of monthly dengue cases using epidemiological and climate signals: A BiLSTM-Negative Binomial Model versus Mechanistic and Count-Model Baselines*. [PLOS Global Public Health](https://doi.org/10.1371/journal.pgph.0005404). **Transferibilidad:** evidencia directa sobre horizonte mensual; no hay ganador universal por horizonte.
- **[E6]** *Effects of climate variability on the spatio-temporal distribution of Dengue in Valle del Cauca, Colombia, from 2001 to 2019* (2024). [Texto](https://pmc.ncbi.nlm.nih.gov/articles/PMC11460706/). **Transferibilidad:** ejemplo colombiano de modelo municipal jerárquico binomial negativo.
- **[E7]** Beal et al. (2025), *Forecasting Dengue: Evaluating the Role of Hydroclimate Information in Subseasonal to Seasonal Prediction*. [GeoHealth](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2024GH001325). **Transferibilidad:** aporta criterios para evaluar clima por horizonte; no garantiza valor incremental en T+1/T+2.
- **[E8]** Kedro, [Data Catalog](https://docs.kedro.org/en/stable/catalog-data/introduction/) y [Modular Pipelines](https://github.com/kedro-org/kedro/blob/main/docs/build/modular_pipelines.md). **Transferibilidad:** describe capacidades del framework, **no** acredita la estructura concreta del repositorio SAT-Dengue.
