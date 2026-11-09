# SAT-Dengue V2
## Informe científico de cierre

**Proyecto:** desarrollo-de-aplicaciones-maia · **Población:** municipios de Meta y Tolima · **Horizontes:** T+1 y T+2  
**Cierre documental:** 8 de noviembre de 2026 · **Estado científico conservado:** G5 `NOT_APPROVED`; `champion: not_selected`.

**Resultado central.** SAT-Dengue V2 identificó información predictiva retrospectiva y procedimientos que detectan más inicios que el canal endémico. No produjo un champion con utilidad general demostrada. En el benchmark académico, ningún candidato cumplió las tres condiciones agregadas en T+1; los cuatro modelos congelados sí las cumplieron en T+2. Este cumplimiento descriptivo no demuestra estabilidad anual, validación prospectiva ni utilidad sanitaria. Los experimentos posteriores no sustituyeron esa conclusión. [C; B; D1; D2R; D3]

**Alcance y criterio de lectura.** Este informe integra los siete análisis aportados, el contrato aprobado y los resultados publicados del benchmark, BETA, DELTA y los dos EDA. También incorpora EXP-DELTA03, ejecutado y documentado posteriormente a los siete análisis. Es una síntesis científica, no un nuevo entrenamiento ni una reproducción independiente de los datos privados. Los resultados históricos conservan sus poblaciones, denominadores y dictámenes; no se suman como ensayos independientes ni se ordenan mediante porcentajes de cohortes distintas. [A1–A7; D3]

El contrato exige, por horizonte: **A)** detectar más inicios que CHANNEL; **B)** detectar más que PERSISTENCE; **C)** FAR del candidato menos FAR del canal ≤0,05. La FAR es la fracción de alertas emitidas cuyo mes objetivo no está en exceso; no es FPR ni falsas alertas por municipio-año. En T+2 una continuación puede ser correcta respecto al exceso y falsa respecto al inicio. Los controles BETA y por año/departamento complementan esas condiciones, pero no las reemplazan. [C, §§3–8]

La «mejor receta» se entiende como un procedimiento completo: datos, variables, entrenamiento, calibración y regla de alerta. Se distingue la mejor alternativa observada de una propuesta todavía no probada. Cerrar V2 no declara imposibilidad predictiva ni autoriza nuevos experimentos.

# 1. Conclusiones finales

## 1.1. Existe señal predictiva, pero el resultado académico es diferente por horizonte

En la cohorte común del benchmark, G0_OFF detectó 146 de 313 inicios T+1, frente a 94 del canal; su FAR de 55,08 % superó el máximo académico de 52,49 %. En T+2, R0 detectó 86 de 219 inicios frente a 46 del canal, con FAR de 59,65 %, inferior al máximo de 60,34 %. G0_OFF, G0_ON y G1_OFF también cumplieron A/B/C agregadas en T+2. Por tanto, sería incorrecto concluir que ningún modelo aportó nada o que ninguno cumplió el contrato en ningún horizonte. [B]

La conclusión defendible es más precisa: **hay mejoras descriptivas de detección y cumplimiento agregado en T+2, pero no un procedimiento aprobado para ambos horizontes ni una ventaja estable en todos los años y territorios**. El año 2022 incumplió la condición FAR en todos los modelos del benchmark, aun cuando detectaron más inicios que el canal. [B]

## 1.2. El estado epidemiológico y el contexto histórico del mes objetivo son los componentes más reutilizables

EXP01 demostró que, dentro de la cohorte sin exceso en T, inicio y exceso T+1 son el mismo objetivo. EXP03 encontró que añadir el estado contemporáneo elevó la sensibilidad T+1 entre 12,86 y 20,00 puntos porcentuales según la familia. Los P25/P75 históricos del mes objetivo produjeron aportes favorables para LightGBM y XGBoost en los cortes estudiados. Son contribuciones condicionadas, no efectos que puedan sumarse ni una demostración de superioridad universal del algoritmo. [A1; A3]

EXP03.1 no justificó sustituir la referencia por resúmenes semestrales más complejos. EDA-EXP02 identificó una relación débil entre recencia de episodios e inicio —mediana de cinco meses frente a ocho en meses sin exceso—, pero sin demostrar utilidad adicional a la memoria ya disponible. La receta reutilizable conserva estado, rezagos y contexto H5; no acumula transformaciones por su sola plausibilidad. [A4; E2]

## 1.3. Más datos o más variables no garantizaron mejores alertas

La ampliación nacional G1 perdió cinco detecciones y añadió ocho falsas alertas T+1 frente a G0_OFF; en T+2 perdió una y añadió 21. La mejora de AP agrupada T+1 fue engañosa como señal de estabilidad: G1 tuvo menor AP que G0 en cada año por separado. [A7, cap. 3]

