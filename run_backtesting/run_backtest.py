import pandas as pd
from backtesting import Backtest, Strategy
import argparse
import importlib
import sys
import os

# Add the project root to the Python path to allow for absolute imports when running directly
# This is generally not needed when running as a module (e.g., `python -m run_backtesting.run_backtest`)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from strategies.base_strategy import BaseStrategy
from src.commission_models import COMMISSION_MODELS
from src.backtesting_extensions import CustomBacktest
from pathlib import Path
import inspect

# --- Signal Executor Wrapper (for signal-based strategies) ---
class SignalExecutor(Strategy):
    underlying_strategy = None

    def init(self):
        if not self.underlying_strategy:
            raise ValueError("SignalExecutor requires an `underlying_strategy` to be set.")
        self.strategy = self.underlying_strategy(self._broker, self.data, self._params)
        self.strategy.init()

    def next(self):
        signal = self.strategy.next()
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

def discover_strategies() -> dict:
    """Dynamically discovers and imports all available strategies."""
    strategies = {}
    
    public_path = Path(project_root) / 'strategies'
    private_path = Path(project_root) / 'strategies_private'
    search_paths = [public_path, private_path]
    
    for path in search_paths:
        for file in path.glob('*.py'):
            if file.name.startswith(('__init__', 'base_')):
                continue

            module_name = f"{path.relative_to(Path(project_root)).as_posix().replace('/', '.')}.{file.stem}"
            
            try:
                module = importlib.import_module(module_name)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, (Strategy, BaseStrategy)) and obj not in (Strategy, BaseStrategy):
                        strategies[name] = obj
            except ImportError as e:
                print(f"Could not import {module_name}: {e}")
    return strategies

def get_strategy_class(strategy_name: str, all_strategies: dict):
    """Returns the strategy class from the discovered strategies."""
    if strategy_name not in all_strategies:
        raise ValueError(f"Unknown strategy: {strategy_name}. Available strategies are: {', '.join(all_strategies.keys())}")
    return all_strategies[strategy_name]

