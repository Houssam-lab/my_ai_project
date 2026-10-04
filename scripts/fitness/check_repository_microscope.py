#!/usr/bin/env python3
"""يفرض مرور أي تغيير على قراءة مجهرية للمستودع كله.

الغرض ليس ادعاء أن الوكيل فهم كل سطر بمجرد حساب hash، بل جعل عبارة
"درست المستودع حرفاً بحرف" لها أثر قابل للفحص: البوابة تقرأ كل ملف متتبع
وكل ملف جديد غير متتبع قراءة بايتية، وتطابق بصمة غير دائرية داخل حزمة القبول.
ملف حزمة القبول نفسه مستثنى من البصمة لأن تضمينها يجعل الإثبات دائرياً.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs/changes/CURRENT_CODE_ACCEPTANCE_PACKET.json"
PACKET_REL = "docs/changes/CURRENT_CODE_ACCEPTANCE_PACKET.json"
MODE = "FULL_REPOSITORY_BYTE_CENSUS_EXCLUDING_PACKET"
REFRESH_COMMAND = "python scripts/fitness/check_repository_microscope.py --update"


def _run_git(args: list[str]) -> str:
    completed = subprocess.run(
        ["git", "-c", "core.quotepath=false", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def _tracked_paths() -> set[str]:
    output = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    return {path.decode("utf-8") for path in output.split(b"\0") if path}


def _untracked_paths() -> set[str]:
    paths: set[str] = set()
    for line in _run_git(["status", "--porcelain=v1", "--untracked-files=all"]).splitlines():
        if line.startswith("?? "):
            relative = line[3:].strip()
            if (ROOT / relative).is_file():
                paths.add(relative)
    return paths


def repository_paths() -> list[str]:
    """المسارات التي يقرأها المجهر: المتتبع + الجديد غير المتتبع، بلا حزمة القبول."""
    paths = (_tracked_paths() | _untracked_paths()) - {PACKET_REL}
    return sorted(path for path in paths if (ROOT / path).is_file())


def build_snapshot(paths: list[str] | None = None) -> dict[str, Any]:
    """يقرأ الملفات بايتاً بايتاً ويبني بصمة غير دائرية للمستودع."""
    selected_paths = repository_paths() if paths is None else sorted(paths)
    digest = hashlib.sha256()
    total_bytes = 0
    total_newlines = 0
    max_file = {"path": "", "bytes": 0}
    for relative in selected_paths:
        payload = (ROOT / relative).read_bytes()
        file_digest = hashlib.sha256(payload).hexdigest()
        size = len(payload)
        total_bytes += size
        total_newlines += payload.count(b"\n")
        if size > max_file["bytes"]:
            max_file = {"path": relative, "bytes": size}
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(size).encode("ascii"))
        digest.update(b"\0")
        digest.update(file_digest.encode("ascii"))
        digest.update(b"\0")
    return {
        "mode": MODE,
        "file_count_excluding_packet": len(selected_paths),
        "total_bytes_excluding_packet": total_bytes,
        "total_newlines_excluding_packet": total_newlines,
        "sha256_excluding_packet": digest.hexdigest(),
        "largest_file_excluding_packet": max_file,
        "packet_excluded_for_non_circular_hash": PACKET_REL,
        "refresh_command": REFRESH_COMMAND,
    }


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_payload(packet: dict[str, Any], computed: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    microscope = packet.get("repository_microscope")
    if not isinstance(microscope, dict):
        return ["حزمة القبول تفتقد repository_microscope — لا دليل قراءة مجهرية للمستودع"]

    expected_scalars = (
        "mode",
        "file_count_excluding_packet",
        "total_bytes_excluding_packet",
        "total_newlines_excluding_packet",
        "sha256_excluding_packet",
        "packet_excluded_for_non_circular_hash",
    )
    for key in expected_scalars:
        if microscope.get(key) != computed.get(key):
            failures.append(
                f"repository_microscope.{key} stale: "
                f"recorded={microscope.get(key)!r}, actual={computed.get(key)!r}"
            )

    if microscope.get("applies_to_existing_code") is not True:
        failures.append("repository_microscope.applies_to_existing_code يجب أن يكون true")
    if microscope.get("applies_to_future_code") is not True:
        failures.append("repository_microscope.applies_to_future_code يجب أن يكون true")
    if microscope.get("old_before_new") is not True:
        failures.append("repository_microscope.old_before_new يجب أن يكون true")
    if microscope.get("grandfathering_forbidden") is not True:
        failures.append("repository_microscope.grandfathering_forbidden يجب أن يكون true")

    for field in ("legacy_rule_ar", "future_rule_ar", "operator_attestation_ar"):
        if not _non_empty_string(microscope.get(field)):
            failures.append(f"repository_microscope.{field} فارغ")
    return failures


def _load_packet() -> dict[str, Any] | None:
    if not PACKET.is_file():
        print(f"❌ حزمة القبول مفقودة: {PACKET.relative_to(ROOT)}")
        return None
    try:
        payload = json.loads(PACKET.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"❌ حزمة القبول ليست JSON صالحاً: {exc}")
        return None
    if not isinstance(payload, dict):
        print("❌ حزمة القبول يجب أن تكون object")
        return None
    return payload


def _write_packet(packet: dict[str, Any], computed: dict[str, Any]) -> None:
    packet["repository_microscope"] = {
        **computed,
        "applies_to_existing_code": True,
        "applies_to_future_code": True,
        "old_before_new": True,
        "grandfathering_forbidden": True,
        "legacy_rule_ar": "قُرئ المستودع المتتبع والملفات الجديدة غير المتتبعة قراءة بايتية غير دائرية؛ الكود القديم ليس معفى ويُدقَّق عند لمسه أو الاعتماد عليه.",
        "future_rule_ar": "أي كود أو عقد أو Workflow مستقبلي لا يدخل قبل تحديث هذه البصمة وحزمة القبول.",
        "operator_attestation_ar": "هذا ليس ادعاء فهم شامل بذاته؛ إنه شرط مجهر آلي يسبق التحليل البشري والمصفوفة، ويجعل تجاهل القديم مرئياً.",
    }
    PACKET.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check or refresh repository microscope proof.")
    parser.add_argument(
        "--update",
        action="store_true",
        help="refresh repository_microscope in the acceptance packet",
    )
    args = parser.parse_args(argv)

    packet = _load_packet()
    if packet is None:
        return 1
    computed = build_snapshot()
    if args.update:
        _write_packet(packet, computed)
        print(
            json.dumps(
                {
                    "repository_microscope": "updated",
                    "file_count_excluding_packet": computed["file_count_excluding_packet"],
                    "sha256_excluding_packet": computed["sha256_excluding_packet"],
                },
                ensure_ascii=False,
            )
        )
        return 0

    failures = validate_payload(packet, computed)
    if failures:
        print("❌ مجهر المستودع مخروق:\n")
        for failure in failures:
            print(f"  • {failure}")
        return 1
    print(
        "✅ مجهر المستودع: "
        f"{computed['file_count_excluding_packet']} ملفاً قُرئت بايتياً "
        f"({computed['total_bytes_excluding_packet']} bytes)، والقديم/المستقبل داخل النطاق."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
