# EXP-BETA V1 — cierre y conocimiento científico integrado

**Estado científico: `COMPLETED_WITH_LIMITATIONS`.** Las cuatro fases obligatorias
del programa retrospectivo acotado fueron implementadas y verificadas localmente
al 2 de noviembre de 2026. Sus resultados se integraron mediante PR #67 en
`a2f89110c84969f2ca2fb635532383e1271ec8b6`. Esta consolidación documental conserva
las identidades y conclusiones de aquella ejecución; no constituye una nueva
corrida, selección, confirmación ni aprobación de uso. **G5 `NOT_APPROVED`;
`champion: not_selected`.**

## Resumen ejecutivo

V1 evaluó predicción tabular compartida/adaptación territorial, conteos NB2 y
políticas de umbral sobre evidencia de Meta y Tolima. Algunas variantes BETA01
mejoran detección y carga agregadas en T+1; la adaptación local no muestra
beneficio estable. NB2 aporta distribuciones reproducibles, pero falla el criterio
conjunto de alertas T+1 y no identifica inicio T+2. BETA03 reduce falsas alertas
con pérdidas excesivas de sensibilidad. **No se demostró una mejora operativa
general ni una política que cumpla consistentemente por horizonte, año y territorio.**

El [diseño original](DESING.md) conserva sus notas históricas de implementación
pendiente: las autorizaciones y ejecuciones posteriores están documentadas en
los protocolos y resultados. Los registros [PHASE1](PHASE1.md) y
[PHASE2](PHASE2.md) describen bloqueos originales en Cloud; la aceptación real
local posterior figura en [PHASE2_IMPLEMENTATION](PHASE2_IMPLEMENTATION.md).
No se sustituyen esos registros por evidencia sintética ni se reescribe su historia.

Las conclusiones individuales son las propietarias del detalle científico:
[BETA01](../EXP-BETA01/CONCLUSIONS.md), [BETA02](../EXP-BETA02/CONCLUSIONS.md) y
[BETA03](../EXP-BETA03/CONCLUSIONS.md). La comparación con EXP00–EXP04 está en
[Análisis científico 6](../analisis-6.md).

## Comparabilidad y criterios comunes

La tabla canónica conserva 17.936 filas × 70 columnas de 76 municipios
(29 Meta, 47 Tolima), desde 2006-06 hasta 2026-01. La población de evaluación
es más estrecha: no exceso conocido en T, predictores completos y etiquetas
observables, con iguales claves y verdad frente a R0. Los cortes 2020/2021/2022/2024
suman 2.653 filas/313 inicios en T+1 y 2.422/219 en T+2; exposición exacta
2.653/12 y 2.422/12 municipio-años elegibles. No se suman horizontes como episodios
independientes. Los agregados de cuatro años incluyen estrés conocido y no
son un nuevo bloque de selección o confirmación.

Se mantuvo H5: inicio T+1 equivale a exceso dentro de la cohorte; T+2 exige
no exceso T+1 seguido de exceso T+2. La probabilidad marginal de exceso T+2
no equivale a inicio. Los criterios adoptados antes de ejecutar fueron
**≤1 FA/municipio-año y Δ sensibilidad ≥−2 pp frente a R0**, con controles por
año y departamento. Cumplir descriptivamente no establece no inferioridad
estadística. R0 conserva su selección original sobre exposición monitoreada;
las comparaciones BETA recalculan tasas sobre exposición elegible común.

