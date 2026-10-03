# Reconnaissance Session — 2026-10-03

Scope: first-contact assessment of this repository under a "decades-grade" review
protocol. This document records **evidence and its limits**, not conclusions that
outrun the evidence.

Status vocabulary (protocol §21): IMPLEMENTED / VERIFIED / INTEGRATION VERIFIED /
RUNTIME VERIFIED / PRODUCTION VERIFIED. Nothing below is claimed above the level
actually reached in this sandbox.

---

## 1. What this repository is (measured, not assumed)

| Property | Value | How measured |
|---|---|---|
| Tracked files | 3,429 | `git ls-files` |
| Python files | 2,292 | `git ls-files '*.py'` |
| Python LOC | 373,535 | `wc -l` |
| Git history available | 1 commit (squashed) | `git log` |
| Target runtime | Python 3.12, uniformly | `.python-version`, `pyproject.toml`, `mypy.ini`, all Dockerfiles, all workflows |
| Fitness gates | 108 scripts in `scripts/fitness/` | `ls` |
| Top-level trees | `app/` (778 py), `tests/` (612), `microservices/` (485), `scripts/` (266), `shared/` (65) | file counts |

**Architectural shape:** a monolith (`app/`) plus 14 services under
`microservices/`, mid-strangler-fig migration (`docs/architecture/MASTER_CUTOVER_RUNBOOK`,
`LEGACY_*`, `PR1..PR5`).

**Maturity signal:** this is not a vibe-coded repo. Pinned linters with recorded
reasoning (D-184), a shrink-only lint-debt ratchet, fail-closed governance gates,
and incident write-ups with verbatim user reports. The protocol's default posture
("assume accidental architecture") was **largely wrong here** and is retracted.

---

## 2. Environment limits — what could NOT be verified, and why

**This sandbox cannot run this repository.** Recorded so the next person does not
repeat the attempt:

- Sandbox interpreter is CPython **3.11**; the project requires **3.12** (PEP 695
  `type` aliases and `class Stack[T]` generics are used in ≥37 files).
- 3.12 could not be provisioned: `python.org`, `deb.debian.org`, and
  `objects.githubusercontent.com` are network-blocked (only PyPI and `github.com`
  are reachable); `uv python install` fails on TLS (`UnknownIssuer`); building
  CPython from source is blocked by missing `openssl`/`zlib`/`ffi` dev headers.
- Consequence: **the root `conftest.py` is uncollectable on 3.11**, so the entire
  612-file test suite produced **zero** runtime evidence here.
  `pytest --collect-only` dies at `tests/conftest_support/helpers.py:51`
  on the PEP 695 generic function definition `_run_async` declared with a
  `[TResult]` type-parameter list.

**Therefore: no claim in this document reaches RUNTIME VERIFIED for application
behaviour.** Static gates below are VERIFIED only.

### False findings generated and discarded during this session

Logged deliberately — these are the errors the protocol exists to catch:

1. *"37 files have syntax errors."* — Wrong. Artifact of parsing 3.12 source with a
   3.11 `ast`. Retracted after checking what the project declares it targets.
2. *"`.gitignore` hides the whole source tree from Ruff."* — Wrong. Artifact of
   combining `--statistics` with `--show-files`. Ruff sees all 2,293 files.
3. *"114 lint errors."* — Wrong. Artifact of running Ruff **0.16.10** instead of
   the CI-pinned **0.14.0**; the extra findings are newer rules (PLR0917, UP042,
   RUF060). This is precisely the failure mode D-184 already documents.

Lesson (Experience Ledger): **reproduce the project's pinned toolchain before
reporting any gate result.** Three of my first four findings were environment
artifacts, not repository defects.

---

## 3. Verified gate results (project-pinned toolchain)

| Gate | Command | Result |
|---|---|---|
| Ruff lint | `ruff==0.14.0 check .` | **PASS** (after the fix in §4) |
| Ruff format | `ruff==0.14.0 format --check .` | **PASS** — 2,263 files already formatted |
| Mypy | `mypy==1.8.0 --config-file mypy.ini --follow-imports=silent shared/ app/integration/` | **PASS** — 0 issues, 73 files |
| Fitness (sample) | `scripts/fitness/check_vibe_coding_constitution.py` | **PASS** |

