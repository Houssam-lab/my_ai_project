"""ISS-212 — a test name long enough to flood the CI log is refused at collection.

A parametrized test printed its 2 MB payload as its name. On the CI runner that single
2,097,263-character line stopped the runner from responding: test-monolith hit its
45-minute limit four times in a row and GitHub kept no log. Locally the same suite passes,
so only a bound on the name itself keeps the failure from coming back.
"""

from __future__ import annotations

import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from tests.conftest_support.policy import MAX_NODE_ID_CHARS, overlong_node_ids

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_a_name_over_the_bound_is_reported() -> None:
    long_name = "tests/x.py::test_x[" + "x" * MAX_NODE_ID_CHARS + "]"
    offenders = overlong_node_ids(["tests/x.py::test_short", long_name])
    assert len(offenders) == 1
    assert f"({len(long_name)} chars)" in offenders[0]


def test_a_name_at_the_bound_is_accepted() -> None:
    assert overlong_node_ids(["t" * MAX_NODE_ID_CHARS]) == []


def test_the_hook_is_registered_on_the_conftest_module(request: pytest.FixtureRequest) -> None:
    """A hook that only lives in an imported shard is never called (ISS-213)."""
    impls = request.config.pluginmanager.hook.pytest_collection_finish.get_hookimpls()
    owners = {getattr(impl.plugin, "__name__", "") for impl in impls}
    assert any(owner.endswith("tests.conftest") or owner == "conftest" for owner in owners), owners


def test_collection_fails_on_a_planted_overlong_name() -> None:
    """Negative proof: a real parametrized test that prints its payload stops collection."""
    probe = REPO_ROOT / "tests" / f"test_iss212_probe_{uuid.uuid4().hex[:8]}.py"
    probe.write_text(
        "import pytest\n\n"
        f"@pytest.mark.parametrize('payload', ['p' * {MAX_NODE_ID_CHARS + 50}])\n"
        "def test_payload(payload):\n"
        "    assert payload\n",
        encoding="utf-8",
    )
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--collect-only",
                "-q",
                "-p",
                "no:cacheprovider",
                str(probe.relative_to(REPO_ROOT)),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
    finally:
        probe.unlink(missing_ok=True)
    output = result.stdout + result.stderr
    assert result.returncode != 0, output[-2000:]
    assert "ISS-212" in output, output[-2000:]
