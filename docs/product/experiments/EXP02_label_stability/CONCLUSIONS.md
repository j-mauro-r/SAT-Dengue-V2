# EXP02 — Estabilidad de etiquetas y episodios: conclusiones científicas

## Resultado y decisión propuesta

**Ejecución real completada y verificada. Clasificación propuesta: `MATERIAL_INSTABILITY` de la identidad de las etiquetas y episodios; `INCONCLUSIVE` respecto de sustituir cinco años por siete o nueve.** Se recomienda conservar cinco años para EXP03 por continuidad, parsimonia y trazabilidad, **no por superioridad demostrada**.

La segunda fila del [plan de experimentos](../experimentos.md) pregunta si la definición del objetivo es estable y si las conclusiones predictivas resisten el cambio. La evidencia muestra sensibilidad que va más allá de pocos meses aislados: cambia qué inicios se consideran verdaderos, aparecen/desaparecen episodios y existen fragmentaciones y uniones. Las mejoras predictivas no son uniformes contra una verdad fija. No hay un umbral de materialidad previamente aprobado: esta clasificación es un juicio descriptivo sustentado en magnitudes y estructura, no un test estadístico, una regla nueva de aceptación ni una elección automática de H.

**Confirmado** identifica resultados verificables; **interpretación** identifica su lectura científica; **limitación** delimita lo que no se demuestra. G5 permanece `NOT_APPROVED`; champion `not_selected`. Esta ejecución cubre únicamente H=5/7/9 conservando todos los años históricos. El eje alternativo de años epidémicos continúa `pending_scientific_definition`.

## Integridad, procedencia y alcance de la auditoría

Fuentes rectoras: [protocolo congelado](protocol.json), [diseño](DESIGN.md), [plan general](../experimentos.md) y [contexto de EXP01](../EXP01_direct_onset/CONCLUSIONS.md). Se leyeron únicamente resultados existentes, metadatos y código de su interpretación; no se cargaron fuentes crudas ni se volvió a ejecutar el experimento.

| Identidad | Valor |
| --- | --- |
| Commit ejecutado | `f13ae214eee83fb59bff22780710dc03137ecbf0` |
| Parent MLflow | `58db5775e2e340a2bfed7ca872b7eb8e` |
| Bundle | `326f636299ce4b87b7ad461dc8aff9c75b167f9876df2769fab1d7d6a267996a` |
| SHA-256 manifiesto | `1f0630b78eba0db7933c3a092f07482a57ef8aa75af68886e423d019475a5c83` |
| SHA-256 result.json | `420d7c8ba42b8d216dad2ea26df7cb0fd3ebddcc5d8cbe4ccfc38b0044da5661` |
| SHA-256 provenance.json | `c9332d4fc3c092b5d1bfff01c7c1334266671003d41433a6317bbd16567bb1cf` |
| protocol_sha256 | `1bb7f929d88a01bc4036fa74046284117b8ebc8b89c6ee9cb69470691c84b31e` |
| data_version | `241aa320e2df20d1d4613c50c61d32b60f161a10d76931721131c93a544a213a` |
| data_sha256 | `f449320b81e2b9961dc8e956609936d48ef518c36c2b63d35f6264dac9951ee3` |
| configuration_sha256 | `f82ccd6cd9901856d5db8fc0b8a14ca81dc87a25a9c31e1bb358ef7820d55a2d` |
| code_sha256 | `46fa5bac441a0ec095404723cb04a5782c0c300ac236e18ce1cf788e0524571b` |
| environment_sha256 | `f58aacee359c2442094b89d1e20278b41f2fd67049fb3eb2c752a02e3da76497` |
| approval_sha256 | `405cb4e693a6a364856aa0824131f63989aad7068396d3277afc1ff149fcc93f` |

Bundle local: `tmp/kedro-migration/exp02-runs/326f636299ce4b87b7ad461dc8aff9c75b167f9876df2769fab1d7d6a267996a`. Tienda: `tmp/kedro-migration/replay-mlflow/tracking.sqlite`, abierta con `mode=ro&immutable=1`.

**Confirmado:** el hash canónico del manifiesto, el tamaño y SHA-256 de ambos payloads, las ocho identidades de la autorización y la correspondencia con el parent concuerdan. `approval_sha256` es el hash del objeto canónico, no el hash de su JSON indentado. La proyección agregada de MLflow coincide íntegramente con el bundle; se reconciliaron sus 405 valores métricos en SQLite. Los 64 runs están `FINISHED`: un parent y 63 children. El inventario verificable `tmp/exp02-scientific-analysis/cell-inventory.csv` contiene la dimensión y el run ID de cada child.

| Capa | Producto cartesiano | Celdas | No evaluables |
| --- | --- | --- | --- |
| Descriptiva | 3 historias × 3 años | 9 | 0 |
| Predictiva | 3 historias × 3 años × 2 horizontes × 3 familias | 54 | 0 |

