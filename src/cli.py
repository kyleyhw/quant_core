import argparse
import sys
from run_backtesting import run_backtest, benchmark
from src import data_downloader
from strategies_private.research import train_regime_model, train_ensemble_models

def handle_backtest(args):
    """Handler for the 'backtest' command."""
    print("Running a single backtest...")
    
    # Construct the argument list for run_backtest.main
    argv = [
        '--strategy', args.strategy,
        '--data', args.data,
        '--cash', str(args.cash),
        '--commission', args.commission,
    ]
    
    run_backtest.main(argv)

def handle_benchmark(args):
    """Handler for the 'benchmark' command."""
    print("Running a benchmark...")
    benchmark.run_benchmark(scope=args.scope, data_path=args.data)

def handle_download(args):
    """Handler for the 'download' command."""
    print("Downloading data...")
    argv = [
        '--tickers', *args.tickers,
        '--start', args.start,
        '--end', args.end,
        '--output', args.output,
    ]
    if args.force:
        argv.append('--force')
    data_downloader.main(argv)

def handle_train_regime(args):
    """Handler for the 'train-regime' command."""
    print("Training regime model...")
    argv = []
    if args.csv:
        argv.extend(['--csv', args.csv])
    if args.symbol:
        argv.extend(['--symbol', args.symbol])
    if args.start:
        argv.extend(['--start', args.start])
    if args.end:
        argv.extend(['--end', args.end])
    if args.output:
        argv.extend(['--output', args.output])
    if args.report:
        argv.extend(['--report', args.report])
    
    train_regime_model.main(argv)

def handle_train_ensemble(args):
    """Handler for the 'train-ensemble' command."""
    print("Training ensemble models...")
    train_ensemble_models.main()

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="quant-core: A command-line interface for the algorithmic trading framework.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # --- Backtest Command ---
    parser_backtest = subparsers.add_parser("backtest", help="Run a backtest for a single strategy.")
    parser_backtest.add_argument("--strategy", required=True, help="The name of the strategy to test.")
    parser_backtest.add_argument("--data", required=True, help="Path to the historical data CSV file.")
    parser_backtest.add_argument("--cash", type=int, default=10000, help="Initial cash for the backtest.")
    parser_backtest.add_argument("--commission", default="0.002", help="Commission to use for the backtest.")
    parser_backtest.set_defaults(func=handle_backtest)

    # --- Benchmark Command ---
    parser_benchmark = subparsers.add_parser("benchmark", help="Run a benchmark of multiple strategies.")
    parser_benchmark.add_argument("--scope", default="all", choices=["public", "private", "all"], help="The scope of strategies to benchmark.")
    parser_benchmark.add_argument("--data", help="Path to the data file or directory to use for benchmarking.")
    parser_benchmark.set_defaults(func=handle_benchmark)

    # --- Download Command ---
    parser_download = subparsers.add_parser("download", help="Download historical market data.")
    parser_download.add_argument("--tickers", nargs="+", required=True, help="A list of tickers to download.")
    parser_download.add_argument("--start", required=True, help="The start date for the data in YYYY-MM-DD format.")
    parser_download.add_argument("--end", required=True, help="The end date for the data in YYYY-MM-DD format.")
    parser_download.add_argument("--output", default="data", help="The directory to save the downloaded data.")
    parser_download.add_argument("--force", action="store_true", help="Force download even if local file exists.")
    parser_download.set_defaults(func=handle_download)

    # --- Train Regime Command ---
    parser_train_regime = subparsers.add_parser("train-regime", help="Train the XGBoost regime classifier.")
    parser_train_regime.add_argument('--csv', type=str, help='Path to CSV file with OHLCV data')
    parser_train_regime.add_argument('--symbol', type=str, default='SPY', help='Symbol to fetch from IBKR')
    parser_train_regime.add_argument('--start', type=str, default='2015-01-01', help='Start date')
    parser_train_regime.add_argument('--end', type=str, default='2023-12-31', help='End date')
    parser_train_regime.add_argument('--output', type=str, default='strategies_private/models/xgb_regime_classifier.json',
                        help='Output model path')
    parser_train_regime.add_argument('--report', type=str, default='strategies_private/research/training_report.md',
                        help='Training report path')
    parser_train_regime.set_defaults(func=handle_train_regime)

    # --- Train Ensemble Command ---
    parser_train_ensemble = subparsers.add_parser("train-ensemble", help="Train the ensemble models.")
    parser_train_ensemble.set_defaults(func=handle_train_ensemble)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()

