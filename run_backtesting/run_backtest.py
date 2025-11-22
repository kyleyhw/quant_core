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

from strategies.simple_demo import SimpleMACrossover
from strategies.rsi_2_period import RSI2PeriodStrategy
from strategies.bollinger_bands import BollingerBandsStrategy

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
    
    # --- 3. Run Backtest ---
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

    # --- 4. Generate Plot and Report ---
    print("\nGenerating plot and report...")
    
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    plot_filename_rel_html = f"backtest_{args.strategy}_{timestamp}.html"
    plot_filename_abs_html = os.path.join('reports', plot_filename_rel_html)

    report_filename = os.path.join('reports', f"report_{args.strategy}_{timestamp}.md")

    # Generate the interactive HTML plot
    bt.plot(filename=plot_filename_abs_html, open_browser=False)
    print(f"Interactive plot saved to {plot_filename_abs_html}")

    with open(report_filename, 'w') as f:
        f.write(f"# Backtest Report: {args.strategy}\n\n")
        f.write(f"**Run Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Strategy Parameters\n")
        strategy_params = stats['_strategy']
        f.write(f"- **Fast MA Period:** {strategy_params.fast_ma_period}\n")
        f.write(f"- **Slow MA Period:** {strategy_params.slow_ma_period}\n")
        f.write(f"- **Risk Percent:** {strategy_params.risk_percent:.2%}\n")
        f.write(f"- **Stop-Loss Percent:** {strategy_params.stop_loss_pct:.2%}\n")
        f.write(f"- **Take-Profit Percent:** {strategy_params.take_profit_pct:.2%}\n\n")

        f.write("## Backtest Metrics\n")
        stats_to_report = stats[~stats.index.str.startswith('_')]
        f.write(stats_to_report.to_markdown())
        f.write("\n\n")

        f.write("## Equity Curve & Trades\n")
        f.write(f"[View interactive plot]({plot_filename_rel_html})\n")

    print(f"Detailed report saved to {report_filename}")

if __name__ == "__main__":
    main()

