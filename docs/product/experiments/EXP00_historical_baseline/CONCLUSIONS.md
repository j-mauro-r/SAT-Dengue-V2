# EXP00 — Conclusiones de la línea base histórica anterior a Kedro

## Estado

- Conclusión científica histórica: **completa**.
- Verificación de reproducibilidad controlada con Kedro: **aprobada** el 25 de octubre de 2026.
- Registro formal en MLflow: **completado** el 25 de octubre de 2026.
- G5: **`NOT_APPROVED`**.
- Champion: **`not_selected`**.
- Decisión de los seis procedimientos: **`does_not_meet`**.

## Objetivo

EXP00 registra como línea base oficial el último entrenamiento y la evaluación
realizados antes de la migración a Kedro. Su propósito es conservar un punto de
comparación reproducible para los experimentos posteriores. Esta ejecución fue un
*replay* de resultados congelados: no entrenó modelos, no recalibró probabilidades,
no cambió umbrales y no realizó una nueva selección.

## Resultado científico

Los procedimientos conservados de XGBoost, LightGBM y GAM para T+1 y T+2
mejoraron la detección de inicios frente a la persistencia, pero los seis
incumplieron la restricción predefinida de falsas alertas. Por tanto, ninguno es
apto para convertirse en champion ni para desplegarse como modelo operativo.

| Modelo | Horizonte | AUROC | Precisión promedio | Brier | Inicios detectados | Sensibilidad de inicios | Alertas emitidas | Falsas alertas | Razón de falsas alertas |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GAM | T+1 | 0,8093 | 0,6448 | 0,1477 | 20 de 86 | 23,26 % | 321 | 151 | 47,04 % |
| LightGBM | T+1 | 0,8192 | 0,6689 | 0,1431 | 34 de 86 | 39,53 % | 403 | 218 | 54,09 % |
| XGBoost | T+1 | 0,8189 | 0,6757 | 0,1433 | 22 de 86 | 25,58 % | 350 | 177 | 50,57 % |
| GAM | T+2 | 0,7465 | 0,5210 | 0,1767 | 62 de 86 | 72,09 % | 611 | 406 | 66,45 % |
| LightGBM | T+2 | 0,7585 | 0,5469 | 0,1689 | 55 de 86 | 63,95 % | 530 | 336 | 63,40 % |
| XGBoost | T+2 | 0,7638 | 0,5611 | 0,1672 | 48 de 86 | 55,81 % | 469 | 289 | 61,62 % |

Cada procedimiento se evaluó sobre 912 ejemplos del bloque consumido de 2025,
con 86 inicios reales.

## Conclusiones clave

1. **Una mayor capacidad de discriminación no garantiza utilidad operativa.**
   Los valores de AUROC, precisión promedio y Brier muestran señal predictiva,
   pero ningún procedimiento mantuvo las falsas alertas dentro del límite
   científico aprobado.
2. **T+2 aumenta la sensibilidad a costa de alertar demasiado.** GAM T+2 alcanzó
   la mayor sensibilidad, 72,09 %, pero también la mayor razón de falsas alertas,
   66,45 %. La ganancia de detección no constituye una mejora operativa.
3. **LightGBM T+1 presentó el mejor equilibrio probabilístico en ese horizonte.**
   Obtuvo el AUROC más alto, el Brier más bajo y la mayor sensibilidad de T+1;
   aun así, su razón de falsas alertas de 54,09 % impide aprobarlo.
4. **XGBoost T+1 obtuvo la mayor precisión promedio de T+1**, pero detectó solo
   22 de 86 inicios y tampoco cumplió la restricción de falsas alertas.
5. **No existe un champion en EXP00.** Elegir el procedimiento con la mayor
   sensibilidad o AUROC ignoraría el criterio operativo previamente acordado.
6. **La línea base confirma la hipótesis que motiva la siguiente iteración:**
   predecir exceso mensual no fue suficiente para anticipar inicios con una carga
   aceptable de falsas alertas. Los experimentos posteriores deben evaluar la
   predicción directa de inicios y comparar contra EXP00 bajo criterios comunes.

## Evidencia de registro en MLflow

- Experimento MLflow: `sat-dengue-bounded-v1`.
- Ejecución padre: `4a93225adb404e20a191a55b92f69457`.
- Hipótesis: `EXP00-H0`.
- Commit reproducido: `bebed44f79c10ef584b748dc33fcdc0933c0391b`.
- Hash canónico del protocolo:
  `4f8e32d8c70ba1661b84efca3cb1cc25288335bbceb2508cec970231756b920b`.
- Identidad del bundle:
  `f01fae3594249ab51fe3e5a19d3f8b88a0c9d2d59af648bddfcf4f01a63e8a10`.
- Identidad del pipeline:
  `d68ad5b031432f9480fd31a646198e3a5a9d3d7237f7eb6aa2599af08335291f`.
- Ventana evaluada: `2025-01..2025-12`.
- Semilla: `42`.
- Ajustes reales realizados: `0`.
- Almacenamiento local:
  `tmp/kedro-migration/replay-mlflow`.

Las seis ejecuciones hijas finalizaron correctamente:

| Modelo | Horizonte | Identificador de ejecución |
|---|---|---|
| XGBoost | T+1 | `943290e169484064a7849adad653bdf5` |
| LightGBM | T+1 | `5a46d1fca0cf4352a6748bca7b016c74` |
| GAM | T+1 | `424e90ea317f4ad6b08c87ce0077f730` |
| XGBoost | T+2 | `c5108cc27baa4af38e449454cfbc776f` |
| LightGBM | T+2 | `46b32f3f7f094e5abfb342eefb5f7702` |
| GAM | T+2 | `835bf433951e4a44b609fd3314d3a366` |

## Evidencia de reproducibilidad

Las pruebas protegidas de extremo a extremo de Kedro y paridad de migración
finalizaron con **78 aprobadas, 0 fallidas y 8 advertencias no bloqueantes** en
1.492,84 segundos. Verificaron el replay de componentes guardados, la trazabilidad
completa, la preservación, el reinicio determinista y la ausencia de entrenamiento
o reentrenamiento real.

Comando de verificación:

```bash
python -m pytest \
  tests/integration/test_kedro_e2e.py \
  tests/integration/test_migration_parity.py \
  --require-migration-evidence -q
```

## Interpretación y limitaciones

- El bloque de comparación de 2025 ya fue consumido y permanece exclusivamente
  disponible para replay y comparación retrospectiva.
- EXP00 demuestra reproducibilidad; no aporta evidencia confirmatoria nueva ni
  constituye una validación prospectiva.
- Los datos fueron consolidados retrospectivamente y no demuestran su
  disponibilidad histórica en un escenario operativo real.
- MLflow conserva métricas, parámetros, etiquetas y recibos de trazabilidad, pero
  no copia los conjuntos de datos científicos ni los modelos protegidos.
- Se mantiene la limitación documentada de transferencia de calibración a los
  modelos finales reajustados.
- Ningún procedimiento está autorizado para despliegue o inferencia en línea.
- La confirmación final de un futuro champion requerirá datos no utilizados para
  entrenamiento, calibración, ajuste, selección ni decisiones científicas previas.

## Decisión

EXP00 queda establecido como la línea base histórica oficial de SAT-Dengue-V2.
Sus métricas y conclusiones deben permanecer inmutables. Los experimentos futuros
podrán compararse con esta referencia, pero no reinterpretar 2025 como una prueba
final ciega ni modificar retroactivamente el resultado `does_not_meet`.
