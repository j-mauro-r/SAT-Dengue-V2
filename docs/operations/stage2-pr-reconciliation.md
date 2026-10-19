# Stage 2 pull-request reconciliation and recovery

## Purpose and source identities

This review reconciles local Stage 2 work and three independently opened pull requests without discarding data, files, decisions or branch history. Stage 2/G2 remain open.

| Source | Starting revision | Disposition |
|---|---|---|
| Local Stage2/Data-Understanding / PR #10 | `ef390f8ea34e7668d748f613823ba1090f1057f3` | Original history preserved; three uncommitted decision documents saved as `f1c0e4b`. |
| Main (squash-merged Stage 1 PR #7) | `3c859d6cafd588769a42760a941e0dafe7b251b8` | Merged into the Stage 2 branch; eight add/add conflicts retain later human-confirmed Stage 1 closure wording. Product requirements are unchanged. |
| [PR #8](https://github.com/j-mauro-r/SAT-Dengue-V2/pull/8) | `b7f00093c543236fc41b03e97b19f87f456e45a6` | Research inventory retained byte-for-byte with all sources and limitations. |
| [PR #9](https://github.com/j-mauro-r/SAT-Dengue-V2/pull/9) | `31c1d8b1504fd60209727ca595573d68c90dd641` | Complete 119-line decision document retained alongside the full local register, with a current-authority/supersession summary. |

The [decision register](../product/traking-concluciones.md) starts with current rules; its preserved source sections are historical evidence, including superseded pending statements. DEC-121 records the imported approved Y configuration and its relationship to DEC-113..120. No source history was replaced with the shorter PR #9 file.

## Local preservation and recovery

A private, Git-ignored backup lives under `tmp/reconciliation-20261018-stage2/` in this checkout. It contains:

- `workspace-files.tar`: 499 files and three symlinks, including supplied data, earlier DWP journals/results and local artifacts. Every archived regular file is checked against its SHA-256 inventory.
- `inventory.json`: byte hashes, sizes and pinned source revisions; no patient rows are printed in the review report.
- `repository.bundle`: all local refs and recoverable Git history, checked by `git bundle verify`.
- `unstaged.patch`, `staged.patch`, `status.txt` and the original tracked-file inventory.

Named `backup/reconcile-20261018-*` refs preserve the starting local head, main and all three PR heads. Restore to a separate directory from the bundle and archive when needed; do not overwrite the live checkout or extract the archive into it without a recovery review. Rebuildable virtual environments/caches are excluded. The active PLAN_007 evidence is journaled separately rather than recursively archiving itself.

All supplied raw/reference data and older DWP evidence are checked again after integration. These archives remain local and are not included in a PR. They protect this reconciliation on this disk; they are not an off-device disaster-recovery service. The data policy remains in force.

## Private source files and existing Git history

The original PR #10 tree tracked `data/sources/Dengue_Datos_2012_210.xlsx` (33,194,283 bytes) despite the local-data boundary. Its other tracked workbook, `Listados_DIVIPOLA.xlsx`, is also local reference material. Both are removed from the Git index while their disk files, hashes and private backups remain intact. Small non-sensitive DIVIPOLA metadata stay versioned.

Removing a path from the final tree does **not** erase its earlier commits. No history rewriting, force push or deletion of an upstream branch is performed. The pre-existing published branch history still contains those workbook blobs. **For the final merge into main, use squash merge of the cleaned integration tree** to avoid importing those original commits into main. This does not purge the already published historical objects; any separate cleanup requires an explicit preservation/retention decision. Never publish the private backup or replay the old data commits onto main.

## Validation and handoff

The executable evidence lives in the local DWP `PLAN_007_reconcile_stage2_pull_requests`: archive integrity, source/earlier-output immutability, all starting heads as ancestors, complete source decision text, research file identity, conflict-free index and no private datasets in the final tracked tree. The standard unit/lint/format/type and Markdown-link checks are applied before updating PR #10. No new EDA, model training or target sensitivity is run by this reconciliation.

The repository-wide DWP check has a pre-existing mixed-lifecycle failure in the old initial-recognition plan. It is reported separately; the new plan must pass scoped conformance. Historical G0 evidence and G2 are not silently approved by integration.

Use [PR #10](https://github.com/j-mauro-r/SAT-Dengue-V2/pull/10) as the integrated review candidate. PRs #8/#9 and all original branches remain open/intact until Mauricio decides their disposition. Merging or closing them is not part of this reconciliation. Before merge, review the latest checks on the exact PR #10 head and the remaining scientific tasks in the master plan.
