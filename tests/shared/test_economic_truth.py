"""D-314 — the Economic Truth Machine: the most we may say, the first missing proof, one human act.

Two kinds of test:

- **On the real repository** — invariants only (every FACT carries evidence that exists, the
  ceiling equals the value chain's own derivation, nothing is written). They must hold on the
  day the owner records a reply, so they never hard-code today's funnel.
- **On small synthetic chains** — every stage of the chain picks its bottleneck and one lawful
  action; a fired kill condition and an unreadable ledger refuse to decide.
"""

from __future__ import annotations

import ast
import hashlib
import sys
from datetime import date
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.research.contact_ledger import ACTIONS, COLUMNS, LEDGER_REL, parse_ledger
from shared.research.economic_decision import (
    BOTTLENECKS,
    DECISION_AVAILABLE,
    NO_LAWFUL_DECISION,
    QUESTIONS,
    build_brief,
    cross_examine,
    preview_outcome,
    render_sentences,
    sentence_problems,
)
from shared.research.economic_truth import (
    ACTIVE_THESIS_ID,
    CLAIMS,
    DECISIONS_REL,
    FIRED,
    KILL_CONDITIONS,
    NOT_YET_EVALUABLE,
    SETTLEMENT_VIEW,
    UNKNOWN,
    build_snapshot,
    load_inputs,
)
from shared.research.value_chain import compute_derived
from tools.hard_currency_engine.buyer_claims import classify, findings

TODAY = date(2026, 10, 2)
# The real ledger rejects rows dated after "today", and the gate and the scorecard read it
# with the real calendar. A pinned date here turns every row logged after it into a
# parse error, and build_snapshot then reads an empty ledger without failing.
REAL_TODAY = date.today()
ROUTE = "TARGETS.csv"
HEADER = ",".join(COLUMNS)
CATALOG = {
    "offers": [
        {
            "id": ACTIVE_THESIS_ID,
            "status": "PROPOSED",
            "offer_outcome_ar": "تقرير قبل/بعد",
            "claims_forbidden_ar": "لا نسبة",
        }
    ]
}
SCORECARD = {"gate_c": "ABSENT", "source_sha256": "x", "hard_currency_scorecard": {}}


def _lint(text: str) -> list[tuple[str, str, str]]:
    return [(item.rule, item.verdict, item.excerpt) for item in findings(text)]


def _classify(text: str) -> tuple[str, str, list[tuple[str, str]]]:
    verdict = classify(text)
    return verdict.verdict, verdict.reason_ar, [(f.rule, f.excerpt) for f in verdict.findings]


def _chain(reached: int = 4) -> dict[str, object]:
    links: dict[str, object] = {}
    for number in range(1, 7):
        if number <= reached:
            links[str(number)] = {"status": "REACHED", "evidence": ["ev.txt"]}
            if number == 3:
                links[str(number)]["contains_user_data"] = False  # type: ignore[index]
        else:
            links[str(number)] = {"status": "NOT_REACHED", "reason_ar": "يلزم ملفٌّ حقيقي"}
    return {
        "paths": [
            {
                "id": "P1",
                "title_ar": "مسارٌ تجريبي",
                "source": "ev.txt",
                "catalog_id": ACTIVE_THESIS_ID,
                "ledger_routes": [ROUTE],
                "links": links,
            }
        ]
    }


def _row(day: str, entity: str, action: str, *, amount: str = "", evidence: str = "") -> str:
    return f"{day},{ROUTE}#id=1,{entity},FR,email,{action},{amount},{evidence},"


def _ledger(*rows: str) -> str:
    return "\n".join([HEADER, *rows]) + "\n"


def _snap(tmp_path: Path, ledger: str, *, reached: int = 4) -> dict[str, object]:
    (tmp_path / "ev.txt").write_text("x", encoding="utf-8")
    return build_snapshot(
        chain_doc=_chain(reached),
        ledger_text=ledger,
        catalog=CATALOG,
        scorecard=SCORECARD,
        root=tmp_path,
        today=TODAY,
    )


ONE_EMAIL = _ledger(_row("2026-09-22", "Cabinet A", "EMAIL_SENT"))


