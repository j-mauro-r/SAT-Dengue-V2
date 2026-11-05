# EXP-DELTA02 — recent neighboring epidemiological activity

**Execution: `COMPLETED_WITH_LIMITATIONS`. Spatial feasibility and scientific
disposition: `NOT_EVALUABLE`.** The official national municipal archives were
retrieved and their target-related topology computed. Nine positive-boundary
relations differ across vintages, affecting six of the 76 target municipalities.
Their historical correspondence remains unresolved. Stage 1 therefore closes
this experiment before feature construction or training, as explicitly required
by Mauricio's request. This is not evidence against the predictive hypothesis.

The [frozen protocol](PROTOCOL.md), [quantitative results](RESULTS.md),
[conclusions](CONCLUSIONS.md) and [provenance](PROVENANCE.json) own this bounded
delivery. G5 remains `NOT_APPROVED`; `champion: not_selected`.

## Authority, preparation and prior evidence

Mauricio authorized both spatial admission and conditional T+1 fitting, including
a stop at `NOT_EVALUABLE` without a second approval between stages. PR
[#75](https://github.com/j-mauro-r/SAT-Dengue-V2/pull/75) was verified merged;
`origin/main` was fetched, and `experiment/EXP-DELTA02` was created from its clean
`bfc10b5` head. No dependency branch or duplicate EDA changes were needed.
The direct bounded implementation uses a frozen scientific protocol; no DWP
plan, independent EDA, production pipeline or framework was created.

Reviewed antecedents: [EDA-EXP01](../EDA-EXP01/CONCLUSIONS.md) found shared errors,
sparse municipal support and insufficient climate evidence; [EDA-EXP02](../EDA-EXP02/PHASE_B_CONCLUSIONS.md)
left O1 geographically unadmitted; [EXP03](../EXP03_feature_ablation/CONCLUSIONS.md)
warned against equating discrimination gains with stable decision utility;
[BETA01](../EXP-BETA01/CONCLUSIONS.md) fixed G0's configuration and temporal roles;
[BETA01 V2](../EXP-BETA01-V2/CONCLUSIONS.md) did not support national expansion;
the [benchmark](../benchmark/CONCLUSIONS.md) found no pooled T+1 academic pass;
[DELTA01](../EXP-DELTA01/CONCLUSIONS.md) found two mandatory policy cells infeasible.
These are context, not rerun experiments or independent validation.

## Sources and methodology

The [source specification](sources.json) pins national, regional, benchmark and
EDA geography-admission publications by exact manifest digest. All their direct
payloads are verified before and after the audit. Canonical source semantics
remain owned by the [national table contract](../../../data/canonical-national-table.md).
No private municipal health rows enter Git.

Geography comes from DANE's [official download catalogue](https://www.dane.gov.co/files/geoportal-provisional/):
[MGN 2005](https://www.dane.gov.co/files/geoportal-provisional/SHP_MGN2005_COLOMBIA.zip),
[MGN 2018](https://www.dane.gov.co/files/geoportal-provisional/SHP_MGN2018_COLOMBIA.zip)
and [MGN 2021](https://www.dane.gov.co/files/geoportal-provisional/SHP_MGN2021_COLOMBIA.zip).
Access date: 2026-11-03. Only municipal SHP/SHX/DBF/PRJ/CPG/XML members were
extracted through HTTP byte ranges, with ZIP CRC and SHA-256 checks. Other levels
in the multi-gigabyte archives were not downloaded. The source publication
retains archive URLs, sizes, member names, retrieval code and byte identities.

The 2005/2018 archives use WGS84 geographic coordinates; 2021 uses MAGNA
geographic coordinates. Each graph is calculated within its own native CRS.
Only topological membership is compared across vintages; lengths/areas remain
native angular audit quantities, not distances or areas in physical units.
No cross-datum coordinate intersection, snapping, buffering, simplification or
geometry repair occurs. The 2018 archive is distinct from the integrated-2018
attribute service inspected by the EDA; its archival identity is not inferred
from that service's version label.

For every target polygon, the spatial index screens all national polygons.
An exact boundary intersection of positive length defines a neighbor; point-only
contacts and the target itself are excluded. Compare target-related undirected
edge sets across the three vintages, retaining all outside-region neighbors.
Check code uniqueness, polygon validity, overlaps and calendar/count coverage.
The union of alternative graphs is only a coverage diagnostic; it is never an
admitted graph or a dengue feature. No source contains a resolved, dated
crosswalk for the observed graph differences and canonical historical units.

Earlier REST exploration is retained as provenance: MGN 2012's national query
returned an ArcGIS error; 2017/2020/2024 national queries returned attributes
without geometry. The successful archives supersede those retrieval failures
as the basis of the scientific stop. Additional archives may exist; the finding
does not assert universal geographic-data unavailability.

## Reproduction and controlled publications

The maintained [audit script](../../../../scripts/audit_exp_delta02_feasibility.py)
has no fitting, calibration, threshold, prediction or spatial-feature builder.
It reproduces this observed stop condition; it is not a generic admission engine.
A missing or changed input raises an execution error, rather than silently
becoming scientific `NOT_EVALUABLE`. The conditional predictor was not implemented.

Use the project `.venv` with the exact private publications in `sources.json`.
Install the two audit-only packages under ignored repository-local `tmp/`:

```bash
.venv/bin/python -m pip install --no-deps --target tmp/exp-delta02/vendor shapely==2.1.2 pyshp==2.3.1
PYTHONPATH=tmp/exp-delta02/vendor .venv/bin/python scripts/audit_exp_delta02_feasibility.py --self-check
PYTHONPATH=tmp/exp-delta02/vendor .venv/bin/python scripts/audit_exp_delta02_feasibility.py --publish
```

PyShp reads official municipal shapefiles; Shapely/GEOS tests valid polygons and
exact shared edges. This small, isolated audit dependency set does not alter
project/model dependencies. Runtime versions are in the result provenance.
The script uses existing repository identity checks and atomic immutable
publication, with identical-byte reuse and corruption/overwrite refusal.
Run it from the repository root; there is no implicit latest-source discovery.

Sources: `data/processed/exp_delta02/sources/9d6ad24d1d1f3bb534deb8a44de446fb22859d29f6e8ce355980932be809c96b/`.
Final result identity and manifest digest are in [PROVENANCE.json](PROVENANCE.json).
Its six payloads are the topology/coverage summary, private municipal relation
audit, changed-edge table, original T+1 baseline aggregates, provenance and manifest.
No training files or candidate predictions are generated. Reproduction uses the
preserved source bundle; rebuilding it requires the exact archived member hashes,
not substituting a later response at the same URL. A data-free checkout can run
generated source-fence tests but cannot reproduce private canonical evidence.

## Validation and handoff

The [testing guide](../../../TESTING_GUIDE.md) owns proportional checks. Validate
geographic edge/point/disjoint/invalid cases; all target and external-code joins;
source tampering refusal; deterministic recomputation; comparator reconciliation;
source preservation; scoped Ruff/format/mypy; Markdown links; changed-file
security and directory boundaries; and repository-only conformance. Scientific
`NOT_EVALUABLE` is the expected result, not a failed test.

Future-feature prefix invariance, fitted temporal roles, candidate cohort/label
pairing, candidate A/B/C and training reproduction are **BLOCKED / not executed**
by geography admission. They are not reported as passes. No full historical
suite, notebook replay or dashboard check is required. CI owns integral checks;
independent scientific review and Mauricio's merge decision remain separate.
Exact local results and PR handoff are recorded in [RESULTS.md](RESULTS.md).
