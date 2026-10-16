# SAT-Dengue V2 — Stage 2 Data Understanding Brief

Revision: 2026-10-16. Status: initial recognition and bounded EDA completed for review; documentary consolidation completed; Stage 2 open and G2 not approved.

## 1. Objective

Understand the existing dengue, severe-dengue and climate inputs through inspectable evidence before approving preparation, target construction or modeling. This brief defines scope and review boundaries; it is not a full-stage execution plan.

## 2. Approved analytical scope

- Epidemiological attribution: **municipality of residence** in Tolima and Meta.
- Case-period reference: **symptom onset**, using the confirmed `INI_SIN` header.
- Product outputs: municipality-level risk at T+1/T+2.
- Dengue and severe-dengue files remain separate until their case relationship is established.
- No automatic substitution of missing/invalid `INI_SIN` by `FEC_NOT` is approved.
- Geographic scope does not guarantee every municipality a valid prediction; eligibility remains pending.

## 3. Inputs and reference ownership

Inputs are `data/raw/dengue.csv`, `data/raw/dengue_grave.csv` and `data/raw/google_earth_engine.csv`. Raw data remain read-only and excluded from Git under the [data policy](../../data/data-policy.md).

| Artifact | Responsibility |
|---|---|
| [Recognition report](DATA-01-Initial%20Recognition%20Report.md) | Historical evidence and saved corrected EDA findings |
| [Canonical priority matrix](DATA-01-Priority%20Field%20Matrix.md) | Single field-definition reference and mapping status |
| [Source provenance](DATA-01-Source%20Provenance.md) | Input fingerprints, saved-run metadata, reference versions and lineage limits |
| [Methodological note](nota-metodologica.md) | Approved scientific choices, literature context and open decisions |
| [Official notebook](../../../notebooks/01_stage2_residence_onset_eda.ipynb) | Executable evidence for the bounded residence/onset EDA |

The duplicate matrix was consolidated into the canonical DATA-01 file; no parallel field dictionary is maintained. Other original source documents remain read-only references.

## 4. Completed increments

1. Initial recognition: structure, coverage signals and unresolved semantics, without assuming inputs are clean.
2. Bounded EDA: residence filters, onset interpretability/consistency, municipal-period coverage and climate missing-versus-zero/gap checks. This explicitly superseded the initial brief's restriction against notebooks and diagnostic aggregation, only for that authorized increment.
3. Current documentary consolidation: merged matrices, reconciled decisions, checked headers only, and recorded file/reference identities. No EDA code, metrics or original data changed.

The repository's engineering, scientific, security and validation standards continue to apply. Prior notebook installation/execution does not authorize arbitrary new analysis or infrastructure.

## 5. Remaining interpretation and data-quality work

- Official municipal inventory and coverage eligibility.
- Required-field aliases and historical dictionary applicability.
- Case inclusion, adjustments, duplicate/identifier semantics and dengue/severe-dengue relationship.
- Missing-onset policy, 2013 temporal alerts and January 2020 climate gap.
- Upstream file/export lineage and climate extraction-run evidence.
- Channel, target and historical information-availability rules.

These are review topics, not authorization to resolve them automatically during this consolidation. Full interpretation of every unused epidemiological column is not a prerequisite for the next bounded step.

## 6. Restrictions and review gate

Do not overwrite, clean, rename or delete raw inputs. Do not expose patient-level records. Do not silently impute missing data, union case streams, turn absent months into confirmed zero cases, or choose a training architecture.

A new bounded request is required before deeper analysis, data preparation, endemic-channel construction, target definition or modeling. G2 is approved only when the sources, temporal rules, target and leakage constraints have evidence and explicit human approval under the [master plan](../../roadmap/master-plan.md).