Se conservan los estados/motivos originales: las 54 celdas predictivas son `evaluable`, con `reason=null`; las nueve descriptivas tienen soporte completo. Los contadores nativos registran **54 modelos, 54 preparadores y 54 calibradores**, y cero ajustes de interfaces sintéticas. Son conteos de la ejecución previa, no de esta auditoría.

La lectura de etiquetas y predicciones guardadas verifica ausencia de 2025. El código ejecutado y los cortes congelados excluyen 2025 de entrenamiento, calibración, selección y evaluación; 2024 aparece únicamente como estrés retrospectivo. **Límite de verificación:** no se persistieron las filas individuales de entrenamiento/calibración; no se reconstruyeron desde datos crudos. Sus fechas se respaldan por el diseño, código ejecutado, cobertura y hashes de roles, no por una segunda auditoría fila a fila. Los hashes de los ficheros fuente pueden abarcar bytes de 2025 sin que esas filas se consuman científicamente.

## Cobertura y estabilidad de las etiquetas

En cada evaluación (2020, 2022, 2024), las tres historias comparten **76 municipios y 912 municipio-meses**: Meta 29/348 y Tolima 47/564. Estados e inicios son evaluables en los 912 registros: cobertura individual y común **100%**, diferencia de cobertura entre H **0 filas/0 puntos porcentuales**. Los cambios siguientes son cambios de etiqueta sobre las mismas claves, no exclusiones disfrazadas de estabilidad.

| Año | H | Comunes/total | Excesos | Inicios | Prevalencia de inicio | Δ inicios vs H5 | Filas P75=0 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | 5 | 912/912 | 209 | 69 | 7.57% | Referencia | 115 |
| 2020 | 7 | 912/912 | 180 | 57 | 6.25% | -12 (-17.39%) | 80 |
| 2020 | 9 | 912/912 | 195 | 61 | 6.69% | -8 (-11.59%) | 111 |
| 2022 | 5 | 912/912 | 228 | 89 | 9.76% | Referencia | 145 |
| 2022 | 7 | 912/912 | 223 | 87 | 9.54% | -2 (-2.25%) | 92 |
| 2022 | 9 | 912/912 | 179 | 74 | 8.11% | -15 (-16.85%) | 107 |
| 2024 | 5 | 912/912 | 446 | 103 | 11.29% | Referencia | 121 |
| 2024 | 7 | 912/912 | 504 | 105 | 11.51% | +2 (1.94%) | 95 |
| 2024 | 9 | 912/912 | 527 | 110 | 12.06% | +7 (6.80%) | 110 |

La prevalencia usa 912 meses por año; no debe confundirse con la prevalencia predictiva en la cohorte elegible sin exceso en origen. Los cambios pareados son simétricos en el desacuerdo, pero sus transiciones se leen de la primera definición a la segunda:

| Año | Par | Exceso cambiado /912 | Exceso 0→1 / 1→0 | Inicio cambiado /912 | Inicio 0→1 / 1→0 |
| --- | --- | --- | --- | --- | --- |
| 2020 | 5/7 | 69 (7.57%) | 20 / 49 | 58 (6.36%) | 23 / 35 |
| 2020 | 5/9 | 54 (5.92%) | 20 / 34 | 44 (4.82%) | 18 / 26 |
| 2020 | 7/9 | 37 (4.06%) | 26 / 11 | 30 (3.29%) | 17 / 13 |
| 2022 | 5/7 | 47 (5.15%) | 21 / 26 | 50 (5.48%) | 24 / 26 |
| 2022 | 5/9 | 75 (8.22%) | 13 / 62 | 65 (7.13%) | 25 / 40 |
| 2022 | 7/9 | 66 (7.24%) | 11 / 55 | 63 (6.91%) | 25 / 38 |
| 2024 | 5/7 | 86 (9.43%) | 72 / 14 | 64 (7.02%) | 33 / 31 |
| 2024 | 5/9 | 123 (13.49%) | 102 / 21 | 87 (9.54%) | 47 / 40 |
| 2024 | 7/9 | 85 (9.32%) | 54 / 31 | 59 (6.47%) | 32 / 27 |

**Interpretación:** los porcentajes sobre todos los meses subestiman cuánto cambia el conjunto de eventos positivos. En 2020, H7 deja de reconocer 35 de los 69 inicios H5 (50.72%) y añade 23; el neto −12 oculta 58 sustituciones. H9 deja de reconocer 26/69 en 2020, 40/89 en 2022 y 40/103 en 2024 (37.68%, 44.94% y 38.83%). En 2024, H9 añade 47 inicios y elimina 40: el neto +7 no significa estabilidad de identidad. No se interpreta ningún H como verdad epidemiológica externa.

### Historia insuficiente, desconocidos y ceros

