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


def test_gate_blocks_when_retired_module_leaks_into_cli(tmp_path, monkeypatch) -> None:
    """البرهان السلبي (D-270 L4): شجرةٌ مكسورة عمداً يجب أن تُحمِّر البوّابة.

    نبني نسخة CLI تستورد وحدةً مسحوبة (`cbam_calculator`) وتُسقِط أمراً من
    مسار العميل المُعلَن، ثم نوجّه البوّابة إليها: يجب أن تحجب (exit 1)
    وتسمّي التسريب — لا أن تخرج بصفرٍ أعمى.
    """
    gate = _load_gate()
    broken_engine = tmp_path / "hard_currency_engine"
    broken_engine.mkdir()
    (broken_engine / "cli.py").write_text(
        "from cbam_calculator import compute\n"
        'CUSTOMER_PATH_COMMANDS = ("france", "belgium")\n'
        "def build_parser():\n    return None\n"
        "def cmd_france(args):\n    return 0\n"
        "def cmd_belgium(args):\n    return 0\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(gate, "ENGINE", broken_engine)
    failures = gate._failures()
    assert len(failures) >= 1
    assert gate.main() == 1
    assert any("retired modules exposed" in failure for failure in failures)
    assert any("customer path drifted" in failure for failure in failures)
