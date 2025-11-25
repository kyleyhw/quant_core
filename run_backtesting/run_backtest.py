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
from src.commission_models import ibkr_tiered_commission
from pathlib import Path
import inspect

def discover_strategies() -> dict:
    """Dynamically discovers and imports all available strategies."""
    strategies = {}
    
    public_path = Path(project_root) / 'strategies'
    private_path = public_path / 'private' / 'private_strategies'
    search_paths = [public_path]
    
    if private_path.exists() and any(private_path.iterdir()):
        search_paths.append(private_path)

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

def main():
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
        default='data/SPY_1hour_1year.csv',
        help='Path to the historical data CSV file.'
    )
    parser.add_argument(
        '--cash',
        type=int,
        default=10000,
        help='Initial cash for the backtest.'
    )
    args = parser.parse_args()

    # --- 1. Load Data ---
    print(f"Loading data from {args.data}...")
    if not os.path.exists(args.data):
        print(f"Error: Data file not found at {args.data}")
        print("Please run the data loader or provide a valid path.")
        return

    # Load the data
    data = pd.read_csv(args.data)
    # Standardize column names to lowercase
    data.columns = [col.lower() for col in data.columns]
    
    # Convert 'date' column to datetime and set as index
    data['date'] = pd.to_datetime(data['date'], utc=True)
    data = data.set_index('date')
    # Make timezone-naive if it became aware during parsing
    if data.index.tz is not None:
        data.index = data.index.tz_localize(None)
    
    # Ensure standard column names (Open, High, Low, Close, Volume)
    data.columns = [col.capitalize() for col in data.columns]

    
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
    print(f"\nRunning backtest with initial cash ${args.cash:,.2f} and IBKR Tiered commission model...")
    bt = Backtest(
        data,
        StrategyClass,
        cash=args.cash,
        commission=ibkr_tiered_commission
    )
    
    stats = bt.run()
    print("\nBacktest Results:")
    print(stats)

    # --- 4. Determine Output Path and Generate Report ---
    print("\nGenerating plot and report...")

    # Dynamically determine if the strategy is private by checking its import path
    if 'strategies.private' in StrategyClass.__module__:
        output_dir = os.path.join('strategies', 'private', 'reports')
    else:
        output_dir = 'reports'
        
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
        stats_to_report = stats[~stats.index.str.startswith('_')]
        f.write(stats_to_report.to_markdown())
        f.write("\n\n")

        f.write("## Equity Curve & Trades\n")
        f.write(f"[View interactive plot]({plot_filename_rel})\n")

    print(f"Detailed report saved to {report_filename}")

if __name__ == "__main__":
    main()

