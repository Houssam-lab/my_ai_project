#!/usr/bin/env python3
"""Machine-check the repository engineering constitution and its change controls.

This is intentionally stdlib-only. It checks the repository controls that are
observable from a checkout; branch-protection state and independent approval
remain external GitHub-admin controls and are reported as such, never guessed.
"""

from __future__ import annotations

import fnmatch
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "docs/governance/ENGINEERING_GOVERNANCE_POLICY.json"
CONSTITUTION_PATH = ROOT / "ENGINEERING_CONSTITUTION.md"
CI_PATH = ROOT / ".github/workflows/ci.yml"
CODEOWNERS_PATH = ROOT / ".github/CODEOWNERS"
DOC_INDEX_PATH = ROOT / "docs/DOCUMENTATION_INDEX.md"
DOC_MANIFEST_PATH = ROOT / "docs/DOCUMENTATION_MANIFEST.json"


@dataclass(frozen=True)
class Change:
    """A changed repository path and its Git status."""

    status: str
    path: str


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _run_git(args: list[str]) -> str:
    completed = subprocess.run(
        ["git", "-c", "core.quotepath=false", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def _parse_name_status(output: str) -> list[Change]:
    changes: list[Change] = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0][:1]
        paths = parts[1:]
        # Treat both sides of a rename/copy as sensitive. A protected file must
        # not be escaped merely by changing its name.
        for path in paths:
            changes.append(Change(status=status, path=path))
    return changes


def _working_tree_changes() -> list[Change]:
    changes: list[Change] = []
    for args in (
        ["diff", "--name-status", "-M"],
        ["diff", "--cached", "--name-status", "-M"],
    ):
        changes.extend(_parse_name_status(_run_git(args)))
    for line in _run_git(["status", "--porcelain=v1", "--untracked-files=all"]).splitlines():
        if line.startswith("?? "):
            changes.append(Change(status="A", path=line[3:].strip()))
    return _unique_changes(changes)


def changed_paths() -> list[Change]:
    """Read a PR diff when a base SHA is supplied, otherwise the worktree."""
    base = os.environ.get("GOVERNANCE_BASE_SHA", "").strip()
    if base:
        return _unique_changes(
            _parse_name_status(_run_git(["diff", "--name-status", "-M", f"{base}...HEAD"]))
        )
    return _working_tree_changes()


def _unique_changes(changes: list[Change]) -> list[Change]:
    return sorted(set(changes), key=lambda change: (change.path, change.status))


def _added_lines(base: str) -> dict[str, list[str]]:
    """Changed additions, including full contents of new worktree files."""
    output = _run_git(
        ["diff", "--unified=0", f"{base}...HEAD"] if base else ["diff", "--unified=0"]
    )
    lines_by_path: dict[str, list[str]] = {}
    current: str | None = None
    for line in output.splitlines():
        if line.startswith("+++ b/"):
            current = line.removeprefix("+++ b/")
            lines_by_path.setdefault(current, [])
        elif current and line.startswith("+") and not line.startswith("+++"):
            lines_by_path[current].append(line[1:])
    if not base:
        for change in changed_paths():
            if change.status == "A" and (ROOT / change.path).is_file():
                lines_by_path.setdefault(
                    change.path, (ROOT / change.path).read_text(encoding="utf-8").splitlines()
                )
    return lines_by_path


def _matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def _amendment_directory(policy: dict[str, Any]) -> str:
    return str(policy["amendment_records"]["directory"]).rstrip("/")


def _is_amendment(path: str, policy: dict[str, Any]) -> bool:
    return path.startswith(f"{_amendment_directory(policy)}/") and path.endswith(".md")


def _load_policy() -> tuple[dict[str, Any] | None, list[str]]:
    if not POLICY_PATH.is_file():
        return None, ["machine-readable engineering governance policy is missing"]
    try:
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"machine-readable policy is invalid JSON: {exc}"]
    if not isinstance(policy, dict):
        return None, ["machine-readable policy root must be an object"]
    return policy, []


def _require_nonempty_list(policy: dict[str, Any], field: str, failures: list[str]) -> list[Any]:
    value = policy.get(field)
    if not isinstance(value, list) or not value:
        failures.append(f"policy.{field} must be a non-empty list")
        return []
    return value


