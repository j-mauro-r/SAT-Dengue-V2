# SAT-Dengue V2 — Source Provenance Register

Revision: 2026-10-16. Branch: `Stage2/Data-Understanding`. Status: documentary traceability established for current files; upstream extraction lineage and G2 remain pending.

## 1. What this register establishes

Current bytes, headers and notebook-execution metadata are identified without patient-record correction or raw-data mutation. A file hash identifies a local artifact; it does not establish source authenticity, extraction correctness or the exact bytes used by a past run unless recorded at that run.

| Artifact owner | Reference |
|---|---|
| Field meanings and export aliases | [Canonical priority matrix](DATA-01-Priority%20Field%20Matrix.md) |
| Saved numerical findings | [Recognition report](DATA-01-Initial%20Recognition%20Report.md) |
| Bounded anomaly comparison evidence | [Date inconsistency investigation](DATA-01-2013-date-inconsistency-investigation.md) |
| Approved scientific decisions | [Methodological note](nota-metodologica.md) |
| Executable evidence | [Official notebook](../../../notebooks/01_stage2_residence_onset_eda.ipynb) |

## 2. Current file identities

Headers, sizes, modification times and SHA-256 were inspected on 2026-10-16. The identity operation did not change records; existing diagnostics were subsequently rerun read-only. Modification times below are local filesystem metadata in America/Bogota, not source extraction/publication dates.

| Repository-relative artifact | Size (bytes) | Local modification time | SHA-256 observed at consolidation |
|---|---:|---|---|
| `data/raw/dengue.csv` | 875,694,283 | `2026-10-15T18:17:22.588385-05:00` | `58d277cfef7a60c28d488eefe4e7a1a7bf0f7b0df3dd88245971cd7b3d32c84b` |
| `data/raw/dengue_grave.csv` | 24,537,734 | `2026-10-15T18:17:22.133687-05:00` | `3d60e96ccbedc35a19a8f5f54be8d786aa599813259c914f131522bf17dd1d70` |
| `data/raw/google_earth_engine.csv` | 1,714,041,810 | `2026-10-15T18:17:23.483286-05:00` | `4287197dc1ce14fc442c3717ccc665e87970d1893d2b7d2c06e247647011f634` |
| `notebooks/01_stage2_residence_onset_eda.ipynb` | 977,372 | `2026-10-16T16:06:17.804572-05:00` | `f1b1f16c8d2b59b93f33775ae7120b132f7469388420b7eebc27843bc1e37eed` |

Initial inspection HEAD: `8e90d554bd0c0f29ecbbcad78caf723427eb3e94`. HEAD at final verification: `29e036ee91d5cffd14d1d8c484e39cfa4c244c20`; it advanced during the audit outside this agent's actions. The audit used a pre-edit working-tree snapshot and made no commits. The notebook path is tracked, but the current working-tree notebook includes later uncommitted changes; raw data are ignored by Git. The epidemiological headers have 69 columns each and match in order; the climate header has 18. Header-only inspection confirms `INI_SIN`, `COD_DPTO_R` and `COD_MUN_R` in both epidemiological files. No row-count claim is derived from this metadata operation.

## 3. Current notebook execution

The analytical cutoff is fixed at **2026-10-15**; audit date is **2026-10-16**. The current execution start and environment are saved in the notebook's parameters/environment outputs. Package versions are evidence of this local run; a dedicated EDA dependency lock is not yet provided by the project. Do not confuse local execution time, extraction time and analytical cutoff. The original 2026-10-15 run did not capture input hashes; later hashes cannot retroactively prove its exact input bytes.

The notebook now loads and validates DIVIPOLA before climate coverage checks. It records supplied metadata, compares hash-bound snapshots, and exports aggregate evidence. The [recognition report](DATA-01-Initial%20Recognition%20Report.md) owns findings/artifact descriptions; [validation operations](../../operations/validation-and-evidence.md) owns current audit outcomes.

## 4. External source register

### Epidemiological files

The repository data policy describes a Kaggle/local-workspace strategy and the project identifies SIVIGILA/INS as the epidemiological origin. Neither establishes the exact upstream object/version of these CSVs. The old microproject README refers to differently named, smaller inputs; that history is not the current extraction lineage.

Pending for each file: exact dataset URL/owner/version, retrieval date, source cutoff, export/transformation recipe and changes applied before delivery. Record these when evidence is available; do not infer them from filenames or modification times.

### Official definitions S and D