La cobertura completa de las evaluaciones no elimina la pérdida histórica de soporte. En los resultados guardados, H7 no tiene estados evaluables en 2012; en 2013 tiene 532/912 estados y 456/912 inicios. H9 no tiene estados en 2012–2014; en 2015 tiene 532/912 estados y 456/912 inicios; desde 2016 las tres definiciones tienen 912/912 en estos años examinados. La expectativa calendárica del diseño se formuló sin comprobar datos privados; esta cobertura describe el bundle ejecutado, cuyo soporte mensual incluye 2006. No se cambia el protocolo ni se reconstruye la fuente histórica.

Los 380 estados no evaluables de 2013/H7 y 2015/H9 tienen motivo `insufficient_history`; no son negativos ni ceros. Los primeros meses evaluables pueden carecer de estado previo, de ahí la diferencia entre cobertura de estado e inicio. El soporte común reduce entrenamiento también para H5, para mantener una comparación equivalente: por ejemplo, T+1/2020 conserva 2,608 filas comunes de las 4,358 elegibles antes de disponibilidad histórica; 1,750 quedan fuera por disponibilidad.

Regla preservada: con historia completa, exceso significa conteo **estrictamente mayor** que P75. Con P75=0, cero casos es no exceso y un conteo positivo es exceso. Fuera de cobertura, el estado queda desconocido. Un no exceso con P75>0 no demuestra cero casos: puede ser un conteo positivo bajo el umbral. Esta revisión no vuelve a contar notificaciones crudas.

## Episodios: estructura y censura

Los episodios son secuencias máximas de exceso conocido, pueden cruzar años y se interrumpen por un mes desconocido. La tabla cuenta episodios que intersectan el año evaluado; **no equivale a inicios ocurridos dentro de ese año**. La duración es la secuencia observada completa del episodio intersectante, incluyendo meses de años vecinos, no solamente los meses dentro del año.

| Año | H | Episodios intersectantes | Inicios confirmados en año | Duración media/mediana/máx. (meses) | Censurados izq./der. |
| --- | --- | --- | --- | --- | --- |
| 2020 | 5 | 101 | 69 | 4.64 / 2 / 23 | 0 / 0 |
| 2020 | 7 | 90 | 57 | 4.87 / 2 / 22 | 0 / 0 |
| 2020 | 9 | 95 | 61 | 4.97 / 2 / 23 | 0 / 0 |
| 2022 | 5 | 97 | 89 | 3.86 / 2 / 24 | 0 / 0 |
| 2022 | 7 | 92 | 87 | 4.18 / 2 / 19 | 0 / 0 |
| 2022 | 9 | 80 | 74 | 3.74 / 2 / 19 | 0 / 0 |
| 2024 | 5 | 134 | 103 | 4.74 / 2 / 24 | 0 / 26 |
| 2024 | 7 | 139 | 105 | 5.14 / 3 / 22 | 0 / 35 |
| 2024 | 9 | 142 | 110 | 4.89 / 2 / 23 | 0 / 42 |

| Año | Par | Fragmentados | Unidos | Sin solapamiento referencia/variante | Ambiguos fragmentación/unión |
| --- | --- | --- | --- | --- | --- |
| 2020 | 5/7 | 3 | 0 | 26 / 11 | 0 / 0 |
| 2020 | 5/9 | 2 | 0 | 19 / 10 | 0 / 0 |
| 2020 | 7/9 | 0 | 1 | 6 / 12 | 0 / 0 |
| 2022 | 5/7 | 1 | 2 | 10 / 6 | 0 / 0 |
| 2022 | 5/9 | 2 | 1 | 23 / 5 | 0 / 0 |
| 2022 | 7/9 | 3 | 1 | 18 / 4 | 0 / 0 |
| 2024 | 5/7 | 2 | 5 | 6 / 17 | 0 / 3 |
| 2024 | 5/9 | 1 | 5 | 6 / 23 | 2 / 6 |
| 2024 | 7/9 | 3 | 6 | 6 / 13 | 2 / 3 |

**Confirmado:** H9 reduce los episodios intersectantes de 97 a 80 en 2022 (−17.53%), pero los aumenta de 134 a 142 en 2024 (+5.97%). Existen relaciones sin solapamiento y fragmentaciones/uniones confirmadas incluso sin pérdidas de cobertura. Por ello no se trata únicamente de cambiar meses marginales conservando los mismos episodios.

En 2024, 26/35/42 episodios H5/H7/H9 están censurados a la derecha por el fin del soporte disponible. Sus duraciones son observadas, no finales. Las relaciones ambiguas se mantienen aparte: por ejemplo, 5/9 tiene dos fragmentaciones y seis uniones ambiguas, además de una fragmentación y cinco uniones confirmadas. No se convierten las ambiguas en cambios epidemiológicos demostrados; tampoco se suman episodios intersectantes entre años como si fueran necesariamente distintos.

## Territorios y condiciones críticas

