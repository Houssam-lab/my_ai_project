# Constitutional Amendment Record — D-308

- **Change ID:** D-308-MANDATORY-DIAGNOSTIC-REMEDIATION
- **Status:** PROPOSED_PENDING_INDEPENDENT_REVIEW
- **Reason:** Deep diagnosis found a mismatch between governance claims and executable evidence: local Python 3.11 cannot compile Python 3.12-targeted code, guardrails reported parse errors while returning success, tests were unavailable locally, and incomplete/duplicated paths require classification.
- **Scope:** The live project diagnostic, mandatory remediation plan, constitution entry contract, agent instructions, and the constitution enforcer.
- **Affected invariants:** Fail-closed governance; no claim without evidence; UNKNOWN remains non-success; old and future code remain under the same constitution; required CI remains authoritative.
- **Risk:** Requiring remediation may block feature work while foundational defects remain. Not requiring it would permit agents to build on an unverified foundation and turn diagnostic uncertainty into production risk.
- **Owner:** Human/admin constitutional authority
- **Independent reviewer:** Required GitHub CODEOWNER reviewer who did not author this change
- **Mitigation:** Machine-check required artifacts and entrypoint references; block production claims while critical remediation is open; permit only evidence-backed, additive diagnosis and repair.
- **Rollback:** Revert this amendment and paired enforcement changes as one reviewed change; preserve the diagnostic history and append a superseding record if needed.
- **Verification plan:** Run memory coherence, constitution, engineering governance, `git diff --check`, and the negative guardrail test after R1/R2 implementation; independently verify branch protection.
- **Expiration:** 2026-11-03 if independent review has not approved, rejected, or replaced this record.
- **Human/admin approval required: YES**

## Declaration

This is a proposal, not approval. No author self-certification or merge is permitted.
