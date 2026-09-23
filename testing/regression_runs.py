"""The fixed set of backtests whose metrics are pinned.

Both the baseline generator and the regression test import from here, so there is
one definition of what "the same run" means.
"""

import math
from typing import Any

from backtesting import Backtest, Strategy

from quant_core.commission_models import COMMISSION_MODELS
from quant_core.strategies.bollinger_bands import BollingerBandsStrategy
from quant_core.strategies.buy_and_hold import BuyAndHoldStrategy
from quant_core.strategies.rsi_2_period import RSI2PeriodStrategy
from quant_core.strategies.simple_ma_crossover import SimpleMACrossover

CASH = 10_000

PINNED_METRICS = [
    "Return [%]",
    "Equity Final [$]",
    "Sharpe Ratio",
    "Max. Drawdown [%]",
    "Win Rate [%]",
    "Profit Factor",
    "Exposure Time [%]",
    "# Trades",
]

# Both commission branches are covered: a float rate and a callable model. The
# float cases would not even complete a run before CustomBroker was removed.
RUNS: dict[str, tuple[type[Strategy], Any]] = {
    "SimpleMACrossover/zero": (SimpleMACrossover, 0.0),
    "RSI2PeriodStrategy/zero": (RSI2PeriodStrategy, 0.0),
    "BollingerBandsStrategy/zero": (BollingerBandsStrategy, 0.0),
    "BuyAndHoldStrategy/zero": (BuyAndHoldStrategy, 0.0),
    "SimpleMACrossover/fixed-10bps": (SimpleMACrossover, 0.001),
    "SimpleMACrossover/ibkr-tiered": (SimpleMACrossover, COMMISSION_MODELS["IBKR Tiered"]),
}


def run_one(strategy_cls: type[Strategy], commission: Any, data: Any) -> dict[str, float | None]:
    """Runs one pinned backtest and returns its metrics, rounded for stable JSON."""
    stats = Backtest(
        data,
        strategy_cls,
        cash=CASH,
        commission=commission,
        finalize_trades=True,
    ).run()

    out: dict[str, float | None] = {}
    for key in PINNED_METRICS:
        value = stats[key]
        value = float(value)
        out[key] = None if math.isnan(value) else round(value, 6)
    return out