El detalle municipal queda exclusivamente en los auxiliares locales. No se publican códigos, nombres ni predicciones individuales. La comparación 5/9 muestra que el territorio con mayor sensibilidad cambia entre años:

| Año | Departamento | Filas | Excesos cambiados | Inicios cambiados |
| --- | --- | --- | --- | --- |
| 2020 | Meta | 348 | 19 (5.46%) | 12 (3.45%) |
| 2020 | Tolima | 564 | 35 (6.21%) | 32 (5.67%) |
| 2022 | Meta | 348 | 42 (12.07%) | 35 (10.06%) |
| 2022 | Tolima | 564 | 33 (5.85%) | 30 (5.32%) |
| 2024 | Meta | 348 | 54 (15.52%) | 42 (12.07%) |
| 2024 | Tolima | 564 | 69 (12.23%) | 45 (7.98%) |

Para 5/9, tienen algún inicio modificado 31, 37 y 47 de los 76 municipios en 2020, 2022 y 2024. Los cinco municipios con más cambios reúnen 27.27%, 26.15% y 21.84% del total de cambios; los diez primeros, 50.00%, 44.62% y 39.08%. La inestabilidad no se limita a uno o dos municipios. El máximo individual es 3/12, 4/12 y 4/12 meses: tasas de 25% o 33.33% apoyadas en apenas doce observaciones, insuficientes para una clasificación municipal estable o inferencial.

Los estratos pareados se definen **siempre con H5**, también para 7/9. “Muchos ceros” significa más de la mitad de los cinco meses históricos de referencia con cero; es una condición municipio-mes, no un perfil municipal permanente ni una exclusión. P75=0 y muchos ceros se solapan, por lo que no se suman entre sí.

| Año | Estrato H5 | Inicios cambiados 5/9 / filas | Tasa |
| --- | --- | --- | --- |
| 2020 | Sin mayoría de ceros | 32/679 | 4.71% |
| 2020 | Mayoría de ceros | 12/233 | 5.15% |
| 2020 | P75>0 | 39/797 | 4.89% |
| 2020 | P75=0 | 5/115 | 4.35% |
| 2022 | Sin mayoría de ceros | 51/642 | 7.94% |
| 2022 | Mayoría de ceros | 14/270 | 5.19% |
| 2022 | P75>0 | 60/767 | 7.82% |
| 2022 | P75=0 | 5/145 | 3.45% |
| 2024 | Sin mayoría de ceros | 73/701 | 10.41% |
| 2024 | Mayoría de ceros | 14/211 | 6.64% |
| 2024 | P75>0 | 81/791 | 10.24% |
| 2024 | P75=0 | 6/121 | 4.96% |

**Interpretación:** P75=0 y escasez histórica son condiciones relevantes para el significado del objetivo, pero no explican por sí solas la inestabilidad observada. En 5/9 la tasa de cambio de inicio es menor con P75=0 en los tres años; los cambios aparecen mayoritariamente fuera de ese estrato. En 2022/2024 la tasa también es mayor sin mayoría de ceros. No se atribuye causalidad: ambos estratos dependen de historia y territorio. El bundle permite analizar esta frecuencia de ceros, pero no reconstruir perfiles de volumen de notificaciones o incidencia sin volver a las fuentes; esos perfiles quedan pendientes.

## Comportamiento predictivo: Y propia y referencia fija

Las 54 celdas conservan X, claves, fechas, elegibilidad basal H5 y hashes de roles entre historias. El canal usado como predictor sigue siendo H5; cambia el objetivo, con ajuste independiente de modelo/preparador/calibrador. Los registros guardados permiten comprobar las mismas claves de selección/evaluación, no volver a auditar todas las matrices de entrenamiento. Se revisaron 43,641 predicciones guardadas, sin generar nuevas.

AP es average precision no interpolada, la medida PR usada por el experimento; no es precisión de alertas ni un área trapezoidal recalculada. En la tabla, cada tripleta corresponde a **H5 / H7 / H9**, sobre las mismas filas de la celda. AP mayor y Brier menor son orientaciones métricas, no una regla para elegir modelo.

