# EXP02 — Ablación de grupos de variables

Estado: borrador de diseño; no autorizado para ejecución.

## Objetivo e hipótesis

Estimar qué grupos mejoran sensibilidad de inicios bajo presupuesto emparejado de falsas alertas y cuáles pueden eliminarse. La hipótesis es predictiva, no causal: canal actual puede favorecer persistencia; clima puede añadir faltantes sin utilidad incremental. No se ejecutó ningún modelo ni fit para este documento.

## Fundamento histórico y autoridad

[EXP00](../EXP00_historical_baseline/CONCLUSIONS.md) acredita que los seis procedimientos no cumplieron la restricción de falsas alertas. Sus resultados son históricos y no evidencia nueva para EXP02. Las afirmaciones de ausencia de ganancia climática y posible beneficio sin canal motivan hipótesis, no una selección preaprobada.

El [contrato de preparación](../../stage-3/training_preparation_contract_v1.json) define 28 variables preparadas y municipio categórico adicional en preparación temporal. El [contrato de modelos](../../stage-4/model_engineering_contract_v1.json) enumera las ablaciones históricas y el de [calibración](../../stage-5/probability_calibration_thresholds_contract_v1.json) preserva criterios relativos a persistencia. Estos inventarios históricos no congelan el conjunto futuro de EXP01. Implementación verificable: `src/sat_dengue/training_preparation/features.py` y preparación temporal del mismo paquete. No se inspeccionaron datos ni almacenes MLflow.

## Inventario verificable de variables

Todas las filas proceden de `development_output.layout`, `derived_features` o `temporal_preparation.municipality_representation` del contrato citado. Clima representa agregados mensuales; historia incluye estado epidemiológico actual y pasado. Municipio es contexto, nunca una variable climática.

