import numpy as np
from typing import Optional, Any

from strategies.base_strategy import BaseStrategy

class RSI2PeriodStrategy(BaseStrategy):
    """
    An RSI (Relative Strength Index) 2-period strategy.

    Why this exists:
    - To provide an additional public example of a trading strategy built upon the BaseStrategy.
    - To demonstrate strategy logic based on overbought/oversold conditions using RSI.
    - To test the flexibility of the framework with a different type of indicator.

    Signal Logic:
    - Entry: When the 2-period RSI crosses below an oversold threshold.
    - Exit: When the 2-period RSI crosses above an overbought threshold.
    """

    # --- Strategy-Specific Parameters ---
    rsi_period = 2
    oversold_threshold = 10
    overbought_threshold = 90

    def init(self, **kwargs: Any) -> None:
        super().init(**kwargs)

    def next(self) -> None:
        # Ensure we have enough data for RSI calculation
        # RSI(2) needs at least 2 periods for initial calculation, plus one more for previous value
        if len(self.data.Close) <= self.rsi_period:
            return

        # Manual RSI calculation (simplified for 2-period)
        # Price changes
        delta = self.data.Close[-self.rsi_period:] - self.data.Close[-(self.rsi_period + 1):-1]
        
        # Gains and Losses
        gains = delta * (delta > 0)
        losses = -delta * (delta < 0)

        # Average Gains and Losses (simple average for 2 periods)
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)

        if avg_loss == 0:
            rs = 100 # Avoid division by zero, strong upward momentum
        else:
            rs = avg_gain / avg_loss

        rsi_val = 100 - (100 / (1 + rs))

        # Get previous RSI value for crossover detection
        # This requires re-calculating RSI for the previous bar
        if len(self.data.Close) <= self.rsi_period + 1: # Need 3 bars for current and previous RSI(2)
            return

        delta_prev = self.data.Close[-(self.rsi_period + 1):-1] - self.data.Close[-(self.rsi_period + 2):-2]
        gains_prev = delta_prev * (delta_prev > 0)
        losses_prev = -delta_prev * (delta_prev < 0)
        avg_gain_prev = np.mean(gains_prev)
        avg_loss_prev = np.mean(losses_prev)

        if avg_loss_prev == 0:
            rs_prev = 100
        else:
            rs_prev = avg_gain_prev / avg_loss_prev
        rsi_prev = 100 - (100 / (1 + rs_prev))

        # Manual Crossover Logic for entry/exit
        cross_below_oversold = (rsi_prev >= self.oversold_threshold and rsi_val < self.oversold_threshold)
        cross_above_overbought = (rsi_prev <= self.overbought_threshold and rsi_val > self.overbought_threshold)

        # --- Entry Signal (Buy when RSI crosses below oversold) ---
        if cross_below_oversold:
            if not self.position:
                self.buy()
        
        # --- Exit Signal (Sell when RSI crosses above overbought) ---
        elif cross_above_overbought:
            if self.position:
                self.position.close()


    def get_params(self) -> dict:
        """
        Returns a dictionary of the strategy's parameters, including inherited ones.
        """
        params = super().get_params()
        params.update({
            "rsi_period": self.rsi_period,
            "oversold_threshold": self.oversold_threshold,
            "overbought_threshold": self.overbought_threshold,
        })
        return params