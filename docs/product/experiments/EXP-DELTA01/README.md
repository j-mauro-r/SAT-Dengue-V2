# EXP-DELTA01 — constrained academic alert policy

**Execution: `COMPLETED`; primary hypothesis: `NO_EVALUABLE`.**
P1 has no feasible historical threshold for T+1/2022 and T+2/2024. Per the frozen
full-cohort rule, neither primary P1 horizon is evaluable. This is a scientific
policy-feasibility result, not an unresolved source or runtime blocker.
G5 remains `NOT_APPROVED`; `champion: not_selected`.

The [results](RESULTS.md) report complete baselines, all annual/department controls,
paired changes, feasibility and FAR transport. The [conclusions](CONCLUSIONS.md)
answer the seven scientific questions and do not claim general P1 improvement.

## Authority and preserved history

The [academic contract](../contrato.md) and [authorized revision 2](protocol.revision-2.json)
control the experiment. [AUTHORIZATION.md](AUTHORIZATION.md) records Mauricio's
explicit adoption and permission to implement/execute. Its sole methodological
amendment is admitting the already recovered G0_OFF selection probabilities.
Hypothesis, cohorts, H5, comparators, objectives, tie/undefined-FAR rules and
acceptance criteria match the [initial protocol](protocol.json), whose SHA-256
remains `c182fbe062faed58100548a43c70cc2a95df05aa86df4532344addb956a3003b`.
The [proposal](protocol.revision-2.proposed.json) is preserved as the original
proposal; [score recovery](SCORE_RECOVERY.md) remains the dated evidence owner.
Revision 2 updates proposal-time authorization metadata explicitly; no hidden
scientific change was admitted.

Originally the Cloud checkout lacked private sources and implementation stopped
at admission. Local investigation found models/calibrators but no original G0
selection arrays; separately authorized inference recovered all 4,386 probabilities,
with exact eight-cell evaluation replay. This experiment consumed that immutable
publication and performed **no new inference, fitting or recalibration**.

## Minimal Kedro execution

The independent `exp_delta01` graph has four responsibilities: verify/prepare
identified sources; select and persist historical P1 thresholds; apply frozen
P0/P1 to identical evaluation rows; calculate metrics and publish immutable results.
It reuses BETA cohort/embargo rules, benchmark CHANNEL/H5 helpers and metric code,
strict source readers and the existing atomic publisher. Default/replay and
historical scientific functions are unchanged. Only the required profile, catalog
and registry bindings were added.

Authorized real command (already executed; a published result cannot be overwritten):

```bash
KEDRO_DISABLE_TELEMETRY=yes .venv/bin/kedro run --pipeline=exp_delta01 --params=profile=exp_delta01,tracking=disabled
```

P1 maximizes detected development onsets subject to selection-block CHANNEL
excess-FAR + 0.05. It keeps whole score ties and resolves ties by fewer false
excess alerts, fewer total alerts, then higher threshold. The margin uses exact
integer cross-products. No-alert has undefined FAR and is infeasible. Both onset
and excess classes, defined CHANNEL FAR, an emitted alert and a detection are
required. The selected policies and complete frontier are saved before application;
evaluation cannot select or modify them. P0 thresholds and alerts are copied.

## Publication and reproduction

- Results: `data/processed/exp_delta01/d5c482b64e0d44e5012b20d24baa73d14f829ca4857bb2e2e53870ab3a82a284`.
- Manifest SHA-256: `a6f67b769cc52365da097ffa1b2709452252f0b7e9a5e6a6644c70a7f1cb0a92`.
- Selection freeze: `data/processed/exp_delta01/selection_freezes/e99f60fed004de212b4310d1114ad60e51b097a48ea7e251d2fbc41b8935d2b0`.
- Local source/reproduction receipts: `tmp/exp-delta01-execution/verification.json`.

Results include all paired rows, 60 metric strata, 30 paired-change strata, eight
policies, selection frontier, transport, protocol, provenance and conclusions.
No individual prediction is exported to docs or GitHub. All raw scores/keys remain
under ignored `data/`. Parent G0/canonical/benchmark/recovery bundles are untouched.

A second computation reloaded the pinned sources, reused only the identical
selection freeze, and reproduced all **10 payloads byte for byte** in memory.
It then exercised actual existing-result overwrite refusal and verified readback
and historical source hashes again. The local reproduction script is
`tmp/exp-delta01-execution/verify_and_reproduce.py`; it makes no model calls.
Run provenance records the supplied branch head with a dirty worktree and exact
source-code hashes; it must not be interpreted as execution of that head's clean
Git tree. The content identities, rather than branch names, bind the implementation.

## Focused validation and integration

PASS: the four-node real run, exact original P0 and P0/P1 probabilities/keys/labels,
complete 2,653/313 and 2,422/219 evaluation rows/onsets, all 4,386 selection scores,
original role/embargo separation, exhaustive independent frontier arithmetic,
all 60 stratum counts, equal AP/Brier, byte reproduction, no-overwrite and historical
preservation. The first technical attempt stopped before threshold selection because
of an overstrict equality check; it was corrected to the original BETA origin embargo
and regression-tested before execution. No method or result-driven threshold changed.

Generated-only DELTA tests cover whole ties, the exact 5 pp boundary, independent
selection, no-alert/insufficient support, no-feasible cells, missing-cell refusal,
original embargo equality, unchanged probabilities, publication and protocol tamper.
The targeted configuration/bootstrap checks also cover strict profiles/catalog and
registration without modeling imports. Adding `exp_delta01` to bootstrap inventories
keeps those existing assertions strict; no historical scientific test was weakened.
See the [testing guide](../../../TESTING_GUIDE.md) for the focused commands.

PASS: 40 focused tests; Ruff/format and mypy over the 12 affected Python files;
changed-document links/privacy checks; local reviewer pass with no confirmed
critical/warning finding. Receipts live under `tmp/exp-delta01-execution/`.
Repository-only DWP conformance: PASS (17 checks). Scoped-plan: not applicable;
no plan was requested. The two inherited all-plan findings remain separate and
were not rerun or waived. Independent review, remote CI and merge approval remain
separate integration gates. PR #73 remains open; no merge is performed.
