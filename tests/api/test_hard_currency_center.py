"""مركز العملة الصعبة (D-305) — للمدير وحده، ونتائجه تطابق المحرّكات حرفياً، ولا يخزّن شيئاً."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest
from sqlalchemy import text

from app.api.routers import hard_currency as hc_router
from app.services.hard_currency import decision_chamber
from app.services.hard_currency.sources import HardCurrencySources, get_hard_currency_sources
from shared.research import cbam_pin
from shared.research.contact_ledger import LEDGER_REL
from shared.research.economic_decision import sentence_problems
from tools.hard_currency_engine.belgium_validator import audit_belgian_csv
from tools.hard_currency_engine.france_validator import audit_french_csv

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO = REPO_ROOT / "docs" / "commercial" / "outreach" / "demo"
BASE = "/admin/api/hard-currency"


@pytest.fixture(autouse=True)
def _fresh_limiter():
    hc_router._compute_limiter.reset()
    yield
    hc_router._compute_limiter.reset()


@pytest.fixture
def student_headers(event_loop, db_session, register_and_login_test_user) -> dict[str, str]:
    token = event_loop.run_until_complete(
        register_and_login_test_user(db_session, "hc-student@example.com")
    )
    return {"Authorization": f"Bearer {token}"}


def _upload(client, headers, *, name: str, content: bytes, corridor: str = "fr"):
    return client.post(
        f"{BASE}/einvoicing-audits",
        files={"file": (name, content, "text/csv")},
        data={"corridor": corridor},
        headers=headers,
    )


# ── الصلاحيات ───────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/frontier"),
        ("get", "/cbam/codes"),
        ("get", "/cbam/codes/2523100090"),
        ("get", "/redteam/classes"),
        ("get", "/chamber"),
        ("post", "/chamber/cross-examination"),
        ("post", "/chamber/outcome-preview"),
    ],
)
def test_requires_authentication(client, method: str, path: str) -> None:
    assert getattr(client, method)(f"{BASE}{path}").status_code == 401


@pytest.mark.parametrize(
    ("method", "path", "kwargs"),
    [
        ("get", "/frontier", {}),
        ("get", "/cbam/codes", {}),
        ("get", "/cbam/codes/2523100090", {}),
        ("post", "/cbam/codes/2523100090/decision", {"json": {"see_actual": 0.6}}),
        ("get", "/redteam/classes", {}),
        ("get", "/chamber", {}),
        ("post", "/chamber/cross-examination", {"json": {"question": "build"}}),
        ("post", "/chamber/outcome-preview", {"json": {}}),
    ],
)
def test_a_student_is_refused(client, student_headers, method: str, path: str, kwargs) -> None:
    response = getattr(client, method)(f"{BASE}{path}", headers=student_headers, **kwargs)
    assert response.status_code == 403


def test_a_student_cannot_upload(client, student_headers) -> None:
    content = (DEMO / "DEMO_20_FICHES.csv").read_bytes()
    assert _upload(client, student_headers, name="x.csv", content=content).status_code == 403


# ── خريطة الجبهة ───────────────────────────────────────────────────────────────


def test_frontier_matches_the_committed_value_chain(client, admin_auth_headers) -> None:
    response = client.get(f"{BASE}/frontier", headers=admin_auth_headers)
    assert response.status_code == 200
    body = response.json()
    committed = json.loads((REPO_ROOT / "docs/commercial/VALUE_CHAIN.json").read_text("utf-8"))
    assert len(body["paths"]) == committed["derived"]["paths_total"]
    assert body["by_classification"] == committed["derived"]["by_classification"]
    assert body["committed_snapshot_current"] is True
    assert body["gate_c"] == "ABSENT"
    assert [link["number"] for link in body["links"]] == list(range(1, 9))
    opp11 = next(path for path in body["paths"] if path["id"] == "OPP-11")
    assert opp11["workbench"] == "cbam"
    assert opp11["owner_decision"].startswith("DROP")
    assert len(opp11["links"]) == 8


def test_frontier_reports_a_missing_source_as_503(client, admin_auth_headers, tmp_path) -> None:
    client.app.dependency_overrides[get_hard_currency_sources] = lambda: HardCurrencySources(
        root=tmp_path
    )
    try:
        response = client.get(f"{BASE}/frontier", headers=admin_auth_headers)
    finally:
        client.app.dependency_overrides.pop(get_hard_currency_sources, None)
    assert response.status_code == 503
    assert "VALUE_CHAIN.json" in response.json()["detail"]


# ── ورشة الفوترة ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("corridor", "demo", "engine"),
    [
        ("fr", "DEMO_20_FICHES.csv", audit_french_csv),
        ("be", "DEMO_BELGIUM_PEPPOL_20_FICHES.csv", audit_belgian_csv),
    ],
)
def test_audit_matches_the_engine_exactly(
    client, admin_auth_headers, corridor, demo, engine
) -> None:
    path = DEMO / demo
    response = _upload(
        client, admin_auth_headers, name=demo, content=path.read_bytes(), corridor=corridor
    )
    assert response.status_code == 200
    body = response.json()
    direct = engine(path)
    assert body["summary"]["total"] == direct["total"]
    assert body["summary"]["valides"] == direct["valides"]
    assert len(body["anomalies"]) == len(direct["anomalies"])
    assert body["stored"] is False and body["online_checks"] is False
    assert body["cleaned_csv"].strip()
    assert body["report_markdown"].strip()


def test_audit_neutralises_spreadsheet_formulas(client, admin_auth_headers) -> None:
    content = b'Nom;SIREN;TVA;CP\n=HYPERLINK("http://evil","x");732829320;FR44732829320;75001\n'
    response = _upload(client, admin_auth_headers, name="inject.csv", content=content)
    assert response.status_code == 200
    cleaned = response.json()["cleaned_csv"]
    assert "'=HYPERLINK" in cleaned
    assert not any(line.startswith("=") for line in cleaned.splitlines())


@pytest.mark.parametrize(
    ("name", "content", "corridor", "status"),
    [
        ("data.xlsx", b"Nom;SIREN\nA;1\n", "fr", 415),
        ("data.csv", b"", "fr", 422),
        ("data.csv", b"Nom;SIREN\nA;1\n", "de", 422),
        ("data.csv", b"\x00\x01binary", "fr", 415),
        ("data.csv", b"x" * (2 * 1024 * 1024 + 10), "fr", 413),
        ("data.csv", b"Nom\n" + b"A\n" * 5001, "fr", 413),
    ],
    # Explicit ids, never the payload (ISS-212): without them pytest printed the 2 MB
    # body as the test name, and that single 2,097,263-character line made the CI runner
    # stop responding — test-monolith hit its 45-minute limit four times with no log.
    ids=[
        "not-a-csv-extension",
        "empty-file",
        "unknown-corridor",
        "binary-content",
        "over-size-limit",
        "over-row-limit",
    ],
)
def test_audit_rejects_bad_inputs(
    client, admin_auth_headers, name, content, corridor, status
) -> None:
    response = _upload(client, admin_auth_headers, name=name, content=content, corridor=corridor)
    assert response.status_code == status


def test_audit_writes_nothing_to_message_tables(
    client, admin_auth_headers, db_session, event_loop
) -> None:
    async def counts() -> tuple[int, int]:
        admin = (await db_session.execute(text("SELECT COUNT(*) FROM admin_messages"))).scalar()
        customer = (
            await db_session.execute(text("SELECT COUNT(*) FROM customer_messages"))
        ).scalar()
        return int(admin or 0), int(customer or 0)

    before = event_loop.run_until_complete(counts())
    content = (DEMO / "DEMO_20_FICHES.csv").read_bytes()
    assert _upload(client, admin_auth_headers, name="d.csv", content=content).status_code == 200
    assert event_loop.run_until_complete(counts()) == before


# ── CBAM ────────────────────────────────────────────────────────────────────────


def test_cbam_codes_carry_live_provenance(client, admin_auth_headers) -> None:
    body = client.get(f"{BASE}/cbam/codes", headers=admin_auth_headers).json()
    asymmetry = cbam_pin.column_asymmetry()
    assert len(body["codes"]) == len(cbam_pin.pinned_codes())
    assert (
        body["provenance"]["pairs_where_switching_forfeits_credit"] == asymmetry["column_b_larger"]
    )
    assert body["provenance"]["route_pairs_pinned"] == asymmetry["route_pairs_pinned"]
    assert body["provenance"]["inputs_fingerprint"] == cbam_pin.inputs_fingerprint()


def test_cbam_detail_equals_the_pinned_engine(client, admin_auth_headers) -> None:
    body = client.get(f"{BASE}/cbam/codes/2523100090?year=2026", headers=admin_auth_headers).json()
    assert body["crossover"] == cbam_pin.crossover_see("2523100090", 2026)
    assert body["path_toll"] == cbam_pin.path_toll("2523100090", 2026)
    assert [point["year"] for point in body["trajectory"]] == list(cbam_pin.HORIZON)


def test_cbam_uncomputable_code_shows_its_reason_not_a_number(client, admin_auth_headers) -> None:
    body = client.get(f"{BASE}/cbam/codes/2507008080", headers=admin_auth_headers).json()
    assert body["computable"] is False
    assert body["absent_reason"]
    assert body["crossover"] is None


@pytest.mark.parametrize(
    ("path", "status"), [("/cbam/codes/99999999", 404), ("/cbam/codes/2523100090?year=2040", 422)]
)
def test_cbam_rejects_unknown_inputs(client, admin_auth_headers, path: str, status: int) -> None:
    assert client.get(f"{BASE}{path}", headers=admin_auth_headers).status_code == status


def test_cbam_decision_equals_the_pinned_engine(client, admin_auth_headers) -> None:
    response = client.post(
        f"{BASE}/cbam/codes/2523100090/decision",
        json={"see_actual": 0.6},
        headers=admin_auth_headers,
    )
    assert response.status_code == 200
    expected = cbam_pin.first_sellable_year("2523100090", 0.6)
    assert response.json()["first_sellable_year"] == expected["first_sellable_year"]
    assert response.json()["trajectory"] == expected["trajectory"]


@pytest.mark.parametrize("value", [0, -1, 500])
def test_cbam_decision_rejects_out_of_range_emissions(client, admin_auth_headers, value) -> None:
    response = client.post(
        f"{BASE}/cbam/codes/2523100090/decision",
        json={"see_actual": value},
        headers=admin_auth_headers,
    )
    assert response.status_code == 422


def test_compute_endpoints_are_rate_limited(client, admin_auth_headers) -> None:
    statuses = [
        client.post(
            f"{BASE}/cbam/codes/2523100090/decision",
            json={"see_actual": 0.6},
            headers=admin_auth_headers,
        ).status_code
        for _ in range(31)
    ]
    assert statuses[:30] == [200] * 30
    assert statuses[30] == 429


# ── الاختراق ────────────────────────────────────────────────────────────────────


def test_redteam_classes_report_publishability(client, admin_auth_headers) -> None:
    body = client.get(f"{BASE}/redteam/classes", headers=admin_auth_headers).json()
    corpus = json.loads(
        (REPO_ROOT / "naas_verifier/corpus/ar_fr_exploit_classes.json").read_text("utf-8")
    )
    assert len(body["classes"]) == len(corpus["classes"])
    assert body["publishable_count"] == sum(1 for item in corpus["classes"] if item["publishable"])
    assert all("probe" not in item for item in body["classes"])  # المسابير لا تُعاد
    assert body["external_probe"]["target_package"] == "better_profanity"


# ── غرفة القرار (D-314) ─────────────────────────────────────────────────────────

BALAGUE_REF = "FR_EINVOICING_TARGETS_2026-09-21.csv#id=7"


def _row(action: str, **extra: str) -> dict[str, str]:
    row = {
        "date": "2026-10-01",
        "target_ref": BALAGUE_REF,
        "entity": "Balagué Expertise",
        "country": "FR",
        "channel": "phone",
        "action": action,
        "amount_eur": "",
        "evidence_ref": "",
        "note": "",
    }
    row.update(extra)
    return row


def test_chamber_speaks_only_within_its_evidence(client, admin_auth_headers) -> None:
    response = client.get(f"{BASE}/chamber", headers=admin_auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert sentence_problems(body["sentences"], body["snapshot"]["evidence"]) == []
    assert body["questions"] == ["ready", "build", "why_no_money", "say_to_buyer"]
    assert "PAYMENT_SETTLED" in body["ledger_vocabulary"]["actions"]
    assert "phone" in body["ledger_vocabulary"]["channels"]
    classes = {sentence["class"] for sentence in body["sentences"]}
    assert {"FACT", "REFUSAL"} <= classes
    assert body["snapshot"]["thesis"]["id"] == "fr-be-einvoicing-referential-cleansing"


def test_chamber_ceiling_equals_the_frontier(client, admin_auth_headers) -> None:
    chamber = client.get(f"{BASE}/chamber", headers=admin_auth_headers).json()
    frontier = client.get(f"{BASE}/frontier", headers=admin_auth_headers).json()
    thesis = {p["id"] for p in chamber["snapshot"]["thesis"]["paths"]}
    reached = max(p["reached"] for p in frontier["paths"] if p["id"] in thesis)
    assert chamber["snapshot"]["ceiling"]["link"] == reached
    assert chamber["snapshot"]["gate_c"] == frontier["gate_c"]


def test_chamber_action_is_for_a_human(client, admin_auth_headers) -> None:
    brief = client.get(f"{BASE}/chamber", headers=admin_auth_headers).json()["brief"]
    if brief["status"] == "DECISION_AVAILABLE":
        assert brief["primary_action"]["owner_ar"].startswith("المالك")
        assert brief["capsule"]["status"] == "HYPOTHESIS"


def test_chamber_reports_a_missing_source_as_503(client, admin_auth_headers, tmp_path) -> None:
    client.app.dependency_overrides[get_hard_currency_sources] = lambda: HardCurrencySources(
        root=tmp_path
    )
    try:
        response = client.get(f"{BASE}/chamber", headers=admin_auth_headers)
    finally:
        client.app.dependency_overrides.pop(get_hard_currency_sources, None)
    assert response.status_code == 503


def _module_level_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
    return names


def test_the_chamber_does_not_import_tools_at_module_level() -> None:
    """``Dockerfile.prod`` ships ``app/`` and ``shared/`` but not ``tools/``.

    A module-level import of ``tools`` made ``import app.main`` fail inside the production
    image (``image: monolith`` on PR #2595). The linter is loaded on demand, like
    ``einvoicing_audit._engine``.
    """
    service = Path(decision_chamber.__file__)
    assert "tools" not in _module_level_imports(service)


def test_chamber_without_the_linter_says_so_and_still_answers(
    client, admin_auth_headers, monkeypatch
) -> None:
    """No linter in the deployment ⇒ the snapshot declares the wording check unrun, and
    "can we say this to a buyer?" refuses with the reason — it never answers unchecked."""
    monkeypatch.setattr(decision_chamber, "_buyer_claims", lambda: None)
    chamber = client.get(f"{BASE}/chamber", headers=admin_auth_headers)
    assert chamber.status_code == 200
    assert chamber.json()["snapshot"]["wording_checked"] is False
    ready = client.post(
        f"{BASE}/chamber/cross-examination", json={"question": "ready"}, headers=admin_auth_headers
    )
    assert ready.status_code == 200
    refused = client.post(
        f"{BASE}/chamber/cross-examination",
        json={"question": "say_to_buyer", "text": "Nous garantissons zéro rejet."},
        headers=admin_auth_headers,
    )
    assert refused.status_code == 503
    assert refused.json()["detail"] == decision_chamber.LINTER_ABSENT_AR


@pytest.mark.parametrize("question", ["ready", "build", "why_no_money"])
def test_cross_examination_answers_with_classified_sentences(
    client, admin_auth_headers, question: str
) -> None:
    response = client.post(
        f"{BASE}/chamber/cross-examination", json={"question": question}, headers=admin_auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["question"] == question
    assert body["sentences"]
    assert all(
        s["class"] in {"FACT", "HYPOTHESIS", "UNKNOWN", "ACTION", "REFUSAL"}
        for s in body["sentences"]
    )


def test_say_to_buyer_refuses_a_guarantee(client, admin_auth_headers) -> None:
    response = client.post(
        f"{BASE}/chamber/cross-examination",
        json={"question": "say_to_buyer", "text": "Nous garantissons zéro rejet."},
        headers=admin_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["verdict"] == "FORBIDDEN"


@pytest.mark.parametrize(
    "payload",
    [
        {"question": "tell me anything"},
        {"question": "say_to_buyer"},
        {"question": "say_to_buyer", "text": "x" * 2001},
    ],
    ids=["open-question", "no-text", "text-too-long"],
)
def test_cross_examination_rejects_open_or_bad_questions(
    client, admin_auth_headers, payload
) -> None:
    response = client.post(
        f"{BASE}/chamber/cross-examination", json=payload, headers=admin_auth_headers
    )
    assert response.status_code == 422


def test_outcome_preview_accepts_a_call_and_writes_nothing(
    client, admin_auth_headers, db_session, event_loop
) -> None:
    async def counts() -> tuple[int, int]:
        admin = (await db_session.execute(text("SELECT COUNT(*) FROM admin_messages"))).scalar()
        customer = (
            await db_session.execute(text("SELECT COUNT(*) FROM customer_messages"))
        ).scalar()
        return int(admin or 0), int(customer or 0)

    ledger = REPO_ROOT / LEDGER_REL
    sha_before = hashlib.sha256(ledger.read_bytes()).hexdigest()
    rows_before = event_loop.run_until_complete(counts())
    response = client.post(
        f"{BASE}/chamber/outcome-preview", json=_row("CALL_MADE"), headers=admin_auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is True
    assert body["written"] is False
    assert body["csv_line"].startswith(f"2026-10-01,{BALAGUE_REF},Balagué Expertise,FR,phone")
    assert hashlib.sha256(ledger.read_bytes()).hexdigest() == sha_before
    assert event_loop.run_until_complete(counts()) == rows_before


def test_outcome_preview_rejects_money_with_no_quote(client, admin_auth_headers) -> None:
    payload = _row("PAYMENT_SETTLED", channel="bank", amount_eur="290", evidence_ref="releve.pdf")
    body = client.post(
        f"{BASE}/chamber/outcome-preview", json=payload, headers=admin_auth_headers
    ).json()
    assert body["accepted"] is False
    assert any("QUOTE_SENT" in problem for problem in body["problems"])
