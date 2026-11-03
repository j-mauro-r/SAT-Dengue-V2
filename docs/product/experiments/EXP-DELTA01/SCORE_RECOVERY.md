# EXP-DELTA01 — controlled G0_OFF score recovery

**Status: `RECOVERY_VERIFIED` (2026-11-03). Eight of eight cells passed.**
Subsequent decision: Mauricio explicitly adopted revision 2 and authorized the
P0/P1 comparison; see [AUTHORIZATION.md](AUTHORIZATION.md). The pending-decision
language below records the recovery handoff before that subsequent approval.

The selection source has been recovered; DELTA implementation/execution and protocol
revision adoption still require a later human decision. No P0/P1 comparison was run.

## Why recovery was necessary

Original BETA publications persist evaluation probabilities, native models and global
intercepts, but not per-observation G0 selection arrays. V2 selection exports belong
to G1. Mauricio explicitly authorized controlled inference using only the eight
original G0_OFF models and their saved global calibrators. This separate authorization
does not silently amend the [initial frozen protocol](protocol.json).

## Method and acceptance

The [bounded recovery script](../../../../scripts/recover_exp_delta01_selection.py)
reuses BETA's original `prepare()`, `role_parts()` and `shifted()` functions and the
existing atomic publisher. It verifies pinned G0, regional canonical and benchmark
manifests, exact file membership, payload/source hashes and scientific code identity.
The numerical runtime matches original provenance: XGBoost 3.0.5, NumPy 2.5.4,
pandas 3.0.6 and scikit-learn 1.7.2.

Before any inference, acceptance was recorded under
`tmp/exp-delta01-score-recovery/pre-inference-acceptance.json`: **absolute tolerance
1e-15, relative tolerance 0**; nonfinite values rejected; exact keys/labels and original
alerts required. The original CSV serializer uses `%.17g`, sufficient for binary64
round-trip precision, and scores are read with `float_precision="round_trip"`.
Exact equality was expected. The tolerance ceiling is below five binary64 machine
epsilons and allows only tiny arithmetic variation, not float32-scale prediction
changes. It was not adjusted after seeing results.

Each original UBJ model is loaded without fitting. The exact ordered 24 OFF predictors,
original zone encoding and float64 input conversion are reused. Positive-class
`predict_proba` values are converted to float64, then passed through original
`shifted()` with the saved global log-odds intercept. No territorial offset is applied.
All evaluation cells must pass before any selection inference. Every prohibition on
fitting, calibration and threshold selection is also enforced by a runtime guard.

## Observed reproduction and complete selection populations

| Horizon | Evaluation | Evaluation rows | Recovered selection rows | Max absolute difference | Nonidentical / above tolerance | Result |
| --- | --- | --- | --- | --- | --- | --- |
| T+1 | 2020 | 661 | 376 | 0.0 | 0 / 0 | PASS |
| T+1 | 2021 | 846 | 661 | 0.0 | 0 / 0 | PASS |
| T+1 | 2022 | 693 | 846 | 0.0 | 0 / 0 | PASS |
| T+1 | 2024 | 453 | 410 | 0.0 | 0 / 0 | PASS |
| T+2 | 2020 | 588 | 355 | 0.0 | 0 / 0 | PASS |
| T+2 | 2021 | 779 | 588 | 0.0 | 0 / 0 | PASS |
| T+2 | 2022 | 641 | 779 | 0.0 | 0 / 0 | PASS |
| T+2 | 2024 | 414 | 371 | 0.0 | 0 / 0 | PASS |

All **5,075** evaluation probabilities reproduced exactly: maximum absolute difference
**0.0**, zero nonidentical values, zero values above tolerance and zero original-alert
discrepancies. Stored G0_OFF evaluation keys, targets, labels, scores and alerts also
match the pinned benchmark exactly. No threshold was selected or changed.

