# executor

Purpose: implement scoped tasks with minimal diffs and validation evidence.

Checklist:
- Execute one scoped objective at a time.
- Keep edits small and reviewable.
- Run and report the relevant gate before declaring completion.


Project execution: `kedro run --pipeline=replay` is the guarded scientific E2E;
`replay_synthetic` is separate. Read docs/operations/kedro-migration.md and
docs/TESTING_GUIDE.md for dependencies, restart, tracking and exact gates. Notebooks
are historical identity evidence. Verify retirement consumers and the separate
cleanup preservation correspondence; do not modify older mappings or scientific
evidence. Keep DWP writers sequential and scientific approval separate from tests.
