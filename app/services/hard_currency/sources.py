"""مصادر المركز وأخطاؤه المُعلَنة — موطنٌ واحد للمسارات والحدود (D-305)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

#: جذر المستودع — المركز يقرأ ملفّاته المصدرية وقت الطلب ولا ينسخها (D-192).
REPO_ROOT = Path(__file__).resolve().parents[3]


class SourceUnavailableError(Exception):
    """مصدرٌ غائب أو غير مقروء في هذا النشر ⇒ 503 بسببٍ منطوق، لا قائمةٌ فارغة تُقرأ «لا شيء»."""

    def __init__(self, reason_ar: str) -> None:
        super().__init__(reason_ar)
        self.reason_ar = reason_ar


class InputRejectedError(Exception):
    """مُدخَلٌ مرفوض بسببه — الرمز يحمل الصنف (413 · 415 · 422 · 404)."""

    def __init__(self, status_code: int, reason_ar: str) -> None:
        super().__init__(reason_ar)
        self.status_code = status_code
        self.reason_ar = reason_ar


@dataclass(frozen=True)
class HardCurrencySources:
    """جذرٌ قابلٌ للحقن — الاختبارات تمرّر مستودعاً مصغّراً بدل الحقيقي."""

    root: Path = REPO_ROOT

    def path(self, rel: str) -> Path:
        return self.root / rel

    def read_text(self, rel: str) -> str:
        try:
            return self.path(rel).read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise SourceUnavailableError(f"المصدر غير موجود في هذا النشر: {rel}") from exc
        except OSError as exc:
            raise SourceUnavailableError(f"تعذّرت قراءة المصدر: {rel}") from exc

    def read_json(self, rel: str) -> dict[str, object]:
        text = self.read_text(rel)
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise SourceUnavailableError(f"المصدر ليس JSON صالحاً: {rel}") from exc
        if not isinstance(payload, dict):
            raise SourceUnavailableError(f"جذر المصدر ليس كائناً: {rel}")
        return payload


def get_hard_currency_sources() -> HardCurrencySources:
    """تبعية FastAPI — تُستبدَل في الاختبارات بـ``dependency_overrides``."""
    return HardCurrencySources()
