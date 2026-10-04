from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "fitness" / "check_vibe_coding_constitution.py"


def _load_gate():
    spec = importlib.util.spec_from_file_location("vibe_constitution_gate", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_constitution_is_wired_to_agent_entrypoints_and_ci() -> None:
    module = _load_gate()
    assert module.main() == 0


def test_gate_blocks_when_constitution_file_is_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """البرهان السلبي (D-270 L4): الخُضرة على مُدخَلٍ مكسورٍ عمداً عمى لا سلامة.

    نوجّه البوّابة إلى دستورٍ غير موجود: يجب أن تحجب (exit 1) وتسمّي
    الغياب، لا أن تصمت. هذا يُثبِت أنّها «تحجب» لا أنّها «تعمل» فقط.
    """
    module = _load_gate()
    monkeypatch.setattr(module, "CONSTITUTION", tmp_path / "missing_constitution.md")
    assert module.main() == 1


def test_gate_blocks_when_agents_entrypoint_drops_the_constitution(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """برهانٌ سلبيٌّ ثانٍ: AGENTS.md بلا إحالةٍ للدستور ⇒ البوّابة حمراء."""
    module = _load_gate()
    severed_agents = tmp_path / "AGENTS.md"
    severed_agents.write_text("# agents file with no constitution link\n", encoding="utf-8")
    monkeypatch.setattr(module, "AGENTS", severed_agents)
    assert module.main() == 1


def test_gate_blocks_when_maturity_matrix_is_not_bound_to_constitution(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """أي دستور يسمح بالقفز فوق مصفوفة النضج ليس دستور منع Vibe Coding."""
    module = _load_gate()
    severed_constitution = tmp_path / "VIBE_CODING_PREVENTION_CONSTITUTION.md"
    text = module.CONSTITUTION.read_text(encoding="utf-8").replace(
        module.MATURITY_GATE,
        "scripts/fitness/missing_maturity_gate.py",
    )
    severed_constitution.write_text(text, encoding="utf-8")
    monkeypatch.setattr(module, "CONSTITUTION", severed_constitution)
    assert module.main() == 1


def test_gate_blocks_when_old_and_future_code_clause_is_removed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """الكود القديم والمستقبلي كلاهما تحت الدستور؛ حذف ذلك يحمّر البوابة."""
    module = _load_gate()
    weakened_constitution = tmp_path / "VIBE_CODING_PREVENTION_CONSTITUTION.md"
    text = (
        module.CONSTITUTION.read_text(encoding="utf-8")
        .replace(
            module.LEGACY_PHRASE,
            "legacy gap hidden",
        )
        .replace(
            module.FUTURE_PHRASE,
            "future gap hidden",
        )
    )
    weakened_constitution.write_text(text, encoding="utf-8")
    monkeypatch.setattr(module, "CONSTITUTION", weakened_constitution)
    assert module.main() == 1
