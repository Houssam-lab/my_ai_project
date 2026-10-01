"""أصناف الاختراق العربي/الفرنسي — تُقرأ بياناتٍ من ملفّ الذخيرة، لا استيراداً (D-305 · L5).

⛔ ``app/`` لا يستورد ``naas_verifier`` أبداً (``check_naas_verifier_boundary``). والمسابير
نفسها لا تُعاد: الواجهة تعرض الجذر وحالة النشر وسببها فقط — للمدير وحده، بعيداً عن مسار الطالب.
"""

from __future__ import annotations

from app.services.hard_currency.sources import HardCurrencySources

CORPUS_REL = "naas_verifier/corpus/ar_fr_exploit_classes.json"
EXTERNAL_PROBE_REL = "docs/research/EXTERNAL_GUARD_PROBE.json"


def _external_probe(sources: HardCurrencySources) -> dict[str, object] | None:
    if not sources.path(EXTERNAL_PROBE_REL).exists():
        return None
    probe = sources.read_json(EXTERNAL_PROBE_REL)
    target = probe.get("target") or {}
    return {
        "decision": probe.get("decision"),
        "target_package": target.get("package") if isinstance(target, dict) else None,
        "classes_measured": probe.get("classes_measured"),
        "classes_violated": probe.get("classes_violated"),
        "honest_limits_ar": probe.get("honest_limits_ar"),
        "source": EXTERNAL_PROBE_REL,
    }


def list_classes(sources: HardCurrencySources) -> dict[str, object]:
    corpus = sources.read_json(CORPUS_REL)
    classes = [
        {
            "class_id": item.get("class_id"),
            "title_ar": item.get("title_ar"),
            "title_en": item.get("title_en"),
            "root_cause": item.get("root_cause"),
            "language_conditioned": bool(item.get("language_conditioned")),
            "publishable": bool(item.get("publishable")),
            "publish_block_reason_ar": item.get("publish_block_reason_ar") or None,
            "sources": item.get("sources") or [],
        }
        for item in corpus.get("classes", []) or []  # type: ignore[union-attr]
        if isinstance(item, dict)
    ]
    return {
        "source": CORPUS_REL,
        "decision": corpus.get("decision"),
        "classes": classes,
        "publishable_count": sum(1 for item in classes if item["publishable"]),
        "external_probe": _external_probe(sources),
    }
