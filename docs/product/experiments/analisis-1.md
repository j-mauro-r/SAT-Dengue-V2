La lectura conjunta deja una conclusión clara: **EXP00 mostró que los modelos detectan más inicios porque emiten muchas más alertas; EXP01 comprobó que cambiar el objetivo a “inicio directo” no resuelve por sí solo ese problema.** El principal cuello de botella sigue siendo la relación entre detección, falsas alertas y estabilidad temporal.

## Qué aprendimos de EXP00

EXP00 es una línea base histórica negativa, pero muy informativa.

- Los seis modelos aumentaron la sensibilidad frente a persistencia.
- Todos incumplieron el máximo permitido de **+5 puntos porcentuales de FAR**.
- Los intervalos respaldan que existe ganancia de detección, pero también respaldan el aumento de carga.
- Ningún modelo quedó habilitado para ser champion.

Los casos más ilustrativos son:

- **LightGBM T+1:** detectó 34 de 86 inicios, con sensibilidad de 39,53%, pero produjo 218 falsas alertas y FAR de 54,09%.
- **GAM T+2:** alcanzó la mayor sensibilidad, 72,09%, pero emitió alertas en el 67% de los municipio-mes y produjo 406 falsas alertas.
- **GAM T+1** fue el más cercano al límite operativo: excedió el máximo de FAR por 1,72 puntos. Aun así, solo detectó 20 de 86 inicios y produjo 151 falsas alertas.

La mayor sensibilidad de T+2 no demuestra mejor anticipación. T+2 presentó peor AP, AUROC y Brier que T+1 en las tres familias, mientras emitía muchas más alertas. Es compatible con una política más permisiva, no con mayor capacidad discriminativa.

Hay además una particularidad importante: **persistencia T+1 tiene sensibilidad cero por construcción**. En un inicio, el mes anterior no está en exceso; persistencia solo alerta cuando el mes actual ya está en exceso. Por tanto, superar su sensibilidad en T+1 es relativamente fácil. El criterio que realmente discrimina a los modelos es la carga adicional de falsas alertas.

## Qué aprendimos de EXP01

### T+1: resultado concluyente

Dentro de la cohorte que está fuera de exceso en T:

- “Exceso en T+1” significa `Y(T+1)=1`.
- “Inicio en T+1” significa `Y(T)=0` y `Y(T+1)=1`.
- Como `Y(T)=0` ya es condición de entrada, ambos objetivos son idénticos.

El resultado empírico confirmó la identidad matemática: **los dos brazos coincidieron en los 1.902 puntos del frente T+1**, con diferencia exacta de cero en detección, falsas alertas y demás métricas.

Esto permite una decisión concreta: **no necesitamos entrenar dos modelos diferentes para T+1** bajo esta definición de población. Cambiar el nombre del objetivo no añade información ni mejora la anticipación.

### T+2: el objetivo sí cambia, pero la mejora no es estable

En T+2, inicio y exceso son eventos diferentes. Por eso el entrenamiento directo podría aportar valor. Sin embargo:

- En 2020 hubo segmentos favorables para las tres familias.
- En 2022 no existió ningún presupuesto donde el modelo directo detectara más inicios sin aumentar las falsas alertas.
- En 2024 reaparecieron segmentos favorables, especialmente para LightGBM, pero 2024 es estrés retrospectivo conocido.

Todas las familias presentaron ganancias, pérdidas y empates dependiendo del presupuesto. No existe una superioridad general del objetivo directo.

Además, **los intervalos pareados no pudieron calcularse** porque cada ventana contiene un solo año. Esto impide distinguir una mejora reproducible de una fluctuación anual.

### La calibración tampoco transporta bien

En T+2, la probabilidad media de inicio se comportó de forma inconsistente:

- 2020: aproximadamente 23,2% predicho frente a 8,7% observado.
- 2022: aproximadamente 3,9% frente a 9,7%.
- 2024: aproximadamente 22,3% frente a 14,7%.

El modelo sobreestima en dos periodos y subestima en otro. La calibración sigmoid fuera de tiempo no resolvió el cambio entre años.

## Cómo comparar EXP00 y EXP01 correctamente

No debemos afirmar que EXP01 “supera” o “empeora” frente a EXP00 comparando directamente sus porcentajes:

- EXP00 evalúa el año consumido 2025 y sus 912 municipio-mes.
- EXP01 evalúa cohortes de riesgo de 2020, 2022 y 2024.
- EXP00 define la falsa alerta respecto al exceso mensual.
- EXP01 la define principalmente respecto al inicio exacto.
- EXP00 conserva umbrales históricos fijos.
- EXP01 compara frentes completos de presupuestos seleccionados fuera de tiempo.

