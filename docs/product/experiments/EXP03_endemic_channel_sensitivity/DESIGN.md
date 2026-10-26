# EXP03 — Sensibilidad de la parametrización del canal endémico

Estado: borrador de diseño; no autorizado para implementación ni ejecución.

## Objetivo e hipótesis

Cuantificar cuánto cambian umbrales, exceso, inicios, episodios y carga de alertas ante decisiones metodológicas del canal. El control no se presume incorrecto; ninguna variante se declara ganadora. Más episodios no implica mayor utilidad predictiva. Este documento no contiene resultados experimentales.

## Fuentes y configuración vigente verificada

La autoridad es el [registro científico](../../traking-concluciones.md), en especial DEC-119–122, DEC-123 y DEC-125. DEC-122 supersede el antiguo requisito de cierre de años completos. El [contrato de preparación](../../stage-3/training_preparation_contract_v1.json) conserva X, controles, elegibilidad y restricciones temporales; los [contratos de modelos](../../stage-4/model_engineering_contract_v1.json) y [evaluación/calibración](../../stage-5/probability_calibration_thresholds_contract_v1.json) distinguen exceso, inicio y alerta probabilística.

| Aspecto | Control vigente | Fuente verificable |
|---|---|---|
| Método | Medianas y percentiles; interpolación lineal Hyndman–Fan tipo 7, no Bortman | DEC-119; `percentile_type7` en `src/sat_dengue/data/consolidation.py` |
| Historia | Cinco observaciones del mismo mes de YYYY−5 a YYYY−1 del año objetivo; sin sustituir un mes faltante por otro año | DEC-122; `history_periods_for_target` |
| Estacionalidad | Mensual, mismo mes calendario, por municipio | DEC-121/122; contrato de preparación |
| Exceso | Conteo de dengue general estrictamente mayor que P75; igualdad no es exceso | DEC-121; `compute_y_labels` y política de etiquetado en consolidación |
| Zonas actuales | EXITO: c<P25; SEGURIDAD: P25≤c≤P50; ALERTA: P50<c≤P75; EXCESO: c>P75 | `classify_endemic_zone` en consolidación |
| Epidemias y brotes | Todos los años con igual peso; incluye 2013 y otros años epidémicos | DEC-113/121 |
| Cero observado | Cero numérico válido dentro de cobertura | DEC-120 |
| Mes sin notificación | Dentro de cobertura y alcance aprobado: cero agregado por decisión del proyecto; no certifica ausencia real de enfermedad | DEC-115/120 |
| Registro ausente | Fuera de cobertura, entrada realmente faltante o sin asignación válida: desconocido, no cero | DEC-120/122 |
| Historia mínima | Las cinco observaciones requeridas y el resultado observado deben existir; de lo contrario etiqueta nula, no negativa | DEC-122; contrato de preparación |
| Endemicidad/elegibilidad | No confundir EXCESO con municipio endémico ni inferir endemicidad desde positividad. Se conserva la política de elegibilidad respaldada por años de notificación y evaluabilidad por horizonte | `src/sat_dengue/training_preparation/eligibility.py`, `policy_from_years`, `build_controls`; `src/sat_dengue/data/readiness.py` |
| T+1/T+2 | Exceso del mes objetivo T+h frente a su referencia propia. Inicio histórico en S exige exceso S y no exceso exactamente S−1; T+2 usa T+1 como antecedente, nunca T | DEC-122/123; DEC-124; interfaces futuras EXP01 pendientes |
| Disponibilidad | Orden mensual retrospectivo no demuestra publicación ni versión disponible en tiempo real | DEC-122; contrato de preparación |

En cada partición se reconstruirá la referencia usando solo observaciones permitidas y disponibles al origen consumidor. El canal del mes S y el de S−1 tienen referencias propias según su año; no reutilizar arbitrariamente P75 de S para ambos estados. Ningún conteo del periodo evaluado entra en su propio percentil. En evaluación secuencial, permitir observaciones anteriores dentro de una ventana solo si el calendario congelado acredita disponibilidad al origen de cada predicción; en evaluación con corte fijo, no incorporarlas. Esta distinción debe cerrarse con EXP01 antes de implementar.

Ejemplo normativo de DEC-122: origen noviembre de 2024, objetivo enero de 2025 → enero de 2020–2024. Es ilustración de calendario, no autorización para reutilizar 2025 en selección.

