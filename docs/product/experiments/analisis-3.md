La lectura conjunta es bastante clara: EXP03 encontró señales útiles, pero también confirmó que el principal problema de SAT-Dengue ya no es simplemente “escoger mejores variables”. El reto central es lograr que esas señales mantengan su utilidad entre años y territorios, con una cantidad controlable de falsas alertas.

## Cómo encajan los cuatro experimentos

| Experimento | Pregunta principal | Resultado |
|---|---|---|
| EXP00 | ¿La línea base detecta inicios con carga aceptable? | Detecta más que persistencia, pero todos los modelos generan demasiadas falsas alertas. |
| EXP01 | ¿Entrenar directamente para inicios resuelve el problema? | No en T+1; en T+2 los beneficios cambian según año, familia y presupuesto. |
| EXP02 | ¿Es estable aquello que llamamos “inicio”? | No completamente. Cambiar la historia del canal modifica muchos inicios y episodios. |
| EXP03 | ¿Qué grupos de información aportan capacidad predictiva? | Estado actual y umbrales históricos aportan señal, pero su beneficio depende del horizonte, familia, año y territorio. |

La secuencia científica es:

```text
EXP00: existe señal, pero cuesta demasiadas alertas
          ↓
EXP01: cambiar el objetivo no resuelve el problema
          ↓
EXP02: además, la definición del evento es sensible
          ↓
EXP03: ciertas variables ayudan, pero no transportan de forma estable
```

## Qué encontró realmente EXP03

### 1. El estado epidemiológico actual ayuda principalmente en T+1

P1 compara:

- Base rezagada: información conocida hasta T−1.
- Base más estado actual: casos, tendencias, zona y razón observados/esperados en T.

En T+1, añadir el estado actual aumentó la sensibilidad entre:

- GAM: +15,71 puntos porcentuales.
- LightGBM: +12,86 pp.
- XGBoost: +20,00 pp.

La dirección fue positiva en 2020, 2021 y 2022 para las tres familias.

Además, GAM y LightGBM detectaron más inicios reduciendo la carga agregada de falsas alertas. Esto demuestra que no toda ganancia de detección se explica simplemente por emitir más alertas.

En T+2, en cambio, el efecto fue prácticamente nulo o negativo: entre −3,16 y +1,90 pp.

**Insight:** la fotografía epidemiológica de T parece útil para anticipar el mes inmediatamente siguiente, pero pierde valor para mirar dos meses adelante.

Esto no significa todavía que sea una alerta operativamente temprana: tanto las variables actuales como la condición Y(T)=0 requieren que los datos de T estén disponibles y consolidados.

### 2. Los umbrales históricos del mes objetivo son la señal más prometedora para boosting

P4 añade a la base los P25/P75 históricos correspondientes al mes que se quiere predecir.

Resultados:

| Familia | T+1 | T+2 |
|---|---:|---:|
| LightGBM | +24,29 pp | +25,32 pp |
| XGBoost | +27,62 pp | +20,89 pp |
| GAM | −1,90 pp | +2,53 pp |

En LightGBM y XGBoost, el efecto fue positivo en los tres años de desarrollo y en ambos horizontes.

Esto es relevante porque los umbrales proporcionan al modelo el contexto estacional del evento futuro: no solo “cuántos casos hay ahora”, sino “qué nivel sería anormal para el mes que viene”.

Pero hay una cautela: el resultado objetivo también se define usando el canal endémico. Por tanto, estos umbrales pueden ayudar a representar mejor la frontera matemática de la etiqueta. EXP03 no demuestra que sean un factor epidemiológico causal independiente.

**Insight:** para boosting, el contexto histórico del mes objetivo parece más valioso y más transportable que añadir clima de forma aislada.

### 3. El clima no presenta una mejora general

Añadir clima rezagado produjo efectos mezclados:

- En T+1, las diferencias fueron pequeñas o negativas.
- En T+2, LightGBM ganó 11 detecciones y XGBoost 16.
- Pero esas ganancias costaron 138 y 153 falsas alertas adicionales, respectivamente.
- En el estrés 2024, ambos efectos T+2 se revirtieron a −11,48 pp.

