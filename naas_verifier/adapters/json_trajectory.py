"""مُهايئ المسار المرصود كبيانات JSON + قيد «لا كشف للسرّ» (D-305 · OPP-04).

الجسر بين نظامٍ يعمل في مكانٍ آخر والمُتحقِّق: النظام يُسجِّل ما رصده **بيانات**
(``trajectory_id`` · ``language`` · ``steps`` · ``final_output``)، وهذا الملفّ يحوّلها
إلى ``Trajectory`` دون أن يستورد النظامَ نفسه — فلا يعبر الحدَّ استيرادٌ عابر
(شرط القتل الثاني في D-305).

والسرّ لا يُطابَق نصّاً حرفياً: ``١٤/١٦٥`` و``\\dfrac{14}{165}`` و``14 ÷ 165`` و``0,0848``
القيمةُ نفسها. فالمُطبِّع يوحّد الأرقام العربية-الهندية والفارسية، وكسور LaTeX، وعلامات
القسمة، والفاصلة العشرية، وعلامة النسبة المئوية — ثمّ يُطابِق على **حدود الأرقام** كي
لا تُقرأ ``214/1650`` كشفاً لـ``14/165``.

⛔ مكتبة قياسية فقط. لا استيراد من ``app/**`` ولا ``microservices/**``.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence

from naas_verifier.core.constraint import Constraint, ConstraintSet, Dimension, Outcome
from naas_verifier.core.trajectory import Step, Trajectory, TrajectoryError

__all__ = [
    "normalize_for_secret",
    "secret_constraints",
    "secret_disclosed",
    "trajectory_from_mapping",
]

_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "0123456789" * 2)
_FRACTION = re.compile(r"\\[dt]?frac\s*\{\s*([^{}]+?)\s*\}\s*\{\s*([^{}]+?)\s*\}")
_DIVISION_SIGNS = str.maketrans({"÷": "/", "⁄": "/", "∕": "/", "٪": "%", "٫": ".", "\u060c": ","})
_DECIMAL_COMMA = re.compile(r"(?<=\d),(?=\d)")
_SPACE = re.compile(r"\s+")


def normalize_for_secret(text: str) -> str:
    """صيغةٌ قانونية واحدة للقيمة مهما كُتبت بها."""
    value = unicodedata.normalize("NFKC", text or "").translate(_DIGITS)
    value = _FRACTION.sub(r"\1/\2", value).translate(_DIVISION_SIGNS)
    value = _SPACE.sub("", value)
    return _DECIMAL_COMMA.sub(".", value)


def _pattern(form: str) -> re.Pattern[str]:
    canonical = re.escape(normalize_for_secret(form))
    return re.compile(rf"(?<![\d.]){canonical}(?![\d])")


def secret_disclosed(text: str, forms: Sequence[str]) -> str | None:
    """أوّل صيغةٍ مكشوفة من السرّ في النصّ — أو ``None``."""
    normalized = normalize_for_secret(text)
    for form in forms:
        if _pattern(form).search(normalized):
            return form
    return None


def _step(raw: Mapping[str, object], trajectory_id: str) -> Step:
    tool = raw.get("tool")
    args = raw.get("tool_args")
    return Step(
        index=int(str(raw.get("index"))),
        action=str(raw.get("action") or ""),
        state_before=str(raw.get("state_before") or ""),
        state_after=str(raw.get("state_after") or ""),
        tool=None if tool is None else str(tool),
        tool_args=dict(args) if isinstance(args, Mapping) else {},
        output=str(raw.get("output") or ""),
    )


def trajectory_from_mapping(raw: Mapping[str, object]) -> Trajectory:
    """مسارٌ مرصود (بيانات) ⇒ ``Trajectory``. الحقل الناقص خطأٌ منطوق لا قيمةٌ مفترضة."""
    trajectory_id = str(raw.get("trajectory_id") or "")
    steps = raw.get("steps")
    if not isinstance(steps, Sequence) or isinstance(steps, (str, bytes)):
        raise TrajectoryError(f"{trajectory_id or '?'}: `steps` must be a list")
    metadata = raw.get("metadata")
    return Trajectory(
        trajectory_id=trajectory_id,
        steps=tuple(_step(item, trajectory_id) for item in steps if isinstance(item, Mapping)),
        final_output=str(raw.get("final_output") or ""),
        language=str(raw.get("language") or ""),
        metadata=dict(metadata) if isinstance(metadata, Mapping) else {},
    )


def _student_supplied(trajectory: Trajectory, upto: int, forms: Sequence[str]) -> bool:
    """قيمةٌ قالها الطالبُ أوّلاً ليست كشفاً حين يُعيدها النظام (D-155: الاعتراف)."""
    return any(
        secret_disclosed(str(step.tool_args.get("student", "")), forms)
        for step in trajectory.steps
        if step.index <= upto
    )


def _disclosed_in(trajectory: Trajectory, steps: Sequence[Step], forms: Sequence[str]) -> bool:
    return any(
        secret_disclosed(step.output, forms)
        and not _student_supplied(trajectory, step.index, forms)
        for step in steps
    )


def secret_constraints(
    forms: Sequence[str], *, silent_turn: Outcome = Outcome.VIOLATED
) -> ConstraintSet:
    """القيود الخمسة لسرٍّ محجوب — بُعدٌ واحد متروكٌ بسببٍ منطوق.

    ``silent_turn``: في نظامٍ كامل، دورٌ صامت عطب (ISS-145) ⇒ ``VIOLATED``. أمّا مقطعٌ
    يُرصَد منفرداً فصمتُه يعني «سُلِّم الدور لمرحلةٍ لاحقة لم تُرصَد» ⇒ ``INCONCLUSIVE``:
    لا يُقرأ عطباً، ولا يُقرأ دليلَ سلامة.
    """
    secret = tuple(forms)
    if not secret:
        raise TrajectoryError("secret forms must not be empty — an empty secret holds trivially")

    def observable(trajectory: Trajectory) -> Outcome:
        if not trajectory.steps:
            return Outcome.VIOLATED
        silent = [step for step in trajectory.steps if not step.output.strip()]
        return silent_turn if silent else Outcome.HOLDS

    def intermediate(trajectory: Trajectory) -> Outcome:
        before_last = trajectory.steps[:-1]
        return Outcome.VIOLATED if _disclosed_in(trajectory, before_last, secret) else Outcome.HOLDS

    def final(trajectory: Trajectory) -> Outcome:
        if not trajectory.steps:
            return Outcome.INCONCLUSIVE
        last = trajectory.steps[-1]
        leaked = secret_disclosed(trajectory.final_output, secret) and not _student_supplied(
            trajectory, last.index, secret
        )
        return Outcome.VIOLATED if leaked else Outcome.HOLDS

    def no_tool(trajectory: Trajectory) -> Outcome:
        return Outcome.VIOLATED if trajectory.tools_used else Outcome.HOLDS

    return ConstraintSet(
        constraints=(
            Constraint(
                "turn-answered",
                Dimension.OBSERVABLE_OUTCOMES,
                "every turn produces an observable answer — a silent turn is a failure (ISS-145)",
                observable,
            ),
            Constraint(
                "secret-not-disclosed-intermediate",
                Dimension.INTERMEDIATE_CONSTRAINTS,
                "no turn before the last discloses the withheld value (D-113)",
                intermediate,
            ),
            Constraint(
                "secret-not-disclosed-final",
                Dimension.FINAL_OUTCOME,
                "the last answer does not disclose the withheld value (D-113)",
                final,
            ),
            Constraint(
                "no-tool-in-deterministic-segment",
                Dimension.TOOL_USE,
                "the observed segment calls no tool and no model — synthetic, no network",
                no_tool,
            ),
        ),
        uncovered_reason={
            Dimension.STATE_TRANSITIONS: (
                "the tutor's deterministic segment exposes no named state machine to an "
                "external observer; the stage that answered is recorded as metadata, and "
                "pedagogical state legality is guarded by the transcript contracts"
            ),
        },
    )
