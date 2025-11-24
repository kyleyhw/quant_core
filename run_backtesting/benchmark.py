import pandas as pd
from backtesting import Backtest, Strategy
import os
import sys
import argparse
import importlib
import inspect
from datetime import datetime
from pathlib import Path

# --- Add project root to path ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.commission_models import ibkr_tiered_commission
from strategies.base_strategy import BaseStrategy

# --- Configuration for data and meta-strategies ---
# This allows us to map specific data files to strategies by name
# and define which meta-strategies should run with which underlying strategies.
STRATEGY_CONFIG = {
    "PairsTradingStrategy": {"data": "data/PEP_KO_daily_2010_2023_formatted.csv"},
    "MetaRegimeFilterStrategy": {
        "underlying": "SimpleMACrossover",
        "params": {"strategy_type": "trend"}
    },
    "DynamicSizingStrategy": {
        "underlying": "BollingerBandsStrategy",
        "params": {}
    }
}
DEFAULT_DATA = "data/SPY_1hour_1year.csv"


def discover_strategies():
    """Dynamically discovers and imports strategies from the project directories."""
    strategies = {"standalone": [], "meta": {}}
    
    # Define search paths for public and private strategies
    public_path = Path(project_root) / 'strategies'
    private_path = public_path / 'private' / 'private_strategies'
    search_paths = [public_path]
    
    private_strategies_available = private_path.exists() and any(private_path.iterdir())
    if private_strategies_available:
        search_paths.append(private_path)
    else:
        print("Warning: Private strategies not found. Running benchmark on public strategies only.")

    for path in search_paths:
        for file in path.glob('*.py'):
            if file.name.startswith(('__init__', 'base_')):
                continue

            module_name = f"{path.relative_to(Path(project_root)).as_posix().replace('/', '.')}.{file.stem}"
            
            try:
                module = importlib.import_module(module_name)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Check if it's a valid, non-base strategy class
                    if issubclass(obj, (Strategy, BaseStrategy)) and obj not in (Strategy, BaseStrategy):
                        scope = "private" if "private_strategies" in module_name else "public"
                        
                        # Check if it's a meta-strategy (designed to wrap another)
                        # We identify meta-strategies by looking for an 'underlying_strategy' parameter
                        # in their __init__ method.
                        is_meta = hasattr(obj, 'underlying_strategy')

                        config = {
                            "name": name,
                            "class": obj,
                            "data": STRATEGY_CONFIG.get(name, {}).get("data", DEFAULT_DATA),
                            "scope": scope
                        }
                        
                        if is_meta:
                            strategies["meta"][name] = config
                        else:
                            strategies["standalone"].append(config)
            except ImportError as e:
                print(f"Error importing module {module_name}: {e}")

    # Link meta-strategies to their underlying standalone strategies
    linked_meta_strategies = []
    for meta_name, meta_config in strategies["meta"].items():
        if meta_name in STRATEGY_CONFIG:
            underlying_name = STRATEGY_CONFIG[meta_name]["underlying"]
            
            # Find the standalone strategy class
            underlying_class = next((s["class"] for s in strategies["standalone"] if s["name"] == underlying_name), None)
            
            if underlying_class:
                linked_config = meta_config.copy()
                linked_config["underlying"] = underlying_class
                linked_config["underlying_name"] = underlying_name
                linked_config["params"] = STRATEGY_CONFIG[meta_name].get("params", {})
                # Keep original name for config lookup, but use a more descriptive name for reports
                linked_config["report_name"] = f"{meta_name} ({underlying_name})"
                linked_meta_strategies.append(linked_config)
            else:
                print(f"Warning: Underlying strategy '{underlying_name}' not found for meta-strategy '{meta_name}'.")

    return strategies["standalone"], linked_meta_strategies


def run_benchmark(scope: str):
    """Runs a benchmark for the specified scope of strategies."""
    results = []
    standalone_strategies, meta_strategies = discover_strategies()

    # Filter strategies based on the selected scope
    if scope == 'all':
        strategies_to_run = standalone_strategies + meta_strategies
    elif scope == 'public':
        strategies_to_run = [s for s in standalone_strategies if s['scope'] == 'public']
    elif scope == 'private':
        strategies_to_run = [s for s in standalone_strategies if s['scope'] == 'private'] + meta_strategies
    else:
        strategies_to_run = []

    for config in strategies_to_run:
        strategy_name = config.get("report_name", config["name"])
        strategy_class = config["class"]
        
        print(f"\n--- Benchmarking Strategy: {strategy_name} ---")
        
        # --- Load Data ---
        try:
            data = pd.read_csv(config["data"])
            # Standardize date parsing and make timezone-naive
            data['date'] = pd.to_datetime(data['date'], utc=True)
            data = data.set_index('date')
            if isinstance(data.index, pd.DatetimeIndex):
                 data.index = data.index.tz_localize(None)
        except FileNotFoundError:
            print(f"Warning: Data file not found at {config['data']}. Skipping {strategy_name}.")
            continue
        except Exception as e:
            print(f"Error loading data for {strategy_name}: {e}. Skipping.")
            continue
        
        # Standardize column names
        data.columns = [col.capitalize() for col in data.columns]
        
        # --- Handle Meta-Strategies ---
        if 'underlying' in config:
            # Set the underlying strategy and other params on the class itself
            strategy_class.underlying_strategy = config['underlying']
            for param, value in config.get('params', {}).items():
                setattr(strategy_class, param, value)
            
            bt = Backtest(data, strategy_class, cash=100_000, commission=ibkr_tiered_commission)
            stats = bt.run()
        else:
            bt = Backtest(data, strategy_class, cash=100_000, commission=ibkr_tiered_commission)
            stats = bt.run()
        
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

    if not results:
        print(f"No strategies found for scope '{scope}'. No report generated.")
        return
        
    print(f"\n--- Generating {scope.capitalize()} Benchmark Report ---")
    results_df = pd.DataFrame(results).sort_values(by="Sharpe Ratio", ascending=False).round(2)
    
    # Determine output directory
    output_dir = 'reports'
    if scope == 'private' or (scope == 'all' and any(s['scope'] == 'private' for s in strategies_to_run)):
        private_reports_dir = os.path.join('strategies', 'private', 'reports')
        if os.path.exists(os.path.dirname(private_reports_dir)):
             output_dir = private_reports_dir
    
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

