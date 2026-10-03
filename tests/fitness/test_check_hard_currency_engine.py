from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "fitness" / "check_hard_currency_engine.py"


def _load_gate():
    spec = importlib.util.spec_from_file_location("hce_quality_gate", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_hce_quality_gate_passes() -> None:
    gate = _load_gate()
    assert gate._failures() == []


def test_customer_path_is_explicitly_bounded() -> None:
    gate = _load_gate()
    assert {"france", "belgium", "crm"} == gate.EXPECTED_COMMANDS
    assert {"cbam_calculator", "zatca_validator", "eaa_scanner"} == gate.FORBIDDEN_CLIENT_MODULES