def main() -> None:
    """
    Runs a backtest for a single strategy.
    """
    all_strategies = discover_strategies()
    
    parser = argparse.ArgumentParser(description="Run a backtest for a given strategy.")
    parser.add_argument(
        '--strategy',
        type=str,
        required=True,
        choices=list(all_strategies.keys()),
        help='The name of the strategy class to test.'
    )
    parser.add_argument(
        '--underlying',
        type=str,
        default=None,
        help='The name of the underlying strategy for a meta-strategy.'
    )
    parser.add_argument(
        '--strategy-type',
        type=str,
        default='mean-reversion',
        choices=['mean-reversion', 'trend'],
        help='The type of the underlying strategy (for meta-strategies).'
    )
    parser.add_argument(
        '--data',
        type=str,
        nargs='+',
        default=['data/SPY_1hour_1year.csv'],
        help='Path(s) to the historical data CSV file(s).'
    )
    parser.add_argument(
        '--cash',
        type=int,
        default=10000,
        help='Initial cash for the backtest.'
    )
    parser.add_argument(
        '--commission',
        type=str,
        default='IBKR Tiered',
        choices=list(COMMISSION_MODELS.keys()),
        help='Commission model to use.'
    )
    args = parser.parse_args()

    # --- 1. Load Data ---
    print(f"Loading data from {args.data}...")
    
    loaded_dfs = []
    # Ensure args.data is a list (it should be with nargs='+')
    data_paths = args.data if isinstance(args.data, list) else [args.data]
    
    for file_path in data_paths:
        if not os.path.exists(file_path):
            print(f"Error: Data file not found at {file_path}")
            return

        # Load the data without parsing dates initially
        df = pd.read_csv(file_path)
        df.rename(columns={'date': 'Date'}, inplace=True)

        # Identify the date column (case-insensitive) and convert to datetime
        date_col_candidates = [col for col in df.columns if col.lower() == 'date']
        if not date_col_candidates:
            print(f"Error: No date column found in {file_path}. Expected 'Date' or 'date'.")
            return
        date_col = date_col_candidates[0]

        df[date_col] = pd.to_datetime(df[date_col], utc=True)
        df.set_index(date_col, inplace=True)
        df.index.name = 'Date'

        # Ensure timezone-naive
        if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        # Standardize column names
        df.columns = [col.capitalize() for col in df.columns]
        
        # Explicitly convert to numeric
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        loaded_dfs.append(df)

    if not loaded_dfs:
        print("Error: No data loaded.")
        return

    # Merge logic
    if len(loaded_dfs) == 1:
        data = loaded_dfs[0]
    else:
        # Multi-file merge
        data = loaded_dfs[0].copy()
        
        # If PairsTradingStrategy, map specifically to _1 and _2
        if args.strategy == 'PairsTradingStrategy':
            # Asset 1 (Primary) -> Suffix _1
            data = data.add_suffix('_1')
            
            # Asset 2 -> Suffix _2
            if len(loaded_dfs) > 1:
                df2 = loaded_dfs[1].add_suffix('_2')
                data = pd.merge(data, df2, left_index=True, right_index=True, how='inner')
            
            # Map Asset 1 back to standard OHLCV for Backtesting.py execution
            # But keep the _1 columns for the strategy logic
            data['Open'] = data['Open_1']
            data['High'] = data['High_1']
            data['Low'] = data['Low_1']
            data['Close'] = data['Close_1']
            data['Volume'] = data['Volume_1']
            
        else:
            # Generic merge for other multi-asset strategies
            base_df = loaded_dfs[0]
            for i, df in enumerate(loaded_dfs[1:], start=2):
                data = pd.merge(data, df, left_index=True, right_index=True, how='inner', suffixes=('', f'_{i}'))

    data.dropna(inplace=True)
    
    print("Data loaded successfully:")
    print(data.head())

    # --- 2. Select Strategy ---
    print(f"\nSelecting strategy: {args.strategy}...")
    StrategyClass = get_strategy_class(args.strategy, all_strategies)

    # If it's a meta-strategy, set its parameters
    if hasattr(StrategyClass, 'underlying_strategy'):
        if not args.underlying:
            raise ValueError(f"The '{args.strategy}' strategy requires the --underlying argument.")
        UnderlyingStrategyClass = get_strategy_class(args.underlying, all_strategies)
        StrategyClass.underlying_strategy = UnderlyingStrategyClass
        
        # Check if strategy_type is a parameter for the meta-strategy and set it
        if hasattr(StrategyClass, 'strategy_type'):
            StrategyClass.strategy_type = args.strategy_type
            print(f"   with Underlying Strategy: {args.underlying} (Type: {args.strategy_type})")
        else:
            print(f"   with Underlying Strategy: {args.underlying}")
    
    # --- 3. Run Backtest ---
    print(f"\nRunning backtest with initial cash ${args.cash:,.2f} and commission model: {args.commission}...")
    
    # --- Wrapper for Signal-based Strategies ---
    bt_strategy_class = StrategyClass
    if args.strategy in ["SimpleMACrossover", "RSI2PeriodStrategy"]:
        SignalExecutor.underlying_strategy = StrategyClass
        bt_strategy_class = SignalExecutor

    bt = CustomBacktest(
        data,
        bt_strategy_class,
        cash=args.cash,
        commission=COMMISSION_MODELS[args.commission]
    )
    
    stats = bt.run()
    print("\nBacktest Results:")
    print(stats)

    # --- 4. Determine Output Path and Generate Report ---
    print("\nGenerating plot and report...")

    # Dynamically determine if the strategy is private by checking its import path
    if 'strategies_private' in StrategyClass.__module__:
        output_dir = os.path.join('strategies_private', 'reports')
    else:
        output_dir = 'strategies/reports' # Changed from 'reports'
        
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    plot_filename_rel = f"backtest_{args.strategy}_{timestamp}.html"
    plot_filename_abs = os.path.join(output_dir, plot_filename_rel)
    report_filename = os.path.join(output_dir, f"report_{args.strategy}_{timestamp}.md")

    # Generate the interactive HTML plot
    bt.plot(filename=plot_filename_abs, open_browser=False)
    print(f"Interactive plot saved to {plot_filename_abs}")

    with open(report_filename, 'w') as f:
        f.write(f"# Backtest Report: {args.strategy}\n\n")
        f.write(f"**Run Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Data Configuration\n")
        f.write(f"- **Data Source:** `{args.data}`\n")
        f.write(f"- **Date Range:** {data.index.min().date()} to {data.index.max().date()}\n")
        f.write(f"- **Commission Model:** {args.commission}\n\n")

        f.write("## Strategy Parameters\n")
        strategy_params = stats._strategy._params
        for param, value in strategy_params.items():
            # Format percentages
            if "percent" in param.lower() and isinstance(value, (int, float)):
                f.write(f"- **{param.replace('_', ' ').title()}:** {value:.2%}\n")
            elif isinstance(value, float):
                f.write(f"- **{param.replace('_', ' ').title()}:** {value:.2f}\n")
            else:
                f.write(f"- **{param.replace('_', ' ').title()}:** {value}\n")
        f.write("\n") # Add a newline after parameters

        f.write("## Backtest Metrics\n")
        # Filter out internal keys (starting with _)
        stats_to_report = stats[~stats.index.str.startswith('_')]
        # Explicitly check for commission if available in the broker or strategy context
        # Note: backtesting.py stats might not have a direct 'Commission' field in the summary series
        # but we can calculate it from trades if needed.
        
        f.write(stats_to_report.to_markdown())
        f.write("\n\n")

        f.write("## Equity Curve\n")
        f.write(f"[View interactive plot]({plot_filename_rel})\n\n")
        
        f.write("## Trade Log\n")
        trades = stats['_trades']
        if not trades.empty:
            # Format trade log for readability
            trades_formatted = trades.copy()
            if 'EntryTime' in trades_formatted.columns:
                trades_formatted['EntryTime'] = trades_formatted['EntryTime'].dt.strftime('%Y-%m-%d %H:%M')
            if 'ExitTime' in trades_formatted.columns:
                trades_formatted['ExitTime'] = trades_formatted['ExitTime'].dt.strftime('%Y-%m-%d %H:%M')
            
            f.write(trades_formatted.to_markdown())
        else:
            f.write("No trades executed.\n")

    print(f"Detailed report saved to {report_filename}")

if __name__ == "__main__":
    main()
