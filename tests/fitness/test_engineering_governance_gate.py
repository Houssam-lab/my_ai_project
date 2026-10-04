"""Negative proofs for the engineering-governance control plane."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "fitness"))

import check_engineering_governance as governance_gate


def _policy() -> dict:
    return json.loads(
        (ROOT / "docs/governance/ENGINEERING_GOVERNANCE_POLICY.json").read_text(encoding="utf-8")
    )


def test_engineering_governance_gate_is_green_on_repository() -> None:
    assert governance_gate.main() == 0


def test_protected_change_without_new_amendment_record_is_rejected() -> None:
    """A normal change cannot silently rewrite the agent constitution entry point."""
    failures = governance_gate.validate_change_control(
        _policy(), [governance_gate.Change(status="M", path="AGENTS.md")]
    )
    assert len(failures) >= 1
    assert "without a new amendment record" in "\n".join(failures)


def test_added_test_skip_is_rejected() -> None:
    """A test may not be weakened by turning an assertion into a silent skip."""
    forbidden_skip = "pytest" + ".skip("
    failures = governance_gate.validate_test_integrity(
        _policy(), {"tests/unit/test_example.py": [f"{forbidden_skip}'make CI green')"]}
    )
    assert len(failures) >= 1
    assert forbidden_skip in "\n".join(failures)


def test_ci_deselection_is_rejected() -> None:
    """A weakened CI command cannot silently deselect its failing test."""
    deselect = "--" + "deselect"
    failures = governance_gate.validate_test_integrity(
        _policy(), {".github/workflows/ci.yml": [f"pytest {deselect} tests/failing_test.py"]}
    )
    assert len(failures) >= 1
    assert deselect in "\n".join(failures)


def test_dependency_manifest_without_adr_is_rejected() -> None:
    """A dependency addition is architecture, not a casual line edit."""
    failures = governance_gate.validate_dependency_and_migration_controls(
        _policy(), [governance_gate.Change(status="M", path="requirements-prod.txt")]
    )
    assert len(failures) >= 1
    assert "without an ADR" in "\n".join(failures)


def test_destructive_migration_is_rejected(tmp_path: Path) -> None:
    """The normal path refuses irreversible SQL even when a test is present."""
    migration = tmp_path / "scripts" / "migrations" / "1000_bad.sql"
    migration.parent.mkdir(parents=True)
    migration.write_text("DROP TABLE customer_messages;\n", encoding="utf-8")
    failures = governance_gate.validate_dependency_and_migration_controls(
        _policy(),
        [
            governance_gate.Change(status="M", path="scripts/migrations/1000_bad.sql"),
            governance_gate.Change(status="M", path="tests/test_migration.py"),
        ],
        root=tmp_path,
    )
    assert len(failures) >= 1
    assert "DROP TABLE" in "\n".join(failures)