| Año | Horizonte | Familia | AP propia 5/7/9 | AP fija 5/7/9 | Brier propio 5/7/9 | Brier fijo 5/7/9 |
| --- | --- | --- | --- | --- | --- | --- |
| 2020 | T+1 | xgboost | 0.1536 / 0.0923 / 0.1203 | 0.1536 / 0.1426 / 0.1472 | 0.1365 / 0.1001 / 0.0980 | 0.1365 / 0.1162 / 0.1100 |
| 2020 | T+1 | lightgbm | 0.1810 / 0.0858 / 0.1242 | 0.1810 / 0.1324 / 0.1454 | 0.1366 / 0.1005 / 0.0981 | 0.1366 / 0.1164 / 0.1101 |
| 2020 | T+1 | gam | 0.1633 / 0.0858 / 0.1109 | 0.1633 / 0.1308 / 0.1306 | 0.1374 / 0.1007 / 0.0985 | 0.1374 / 0.1167 / 0.1106 |
| 2020 | T+2 | xgboost | 0.1441 / 0.1076 / 0.0986 | 0.1441 / 0.0973 / 0.1047 | 0.1002 / 0.0869 / 0.0859 | 0.1002 / 0.0990 / 0.0938 |
| 2020 | T+2 | lightgbm | 0.1231 / 0.0948 / 0.0963 | 0.1231 / 0.0912 / 0.0935 | 0.1003 / 0.0869 / 0.0860 | 0.1003 / 0.0990 / 0.0939 |
| 2020 | T+2 | gam | 0.1216 / 0.1079 / 0.0926 | 0.1216 / 0.1047 / 0.0955 | 0.1004 / 0.0870 / 0.0862 | 0.1004 / 0.0990 / 0.0941 |
| 2022 | T+1 | xgboost | 0.3243 / 0.1727 / 0.1658 | 0.3243 / 0.2221 / 0.2173 | 0.1192 / 0.1018 / 0.0792 | 0.1192 / 0.1205 / 0.1209 |
| 2022 | T+1 | lightgbm | 0.2785 / 0.1469 / 0.1297 | 0.2785 / 0.1891 / 0.1701 | 0.1192 / 0.1018 / 0.0792 | 0.1192 / 0.1205 / 0.1210 |
| 2022 | T+1 | gam | 0.2714 / 0.1637 / 0.1576 | 0.2714 / 0.1894 / 0.2056 | 0.1190 / 0.1017 / 0.0792 | 0.1190 / 0.1205 / 0.1209 |
| 2022 | T+2 | xgboost | 0.1421 / 0.1356 / 0.0816 | 0.1421 / 0.0968 / 0.0953 | 0.0906 / 0.0881 / 0.0666 | 0.0906 / 0.0910 / 0.0913 |
| 2022 | T+2 | lightgbm | 0.1040 / 0.1091 / 0.0657 | 0.1040 / 0.0968 / 0.0848 | 0.0907 / 0.0881 / 0.0666 | 0.0907 / 0.0910 / 0.0913 |
| 2022 | T+2 | gam | 0.1028 / 0.1190 / 0.0845 | 0.1028 / 0.1019 / 0.1047 | 0.0906 / 0.0881 / 0.0666 | 0.0906 / 0.0910 / 0.0913 |
| 2024 | T+1 | xgboost | 0.3183 / 0.2793 / 0.2741 | 0.3183 / 0.3097 / 0.3105 | 0.1869 / 0.1793 / 0.1767 | 0.1869 / 0.1808 / 0.1772 |
| 2024 | T+1 | lightgbm | 0.3233 / 0.2730 / 0.2675 | 0.3233 / 0.3055 / 0.3065 | 0.1868 / 0.1793 / 0.1769 | 0.1868 / 0.1807 / 0.1771 |
| 2024 | T+1 | gam | 0.3229 / 0.2879 / 0.2652 | 0.3229 / 0.3200 / 0.3285 | 0.1864 / 0.1793 / 0.1769 | 0.1864 / 0.1806 / 0.1768 |
| 2024 | T+2 | xgboost | 0.1683 / 0.1496 / 0.1704 | 0.1683 / 0.1709 / 0.1723 | 0.1313 / 0.1278 / 0.1312 | 0.1313 / 0.1292 / 0.1265 |
| 2024 | T+2 | lightgbm | 0.2051 / 0.1474 / 0.1673 | 0.2051 / 0.1667 / 0.1922 | 0.1313 / 0.1278 / 0.1312 | 0.1313 / 0.1292 / 0.1264 |
| 2024 | T+2 | gam | 0.1890 / 0.1577 / 0.1652 | 0.1890 / 0.1972 / 0.2058 | 0.1313 / 0.1278 / 0.1312 | 0.1313 / 0.1292 / 0.1264 |

**Confirmado:** respecto de H5, Brier contra Y propia mejora en las 36 comparaciones alternativas; AP propia mejora en tres y empeora en 33. Contra la misma Y5, Brier mejora en las 24 comparaciones de 2020/2024, pero empeora en las doce de 2022. AP fija mejora solamente en seis de 36 y empeora en treinta. Menor Brier propio no basta para demostrar mejor capacidad de anticipar el mismo fenómeno.

### Calibración y cobertura operativa

Se reconciliaron AP, Brier y los agregados de calibración con las predicciones guardadas. Los siguientes intervalos son **rangos entre las tres familias**, no intervalos de confianza. Las prevalencias son propias/fijas dentro de la cohorte predictiva, no sobre los 912 meses descriptivos.