# ── the real repository ─────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def real() -> dict[str, object]:
    inputs = load_inputs(REPO_ROOT)
    snapshot = build_snapshot(**inputs, root=REPO_ROOT, today=REAL_TODAY, wording=_lint)
    assert snapshot["ledger_problems"] == []
    return {"inputs": inputs, "snapshot": snapshot, "brief": build_brief(snapshot)}


def test_real_every_sentence_stays_within_its_evidence(real) -> None:
    snapshot, brief = real["snapshot"], real["brief"]
    sentences = render_sentences(snapshot, brief)
    assert sentence_problems(sentences, snapshot["evidence"]) == []
    for question in ("ready", "build", "why_no_money"):
        answer = cross_examine(question, snapshot, brief)
        assert sentence_problems(answer["sentences"], snapshot["evidence"]) == [], question


def test_real_every_cited_evidence_exists_on_disk(real) -> None:
    missing = [item["id"] for item in real["snapshot"]["evidence"] if not item["exists"]]
    assert missing == []


def test_real_ceiling_is_the_value_chain_derivation(real) -> None:
    inputs, snapshot = real["inputs"], real["snapshot"]
    rows = parse_ledger(inputs["ledger_text"], today=REAL_TODAY)
    derived = compute_derived(inputs["chain_doc"], rows)
    thesis_ids = {p["id"] for p in snapshot["thesis"]["paths"]}
    reached = max(p["reached"] for p in derived["paths"] if p["id"] in thesis_ids)
    assert snapshot["ceiling"]["link"] == reached
    assert snapshot["gate_c"] == load_inputs(REPO_ROOT)["scorecard"]["gate_c"]


def test_real_primary_action_belongs_to_a_human(real) -> None:
    brief = real["brief"]
    assert brief["status"] in {DECISION_AVAILABLE, NO_LAWFUL_DECISION}
    if brief["status"] == DECISION_AVAILABLE:
        assert brief["bottleneck"] in BOTTLENECKS
        assert brief["primary_action"]["owner_ar"].startswith("المالك")


def test_real_catalog_zero_rejection_wording_is_reported(real) -> None:
    """The catalog promises «صفر رفض توجيه»; the machine names it instead of repeating it."""
    kinds = [(c["kind"], c["detail_ar"]) for c in real["snapshot"]["contradictions"]]
    assert any(kind == "catalog_wording" and "صفر رفض" in detail for kind, detail in kinds)


def test_active_thesis_and_kill_conditions_are_quoted_from_d300() -> None:
    text = (REPO_ROOT / DECISIONS_REL).read_text(encoding="utf-8")
    d300 = text[text.index("## D-300 ") : text.index("## D-299 ")]
    assert f"`{ACTIVE_THESIS_ID}`" in d300
    for kill in KILL_CONDITIONS:
        assert kill.source_quote in d300, kill.kill_id
    catalog_ids = {o["id"] for o in load_inputs(REPO_ROOT)["catalog"]["offers"]}
    assert ACTIVE_THESIS_ID in catalog_ids


def test_snapshot_is_deterministic_and_reads_no_clock(tmp_path) -> None:
    assert _snap(tmp_path, ONE_EMAIL) == _snap(tmp_path, ONE_EMAIL)


def test_a_newer_row_outside_the_thesis_is_not_its_last_event(tmp_path) -> None:
    # Evidence lists only thesis rows, so a later row on another path must not become the
    # "last event" — its sentence would cite a ledger line the evidence does not hold.
    other_path = "2026-09-30,OTHER.csv#id=1,Platform X,US,platform,FORM_SUBMITTED,,,"
    snapshot = _snap(tmp_path, _ledger(_row("2026-09-22", "Cabinet A", "EMAIL_SENT"), other_path))
    assert snapshot["last_event"]["entity"] == "Cabinet A"
    assert snapshot["days_since_last_event"] == 10
    sentences = render_sentences(snapshot, build_brief(snapshot))
    assert sentence_problems(sentences, snapshot["evidence"]) == []


# ── each stage picks its bottleneck and one lawful action ─────────────────────


