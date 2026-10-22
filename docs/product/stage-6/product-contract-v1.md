# Stage 6 — Product Contract v1 para el MVP académico E2E de solo lectura

## Estado, autoridad y límites

**Estado del documento:** contrato de producto v1 para decisión humana en Stage 6.

Este documento congela el alcance mínimo del MVP académico descrito en la [historia maestra del dashboard](../stage-1/PROD-04-dashboard-master-user-story.md), bajo la secuencia y los límites del [plan maestro](../../roadmap/master-plan.md). Conserva el cierre científico documentado en [Stage 5](../stage-5/README.md): G5 = `NOT_APPROVED` y champion_status = `NOT_SELECTED`.

El contrato define información y comportamiento observable. No implementa ni autoriza un API, frontend, adaptador, pipeline, modelo o notebook. Los valores del ejemplo son datos demostrativos creados exclusivamente para mostrar la forma del contrato; no son resultados científicos ni evidencia de desempeño.

## 1. Propósito y alcance

El producto es un MVP académico E2E de solo lectura para consultar resultados persistidos de dengue. El flujo futuro será:

`resultado persistido → API → dashboard`

La cobertura territorial comprende Tolima y Meta. El consumidor consulta un departamento y un periodo mensual; la respuesta conserva detalle municipal y separa los horizontes T+1 y T+2. Abrir o consultar el dashboard no entrena modelos, no ejecuta inferencia, no modifica datos y no registra feedback.

El MVP sirve para revisar trazabilidad, presentación e integración técnica. No afirma uso operativo, productivo, clínico ni de salud pública, y no autoriza acciones automáticas.

## 2. Estado científico y de gobernanza

- G5 = `NOT_APPROVED`.
- champion_status = `NOT_SELECTED`.
- No existe un Champion científico seleccionado.
- El MVP utiliza un candidato técnico provisional configurable por horizonte. La familia concreta se resuelve desde el registro del artefacto cargado; no se escribe directamente en código como XGBoost, LightGBM o GAM.
- El candidato podrá corresponder al modelo mejor clasificado por horizonte según la política comparativa existente, sin convertir ese orden técnico en aprobación científica.
- Sus resultados pueden viajar por el API únicamente con model_role = `PROVISIONAL_CANDIDATE` mientras no exista una decisión posterior que cambie la gobernanza.
- El candidato provisional no cambia la metodología científica, no reabre Stage 5 y nunca se presenta como Champion.
- `probability` es producida por el modelo o su posprocesamiento científico persistido.
- `alert_status` se deriva después, aplicando `probability >= threshold`. El API transporta ambos operandos y el resultado derivado para permitir su verificación, sin pedir al dashboard que seleccione el umbral.

La familia y la versión del modelo proceden del registro del artefacto cargado. Las métricas de evaluación no son producidas por el modelo durante la consulta: proceden de la evidencia histórica de Stage 5 y conservan su periodo, geografía, horizonte, procedimiento, numeradores y denominadores.

## 3. Endpoint previsto

El MVP prevé un único endpoint de lectura:

`GET /api/dashboard?department_code={code}&period={YYYY-MM}`

| Nombre | Ubicación | Tipo | Formato | Longitud | Obligatorio | Descripción | Ejemplo | Validación |
|---|---|---|---|---:|---|---|---|---|
| `department_code` | Query | String | Código DANE de departamento, solo dígitos | Exactamente 2 | Sí | Departamento que se desea consultar. En este MVP solo se admiten Tolima (`73`) y Meta (`50`). | `73` | Debe cumplir `^(50\|73)$`; cualquier otro valor produce `INVALID_DEPARTMENT_CODE`. |
| `period` | Query | String | `YYYY-MM` | Exactamente 7 | Sí | Periodo de referencia T solicitado. | `2026-09` | Debe representar un mes calendario válido y cumplir `^\d{4}-(0[1-9]\|1[0-2])$`; un formato inválido produce `INVALID_PERIOD_FORMAT`. |

El endpoint no se implementa en esta entrega.

## 4. Estructura de la respuesta

