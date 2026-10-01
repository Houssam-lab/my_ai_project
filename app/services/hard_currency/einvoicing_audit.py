"""ورشة الفوترة FR/BE — غلافٌ رفيع فوق ``tools/hard_currency_engine`` بلا إعادة كتابة منطق (D-305).

**ما يضيفه الغلاف وحده:** حدود المُدخَل (الحجم · الصفوف · الامتداد)، وتحييد حقن الصيغ في
الملفّ المنظَّف (خليّةٌ تبدأ بـ``= + - @`` تُنفَّذ صيغةً حين يفتحها مكتب المحاسبة في Excel)،
وأنّ الملفّ **لا يُخزَّن**: يُكتب في دليلٍ مؤقّت يُحذَف بخروج الدالّة، ولا سطرٌ منه في السجلّ.

الأداة تُستورَد كسولاً: صورة الإنتاج (``Dockerfile.prod``) لا تحمل ``tools/``، وغيابها يُعلَن
503 بسببه — لا يُسقط إقلاع المونوليث ولا يتظاهر بنتيجة.
"""

from __future__ import annotations

import re
import tempfile
from collections.abc import Callable
from datetime import date
from pathlib import Path

from app.services.hard_currency.sources import InputRejectedError, SourceUnavailableError

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_ROWS = 5000
MAX_ANOMALIES_RETURNED = 500
CORRIDORS = ("fr", "be")
#: محارف تجعل الخليّة صيغةً في جداول البيانات (OWASP CSV Injection).
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
_SAFE_NAME = re.compile(r"[^\w.\- ]+", re.UNICODE)


def neutralize_cell(value: object) -> object:
    """``=HYPERLINK(...)`` ⇒ ``'=HYPERLINK(...)`` — يبقى النصّ ويسقط التنفيذ."""
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


def safe_display_name(filename: str) -> str:
    """اسمٌ للعرض فقط — لا يُستعمل مساراً أبداً."""
    base = Path(filename or "").name
    cleaned = _SAFE_NAME.sub("_", base).strip() or "fichier.csv"
    return cleaned[:100]


def _validate_input(corridor: str, filename: str, content: bytes) -> None:
    if corridor not in CORRIDORS:
        raise InputRejectedError(
            422, f"ممرٌّ غير معروف: {corridor!r} (المسموح: {', '.join(CORRIDORS)})"
        )
    if not (filename or "").lower().endswith(".csv"):
        raise InputRejectedError(415, "CSV فقط — ملفّات Excel تُصدَّر CSV أوّلاً")
    if not content:
        raise InputRejectedError(422, "الملفّ فارغ")
    if len(content) > MAX_UPLOAD_BYTES:
        raise InputRejectedError(413, f"الملفّ أكبر من {MAX_UPLOAD_BYTES // (1024 * 1024)} م.ب")
    if b"\x00" in content:
        raise InputRejectedError(415, "ملفٌّ ثنائي لا نصّ CSV")
    if content.count(b"\n") > MAX_ROWS:
        raise InputRejectedError(413, f"أكثر من {MAX_ROWS} سطر — يُقسَّم الملفّ")


def _engine(corridor: str) -> tuple[Callable, Callable, Callable]:
    try:
        if corridor == "fr":
            from tools.hard_currency_engine.france_validator import (
                audit_french_csv,
                export_cleaned_french_csv,
                format_french_report,
            )

            return audit_french_csv, export_cleaned_french_csv, format_french_report
        from tools.hard_currency_engine.belgium_validator import (
            audit_belgian_csv,
            export_cleaned_belgian_csv,
            format_belgian_report,
        )

        return audit_belgian_csv, export_cleaned_belgian_csv, format_belgian_report
    except ImportError as exc:
        raise SourceUnavailableError(
            "أدوات الفوترة غير موجودة في هذا النشر (tools/hard_currency_engine)"
        ) from exc


def run_audit(
    *, corridor: str, filename: str, content: bytes, report_date: date | None = None
) -> dict[str, object]:
    """تدقيقٌ حتمي بلا شبكة — الملفّ لا يُخزَّن، والنتيجة أعدادٌ وشذوذاتٌ وتقرير وملفٌّ منظَّف."""
    _validate_input(corridor, filename, content)
    audit, export, report = _engine(corridor)
    display = safe_display_name(filename)

    with tempfile.TemporaryDirectory(prefix="hc-audit-") as tmp:
        source = Path(tmp) / "input.csv"
        source.write_bytes(content)
        results = audit(source)
        results["annotees"] = [
            {key: neutralize_cell(value) for key, value in row.items()}
            for row in results.get("annotees", [])
        ]
        cleaned = export(results, Path(tmp) / "cleaned.csv")
        cleaned_text = cleaned.read_text(encoding="utf-8-sig")
        report_md = report(results, display, report_date=report_date)

    anomalies = list(results.get("anomalies", []))
    summary = {
        key: value
        for key, value in results.items()
        if key not in {"anomalies", "annotees"} and isinstance(value, (int, bool))
    }
    return {
        "corridor": corridor,
        "filename": display,
        "summary": summary,
        "anomalies": anomalies[:MAX_ANOMALIES_RETURNED],
        "anomalies_truncated": len(anomalies) > MAX_ANOMALIES_RETURNED,
        "report_markdown": report_md,
        "cleaned_csv": cleaned_text,
        "cleaned_filename": f"{Path(display).stem}_ASSAINI.csv",
        "stored": False,
        "online_checks": False,
    }
