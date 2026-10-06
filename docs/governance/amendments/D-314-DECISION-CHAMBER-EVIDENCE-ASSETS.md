# Constitutional Amendment Record — D-314

- **Change ID:** D-314-DECISION-CHAMBER-EVIDENCE-ASSETS
- **Status:** PROPOSED_PENDING_INDEPENDENT_REVIEW
- **Reason:** The D-314 decision chamber (admin-only, read-and-compute, zero writes) ships three own-work screenshots under `docs/evidence/` as its browser evidence. `check_asset_license_clearance` requires every tracked binary to have a row in `docs/governance/ASSET_LICENSE_CLEARANCE.json`, and that file is a protected path under `docs/governance/**`. This record is the reviewed path for adding those three rows. Nothing else under a protected path is changed.
- **Scope:** Three appended rows in `docs/governance/ASSET_LICENSE_CLEARANCE.json` → `tracked_binary_artifacts`, one for each file:
  - `docs/evidence/d314-decision-chamber-2026-10-02.png`
  - `docs/evidence/d314-decision-chamber-dark-2026-10-02.png`
  - `docs/evidence/d314-outcome-preview-refused-2026-10-02.png`

  Each row reads `own_work_image`, `OWN_WORK_MIT`, with its measured `size_bytes`. No existing row is edited or removed, and no policy, gate, workflow or constitution text changes.
- **Affected invariants:** Every tracked binary is cleared before distribution. Protected paths change only through a new append-only record. No self-approval. Old before new: the clearance register keeps all previous rows byte-identical.
- **Risk:** Low. The rows describe screenshots taken by the authoring agent of this repository's own UI, rendered from a local stack with synthetic data. The risk is a screenshot that carries something it should not, such as a secret or personal data. They were opened and read before commit. They show only the chamber's derived text, the one company already named in the committed `docs/commercial/outreach/CONTACT_LEDGER.csv`, and synthetic form input (`releve.pdf`, `290`). They contain no email address, key, token or password.
- **Owner:** Human/admin constitutional authority
- **Independent reviewer:** Required GitHub CODEOWNER reviewer who did not author this change
- **Mitigation:** The rows are append-only and machine-checked by `check_asset_license_clearance`, so a size mismatch or a missing file fails CI. The screenshots are reproducible with `node scripts/e2e/hard_currency_center_ui.cjs` against a local stack. The same change introduces no new binary type and no third-party asset.
- **Rollback:** Revert the D-314 change as one reviewed change: the three PNGs, their three rows, and this record together. No data, schema or runtime state depends on them.
- **Verification plan:**
  - Run `python scripts/fitness/check_asset_license_clearance.py`, `python scripts/fitness/check_engineering_governance.py` (with `GOVERNANCE_BASE_SHA` set to the PR base), `python scripts/fitness/check_code_acceptance.py` and `git diff --check`.
  - The independent reviewer opens the three images and confirms they contain no secret or personal data.
- **Expiration:** 2026-11-05 if independent review has not approved, rejected, or replaced this record.
- **Human/admin approval required: YES**

## Declaration

This is a proposal, not approval. The authoring agent may not self-approve or merge it without independent review.