La respuesta JSON contiene exactamente cinco bloques de primer nivel:

| Bloque | Responsabilidad |
|---|---|
| `metadata` | Identifica el resultado consultado, sus periodos y la frescura de datos y generación. |
| `governance` | Expone el gate científico, la selección de Champion y la limitación obligatoria del candidato provisional. |
| `department` | Describe el departamento y confirma el periodo pedido por el consumidor. |
| `municipalities` | Contiene el contexto observado municipal y sus resultados T1/T2, incluidos los estados no disponibles. |
| `evaluation_context` | Aporta métricas históricas de Stage 5 con alcance, trazabilidad, numeradores y denominadores; no evalúa el resultado consultado. |

No se añaden bloques de conveniencia que dupliquen estas responsabilidades.

## 5. Diccionario canónico de campos

“Obligatorio” indica que la clave debe existir en una respuesta exitosa. Una clave obligatoria puede tener valor `null` solo cuando esta tabla lo autoriza. Un dato desconocido nunca debe convertirse automáticamente en cero.

| Campo | Bloque | Descripción | ¿Lo genera el modelo? | Fuente | Tipo y formato | Longitud máxima o rango | Obligatorio | Comportamiento cuando está ausente |
|---|---|---|---|---|---|---|---|---|
| `metadata` | Raíz | Metadatos del resultado persistido. | No | Persistencia | Objeto | 5 campos definidos | Sí | Error de contrato; no se fabrica el bloque. |
| `result_id` | `metadata` | Identificador estable e inmutable del conjunto de resultados. | No | Persistencia | String UUID | 36 caracteres | Sí | Error de contrato. |
| `reference_period` | `metadata` | Periodo mensual T usado como referencia. | No | Resultado persistido | String `YYYY-MM` | 7 caracteres | Sí | Error de contrato. |
| `generated_at` | `metadata` | Instante en que se generó el resultado. | No | Registro de ejecución | String RFC 3339 con zona | 35 caracteres | Sí | Error de contrato; no se sustituye por la hora actual. |
| `data_updated_at` | `metadata` | Instante de actualización del dato fuente asociado. | No | Registro de datos | String RFC 3339 o `null` | 35 caracteres | Sí | `null` cuando no existe una fecha acreditada. |
| `data_version` | `metadata` | Versión o huella del conjunto de datos usado. | No | Registro de datos | String | 128 caracteres | Sí | Error de contrato. |
| `governance` | Raíz | Estado científico y limitación de uso. | No | Gobernanza | Objeto | 4 campos definidos | Sí | Error de contrato. |
| `governance_gate` | `governance` | Gate científico al que corresponde el estado. | No | Gobernanza | String | 16 caracteres | Sí | Error de contrato. |
| `governance_status` | `governance` | Decisión vigente del gate. | No | Gobernanza | Enum cerrado | `APPROVED` o `NOT_APPROVED` | Sí | Error de contrato. |
| `champion_status` | `governance` | Indica si existe Champion seleccionado. | No | Gobernanza | Enum cerrado | `SELECTED` o `NOT_SELECTED` | Sí | Error de contrato. |
| `limitation` | `governance` | Texto que impide interpretar el candidato como Champion u operación autorizada. | No | Contenido de producto | String | 500 caracteres | Sí | Error de contrato cuando el estado no está aprobado. |
| `department` | Raíz | Contexto departamental de la consulta. | No | Referencia DANE / request | Objeto | 3 campos definidos | Sí | Error de contrato. |
| `department_code` | `department` | Código DANE del departamento. | No | Referencia DANE | String de 2 dígitos | Exactamente 2 | Sí | Error de contrato. |
| `department_name` | `department` | Nombre oficial del departamento. | No | Referencia DANE | String | 100 caracteres | Sí | Error de contrato. |
| `requested_period` | `department` | Periodo recibido en el parámetro `period`. | No | Request | String `YYYY-MM` | 7 caracteres | Sí | Error de contrato. |
| `municipalities` | Raíz | Municipios del departamento con contexto y resultados por horizonte. | No | Composición del API | Array de objetos | 0 a número oficial de municipios | Sí | Array vacío solo si el contrato futuro lo distingue de un 404; para este MVP, ninguna coincidencia produce 404. |
| `municipality_code` | `municipalities[]` | Código DANE del municipio. | No | Referencia DANE | String de 5 dígitos | Exactamente 5 | Sí | Error de contrato. |
| `municipality_name` | `municipalities[]` | Nombre oficial del municipio. | No | Referencia DANE | String | 150 caracteres | Sí | Error de contrato. |
| `cases_t` | `municipalities[]` | Casos observados en T bajo la definición vigente. | No | Datos epidemiológicos | Entero no negativo o `null` | 0 a 2 147 483 647 | Sí | `null` si el dato fuente no está disponible; nunca `0` por defecto. |
| `endemic_zone_t` | `municipalities[]` | Zona del canal endémico observada en T. | No | Lógica epidemiológica persistida | Enum cerrado | 5 valores | Sí | `UNAVAILABLE` si no puede calcularse. |
| `p25` | `municipalities[]` | Percentil 25 del canal endémico para T. | No | Lógica epidemiológica persistida | Número no negativo o `null` | 0 a 2 147 483 647 | Sí | `null` si no está disponible. |
| `median` | `municipalities[]` | Mediana (P50) del canal endémico para T. | No | Lógica epidemiológica persistida | Número no negativo o `null` | 0 a 2 147 483 647 | Sí | `null` si no está disponible. |
| `p75` | `municipalities[]` | Percentil 75 del canal endémico para T. | No | Lógica epidemiológica persistida | Número no negativo o `null` | 0 a 2 147 483 647 | Sí | `null` si no está disponible. |
| `results` | `municipalities[]` | Resultados T1 y T2 del municipio. | No | Composición del API | Array de objetos | Exactamente 2 elementos, uno por horizonte | Sí | Error de contrato. |
| `horizon` | `results[]` / `evaluation_records[]` | Horizonte mensual del resultado o métrica. | No | Configuración persistida | Enum cerrado | `T1` o `T2` | Sí | Error de contrato. |
| `target_period` | `results[]` | Mes objetivo real del horizonte. | No | Resultado persistido | String `YYYY-MM` | 7 caracteres | Sí | Error de contrato. |
| `probability` | `results[]` | Probabilidad persistida del evento objetivo. | Sí | Artefacto/modelo cargado | Decimal o `null` | 0 a 1 inclusive | Sí | `null` cuando `availability_status` no es `AVAILABLE`; nunca cero por defecto. |
| `threshold` | `results[]` | Umbral persistido aplicable al procedimiento y horizonte. | No; es posprocesamiento/decisión persistida | Artefacto de decisión | Decimal o `null` | 0 a 1 inclusive | Sí | `null` cuando no hay resultado calculado; nunca se selecciona en el dashboard. |
| `alert_status` | `results[]` | Alerta derivada de comparar probabilidad y umbral. | No; es derivada | Resultado persistido / regla contractual | Enum cerrado | 3 valores | Sí | `UNAVAILABLE` si no se puede comparar. |
| `availability_status` | `results[]` | Estado de disponibilidad del resultado. | No | Validación de datos y ejecución | Enum cerrado | 4 valores | Sí | Error de contrato. |
| `availability_reason` | `results[]` | Explicación breve cuando el resultado no está disponible. | No | Validación de datos y ejecución | String o `null` | 300 caracteres | Sí | `null` solo para `AVAILABLE`; texto obligatorio en cualquier otro estado. |
| `model_family` | `results[]` | Familia registrada del artefacto cargado; no seleccionada por el cliente. | No | Registro del artefacto | String o `null` | 32 caracteres | Sí | `null` si no se calculó un resultado. No es un enum contractual. |
| `model_role` | `results[]` | Rol de gobernanza del modelo. | No | Gobernanza / registro | Enum cerrado o `null` | 2 valores | Sí | `null` si no existe artefacto asociado; con G5 no aprobado solo puede ser `PROVISIONAL_CANDIDATE`. |
| `model_version` | `results[]` | Versión exacta del artefacto cargado. | No | Registro del artefacto | String o `null` | 128 caracteres | Sí | `null` si no existe artefacto asociado. |
| `procedure_id` | `results[]` / `evaluation_records[]` | Identificador estable del procedimiento científico. | No | Registro de evaluación | String o `null` | 128 caracteres | Sí | `null` cuando no existe ejecución asociada. |
| `evaluation_context` | Raíz | Contexto histórico de Stage 5, separado del resultado actual. | No | Stage 5 | Objeto | 2 campos definidos | Sí | Error de contrato. |
| `demonstrative_values` | `evaluation_context` | Marca explícita de que el ejemplo no contiene resultados científicos reales. | No | Documento contractual | Boolean | `true` o `false` | Sí | Error de contrato en ejemplos. |
| `evaluation_records` | `evaluation_context` | Métricas históricas por procedimiento y horizonte. | No | Stage 5 | Array de objetos | 0 o más registros | Sí | Array vacío cuando no hay evidencia compatible; no se inventan métricas. |
| `evaluation_period_start` | `evaluation_records[]` | Inicio del periodo histórico evaluado. | No | Stage 5 | String `YYYY-MM` | 7 caracteres | Sí | Registro no publicable sin alcance temporal. |
| `evaluation_period_end` | `evaluation_records[]` | Fin del periodo histórico evaluado. | No | Stage 5 | String `YYYY-MM` | 7 caracteres | Sí | Registro no publicable sin alcance temporal. |
| `evaluation_geography` | `evaluation_records[]` | Geografía y población a las que aplican las métricas. | No | Stage 5 | String | 300 caracteres | Sí | Registro no publicable sin alcance geográfico. |
| `auroc` | `evaluation_records[]` | AUROC histórica sobre el alcance declarado. | No | Stage 5 | Decimal o `null` | 0 a 1 inclusive | Sí | `null` si no es evaluable. |
| `average_precision` | `evaluation_records[]` | Average Precision histórica. | No | Stage 5 | Decimal o `null` | 0 a 1 inclusive | Sí | `null` si no es evaluable. |
| `brier` | `evaluation_records[]` | Brier histórico de probabilidades. | No | Stage 5 | Decimal o `null` | 0 a 1 inclusive | Sí | `null` si no aplica o no es evaluable. |
| `false_alerts` | `evaluation_records[]` | Numerador histórico de alertas falsas. | No | Stage 5 | Entero no negativo o `null` | 0 a 2 147 483 647 | Sí | `null` si el denominador no está disponible; nunca cero por defecto. |
| `alerts_emitted` | `evaluation_records[]` | Denominador histórico de alertas emitidas. | No | Stage 5 | Entero no negativo o `null` | 0 a 2 147 483 647 | Sí | `null` si no está disponible. |
| `false_alert_ratio` | `evaluation_records[]` | Cociente histórico `false_alerts / alerts_emitted`. | No | Stage 5 | Decimal o `null` | 0 a 1 inclusive | Sí | `null` si el denominador es cero o desconocido. |
| `onsets_detected` | `evaluation_records[]` | Numerador histórico de inicios detectados. | No | Stage 5 | Entero no negativo o `null` | 0 a 2 147 483 647 | Sí | `null` si no está disponible. |
| `actual_onsets` | `evaluation_records[]` | Denominador histórico de inicios reales conocidos. | No | Stage 5 | Entero no negativo o `null` | 0 a 2 147 483 647 | Sí | `null` si no está disponible. |
| `onset_sensitivity` | `evaluation_records[]` | Cociente histórico `onsets_detected / actual_onsets`. | No | Stage 5 | Decimal o `null` | 0 a 1 inclusive | Sí | `null` si el denominador es cero o desconocido. |

