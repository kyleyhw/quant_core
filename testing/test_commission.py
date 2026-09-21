"""Commission is applied once, by the engine, for both float and callable models.

Until the ``CustomBroker`` override was removed, a callable model was charged
twice and a float model raised ``TypeError: 'float' object is not callable``
mid-run. Three of the four entries in ``COMMISSION_MODELS`` are floats, so most
of the dashboard's options could not complete a backtest.
"""

import pytest
from backtesting import Backtest

from src.backtesting_extensions import CustomBacktest
from src.commission_models import COMMISSION_MODELS, ibkr_tiered_commission
from strategies.simple_ma_crossover import SimpleMACrossover

CASH = 10_000


def run(commission, data):
    return Backtest(
        data, SimpleMACrossover, cash=CASH, commission=commission, finalize_trades=True
    ).run()


@pytest.mark.parametrize("name", list(COMMISSION_MODELS), ids=list(COMMISSION_MODELS))
def test_every_registered_commission_model_completes_a_run(name, ohlcv):
    """Each model the dashboard offers must survive a full backtest."""
    stats = run(COMMISSION_MODELS[name], ohlcv)
    assert stats["# Trades"] > 0


def test_higher_commission_never_improves_return(ohlcv):
    returns = [run(rate, ohlcv)["Return [%]"] for rate in (0.0, 0.001, 0.005)]
    assert returns == sorted(returns, reverse=True)


def test_commission_is_charged_once_per_side(ohlcv):
    """
    Drag should match a single charge on entry and a single charge on exit.

    Double-charging, the old behaviour, lands at roughly twice this and fails the
    upper bound.
    """
    rate = 0.001
    free = run(0.0, ohlcv)
    charged = run(rate, ohlcv)

    trades = int(free["# Trades"])
    committed = SimpleMACrossover.risk_percent / SimpleMACrossover.stop_loss_pct
    # entry + exit, on the committed fraction of the book, expressed in points
    expected_drag = trades * 2 * rate * committed * 100
    actual_drag = free["Return [%]"] - charged["Return [%]"]

    assert 0.5 * expected_drag <= actual_drag <= 1.5 * expected_drag, (
        f"commission drag was {actual_drag:.3f} points against an expected "
        f"{expected_drag:.3f} for {trades} trades at {rate:.3%}"
    )


def test_deprecated_alias_matches_the_engine(ohlcv):
    """CustomBacktest is kept only for import compatibility and must add nothing."""
    direct = run(ibkr_tiered_commission, ohlcv)
    aliased = CustomBacktest(
        ohlcv,
        SimpleMACrossover,
        cash=CASH,
        commission=ibkr_tiered_commission,  # ty:ignore[invalid-argument-type]
        finalize_trades=True,
    ).run()
    assert aliased["Return [%]"] == pytest.approx(direct["Return [%]"], rel=1e-12)
    assert aliased["# Trades"] == direct["# Trades"]
