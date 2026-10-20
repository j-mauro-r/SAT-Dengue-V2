# Harness documentation audit — 2026-10-20

## Scope and evidence boundary

Requested by Mauricio: audit the project harness documents, reconcile planning with implemented work, remove unused/duplicate guidance and apply changes on the existing branch. Starting branch: `Stage3/Data-Preparation`; implementation HEAD: `2e1c91992625408810b0e598d6025aa9619f0b09`; working tree initially clean. This is a dated audit record, not another planning authority. Direct documentation edits were explicitly authorized; no new branch, DWP plan, commit, push or PR was created by this audit.

Reviewed first-party entry points, governance, standards, stage roadmap, current contracts/evidence, CI/review instructions, agent catalogs and links from Stage 1. Repository inspection and local Git history support implementation claims; this audit does not assert fresh remote CI/PR states. Installed DWP/reviewer manuals were inspected as tool dependencies, not rewritten as project prose.

## Inventory and disposition

| Document / surface | Decision and reason |
|---|---|
| `docs/roadmap/master-plan.md` | KEEP / UPDATE. It remains useful as the single stage-level guide. Replaced obsolete Stage 2 queue with delivered notebook 03/04 work, explicit open G2/G3, corrected five-month historical rule and next bounded model handoff. No new EDA backlog. |
| `AGENTS.md`, root README and `docs/README.md` | KEEP / SIMPLIFY. Remove stale stage assertions and repeated validation policy; point to owning roadmap/testing documents. Distinguish current EDA from retired experiments. |
| `docs/governance/ai-developer-first.md` | KEEP / UPDATE. Retains approval and review boundaries; owns material contract-change rules. Clarifies that explicit current human instructions authorize work while copied assistant text does not establish approval. |
| `docs/governance/dwp.md` | KEEP / UPDATE. Pin installation history separately from present status, explain scoped/repo/all-plan checks; no mandatory new plan for routine documentation changes. |
| `docs/contracts/contract-lifecycle.md` | REMOVE AS DUPLICATE. Freeze ordering already belongs to the master plan. Moved unique contract-type/change rules to governance; redirected all active references. This was a short policy summary, not an executable scientific contract. |
| `docs/methodology/crisp-mlq-framework.md` | REMOVE AS DUPLICATE. Stage mapping belongs to the master plan; methodological/quality rules now live in ML standards. Redirected references without changing approved Stage 1 requirements. |
| `docs/architecture/system-overview.md` | KEEP / REWRITE. A future-only diagram missed the implemented notebook 03 -> modules/notebook 04 path. Now separates actual processing from future API/dashboard. |
| Engineering / ML standards and data policy | KEEP / UPDATE. Replace foundation-era assumptions and a mandatory `src/` convention with current modules, train-only preparation, preserved data and conditional infrastructure. No extra packaging, MLflow, DVC/S3 or benchmark system is required solely by these docs. |
| `.review/extension.md` | KEEP / UPDATE. Replace Stage 2-only context with concrete temporal/preprocessing review risks; retain severity and control-plane safeguards. |
| `.agents/README.md` and settings note | KEEP / CLARIFY. Custom settings keys are not evidence of enforced approval/testing. Existing personas are optional eight-line guidance, not a required team for every task. No settings behavior, hook or permission changed. |
| `.agents/docs/` catalogs and command delegators | KEEP. Catalogs describe installed tools; commands route to them. Distinct navigation roles, not extra implementation specifications. |
| `.agents/skills/**` and `.agents/agents/**` | KEEP UNCHANGED. Pinned vendor manuals/examples are tool resources; deleting them because the project does not currently use every workflow would break dependency integrity. Small optional personas do not justify a cleanup migration. |
| `docs/operations/validation-and-evidence.md` | KEEP / LABEL HISTORY. General evidence rules remain live; the old audit is explicitly dated, with current evidence owners linked instead of treating its results as fresh. |
| `docs/operations/stage2-pr-reconciliation.md` | KEEP AS HISTORY. Contains unique recovery/privacy information; obsolete PR #10 merge instructions are clearly historical, not active work. |
| `docs/product/traking-concluciones.md` | KEEP / RECONCILE CURRENT SUMMARY. Correct restored matrix, implemented Y/channel/climate and notebook 04 facts. Historical source sections remain discoverable and do not override later decisions. |
| Active 69-field matrix, scientific contracts, Stage 1 requirements, candidate dataset record and Stage 3 evidence | KEEP. Different semantic, executable, acceptance and evidence responsibilities. No scientific definitions or executable contract changed; Stage 1 edits only redirect retired document links. |
| Retired EDA archive, research inventory and local DWP journals | KEEP UNCHANGED. Unique provenance/decision evidence, not standing instructions or a reason to rerun EDA. |

## Gate reconciliation and remaining decisions

Technical preparation exists and is testable. G2/G3 acceptance is not recorded and cannot be supplied by a documentation edit. Present existing evidence for a bounded human decision before the next modeling phase; the old 5/7/9-year sensitivity remains unexecuted here and needs an explicit disposition rather than silent deletion or a fabricated PASS. Historical operational availability remains unproven. Global legacy-plan findings must remain distinct from repository/scoped-plan checks. No scientific result is modified by this audit.

## Validation and limitations

| Check executed in this audit | Observed result |
|---|---|
| `python -m pytest tests/unit -q` with repository-local temporary files and cache disabled | PASS: 184 tests; eight existing Stage 2 pandas warnings. No tests added for prose/link changes. |
| Ruff lint and format of tests; `mypy tests` | PASS: lint clean, 11 files formatted, 11 source files type-checked. |
| `python scripts/check_markdown_links.py`; `git diff --check` | PASS: current project Markdown targets resolve; no whitespace errors. References to both removed summaries redirected. |
| `conformance.sh --repo-only` | CONFORMANT: 17 checks, zero advisories. |
| `conformance.sh --plan .dwp/plans/PLAN_018_training_data_preparation` | CONFORMANT: nine checks, one semantic-review advisory; no plan records modified. |
| Default all-local-plan conformance | FAIL: two existing findings, PLAN_012 unresolved-critical-text detection and mixed lifecycle in the legacy initial-recognition plan; 178 passed, 24 advisories at inspection. This audit does not adjudicate, repair or waive these findings. |
| Protected-file SHA-256 comparison | PASS: 248 tracked code/test/notebook/tool/command/persona/CI/metadata/contract files unchanged. |
| Scientific preservation against PLAN_018 baseline | PASS: all 17 files unchanged, including original CSVs, notebook 03, panel, scientific construction contract and trace evidence. |
| Secret-pattern and excluded-runtime scans over tracked/new project files | PASS: no matches; ignored virtual environments, private data and local journals were outside this project-source scan. No sensitive values printed. |

No fresh notebook execution or model training was performed by this audit. A separate local `PLAN_019_notebook04_runtime_acceptance` appeared during the work and was observed with T-runtime started / 0 of 2 closures; its replay result is not supplied by this documentation audit. The protected files remained unchanged when checked. No claim of a new independent review or merge readiness is made; the existing human review/merge rules remain in force.

First-party documents and their use were inspected for this snapshot. No universal claim is made that a host cannot consume `.agents/settings.json`; the finding is narrower: the present custom keys have no enforcing consumer in this repository's code or CI. Installed manuals/catalogs/personas remain because they are valid tool resources, not redundant scientific specifications.