def validate_project_remediation_gate(  # noqa: PLR0912, PLR0915
    policy: dict[str, Any], root: Path = ROOT
) -> list[str]:
    """Validate the mandatory live diagnostic and remediation start gate."""
    failures: list[str] = []
    gate = policy.get("project_remediation_gate")
    if not isinstance(gate, dict):
        return ["policy.project_remediation_gate must be an object"]

    diagnostic = str(gate.get("diagnostic_path", ""))
    remediation_plan = str(gate.get("remediation_plan_path", ""))
    if not diagnostic or not (root / diagnostic).is_file():
        failures.append("project remediation diagnostic path is missing")
    elif not _read(root / diagnostic).strip():
        failures.append("project remediation diagnostic is empty")

    plan_payload: dict[str, Any] | None = None
    if not remediation_plan or not (root / remediation_plan).is_file():
        failures.append("project remediation plan path is missing")
    else:
        try:
            loaded_plan = json.loads((root / remediation_plan).read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"project remediation plan is invalid JSON: {exc}")
        else:
            if not isinstance(loaded_plan, dict):
                failures.append("project remediation plan root must be an object")
            else:
                plan_payload = loaded_plan

    blocked_statuses = set(gate.get("blocked_statuses_for_critical", []))
    for status in ("OPEN", "UNKNOWN", "UNVERIFIED"):
        if status not in blocked_statuses:
            failures.append(f"critical remediation status `{status}` must remain blocking")
    if "CRITICAL" not in set(gate.get("critical_severities", [])):
        failures.append("project remediation gate must treat CRITICAL severity as blocking")
    if gate.get("non_self_certification_required") is not True:
        failures.append("project remediation closure must require non-self-certification")

    if plan_payload is not None:
        for field in gate.get("required_plan_fields", []):
            if plan_payload.get(str(field)) in (None, "", [], {}):
                failures.append(f"project remediation plan missing `{field}`")
        if diagnostic and plan_payload.get("diagnostic") != diagnostic:
            failures.append("project remediation plan diagnostic path does not match policy")
        remediations = plan_payload.get("remediations")
        if not isinstance(remediations, list) or not remediations:
            failures.append("project remediation plan must contain remediation records")
        else:
            required_fields = [str(field) for field in gate.get("required_remediation_fields", [])]
            critical_blockers = 0
            for index, item in enumerate(remediations, start=1):
                if not isinstance(item, dict):
                    failures.append(f"project remediation record {index} must be an object")
                    continue
                for field in required_fields:
                    if item.get(field) in (None, "", [], {}):
                        failures.append(f"project remediation record {index} missing `{field}`")
                if (
                    item.get("severity") in set(gate.get("critical_severities", []))
                    and item.get("status") in blocked_statuses
                ):
                    critical_blockers += 1
            if critical_blockers and "BLOCKED" not in str(plan_payload.get("status", "")):
                failures.append(
                    "project remediation plan has critical blockers but does not declare a blocked status"
                )

    for entrypoint in gate.get("required_agent_entrypoints", []):
        entrypoint_path = root / str(entrypoint)
        text = _read(entrypoint_path)
        if not text:
            failures.append(f"project remediation entrypoint is missing: {entrypoint}")
            continue
        if diagnostic not in text or remediation_plan not in text:
            failures.append(f"{entrypoint} does not bind the live diagnostic and remediation plan")
    return failures


