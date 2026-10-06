"""غرفة القرار (D-314) — الطبقة الرقيقة بين مصادر المركز وآلة الحقيقة الاقتصادية.

الحساب كلّه في ``shared/research/economic_truth`` و``economic_decision``؛ هنا القراءة من
المصادر المحقونة، وحقن مُدقِّق نصّ المشتري (``tools`` — ``shared`` لا يستورده)، والامتناع.

**الغرفة تمتنع ولا تتجاوز:** إن رفض المُدقِّق جملةً واحدة من جملها هي، لا تُعرَض الشاشة —
503 بالسبب. شاشةٌ تقول ما لا يسنده دليلٌ أسوأ من شاشةٍ لا تقول شيئاً.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from types import ModuleType

from app.services.hard_currency.sources import (
    HardCurrencySources,
    InputRejectedError,
    SourceUnavailableError,
)
from shared.research.contact_ledger import ACTIONS, CHANNELS, LEDGER_REL, SCORECARD_REL
from shared.research.economic_decision import (
    QUESTIONS,
    build_brief,
    cross_examine,
    preview_outcome,
    render_sentences,
    sentence_problems,
)
from shared.research.economic_truth import build_snapshot
from shared.research.value_chain import CATALOG_REL, VALUE_CHAIN_REL

#: نصّ المشتري المعروض للاستجواب — جملٌ لا وثائق.
MAX_BUYER_TEXT_CHARS = 2000

#: سبب الامتناع حين يغيب المُدقِّق — نصٌّ واحد لموضعَي الاستعمال.
LINTER_ABSENT_AR = "مُدقِّق نصّ المشتري غير موجود في هذا النشر (tools/hard_currency_engine)"


def _buyer_claims() -> ModuleType | None:
    """المُدقِّق يُحمَّل عند الطلب لا في رأس الوحدة — نمط ``einvoicing_audit._engine``.

    صورة الإنتاج (``Dockerfile.prod``) تنسخ ``app/`` و``shared/`` ولا تنسخ ``tools/``؛ فاستيراده
    في رأس الوحدة أسقط إقلاع المونوليث كلّه (``image: monolith`` في PR #2595). غيابه يُعلَن:
    اللقطة تقول ``wording_checked=false``، وسؤال «هل نقول هذا للمشتري؟» يمتنع بـ503.
    """
    try:
        from tools.hard_currency_engine import buyer_claims
    except ImportError:
        return None
    return buyer_claims


def _linter() -> ModuleType:
    module = _buyer_claims()
    if module is None:
        raise SourceUnavailableError(LINTER_ABSENT_AR)
    return module


def _wording(text: str) -> list[tuple[str, str, str]]:
    return [(item.rule, item.verdict, item.excerpt) for item in _linter().findings(text)]


def _wording_or_none() -> Callable[[str], list[tuple[str, str, str]]] | None:
    return _wording if _buyer_claims() is not None else None


def _classify(text: str) -> tuple[str, str, list[tuple[str, str]]]:
    verdict = _linter().classify(text)
    return verdict.verdict, verdict.reason_ar, [(f.rule, f.excerpt) for f in verdict.findings]


@dataclass(frozen=True)
class _Inputs:
    chain_doc: dict[str, object]
    ledger_text: str
    catalog: dict[str, object]
    scorecard: dict[str, object]


def _inputs(sources: HardCurrencySources) -> _Inputs:
    return _Inputs(
        chain_doc=sources.read_json(VALUE_CHAIN_REL),
        ledger_text=sources.read_text(LEDGER_REL),
        catalog=sources.read_json(CATALOG_REL),
        scorecard=sources.read_json(SCORECARD_REL),
    )


def _snapshot(sources: HardCurrencySources, today: date | None) -> dict[str, object]:
    inputs = _inputs(sources)
    return build_snapshot(
        chain_doc=inputs.chain_doc,
        ledger_text=inputs.ledger_text,
        catalog=inputs.catalog,
        scorecard=inputs.scorecard,
        root=sources.root,
        today=today or date.today(),
        wording=_wording_or_none(),
    )


def _guard(sentences: Sequence[Mapping[str, object]], snapshot: Mapping[str, object]) -> None:
    evidence = snapshot.get("evidence")
    problems = sentence_problems(sentences, evidence if isinstance(evidence, list) else [])
    if problems:
        raise SourceUnavailableError(
            "الغرفة امتنعت: جملٌ تتجاوز دليلها — " + " · ".join(problems[:3])
        )


def chamber(sources: HardCurrencySources, *, today: date | None = None) -> dict[str, object]:
    """الشاشة الأولى: الحقيقة، والموجز، والجمل — أو امتناعٌ بسببه."""
    snapshot = _snapshot(sources, today)
    brief = build_brief(snapshot)
    sentences = render_sentences(snapshot, brief)
    _guard(sentences, snapshot)
    return {
        "snapshot": snapshot,
        "brief": brief,
        "sentences": sentences,
        "questions": list(QUESTIONS),
        # مجموعتا السجلّ المغلقتان من موطنهما — الواجهة لا تحمل نسخةً ثانية (D-192).
        "ledger_vocabulary": {"actions": sorted(ACTIONS), "channels": sorted(CHANNELS)},
    }


def examine(
    sources: HardCurrencySources,
    question: str,
    text: str | None,
    *,
    today: date | None = None,
) -> dict[str, object]:
    if question not in QUESTIONS:
        raise InputRejectedError(422, f"سؤالٌ خارج المجموعة المغلقة: {question}")
    if question == "say_to_buyer" and not (text or "").strip():
        raise InputRejectedError(422, "say_to_buyer يتطلّب نصّاً")
    if text is not None and len(text) > MAX_BUYER_TEXT_CHARS:
        raise InputRejectedError(413, f"النصّ أطول من {MAX_BUYER_TEXT_CHARS} حرفاً")
    snapshot = _snapshot(sources, today)
    answer = cross_examine(
        question, snapshot, build_brief(snapshot), text=text, classify_text=_classify
    )
    sentences = answer.get("sentences")
    _guard(sentences if isinstance(sentences, list) else [], snapshot)
    return {"verdict": None, "findings": None, **answer}


def preview(
    sources: HardCurrencySources, row: Mapping[str, str], *, today: date | None = None
) -> dict[str, object]:
    """⛔ لا كتابة: السطر والفرق و``written: false`` — المالك يلتزم عبر git."""
    inputs = _inputs(sources)
    return preview_outcome(
        row=row,
        chain_doc=inputs.chain_doc,
        ledger_text=inputs.ledger_text,
        catalog=inputs.catalog,
        scorecard=inputs.scorecard,
        root=sources.root,
        today=today or date.today(),
        wording=_wording_or_none(),
    )
