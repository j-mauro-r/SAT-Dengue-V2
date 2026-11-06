# SAT-Dengue V2 Master Plan

This document is the single durable master plan for the project. It defines all Stages 0–10, their goals, dependencies, gates, and stage-level progress. Runtime task state remains local.

## Planning and Execution Policy

- A project-wide DWP Full Master Plan is not required and will not be created.
- DWP Full plans per Stage are deprecated and will not be created.
- Execute incrementally through bounded user stories (HUs), each with scope, acceptance criteria, validation, and evidence. Do not execute an entire Stage or the project in a single prompt.
- Use DWP only when a concrete HU/task warrants an execution plan because of complexity, risk, dependencies, or work across sessions. Select the appropriate plan format for that bounded objective.
- Record stage progress and gate evidence here; record HU/task acceptance and validation in its issue/PR. No separate DWP master-plan ID is a prerequisite for G0.

## Current Status — scientific decisions 2026-10-21; engineering migration 2026-10-23

Implementation and human gate approval are separate. Mauricio accepted G4 and exact freeze proposal `66d7208066476b027721182d185770d2522dfe5d891caf4b3b2759177dcc5e09`; PLAN_028 then executed the authorized frozen 2025 evaluation without retuning. On 2026-10-21 Mauricio accepted the scientific disposition G5 `NOT_APPROVED`: Stage 5 is closed, Champion remains `NOT_SELECTED`, and every exposed model retains the `PROVISIONAL_CANDIDATE` role. The implemented Stage 6–8 read-only slice presents traceable persisted demonstrative evaluation results and their governance status; it does not perform online inference or establish operational prediction.

| Stage / gate | Implementation state | Gate / evidence state |
|---|---|---|
| Stage 0 foundation / G0 | Foundation delivered in PR #5 | Historical dedicated independent foundation review remains UNVERIFIED. Later reviews do not retroactively supply it. |
| Stage 1 product definition / G1 | Delivered in PR #7 | CLOSED by Mauricio's explicit confirmation; final runtime schemas remain unfrozen. |
| Stage 2 data understanding / G2 | Kedro data construction, Y and current channel; original notebook 03 and bounded EDA preserved as historical evidence | G2 APPROVED by Mauricio on 2026-10-21. The accepted Data & Target Freeze retains the documented retrospective-availability, provenance, field-definition and unexecuted 5/7/9-year-sensitivity limitations. |
| Stage 3 data engineering / G3 | Kedro preparation: 16 derived features, temporal partitions and saved train-only preparer replay; notebook 04 historical | G3 APPROVED by Mauricio on 2026-10-21. The preparation is accepted for the current project baseline; this does not prove operational availability or approve a model. |
| Stage 4 model engineering / G4 | References corrected in PLAN_021; XGBoost in PLAN_022; three families and two controlled XGBoost ablations executed in PLAN_023 / draft PR #15 | G4 ACCEPTED by Mauricio for the exact PLAN_028 proposal/protocol on 2026-10-21. This does not approve a champion or G5. |
| Stage 5 / G5 | PLAN_027 corrected development calibration/threshold availability; PLAN_028 executed and reproduced six frozen final model/preparer procedures over the complete 2025 block. All six candidate/horizon procedures are `does_not_meet`. | CLOSED with Mauricio's accepted disposition G5 `NOT_APPROVED`; Champion `NOT_SELECTED`. The 2025 block is consumed for this comparison. |
| Stage 6 / G6 | Product Contract v1.1 is implemented and technically reviewed for the bounded read-only demonstrative slice. | G6 `PENDING` Mauricio's explicit human decision; technical completion does not approve the gate. |
| Stage 7 / G7 | The read-only API is implemented, packaged and validated against Product Contract v1.1. It serves persisted demonstrative results and performs no online inference. | G7 `PENDING` Mauricio's explicit human decision; local DWP completion and passing validation do not approve the gate. |
| Stage 8 / G8 | The read-only dashboard is integrated with the Stage 7 API and was squash-merged through PR #22 as `b8d2ea3cab676bb986dc2c180e1db167f24d61ea`; its tree matches technical HEAD `2932ff87a86ae9d8e81f3484ab6dbddc733ee823`. | G8 `PENDING` synchronization and published-app validation in Lovable, followed by Mauricio's explicit human decision. Remote CI on the merge commit remains `UNVERIFIED` where GitHub access prevents observation. |
| Stages 9–10 / G9–G10 | `NOT STARTED` | Deployment, monitoring and later gates remain future work and require the preceding human decisions. |

