> **أرشيف — لقطة مؤرَّخة (D-188):** هذا تقرير المرحلة 0 (بروتوكول المالك Ω∞ — قراءةٌ فقط) كما سُلِّم للمالك في 2026-10-02.
> الحقيقة الحيّة لا تعيش هنا: القرارات في `.memory/decisions.md` · الحالة التشغيلية في `.memory/runtime_truth.md` · الحقيقة التجارية في `docs/commercial/outreach/CONTACT_LEDGER.csv`.
> الفحص أُجري على الالتزام `359d4e3458e47688aee53c04c0f1380df20c4902` — الأرقام صحيحة عنده وتتقادم بعده.

# PROJECT SOVEREIGN FORENSIC REPORT — PHASE 0 (READ-ONLY)

**Date:** 2026-10-02 · **Snapshot:** commit `359d4e3458e47688aee53c04c0f1380df20c4902` (branch `arena/01a0fc8d-naas-agentic-core`, branched from `main`)
**Method:** Full-tree read-only inspection. No file modified, nothing committed, nothing pushed, no PR opened. This report file is the **only new artifact** (untracked; delete it if a zero-delta audit trail is required).
**Executor:** Agent (Arena.ai Agent Mode) executing the Sovereign Ω∞ protocol, §38.

**Evidence legend used throughout** (per §6, never promoted):
`RUNTIME FACT` (executed in this session) · `CI RESULT` (workflow file proves enforcement) · `REPO FACT` (file/symbol verified on disk) · `DOC CLAIM` (documented, not independently verified) · `EXTERNAL CLAIM` (external fact cited in repo docs, not re-verified here) · `UNKNOWN`.

