# SAT-Dengue V2 — Source Provenance Register

Revision: 2026-10-16. Branch: `Stage2/Data-Understanding`. Status: documentary traceability established for current files; upstream extraction lineage and G2 remain pending.

## 1. What this register establishes

Current bytes, headers and notebook-execution metadata are identified without patient-record correction or raw-data mutation. A file hash identifies a local artifact; it does not establish source authenticity, extraction correctness or the exact bytes used by a past run unless recorded at that run.

| Artifact owner | Reference |
|---|---|
| Field meanings and export aliases | [Canonical priority matrix](DATA-01-Priority%20Field%20Matrix.md) |
| Saved numerical findings | [Recognition report](DATA-01-Initial%20Recognition%20Report.md) |
| Approved scientific decisions | [Methodological note](nota-metodologica.md) |
| Executable evidence | [Official notebook](../../../notebooks/01_stage2_residence_onset_eda.ipynb) |

## 2. Current file identities

Headers, sizes, modification times and SHA-256 were inspected on 2026-10-16. No records were profiled or changed. Modification times below are local filesystem metadata in America/Bogota, not source extraction/publication dates.

| Repository-relative artifact | Size (bytes) | Local modification time | SHA-256 observed at consolidation |
|---|---:|---|---|
| `data/raw/dengue.csv` | 875,694,283 | `2026-10-15T18:17:22.588385-05:00` | `58d277cfef7a60c28d488eefe4e7a1a7bf0f7b0df3dd88245971cd7b3d32c84b` |
| `data/raw/dengue_grave.csv` | 24,537,734 | `2026-10-15T18:17:22.133687-05:00` | `3d60e96ccbedc35a19a8f5f54be8d786aa599813259c914f131522bf17dd1d70` |
| `data/raw/google_earth_engine.csv` | 1,714,041,810 | `2026-10-15T18:17:23.483286-05:00` | `4287197dc1ce14fc442c3717ccc665e87970d1893d2b7d2c06e247647011f634` |
| `notebooks/01_stage2_residence_onset_eda.ipynb` | 880,916 | `2026-10-16T14:07:06.102713-05:00` | `1e19102183b79bb0713b75f4fd32d05be5f32a6c241f9f6c0f4842ae1927ff5a` |

Repository HEAD at inspection: `8e90d554bd0c0f29ecbbcad78caf723427eb3e94`. The notebook is tracked at that commit; raw data are ignored by Git. The epidemiological headers have 69 columns each and match in order; the climate header has 18. Header-only inspection confirms `INI_SIN`, `COD_DPTO_R` and `COD_MUN_R` in both epidemiological files. No row-count claim is derived from this metadata operation.

## 3. Notebook evidence snapshots

- Analysis cutoff: **2026-10-15**, fixed in the notebook. Documentation review: **2026-10-16**.
- Saved execution start: `2026-10-15T21:00:51.697347-05:00`; timezone `America/Bogota`.
- Saved package table: Python 3.12.11, pandas 3.0.6, NumPy 2.5.4, Matplotlib 3.11.2, seaborn 0.13.2. This is recorded environment evidence, not a newly created dependency lockfile.
- The saved input-size and local-modification metadata agree with the current identities to the displayed precision. Original execution did **not** record SHA-256, so current hashes cannot retroactively prove byte-for-byte run input identity.
- Notebook source and outputs were intentionally extended and re-executed in this increment to add DIVIPOLA-based territorial coverage and temporal continuity diagnostics.

Execution references for this increment are tracked by exported aggregate artifacts under `data/interim/stage2_divipola_validation/` and by semantic notebook section titles, not by ephemeral execution counters.

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

## 5. Consolidation record and unresolved boundaries

Reviewed: both prior matrices, recognition report, brief, methodological note, index, saved notebook, governance/data/scientific rules and the references above. Current headers and identities were added as metadata evidence only.

Updated: the indexed DATA-01 matrix, recognition report, brief, methodological note and documentation index. Added: this provenance register. Removed after merging: `priority-field-matrix.md`, whose unique alias, identifier, classification, unit and evidence caveats are retained in the canonical matrix; its literature context already lives in the methodological note. Git history preserves both originals.

The current snapshot is traceable but upstream extraction is not fully established. This limitation is documented, not silently resolved. No data remediation, new EDA, model decision, G2 approval, commit or publication is part of this change.