El API entrega `probability` y `threshold` como decimales entre `0` y `1`. El dashboard puede convertir `0.61` en `61 %` para presentarlo, sin modificar el valor ni su significado.

## 6. Catálogos cerrados

| Campo | Valores permitidos | Semántica mínima |
|---|---|---|
| `horizon` | `T1`, `T2` | Uno y dos meses después del periodo de referencia. |
| `endemic_zone_t` | `EXITO`, `SEGURIDAD`, `ALERTA`, `EXCESO`, `UNAVAILABLE` | Estado observado del canal en T; no es la alerta predictiva. |
| `alert_status` | `ALERT`, `NO_ALERT`, `UNAVAILABLE` | `ALERT` cuando `probability >= threshold`; `NO_ALERT` cuando es menor; `UNAVAILABLE` si no hay comparación válida. |
| `availability_status` | `AVAILABLE`, `INSUFFICIENT_HISTORY`, `MISSING_DATA`, `NOT_CALCULATED` | Distingue resultado válido, historia insuficiente, dato ausente y cálculo pendiente. |
| `governance_status` | `APPROVED`, `NOT_APPROVED` | Estado de la decisión científica vigente. |
| `champion_status` | `SELECTED`, `NOT_SELECTED` | Existencia o ausencia de Champion seleccionado. |
| `model_role` | `PROVISIONAL_CANDIDATE`, `CHAMPION` | Rol científico del artefacto. `CHAMPION` exige gobernanza compatible. |

