#!/usr/bin/env python3
"""يفرض وجود دستور منع Vibe Coding وربطه بكل مسارات إقلاع الوكلاء وCI."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONSTITUTION = ROOT / "docs/architecture/VIBE_CODING_PREVENTION_CONSTITUTION.md"
AGENTS = ROOT / "AGENTS.md"
CLAUDE = ROOT / "CLAUDE.md"
INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
MANIFEST = ROOT / "docs/DOCUMENTATION_MANIFEST.json"
CI = ROOT / ".github/workflows/ci.yml"
GATE = "scripts/fitness/check_vibe_coding_constitution.py"
REQUIRED_LAWS = ("L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9", "L10", "L11", "L12")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def main() -> int:
    failures: list[str] = []
    constitution = _read(CONSTITUTION)
    if not constitution:
        failures.append("constitution file is missing")
    for law in REQUIRED_LAWS:
        if f"### {law} —" not in constitution:
            failures.append(f"constitution is missing {law}")

    agents = _read(AGENTS)
    claude = _read(CLAUDE)
    index = _read(INDEX)
    manifest = _read(MANIFEST)
    ci = _read(CI)
    if "VIBE_CODING_PREVENTION_CONSTITUTION.md" not in agents:
        failures.append("AGENTS.md does not require the constitution")
    if "VIBE_CODING_PREVENTION_CONSTITUTION.md" not in claude:
        failures.append("CLAUDE.md does not expose the constitution")
    if "VIBE_CODING_PREVENTION_CONSTITUTION.md" not in index:
        failures.append("documentation index does not list the constitution")
    if '"path": "docs/architecture/VIBE_CODING_PREVENTION_CONSTITUTION.md"' not in manifest:
        failures.append("documentation manifest does not register the constitution")

    guardrails_start = ci.find("  guardrails:")
    required_start = ci.find("  required-ci:")
    guardrails = ci[guardrails_start : required_start if required_start >= 0 else None]
    if GATE not in guardrails:
        failures.append("constitution gate is not inside CI guardrails")
    if required_start < 0 or "guardrails," not in ci[required_start:]:
        failures.append("required-ci does not depend on guardrails")
    if "set -euo pipefail" not in guardrails:
        failures.append("guardrails is not fail-closed")

    if failures:
        for failure in failures:
            print(f"VIBE CODING CONSTITUTION: FAIL: {failure}")
        return 1
    print("VIBE CODING CONSTITUTION: PASS — agent entrypoints and required CI are wired")
    return 0


if __name__ == "__main__":
    sys.exit(main())