def validate_policy(policy: dict[str, Any], root: Path = ROOT) -> list[str]:  # noqa: PLR0912, PLR0915
    """Validate static law, wiring, documentation, and ownership connections."""
    failures: list[str] = []
    if policy.get("$schema_version") != "1":
        failures.append("policy schema version must be 1")
    if policy.get("canonical_constitution") != "ENGINEERING_CONSTITUTION.md":
        failures.append("policy must name ENGINEERING_CONSTITUTION.md as canonical")
    if not (root / policy.get("canonical_constitution", "")).is_file():
        failures.append("canonical engineering constitution is missing")
    if policy.get("enforcer") != "scripts/fitness/check_engineering_governance.py":
        failures.append("policy enforcer path is wrong")
    if not (root / str(policy.get("enforcer", ""))).is_file():
        failures.append("engineering governance enforcer is missing")

    for path in _require_nonempty_list(policy, "entrypoints", failures):
        if not isinstance(path, str) or not (root / path).is_file():
            failures.append(f"policy entrypoint is missing: {path!r}")
    _require_nonempty_list(policy, "protected_paths", failures)
    _require_nonempty_list(policy, "required_evidence_statuses", failures)
    failures.extend(validate_project_remediation_gate(policy, root))

    packet = policy.get("pre_modification_packet")
    required_pre_modification = {
        "current_state",
        "architecture_and_boundaries",
        "existing_failures_and_old_debt",
        "dependency_path",
        "foundational_frontier",
        "root_cause",
        "intended_change",
        "affected_invariants",
        "test_plan",
        "rollback_strategy",
        "verification_strategy",
        "claim_statuses",
    }
    if not isinstance(packet, dict):
        failures.append("policy.pre_modification_packet must be an object")
    else:
        if set(packet.get("required_fields", [])) != required_pre_modification:
            failures.append("pre-modification packet fields are incomplete or drifted")
        if not (root / str(packet.get("path", ""))).is_file():
            failures.append("pre-modification packet path is missing")

    platform_controls = policy.get("platform_controls")
    if not isinstance(platform_controls, dict):
        failures.append("policy.platform_controls must be an object")
    else:
        if platform_controls.get("verification_status") != "EXTERNAL_ADMIN_VERIFICATION_REQUIRED":
            failures.append("policy must preserve explicit external-admin verification status")
        if not platform_controls.get("forbidden_local_claim_statuses"):
            failures.append("policy must forbid false local verification claims")

    amendment = policy.get("amendment_records")
    if not isinstance(amendment, dict):
        failures.append("policy.amendment_records must be an object")
    else:
        directory = root / str(amendment.get("directory", ""))
        if not directory.is_dir():
            failures.append("constitutional-amendment directory is missing")
        if amendment.get("new_record_required_for_protected_change") is not True:
            failures.append("protected changes must require a new amendment record")
        if amendment.get("append_only") is not True:
            failures.append("amendment records must be append-only")
        if not amendment.get("required_markers"):
            failures.append("amendment record markers must be declared")

    constitution = _read(root / "ENGINEERING_CONSTITUTION.md")
    for anchor in (
        "Mandatory pre-modification gate",
        "Old-problem frontier",
        "Microscopic diagnosis and compulsory remediation",
        "No self-certification",
        "Constitutional amendment",
        "Evidence status",
        "Immutability model",
    ):
        if anchor not in constitution:
            failures.append(f"constitution is missing required section: {anchor}")

    agents = _read(root / "AGENTS.md")
    claude = _read(root / "CLAUDE.md")
    context_registry = _read(root / "docs/governance/AGENT_CONTEXT_REGISTRY.json")
    for name, text in (("AGENTS.md", agents), ("CLAUDE.md", claude)):
        if "ENGINEERING_CONSTITUTION.md" not in text:
            failures.append(f"{name} does not load the engineering constitution")
        if "check_engineering_governance.py" not in text:
            failures.append(f"{name} does not expose the governance audit")
    if "ENGINEERING_CONSTITUTION.md" not in context_registry:
        failures.append("agent context registry does not load the engineering constitution")

    workflow = _read(root / ".github/workflows/ci.yml")
    guardrails_start = workflow.find("  guardrails:")
    required_start = workflow.find("  required-ci:")
    guardrails = workflow[guardrails_start : required_start if required_start >= 0 else None]
    if guardrails_start < 0 or "scripts/fitness/check_engineering_governance.py" not in guardrails:
        failures.append("engineering governance audit is not in CI guardrails")
    if required_start < 0 or "guardrails," not in workflow[required_start:]:
        failures.append("required-ci does not aggregate guardrails")

    codeowners = _read(root / ".github/CODEOWNERS")
    for required_owner_path in ("/ENGINEERING_CONSTITUTION.md", "/.github/", "/docs/", "/scripts/"):
        if required_owner_path not in codeowners:
            failures.append(f"CODEOWNERS does not protect {required_owner_path}")

    index = _read(root / "docs/DOCUMENTATION_INDEX.md")
    manifest = _read(root / "docs/DOCUMENTATION_MANIFEST.json")
    if "ENGINEERING_CONSTITUTION.md" not in index:
        failures.append("documentation index does not expose the engineering constitution")
    if '"path": "ENGINEERING_CONSTITUTION.md"' not in manifest:
        failures.append("documentation manifest does not register the engineering constitution")
    return failures