**Scope limits (stated honestly):**
- This clone is **shallow (1 commit)**. All historical claims (PR #2529, merged red gates, prior states) are `DOC CLAIM` — they cannot be re-verified from local git history.
- The full test suite and CI were **not executed** (dependencies not installed in this session; a full run is a Phase 4 activity). Runtime evidence in this report comes from code reading plus two read-only CLI probes.
- No secret values were reproduced anywhere in this report (§8). Only type/location/class/required-action.

---

## A. WHAT THE PROJECT REALLY IS

A **solo-founder, AI-agent-co-built venture** (owner-identified in `دليل-التشغيل-الميداني-والإنزال-التجاري-للعملة-الصعبة.md`; repos mirrored between `Houssam-lab/NAAS-Agentic-Core` and `bakabala27-svg/NAAS-Agentic-Core` — `REPO FACT`: `.github/workflows/repo-sync.yml`) that, over ~10 months (`.memory/decisions.md` D-001→D-305; `.memory/issues.md` ISS-001→ISS-214), has produced **four stacked identities**:

1. **An Algerian Baccalauréat "Cognitive Lab" platform** — engine **CogniForge**, product **ETAALIM.AI** (`README.md`, `CLAUDE.md`). ~204K LOC of application code (`app/` 121,232 + `microservices/` 70,975 + `frontend/` 12,027 — `REPO FACT`, counted). **Frozen by owner decision D-300 (2026-09-29).**
2. **A foreign-currency ("العملة الصعبة") commercial program** — market research corpus (7 root Arabic research docs ≈ 260KB, `studies/`, `docs/sovereign-atlas/` 18 docs, `docs/research/`), plus a **working delivery wedge**: FR/BE e-invoicing referential-cleansing tools (`tools/hard_currency_engine/` — 1,965 LOC of money-path code per `docs/commercial/CODEBASE_ECONOMIC_AUDIT_2026-09-29.md` §6) and an admin-only **Hard Currency Center** in the monolith (D-305, 2026-10-01).
3. **A NAAS Verification Layer** (`naas_verifier/`, 1,929 LOC) — trajectory-based verification of agent behavior, AR/FR corpus derived from real production incidents. `EXPERIMENTAL / FROZEN` per D-300.
4. **A governance apparatus of unusual size**: 103 fitness gates (`scripts/fitness/` — `REPO FACT`), 24 files named "constitution", 567 markdown files, 8.9MB `docs/`, 2.8MB `.memory/`, 15 workflow files, 12-job required CI (`REPO FACT`).

Total: 2,288 Python files, 373,342 Python LOC including tests (96,852 LOC of tests — `REPO FACT`).

**The economic truth (`REPO FACT` + `DOC CLAIM`):** zero revenue ever; exactly **one** outbound commercial contact in history (`docs/commercial/outreach/CONTACT_LEDGER.csv`, 1 data row); all four NAAS gates `ABSENT` (`docs/governance/GATE_LEDGER.json`).

## B. WHAT IT CLAIMS TO BE

- `README.md` (head): "A learning engine that measures what a student actually knows — and refuses to hand over the answer… built for the Algerian Baccalauréat, engineered to the standard the US and EU markets audit for." Claims: zero LLM in the number path, answers withheld by law (citing Bastani et al., PNAS 2025), every capability gated by import+call-chain+runtime evidence, 39 skills, 37-concept curriculum, 13 declared microservices, API-first parity 15/15, 12 required CI jobs (`CI RESULT`: verified the `required-ci` `needs` list in `.github/workflows/ci.yml`).
- `CLAUDE.md` (173KB, "operational constitution"): "The system is not a Chat Tutor. It is a Cognitive Lab." Pedagogical doctrine, §0 core laws, D-001→D-305.
- `spec.md`: an API-first microservices simplification **target** — explicitly "an aim, not current reality".
- `docs/FOREIGN_CURRENCY_DOCTRINE.md`: revenue must be **hard currency from an institutional customer outside Algeria**, via 4 legal channels, with prohibitions K1–K4 (no crypto, no sale without bank project declaration, no personal accounts, 306-day repatriation limit).
- `docs/naas/ONE_PAGER.md`: NAAS verification layer — explicitly labelled "internal preparation document. Not sent to anyone."

## C. WHAT USERS ACTUALLY EXPERIENCE

- **Students (the platform's nominal users):** a WebSocket Arabic chat tutor (`/api/chat/ws`), one terminal frame per turn, deterministic pre-empts, Socratic withholding. **But no real student population is evidenced**: ISS-203/ISS-204 record that **CI wrote 96.4% of production messages** and CI ran against the production database (`DOC CLAIM`, `.memory/issues.md` ISS-203/ISS-204; contained by D-299).
- **The admin/owner (the only proven human user):** sees "ETAALIM · CLI" with an admin menu containing the **Hard Currency Center** (D-305: 25 value-chain paths, e-invoicing audit upload/clean/CSV download with BOM, CBAM code explorer, red-team class registry) — admin-only, `require_roles(ADMIN_ROLE)` on all 6 endpoints (`REPO FACT`: `app/api/routers/hard_currency.py`; frontend gate `user.is_admin` in `frontend/app/components/CogniForgeApp.jsx:431`, loaded via `next/dynamic`).
- **Prospects (the intended customers):** one FR accounting firm received one email (2026-09-22, free 20-file diagnostic offer). No reply (`REPO FACT`: ledger row).

## D. WHAT THE CODE ACTUALLY DOES

- **Monolith** (`app/`, FastAPI :8000): routers (chat WS-only by design), 39-skill registry, deterministic engines (probability, foundations, reasoning), BKT/FSRS, tutor_state append-only. Single writer; one terminal frame.
- **Orchestrator-service** (`microservices/orchestrator_service/`, 42,662 LOC — `REPO FACT`): LangGraph "single brain" (Supervisor → GeneralKnowledge → Validator, `graph_ready=true` proven live 2026-10-01 per `.memory/runtime_truth.md` D-305). It is effectively a **second, smaller monolith** (the Ω∞ §17 risk, realized).
- **13 declared microservices** (`config/microservice_catalog.json`) + api_gateway; compose topology (b) is the strangler target with per-service Postgres and the monolith deliberately absent; **topology (a)** (supervisor, monolith+orchestrator) is what actually serves today (`README.md` §04, `.memory/runtime_truth.md`).
- **The money path** (`tools/hard_currency_engine/`): `france` / `belgium` / `crm` subcommands. `RUNTIME FACT` (this session): `python3 -m tools.hard_currency_engine.cli --help` executes cleanly (stdlib, no keys, no LLM). France validator: Luhn/SIREN/SIRET keys, TVA key computation, postal-code zero-strip, SIRENE online lookup (opt-in `--online`), duplicate detection by identifier (D-300/ISS-205), €50/invoice fine wording with cap and dates. Belgium: BCE modulo-97, VAT, Peppol ID formatting (explicitly **does not verify actual registration** — documented limit).
- **naas_verifier** `RUNTIME FACT` (this session): `python3 -m naas_verifier.cli --help` executes; the help text itself carries the credibility limit (measures reference targets, not real third-party systems).
- **Governance execution**: 103 gates run in the `guardrails` job (9 grouped steps — `REPO FACT` in `ci.yml`); scorecard is **derived** from the ledger, never hand-typed (`scripts/research/hard_currency_scorecard.py` + sha256 of source in `docs/commercial/HARD_CURRENCY_SCORECARD.json`); a **research-freeze gate** (`scripts/fitness/check_outbound_before_research.py`) blocks new research docs that don't ship with a new outbound contact row (D-297).

## E. WHAT THE DOCUMENTATION ACTUALLY KNOWS

Institutional memory of genuinely high quality and unusual honesty:
- `.memory/decisions.md` (1MB, D-001→D-305) and `.memory/issues.md` (582KB, ISS-001→ISS-214) — append-only, including failures and root causes.
- `.memory/runtime_truth.md` — the proof-ladder lock (ACTIVE requires import + call chain + runtime evidence), with dated live proofs.
- Status documents per subsystem (`*_truth.md` ≈ 30 files), each naming its enforcer gate.
- `docs/commercial/` — the commercial ledger, offer catalog, opportunity dossier, economic audit, outreach kits.
- `docs/governance/` — GATE_LEDGER, state machine, negative proofs, registries.
- Weakness: the corpus is **oversized relative to the venture's stage** (62% of added lines in the two weeks after the initial import were research docs vs 8% sellable tools — measured in D-297), which is exactly why the research-freeze gate now exists.

## F. WHAT THE MARKET EVIDENCE ACTUALLY SHOWS

- **External legal deadline (`EXTERNAL CLAIM`, cited with sources in D-300/D-304):** France e-invoicing reception mandatory since 2026-09-01; PME issuance 2027-09-01; €50/invoice non-compliance fine capped €15,000/year (Finance Law 2026). This is the demand clock behind the wedge.
- **Target lists:** `docs/commercial/FR_EINVOICING_TARGETS_2026-09-21.csv`, `MASTER_CLIENT_TARGETS_GLOBAL_2026.csv`, `FR_EINVOICING_TARGET_CONTACT_DOSSIER.md`, prospect intelligence deep-dives.
- **Market sweeps:** `studies/market-first-sales-reality/` (7 rounds + evidence CSVs), sovereign atlas of Algeria (18 sector docs), global compelled-buyer atlas (`أطلس-الدافعين-المجبرين-عالميا.md`).
- **Hard boundary:** all of the above is desk research. **Zero buyer conversations** are recorded. The single warm target (Balagué Expertise) did not reply, and the planned follow-up call was not made (owner-confirmed 2026-09-28 — `DOC CLAIM`, D-297 context; ledger note).

## G. WHAT THE COMMERCIAL SYSTEM ACTUALLY PROVES

`REPO FACT` — `docs/commercial/outreach/CONTACT_LEDGER.csv` (1 row) and the derived `HARD_CURRENCY_SCORECARD.json` (source sha256 pinned):

| Funnel | Value |
|---|---|
| contacts_sent / entities | **1 / 1** |
| replies / samples / quotes / deposits / payments | **0 / 0 / 0 / 0 / 0** |
| paid customers (foreign or domestic) | **0** |
| settled revenue EUR | **0** |
| recurring revenue / margin / retention | `null` (no basis — honest nulls, not zeros) |

`GATE_C_COMMERCIAL = ABSENT` (blocks PMF and revenue claims); `GATE_0_LEGAL = ABSENT` (no legal opinion recorded); `GATE_A/B = ABSENT` (NAAS). **No offer has ever risen above `PROPOSED`** (`docs/commercial/OFFER_CATALOG.json` — 8 offers, all `PROPOSED`, all with empty `evidence_paths` except status discipline itself).

## H. ALL ACTIVE PRODUCT THESES

| # | Thesis | State (evidence) | Customer contact | Payment evidence |
|---|---|---|---|---|
| 1 | **ETAALIM.AI** — Algerian Bac cognitive tutor (DZD, B2C/D2C parents) | **FROZEN by D-300** (`.memory/decisions.md` D-300; code+tests+CI retained, no feature work) | none evidenced (production data was CI-written, ISS-203/204) | €0 / 0 DZD |
| 2 | **fr-be-einvoicing-referential-cleansing** — manual service delivered by owner with `tools/hard_currency_engine` | **SOLE ACTIVE THESIS per D-300** (owner's written decision 2026-09-29) | 1 email sent, 0 replies | €0 |
| 3 | **NAAS Verification Layer** — trajectory verification for AR/FR agents | `EXPERIMENTAL / FROZEN` (D-300); gates ABSENT; measured 100% vs 10% baseline **on reference targets only**; one external OSS target diagnosed (better_profanity `Lo` class gap — `docs/naas/ONE_PAGER.md` §4, with stated limits) | none ("internal preparation document") | €0 |
| 4 | OFFER_CATALOG other 6 lines (AI red-teaming AR/FR, niche RLHF data, on-prem energy AI, physics-informed AI, formal verification, EU AI Act compliance, high-RPM affiliation) | `PROPOSED`, no work | none | €0 |
| 5 | CBAM / ZATCA / EAA export services | **WITHDRAWN** from customer path (D-297 §4: invented 0.025 coefficient ≈71×, fake hash "repair", legal declaration risk) | none | €0 |
| 6 | Outcome Attestation (`docs/reconstitution/` 12 docs) | `HYPOTHESIS`, frozen | none | €0 |
| 7 | Hard Currency Center (D-305 admin workbench) | Active as **internal tooling for thesis 2**, not a product | — | — |

## I. PRODUCT CONFLICTS

1. **The constitution does not know the product decision.** `CLAUDE.md` (the "operational constitution every contributor and agent inherits") contains **zero references to D-300** (`REPO FACT`: grep). A fresh agent loading the cognitive path inherits the *pedagogical* mission, not the hard-currency priority. `README.md` likewise sells the education platform as the product.
2. **Three names, one repo:** `NAAS-Agentic-Core` (repo) vs **CogniForge** (engine) vs **ETAALIM.AI** (product) vs the now-primary **hard-currency service** which has no product name at all.
3. **The wedge lives inside the frozen platform.** D-300 froze the platform, then D-305 (one day later) added an admin UI + routers + services to the monolith as a "limited exception". Legitimate, but it is the first bend in the freeze and must not become the pattern.
4. **spec.md (API-first microservices target) vs D-300** ("no service migration, no orchestrator folding, no table-ownership convergence while frozen") — two architecture doctrines with opposite momentum; the freeze wins by decision, but the documents don't say so at the point of reading.

## J. DATA OWNERSHIP CONFLICTS

`REPO FACT` (duplicate ORM table definitions):
- `users` ×3: `app/core/domain/user.py`, `microservices/orchestrator_service/src/core/domain/user.py`, `microservices/user_service/models.py`
- `missions`, `mission_plans`, `mission_events`, `mission_outbox` ×2 (monolith + orchestrator)
- `customer_messages` / `customer_conversations` / `admin_messages` / `admin_conversations` ×2 (monolith + orchestrator)
- `roles`, `permissions`, `role_permissions`, `user_roles`, `refresh_tokens`, `password_resets`, `tasks` ×2

The docs frame this as deliberate vendoring ("shared logic is vendored with a parity gate rather than imported" — `README.md` §04; `check_*` gates). Under Ω∞ §16 this remains **duplicated truth with parity enforcement instead of single ownership** — an architectural defect by the directive's definition, consciously deferred by D-300 ("those are phases 5–6 and are not scheduled unless the freeze is lifted"). Classified correctly in-repo; recorded here as a standing conflict, not an emergency.

## K. STATE CONFLICTS

- **Chat persistence** is split-brain-managed: monolith writes the user message at WS entry; assistant persistence coordinated via an explicit `persisted` flag to prevent dual writes (`README.md` §04; `CLAUDE.md` §6.5) — mitigated, not owned-once.
- **Two state stores for one conversation:** monolith `tutor_state` (append-only) vs orchestrator LangGraph **Postgres checkpointer** (`checkpointer_backend=postgres`, runtime_truth D-305).
- **Live runtime contradiction (carried in the lock):** `CONVERSATION_SERVICE_URL` defaults to the Docker name `http://conversation-service:8010` (`microservices/orchestrator_service/src/api/conversation_store.py:31`) → in the actually-serving topology (a) every history fetch fails with `[HISTORY_RETRY] Name or service not known` on **every turn**. Classified `PARTIAL`, reported, deliberately not fixed in that change (`DOC CLAIM`, runtime_truth D-305).

## L. DOCUMENTATION CONTRADICTIONS

1. README presents the platform as *the* product; D-300 froze it (see I.1). **Document drift at the highest-authority layer.**
2. README §12 roadmap M0→M11 for the pedagogical engine + parallel tracks — all inoperative while frozen; no banner says so.
3. `docker-compose.yml` = strangler destination (monolith absent, 3 gates prevent re-adding); `docker-compose.legacy.yml` + supervisor = what runs. Correctly documented as two topologies, but a newcomer cannot tell which is *current* without reading `.memory`.
4. Root-level scratch/relic files contradict the documentation-contract discipline: `pr_description_test.md`, `pr_description_test2.md`, `SYNC_TEST_MARKER.txt`, `fix.py`, `test_validate.py`, `test_visual_pedagogy_ui.py`, `live_db_restructure.py`, `.magic_urls`, 52-byte `uv.lock` (`REPO FACT`).
5. A 9.4MB PDF (`Introduction to Agents.pdf`) is committed at root — binary ballast in a repo that prides itself on low-entropy memory.

## M. RUNTIME CONTRADICTIONS

- Conversation history retry failure on every turn (K, above) — **live, known, open**.
- `temporal` server proven in CI; **no workflow has ever executed** (README §09 table, `DOC CLAIM`).
- Vector retrieval DORMANT (embeddings/rerankers present, zero request-time calls).
- OpenRouter free-tier 429s (ISS-206): CI red derived from provider capacity, not code; deferred by D-301 until a paid key.
- ISS-213 (`OPEN`): `tests/conftest_support/policy.py` policy hooks silently unregistered since D-258 — a *warning guard and test-ordering guard that are dead while appearing alive*.
- ISS-209 (`OPEN`): response guard erases the parenthesized scientific term («قانون أوم ( ) هو…»).
- ISS-210: three active admin accounts in production (two ownerless) + a Codespaces script rewriting the admin password on every boot — fixed in code+prod by D-305, **awaiting one production boot to close** (`DOC CLAIM`).

## N. TEST/REALITY CONTRADICTIONS

- **ISS-214 (fixed at this HEAD):** the existing auth-boundary test fed `get_me` a hand-written dict containing `is_admin` — a shape the real user-service never returns — so the test false-passed while every admin was rendered as a student. Classic false-pass, root-caused and fixed with service-shaped payloads (`tests/services/test_auth_boundary_admin_flag.py`, red-before proof).
- **ISS-203:** the live answerability metric counted an *apology* as a successful answer; `required-ci` was red on `main` for four pushes. Fixed in code by D-298. The repo itself states the Ω∞ §20 principle: "a test that can certify an apology as a successful answer is itself broken."
- **E2E blind spot (ISS-214 lesson):** the D-305 live journeys ran *without* user-service, so `/me` fell back to the local path — coverage that proved less than it appeared to.
- **Process failures recorded:** PR #2526 merged before CI finished (red); PR #2529 merged with the packet-description gate red (empty `HUMAN:` section) — `DOC CLAIM`, economic-audit §6. Gates exist; merge discipline is human.
- CI wrote 96.4% of production messages and wrote to the production DB (ISS-203/204) — the deepest test/reality inversion in the project's history; contained by D-299 (live-e2e now on ephemeral Postgres in the runner).

## O. FALSE-PASS / FALSE-FAIL RISKS

| Risk | Class | Status |
|---|---|---|
| Secret-capture parity gate checks **binding, not value** (wrong value passes) | False-pass, documented | `.memory/secret_capture_truth.md` §3 row 2 — honest, unfixed by design |
| Research-freeze gate ran in CI **without a basis** (read clean tree, always green) — ISS-208 | False-pass | Fixed in PR #2533 (`DOC CLAIM`) |
| Coverage gate `--cov-fail-under=73` measures a **frozen** platform | Measurement drift | Accepted while frozen |
| Scorecard derived + sha-pinned; ledger closed action-set | False-pass resistant | Strong design (`REPO FACT`) |
| Canary range deterministic (190 probes, `--check` byte-identical rerun), 19 turns honestly flagged unmeasured | Honest measurement | Strong design |
| Gates that parse files must fail on parse error (`check_gate_parse_honesty`) | Anti-blindness | Enforced in CI |
| Negative proofs registry (8 entries) for gates | Trustworthy verification | Enforced |

## P. ORPHAN CODE

`REPO FACT` (candidates — deletion is an owner decision per audit §5.2):
- `tools/hard_currency_engine/cbam_calculator.py`, `zatca_validator.py`, `eaa_scanner.py` (996 LOC) — withdrawn from the customer path (D-297 §4), **wrong-number risk if re-run on client data**.
- `tools/fr_einvoicing/` (700 LOC) — superseded by `france --online`; no importer.
- `tools/cbam/cbam_savings_calculator.py` (205 LOC) — carries the withdrawn 0.025 coefficient.
- `contracts.py` unused types (file itself now has a live consumer: `flag_duplicate`).
- Root scratch: `fix.py`, `live_db_restructure.py`, `pr_description_test*.md`, `SYNC_TEST_MARKER.txt`, `test_validate.py`, `test_visual_pedagogy_ui.py`.
- `frontend/verify_admin_mission_selector.py`, `frontend/verify_mission_selector.py` — stray verify scripts in a Next.js tree.

## Q. ORPHAN DOCUMENTATION

- 7 root Arabic research monoliths (≈260KB) + `docs/sovereign-atlas/` (18 docs) + `studies/` (8 dirs, 5 with code) + `docs/research/` (~40 files) — the 43-day research loop that D-297 froze; still on the active cognitive path (root level) rather than archived.
- `REPORT-D261.md`, `docs/FINAL_REPORT_*_AR.md` — dated snapshots at live locations (D-188 discipline says dated tables belong in archive).
- `docs/archive/` exists and is used — the split is defined but not applied to the above.
- `Introduction to Agents.pdf` (9.4MB binary).

## R. DUPLICATION

- Validator helpers copy-pasted verbatim: `strip_accents`, `norm`, `_read_csv_lines_multi_encoding` in both `france_validator.py` and `belgium_validator.py` (`REPO FACT`, line numbers captured). Audit prescribes unification **after first payment**.
- ORM table definitions duplicated (J above) — parity-gated, by design.
- Historical: three competing curriculum concept definitions (unified, README §05); intent keyword lists duplicated in 7 places (unified, `check_intent_single_source`).

## S. HIDDEN COUPLING

- **Documentation-as-code coupling:** 103 gates read docs as data; every diff updates an acceptance packet. Change amplification is deliberate (drift control) but expensive — the audit calls it "cost of speed" debt (§4 item 13).
- **CI ↔ production coupling** (now severed by D-299 — ephemeral Postgres in runner).
- **Mirror coupling:** two GitHub repos sync on every push to `main` (`repo-sync.yml`, `main` only, measured refs outside contract).
- **Frontend ↔ user-service `/me` coupling:** the ISS-214 class — a silently-shaping response contract.
- **Monolith ↔ orchestrator:** service JWT auth + HTTP; orchestrator ↔ conversation-service via env URL (broken default, K).

## T. TECHNICAL DEBT

Frozen-debt registers exist and mostly read empty (by design). Material items: 103-gate maintenance per diff; 24 constitutions to keep mutually consistent; duplicated validators (R); duplicated ORM truth (J); conversation-URL default (K); ISS-213 dead hooks; ISS-209 guard bug; free-tier model dependency for the platform (ISS-206); compose-vs-supervisor port divergence (5 services, documented in `docs/architecture/PORTS_SOURCE_OF_TRUTH.json`).

## U. STRATEGIC DEBT

One repository carrying a frozen first act (education platform, no users), an unfunded second act (verification layer, no external validation), and a third act (hard-currency services) that is **all preparation and one email**. The repo's own D-297 diagnosis is exact: 17 "first opportunities" in 43 days, 62% research lines vs 8% sellable tools, one message sent. The research-freeze gate now enforces the cure.

## V. COMMERCIAL DEBT

- **No payment rails operational:** bank EUR-reception question unasked in writing; ANAE registration not started; no Malt/Payoneer (D-297 owner answers).
- **No DPA reviewed** (template exists: `docs/commercial/outreach/templates/DPA_NDA_TEMPLATE_FR.md`).
- **No legal opinion** (`GATE_0_LEGAL = ABSENT`) — blocks external commercial actions.
- GDPR posture: non-EU processor handling EU client referentials — recognized, unmitigated by counsel.
- Algerian accountancy monopoly limit: administrative-data cleansing only (service scope constraint, documented).
- Defensibility: the wedge is copyable; the moat claim is gated (`GATE_B`).

## W. SECURITY RISKS

`REPO FACT` scan (this session, values never printed) + `DOC CLAIM`:

| Item | Location | Exposure class | Status / Required action |
|---|---|---|---|
| Production credentials once committed in a **public** repo; SQL backdoor bridge executing free SQL on production; CI writing to prod DB | ISS-204; bridge retired (`.memory/runbooks/supabase-bridge.md` marked retired; `claude-admin` code replaced by 410-Gone template) | **CRITICAL (historical)** | Contained **in-repo and in-platform** by D-299 (PR #2529). **ROTATION of the leaked production credentials remains an OWNER ACTION — OPEN.** History cleaning not evidenced (shallow clone — `UNKNOWN`). |
| Live-credential scan at this commit | All DSN-shaped strings on disk are placeholders/doc examples (`user:pass@host`, `<…>`, localhost) | None found at snapshot | Continue enforcing `check_no_committed_secrets` |
| Three active production admins, two ownerless; admin password rewritten each Codespaces boot | ISS-210 | High (identity) | Fixed in code+prod by D-305; **close after one production boot** |
| Rate-limited admin upload surface (Hard Currency Center) | `app/api/routers/hard_currency.py` | Mitigated | `_rate_limited` dependency present |
| Guard blindness class | ISS-213 (dead policy hooks), ISS-208 (blind gate, fixed) | Medium | ISS-213 OPEN — owner action to repair |

**Security does not wait for architecture (Ω∞ §34): rotation + verification of ISS-204 closure is the only red-line item in this report.**

## X. CURRENT CUSTOMER STATE

- **Prospects:** 1 entity contacted ever (Balagué Expertise, FR, email 2026-09-22, free-diagnostic offer, no reply; planned call not made). 15 named emails prepared, unsent (`docs/commercial/outreach/ready_to_send/`).
- **Platform users:** no evidence of any real student cohort; production interactions were predominantly CI-generated (ISS-203/204).
- **Readiness:** outreach kits, demo files (manufactured — audit notes the two demo files are fabricated samples, correctly labeled), pricing hypothesis 290–390 €/file, 90–150 €/month monitoring.

## Y. CURRENT REVENUE STATE

**€0 lifetime. DZD 0 evidenced.** Every monetary metric in the scorecard is 0 or honest-null. Funnel conversion rates with zero denominators return `null` with reasons (D-212 discipline). Time-to-first-payment: null — has not happened.

## Z. CANDIDATE PRODUCT THESIS COMPARISON (WAR ROOM)

| Dimension | (1) ETAALIM platform | (2) FR/BE e-invoicing cleansing | (3) NAAS verification | (4) Other catalog lines |
|---|---|---|---|---|
| Target customer | Algerian Bac students/parents | FR/BE accounting firms (5–50 staff) | AI model/product teams (AR/FR) | various |
| Problem | exam performance | referential data errors → rejected e-invoices, €50/fine | unverifiable agent trajectories | various |
| External demand evidence | none paid; free content abundant (their own analysis) | **legal mandate with dates** (EXTERNAL CLAIM, cited) | none; one OSS diagnostic | none |
| Buyer & budget | parents, DZD | managing partner, EUR | platform teams, USD/EUR | unknown |
| Time to first payment | long (launch, trust, DZD micro-payments) | **shortest** (dossier §12: 14-day path) | long (GATE_0–C all ABSENT) | unknown |
| Delivery complexity | high (frozen platform) | **low** (stdlib tool, runtime-verified, manual) | medium (exists, needs third-party target) | high |
| Cost to deliver | high (LLM, infra) | ~zero marginal (no LLM in path — scorecard: `ai_cost_per_customer_eur = 0.0`) | medium | high |
| Trust/compliance | minors, safeguarding | GDPR (non-EU processor), DPA, ANAE cap ≈€32.4k/yr | credibility gates | unknown |
| Technical assets present | 204K LOC | **1,965 LOC working tool** | 1,929 LOC + corpus + gates | partial |
| Customer evidence | none | 1 email, 0 replies | none | none |
| Repeatability | unproven | defined (12h/200 records kill test, monthly monitoring) | unproven | unproven |
| Defensibility | low–medium | low (copyable) | medium if externally validated | unknown |
| Verdict | FROZEN (D-300) | **SOLE ACTIVE (D-300)** | FROZEN (D-300) | PROPOSED, no work |

## AA. PROPOSED ONE PRODUCT

**Ratify — do not re-litigate — the owner's own written decision D-300 (2026-09-29):**

> **Active thesis (sole): `fr-be-einvoicing-referential-cleansing`** — a manually-delivered service for French (then Belgian) accounting firms: cleanse third-party referential CSVs (SIREN/SIRET/TVA/BCE/Peppol, duplicates, postal codes), delivered within 24h by the owner using `tools/hard_currency_engine`, priced 290–390 €/file, recurring monitoring 90–150 €/month. Everything else frozen, one line each.

**Why (evidence):** it is the only thesis combining (1) a verified external legal deadline, (2) a runtime-proven tool (`RUNTIME FACT` this session), (3) a defined pricing hypothesis, (4) a prepared outreach kit, (5) near-zero delivery cost, (6) the shortest path to first payment (dossier §12). All competitors for "active" status have zero customer contact and are already correctly frozen.

**Known weaknesses (from D-300 itself):** low defensibility; ANAE ceiling; GDPR non-EU posture; zero buyer conversations; untested payment rails; manufactured demo files.

**Invalidation (kill conditions, verbatim from dossier §12):** 30 qualified contacts → <3 conversations (channel dead) · 10 conversations → 0 quote requests (offer dead) · 5 quotes → 0 deposit (opportunity unproven) · bank/Malt refusal without alternative (cannot sell) · no payment within 14 days of full seriousness.

**What becomes of the others:** platform stays `FROZEN` (second act, unfrozen only by written decision); NAAS stays `EXPERIMENTAL/FROZEN` until a buyer asks a third-party agent to read it (its own gate machine already encodes the Ω∞ §21 progression: SYNTHETIC → OSS → third-party → paid); catalog lines stay `PROPOSED` with no work; CBAM/ZATCA/EAA stay withdrawn.

## AB. WHAT MUST BE FROZEN (already is, keep it that way)

`app/` + `microservices/` + `frontend/` (199.5K LOC); `naas_verifier`; research-corpus growth (gate-enforced); the 6 catalog lines; Outcome Attestation; **new rule to consider: freeze further growth of the Hard Currency Center itself** — it is internal tooling for a manual service; a UI must not become a second product while the first payment is still €0.

## AC. WHAT MUST BE DELETED (owner decision, per audit §5.2)

≈1,900 LOC of withdrawn/dead money-adjacent code (`cbam_calculator.py`, `zatca_validator.py`, `eaa_scanner.py`, `tools/fr_einvoicing/`, `tools/cbam/`) — the stated reason is sharp: their continued existence keeps open the possibility that a wrong number runs on client data. Plus root scratch files (P) and the 9.4MB PDF (move to release assets). **Recommendation: execute deletions only after first payment or by explicit owner decision, as the audit prescribes** — deletion is not urgent; rotation is.

## AD. WHAT MUST BE PRESERVED

- The **commercial truth system**: `CONTACT_LEDGER.csv` + derived scorecard + research-freeze gate + `check_outbound_before_research` — this is the repo's best institutional machinery.
- `tools/hard_currency_engine` (france/belgium/cli/crm_dispatcher/contracts) + the ledger contract (`shared/research/contact_ledger.py`).
- `.memory/` (decisions/issues/runtime_truth) — the organizational memory, including failures.
- The frozen platform as a whole (asset for a second act; the corpus source for NAAS).
- The subset of the 103 gates that guard the wedge and CI honesty; `GATE_LEDGER` state machine.

## AE. WHAT MUST BE REBUILT (after approval)

1. **The active constitution** — a short document that makes D-300/D-305 the first thing any agent or contributor reads; today the cognitive path still opens with the pedagogical constitution (I.1). CLAUDE.md/README need a single banner-level pointer, not a rewrite.
2. **The outreach habit** — human, not code; the system can measure it (ledger) but cannot perform it.
3. **Payment rails** — bank answer in writing, ANAE, Malt/Payoneer (all owner actions).

## AF. TARGET ORGANIZATIONAL MODEL (mapped to what exists)

| Department | Current home | Verdict |
|---|---|---|
| STRATEGY | `.memory/decisions.md` D-296→D-305 | thin but real; keep |
| KNOWLEDGE | `.memory/` + `docs/` + archive | overweight; freeze-enforced; apply archive split (Q) |
| MARKET | `studies/`, atlas, targets CSVs | complete desk phase; now execution-only |
| CUSTOMER | `CONTACT_LEDGER.csv` | **the binding constraint** — 1 row |
| PRODUCT | `VALUE_CHAIN.json` (25 paths), dossier | adequate for the wedge |
| COGNITION/CHAT | orchestrator + monolith | frozen; owned; correct boundaries documented |
| ENGINEERING | `app/` + `microservices/` | frozen; healthy gates |
| DATA | per-service Postgres (target), duplicated ORM (J) | deferred by decision |
| QUALITY | 103 gates, negative proofs | strong; simplify post-payment |
| SECURITY | secret catalog, ISS-204 containment | **rotation outstanding (W)** |
| OPERATIONS | CI (12 required jobs), compose | strong; merge discipline is human |
| FINANCE | scorecard (derived) | correct, empty — honestly |
| REVENUE | outreach kits, ready_to_send | prepared, unexecuted |
| MEMORY | `.memory/*_truth.md` | exemplary |
| AUDIT | GATE_LEDGER, evidence schema | exemplary |

## AG. TARGET ARCHITECTURE

No change while frozen (D-300 is architecturally conservative and correct): **one deployable serving topology (a)**; wedge = stdlib CLI + CSV in/out with **no platform dependency**; orchestrator folding and table-ownership convergence remain phases 5–6 behind the freeze. Modular-monolith default (Ω∞ §18) is already the de-facto serving reality; the microservice island program pauses with the platform.

## AH. MIGRATION SEQUENCE (proposed, none executed)

1. **Phase 1 (security, owner):** rotate leaked production credentials; verify ISS-210 closure on next production boot; record both in the ledger/issues. *Nothing else in this phase.*
2. **Phase 2 (decision):** ratify D-300 as AA above; write the banner pointer (AE.1) — one PR, gated.
3. **Phase 3 (constitution):** short active constitution (mission, one product, kill list) + move root research monoliths to `docs/archive/`.
4. **Human wedge (parallel, no code):** the 14-day sequence — bank letter, ANAE, Malt/Payoneer, Balagué call, 15 named emails — every action a ledger row the same day.
5. Code deletions (AC) after first payment or explicit owner decision.
6. Platform phases 5–6 only when/unless the freeze is lifted by written decision.

## AI. VERIFICATION GATES (what proves what)

- Existing and trusted: `required-ci` 12 jobs; runtime-truth lock; scorecard derivation (sha-pinned); research-freeze gate; negative-proofs registry; GATE state machine (self-approval forbidden: `issuer`/`reviewer` must be human).
- Gaps to add (post-approval): a cheap CI step that imports and `--help`s the wedge CLI (stdlib, no quota) so the money path can never silently rot; a payment-settlement evidence template (bank statement reference) awaiting the first `PAYMENT_SETTLED` row; closure verification for ISS-204 rotation.

## AJ. HIGHEST-LEVERAGE NEXT ACTION

**Not code.** The evidence is unambiguous: the binding constraint on the mission (hard-currency revenue) is **one unsent batch of emails and one unmade phone call**, preceded by one security action:

1. **Owner, immediately:** rotate the production credentials exposed in ISS-204 and verify it — an EU accounting firm's first due-diligence question to a non-EU data processor is exactly this class of incident; it is both a security red line and the first trust gate of the wedge.
2. **Owner, days 0–14:** execute dossier §12 verbatim (bank question in writing → ANAE → Malt/Payoneer → Balagué call → 15 named emails), every action a `CONTACT_LEDGER.csv` row the same day.
3. **Engineering (small, gated, after approval):** the constitution banner (AE.1) + wedge-CLI CI probe (AI). Nothing else. Per the repo's own rule: **no new code before the first payment except what a real customer sample reveals.**

---

## PHASE 0 STOP CONFIRMATION (Ω∞ §40)

Phase 0 is complete. **No file was modified, no migration started, no product silently chosen (AA ratifies the owner's existing written D-300 rather than replacing it), no commit, no push, no PR.**

Awaiting explicit owner approval before executing any phase. Recommended order: Phase 1 (security containment completion — credential rotation support and verification), then Phase 2/3 (decision ratification + short active constitution), then the human wedge plan.

*Evidence appendix: all file paths cited above were verified read-only at commit `359d4e3458e47688aee53c04c0f1380df20c4902` on 2026-10-02. Historical claims are marked `DOC CLAIM` and traceable to `.memory/decisions.md`, `.memory/issues.md`, and `docs/commercial/CODEBASE_ECONOMIC_AUDIT_2026-09-29.md`.*
