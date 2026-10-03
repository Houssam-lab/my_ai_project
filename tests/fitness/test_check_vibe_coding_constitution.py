from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "fitness" / "check_vibe_coding_constitution.py"


def test_constitution_is_wired_to_agent_entrypoints_and_ci() -> None:
    spec = importlib.util.spec_from_file_location("vibe_constitution_gate", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.main() == 0