La adaptación departamental L1 no mostró una ventaja estable. NB2 produjo distribuciones reproducibles de conteos, pero no cumplió sus criterios conjuntos T+1; sus distribuciones marginales tampoco identificaron la probabilidad de un inicio T+2. Estos resultados no son pruebas contra todo modelo jerárquico o de conteos. [A6, §§C–D]

La información ambiental tampoco obtuvo un respaldo general. BETA mostró un efecto climático distinto por horizonte; el EDA climático encontró asociaciones débiles y solapamiento entre aciertos y errores. EXP-DELTA02-R1 añadió una detección y siete falsas alertas, con señal espacial disponible solo en 481/2.653 observaciones. EXP-DELTA03, con bloques ambientales, territoriales y demográficos, tampoco cumplió A/C. Esto limita las formulaciones ensayadas; **no refuta el papel biológico del clima, toda transferencia nacional ni toda información espacial**. [A6; E1; D2R; D3]

## 1.4. Mejorar probabilidades o reducir alertas no equivale a mejorar la decisión

EXP04 redujo Brier y carga mediante ventanas móviles, pero perdió entre 5,7 y 15,2 puntos de sensibilidad en sus comparaciones. BETA03 ahorró 95/81 falsas alertas T+1/T+2 a costa de 46/29 detecciones. DELTA01 no encontró un umbral académico admisible en dos celdas obligatorias y solo tres de las seis políticas disponibles conservaron el margen de FAR durante evaluación. [A5; A6; D1]

Así, discriminación —ordenar riesgos—, calibración —dar significado a la probabilidad— y decisión —emitir alertas útiles— deben evaluarse por separado. Ninguna métrica probabilística aislada sustituye A/B/C. El criterio relativo frente a CHANNEL también cambia con el periodo: una FAR absoluta menor puede seguir incumpliendo si la del canal disminuye aún más. [A5; D1]

## 1.5. El mayor activo de V2 es una base experimental reproducible, con incertidumbres delimitadas

La tabla canónica, las cohortes emparejadas, los protocolos y las publicaciones inmutables permitieron distinguir mejoras parciales, hipótesis no respaldadas y preguntas no evaluadas. EDA-EXP01 mostró que la prevalencia explica contablemente gran parte de la diferencia territorial de FAR y que los eventos por municipio-año son muy escasos para sostener umbrales municipales libres. EXP02 demostró que cambiar H5 por H9 altera la identidad de los inicios, sin establecer cuál es epidemiológicamente verdadero. [A2; A6; E1]

El cierre correcto es conservar esta evidencia y no fabricar un ganador. **Reproducibilidad técnica, cumplimiento académico descriptivo y aprobación de un champion son estados diferentes.** V2 cierra con resultados válidos para las preguntas ejecutadas, pero sin aprobación de G5, validación prospectiva ni despliegue sanitario demostrado. [C; A7; D3]

# 2. Mejor receta explorada

## 2.1. No existe una receta única ganadora para ambos horizontes

La comparación principal debe hacerse con el benchmark común, no con el mayor porcentaje observado en cualquier experimento. Se evaluaron 2.653 municipio-mes y 313 inicios en T+1, y 2.422 municipio-mes y 219 inicios en T+2, correspondientes a 2020, 2021, 2022 y 2024. Los horizontes no representan exactamente los mismos eventos y no deben sumarse. [B]

**Tabla 1. Resultados T+1 sobre la cohorte común.**

| Procedimiento | Detectados / 313 | Sensibilidad | Falsas alertas de exceso | FAR | A/B/C conjunto |
|---|---:|---:|---:|---:|---|
| CHANNEL | 94 | 30,03 % | 85 | 47,49 % | Referencia |
| R0 / M00–XGBoost | 142 | 45,37 % | 231 | 61,93 % | No |
| G0_OFF regional | 146 | 46,65 % | 179 | 55,08 % | No |
| G0_ON regional | 152 | 48,56 % | 204 | 57,30 % | No |
| G1_OFF nacional | 141 | 45,05 % | 187 | 57,01 % | No |
| DELTA02-R1 espacial | 147 | 46,96 % | 186 | 55,86 % | No |

Fuentes: benchmark [B] y revisión espacial [D2R]. PERSISTENCE emite cero alertas y detecta cero inicios en esta cohorte; su FAR es indefinida. Máximo académico T+1: FAR_CHANNEL +0,05 = 52,4860 %, redondeado a 52,49 %.

**Tabla 2. Resultados T+2 sobre la cohorte común.**

