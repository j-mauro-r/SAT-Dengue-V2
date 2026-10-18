# Seguimiento de conclusiones y decisiones — SAT-Dengue V2

> **Nota de integración (18-10-2026):** este archivo se crea como propuesta versionada porque `docs/product/traking-concluciones.md` **no existe en la rama `main` consultada**. Se ha informado de una versión de trabajo local del mismo nombre. **Antes de integrar el PR, reconciliar este contenido con el archivo local y preservar todas sus conclusiones previas.** Este documento no pretende reemplazar ni invalidar el historial local.

## Decisión DEC-Y-2026-10-18-01 — Configuración inicial aprobada de la variable objetivo Y

- **Fecha de aprobación:** 18 de octubre de 2026.
- **Aprobación:** expresa del responsable del proyecto en conversación de seguimiento.
- **Etapa:** Stage 2 — Data Understanding.
- **Estado de la decisión:** **APROBADA como configuración inicial de referencia**; la sensibilidad, los criterios de evaluabilidad y la formalización computacional permanecen pendientes.
- **Alcance:** clasificación binaria de exceso epidemiológico de dengue por **municipio × mes**, con predicción **T+1 y T+2**.
- **No implica:** aprobación del Gate G2, entrenamiento de modelos, selección de umbrales de alerta operativa ni declaración oficial de brote.

### 1. Configuración aprobada

| Parámetro | Decisión aprobada | Precisión |
|---|---|---|
| Unidad geográfica | **Municipio**, identificado mediante código DIVIPOLA | Ámbito del proyecto: Tolima y Meta. |
| Unidad temporal | **Mes calendario** | El panel objetivo se define a escala municipio-mes. |
| Resultado observado | **Conteo mensual de casos de dengue**, según la regla de inclusión de registros del proyecto | Se conserva **2013** y no se excluyen registros/años epidémicos por defecto. La validación de duplicados y la calidad de datos siguen siendo requisitos independientes. |
| Variable objetivo | **Binaria**: `Y=1` exceso; `Y=0` sin exceso | Si la etiqueta no puede evaluarse con datos válidos, **no** se codifica como cero. |
| Canal de referencia | **Percentil 75 (P75)** del histórico | Se utiliza el método de percentiles, **no** el límite superior de Bortman. |
| Regla de decisión | **Exceso si y solo si casos observados > P75** | La igualdad al umbral se clasifica `Y=0`. |
| Ventana histórica inicial | **Cinco (5) años calendario completos**, históricos y disponibles al corte de predicción | La ventana se determina retrospectivamente para cada corte `T`, sin incluir periodos futuros. |
| Agrupación estacional | **Mismo mes calendario** de cada uno de los cinco años de referencia | Enero contra eneros, abril contra abriles, etc.; no agrupar los 12 meses indiscriminadamente. |
| Años epidémicos | **Se incluyen**; no excluir 2013, 2016, 2019, 2023 ni otros años por su condición epidémica | Las exclusiones solo podrían justificarse posteriormente por un problema de calidad demostrado y documentado, no por el resultado de la etiqueta. |
| Actualización | **Recalcular el canal en cada corte temporal** usando exclusivamente historia disponible en ese momento | Obligatorio para evaluación retrospectiva con ventana expansiva y uso prospectivo. |
| Horizontes | **T+1** y **T+2** meses | Ambos se predicen desde el mismo corte `T`. |
| Sensibilidad prevista | **5 años (referencia aprobada) frente a 7 y 9 años** | No cambia la configuración de referencia por sí sola; cualquier revisión requerirá nueva decisión explícita. |

**Alcance de la aprobación:** se aprueba **5 años + mismo mes + P75 + inclusión de años epidémicos** como configuración **inicial**. No se afirma que sea el óptimo empírico para todos los municipios.

### 2. Definición formal de Y y restricción anti-leakage

Sean:
- `m`: municipio DIVIPOLA.
- `T`: mes de corte desde el que se emite la predicción.
- `h ∈ {1, 2}`: horizonte de meses futuros.
- `C(m,T+h)`: conteo observado y validado de casos del municipio `m` en el mes objetivo.
- `H5(m,T+h | T)`: conjunto de **cinco conteos históricos** del **mismo mes calendario** que `T+h`, correspondientes a los **cinco años calendario completos** elegibles según información disponible al corte `T`.
- `P75(H5)`: percentil 75 de esos cinco conteos.

