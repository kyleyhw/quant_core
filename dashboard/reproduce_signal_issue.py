
import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# --- Mock Signal Strategy ---
class MockSignalStrategy(Strategy):
    def init(self):
        self.sma1 = self.I(lambda x: pd.Series(x).rolling(10).mean(), self.data.Close)
        self.sma2 = self.I(lambda x: pd.Series(x).rolling(20).mean(), self.data.Close)


    def next(self):
        print(f"Mock Next: SMA1={self.sma1[-1]}, SMA2={self.sma2[-1]}")
        if crossover(self.sma1, self.sma2):
            print("Mock Signal: BUY")
            return 'buy'
        elif crossover(self.sma2, self.sma1):
            print("Mock Signal: SELL")
            return 'sell'
        return None

# --- Signal Executor Logic (Dynamic Subclassing Approach) ---
def create_executable_strategy(base_strategy_class):
    class ExecutableStrategy(base_strategy_class):
        def next(self):
            # Call the underlying strategy's next method
            signal = super().next()
            
            # Debug print
            print(f"Wrapper Next: Signal={signal}")

            if signal == 'buy':
                if self.position.is_short:
                    self.position.close()
                if not self.position.is_long:
                    self.buy()
            elif signal == 'sell':
                if self.position.is_long:
                    self.position.close()
                if not self.position.is_short:
                    self.sell()
    
    # Copy name and docstring for clarity
    ExecutableStrategy.__name__ = f"Executable{base_strategy_class.__name__}"
    ExecutableStrategy.__doc__ = base_strategy_class.__doc__
    return ExecutableStrategy

# --- Test Setup ---
def run_test():
    # Create dummy data
    dates = pd.date_range(start='2023-01-01', periods=100)
    data = pd.DataFrame({
        'Open': [100] * 100,
        'High': [105] * 100,
        'Low': [95] * 100,

        'Close': [100 + i%20 - 10 + (i%3)*0.1 for i in range(100)], # Oscillating price with noise
        'Volume': [1000] * 100
    }, index=dates)
    
    # Ensure columns are capitalized
    data.columns = [c.capitalize() for c in data.columns]
    data.index.name = 'Date'

    print("Running Backtest with Dynamic Subclassing...")
    
    # Create the executable strategy class dynamically
    ExecutableMockStrategy = create_executable_strategy(MockSignalStrategy)
    
    bt = Backtest(data, ExecutableMockStrategy, cash=10000, commission=.002)
    stats = bt.run()
    
    print("\n--- Results ---")
    print(stats)
    print("\n--- Trades ---")
    print(stats['_trades'])

    if len(stats['_trades']) > 0:
        print("\nSUCCESS: Trades were executed.")
    else:
        print("\nFAILURE: No trades executed.")

if __name__ == "__main__":
    run_test()