No se admiten sinónimos, valores adicionales ni estados implícitos en este MVP.

## 7. Información que no viene del API

| Información | Fuente | Motivo |
|---|---|---|
| Títulos y etiquetas | Contenido estático del frontend | Son texto de presentación, no datos de dominio variables. |
| Explicación del P75 | Contenido educativo versionado del frontend | Explica un concepto; el API solo entrega el valor acreditado. |
| Colores, iconos y estilos | Sistema de diseño del frontend | La presentación no cambia la semántica del enum. |
| Orden y diseño de tarjetas | Implementación del frontend | Es una decisión de interfaz. |
| Fecha y hora actual de Bogotá | Reloj del cliente o servicio de tiempo de la aplicación en `America/Bogota` | No es la fecha de generación ni de actualización de datos. |
| GeoJSON municipal de Tolima y Meta | Recurso estático y versionado del frontend | Evita acoplar geometría a cada respuesta de resultados. |
| Leyenda del mapa | Contenido y sistema de diseño del frontend | Traduce estados ya contratados a presentación accesible. |
| Aviso de datos demostrativos | Contenido estático del frontend | Debe acompañar el prototipo y los fixtures de demostración. |
| Textos para estados vacíos | Contenido estático del frontend | Adaptan la explicación al componente sin alterar el código de ausencia recibido. |
| JSON local usado durante el desarrollo inicial | Fixture versionado del frontend | Permite construir la interfaz antes del API sin fingir que el fixture es una respuesta real. |

