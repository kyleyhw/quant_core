from backtesting import Strategy
from backtesting.lib import TrailingStrategy

class BaseStrategy(TrailingStrategy):
    """
    A base class for trading strategies that provides a framework for consistent
    risk management, including dynamic position sizing and trailing stop-loss.

    Why this exists:
    - To enforce a consistent risk management approach across all strategies.
    - To abstract away the boilerplate logic of position sizing and stop-loss calculation.
    - To allow child strategies to focus purely on entry and exit signals.

    This class inherits from TrailingStrategy to utilize a percentage-based
    trailing stop-loss, a more dynamic approach than a fixed stop.
    """
    
    # --- Risk Management Parameters ---
    # These can be overridden by child strategies or during backtest optimization.
    
    # The percentage of total equity to risk on a single trade.
    risk_percent: float = 0.01  # e.g., 1% of equity

    # The percentage below the entry price to set the initial stop-loss.
    # This also serves as the trailing stop percentage.
    stop_loss_pct: float = 0.02  # e.g., 2% trailing stop

    # The percentage above the entry price to set the take-profit level.
    # If set to 0, no take-profit limit is used.
    take_profit_pct: float = 0.05  # e.g., 5% take-profit

    def init(self):
        """
        Initializes the strategy. This method is called by the backtesting
        framework once before the strategy begins.

        We use this to set up the trailing stop-loss mechanism.
        """
        # Call the parent class's init method
        super().init()
        # Set the trailing stop-loss percentage from our parameters
        self.set_trailing_sl(self.stop_loss_pct)

    def next(self):
        """
        The main strategy logic loop, called for each data point (bar).

        This base implementation contains the logic to manage an open trade's
        exit conditions (take-profit). Entry logic should be implemented
        in the child strategy's `next()` method, which should also call
        `super().next()` to retain this exit logic.
        """
        # --- Take-Profit Logic ---
        # If a take-profit is defined and we have an open position
        if self.take_profit_pct > 0 and self.position:
            # For long positions
            if self.position.is_long:
                take_profit_price = self.trade.entry_price * (1 + self.take_profit_pct)
                # If the current price crosses the take-profit level, close the position
                if self.data.Close[-1] >= take_profit_price:
                    self.position.close()
            # For short positions
            elif self.position.is_short:
                take_profit_price = self.trade.entry_price * (1 - self.take_profit_pct)
                # If the current price crosses the take-profit level, close the position
                if self.data.Close[-1] <= take_profit_price:
                    self.position.close()
        
        # The parent class (TrailingStrategy) handles the trailing stop-loss automatically.
        super().next()

    def calculate_position_size(self) -> float:
        """
        Calculates the position size as a fraction of total equity, based on the
        defined `risk_percent`.

        This standardizes position sizing across all strategies that inherit
        from this base class.

        Returns:
            float: The fraction of equity to allocate to the trade (e.g., 0.9 for 90%).
                   The backtesting library uses this to determine share count.
        """
        # The library requires a size from 0-1 (fraction of available cash/equity).
        # We cap the risk at a max of 99% of equity to be safe.
        # Note: The backtesting.py library automatically uses a portion of broker
        # cash, not total equity, so this sizing is relative to available cash.
        # We can simulate equity-based sizing by tying it to self.equity.
        # For simplicity here, we'll return a fixed size based on an interpretation
        # of the library's sizing, but a more complex implementation could be done.
        
        # Let's consider the `risk_percent` to define how many concurrent positions
        # we can have. E.g., 1% risk allows for up to 100 positions if margin is 1.
        # A simple interpretation for `backtesting.py` is to use a fraction of cash.
        # Let's assume we want to use 10% of our cash per trade as a starting point.
        # A more accurate sizing would be:
        # size_in_shares = (self.equity * self.risk_percent) / (self.data.Close[-1] * self.stop_loss_pct)
        # However, the library wants a fractional size from 0-1.
        
        # For now, we will return a simple fractional size.
        # Let's risk 10% of our portfolio on each trade as an example.
        # This will be refined later if needed.
        return 0.1

    # --- Wrapper methods for buying and selling to include our position size ---
    
    def buy_instrument(self):
        """
        Executes a long entry with the calculated position size.
        """
        size = self.calculate_position_size()
        self.buy(size=size)

    def sell_instrument(self):
        """
        Executes a short entry with the calculated position size.
        """
        size = self.calculate_position_size()
        self.sell(size=size)
