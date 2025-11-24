import pandas as pd
from backtesting import Backtest
import os
import sys
import argparse
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
    from strategies.private.private_strategies.regime_based_strategy import MLRegimeStrategy
    from strategies.private.private_strategies.hmm_regime_strategy import HmmRegimeStrategy
    from strategies.private.private_strategies.pairs_trading_strategy import PairsTradingStrategy
    PRIVATE_STRATEGIES_AVAILABLE = True
except ImportError:
    PRIVATE_STRATEGIES_AVAILABLE = False

# --- Strategy and Data Configuration ---
ALL_STRATEGIES = [
    {
        "name": "Simple MA Crossover",
        "class": SimpleMACrossover,
        "data": "data/SPY_1hour_1year.csv",
        "scope": "public"
    },
    {
        "name": "RSI(2) Strategy",
        "class": RSI2PeriodStrategy,
        "data": "data/SPY_1hour_1year.csv",
        "scope": "public"
    },
    {
        "name": "Bollinger Bands",
        "class": BollingerBandsStrategy,
        "data": "data/SPY_1hour_1year.csv",
        "scope": "public"
    },
]

if PRIVATE_STRATEGIES_AVAILABLE:
    ALL_STRATEGIES.extend([
        {
            "name": "ML Regime (XGBoost)",
            "class": MLRegimeStrategy,
            "data": "data/SPY_1hour_1year.csv",
            "scope": "private"
        },
        {
            "name": "HMM Regime",
            "class": HmmRegimeStrategy,
            "data": "data/SPY_1hour_1year.csv",
            "scope": "private"
        },
        {
            "name": "Pairs Trading (PEP/KO)",
            "class": PairsTradingStrategy,
            "data": "data/PEP_KO_daily_2010_2023.csv",
            "scope": "private"
        }
    ])

def run_benchmark(scope: str):
    """
    Main function to run the benchmark for a given scope.
    """
    results = []
    
    # Filter strategies based on scope
    if scope == 'all':
        strategies_to_run = ALL_STRATEGIES
    else:
        strategies_to_run = [s for s in ALL_STRATEGIES if s['scope'] == scope]

    for config in strategies_to_run:
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
        else: # Handle pairs data case
            first_col_name = data.columns[0]
            data.rename(columns={first_col_name: 'date'}, inplace=True)
            data['date'] = pd.to_datetime(data['date'], utc=True)
            data = data.set_index('date')

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
    if not results:
        print(f"No strategies found for scope '{scope}'. No report generated.")
        return
        
    print(f"\n--- Generating {scope.capitalize()} Benchmark Report ---")
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values(by="Sharpe Ratio", ascending=False)
    
    # Determine output directory based on scope
    if scope == 'public':
        output_dir = 'reports'
    else:
        output_dir = os.path.join('strategies', 'private', 'reports')
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = os.path.join(output_dir, f"benchmark_report_{scope}_{timestamp}.md")
    
    with open(report_path, "w") as f:
        f.write(f"# {scope.capitalize()} Strategy Benchmark Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("This report compares the performance of implemented trading strategies using the IBKR Tiered commission model.\n\n")
        f.write("## Performance Summary\n\n")
        f.write(results_df.to_markdown(index=False))
        
    print(f"Benchmark report saved to {report_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a benchmark of trading strategies.")
    parser.add_argument(
        '--scope',
        type=str,
        default='all',
        choices=['public', 'private', 'all'],
        help='The scope of strategies to benchmark.'
    )
    args = parser.parse_args()
    run_benchmark(scope=args.scope)