def test_one_unanswered_email_asks_for_a_follow_up_call(tmp_path) -> None:
    brief = build_brief(_snap(tmp_path, ONE_EMAIL))
    assert brief["status"] == DECISION_AVAILABLE
    assert brief["bottleneck"] == "channel"
    assert brief["primary_action"]["action_id"] == "FOLLOW_UP_CALL"
    assert "Cabinet A" in brief["primary_action"]["title_ar"]
    assert brief["ledger_row_template"]["action"] == "CALL_MADE"
    assert brief["capsule"]["status"] == "HYPOTHESIS"


def test_after_a_follow_up_the_next_act_is_a_new_contact(tmp_path) -> None:
    ledger = _ledger(
        _row("2026-09-22", "Cabinet A", "EMAIL_SENT"),
        _row("2026-09-24", "Cabinet A", "CALL_MADE"),
    )
    brief = build_brief(_snap(tmp_path, ledger))
    assert brief["primary_action"]["action_id"] == "NEXT_CONTACT"


def test_a_reply_moves_the_bottleneck_to_data_access(tmp_path) -> None:
    ledger = _ledger(
        _row("2026-09-22", "Cabinet A", "EMAIL_SENT"),
        _row("2026-09-23", "Cabinet A", "REPLY_RECEIVED"),
    )
    brief = build_brief(_snap(tmp_path, ledger))
    assert (brief["bottleneck"], brief["primary_action"]["action_id"]) == (
        "data_access",
        "REQUEST_REAL_FILE",
    )


def test_a_sample_without_link_5_is_an_evidence_gap(tmp_path) -> None:
    ledger = _ledger(
        _row("2026-09-22", "Cabinet A", "EMAIL_SENT"),
        _row("2026-09-23", "Cabinet A", "REPLY_RECEIVED"),
        _row("2026-09-24", "Cabinet A", "SAMPLE_DELIVERED"),
    )
    brief = build_brief(_snap(tmp_path, ledger))
    assert brief["primary_action"]["action_id"] == "DECLARE_LINK_5"


def test_no_paid_quote_while_the_collection_path_is_unknown(tmp_path) -> None:
    """D-304: no paid order before the bank, ANAE and the DPA. Unknown is not ready."""
    ledger = _ledger(
        _row("2026-09-22", "Cabinet A", "EMAIL_SENT"),
        _row("2026-09-23", "Cabinet A", "REPLY_RECEIVED"),
        _row("2026-09-24", "Cabinet A", "SAMPLE_DELIVERED"),
    )
    brief = build_brief(_snap(tmp_path, ledger, reached=5))
    assert brief["bottleneck"] == "payment"
    assert brief["primary_action"]["action_id"] == "ASK_BANK_IN_WRITING"
    quote = next(c for c in brief["candidates_considered"] if c["action_id"] == "SEND_QUOTE")
    assert quote["lawful_now"] is False


def test_a_fired_kill_condition_refuses_to_decide(tmp_path) -> None:
    rows = [_row("2026-09-01", f"Cabinet {n}", "EMAIL_SENT") for n in range(30)]
    snapshot = _snap(tmp_path, _ledger(*rows))
    k1 = next(k for k in snapshot["kill_conditions"] if k["kill_id"] == "K1")
    assert k1["status"] == FIRED
    brief = build_brief(snapshot)
    assert brief["status"] == NO_LAWFUL_DECISION
    assert brief["primary_action"] is None
    assert any("K1" in line for line in brief["details"])


def test_a_quote_unpaid_after_14_days_fires_k5(tmp_path) -> None:
    ledger = _ledger(
        _row("2026-09-01", "Cabinet A", "EMAIL_SENT"),
        _row("2026-09-02", "Cabinet A", "REPLY_RECEIVED"),
        _row("2026-09-03", "Cabinet A", "QUOTE_SENT", amount="290"),
    )
    k5 = next(k for k in _snap(tmp_path, ledger)["kill_conditions"] if k["kill_id"] == "K5")
    assert k5["status"] == FIRED


