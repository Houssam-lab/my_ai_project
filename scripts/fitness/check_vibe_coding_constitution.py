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
MATURITY_DOC = "ENGINEERING_MATURITY_MATRIX.md"
MATURITY_JSON = "ENGINEERING_MATURITY_MATRIX.json"
MATURITY_GATE = "scripts/fitness/check_engineering_maturity_matrix.py"
LEGACY_PHRASE = "الكود القديم"
FUTURE_PHRASE = "كود مستقبلي"
MICROSCOPE_GATE = "scripts/fitness/check_repository_microscope.py"
MICROSCOPE_FIELD = "repository_microscope"
DIAGNOSTIC = ".memory/project_diagnostic_truth.md"
REMEDIATION_PLAN = "docs/governance/PROJECT_REMEDIATION_PLAN.json"
FOUNDATION_CONSTITUTION = "docs/architecture/FOUNDATION_SAFETY_CONSTITUTION.md"
REQUIRED_LAWS = (
    "L1",
    "L2",
    "L3",
    "L4",
    "L5",
    "L6",
    "L7",
    "L8",
    "L9",
    "L10",
    "L11",
    "L12",
    "L13",
    "L14",
    "L15",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def main() -> int:  # noqa: PLR0912, PLR0915
    failures: list[str] = []
    constitution = _read(CONSTITUTION)
    if not constitution:
        failures.append("constitution file is missing")
    for law in REQUIRED_LAWS:
        if f"### {law} —" not in constitution:
            failures.append(f"constitution is missing {law}")
    # D-307: this repository is high-consequence by default. The risk ladder is
    # part of the enforced constitution, not explanatory prose that an agent may
    # bypass by calling a change "small" or "documentation-only".
    for anchor in (
        "تصنيف الخطر الكارثي للمشروع",
        "C0 — سلامة الحوكمة",
        "C1 — سلامة البيانات والخصوصية",
        "C2 — سلامة القرار الوكيلي",
        "C3 — سلامة التشغيل",
        "إذا تعذر تحديد المستوى، يُعامل التغيير كأعلى مستوى",
        "اختبار إيجابي وسلبي",
    ):
        if anchor not in constitution:
            failures.append(f"constitution is missing catastrophic-risk control: {anchor}")

    agents = _read(AGENTS)
    claude = _read(CLAUDE)
    index = _read(INDEX)
    manifest = _read(MANIFEST)
    ci = _read(CI)
    if "VIBE_CODING_PREVENTION_CONSTITUTION.md" not in agents:
        failures.append("AGENTS.md does not require the constitution")
    if MATURITY_DOC not in agents:
        failures.append("AGENTS.md does not require the engineering maturity matrix")
    if "VIBE_CODING_PREVENTION_CONSTITUTION.md" not in claude:
        failures.append("CLAUDE.md does not expose the constitution")
    if MATURITY_DOC not in claude:
        failures.append("CLAUDE.md does not expose the engineering maturity matrix")
    if "VIBE_CODING_PREVENTION_CONSTITUTION.md" not in index:
        failures.append("documentation index does not list the constitution")
    if MATURITY_DOC not in index:
        failures.append("documentation index does not list the engineering maturity matrix")
    if '"path": "docs/architecture/VIBE_CODING_PREVENTION_CONSTITUTION.md"' not in manifest:
        failures.append("documentation manifest does not register the constitution")
    if '"path": "docs/architecture/ENGINEERING_MATURITY_MATRIX.md"' not in manifest:
        failures.append("documentation manifest does not register the engineering maturity matrix")

    if (
        MATURITY_DOC not in constitution
        or MATURITY_JSON not in constitution
        or MATURITY_GATE not in constitution
    ):
        failures.append("constitution does not bind the engineering maturity matrix and its gate")
    if LEGACY_PHRASE not in constitution or FUTURE_PHRASE not in constitution:
        failures.append("constitution does not explicitly bind old and future code")
    if MICROSCOPE_GATE not in constitution or MICROSCOPE_FIELD not in constitution:
        failures.append("constitution does not bind the repository microscope gate")
    if DIAGNOSTIC not in constitution or REMEDIATION_PLAN not in constitution:
        failures.append(
            "constitution does not bind the live diagnostic and mandatory remediation plan"
        )
    if FOUNDATION_CONSTITUTION not in constitution:
        failures.append("constitution does not bind the foundation safety constitution")
    foundation = _read(ROOT / FOUNDATION_CONSTITUTION)
    for anchor in (
        "### L1 —",
        "### L12 —",
        "الأفق التاريخي والمستقبلي",
        "المجهر الكامل غير الدائري",
    ):
        if anchor not in foundation:
            failures.append(f"foundation constitution is missing: {anchor}")
    for path in (DIAGNOSTIC, REMEDIATION_PLAN, FOUNDATION_CONSTITUTION):
        if not (ROOT / path).is_file() or not (ROOT / path).read_text(encoding="utf-8").strip():
            failures.append(
                f"mandatory diagnostic/remediation artifact is missing or empty: {path}"
            )
    if (
        DIAGNOSTIC not in agents
        or REMEDIATION_PLAN not in agents
        or FOUNDATION_CONSTITUTION not in agents
    ):
        failures.append(
            "AGENTS.md does not require the diagnostic, remediation plan, and foundation constitution"
        )
    if (
        DIAGNOSTIC not in claude
        or REMEDIATION_PLAN not in claude
        or FOUNDATION_CONSTITUTION not in claude
    ):
        failures.append(
            "CLAUDE.md does not require the diagnostic, remediation plan, and foundation constitution"
        )
    if LEGACY_PHRASE not in claude or "مستقبلي" not in claude:
        failures.append("CLAUDE.md does not bind old and future code to the constitution")
    if "existing code" not in agents or "future code" not in agents:
        failures.append("AGENTS.md does not bind old and future code to the constitution")
    if MICROSCOPE_GATE not in agents or MICROSCOPE_FIELD not in agents:
        failures.append("AGENTS.md does not require repository microscope proof")
    if MICROSCOPE_GATE not in claude or MICROSCOPE_FIELD not in claude:
        failures.append("CLAUDE.md does not require repository microscope proof")

    guardrails_start = ci.find("  guardrails:")
    required_start = ci.find("  required-ci:")
    guardrails = ci[guardrails_start : required_start if required_start >= 0 else None]
    if GATE not in guardrails:
        failures.append("constitution gate is not inside CI guardrails")
    if MATURITY_GATE not in guardrails:
        failures.append("engineering maturity matrix gate is not inside CI guardrails")
    if MICROSCOPE_GATE not in guardrails:
        failures.append("repository microscope gate is not inside CI guardrails")
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