La relación correcta es conceptual:

1. **EXP00 identificó el problema:** los modelos de exceso contienen señal, pero compran sensibilidad mediante demasiadas alertas.
2. **EXP01 probó una posible solución:** entrenar directamente el inicio.
3. **Resultado:** la solución no cambia nada en T+1 y produce resultados inestables en T+2.

EXP01 mejora el protocolo de evaluación, pero todavía no mejora de forma demostrada el modelo operativo.

## Insights de mayor valor

### 1. Cambiar el objetivo no es el principal camino de mejora

EXP01 reduce la probabilidad de que el problema de EXP00 se explique solamente por entrenar contra exceso mensual. El cuello de botella parece estar más relacionado con:

- información predictiva insuficientemente anticipatoria;
- transporte temporal de probabilidades y umbrales;
- presupuesto operativo no definido;
- heterogeneidad territorial.

Esto da mayor valor al EXP03 de ablación y al experimento de adaptación temporal.

### 2. T+1 y T+2 deben tener estrategias distintas

Para T+1:

- conservar un solo objetivo;
- simplificar el pipeline;
- investigar qué variables aportan señal anticipatoria y cuáles solo describen el estado actual.

Para T+2:

- conservar exceso e inicio como brazos pareados;
- no seleccionar todavía uno como salida definitiva;
- exigir consistencia en varios años antes de adoptar el objetivo directo.

### 3. Debemos fijar primero una carga operativa interpretable

EXP01 compara todos los presupuestos posibles, pero no existe un punto operativo previamente aprobado. Sin ese límite, siempre podemos encontrar algún presupuesto favorable después de ver los resultados.

La próxima decisión debería expresarse en una unidad interpretable, por ejemplo:

- falsas alertas por municipio-año;
- meses bajo alerta por municipio;
- máximo de alertas mensuales que la operación puede investigar.

Después se selecciona el umbral en desarrollo y se evalúa sin modificarlo.

### 4. El ranking de algoritmos es secundario

En EXP00, distintas familias ocupan distintos lugares del frente:

- GAM maximiza sensibilidad T+2;
- XGBoost reduce parcialmente la carga;
- LightGBM ofrece alta sensibilidad T+1.

En EXP01, esas posiciones cambian entre 2020, 2022 y 2024. No hay evidencia de que buscar otra familia de boosting sea la mejora principal.

### 5. El promedio agregado oculta redistribución territorial

En el ejemplo T+2 de 2020 con igual número agregado de falsas alertas:

- Meta redujo falsas alertas sin ganar detecciones.
- Tolima ganó una detección aumentando falsas alertas.

En 2024, algunas mejoras en Meta coexistieron con deterioro en Tolima. Un beneficio agregado puede empeorar el sistema en un departamento.

EXP03 y los siguientes experimentos deberían informar siempre efectos por territorio y perfil de transmisión.

### 6. Necesitamos varios años fuera de muestra

EXP00 mostró deterioro entre desarrollo y 2025. EXP01 mostró que una señal favorable en 2020 desapareció en 2022 y reapareció en el estrés 2024.

La próxima iteración debe producir predicciones fuera de muestra para varios años y calcular incertidumbre sobre ese conjunto. Una ventana anual aislada no basta para decidir.

## Decisiones que podemos tomar ahora

- Mantener **G5 como `NOT_APPROVED`** y champion como `not_selected`.
- No mantener dos objetivos separados para T+1 bajo la cohorte actual.
- Conservar exceso como control obligatorio para T+2.
- No seleccionar un modelo o presupuesto usando los segmentos favorables de 2024.
- Usar EXP00 como contexto histórico secundario, no como control causal de EXP01.
- Orientar EXP03 a descubrir variables que aporten anticipación, especialmente para T+2.
- Priorizar después adaptación temporal de calibración y umbral.
- Reservar información futura realmente no observada para confirmación.

La evidencia está documentada en [EXP00 — conclusiones](/Users/mauriciorodriguez/Projects/AI-Masters/SAT-Dengue-V2/docs/product/experiments/EXP00_historical_baseline/CONCLUSIONS.md), [EXP01 — conclusiones](/Users/mauriciorodriguez/Projects/AI-Masters/SAT-Dengue-V2/docs/product/experiments/EXP01_direct_onset/CONCLUSIONS.md) y el [plan de experimentos](/Users/mauriciorodriguez/Projects/AI-Masters/SAT-Dengue-V2/docs/product/experiments/experimentos.md).