def test_kill_conditions_below_their_denominator_say_so(tmp_path) -> None:
    statuses = {k["kill_id"]: k["status"] for k in _snap(tmp_path, ONE_EMAIL)["kill_conditions"]}
    assert statuses == {
        "K1": NOT_YET_EVALUABLE,
        "K2": NOT_YET_EVALUABLE,
        "K3": NOT_YET_EVALUABLE,
        "K4": "NOT_RECORDABLE",
        "K5": NOT_YET_EVALUABLE,
    }


def test_an_unreadable_ledger_refuses_to_decide(tmp_path) -> None:
    snapshot = _snap(tmp_path, _ledger(_row("2026-09-22", "X", "PAYMENT_SETTLED", amount="290")))
    assert snapshot["ledger_valid"] is False
    brief = build_brief(snapshot)
    assert brief["status"] == NO_LAWFUL_DECISION
    assert brief["details"]


def test_unrecorded_claims_are_unknown_and_listed_as_blind_spots(tmp_path) -> None:
    snapshot = _snap(tmp_path, ONE_EMAIL)
    unknown = {c["claim_id"] for c in snapshot["claims"] if c["status"] == UNKNOWN}
    assert unknown == {c.claim_id for c in CLAIMS if c.basis == "unrecorded"}
    spots = " ".join(s["detail_ar"] for s in snapshot["blind_spots"])
    assert all(claim_id in spots for claim_id in unknown)


def test_settlement_view_adds_no_ledger_action() -> None:
    """A view, not a third ladder: each observed state is a ledger action or a derivation."""
    for state in SETTLEMENT_VIEW:
        observed = state.observed_by
        if observed is None or observed.startswith(("derived:", "value_chain_", "targets_")):
            continue
        assert observed in ACTIONS or observed == "OUTBOUND", state.state


# ── the sentence contract ─────────────────────────────────────────────────────


EVIDENCE = [
    {"id": "LEDGER:2", "kind": "ledger"},
    {"id": "P1.L4", "kind": "chain"},
    {"id": "D-300", "kind": "decision"},
]


@pytest.mark.parametrize(
    ("sentence", "fragment"),
    [
        ({"sentence": "الأداة تعمل.", "class": "FACT", "evidence_ids": []}, "FACT بلا"),
        ({"sentence": "x", "class": "FACT", "evidence_ids": ["NOPE"]}, "غير موجودة"),
        ({"sentence": "x", "class": "OPINION", "evidence_ids": []}, "صنفٌ خارج"),
        ({"sentence": "منتجٌ ثوري", "class": "HYPOTHESIS", "evidence_ids": []}, "ممنوع"),
        (
            {"sentence": "لدينا عميل يدفع.", "class": "FACT", "evidence_ids": ["P1.L4"]},
            "بلا دليلٍ من",
        ),
        (
            {"sentence": "العرض جاهز قانونياً.", "class": "FACT", "evidence_ids": ["LEDGER:2"]},
            "بلا دليلٍ من",
        ),
    ],
)
def test_sentences_that_outrun_their_evidence_are_rejected(sentence, fragment) -> None:
    problems = sentence_problems([sentence], EVIDENCE)
    assert any(fragment in p for p in problems), problems


def test_owner_is_not_money() -> None:
    """«مالك» (owner) contains «مال» (money); the check works on words, not substrings."""
    sentence = {"sentence": "مالك الحلقة إنسان.", "class": "FACT", "evidence_ids": ["P1.L4"]}
    assert sentence_problems([sentence], EVIDENCE) == []


def test_a_refusal_may_name_what_it_forbids() -> None:
    sentence = {"sentence": "لا يُقال: منتجٌ ثوري.", "class": "REFUSAL", "evidence_ids": []}
    assert sentence_problems([sentence], EVIDENCE) == []


# ── the cross-examination ─────────────────────────────────────────────────────


def test_build_answers_no_when_the_next_link_is_human(tmp_path) -> None:
    snapshot = _snap(tmp_path, ONE_EMAIL)
    answer = cross_examine("build", snapshot, build_brief(snapshot))
    assert answer["sentences"][0]["sentence"].startswith("لا.")


def test_why_no_money_names_the_first_break(tmp_path) -> None:
    snapshot = _snap(tmp_path, ONE_EMAIL)
    answer = cross_examine("why_no_money", snapshot, build_brief(snapshot))
    assert "الحلقة 7" in answer["sentences"][-1]["sentence"]


