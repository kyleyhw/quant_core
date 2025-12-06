import sys
import os
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, os.getcwd())

from src.backtesting_extensions import CustomBacktest
from backtesting import Strategy

# Mock commission
def ibkr_tiered_commission(quantity: float, price: float) -> float:
    return 1.0

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
    print("Instantiating CustomBacktest...")
    bt = CustomBacktest(data, DummyStrategy, commission=ibkr_tiered_commission)
    print("Running backtest...")
    stats = bt.run()
    print("Backtest ran successfully.")
    print(f"Number of trades: {stats['# Trades']}")
except Exception as e:
    print(f"Failed: {e}")
    import traceback
    traceback.print_exc()