## Umaña y V1: evidencia y límites

DEC-121 contiene la síntesis de [Umaña et al.](https://publichealth.jmir.org/2026/1/e79914), DOI [10.2196/79914](https://doi.org/10.2196/79914): ventanas de 5–9 años, tendencias de brote y periodos sin casos son factores metodológicamente relevantes. La síntesis indica resultados centrados en Bortman; no acredita superioridad de ninguna ventana para el P75 mensual municipal de SAT-Dengue. La consulta del original devolvió HTTP 403: no se afirman detalles adicionales ni magnitudes del artículo no verificadas.

El registro científico documenta V1 como antecedente de P75 y separa antecedentes de aprobación vigente. Sus particiones, calibración y umbrales no se transfieren: DEC-124–127 requieren independencia y definiciones propias de V2. Ningún resultado histórico de V1, EXP00 o la literatura es evidencia nueva de EXP03.

## Factores y matriz mínima

Identificadores y factores son idénticos a `channel-matrix.draft.yml`:

- `C5`: control, cinco años, mismo mes, P75 tipo 7, todos los años y ceros dentro de cobertura.
- `W6`: solo cambia longitud a seis años.
- `W7`: solo cambia longitud a siete años.
- `W8`: solo cambia longitud a ocho años.
- `W9`: solo cambia longitud a nueve años.
- `E5`: exclusión epidémica, condicional y bloqueada hasta aprobar regla y autoridad; cinco años calendario candidatos, sin extender retrospectivamente para reemplazar exclusiones. Requiere al menos cinco observaciones utilizables: una exclusión puede volverla no evaluable. Esa pérdida de soporte es un resultado metodológico, no se oculta relajando historia.

Cinco variantes ejecutables solo bajo futura autorización y una propuesta condicional; no producto cartesiano. Se mantienen ceros observados y meses cubiertos sin casos en todas. Excluir ceros o convertir faltantes en ceros carece de autoridad suficiente y queda fuera de la matriz. Tendencias y brotes permanecen con peso uniforme; ponderaciones por recencia no se proponen sin justificación y aprobación previas.

Para E5, la autoridad epidemiológica humana deberá aprobar una clasificación oficial INS/territorial con ámbito geográfico y fecha de publicación versionados. Un año epidémico nacional no implica automáticamente año epidémico municipal. La clasificación debe existir antes del origen consumidor; si solo se conoce después, E5 será exclusivamente retrospectiva y no candidata operativa. Nunca clasificar un año como epidémico porque perjudica el score o supera el canal que se está comparando: sería circular. Definir tratamiento de clasificación desconocida sin asumir año ordinario. No modificar DEC-121: se estudia una sensibilidad pendiente de aprobación.

La interacción ventana×exclusión es científicamente relevante pero no identificable con la matriz principal: queda fuera hasta justificar soporte y un contraste adicional predeclarado. No afirmar ausencia de interacción. Ceros×exclusión y pesos×ventana quedan fuera. Si E5 carece de soporte, informar imposibilidad; no añadir retrospectivamente E7/E9.

## Estrategia por etapas

1. Sensibilidad epidemiológica alrededor de C5, antes de modelos. Comparar tanto soporte propio como intersección común fija y registrar todas las exclusiones.
2. Validez y estabilidad en desarrollo previo a 2024: verificar historia, disponibilidad, cobertura e interpretabilidad. Los límites de aceptación metodológica quedan pendientes de Mauricio; estabilidad por sí sola no selecciona una configuración. Congelar preselección antes de ver estrés.
3. Comparación predictiva futura solo para configuraciones preseleccionadas con interfaces EXP01 congeladas y autorización separada.
4. Confirmación prospectiva con datos no observados. 2024 será estrés retrospectivo; 2025 consumido no interviene en selección.

## Métricas epidemiológicas

Por municipio/mes y departamento: P75, diferencia absoluta contra C5 y relativa solo cuando P75_control>0. Con control cero, diferencia relativa no evaluable, mostrando conteos y diferencia absoluta sin epsilon inventado. Comparar exceso positivo, frecuencia de cambios de etiqueta sobre pares evaluables, tabla de transición y concordancia bruta; añadir Jaccard positivo y kappa con sus límites por prevalencia. No tratar dos nulos como acuerdo.

Definir episodios como rachas de exceso consecutivo evaluable: inicio requiere antecedente conocido no excesivo; desconocidos interrumpen observabilidad, no prueban fin o nuevo inicio. Informar censura izquierda/derecha, duración observable, inicios, episodios completos y límites censurados. Emparejar episodios entre parametrizaciones por municipio y solapamiento temporal; componentes uno-a-varios indican fragmentación, varios-a-uno fusión; sin solapamiento indica aparición/desaparición. La política exacta de correspondencia se congelará con EXP01.

Reportar cambios absolutos/relativos de inicios y duración, proporción de episodios fusionados/fragmentados, municipios elegibles y meses evaluables, pérdida de cobertura y estratificación ordinario/epidémico solo con clasificación independiente. Mantener denominadores comunes y propios visibles: una ventana más larga no puede parecer estable simplemente descartando municipios difíciles.

## Comparación predictiva y métricas operativas

La fórmula operativa de inicio permanece fija; las realizaciones de etiquetas cambian por construcción cuando cambia el canal. No afirmar que se conserva el vector de etiquetas. Para evitar comparación circular de scores contra verdades distintas, separar: (a) entrenamiento/evaluación respecto de cada definición, descriptivo y no directamente superior; (b) evaluación común contra referencia externa independiente o control preacordado, pendiente de aprobación. Una referencia C5 común favorece su definición y debe declararse como limitación, no verdad clínica.

Mantener cohorte común elegible, predictores y sus valores, familias, preparación, calendarios, calibración, política de umbral, semillas, presupuesto y métricas. El único factor variado es la parametrización que genera etiquetas. Congelar las variables de canal de X al control o excluirlas uniformemente por acuerdo previo; recalcular simultáneamente X y Y introduciría otro estimando. El método de calibración/selección será común, con parámetros aprendidos solo en desarrollo; no forzar igualdad numérica de calibradores incompatibles ni igualar falsas alertas mirando evaluación.

Utilidad: sensibilidad y precisión de inicios, episodios perdidos, falsas alertas, falsas alertas por municipio-año y anticipación útil con correspondencia alerta/episodio EXP01. Probabilísticas: PR-AUC (convención AP o integral por congelar), Brier, calibración; AUROC solo complemento. Denominadores nulos permanecen no evaluables.

DEC-125 aprueba históricamente +10 puntos porcentuales de sensibilidad frente a persistencia y hasta +5 puntos de razón de falsas alertas; no son criterios para elegir canal ni se transfieren automáticamente a etiquetas EXP01. No existe autoridad suficiente para declarar superioridad/no inferioridad de parametrización: pendientes referencia epidemiológica independiente, presupuesto, márgenes y criterio humano de aceptación.

## Política temporal y pruebas futuras de rechazo

- Historia de cada partición disponible a su corte, trazabilidad de fechas y versiones; ningún percentil usa el mes evaluado ni información futura.
- Rechazar calcular P75 de enero de un año usando ese mismo enero; rellenar enero faltante con el sexto año; o calcular todos los canales con el histórico completo antes de dividir train/test.
- Rechazar exclusión de un año basada en un boletín publicado después del origen si se presenta como operativa.
- Rechazar tratar el antecedente desconocido como no exceso o usar T en lugar de S−1 para inicio T+2.
- 2025 consumido: prohibido para entrenamiento, calibración, ajustes, elección de parámetros, umbrales y champion en EXP03. No consultar sus resultados para diseñar ganadores.
- 2024: estrés retrospectivo posterior al congelamiento; no prueba final ciega. Selección solo en ventanas de desarrollo anteriores al periodo evaluado.
- Confirmación final en datos futuros no utilizados. Todo cambio posterior a estrés requiere nueva versión y nueva confirmación.

## Incertidumbre y multiplicidad

Comparaciones pareadas de municipios y periodos comunes. Bootstrap jerárquico por municipio estratificado por departamento y bloques temporales comunes, preservando episodios, autocorrelación y horizontes solapados; remuestreo temporal sincronizado entre municipios para perturbaciones compartidas. Longitud de bloque, réplicas e intervalos se fijarán con desarrollo. Mostrar distribución municipal/departamental y soporte efectivo; pocos episodios implican conclusión incierta.

Familia primaria: W6–W9 contra C5 para cambio de etiquetas; E5 pertenece a una familia condicional predeclarada antes de resultados. Holm para contrastes inferenciales; no elegir el menor p-valor. Métricas secundarias descriptivas sin reclamos confirmatorios. No seleccionar ventana por AUROC, más inicios ni menor cambio frente a C5; sensibilidad metodológica no establece exactitud ni superioridad científica.

## Riesgos y mitigaciones

| Riesgo | Mitigación concreta |
|---|---|
| Fuga temporal | Linaje por origen y rechazo de ejemplos anteriores. |
| Etiquetas circulares | Clasificación epidémica independiente; separar referencia de evaluación. |
| Estabilidad confundida con exactitud | Referencia externa y decisión humana; no optimizar acuerdo con control. |
| Más brotes confundidos con mejor detección | Denominadores de episodios y carga de falsas alertas explícitos. |
| Exclusión retrospectiva de años difíciles | Regla fechada, autoridad, ámbito y versión previos. |
| Ceros mal clasificados | DEC-120 solo dentro de cobertura; faltantes nunca negativos. |
| Historia insuficiente y baja cobertura | Soporte propio y común, censura y no sustitución. |
| Multiplicidad | Matriz cerrada, Holm, todos los resultados y confirmación independiente. |
| Dependencia EXP01 | Bloqueo hasta interfaces versionadas; cambios invalidan comparabilidad. |
| Extrapolación Umaña/Bortman | No transportar tamaños de efecto ni óptimos a P75 mensual. |
| Cambio de prevalencia | Desgloses temporales/territoriales y calibración; no reajuste en estrés. |
| Reutilización 2025 | Exclusión de selección y de toda ejecución de este diseño. |

## Interfaces requeridas de EXP01

Los nombres siguientes son necesidades contractuales, no módulos existentes inventados.

| Interfaz | Ubicación esperada | Información requerida | Estabilidad requerida | Riesgo de cambio |
|---|---|---|---|---|
| T+1 | PENDING_EXP01 | Fórmula, antecedente y disponibilidad | Contrato aprobado, versión y hash | Etiquetas incomparables |
| T+2 | PENDING_EXP01 | Inicio S/S−1 y anticipación | Contrato aprobado, versión y hash | Fuga o desfase |
| Cohorte | PENDING_EXP01 | Llaves, elegibilidad, faltantes, censura | Llaves congeladas y pruebas | Sesgo de cobertura |
| Calendario | PENDING_EXP01 | Cortes, roles, desarrollo y estrés | Fechas y disponibilidad verificadas | Fuga temporal |
| Comparador | PENDING_EXP01 | Modelo completo y referencia de verdad común | Política aprobada | Circularidad |
| Calibración | PENDING_EXP01 | Método y roles temporales | Contrato y pruebas | Ajuste externo |
| Umbral | PENDING_EXP01 | Presupuesto y selección en desarrollo | Política aprobada | Carga no comparable |
| Métricas por episodio | PENDING_EXP01 | Emparejamiento, duración, anticipación, denominadores | Definiciones aprobadas | Conteo doble |
| MLflow | PENDING_EXP01 | Parent/child, etiquetas, versiones y linaje | Interfaz aprobada | Runs no comparables |

## Decisiones pendientes y preparación

Mauricio deberá aprobar reglas de exclusión epidémica, ámbito y autoridad, suficiencia tras exclusiones, eventual descarte de E5, referencia epidemiológica común, tratamiento de X del canal, criterios metodológicos, márgenes operativos, incertidumbre y multiplicidad. Ninguna variante gana por este diseño.

Para implementar: EXP01 estable, revisión independiente científica, reconciliación de todas las dependencias y autorización humana explícita; entonces crear un protocolo final en PR separado, sin alterar contratos vigentes por implicación.

Para ejecutar: protocolo final aprobado y versionado, ventanas y referencias congeladas, pruebas temporales/ceros/censura acreditadas, cohortes pareadas, registro oficial autorizado y autorización específica de ejecución. No crear protocol.json ni registrar EXP03 ahora. Mantener G5 NOT_APPROVED y Champion no seleccionado.

Este trabajo añade únicamente diseño y matriz. Cero implementaciones de pipelines, cero ejecuciones científicas, cero canales recalculados y cero fits; no se accedió a datos, bundles o MLflow local.
