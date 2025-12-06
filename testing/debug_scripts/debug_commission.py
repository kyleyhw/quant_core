from backtesting import Backtest, Strategy
import pandas as pd
import numpy as np
from typing import Any

class DummyStrategy(Strategy):
    def init(self) -> None:
        pass
    def next(self) -> None:
        self.buy()

def dummy_commission(broker: Any, trade: Any, price: float) -> float:
    return 1.0

# Create dummy data
data = pd.DataFrame({
    'Open': np.random.rand(100) + 100,
    'High': np.random.rand(100) + 105,
    'Low': np.random.rand(100) + 95,
    'Close': np.random.rand(100) + 100,
    'Volume': np.random.randint(100, 1000, 100)
}, index=pd.date_range('2024-01-01', periods=100))

try:
    bt = Backtest(data, DummyStrategy, commission=dummy_commission)
    print("Backtest instantiated successfully with callable commission.")
    bt.run()
    print("Backtest ran successfully.")
except Exception as e:
    print(f"Failed: {e}")
