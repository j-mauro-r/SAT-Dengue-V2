# EXP02 — Estabilidad de etiquetas y episodios

## Autoridad y alcance

La segunda fila del [plan oficial](../experimentos.md) define EXP02. El [protocolo](protocol.json) y su hash canónico en el [registro](../experiment-registry.yml) fijan la comparación de ventanas de 5, 7 y 9 años. No se cambian las variables predictoras.

G5 permanece en `NOT_APPROVED` y el champion en `not_selected`. Se excluye 2025 de toda operación científica; 2024 es estrés retrospectivo, no evidencia ciega. Esta implementación no autoriza lectura privada, ajustes reales ni ejecución del experimento.

## Auditoría científica

`data/consolidation.py::history_periods_for_target` selecciona el mismo mes de los H años inmediatamente anteriores al año objetivo. `percentile_type7` usa interpolación lineal y `compute_current_endemic_channel` ya acepta el parámetro H. Ningún mes futuro interviene en el canal. DEC-120/121/122 del [registro de decisiones](../../traking-concluciones.md#dec-122) mantienen las siguientes reglas:

- El exceso exige conteo estrictamente mayor que P75. Con P75=0, cero casos no es exceso y cualquier conteo positivo sí lo es.
- Los H meses históricos deben estar disponibles. No se sustituye un año faltante por otro más antiguo ni se completa historia desconocida con ceros.
- Cero notificaciones requiere respaldo de cobertura. Fuera de cobertura, el conteo permanece desconocido. El clima no se imputa para crear soporte.
- El inicio requiere exceso en S y ausencia de exceso en S−1, usando el mes calendario exacto. Un estado desconocido no se convierte en negativo.

`experiments/onset.py` aporta objetivos por horizonte, elegibilidad en origen y particiones; `onset_evaluation.py` aporta métricas y selección de umbrales. EXP01 no identificaba episodios completos ni sus relaciones de fragmentación. EXP02 define cada episodio como una secuencia máxima de meses consecutivos conocidos en exceso. Conserva identidad, duración observada, inicio/final confirmado y censura izquierda/derecha. Los episodios pueden cruzar años; un hueco desconocido los interrumpe. Las relaciones entre segmentos censurados se reportan como ambiguas, separadas de fragmentación o unión confirmadas.

La documentación del proyecto distingue el inicio del objetivo en 2012 del comienzo del soporte bruto común en 2007. Una ventana de nueve años puede disponer de estados desde 2016 e inicios desde febrero de 2016, condicionado a historia completa. Esto es una consecuencia del calendario documentado, no una comprobación de datos privados.

Las fuentes históricas de Umaña y SAT-Dengue V1, junto con las decisiones vigentes de V2, no fijan una alternativa mensual trasladable para excluir años epidémicos. El ejemplo semanal del INS que excluye 2016/2019 y las referencias Bortman de 5–9 años no autorizan una nueva regla mensual. La política vigente conserva todos los años, incluido 2013. El segundo eje queda como `pending_scientific_definition`.

## Población y comparación

La población declarada comprende 76 municipios de Meta y Tolima. La carga reutiliza `prepare_exp01_inputs`: valida fuentes, cobertura y dimensiones después de autorizar; proyecta columnas raw; excluye 2025 antes del tipado semántico; ignora etiquetas, P75 y canal heredados.

La capa descriptiva conserva cobertura individual y usa la intersección de estados evaluables 5/7/9 para los cambios de exceso. Los cambios de inicio requieren S y S−1 evaluables en las tres definiciones. Los desgloses individuales conservan su H; los desgloses **pareados** por municipio, departamento, año, muchos ceros, P75=0 e historia insuficiente usan una definición de estrato fija de cinco años. Los denominadores comunes y las exclusiones quedan explícitos. Así, un cambio de composición no se interpreta como un cambio de etiqueta.

La capa predictiva mantiene el canal de cinco años como predictor y la elegibilidad basal de ausencia de exceso en origen T. X, fechas y claves son idénticos entre las tres variantes; solo cambia Y. Cada modelo, preparador y calibrador se ajusta independientemente. Si alguna variante carece de un rol temporal o tiene una sola clase en entrenamiento/calibración, se conservan las tres celdas del grupo como no evaluables antes de cualquier ajuste.

| Periodo | Entrenamiento | Calibración | Selección | Evaluación |
| --- | --- | --- | --- | --- |
| Desarrollo 2020 | 2012–2018 | Ene–jun 2019 | Jul–dic 2019 | 2020 |
| Desarrollo 2022 | 2012–2020 | Ene–jun 2021 | Jul–dic 2021 | 2022 |
| Estrés retrospectivo 2024 | 2012–2022 | Ene–jun 2023 | Jul–dic 2023 | 2024 |

Se reutilizan las tres familias y parámetros de EXP01, los horizontes 1/2, semilla 42 y un hilo. Los cortes se aplican al mes objetivo con embargo entre roles. Noviembre y diciembre de 2024 se conservan cuando existe soporte. El diseño contempla 9 celdas descriptivas y 54 predictivas: como máximo 54 ajustes de modelo/preparador y 54 calibraciones, únicamente tras autorización futura.

## Métricas e interpretación

Se reportan cobertura, etiquetas cambiadas 0→1 y 1→0, inicios, episodios, fragmentación, unión y relaciones ambiguas. El bundle conserva etiquetas mensuales y episodios completos, no solo los totales.

Las métricas predictivas distinguen la verdad propia de cada H y una referencia fija de inicio de cinco años. Las primeras describen sensibilidad a la definición; las segundas comparan alertas contra el mismo desenlace. Una probabilidad calibrada para Y propia no implica calibración respecto de la referencia fija. Se conservan AP/PR-AUC, Brier, sensibilidad, precisión, inicios perdidos, alertas y falsas alertas. FAR es falsas alertas dividido por alertas evaluables; AP no es precisión de alertas.

La selección utiliza todos los presupuestos enteros de falsas alertas posibles en selección sobre la verdad fija, respetando empates completos. Cada variante recibe el mismo límite; el gasto realizado puede ser distinto. El frente completo se conserva, sin elegir retrospectivamente una política por el resultado de evaluación.

La incertidumbre usa bootstrap pareado por municipio y año, 1.000 réplicas, semilla 42 y percentiles 2,5/97,5. Exige al menos dos municipios y dos años. Las celdas anuales devuelven intervalo nulo por soporte insuficiente, sin sustituto IID. No existe umbral aprobado de materialidad ni regla automática para declarar una ventana ganadora. Cambiar Y y mejorar sus métricas no demuestra mejor capacidad predictiva.

## Integración y protecciones

Los pipelines registrados son `exp02_preflight`, `exp02_synthetic` y `exp02`. El recorrido real es:

`preflight → autorización/carga → variantes → estabilidad → evaluación predictiva → publicación`

El catálogo materializa fuentes que solo consultan metadatos y un dataset final con ruta fija `tmp/kedro-migration/exp02-runs`. Se rechazan rutas externas, traversal, symlinks y solapamiento con tracking. La ruta absoluta equivalente que Kedro construye sí es válida.

El preflight no abre contenido privado, ajusta, calibra, reserva ni escribe MLflow. Comprueba commit limpio, protocolo/registro, autoridades públicas, catálogo/grafo, correspondencia del código cargado, runtime congelado, metadatos de fuentes y destinos. El descriptor de datos combina la identidad declarada del manifiesto con tamaño, tiempos e inode; **no afirma haber verificado contenido privado**. La admisión posterior a la autorización verifica hashes y reglas de contenido. `execution_ready=false` siempre.

La autorización futura mediante `SAT_DENGUE_EXP02_APPROVAL` vincula los ocho campos de `BINDINGS`, exige autoridad Mauricio, identidad real y decisión explícita del revisor independiente, reconocimiento retrospectivo y permiso explícito para los máximos 54/54 ajustes. Es un registro local auditable, no autenticación criptográfica. Debe crearse fuera de esta implementación después de revisar un preflight operativo nuevo.

Se revalidan autorización, código, entorno, configuración, fuentes y rutas antes de las etapas y de cada interfaz de ajuste. Los hashes de contenido se verifican en admisión y en fronteras de ejecución/publicación. La reserva se crea exclusivamente después de autorizar y admitir las fuentes; persiste ante fallos. Cambiar el archivo de aprobación no permite repetir la identidad científica reservada.

La publicación usa staging, fsync y renombre atómico, nunca sobrescritura. El manifiesto verifica todos los payloads antes de declarar éxito. MLflow se abre después de publicar y verificar el bundle; una interrupción anterior deja reserva persistente sin crear runs. Si falla el tracking, el bundle se conserva para una exportación posterior autorizada, sin reentrenar.

## Artefactos y tracking

El bundle local contiene manifiesto, procedencia, etiquetas, episodios, cobertura, cambios y desgloses, predicciones individuales de selección/evaluación, frentes, calibración, incertidumbre y motivos de no evaluación. `verified_result` comprueba integridad y estructura; `export_authorized` permite registrar una publicación existente sin ajustes, bajo las identidades autorizadas vigentes.

MLflow recibe una proyección cerrada con un parent comparativo y 63 children. Incluye dimensiones científicas, hashes, conteos, probabilidades agregadas, calibración y frentes sin desgloses municipales. La política epidémica está etiquetada como `include_all_years`. Los contadores reales permanecen en el bundle nativo; no se sustituyen por ceros en tracking. No se admiten identificadores municipales, predicciones individuales, rutas privadas, texto libre ni secretos. La proyección se valida nuevamente en el repositorio de artefactos MLflow.

Las pruebas usan tiendas y publicaciones aisladas; las rutas sintéticas no pueden coincidir ni solaparse con los destinos operativos protegidos. `exp02_synthetic` devuelve únicamente memoria con tracking deshabilitado y adaptadores fijos sin estimadores/calibradores reales. Sus resultados no son evidencia epidemiológica.

## Operación futura y gate humano

Después del merge decidido por Mauricio, otra preparación deberá construir e instalar el paquete revisado, verificar correspondencia y dependencias, preservar la tienda existente y emitir un preflight nuevo. El comando futuro es:

```sh
SAT_DENGUE_TRACKING_ROOT=tmp/kedro-migration/replay-mlflow \
KEDRO_DISABLE_TELEMETRY=yes \
kedro run --pipelines=exp02_preflight \
  --params=profile=exp02_preflight,tracking=enabled,experiment_id=EXP02
```

Este comando no se ejecuta operativamente durante la implementación. Mauricio y un revisor independiente deberán revisar sus identidades y condiciones antes de crear una autorización real. Solo después corresponderá la ejecución manual de Mauricio. El eje epidémico pendiente, la disponibilidad histórica no demostrada y la falta de umbral de materialidad deben mantenerse visibles en esa revisión.