R0 ya agrupa municipios. Las ventanas de ajuste/calibración y representación
BETA01/02 difieren de R0: se comparan procedimientos completos, sin atribuir
causalmente el efecto a una sola pieza. BETA03 sí mantiene probabilidades y
cambia la política. [Protocolos y resultados individuales](../EXP-BETA01/CONCLUSIONS.md#trazabilidad).

## Matriz de cumplimiento de las cuatro fases

| Fase de DESING.md | Componente | Estado | Evidencia real | Límite científico |
|---|---|---|---|---|
| 1 | Canonical Model Table y ruta Kedro independiente | `IMPLEMENTADO_Y_VALIDADO` | Tabla, contrato, columnas y cobertura reproducidos desde Stage 2 identificado; identidad abajo | Solo Meta–Tolima; 608 municipio-meses sin clima; datos consolidados |
| 2 | G0/L1, clima OFF/ON y R0 | `IMPLEMENTADO_Y_VALIDADO` | [Resultados BETA01](RESULTS.md): 16 modelos únicos, 20.300 puntuaciones nativas verificadas y 120 estratos | Adaptación local `NO_RESPALDADA`; T+2 pierde sensibilidad |
| 2 | G1 nacional / perfiles de transmisión | `NO_EVALUABLE` | Fuente canónica admitida solo de 76 municipios; sin perfil validado temporalmente | Los originales nacionales conservados no son una tabla nacional elegible ni un entrenamiento G1 |
| 3 | NB2 parsimoniosa, conteos y riesgo H5 | `IMPLEMENTADO_Y_VALIDADO` | [Resultados BETA02](../EXP-BETA02/RESULTS.md): 16 modelos, 10.150 pronósticos, 48 estratos de conteos y 84 de inicio/referencia | Criterio conjunto T+1 incumplido |
| 3 | Inicio T+2 NB2 conjunto | `NO_EVALUABLE` | Pronósticos marginales preservados, inicio ausente explícitamente | No se identificó distribución conjunta de transición |
| 3 | DeepAR/GRU | `CONDICIONAL_NO_JUSTIFICADO` | Sin limitación remediable por secuencias demostrada independientemente ni soporte temporal nuevo | No se ejecutó; no es resultado negativo de todas las redes |
| 4 | Política global restringida sobre R0 | `IMPLEMENTADO_Y_VALIDADO` | [Resultados BETA03](../EXP-BETA03/RESULTS.md): 30 contrastes, grafo de cuatro nodos y nueve archivos reproducidos | Hipótesis conjunta `NO_RESPALDADA`; el límite en desarrollo no garantiza carga futura |
| 4 | Política departamental regularizada | `IMPLEMENTADO_Y_VALIDADO / NO_EVALUABLE` | Activación en desarrollo solo para ambos horizontes 2020; seis estratos emparejados | 0/6 cumplen conjuntamente; retorno global en otros cortes; perfiles no disponibles |
| 4 | Aprendizaje adicional consciente de falsos positivos | `CONDICIONAL_NO_JUSTIFICADO` | Cero FP con puntuación ≥0,8 en ocho cortes; un bloque de selección por predictor | Sin hard-negative mining, ajuste asimétrico, segundo clasificador ni DRL |
| Todas | Confirmación independiente / no inferioridad estadística | `NO_EVALUABLE` | 2024 consumido; ningún objetivo 2025 evaluado en BETA | Incertidumbre inferencial `UNAVAILABLE`; superioridad `NOT_ESTABLISHED` |

## Hallazgos comparados e hipótesis

Las cifras son observaciones agrupadas de las cohortes BETA indicadas; FA significa
falsa alerta de inicio. Las tablas completas, Brier/AP y controles territoriales
permanecen en las conclusiones individuales y sus CSV originales.

| Experimento | Hallazgo favorable observado | Resultado negativo y límite | Disposición científica |
|---|---|---|---|
| [BETA01](../EXP-BETA01/CONCLUSIONS.md) | G0 OFF/ON T+1: 146/152 detecciones de 313 frente a 142 de R0, con 179/204 FA frente a 231 | Todos los brazos T+2 pierden 8,68–10,96 pp; L1 falla 43/48 estratos conjuntos | Adaptación `NO_RESPALDADA`; pooling nuevo/G1 `NO_EVALUABLE` |
| [BETA02](../EXP-BETA02/CONCLUSIONS.md) | NB2 ON T+1: 152/313 frente a 142/313 de R0, Brier 0,091055; distribuciones de conteos reproducibles | OFF pierde 2,2364 pp; ON carga **1,004146 > 1**; 19/24 estratos T+1 fallan; inicio T+2 no identificado | NB2 marginal `NO_RESPALDADA`; inicio T+2 `NO_EVALUABLE` |
| [BETA03](../EXP-BETA03/CONCLUSIONS.md) | GLOBAL reduce FA de 231→136 T+1 y 256→175 T+2; carga 0,615153/0,867052 | Detecciones 142→96 y 86→57: −14,70/−13,24 pp; solo 8/24 estratos cumplen; DEPARTMENT 0/6 | Política congelada `NO_RESPALDADA`; aprendizaje adicional no ejecutado |

**Respaldado como observación descriptiva:** existen ganancias agregadas T+1 de
G0, pronósticos NB2 identificados y reducción de FA con umbrales más restrictivos.
No hay hipótesis principal de mejora general que reciba `RESPALDADA`. Las
hipótesis de adaptación L1, NB2 marginal como mejora de alertas y política BETA03
no están respaldadas bajo sus criterios. G1, perfiles, inicio NB2 T+2 y confirmación
permanecen sin evaluar; no deben convertirse en rechazos científicos.

## Interpretación transversal

La sensibilidad y la carga deben leerse juntas: en BETA01 algunas mejoras T+1
son compatibles con señal aprovechable, pero no se transportan a T+2. NB2 OFF
ahorra falsas alertas con una pérdida de sensibilidad superior al margen; ON
conserva mayor detección sin satisfacer el presupuesto. Cobertura predictiva
NB2 de 97,3–97,8% para intervalos nominales del 90%, con amplitud elevada, no
prueba precisión útil ni una mejor decisión. R0 no ofrece conteos para comparar
MAE/RMSE directamente. [BETA02](../EXP-BETA02/CONCLUSIONS.md).

La heterogeneidad no desaparece al agrupar. BETA03 mantiene las decisiones R0
en 2021/2022, pierde sensibilidad en 2020/2024 y excede la carga en Meta T+1/2022,
Tolima T+1/2024 y ambos departamentos T+2/2022. Sus Brier/AP no cambian al mover
umbrales. La política departamental solo tiene evidencia de 2020; compararla
con R0 de cuatro años sería cambiar denominadores. [BETA03](../EXP-BETA03/CONCLUSIONS.md).

El clima se conserva como información y contraste, sin presumir utilidad universal:
G0 ON mejora detecciones respecto a OFF con efectos de carga diferentes por
horizonte; NB2 ON reduce MAE pero empeora RMSE T+2. Ninguno de esos resultados
atribuye causalidad epidemiológica ni acredita desempeño en tiempo real.

## Identidades y preservación del cierre original

Tabla canónica: `ddf4d3be23f7ce2cd874bbdc73fdf0f7b9ae5e6f7055b2761ec23bd31fc15c98`;
manifiesto SHA-256 `037445487086f7123ee2bf4b97b9af06b96716e2f24e9ff5160177c59da261d8`.
Ruta local: `data/processed/canonical_model_table_v1/<bundle_id>/`.
Los documentos individuales identifican los bundles nativos, manifiestos,
protocolos, commits y tablas de cada experimento; [BETA01 implementación](PHASE2_IMPLEMENTATION.md),
[BETA02 implementación](../EXP-BETA02/README.md) y
[BETA03 implementación](../EXP-BETA03/README.md) conservan sus recibos de ejecución.

La evidencia histórica distingue ejecución real, reproducción y replay nativo
sin ajustes. BETA01 registra 64 ajustes reales entre su secuencia inicial,
corrección de disposición L1 y reproducciones, con 16 identidades únicas por
publicación; predicciones, políticas y criterios no cambiaron en esa corrección.
BETA02 registra 32 ajustes incluyendo reproducción, con 16 modelos únicos;
BETA03 registra cero. La consolidación actual no repitió esos ajustes.

El cierre original verificó 437 archivos inventariados (hash, tamaño y permisos),
los 27 payloads BETA02, 96 celdas nativas R0 y correspondencia exacta de H5 y
puntuaciones en ocho cortes BETA03. Sus nueve archivos se reprodujeron idénticos
y se rechazó sobrescritura. El lote técnico de cierre pasó 70 tests; son evidencia
histórica de ingeniería, distinta de las métricas científicas. Los originales
privados y modelos no se publican en GitHub: un checkout no proporciona esos datos.

La discrepancia heredada del inventario privado de migración sobre el registro
de decisiones ya modificado sigue abierta, sin reiniciar hashes ni omitir controles.
Conformidad DWP del repositorio: PASS; auditoría de todos los planes: dos fallos
heredados (PLAN_012, revisión pendiente, y ciclo de vida Stage 2 legado).
No se presentan como fallos nuevos de código ni se declaran resueltos.

Para esta consolidación se leyeron los manifiestos y se verificaron todos sus
payloads BETA01/02/03 (25/27/8), además de cotejar numéricamente las tablas públicas
con las nativas. Se recalcularon agregados a partir de métricas persistidas.
Esto no repite ni sustituye las comprobaciones científicas históricas anteriores.

## Estado final de V1 y límites para una posible V2

V1 queda cerrada con resultados mixtos/negativos y componentes no evaluables,
sin champion. H5 sigue siendo un proxy retrospectivo; cuatro años reutilizados,
cohortes completas seleccionadas y notificaciones consolidadas no acreditan
no inferioridad estadística, causalidad, beneficio sanitario ni anticipación
operativa. Los criterios y las fuentes originales permanecen intactos.

La [auditoría local de conservación](../analisis-6.md#f-limitaciones-de-exp-beta-v1)
confirma fuentes epidemiológicas nacionales conservadas y verificadas por identidad,
pero ninguna tabla canónica nacional elegible ni entrenamiento G1 de V1.
No hubo pérdida demostrada de los originales. La brecha climática nacional,
la homologación geográfica/temporal y la disponibilidad histórica requieren
validación propia; más registros no crean periodos independientes nuevos.

Una V2 nacional es una hipótesis futura: conservaría V1 y R0 como referencias
identificadas, contrastes pareados y controles de carga, sensibilidad y territorio.
Ampliar fuentes, definir perfiles o trayectorias conjuntas y obtener evidencia
independiente requiere una autorización y un protocolo nuevos. Este documento
no crea ese plan ni autoriza otra ejecución. La revisión de este PR documental
corresponde a Mauricio; no se realiza merge automático.