Entonces, para periodos **evaluables**:

```text
Y(m,T+h | T) = 1  si C(m,T+h) > P75(H5(m,T+h | T))
Y(m,T+h | T) = 0  si C(m,T+h) <= P75(H5(m,T+h | T))
Y(m,T+h | T) = NA si no existe observación válida o histórico suficiente
```

**Ejemplo estacional:** para un corte en marzo de 2024 y objetivo abril de 2024, los cinco abriles de referencia son **abril de 2019, 2020, 2021, 2022 y 2023**, siempre que esos datos fueran válidos y estuvieran disponibles en marzo de 2024. No utilizar abril de 2024 para calcular su propio umbral.

**Regla temporal vinculante:** la construcción del umbral de T+1 y T+2 **no puede usar casos de T+1/T+2 ni datos publicados o corregidos después de T como si hubieran estado disponibles en T**. El conteo observado del mes objetivo se consulta **solo después**, para asignar la etiqueta de evaluación; nunca se introduce como predictor en T.

**Interpretación de «años completos»:** usar cinco años calendario **cerrados y disponibles al corte T**, no una ventana móvil de 60 meses indiferenciada. La regla de corte, cierres anuales y rezagos de publicación debe codificarse de forma determinista en el contrato de datos. No asumir disponibilidad instantánea de SIVIGILA.

### 3. Inicio frente a continuación: clasificación retrospectiva

La etiqueta principal es exceso `Y`; **inicio/continuación** es una clasificación secundaria del episodio, no una segunda definición de P75.

| Horizonte evaluado desde T | Inicio | Continuación |
|---|---|---|
| T+1 | `Y(T)=0` y `Y(T+1)=1` | `Y(T)=1` y `Y(T+1)=1` |
| T+2 | `Y(T+1)=0` y `Y(T+2)=1` | `Y(T+1)=1` y `Y(T+2)=1` |

La evaluación retrospectiva de inicio en **T+2** requiere el estado observado de **T+1**. Ese estado es futuro respecto a T y **no debe utilizarse como predictor** en T. Los umbrales usados para estados de meses consecutivos deberán aplicar una política temporal consistente, que se documentará en el contrato.

### 4. Evidencia documental y alcance de cada fuente

