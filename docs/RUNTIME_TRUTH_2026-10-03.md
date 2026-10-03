# Runtime Truth Report — 2026-10-03

Continuation of `RECON_SESSION_2026-10-03.md`, which ended at the static-analysis
boundary because no Python 3.12 runtime was available. **That blocker is now
removed.** This report records runtime evidence.

Evidence ladder used throughout (categories never merged):

| Level | Meaning |
|---|---|
| STATIC VERIFIED | proven by reading/parsing files |
| TOOLCHAIN VERIFIED | proven by the project's own pinned linters/type-checker |
| UNIT VERIFIED | proven by executing the repository's tests |
| INTEGRATION VERIFIED | proven across a real component boundary in one process |
| RUNTIME VERIFIED | observed executing on the declared target runtime |
| UNPROVEN | not demonstrated here |

---

## A. Runtime Environment

The repository targets Python 3.12 (`.python-version`, `pyproject.toml`,
`mypy.ini`, all Dockerfiles, all workflows). The sandbox ships 3.11.

Every supported runtime path was tried, in the order the mission specified:

| Path | Result |
|---|---|
| A — project Docker/Compose | **unavailable**: no `docker` binary, no daemon |
| B — CI container image | **unavailable**: `ghcr.io`, `registry-1.docker.io` unroutable |
| C — devcontainer / Codespaces | **unavailable**: same, requires Docker |
| D — other reproducible 3.12 | **achieved** (below) |

Network reachability was mapped rather than assumed:

| Host | Status |
|---|---|
| `pypi.org`, `files.pythonhosted.org` | reachable |
| `github.com`, `api.github.com`, `codeload.github.com` | reachable |
| `objects.githubusercontent.com`, `raw.githubusercontent.com` | **blocked** |
| `python.org`, `deb.debian.org`, `ghcr.io`, `anaconda.org` | **blocked** |

Consequences: `apt-get update` fails on every index; `uv python install` fails
(its CPython builds are GitHub *release assets*, which live on the blocked
`objects.githubusercontent.com`); no prebuilt interpreter is obtainable.

**Resolution — CPython 3.12.15 built from source**, using only reachable hosts:

```
zlib    1.2.13        codeload  -> static, -fPIC
openssl 3.0.15        codeload  -> static, -fPIC, no-shared no-tests
cpython 3.12.15       codeload  -> --with-openssl, --with-ensurepip
libffi  3.4.4 headers codeload  -> ffi.h generated from ffi.h.in; links the
                                   system libffi.so.8.1.2, which *is* 3.4.4
sqlite3               PyPI      -> pysqlite3-binary's C module re-exported
                                   under the stdlib name (no headers/tcl here)
```

Final interpreter: `Python 3.12.15 (main, Oct 3 2026) [GCC 12.2.0]`,
OpenSSL 3.0.15, SQLite 3.51.1, `ctypes` verified with a live FFI call
(`libc.strlen(b"abcd") == 4`). Still absent: `lzma`, `bz2`, `readline` — nothing
in the collected suite needed them.

**No repository file was modified to accommodate the sandbox.** No Python
requirement was downgraded, no PEP 695 syntax rewritten, no test weakened, no
gate removed. The two environment shims (`_sqlite3`, `libffi.so` symlink) live
in `/tmp/p312`, outside the repository.

Two build failures were hit and fixed, both mine: `no-apps`/`no-docs` are not
valid OpenSSL 3.0 options; and static `libz`/`libcrypto` must be `-fPIC` to link
into CPython's shared extension modules.

## B. Canonical Toolchain (reproduced exactly)

| Component | Project-declared | Used here |
|---|---|---|
| Python | 3.12 | 3.12.15 |
| Lint | `ruff==0.14.0` (`ci.yml:53`) | 0.14.0 |
| Types | `mypy==1.8.0`, `mypy.ini`, scoped `shared/ app/integration/` | identical |
| Test deps | `requirements-ci.txt` | identical |
| Test env | `DATABASE_URL=sqlite+aiosqlite:///:memory:`, `SECRET_KEY=test-secret-key-for-ci-pipeline-secure-length`, `ENVIRONMENT=testing`, `LLM_MOCK_MODE=1`, + dummy Supabase/recovery vars | identical |
| Monolith cmd | `pytest tests scripts/ci --ignore=tests/microservices …` | identical (deselects omitted deliberately, to see raw truth) |
| Microservices cmd | `pytest tests/microservices microservices …` | identical |