def validate_amendment_record(path: Path, policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if not path.is_file():
        return [f"amendment record is missing: {path.relative_to(ROOT)}"]
    text = path.read_text(encoding="utf-8")
    for marker in policy["amendment_records"]["required_markers"]:
        if marker not in text:
            failures.append(f"{path.name}: missing amendment marker `{marker}`")
    statuses = policy["amendment_records"].get("allowed_statuses", [])
    if not any(f"Status:** {status}" in text for status in statuses):
        failures.append(
            f"{path.name}: status must be pending independent review or emergency retrospective"
        )
    if "approved by author" in text.lower() or "self-approved" in text.lower():
        failures.append(f"{path.name}: author self-approval is forbidden")
    return failures


def validate_change_control(
    policy: dict[str, Any], changes: list[Change], root: Path = ROOT
) -> list[str]:
    """Require an append-only amendment record for every protected-file change."""
    failures: list[str] = []
    protected = [
        change
        for change in changes
        if _matches(change.path, list(policy["protected_paths"]))
        and not _is_amendment(change.path, policy)
    ]
    amendment_changes = [change for change in changes if _is_amendment(change.path, policy)]
    modified_records = [change.path for change in amendment_changes if change.status != "A"]
    if modified_records:
        failures.append(
            f"amendment records are append-only; modification/deletion is forbidden: {sorted(set(modified_records))}"
        )
    for change in amendment_changes:
        if change.status == "A":
            failures.extend(validate_amendment_record(root / change.path, policy))
    if protected and (
        policy["amendment_records"].get("new_record_required_for_protected_change") is True
        and not any(change.status == "A" for change in amendment_changes)
    ):
        failures.append(
            "constitutionally sensitive artifacts changed without a new amendment record: "
            f"{sorted({change.path for change in protected})}"
        )
    deleted_tests = [
        change.path
        for change in changes
        if change.status == "D"
        and any(
            change.path.startswith(prefix) for prefix in policy["test_integrity"]["test_prefixes"]
        )
    ]
    if deleted_tests:
        failures.append(f"test deletion is forbidden on the normal path: {sorted(deleted_tests)}")
    return failures


def validate_test_integrity(policy: dict[str, Any], added_lines: dict[str, list[str]]) -> list[str]:
    failures: list[str] = []
    prefixes = list(policy["test_integrity"]["test_prefixes"])
    forbidden = list(policy["test_integrity"]["forbidden_added_tokens"])
    for path, lines in added_lines.items():
        is_test_surface = (
            any(path.startswith(prefix) for prefix in prefixes)
            or path == ".github/workflows/ci.yml"
        )
        if not is_test_surface:
            continue
        for token in forbidden:
            if any(token in line for line in lines):
                failures.append(f"test/CI weakening token `{token}` added in {path}")
    return failures


def validate_dependency_and_migration_controls(
    policy: dict[str, Any], changes: list[Change], root: Path = ROOT
) -> list[str]:
    failures: list[str] = []
    changed_paths_only = {change.path for change in changes if change.status != "D"}
    dependency = policy["dependency_control"]
    manifest_changed = any(
        _matches(path, list(dependency["manifest_globs"])) for path in changed_paths_only
    )
    has_adr = any(
        _matches(path, [str(dependency["required_adr_glob"])]) for path in changed_paths_only
    )
    if manifest_changed and not has_adr:
        failures.append("dependency manifest changed without an ADR in the same governed change")

    migration = policy["migration_control"]
    migration_paths = [
        path for path in changed_paths_only if _matches(path, list(migration["path_globs"]))
    ]
    if migration_paths and migration.get("requires_changed_test") is True:
        test_prefixes = policy["test_integrity"]["test_prefixes"]
        if not any(
            any(path.startswith(prefix) for prefix in test_prefixes) for path in changed_paths_only
        ):
            failures.append("migration change requires an accompanying changed test")
    prohibited = [pattern.upper() for pattern in migration["forbidden_sql_patterns"]]
    for path in migration_paths:
        file_path = root / path
        if not file_path.is_file():
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore").upper()
        for pattern in prohibited:
            if pattern in text:
                failures.append(
                    f"destructive migration operation `{pattern}` is blocked in normal governance: {path}"
                )
    return failures


def main() -> int:
    policy, failures = _load_policy()
    if policy is not None:
        failures.extend(validate_policy(policy))
        changes = changed_paths()
        failures.extend(validate_change_control(policy, changes))
        failures.extend(
            validate_test_integrity(
                policy, _added_lines(os.environ.get("GOVERNANCE_BASE_SHA", "").strip())
            )
        )
        failures.extend(validate_dependency_and_migration_controls(policy, changes))
    if failures:
        print("❌ ENGINEERING GOVERNANCE: FAIL")
        for failure in failures:
            print(f"  • {failure}")
        return 1
    print(
        "✅ ENGINEERING GOVERNANCE: PASS — policy, amendment controls, CI wiring, and normal-path safeguards are intact."
    )
    print(
        "ℹ️ external platform status: EXTERNAL_ADMIN_VERIFICATION_REQUIRED (not asserted by this checkout)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