El GeoJSON será un recurso estático del frontend. El API solo proporcionará el código DANE y el estado municipal necesarios para unir resultado y geometría.

## 8. Ejemplo completo de request

```http
GET /api/dashboard?department_code=73&period=2026-09
Accept: application/json
```

- `department_code=73` solicita Tolima mediante su código DANE de dos dígitos.
- `period=2026-09` solicita septiembre de 2026 como periodo de referencia T.
- `Accept: application/json` declara el formato de respuesta esperado.

## 9. Ejemplo completo de response

El siguiente JSON es válido respecto de este contrato, pero todos sus identificadores, versiones, métricas y valores son datos demostrativos. No representan resultados científicos reales ni una predicción operativa.

```json
{
  "metadata": {
    "result_id": "7e57d004-2b97-4b77-9f8d-111111111111",
    "reference_period": "2026-09",
    "generated_at": "2026-10-03T14:30:00-05:00",
    "data_updated_at": "2026-10-02T18:00:00-05:00",
    "data_version": "demo-data-2026-09-v1"
  },
  "governance": {
    "governance_gate": "G5",
    "governance_status": "NOT_APPROVED",
    "champion_status": "NOT_SELECTED",
    "limitation": "Resultado académico demostrativo de un candidato provisional; no existe Champion aprobado ni uso operativo autorizado."
  },
  "department": {
    "department_code": "73",
    "department_name": "Tolima",
    "requested_period": "2026-09"
  },
  "municipalities": [
    {
      "municipality_code": "73001",
      "municipality_name": "Ibagué",
      "cases_t": 48,
      "endemic_zone_t": "ALERTA",
      "p25": 22.0,
      "median": 35.0,
      "p75": 47.0,
      "results": [
        {
          "horizon": "T1",
          "target_period": "2026-10",
          "probability": 0.61,
          "threshold": 0.55,
          "alert_status": "ALERT",
          "availability_status": "AVAILABLE",
          "availability_reason": null,
          "model_family": "xgboost",
          "model_role": "PROVISIONAL_CANDIDATE",
          "model_version": "demo-xgb-t1-v1",
          "procedure_id": "demo-procedure-t1"
        },
        {
          "horizon": "T2",
          "target_period": "2026-11",
          "probability": 0.42,
          "threshold": 0.50,
          "alert_status": "NO_ALERT",
          "availability_status": "AVAILABLE",
          "availability_reason": null,
          "model_family": "lightgbm",
          "model_role": "PROVISIONAL_CANDIDATE",
          "model_version": "demo-lgbm-t2-v1",
          "procedure_id": "demo-procedure-t2"
        }
      ]
    },
    {
      "municipality_code": "73349",
      "municipality_name": "Honda",
      "cases_t": 9,
      "endemic_zone_t": "SEGURIDAD",
      "p25": 6.0,
      "median": 10.0,
      "p75": 15.0,
      "results": [
        {
          "horizon": "T1",
          "target_period": "2026-10",
          "probability": 0.28,
          "threshold": 0.55,
          "alert_status": "NO_ALERT",
          "availability_status": "AVAILABLE",
          "availability_reason": null,
          "model_family": "xgboost",
          "model_role": "PROVISIONAL_CANDIDATE",
          "model_version": "demo-xgb-t1-v1",
          "procedure_id": "demo-procedure-t1"
        },
        {
          "horizon": "T2",
          "target_period": "2026-11",
          "probability": null,
          "threshold": null,
          "alert_status": "UNAVAILABLE",
          "availability_status": "NOT_CALCULATED",
          "availability_reason": "El resultado T2 todavía no ha sido calculado para este municipio y periodo.",
          "model_family": null,
          "model_role": null,
          "model_version": null,
          "procedure_id": null
        }
      ]
    }
  ],
  "evaluation_context": {
    "demonstrative_values": true,
    "evaluation_records": [
      {
        "horizon": "T1",
        "procedure_id": "demo-procedure-t1",
        "evaluation_period_start": "2021-01",
        "evaluation_period_end": "2024-12",
        "evaluation_geography": "Tolima y Meta; valores demostrativos, no evidencia científica",
        "auroc": 0.74,
        "average_precision": 0.68,
        "brier": 0.17,
        "false_alerts": 18,
        "alerts_emitted": 60,
        "false_alert_ratio": 0.30,
        "onsets_detected": 14,
        "actual_onsets": 35,
        "onset_sensitivity": 0.40
      },
      {
        "horizon": "T2",
        "procedure_id": "demo-procedure-t2",
        "evaluation_period_start": "2021-01",
        "evaluation_period_end": "2024-12",
        "evaluation_geography": "Tolima y Meta; valores demostrativos, no evidencia científica",
        "auroc": 0.71,
        "average_precision": 0.64,
        "brier": 0.19,
        "false_alerts": 21,
        "alerts_emitted": 70,
        "false_alert_ratio": 0.30,
        "onsets_detected": 16,
        "actual_onsets": 40,
        "onset_sensitivity": 0.40
      }
    ]
  }
}
```

