# Constitutional Amendment Record — D-310

- **Change ID:** D-310-MICROSCOPIC-REVIEW
- **Status:** PROPOSED_PENDING_INDEPENDENT_REVIEW
- **Reason:** A diff-only review can miss load-bearing history, untracked files, hidden dependencies, and future compatibility risk. The repository needs a mandatory full byte census plus historical and forward-looking review before every character change.
- **Scope:** Foundation safety constitution, its machine enforcer, decision index, and the required agent entry contract.
- **Affected invariants:** Existing code is not grandfathered; future code cannot enter without updated evidence; UNKNOWN is not PASS; repository microscope remains non-circular.
- **Risk:** Full review costs time and may block changes; permitting local edits without it creates unbounded structural risk and false confidence.
- **Owner:** Human/admin constitutional authority
- **Independent reviewer:** Required GitHub CODEOWNER reviewer who did not author this change
- **Mitigation:** Byte census excludes only the acceptance packet, historical/forward review is explicit, and the gate checks the constitution anchors.
- **Rollback:** Revert as one reviewed governance change; preserve the amendment record and append a superseding record if needed.
- **Verification plan:** Run repository microscope, constitution, memory coherence, engineering governance, and `git diff --check`; independently verify branch protection.
- **Expiration:** 2026-11-03 if independent review has not approved, rejected, or replaced this record.
- **Human/admin approval required: YES**

## Declaration

This is a proposal, not approval. The author may not self-certify or merge it.
