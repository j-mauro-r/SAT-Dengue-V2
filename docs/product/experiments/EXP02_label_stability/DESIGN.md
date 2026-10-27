# EXP02 — Diseño de estabilidad de etiquetas y episodios

## Autoridad y límites

La segunda fila del [plan oficial](../experimentos.md) defineEXP02. No es una ablación de variables. Se mantienen G5`NOT_APPROVED`, champion`not_selected`, exclusión de2025 y2024como estrés retrospectivo. La implementación no autoriza lectura privada, ejecución ni decisiones científicas nuevas. El [protocolo](protocol.json) fija la comparación; el registro conserva su hash canónico.

## Auditoría científica

`data/consolidation.py::history_periods_for_target` requiere el mismo mes de losHaños inmediatamente anteriores al año objetivo. `percentile_type7` fija interpolación lineal; `compute_current_endemic_channel` ya aceptaH. DEC-120/121/122del [registro](../../traking-concluciones.md#dec-122) mantienen ceros respaldados por cobertura y todos los años epidémicos; no se sustituye un mes faltante por otro año. El percentil usa solo meses anteriores al objetivo y, para h=1/2, anteriores al origen. El conteo del objetivo pertenece únicamente a la verdad retrospectiva.

P75=0con historia completa: cero no es exceso y cualquier conteo positivo sí lo es. Historia incompleta o conteo desconocido: no evaluable. No se convierte desconocido en cero. `experiments/onset.py::labels` exige los estados exactosS/S−1, también en enero/diciembre; no se utiliza el T+1futuro como predictor ni como filtro de elegibilidadT.

Un episodio es una secuencia máxima de exceso en meses consecutivos conocidos. Un hueco rompe la secuencia y genera censura, no un inicio confirmado. Se conserva identificador local, duración observada y censura izquierda/derecha. Los episodios pueden cruzar años; recortar un periodo no crea nuevos inicios ni sustituye la duración global por la porción observada. Fragmentación: un episodio de referencia intersecta más de uno de la variante en claves comunes; unión: la relación inversa. Se informan denominadores y episodios sin solapamiento.

Las notas locales de Umaña y V1 apoyan analizar episodios, incertidumbre y sensibilidad5/7/9, pero no establecen causalidad ni una regla transferible para excluir años epidémicos del percentil mensual. El ejemploINSde2015–2022que excluye2016/2019es contextual, no una política automática para cada municipio/corte. El [registro de brotes](../../../research/colombia-dengue-outbreak-events.md) no es verdad de entrenamiento. Por tanto se incluye toda historia válida y el segundo eje queda `pending_scientific_definition`, sin fabricar variantes o resultados.

El intervalo común documentado desde2007es evidencia histórica de cobertura, no garantía de completitud de cada municipio. Con historia completa, nueve años permitirían estados desde2016; enero todavía puede carecer de predecesor conocido. La carga autorizada determina soporte real; nunca se inventa historia ni se presume soporte suficiente por las fechas nominales.

## Cohortes y controles constantes

Se reutilizan los calendarios EXP01: entrenamiento2012–2018/calibración2019-01..06/selección2019-07..12/evaluación2020; entrenamiento2012–2020/calibración2021-01..06/selección2021-07..12/evaluación2022; entrenamiento2012–2022/calibración2023-01..06/selección2023-07..12/evaluación2024. Los límites son meses objetivo; los embargos por origen se conservan. Noviembre y diciembre2024se mantienen cuando el horizonte dispone de sus orígenes y contexto;2025no interviene.

CapaA: conservar todas las etiquetas5/7/9y su cobertura individual; comparar exceso e inicio en respectivas intersecciones de disponibilidad, sin filtrar por valor deY. Desgloses locales por municipio, departamento y periodo, conP75=0, cantidad de historia y proporción de ceros. “Mayoría de ceros” significa fracción histórica5años>0.5y es solo un descriptor, no una selección poblacional.

CapaB: construirXuna sola vez con el canal aprobado5años y el mismo allowlist de29predictores EXP01. Elegibilidad operativa común=estado5años no excesivo enT; no cambiarXo población al variarY. Intersectar disponibilidad de objetivos5/7/9y deXen cada rol. Entrenar cada objetivo de inicio por separado, con misma familia/configuración/semilla y preparador independiente. No reutilizar modelos de otra definición.

Se congelan9celdas descriptivas(3definiciones×3periodos) y54predictivas(3definiciones×3periodos×2horizontes×3familias). Todas las celdas existen aun sin soporte; no se omiten silenciosamente. Máximo54fits/preparadores/calibradores, únicamente en futura ejecución autorizada. Si cualquier variante tiene rol vacío o entrenamiento/calibración de clase única, el grupo pareado completo queda no evaluable antes de ajustar. No hay fallback ni selección automática de ventana.

## Interpretación predictiva

Se reutilizan modelos, sigmoid y métricas existentes. Calibrar cada modelo contra su propiaYcon rol temporal separado. Frente principal: todos los topes enteros de falsas alertas de selección, usando inicio5años como referencia fija para las tres variantes. Los topes se emparejan en selección; no prometen igual carga realizada en evaluación. Se conserva el frente completo, sin elegir retrospectivamente un presupuesto.

Separar métricas contraYpropia y contra referencia5años. Las primeras describen sensibilidad a la definición; las segundas permiten comparar alertas sobre el mismo desenlace. Probabilidad calibrada paraYpropia no implica calibración para referencia5años. Registrar AP/PR-AUC, Brier, sensibilidad, precisión, inicios perdidos, alertas y falsas alertas; FAR=falsas/alertas. No confundir APcon precisión ni filas con episodios.

Bootstrap pareado por municipio y año,1000réplicas/semilla42, percentiles2.5/97.5; exigir al menos2municipios y2años. Celdas anuales devuelven intervalo nulo por soporte insuficiente, sin sustitutoIID. No hay umbral de materialidad aprobado ni regla para declarar ganador. La revisión humana distinguirá hallazgo descriptivo, interpretación, limitación e hipótesis.

## Seguridad e integración

Preflight sin contenido privado, fits, calibración, reserva ni escrituraMLflow. Debe comprobar commit limpio, protocolo/registro/configuración, código instalado, entorno, identidades declaradas, rutas y grafo/catálogo materializado. `execution_ready=false` siempre. La autorización posterior vía`SAT_DENGUE_EXP02_APPROVAL`vincula commit, protocolo, datos, configuración, código, entorno y destinos; exige Mauricio, revisión independiente, reconocimiento retrospectivo y presupuesto explícito.

La carga reutiliza la admisiónrawcorregida deEXP01: ignorar etiquetas/canal/P75heredados; excluir2025antes de tipado semántico; validar fuentes y dimensiones después de autorizar. Revalidar identidades antes de reserva, ajuste y publicación; reservar persistentemente, publicar atómicamente y no sobrescribir. Un fallo exige recuperación humana; no borrar reservas ni reintentar ciencia automáticamente.

El bundle local conserva manifiesto, procedencia, etiquetas/episodios, resultados, frentes, probabilidades, calibración, incertidumbre y motivos de no evaluación para exportar sin entrenar otra vez. MLflow solo recibe una proyección cerrada y agregada: parentcomparativo y63childrencon dimensiones científicas validadas. Nunca IDsmunicipales, predicciones individuales, rutas privadas, texto libre ni secretos. Pruebas en tiendas temporales aisladas; futura tienda formal mediante`SAT_DENGUE_TRACKING_ROOT`.

La verificación sintética demuestra contratos y recorrido técnico, no evidencia epidemiológica. Preparación operacional, preflight definitivo, autorización real y ejecución manual corresponden a otra sesión después del merge decidido por Mauricio.