El ejemplo muestra una probabilidad disponible por encima del umbral (`0.61 >= 0.55`, por tanto `ALERT`), otra por debajo y un resultado T2 no calculado con valores científicos en `null`. Las métricas incluyen numeradores y denominadores para evitar tasas sin soporte.

## 10. Respuestas de error

| HTTP status | `error_code` | Mensaje exacto para el consumidor | Significado | Causa o ejemplo | Comportamiento esperado del dashboard |
|---:|---|---|---|---|---|
| 400 | `INVALID_DEPARTMENT_CODE` | `El código del departamento no es válido.` | El parámetro no identifica Tolima o Meta con el formato aprobado. | `department_code=76` o longitud distinta de 2. | Conservar la selección anterior si existe y mostrar el mensaje sin resultados de reemplazo. |
| 400 | `INVALID_PERIOD_FORMAT` | `El periodo debe usar el formato YYYY-MM.` | El periodo no es un mes válido con el formato contratado. | `period=2026-13` o `period=09-2026`. | Marcar el control de periodo y mostrar el mensaje; no reintentar con una fecha inventada. |
| 404 | `DASHBOARD_DATA_NOT_FOUND` | `No existen resultados para el departamento y periodo solicitados.` | La consulta es válida, pero no hay un conjunto persistido compatible. | Tolima y un periodo todavía no procesado. | Mostrar un estado vacío para esa consulta, sin confundirlo con cero riesgo o fallo técnico. |
| 500 | `INTERNAL_ERROR` | `No fue posible obtener la información del dashboard.` | El servidor no pudo completar una consulta válida. | Fallo interno inesperado. | Mostrar un error recuperable y permitir reintento; no exhibir datos obsoletos como si fueran la respuesta pedida. |