| Año | Horiz. | H | Cobertura operativa | Inicios propios/fijos | Prevalencia propia/fija | Probabilidad media | ECE propia / fija |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | T+1 | 5 | 661/912 (72.48%) | 69/69 | 10.44% / 10.44% | 0.3148–0.3171 | 0.2104–0.2127 / 0.2104–0.2127 |
| 2020 | T+1 | 7 | 661/912 (72.48%) | 47/69 | 7.11% / 10.44% | 0.2562–0.2576 | 0.1851–0.1865 / 0.1518–0.1532 |
| 2020 | T+1 | 9 | 661/912 (72.48%) | 54/69 | 8.17% / 10.44% | 0.2345–0.2359 | 0.1529–0.1542 / 0.1302–0.1315 |
| 2020 | T+2 | 5 | 588/912 (64.47%) | 51/51 | 8.67% / 8.67% | 0.2322–0.2326 | 0.1454–0.1459 / 0.1454–0.1459 |
| 2020 | T+2 | 7 | 588/912 (64.47%) | 38/51 | 6.46% / 8.67% | 0.2273–0.2276 | 0.1626–0.1630 / 0.1405–0.1409 |
| 2020 | T+2 | 9 | 588/912 (64.47%) | 43/51 | 7.31% / 8.67% | 0.2078–0.2089 | 0.1347–0.1358 / 0.1211–0.1221 |
| 2022 | T+1 | 5 | 693/912 (75.99%) | 89/89 | 12.84% / 12.84% | 0.0427–0.0430 | 0.0854–0.0858 / 0.0854–0.0858 |
| 2022 | T+1 | 7 | 693/912 (75.99%) | 75/89 | 10.82% / 12.84% | 0.0354–0.0356 | 0.0726–0.0728 / 0.0928–0.0930 |
| 2022 | T+1 | 9 | 693/912 (75.99%) | 58/89 | 8.37% / 12.84% | 0.0332–0.0334 | 0.0503–0.0505 / 0.0950–0.0952 |
| 2022 | T+2 | 5 | 641/912 (70.29%) | 62/62 | 9.67% / 9.67% | 0.0393–0.0395 | 0.0573–0.0574 / 0.0573–0.0574 |
| 2022 | T+2 | 7 | 641/912 (70.29%) | 60/62 | 9.36% / 9.67% | 0.0365–0.0367 | 0.0569–0.0571 / 0.0601–0.0602 |
| 2022 | T+2 | 9 | 641/912 (70.29%) | 45/62 | 7.02% / 9.67% | 0.0338–0.0338 | 0.0364–0.0364 / 0.0629–0.0630 |
| 2024 | T+1 | 5 | 453/912 (49.67%) | 103/103 | 22.74% / 22.74% | 0.3450–0.3455 | 0.1181–0.1220 / 0.1181–0.1220 |
| 2024 | T+1 | 7 | 453/912 (49.67%) | 101/103 | 22.30% / 22.74% | 0.3044–0.3048 | 0.0814–0.0819 / 0.0770–0.0774 |
| 2024 | T+1 | 9 | 453/912 (49.67%) | 102/103 | 22.52% / 22.74% | 0.2783–0.2797 | 0.0531–0.0614 / 0.0523–0.0637 |
| 2024 | T+2 | 5 | 414/912 (45.39%) | 61/61 | 14.73% / 14.73% | 0.2229–0.2231 | 0.0756–0.0757 / 0.0756–0.0757 |
| 2024 | T+2 | 7 | 414/912 (45.39%) | 60/61 | 14.49% / 14.73% | 0.2072–0.2077 | 0.0623–0.0627 / 0.0599–0.0603 |
| 2024 | T+2 | 9 | 414/912 (45.39%) | 64/61 | 15.46% / 14.73% | 0.1763–0.1768 | 0.0217–0.0222 / 0.0290–0.0295 |

En T+1/H5 la probabilidad media es aproximadamente 0.315–0.317 frente a prevalencia 0.104 en 2020, 0.043 frente a 0.128 en 2022 y 0.345 frente a 0.227 en 2024. Las historias mayores reducen las probabilidades; esto es compatible con menor sobrepredicción en 2020/2024 y mayor subpredicción en 2022, sin demostrar una explicación causal. La calibración de Y propia no garantiza calibración de Y5.

La cobertura operativa inferior a 100% proviene de elegibilidad sin exceso en origen y del soporte/embargo por horizonte, no de una población diferente entre H. T+2 conserva menos filas y algunos inicios H5 quedan fuera de su conjunto elegible. No se interpreta esa reducción como fallos predictivos sobre registros nunca evaluables.

## Frente completo de falsas alertas

Se revisaron **10,764 puntos guardados** y las tres parejas de historias en las 18 combinaciones de año/horizonte/familia: 54 grupos pareados. Cada punto conserva sensibilidad, precisión, inicios detectados/perdidos, alertas, falsas alertas y FAR tanto contra Y propia como contra Y5. Las tablas exhaustivas `frontiers-all.csv` y `frontiers-departments.csv` quedan en los auxiliares locales; no se seleccionó ni recalculó ningún umbral.