| Variable exacta | Fuente | Tipo | Disponibilidad | Transformación | Grupo | Horizonte | Riesgo de fuga | Depende del canal |
|---|---|---|---|---|---|---|---|---|
| `dengue_notifications_count` | `dengue_notifications_count` | numérica | cierre de T; disponibilidad operativa no demostrada | identidad | historia | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `dengue_grave_notifications_count` | `dengue_grave_notifications_count` | numérica | cierre de T; disponibilidad operativa no demostrada | identidad | historia | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `dengue_lag_1` | `dengue_notifications_count` | numérica | T−1 | {"operation": "lag", "source": "dengue_notifications_count", "months": 1, "missing": "preserve"} | historia | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `dengue_lag_2` | `dengue_notifications_count` | numérica | T−2 | {"operation": "lag", "source": "dengue_notifications_count", "months": 2, "missing": "preserve"} | historia | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `dengue_lag_3` | `dengue_notifications_count` | numérica | T−3 | {"operation": "lag", "source": "dengue_notifications_count", "months": 3, "missing": "preserve"} | historia | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `grave_lag_1` | `dengue_grave_notifications_count` | numérica | T−1 | {"operation": "lag", "source": "dengue_grave_notifications_count", "months": 1, "missing": "preserve"} | historia | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `grave_lag_2` | `dengue_grave_notifications_count` | numérica | T−2 | {"operation": "lag", "source": "dengue_grave_notifications_count", "months": 2, "missing": "preserve"} | historia | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `dengue_cambio_1m` | `dengue_notifications_count` | numérica | cierre de T; disponibilidad operativa no demostrada | {"operation": "difference", "source": "dengue_notifications_count", "formula": "T minus T-1", "negative_values": "valid"} | historia | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `dengue_media_3m` | `dengue_notifications_count` | numérica | cierre de T; disponibilidad operativa no demostrada | {"operation": "mean", "source": "dengue_notifications_count", "offsets_months": [0, 1, 2], "min_observations": 3, "centered": false} | historia | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `zona_canal_t` | `zona_canal_t` | categórica | cierre de T; disponibilidad operativa no demostrada | codificación categórica train-only | canal_actual | T+1/T+2 pendientes EXP01 | canal retrospectivo; publicación no demostrada | sí |
| `zona_canal_lag_1` | `zona_canal_t` | categórica | T−1 | {"operation": "lag", "source": "zona_canal_t", "months": 1, "missing": "preserve"} | canal_historia | T+1/T+2 pendientes EXP01 | canal retrospectivo; publicación no demostrada | sí |
| `mes_sin` | `year_month` | numérica | calendario conocido en T | {"operation": "cyclic_calendar", "formula": "sin(2*pi*(month-1)/12)"} | estacionalidad | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `mes_cos` | `year_month` | numérica | calendario conocido en T | {"operation": "cyclic_calendar", "formula": "cos(2*pi*(month-1)/12)"} | estacionalidad | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `rain_mm_month_sum` | `rain_mm_month_sum` | numérica | cierre de T; disponibilidad operativa no demostrada | identidad | clima | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `temp_mean_c_month_mean` | `temp_mean_c_month_mean` | numérica | cierre de T; disponibilidad operativa no demostrada | identidad | clima | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `dewpoint_mean_c_month_mean` | `dewpoint_mean_c_month_mean` | numérica | cierre de T; disponibilidad operativa no demostrada | identidad | clima | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `surface_runoff_mm_month_sum` | `surface_runoff_mm_month_sum` | numérica | cierre de T; disponibilidad operativa no demostrada | identidad | clima | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `total_evaporation_mm_month_sum_ecmwf` | `total_evaporation_mm_month_sum_ecmwf` | numérica | cierre de T; disponibilidad operativa no demostrada | identidad | clima | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `solar_radiation_mj_m2_month_sum` | `solar_radiation_mj_m2_month_sum` | numérica | cierre de T; disponibilidad operativa no demostrada | identidad | clima | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `soil_water_l1_month_mean` | `soil_water_l1_month_mean` | numérica | cierre de T; disponibilidad operativa no demostrada | identidad | clima | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `wind_u_ms_month_mean` | `wind_u_ms_month_mean` | numérica | cierre de T; disponibilidad operativa no demostrada | identidad | clima | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `wind_v_ms_month_mean` | `wind_v_ms_month_mean` | numérica | cierre de T; disponibilidad operativa no demostrada | identidad | clima | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `lluvia_lag_1` | `rain_mm_month_sum` | numérica | T−1 | {"operation": "lag", "source": "rain_mm_month_sum", "months": 1, "missing": "preserve"} | clima | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `lluvia_lag_2` | `rain_mm_month_sum` | numérica | T−2 | {"operation": "lag", "source": "rain_mm_month_sum", "months": 2, "missing": "preserve"} | clima | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `temperatura_lag_1` | `temp_mean_c_month_mean` | numérica | T−1 | {"operation": "lag", "source": "temp_mean_c_month_mean", "months": 1, "missing": "preserve"} | clima | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `temperatura_lag_2` | `temp_mean_c_month_mean` | numérica | T−2 | {"operation": "lag", "source": "temp_mean_c_month_mean", "months": 2, "missing": "preserve"} | clima | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `rocio_lag_1` | `dewpoint_mean_c_month_mean` | numérica | T−1 | {"operation": "lag", "source": "dewpoint_mean_c_month_mean", "months": 1, "missing": "preserve"} | clima | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `escorrentia_lag_1` | `surface_runoff_mm_month_sum` | numérica | T−1 | {"operation": "lag", "source": "surface_runoff_mm_month_sum", "months": 1, "missing": "preserve"} | clima | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |
| `municipality_code` | `municipality_code` | categórica | cierre de T; disponibilidad operativa no demostrada | codificación categórica train-only | contexto | T+1/T+2 pendientes EXP01 | revisiones retrospectivas; ajuste solo train | no |

Los conteos actuales representan estado; rezagos, cambio y media representan historia; mes_sin/mes_cos estacionalidad. Los nueve agregados climáticos representan clima actual y sus seis rezagos historia climática. No existe predictor binario independiente de exceso ni razón de incidencia en este inventario. `zona_canal_t` incluye EXCESO: retirarla elimina también posición actual, por lo que esa variante es un sustituto explícito y no una prueba aislada del exceso. `p25_canal_t`, `p50_canal_t`, `p75_canal_t`, `p75_t1`, `p75_t2` son controles excluidos de X; no se convierten en predictores. Si EXP01 incorpora un indicador independiente, requerirá revisión del diseño antes de congelar la variante exacta sin exceso.

## Matriz mínima y comparador

