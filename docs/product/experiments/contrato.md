# SAT-Dengue — Propuesta de contrato académico de evaluación

**Versión propuesta:** 1.0  
**Estado:** Aprobado
**Alcance:** Meta y Tolima, horizontes T+1 y T+2

### 1. Pregunta central

¿Los modelos de aprendizaje automático permiten detectar una proporción mayor de nuevos inicios de brote que el canal endémico y la persistencia, sin incrementar la tasa de falsas alarmas en más de cinco puntos porcentuales respecto al canal?

### 2. Unidad de análisis

Una predicción corresponde a:

**Municipio DIVIPOLA + mes de origen T + horizonte de predicción.**

Cada alerta se refiere a un mes objetivo determinado. No se contabilizará una continuación de brote como un nuevo inicio.

### 3. Definición del evento

Conservar H5 y el percentil 75 como referencia epidemiológica principal para la comparación actual.

- **T+1:** el municipio no está en exceso en T y entra en exceso en T+1.
- **T+2:** respetar la transición H5 vigente de inicio en T+2, sin contar una continuación iniciada en T+1.

La cohorte principal estará formada por municipios-mes sin exceso en T y con desenlace evaluable.

Para determinar los resultados reales se podrán consultar los meses posteriores; esos resultados futuros jamás podrán utilizarse para construir las predicciones emitidas en T.

H5 seguirá siendo una definición experimental, no una verdad epidemiológica externamente validada.

### 4. Comparadores obligatorios

**C0 — Canal endémico**

Reconstruir la regla anticipatoria utilizada en el informe académico: comparar la información epidemiológica conocida en el origen T con el P75 histórico correspondiente al mes objetivo.

Verificar la implementación exacta y calcular el P75 usando exclusivamente historia permitida hasta T.

**C1 — Persistencia**

Reproducir la regla histórica de alertar según el estado epidemiológico de exceso conocido en T, para el horizonte correspondiente.

No utilizar estados futuros para construir esta alerta.

**C2 — R0 histórico**

Conservar la referencia M00/XGBoost/onset y sus predicciones congeladas.

**C3 — G0 regional**

Conservar el modelo XGBoost de BETA01 V1, incluyendo las variantes OFF/ON existentes, sin reentrenarlas.

**C4 — G1 nacional**

Utilizar las predicciones congeladas de BETA01 V2 únicamente sobre observaciones exactamente comparables.

Los modelos R0, G0 y G1 no sustituyen al canal ni a persistencia.

### 5. Métricas principales

**Sensibilidad de inicio**

\[
S=\frac{\text{Inicios detectados}}{\text{Inicios reales}}
\]

**Tasa de falsas alarmas (FAR)**

Para reproducir el informe académico original:

\[
FAR=\frac{\text{Alertas emitidas cuando no hay exceso}}{\text{Total de alertas emitidas}}
\]

La FAR se calculará respecto al mismo evento y sobre la misma cohorte para todos los comparadores.

Separadamente, reportar falsas alertas respecto al objetivo específico de inicio, porque una alerta de continuación puede ser correcta respecto al exceso, pero no anticipar un nuevo brote.

También reportar:

- Inicios detectados y omitidos.
- Falsas alertas absolutas.
- FA por municipio-año elegible.
- Precisión de inicio y Brier/AP, cuando existan probabilidades.
- Resultados por año, horizonte y departamento.

Si un procedimiento no emite alertas, FAR y precisión tendrán denominador cero y se informarán como no definidas, no como cero automáticamente.

### 6. Reglas primarias de aceptación

Para cada horizonte, el candidato deberá cumplir simultáneamente:

**Condición A — Superar el canal**

\[
TP_{\text{modelo}}>TP_{\text{canal}}
\]

**Condición B — Superar persistencia**

\[
TP_{\text{modelo}}>TP_{\text{persistencia}}
\]

**Condición C — Respetar el margen de falsas alarmas**

\[
FAR_{\text{modelo}}-FAR_{\text{canal}}\leq 0,05
\]

El margen es de cinco puntos porcentuales, no un incremento relativo del 5 %.

Estas tres condiciones reproducen el objetivo académico presentado. Los criterios adicionales de BETA y los controles por año/departamento permanecen como evaluaciones complementarias, sin modificar los criterios originales.

### 7. Reglas temporales

Separar cronológicamente entrenamiento, calibración, selección de umbral y evaluación.

Los umbrales de los modelos deben elegirse exclusivamente en datos de desarrollo anteriores al periodo evaluado.

El canal y la persistencia deben utilizar únicamente información permitida en T.

Los resultados retrospectivos de 2020, 2021, 2022, 2024 y 2025 ya han contribuido a la investigación. No podrán presentarse como confirmación independiente nueva.

Se deberá distinguir entre predicción retrospectiva con información consolidada y anticipación operativa con datos efectivamente disponibles al cierre del mes.

### 8. Condiciones de aprobación científica

El benchmark permitirá establecer si se cumplen descriptivamente las tres reglas originales.

No permitirá, por sí solo, declarar:

- Superioridad estadística sin incertidumbre estimable y suficiente soporte.
- Desempeño prospectivo.
- Disponibilidad histórica operacional.
- Eficacia sanitaria o clínica.
- Aprobación automática de G5 o selección de champion.

**G5 permanece `NOT_APPROVED` y `champion: not_selected` hasta satisfacer los requisitos de gobernanza correspondientes.**