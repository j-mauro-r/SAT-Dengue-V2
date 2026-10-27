# EXP03 independent method and code review

Current protocol: 2.0.1; primary budget fixed by the [human decision](DESIGN.md#primary-budget-decision--2026-10-27).
The earlier review/validation records below describe protocol 2.0.0 and remain historical evidence;
their hashes and test counts do not certify the budget patch. Scientific execution remains unauthorized.


Source review: **PASS**. All fourteen concrete findings below are resolved in
the reviewed candidate. Core combined validation is **PASS**, with supplemental
validation for the final presentation-only correction;
remote CI and publication status are not asserted here.

## Identity and review boundary

- Review base: `01ce215c2d7738efe3a664e869ae87a3dd7199a6`.
- Pre-implementation HEAD: `b61cec9e1658b81efb5985b68cf511b610961e90`, including
  reconciliation with main's consolidated EXP00/EXP01 conclusions.
- Reviewed implementation commit: `a95bf04473aff1962240dc3da50f75fff5145628`.
- Canonical protocol SHA-256:
  `f806f3897a8dbef2bea01333626ee943e45aec9892f91607ca899f003e55beaf`.
- Reviewed source candidate fingerprint:
  `cfd563546031c16fa9f1bd53b154722108711c1f31daaf28d727ea8693e089e0`.

The fingerprint covers the 44 changed/new nonignored files other than this
review document, excluded to avoid a self-referential digest. Its definition is SHA-256 of the
UTF-8 JSON mapping from sorted file paths to their SHA-256 values, using
`sort_keys=True, separators=(',', ':')`. Paths are the union of
`git diff --name-only <review-base>` and
`git ls-files --others --exclude-standard`, retaining present files. Subsequent
validation-status documentation does not itself change the reviewed science.

An independent agent lane reviewed the authors' code using local Flow A from
`.agents/skills/ai-diff-reviewer/SKILL.md`, its shipped `prompt.md`, and
`.review/extension.md`. Reviewer and authors use the same backend; this is not
a separate vendor/account attestation or a human scientific sign-off. The
reviewer edited only review records, performed no private-data reads, and ran
no scientific experiment or permanent MLflow operation.

## Resolved findings

| Findings | Substantive correction | Generated regression evidence |
| --- | --- | --- |
| 1–2: stress uncertainty and different-target calibration | Restrict paired intervals to development; represent stress intervals as unavailable. Onset/excess controls keep individually labelled probability metrics and unknown cross-target calibration comparisons, including subgroups. | `test_exp03.py::test_probe_counts_pairing_freeze_and_controls`; development/stress rejection tests in `test_exp03_evaluation.py`. |
| 3–4: frozen profiles and stale recipes | Restore structured municipality/profile memberships. Recompute complete current arithmetic recipes at T-1 while independent lagged blocks and target thresholds retain their source dates. | Structured-profile benchmark test in `test_exp03_persistence.py`; whole-current-arithmetic delay test in `test_exp03_revision.py`. |
| 5–6: protected writes and native reconstruction | Reject symlink descendants before native writes. Reconstruct whole-tie threshold optimality and headline cell/contrast metrics from protected predictions and pre-gate exposure. | Symlink no-write, threshold reconstruction and metric-tamper tests in `test_exp03_reporting.py`. |
| 7–8: complete transport and publication provenance | Add annual, territorial/profile, common-calendar-month and count-pooled descriptive transport. Supply scope/matrix identities and actual terminal-freeze timestamp before publication. | Native transport and missing-provenance tests in `test_exp03_benchmark.py`; generated admission/publication/tracking integration tests. |
| 9–10: group coverage and revised protocol | Derive group onset denominators from matching pre-gate ledgers. Remove legacy FAR-margin and all-zero-onset-draw rejection language; record metric-specific resampling support. | Excluded-onset, exposure-only municipality and sparse-interval tests in `test_exp03_evaluation.py`; canonical matrix/protocol checks. |
| 11–12: evidence cache and historical missingness | Fingerprint source, protocols, dependency pins, installed versions and Python runtime before reusing generated fitted output; verify its payload checksum. Historical onset diagnostics now report evaluable/unknown transitions and null counts when no transition is evaluable. | Cache identity inspected in `tests/conftest.py`; missing-reference versus observed-zero profile test in `test_exp03_revision.py`. |
| 13–14: empty evaluation and population counts | Avoid empty predictor calls and retain truthful `model_fitted` counters for fitted cells without evaluation support. Distinguish covered, eligible and common onsets throughout ledgers, group metrics, benchmark and native reconstruction. | `test_exp03_engine_support.py`; actual T+2 covered-ineligible onset case, covered 5 / eligible 3 / common 1, and native reconstruction tests. |

The final follow-up also verified identical municipality/year bootstrap weights
on event counts, false-alert counts and all three exposure denominators. An
independent joint-draw reconstruction checks this correspondence, including
covered ineligible clusters. Cached exposure ledgers and attrs-free numerical
views preserve the pre-gate population and source-cut keys.

The final closure pass inspected coverage reconciliation for department,
municipality, historical profile and year. Pre-embargo groups remain represented
even when entirely excluded, and source/state, label, eligibility, feature and
abstention counts remain separate. Phase counters derive executed work from
`model_fitted` cells: the complete generated grid has 306 development fits, 102
terminal fits and zero benchmark fits, with zero searches. Native counter
validation checks these identities independently of evaluation support. The
synthetic example hashes its actual generated training/benchmark rows and uses
public code/runtime inventories for provenance; no label-only substitute
identity or private-data inspection is involved.

## Validation status and recommendation

The reviewer inspected the final frozen-source gate log at
`.dwp/plans/PLAN_016_exp03_complete_scope/gates/T-implementation/007-bash-tmp-exp03-checks.sh.log`:
**170 tests passed in 497.73 seconds**, with 30 dependency/framework warnings;
Ruff passed, 33 files were already formatted, mypy found no issues in 32 source
files, and Markdown links passed. The canonical generator confirmed 384 onset
plus 24 excess fits and 102 terminal cells. The gate exited zero. These are
generated-data engineering checks, not scientific results.

The lead additionally reports 25 repository-disposition checks passing after
fetching pinned historical Git references, plus preservation and scan checks.
Preliminary 164/168-test runs are superseded by the 170-test frozen-source gate.
Published commit identity and remote CI remain separate publication evidence;
neither is asserted by this review.

After that core gate, visual inspection identified presentation-only defects.
The final change is limited to `exp03_reporting.py` and its generated tests;
the scientific engine, predictors, metrics, decisions and native predictions
remain unchanged. The reviewer read `tmp/exp03-reporting-final.log`: **19 tests
PASS in 0.94 seconds**. Scoped Ruff, format and mypy also passed. No additional fit, calibration or threshold
selection is needed to render those validated native predictions again.

The reviewer inspected the numerical aggregation and completeness rules:
coverage sums each evaluation ledger cluster once, yielding eight horizon/cut
rows; annual transport flattens all 204 year/cell rows and displays every one
of the 102 terminal cells; the decision overview includes all 24 primary
development comparisons, with stress separately linked. Null and adverse
outcomes are retained. All secondary/objective and common-month/pooled transport
rows remain in their complete native source tables. Figure captions identify
the narrower primary overview and its complete source, rather than selecting
favorable variants. The renderer SHA-256 at review is
`7240deb83925707097d26e02ccb697a8f28e56db30eaad1c841f195cb3248f1a`;
the original producer identity and final renderer identity remain distinct.

The final table formats detection differences and their intervals in percentage
points (both multiplied by 100) and preserves burden in false alerts per
monitored municipality-year. Aggregate support and department/profile guardrails
are shown separately; unknown subgroup checks remain unknown. This formatting
does not change any native CSV value, statistical result or model decision.
The lead inspected the regenerated coverage/transport images and reports the
synthetic bundle at `tmp/exp03-generated-example`, identity
`f9f0241e00528c74e3ed19e364558ddc63ca00666b807106b2301ea27ef3bbe3`.
Rendering reused the validated native predictions with zero additional fits.

Recommendation: approve the reviewed source; the core combined gate and focused
presentation checks passed. No remaining source blocker was found. This review supplies
no merge approval, human execution authorization, G5 approval or champion
selection. At that review of protocol 2.0.0, `B_primary` and scientific execution were pending
(the budget decision is superseded by 2.0.1), G5 remains
`NOT_APPROVED`, and champion remains `not_selected`.

## PR #34 transport-period correction review

A separate same-backend agent reviewed the bounded working diff and actual
producer-shaped generated regressions. It identified fixture issues (conflicting
year must itself be valid; reload presentation summary must be regenerated;
explicit null differs from absence) and a contradictory `target_months` gap.
All were corrected before publication. The final checks cover canonical period,
redundant-alias agreement, annual/common/pooled view identity, retrospective
classification and five strict integer-zero counters at write and reload.
Valid unavailable rows preserve their reasons and explicit zeros. No unresolved
correctness findings were reported in the working-diff review.

This is engineering review by an independent agent lane on the same backend,
not cross-vendor review, scientific authorization, formal orchestra approval or
merge approval. The protocol and scientific sources are unchanged. See the
[validation correction evidence](VALIDATION.md#consumed-2025-transport-validation-correction-pr-34).

## Protocol 2.0.1 budget decision review — 2026-10-27

An independent read-only agent applied the installed AI Diff Reviewer methodology
and repository extension to the bounded diff against `4f43482c5fd25e64df73c0396c1fef183f95c39a`.
Recommendation: approve the code change; no unresolved findings. A historical
wording concern was corrected by distinguishing 2.0.0 evidence from current status.
The reviewer independently verified the approved value/rationale, historical
protocol byte preservation, both canonical hashes, registry/matrix agreement,
unchanged 408/102 scope and EXP00–EXP02 identities, fail-closed admission and
unchanged execution/G5/champion boundaries. All eight original EXP03 artifacts
were inspected, including the SIR/climate and 2024/2025 limitations.

This is engineering review, not scientific execution authorization or merge approval.
No experiment, fit, calibration, private read, operational preflight, approval-file
creation or MLflow write was performed for this patch.

## Three-phase operational admission review — 2026-10-27

An independent read-only agent reviewed the complete catalog → structural
preflight → authorization → admission → reservation → tracking → preparation/
fitting → benchmark → publication path using the installed AI Diff Reviewer
methodology and repository extension. Final recommendation: **approve**, with no
unresolved critical, high or medium findings.

A high TOCTOU finding was corrected: hashing a path before a later parser reopen
was insufficient against replace-and-restore. The adapters now consume verified
temporary copies; a regression changes/restores the original during parser access
and confirms approved values are consumed. A medium failure-reporting finding was
corrected: pre-reservation errors expose zero-effect receipts, while late errors
do not claim earlier effects were zero.

The final review verified privacy before authorization, full structural-receipt
binding, expected/observed manifest and payload identities, pinned catalog checks,
snapshot cleanup, benchmark revalidation, native lineage and publication gates.
Protocol 2.0.1, its canonical hash, budget, 408/102 matrix and EXP00–EXP02 remain
unchanged. The [operational handoff](IMPLEMENTATION.md#operational-admission-contract)
requires separate post-merge runtime/review/authorization/admission work.
No scientific approval, real authorization, experiment or result follows from
this engineering review. The reviewer performed no tests or scientific operations.
