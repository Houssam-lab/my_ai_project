# Constitutional Amendment Record — D-313

- **Change ID:** D-313-CI-REALITY-AND-FORMAT-FOLLOWUP
- **Status:** PROPOSED_PENDING_INDEPENDENT_REVIEW
- **Reason:** Required CI reported remaining reality/format drift after the remediation gate follow-up: documentation authority summaries still named D-305 while `.memory/decisions.md` records D-310, and Ruff format required deterministic formatting of the changed governance files.
- **Scope:** README decision-range summaries, `docs/DOCUMENTATION_INDEX.md`, Ruff formatting for changed governance files, and refreshed acceptance/microscope evidence.
- **Affected invariants:** Constitution equals reality; generated/derived numbers must match source memory; required CI must pass without weakening gates; protected documentation changes remain visible through an amendment record.
- **Risk:** Updating summary numbers can be mistaken for changing the underlying decisions. This change only aligns summaries with the existing `.memory/decisions.md` maximum and does not add or close decisions.
- **Owner:** Human/admin constitutional authority
- **Independent reviewer:** Required GitHub CODEOWNER reviewer who did not author this change
- **Mitigation:** Run `check_constitution_reality.py`, documentation contract, Ruff format/check, governance, code acceptance in PR-base mode, repository microscope, and `git diff --check` after the update.
- **Rollback:** Revert this follow-up commit after independent review; D-311/D-312 remain separately governed.
- **Verification plan:** Required CI plus local constitution-reality, documentation, formatting, governance, code-acceptance, and microscope checks.
- **Expiration:** 2026-11-03 if independent review has not approved, rejected, or replaced this record.
- **Human/admin approval required: YES**

## Declaration

This is a proposal, not approval. The authoring agent may not self-approve or merge it without independent review.
