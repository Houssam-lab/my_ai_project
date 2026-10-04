#!/usr/bin/env python3
"""يفرض مصفوفة النضج الهندسي ذات أفق 500 سنة.

هذه البوابة تمنع تحوّل السلم المعرفي إلى نص زخرفي: يجب أن يكون هناك JSON
آلي يحتوي 200-300 checkpoint، ولكل checkpoint دليل مطلوب وبصمة فشل واختبار
وقاعدة قبول ومستوى نضج، ثم تطبيق محافظ على المستودع بدليل ملفي موجود.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "docs/governance/ENGINEERING_MATURITY_MATRIX.json"
AUDIT = ROOT / "docs/governance/ENGINEERING_MATURITY_AUDIT.json"
DOC = ROOT / "docs/architecture/ENGINEERING_MATURITY_MATRIX.md"
INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
MANIFEST = ROOT / "docs/DOCUMENTATION_MANIFEST.json"
CI = ROOT / ".github/workflows/ci.yml"
GATE = "scripts/fitness/check_engineering_maturity_matrix.py"
EXPECTED_STAGE_IDS = [f"M{number:02d}" for number in range(29)]
REQUIRED_EVIDENCE_KEYS = ("UNDERSTOOD", "DESIGNED", "IMPLEMENTED", "VERIFIED", "EVOLVABLE")
REQUIRED_FIVE_KEYS = tuple(f"{key}?" for key in REQUIRED_EVIDENCE_KEYS)
ALLOWED_AUDIT_STATUS = {"EVIDENCED", "PARTIAL", "UNKNOWN", "NOT_APPLICABLE"}
MICROSCOPE_GATE = "scripts/fitness/check_repository_microscope.py"
REQUIRED_COVERAGE_TARGETS = {
    "existing_tracked_code",
    "existing_documentation",
    "existing_ci_workflows",
    "future_code",
    "future_generated_artifacts",
    "future_contracts_and_schemas",
}


def _load_json(path: Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.is_file():
        return None, [f"{label} مفقود: {path.relative_to(ROOT)}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{label} ليس JSON صالحاً: {exc}"]
    if not isinstance(payload, dict):
        return None, [f"{label} يجب أن يكون object في الجذر"]
    return payload, []


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _non_empty_list(value: Any) -> bool:
    return (
        isinstance(value, list) and bool(value) and all(_non_empty_string(item) for item in value)
    )


def _path_exists(relative: str) -> bool:
    return (ROOT / relative).exists()


def _validate_coverage_policy(matrix: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    policy = matrix.get("coverage_policy")
    if not isinstance(policy, dict):
        return ["matrix.coverage_policy يجب أن يثبت أن القديم والمستقبلي داخل النطاق"]
    applies_to = policy.get("applies_to")
    if not isinstance(applies_to, list):
        failures.append("matrix.coverage_policy.applies_to يجب أن تكون list")
    else:
        missing = sorted(REQUIRED_COVERAGE_TARGETS - {str(item) for item in applies_to})
        if missing:
            failures.append(f"coverage_policy لا يغطي القديم والمستقبل بالكامل؛ ناقص={missing}")
    for field in ("legacy_rule_ar", "future_rule_ar", "ratchet_rule_ar"):
        if not _non_empty_string(policy.get(field)):
            failures.append(f"matrix.coverage_policy.{field} فارغ")
    if policy.get("grandfathering_forbidden") is not True:
        failures.append("matrix.coverage_policy.grandfathering_forbidden يجب أن يكون true")
    if policy.get("microscopic_repository_census_required") is not True:
        failures.append(
            "matrix.coverage_policy.microscopic_repository_census_required يجب أن يكون true"
        )
    if policy.get("old_before_new_required") is not True:
        failures.append("matrix.coverage_policy.old_before_new_required يجب أن يكون true")
    if policy.get("repository_microscope_gate") != MICROSCOPE_GATE:
        failures.append("matrix.coverage_policy.repository_microscope_gate لا يطابق بوابة المجهر")
    return failures


def _validate_stage_rows(matrix: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    stages = matrix.get("stages")
    if not isinstance(stages, list):
        return ["matrix.stages يجب أن تكون list"]
    ids = [str(row.get("id")) for row in stages if isinstance(row, dict)]
    if ids != EXPECTED_STAGE_IDS:
        failures.append(f"المراحل يجب أن تكون M00→M28 بالترتيب؛ الموجود={ids}")
    seen: set[str] = set()
    for row in stages:
        if not isinstance(row, dict):
            failures.append("صف مرحلة ليس object")
            continue
        stage_id = str(row.get("id"))
        if stage_id in seen:
            failures.append(f"مرحلة مكررة: {stage_id}")
        seen.add(stage_id)
        for field in ("id", "name_ar", "thesis_ar", "vibe_jump_if_missing_ar"):
            if not _non_empty_string(row.get(field)):
                failures.append(f"{stage_id}: حقل المرحلة `{field}` فارغ")
        if row.get("maturity_level") != row.get("number"):
            failures.append(f"{stage_id}: maturity_level يجب أن يساوي number")
    return failures


def _validate_checkpoint(  # noqa: PLR0912
    checkpoint: dict[str, Any], stage_ids: set[str]
) -> list[str]:
    failures: list[str] = []
    checkpoint_id = str(checkpoint.get("id", "<missing>"))
    for field in (
        "id",
        "stage_id",
        "name_ar",
        "question_ar",
        "failure_signature_ar",
        "test_ar",
        "pass_fail_rule_ar",
    ):
        if not _non_empty_string(checkpoint.get(field)):
            failures.append(f"{checkpoint_id}: حقل checkpoint `{field}` فارغ")
    stage_id = str(checkpoint.get("stage_id"))
    if stage_id not in stage_ids:
        failures.append(f"{checkpoint_id}: stage_id غير معروف: {stage_id}")
    if not isinstance(checkpoint.get("stage_number"), int):
        failures.append(f"{checkpoint_id}: stage_number يجب أن يكون int")
    if checkpoint.get("maturity_level") != checkpoint.get("stage_number"):
        failures.append(f"{checkpoint_id}: maturity_level يجب أن يساوي stage_number")

    evidence = checkpoint.get("required_evidence")
    if not isinstance(evidence, dict):
        failures.append(f"{checkpoint_id}: required_evidence يجب أن يكون object")
    else:
        if set(evidence) != set(REQUIRED_EVIDENCE_KEYS):
            failures.append(
                f"{checkpoint_id}: required_evidence يجب أن يحمل المفاتيح {REQUIRED_EVIDENCE_KEYS}"
            )
        for key in REQUIRED_EVIDENCE_KEYS:
            if not _non_empty_list(evidence.get(key)):
                failures.append(f"{checkpoint_id}: required_evidence.{key} فارغ")

    five = checkpoint.get("five_question_gate")
    if not isinstance(five, dict):
        failures.append(f"{checkpoint_id}: five_question_gate يجب أن يكون object")
    else:
        if set(five) != set(REQUIRED_FIVE_KEYS):
            failures.append(f"{checkpoint_id}: five_question_gate يجب أن يحمل {REQUIRED_FIVE_KEYS}")
        for key in REQUIRED_FIVE_KEYS:
            if not _non_empty_string(five.get(key)):
                failures.append(f"{checkpoint_id}: five_question_gate.{key} فارغ")
    return failures


def _validate_matrix(matrix: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for field in ("title_ar", "purpose_ar", "scope_ar"):
        if not _non_empty_string(matrix.get(field)):
            failures.append(f"matrix.{field} فارغ")
    failures.extend(_validate_coverage_policy(matrix))
    failures.extend(_validate_stage_rows(matrix))

    checkpoints = matrix.get("checkpoints")
    if not isinstance(checkpoints, list):
        return [*failures, "matrix.checkpoints يجب أن تكون list"]
    if not 200 <= len(checkpoints) <= 300:
        failures.append(f"عدد checkpoints يجب أن يكون بين 200 و300؛ الموجود={len(checkpoints)}")
    if matrix.get("checkpoint_count") != len(checkpoints):
        failures.append("matrix.checkpoint_count لا يساوي العدد الفعلي")
    if matrix.get("stage_count") != 29:
        failures.append("matrix.stage_count يجب أن يساوي 29")

    stages = matrix.get("stages", [])
    stage_ids = {str(row.get("id")) for row in stages if isinstance(row, dict)}
    seen_ids: set[str] = set()
    counts_by_stage = dict.fromkeys(EXPECTED_STAGE_IDS, 0)
    for checkpoint in checkpoints:
        if not isinstance(checkpoint, dict):
            failures.append("checkpoint ليس object")
            continue
        checkpoint_id = str(checkpoint.get("id", "<missing>"))
        if checkpoint_id in seen_ids:
            failures.append(f"checkpoint مكرر: {checkpoint_id}")
        seen_ids.add(checkpoint_id)
        stage_id = str(checkpoint.get("stage_id"))
        if stage_id in counts_by_stage:
            counts_by_stage[stage_id] += 1
        failures.extend(_validate_checkpoint(checkpoint, stage_ids))

    missing_stage_checkpoints = [
        stage_id for stage_id, count in counts_by_stage.items() if count < 5
    ]
    if missing_stage_checkpoints:
        failures.append(
            f"كل مرحلة تحتاج 5 checkpoints على الأقل؛ ناقصة={missing_stage_checkpoints}"
        )
    return failures


def _validate_audit(  # noqa: PLR0912, PLR0915
    audit: dict[str, Any], matrix: dict[str, Any]
) -> list[str]:
    failures: list[str] = []
    scope = audit.get("scope")
    if not isinstance(scope, dict):
        failures.append("audit.scope يجب أن يكون object")
    else:
        if scope.get("governing_decision") != "D-300":
            failures.append("audit.scope.governing_decision يجب أن يبقى D-300")
        if scope.get("active_product_thesis") != "fr-be-einvoicing-referential-cleansing":
            failures.append("audit.scope.active_product_thesis يجب أن يطابق الإسفين النشط")
        if scope.get("frozen_platform") is not True:
            failures.append("audit.scope.frozen_platform يجب أن يكون true")
        coverage = scope.get("coverage_policy")
        if not isinstance(coverage, dict):
            failures.append(
                "audit.scope.coverage_policy يجب أن يثبت تطبيق المصفوفة على القديم والمستقبل"
            )
        else:
            if coverage.get("existing_tracked_code") is not True:
                failures.append(
                    "audit.scope.coverage_policy.existing_tracked_code يجب أن يكون true"
                )
            if coverage.get("future_changes") is not True:
                failures.append("audit.scope.coverage_policy.future_changes يجب أن يكون true")
            if coverage.get("repository_microscope_required") is not True:
                failures.append(
                    "audit.scope.coverage_policy.repository_microscope_required يجب أن يكون true"
                )
            if coverage.get("old_before_new") is not True:
                failures.append("audit.scope.coverage_policy.old_before_new يجب أن يكون true")
            if coverage.get("gate") != MICROSCOPE_GATE:
                failures.append("audit.scope.coverage_policy.gate لا يطابق بوابة المجهر")
            for field in ("legacy_is_not_exempt_ar", "future_is_not_exempt_ar"):
                if not _non_empty_string(coverage.get(field)):
                    failures.append(f"audit.scope.coverage_policy.{field} فارغ")

    matrix_stage_ids = {
        str(row.get("id")) for row in matrix.get("stages", []) if isinstance(row, dict)
    }
    assessments = audit.get("stage_assessments")
    if not isinstance(assessments, list):
        return [*failures, "audit.stage_assessments يجب أن تكون list"]
    ids = [str(row.get("stage_id")) for row in assessments if isinstance(row, dict)]
    if ids != EXPECTED_STAGE_IDS:
        failures.append(f"audit.stage_assessments يجب أن تغطي M00→M28 بالترتيب؛ الموجود={ids}")
    for row in assessments:
        if not isinstance(row, dict):
            failures.append("audit stage assessment ليس object")
            continue
        stage_id = str(row.get("stage_id"))
        if stage_id not in matrix_stage_ids:
            failures.append(f"audit يشير إلى مرحلة غير موجودة في matrix: {stage_id}")
        if row.get("current_status") not in ALLOWED_AUDIT_STATUS:
            failures.append(f"{stage_id}: current_status غير مسموح: {row.get('current_status')}")
        for field in ("summary_ar", "risk_of_vibe_jump_ar", "next_investigation_ar"):
            if not _non_empty_string(row.get(field)):
                failures.append(f"{stage_id}: audit.{field} فارغ")
        evidence_paths = row.get("evidence_paths")
        if not _non_empty_list(evidence_paths):
            failures.append(f"{stage_id}: evidence_paths فارغ")
        else:
            for relative in evidence_paths:
                if not _path_exists(relative):
                    failures.append(f"{stage_id}: دليل غير موجود: {relative}")

    findings = audit.get("jump_findings")
    if not isinstance(findings, list) or not findings:
        failures.append("audit.jump_findings يجب أن تحمل نتيجة قفز واحدة على الأقل")
    else:
        for finding in findings:
            if not isinstance(finding, dict):
                failures.append("jump finding ليس object")
                continue
            for field in ("id", "finding_ar", "required_action_ar"):
                if not _non_empty_string(finding.get(field)):
                    failures.append(f"jump finding `{field}` فارغ")
            if not _non_empty_list(finding.get("evidence_paths")):
                failures.append(f"{finding.get('id')}: evidence_paths فارغ")
            else:
                for relative in finding["evidence_paths"]:
                    if not _path_exists(relative):
                        failures.append(f"{finding.get('id')}: دليل غير موجود: {relative}")
    return failures


def _validate_wiring() -> list[str]:
    failures: list[str] = []
    for path in (DOC, INDEX, MANIFEST, CI):
        if not path.is_file():
            failures.append(f"ملف لازم للربط مفقود: {path.relative_to(ROOT)}")
            return failures
    doc_rel = "docs/architecture/ENGINEERING_MATURITY_MATRIX.md"
    index_text = INDEX.read_text(encoding="utf-8")
    if (
        doc_rel not in index_text
        and "architecture/ENGINEERING_MATURITY_MATRIX.md" not in index_text
    ):
        failures.append("DOCUMENTATION_INDEX.md لا يذكر ENGINEERING_MATURITY_MATRIX.md")
    manifest = MANIFEST.read_text(encoding="utf-8")
    if f'"path": "{doc_rel}"' not in manifest:
        failures.append("DOCUMENTATION_MANIFEST.json لا يسجل ENGINEERING_MATURITY_MATRIX.md")
    ci_text = CI.read_text(encoding="utf-8")
    if GATE not in ci_text:
        failures.append("ci.yml لا يشغل check_engineering_maturity_matrix.py في guardrails")
    if not DOC.read_text(encoding="utf-8").strip():
        failures.append("وثيقة المصفوفة فارغة")
    return failures


def validate(
    matrix_path: Path = MATRIX, audit_path: Path = AUDIT, *, check_wiring: bool = True
) -> list[str]:
    failures: list[str] = []
    matrix, matrix_errors = _load_json(matrix_path, "engineering maturity matrix")
    audit, audit_errors = _load_json(audit_path, "engineering maturity audit")
    failures.extend(matrix_errors)
    failures.extend(audit_errors)
    if matrix is not None:
        failures.extend(_validate_matrix(matrix))
    if matrix is not None and audit is not None:
        failures.extend(_validate_audit(audit, matrix))
    if check_wiring:
        failures.extend(_validate_wiring())
    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("❌ مصفوفة النضج الهندسي مخروقة:\n")
        for failure in failures:
            print(f"  • {failure}")
        return 1
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    print(
        "✅ مصفوفة النضج الهندسي: "
        f"{matrix['stage_count']} مرحلة و{matrix['checkpoint_count']} checkpoint، "
        "والتطبيق الحالي مربوط بدليل ملفّي وD-300."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
