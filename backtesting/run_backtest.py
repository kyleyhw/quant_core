import pandas as pd
from backtesting import Backtest
import argparse
import importlib
import sys
import os

# Add the project root to the Python path to allow for absolute imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from strategies.simple_demo import SimpleMACrossover

def get_strategy_class(strategy_name: str):
    """
    Dynamically imports and returns a strategy class from a given name.
    
    Example: "SimpleMACrossover" -> from strategies.simple_demo import SimpleMACrossover
    Assumes a convention where the module name is the snake_case version of the class name.
    """
    # For now, we'll use a simple if/else, but this can be made more dynamic later.
    if strategy_name == "SimpleMACrossover":
        return SimpleMACrossover
    # Add other strategies here as they are created
    # elif strategy_name == "AnotherStrategy":
    #     from strategies.another_strategy import AnotherStrategy
    #     return AnotherStrategy
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
        default='SimpleMACrossover',
        help='The name of the strategy class to test.'
    )
    parser.add_argument(
        '--data',
        type=str,
        default='data/SPY_1hour.csv',
        help='Path to the historical data CSV file.'
    )
    parser.add_argument(
        '--cash',
        type=int,
        default=10000,
        help='Initial cash for the backtest.'
    )
    parser.add_argument(
        '--commission',
        type=float,
        default=0.005,  # 0.5% as specified
        help='Commission per trade.'
    )
    args = parser.parse_args()

    # --- 1. Load Data ---
    print(f"Loading data from {args.data}...")
    if not os.path.exists(args.data):
        print(f"Error: Data file not found at {args.data}")
        print("Please run the data loader or provide a valid path.")
        return

    # Load the data, parse dates, and set the index
    data = pd.read_csv(args.data, index_col='date', parse_dates=True)
    
    # Ensure standard column names (Open, High, Low, Close, Volume)
    # The backtesting library is case-sensitive.
    data.columns = [col.capitalize() for col in data.columns]
    
    print("Data loaded successfully:")
    print(data.head())

    # --- 2. Pre-calculate Indicators ---
    # To avoid issues with the self.I() method and to make the process more explicit,
    # we can pre-calculate indicators and add them to the dataframe.
    # This is a robust pattern when using libraries like pandas-ta.
    print("\nPre-calculating indicators...")
    import pandas_ta as ta
    
    # Get the strategy class to access its parameters
    StrategyClass = get_strategy_class(args.strategy)
    
    # Calculate SMAs using pandas-ta and add them to the dataframe
    data.ta.sma(length=StrategyClass.fast_ma_period, append=True)
    data.ta.sma(length=StrategyClass.slow_ma_period, append=True)
    
    print("Indicators calculated and added to data:")
    print(data.tail())


    # --- 3. Select Strategy ---
    print(f"\nSelecting strategy: {args.strategy}...")
    
    # --- 4. Run Backtest ---
    print(f"\nRunning backtest with initial cash ${args.cash:,.2f} and {args.commission:.3%} commission...")
    bt = Backtest(
        data,
        StrategyClass,
        cash=args.cash,
        commission=args.commission
    )
    
    stats = bt.run()
    print("\nBacktest Results:")
    print(stats)

    # --- 5. Generate Plot and Report ---
    print("\nGenerating plot and report...")
    
    # Generate a unique filename for the plot and report
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    plot_filename_rel = f"backtest_{args.strategy}_{timestamp}.html"
    plot_filename_abs = os.path.join('reports', plot_filename_rel)

    report_filename = os.path.join('reports', f"report_{args.strategy}_{timestamp}.md")

    # Generate the plot
    bt.plot(filename=plot_filename_abs, open_browser=False)
    print(f"Plot saved to {plot_filename_abs}")

    # Generate the markdown report
    with open(report_filename, 'w') as f:
        f.write(f"# Backtest Report: {args.strategy}\n\n")
        f.write(f"**Run Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Strategy Parameters\n")
        # The _strategy object holds the parameters
        strategy_params = stats['_strategy']
        f.write(f"- **Fast MA Period:** {strategy_params.fast_ma_period}\n")
        f.write(f"- **Slow MA Period:** {strategy_params.slow_ma_period}\n")
        f.write(f"- **Risk Percent:** {strategy_params.risk_percent:.2%}\n")
        f.write(f"- **Stop-Loss Percent:** {strategy_params.stop_loss_pct:.2%}\n")
        f.write(f"- **Take-Profit Percent:** {strategy_params.take_profit_pct:.2%}\n\n")

        f.write("## Backtest Metrics\n")
        # Filter out internal stats values (which start with '_') before converting to markdown
        stats_to_report = stats[~stats.index.str.startswith('_')]
        f.write(stats_to_report.to_markdown())
        f.write("\n\n")

        f.write("## Equity Curve & Trades\n")
        f.write(f"[View interactive plot]({plot_filename_rel})\n")

    print(f"Detailed report saved to {report_filename}")

if __name__ == "__main__":
    main()
