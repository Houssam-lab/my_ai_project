# Constitutional Amendment Record — D-311

- **Change ID:** D-311-MANDATORY-REMEDIATION-START-GATE
- **Status:** PROPOSED_PENDING_INDEPENDENT_REVIEW
- **Reason:** The owner requested that microscopic diagnosis and treatment of old foundational defects become unavoidable for any agent before beginning work. Existing anti-vibe-coding controls referenced this rule; the canonical engineering constitution and governance audit now need to make the remediation start gate explicit and machine-checked.
- **Scope:** `ENGINEERING_CONSTITUTION.md`, the engineering governance policy and enforcer, agent context registry binding, negative tests, and the fail-closed parser behavior of `scripts/ci_guardrails.py`.
- **Affected invariants:** Old foundations before new work; no feature before foundation; no claim before evidence; fail-closed gates; no self-certification of remediation closure; entrypoint visibility for every agent.
- **Risk:** The start gate may block feature work when critical remediation remains open. That is intentional; the mitigation is to allow only foundation repair, containment, evidence capture, or independently reviewed closure while blockers exist.
- **Owner:** Human/admin constitutional authority
- **Independent reviewer:** Required GitHub CODEOWNER reviewer who did not author this change
- **Mitigation:** Add machine-readable policy for the diagnostic/remediation gate; require entrypoint binding; add negative tests that prove missing bindings and non-blocking critical statuses are rejected; make parser failures return violations instead of silent success.
- **Rollback:** Revert this amendment and the paired governance/script/test changes as one reviewed change; leave any diagnostic findings append-only unless superseded by a reviewed record.
- **Verification plan:** Run focused governance tests, the engineering governance audit, the repository microscope, `git diff --check`, and the parser-fail negative test. External branch protection remains human/admin verified.
- **Expiration:** 2026-11-03 if independent review has not approved, rejected, or replaced this record.
- **Human/admin approval required: YES**

## Declaration

This is a proposal, not approval. The authoring agent may not self-approve or merge it without independent review.
