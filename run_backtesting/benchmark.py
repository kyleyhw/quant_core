
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

try:
    from strategies.private.private_strategies.regime_based_strategy import MLRegimeStrategy
    from strategies.private.private_strategies.hmm_regime_strategy import HmmRegimeStrategy
    from strategies.private.private_strategies.pairs_trading_strategy import PairsTradingStrategy
    from strategies.private.private_strategies.meta_regime_filter_strategy import MetaRegimeFilterStrategy
    from strategies.private.private_strategies.dynamic_sizing_strategy import DynamicSizingStrategy
    PRIVATE_STRATEGIES_AVAILABLE = True
except ImportError:
    PRIVATE_STRATEGIES_AVAILABLE = False
    print("Warning: Private strategies not found. Running benchmark on public strategies only.")

# --- Strategy and Data Configuration ---
STANDALONE_STRATEGIES = [
    {"name": "Simple MA Crossover", "class": SimpleMACrossover, "data": "data/SPY_1hour_1year.csv", "scope": "public"},
    {"name": "RSI(2) Strategy", "class": RSI2PeriodStrategy, "data": "data/SPY_1hour_1year.csv", "scope": "public"},
    {"name": "Bollinger Bands", "class": BollingerBandsStrategy, "data": "data/SPY_1hour_1year.csv", "scope": "public"},
]

META_STRATEGIES = []

if PRIVATE_STRATEGIES_AVAILABLE:
    STANDALONE_STRATEGIES.extend([
        {"name": "ML Regime (XGBoost)", "class": MLRegimeStrategy, "data": "data/SPY_1hour_1year.csv", "scope": "private"},
        {"name": "HMM Regime", "class": HmmRegimeStrategy, "data": "data/SPY_1hour_1year.csv", "scope": "private"},
        {"name": "Pairs Trading (PEP/KO)", "class": PairsTradingStrategy, "data": "data/PEP_KO_daily_2010_2023_formatted.csv", "scope": "private"},
    ])
    META_STRATEGIES.extend([
        {
            "name": "Meta Filter (Trend)", 
            "class": MetaRegimeFilterStrategy, 
            "underlying": SimpleMACrossover,
            "underlying_name": "Simple MA Crossover",
            "params": {"strategy_type": "trend"},
            "data": "data/SPY_1hour_1year.csv",
            "scope": "private"
        },
        {
            "name": "Dynamic Sizing (Bollinger)", 
            "class": DynamicSizingStrategy, 
            "underlying": BollingerBandsStrategy,
            "underlying_name": "Bollinger Bands",
            "params": {},
            "data": "data/SPY_1hour_1year.csv",
            "scope": "private"
        },
    ])

def run_benchmark(scope: str):
    results = []
    
    # Filter strategies
    if scope == 'all':
        strategies_to_run = STANDALONE_STRATEGIES + META_STRATEGIES
    else:
        strategies_to_run = [s for s in STANDALONE_STRATEGIES if s['scope'] == scope]
        if scope == 'private':
            strategies_to_run += META_STRATEGIES

    for config in strategies_to_run:
        strategy_name = config["name"]
        strategy_class = config["class"]
        
        print(f"\n--- Benchmarking Strategy: {strategy_name} ---")
        
        # --- Load Data ---
        data = pd.read_csv(config["data"])
        data['date'] = pd.to_datetime(data['date'])
        data = data.set_index('date')
        
        if isinstance(data.index, pd.DatetimeIndex) and data.index.tz is not None:
            data.index = data.index.tz_localize(None)
        data.columns = [col.capitalize() for col in data.columns]
        
        # --- Handle Meta-Strategies ---
        if 'underlying' in config:
            strategy_class.underlying_strategy = config['underlying']
            for param, value in config['params'].items():
                setattr(strategy_class, param, value)

        bt = Backtest(data, strategy_class, cash=10000, commission=ibkr_tiered_commission)
        stats = bt.run()
        
        key_metrics = {
            "Strategy": strategy_name,
            "Return [%]": stats["Return [%]"], "Sharpe Ratio": stats["Sharpe Ratio"],
            "Max. Drawdown [%]": stats["Max. Drawdown [%]"], "Win Rate [%]": stats["Win Rate [%]"],
            "# Trades": stats["# Trades"]
        }
        results.append(key_metrics)
        print(f"--- Finished: {strategy_name} ---")

    if not results:
        print(f"No strategies found for scope '{scope}'. No report generated.")
        return
        
    print(f"\n--- Generating {scope.capitalize()} Benchmark Report ---")
    results_df = pd.DataFrame(results).sort_values(by="Sharpe Ratio", ascending=False)
    
    output_dir = 'reports' if scope == 'public' else os.path.join('strategies', 'private', 'reports')
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = os.path.join(output_dir, f"benchmark_report_{scope}_{timestamp}.md")
    
    with open(report_path, "w") as f:
        f.write(f"# {scope.capitalize()} Strategy Benchmark Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(results_df.to_markdown(index=False))
        
    print(f"Benchmark report saved to {report_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a benchmark of trading strategies.")
    parser.add_argument(
        '--scope', type=str, default='all', choices=['public', 'private', 'all'],
        help='The scope of strategies to benchmark.'
    )
    args = parser.parse_args()
    run_benchmark(scope=args.scope)

