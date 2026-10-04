# Constitutional Amendment Record — Engineering Governance Bootstrap

- **Change ID:** BOOTSTRAP-ENGINEERING-GOVERNANCE-2026-10-04
- **Status:** BOOTSTRAP_PENDING_INDEPENDENT_REVIEW
- **Reason:** Establish a canonical engineering constitution and machine-checkable enforcement path after discovering that existing governance is extensive but lacks a single protected amendment protocol, a machine-readable protected-artifact policy, direct deletion detection in the acceptance gate, and an explicit audit of these controls.
- **Scope:** Governance documents, policy, fitness gates, governance tests, CI wiring, agent entry points, CODEOWNERS, PR declaration, and acceptance evidence only. No product or application behavior is changed.
- **Affected invariants:** Independent verification; fail-closed required CI; zero silent test deletion; no self-approval of constitutional changes; explicit old-problem frontier; dependency and migration safety.
- **Risk:** A too-broad control could block legitimate changes; a too-narrow control could leave a bypass path. The policy therefore limits special checks to governance-sensitive artifacts, new dependency manifests, migration paths, and added test-weakening tokens.
- **Owner:** Human/admin constitutional authority
- **Independent reviewer:** Required GitHub CODEOWNER reviewer who did not author this change
- **Mitigation:** Deterministic policy validation, negative tests, required-CI wiring, and a minimal amendment record rather than a second copy of existing domain constitutions.
- **Rollback:** Revert this governed bootstrap as one reviewable change only after human/admin review. No database, runtime, product, or deployment state is altered.
- **Verification plan:** Run the governance audit, the acceptance gate, negative-proof gate, documentation contract, the focused governance tests, and `git diff --check`; independently verify the live branch-protection configuration with an administrator-capable GitHub identity.
- **Expiration:** 2026-11-03 if independent review has not approved, rejected, or replaced this bootstrap record.
- **Human/admin approval required: YES**

## Declaration

This record is an implementation proposal created under the one-time bootstrap exception. It is **not** an approval and does not authorize its author to merge it. The independent reviewer and GitHub protected-branch controls remain external authorities.
