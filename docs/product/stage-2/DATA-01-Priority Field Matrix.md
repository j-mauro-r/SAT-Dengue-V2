# SAT-Dengue V2 — DATA-01 Priority Field Matrix

Date: 2026-10-15
Status: Stage 2 working artifact (Data Understanding). Not a final 69-column signed mapping.

## Purpose

This matrix documents the first priority fields for Stage 2 checks, linking observed CSV names to intended meaning and source references.

Scope limits:
- Documentation-only matrix.
- No data transformation decisions are approved by this file.
- Stage 2 remains open and G2 is not approved.

## Priority Field Matrix

| Domain | CSV field | Intended meaning (working) | Source reference | Source version/period | Evidence state | Notes |
|---|---|---|---|---|---|---|
| Epidemiological | COD_EVE | Event code (e.g., dengue, severe dengue) | https://www.ins.gov.co/BibliotecaDigital/210_220_580_Dengue_2019.pdf | INS guideline (2019) | Documented in source | Session could not extract machine-readable clauses from PDF; verify with citable text later. |
| Epidemiological | INI_SIN | Symptom onset date | https://www.ins.gov.co/Direcciones/Vigilancia/Lineamientosydocumentos/3.%20Diccionario_de_datos_Sivigila%202018_2020.pdf | INS SIVIGILA dictionary (2018–2020) | Documented in source + Confirmed in data (field presence) | In-scope quality checks executed in notebook. |
| Epidemiological | FEC_NOT | Notification date | https://www.ins.gov.co/Direcciones/Vigilancia/Lineamientosydocumentos/3.%20Diccionario_de_datos_Sivigila%202018_2020.pdf | INS SIVIGILA dictionary (2018–2020) | Documented in source + Confirmed in data (field presence) | Used only for diagnostics and consistency checks; no automatic replacement policy applied. |
| Epidemiological | ANO | Epidemiological year candidate | https://www.ins.gov.co/Direcciones/Vigilancia/Lineamientosydocumentos/3.%20Diccionario_de_datos_Sivigila%202018_2020.pdf | INS SIVIGILA dictionary (2018–2020) | Confirmed in data + Pending official textual confirmation | Descriptive consistency checks against ISO week-year were run; not an official rule validation. |
| Epidemiological | SEMANA | Epidemiological week candidate | https://www.ins.gov.co/Direcciones/Vigilancia/Lineamientosydocumentos/3.%20Diccionario_de_datos_Sivigila%202018_2020.pdf | INS SIVIGILA dictionary (2018–2020) | Confirmed in data + Pending official textual confirmation | Descriptive checks only; semantics pending official confirmation. |
| Epidemiological | COD_DPTO_R | Residence department code | https://www.ins.gov.co/Direcciones/Vigilancia/Lineamientosydocumentos/3.%20Diccionario_de_datos_Sivigila%202018_2020.pdf | INS SIVIGILA dictionary (2018–2020) | Confirmed in data | Used for Tolima/Meta residence filtering in official notebook. |
| Epidemiological | COD_MUN_R | Residence municipality code | https://www.ins.gov.co/Direcciones/Vigilancia/Lineamientosydocumentos/3.%20Diccionario_de_datos_Sivigila%202018_2020.pdf | INS SIVIGILA dictionary (2018–2020) | Confirmed in data | Treated as string-style code fields in notebook to preserve leading zeros. |
| Epidemiological | Departamento_residencia | Residence department label | https://www.ins.gov.co/Direcciones/Vigilancia/Lineamientosydocumentos/3.%20Diccionario_de_datos_Sivigila%202018_2020.pdf | INS SIVIGILA dictionary (2018–2020) | Confirmed in data | Used as secondary consistency signal for residence scope. |
| Epidemiological | Municipio_residencia | Residence municipality label | https://www.ins.gov.co/Direcciones/Vigilancia/Lineamientosydocumentos/3.%20Diccionario_de_datos_Sivigila%202018_2020.pdf | INS SIVIGILA dictionary (2018–2020) | Confirmed in data | Used as descriptive metadata in municipality-level outputs. |
| Epidemiological | CONSECUTIVE | Record identifier candidate | https://www.ins.gov.co/Direcciones/Vigilancia/Lineamientosydocumentos/3.%20Diccionario_de_datos_Sivigila%202018_2020.pdf | INS SIVIGILA dictionary (2018–2020) | Confirmed in data + Pending semantics | Cross-file overlap is non-zero but interpretation is unresolved. |
| Climate | date | Municipality-day date | https://github.com/j-mauro-r/microproyecto-tema3/blob/main/data/docs/diccionario_datos_ambiente_dengue.csv | External reference repo, observed at commit view c0b5b13 | Confirmed in data + Documented in source | In-scope climate window in notebook: 2007-01-01 to 2025-12-31. |
| Climate | year | Calendar year | https://github.com/j-mauro-r/microproyecto-tema3/blob/main/data/docs/diccionario_datos_ambiente_dengue.csv | External reference repo, observed at commit view c0b5b13 | Confirmed in data + Documented in source | Treated as descriptive field in this increment. |
| Climate | month | Calendar month | https://github.com/j-mauro-r/microproyecto-tema3/blob/main/data/docs/diccionario_datos_ambiente_dengue.csv | External reference repo, observed at commit view c0b5b13 | Confirmed in data + Documented in source | No temporal aggregation decisions approved here. |
| Climate | dpto_ccdgo | Department code | https://github.com/j-mauro-r/microproyecto-tema3/blob/main/data/docs/diccionario_datos_ambiente_dengue.csv | External reference repo, observed at commit view c0b5b13 | Confirmed in data + Documented in source | Used for in-scope department filtering checks. |
| Climate | mpio_cdpmp | Municipality code (DANE-like) | https://github.com/j-mauro-r/microproyecto-tema3/blob/main/data/docs/diccionario_datos_ambiente_dengue.csv | External reference repo, observed at commit view c0b5b13 | Confirmed in data + Documented in source | Used as climate-side municipality key for scope checks. |
| Climate | rain_mm_day | Daily rainfall (mm/day) | https://github.com/j-mauro-r/microproyecto-tema3/blob/main/data/docs/diccionario_datos_ambiente_dengue.csv | External reference repo, observed at commit view c0b5b13 | Confirmed in data + Documented in source | Missingness in notebook in-scope subset: 0; zero-value proportion: 44.6858%. |
| Climate | temp_mean_c | Daily mean air temperature (deg C) | https://github.com/j-mauro-r/microproyecto-tema3/blob/main/data/docs/diccionario_datos_ambiente_dengue.csv | External reference repo, observed at commit view c0b5b13 | Confirmed in data + Documented in source | Missingness in notebook in-scope subset: 0. |
| Climate | dewpoint_mean_c | Daily dew point temperature (deg C) | https://github.com/j-mauro-r/microproyecto-tema3/blob/main/data/docs/diccionario_datos_ambiente_dengue.csv | External reference repo, observed at commit view c0b5b13 | Confirmed in data + Documented in source | Missingness in notebook in-scope subset: 0. |
| Climate | soil_water_l1_mean | Layer-1 soil water indicator | https://github.com/j-mauro-r/microproyecto-tema3/blob/main/data/docs/diccionario_datos_ambiente_dengue.csv | External reference repo, observed at commit view c0b5b13 | Confirmed in data + Documented in source | Unit/processing assumptions remain external-reference dependent. |
| Climate | surface_runoff_mm_day | Daily surface runoff (mm/day) | https://github.com/j-mauro-r/microproyecto-tema3/blob/main/data/docs/diccionario_datos_ambiente_dengue.csv | External reference repo, observed at commit view c0b5b13 | Confirmed in data + Documented in source | Missingness in notebook in-scope subset: 0; zero-value proportion: 0.5239%. |
| Climate | total_evaporation_mm_day_ecmwf | Daily evaporation proxy (mm/day, ECMWF convention) | https://github.com/j-mauro-r/microproyecto-tema3/blob/main/data/docs/gee-query-dengue.py | External reference repo, observed at commit view c0b5b13 | Documented in source + Confirmed in data (field presence) | Sign convention documented externally; in-repo provenance not yet proven. |
| Climate | wind_u_mean_ms | Zonal wind component (m/s) | https://github.com/j-mauro-r/microproyecto-tema3/blob/main/data/docs/diccionario_datos_ambiente_dengue.csv | External reference repo, observed at commit view c0b5b13 | Confirmed in data + Documented in source | Missingness in notebook in-scope subset: 0. |
| Climate | wind_v_mean_ms | Meridional wind component (m/s) | https://github.com/j-mauro-r/microproyecto-tema3/blob/main/data/docs/diccionario_datos_ambiente_dengue.csv | External reference repo, observed at commit view c0b5b13 | Confirmed in data + Documented in source | Missingness in notebook in-scope subset: 0. |
| Climate | solar_radiation_mj_m2_day | Daily solar radiation (MJ/m2/day) | https://github.com/j-mauro-r/microproyecto-tema3/blob/main/data/docs/diccionario_datos_ambiente_dengue.csv | External reference repo, observed at commit view c0b5b13 | Confirmed in data + Documented in source | Missingness in notebook in-scope subset: 0. |

## Traceability to notebook evidence

Official Stage 2 bounded EDA notebook:
- `notebooks/01_stage2_residence_onset_eda.ipynb`

This notebook provides:
- Header correspondence checks for required fields.
- In-scope residence filtering diagnostics (Tolima/Meta).
- `INI_SIN` quality and delay diagnostics.
- Climate coverage and missingness diagnostics for validated residence municipalities.

Cell-level traceability in the current corrected run:
- Code cell 6: residence filtering controls and synthetic tests.
- Code cells 7 and 8: `INI_SIN` quality and temporal diagnostics.
- Code cells 9 and 10: climate coverage, missing-vs-zero diagnostics, and municipality gap patterns.
- Code cell 11: evidence states and key metrics table used for documentation reconciliation.

## Pending for full mapping completion

- Complete 69-column official mapping against citable INS clauses and period applicability notes.
- Resolve historical applicability of references outside 2018–2020 / 2019 windows.
- Confirm or reject provenance linkage between `data/raw/google_earth_engine.csv` and external extraction workflow artifacts.