Mauricio authorized the bounded preparation implementation before the formal G2/G3 decisions and subsequently approved both gates on 2026-10-21 using the existing notebook 03/04 evidence. This later approval does not retroactively change historical plan states. Stage dependencies below remain the acceptance order; branch names, plan completion and passing tests do not themselves close gates.

The separate local `PLAN_019_notebook04_runtime_acceptance` completed actual fresh-kernel execution and real-artifact acceptance (3/3 criteria), preserving scientific sources. Stage 4 PLAN_020 then implemented simple references under explicit bounded authority. Its accredited AP/onset results require PLAN_021's correction; the historical approval is preserved rather than rewritten. The approved selection policy is owned by the Stage 4 contract/README and DEC-123. No candidate search, final-block comparison or champion is authorized by the corrective delivery.

### Current deliverables and authoritative evidence

| Delivered scope | Evidence owner | What it does not establish |
|---|---|---|
| Source decisions, residence/onset, supplied 2013 records unchanged, all notification classifications and coverage zeros | [Scientific decision register](../product/traking-concluciones.md), DEC-113/114/118/120/122 | Certified reporting completeness or historical operational availability |
| All 69 source-field definitions and explicit unresolved semantics | [Active canonical matrix](../product/stage-2/DATA-01-Priority%20Field%20Matrix.md) | Selection of all fields as predictors; six insufficient operational definitions remain explicit |
| Individual consolidated file, monthly climate panel, Y T+1/T+2 and current four-zone channel | [Notebook 03](../../notebooks/03_consolidated_dataset_pipeline.ipynb), [construction record](../product/stage-2/CH1-dataset-construction-candidate.md) and local construction contract/manifest | Final model suitability or G2 approval |
| 16 derived candidates, 28 deterministic features, 29 raw model inputs, separate X/Y and eight temporal windows | [Preparation workflow and contract](../product/stage-3/README.md), [final technical evidence](../product/stage-3/milestone-3-validation.md), notebook 04 | Predictive utility, estimator compatibility or performance |
| Executed code-only notebook, immutable artifact identities and training-only transformations | Same preparation evidence and local PLAN_018 journal/review | A trained or deployed predictor |

The five-value channel rule is **five historical observations of the same calendar month from the five years before the target year**, with required month-level history and no future periods. Entire historical years need not have closed (DEC-122). November 2024 → January 2025 can use January 2020–2024. Current `zona_canal_t` describes T; future Y remains an outcome, never an input. General dengue defines the initial target; severe dengue stays separate. Combining streams for Y is a later experiment.

January 2020 climate has been recovered/incorporated for the 76 reviewed municipalities (2,356 municipality-days). Monthly aggregation, numerical percentiles, evaluability, current zones and temporal selection are implemented; they are no longer blank implementation tasks. Source lineage and retrospective-availability limits remain explicit in their evidence owners.

### Next bounded work

1. Merge the reviewed `dengue-signal-atlas/stage8/api-integration` branch into that repository's `main`, confirm the resulting Lovable deployment, and review the published dashboard. This synchronization does not approve a gate.
2. After that published-app review, record Mauricio's explicit decisions for G6, G7 and G8 in dependency order while preserving G5 `NOT_APPROVED`, Champion `NOT_SELECTED`, `PROVISIONAL_CANDIDATE` model roles and the demonstrative no-online-inference boundary.
3. If further scientific work is authorized, use a separate bounded plan and protocol for the single recommended experiment: conservative shared-threshold selection with nested rolling temporal development. Do not optimize on consumed 2025 results; require a later independent period or predeclared nested outer validation.

Historical experiments, old PR reconciliation instructions and local plan failures are provenance, not a recurring analysis backlog. Reopen an analysis only for a concrete unresolved question that affects the next decision. No new EDA chapter is required by this documentation audit.

