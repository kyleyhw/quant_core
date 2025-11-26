import pandas as pd
from backtesting import Backtest, Strategy
import os
import sys
import argparse
import importlib
import inspect
from datetime import datetime
from pathlib import Path
import time

# --- Add project root to path ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.commission_models import ibkr_tiered_commission
from strategies.base_strategy import BaseStrategy

# --- Signal Executor Wrapper ---
class SignalExecutor(Strategy):
    """
    A wrapper to execute trades based on signals returned by an underlying strategy.
    This allows strategies designed for meta-strategy integration (which return
    signals) to be backtested directly.
    """
    underlying_strategy = None

    def init(self):
        if not self.underlying_strategy:
            raise ValueError("SignalExecutor requires an `underlying_strategy` to be set.")
        # Instantiate the actual strategy
        self.strategy = self.underlying_strategy(self._broker, self.data, self._params)
        self.strategy.init()

    def next(self):
        # Get signal from the underlying strategy
        signal = self.strategy.next()
        if signal == 'buy':
            self.buy()
        elif signal == 'sell':
            self.position.close()

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
DEFAULT_DATA = "data/benchmark"


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
                            
                            # Create "Hold" variants for Regime strategies
                            # DISABLED per user request (2025-11-25) to declutter reports
                            # if name in ["MLRegimeStrategy", "HmmRegimeStrategy", "MetaRegimeFilterStrategy"]:
                            #     config_hold = config.copy()
                            #     config_hold["name"] = f"{name}_Hold"
                            #     config_hold["report_name"] = f"{name} (Hold Sideways)"
                            #     if name == "MetaRegimeFilterStrategy":
                            #          config_hold["params"] = {"hold_during_unfavorable": True}
                            #     else:
                            #          config_hold["params"] = {"hold_during_sideways": True}
                            #     strategies["standalone"].append(config_hold)

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
    """Runs a benchmark for the specified scope of strategies across provided data."""
    
    # Use default data directory if no path provided
    if data_path is None:
        data_path = DEFAULT_DATA
        
    results = []
    standalone_strategies, meta_strategies = discover_strategies()

    # Filter strategies based on the selected scope
    if scope == 'all':
        strategies_to_run = standalone_strategies + meta_strategies
    elif scope == 'private':
        strategies_to_run = [s for s in standalone_strategies if s['scope'] == 'private'] + meta_strategies
    else:  # 'public'
        strategies_to_run = [s for s in standalone_strategies if s['scope'] == 'public']

    # --- Data Loading & Asset Discovery ---
    assets_map = {} # { 'Asset_Name': {'data': DataFrame, 'source': str} }
    
    if data_path:
        # Check if data_path is a directory or file
        if os.path.isdir(data_path):
            print(f"Loading all CSV files from directory: {data_path}...")
            import glob
            csv_files = glob.glob(os.path.join(data_path, "*.csv"))
            
            for file_path in csv_files:
                try:
                    # Check for MultiIndex (Price/Ticker structure)
                    with open(file_path, 'r') as f:
                        header_line_1 = f.readline()
                        header_line_2 = f.readline()
                    
                    if "Ticker" in header_line_2 or "Price" in header_line_1:
                        print(f"Loading multi-asset data from {os.path.basename(file_path)}...")
                        full_data = pd.read_csv(file_path, header=[0, 1], index_col=0)
                        full_data.index.name = 'date'
                        
                        tickers = full_data.columns.get_level_values(1).unique().tolist()
                        
                        for ticker in tickers:
                            df = pd.DataFrame()
                            # Handle cases where columns might be missing for some tickers
                            try:
                                df['Open'] = full_data[('Open', ticker)]
                                df['High'] = full_data[('High', ticker)]
                                df['Low'] = full_data[('Low', ticker)]
                                df['Close'] = full_data[('Close', ticker)]
                                df['Volume'] = full_data[('Volume', ticker)]
                            except KeyError:
                                continue

                            df = df.apply(pd.to_numeric, errors='coerce')
                            df.dropna(inplace=True)
                            
                            if not isinstance(df.index, pd.DatetimeIndex):
                                df.index = pd.to_datetime(df.index, utc=True)
                            if isinstance(df.index, pd.DatetimeIndex):
                                df.index = df.index.tz_localize(None)
                                
                            assets_map[ticker] = {'data': df, 'source': os.path.basename(file_path)}
                            print(f"   Loaded {ticker}")
                    else:
                        # Single Asset File
                        df = pd.read_csv(file_path)
                        # Infer asset name from filename (e.g., TSLA_2024_2025.csv -> TSLA)
                        asset_name = Path(file_path).stem.split('_')[0]
                        
                        # Standardize columns
                        df.columns = [col.capitalize() for col in df.columns]
                        
                        # Standardize Index
                        if 'Date' in df.columns:
                            df['Date'] = pd.to_datetime(df['Date'], utc=True)
                            df.set_index('Date', inplace=True)
                        elif 'date' in df.columns:
                            df['date'] = pd.to_datetime(df['date'], utc=True)
                            df.set_index('date', inplace=True)
                            df.index.name = 'Date'
                        
                        if isinstance(df.index, pd.DatetimeIndex):
                            df.index = df.index.tz_localize(None)
                        
                        # Clean data
                        df.dropna(inplace=True)
                            
                        assets_map[asset_name] = {'data': df, 'source': os.path.basename(file_path)}
                        print(f"Loaded {asset_name} from {os.path.basename(file_path)}")
                    
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
                    
        else:
            # Single File Logic (Existing)
            try:
                # Read first few lines to check for multi-header
                with open(data_path, 'r') as f:
                    header_line_1 = f.readline()
                    header_line_2 = f.readline()
                
                # Check for MultiIndex (Price/Ticker structure from yfinance)
                if "Ticker" in header_line_2 or "Price" in header_line_1:
                     print(f"Loading multi-asset data from {data_path}...")
                     full_data = pd.read_csv(data_path, header=[0, 1], index_col=0)
                     full_data.index.name = 'date'
                     
                     tickers = full_data.columns.get_level_values(1).unique().tolist()
                     
                     for ticker in tickers:
                         df = pd.DataFrame()
                         df['Open'] = full_data[('Open', ticker)]
                         df['High'] = full_data[('High', ticker)]
                         df['Low'] = full_data[('Low', ticker)]
                         df['Close'] = full_data[('Close', ticker)]
                         df['Volume'] = full_data[('Volume', ticker)]
                         
                         df = df.apply(pd.to_numeric, errors='coerce')
                         df.dropna(inplace=True)
                         
                         if not isinstance(df.index, pd.DatetimeIndex):
                             df.index = pd.to_datetime(df.index, utc=True)
                         if isinstance(df.index, pd.DatetimeIndex):
                             df.index = df.index.tz_localize(None)
                             
                         assets_map[ticker] = {'data': df, 'source': os.path.basename(data_path)}
                else:
                     # Single Asset File
                     print(f"Loading single-asset data from {data_path}...")
                     df = pd.read_csv(data_path)
                     df.columns = [col.capitalize() for col in df.columns]
                     
                     if 'Date' in df.columns:
                         df['Date'] = pd.to_datetime(df['Date'], utc=True)
                         df.set_index('Date', inplace=True)
                     elif 'date' in df.columns:
                         df['date'] = pd.to_datetime(df['date'], utc=True)
                         df.set_index('date', inplace=True)
                         df.index.name = 'Date'
                     
                     if isinstance(df.index, pd.DatetimeIndex):
                         df.index = df.index.tz_localize(None)
                     
                     asset_name = Path(data_path).stem.split('_')[0]
                     assets_map[asset_name] = {'data': df, 'source': os.path.basename(data_path)}
                     
            except Exception as e:
                print(f"Critical Error loading data {data_path}: {e}")
                return

    # --- Benchmarking Loop ---
    for asset_name, asset_info in assets_map.items():
        print(f"\n>>> Processing Asset: {asset_name} <<<")
        asset_data = asset_info['data']
        
        for config in strategies_to_run:
            strategy_name = config.get("report_name", config["name"])
            strategy_class = config["class"]
            
            if "Pairs" in strategy_name:
                if data_path: 
                    print(f"Skipping {strategy_name} for {asset_name} (Requires specific pair data).")
                    continue

            # Prepare Data
            if asset_data is not None:
                data = asset_data.copy()
            else:
                # Legacy/Default load
                target_data = config["data"]
                try:
                    data = pd.read_csv(target_data)
                    data.columns = [col.capitalize() for col in data.columns]
                    data['Date'] = pd.to_datetime(data['Date'] if 'Date' in data.columns else data['date'], utc=True)
                    data.set_index('Date', inplace=True)
                    data.index = data.index.tz_localize(None)
                except:
                    continue

            # Standardize columns for Backtesting.py
            data.columns = [col.capitalize() for col in data.columns]
            
            try:
                # Handle Meta-Strategies
                if 'underlying' in config:
                    strategy_class.underlying_strategy = config['underlying']
                
                # Reset specific parameters to defaults to prevent pollution across runs
                if hasattr(strategy_class, 'hold_during_sideways'):
                    strategy_class.hold_during_sideways = False
                if hasattr(strategy_class, 'hold_during_unfavorable'):
                    strategy_class.hold_during_unfavorable = False

                # Apply parameters (for both Meta and Standalone variants)
                for param, value in config.get('params', {}).items():
                    setattr(strategy_class, param, value)

                # --- Wrapper for Signal-based Strategies ---
                if config["name"] in ["SimpleMACrossover", "RSI2PeriodStrategy"]:
                    SignalExecutor.underlying_strategy = strategy_class
                    bt_strategy_class = SignalExecutor
                else:
                    bt_strategy_class = strategy_class
                
                bt = Backtest(data, bt_strategy_class, cash=10000, commission=ibkr_tiered_commission)
                
                start_time = time.time()
                stats = bt.run()
                end_time = time.time()
                runtime = end_time - start_time
                
                key_metrics = {
                    "Asset": asset_name,
                    "Strategy": strategy_name,
                    "Return [%]": stats["Return [%]"],
                    "Sharpe Ratio": stats["Sharpe Ratio"],
                    "Max. Drawdown [%]": stats["Max. Drawdown [%]"],
                    "Win Rate [%]": stats["Win Rate [%]"],
                    "# Trades": stats["# Trades"],
                    "Runtime [s]": round(runtime, 4),
                    "Source": asset_info['source']
                }
                results.append(key_metrics)
                print(f"   Finished: {strategy_name} (Runtime: {runtime:.4f}s)")
                
            except Exception as e:
                print(f"   Error running {strategy_name} on {asset_name}: {e}")

    # --- Report Generation ---
    if not results:
        print("No results generated.")
        return

    print(f"\n--- Generating Consolidated Benchmark Report ---")
    
    # Group results by Asset
    results_df = pd.DataFrame(results)
    assets = results_df['Asset'].unique()
    
    output_dir = 'reports'
    if scope == 'private' or (scope == 'all' and any(s['scope'] == 'private' for s in strategies_to_run)):
        private_reports_dir = os.path.join('strategies', 'private', 'reports')
        if os.path.exists(os.path.dirname(private_reports_dir)):
             output_dir = private_reports_dir
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = os.path.join(output_dir, f"benchmark_report_multi_asset_{timestamp}.md")
    
    with open(report_path, "w") as f:
        f.write(f"# Multi-Asset Strategy Benchmark Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # --- Strategy Summary & Training Data ---
        f.write("## Strategy Summary & Training Data\n")
        f.write("| Strategy Type | Strategies | Training Data Source |\n")
        f.write("| :--- | :--- | :--- |\n")
        f.write("| **Baseline** | `BuyAndHoldStrategy` | N/A |\n")
        f.write("| **Machine Learning** | `MLRegimeStrategy`, `EnsembleSignalStrategy` | **SPY (2010-2023)** |\n")
        f.write("| **Meta-Strategies** | `DynamicSizing`, `MetaRegimeFilter` | N/A (Uses underlying logic) |\n")
        f.write("| **Technical** | `SimpleMACrossover`, `RSI2Period`, `BollingerBands` | N/A (Rule-based) |\n\n")
        
        f.write("## Performance Metrics by Asset\n\n")
        
        for asset in sorted(assets):
            f.write(f"### {asset}\n")
            asset_results = results_df[results_df['Asset'] == asset].sort_values(by="Sharpe Ratio", ascending=False).round(2)
            
            # Get source for this asset (should be same for all rows of this asset)
            source_file = asset_results['Source'].iloc[0]
            f.write(f"**Test Data Source:** `{source_file}`\n\n")
            
            # Remove redundant columns
            asset_results = asset_results.drop(columns=['Asset', 'Source'])
            f.write(asset_results.to_markdown(index=False))
            f.write("\n\n")
        
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
