"""Regenerates testing/baselines/backtest_metrics.json.

Run this only when a change to the engine or a strategy is *meant* to move the
numbers, and say so in the commit message:

    uv run python testing/generate_baseline.py

Always run it through `uv`, so the baseline reflects the locked engine version.
A different backtesting.py release moves Sharpe and Sortino slightly, and the
baseline is meant to notice that.

A diff in that file is the point of the regression test. It should never be
regenerated to make a red test go green without understanding why it moved.
"""

import json
import sys
from pathlib import Path

# Run as a plain script, so the repo root is not on sys.path the way pytest puts
# it there via the pythonpath setting in pyproject.toml.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from quant_core.testing import synthetic_ohlcv
from testing.regression_runs import RUNS, run_one

BASELINE = Path(__file__).parent / "baselines" / "backtest_metrics.json"


def main() -> None:
    data = synthetic_ohlcv()
    baseline = {name: run_one(cls, commission, data) for name, (cls, commission) in RUNS.items()}
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE.write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n")
    print(f"wrote {BASELINE} ({len(baseline)} runs)")


if __name__ == "__main__":
    main()
