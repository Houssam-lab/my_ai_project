#!/usr/bin/env python3
"""
CI gate — verify SECRET_KEY consistency across all service-launch blocks in
supervisor.sh.

D-WS-SECRET-KEY-001 (2026-05-26): The catastrophic 4401 cycle that haunted
the user for days was caused by ONE line in supervisor.sh:

    # user-service block (BEFORE):
    SECRET_KEY="${SECRET_KEY:-cogniforge-user-service-dev-key}"  ❌ unique default

    # monolith / orchestrator (always):
    SECRET_KEY="${SECRET_KEY:-dev-secret-change-me}"             ✓ shared default

When Codespaces users don't set SECRET_KEY as a secret, services diverged
silently. user-service signed JWTs with one key; monolith verified with
another. Every WS handshake → 4401 → kick → cycle.

This gate prevents that drift from ever returning. It greps supervisor.sh
for SECRET_KEY assignments and asserts:
  1. All non-trivial defaults are the same literal.
  2. The canonical default is `dev-secret-change-me`.

Hardening (2026-10-03) — this gate was mutation-tested and found FAIL-OPEN on
the *class* of defect while STRONG on the historical *instance*. Two holes,
both now closed:

  M2 · SILENT SCOPE NARROWING. Detection was keyed to variable *names*
      (`shared_<x>_secret`). Renaming one assignment removed it from the scan,
      so the same drift that caused the 4401 cycle became invisible while the
      gate printed "✅ All 4 default(s) agree" — green, with the count quietly
      down from 5. Fixed by matching the `${SECRET_KEY:-...}` *expansion*
      itself, which no rename can escape, plus a shrink-only floor on the
      number of assignments found.

  M3 · EXPLICIT FAIL-OPEN. Finding zero assignments returned 0 ("cannot
      verify"). Deleting every assignment — the most complete form of the
      breach — passed. A gate that cannot verify must not report success.
      Fixed: unverifiable is now failure.

Exit codes:
  0 — all good
  1 — drift detected, scope narrowed, or verification impossible
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SUPERVISOR = ROOT / ".devcontainer" / "supervisor.sh"
CANONICAL_DEFAULT = "dev-secret-change-me"

#: عدد التعيينات المرصودة فعلياً عند التقسية (2026-10-03). سقفٌ لا يَنزل:
#: خدمةٌ جديدة ترفعه، وأي هبوطٍ يعني أن تعييناً اختفى أو أفلت من الفحص —
#: وكلاهما هو بالضبط ما سمح للعطب الأصلي بالمرور.
MIN_EXPECTED_ASSIGNMENTS = 5


def _scan(code_lines: list[tuple[int, str]]) -> tuple[list[tuple[int, str]], int]:
    """استخراج كل قيمةٍ افتراضية تُمنَح لـSECRET_KEY، وعدّ فحوص الحضور.

    نُطابق **التوسعة** `${SECRET_KEY:-<default>}` نفسها، لا أسماء المتغيّرات.
    هذا هو جوهر التقسية: الاسم يُعاد تسميته، أمّا التوسعة فلا مهرب منها —
    فأيّ سطرٍ يمنح SECRET_KEY قيمةً افتراضية يقع في الشبكة مهما سُمّي.
    القالبان القديمان (`SECRET_KEY="..."` و`shared_*_secret="..."`) مُحتوَيان
    في هذا القالب حرفياً، فالتغطية تتّسع ولا تضيق.

    Returns:
        (التعيينات مع أرقام أسطرها، عدد فحوص الحضور الفارغة).
    """
    expansion_pattern = re.compile(r"\$\{SECRET_KEY:-([^}]*)\}")
    defaults_found: list[tuple[int, str]] = []
    presence_checks = 0
    for line_no, line in code_lines:
        for m in expansion_pattern.finditer(line):
            default = m.group(1)
            # `${SECRET_KEY:-}` بقيمةٍ فارغة ليس تعييناً بل فحص حضور
            # (`if [ -n ... ]`) — لا يُسهم في الانحراف فلا يُحسب ولا يُشوّش.
            if default == "":
                presence_checks += 1
                continue
            defaults_found.append((line_no, default))
    return defaults_found, presence_checks


def main() -> int:
    if not SUPERVISOR.is_file():
        print(f"❌ supervisor.sh not found at {SUPERVISOR}")
        return 1

    text = SUPERVISOR.read_text()
    # Skip shell comment lines so we only inspect actual code.
    code_lines: list[tuple[int, str]] = []
    for i, raw in enumerate(text.splitlines(), start=1):
        if raw.lstrip().startswith("#"):
            continue
        code_lines.append((i, raw))

    defaults_found, presence_checks = _scan(code_lines)

    print("=" * 70)
    print("D-WS-SECRET-KEY-001 — SECRET_KEY consistency gate")
    print("=" * 70)
    print()

    if not defaults_found:
        print("❌ No SECRET_KEY default assignments found in supervisor.sh.")
        print("   This gate previously returned success here. That was wrong:")
        print("   deleting every assignment is the most complete form of the")
        print("   breach, and it passed. A gate that cannot verify its claim")
        print("   must not report that the claim holds.")
        print()
        print(f"   Expected at least {MIN_EXPECTED_ASSIGNMENTS} assignment(s).")
        print("   If supervisor.sh legitimately stopped defaulting SECRET_KEY,")
        print("   update this gate deliberately — do not let it pass by silence.")
        return 1

    print(f"Found {len(defaults_found)} SECRET_KEY default assignment(s):")
    for line_no, default in defaults_found:
        marker = "✓" if default == CANONICAL_DEFAULT else "✗"
        print(f"  {marker} line {line_no}: default = `{default}`")
    print()

    if len(defaults_found) < MIN_EXPECTED_ASSIGNMENTS:
        print(
            f"❌ SCOPE NARROWED: found {len(defaults_found)} assignment(s), "
            f"expected at least {MIN_EXPECTED_ASSIGNMENTS}."
        )
        print("   An assignment was removed or now escapes detection. Drift can")
        print("   hide in whatever is no longer being read, which is how the")
        print("   original 4401 cycle survived review.")
        print("   If a service was genuinely retired, lower the floor on purpose.")
        return 1

    unique_defaults = {d for _, d in defaults_found}
    if len(unique_defaults) > 1:
        print(f"❌ DRIFT DETECTED: {len(unique_defaults)} distinct defaults:")
        for d in sorted(unique_defaults):
            print(f"     - `{d}`")
        print()
        print("All services sharing JWTs MUST use the same default. The canonical")
        print(f"default is `{CANONICAL_DEFAULT}`.")
        return 1

    (only,) = unique_defaults
    if only != CANONICAL_DEFAULT:
        print(f"❌ Non-canonical default in use: `{only}`")
        print(f"   Expected: `{CANONICAL_DEFAULT}`")
        return 1

    print(f"✅ All {len(defaults_found)} default(s) agree on `{CANONICAL_DEFAULT}`.")
    print(f"   (plus {presence_checks} presence check(s) with no default — not drift)")
    print()
    print("D-WS-SECRET-KEY-001 invariants verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
