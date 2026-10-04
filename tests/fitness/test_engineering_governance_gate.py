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


def test_project_remediation_gate_requires_entrypoint_binding(tmp_path: Path) -> None:
    """The live diagnostic and remediation plan must be visible at agent boot."""
    policy = _policy()
    diagnostic = tmp_path / ".memory" / "project_diagnostic_truth.md"
    diagnostic.parent.mkdir(parents=True)
    diagnostic.write_text("# diagnostic\n", encoding="utf-8")
    plan = tmp_path / "docs" / "governance" / "PROJECT_REMEDIATION_PLAN.json"
    plan.parent.mkdir(parents=True)
    plan.write_text(
        json.dumps(
            {
                "$schema_version": "1",
                "status": "OPEN_BLOCKED_FOR_PRODUCTION_CLAIMS",
                "diagnostic": ".memory/project_diagnostic_truth.md",
                "owner": "test",
                "rule": "critical remediation blocks production claims",
                "remediations": [
                    {
                        "id": "R1",
                        "severity": "CRITICAL",
                        "title": "test blocker",
                        "status": "OPEN",
                        "acceptance": "evidence",
                    }
                ],
                "amendment_rule": "no self-certification",
            }
        ),
        encoding="utf-8",
    )
    for entrypoint in ("AGENTS.md", "CLAUDE.md", "docs/governance/AGENT_CONTEXT_REGISTRY.json"):
        entrypoint_path = tmp_path / entrypoint
        entrypoint_path.parent.mkdir(parents=True, exist_ok=True)
        entrypoint_path.write_text("missing remediation binding\n", encoding="utf-8")

    failures = governance_gate.validate_project_remediation_gate(policy, tmp_path)

    assert len(failures) >= 1
    assert "does not bind the live diagnostic" in "\n".join(failures)


def test_project_remediation_gate_requires_open_unknown_unverified_to_block() -> None:
    """Critical remediation cannot become a decorative non-blocking list."""
    policy = _policy()
    policy["project_remediation_gate"]["blocked_statuses_for_critical"] = ["OPEN"]

    failures = governance_gate.validate_project_remediation_gate(policy)

    assert len(failures) >= 1
    assert "UNKNOWN" in "\n".join(failures)
    assert "UNVERIFIED" in "\n".join(failures)


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
