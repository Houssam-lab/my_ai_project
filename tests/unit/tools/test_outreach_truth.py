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

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.hard_currency_engine.france_validator import tva_fr_check

OUTREACH = REPO_ROOT / "docs/commercial/outreach"
KIT = OUTREACH / "BALAGUE_FIRST_CLIENT_KIT_2026-09-22.md"
MALT = OUTREACH / "ready_to_send/03_PROFIL_MALT.md"
CATALOG = REPO_ROOT / "docs/commercial/OFFER_CATALOG.json"
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