| Fuente | Qué respalda | Qué **no** demuestra |
|---|---|---|
| **Notas de sesión con experto**, sección 5, `Sesion_1_con_Experto_Notas.docx` | Objetivo binario exceso / no exceso y comparación con canal endémico. | No fija cinco años ni una agrupación mensual exacta. |
| **Reporte de Entrega 3**, sección 2.1, `Reporte_Entrega3_final-2.docx` | Criterio `casos > P75` para horizonte futuro; T+1/T+2. | No determina la ventana histórica del P75. |
| **Propuesta de grado**, sección 10, `Formato-propuesta_Proyecto-de-grado-Mauricio.pdf` | Validación temporal con ventana expansiva y parámetros recalculados solo con historia permitida; distinción inicio/continuación. | Ventana expansiva **no equivale** a cinco años del canal. |
| **INS (2023), Informe de evento: Dengue, periodo epidemiológico IV**, [PDF oficial](https://www.ins.gov.co/buscador-eventos/Informesdeevento/DENGUE%20PE%20IV%202023.pdf) | Antecedente institucional de canal por medianas/percentiles con límite P75; referencia **semanal** y selección histórica 2015–2022 con exclusión de 2016 y 2019 en ese informe. | **No prescribe** para este proyecto un canal P75 **mensual de cinco años**; otros métodos del INS usan límites distintos. |
| **Umaña y colaboradores (2026)**, *Endemic Channel Parametrization in Dengue Surveillance: Methodological Assessment of Retrospective Windows, Outbreak Trends, and Zero-Case Periods in Colombia*, [artículo](https://publichealth.jmir.org/2026/1/e79914), [DOI](https://doi.org/10.2196/79914) | Relevancia metodológica de la ventana retrospectiva, años epidémicos y periodos de cero casos; se estudiaron ventanas de 5–9 años. | Sus resultados se centran en **Bortman**; **no prueban** que cinco años sea óptimo para P75 mensual municipio-mes. |
| **Registro documental de brotes** (PR #8), [documento](https://github.com/j-mauro-r/SAT-Dengue-V2/pull/8) | Casos externos para contextualización y validación cualitativa. | La fecha de una noticia, alerta o decreto **no es** automáticamente el primer mes con `Y=1`. |

**Fundamento de la selección:** el uso de **P75** proviene de la documentación del proyecto y tiene antecedente oficial; **cinco años y agrupación por mismo mes** son **decisiones metodológicas explícitas del proyecto**, compatibles con las referencias, no una regla nacional obligatoria. La elección inicial se aprueba por criterio del responsable y deberá someterse a sensibilidad.

### 5. Condiciones aún no cerradas (no suponer resueltas)

1. **Convención exacta del percentil:** método de interpolación, manejo de empates y resultado con solo cinco observaciones. Debe quedar fijado y probado para reproducibilidad.
2. **Meses sin registros:** ausencia de notificaciones **no equivale automáticamente a cero**. Resolver continuidad y elegibilidad municipal antes de asignar `Y=0`.
3. **Histórico incompleto:** establecer mínimo de años válidos, qué hacer si falta uno o más de los cinco valores, y desde qué fecha un municipio es evaluable. No imputar ni rellenar silenciosamente.
4. **Baja transmisión:** cuantificar la frecuencia de `P75=0` y el caso de un solo registro que activa exceso; documentar comportamiento por municipio.
5. **Disponibilidad as-of:** definir la fuente y fecha efectiva de disponibilidad, revisiones de datos y criterio de cierre del mes. La ausencia de instantáneas históricas de notificación limita lo que puede probarse sobre disponibilidad real.
6. **Conteo y trazabilidad:** documentar inclusión de tipos de dengue, duplicados, municipios desconocidos, fechas `INI_SIN`/`FEC_NOT`, y calidad de registros, incluyendo la investigación de inconsistencias de 2013.
7. **Coherencia de estados consecutivos:** formalizar cómo se calculan `Y(T)`, `Y(T+1)` y `Y(T+2)` para clasificar inicio/continuación sin introducir referencias futuras.

### 6. Validación de sensibilidad acotada, antes del Target Freeze

**Objetivo:** evaluar estabilidad de la configuración aprobada sin entrenar modelos ni alterar el umbral P75.

| Variante | Ventana histórica | Agrupación | Umbral | Uso |
|---|---:|---|---|---|
| **A — referencia aprobada** | **5 años** | Mismo mes | **P75** | Base de comparación. |
| B | 7 años | Mismo mes | P75 | Sensibilidad. |
| C | 9 años | Mismo mes | P75 | Sensibilidad. |

**Salidas mínimas:** cobertura de municipio-mes evaluables y no evaluables; proporción de meses `Y=1`; cambios de etiqueta respecto a A; número y distribución de inicios/continuaciones; casos `P75=0`; análisis por municipio y nivel de transmisión. Mantener constantes fuente, conteo, criterios de calidad y política temporal. **No entrenar modelos** en esta actividad.

**Regla de gobernanza:** A es la configuración inicial **aprobada**. Los resultados de B/C no la sustituyen automáticamente; cualquier cambio requiere justificación y nueva aprobación explícita.

### 7. Estado de cierre de Stage 2

- **Definición conceptual de Y:** **APROBADA**.
- **Regla estricta `conteo > P75`:** **APROBADA**.
- **Configuración inicial `5 años / mismo mes / sin excluir años epidémicos`:** **APROBADA**.
- **Horizontes T+1 y T+2:** **APROBADOS**.
- **Validación de sensibilidad y condiciones de evaluabilidad:** **PENDIENTES**.
- **Contrato de datos/objetivo, controles anti-leakage y evidencia del Gate G2:** **PENDIENTES**.
- **Gate G2 — Data & Target Freeze:** **NO APROBADO**.

**Próxima acción mínima:** documentar la convención exacta de P75 y las reglas de meses no observados/histórico insuficiente; luego ejecutar una única sensibilidad controlada 5/7/9 años y revisar los resultados antes del freeze.

---

*Registro de decisión: la aprobación se refiere a la **configuración inicial** y no constituye certificación de desempeño ni clasificación epidemiológica oficial del INS.*
