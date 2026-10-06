# Constitutional Amendment Record — D-315

- **Change ID:** D-315-MONOLITH-TEST-TIMEOUT-HEADROOM
- **Status:** PROPOSED_PENDING_INDEPENDENT_REVIEW
- **Reason:** The `test-monolith` job in `.github/workflows/ci.yml` went red on `main` at the merge of PR #2595 (commit 9cfa5cd, CI run 37462983764). No test failed. The step `Run monolith tests` was killed at its 42-minute limit with the suite 96% done, and `required-ci` then failed with it. The same tree ran in 40.0 minutes on the PR (6217 passed), and the commit before it, b80c44d, took 38.2 minutes. One re-run of the failed job on `main` (attempt 2) then passed in 40.0 minutes, with all 29 jobs green. So the cap, not the code, caused the red, and the green on `main` now depends on runner luck. A 42-minute cap left about 2 minutes of headroom against more than 2 minutes of runner-to-runner variance. The owner chose this fix on 2026-10-06.
- **Scope:** Two numbers in `.github/workflows/ci.yml` for the `test-monolith` job, plus their comments:
  - job `timeout-minutes` goes from 45 to 55;
  - step `timeout-minutes` goes from 42 to 52, keeping the existing rule that the step cap is the job cap minus about 2.5 minutes for install.

  No test, deselect, ignore, coverage floor, `--timeout` per test, or other job is changed.
- **Affected invariants:**
  - A red gate over a green run is not allowed (D-105, the reason this cap was already raised from 30 to 45).
  - No test is weakened or skipped to get green.
  - The step limit stays below the job limit, so the log is kept when the suite is slow (ISS-212).
- **Risk:** A genuinely hung run now takes up to 10 more minutes to be stopped. The per-test `--timeout=300` still names a single hung test. The larger risk is hiding the real problem: the suite's runtime. That is mitigated by recording the cause and the follow-up rather than treating the new cap as the fix.
- **Owner:** Human/admin constitutional authority
- **Independent reviewer:** Required GitHub CODEOWNER reviewer who did not author this change
- **Mitigation:** The new comment in `ci.yml` records the three measured durations and the measured cause. That cause is the autouse `db_lifecycle` fixture in `tests/conftest.py`, which drops and recreates the whole schema before every test (about 0.3 s per test across 6217 tests). The way back down is still to make the suite faster, not to shave the cap. That speed-up is recorded in D-315 as owed follow-up work.
- **Rollback:** Revert this commit. That restores 45 and 42 exactly; nothing else depends on these values.
- **Verification plan:**
  - Run `python scripts/fitness/check_engineering_governance.py` with `GOVERNANCE_BASE_SHA` set to the PR base. Its test-integrity check rejects added skip, xfail, deselect or ignore tokens in `ci.yml`.
  - Run `python scripts/run_fitness_gates.py` and `git diff --check`.
  - Then confirm `test-monolith` and `required-ci` are green on the PR head and on `main` after merge.
- **Expiration:** 2026-11-06 if independent review has not approved, rejected, or replaced this record.
- **Human/admin approval required: YES**

## Declaration

This is a proposal, not approval. The authoring agent may not self-approve or merge it without independent review.
