# PROD-03 — Supported Decisions
Status and Purpose
**Document status: CLOSED — Stage 1 product definition, confirmed by Mauricio after PR #7 merge.**
Human Gate: APPROVED.
This document defines the type of human decision that SAT-Dengue V2 is intended to support. Detailed dashboard behavior belongs to PROD-04.
Decision-Support Boundary — Approved Decision
SAT-Dengue V2 supports departmental health officials in the early identification of risk of dengue excess or outbreak onset for T+1 and T+2.
The system provides predictive information to support human judgment. It does not autonomously decide, authorize, schedule, or execute public-health interventions.

# Supported Decision
The central decision supported by SAT-Dengue V2 is:
Does the available evidence indicate an increased risk of dengue excess or outbreak onset that warrants attention or preventive preparation?

The prediction may support consideration of actions such as:
- deeper epidemiological review;
- intensified surveillance;
- preventive activities;
- preparation for a possible increase in healthcare demand.
The specific action remains a human decision outside the system.

# Interpretation Boundary
T+1 and T+2 must be interpreted as separate future horizons.
A prediction represents estimated risk, not certainty.
The distinction between new outbreak onset and continuation of an existing event remains subject to the formal target definition in Stage 2.

# To Be Frozen Later
The following are not defined in PROD-03:
- alert thresholds;
- traffic-light semantics;
- probability interpretation rules;
- onset/continuation rules;
- handling of unavailable or insufficient predictions.
These will be frozen in the corresponding later stages.