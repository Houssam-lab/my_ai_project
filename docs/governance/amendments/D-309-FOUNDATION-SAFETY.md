# Constitutional Amendment Record — D-309

- **Change ID:** D-309-FOUNDATION-SAFETY
- **Status:** PROPOSED_PENDING_INDEPENDENT_REVIEW
- **Reason:** The project diagnostic and structural metaphor expose a foundational risk: agents can add surface code while dependency paths, parser compatibility, contracts, tests, and rollback remain unknown.
- **Scope:** Foundation safety constitution, agent boot instructions, the live diagnostic, decision index, and constitution enforcement.
- **Affected invariants:** No change without evidence; no higher layer over an unverified lower layer; fail-closed parsing; zero silent deletion; independent constitutional review.
- **Risk:** A mandatory pre-change packet increases friction, but omitting it permits irreversible edits to unknown load-bearing paths.
- **Owner:** Human/admin constitutional authority
- **Independent reviewer:** Required GitHub CODEOWNER reviewer who did not author this change
- **Mitigation:** Machine-checked foundation constitution reference, baseline/dependency/positive-negative-test/rollback requirements, and explicit stop rules.
- **Rollback:** Revert the amendment and paired enforcement changes as one reviewed change; preserve the historical record and append any superseding amendment.
- **Verification plan:** Run memory coherence, constitution enforcement, engineering governance, and `git diff --check`; independently verify branch protection.
- **Expiration:** 2026-11-03 if independent review has not approved, rejected, or replaced this record.
- **Human/admin approval required: YES**

## Declaration

This is a proposal, not approval. The author may not self-certify or merge it.