| Procedimiento | Detectados / 219 | Sensibilidad | FP de exceso / FA de inicio | FAR de exceso | A/B/C conjunto |
|---|---:|---:|---:|---:|---|
| CHANNEL | 46 | 21,00 % | 114 / 160 | 55,34 % | Referencia |
| R0 / M00–XGBoost | 86 | 39,27 % | 204 / 256 | 59,65 % | Sí, agregado |
| G0_OFF regional | 62 | 28,31 % | 130 / 161 | 58,30 % | Sí, agregado |
| G0_ON regional | 67 | 30,59 % | 126 / 152 | 57,53 % | Sí, agregado |
| G1_OFF nacional | 61 | 27,85 % | 139 / 182 | 57,20 % | Sí, agregado |

Fuente: [B]. Máximo académico T+2: 60,3398 %, redondeado a 60,34 %. La columna de falsas alertas diferencia meses sin exceso de alertas que no identifican un nuevo inicio. PERSISTENCE mantiene cero detecciones y FAR indefinida.

## 2.2. Mejor resultado académico observado: R0 para T+2

**R0/M00–XGBoost es la receta con mayor detección T+2 entre los cuatro candidatos del benchmark que cumplen A/B/C agregadas.** Detecta 40 inicios más que CHANNEL y su incremento de FAR es 4,31 puntos, dentro del margen de cinco. Cumple el agregado de cada departamento y tres de los cuatro controles anuales. No cumple 2022 y genera la mayor cantidad de falsas alertas de inicio de esos candidatos: 256. [B]

Esta elección es descriptiva y utiliza el criterio «máxima detección entre procedimientos académicamente admisibles en ese horizonte». No constituye una selección formal posterior de champion ni prueba estadística de superioridad. Bajo un criterio distinto, como reducir carga absoluta, cambia la preferencia. G0_ON es la alternativa T+2 de menor carga entre los cuatro modelos: 67 detecciones y 152 falsas alertas de inicio; pierde 19 detecciones respecto a R0, pero elimina 104 de esas falsas alertas. [B]

**Precisión de nomenclatura.** M00 es el brazo de referencia de EXP03.1, construido sobre la configuración completa V09 de EXP03; no es el nombre de un algoritmo distinto ni necesariamente el primer modelo de todo el proyecto. R0 designa la referencia congelada M00/XGBoost con objetivo inicio utilizada después. No deben atribuírsele automáticamente los hiperparámetros o las particiones de G0, que es otro procedimiento. [M; A7, cap. 3]

## 2.3. Mejor base de investigación para T+1: G0_OFF regional

G0_OFF ofrece el punto operativo T+1 más cercano al límite de FAR entre los candidatos del benchmark. Frente a R0 añade cuatro detecciones y elimina 52 falsas alertas. Frente a G1 detecta cinco inicios más y emite ocho falsas alertas menos. Su FAR aún excede el máximo académico en 2,59 puntos porcentuales. [B; A7]

G0_ON detecta seis inicios más que G0_OFF, pero añade 25 falsas alertas. Por ello G0_OFF es la base más parsimoniosa para investigar la brecha T+1, no un ganador absoluto: G0_ON maximiza detecciones y ninguno cumple C. Esta preferencia no borra el resultado favorable del clima en el contraste T+2 ON/OFF. [A6; B]

**Tabla 3. Receta G0_OFF que debe conservarse como referencia.**

| Componente | Configuración efectivamente explorada |
|---|---|
| Algoritmo | XGBoost binario; 80 árboles, profundidad 2, learning rate 0,05; semilla 1729; sin búsqueda de hiperparámetros. |
| Población | Aprendizaje compartido entre los 76 municipios; no 76 modelos independientes. |
| Predictores | 24 variables sin clima: notificaciones actuales de dengue, dengue grave y total; rezagos 1/2/3/12; estado y percentiles del canal; mes; P25/P75 históricos seguros de T+1/T+2. |
| Objetivo | Inicio H5 por horizonte; etiqueta separada de los predictores; elegibilidad sin exceso en T. |
| Datos | Proyección regional canónica identificada; mismas observaciones completas para el contraste OFF/ON. |
| Roles para evaluar Y | Entrenamiento hasta Y−4; calibración Y−3; año Y−2 reservado a adaptación y no utilizado en G0; selección Y−1; evaluación Y, con embargo. |
| Calibración y alerta | Intercepto global regularizado; selector BETA que maximiza detecciones bajo ≤1 falsa alerta de inicio por municipio-año elegible. Este selector no equivale al criterio académico FAR +5 pp. |

Fuente: protocolo BETA01 [P]. En T+1, inicio y exceso coinciden solo dentro de la cohorte vigente. La calibración y el umbral se estiman en sus bloques autorizados; «conservar el método» no significa copiar el mismo valor numérico entre años.

