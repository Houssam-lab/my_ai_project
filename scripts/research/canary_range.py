#!/usr/bin/env python3
"""ميدان الكناري (D-305 · OPP-04) — مسابير عربية/فرنسية/دارجة على معلّم المنصّة نفسه.

الهدف: **المقطع الحتمي** لدور الطالب — المراحل نفسها التي تحرسها عقود الترانسكريبت،
بالمُشغِّل نفسه (``tests/test_transcript_contracts._run_turn``) لا بنسخةٍ ثانية تنحرف.
والسرّ: الجواب النهائي للتمرين ``P(A)`` الذي تمنع D-113 تسليمه.

كلّ مسبارٍ يُسجَّل **مساراً بيانات** (خطوةٌ لكلّ دور)، ثمّ يقرؤه المُتحقِّق عبر
``naas_verifier.adapters.json_trajectory`` — بلا استيرادٍ عابر للحدّ (شرط القتل الثاني).

⛔ ما لا يُدّعى: نظامُنا نحن ليس «نظاماً مستقلاً» — النتيجة هنا تخدم الحلقتين 3–4 لـOPP-04
(مسبارٌ يحفظ الخصوصية · اختبارٌ موثوق) ولا تُحتسَب للحلقة 5. ولا شبكة ولا نموذج لغوي.

    python3 scripts/research/canary_range.py          # يكتب الأثر
    python3 scripts/research/canary_range.py --check  # يُعيد التشغيل ويطابق الأثر المُلتزَم
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import socket
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from naas_verifier.adapters.canary import (
    BENCHMARK_REL,
    CORPUS_REL,
    REPRODUCTION,
    family_summary,
    load_canary_corpus,
)
from naas_verifier.adapters.json_trajectory import (
    secret_constraints,
    secret_disclosed,
    trajectory_from_mapping,
)
from naas_verifier.core.constraint import Dimension, Outcome
from naas_verifier.core.verdict import verify


class _NetworkGuard:
    """«بلا شبكة» قيدٌ مفروض لا ادّعاء: كلّ محاولة اتّصالٍ تُعَدّ وتُرفَض، فلا يخرج شيء.

    ولماذا تُرفَض بدل أن تُفشِل التشغيل: بعض المراحل «الحتمية» تستدعي نموذجاً عمداً
    (`semantic_property_skill.define_concept` — مُعرِّف المفاهيم الجديدة D-132). الدور الذي
    يحاول ذلك يُعرَض في الإنتاج بنصّ نموذج لا بالنصّ البديل الذي نراه هنا، فيُوسَم
    «مسار نموذج» ولا يُحتسَب مقيساً.
    """

    def __init__(self) -> None:
        self.attempts: list[str] = []

    def __enter__(self) -> _NetworkGuard:
        self._connect = socket.socket.connect
        self._connect_ex = socket.socket.connect_ex
        attempts = self.attempts

        def refuse(_sock: socket.socket, address: object, *_: object) -> None:
            attempts.append(str(address))
            raise OSError("canary range: network is not part of this measurement")

        def refuse_ex(_sock: socket.socket, address: object) -> int:
            attempts.append(str(address))
            return 111

        socket.socket.connect = refuse  # type: ignore[method-assign,assignment]
        socket.socket.connect_ex = refuse_ex  # type: ignore[method-assign,assignment]
        return self

    def __exit__(self, *_: object) -> None:
        socket.socket.connect = self._connect  # type: ignore[method-assign]
        socket.socket.connect_ex = self._connect_ex  # type: ignore[method-assign]


def _observe(
    client: object, probe: dict, seed: list[dict[str, str]], guard: _NetworkGuard
) -> dict[str, object]:
    """يُشغِّل أدوار المسبار على المراحل الحتمية ويُرجِع المسار المرصود بيانات."""
    from tests.test_transcript_contracts import _run_turn

    history = [dict(m) for m in seed]
    tutor_state: dict[str, object] = {"kc_progress": {}}
    steps: list[dict[str, object]] = []
    for index, question in enumerate(probe["turns"]):
        before = len(guard.attempts)
        answer = asyncio.run(_run_turn(client, str(question), history, tutor_state))
        steps.append(
            {
                "index": index,
                "action": "tutor_turn",
                "state_before": f"turn-{index}",
                "state_after": f"turn-{index + 1}",
                "tool": None,
                "tool_args": {"student": str(question), "model_path": len(guard.attempts) > before},
                "output": answer,
            }
        )
        history.append({"role": "user", "content": str(question)})
        if answer.strip():
            history.append({"role": "assistant", "content": answer})
    return {
        "trajectory_id": str(probe["probe_id"]),
        "language": str(probe["language"]),
        "steps": steps,
        "final_output": str(steps[-1]["output"]) if steps else "",
        "metadata": {"family": probe["family"]},
    }


def _record(probe: dict, observed: dict[str, object], forms: list[str]) -> dict[str, object]:
    trajectory = trajectory_from_mapping(observed)
    constraints = secret_constraints(forms, silent_turn=Outcome.INCONCLUSIVE)
    verdict = verify(trajectory, constraints, reproduction=REPRODUCTION)
    # دورٌ لم يُقَس: فراغٌ سُلِّم لمرحلةٍ لاحقة، أو محاولةُ نموذجٍ رُفضت (نصّ الإنتاج غير ما نراه).
    empty = [step.index + 1 for step in trajectory.steps if not step.output.strip()]
    model_path = [
        step.index + 1 for step in trajectory.steps if step.tool_args.get("model_path") is True
    ]
    deferred = sorted(set(empty) | set(model_path))
    secret_dims = {Dimension.INTERMEDIATE_CONSTRAINTS, Dimension.FINAL_OUTCOME}
    leaked = any(
        row.outcome is Outcome.VIOLATED
        for row in verdict.dimensions
        if row.dimension in secret_dims
    )
    leaked_at = next(
        (step.index + 1 for step in trajectory.steps if secret_disclosed(step.output, forms)),
        None,
    )
    return {
        "probe_id": probe["probe_id"],
        "family": probe["family"],
        "language": probe["language"],
        "turns": len(probe["turns"]),
        "answer_chars": [len(step.output) for step in trajectory.steps],
        "empty_turns": empty,
        "model_path_turns": model_path,
        "deferred_turns": deferred,
        "measured": not deferred,
        "leaked": leaked,
        "leaked_at_turn": leaked_at if leaked else None,
        "verdict": verdict.outcome.value,
        "violated": [name for row in verdict.dimensions for name in row.violated],
    }


def run() -> dict[str, object]:
    from app.infrastructure.clients.orchestrator_client import OrchestratorClient
    from tests.test_transcript_contracts import _DETERMINISTIC_STAGES

    corpus_path = REPO_ROOT / CORPUS_REL
    corpus = load_canary_corpus(corpus_path)
    target = corpus["target"]
    seed = [dict(m) for m in target["seed_history"]]
    forms = [str(f) for f in corpus["secret"]["forms"]]
    client = OrchestratorClient()

    with _NetworkGuard() as guard:
        records = [_record(p, _observe(client, p, seed, guard), forms) for p in corpus["probes"]]
    families = corpus["families"]
    summary = family_summary(records, families)
    attack = [r for r in records if not families[r["family"]].get("baseline")]
    baseline = [r for r in records if families[r["family"]].get("baseline")]

    def _rate(rows: list[dict[str, object]]) -> float | None:
        measured = [r for r in rows if r["measured"]]
        leaks = sum(1 for r in rows if r["leaked"])
        return round(leaks / len(measured), 4) if measured else None

    return {
        "$schema_version": 1,
        "decision": "D-305",
        "reproduction": REPRODUCTION,
        "corpus": CORPUS_REL,
        "corpus_sha256": hashlib.sha256(corpus_path.read_bytes()).hexdigest(),
        "target": {
            "system": "CogniForge tutor — deterministic turn segment",
            "stages": list(_DETERMINISTIC_STAGES),
            "runner": "tests/test_transcript_contracts.py::_run_turn",
            "network_egress": False,
            "refused_connection_attempts": len(guard.attempts),
            "model_path_turns": sum(len(r["model_path_turns"]) for r in records),
            "empty_turns": sum(len(r["empty_turns"]) for r in records),
            "independent_system": False,
            "independence_note_ar": (
                "نظامُنا نحن: النتيجة تخدم الحلقتين 3–4 لـOPP-04 ولا تُحتسَب للحلقة 5."
            ),
        },
        "secret": {"name": corpus["secret"]["name"], "forms": forms},
        "families": summary,
        "comparison": {
            "ar_fr_leak_rate": _rate(attack),
            "en_baseline_leak_rate": _rate(baseline),
        },
        "bridge": {
            "status": "holds",
            "evidence": (
                "naas_verifier reads the observed trajectories as data through "
                "naas_verifier/adapters/json_trajectory.py; check_naas_verifier_boundary "
                "forbids app/microservices imports inside the package"
            ),
        },
        "probes": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="re-run and compare with the committed artifact"
    )
    args = parser.parse_args()
    logging.disable(logging.CRITICAL)

    result = run()
    rendered = json.dumps(result, ensure_ascii=False, indent=1) + "\n"
    target = REPO_ROOT / BENCHMARK_REL
    for family, row in result["families"].items():
        print(
            f"{family}: {row['probes']} probes · {row['measured']} measured · "
            f"{row['leaks']} leaks · {row['kill_status']}"
        )
    if args.check:
        if not target.is_file() or target.read_text(encoding="utf-8") != rendered:
            print(f"❌ {BENCHMARK_REL} does not match a fresh run — regenerate it")
            return 1
        print(f"✅ {BENCHMARK_REL} matches a fresh run")
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    print(f"✅ wrote {BENCHMARK_REL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
