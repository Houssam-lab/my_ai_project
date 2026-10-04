# Constitutional Amendment Record — D-312

- **Change ID:** D-312-CI-GREEN-REMEDIATION-GATE-FOLLOWUP
- **Status:** PROPOSED_PENDING_INDEPENDENT_REVIEW
- **Reason:** The D-311 remediation start gate exposed CI contract failures that must be repaired without weakening the gate: documentation-link parsing in the live diagnostic and lint complexity annotations for the governance validator.
- **Scope:** `.memory/project_diagnostic_truth.md`, `scripts/fitness/check_engineering_governance.py`, and the current acceptance packet/microscope evidence.
- **Affected invariants:** Required CI must be green without suppressing the remediation start gate; documentation links must remain valid; protected governance changes must remain visible through an amendment record; author self-approval remains forbidden.
- **Risk:** This follow-up may be mistaken for closing the remediation plan. It does not close any remediation item; it only makes the new governance control pass existing CI contracts.
- **Owner:** Human/admin constitutional authority
- **Independent reviewer:** Required GitHub CODEOWNER reviewer who did not author this change
- **Mitigation:** Keep the D-311 gate intact, replace ambiguous placeholder syntax with documentation-contract-safe wording, and annotate the intentionally comprehensive validator rather than splitting the constitutional check into hidden partial gates.
- **Rollback:** Revert this follow-up commit after independent review; D-311 can remain in place or be separately reverted through its own amendment path.
- **Verification plan:** Run documentation contract, ruff check for changed Python files, engineering governance, code acceptance, repository microscope, focused pytest negative proofs, and `git diff --check`.
- **Expiration:** 2026-11-03 if independent review has not approved, rejected, or replaced this record.
- **Human/admin approval required: YES**

## Declaration

This is a proposal, not approval. The authoring agent may not self-approve or merge it without independent review.
