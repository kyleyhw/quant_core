"""Test helpers for quant-core and for packages that build on it.

``probe`` runs a strategy through a backtest and records every open trade on
every bar, so a test can assert on stops, take-profits and sizing from the
inside. ``synthetic_ohlcv`` is deterministic price data to run it on.

The conformance test ``testing/test_risk_parameters.py`` in the quant-core
repository is built from these. A downstream package copies that one file and
points its ``STRATEGIES`` list at its own classes.
"""

from quant_core.testing.fixtures import BARS, SEED, synthetic_ohlcv
from quant_core.testing.probe import CASH, Observation, ProbeResult, probe

__all__ = ["BARS", "CASH", "SEED", "Observation", "ProbeResult", "probe", "synthetic_ohlcv"]