## 2.4. Qué conservar de datos, arquitectura y prácticas

La **canónica regional V1** es la referencia reproducible para los 76 municipios: 17.936 filas y 70 columnas, de las cuales solo la lista autorizada entra al modelo. La **canónica nacional V1** tiene 182.886 filas y 1.122 territorios, pero ese volumen no equivale al entrenamiento efectivo ni a cobertura homogénea: fuera de Meta/Tolima el soporte H5 comienza en junio de 2016. Ninguna tabla es «mejor» por ser más grande. [A6, §E; A7, cap. 3]

La solución técnica más defendible que deja V2 es un **predictor tabular compartido, con datos versionados, calibración y política separadas, comparadores congelados y pipelines Kedro identificables**. Su valor es la reproducibilidad y la posibilidad de aislar cambios; no se probó que esa arquitectura supere universalmente a cualquier alternativa. No se evaluaron un backbone neuronal nacional, una cascada detector–filtro, DeepAR/GRU ni hard-negative mining como soluciones efectivas. [A6, §E; A7, cap. 5]

Se conservan las decisiones sobre claves DIVIPOLA, calendario exacto, ceros epidemiológicos bajo el supuesto aprobado, faltantes climáticos explícitos, H5 fija, separación X/etiquetas, políticas fuera de muestra y publicaciones sin sobrescritura. El supuesto retrospectivo de datos disponibles no demuestra entrega operacional en T. [C; A6]

**Actualización de fuentes.** El repositorio también contiene una canónica nacional V4 extendida hasta 2025, destinada a SAT-Dengue V3. Es una ampliación de datos, no una receta predictiva validada ni una nueva reserva temporal intacta. No sustituye las identidades de los datasets que produjeron los resultados de V2. [V4]

## 2.5. Por qué los últimos experimentos no reemplazan estas referencias

DELTA01 no tuvo una política P1 completa evaluable; DELTA02 original se detuvo por admisión geográfica y su revisión R1, ya entrenada con MGN 2018 fijo, incumplió C. Ambos registros se conservan: un bloqueo metodológico original no equivale al resultado predictivo negativo posterior. [D1; D2; D2R]

EXP-DELTA03 debe leerse con sus propios periodos. En desarrollo 2020–2022, FULL_COMMON detectó 40/210 inicios T+1 y 17/158 T+2, frente a 52/210 y 25/158 del canal; sus FAR fueron 87,84 % y 89,75 %. En el estrés 2024 detectó 15/103 y 8/61, también por debajo del canal. HISTORY mejoró descriptivamente algunos conteos frente a FULL_COMMON, pero sus intervalos de diferencia de sensibilidad cruzaron cero; no se convierte en una nueva referencia ganadora. [D3]

Además, DELTA03 excluyó el conteo contemporáneo y el contexto completo de canal de su bloque HISTORY, amplió el entrenamiento y cambió la representación. El contraste contra G0 no aísla el efecto de «añadir clima»; las ablaciones emparejadas son la evidencia apropiada para cada bloque. Estas tampoco demostraron una contribución estable general. [D3; D3D]

# 3. Mejor receta propuesta — no probada

## 3.1. Propuesta: XGBoost regional T+1 con actualización temporal explícita y base epidemiológica conservada

**Esta es una hipótesis de diseño derivada de la síntesis, no una receta cuya superioridad esté demostrada.** La evidencia no permite prometer un porcentaje de mejora ni presentar una combinación de componentes como «el champion que faltó».

La propuesta conserva la simplicidad de G0_OFF y concentra la intervención en la antigüedad del aprendizaje y la validación temporal del procedimiento completo. No añade automáticamente clima, recencia, vecinos o nuevos bloques ambientales. La justificación es concreta: el protocolo BETA deja el entrenamiento del predictor en Y−4, mientras la calibración y las tasas observadas cambian fuertemente entre años; EXP04 cambió la calibración sobre predictores congelados, no probó de forma aislada esta receta regional actualizada. Eso vuelve razonable la pregunta, pero no demuestra que la antigüedad sea la causa del error. [P; A5; A7, cap. 3; E1]

**Tabla 4. Componentes de la receta propuesta y su fundamento.**

