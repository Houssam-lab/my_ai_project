"""D-304 — what the owner sends to a buyer is checked like code.

The wedge's first buyer reads these files word for word, under the owner's name.
Three defects were found in them before any of them had a reply:

- C12: a research file gave Balagué a valid French VAT number that belongs to
  another company (SIREN 791 349 749 instead of 501 058 812).
- C7/C8: sales sentences stated measured trends ("ont fortement augmenté", "une
  part significative des échecs") and guarantees ("garantir un routage sans
  échec"). The error rate in real files has never been measured
  (``OFFER_CATALOG.json`` — ``claims_forbidden_ar``).
- C5: three different package prices in three files (150–300 €, 290 €,
  290–390 €). The owner chose one on 2026-09-30: 290 € HT up to 200 records.

The email already sent to Balagué on 2026-09-22 is kept verbatim as the record;
a warning next to it says not to reuse its unmeasured phrase.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.hard_currency_engine.belgium_validator import (
    audit_belgian_csv,
    export_cleaned_belgian_csv,
    format_belgian_report,
)
from tools.hard_currency_engine.crm_dispatcher import dispatch_campaign
from tools.hard_currency_engine.france_validator import (
    audit_french_csv,
    export_cleaned_french_csv,
    format_french_report,
    tva_fr_check,
)

OUTREACH = REPO_ROOT / "docs/commercial/outreach"
KIT = OUTREACH / "BALAGUE_FIRST_CLIENT_KIT_2026-09-22.md"
MALT = OUTREACH / "ready_to_send/03_PROFIL_MALT.md"
CATALOG = REPO_ROOT / "docs/commercial/OFFER_CATALOG.json"
MASTER_TARGETS = REPO_ROOT / "docs/commercial/MASTER_CLIENT_TARGETS_GLOBAL_2026.csv"
COMMITTED_DRAFTS = OUTREACH / "drafts_2026"
DEMO = OUTREACH / "demo"
DEMO_REPORT_DATE = date(2026, 9, 29)
WEDGE_ID = "fr-be-einvoicing-referential-cleansing"

#: The files the owner copies into an email, a call or a profile for the active wedge.
#: ``04_SCRIPTS_EXPANSION_GLOBAL.md`` is not listed: its corridors 3→9 are frozen
#: (D-300) and its header says so.
SEND_FILES = (
    OUTREACH / "ready_to_send/00_PLAN_ENVOI.md",
    OUTREACH / "ready_to_send/01_MAILS_CABINETS_PRETS.md",
    OUTREACH / "ready_to_send/02_PARTENARIATS_PDP.md",
    MALT,
    KIT,
)

#: The one package price the owner chose (D-304).
PACKAGE_PRICE = "290 €"

_TVA = re.compile(r"\bFR ?\d{2} ?\d{3} ?\d{3} ?\d{3}\b")
_SIREN_AFTER_LABEL = re.compile(r"SIREN\W{0,6}(\d{3} ?\d{3} ?\d{3})\b")
_GUARANTEE = re.compile(r"garanti", re.IGNORECASE)
_EURO_RANGE = re.compile(r"\d[\d  ]*\s?[–-]\s?\d[\d  ]*\s?€")
_CRM_UNMEASURED_CLAIM = re.compile(
    r"\b\d+\s?%|garanti|garantie|z[eé]ro\s+rejet",
    re.IGNORECASE,
)


def identifier_mismatches(line: str) -> list[str]:
    """A TVA printed on the same line as a labelled SIREN must carry that SIREN."""
    sirens = {match.replace(" ", "") for match in _SIREN_AFTER_LABEL.findall(line)}
    problems = []
    for raw in _TVA.findall(line):
        tva = raw.replace(" ", "")
        ok, _clean, message = tva_fr_check(tva)
        if not ok:
            problems.append(f"{tva}: {message}")
        elif sirens and tva[4:] not in sirens:
            problems.append(f"{tva} carries SIREN {tva[4:]}, the line names {sorted(sirens)}")
    return problems


def buyer_text(path: Path) -> list[tuple[int, str]]:
    """Lines a buyer reads: inside code fences (emails, profile) and ``>`` quotes (scripts)."""
    lines, inside = [], False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.lstrip().startswith("```"):
            inside = not inside
            continue
        if inside or line.lstrip().startswith(">"):
            lines.append((number, line))
    return lines


def test_the_c12_line_is_caught() -> None:
    """The negative proof: the wrong line from the research file fails the rule."""
    line = "Balagué — **SIREN 501 058 812** (RCS Toulouse 501 058 812) · TVA FR 61 791 349 749"
    assert identifier_mismatches(line) == [
        "FR61791349749 carries SIREN 791349749, the line names ['501058812']"
    ]
    assert identifier_mismatches("SIREN 501 058 812 · TVA FR40501058812") == []


def test_master_targets_csv_is_rectangular() -> None:
    with MASTER_TARGETS.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        problems = [
            f"line {line_number}: {len(row)} fields instead of {len(header)}"
            for line_number, row in enumerate(reader, start=2)
            if len(row) != len(header)
        ]
    assert problems == []


def test_every_outreach_vat_number_matches_its_siren() -> None:
    problems = [
        f"{path.relative_to(REPO_ROOT)}:{number}: {problem}"
        for path in sorted(OUTREACH.rglob("*.md"))
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        for problem in identifier_mismatches(line)
    ]
    assert problems == []


def test_buyer_text_states_no_rate_and_no_guarantee() -> None:
    problems = [
        f"{path.relative_to(REPO_ROOT)}:{number}: {line.strip()[:90]}"
        for path in SEND_FILES
        for number, line in buyer_text(path)
        if "%" in line or _GUARANTEE.search(line)
    ]
    assert problems == []


def _crm_draft_claim_problems(path: Path | str, text: str) -> list[str]:
    """Generated CRM drafts are buyer text too; draft status does not license claims."""
    if not text.startswith("STATUS: DRAFT"):
        return []
    return [
        f"{path}:{number}: {line.strip()[:120]}"
        for number, line in enumerate(text.splitlines(), start=1)
        if _CRM_UNMEASURED_CLAIM.search(line)
    ]


def test_generated_crm_drafts_state_no_rate_and_no_guarantee(tmp_path: Path) -> None:
    generated = dispatch_campaign(MASTER_TARGETS, tmp_path)
    problems = [
        problem
        for path in generated
        for problem in _crm_draft_claim_problems(path.name, path.read_text(encoding="utf-8"))
    ]
    assert problems == []


def test_committed_crm_drafts_state_no_rate_and_no_guarantee() -> None:
    problems = [
        problem
        for path in sorted(COMMITTED_DRAFTS.glob("*.txt"))
        for problem in _crm_draft_claim_problems(
            path.relative_to(REPO_ROOT),
            path.read_text(encoding="utf-8"),
        )
    ]
    assert problems == []


def test_committed_crm_drafts_match_generated_output(tmp_path: Path) -> None:
    """The committed draft folder is a reproducible view, not a second source of truth."""
    dispatch_campaign(MASTER_TARGETS, tmp_path)
    committed = {path.name: path.read_text(encoding="utf-8") for path in COMMITTED_DRAFTS.glob("*.txt")}
    generated = {path.name: path.read_text(encoding="utf-8") for path in tmp_path.glob("*.txt")}
    assert sorted(committed) == sorted(generated)
    differing = sorted(name for name in committed if committed[name] != generated[name])
    assert differing == []


def test_committed_france_demo_artifacts_match_generator(tmp_path: Path) -> None:
    """The France demo report and cleaned CSV are generated artifacts with a fixed date."""
    source = DEMO / "DEMO_20_FICHES.csv"
    results = audit_french_csv(source)
    report = format_french_report(results, source.name, report_date=DEMO_REPORT_DATE)
    assert report == (DEMO / "RAPPORT_DIAGNOSTIC_FRANCE_RFE.md").read_text(encoding="utf-8")

    generated_csv = tmp_path / "DEMO_20_FICHES_ASSAINI.csv"
    export_cleaned_french_csv(results, generated_csv)
    assert generated_csv.read_bytes() == (DEMO / "DEMO_20_FICHES_ASSAINI.csv").read_bytes()


def test_committed_belgium_demo_artifacts_match_generator(tmp_path: Path) -> None:
    """The Belgium Peppol demo report and cleaned CSV are generated artifacts too."""
    source = DEMO / "DEMO_BELGIUM_PEPPOL_20_FICHES.csv"
    results = audit_belgian_csv(source)
    report = format_belgian_report(results, source.name, report_date=DEMO_REPORT_DATE)
    assert report == (DEMO / "RAPPORT_DIAGNOSTIC_BELGIQUE_PEPPOL.md").read_text(
        encoding="utf-8"
    )

    generated_csv = tmp_path / "DEMO_BELGIUM_PEPPOL_20_FICHES_ASSAINI.csv"
    export_cleaned_belgian_csv(results, generated_csv)
    assert generated_csv.read_bytes() == (
        DEMO / "DEMO_BELGIUM_PEPPOL_20_FICHES_ASSAINI.csv"
    ).read_bytes()


def test_one_package_price_everywhere() -> None:
    route = next(
        offer["hard_currency_route_ar"]
        for offer in json.loads(CATALOG.read_text(encoding="utf-8"))["offers"]
        if offer["id"] == WEDGE_ID
    )
    for name, text in (
        ("kit", KIT.read_text(encoding="utf-8")),
        ("malt", MALT.read_text(encoding="utf-8")),
    ):
        assert PACKAGE_PRICE in text, name
        assert _EURO_RANGE.findall(text) == [], name
    # The catalog route also cites market day rates as ranges (sources, not our price).
    assert PACKAGE_PRICE in route
    assert "290–390" not in route