## 6. Consolidation validation — 2026-10-16

| Control | State | Evidence / limit |
|---|---|---|
| Branch and change scope | PASS | `Stage2/Data-Understanding`; five existing documents updated, this register added and one duplicate removed. No staged changes or publication. |
| Raw files preserved and notebook traceability maintained | PASS | Raw-data SHA-256 values are unchanged; notebook was intentionally updated and re-executed, and its current identity is recorded in section 2. |
| Lint, format, types and unit test | PASS | Ruff, mypy and the existing repository bootstrap test passed under the local `.venv`. This verifies repository checks, not scientific data quality. |
| Documentation links and diff whitespace | FAIL | `python3 scripts/check_markdown_links.py` currently fails because the tracked path `docs/product/stage-2/priority-field-matrix.md` is absent in the working tree; this is tracked as a known branch-state issue. |
| Repository DWP conformance | PASS | `conformance.sh --repo-only`: 17 checks passed. |
| Full DWP conformance including old plans | FAIL | Existing `PLAN_stage2_data_understanding_initial_recognition` mixes Final Review with legacy discovery/report tasks. Plan records were outside this documentation change and were not modified. Two additional advisory findings concern finalization evidence and task links. |
| Policy and secret scans | PASS for project changes | No prohibited runtime/config references or secret patterns in modified/new documents. The full-workspace secret-pattern scan matched embedded font data in the ignored Pillow dependency; it is not an introduced project credential. |

The full DWP gate is not reported as passing. Resolving the earlier plan's lifecycle is separate from this consolidation and remains pending before claiming all repository gates are green.

## 7. DIVIPOLA increment provenance snapshot (execution date 2026-10-16)

This section records metadata emitted by the executed notebook increment that performed DIVIPOLA-based territorial coverage and temporal continuity diagnostics.

### 7.1 Catalog identity captured during execution

Metadata source:
- `data/interim/stage2_divipola_validation/divipola_catalog_metadata.json`

| Catalog artifact | Local relative path | SHA-256 | Size (bytes) | Local modified timestamp | Declared conteo | Parsed rows | estado |
|---|---|---|---:|---|---:|---:|---|
| Departments catalog payload | `data/sources/Divipola-departamentos.md` | `6f93361c96a860c941a657fcb938c7698df3cfbe8eb04396fdf076209498e959` | 2,185 | `2026-10-16T12:13:19.757730007-05:00` | n/a | 33 | `true` |
| Municipalities catalog payload | `data/sources/Divipola-municipios.md` | `72eabcea0ff26370d23b9688e8d8f2246946cc815c040ccf1a6966b37a1de9f3` | 209,867 | `2026-10-16T12:12:20.122043610-05:00` | 1,122 | 1,122 | `true` |

Execution metadata captured in the same artifact:
- generated_at: `2026-10-16T14:09:01.665826-05:00`
- execution timezone: `America/Bogota`

### 7.2 Executed territorial and continuity artifact inventory

The notebook execution exported the following reproducible aggregate artifacts:

- `data/interim/stage2_divipola_validation/divipola_catalog_validation.csv`
- `data/interim/stage2_divipola_validation/divipola_department_municipality_counts.csv`
- `data/interim/stage2_divipola_validation/territorial_coverage_by_code.csv`
- `data/interim/stage2_divipola_validation/territorial_exceptions.csv`
- `data/interim/stage2_divipola_validation/territorial_summary_by_dataset.csv`
- `data/interim/stage2_divipola_validation/temporal_continuity_epi.csv`
- `data/interim/stage2_divipola_validation/temporal_continuity_climate.csv`
- `data/interim/stage2_divipola_validation/temporal_continuity_summary.csv`
- `data/interim/stage2_divipola_validation/coverage_controls_status.csv`

These outputs are aggregate evidence. They do not imply data correction, municipality eligibility approval, Stage 2 closure, or G2 approval.

### 7.3 Explicit unknowns retained as pending

The executed metadata explicitly preserves unresolved external catalog lineage fields:
- `official_dane_url = pending`
- `download_date = pending`
- `dane_version = pending`

Therefore, this increment provides local identity/consistency traceability for supplied files, but it does not establish official external publication provenance. The associated pending decision items remain in the recognition report's dedicated pending decision section.