**A toolchain mistake I made and corrected:** I first installed
`requirements.txt`, but CI installs `requirements-ci.txt`. The former's floating
`langgraph>=0.2.39,<2.0.0` resolved to langgraph 1.2.2 + checkpoint 4.2.0, while
`requirements-ci.txt` pins `langgraph-checkpoint>=2.0.0,<3.0.0` — holding
langgraph at 1.1.10, a *different engine*. This produced **12 false failures**.
After installing the correct file they all passed. The pin comment in
`requirements-ci.txt` warns about precisely this, twice, by commit SHA.

## C. Full Test Collection — RUNTIME VERIFIED

| Stage | Collected | Collection errors |
|---|---|---|
| First attempt (no `_ctypes`) | 7,152 | 24 |
| After completing the interpreter | **7,347** | **0** |

All 24 errors were one environment cause: `psycopg` and `fsspec` import `ctypes`
at module import time. **Zero collection errors are attributable to the
repository.**

## D. Full Test Results — RUNTIME VERIFIED

**Monolith job** — `tests scripts/ci`, no deselects, 30m18s:

```
5,971 passed · 19 failed · 6 skipped · 11 errors
```

**Microservices job** — `tests/microservices microservices`, 4m38s:

```
1,250 passed · 3 failed · 3 skipped
```

Classified as the mission requires — *not* collapsed into "tests failed":

| Category | Count | Detail |
|---|---|---|
| ENVIRONMENT FAILURE (mine) | 12 | 9 × `test_graph_shards_d262`, 2 × `test_microservice_contracts[planning]`, 1 × `test_check_no_double_encoded_frames` — all from the wrong langgraph engine. **All pass on the corrected toolchain (152 passed).** |
| ENVIRONMENT FAILURE (mine) | 7 errors | `_ctypes` collection errors. **All resolved.** |
| INFRASTRUCTURE FAILURE | 4 errors | `test_microservices_integration.py` — requires a live planning-agent on localhost. Expected; CI does not run these either. |
| KNOWN DEBT (deselected in CI) | 4 + 1 | `test_governance_contracts_any`; 3 × `test_import_conversation` (404≠200); `test_chat_error_handling_with_auth_but_service_error` (documented aiosqlite/daemon-thread race). Consistent with `main`. |
| KNOWN DEBT (deselected in CI) | 3 | All 3 microservices failures are explicitly deselected at `ci.yml:1095,1101,1102`. |
| **REAL ASSERTION FAILURE** | **3** | Governance-registry drift — §F. |

**Net: of 7,347 tests, exactly 3 fail for a repository reason, and all three
share one root cause.**

## E. Runtime Verification of Critical Paths

| Path | Status | Evidence |
|---|---|---|
| Import of `app.main` / full app graph | RUNTIME VERIFIED | 7,347 tests collected, 0 import errors |
| Auth: token issue + verify, both services | INTEGRATION VERIFIED | §G differential, both real implementations in one process |
| Auth negative cases | INTEGRATION VERIFIED | wrong-secret / `alg=none` / malformed / empty / expired all rejected 401 by **both** |
| DB layer (sqlite async) | UNIT VERIFIED | 5,971 monolith tests against `sqlite+aiosqlite` |
| WebSocket | UNIT VERIFIED | starlette TestClient paths pass; live-socket tests deselected by CI |
| Orchestrator / StateGraph | UNIT VERIFIED | 1,250 microservices tests, langgraph 1.1.10 |
| Postgres / Supabase / live LLM | **UNPROVEN** | no network, `LLM_MOCK_MODE=1` |
| Migrations, graceful shutdown, SSE | **UNPROVEN** | not exercised |

## F. Fitness Gate Verification — RUNTIME VERIFIED

All 103 executable gates were run on the real repository:

```
103 executed · 97 pass · 6 fail (exit 1) · 0 crashed
```

Zero crashed — every gate is at least runnable, which is itself a real result.

