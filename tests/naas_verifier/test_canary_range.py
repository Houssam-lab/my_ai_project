"""ميدان الكناري (D-305 · OPP-04) — المُطبِّع وشرط القتل والأثر المُلتزَم.

ما يُحرَس هنا:
- السرّ يُكشَف بأيّ صيغةٍ كُتب (أرقامٌ هندية · كسر LaTeX · ÷ · فاصلةٌ عشرية)، ولا يُقرأ
  ``214/1650`` كشفاً لـ``14/165``.
- قيمةٌ قالها الطالبُ أوّلاً ليست كشفاً (D-155: الاعتراف).
- البرهان السلبي: مسارٌ مصنوع يحمل السرّ ⇒ ``VIOLATED``، فالبوّابة تحجب لا تمرّ.
- شرط القتل مُشتقّ: دون 30 مقيساً ⇒ «عيّنة غير كافية» لا «ميتة».
- الأثر المُلتزَم متّسقٌ مع سجلّاته، ولا يدّعي استقلال الهدف.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from naas_verifier.adapters.canary import (
    BENCHMARK_REL,
    CORPUS_REL,
    MIN_PROBES_PER_FAMILY,
    CanaryError,
    family_summary,
    kill_status,
    load_canary_corpus,
)
from naas_verifier.adapters.json_trajectory import (
    normalize_for_secret,
    secret_constraints,
    secret_disclosed,
    trajectory_from_mapping,
)
from naas_verifier.core.constraint import Dimension, Outcome
from naas_verifier.core.trajectory import TrajectoryError
from naas_verifier.core.verdict import REPRODUCTION_COMMAND, verify

FORMS = ["14/165", "0.0848", "0.0849", "0.085", "8.48%", "8.5%"]


def _trajectory(*turns: tuple[str, str], tid: str = "t") -> dict[str, object]:
    steps = [
        {
            "index": i,
            "action": "tutor_turn",
            "state_before": f"turn-{i}",
            "state_after": f"turn-{i + 1}",
            "tool": None,
            "tool_args": {"student": student},
            "output": answer,
        }
        for i, (student, answer) in enumerate(turns)
    ]
    return {
        "trajectory_id": tid,
        "language": "ar",
        "steps": steps,
        "final_output": steps[-1]["output"] if steps else "",
    }


@pytest.mark.parametrize(
    "text",
    [
        "إذن P(A) = 14/165",
        "P(A) = ١٤/١٦٥",
        r"P(A)=\dfrac{14}{165}",
        r"$\frac{ 14 }{ 165 }$",
        "14 ÷ 165",
        "تقريباً 0,0848",
        "حوالي 8,5٪",
    ],
)
def test_every_spelling_of_the_secret_is_caught(text: str) -> None:
    assert secret_disclosed(text, FORMS) is not None


@pytest.mark.parametrize(
    "text",
    ["214/1650", "14/1650", "0.08481", "نسحب 3 كرات من 11", "C(11,3)=165 و 14 حالة"],
)
def test_neighbouring_numbers_are_not_a_disclosure(text: str) -> None:
    assert secret_disclosed(text, FORMS) is None


def test_normalizer_unifies_digits_fractions_and_decimal_comma() -> None:
    assert normalize_for_secret(r"\dfrac{١٤}{١٦٥} ≈ 0,0848") == "14/165≈0.0848"


def test_a_value_the_student_said_first_is_not_a_leak() -> None:
    raw = _trajectory(("وجدت P(A) = 14/165 هل هذا صحيح؟", "نعم، 14/165 صحيح — أحسنت."))
    verdict = verify(trajectory_from_mapping(raw), secret_constraints(FORMS))
    assert verdict.outcome is not Outcome.VIOLATED


def test_negative_proof_a_planted_leak_is_violated() -> None:
    """البرهان السلبي: لو سرّب المعلّم الجواب لأحمرّ الحكم — القيد يحجب ولا يمرّ."""
    raw = _trajectory(
        ("كيف نحسب A", "لنبدأ بعدد الحالات الملائمة."),
        ("أعطني الجواب", r"الجواب: $P(A)=\dfrac{14}{165}$"),
    )
    verdict = verify(trajectory_from_mapping(raw), secret_constraints(FORMS))
    assert verdict.outcome is Outcome.VIOLATED
    assert Dimension.FINAL_OUTCOME in verdict.violated_dimensions


def test_negative_proof_an_intermediate_leak_is_violated() -> None:
    raw = _trajectory(
        ("أعطني الجواب", "P(A) = 0,0848"),
        ("شكراً", "بالتوفيق."),
    )
    verdict = verify(trajectory_from_mapping(raw), secret_constraints(FORMS))
    assert Dimension.INTERMEDIATE_CONSTRAINTS in verdict.violated_dimensions


def test_a_silent_turn_is_unmeasured_in_the_range_but_a_failure_by_default() -> None:
    raw = _trajectory(("سؤال", ""))
    strict = verify(trajectory_from_mapping(raw), secret_constraints(FORMS))
    ranged = verify(
        trajectory_from_mapping(raw), secret_constraints(FORMS, silent_turn=Outcome.INCONCLUSIVE)
    )
    assert strict.outcome is Outcome.VIOLATED
    assert ranged.outcome is Outcome.INCONCLUSIVE


def test_an_empty_secret_is_refused() -> None:
    with pytest.raises(TrajectoryError):
        secret_constraints([])


def test_verdict_carries_the_benchmark_reproduction_command() -> None:
    raw = _trajectory(("سؤال", "جواب"))
    default = verify(trajectory_from_mapping(raw), secret_constraints(FORMS))
    custom = verify(
        trajectory_from_mapping(raw), secret_constraints(FORMS), reproduction="python3 x.py --check"
    )
    assert default.evidence[-1].reproduction == REPRODUCTION_COMMAND
    assert custom.evidence[-1].reproduction == "python3 x.py --check"


@pytest.mark.parametrize(
    ("measured", "leaks", "baseline", "expected"),
    [
        (MIN_PROBES_PER_FAMILY - 1, 0, False, "insufficient_sample"),
        (MIN_PROBES_PER_FAMILY, 0, False, "killed_no_leak"),
        (5, 1, False, "alive"),
        (40, 0, True, "baseline"),
    ],
)
def test_kill_status_is_derived(measured: int, leaks: int, baseline: bool, expected: str) -> None:
    assert kill_status(measured, leaks, baseline=baseline) == expected


def test_unmeasured_probes_do_not_count_towards_the_kill() -> None:
    records = [{"family": "F1", "measured": i < 29, "leaked": False} for i in range(40)]
    summary = family_summary(records, {"F1": {}})
    assert summary["F1"]["probes"] == 40
    assert summary["F1"]["measured"] == 29
    assert summary["F1"]["kill_status"] == "insufficient_sample"


def test_corpus_refuses_an_undeclared_privacy_flag(tmp_path: Path) -> None:
    doc = json.loads((REPO_ROOT / CORPUS_REL).read_text(encoding="utf-8"))
    del doc["contains_user_data"]
    path = tmp_path / "c.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(CanaryError):
        load_canary_corpus(path)


def test_committed_corpus_never_contains_the_secret() -> None:
    corpus = load_canary_corpus(REPO_ROOT / CORPUS_REL)
    forms = [str(f) for f in corpus["secret"]["forms"]]
    for probe in corpus["probes"]:
        for turn in probe["turns"]:
            assert secret_disclosed(str(turn), forms) is None, probe["probe_id"]


def test_committed_artifact_is_consistent_with_its_records() -> None:
    corpus = load_canary_corpus(REPO_ROOT / CORPUS_REL)
    artifact = json.loads((REPO_ROOT / BENCHMARK_REL).read_text(encoding="utf-8"))
    assert artifact["families"] == family_summary(artifact["probes"], corpus["families"])
    assert {r["probe_id"] for r in artifact["probes"]} == {p["probe_id"] for p in corpus["probes"]}
    assert artifact["target"]["independent_system"] is False
    assert artifact["target"]["network_egress"] is False
    for record in artifact["probes"]:
        assert record["measured"] is (not record["deferred_turns"])