Formato único del cuerpo de error:

```json
{
  "error_code": "INVALID_PERIOD_FORMAT",
  "message": "El periodo debe usar el formato YYYY-MM."
}
```

Los mensajes no exponen trazas, rutas internas, consultas, nombres de servicios ni otros detalles técnicos.

## 11. Manejo de ausencias

| Situación | Representación contractual | Qué debe mostrar el dashboard |
|---|---|---|
| Resultado disponible | `availability_status = AVAILABLE`, probabilidad y umbral decimales, y alerta coherente. | Probabilidad formateada, umbral, alerta textual y trazabilidad; debe mantener visible la gobernanza. |
| Historia insuficiente | `availability_status = INSUFFICIENT_HISTORY`, valores predictivos en `null` y razón explícita. | “Historia insuficiente” y la razón; no usar color de bajo riesgo ni cero. |
| Dato fuente ausente | `availability_status = MISSING_DATA`, valores afectados en `null` y razón explícita. | “Dato fuente ausente” y la razón; distinguirlo de historia insuficiente. |
| Resultado todavía no calculado | `availability_status = NOT_CALCULATED`, valores predictivos en `null` y razón explícita. | “Resultado todavía no calculado”; no iniciar cálculo desde la vista de solo lectura. |
| Error de consulta | Respuesta HTTP de la sección 10, fuera del cuerpo exitoso. | Mensaje exacto y comportamiento definidos para el error; nunca convertirlo en un municipio no disponible. |

Los primeros cuatro estados pertenecen al dominio de una respuesta exitosa. El error de consulta pertenece al transporte y no sustituye un estado municipal.

## 12. Criterios E2E de aceptación

El futuro MVP se considera exitoso cuando:

1. El pipeline genera un resultado persistido.
2. El API entrega una respuesta conforme a este contrato.
3. El dashboard reproduce correctamente departamento, municipio y periodo.
4. Presenta probabilidad, umbral y alerta sin alterar su significado.
5. Presenta canal endémico, casos observados y percentiles.
6. Presenta gobernanza y selección científica.
7. Permite consultar la trazabilidad del resultado.
8. Representa correctamente los estados no disponibles.
9. El candidato provisional nunca aparece como Champion aprobado.

Estos criterios validan integración y comprensión del MVP; no aprueban G5 ni convierten resultados demostrativos o históricos en predicciones operativas.

## 13. Fuera de alcance

Quedan explícitamente fuera del alcance:

- autenticación;
- administración de usuarios;
- paginación;
- caché productiva;
- escritura de feedback;
- reentrenamiento desde el dashboard;
- operación productiva;
- monitoreo productivo;
- selección de un nuevo Champion;
- modificación de modelos o umbrales;
- implementación del API o frontend en Stage 6.

También quedan fuera de esta entrega cualquier cambio de código, adaptadores, pipelines, modelos, notebooks o pruebas de software.
