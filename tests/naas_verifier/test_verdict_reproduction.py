"""D-303 · E10 — the reproduction command a verdict ships must actually run.

Before: every verdict's constraint-evaluation evidence carried
``python -m naas_verifier.cli run --corpus ar_fr``. The CLI never accepted
``--corpus``, so the command a reader was told to run exited 2. Evidence that
cannot be reproduced is a claim, not evidence (D-267 L7).
"""

from __future__ import annotations

import shlex
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from naas_verifier import cli
from naas_verifier.core import (
    Constraint,
    ConstraintSet,
    Dimension,
    EvidenceKind,
    Outcome,
    Step,
    Trajectory,
    verify,
)
from naas_verifier.core.verdict import REPRODUCTION_COMMAND

_MODULE_PREFIX = ["python", "-m", "naas_verifier.cli"]


def _verdict():
    trajectory = Trajectory(
        trajectory_id="t-repro",
        steps=(Step(0, "decide", "idle", "decided", tool="control", output="fired"),),
        final_output="fired",
        language="ar",
    )
    constraints = ConstraintSet(
        constraints=(
            Constraint("c::final", Dimension.FINAL_OUTCOME, "holds", lambda _t: Outcome.HOLDS),
        ),
        uncovered_reason={
            dimension: "not exercised by this reproduction test"
            for dimension in Dimension
            if dimension is not Dimension.FINAL_OUTCOME
        },
    )
    return verify(trajectory, constraints)


def test_every_verdict_ships_the_named_reproduction_command() -> None:
    trace = next(
        item for item in _verdict().evidence if item.kind is EvidenceKind.CONSTRAINT_EVALUATION
    )
    assert trace.reproduction == REPRODUCTION_COMMAND


def test_the_reproduction_command_runs_and_exits_zero(capsys) -> None:
    argv = shlex.split(REPRODUCTION_COMMAND)
    assert argv[:3] == _MODULE_PREFIX
    assert cli.main(argv[3:]) == 0
    assert "Measured against reference targets" in capsys.readouterr().out


def test_the_old_command_is_what_the_cli_rejected() -> None:
    """The negative proof: the string verdicts used to ship does not parse."""
    try:
        cli.main(["run", "--corpus", "ar_fr"])
    except SystemExit as exit_:
        assert exit_.code == 2
    else:  # pragma: no cover
        raise AssertionError("the old reproduction command parsed")