| Componente | Propuesta y condición |
|---|---|
| Objetivo inicial | Resolver T+1 primero, manteniendo H5, P75 y los 76 municipios. T+2 conserva sus referencias y se investiga por separado. |
| Modelo | XGBoost regional compartido, inicialmente con la configuración compacta G0_OFF; sin redes nuevas ni modelos municipales libres. |
| Variables | Conservar exactamente el bloque epidemiológico G0_OFF: estado T, historia rezagada, estacionalidad y P25/P75 seguros. No retirar señales útiles para compensarlas con más variables externas. |
| Entrenamiento | Actualizar el predictor con historia regional más reciente, dejando bloques posteriores y separados para calibración, política y evaluación; duración y frecuencia fijadas antes de ver resultados. |
| Calibración y política | Mantener inicialmente los métodos de referencia para no cambiar todas las capas simultáneamente. Evaluar A/B/C aunque el selector heredado use presupuesto BETA. No asumir que adoptar P1 de DELTA01 resolvería la brecha. |
| Datos | Versión regional identificada con cobertura, madurez y semántica cero/faltante explícitas. Para evaluación operativa, registrar qué valores estaban disponibles al emitir cada pronóstico. |
| Confirmación | Un periodo futuro maduro y no inspeccionado, o seguimiento prospectivo; 2020–2025 ya utilizados no recuperan independencia por redistribuir particiones. |

La mejora postulada no es «recalibrar otra vez» ni «entrenar con toda Colombia». Es comprobar si un procedimiento regional que conserva las variables útiles y renueva su aprendizaje más cerca de la emisión transporta mejor la relación entre riesgo y alerta. **No se identificó en las fuentes revisadas un contraste completo y controlado de esta receta exacta contra G0_OFF.** Si se ejecutara en otra versión, cambiar la distribución de roles tendría que declararse como contraste de procedimientos, sin atribución causal automática a un solo componente.

## 3.2. Qué resultado la respaldaría y qué la refutaría

La respaldaría detectar más inicios que CHANNEL y PERSISTENCE con FAR ≤FAR_CHANNEL+0,05 en la evaluación predeclarada, acompañada de diferencias pareadas frente a G0_OFF y revisión anual/territorial. Conservar o superar su sensibilidad sería una meta adicional, no una nueva condición retroactiva del contrato. Los umbrales absolutos de 52,49 % o 60,34 % pertenecen al benchmark histórico; en otro periodo se recalcula el límite con el canal de ese periodo. [C; B]

No la respaldaría una mejora limitada a Brier/AP, una FAR menor obtenida perdiendo demasiados inicios, un efecto que desaparezca fuera del desarrollo o cobertura insuficiente de los datos necesarios. Si el predictor actualizado tampoco cumple, la hipótesis debe conservar ese resultado sin buscar ventanas hasta obtener una favorable. No hay autorización de implementación dentro del cierre de V2.

# 4. Los tres retos más grandes

## 4.1. Mejorar la separación donde realmente se decide la alerta

Los modelos reconocen parte del riesgo, pero mezclan inicios y no inicios en los niveles de probabilidad que originan las alertas. G0_OFF recupera inicios que CHANNEL omite y pierde otros que el canal detecta. Ni eliminar observaciones cercanas a P75 ni bajar el volumen de alertas ofreció una solución general. El reto es mejorar simultáneamente detección y error relevante, no solo el promedio de probabilidades. [B; E1; D1]

## 4.2. Conservar utilidad cuando cambian el año y la composición territorial

Una política admisible en desarrollo no conservó siempre su carga ni su margen frente al canal. La FAR depende también de la prevalencia y de quién integra la cohorte: el diagnóstico territorial impide atribuir automáticamente peor desempeño a Tolima. Se necesita un procedimiento estable con suficiente evidencia por periodo y territorio, sin responder a la heterogeneidad creando 76 umbrales poco sustentados. [A5; E1; D1]

## 4.3. Conectar el objetivo experimental con una alerta realmente emitible

H5 define un evento reproducible, pero no sustituye la validación externa de brotes. Las notificaciones consolidadas y los agregados climáticos no reconstruyen necesariamente lo conocido en T. La pregunta pendiente es si el sistema distingue el inicio relevante a tiempo para la vigilancia, no simplemente si predice una transición de una serie completada después. Resolverlo requiere evidencia del evento, de entrega del dato y de evaluación futura. [C; A2; A7]

# 5. Tres preguntas clave para una siguiente versión

## 5.1. ¿Actualizar el aprendizaje regional cambia la separación de riesgos o solo su escala?

Debe determinarse si la historia reciente mejora las decisiones sobre los mismos tipos de inicio, manteniendo controladas las variables y sin confundir nuevos parámetros con nueva información. La respuesta debe incluir detecciones y FAR, además de calibración y ordenación, y contrastarse temporalmente fuera de desarrollo. Esta pregunta fundamenta la receta propuesta; su respuesta todavía no está demostrada. [A5; P; E1]

## 5.2. ¿Qué información añade valor después de considerar el estado local y el contexto H5?