**Insight:** el clima puede contener señal en determinados periodos, pero EXP03 no respalda incorporarlo como una mejora general. Parte de su aparente beneficio provino de operar con mucha más carga y estuvo dominado por 2022.

No conviene eliminarlo definitivamente, pero sí tratarlo como una señal condicionada que requiere mejor control temporal y operacional.

### 4. El canal completo no debería eliminarse

Los contrastes secundarios muestran que retirar todo el canal del modelo completo reduce la detección en las seis combinaciones de familia y horizonte.

Sin embargo, retirar componentes individuales produce resultados distintos:

- El canal reciente podría ser prescindible en algunos modelos T+1.
- Las razones observados/esperados pueden ayudar en T+2, pero ser redundantes o perjudiciales en T+1.
- El clima podría retirarse en T+1 sin una pérdida importante, pero no se ha demostrado equivalencia.
- Los umbrales históricos parecen especialmente importantes para boosting.

**Insight:** no debemos preguntar “¿sirve el canal completo?”. La pregunta útil es “¿qué partes del canal aportan valor en cada horizonte?”.

Esto abre una posible simplificación posterior, pero requeriría márgenes de no inferioridad definidos previamente.

## Qué aprendimos sobre falsas alertas

EXP03 fijó un presupuesto común de una falsa alerta por municipio-año durante la selección. Sin embargo, el umbral congelado no conservó siempre esa carga en los años evaluados.

Por ejemplo:

- En T+1/2020, 47 de 48 celdas superaron una falsa alerta por municipio-año.
- En T+2/2022, 43 de 54 superaron ese valor.
- Los umbrales cambiaron considerablemente entre años.
- En 2022, las probabilidades y umbrales fueron mucho menores que en 2020 o 2024.

La analogía sería ajustar una alarma para que produzca máximo una falsa activación en una prueba de laboratorio, pero al instalarla en otro edificio comienza a sonar dos o tres veces más.

**Insight:** EXP03 confirma el problema central de EXP00: seleccionar un umbral con una carga determinada no garantiza que esa carga se conserve en otro año.

Esta es una justificación fuerte para EXP04: adaptación temporal de calibración y umbral.

## Qué aprendimos sobre estabilidad temporal

Algunas señales fueron relativamente consistentes:

- Estado actual en T+1: dirección positiva en los tres años.
- Umbrales históricos con boosting: dirección positiva en ambos horizontes y los tres años.

Otras fueron inestables:

- Estado actual en T+2.
- Clima, especialmente en boosting T+2.
- Algunas partes del canal reciente.
- Calibración y nivel de las probabilidades.

En 2024:

- El estado actual siguió ayudando en T+1, pero ahora aumentó la carga en las tres familias.
- Las mejoras climáticas T+2 se revirtieron.
- Los umbrales históricos mantuvieron dirección favorable en boosting, aunque con magnitudes y cargas diferentes.

**Insight:** una variable puede contener señal predictiva y, al mismo tiempo, no tener un comportamiento operativo estable.

## Qué aprendimos sobre territorio y perfiles

Todos los guardrails por perfil de transmisión fallaron. Algunos guardrails por departamento también fallaron.

Esto no significa que todas las variables perjudiquen a todos los perfiles. Significa que ninguna comparación primaria consiguió demostrar simultáneamente:

- mejora agregada;
- carga aceptable;
- consistencia por departamento;
- consistencia por perfil;
- soporte suficiente.

Una mejora global podía coexistir con:

- más falsas alertas en un perfil;
- pérdida de detecciones en otro;
- resultados distintos entre Meta y Tolima.

Esto reproduce lo observado en EXP01 y EXP02.

**Insight:** el modelo compartido puede aprender señal válida, pero su calibración o utilidad probablemente no sea homogénea para todos los territorios.

Esto justifica EXP05, pero todavía no justifica entrenar modelos separados ni retirar municipios con muchos ceros.

## Relación con EXP00

EXP00 encontró que todos los modelos detectaban más inicios que persistencia, pero compraban esa sensibilidad con una carga excesiva:

- Sensibilidades entre 23,26% y 72,09%.
- Entre 151 y 406 falsas alertas.
- Ninguno cumplió la política de aceptación.

EXP03 matiza ese resultado:

- Algunas variables sí permiten ganar detección reduciendo falsas alertas, especialmente el estado actual en T+1.
- Otras reproducen el comportamiento de EXP00: más detección a cambio de mucha más carga, como el clima en boosting T+2.
- El problema no es únicamente que el modelo emita muchas alertas; también importa qué información recibe y si el umbral transporta.

## Relación con EXP01

EXP01 demostró que:

- En T+1, predecir inicio y exceso es exactamente el mismo problema bajo la cohorte Y(T)=0.
- En T+2, predecir directamente el inicio puede ayudar, pero no de manera estable.

EXP03 confirma esa lectura:

- Conservó un solo objetivo en T+1.
- En T+2, los controles inicio frente a exceso siguieron mostrando intercambios entre detección y carga.
- Cambiar el objetivo no reemplaza la necesidad de mejores variables, calibración y umbrales transportables.

**Insight:** el objetivo directo de inicio puede ser útil en T+2, pero no es por sí solo la solución operacional.

## Relación con EXP02

EXP02 mostró que cambiar la ventana histórica de cinco a siete o nueve años modifica la identidad de muchos inicios y episodios.

EXP03 mantuvo H5 fija. Esto fue metodológicamente correcto porque permitió atribuir las diferencias a las variables y no a un cambio simultáneo en la definición de Y.

Por eso:

- EXP03 no demuestra que H5 sea epidemiológicamente superior.
- Sus conclusiones están condicionadas a la definición H5.
- Los buenos resultados de los umbrales históricos no resuelven la inestabilidad de etiquetas identificada por EXP02.

**Insight:** el modelo parece beneficiarse de conocer mejor la frontera H5, pero seguimos necesitando una validación epidemiológica externa de esa frontera.

## La gran conclusión conjunta

Los cuatro experimentos descartan explicaciones demasiado simples:

- No basta con cambiar de algoritmo.
- No basta con cambiar el objetivo a inicio.
- No basta con ampliar la historia del canal.
- No basta con añadir clima.
- No basta con fijar una carga en selección.
- No conviene eliminar municipios con muchos ceros.

La evidencia apunta a tres problemas conectados:

1. **Señal:** el estado actual y los umbrales históricos contienen información útil.
2. **Transporte:** probabilidades, calibración y umbrales cambian entre años.
3. **Heterogeneidad:** el beneficio agregado no se distribuye igual entre territorios y perfiles.

## Decisiones que ya podemos tomar

- Mantener H5 fija para comparar las próximas iteraciones.
- Priorizar el estado actual para T+1.
- Conservar los umbrales históricos del mes objetivo, especialmente con boosting.
- No usar clima como mejora general sin una nueva comprobación controlada.
- No retirar el canal completo.
- Mantener el control onset/exceso en T+2.
- Evaluar siempre detección y carga conjuntamente.
- Informar resultados por año, departamento y perfil.
- Priorizar EXP04 sobre transporte temporal y EXP05 sobre heterogeneidad.
- Mantener G5 `NOT_APPROVED` y champion `not_selected`.

## Lo que aún no podemos concluir

- Que exista una variante ganadora.
- Que LightGBM o XGBoost sean superiores en general.
- Que las mejoras sean prospectivamente estables.
- Que el sistema respete una carga operativa real.
- Que el clima sea inútil.
- Que un bloque sea equivalente y pueda eliminarse.
- Que deban excluirse municipios con muchos ceros.
- Que T+2 proporcione dos meses reales de anticipación.
- Que exista desempeño válido en 2025.

La ruta de transporte 2024–2025 quedó `not_evaluable` por cobertura o madurez no verificadas. Los resultados válidos de 2024 corresponden únicamente al estrés retrospectivo del motor. No existen métricas científicas válidas de benchmark 2025.

En una frase: **EXP03 encontró qué información parece útil, pero también mostró que la próxima mejora importante no consiste en añadir más variables, sino en conseguir que la señal identificada mantenga calibración, carga y utilidad entre años y territorios.**