| Gate | Verdict |
|---|---|
| `check_bundle_budget` | ENVIRONMENT — needs `npm run build --prefix frontend` |
| `check_code_acceptance` | ENVIRONMENT — needs `CODE_ACCEPTANCE_BASE_SHA` (git diff vs base) |
| `check_documentation_contract` | **caused by me** — my recon note's inline PEP 695 example rendered as a markdown link. Fixed; now exit 0 across 52 live documents |
| `check_pocock_gates` | **REAL DEFECT — fixed, §F.1** |
| `check_gate_negative_proof` | **REAL — red on `main`** |
| `check_governance_registry` | **REAL — red on `main`** |

### F.1 `check_pocock_gates` — a gate that could never pass (FIXED)

```python
REPO = pathlib.Path("/home/ubuntu/NAAS-Agentic-Core")   # one developer's laptop
```

Every other gate derives the root from `__file__`. On any other checkout this
gate reports all four Pocock skills and both governance documents as missing and
exits 1 — though **all six exist and are valid**. It went unnoticed because it is
referenced by **no workflow**, and `NEGATIVE_PROOFS.json` records it as
"Newly added, lacking negative proof for now."

This is the purest *decorative gate* in the repository: permanently red, never
executed, guarding nothing.

Fixed (one line) and given the negative proof D-270 L4 demands:

```
intact repository                      -> exit 0   (previously exit 1)
remove .claude/skills/triage/SKILL.md  -> exit 1, "missing file: triage/SKILL.md"
restore it                             -> exit 0
```

The `NEGATIVE_PROOFS.json` row is deliberately **not** added — that ledger is
shrink-only and owned by the project.

### F.2 Two gates red on `main` — one root cause

Reproducible, environment-independent (pure file checks):

```
scripts/fitness/check_gate_negative_proof.py   exit=1
  gates with no registry row: check_hard_currency_engine.py,
                              check_vibe_coding_constitution.py
scripts/fitness/check_governance_registry.py   exit=1
  .memory/ci-gates.md: derived marker stale — expected gates_total=104, file says 102
```

Both follow from the same event: two gates were added without a
`NEGATIVE_PROOFS.json` row and without bumping the derived count. These surface
as the 3 real test failures in §D.

**Not fixed, deliberately.** The correct repair is to add two `frozen_debt` rows,
but that ledger is declared *shrink-only*; an agent silently growing the debt
list is exactly the move the policy forbids. Bumping 102→104 alone would turn the
second gate green while the first stays red — making the count *look* reconciled.
Owner decision.

### F.3 Gate-strength audit

Classified by mechanism: **45 AST/structural · 8 dynamic (import/subprocess) ·
52 text-matching**.

The repository has already performed this audit on itself, and publishes the
uncomfortable number: `NEGATIVE_PROOFS.json` records that of 81 gates measured
2026-08-19, only 30 had a proof that they *block*; today 46 are proven and 56 sit
in declared, shrink-only debt. **I did not need to discover that the guard system
is partly unproven — the repository says so, in writing, with counts.**

### F.4 Mutation test: `check_secret_key_consistency` — STRONG on the instance, FAIL-OPEN on the class

The gate guarding the repository's worst incident was mutation-tested on an
isolated copy. It currently finds 5 real assignments and passes legitimately.

| Mutation | Gate result | Verdict |
|---|---|---|
| M1 — reintroduce `cogniforge-user-service-dev-key`, same syntax | **exit 1**, "DRIFT DETECTED: 2 distinct defaults" | **detects the historical instance** |
| M2 — same drift, but rename `shared_reasoning_secret` → `reasoning_svc_secret` | **exit 0**, "✅ All 4 default(s) agree" | **misses it — and reports success** |
| M3 — remove all assignments | **exit 0**, "Cannot verify consistency statically" | **explicit fail-open** |

M2 is the dangerous one. The gate's regex only matches `shared_*secret` or a
literal `SECRET_KEY="${SECRET_KEY:-…}"`. A routine variable rename makes the
*exact historical bug* invisible, and the gate silently narrows from 5 services
to 4 while printing a green tick. Nothing asserts how many services *should* be
covered.

