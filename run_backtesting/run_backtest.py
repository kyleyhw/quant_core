import pandas as pd
from backtesting import Backtest
import argparse
import importlib
import sys
import os

# Add the project root to the Python path to allow for absolute imports when running directly
# This is generally not needed when running as a module (e.g., `python -m run_backtesting.run_backtest`)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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
except ImportError:
    MLRegimeStrategy = None
    HmmRegimeStrategy = None
    PairsTradingStrategy = None
    MetaRegimeFilterStrategy = None
    DynamicSizingStrategy = None

def get_strategy_class(strategy_name: str):
    """
    Dynamically imports and returns a strategy class from a given name.
    """
    if strategy_name == "simple-ma-crossover":
        return SimpleMACrossover
    elif strategy_name == "rsi-2-period":
        return RSI2PeriodStrategy
    elif strategy_name == "bollinger-bands":
        return BollingerBandsStrategy
    elif strategy_name == "ml-regime" and MLRegimeStrategy:
        return MLRegimeStrategy
    elif strategy_name == "hmm-regime" and HmmRegimeStrategy:
        return HmmRegimeStrategy
    elif strategy_name == "pairs-trading" and PairsTradingStrategy:
        return PairsTradingStrategy
    elif strategy_name == "meta-regime-filter" and MetaRegimeFilterStrategy:
        return MetaRegimeFilterStrategy
    elif strategy_name == "dynamic-sizing" and DynamicSizingStrategy:
        return DynamicSizingStrategy
    elif (strategy_name == "ml-regime" and not MLRegimeStrategy) or \
         (strategy_name == "hmm-regime" and not HmmRegimeStrategy) or \
         (strategy_name == "pairs-trading" and not PairsTradingStrategy) or \
         (strategy_name == "meta-regime-filter" and not MetaRegimeFilterStrategy) or \
         (strategy_name == "dynamic-sizing" and not DynamicSizingStrategy):
        raise ImportError(f"Could not import {strategy_name}. Is the private submodule available?")
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

def main():
    """
    Runs a backtest for a single strategy.
    """
    parser = argparse.ArgumentParser(description="Run a backtest for a given strategy.")
    parser.add_argument(
        '--strategy',
        type=str,
        default='simple-ma-crossover',
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
    StrategyClass = get_strategy_class(args.strategy)

    # If it's a meta-strategy, set its parameters
    if args.strategy in ['meta-regime-filter', 'dynamic-sizing']:
        if not args.underlying:
            raise ValueError(f"The '{args.strategy}' strategy requires the --underlying argument.")
        UnderlyingStrategyClass = get_strategy_class(args.underlying)
        StrategyClass.underlying_strategy = UnderlyingStrategyClass
        if args.strategy == 'meta-regime-filter':
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

