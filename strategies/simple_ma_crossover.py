import numpy as np
from backtesting.lib import crossover

from strategies.base_strategy import BaseStrategy

class SimpleMACrossover(BaseStrategy):
    """
    A simple moving average (SMA) crossover strategy.

    Why this exists:
    - To provide a clear, public example of a trading strategy built upon the BaseStrategy.
    - To demonstrate how to inherit from BaseStrategy and implement a custom entry signal.
    - To serve as a baseline for benchmarking against more complex strategies.

    Signal Logic:
    - Entry: A "fast" SMA crossing over a "slow" SMA.
    - Exit: Managed by the parent BaseStrategy (trailing stop-loss and take-profit).
    """

    # --- Strategy-Specific Parameters ---
    # These can be overridden during backtest optimization.
    fast_ma_period = 10  # Lookback period for the fast moving average
    slow_ma_period = 20  # Lookback period for the slow moving average

    def init(self):
        """
        Initializes the strategy. We no longer pre-calculate or access indicators here.
        """
        # Call the parent class's init to set up risk management
        super().init()

    def next(self):
        """
        The main strategy logic loop, called for each data point (bar).
        """
        # Ensure we have enough data for the longest SMA period
        if len(self.data.Close) < self.slow_ma_period:
            return

        # Calculate SMAs manually using numpy
        fast_ma_val = np.mean(self.data.Close[-self.fast_ma_period:])
        slow_ma_val = np.mean(self.data.Close[-self.slow_ma_period:])

        # Get previous SMA values for crossover detection
        # Ensure we have enough history for the previous bar's MAs
        if len(self.data.Close) < self.slow_ma_period + 1:
            return

        fast_ma_prev = np.mean(self.data.Close[-(self.fast_ma_period + 1):-1])
        slow_ma_prev = np.mean(self.data.Close[-(self.slow_ma_period + 1):-1])

        # Manual Crossover Logic
        cross_up = (fast_ma_prev <= slow_ma_prev and fast_ma_val > slow_ma_val)
        cross_down = (fast_ma_prev >= slow_ma_prev and fast_ma_val < slow_ma_val)

        # --- Entry Signal ---
        if cross_up:
            if not self.position:
                return "buy"
        
        # --- Exit Signal ---
        elif cross_down:
            if self.position:
                return "sell"

        return None

    def get_params(self) -> dict:
        """
        Returns a dictionary of the strategy's parameters, including inherited ones.
        """
        params = super().get_params()
        params.update({
            "fast_ma_period": self.fast_ma_period,
            "slow_ma_period": self.slow_ma_period,
        })
        return params