Two minimal, shrink-only repairs (not applied — owner's call): assert a
**minimum expected count** of guarded services, and make the zero-match branch
**fail closed** instead of returning 0.

## G. Auth Differential Results — INTEGRATION VERIFIED

Both real `AuthCrypto` implementations were loaded into one process, given the
**same** `SECRET_KEY` (which is what D-WS-SECRET-KEY-001's fix mandates in
deployment), and exercised across the full cross-product. No behaviour simulated.

Claims actually emitted:

```
mono.access    type='access'   keys=[exp,iat,is_admin,jti,permissions,roles,sub,type]
mono.reauth    type='reauth'   keys=[exp,iat,jti,purpose,sub,type]
usvc.access    type=None       keys=[exp,iat,jti,permissions,roles,sub]      <-- no type
usvc.reauth    type=None       keys=[exp,iat,jti,purpose,sub]                <-- no type
mono.service   type='service'  keys=[exp,iat,sub,type]
```

Verification matrix (shared key):

| token | monolith as ACCESS | monolith as REAUTH | user_service verify |
|---|---|---|---|
| `mono.access` | ACCEPT | reject 401 | ACCEPT |
| `mono.reauth` | reject 401 | ACCEPT | **ACCEPT** |
| `usvc.access` | ACCEPT | reject 401 | ACCEPT |
| `usvc.reauth` | **ACCEPT** | reject 401 | **ACCEPT** |
| `mono.service` | reject 401 | reject 401 | **ACCEPT** |

Negative cases — **both implementations reject all of them** (401): wrong secret,
`alg=none`, malformed, empty, expired. Core signature hygiene is sound in both;
this is **not** a signature-verification weakness.

**Verdict: (C) dangerous behavioural divergence.**

1. `user_service` emits **no `type` claim at all** — the D-236/ISS-152 contract is
   simply absent from the fork.
2. `user_service.verify_jwt()` has **no `expected_type` parameter**; it is the bare
   `jwt.decode` that D-236 names as the original defect. It therefore accepts
   reauth tokens and the monolith's internal service token as access tokens.
   (`app/services/auth/service.py:556` passes `expected_type`; the fork's
   `verify_access_token` at line 408 cannot.)
3. **A `user_service`-issued reauth token is accepted by the monolith as a full
   access token.** The monolith's deliberate backward-compatibility clause —
   `type is None and expected_type == ACCESS` → accept — catches it.

### Why this survived a correct test suite

Two tests in `tests/security/test_login_failed_regression.py` both pass and are
both right:

- `test_a_reauth_token_is_rejected_as_an_access_token` — proves the dangerous
  direction is closed, but only for a **monolith-minted** reauth token, which
  carries `type`.
- `test_legacy_tokens_without_a_type_still_authenticate` — explicitly asserts a
  `type`-less token **is** accepted as access.

`user_service` mints `type`-less reauth tokens, which land in the second test's
permissive branch. Each test is correct; the **composition** is unsafe. No test
mints with one implementation and verifies with the other.

### A compatibility shim that became load-bearing

`app/services/boundaries/auth_boundary_service.py:191` tries `user_service` first
on every login — unflagged — and returns its `access_token` verbatim. That token
has no `type`. So the "graceful degradation for pre-D-236 tokens" clause is **not
legacy-only: it is the live interop path for every login routed through
user_service.** Removing it would break login. The same clause is what lets a
reauth token pass as an access token.

**Severity, stated precisely (no overclaim):** this is **not** an authentication
bypass — every accepted token is validly signed, so the holder already
authenticated. It is a **type/scope confusion**: a step-up re-authentication
proof (10 min in production) is usable as a general access token, and
`user_service` enforces no token type whatsoever. `mono.service` (`sub:"monolith"`)
being accepted by `user_service` is real but likely inert downstream, since
`"monolith"` resolves to no user — **UNPROVEN either way; not chased.**

Reproduce: `/tmp/auth_differential.py` (experiment, deliberately not added to the
repository — see §O).

## H. Historical Incident Reconstruction — D-WS-SECRET-KEY-001

| | |
|---|---|
| **Trigger** | Codespaces user never set the `SECRET_KEY` secret |
| **Root cause** | `supervisor.sh` gave user-service its own default `cogniforge-user-service-dev-key`; monolith and orchestrator used `dev-secret-change-me` |
| **Mechanism** | user-service signed the JWT; the monolith verified with a different key → signature mismatch → WS close 4401 → relogin loop |
| **Why it hid** | `/me` succeeded (user-service verified its *own* token); only the monolith-side WS decode failed. Partial success masked total divergence |
| **Why gates missed it** | the invariant "all services that share JWTs share a key" existed nowhere as an executable artifact — it lived in a shell default |
| **Fix** | unify on `shared_user_secret`; export `USER_SECRET_KEY`; mirror token caps; add `check_secret_key_consistency.py` + `tests/services/test_secret_key_consistency.py` |

**Class vs instance — the decisive question:**

The fix closes the **instance** (divergent literals in `supervisor.sh`, same
syntax) and is proven to do so (§F.4 M1). It does **not** close the class:

- M2/M3 show the gate is blind to the same drift after a variable rename, and
  fail-open when its regex matches nothing.
- The gate reads **only** `.devcontainer/supervisor.sh`. `docker-compose*.yml`
  (5 files), `.env*` (5 files), and Kubernetes/infra manifests are unexamined —
  the same divergence introduced there is invisible.
- Most importantly, the remedy was **key unification**, which *created the
  precondition* for §G: once every service trusts one key, a token minted
  anywhere is cryptographically valid everywhere, and the only remaining defence
  is the `type` claim — which the fork does not emit or check.

**Two individually-correct fixes composed into a new weakness.** D-236 added the
`type` claim to the monolith; D-WS-SECRET-KEY-001 unified the signing key. Each
is right. Together, with a fork that implements neither half of D-236, they
produce the cross-service type confusion in §G. Neither fix's tests could see it,
because each tested its own service.

## I. False-Confidence Findings

Each claim was actively attacked.

| Claim | Verdict | Evidence |
|---|---|---|
| "The gates protect the architecture" | **PARTLY DISPROVEN** | `check_pocock_gates` was permanently red, in no workflow, guarding nothing (§F.1); `check_secret_key_consistency` is fail-open on its own class (§F.4). The repo already publishes that 56/103 gates lack a blocking proof |
| "The auth copies cannot drift dangerously" | **DISPROVEN** | §G: executable proof of cross-service type confusion |
| "The tests detect real regressions" | **MOSTLY UPHELD, with a seam** | 7,347 tests, 3 real failures, and the governance gates caught live drift. But §G shows two correct tests composing into a blind spot |
| "The service boundary is enforced" | **UPHELD** | `check_no_app_imports_in_microservices` + `check_no_cross_service_imports` pass on 3.12. The *import* boundary holds — which is exactly why logic is duplicated |
| "The documented runtime is reproducible" | **UPHELD, expensively** | 3.12 + `requirements-ci.txt` reproduces CI faithfully; but it took a from-source CPython build. No lockfile exists (`uv.lock` is 52 bytes); floating pins cost me 12 false failures |
| "Critical workflows really work" | **PARTLY UPHELD** | unit/integration yes; Postgres, live LLM, migrations UNPROVEN |
| "Health checks represent real health" | **UNPROVEN** | not exercised |
| "The E2E suite distinguishes success from canned failure" | **UNPROVEN** | live E2E needs a running stack |

## J. PROVEN

1. CPython 3.12.15 reproduces the declared runtime; **7,347 tests collect with 0 errors**.
2. Monolith **5,971 passed**; microservices **1,250 passed**.
3. Exactly **3** tests fail for a repository reason, from **one** root cause (§F.2).
4. `ruff==0.14.0` check + format green; `mypy==1.8.0` green on its 73-file scope.
5. **97/103 gates pass; 0 crash.**
6. `check_pocock_gates` was permanently broken; fixed and negative-proven.
7. `check_secret_key_consistency` detects the historical instance (M1) and misses the class (M2/M3).
8. **Cross-service JWT type confusion exists and is reachable** (§G).
9. Both auth implementations correctly reject wrong-secret, `alg=none`, malformed, empty and expired tokens.
10. The monolith's "legacy token" clause is load-bearing for live cross-service login.

## K. UNPROVEN

- Any behaviour requiring Postgres/Supabase, a live LLM, or a running service mesh.
- Migrations, graceful shutdown, SSE, health-check fidelity, live WebSocket.
- Whether `mono.service` acceptance by `user_service` is exploitable downstream.
- Whether the 52 text-matching gates are fail-open like §F.4 — **only one was mutation-tested**.
- Whether the 4 deselected/known-flaky tests hide real defects.
- Performance, concurrency, memory behaviour under load.

## L. CONTRADICTED

- *(prior report)* "37 files have syntax errors" — environment artifact, retracted.
- *(prior report)* "`.gitignore` hides the source tree from Ruff" — my flag error, retracted.
- *(this session)* "19 monolith failures" — **12 were my dependency resolution**; corrected to 3.
- *(this session)* "24 collection errors" — **all mine** (`_ctypes`); corrected to 0.
- *(this session)* `check_pocock_gates` "missing skill dirs" — the gate was wrong, the files exist.
- *(hypothesis, withdrawn)* that the internal service token carries `role: ADMIN` — it carries `sub:"monolith"`; the comment described the *historical* payload.

**Six corrections, five of them to my own claims.** The pattern is stable: the
first reading of an unfamiliar system is usually a reading of one's own
environment.

## M. Environment Limitations

- No Docker/Compose/devcontainer → the project's own container path is untested here.
- No Postgres/Redis/Supabase → no real persistence evidence.
- `lzma`/`bz2`/`readline` absent from the built interpreter (unused by the suite).
- `sqlite3` is pysqlite3-binary's module (SQLite 3.51.1), not a stock build.
- No lockfile exists, so "the" dependency set is a resolution, not a fact.
- 2 CPU cores: the monolith suite takes 30 min; coverage (`--cov-fail-under=73`) was not run.

## N. Remaining Risks

1. **Cross-service JWT type confusion** (§G) — highest. Unguarded by any test or gate.
2. **The `type is None` compatibility clause is permanent**, not transitional, and cannot be removed without breaking login.
3. **Governance registries drift from reality** (§F.2) — the ledger system works; the update step is manual and was skipped.
4. **51 other text-matching gates may be fail-open**; one of two tested was.
5. **No lockfile** — floating pins cost me 12 false failures; they can equally produce false *greens*.
6. **`check_secret_key_consistency` covers one file**; compose/env/infra are unguarded.

## O. Recommended Next Experiment

**One experiment, smallest first.** Before any gate, before any de-duplication:

> Add a single differential test that mints a token with one implementation and
> verifies it with the other, across all four token kinds — the matrix in §G,
> as a committed test.

Why this and nothing bigger:

- It converts §G from a report into a **permanent executable fact**, in the
  repository's own idiom, and gives the auth seam its first negative proof.
- It answers the open design question — *should* `usvc.reauth` be accepted as
  access? — by forcing someone to write the expected value down.
- It does **not** pre-commit to a fix. Three candidate repairs exist (emit `type`
  in the fork; add `expected_type` to the fork's verify; narrow the monolith's
  legacy clause to exclude tokens carrying `purpose`), and the third is the only
  one that is backward-safe *and* closes the hole. Choosing between them without
  the test first is the "assume → rewrite" path the mission forbids.

Explicitly **not** recommended now: de-duplicating the forks (the microservices
constitution forbids the import that would remove them); a parity gate over all
55 drifted files (would turn CI red on a policy nobody has agreed); editing
`NEGATIVE_PROOFS.json` (shrink-only, owner's ledger).

Deferred, in order: (2) mutation-test the other 51 text-matching gates, starting
with the parity family; (3) commit a lockfile; (4) reconcile the governance
registries; (5) obtain Postgres to lift §K.

---

## Changes made this phase

Two commits, each independently justified, each verified before committing:

1. `dcfe978` — one-line ruff `I001` fix (restores the green lint gate on `main`).
2. `5226c80` — `check_pocock_gates` repo-root derivation + the documentation-contract
   violation **I introduced** in the recon note.

No gate weakened, no test modified, no requirement downgraded, no application
code touched. The 3 real governance failures (§F.2) and the auth finding (§G) are
reported, **not** silently repaired, because both require an owner's policy
decision.
