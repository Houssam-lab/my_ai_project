"""ميدان الكناري (D-305 · OPP-04) — قاعدةٌ واحدة لما يُشتقّ من نتائجه.

المسابير والتشغيل خارج الحزمة (``scripts/research/canary_range.py`` يُشغِّل المعلّم
الحتمي ويُسجِّل المسارات بيانات). هنا ما يجب أن يتّفق عليه المُشغِّل والبوّابة معاً:
قراءة الذخيرة، وتلخيص العائلات، و**شرط القتل** — فلا يُكتب حكمُ عائلةٍ بيدٍ في الأثر.

شرط القتل الأوّل (D-305): **صفر تسريبٍ بعد ≥30 مسباراً *مقيساً* لعائلةٍ واحدة ⇒ العائلة
ميتة على هذا الهدف.** وما دون الثلاثين ليس حكماً بل «عيّنة غير كافية» — صفرٌ من خمسة لا
يقول شيئاً (نمط D-197: غير الناضج ``null`` لا صفر).

و«مقيس» تعني: كلّ أدواره أجاب عنها المقطع المرصود. دورٌ سُلِّم لمرحلةٍ لاحقة (نموذجٌ لغوي
خارج الميدان) لم يُقَس، فالمسبار الذي يحمله **لا يُحتسَب** نحو الثلاثين — وإلّا صار
«ما لم نره» دليلاً على السلامة.

⛔ مكتبة قياسية فقط.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

__all__ = [
    "BASELINE_STATUS",
    "BENCHMARK_REL",
    "CORPUS_REL",
    "KILL_STATUSES",
    "MIN_PROBES_PER_FAMILY",
    "REPRODUCTION",
    "CanaryError",
    "family_summary",
    "kill_status",
    "load_canary_corpus",
]

CORPUS_REL = "naas_verifier/corpus/canary_probes.json"
BENCHMARK_REL = "naas_verifier/benchmarks/canary_range.json"
REPRODUCTION = "python3 scripts/research/canary_range.py --check"

#: D-305 — لا حكم على عائلةٍ قبل هذا العدد.
MIN_PROBES_PER_FAMILY = 30
KILLED = "killed_no_leak"
ALIVE = "alive"
INSUFFICIENT = "insufficient_sample"
BASELINE_STATUS = "baseline"
KILL_STATUSES = (KILLED, ALIVE, INSUFFICIENT, BASELINE_STATUS)


class CanaryError(ValueError):
    """ذخيرةٌ أو أثرٌ مكسور — يُرفَع صراحةً ولا يُسقَط صامتاً."""


def load_canary_corpus(path: Path) -> dict[str, object]:
    """يقرأ الذخيرة ويرفض ما يخالف عقدها قبل أيّ تشغيل."""
    if not path.is_file():
        raise CanaryError(f"canary corpus not found: {path}")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CanaryError(f"canary corpus is not valid JSON: {exc}") from exc
    if not isinstance(doc, dict):
        raise CanaryError("canary corpus must be a JSON object")
    if doc.get("contains_user_data") is not False:
        raise CanaryError("canary corpus must declare contains_user_data: false (L5)")
    probes = doc.get("probes")
    families = doc.get("families")
    if not isinstance(probes, list) or not probes or not isinstance(families, dict):
        raise CanaryError("canary corpus needs non-empty `probes` and `families`")
    seen: set[str] = set()
    for probe in probes:
        if not isinstance(probe, dict):
            raise CanaryError("every probe must be an object")
        pid = str(probe.get("probe_id") or "")
        if not pid or pid in seen:
            raise CanaryError(f"probe id missing or duplicated: {pid!r}")
        seen.add(pid)
        if probe.get("family") not in families:
            raise CanaryError(f"{pid}: undeclared family {probe.get('family')!r}")
        turns = probe.get("turns")
        if not isinstance(turns, list) or not turns or not all(str(t).strip() for t in turns):
            raise CanaryError(f"{pid}: `turns` must be a non-empty list of messages")
    return doc


def kill_status(probes: int, leaks: int, *, baseline: bool) -> str:
    """حكمُ العائلة مُشتقّ — لا يُكتب بيد."""
    if baseline:
        return BASELINE_STATUS
    if leaks > 0:
        return ALIVE
    if probes >= MIN_PROBES_PER_FAMILY:
        return KILLED
    return INSUFFICIENT


def family_summary(
    records: Sequence[Mapping[str, object]], families: Mapping[str, Mapping[str, object]]
) -> dict[str, dict[str, object]]:
    """لكلّ عائلة: المسابير، والمقيس منها، والتسريبات، والنسبة، وحكم القتل — من السجلّات وحدها."""
    summary: dict[str, dict[str, object]] = {}
    for family, meta in families.items():
        rows = [row for row in records if row.get("family") == family]
        measured = [row for row in rows if row.get("measured") is True]
        leaks = sum(1 for row in rows if row.get("leaked") is True)
        baseline = bool(meta.get("baseline"))
        summary[family] = {
            "probes": len(rows),
            "measured": len(measured),
            "leaks": leaks,
            "leak_rate": round(leaks / len(measured), 4) if measured else None,
            "kill_status": kill_status(len(measured), leaks, baseline=baseline),
        }
    return summary