FAR = falsas alertas / alertas evaluables; sensibilidad = inicios detectados / inicios reales; precisión = inicios detectados / alertas evaluables. Con cero alertas, precisión/FAR son indefinidas, no evidencia de precisión perfecta. “Inicios perdidos” se refiere al desenlace puntual de inicio evaluable, no a perder necesariamente todo un episodio por cualquier horizonte o fecha.

Presupuestos iguales en selección **no garantizan** falsas alertas realizadas iguales en evaluación. Por eso se verificaron ambas cargas. La tabla resume todos los puntos; “ventaja” exige más inicios Y5 detectados con iguales o menos falsas alertas realizadas, y “reversa” exige menos inicios con iguales o más falsas alertas. Los demás puntos incluyen empates y compensaciones; no se ocultan ni se convierten en votos.

| Año | Par | Puntos (3 familias × 2 horizontes × presupuestos) | Ventajas | Reversas | Ventajas con deterioro departamental |
| --- | --- | --- | --- | --- | --- |
| 2020 | 5/7 | 630 | 2 | 112 | 2 |
| 2020 | 5/9 | 630 | 1 | 149 | 1 |
| 2020 | 7/9 | 630 | 54 | 39 | 48 |
| 2022 | 5/7 | 2145 | 47 | 374 | 31 |
| 2022 | 5/9 | 2145 | 49 | 472 | 18 |
| 2022 | 7/9 | 2145 | 182 | 249 | 97 |
| 2024 | 5/7 | 813 | 37 | 45 | 25 |
| 2024 | 5/9 | 813 | 40 | 26 | 14 |
| 2024 | 7/9 | 813 | 71 | 44 | 41 |

**Confirmado:** ninguna pareja domina punto por punto en todo el frente de ninguna de las 54 combinaciones. Las envolventes descriptivas de los puntos ya guardados frente a carga realizada también contienen diferencias de ambos signos en todos los grupos; no son una nueva política optimizada. Existen ventajas parciales frente a H5 —176 puntos—, pero 91 esconden al menos un departamento con menos detecciones o más falsas alertas. Las alternativas suman tres ventajas frente a 261 reversas en 2020; 96 frente a 846 en 2022; 77 frente a 71 en 2024. Estos puntos están fuertemente correlacionados y los frentes tienen longitudes distintas: las sumas no constituyen prueba estadística, estimación de probabilidad de ganar ni criterio de selección.

La falta de dominio se observa por familia y horizonte, no solo al agregarlos. Una mejora localizada en presupuesto/familia/año no se transporta automáticamente. La evidencia de 2024 puede revelar fragilidad, pero no confirma una alternativa como evaluación ciega.

### Precisión de la evidencia guardada

Las probabilidades individuales se serializan a 15 decimales, mientras que los umbrales guardados conservan precisión float completa. Reaplicar literalmente `p >= umbral` a las probabilidades redondeadas difiere en **402 puntos del frente** (804 registros al contar las dos verdades), con hasta 17 alertas en una frontera de puntuaciones comprimidas. Los conteos originales quedan dentro de límites conservadores de redondeo ±1e−15; AP/Brier y calibración agregada concuerdan con la comprobación independiente. Esto limita la reproducción exacta del umbral desde el payload individual, no es un hash inconsistente ni justifica reemplazar los resultados originales. Los conteos originales del frente siguen siendo la evidencia primaria; una precisión de exportación mayor requiere una corrección separada y revisión antes de futuros experimentos.

## Incertidumbre y fuerza de las conclusiones

Todos los 10,764 registros de intervalo predictivo tienen `interval=null`, `status=insufficient_cluster_support`; las comparaciones anuales de cambio de etiqueta muestran el mismo estado. El bootstrap previsto exige al menos dos municipios y dos años, con 1,000 réplicas y semilla 42. Cada celda de evaluación contiene un solo año. Un intervalo nulo significa **inferencia no disponible**, no incertidumbre cero ni efecto nulo. No se creó bootstrap IID, intervalo combinado de años ni alternativa no prevista.

Las magnitudes descriptivas permiten afirmar que la identidad de eventos y los resultados dependen de H; no permiten declarar significancia, superioridad general, una ventana epidemiológicamente verdadera o transportabilidad prospectiva. Tampoco hay un umbral de materialidad aprobado: `MATERIAL_INSTABILITY` sintetiza sustituciones de eventos, cobertura histórica y cambios estructurales, mientras que la elección de reemplazo sigue `INCONCLUSIVE`.

## Tabla de decisión