All **4,386** selection probabilities were recovered (T+1: **2,293**; T+2: **2,093**).
Full common ON/OFF eligibility is retained even for OFF, including climate completeness.
All five role audits match original cells, including T+2 selection embargo exclusions
53/21/73/52. Complete ordered selection keys/labels are preserved; no intersection or
population reduction was used. Within each cell, selection is disjoint from training,
calibration, adaptation and evaluation; training/calibration targets precede selection
origins. Predictor matrices, memberships, model bytes and calibrators have recorded hashes.

## New private publication

- Directory: `data/processed/exp_delta01/recovered_selection/b2e8256c9c37f8ecdb5f895ccd6d936cfb11f3896adc654ecab3c386bf57acc1`
- Bundle ID: `b2e8256c9c37f8ecdb5f895ccd6d936cfb11f3896adc654ecab3c386bf57acc1`
- Manifest SHA-256: `9261b170ba059ca81d4409f30a4fd08e377f2e1e6debf64b9d337d7f3a1bb4b6`
- Parent G0 bundle: `37a0cae62f4d3fa59cede281e032c9abd1b568a90933855b9eebd3b3d3fb5f4a`;
  manifest SHA-256 `4f6b86fcfcf46dbb47123b33ac29ecc9c23b62e65ac1c83ec460231f04816d7e`.
- Parent regional canonical bundle: `ddf4d3be23f7ce2cd874bbdc73fdf0f7b9ae5e6f7055b2761ec23bd31fc15c98`;
  manifest SHA-256 `037445487086f7123ee2bf4b97b9af06b96716e2f24e9ff5160177c59da261d8`.

The new manifest binds eight private selection CSVs, full cell/model/calibrator and
role metadata, source/code/runtime provenance, acceptance, evaluation reproduction
audits, limitations and the executed recovery script. Detailed scores/keys remain
under ignored `data/`; this document contains aggregates and identities only.

Two complete inference passes produced identical bytes for every payload. The existing
publisher verified the actual publication, rejected an attempted existing-output
publication with its no-overwrite policy, and verified all bytes again. Source and
historical publication hashes were preserved. Total: **32 inference calls**, **zero
model fits, zero calibrator fits and zero threshold selections**.

## Limitations and next decision

No original selection-array digest exists: exact historical equality of those absent
arrays cannot be independently demonstrated. Exact evaluation reproduction and repeated
recovery equality establish consistency with the frozen artifacts. Historical fit
membership is verified through pinned code, data and matching role metadata, rather
than an independent per-row runtime attestation. H5/consolidated-data retrospective
availability limits remain; 2024 is consumed stress and 2025 is excluded. Recovery
establishes no policy benefit, P1 feasibility, G5 approval or champion.

**Recommendation: proceed to the protocol-adoption and later implementation/execution
decisions. Do not start DELTA automatically.**
[Revision 2 proposal](protocol.revision-2.proposed.json) explicitly pins this recovered
source and contains guarded JSON Patch operations against initial protocol SHA-256
`c182fbe062faed58100548a43c70cc2a95df05aa86df4532344addb956a3003b`. It is `PROPOSED_NOT_APPROVED` and preserves the initial file byte for byte.
P0/P1 objectives, H5, cohorts, evaluation outcomes and policy rules are unchanged.

## Focused validation

PASS: source/payload identity, eight-cell evaluation reproduction, complete cohort and
temporal separation checks, two-pass byte equality, publication readback and no-overwrite
refusal. An independent publication readback reverified all 14 payloads, complete
selection keys/labels, calibrated scores, historical input preservation and the
guarded revision proposal without additional inference. Four generated-only tests
passed; they cover strict discrepancy reporting, source tampering,
prohibited-call guards and publication corruption/overwrite refusal. Scoped Ruff,
format and mypy pass, as do changed-document links and secret/privacy checks.
No full experiment or full test suite was invoked.

Repository-only DWP: PASS (17 checks). Scoped-plan: N/A (bounded recovery, no new plan).
All-plan DWP: two inherited local issues (465 passed, 60 advisories), separate from this
recovery. Independent review and new remote CI remain pending. PR #73 stays open,
without merge. Local receipts are under `tmp/exp-delta01-score-recovery/`.
