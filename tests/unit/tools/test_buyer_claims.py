"""D-314 — "can we say this to a buyer?" answered by the D-304 rules, not by tone.

Every case below is a shape D-304 found in texts sent under the owner's name, or the
honest default: a sentence no rule recognises is UNSUPPORTED — a human judges it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.hard_currency_engine.buyer_claims import (
    KNOWN_FACTS,
    VERDICTS,
    buyer_lines,
    classify,
    findings,
)


@pytest.mark.parametrize(
    ("text", "verdict", "rule"),
    [
        # C8 — a guarantee.
        ("Nous garantissons un routage sans échec.", "FORBIDDEN", "guarantee"),
        # An outcome nobody measured, stated as certain.
        ("Un fichier prêt à importer, zéro rejet.", "FORBIDDEN", "zero_failure"),
        ("ملفّ جاهز للاستيراد بصفر رفض توجيه", "FORBIDDEN", "zero_failure"),
        # C7 — a rate.
        ("32 % des factures sont rejetées la première semaine.", "UNSUPPORTED", "unmeasured_rate"),
        # C7 — a trend stated as observed.
        ("Les rejets ont fortement augmenté.", "HYPOTHESIS_ONLY", "observed_trend"),
        # C5 — a price range where the owner set one price.
        ("Le forfait coûte 290–390 € HT.", "UNSUPPORTED", "price_range"),
        # C12 — a valid TVA that belongs to another company.
        (
            "SIREN 501 058 812 · TVA FR 61 791 349 749",
            "FORBIDDEN",
            "identifier_mismatch",
        ),
        # Clients that the ledger does not show.
        ("Nos clients nous font confiance.", "UNSUPPORTED", "existing_clients"),
        # A forbidden superlative (D-305).
        ("Une solution révolutionnaire.", "FORBIDDEN", "forbidden_term"),
    ],
)
def test_d304_shapes_are_caught(text: str, verdict: str, rule: str | None) -> None:
    result = classify(text)
    assert result.verdict == verdict, (text, result)
    if rule is not None:
        assert rule in {item.rule for item in result.findings}


def test_the_catalog_outcome_wording_is_caught() -> None:
    """The catalog promises "صفر رفض توجيه" — an outcome no real file has measured (D-300)."""
    catalog = json.loads((REPO_ROOT / "docs/commercial/OFFER_CATALOG.json").read_text("utf-8"))
    outcome = next(
        offer["offer_outcome_ar"]
        for offer in catalog["offers"]
        if offer["id"] == "fr-be-einvoicing-referential-cleansing"
    )
    assert classify(outcome).verdict == "FORBIDDEN"
    assert classify("Fichier prêt à l'import, zéro rejet de routage").verdict == "FORBIDDEN"


def test_a_mechanism_said_as_a_possibility_is_safe_with_qualification() -> None:
    result = classify("Une facture électronique peut être rejetée si le SIREN est radié.")
    assert result.verdict == "SAFE_WITH_QUALIFICATION"
    assert result.findings == ()


def test_a_fact_on_record_is_factually_safe_with_its_source() -> None:
    result = classify("La réception devient obligatoire le 1er septembre 2026.")
    assert result.verdict == "FACTUALLY_SAFE"
    assert result.facts == ("fr_reception_2026",)
    assert all(fact.source.startswith(".memory/decisions.md#D-") for fact in KNOWN_FACTS)


def test_the_one_price_is_a_fact() -> None:
    assert classify("Forfait 290 € HT jusqu'à 200 fiches.").verdict == "FACTUALLY_SAFE"


def test_unrecognised_is_unsupported_not_safe() -> None:
    result = classify("Notre outil est le meilleur choix pour votre cabinet.")
    assert result.verdict == "UNSUPPORTED"
    assert "إنسان" in result.reason_ar


def test_existing_clients_are_sayable_once_a_payment_is_recorded() -> None:
    assert "existing_clients" not in {
        item.rule for item in findings("Nos clients", settled_customers=1)
    }


def test_verdict_is_the_most_severe_finding() -> None:
    result = classify("Garanti, et 40 % moins cher.")
    assert result.verdict == "FORBIDDEN"
    assert {item.verdict for item in result.findings} == {"FORBIDDEN", "UNSUPPORTED"}
    assert VERDICTS[0] == "FORBIDDEN"


def test_social_security_is_not_a_guarantee() -> None:
    """Arabic word boundaries: «الضمان الاجتماعي» is not «ضمان» the promise."""
    assert "guarantee" not in {item.rule for item in findings("الضمان الاجتماعي")}


def test_buyer_lines_reads_fences_and_quotes_only() -> None:
    text = "intro\n```\nBonjour,\n```\n> script line\n> ⛔ note au propriétaire\nnote\n"
    assert list(buyer_lines(text)) == [(3, "Bonjour,"), (5, "> script line")]


def test_the_50_euro_fine_is_not_tied_to_reception() -> None:
    """LF 2026 art. 123: 50 € per invoice (cap 15,000 €/year) punishes not *issuing* an
    e-invoice. Not being able to *receive* from 2026-09-01 costs 500 €, then 1,000 €, after
    formal notice (entreprendre.service-public.gouv.fr, A18802). Two true numbers can make
    one false sentence."""
    wrong = classify("Dès le 1er septembre 2026, sans réception électronique : 50 € par facture.")
    assert wrong.verdict == "UNSUPPORTED"
    assert "penalty_scope" in {item.rule for item in wrong.findings}
    right = classify("Une facture non émise électroniquement coûte 50 € (plafond 15 000 € par an).")
    assert right.verdict == "FACTUALLY_SAFE"


@pytest.mark.parametrize(
    "text",
    [
        "Si vous nous confiez vos fichiers, vous n'aurez plus jamais de rejet.",
        "Nous éliminons tous les rejets de routage.",
        "Aucun rejet après notre nettoyage.",
        "We eliminate every rejection.",
    ],
)
def test_an_absolute_outcome_is_forbidden_even_behind_an_if(text: str) -> None:
    """A conditional wrapper («Si …») must not launder a promise into a possibility."""
    result = classify(text)
    assert result.verdict == "FORBIDDEN", (text, result)
    assert "absolute_outcome" in {item.rule for item in result.findings}
