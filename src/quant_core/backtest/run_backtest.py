"""Run one installed strategy on one or more data inputs and write a report.

Strategies come from the ``quant_core.strategies`` entry-point group. A strategy
that sets ``data_assets = 2`` receives two inputs merged column-wise with ``_1``
and ``_2`` suffixes, and the first asset's columns are also exposed as plain
``Open``/``High``/``Low``/``Close``/``Volume`` for the engine to trade.
"""

import argparse
import ast
import os

import pandas as pd
from backtesting import Backtest

from quant_core.commission_models import COMMISSION_MODELS
from quant_core.registry import discover_strategies, print_discovery_errors

DEFAULT_OUTPUT = "reports"


def parse_params(pairs: list[str]) -> dict:
    """Parses ``KEY=VALUE`` strings. Values are read as Python literals when they
    parse as one (``0.02``, ``True``, ``[1, 2]``) and as plain strings otherwise."""
    params = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"--param expects KEY=VALUE, got {pair!r}")
        key, raw = pair.split("=", 1)
        try:
            params[key] = ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            params[key] = raw
    return params


def main(argv: list[str] | None = None) -> None:
    """
    Runs a backtest for a single strategy.
    """
    discovery = discover_strategies()
    print_discovery_errors(discovery)
    all_strategies = {name: s.cls for name, s in discovery.strategies.items()}

    parser = argparse.ArgumentParser(description="Run a backtest for a given strategy.")
    parser.add_argument(
        "--strategy",
        type=str,
        required=True,
        choices=list(all_strategies.keys()),
        help="The name of the strategy class to test.",
    )
    parser.add_argument(
        "--underlying",
        type=str,
        default=None,
        help="The name of the underlying strategy for a meta-strategy.",
    )
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override a strategy parameter. Repeatable, e.g. --param stop_loss_pct=0.03.",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT,
        help=f"Where to write the plot and report (default: {DEFAULT_OUTPUT}).",
    )
    parser.add_argument(
        "--data",
        type=str,
        nargs="+",
        default=["data/SPY_1hour_1year.csv"],
        help="Path(s) to the historical data CSV file(s).",
    )
    parser.add_argument("--cash", type=int, default=10000, help="Initial cash for the backtest.")
    parser.add_argument(
        "--commission",
        type=str,
        default="IBKR Tiered",
        choices=list(COMMISSION_MODELS.keys()),
        help="Commission model to use.",
    )
    parser.add_argument(
        "--start",
        type=str,
        default="2020-01-01",
        help="Start date for fetching ticker data (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--end",
        type=str,
        default="2023-12-31",
        help="End date for fetching ticker data (YYYY-MM-DD).",
    )
    args = parser.parse_args(argv)
    params = parse_params(args.param)
    StrategyClass = all_strategies[args.strategy]
    data_assets = int(getattr(StrategyClass, "data_assets", 1))

    # --- 1. Load Data ---
    from quant_core.data_loader import SmartLoader

    loaded_dfs = []

    with SmartLoader() as loader:
        data_inputs = args.data if isinstance(args.data, list) else [args.data]

        for input_val in data_inputs:
            df = None

            # Case A: Local CSV File
            if input_val.endswith(".csv") and os.path.exists(input_val):
                print(f"Loading local file: {input_val}")
                df = pd.read_csv(input_val)
                df.rename(columns={"date": "Date"}, inplace=True)

                # Identify date column
                date_col_candidates = [col for col in df.columns if col.lower() == "date"]
                if not date_col_candidates:
                    print(f"Error: No date column found in {input_val}.")
                    return
                date_col = date_col_candidates[0]

                df[date_col] = pd.to_datetime(df[date_col], utc=True)
                df.set_index(date_col, inplace=True)
                df.index.name = "Date"

            # Case B: Ticker Symbol (via SmartLoader)
            else:
                print(f"Requesting data for ticker: {input_val} ({args.start} to {args.end})")
                try:
                    df = loader.load_data(input_val, args.start, args.end)
                    # SmartLoader returns index as Date, but might be timezone aware or not.
                    # Ensure consistency.
                    df.index.name = "Date"
                except Exception as e:
                    print(f"Error loading {input_val}: {e}")
                    return

            # Common Post-Processing
            if df is not None:
                # Explicitly ensure index is DatetimeIndex
                if not isinstance(df.index, pd.DatetimeIndex):
                    try:
                        df.index = pd.to_datetime(df.index, utc=True)
                    except Exception as e:
                        print(f"Error converting index to datetime: {e}")
                        return

                # Ensure timezone-naive
                idx = pd.DatetimeIndex(df.index)
                if idx.tz is not None:
                    df.index = idx.tz_localize(None)

                # Standardize column names
                df.columns = [col.capitalize() for col in df.columns]

                # Explicitly convert to numeric
                for col in ["Open", "High", "Low", "Close", "Volume"]:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")

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

        # A two-asset strategy gets _1 / _2 suffixed columns
        if data_assets == 2:
            # Asset 1 (Primary) -> Suffix _1
            data = data.add_suffix("_1")

            # Asset 2 -> Suffix _2
            if len(loaded_dfs) > 1:
                df2 = loaded_dfs[1].add_suffix("_2")
                data = pd.merge(data, df2, left_index=True, right_index=True, how="inner")

            # Map Asset 1 back to standard OHLCV for Backtesting.py execution
            # But keep the _1 columns for the strategy logic
            data["Open"] = data["Open_1"]
            data["High"] = data["High_1"]
            data["Low"] = data["Low_1"]
            data["Close"] = data["Close_1"]
            data["Volume"] = data["Volume_1"]

        else:
            # Generic merge; `data` already seeded from loaded_dfs[0] above.
            for i, df in enumerate(loaded_dfs[1:], start=2):
                data = pd.merge(
                    data, df, left_index=True, right_index=True, how="inner", suffixes=("", f"_{i}")
                )

    data.dropna(inplace=True)

    print("Data loaded successfully:")
    print(data.head())

    # --- 2. Select Strategy ---
    print(f"\nSelecting strategy: {args.strategy}...")

    # If it's a meta-strategy, set its parameters
    if hasattr(StrategyClass, "underlying_strategy"):
        if not args.underlying:
            raise ValueError(f"The '{args.strategy}' strategy requires the --underlying argument.")
        if args.underlying not in all_strategies:
            raise ValueError(f"Unknown underlying strategy: {args.underlying}")
        StrategyClass.underlying_strategy = all_strategies[args.underlying]
        print(f"   with Underlying Strategy: {args.underlying}")

    # --- 3. Run Backtest ---
    print(
        f"\nRunning backtest with initial cash ${args.cash:,.2f} "
        f"and commission model: {args.commission}..."
    )

    bt = Backtest(
        data,
        StrategyClass,
        cash=args.cash,
        commission=COMMISSION_MODELS[args.commission],  # ty:ignore[invalid-argument-type]
    )

    stats = bt.run(**params)
    print("\nBacktest Results:")
    print(stats)

    # --- 4. Determine Output Path and Generate Report ---
    print("\nGenerating plot and report...")

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    plot_filename_rel = f"backtest_{args.strategy}_{timestamp}.html"
    plot_filename_abs = os.path.join(output_dir, plot_filename_rel)
    report_filename = os.path.join(output_dir, f"report_{args.strategy}_{timestamp}.md")

    # Generate the interactive HTML plot
    bt.plot(filename=plot_filename_abs, open_browser=False)
    print(f"Interactive plot saved to {plot_filename_abs}")

    with open(report_filename, "w") as f:
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
            if "percent" in param.lower() and isinstance(value, int | float):
                f.write(f"- **{param.replace('_', ' ').title()}:** {value:.2%}\n")
            elif isinstance(value, float):
                f.write(f"- **{param.replace('_', ' ').title()}:** {value:.2f}\n")
            else:
                f.write(f"- **{param.replace('_', ' ').title()}:** {value}\n")
        f.write("\n")  # Add a newline after parameters

        f.write("## Backtest Metrics\n")
        # Filter out internal keys (starting with _)
        stats_to_report = stats[~stats.index.str.startswith("_")]
        # Explicitly check for commission if available in the broker/strategy
        # context. Note: backtesting.py stats may not have a direct 'Commission'
        # field in the summary series but it can be calculated from trades.

        f.write(stats_to_report.to_markdown())
        f.write("\n\n")

        f.write("## Equity Curve\n")
        f.write(f"[View interactive plot]({plot_filename_rel})\n\n")

        f.write("## Trade Log\n")
        trades = stats["_trades"]
        if not trades.empty:
            # Format trade log for readability
            trades_formatted = trades.copy()
            if "EntryTime" in trades_formatted.columns:
                trades_formatted["EntryTime"] = trades_formatted["EntryTime"].dt.strftime(
                    "%Y-%m-%d %H:%M"
                )
            if "ExitTime" in trades_formatted.columns:
                trades_formatted["ExitTime"] = trades_formatted["ExitTime"].dt.strftime(
                    "%Y-%m-%d %H:%M"
                )

            f.write(trades_formatted.to_markdown())
        else:
            f.write("No trades executed.\n")

    print(f"Detailed report saved to {report_filename}")


if __name__ == "__main__":
    main()
