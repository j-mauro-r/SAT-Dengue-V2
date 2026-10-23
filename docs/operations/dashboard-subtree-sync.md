# Dashboard subtree synchronization

`apps/dashboard` remains an independent Bun/Vite application mirrored through
Git subtree. Run all synchronization commands from a clean feature branch in the
SAT-Dengue-V2 repository. The helper refuses to operate on `main` or `master`.

## Imported revision

| Field | Value |
|---|---|
| Source | `https://github.com/j-mauro-r/dengue-signal-atlas.git` |
| Source branch | `main` |
| Imported commit | `958d64186da2c9a266d49c760453b24dc12145e1` |
| Prefix | `apps/dashboard` |
| Synchronized on | 2026-10-23 UTC |
| Import command | `git --exec-path=/usr/lib/git-core subtree add --prefix=apps/dashboard https://github.com/j-mauro-r/dengue-signal-atlas.git main --squash --message 'feat(dashboard): import Lovable dashboard - Task 1 of PLAN_007_stage8_dashboard_subtree'` |

The import commit includes the standard `git-subtree-dir` and
`git-subtree-split` trailers, so the source revision can be verified from Git
history. No dashboard-origin push was performed during this delivery.

## Pull Lovable changes into the monorepo

Create or switch to a clean SAT-Dengue-V2 feature branch, then run:

```bash
bash scripts/dashboard_subtree_sync.sh pull
```

This pulls and squashes the current `dengue-signal-atlas/main` tree into
`apps/dashboard`. Validate and review the resulting commit before publishing the
SAT-Dengue-V2 branch.

## Publish monorepo dashboard changes for Lovable review

Pass a new dashboard-repository branch explicitly:

```bash
bash scripts/dashboard_subtree_sync.sh publish stage8/<new-dashboard-branch>
```

The outbound command first performs the inbound pull above, verifies that the
destination branch does not already exist, splits `apps/dashboard`, and pushes
that split only to the named new branch. It rejects `main` and `master`; review
and merge the new branch in the dashboard repository through its normal process.

## Standalone validation

The committed `bun.lock` selects Bun. Its imported Lovable-cache URLs were
normalized to the public npm registry so a clean environment can install it.
The import review also applied compatible security patches, including Vite
8.1.5 to 8.1.6, without changing the application stack. From the imported
project directory:

```bash
cd apps/dashboard
bun install --frozen-lockfile
bun run lint
bun run test
bun run build
bun audit --audit-level=high
bun run dev
```

Generated `node_modules`, `dist`, `.output`, `.vinxi`, `.tanstack`, and `.nitro`
paths remain ignored by the imported project.