- **S:** [INS dictionary 2018–2020](https://www.ins.gov.co/Direcciones/Vigilancia/Lineamientosydocumentos/3.%20Diccionario_de_datos_Sivigila%202018_2020.pdf), reviewed in readable form on 2026-10-16. Basic-data structure starts at PDF viewer page 29; residence/onset fields are on page 34, and dengue-specific structure starts on page 98.
- **D:** [INS dengue form/instructions, 2019](https://www.ins.gov.co/BibliotecaDigital/210_220_580_Dengue_2019.pdf), reviewed on 2026-10-16; section 7.1 supplies the clinical classification context.

These are version-bounded definitions, not a lineage manifest for the supplied exports. Their URLs are public but no immutable PDF snapshot/hash was captured here. Historical applicability and export aliases remain explicit limitations.

### Environmental references E1–E3

References reviewed at immutable repository commit `b63257c17f3064a0dcda6fcf4e7028fae4a43078`:

| ID | Pinned reference | Git blob SHA |
|---|---|---|
| E1 | [18-field dictionary](https://github.com/j-mauro-r/microproyecto-tema3/blob/b63257c17f3064a0dcda6fcf4e7028fae4a43078/data/docs/diccionario_datos_ambiente_dengue.csv) | `39824406eed78e8dcd30dc75a39b2763484d2233` |
| E2 | [Extraction workflow](https://github.com/j-mauro-r/microproyecto-tema3/blob/b63257c17f3064a0dcda6fcf4e7028fae4a43078/data/docs/README.MD) | `18f4a989a4bbdb56e915cd3ed63bbbee3cf7b2bf` |
| E3 | [Extraction script](https://github.com/j-mauro-r/microproyecto-tema3/blob/b63257c17f3064a0dcda6fcf4e7028fae4a43078/data/docs/gee-query-dengue.py) | `215c269effc045edc83a7624ebfd39a661e7e72f` |

E3 names CHIRPS Daily and ERA5-Land Daily Aggregated products. Its configured years are 2018–2024, while saved climate output coverage is 2007–2025 and E2 shows export examples starting in 2007. E2 and E3 also differ on asset spelling (`municipio` versus `municipios`). These differences may reflect different runs/versions; they do not prove an error or establish the current run.

Pending: actual generating commit, year/month job manifest, asset version, source-product versions and export/concatenation completeness for `google_earth_engine.csv`. January 2020 is absent in saved diagnostics; the cause and recovery policy remain unverified.

### Private project references

The methodological note identifies `Sesion_1_con_Experto_Notas.docx`, `Formato-propuesta_Proyecto-de-grado-Mauricio.pdf` and `Reporte_Entrega3_final-2.docx` by name and relevant section. They are external, private references; no absolute personal paths, broken local links or copies are required in this repository. The synchronized project `sources/` material remains read-only.

## 5. DIVIPOLA source metadata

Canonical machine-readable record: `data/sources/divipola-provenance.json`, bound to both supplied snapshot SHA-256 values. The original JSON payloads are unchanged despite their `.md` extension.

- Department service: [DANE departamentos](https://geoportal.dane.gov.co/laboratorio/serviciosjson/gdivipola/servicios/departamentos.php).
- Municipality service: [DANE municipios](https://geoportal.dane.gov.co/laboratorio/serviciosjson/gdivipola/servicios/municipios.php).
- Download date **2026-10-16**; reported version date **2026-09-30**.
- Attribution: URLs and dates supplied by Mauricio in the project conversation. Recorded provenance is complete for this supplied snapshot; publication/version authenticity has not been independently verified by this audit.
- Historical applicability remains UNVERIFIED: this snapshot is not a municipal-boundary change log for the full study period.

| Supplied snapshot | SHA-256 |
|---|---|
| `Divipola-departamentos.md` | `6f93361c96a860c941a657fcb938c7698df3cfbe8eb04396fdf076209498e959` |
| `Divipola-municipios.md` | `72eabcea0ff26370d23b9688e8d8f2246946cc815c040ccf1a6966b37a1de9f3` |

The executed `divipola_catalog_metadata.json` carries the same source record plus execution metadata and catalogue checks. Source metadata recorded successfully is separate from a perfect territorial-quality result; unresolved codes/absences remain visible in the report.

## 6. Next source comparison

Mauricio is obtaining the original 2013 SIVIGILA source. Its URL, retrieval date, version and hash must be recorded when supplied. No comparison has occurred and no date-correction policy is approved. Original current CSV snapshots remain unchanged.
