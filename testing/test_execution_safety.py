"""Order-level safety limits enforced by ExecutionManager.

These limits are per-order only. Account-level limits (daily loss, total
drawdown) are Phase 17 and are deliberately not covered here.
"""

import pytest

from quant_core.execution import ExecutionManager

PRICE = 150.0
SYMBOL = "AAPL"


@pytest.fixture
def manager() -> ExecutionManager:
    return ExecutionManager()


def order(**overrides) -> dict:
    base = {"action": "BUY", "quantity": 10, "order_type": "MKT", "symbol": SYMBOL}
    base.update(overrides)
    return base


def test_market_order_within_limits_passes(manager):
    assert manager.check_order_limits(order(), PRICE) is True


def test_limit_order_within_price_deviation_passes(manager):
    assert manager.check_order_limits(order(order_type="LMT", limit_price=155.0), PRICE) is True


def test_quantity_above_max_shares_is_blocked(manager):
    with pytest.raises(ValueError, match="exceeds limit of 100"):
        manager.check_order_limits(order(quantity=101), PRICE)


def test_quantity_at_max_shares_is_allowed(manager):
    # 100 shares would breach the dollar limit at $150, so price down to stay
    # inside it and isolate the share check.
    assert manager.check_order_limits(order(quantity=100), 40.0) is True


def test_notional_above_max_dollar_value_is_blocked(manager):
    # 50 shares at $150 is $7,500, past the $5,000 cap, while staying under
    # the 100-share cap so this test fails for one reason only.
    with pytest.raises(ValueError, match=r"exceeds limit of \$5000"):
        manager.check_order_limits(order(quantity=50), PRICE)


def test_limit_price_far_from_market_is_blocked(manager):
    with pytest.raises(ValueError, match="deviates"):
        manager.check_order_limits(order(quantity=1, order_type="LMT", limit_price=200.0), PRICE)


def test_market_order_ignores_price_deviation(manager):
    """A market order carries no limit price, so the deviation check must not fire."""
    assert manager.check_order_limits(order(quantity=1, limit_price=200.0), PRICE) is True