No basta encontrar correlación marginal, una diferencia de medianas o una fuente biológicamente plausible. Debe existir aporte incremental bajo cobertura suficiente, con comparadores y roles equivalentes. La pregunta permanece abierta para representaciones espaciales, entomológicas o de episodios, pero sus formulaciones actuales no justifican adopción. DELTA03 reduce la prioridad de incorporar grandes bloques ambientales sin una hipótesis más específica. [E1; E2; D2R; D3]

## 5.3. ¿La mejora persiste sobre eventos y datos que no hayan guiado su desarrollo?

La respuesta requiere un periodo realmente no consumido, desenlaces maduros, documentación de disponibilidad y análisis separado de Meta/Tolima. También exige comprobar qué inicios H5 corresponden al fenómeno de interés sanitario, sin cambiar retrospectivamente las etiquetas del benchmark. Sin esta evidencia puede hablarse de resultados exploratorios, pero no de superioridad general ni de champion operativo. [C; A7]

# 6. Tres limitaciones finales no superadas

## 6.1. Independencia y soporte efectivo insuficientes

Se reutilizaron años, municipios y observaciones a lo largo de una secuencia extensa de decisiones. Los análisis 1–7 son síntesis de esa misma evidencia, no siete replicaciones. En EDA-EXP01, 273/300 municipio-años T+1 y 294/298 T+2 tuvieron menos de tres inicios; la granularidad municipal reduce mucho el soporte de tasas y perfiles. La reproducción exacta no transforma esos datos en confirmación independiente. [A7; E1]

## 6.2. Verdad epidemiológica y disponibilidad operacional no demostradas

H5 permanece como definición experimental sensible a la historia del canal; no se obtuvo adjudicación externa que establezca su superioridad epidemiológica. El supuesto aprobado de disponibilidad retrospectiva hizo posibles las comparaciones, pero no acredita entrega en tiempo real. Los ceros por ausencia de notificaciones, posibles duplicados y correspondencias territoriales son supuestos o límites de las fuentes, no equivalencias demostradas con ausencia de infección. [C; A2; A6; A7]

## 6.3. Cobertura y comparabilidad de las señales adicionales

La historia nacional es desigual; la característica vecina R1 tuvo 81,9 % de faltantes bajo su regla de vecinos completos; el agua superficial de DELTA03 solo tuvo cobertura genuina hasta 2021, con vistas parciales posteriores y resultados 2024 no evaluables para ese bloque. Por ello no se estimó limpiamente el potencial de toda señal externa. También cambiaron características y roles entre procedimientos: comparar sus totales no identifica por sí solo la causa de las diferencias. [A7; D2R; D3]

# 7. Oportunidades de mejora

Estas oportunidades quedan como conocimiento transferible a otra versión. No constituyen tareas pendientes para mantener abierto SAT-Dengue V2 ni una autorización de nuevos experimentos.

## 7.1. Mejoras directamente sustentadas para datos y evaluación

**Conservar el contrato y la identidad de los eventos.** Mantener H5 durante comparaciones y documentar cualquier investigación alternativa como pregunta distinta. Separar inicio, exceso y continuación, así como FAR, FPR y carga. No añadir el presupuesto BETA como condición primaria no aprobada ni omitir los controles territoriales por ser complementarios. [C; A2; B]

**Comprobar cobertura efectiva antes de ajustar.** La fuente nacional tenía filas de calendario, pero R1 no contó con una señal espacial completa en la mayoría de la evaluación. La disponibilidad debe medirse por característica, rol, año y territorio, incluyendo cómo se tratan los indicadores de ausencia. La regla de ceros de la canónica y una regla posterior más estricta para vecinos deben reconciliarse explícitamente antes de otro contraste; no corregirse sobre la marcha ni sobrescribir publicaciones. [A6; D2R]

**Preservar los controles competitivos y todos los artefactos intermedios.** Conservar modelos, scores de selección, calibradores, umbrales y claves a precisión completa. DELTA01 necesitó reconstruir 4.386 scores no persistidos; la reproducción exacta de 5.075 probabilidades de evaluación permitió continuar, pero no demostrar igualdad directa con arrays de selección que nunca se guardaron. Esta es una mejora concreta del proceso, no del algoritmo. [D1]

**Separar disponibilidad y observación.** Incorporar registros de fecha de llegada y revisión de las fuentes en una versión futura. No reemplazar las fuentes consolidadas históricas: mantenerlas para reproducir V2 y admitir nuevas publicaciones de forma explícita. La canónica nacional V4 puede servir de infraestructura de transición, pero su extensión hasta 2025 no genera un bloque de prueba independiente. [C; V4]

## 7.2. Investigación futura que sí merece una hipótesis específica

