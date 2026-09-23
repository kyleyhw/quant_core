import math
from typing import Any

from backtesting.lib import TrailingStrategy

from quant_core.interfaces import IMarketAdapter


class BaseStrategy(TrailingStrategy):
    """
    A base class for trading strategies, designed for both backtesting and live
    trading. It provides a consistent framework for risk management and can
    operate with the backtesting.py engine or a live market via an IMarketAdapter.

    Why this exists:
    - To provide a single, consistent strategy definition for both simulation and
      live execution.
    - To abstract away the boilerplate logic of position sizing and stop-loss calculation.
    - To allow child strategies to focus purely on entry and exit signals,
      regardless of the execution environment.

    Subclasses implement `on_bar()`, never `next()`. `next()` is owned by this
    class: it applies take-profit, runs the subclass's signal logic, and then
    maintains the trailing stop. Overriding `next()` in a subclass raises at class
    definition time, because doing so silently disabled risk management for two of
    the three public strategies.
    """

    # --- Risk Management Parameters ---
    # risk_percent is the fraction of equity a single stop-out should cost.
    # stop_loss_pct is the trailing stop distance, as a fraction of price.
    # take_profit_pct is the profit target, as a fraction of the entry price.
    # Set stop_loss_pct or take_profit_pct to 0 to disable that leg.
    risk_percent: float = 0.01
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.05

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if "next" in cls.__dict__:
            raise TypeError(
                f"{cls.__name__} defines next(), which BaseStrategy owns. "
                "Put entry and exit logic in on_bar() instead. BaseStrategy.next() "
                "applies take-profit and maintains the trailing stop around it, so a "
                "subclass that overrides next() without calling up silently trades "
                "with no risk management."
            )

    def __init__(self, broker: Any, data: Any, params: dict) -> None:
        super().__init__(broker, data, params)
        self.market_adapter: IMarketAdapter | None = None
        self.entry_price = None
        self.size_factor = 1.0
        self._trailing_enabled = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def init(self, market_adapter: IMarketAdapter | None = None) -> None:
        """
        Initializes the strategy for either backtesting or live trading.

        Subclasses that need their own setup should override `on_init()`.
        """
        self.market_adapter = market_adapter
        # Only initialize backtesting-specific components if not live
        if not self.market_adapter:
            super().init()  # TrailingStrategy.init() computes the ATR series
            self._arm_trailing_stop()
        self.on_init()

    def on_init(self) -> None:
        """Hook for subclass setup. Called after risk management is armed."""

    def on_bar(self) -> None:
        """
        Hook for subclass signal logic, called once per bar.

        Implement entry and exit signals here. Risk management runs around this
        method, so there is no need to call up.
        """

    def next(self) -> None:
        """
        Owned by BaseStrategy; subclasses implement `on_bar()` instead.

        Order per bar: arm take-profit on any open trade, run the subclass's
        signal logic, then let TrailingStrategy ratchet the stop.
        """
        self._apply_take_profit()
        self.on_bar()
        if self._trailing_enabled:
            super().next()

    # ------------------------------------------------------------------
    # Risk management
    # ------------------------------------------------------------------
    def _arm_trailing_stop(self) -> None:
        """
        Arms the trailing stop at `stop_loss_pct` below the running peak.

        `TrailingStrategy.set_trailing_sl()` takes a multiple of ATR, not a
        percentage. Passing a percentage to it placed the stop roughly seventy
        times tighter than intended. `set_trailing_pct()` does the conversion.
        """
        pct = self.stop_loss_pct
        if pct and 0 < pct < 1:
            self.set_trailing_pct(pct)
            self._trailing_enabled = True
        else:
            self._trailing_enabled = False

    def _apply_take_profit(self) -> None:
        """Attaches a take-profit order to any open trade that lacks one."""
        pct = self.take_profit_pct
        if not pct or pct <= 0:
            return
        for trade in self.trades:
            if trade.tp is not None:
                continue
            entry = trade.entry_price
            if not entry or entry <= 0:
                continue
            trade.tp = entry * (1 + pct) if trade.is_long else entry * (1 - pct)

    # ------------------------------------------------------------------
    # Position sizing
    # ------------------------------------------------------------------
    def calculate_position_size(self) -> float:
        """
        Fraction of equity to commit, so that being stopped out costs about
        `risk_percent` of equity.

        With a 1% risk budget and a 2% stop, half of equity is committed: a 2%
        adverse move on half the account is a 1% account loss. The fraction is
        capped at 1.0, so the strategy never implies leverage.

        Backtest and live execution both size from this method, so a backtest
        cannot quietly trade a different book to the live runner.
        """
        if self.stop_loss_pct and self.stop_loss_pct > 0:
            fraction = self.risk_percent / self.stop_loss_pct
        else:
            fraction = 1.0
        return float(min(max(fraction, 0.0), 1.0))

    def calculate_order_quantity(self, price: float, equity: float) -> int:
        """
        Whole units to order at `price` given `equity`, using the same fraction
        as `calculate_position_size()`.

        Used by the live path, where an order is a share count rather than a
        fraction of cash.
        """
        if price <= 0 or equity <= 0:
            return 0
        notional = equity * self.calculate_position_size() * self.size_factor
        return max(int(math.floor(notional / price)), 0)

    def _default_buy(self) -> None:
        """
        Backtest helper that sizes from `calculate_position_size()` and honors
        `self.size_factor`.

        Note: backtesting.py reads `size >= 1` as a discrete number of units, not
        a multiplier, so a fraction of 1.0 or more is sent as an unsized order,
        which commits all available cash.
        """
        size = self.calculate_position_size() * self.size_factor
        if size >= 1.0:
            self.buy()
        else:
            self.buy(size=max(size, 1e-3))
        self.entry_price = self.data.Close[-1]

    def _default_sell(self) -> None:
        """Short counterpart to `_default_buy()`."""
        size = self.calculate_position_size() * self.size_factor
        if size >= 1.0:
            self.sell()
        else:
            self.sell(size=max(size, 1e-3))
        self.entry_price = self.data.Close[-1]

    def get_params(self) -> dict:
        """Returns a dictionary of the base strategy's parameters."""
        return {
            "risk_percent": self.risk_percent,
            "stop_loss_pct": self.stop_loss_pct,
            "take_profit_pct": self.take_profit_pct,
        }

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    def buy_instrument(self, symbol: str, quantity: float | None = None) -> None:
        """
        Executes a long entry. Delegates to the market adapter if live,
        otherwise uses the backtesting engine.

        `quantity` is required live. Leave it unset in a backtest to size from
        `calculate_position_size()`.
        """
        if self.market_adapter and self.market_adapter.execution_handler:
            if quantity is None:
                raise ValueError("quantity is required when trading through a market adapter")
            order_details = {
                "symbol": symbol,
                "quantity": quantity,
                "action": "BUY",
                "order_type": "MKT",
            }
            self.market_adapter.execution_handler.place_order(order_details)
        else:
            self._default_buy()

    def sell_instrument(self, symbol: str, quantity: float | None = None) -> None:
        """
        Executes a short entry. Delegates to the market adapter if live,
        otherwise uses the backtesting engine.
        """
        if self.market_adapter and self.market_adapter.execution_handler:
            if quantity is None:
                raise ValueError("quantity is required when trading through a market adapter")
            order_details = {
                "symbol": symbol,
                "quantity": quantity,
                "action": "SELL",
                "order_type": "MKT",
            }
            self.market_adapter.execution_handler.place_order(order_details)
        else:
            self._default_sell()
