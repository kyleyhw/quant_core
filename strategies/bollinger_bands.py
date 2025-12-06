import numpy as np
from typing import Any

from strategies.base_strategy import BaseStrategy

class BollingerBandsStrategy(BaseStrategy):
    """
    A Bollinger Bands strategy.

    Why this exists:
    - To provide an additional public example of a trading strategy built upon the BaseStrategy.
    - To demonstrate strategy logic based on volatility bands around a moving average.
    - To test the flexibility of the framework with a multi-component indicator.

    Signal Logic:
    - Entry: When price crosses below the Lower Bollinger Band.
    - Exit: When price crosses above the Middle Bollinger Band.
    """

    # --- Strategy-Specific Parameters ---
    bb_period = 20        # Period for the Moving Average and Standard Deviation
    bb_std_dev = 2.0      # Number of standard deviations for the bands

    def init(self, **kwargs: Any) -> None:
        super().init(**kwargs)

    def next(self) -> None:
        # Ensure we have enough data for Bollinger Bands calculation
        if len(self.data.Close) < self.bb_period:
            return

        # Calculate Middle Band (SMA)
        middle_band = np.mean(self.data.Close[-self.bb_period:])

        # Calculate Standard Deviation
        std_dev = np.std(self.data.Close[-self.bb_period:])

        # Calculate Upper and Lower Bands
        upper_band = middle_band + (std_dev * self.bb_std_dev)
        lower_band = middle_band - (std_dev * self.bb_std_dev)

        # Get previous values for crossover detection
        if len(self.data.Close) < self.bb_period + 1:
            return

        # Previous Middle Band
        middle_band_prev = np.mean(self.data.Close[-(self.bb_period + 1):-1])
        
        # Previous Lower Band
        lower_band_prev = middle_band_prev - (np.std(self.data.Close[-(self.bb_period + 1):-1]) * self.bb_std_dev)

        # Manual Crossover Logic
        cross_below_lower = (self.data.Close[-2] >= lower_band_prev and self.data.Close[-1] < lower_band)
        cross_above_middle = (self.data.Close[-2] <= middle_band_prev and self.data.Close[-1] > middle_band)

        # --- Entry Signal (Buy when price crosses below Lower Band) ---
        if cross_below_lower:
            if not self.position:
                self.buy()
        
        # --- Exit Signal (Sell when price crosses above Middle Band) ---
        elif cross_above_middle:
            if self.position:
                self.position.close()

        super().next()

    def get_params(self) -> dict:
        """
        Returns a dictionary of the strategy's parameters, including inherited ones.
        """
        params = super().get_params()
        params.update({
            "bb_period": self.bb_period,
            "bb_std_dev": self.bb_std_dev,
        })
        return params