# SAT-Dengue V2 — Fecha del caso y estrategia geográfica de modelado

Fecha de revisión: 15 de octubre de 2026.

Esta nota registra las decisiones confirmadas por Mauricio y revisa las fuentes del proyecto y los cinco estudios del estado del arte. La elección entre entrenamiento compartido, departamental o municipal permanece abierta. No se analizaron nuevamente los CSV ni se entrenaron modelos. Esta nota no cierra Stage 2 ni aprueba G2.

## 1. Decisiones confirmadas y pendientes

| Tema | Estado | Definición |
|---|---|---|
| Alcance geográfico del producto | Confirmado por Mauricio | Municipios pertenecientes a Tolima y Meta. Las alertas y predicciones se orientan a estos dos departamentos. |
| Unidad de salida | Confirmada por el alcance del producto | Municipio y horizonte T+1/T+2. Una pestaña departamental reúne sus resultados municipales; no obliga a entrenar un modelo departamental. |
| Fecha epidemiológica | Confirmada por Mauricio en esta conversación | Inicio de síntomas. El campo candidato es `INI_SIN`. |
| Significado oficial de `INI_SIN` | Documentado por el INS | Fecha de inicio de síntomas. Falta verificar correspondencia y calidad en los CSV del proyecto. |
| Respaldo temporal | Pendiente | No se autoriza sustituir automáticamente `INI_SIN` por `FEC_NOT` cuando falte o sea inválido. Se debe definir y documentar la política. |
| Geografía epidemiológica | Pendiente | Elegir ocurrencia, residencia o notificación para asignar el caso a un municipio y aplicar el filtro Tolima/Meta. |
| Municipios con predicción válida | Pendiente de calidad de datos | Todos forman parte del alcance geográfico; la posibilidad de emitir una predicción depende de historia, cobertura y calidad suficientes. La ausencia de predicción debe ser explícita. |
| Unidad de entrenamiento | Pendiente | Comparar alternativas compartidas y locales con evidencia. No está aprobado entrenar automáticamente un modelo por municipio ni uno por departamento. |

