# EXP-DELTA01 revision 2 authorization — 2026-11-03

Mauricio explicitly approved revision 2 and authorized implementation, execution,
validation and documentation of EXP-DELTA01 in the current request, titled
“Codex Local — Completar EXP-DELTA01”. The request states:

> Mauricio ha aprobado explícitamente la revisión 2 de EXP-DELTA01.

It authorizes only the admission of the existing 4,386 recovered G0_OFF selection
probabilities and the P0/P1 threshold comparison on the original eight cells.
Do not repeat recovery/inference, train, recalibrate, change cohorts/H5, select P0
thresholds again, introduce another policy, or merge automatically.

- Initial protocol SHA-256: `c182fbe062faed58100548a43c70cc2a95df05aa86df4532344addb956a3003b`.
- Approved proposal SHA-256: `79f331dd5f09c34d5fb1611a78ff631ee321b5350f492620ee4e0c9136cc12b0`.
- Recovered source bundle: `b2e8256c9c37f8ecdb5f895ccd6d936cfb11f3896adc654ecab3c386bf57acc1`.
- Recovered manifest SHA-256: `9261b170ba059ca81d4409f30a4fd08e377f2e1e6debf64b9d337d7f3a1bb4b6`.

The guarded proposal patch preserves hypotheses, policy rules, cohorts, H5,
comparators and acceptance criteria. Its remaining blocked/pending-authorization
metadata described the time of proposal; the present request supplies both
adoption and bounded execution authorization. Revision 2 updates that metadata
explicitly and binds this approval. No additional scientific change is admitted.

The [initial protocol](protocol.json) and [proposal](protocol.revision-2.proposed.json)
remain unchanged. [Revision 2](protocol.revision-2.json) is the authorized execution
protocol. G5 remains `NOT_APPROVED`; champion remains `not_selected`.
