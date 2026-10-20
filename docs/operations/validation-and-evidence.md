# Validation and Evidence Operations

## Evidence rules

- PASS: a named control executed successfully; state what it checked.
- FAIL: a named control executed and failed its criterion; distinguish code failure from a data-quality finding.
- BLOCKED: a control could not execute because a required dependency is unavailable.
- UNVERIFIED: evidence or approval has not been established.

Successful notebook execution does not approve date quality, complete reporting or a stage gate. Use the commands and surface mapping in the [testing guide](../TESTING_GUIDE.md); do not maintain a second command inventory here. A source/code/evidence-sensitive change invalidates affected checks, which must be rerun.

Independent review records severity, concrete references and resolution notes. Human approval governs merge and stage freezes. Dated historical outcomes remain historical; current evidence owns the present assessment.

## Current evidence navigation

Use the [master plan](../roadmap/master-plan.md) for progress and human gate status, the [preparation validation report](../product/stage-3/milestone-3-validation.md) for implemented pipeline evidence, and the [2026-10-20 harness audit](harness-documentation-audit-2026-10-20.md) for documentation changes and checks. Revalidate affected surfaces after edits; an earlier PASS is not a current test result.

The record below is historical. Its references to a current notebook, recognition report, open PR or then-active Stage describe 2026-10-16 and must not be used to resurrect the retired EDA or overwrite later decisions. Its original limitations are preserved.

## Historical reconciliation audit — 2026-10-16

Scope: all first-party project documentation, Stage 1/2 requirements, notebook source/saved results, local DWP status, link-check tooling and entry/review instructions. This is a consistency and reproducibility audit, not a new clinical/source audit or production implementation review.

| Finding | Resolution / remaining limit |
|---|---|
| Entry points falsely described Stage 0 as current | Stage 2 is current; Stage 1 closure recorded from Mauricio's explicit confirmation. Historical G0 review evidence remains UNVERIFIED. |
| Catalogue available but early notebook reported inventory BLOCKED | Catalogue parsing moved before climate controls; obsolete existence checks retired. Current states derive from executed validation. |
| Supplied DANE provenance still marked pending | One hash-bound JSON source record contains human-supplied URLs, download and reported version. Independent publication verification and historical applicability remain separate limitations. |
| Successful onset diagnostics could be read as clean dates | Label explicitly states diagnostic execution; 8,556 temporal alerts remain unresolved. |
| Territorial-quality rule omitted unresolved record codes | Criterion now includes record-code exceptions as well as absences/additional codes. No FAIL was changed to PASS to conceal exceptions. |
| Multiple accumulated result/provenance addenda conflicted | Recognition report is one current summary; provenance owns source/version limits; roadmap owns stage progress. |
| Redundant wrappers, initial brief and identical control exports | Unique handoff/performance/scope content merged into authoritative owners; eight shallow documents removed. Duplicate temporal-summary export retired in favor of coverage_controls_status.csv. |
| Link checker crashed on deleted tracked docs and missed new docs | Checker now inspects existing tracked plus untracked project Markdown; focused regression tests cover deletion, new documents and actual broken targets. |

Eight removed documents: `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/STANDARDS.md`, `docs/AI_AGENT_ONBOARDING.md`, `docs/AI_AGENT_COLLAB.md`, `docs/DEVELOPMENT_COMMANDS.md`, `docs/PERFORMANCE.md`, and the superseded `docs/product/stage-2/DATA-01-Data Understanding.md`. Their current useful content is available through the documentation index. The previously removed duplicate field matrix stays removed; Stage 1 requirements retain their distinct roles.

Validation and independent-review outcomes will be recorded below after execution. Historical plan outcomes are preserved rather than rewritten. No commit, push, PR or merge is authorized by this audit.

### Validation results

- PASS: Markdown link checks on existing tracked and new project docs, Ruff lint/format, mypy and both unit tests (including the working-tree link regression).
- PASS: independent reviewer `/root/audit_consistency` completed two read-only passes against the pre-audit working-tree snapshot. No unresolved high/critical source regressions remained; two wording findings were corrected. Scope: documentation, notebook source, metadata and link tooling. Final execution/output verification is recorded separately below.
- FAIL: full local DWP conformance — initial-recognition plan mixes legacy and Final Review lifecycle shapes. This was not introduced or concealed by this audit.
- UNVERIFIED: formal closure of PLAN_003. Its narrative reports 6/6 completed, but the current v7 journal contains only approval and derives 0/6 task closures. The underlying diagnostic artifacts exist; that does not repair missing machine-checkable closure evidence. Historical records were not rewritten.

These remaining harness/evidence findings do not mean the supplied catalogue is missing. This audit does not claim all project gates are green or authorize a merge.

### Final execution and preservation evidence

- PASS: final simplified notebook executed top-to-bottom from a clean kernel (11 code cells, consecutive execution counters, no error outputs); final notebook format validated and its actual fingerprint refreshed in the provenance register.
- PASS: all six retained territorial/count/temporal aggregate tables reconcile with the pre-audit outputs. The 8,556 temporal alerts, 76/71/76 municipal presence and 383/21 unresolved municipal-code records remain visible.
- PASS: both supplied catalogues and all three raw CSVs retain their pre-audit SHA-256 values. No 2013 source comparison or date correction occurred.
- PASS: supplied provenance in executed metadata matches the hash-bound source record; obsolete inventory/provenance-pending messages are absent. Territorial quality still FAILs its explicit criterion.
- PASS: five retained saved figures were visually inspected and their PNG hashes match the final execution. Two redundant climate-gap plots and one duplicate generated control table were removed; no active export inventory lists that table.
- PASS: project secret-pattern and excluded-runtime/config scans found no introduced matches. The ignored local Pillow dependency's known embedded-font pattern is outside project changes; no credential content was printed.

Assessment: documentation and saved evidence are reconciled within this audit's scope. Historical DWP/G0 evidence deficiencies, independent verification of DANE publication vintage, upstream export lineage and scientific remediation decisions remain explicitly unresolved. Stage 2/G2 are open; work remains local, without commit, push, PR or merge.