| Prioridad | Oportunidad | Qué debe cambiar respecto a V2 |
|---|---|---|
| Principal | Procedimiento regional temporalmente actualizado | Conservar señales útiles; estudiar la antigüedad del aprendizaje y medir decisiones, no repetir solo la recalibración. |
| Prerrequisito de confirmación | Evaluación futura y datos disponibles al origen | Reservar evidencia no consumida y registrar emisiones antes del desenlace; separar validez retrospectiva de utilidad operativa. |
| Condicionada | Información externa con cobertura efectiva | No repetir R1 con 18,1 % de disponibilidad ni incorporar todos los bloques de DELTA03 por defecto; exigir una justificación incremental concreta. |
| Condicionada | T+2 como transición temporal coherente | No derivar inicio de dos marginales NB2 ni multiplicarlas sin un modelo de dependencia; mantener el control directo de inicio. |
| Condicionada | Personalización con información compartida | Solo con perfiles históricos y soporte; no convertir el escaso soporte municipal en 76 modelos o umbrales independientes. |

La prioridad no se asigna por novedad del método. Bayes jerárquico, aprendizaje sensible al costo, redes temporales y filtros de falsas alarmas quedaron sin evidencia predictiva suficiente o sin ejecución en esta versión; no deben presentarse como soluciones que fallaron ni como la receta ganadora. [A6; A7]

## 7.3. Qué no conviene repetir sin una pregunta distinta

No se justifica otra búsqueda amplia de algoritmos, añadir más municipios sin controlar la historia y composición, elegir clima por correlaciones de los mismos años, descartar alertas próximas a P75 o modificar umbrales hasta cumplir retrospectivamente. Tampoco debe interpretarse una mejor distribución de conteos como demostración de mejor inicio. Las formulaciones negativas delimitan lo investigado, pero no prueban que todas sus alternativas sean inútiles. [A1–A7; E1; D1; D3]

# 8. Hipótesis final y decisión de cierre

## 8.1. Hipótesis integradora

**La principal limitación pendiente de SAT-Dengue no se explica suficientemente por falta de complejidad algorítmica ni por falta de municipios, sino por una separación incompleta y temporalmente variable de los inicios H5 en la región donde se emiten alertas, combinada con cambios de composición epidemiológica y límites de los datos. Una receta regional que conserve estado T y contexto histórico del mes objetivo, renueve su aprendizaje con cronología explícita y se valide con datos oportunos e independientes podría mejorar el equilibrio entre detección y FAR.**

Esta formulación sintetiza los resultados y propone un mecanismo investigable; **no identifica una causa única demostrada ni garantiza una mejora**. La heterogeneidad, la definición del evento, la cobertura y la política pueden coexistir como explicaciones. La hipótesis sigue abierta tras cerrar V2. [A7; E1; D1; D2R; D3]

## 8.2. Condición de contraste

Para T+1, un futuro procedimiento deberá superar a CHANNEL y PERSISTENCE en inicios detectados y respetar FAR≤FAR_CHANNEL+0,05 en el periodo predeclarado. Se contrastarán sus decisiones con G0_OFF y se informarán ganancias, pérdidas, falsas alertas y resultados por año/departamento. La evidencia deberá distinguir mejora académica agregada de estabilidad y aptitud operacional. Si solo mejoran métricas de probabilidad, si la ventaja no se transporta o si no hay soporte, la hipótesis no recibirá respaldo bajo ese contraste. [C]

T+2 conservará R0 como referencia de mayor detección académicamente admisible en el benchmark y G0_ON como alternativa de menor carga entre los modelos; esto no configura una arquitectura combinada ya validada. La diferencia entre horizontes impide exigir una receta única por conveniencia. [B]

## 8.3. Cierre definitivo de SAT-Dengue V2

**V2 se cierra sin champion, pero con una respuesta científica sustantiva.** El aprendizaje automático aportó detecciones retrospectivas adicionales; T+2 alcanzó cumplimiento agregado del contrato en varios procedimientos, mientras T+1 mantuvo el incumplimiento de FAR. Ninguna ampliación posterior acreditó una solución general estable y oportuna.

Se conservan `G5: NOT_APPROVED` y `champion: not_selected`. El cierre científico no declara aprobación de despliegue ni certifica el estado actual de todos los controles de integración. La receta propuesta y las oportunidades anteriores son hipótesis para otra versión, no condiciones para cerrar esta. La contribución final es saber qué señal se aprovechó, qué formulaciones no funcionaron y qué evidencia falta, sin cambiar la pregunta para presentar un éxito artificial. [C; B; D3]

---

## Fuentes y trazabilidad del cierre

**Base documental.** Los análisis A1–A7 y el contrato corresponden a los archivos adjuntos. Los resultados posteriores se consultaron en `j-mauro-r/SAT-Dengue-V2`; corte de repositorio: `2bea6ac115ad2e80975376a91433ec30e54caaf2`. No se recalcularon los resultados desde los bundles privados. Las pequeñas diferencias aritméticas de tasas se derivan de los conteos publicados y no constituyen una nueva evaluación.