def test_say_to_buyer_uses_the_d304_rules(tmp_path) -> None:
    snapshot = _snap(tmp_path, ONE_EMAIL)
    answer = cross_examine(
        "say_to_buyer",
        snapshot,
        build_brief(snapshot),
        text="Nous garantissons zéro rejet.",
        classify_text=_classify,
    )
    assert answer["verdict"] == "FORBIDDEN"
    assert answer["sentences"][0]["class"] == "REFUSAL"


def test_questions_are_a_closed_set(tmp_path) -> None:
    snapshot = _snap(tmp_path, ONE_EMAIL)
    assert QUESTIONS == ("ready", "build", "why_no_money", "say_to_buyer")
    with pytest.raises(ValueError):
        cross_examine("tell me anything", snapshot, build_brief(snapshot))


# ── the outcome preview writes nothing ───────────────────────────────────────


def _preview(tmp_path: Path, row: dict[str, str], ledger: str = ONE_EMAIL) -> dict[str, object]:
    (tmp_path / "ev.txt").write_text("x", encoding="utf-8")
    return preview_outcome(
        row=row,
        chain_doc=_chain(),
        ledger_text=ledger,
        catalog=CATALOG,
        scorecard=SCORECARD,
        root=tmp_path,
        today=TODAY,
    )


def _proposed(action: str, **extra: str) -> dict[str, str]:
    row = dict.fromkeys(COLUMNS, "")
    row.update(
        date="2026-10-02",
        target_ref=f"{ROUTE}#id=1",
        entity="Cabinet A",
        country="FR",
        channel="phone",
        action=action,
    )
    row.update(extra)
    return row


def test_preview_accepts_a_valid_row_and_shows_the_delta(tmp_path) -> None:
    result = _preview(tmp_path, _proposed("CALL_MADE"))
    assert result["accepted"] is True
    assert result["written"] is False
    assert result["csv_line"].startswith("2026-10-02,TARGETS.csv#id=1,Cabinet A,FR,phone,CALL_MADE")
    assert result["delta"]["primary_action"] == ["FOLLOW_UP_CALL", "NEXT_CONTACT"]


@pytest.mark.parametrize(
    ("row", "fragment"),
    [
        (_proposed("PAYMENT_SETTLED", amount_eur="290", evidence_ref="r.pdf"), "QUOTE_SENT"),
        (_proposed("CALL_MADE", target_ref="OTHER.csv#id=1"), "غير موجَّه"),
        (_proposed("CALL_MADE", date="2027-01-01"), "المستقبل"),
        (_proposed("TWEETED"), "خارج المجموعة"),
    ],
)
def test_preview_rejects_what_the_ledger_would_reject(tmp_path, row, fragment) -> None:
    result = _preview(tmp_path, row)
    assert result["accepted"] is False
    assert any(fragment in p for p in result["problems"]), result["problems"]


def test_preview_on_the_real_ledger_leaves_the_file_untouched() -> None:
    path = REPO_ROOT / LEDGER_REL
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    inputs = load_inputs(REPO_ROOT)
    preview_outcome(
        row=_proposed("CALL_MADE", target_ref="FR_EINVOICING_TARGETS_2026-09-21.csv#id=7"),
        root=REPO_ROOT,
        today=TODAY,
        **inputs,
    )
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


# ── purity ───────────────────────────────────────────────────────────────────


#: Stdlib modules that would give the machine a network or a shell.
_REACH = {"http", "urllib", "socket", "ssl", "subprocess", "asyncio", "smtplib", "ftplib"}


@pytest.mark.parametrize("module", ["economic_truth", "economic_decision"])
def test_the_machine_imports_nothing_but_stdlib_and_shared(module: str) -> None:
    """No app, no tools, no network or shell, no model client — by construction, not by review."""
    tree = ast.parse((REPO_ROOT / "shared" / "research" / f"{module}.py").read_text("utf-8"))
    imported = {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    } | {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    outside = imported - {"shared"} - set(sys.stdlib_module_names)
    assert outside == set(), outside
    assert imported & _REACH == set(), imported & _REACH
