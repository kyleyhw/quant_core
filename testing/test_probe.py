"""The probe measures short trades the same way as long ones."""

import pytest

from quant_core.strategies.base_strategy import BaseStrategy
from quant_core.testing import probe


class AlwaysShort(BaseStrategy):
    def on_bar(self) -> None:
        if not self.position:
            self._default_sell()


class AlwaysLong(BaseStrategy):
    def on_bar(self) -> None:
        if not self.position:
            self._default_buy()


@pytest.mark.parametrize("strategy_cls", [AlwaysLong, AlwaysShort], ids=["long", "short"])
def test_stop_distance_is_positive_on_either_side(strategy_cls, ohlcv):
    """
    A short's stop sits above the price. Measured as close - sl, it came out
    negative, and a strategy trading both sides averaged towards zero.
    """
    result = probe(strategy_cls, ohlcv)
    assert result.with_stop(), f"{strategy_cls.__name__} never held a stopped trade"
    assert all(o.stop_distance_pct > 0 for o in result.with_stop())

    target = strategy_cls.stop_loss_pct
    assert 0.5 * target <= result.mean_stop_distance_pct() <= 2.0 * target
