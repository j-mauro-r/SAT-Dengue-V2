Mauricio, usando exclusivamente los archivos adjuntos, **EXP03.1 cambia de forma importante la lectura acumulada de EXP00–EXP03, pero no cambia la decisión de no seleccionar champion**.

## 1. Conclusión ejecutiva

La secuencia completa queda así:

| Experimento | Evidencia principal | Conclusión |
|---|---|---|
| **EXP00** | Los modelos aumentan detección, pero todos exceden la carga permitida de falsas alertas. analisis-1 | Existe señal predictiva, pero no utilidad operativa demostrada. |
| **EXP01** | T+1: predecir exceso e inicio es equivalente bajo la cohorte vigente. T+2: resultados variables entre años y presupuestos. analisis-1 | Cambiar el target no resuelve el problema. |
| **EXP02** | Cambiar H5/H7/H9 modifica sustancialmente la identidad de inicios; ninguna ventana domina. analisis-2 | La propia definición del evento es inestable. |
| **EXP03** | Estado actual y P25/P75 aportan señal; clima y otros componentes son inconsistentes. analisis-3 | Existen variables útiles, pero su utilidad no transporta uniformemente. |
| **EXP03.1** | Memoria reciente produce una ganancia mínima; añadir cambio semestral deteriora onset. CONCLUSIONS | La trayectoria del canal **no resuelve** el problema de estabilidad/carga. |

La evidencia acumulada ahora descarta otra explicación sencilla: **no basta con añadir memoria temporal del canal endémico**.

---

# 2. Hallazgos confirmados de EXP03.1

### A. M01 — memoria reciente: señal real pero prácticamente marginal

**Evidencia**

M01 frente a M00:

- detecciones: **662 → 667: +5**;
- falsas alertas: **1.684 → 1.742: +58**;
- alertas totales: **2.346 → 2.409: +63**;
- sensibilidad macro: **+0,000769**;
- precisión macro disminuye. CONCLUSIONS

Además, 55 de las 58 falsas alertas adicionales aparecen sobre periodos de **no-exceso**. CONCLUSIONS

**Interpretación**

Existe una señal incremental en la frecuencia reciente de estados del canal, pero es **demasiado pequeña respecto al coste operacional**.

No es equivalente a “la memoria no contiene información”. Sí contiene alguna información; lo que EXP03.1 demuestra es que **esta representación no consigue convertirla en una mejora suficientemente limpia y estable**.

---

### B. El pequeño beneficio de memoria se concentra más en T+2

**Evidencia**

Q1:

- T+1: +2 detecciones, +38 falsas alertas; la sensibilidad macro incluso baja ligeramente.
- T+2: +3 detecciones, +20 falsas alertas y sensibilidad macro **+0,002323**. CONCLUSIONS

**Interpretación**

La memoria reciente parece conceptualmente más prometedora para **T+2 que T+1**, pero el efecto observado es demasiado pequeño para justificar una nueva configuración.

Esto complementa EXP03: allí el **estado contemporáneo T** era fuerte principalmente para T+1, mientras que aquí una representación de historia reciente ofrece algo más de señal relativa en T+2. EXP03 había mostrado aumentos T+1 de +12,86 a +20 pp al añadir estado actual, frente a efectos casi nulos en T+2. analisis-3

---

### C. M02 — cambio entre semestres: hipótesis rechazada en su formulación actual

**Evidencia**

M02 frente a M01:

- −15 detecciones;
- −28 falsas alertas;
- −43 alertas;
- sensibilidad macro −0,008923. CONCLUSIONS

Frente a M00:

- −10 detecciones;
- +30 falsas alertas;
- +20 alertas;
- sensibilidad macro −0,008154. CONCLUSIONS

**Conclusión**

El descriptor de **“cambio del semestre reciente respecto al anterior” no aporta valor general para onset**.

La disminución de alertas de Q2 no representa una mejora porque simultáneamente desaparecen detecciones verdaderas.

---

# 3. Qué confirma EXP03.1 de lo aprendido anteriormente

## 3.1 El problema principal sigue siendo transporte y estabilidad

EXP00 reveló el conflicto detección–falsas alertas. EXP01 mostró problemas de transporte de probabilidades entre años. EXP03 demostró que incluso seleccionando bajo una falsa alerta por municipio-año, esa carga no se conserva necesariamente en otros periodos. analisis-1 analisis-3

EXP03.1 vuelve a encontrar:

- resultados que cambian por año;
- cambios por familia;
- diferencias T+1/T+2;
- heterogeneidad territorial;
- cambios de signo entre cortes. CONCLUSIONS

**Interpretación:** tenemos cada vez más evidencia de que el cuello de botella no es exclusivamente representación de variables. Es **transportabilidad temporal y territorial de la regla de decisión**.

---

## 3.2 La heterogeneidad territorial ya es un resultado recurrente, no una anomalía aislada

EXP01 mostró redistribución distinta entre Meta y Tolima. EXP02 encontró que 91 de 176 puntos favorables agregados deterioraban al menos un departamento. EXP03 falló guardrails por perfiles y algunos por departamento. analisis-1 analisis-2 analisis-3

EXP03.1 repite el patrón. En Q1, Meta presenta más comparaciones municipales con menor sensibilidad que con mayor sensibilidad, mientras Tolima muestra el patrón contrario; Q2 y Q3 tampoco son uniformes. CONCLUSIONS

**Conclusión científica:** el supuesto de una única relación predictor→riesgo→umbral suficientemente homogénea para todos los municipios se debilita.

