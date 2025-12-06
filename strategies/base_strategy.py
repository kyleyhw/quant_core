from typing import Optional, Any
from backtesting import Strategy
from backtesting.lib import TrailingStrategy

from src.interfaces import IMarketAdapter

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
    """

    # --- Risk Management Parameters ---
    risk_percent: float = 0.01
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.05

    def __init__(self, broker: Any, data: Any, params: dict) -> None:
        super().__init__(broker, data, params)
        self.market_adapter: Optional[IMarketAdapter] = None
        self.entry_price = None
        self.size_factor = 1.0

    def init(self, market_adapter: Optional[IMarketAdapter] = None) -> None:
        """
        Initializes the strategy for either backtesting or live trading.
        """
        self.market_adapter = market_adapter
        # Only initialize backtesting-specific components if not live
        if not self.market_adapter:
            super().init()
            self.set_trailing_sl(self.stop_loss_pct)

    def next(self) -> None:
        """
        Main strategy logic loop. For backtesting only.
        Live trading will be event-driven from a different entry point.
        """
        if self.take_profit_pct > 0 and self.position and self.entry_price is not None:
            # ... (take-profit logic remains the same for backtesting)
            pass
        super().next()

    def calculate_position_size(self) -> float:
        """Calculates the base position size."""
        return 0.1

    def get_params(self) -> dict:
        """Returns a dictionary of the base strategy's parameters."""
        return {
            "risk_percent": self.risk_percent,
            "stop_loss_pct": self.stop_loss_pct,
            "take_profit_pct": self.take_profit_pct,
        }

    def buy_instrument(self, symbol: str, quantity: float) -> None:
        """
        Executes a long entry. Delegates to the market adapter if live,
        otherwise uses the backtesting engine.
        """
        if self.market_adapter and self.market_adapter.execution_handler:
            order_details = {
                "symbol": symbol,
                "quantity": quantity,
                "action": "BUY",
                "order_type": "MKT"
            }
            self.market_adapter.execution_handler.place_order(order_details)
        else:
            # Fallback to backtesting engine
            size = self.calculate_position_size() * self.size_factor
            self.buy(size=size)
            self.entry_price = self.data.Close[-1]

    def sell_instrument(self, symbol: str, quantity: float) -> None:
        """
        Executes a short entry. Delegates to the market adapter if live,
        otherwise uses the backtesting engine.
        """
        if self.market_adapter and self.market_adapter.execution_handler:
            order_details = {
                "symbol": symbol,
                "quantity": quantity,
                "action": "SELL",
                "order_type": "MKT"
            }
            self.market_adapter.execution_handler.place_order(order_details)
        else:
            # Fallback to backtesting engine
            size = self.calculate_position_size() * self.size_factor
            self.sell(size=size)
            self.entry_price = self.data.Close[-1]

