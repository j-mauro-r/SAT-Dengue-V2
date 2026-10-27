**EXP02 añade una conclusión importante: el problema no está solamente en cómo predice el modelo, sino también en cómo definimos aquello que debe predecir.** Cambiar la historia del canal modifica considerablemente la identidad de los inicios y episodios. Sin embargo, **no demuestra que siete o nueve años sean mejores que cinco**.

Revisé `main` en `a1b7413`, el documento de conclusiones y el bundle local existente. Verifiqué la integridad de sus archivos y recalculé los cambios de inicios y AP/Brier de las 54 celdas predictivas. Esas comprobaciones coinciden con el análisis publicado. No reentrené modelos ni modifiqué los resultados. [Conclusiones de EXP02](https://github.com/j-mauro-r/SAT-Dengue-V2/blob/a1b7413017f0874bd25d318663a7c623fc6e857d/docs/product/experiments/EXP02_label_stability/CONCLUSIONS.md).

**Cómo cambia nuestra lectura conjunta**

| Experimento | Pregunta que responde | Hallazgo principal |
|---|---|---|
| [EXP00](https://github.com/j-mauro-r/SAT-Dengue-V2/blob/a1b7413017f0874bd25d318663a7c623fc6e857d/docs/product/experiments/EXP00_historical_baseline/CONCLUSIONS.md) | ¿La línea base ofrece detección con una carga aceptable? | Detecta más inicios que persistencia, pero los seis procedimientos incumplen el límite de falsas alarmas. |
| [EXP01](https://github.com/j-mauro-r/SAT-Dengue-V2/blob/a1b7413017f0874bd25d318663a7c623fc6e857d/docs/product/experiments/EXP01_direct_onset/CONCLUSIONS.md) | ¿Ayuda entrenar directamente para inicio? | En T+1 los objetivos son idénticos bajo la cohorte vigente; en T+2 las ventajas son inestables. |
| EXP02 | ¿Es estable la definición de inicio al cambiar la historia del canal? | Cambian muchos eventos positivos y la estructura de episodios; ninguna alternativa presenta superioridad general. |

Matizo una frase de mi análisis anterior: EXP00 mostró **más detección acompañada de muchas más alertas**. Eso no demuestra que emitir más alertas sea la única explicación de la ganancia. Tampoco EXP02 demuestra que la inestabilidad de las etiquetas haya causado los errores de EXP00 o EXP01.

**1. El hallazgo más valioso: un total parecido puede representar eventos diferentes**

En 2024, pasar de cinco a nueve años cambia el total de inicios de **103 a 110**. Parece una variación pequeña. Pero detrás de ese neto de siete:

- 40 inicios reconocidos con cinco años dejan de serlo.
- Aparecen 47 inicios diferentes.
- Solo 63 coinciden.

**La estabilidad debe evaluarse identificando los mismos eventos, no únicamente comparando sus totales.**

Además, aparecen fragmentaciones y uniones de episodios. Por tanto, cambiar H puede modificar cuándo empieza un episodio, cuánto dura y si dos periodos se consideran uno solo.

Esto respalda la clasificación descriptiva `MATERIAL_INSTABILITY`. Pero no significa que las etiquetas H5 sean incorrectas: **ninguna de las tres definiciones constituye una verdad epidemiológica externa**.

**2. Debemos revisar nuestra hipótesis sobre los ceros**

Inicialmente destacamos P75=0 y transmisión intermitente como posibles focos de inestabilidad. EXP02 muestra que esa explicación es insuficiente.

Por ejemplo, en 2024, al comparar H5/H9, cambia la etiqueta de inicio en:

- **4,96%** de los meses con P75=0.
- **10,24%** de los meses con P75>0.

La tasa también es menor con P75=0 en los otros dos años.

**Insight:** no conviene diseñar toda la solución alrededor de municipios con muchos ceros. Debemos investigar también municipios con transmisión sostenida y cambios en su historia epidemiológica. Los ceros siguen importando para interpretar una alerta, pero no explican por sí solos la sensibilidad observada.

**3. Una métrica mejor puede ocultar que cambiamos la pregunta**

Este es uno de los resultados más instructivos para la tesis:

- El Brier mejora en **36 de 36 comparaciones** alternativas cuando cada modelo se evalúa contra su propia definición.
- Contra una referencia común H5, mejora en 2020/2024, pero **empeora en las doce comparaciones de 2022**.
- La AP contra esa misma referencia mejora solamente en **6 de 36 comparaciones**.

Es como cambiar las respuestas consideradas correctas de un examen y después concluir que el estudiante aprendió más porque obtuvo mejor nota.

La referencia fija permite preguntar si mejora la predicción del **mismo evento**. Aun así, usar H5 como referencia tampoco demuestra que H5 sea epidemiológicamente superior.

**Conclusión:** no debemos elegir siete o nueve años por su menor Brier propio.

**4. La inestabilidad temporal sigue apareciendo**

EXP01 ya mostraba sobreestimación en unos años y subestimación en otros. EXP02 mantiene ese patrón.

En T+1/H5, por ejemplo:

- En 2020, la probabilidad media ronda **31,5%**, frente a **10,4%** de inicios observados.
- En 2022, ronda **4,3%**, frente a **12,8%** observado.

Las historias mayores reducen las probabilidades. Eso es compatible con aliviar la sobreestimación en ciertos periodos y agravar la subestimación en otros.

**Insight:** ampliar la historia del canal no sustituye la investigación sobre calibración y transporte temporal. EXP04 sigue teniendo una justificación fuerte; todavía debemos demostrar qué adaptación funciona.

**5. Una mejora agregada puede perjudicar a un territorio**

El documento identifica 176 puntos favorables frente a H5; **91 presentan deterioro en al menos un departamento**.

Esto refuerza lo que observamos en EXP01: conservar o mejorar el resultado agregado puede redistribuir falsas alertas y detecciones entre Meta y Tolima. Esos puntos están correlacionados y no deben interpretarse como una probabilidad de ganar.

También cambia entre años el departamento más sensible a la definición del canal. **No hay evidencia para declarar permanentemente que un territorio tiene una definición estable y otro inestable.**

**Qué decisiones tomaría para EXP03**

1. **Conservar H5**, por continuidad y trazabilidad, explicitando su sensibilidad. No presentarlo como ganador de EXP02.
2. **Mantener fijas las etiquetas durante la ablación.** EXP03 debe identificar el aporte de las variables; cambiar simultáneamente el objetivo impediría atribuir las diferencias.
3. **Congelar la cohorte y documentar su relación con EXP02.** La intersección 5/7/9 redujo el entrenamiento: en T+1/2020 quedaron 2.608 filas de las 4.358 elegibles. Recuperar historia exclusiva de H5 puede ser razonable, pero los resultados ya no serían una comparación directa con EXP02.
4. **Mantener detección, carga realizada, territorio y consistencia temporal como criterios conjuntos.** AP o Brier por sí solos no resuelven la decisión.
5. **Asegurar reproducción exacta de las alertas guardadas.** EXP02 documenta discrepancias al reaplicar umbrales sobre probabilidades redondeadas. EXP03 ya contempla conservar precisión y reconstruir la selección; esa protección es relevante científicamente.

**Límites que deben acompañar las conclusiones**

Los intervalos predictivos de EXP02 quedaron indisponibles por soporte temporal insuficiente dentro de cada celda anual. Eso no invalida los cambios descriptivos observados, pero impide declarar superioridad estadística. La clasificación de inestabilidad tampoco procede de un umbral de materialidad previamente aprobado.

Además, EXP02 conserva el canal H5 entre los predictores y la elegibilidad basal H5: prueba un cambio de objetivo, **no un sistema completo rediseñado alrededor de H7/H9**. El tratamiento alternativo de años epidémicos sigue pendiente.

**La contribución científica conjunta es concreta:** EXP00 documenta el compromiso entre detección y falsas alertas; EXP01 delimita el valor de cambiar el objetivo; EXP02 demuestra que la definición de los eventos también es sensible. EXP03 debe ahora determinar qué información añade capacidad predictiva **manteniendo explícita y estable esa definición**.