**Jerarquía.** El contrato gobierna aceptación y alcance. Los documentos originales de resultados gobiernan cifras y estados. Los análisis aportan interpretación en la fecha en que se escribieron; sus recomendaciones históricas no se convierten en decisiones vigentes. «No evaluable» no es fracaso predictivo, y «no respaldada» se limita a la formulación y protocolo ejecutados.

| Referencia | Fuente y alcance |
|---|---|
| C | `contrato(1).md`, adjunto. Contrato académico aprobado, §§1–8. |
| A1 | `analisis-1(2).md`, adjunto. EXP00–EXP01: línea histórica, equivalencia T+1 y diferencias de cohortes. |
| A2 | `analisis-2(2).md`, adjunto. EXP02: sensibilidad de la identidad H5/H7/H9. |
| A3 | `analisis-3(1).md`, adjunto. EXP03: ablación de estado, canal y clima. |
| A4 | `analisis-4(1).md`, adjunto. EXP03.1: M00, memoria semestral y cambio de trayectoria. |
| A5 | `analisis-5(1).md`, adjunto. EXP00–EXP04: calibración, carga y detección. |
| A6 | `analisis-6.md`, adjunto. BETA V1, arquitectura realmente implementada y preservación de fuentes. |
| A7 | `analisis-7.md`, adjunto. G1 nacional, comparación controlada y límites de generalización. |
| B | `docs/product/experiments/benchmark/RESULTS.md`. Comparación académica común y estratos. |
| P | `docs/product/experiments/EXP-BETA01/protocol.phase2.json`. Predictores, modelos y roles G0/L1. |
| M | `docs/product/experiments/EXP03.1_add_pass_info/DESIGN.md`. Identidad M00 como referencia V09; su estado preejecución no sustituye las conclusiones posteriores. |
| D1 | `docs/product/experiments/EXP-DELTA01/RESULTS.md`. Recuperación, factibilidad P1 y transporte. |
| E1 | `docs/product/experiments/EDA-EXP01/FINDINGS.md`. F1–F8 y C7.1–C7.5: diagnóstico territorial, temporal y climático. |
| E2 | `docs/product/experiments/EDA-EXP02/PHASE_B_CONCLUSIONS.md`. O2 exploratoria y O1 originalmente no evaluable. |
| D2 | `docs/product/experiments/EXP-DELTA02/CONCLUSIONS.md`. Cierre original en la admisión geográfica; antecedente revisado en el proyecto. |
| D2R | `docs/product/experiments/EXP-DELTA02-R1/RESULTS.md` y `CONCLUSIONS.md`. Candidato espacial ejecutado y cobertura de la característica. |
| D3 | `docs/product/experiments/EXP-DELTA03/PHASE3.md` y `CONCLUSIONS.md`. Ejecución manual del 6 de noviembre de 2026, 108 ajustes y resultados por bloques. |
| D3D | `docs/product/experiments/EXP-DELTA03/DESIGN.md`, bloque HISTORY y transformaciones. Diferencias de representación frente a G0. |
| V4 | `docs/data/canonical-national-table.md`, sección «National V4 through December 2025». Fuente de transición a V3, no evidencia predictiva nueva de V2. |

**Notas de reconciliación histórica.** EXP00 sí utilizó 2025 como evaluación histórica consumida; las frases de análisis anteriores sobre ausencia de resultados 2025 se refieren a rutas posteriores no evaluables. G1 pendiente en BETA V1 fue evaluado después en BETA01 V2. O1 bloqueada en EDA-EXP02 y DELTA02 original fue ejecutada bajo el supuesto autorizado MGN 2018 en DELTA02-R1. Las nuevas pruebas de DELTA03 amplían el cierre más allá de los siete adjuntos; no reescriben sus resultados ni hacen equivalentes sus roles. La canónica V4 no vuelve independiente 2025. [A7, cap. 2; D2R; D3; V4]

**Glosario breve.** Inicio: transición H5 desde no exceso a exceso; exceso: conteo sobre P75 histórico. H5: cinco años de referencia del mismo mes. G0_OFF/G0_ON: procedimiento regional BETA sin/con nueve variables climáticas. G1: expansión nacional del entrenamiento. R0: referencia congelada M00/XGBoost/onset. FAR: falsas alertas de exceso / alertas emitidas. FPR: falsos positivos / observaciones realmente negativas. AP: precisión promedio a lo largo de niveles de recuperación. Brier: error cuadrático medio de probabilidades. Un «fit» es un ajuste por combinación de horizonte/corte/variante, no una arquitectura nueva.
