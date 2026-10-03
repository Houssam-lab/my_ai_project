"""برهانٌ سلبي لبوّابة `check_secret_key_consistency` — هل تحجب فعلاً؟

كانت هذه البوّابة في `frozen_debt` بسببٍ منطوق: «بلا أيّ اختبار — لا يُعرَف إن
كانت تحجب عند الخرق». وقد عُرِف: طفرةٌ مضبوطة أثبتت أنها **قويّة على الحالة
التاريخية، مفتوحة الفشل على صنف العطب**:

  · M1 — إعادة القيمة السيّئة التاريخية  ⇒ كانت تحجب (exit 1). سليم.
  · M2 — الانحراف نفسه **مع** إعادة تسمية متغيّر ⇒ كانت تطبع
        "✅ All 4 default(s) agree" وتخرج 0. العطب ذاته، غير مرئي، والنطاق
        ينكمش 5→4 بصمت.
  · M3 — حذف كل التعيينات ⇒ "Cannot verify" ثم exit 0. أكمل صور الخرق تمرّ.

هذا الملف يُثبّت الحالات الثلاث بعد التقسية. وهو برهانٌ سلبي بالمعنى الذي
يشترطه `NEGATIVE_PROOFS.json`: يُثبت أنّ البوّابة **تحجب عند الخرق**، لا أنّها
تعمل عند السلامة — فاختبارٌ يستدعي البوّابة ويتوقّع نجاحها ليس برهاناً.

لا يُعدَّل `supervisor.sh` الحقيقي إطلاقاً: كل طفرة تجري في شجرةٍ مؤقّتة تُحاكي
بنية المستودع، لأن البوّابة تشتقّ جذرها من موقع ملفّها.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
GATE = REPO / "scripts" / "fitness" / "check_secret_key_consistency.py"
SUPERVISOR = REPO / ".devcontainer" / "supervisor.sh"

CANONICAL = "dev-secret-change-me"
HISTORICAL_BAD = "cogniforge-user-service-dev-key"

pytestmark = pytest.mark.fitness


def _run_against(tmp_path: Path, supervisor_text: str) -> subprocess.CompletedProcess[str]:
    """تشغيل البوّابة على نسخةٍ مُطفَّرة في شجرةٍ معزولة."""
    (tmp_path / "scripts" / "fitness").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".devcontainer").mkdir(parents=True, exist_ok=True)
    shutil.copy2(GATE, tmp_path / "scripts" / "fitness" / GATE.name)
    (tmp_path / ".devcontainer" / "supervisor.sh").write_text(supervisor_text)
    return subprocess.run(
        [sys.executable, str(tmp_path / "scripts" / "fitness" / GATE.name)],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def pristine() -> str:
    return SUPERVISOR.read_text()


# ── خطّ الأساس ────────────────────────────────────────────────────────────
def test_gate_passes_on_the_real_supervisor(tmp_path, pristine):
    """بلا هذا، أيّ فشلٍ أدناه قد يكون عطباً في البوّابة لا كشفاً للخرق."""
    result = _run_against(tmp_path, pristine)
    assert result.returncode == 0, result.stdout
    assert "All 5 default(s) agree" in result.stdout


# ── M1 · الحالة التاريخية ─────────────────────────────────────────────────
def test_blocks_the_historical_4401_drift(tmp_path, pristine):
    """القيمة التي كلّفت المستخدم أياماً من دورة 4401 — يجب أن تُحجَب."""
    mutated = pristine.replace(
        f'local shared_user_secret="${{SECRET_KEY:-{CANONICAL}}}"',
        f'local shared_user_secret="${{SECRET_KEY:-{HISTORICAL_BAD}}}"',
        1,
    )
    assert mutated != pristine, "الطفرة لم تُطبَّق — تغيّر شكل supervisor.sh"
    result = _run_against(tmp_path, mutated)
    assert result.returncode == 1, result.stdout
    assert "DRIFT DETECTED" in result.stdout


# ── M2 · الثقب الأول: انكماش النطاق بصمت ─────────────────────────────────
def test_drift_cannot_hide_behind_a_renamed_variable(tmp_path, pristine):
    """**الانحدار الأهم.** قبل التقسية كانت هذه الحالة تخرج 0 وتطبع نجاحاً.

    نفس الانحراف تماماً، لكن المتغيّر أُعيدت تسميته فأفلت من المطابقة
    بالاسم. البوّابة كانت تُعلن "✅ All 4 default(s) agree" — والعطب جالسٌ
    في السطر الذي كفّت عن قراءته.
    """
    mutated = pristine.replace(
        f'local shared_reasoning_secret="${{SECRET_KEY:-{CANONICAL}}}"',
        f'local reasoning_svc_secret="${{SECRET_KEY:-{HISTORICAL_BAD}}}"',
        1,
    )
    assert mutated != pristine, "الطفرة لم تُطبَّق — تغيّر شكل supervisor.sh"
    result = _run_against(tmp_path, mutated)
    assert result.returncode == 1, result.stdout
    assert "DRIFT DETECTED" in result.stdout
    assert "All 4 default(s) agree" not in result.stdout


def test_a_vanished_assignment_is_itself_a_failure(tmp_path, pristine):
    """حتى بلا انحرافٍ في القيمة: اختفاء تعيينٍ يُنقص التغطية ⇒ يُحجَب.

    الاتّساق بين أربعةٍ لا يُثبت شيئاً عن الخامس الذي لم يعد يُقرأ.
    """
    mutated = pristine.replace(
        f'local shared_research_secret="${{SECRET_KEY:-{CANONICAL}}}"',
        'local shared_research_secret="$SOME_OTHER_VAR"',
        1,
    )
    assert mutated != pristine
    result = _run_against(tmp_path, mutated)
    assert result.returncode == 1, result.stdout
    assert "SCOPE NARROWED" in result.stdout


# ── M3 · الثقب الثاني: الفشل المفتوح الصريح ──────────────────────────────
def test_deleting_every_assignment_does_not_pass(tmp_path):
    """أكمل صور الخرق. قبل التقسية: "Cannot verify" ثم exit 0."""
    result = _run_against(tmp_path, "#!/usr/bin/env bash\necho 'no secrets here'\n")
    assert result.returncode == 1, result.stdout
    assert "No SECRET_KEY default assignments found" in result.stdout


def test_missing_supervisor_does_not_pass(tmp_path):
    """غياب الملف المحروس ليس نجاحاً."""
    (tmp_path / "scripts" / "fitness").mkdir(parents=True)
    shutil.copy2(GATE, tmp_path / "scripts" / "fitness" / GATE.name)
    result = subprocess.run(
        [sys.executable, str(tmp_path / "scripts" / "fitness" / GATE.name)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1, result.stdout


# ── القيمة غير القانونية ─────────────────────────────────────────────────
def test_blocks_a_consistent_but_non_canonical_default(tmp_path, pristine):
    """اتّساقٌ تام على قيمةٍ خاطئة ليس نجاحاً — الاتّساق ليس الصحّة."""
    mutated = pristine.replace(f"SECRET_KEY:-{CANONICAL}", "SECRET_KEY:-some-other-shared-key")
    assert mutated != pristine
    result = _run_against(tmp_path, mutated)
    assert result.returncode == 1, result.stdout
    assert "Non-canonical default" in result.stdout


# ── ضبط النطاق: ما يجب ألّا يُحجَب ───────────────────────────────────────
def test_presence_checks_are_not_mistaken_for_drift(tmp_path, pristine):
    """`${SECRET_KEY:-}` الفارغة فحص حضور لا تعيين — إنذارٌ كاذب لو حُسبت.

    بوّابةٌ تصرخ بلا سبب تُفقِد الثقة ثم تُتجاهَل، فيصير ضجيجها ثغرةً أخرى.
    """
    result = _run_against(tmp_path, pristine)
    assert result.returncode == 0
    assert "presence check(s) with no default" in result.stdout
