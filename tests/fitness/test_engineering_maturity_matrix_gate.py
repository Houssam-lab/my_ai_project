from __future__ import annotations

import json
from pathlib import Path

from scripts.fitness import check_engineering_maturity_matrix as gate


def test_engineering_maturity_matrix_rejects_checkpoint_without_evidence(tmp_path: Path) -> None:
    matrix = json.loads(gate.MATRIX.read_text(encoding="utf-8"))
    matrix["checkpoints"][0]["required_evidence"]["VERIFIED"] = []
    broken_matrix = tmp_path / "matrix.json"
    broken_matrix.write_text(json.dumps(matrix, ensure_ascii=False), encoding="utf-8")

    failures = gate.validate(broken_matrix, gate.AUDIT, check_wiring=False)

    assert len(failures) >= 1
    assert any("required_evidence.VERIFIED" in failure for failure in failures)


def test_engineering_maturity_matrix_rejects_audit_evidence_that_is_not_on_disk(
    tmp_path: Path,
) -> None:
    audit = json.loads(gate.AUDIT.read_text(encoding="utf-8"))
    audit["stage_assessments"][0]["evidence_paths"] = ["missing/maturity-proof.md"]
    broken_audit = tmp_path / "audit.json"
    broken_audit.write_text(json.dumps(audit, ensure_ascii=False), encoding="utf-8")

    failures = gate.validate(gate.MATRIX, broken_audit, check_wiring=False)

    assert len(failures) >= 1
    assert any("دليل غير موجود" in failure for failure in failures)


def test_engineering_maturity_matrix_rejects_missing_legacy_or_future_scope(
    tmp_path: Path,
) -> None:
    matrix = json.loads(gate.MATRIX.read_text(encoding="utf-8"))
    matrix["coverage_policy"]["applies_to"] = ["future_code"]
    broken_matrix = tmp_path / "matrix.json"
    broken_matrix.write_text(json.dumps(matrix, ensure_ascii=False), encoding="utf-8")

    failures = gate.validate(broken_matrix, gate.AUDIT, check_wiring=False)

    assert len(failures) >= 1
    assert any("coverage_policy" in failure for failure in failures)