Note on mypy scope: the gate covers **73 of 2,292 files (3.2%)**. This is a
deliberate, documented beachhead ("grows by shrinking debt, never by loosening
mypy.ini"), not an oversight. Recorded as a *coverage fact*, not a criticism.

`check_no_app_imports_in_microservices.py` and `check_no_cross_service_imports.py`
could not be run here — they `ast.parse` repository sources with the running
interpreter and therefore need 3.12. **UNVERIFIED in this environment.**

---

## 4. Defect found and fixed (VERIFIED)

`main` was **red on its own lint gate**.

- `ci.yml:53` installs `ruff==0.14.0`; `ci.yml:73` runs `ruff check .`.
- That command failed with one `I001` on
  `tests/fitness/test_check_vibe_coding_constitution.py:1`.
- Cause: two blank lines after the import block. Ruff's isort default
  `lines-after-imports = -1` means *one* line before a module-level assignment
  (two only before a `def`/`class`). The next statement is `ROOT = Path(...)`.
- Fix: remove one blank line (1 deletion).
- Verified: both `ruff check .` and `ruff format --check .` pass, so the fix is
  format-stable and does not trade one gate for the other.

---

## 5. Principal open risk (evidence-backed, NOT yet actioned)

**Duplicated security-critical auth logic across the strangler boundary, with
class-level drift protection missing.**

Measured duplication between `app/` and `microservices/`:

- **28** byte-identical forked files.
- **55** substantive forks that have **drifted** (same logical path, different
  content), including:

| Similarity | Monolith | Service copy |
|---|---|---|
| 50.2% | `app/services/auth/crypto.py` | `microservices/user_service/src/services/auth/crypto.py` |
| 78.8% | `app/services/auth/service.py` | `microservices/user_service/src/services/auth/service.py` |
| 83.3% | `app/services/rbac.py` | `microservices/user_service/src/services/rbac.py` |
| 90.7% | `app/services/auth/registration.py` | `.../auth/registration.py` |
| 91.7% | `app/services/auth/token_manager.py` | `.../auth/token_manager.py` |
| 91.9% | `app/services/auth/password_manager.py` | `.../auth/password_manager.py` |

**This duplication is intentional and correct by the project's own constitution.**
`docs/ARCH_MICROSERVICES_CONSTITUTION.md` forbids `app/*` from importing
`microservices/*` specifically to avoid a distributed monolith, and that boundary
*is* gated. The duplication is a chosen cost, not an accident. The finding is not
"stop duplicating".

The finding is narrower and sharper:

> This duplication has **already caused a production incident**
> (D-WS-SECRET-KEY-001: monolith and user-service signed/verified JWTs with
> different default `SECRET_KEY`s, producing a login/WS-disconnect loop), and the
> regression test written afterwards
> (`tests/services/test_secret_key_consistency.py`) guards **the specific instance**
> — the `supervisor.sh` secret defaults — rather than **the class**: the ongoing
> semantic parity of the two forked crypto implementations.

The service copy's own comment states it exists
"لمطابقة monolith's `app/services/auth/crypto.py`" (*to match the monolith's*) —
i.e. parity is maintained **by hand and by comment**, with no executable check.
The monolith copy additionally carries documented security reasoning (token-type
constants as single source of truth; a recorded negative result on `iss`/`aud`)
that the fork does not.

Protocol §15 framing: the incident produced a fix and an instance-level regression
test, but not a **prevention** that makes the whole class harder to reintroduce.

**Status: UNPROVEN that current drift is harmful.** I did not demonstrate an
exploitable or behavioural divergence in today's code — only that the mechanism
which previously failed is still unguarded. Confirming or refuting actual
divergence requires 3.12 and is the top recommended next experiment.

---

## 6. Recommended next experiments (smallest-first, §11)

1. **Get a 3.12 runtime** (CI container, or a sandbox with `python:3.12-slim`).
   Everything else is gated behind this. Until then the 612-file suite is dark.
2. **Differential test, not a new gate.** Before adding any CI check, write one
   test that exercises both `crypto.py` implementations over the same inputs
   (sign in A → verify in B, and vice versa; token-type and expiry semantics).
   This *measures* whether drift is currently harmful. A gate added first would
   turn CI red on 55 pairs and assert a policy nobody has agreed to.
3. Only if (2) shows real divergence: propose a parity gate in the repo's existing
   `check_*_parity.py` convention, scoped to the auth pair, shrink-only.

Not recommended: de-duplicating the forks. That would violate the microservices
constitution and trade a measured, bounded risk for an architectural one.

---

## 7. Honest ledger

**PROVEN (in this sandbox):** the lint-gate defect existed and is fixed; Ruff
check+format and the mypy beachhead pass under the pinned toolchain; the
duplication and drift counts in §5 are exact byte/line measurements.

**UNPROVEN:** all application runtime behaviour; whether any of the 55 drifted
forks is semantically harmful today; whether the two uncheckable boundary gates
pass; whether the 108 fitness gates pass as a set.

**UNKNOWN:** everything that would require history (1 squashed commit), production
telemetry, or the 3.12 runtime.
