"""Negative proofs for the acceptance packet's pre-modification and deletion controls."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "fitness"))

import check_code_acceptance as acceptance_gate


def _policy() -> dict:
    return json.loads(
        (ROOT / "docs/governance/ENGINEERING_GOVERNANCE_POLICY.json").read_text(encoding="utf-8")
    )


def test_pre_modification_evidence_is_required() -> None:
    """Feature-first packets without current state or old-debt analysis are red."""
    failures = acceptance_gate.validate_pre_modification({}, _policy())
    assert len(failures) >= 1
    assert "pre_modification" in "\n".join(failures)


def test_false_external_verified_claim_is_rejected() -> None:
    """A checkout cannot turn an unavailable GitHub Admin/API observation into VERIFIED."""
    pre_modification = {
        field: "evidence"
        for field in _policy()["pre_modification_packet"]["required_fields"]
        if field not in {"foundational_frontier", "claim_statuses"}
    }
    pre_modification["foundational_frontier"] = {
        "status": "NO_BLOCKING_FOUNDATIONAL_DEFECT_IDENTIFIED"
    }
    pre_modification["claim_statuses"] = {"branch_protection_live_state": "RUNTIME " + "VERIFIED"}
    failures = acceptance_gate.validate_pre_modification(
        {"pre_modification": pre_modification}, _policy()
    )
    assert len(failures) >= 1
    assert "falsely claims local verification" in "\n".join(failures)


def test_actual_deleted_path_cannot_be_hidden_by_zero_declaration(monkeypatch) -> None:
    """A declared zero is not proof when Git reports a deleted test or gate."""
    monkeypatch.setattr(acceptance_gate, "run_git", lambda _args: "tests/test_removed.py\n")
    monkeypatch.delenv("CODE_ACCEPTANCE_BASE_SHA", raising=False)
    assert acceptance_gate.current_deleted_paths() == ["tests/test_removed.py"]