| Hallazgo | Evidencia | Interpretación | Limitación | Decisión habilitada | Decisión no habilitada |
| --- | --- | --- | --- | --- | --- |
| Identidad de inicios sensible a H | H9 retira 26/69, 40/89 y 40/103 inicios H5 | El neto de inicios oculta sustituciones | No existe verdad externa ni umbral de materialidad | Reportar MATERIAL_INSTABILITY descriptiva | Elegir H7/H9 automáticamente |
| Cambios estructurales de episodios | Fragmentación/unión y episodios sin solapamiento; 97→80 en 2022 | No son solo meses aislados | Censura derecha 2024 y episodios cruzan años | Mantener análisis de identidad/censura | Tratar duración observada como duración final |
| Cobertura evaluativa idéntica | 912/912 por H y año | Cambios reales de definición | Historia común reduce entrenamiento | Conservar población común para comparaciones | Comparar con cohortes históricas diferentes como si fueran pares |
| Heterogeneidad territorial | 5/9 afecta 31/37/47 municipios; orden Meta/Tolima varía | No hay explicación exclusivamente local | Doce meses por municipio/año | Desgloses y denominadores obligatorios | Inferencia municipal estable o perfiles por volumen sin soporte |
| Brier propio mejora; utilidad no uniforme | 36/36 Brier propio; 12/12 Brier fijo peor en 2022; ningún dominio completo | Cambiar Y puede mejorar una métrica sin mejorar la misma tarea | Intervalos indisponibles y redondeo en umbrales | Conservar referencia fija y frente completo | Cambiar objetivo, familia o presupuesto por un punto favorable |
| Disponibilidad histórica no demostrada | Evidencia retrospectiva; 2024 estrés | No valida oportunidad real de alerta | Sin vintages históricos de disponibilidad | Mantener limitación explícita | Aprobar despliegue, G5 o champion |

## Recomendación para EXP03 y preguntas pendientes

1. **Conservar H5 por continuidad**, documentando su sensibilidad frente a H7/H9; no presentarlo como una definición superior. No sustituir el objetivo o las reglas de episodios durante una ablación de variables.
2. Congelar en el protocolo de EXP03: población y claves elegibles, verdad de evaluación, canal H5, cortes/embargos, familias/hiperparámetros, calibración, semilla y carga de alertas. Cambiar únicamente grupos de predictores predeclarados: historia/estacionalidad, umbrales del mes objetivo, estado reciente/zona, razón de incidencia y clima, según el plan general. La decisión sobre mantener exactamente la intersección 5/7/9 o recuperar soporte exclusivo de H5 debe aprobarse **antes**: no mezclar un cambio de cohorte con el efecto de una ablación.
3. EXP02 **no es una ablación**. El mismo conjunto X responde al cambio de Y; no hay evidencia del aporte marginal de clima, canal o variables individuales. No se usó importancia interna de árboles ni se formularon afirmaciones causales.
4. Resolver previamente soporte temporal suficiente para inferencia pareada, carga operativa y criterio de materialidad/decisión. No reutilizar 2020/2022/2024 como si fueran confirmación ciega; 2025 sigue excluido y consumido para su comparación histórica.
5. Mantener pendiente la definición científica del eje de años epidémicos. Esta ejecución incluye todos los años históricos; no valida excluir años concretos.

**Preguntas abiertas:** qué regla define un episodio epidemiológicamente defendible con pocos casos; cómo comprobar el efecto de volumen de dengue sin confundir ceros con cobertura; si la heterogeneidad se mantiene en años no examinados; cómo transportar calibración; qué carga de falsas alertas es aceptable; cómo disponer de intervalos con dependencia municipal/temporal; cómo conservar precisión suficiente para reproducir umbrales; y qué predictores estaban realmente disponibles en cada fecha de emisión.

## Reproducibilidad y límites de acceso

Auxiliares reproducibles, locales e ignorados: `tmp/exp02-scientific-analysis/`. Incluyen `integrity.py`, `verify_tracking.py`, `labels_analysis.py`, `cell-inventory.csv`, `labels-summary.csv`, `pairs-summary.csv`, `strata-summary.csv`, `historical-coverage.csv`, y `predictive/audit.py`, `predictive/summarize.py`, `predictive/metrics54.csv`, `predictive/frontiers-all.csv`, `predictive/pair-frontier-summary.csv` y sus verificaciones. El detalle municipal y las predicciones individuales permanecen fuera del documento versionado.

Localizadores originales: `result.stability.children` (9 coberturas/conteos), `.pairs` (9 comparaciones), `.paired_by_group` (estratos H5), `result.labels[H]`, `result.episodes[H]`, `result.predictive.children` (54 celdas, métricas propias/fijas y frentes), `.predictions` (selección/evaluación), y los tres contadores reales en `result.predictive`. Los agregados se contrastaron con el artefacto del parent y SQLite. Los hashes antes/después de bundle, reservas, tienda y protocolo se conservan en los auxiliares.

No hubo nuevos fits, preparaciones ajustadas, calibraciones, selección de umbrales, ejecución experimental ni escrituras MLflow durante esta revisión. El único cambio científico documental es esta conclusión; protocolo, código, resultados originales, G5 y champion permanecen intactos. Mauricio decide el merge y las decisiones científicas posteriores.
