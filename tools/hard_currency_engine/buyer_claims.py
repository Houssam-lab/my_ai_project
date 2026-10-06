"""What the owner may say to a buyer — the D-304 rules in one home (D-314).

**Why this module exists.** D-304 found unmeasured trends ("les factures sont rejetées à
cause de SIREN erronés"), guarantees ("garantir un routage sans échec"), three different
prices and a VAT number that belonged to another company — in texts sent under the owner's
name. Those rules lived inside one test, so nothing else could ask "can we say this?".
The Decision Chamber (D-314) asks it of any sentence the owner types, and the outreach test
asks it of the files the owner sends. One rule set, two callers.

**The verdicts** (most severe first):

- ``FORBIDDEN`` — a guarantee, a zero-failure outcome, a wrong identifier, a forbidden
  superlative. No qualification makes it sayable.
- ``UNSUPPORTED`` — a rate, a price other than the owner's one price, a claim about existing
  clients while no payment is recorded; or a sentence no rule recognised (a human judges it —
  silence from the linter is not approval).
- ``HYPOTHESIS_ONLY`` — a trend stated as observed ("augmentent", "la plupart"). Say the
  mechanism instead: "une facture peut être rejetée si…".
- ``SAFE_WITH_QUALIFICATION`` — stated as a possibility ("peut", "si"), with no finding.
- ``FACTUALLY_SAFE`` — matches a fact on record (``KNOWN_FACTS``) and nothing else fires.

⛔ No network, no LLM: these are lexical rules. They catch the shapes D-304 found; a claim
phrased without any of them is ``UNSUPPORTED``, not safe.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from shared.research.value_chain import FORBIDDEN_TERMS
from tools.hard_currency_engine.france_validator import tva_fr_check

__all__ = [
    "EURO_RANGE",
    "KNOWN_FACTS",
    "PACKAGE_PRICE",
    "VERDICTS",
    "Finding",
    "KnownFact",
    "Verdict",
    "buyer_lines",
    "classify",
    "findings",
    "identifier_mismatches",
]

FORBIDDEN = "FORBIDDEN"
UNSUPPORTED = "UNSUPPORTED"
HYPOTHESIS_ONLY = "HYPOTHESIS_ONLY"
SAFE_WITH_QUALIFICATION = "SAFE_WITH_QUALIFICATION"
FACTUALLY_SAFE = "FACTUALLY_SAFE"

#: Most severe first — the verdict of a text is the most severe of its findings.
VERDICTS: tuple[str, ...] = (
    FORBIDDEN,
    UNSUPPORTED,
    HYPOTHESIS_ONLY,
    SAFE_WITH_QUALIFICATION,
    FACTUALLY_SAFE,
)

#: The one package price the owner chose on 2026-09-30 (D-304).
PACKAGE_PRICE = "290 €"

_TVA = re.compile(r"\bFR ?\d{2} ?\d{3} ?\d{3} ?\d{3}\b")
_SIREN_AFTER_LABEL = re.compile(r"SIREN\W{0,6}(\d{3} ?\d{3} ?\d{3})\b")
#: A euro range ("290–390 €") — the shape of the three-prices defect (D-304 C5).
EURO_RANGE = re.compile(r"\d[\d  ]*\s?[–-]\s?\d[\d  ]*\s?€")
#: Arabic has no \b worth trusting next to a prefix; a word is not preceded or followed by one.
_AR_WORD = r"(?<!\w)({})(?!\w)"


@dataclass(frozen=True)
class _Rule:
    rule: str
    verdict: str
    pattern: re.Pattern[str]
    reason_ar: str


_I = re.IGNORECASE

#: Each rule names the D-304 class it comes from.
_RULES: tuple[_Rule, ...] = (
    _Rule(
        "guarantee",
        FORBIDDEN,
        re.compile(
            r"garanti|guarantee|\bensures?\b|" + _AR_WORD.format("مضمون|نضمن|ضمان|بضمان"), _I
        ),
        "ضمانٌ لنتيجةٍ لم تُقَس (D-304 C8)",
    ),
    _Rule(
        "zero_failure",
        FORBIDDEN,
        re.compile(
            r"sans (aucun |aucune )?(échec|rejet|erreur)|z[ée]ro (rejet|erreur|échec)"
            r"|\bzero (rejection|errors?|failures?)\b|without (any )?(errors?|rejections?)"
            r"|صفر (رفض|خطأ|أخطاء)|بلا (رفض|أخطاء)|100 ?%",
            _I,
        ),
        "نتيجةٌ بلا فشلٍ تُقال يقيناً — لم يُقَس أيّ ملفٍّ حقيقي (D-300)",
    ),
    _Rule(
        "absolute_outcome",
        FORBIDDEN,
        re.compile(
            r"plus jamais|jamais plus|aucun rejet|aucune erreur|tous les rejets|toutes les erreurs"
            r"|[ée]limin(e|ons|ez|er)\b|never again|eliminat\w*|every rejection|all rejections"
            r"|no more rejections|لن تُرفَض|لن ترفض|أيّ رفض بعد|نهائياً",
            _I,
        ),
        "وعدٌ مطلق بنتيجة — وصيغة الشرط («إذا…») لا تحوّله احتمالاً (D-314)",
    ),
    _Rule(
        "unmeasured_rate",
        UNSUPPORTED,
        re.compile(r"%|pour ?cent|percent|بالمئة|بالمائة|في المئة", _I),
        "نسبةٌ بلا قياس — نسبة الأخطاء في الملفّات الحقيقية مجهولة (D-304 C7)",
    ),
    _Rule(
        "existing_clients",
        UNSUPPORTED,
        re.compile(
            r"nos clients|clients satisfaits|déjà utilisé|our (customers|clients)"
            r"|trusted by|عملاؤنا|زبائننا",
            _I,
        ),
        "حديثٌ عن عملاء قائمين — يتطلّب PAYMENT_SETTLED في السجلّ",
    ),
    _Rule(
        "observed_trend",
        HYPOTHESIS_ONLY,
        re.compile(
            r"augment|de plus en plus|la plupart|la majorité|majoritairement|souvent"
            r"|significati|premier (facteur|blocage)|fortement|increasingly|most (firms|companies)"
            r"|في تزايد|أغلب|معظم",
            _I,
        ),
        "اتّجاهٌ يُقال مُلاحَظاً بلا قياس — قُل الآلية: «يمكن أن تُرفَض الفاتورة إذا…» (D-304 C7)",
    ),
)

_QUALIFIED = re.compile(
    r"\bpeu(t|vent)\b|\bpourrai(t|ent)\b|\bsi\b|\bmay\b|\bcan\b|\bmight\b|\bif\b|"
    + _AR_WORD.format("يمكن|قد|إذا|إن"),
    _I,
)


@dataclass(frozen=True)
class KnownFact:
    fact_id: str
    pattern: re.Pattern[str]
    statement_ar: str
    source: str


#: Facts on record that a buyer sentence may state plainly. Each one names its source;
#: a sentence that matches one and trips no rule is FACTUALLY_SAFE.
KNOWN_FACTS: tuple[KnownFact, ...] = (
    KnownFact(
        "fr_reception_2026",
        re.compile(r"(1(er)? septembre 2026|2026-09-01|01/09/2026)", _I),
        "استقبال الفواتير الإلكترونية إلزاميٌّ في فرنسا منذ 2026-09-01",
        ".memory/decisions.md#D-300",
    ),
    KnownFact(
        "fr_issuance_pme_2027",
        re.compile(r"(1(er)? septembre 2027|2027-09-01|01/09/2027)", _I),
        "الإصدار إلزاميٌّ للـPME في 2027-09-01",
        ".memory/decisions.md#D-300",
    ),
    KnownFact(
        "fr_penalty",
        re.compile(r"50 ?€.{0,40}15[  .]?000 ?€", _I),
        "50 € لكلّ فاتورةٍ لم تُصدَر إلكترونياً بسقف 15,000 €/سنة (قانون المالية 2026 م123) — للإصدار لا للاستقبال",
        ".memory/decisions.md#D-300",
    ),
    KnownFact(
        "package_price",
        re.compile(re.escape(PACKAGE_PRICE)),
        "السعر الواحد 290 € HT حتى 200 سجلّ",
        ".memory/decisions.md#D-304",
    ),
)


@dataclass(frozen=True)
class Finding:
    rule: str
    verdict: str
    excerpt: str
    reason_ar: str


@dataclass(frozen=True)
class Verdict:
    verdict: str
    findings: tuple[Finding, ...]
    facts: tuple[str, ...]
    reason_ar: str


def identifier_mismatches(line: str) -> list[str]:
    """A TVA printed on the same line as a labelled SIREN must carry that SIREN (D-304 C12)."""
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


#: LF 2026 art. 123 (entreprendre.service-public.gouv.fr, A18802): 50 € per invoice punishes
#: not *issuing* an e-invoice; not being able to *receive* costs 500 € then 1,000 € after
#: formal notice. Two true numbers can make one false sentence.
_RECEPTION = re.compile(r"réception|recevoir|reçu|receiv|استقبال|تلقّي", _I)
_FIFTY_EUROS = re.compile(r"(?<![\d.,])50 ?€")


def findings(text: str, *, settled_customers: int = 0) -> list[Finding]:
    """Every rule the text trips — all of them, not the first."""
    found: list[Finding] = []
    if _RECEPTION.search(text) and (fifty := _FIFTY_EUROS.search(text)):
        found.append(
            Finding(
                "penalty_scope",
                UNSUPPORTED,
                fifty.group(0),
                "غرامة 50 € للفاتورة تخصّ عدم الإصدار؛ عدم القدرة على الاستقبال 500 € ثمّ 1,000 € بعد إنذار (LF 2026 م123)",
            )
        )
    for rule in _RULES:
        if rule.rule == "existing_clients" and settled_customers > 0:
            continue
        for match in rule.pattern.finditer(text):
            found.append(Finding(rule.rule, rule.verdict, match.group(0), rule.reason_ar))
    lowered = text.lower()
    for term in FORBIDDEN_TERMS:
        if term.lower() in lowered:
            found.append(
                Finding("forbidden_term", FORBIDDEN, term, "وصفٌ ممنوع دون دليلٍ تجاري (D-305)")
            )
    for problem in identifier_mismatches(text):
        found.append(
            Finding("identifier_mismatch", FORBIDDEN, problem, "معرّفٌ لا يطابق صاحبه (D-304 C12)")
        )
    for match in EURO_RANGE.finditer(text):
        found.append(
            Finding(
                "price_range",
                UNSUPPORTED,
                match.group(0),
                "المالك قرّر سعراً واحداً لا نطاقاً (D-304 C5)",
            )
        )
    return found


def classify(text: str, *, settled_customers: int = 0) -> Verdict:
    """The verdict of one buyer-facing text. Unrecognised is UNSUPPORTED, never safe."""
    found = tuple(findings(text, settled_customers=settled_customers))
    facts = tuple(fact.fact_id for fact in KNOWN_FACTS if fact.pattern.search(text))
    if found:
        worst = min(found, key=lambda item: VERDICTS.index(item.verdict))
        return Verdict(worst.verdict, found, facts, worst.reason_ar)
    if facts:
        return Verdict(FACTUALLY_SAFE, found, facts, "يطابق حقيقةً مسجّلة بمصدرها")
    if _QUALIFIED.search(text):
        return Verdict(SAFE_WITH_QUALIFICATION, found, facts, "يُقال احتمالاً بآليته لا قياساً")
    return Verdict(
        UNSUPPORTED,
        found,
        facts,
        "لم تتعرّف عليه أيّ قاعدة — يحكم فيه إنسان؛ صمت المُدقِّق ليس موافقة",
    )


def buyer_lines(text: str) -> Iterable[tuple[int, str]]:
    """Lines a buyer reads: inside code fences (emails, profile) and ``>`` quotes (scripts).

    A line carrying ⛔ is a note to the owner, not buyer text — the law must be able to name
    what it forbids (the ``value_chain`` convention, D-208 §7).
    """
    inside = False
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            inside = not inside
            continue
        if (inside or line.lstrip().startswith(">")) and "⛔" not in line:
            yield number, line