Esto **fortalece EXP05**.

---

## 3.3 EXP03.1 no invalida los mejores hallazgos de EXP03

Esto es importante.

EXP03 había identificado como señales más prometedoras:

1. **estado actual T para T+1**;
2. **P25/P75 del mes objetivo, especialmente con boosting**. analisis-3

EXP03.1 no vuelve a evaluar si esos hallazgos son superiores; usa M00 como referencia ya construida sobre EXP03.

Por tanto:

> **EXP03.1 no refuta estado actual ni P25/P75. Refuta que añadir encima de ellos esta formulación de trayectoria reciente produzca una mejora general.**

---

# 4. Insight científico nuevo más importante

La secuencia EXP03 → EXP03.1 permite separar tres tipos de información:

### **Estado**
“¿Dónde estamos ahora?”

EXP03 mostró que es útil, principalmente para T+1.

### **Contexto estacional**
“¿Qué sería anormal en el periodo que quiero predecir?”

Los P25/P75 fueron una de las señales más robustas de EXP03 para boosting.

### **Trayectoria**
“¿Cómo hemos llegado hasta aquí?”

EXP03.1 muestra que **resumir esa trayectoria mediante conteos de estados recientes y diferencias entre semestres añade poco o nada**.

Esto sugiere una hipótesis más precisa:

> **La información predictiva relevante parece estar más relacionada con el nivel/estado y el contexto estacional que con resúmenes gruesos de frecuencia y cambio del canal.**

Esto es una **interpretación**, no una demostración causal.

---

# 5. Qué decisiones cambian

### 1. EXP03.1 deja de estar pendiente

`experimentos.md` todavía lo describe como “pendiente”. experimentos

Con el bundle analizado, su estado debe actualizarse a:

**EXP03.1 — parcialmente soportada únicamente para memoria reciente; no soportada para cambio semestral ni trayectoria completa.**

---

### 2. M02 debe detenerse como línea general

La recomendación de EXP03.1 es explícita: no continuar M02 como mejora general de onset; cualquier reformulación debe considerarse una hipótesis nueva. CONCLUSIONS

Estoy de acuerdo con esa decisión según la evidencia adjunta.

---

### 3. M01 no merece convertirse en nueva baseline

Aunque Q1 es `PARCIALMENTE_RESPALDADA`, +5 detecciones contra +58 falsas alertas no justifica reemplazar M00. CONCLUSIONS

**M00 debe continuar como referencia científica.**

---

### 4. Aumenta la prioridad relativa de EXP04 y EXP05

Antes EXP03.1 era todavía una hipótesis plausible de mejora de señal.

Ahora esa vía produce una ganancia marginal.

Por tanto, la evidencia acumulada desplaza aún más la prioridad hacia:

**EXP04 → transporte temporal de calibración/threshold**  
**EXP05 → calibración/decisión condicionada a territorio o perfil**

Esto ya era la ruta propuesta tras EXP03. experimentos

---

# 6. Hipótesis que permanecen abiertas

No están demostradas por EXP03.1:

- que la trayectoria sea inútil en cualquier representación;
- que una secuencia temporal más rica no funcione;
- que T+2 no pueda beneficiarse de memoria;
- que las diferencias territoriales deban resolverse entrenando modelos distintos;
- que el problema sea exclusivamente calibración;
- que P25/P75 representen señal epidemiológica independiente y no parcialmente la frontera matemática de Y;
- que exista estabilidad prospectiva.

El propio EXP03.1 carece de intervalos de incertidumbre y no dispone de evaluación válida de 2025. CONCLUSIONS

---

# 7. Próximos experimentos recomendados

## Prioridad 1 — EXP04: transporte temporal

Es ahora el experimento con mayor valor informativo.

Pregunta:

> **¿Podemos conservar aproximadamente la misma sensibilidad y carga cuando cambia el año?**

Debería aislar:

- ventana de calibración;
- método de calibración;
- política de threshold;
- transporte entre cortes.

Sin modificar simultáneamente features.

---

## Prioridad 2 — EXP05: heterogeneidad

Pregunta:

> **¿Una regla de calibración global está causando parte de las pérdidas por territorio/perfil?**

Comparar global vs departamento vs perfil vs esquema parcialmente jerárquico, como ya plantea el plan. experimentos

No implica todavía modelos independientes.

---

## Prioridad 3 — solo si se quiere rescatar memoria: nueva hipótesis acotada

No repetiría M02.

Una futura prueba de memoria debería concentrarse únicamente donde apareció la pequeña señal:

**T+2**, con una representación diferente y preespecificada.

Por ejemplo, conceptualmente, estudiar dinámica continua del canal en lugar de solo conteos SECURITY/WARNING/EXCESS. Esto es una **hipótesis**, no una conclusión derivada de los resultados.

---

# 8. Síntesis científica acumulada

La lectura de EXP00–EXP03.1 queda:

> **SAT-Dengue sí contiene señal anticipatoria, pero hasta ahora ninguna modificación aislada —algoritmo, target, ventana del canal, clima, ablación de variables o memoria reciente— ha producido una mejora suficientemente estable en detección de inicios, carga de falsas alertas, tiempo y territorio.**

EXP03.1 estrecha aún más el problema: **la falta de memoria histórica resumida no parece ser el cuello de botella principal**.

La evidencia apunta con creciente consistencia a dos frentes: **transportabilidad temporal de calibración/umbral** y **heterogeneidad territorial**.

Por ello, la decisión sigue siendo **G5 `NOT_APPROVED` y `champion: not_selected`**. CONCLUSIONS