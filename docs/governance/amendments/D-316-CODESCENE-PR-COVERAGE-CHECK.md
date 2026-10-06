# Constitutional Amendment Record — D-316

- **Change ID:** D-316-CODESCENE-PR-COVERAGE-CHECK
- **Status:** PROPOSED_PENDING_INDEPENDENT_REVIEW
- **Reason:** The external `CodeScene Code Coverage (main)` check never completes on a pull request. On PR #2595 it ended `timed_out` after exactly 6 hours (check run 112247837361): "Code Coverage Gate Timed Out — No valid coverage report found in the build pipeline". That leaves a red X on a PR whose GitHub Actions checks are all green. The owner asked on 2026-10-06 for the green check to appear on the current branches first. The cause is in our own job log (job 112454859769): on a PR branch, `cs-coverage upload` prints "Usage error: ... CodeScene only analyse the following branches: ("main")" and then "Uploaded code coverage data done.", and the step exits 0. CodeScene accepts that data but keeps it out of every analysis. Its pull-request gate is fed by a different command, `cs-coverage check --coverage-files`, with `CS_PROJECT_URL` set (https://codescene.io/docs/guides/code-coverage-gates/check-code-coverage-in-pull-and-merge-requests.html).
- **Scope:** One job in `.github/workflows/ci.yml`, `codescene-coverage`:
  - a new step runs `cs-coverage check --verbose --coverage-files coverage.xml` on `pull_request` only, with `CS_PROJECT_URL=https://api.codescene.io/v2/projects/83387`;
  - the existing `upload` step is limited to `push`, which is `main` only;
  - the warning text and the job's header comment are updated.

  No other job changes. The job stays out of `required-ci`, and no test, coverage floor or gate changes.
- **Affected invariants:**
  - A green job must not mean "did nothing" (D-235). The old PR upload was exactly that.
  - A third-party service must never block merges (D-234). The job is still absent from `required-ci`, and `check_ci_workflow_hygiene` still passes.
  - The token stays job-scoped, with both `!= ''` and `== ''` guards (D-234/D-235).
  - The installer is downloaded to a file, not piped to a shell (D-187).
- **Risk:**
  - The real token is a repository secret, so `check` cannot be run outside CI. If the project URL or the token's scope is wrong, the new step goes red on PRs. That is visible, and it does not block merges.
  - If CodeScene's own gate fails a threshold, the external check goes red. That is a real verdict, and the threshold is a CodeScene setting.
  - Measured locally with the same CLI (sha256 matches the published one): `check` takes only `--coverage-files`, and it exits 1 on an authentication error, so a failure cannot be silent.
- **Owner:** Human/admin constitutional authority
- **Independent reviewer:** Required GitHub CODEOWNER reviewer who did not author this change
- **Mitigation:**
  - The step summary says which path ran ("PR gate checked" versus "uploaded").
  - D-316 in `.memory/decisions.md` and `.memory/code_quality_truth.md` record that the live proof is still pending, and do not claim it.
  - The `push` path is byte-identical to before, so `main`'s baseline upload is unaffected.
- **Rollback:** Revert this commit. That restores the single `upload` step on every event, and with it the 6-hour timeout on PRs.
- **Verification plan:**
  - Run `python scripts/fitness/check_ci_workflow_hygiene.py`, then `python scripts/run_fitness_gates.py` and `git diff --check`.
  - On the next PR head, confirm that `codescene-coverage` logs the `cs-coverage check` output, and that `CodeScene Code Coverage (main)` completes instead of timing out.
  - After merge, confirm that `upload` still runs on `main`.
- **Expiration:** 2026-11-06 if independent review has not approved, rejected, or replaced this record.
- **Human/admin approval required: YES**

## Declaration

This is a proposal, not approval. The authoring agent may not self-approve or merge it without independent review.
