# Experimental EDA archive — DEPRECATED

Mauricio retired **all experimental EDA** on 2026-10-19 after using it to understand and refine the supplied data. This archive preserves the experiments; its reports, saved notebook outputs, exploratory associations, candidate variables and pending rerun instructions are historical. They do not establish current feature selection, target validation, accepted model performance or Stage 2/G2 closure.

The [decision register](../../product/traking-concluciones.md) is the active Stage 2 scientific decision document. Approved decisions remain in force; experimental choices are not promoted to approved rules. The [master plan](../../roadmap/master-plan.md) retains stage-level ownership; governance, Stage 1 requirements and scientific standards remain active.

## Restored active reference

The [canonical field dictionary](../../product/stage-2/DATA-01-Priority%20Field%20Matrix.md) was explicitly restored by Mauricio. It remains the sole reference for all 69 fields under DEC-032/033; field documentation is not retired EDA interpretation. Its former archive path is now a compatibility pointer. The six insufficient operational definitions remain explicit.

## Retired artifacts

| Original repository path | Archived artifact |
|---|---|
| `docs/product/stage-2/DATA-01-2013-date-inconsistency-investigation.md` | [DATA-01-2013-date-inconsistency-investigation.md](stage-2/DATA-01-2013-date-inconsistency-investigation.md) |
| `docs/product/stage-2/DATA-01-Initial Recognition Report.md` | [DATA-01-Initial Recognition Report.md](stage-2/DATA-01-Initial%20Recognition%20Report.md) |
| `docs/product/stage-2/DATA-01-Source Provenance.md` | [DATA-01-Source Provenance.md](stage-2/DATA-01-Source%20Provenance.md) |
| `docs/product/stage-2/DATA-02-monthly-sensitivity-associations.md` | [DATA-02-monthly-sensitivity-associations.md](stage-2/DATA-02-monthly-sensitivity-associations.md) |
| `docs/product/stage-2/DATA-03-panel-review.md` | [DATA-03-panel-review.md](stage-2/DATA-03-panel-review.md) |
| `docs/product/stage-2/DATA-04-retrospective-use-rules.md` | [DATA-04-retrospective-use-rules.md](stage-2/DATA-04-retrospective-use-rules.md) |
| `docs/product/stage-2/nota-metodologica.md` | [nota-metodologica.md](stage-2/nota-metodologica.md) |
| `notebooks/01_stage2_residence_onset_eda.ipynb` | [01_stage2_residence_onset_eda.ipynb](notebooks/01_stage2_residence_onset_eda.ipynb) |
| `notebooks/02_stage2_monthly_sensitivity_associations.ipynb` | [02_stage2_monthly_sensitivity_associations.ipynb](notebooks/02_stage2_monthly_sensitivity_associations.ipynb) |

The [path and SHA-256 manifest](manifest.json) records both identities and the matrix restoration, preserving the original retirement hash separately. The two notebooks were moved byte-for-byte without execution. Reports preserve their original body apart from this archive's retirement banners and relocated relative Markdown links. Plain-text paths, original "official/current" wording, dates and commands inside historical bodies describe the old layout and are not instructions to recreate it. Git history retains the prior report bytes; local PLAN_012 also holds the exact pre-move copies for verification. To recover an artifact, consult the manifest and restore a copy deliberately to the recorded original path without overwriting later work.

## Related historical execution evidence

PLAN_005 and its sensitivity/association derivatives, the initial recognition EDA, municipal diagnostics, the date investigation, PLAN_006 panel experiments and PLAN_011's derived analytical comparisons are historical. Local DWP paths, contracts, journals and recorded gates stay in place; their original completion records are not rewritten. No rerun of these retired studies is required by this cleanup. Any future EDA needs a new bounded objective and its own acceptance evidence.

The three scripts `scripts/stage2_monthly_sensitivity_analysis.py`, `scripts/stage2_panel_review.py` and `scripts/stage2_derived_recompute_reconciliation.py` remain at their original paths, explicitly deprecated, because existing tests and historical audit helpers import them. Their logic is unchanged. Existing synthetic regressions and artifact consistency tests remain safeguards; a passing test does not make the retired interpretation active again.

## Evidence and data retained

Raw sources, reference files, climate backups and all `data/interim/` outputs remain untouched at their original locations. PLAN_008/009/010 climate audit/recovery/incorporation evidence and PLAN_011 manifest reconciliation remain available as data-integrity provenance. The Earth Engine recovery script remains in `notebooks/`; it supports the data repair rather than the retired EDA. `scripts/stage2_manifest_traceability.py` and `scripts/january_2020_climate_incorporation.py`, with their tests, remain active data-integrity tools. Retiring the EDA does not undo the January repair or erase known manifest-reconstruction limits.
