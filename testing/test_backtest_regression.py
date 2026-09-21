"""Pinned backtest metrics.

A failure here means a change moved the numbers. That is not automatically a bug,
but it is never something to accept without reading. If the move is intended,
regenerate with `python testing/generate_baseline.py` and explain the diff in the
commit message.
"""

import json
from pathlib import Path

import pytest

from testing.regression_runs import PINNED_METRICS, RUNS, run_one

BASELINE_PATH = Path(__file__).parent / "baselines" / "backtest_metrics.json"


@pytest.fixture(scope="module")
def baseline() -> dict:
    if not BASELINE_PATH.exists():  # pragma: no cover
        pytest.fail(f"missing baseline at {BASELINE_PATH}; run testing/generate_baseline.py")
    return json.loads(BASELINE_PATH.read_text())


def test_baseline_covers_every_pinned_run(baseline):
    assert set(baseline) == set(RUNS), (
        "the baseline and the pinned run list have drifted apart; "
        "regenerate with testing/generate_baseline.py"
    )


@pytest.mark.parametrize("name", list(RUNS), ids=list(RUNS))
def test_metrics_match_baseline(name, baseline, ohlcv):
    strategy_cls, commission = RUNS[name]
    actual = run_one(strategy_cls, commission, ohlcv)
    expected = baseline[name]

    for metric in PINNED_METRICS:
        if expected[metric] is None:
            assert actual[metric] is None, f"{name}: {metric} became {actual[metric]}"
        else:
            assert actual[metric] == pytest.approx(expected[metric], rel=1e-6), (
                f"{name}: {metric} moved from {expected[metric]} to {actual[metric]}"
            )
