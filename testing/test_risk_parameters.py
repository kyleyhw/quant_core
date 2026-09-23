"""Every strategy must honour the risk parameters it declares.

This is the test that would have caught the three Phase 11 bugs:

* `set_trailing_sl()` takes a multiple of ATR, so passing a percentage placed the
  stop roughly seventy times tighter than documented.
* `SimpleMACrossover` and `RSI2PeriodStrategy` overrode `next()` without calling
  up, so the trailing stop never ran for them at all.
* The take-profit branch was a bare `pass`.
"""

import pytest

from quant_core.strategies.base_strategy import BaseStrategy
from quant_core.strategies.bollinger_bands import BollingerBandsStrategy
from quant_core.strategies.rsi_2_period import RSI2PeriodStrategy
from quant_core.strategies.simple_ma_crossover import SimpleMACrossover
from testing.strategy_probe import CASH, probe

# BuyAndHoldStrategy is deliberately excluded: it extends Strategy directly and
# declares no risk parameters to honour.
STRATEGIES = [SimpleMACrossover, RSI2PeriodStrategy, BollingerBandsStrategy]
IDS = [s.__name__ for s in STRATEGIES]


# ----------------------------------------------------------------------
# The contract itself
# ----------------------------------------------------------------------
@pytest.mark.parametrize("strategy_cls", STRATEGIES, ids=IDS)
def test_strategy_does_not_define_next(strategy_cls):
    """Signal logic belongs in on_bar(); next() is owned by BaseStrategy."""
    assert "next" not in strategy_cls.__dict__
    assert "on_bar" in strategy_cls.__dict__


def test_defining_next_is_rejected_at_class_creation():
    with pytest.raises(TypeError, match="owns"):

        class Rogue(BaseStrategy):
            def next(self):  # pragma: no cover - the class never gets built
                pass


# ----------------------------------------------------------------------
# Trailing stop
# ----------------------------------------------------------------------
@pytest.mark.parametrize("strategy_cls", STRATEGIES, ids=IDS)
def test_trailing_stop_is_armed_on_open_trades(strategy_cls, ohlcv):
    result = probe(strategy_cls, ohlcv)
    assert result.observations, f"{strategy_cls.__name__} never opened a trade"
    assert result.with_stop(), (
        f"{strategy_cls.__name__} held open trades with no stop-loss. "
        "The trailing stop is not reaching this strategy."
    )


@pytest.mark.parametrize("strategy_cls", STRATEGIES, ids=IDS)
def test_trailing_stop_distance_is_a_percentage_not_an_atr_multiple(strategy_cls, ohlcv):
    """
    The stop should sit about `stop_loss_pct` below the running peak.

    `set_trailing_pct` converts the percentage into ATR units, so the realised
    distance drifts with volatility. The bound is loose on purpose: it tolerates
    that drift while still failing decisively on the unit mix-up, which lands two
    orders of magnitude away.
    """
    target = strategy_cls.stop_loss_pct
    mean_distance = probe(strategy_cls, ohlcv).mean_stop_distance_pct()
    assert 0.5 * target <= mean_distance <= 2.0 * target, (
        f"{strategy_cls.__name__} stops at {mean_distance:.4%} of price, "
        f"but declares stop_loss_pct={target:.2%}"
    )


@pytest.mark.parametrize("strategy_cls", STRATEGIES, ids=IDS)
def test_zero_stop_loss_disables_the_trailing_stop(strategy_cls, ohlcv):
    result = probe(strategy_cls, ohlcv, stop_loss_pct=0)
    assert result.observations, f"{strategy_cls.__name__} never opened a trade"
    assert not result.with_stop(), "stop_loss_pct=0 should leave trades unstopped"


# ----------------------------------------------------------------------
# Take profit
# ----------------------------------------------------------------------
@pytest.mark.parametrize("strategy_cls", STRATEGIES, ids=IDS)
def test_take_profit_is_armed_at_the_declared_distance(strategy_cls, ohlcv):
    target = strategy_cls.take_profit_pct
    observations = probe(strategy_cls, ohlcv).observations
    assert observations, f"{strategy_cls.__name__} never opened a trade"

    armed = [o for o in observations if o.tp is not None]
    assert armed, (
        f"{strategy_cls.__name__} held open trades with no take-profit, "
        f"despite declaring take_profit_pct={target:.2%}"
    )
    for o in armed:
        expected = o.entry * (1 + target) if o.size > 0 else o.entry * (1 - target)
        assert o.tp == pytest.approx(expected, rel=1e-9)


@pytest.mark.parametrize("strategy_cls", STRATEGIES, ids=IDS)
def test_zero_take_profit_disables_it(strategy_cls, ohlcv):
    result = probe(strategy_cls, ohlcv, take_profit_pct=0)
    assert result.observations, f"{strategy_cls.__name__} never opened a trade"
    assert all(o.tp is None for o in result.observations)


# ----------------------------------------------------------------------
# Position sizing
# ----------------------------------------------------------------------
@pytest.mark.parametrize("strategy_cls", STRATEGIES, ids=IDS)
def test_position_size_derives_from_risk_and_stop(strategy_cls, ohlcv):
    """A stop-out should cost about risk_percent of equity, so size = risk / stop."""
    expected = min(strategy_cls.risk_percent / strategy_cls.stop_loss_pct, 1.0)
    observations = probe(strategy_cls, ohlcv).observations
    assert observations, f"{strategy_cls.__name__} never opened a trade"

    first = observations[0]
    committed = abs(first.size) * first.entry
    assert committed / CASH == pytest.approx(expected, rel=0.05), (
        f"{strategy_cls.__name__} committed {committed / CASH:.1%} of equity, "
        f"expected about {expected:.1%} from risk_percent / stop_loss_pct"
    )


def test_sizing_fraction_is_capped_and_falls_back():
    class Sized(BaseStrategy):
        pass

    sized = Sized.__new__(Sized)
    sized.size_factor = 1.0

    # risk 1% against a 2% stop commits half the book
    sized.risk_percent, sized.stop_loss_pct = 0.01, 0.02
    assert sized.calculate_position_size() == pytest.approx(0.5)

    # never implies leverage
    sized.risk_percent, sized.stop_loss_pct = 0.10, 0.02
    assert sized.calculate_position_size() == 1.0

    # no stop means no risk-derived size, so fall back to fully invested
    sized.risk_percent, sized.stop_loss_pct = 0.01, 0.0
    assert sized.calculate_position_size() == 1.0


def test_order_quantity_matches_the_sizing_fraction():
    """The live path converts the same fraction into whole shares."""

    class Sized(BaseStrategy):
        pass

    sized = Sized.__new__(Sized)
    sized.size_factor = 1.0
    sized.risk_percent, sized.stop_loss_pct = 0.01, 0.02

    assert sized.calculate_order_quantity(price=100.0, equity=10_000) == 50
    assert sized.calculate_order_quantity(price=0.0, equity=10_000) == 0
    assert sized.calculate_order_quantity(price=100.0, equity=0.0) == 0