El [diccionario oficial de SIVIGILA 2018–2020](https://www.ins.gov.co/Direcciones/Vigilancia/Lineamientosydocumentos/3.%20Diccionario_de_datos_Sivigila%202018_2020.pdf), en la sección de datos básicos, identifica `INI_SIN` como inicio de síntomas y distingue esa fecha de la notificación. Su formato documental no demuestra el formato real de nuestros archivos ni sustituye la revisión de versiones históricas.

El inicio de síntomas define a qué periodo se atribuye un caso. La fecha en que el caso estuvo disponible define si podía usarse para una predicción emitida en un corte histórico. Ambas reglas deben mantenerse separadas: un registro notificado después del corte no debe convertirse retrospectivamente en información ya conocida. La fecha de notificación es una referencia útil para este control, pero no reconstruye por sí sola el historial de ajustes del registro.

## 2. Qué dicen las fuentes del proyecto

### Notas de la sesión con el experto

Fuente: [Sesion_1_con_Experto_Notas.docx](/Users/mauriciorodriguez/.codex/.chatgpt-projects/g-p-6a7796c7ddd88191bc71cf8fe4c406e4/sources/Sesion_1_con_Experto_Notas.docx), secciones 3 y 4.

Las notas aconsejan no comenzar entrenando modelos independientes para todos los municipios de Colombia y proponen un piloto reducido, posiblemente de tres municipios, seleccionado con criterios objetivos. Presentan la secuencia municipio → serie temporal → características → modelo → riesgo T+2 y sugieren evaluar el inicio de síntomas como fecha de referencia.

No se encontró una instrucción explícita equivalente a “dos ciudades exigen dos modelos independientes”. La secuencia describe una salida municipal, pero no prueba que los parámetros deban ajustarse por separado para cada municipio. Estas son notas consolidadas, no una transcripción literal de la sesión; la ausencia de la instrucción en ellas no demuestra que el tutor nunca la haya expresado.

La sugerencia histórica de un piloto de tres municipios no modifica el alcance actual confirmado: Tolima y Meta.

### Propuesta de proyecto de grado

Fuente: [Formato-propuesta_Proyecto-de-grado-Mauricio.pdf](/Users/mauriciorodriguez/.codex/.chatgpt-projects/g-p-6a7796c7ddd88191bc71cf8fe4c406e4/sources/Formato-propuesta_Proyecto-de-grado-Mauricio.pdf), páginas 3–7.

La propuesta plantea un panel municipio-mes, comparación de XGBoost, LightGBM y GAM, horizontes T+1/T+2 y evaluación temporal con resultados municipales y agregados. No fija explícitamente si el entrenamiento debe ser compartido o independiente por ubicación. Tener un panel municipal tampoco decide por sí solo esa cuestión.

### Antecedente del microproyecto

Fuente: [Reporte_Entrega3_final-2.docx](/Users/mauriciorodriguez/.codex/.chatgpt-projects/g-p-6a7796c7ddd88191bc71cf8fe4c406e4/sources/Reporte_Entrega3_final-2.docx), sección 3.1 y tabla de fuentes.

El reporte describe una entrada de dos filas, Cali y Bucaramanga, que alimenta el Champion para producir cuatro predicciones: dos municipios y dos horizontes. También documenta `INI_SIN` con notificación como respaldo. Esto es un antecedente de inferencia conjunta; no acredita por sí solo la procedencia exacta de los datos de entrenamiento de cada artefacto. Ni esas ciudades ni el respaldo temporal pasan automáticamente a ser decisiones de V2.

## 3. Qué hicieron los estudios citados

| Estudio | Estrategia geográfica documentada | Implicación para SAT-Dengue V2 |
|---|---|---|
| [Beal et al., 2025](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2024GH001325), secciones 2.1–2.3 | Desarrollan modelos separados por ciudad y mes para Cali, Cúcuta, Medellín y Leticia, con distintos horizontes. Justifican la separación por diferencias de estacionalidad. | Es un precedente de modelos locales. Predice incidencia; sus horizontes y validación no equivalen al objetivo de inicio de brote de V2. Su validación dejando un año fuera no se adopta automáticamente como simulación operativa temporal. |
| [Schlesinger et al., 2024](https://www.frontiersin.org/journals/public-health/articles/10.3389/fpubh.2024.1323618/full), introducción y secciones 2.3–2.5 | Describen EWARS-csd como un marco capaz de modelar municipios conjuntamente con covarianza espaciotemporal. En 11 municipios de Bolívar y Cesar evalúan y optimizan configuraciones por municipio. | Compartir información entre territorios y ajustar umbrales o configuraciones locales son decisiones compatibles. Calibración local no demuestra entrenamiento completamente independiente. El indicador estudiado son hospitalizaciones semanales. |
| [Wu et al., 2025](https://www.pnas.org/doi/10.1073/pnas.2422335122), resultados y métodos | Evalúan pronósticos por ubicación. Incluyen modelos locales y otros con información entre provincias; las variantes VAR se ajustan por país. También comparan configuraciones de ensambles por país y generales. | No representa una elección binaria uniforme entre un modelo local y uno universal. “Evaluación global” o hiperparámetros compartidos no significan un único modelo ajustado con todas las observaciones. Su objetivo son conteos a escala provincial. |
| [Umaña et al., 2026](https://publichealth.jmir.org/2026/1/e79914), métodos | Analizan canales endémicos con datos agregados por municipio de ocurrencia y semana según inicio de síntomas; replican el protocolo a escala departamental. | Respalda considerar inicio de síntomas y ocurrencia. No resuelve el número de modelos predictivos: estudia parametrización del canal endémico y los efectos de la agregación territorial. |
| [Velandia et al., 2026](https://www.nature.com/articles/s41598-026-63542-8), marco experimental y resultados | Comparan un modelo nacional, HDG, con modelos independientes por cada uno de cinco departamentos, LDG. La partición es cronológica y los mismos municipios pueden aparecer en distintos periodos. | Es el antecedente más directo para comparar entrenamiento compartido y departamental. Su clasificación espacial de riesgo con U-Net++ no equivale a anticipar inicios T+1/T+2 ni demuestra transferencia a municipios nunca observados. |

La revisión no identifica una regla científica que obligue a usar un modelo distinto por municipio. Sí muestra razones para evaluar la heterogeneidad territorial y reportar desempeño local, incluso con modelos compartidos. Los resultados de esos artículos no permiten declarar ganadora una estrategia para nuestros datos sin compararla.

## 4. Alternativas para V2

Las alternativas conservan filas municipio-mes y salidas municipales. Entrenar por departamento no significa sumar todos sus municipios para predecir un único total departamental.

| Alternativa | Datos usados para ajustar cada modelo | Ventaja potencial | Riesgo por comprobar |
|---|---|---|---|
| Compartida Tolima + Meta | Series de los municipios elegibles de ambos departamentos | Comparte información cuando hay pocos inicios de brote por municipio. | El desempeño agregado puede ocultar errores persistentes en ciertos municipios o departamentos. |
| Un modelo por departamento | Series municipales de Tolima por un lado y de Meta por otro | Permite relaciones distintas entre departamentos sin fragmentar todas las series. | Reduce información compartida y no garantiza homogeneidad dentro de cada departamento. |
| Un modelo por municipio | Una serie municipal por ajuste | Máxima especialización local. | Pocos meses y pocos inicios independientes pueden dificultar ajuste, calibración y evaluación. |

Ventajas y riesgos son razonamiento metodológico para este proyecto, no resultados experimentales. El número de notificaciones individuales no equivale al número de ejemplos municipio-mes disponibles después de agregar y crear rezagos.

El número de modelos por horizonte y algoritmo es otra decisión. Un modelo compartido para ambos departamentos puede tener un artefacto para T+1 y otro para T+2; por tanto, “compartido” no implica necesariamente un único archivo de modelo.

Una misma corrida mensual puede procesar todas las filas con modelos compartidos o repartirlas entre modelos locales previamente entrenados. La organización de la corrida no determina la unidad de entrenamiento.

## 5. Recomendación pendiente de aprobación y evidencia

Preparar una comparación acotada entre entrenamiento compartido para Tolima + Meta y entrenamiento separado por departamento, manteniendo la unidad municipio-mes. Los modelos independientes por municipio quedarían como alternativa selectiva cuando haya historia y suficientes inicios para sostener la comparación. No se propone construir ahora un sistema jerárquico adicional ni ampliar el entrenamiento a toda Colombia.

Para comparar en la etapa de modelado:

1. Utilizar los mismos municipios, periodos, etiquetas, variables y horizontes en ambas alternativas.
2. Dividir por tiempo con los mismos cortes para todos los municipios; ajustar transformaciones, selección, canales y calibración sin información futura.
3. Reportar inicios detectados y totales, falsas alarmas, PR-AUC y calibración por horizonte, departamento y municipio; acompañar promedios por municipio y resultados agregados.
4. Justificar la selección por estabilidad y utilidad local, no solo por la mejor métrica agregada. Fijar la regla de selección antes de consultar el bloque de prueba final.
5. Conservar canales endémicos municipales como referencia contextual. El método, las ventanas y el manejo de ceros siguen pendientes de su análisis específico.

Esta recomendación no elige un ganador ni autoriza implementación o entrenamiento en Stage 2.

## 6. Próximo paso de Data Understanding

Completar primero la interpretación documental de `INI_SIN`, `FEC_NOT` y las tres geografías epidemiológicas. Luego autorizar una comprobación pequeña, restringida a Tolima y Meta según la geografía elegida, sobre cobertura municipal, calidad de `INI_SIN`, retrasos de notificación e historia útil. Los inicios de brote solo pueden contarse después de definir y validar el canal y la etiqueta.

El resultado permitirá justificar qué municipios tienen información suficiente y diseñar la comparación geográfica de modelos. La decisión final de arquitectura se documentará cuando exista esa evidencia; no se deduce del número de pestañas del dashboard.

## 7. Alcance de esta revisión

Se leyeron las notas del experto, la propuesta y el reporte del microproyecto; se consultaron los métodos de los cinco artículos citados y el diccionario del INS. No se auditaron sus códigos completos, suplementos ni todas sus cifras. No se verificaron los CSV originales, no se ejecutaron nuevos análisis de datos y no se modificaron los archivos sincronizados de `sources/` ni el repositorio `SAT-Dengue-V2`.