### Historical foundation evidence

- [PR #5](https://github.com/j-mauro-r/SAT-Dengue-V2/pull/5) merged on 2026-10-14, commit `1abbc08b8429c15b9145119da13cfc955da03067`.
- [Main CI run 38790310683](https://github.com/j-mauro-r/SAT-Dengue-V2/actions/runs/38790310683) passed on commit `4e816d43e92638f773f26bdb2d0ec8929ffeb4c2`; this is dated CI evidence, not current full-workspace conformity.
- Independent foundation review remains UNVERIFIED. Current audit/review does not claim to supply the missing historical review.

## Stage Plan

### Stage 0 — Engineering Foundation

Deliverables:
- Governance model
- Knowledge architecture
- Cross-cutting standards
- DWP-enabled workflow

Gate G0 — Engineering Foundation Ready:
- Foundation documentation accepted.
- DWP conformance passes.
- Repository validation baseline is green.
- Independent review evidence is recorded under the governance and validation policies.

### Stage 1 — Product Definition

Deliverables:
- Product goals and user workflow definition
- Dashboard functional requirements baseline
- Draft information needs for input/output contracts

Dependency:
- Stage 0 complete.

Gate G1 — Product Contract Ready:
- User, decision-support goals, dashboard capabilities, and inference workflow are approved.

### Stage 2 — Data Understanding

Deliverables:
- Data source characterization
- Data quality profile
- Endemic-channel analysis
- Target definition
- Data Contract draft/freeze
- Target Freeze

Dependency:
- Stage 1 product direction available.

Gate G2 — Data & Target Freeze:
- Data sources, temporal rules, target definition, and leakage constraints are approved.

### Stage 3 — Data Engineering

Deliverables:
- Reproducible data preparation pipeline
- Data quality controls
- Temporal split implementation
- Feature contract baseline

Dependency:
- Stage 2 Data & Target Freeze.

Gate G3 — Data Engineering Ready:
- Reproducible training dataset and quality/anti-leakage checks pass.

### Stage 4 — Model Engineering

Deliverables:
- Baseline implementations
- XGBoost candidate
- LightGBM candidate
- GAM candidate
- Planned ablation experiments
- Experiment tracking evidence

Dependency:
- Stage 3 pipeline and contracts ready.

Gate G4 — Candidate Models Ready:
- Candidate models and baselines complete under a common evaluation protocol.
- PLAN_023 adds LightGBM and Bernoulli/logit additive GAM, preserving the approved
  AP/Brier/simplicity policy and all eight cohorts. Notebook05/06 use fresh kernels;
  five experiments (three full candidates, two fixed-parameter XGBoost ablations)
  provide40 saved outer models,3,344 predictions each and territorial support.
- Frozen budget264 fits per run; the budget-guard correction requires a second
  identical run,528 actual fits in two preserved identities. No search expansion.
- Technical results and limitations: [Stage4 evidence](../product/stage-4/README.md).
  This supplies candidate-readiness evidence without accepting G4 or choosing a champion.
- Stage5 handoff: review temporal/territorial variation, calibration and an approved
  operational alert criterion; establish the reserved-evaluation protocol before
  accessing objectives from2025-01. Retrospective availability remains unproven.

### Stage 5 — Evaluation and Quality Assurance

Deliverables:
- Temporal validation and comparative evidence
- Calibration and threshold evidence
- Outbreak-onset evaluation
- Champion candidate recommendation

Dependency:
- Stage 4 candidate runs complete.

Gate G5 — Champion Approved:
- Champion recommendation is evidence-backed and approved for product integration.

### Stage 6 — Product Contract Freeze

Deliverables:
- Reviewed read-only dashboard prototype and resolved information hierarchy
- Final Input Contract for the implemented product slice
- Final Feature Contract
- Final Prediction Contract
- Final API Contract
- Explicit boundary for the later write-enabled input/feedback iteration

Dependency:
- Stage 5 evidence and product constraints.

Gate G6 — Product Contracts Frozen:
- The primary user has reviewed the read-only prototype.
- Product/model/API boundaries for the first vertical slice are versioned and approved for implementation.
- Model integration remains contingent on an approved G5 champion.

### Stage 7 — API

Deliverables:
- Read-only API implementation aligned to frozen contracts
- Persisted-result retrieval without training/inference side effects
- Contract and integration tests

Dependency:
- Stage 6 contract freeze.

Gate G7 — API Contract Pass:
- API contract, validation, inference integration, and persistence behavior pass.

### Stage 8 — Dashboard

Deliverables:
- Read-only dashboard MVP aligned to product requirements and API contracts
- Governance/performance context and explicit unavailable states
- Read-only refresh, filtering, and navigation behavior
- Write-enabled upload/inference and expert-feedback workflow only in a later approved iteration

Dependency:
- Stage 7 API readiness.

Gate G8 — Dashboard Functional Pass:
- Approved user journeys and dashboard acceptance criteria pass.

### Stage 9 — E2E and Deployment

Deliverables:
- End-to-end validation
- Packaging/deployment readiness
- Deployment evidence for the academic environment

Dependency:
- Stages 7 and 8 complete.

Gate G9 — E2E / Deployment Pass:
- First milestone: persisted approved result -> read-only API -> dashboard flow passes end to end.
- A later write-enabled milestone, when approved, validates input -> inference -> persistence and separate feedback capture end to end.

### Stage 10 — Monitoring, Maintenance, Final Review

Deliverables:
- Monitoring and maintenance operating model
- Retraining guidance
- Final governance, scientific, and product review

Dependency:
- Stage 9 complete.

Gate G10 — Final Review Pass:
- No unresolved critical/high findings and final evidence package is complete.

## Ordering Constraint (non-negotiable)

Product Definition -> Dashboard requirements -> draft information contracts -> Data Understanding -> Data/Target Freeze -> Data Engineering -> modeling -> QA/Champion -> final contracts -> API -> Dashboard -> E2E/deployment -> monitoring/final review


## Bounded Kedro engineering migration

PLAN_030 supplies explicit `kedro run --pipeline=replay`, separate synthetic E2E,
safe sequential restart, immutable publication and optional allowlisted MLflow.
The migration owner and testing guide define execution and required private parity.
Cleanup reconciles replaced facades, preserved original identities, documentation,
CI and harness; the plan's independent Final Review remains a separate pending
task. No Stage 6 implementation, G5 approval, champion selection, new real fitting
or operational deployment follows. The next approved product direction remains
the read-only prototype described above, subject to its own bounded authorization.


## Bounded EXP01 runner correction

The [EXP01 runner handoff](../operations/exp01-runner-handoff.md) records the
registered real graph and metadata-only preflight from corrective PLAN_037 on
PR #27. This infrastructure does not execute EXP01 or change its frozen protocol,
EXP00, EXP03, G5 `NOT_APPROVED` or champion `not_selected`. Real execution requires
a separate protocol-, commit- and data-bound human/reviewer authorization.

## Bounded EXP-BETA retrospective program

Mauricio authorized integral closure on `experiment/EXP-BETA02`, existing PR #67,
without merge. The [scientific closure and four-phase compliance matrix](../product/experiments/EXP-BETA/CONCLUSIONS.md)
record real canonical/Beta01/Beta02 verification and the independently identified
EXP-BETA03 frozen-score policy execution/reproduction. Bounded scientific status
is COMPLETED_WITH_LIMITATIONS; conditional/non-evaluable components remain explicit.
No stable joint sensitivity/load improvement was established, no further model
is automatically authorized, G5 remains NOT_APPROVED and champion not_selected.
The next integration gate is Mauricio's personal PR review and green required CI;
no merge or operational/product release approval is inferred from scientific closure.

## Bounded national canonical construction

Mauricio authorized the independent Step 3 national construction on
`feature/canonical-nacional-data-v1`, using the explicitly identified local
Step 1 notification calendar and Step 2 climate complement. The
[construction owner](../data/canonical-national-table.md) defines the independent
Kedro route, publication, comparison and technical eligibility gates. The scope
is one national table; G1 fitting and all national BETA extensions remain future
bounded work. Integration requires Mauricio's review and required CI, without
automatic merge. Existing scientific gates and BETA publications are preserved.

## Bounded EXP-BETA01 V2 national transfer

The [V2 owner](../product/experiments/EXP-BETA01-V2/README.md) records Mauricio's
authorization for the national G1 no-climate experiment, frozen before fitting.
The original 76 municipalities' role populations and G0/R0 predictions remain
fixed. Eight horizon/year cells passed the no-fit gate; 2020's restricted
additional history is explicitly limited. The new independent route does not
alter V1, default/replay or scientific gates. Results, uncertainty and any
follow-up recommendation belong to V2; no further model is automatically
authorized. Existing CI/preservation findings remain separately identified.

The authorized native execution is now complete and reproduced: eight G1
predictors, no historical refits, identical frozen evaluation cohorts and
byte-identical prediction/metric replay. [V2 results](../product/experiments/EXP-BETA01-V2/RESULTS.md)
classify expansion as `NO_RESPALDADA`; no national follow-up is automatically
recommended. Review/integration and inherited CI disposition remain separate
human/engineering gates; G5 and champion status are unchanged.

## Bounded EXP-DELTA01 academic alert policy

Mauricio authorized revision 2 and the independent four-responsibility `exp_delta01`
Kedro comparison, using the existing recovered G0_OFF selection scores and original
frozen evaluation predictions. [The experiment owner](../product/experiments/EXP-DELTA01/README.md)
records execution, source identities, validation and scientific disposition.

The run completed and all result payloads reproduced identically without new
inference, fitting or recalibration. The primary hypothesis is `NO_EVALUABLE`:
no feasible historical P1 threshold exists in T+1/2022 or T+2/2024, so neither
complete horizon may be replaced with partial pooling. Available annual results
do not establish general academic-policy improvement or territorial stability.
The source-admission blocker is resolved; these policy-feasibility limits remain
scientific results. Independent review, required CI and Mauricio's PR #73 review
remain integration gates. No merge, new experiment, G5 approval or champion follows.


### EDA-EXP02 Phase B — bounded exploratory closure, 2026-11-03

Mauricio authorized and the agent executed the new five-chapter
[anticipatory-signal EDA](../product/experiments/EDA-EXP02/README.md), preserving
Phase A and all original benchmark cohorts. O2 `EXPLORATORY_SIGNAL_FOUND` records
weak completed-episode recency association and representation variation, with
substantial existing-memory overlap and sparse conditional support. O1
`NOT_EVALUABLE` records the unresolved historical geography admission, despite a
verified official DANE service and matching regional codes. The
[conclusions](../product/experiments/EDA-EXP02/PHASE_B_CONCLUSIONS.md) delimit both.
No predictive experiment, training, policy change or EXP-DELTA02 was started.
Any later O2 ablation needs a separate human authorization and protocol; O1 first
needs historical geometry/crosswalk/topology evidence. PR #75 carries reproduction,
CI and pending independent-review integration evidence; no merge is authorized.
G5 `NOT_APPROVED`; `champion: not_selected`.

### EXP-DELTA02 — bounded spatial admission closure, 2026-11-03

Mauricio subsequently authorized the single T+1 neighbor-signal experiment,
including conditional fitting and a mandatory stop for invalid historical
spatial admission. [EXP-DELTA02](../product/experiments/EXP-DELTA02/README.md)
retrieved official national MGN 2005/2018/2021 municipal archives, verified the
76 target codes and potential-neighbor count coverage, and found nine unresolved
cross-vintage adjacency changes affecting six targets. Feasibility/scientific
disposition: `NOT_EVALUABLE`; execution: `COMPLETED_WITH_LIMITATIONS`.
No spatial feature, candidate fit or prediction was produced. The protocol,
quantitative topology, source identities and deterministic closure evidence are
preserved. This resolves the authorized scope without changing the academic
contract or opening another hypothesis. Required CI, independent review and
Mauricio's merge decision remain integration gates; no merge is authorized.
G5 `NOT_APPROVED`; `champion: not_selected`.

### EXP-DELTA02-R1 — fixed-MGN spatial candidate closure, 2026-11-03

Mauricio explicitly authorized a separate revision using only DANE MGN 2018 as
the retrospective topology decision. [EXP-DELTA02-R1](../product/experiments/EXP-DELTA02-R1/README.md)
appended the single T−1 neighbor notification mean to G0_OFF, executed the
frozen 2,653-row/313-onset T+1 cohort, and reproduced its immutable private
publication byte-for-byte. It gains one onset over G0_OFF and adds seven false
excess alerts. Pooled A/B pass but C fails (55.86% FAR-excess versus a 52.49%
ceiling), so the scientific disposition is `NOT_SUPPORTED`. Complete feature
coverage exists for 481 rows; 2,172 remain honestly missing. The original
EXP-DELTA02 `NOT_EVALUABLE` record is unchanged. No promotion, T+2,
EXP-DELTA03, new spatial search, G5/champion change, deployment, or merge is
authorized by this closure.

### EXP-DELTA03 — approved retrospective Phase 1 preparation

Mauricio approved [proposal A](../product/experiments/EXP-DELTA03/PHASE1-AUTHORIZATION.md)
on existing PR #78: preserve historical V2 residence/INI_SIN labels and cohorts,
prepare consolidated-data retrospective matrices, and use four separate MODIS
fractions with bare/other reference. Main national expansion is training only;
regional development/evaluation and explicit transfer boundaries remain fixed.
The [handoff](../product/experiments/EXP-DELTA03/PHASE1.md) owns actual publications,
reproduction, focused validation and final CI evidence. PLAN055 revision3 records
the bounded acceptance amendment; PLAN054 and prior failures remain preserved.

The [reconciliation](../product/experiments/EXP-DELTA03/SCIENTIFIC-RECONCILIATION.md)
explains all observed source differences and reproduces historical H5/cohort keys.
Current occurrence counts are audit-only. Historical release/value vintages and
operational E(T) availability remain unproved; results cannot imply PIT or
deployment readiness.2024 remains consumed retrospective stress;2025 excluded.
Water uses genuine observations through2021 without later-source fill; unsupported
2024 water pairs remain unavailable. No predictive experiment has run.

Mauricio subsequently authorized Phase 2 implementation and generated-only
validation on the same branch/PR78. PLAN_056 owns this bounded execution; PLAN054,
PLAN055 and the Phase 1 native matrix bundle remain unchanged. The
[implementation record](../product/experiments/EXP-DELTA03/PHASE2.md) and
[Phase 3 handoff](../product/experiments/EXP-DELTA03/PHASE3-HANDOFF.md) are the
current consumers. Technical synthetic runs do not grant a scientific freeze.

Mauricio approved the complete bundled scientific proposal on 2026-11-06,
recorded in [Phase 2 authority](../product/experiments/EXP-DELTA03/PHASE2-AUTHORIZATION.md)
and PLAN_056 revision 2. Model/calibration, experimental B=1 and paired block
uncertainty are `APPROVED_FOR_PHASE2_IMPLEMENTATION`. The separate
[annex preparation](../product/experiments/EXP-DELTA03/ANNEX.md) preserves the
Phase 1 core and copies national primary cohort/calendar keys with explicit
pending executable inputs. Original learned roles and regional evaluation remain
frozen. Final closure requires independent review and final-head green CI.
Protocol execution remains not_authorized; no Phase 3, real training/calibration/
prediction, permanent MLflow, merge, G5 approval or champion selection is authorized.


### EXP-DELTA03 — bounded manual Phase 3 preparation

Mauricio requests PLAN_057 with three substantive tasks: operational preparation,
verification after his manual execution, and analysis/documentary closure with
Final Review. [PHASE3.md](../product/experiments/EXP-DELTA03/PHASE3.md) owns this
scope from merged PR78/e266b9c. PLAN056 remains recorded7/8; merge is not CI evidence.
The agent completes missing executable connections and installed-runtime no-fit
admission using the existing graph and architecture, then stops at the manual
handoff. No scientific execution, automatic champion/G5, deployment or merge is
performed. Later tasks require Mauricio's actual completion report.