- `full`: incluye historia, canal_actual, canal_historia, estacionalidad, clima, contexto. Comparador completo congelado de EXP01.
- `without_current_zone`: incluye historia, canal_historia, estacionalidad, clima, contexto. Retira toda la zona actual; no equivale a retirar solo EXCESO.
- `without_channel`: incluye historia, estacionalidad, clima, contexto. Contrasta dependencia conjunta del canal.
- `history`: incluye historia. Referencia epidemiológica mínima.
- `history_season`: incluye historia, estacionalidad. Incremento de estacionalidad frente a history.
- `history_climate`: incluye historia, clima. Incremento climático frente a history en idéntica cohorte; condicional a cobertura suficiente.

Seis variantes como máximo; sin combinatoria exhaustiva. history_climate es condicional y se elimina antes de resultados si no existe hipótesis y cobertura común suficientes. No se añade una variante redundante sin exceso independiente, porque tal predictor no existe. El completo se reconciliará con EXP01: cualquier grupo adicional o ausente bloquea el congelamiento, no se incorpora silenciosamente.

Solo cambia X. Cohorte, etiquetas, fechas, particiones, familias, parámetros, semillas, presupuesto, métricas y métodos de preparación/calibración/umbral serán idénticos. Se reajustará cada preparador reducido exclusivamente en su train; no se reutilizan parámetros dimensionalmente incompatibles. Calibradores y umbrales numéricos pueden diferir por variante, pero sus métodos, roles temporales y presupuesto serán idénticos. No habrá nueva búsqueda por variante.

## Métricas y criterio de éxito

Primaria: diferencia pareada de sensibilidad de inicios respecto a full bajo el mismo presupuesto de falsas alertas fijado en desarrollo. No se emparejan umbrales mirando resultados externos. Si el presupuesto discreto no es alcanzable se informa la desviación y no se afirma equivalencia. Complementarias: precisión de inicios, episodios detectados/perdidos, falsas alertas, falsas alertas por municipio-año, razón de falsas alertas, anticipación útil, PR-AUC, Brier, calibración, cobertura, estabilidad por municipio/departamento/horizonte/ventana y reducción de variables/complejidad.

EXP01 debe fijar denominadores, correspondencia alerta-episodio, deduplicación y anticipación admisible. Sin alertas o sin inicios el cociente es no evaluable, nunca cero. El contrato histórico exige sensibilidad al menos persistencia más margen aprobado y razón de falsas alertas no superior a persistencia más margen aprobado; esos márgenes no se transfieren automáticamente a una nueva etiqueta. Presupuesto concreto, margen mínimo y no inferioridad para eliminación quedan PENDIENTES de autoridad humana y EXP01.

Incertidumbre: bootstrap pareado jerárquico, estratificado por departamento, remuestreando municipios y bloques temporales comunes a todas las variantes; preservar episodios completos y solapamiento de horizontes. Longitud de bloque y número de réplicas se fijarán con desarrollo, antes de estrés. No tratar municipio-mes como independiente. Informar intervalos y número efectivo de episodios; pocos eventos implican resultado inconcluso.

## Política temporal y multiplicidad

2025 está consumido y queda prohibido para entrenamiento, calibración, ajuste, selección de variables, umbrales o champion. 2024 solo admite estrés retrospectivo, nunca prueba ciega ni criterio de selección. La selección ocurre en ventanas anteriores al periodo evaluado, con anidamiento y disponibilidad de todas las etiquetas antes del origen consumidor. Confirmación requiere datos futuros no observados.

Congelar lista de variantes, familias, horizontes, contrastes y política de faltantes antes de cualquier resultado. Reportar todas las variantes, incluidas fallidas. Contrastes primarios contra full constituyen una familia conjunta por variantes, familias y horizontes; usar ajuste Holm para pruebas confirmatorias futuras y reportar intervalos simultáneos. history_season−history y history_climate−history son contrastes exploratorios predeclarados, sin promoción por significación. No seleccionar ganador por 2024/2025 ni ampliar combinaciones tras observar resultados.

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Correlación e interacciones entre grupos | Interpretar efectos condicionales predictivos; no causalidad ni importancia intrínseca. |
| Selección posterior y multiplicidad | Congelar matriz y contrastes; informar todos; Holm y confirmación independiente. |
| Faltantes y pérdida de cobertura climática | Misma cohorte elegible para todas las variantes; ninguna eliminación por variante. Informe de cobertura separado y política común train-only congelada por EXP01. |
| Canal y fuga temporal | Controles futuros fuera de X, rezagos por municipio, linaje y disponibilidad revisados. |
| Cambio de prevalencia | Desgloses por ventana/departamento y calibración; no reajuste sobre estrés. |
| Potencia insuficiente | Intervalos por bloques y episodios; admitir inconclusión sin rebajar criterios. |
| Cambios de cohortes o etiquetas EXP01 | Bloquear ejecución, revisar versión/hashes y repetir revisión contractual. |
| Identificador municipal domina | Mantenerlo explícito en full y ablaciones parciales; referencias history puras lo excluyen, sin atribuir la diferencia a un solo grupo. |

