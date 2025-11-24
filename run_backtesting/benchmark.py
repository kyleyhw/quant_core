"""
This script runs a benchmark comparison of all available trading strategies.

It iterates through a defined list of strategies, runs a backtest for each
on its designated dataset, and compiles the key performance metrics into a
single markdown report. The final report ranks the strategies by their
Sharpe Ratio to provide a clear, comparative overview of their performance.
"""

import pandas as pd
from backtesting import Backtest
import os
import sys
from datetime import datetime

# --- Add project root to path ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Import all strategies ---
from strategies.simple_ma_crossover import SimpleMACrossover
from strategies.rsi_2_period import RSI2PeriodStrategy
from strategies.bollinger_bands import BollingerBandsStrategy
from src.commission_models import ibkr_tiered_commission

# Attempt to import private strategies
try:
    from strategies.private.regime_based_strategy import MLRegimeStrategy
    from strategies.private.hmm_regime_strategy import HmmRegimeStrategy
    from strategies.private.pairs_trading_strategy import PairsTradingStrategy
    PRIVATE_STRATEGIES_AVAILABLE = True
except ImportError:
    PRIVATE_STRATEGIES_AVAILABLE = False
    print("Warning: Private strategies not found. Running benchmark on public strategies only.")

# --- Strategy and Data Configuration ---
STRATEGIES_TO_BENCHMARK = [
    {
        "name": "Simple MA Crossover",
        "class": SimpleMACrossover,
        "data": "data/SPY_1hour_1year.csv"
    },
    {
        "name": "RSI(2) Strategy",
        "class": RSI2PeriodStrategy,
        "data": "data/SPY_1hour_1year.csv"
    },
    {
        "name": "Bollinger Bands",
        "class": BollingerBandsStrategy,
        "data": "data/SPY_1hour_1year.csv"
    },
]

if PRIVATE_STRATEGIES_AVAILABLE:
    STRATEGIES_TO_BENCHMARK.extend([
        {
            "name": "ML Regime (XGBoost)",
            "class": MLRegimeStrategy,
            "data": "data/SPY_1hour_1year.csv"
        },
        {
            "name": "HMM Regime",
            "class": HmmRegimeStrategy,
            "data": "data/SPY_1hour_1year.csv"
        },
        {
            "name": "Pairs Trading (PEP/KO)",
            "class": PairsTradingStrategy,
            "data": "data/PEP_KO_daily_2010_2023.csv"
        }
    ])

def run_benchmark():
    """
    Main function to run the benchmark.
    """
    results = []
    
    for config in STRATEGIES_TO_BENCHMARK:
        strategy_name = config["name"]
        strategy_class = config["class"]
        data_path = config["data"]
        
        print(f"\n--- Benchmarking Strategy: {strategy_name} ---")
        
        # --- Load Data ---
        print(f"Loading data from {data_path}...")
        data = pd.read_csv(data_path)
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'], utc=True)
            data = data.set_index('date')
        else:
            first_col_name = data.columns[0]
            data[first_col_name] = pd.to_datetime(data[first_col_name], utc=True)
            data = data.set_index(first_col_name)
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
        data.columns = [col.capitalize() for col in data.columns]
        
        # --- Run Backtest ---
        bt = Backtest(
            data,
            strategy_class,
            cash=10000,
            commission=ibkr_tiered_commission
        )
        stats = bt.run()
        
        # --- Store Results ---
        # Select and rename key metrics for the report
        key_metrics = {
            "Strategy": strategy_name,
            "Return [%]": stats["Return [%]"],
            "Sharpe Ratio": stats["Sharpe Ratio"],
            "Max. Drawdown [%]": stats["Max. Drawdown [%]"],
            "Win Rate [%]": stats["Win Rate [%]"],
            "# Trades": stats["# Trades"]
        }
        results.append(key_metrics)
        print(f"--- Finished: {strategy_name} ---")

    # --- Generate Report ---
    print("\n--- Generating Benchmark Report ---")
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values(by="Sharpe Ratio", ascending=False)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = f"reports/benchmark_report_{timestamp}.md"
    
    with open(report_path, "w") as f:
        f.write("# Strategy Benchmark Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("This report compares the performance of all implemented trading strategies using the IBKR Tiered commission model.\n\n")
        f.write("## Performance Summary\n\n")
        f.write(results_df.to_markdown(index=False))
        
    print(f"Benchmark report saved to {report_path}")

if __name__ == "__main__":
    run_benchmark()
