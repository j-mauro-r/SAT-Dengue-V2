# SAT-Dengue V2 — Stage 2: Data Understanding
## Primera aproximación controlada a los datos

**Estado:** reconocimiento inicial autorizado (pendiente de revisión de resultados)  
**Alcance:** inspección básica de tres archivos existentes  
**Punto de control:** revisión de resultados por ChatGPT antes de profundizar

## 1. Objetivo

Obtener una primera descripción verificable de los datos disponibles y detectar las preguntas que deben resolverse antes de realizar análisis exploratorio, transformaciones o desarrollo de código.

Esta actividad es únicamente el inicio de Stage 2. No pretende completar la etapa ni aprobar el gate **G2 — Data & Target Freeze**.

## 2. Archivos por inspeccionar

- `dengue.csv`
- `dengue_grave.csv`
- `google_earth_engine.csv`

Los dos primeros contienen aparentemente información de dengue y dengue grave; el tercero, información climática. Estas descripciones deben verificarse con el contenido disponible.

**No asumir que un archivo está limpio o listo para modelar por su apariencia o nombre.**

Si los archivos no están disponibles o existen varias versiones, reportar la situación y detener la inspección afectada. No descargar ni sustituir datos por iniciativa propia.

## 3. Alcance y restricciones

Realizar una inspección de solo lectura, utilizando herramientas existentes y el mínimo procesamiento necesario.

- No modificar, sobrescribir, renombrar ni limpiar los archivos.
- No instalar dependencias ni crear scripts, notebooks, pipelines o pruebas.
- No modificar el repositorio fuera de documentación y artefactos internos de DWP autorizados.
- No generar archivos de resultados fuera de los entregables documentales autorizados.
- Si una comprobación requiere código nuevo o un procesamiento considerable, dejarla pendiente y explicar su propósito.

## 4. Comprobaciones de primera pasada

### A. Estructura de cada archivo

Identificar:

- Tamaño del archivo y número de filas y columnas, cuando sea sencillo obtenerlos.
- Separador, encabezados y posibles dificultades de lectura.
- Nombres de columnas y tipos aparentes.
- Una muestra breve de registros que permita comprender su estructura.
- Qué parece representar una fila y si esto puede confirmarse.

Distinguir los tipos observados de su interpretación: por ejemplo, un código municipal puede contener números sin ser una variable numérica.

### B. Cobertura temporal y geográfica

Comprobar:

- Columnas que representan fechas o periodos.
- Formato y frecuencia aparente: diaria, semanal, mensual u otra.
- Periodo mínimo y máximo, si puede determinarse sin transformaciones complejas.
- Campos de departamento, municipio y códigos geográficos.
- Presencia identificable de **Tolima** y **Meta**.

No inferir cobertura completa por encontrar algunos registros. Señalar si faltan elementos para verificarla.

### C. Señales básicas de calidad

Identificar, sin corregir:

- Valores vacíos en campos que parecen esenciales.
- Formatos inconsistentes o valores evidentemente sospechosos.
- Posibles filas repetidas.
- Repeticiones de una posible clave municipio-periodo.
- Unidades, abreviaturas o categorías cuyo significado no esté documentado.

Una clave repetida no debe declararse un error hasta comprender qué representa cada fila. Si se informan conteos, indicar cómo se obtuvieron.

### D. Relación potencial entre los archivos

Evaluar preliminarmente:

- Si dengue y dengue grave comparten estructura y cobertura.
- Si dengue grave podría estar incluido en dengue o representar un conjunto independiente.
- Qué campos permitirían relacionar los datos epidemiológicos y climáticos.
- Si coinciden las unidades temporales y geográficas.
- Si las variables climáticas tienen unidades y método de agregación identificables.

**No sumar casos, unir archivos, agregar periodos ni resolver estas relaciones mediante supuestos.** Presentar las relaciones propuestas como hipótesis cuando falte evidencia.

## 5. Evidencia esperada

Entregar un informe breve con:

1. **Inventario:** archivo, dimensiones disponibles, lectura y estructura.
2. **Descripción por archivo:** columnas, muestra mínima, cobertura y significado aparente de una fila.
3. **Hallazgos prioritarios:** observación, evidencia, posible implicación y duda pendiente.
4. **Compatibilidad preliminar:** posibles campos de relación y obstáculos.
5. **Preguntas para revisión:** decisiones necesarias antes de continuar.
6. **Siguiente paso propuesto:** una actividad pequeña, justificada por los hallazgos.

Separar explícitamente:

- **Confirmado:** respaldado por contenido observado.
- **Hipótesis:** interpretación pendiente de validación.
- **Pendiente:** comprobación que no se realizó.

No incluir registros individuales sensibles en la respuesta; enmascararlos si aparecen.

## 6. Fuera de alcance

En esta primera aproximación no se realizará:

- EDA completo ni elaboración masiva de gráficos.
- Limpieza, imputación, eliminación de duplicados o tratamiento de atípicos.
- Integración de datos o ingeniería de variables.
- Construcción del canal endémico.
- Definición definitiva de la variable objetivo `Y`.
- Selección definitiva de municipios.
- Entrenamiento, evaluación o comparación de modelos.
- Elaboración del Data Contract final.

## 7. Punto de parada y revisión

**Detenerse al entregar el informe de reconocimiento.**

ChatGPT revisará la evidencia con el usuario para decidir qué dudas resolver y qué actividad autorizar a continuación. No continuar automáticamente con limpieza, integración, EDA o modelado.

Esta aproximación se considera completa cuando permite entender qué contienen los archivos, qué permanece incierto y cuál es el siguiente paso razonable. **No equivale al cierre de Stage 2 ni a la aprobación de G2.**

## 8. Entregables documentales autorizados

1. `docs/product/stage-2/DATA-01-Data Understanding.md` (este brief de reconocimiento).
2. `docs/product/stage-2/DATA-01-Initial Recognition Report.md` (informe de reconocimiento inicial).

La ejecución de esta aproximación termina al entregar el informe inicial para revisión.