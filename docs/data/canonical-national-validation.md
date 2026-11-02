# National Canonical Table — Local Acceptance, 2026-11-02

Status: `STEP3_APPROVED_WITH_LIMITATIONS` for construction and technical
eligibility. Model fitting, G1 evaluation and merge remain separate human gates.

The [construction contract and owner](canonical-national-table.md) specify the
independent route. Real private acceptance used committed implementation
`a2d785ae22782121432aa9f87515509616bd150e` with a clean worktree, Step 1 execution
`aa25e8cee5fd9cdaa4bf`, the pinned Step 2 union and the original BETA publication.
Only aggregate technical evidence is versioned; all source and output CSVs stay
local and ignored.

| Measure | Observed |
|---|---:|
| Territories / origin months / unique rows | 1,122 / 163 / 182,886 |
| Origin range | 2011-06 through 2024-12 |
| Accepted dengue / severe notifications | 1,308,130 / 20,022 |
| Unassigned in-window territorial records | 5,663, preserved in Step 1 |
| Complete-climate municipality-months | 182,560 |
| Current H5 available municipality-months | 120,126 |
| Original municipalities / paired keys | 76 / 12,388 |
| Compared columns, including onset/cohort reconstruction | 74 |
| Unexplained material differences | 0 |

The final publication is explicitly identified by bundle
`c2267f61c7624f19ea7056c2d891512b12e85d81214145df1d31815d28fc3c29` under
`data/processed/canonical_model_table_national_v1/`. Its single CSV is
116,008,632 bytes, SHA-256
`66c58d862f397b7953f7b32cfb6399330acc86e0acab1b5e3a6e809ea4b392d0`.

Counts, H5, zones, lags, onset labels, coverage controls and eligibility masks
match BETA exactly on shared keys. Monthly climate differs by at most
3.410605131648481e-13 due to floating serialization precision; the declared
blocking tolerance is 1e-10. Legacy outcome-gated columns differ only for targets
beyond December 2024; these cannot admit national training rows. Detailed local
comparison includes affected codes/months and causes.

| Logical view | T+1 eligible rows / territories | T+2 eligible rows / territories |
|---|---:|---:|
| Epidemiological readiness | 119,004 / 1,122 | 117,882 / 1,122 |
| G1_NO_CLIMATE | 92,735 / 1,122 | 92,061 / 1,122 |
| G1_WITH_CLIMATE | 92,584 / 1,120 | 91,911 / 1,120 |

All territories remain in the table. The two insular territories retain their
climate missingness. Outside the original 76 municipalities, approved window
history first permits current H5 in 2016-06; earlier rows remain ineligible.
This support asymmetry must be disclosed in any future comparison. Climate
contrasts require the intersection of cohorts. BETA target-role boundaries and
origin embargo are unchanged; the publication includes 80 temporal-role rows.

Real acceptance reproduced every final payload byte for byte, published and read
back all hashes, refused replacement of an existing identity, rejected an
altered in-memory payload and rechecked every source/code identity. No original
source, historical contract or BETA payload was modified. Model fits: zero.
Local detailed reports remain under `data/interim/canonical-nacional-data/`.

Focused validation: 77 unit/contract/bootstrap tests, Ruff, format, mypy,
Markdown links, whitespace and repo-only conformance (17 checks) passed. This
does not claim all historical DWP plans were revalidated. Source snapshots do
not establish operational availability, official extraction completeness or
historical boundary equivalence. Personal PR review and required remote CI
remain required for integration.