## Interfaces requeridas de EXP01

Los siguientes nombres son requisitos de interfaz, no nombres de columnas ni módulos existentes. No se presupone su ubicación definitiva.

| Interfaz | Archivo/módulo esperado | Información requerida | Estabilidad | Riesgo si cambia |
|---|---|---|---|---|
| T+1 | PENDING_EXP01: ubicación por acordar | definición, versión y hash de T+1 | contrato aprobado y pruebas de interfaz acreditadas | invalida comparabilidad; revisar diseño |
| T+2 | PENDING_EXP01: ubicación por acordar | definición, versión y hash de T+2 | contrato aprobado y pruebas de interfaz acreditadas | invalida comparabilidad; revisar diseño |
| cohorte_operativa | PENDING_EXP01: ubicación por acordar | definición, versión y hash de cohorte_operativa | contrato aprobado y pruebas de interfaz acreditadas | invalida comparabilidad; revisar diseño |
| calendario | PENDING_EXP01: ubicación por acordar | definición, versión y hash de calendario | contrato aprobado y pruebas de interfaz acreditadas | invalida comparabilidad; revisar diseño |
| comparador_principal | PENDING_EXP01: ubicación por acordar | definición, versión y hash de comparador_principal | contrato aprobado y pruebas de interfaz acreditadas | invalida comparabilidad; revisar diseño |
| calibracion | PENDING_EXP01: ubicación por acordar | definición, versión y hash de calibracion | contrato aprobado y pruebas de interfaz acreditadas | invalida comparabilidad; revisar diseño |
| umbral | PENDING_EXP01: ubicación por acordar | definición, versión y hash de umbral | contrato aprobado y pruebas de interfaz acreditadas | invalida comparabilidad; revisar diseño |
| mlflow_parent_child | PENDING_EXP01: ubicación por acordar | definición, versión y hash de mlflow_parent_child | contrato aprobado y pruebas de interfaz acreditadas | invalida comparabilidad; revisar diseño |
| presupuesto_falsas_alertas | PENDING_EXP01: ubicación por acordar | definición, versión y hash de presupuesto_falsas_alertas | contrato aprobado y pruebas de interfaz acreditadas | invalida comparabilidad; revisar diseño |
| definicion_metricas | PENDING_EXP01: ubicación por acordar | definición, versión y hash de definicion_metricas | contrato aprobado y pruebas de interfaz acreditadas | invalida comparabilidad; revisar diseño |

## Decisiones pendientes y preparación

Para implementar: EXP01 congela etiquetas T+1/T+2, cohorte, calendario, comparador, calibración, umbral, familias, semillas, preparación y MLflow parent/child; reconciliar inventario con X real, resolver exceso independiente, aprobar matriz y cobertura. El esquema de tracking solo se especificará tras esa entrega; no acceder al MLflow local de Mauricio.

Para ejecutar: protocolo final revisado y aprobado por Mauricio, interfaces versionadas, controles de fuga y pareamiento acreditados, presupuesto y métricas/denominadores cerrados, ventanas de desarrollo y estrés separadas, multiplicidad e incertidumbre congeladas y autorización explícita de ejecución. Solo entonces crear protocol.json en un PR posterior y registrar EXP02 mediante el dueño del registro. G5 permanece NOT_APPROVED y no se selecciona champion.

No se modifica EXP00/EXP01, contratos vigentes, registro, Kedro, tracking ni código compartido. Integrar este diseño por rebase desde main o PR separado; si EXP01 cambia interfaces, revisar exclusivamente estos dos archivos antes de implementar.
