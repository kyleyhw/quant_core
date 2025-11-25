import backtesting
from backtesting import Strategy
from backtesting.lib import crossover

class BuyAndHoldStrategy(Strategy):
    """
    Simple Buy and Hold Strategy.
    Buys on the first available bar and holds until the end.
    Used as a baseline for benchmarking.
    """
    
    def init(self):
        pass

    def next(self):
        # If we don't have a position, buy full size
        if not self.position:
            self.buy()
