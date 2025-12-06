from backtesting import Backtest, Strategy
from backtesting.backtesting import _Broker
import pandas as pd
import numpy as np
from math import copysign
from typing import Any, Optional, Type

# Mock the tiered commission function
def ibkr_tiered_commission(quantity: float, price: float) -> float:
    # Simple mock: $1 per trade
    return 1.0

class CustomBroker(_Broker):
    def __init__(self, **kwargs: Any) -> None:
        commission = kwargs.pop('commission', 0.0)
        # Pass 0.0 to super to bypass validation
        super().__init__(commission=0.0, **kwargs)
        # Set the real commission
        self._commission = commission

    def _adjusted_price(self, size: Optional[float] = None, price: Optional[float] = None) -> float:
        price = price or self.last_price
        commission = self._commission
        
        if callable(commission):
            comm_amount = commission(size, price)
            # Adjust price to include commission
            # For buy (size > 0): price + (comm / size)
            # For sell (size < 0): price + (comm / size) -> price - (comm / abs(size))
            return price + (comm_amount / size)
            
        return super()._adjusted_price(size, price)

class CustomBacktest(Backtest):
    def __init__(self, data: pd.DataFrame, strategy: Type[Strategy], **kwargs: Any) -> None:
        # Bypass validation by passing 0.0 commission initially
        commission = kwargs.pop('commission', 0.0)
        super().__init__(data, strategy, commission=0.0, **kwargs)
        
        # Now inject our custom broker with the real commission
        from functools import partial
        self._broker = partial(
            CustomBroker, cash=kwargs.get('cash', 10000), 
            commission=commission, 
            margin=kwargs.get('margin', 1.0),
            trade_on_close=kwargs.get('trade_on_close', False), 
            hedging=kwargs.get('hedging', False),
            exclusive_orders=kwargs.get('exclusive_orders', False), 
            index=data.index,
        )

class DummyStrategy(Strategy):
    def init(self) -> None:
        pass
    def next(self) -> None:
        if not self.position:
            self.buy()
        elif len(self.data) == len(self.data.df) - 1:
            self.position.close()

# Create dummy data
data = pd.DataFrame({
    'Open': np.random.rand(100) + 100,
    'High': np.random.rand(100) + 105,
    'Low': np.random.rand(100) + 95,
    'Close': np.random.rand(100) + 100,
    'Volume': np.random.randint(100, 1000, 100)
}, index=pd.date_range('2024-01-01', periods=100))

try:
    bt = CustomBacktest(data, DummyStrategy, commission=ibkr_tiered_commission)
    print("CustomBacktest instantiated.")
    stats = bt.run()
    print("Backtest ran successfully.")
    print(f"Number of trades: {stats['# Trades']}")
except Exception as e:
    print(f"Failed: {e}")
    import traceback
    traceback.print_exc()
