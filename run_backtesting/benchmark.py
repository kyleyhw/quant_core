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
    "PairsTradingStrategy": {"data": "data/PEP_KO_2024_2025.csv"},
    "PortfolioAllocationStrategy": {"data": "data/SPY_2024_2025.csv"},
    "EnsembleSignalStrategy": {"data": "data/SPY_2024_2025.csv"},
    "MetaRegimeFilterStrategy": {
        "underlying": "SimpleMACrossover",
        "params": {"strategy_type": "trend"}
    },
    "DynamicSizingStrategy": {
        "underlying": "BollingerBandsStrategy",
        "params": {}
    }
}
DEFAULT_DATA = "data/SPY_2024_2025.csv"


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


def run_benchmark(scope: str, data_path: str = None):
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
        target_data = data_path if data_path else config["data"]
        
        # Special handling for PairsStrategy if we are overriding with single-asset data like SPY
        if "Pairs" in strategy_name and data_path and "SPY" in data_path:
             print(f"Skipping data override for {strategy_name} (requires pair data). Using config default.")
             target_data = config["data"]

        try:
            # Read first few lines to check for multi-header
            with open(target_data, 'r') as f:
                header_line_1 = f.readline()
                header_line_2 = f.readline()
            
            # Check if second line contains Tickers (common in yfinance multi-index)
            if "Ticker" in header_line_2 or "Price" in header_line_1:
                 # Load with multi-index header
                 data = pd.read_csv(target_data, header=[0, 1], index_col=0)
                 
                 # Check if we have multiple tickers (Pairs Strategy)
                 tickers = data.columns.get_level_values(1).unique().tolist()
                 
                 if len(tickers) >= 2 and "Pairs" in strategy_name:
                     # Assume Ticker 1 is the primary asset (e.g., PEP) and Ticker 2 is the secondary (e.g., KO)
                     # We need to sort them to be deterministic or use specific names if known
                     # For PEP/KO, let's just pick the first one as primary.
                     t1 = tickers[0]
                     t2 = tickers[1]
                     
                     # Create a flat DataFrame for Backtesting.py using Ticker 1's OHLC
                     flat_data = pd.DataFrame()
                     flat_data['Open'] = data[('Open', t1)]
                     flat_data['High'] = data[('High', t1)]
                     flat_data['Low'] = data[('Low', t1)]
                     flat_data['Close'] = data[('Close', t1)]
                     flat_data['Volume'] = data[('Volume', t1)]
                     
                     # Add Close_1 and Close_2 for the strategy logic
                     flat_data['Close_1'] = data[('Close', t1)]
                     flat_data['Close_2'] = data[('Close', t2)]
                     
                     data = flat_data
                 else:
                     # Single asset (SPY) but with multi-index
                     # Just take the first ticker found
                     t1 = tickers[0]
                     flat_data = pd.DataFrame()
                     flat_data['Open'] = data[('Open', t1)]
                     flat_data['High'] = data[('High', t1)]
                     flat_data['Low'] = data[('Low', t1)]
                     flat_data['Close'] = data[('Close', t1)]
                     flat_data['Volume'] = data[('Volume', t1)]
                     data = flat_data

                 # Index is likely the Date (from read_csv index_col=0)
                 data.index.name = 'date'
                 
                 # Convert to numeric
                 data = data.apply(pd.to_numeric, errors='coerce')
                 
            else:
                 data = pd.read_csv(target_data)

            # Standardize column names to lowercase (Backtesting.py expects capitalized, but we do it later)
            data.columns = [col.lower() for col in data.columns]
            
            # Standardize date parsing and make timezone-naive
            if data.index.name == 'date' or 'date' in data.columns:
                if 'date' in data.columns:
                    data['date'] = pd.to_datetime(data['date'], utc=True)
                    data = data.set_index('date')
                else:
                    data.index = pd.to_datetime(data.index, utc=True)
            
            if isinstance(data.index, pd.DatetimeIndex):
                 data.index = data.index.tz_localize(None)
            
            # Drop any rows with missing values (crucial for backtesting)
            data = data.dropna()
                 
        except FileNotFoundError:
            print(f"Warning: Data file not found at {target_data}. Skipping {strategy_name}.")
            continue
        except Exception as e:
            print(f"Error loading data for {strategy_name}: {e}. Skipping.")
            continue
        
        # Standardize column names for Backtesting.py (Capitalized)
        data.columns = [col.capitalize() for col in data.columns]
        
        # --- Handle Meta-Strategies ---
        if 'underlying' in config:
            strategy_class.underlying_strategy = config['underlying']
            for param, value in config.get('params', {}).items():
                setattr(strategy_class, param, value)
            
        bt = Backtest(data, strategy_class, cash=10000, commission=ibkr_tiered_commission)
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
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Add Data Source Info
        f.write(f"**Test Data Source:** `{data_path if data_path else 'Strategy Defaults'}`\n")
        if data_path and os.path.exists(data_path):
             try:
                 df_meta = pd.read_csv(data_path)
                 if 'date' in df_meta.columns:
                     start_date = df_meta['date'].min()
                     end_date = df_meta['date'].max()
                     f.write(f"**Test Period:** {start_date} to {end_date}\n")
             except:
                 pass
        f.write("\n")
        f.write(results_df.to_markdown(index=False))
        
    print(f"Benchmark report saved to {report_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a benchmark of trading strategies.")
    parser.add_argument(
        '--scope', type=str, default='all', choices=['public', 'private', 'all'],
        help='The scope of strategies to benchmark.'
    )
    parser.add_argument(
        '--data', type=str, default=None,
        help='Path to the data file to use for benchmarking (overrides config defaults).'
    )
    args = parser.parse_args()
    run_benchmark(scope=args.scope, data_path=args.data)
