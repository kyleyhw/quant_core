"""Run every installed strategy across a directory of price data and write a report.

Strategies come from the ``quant_core.strategies`` entry-point group, so the
benchmark runs whatever is installed: the platform's reference strategies, plus
any strategies a downstream package registers. Paths are relative to the
current working directory, so the same command works from a checkout of this
repository or from a project that depends on it.

Two class attributes let a strategy shape how it is benchmarked:

- ``data_assets``: how many assets it trades at once. The benchmark feeds one
  asset per run, so a strategy with ``data_assets = 2`` is skipped. Use
  ``qc backtest`` with two ``--data`` inputs for those.
- ``underlying_strategy``: a meta-strategy that wraps another. Register a
  subclass that sets it; one registered with it still ``None`` is skipped.
"""

import argparse
import glob
import os
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from backtesting import Backtest

from quant_core.commission_models import ibkr_tiered_commission
from quant_core.registry import RegisteredStrategy, discover_strategies, print_discovery_errors

DEFAULT_DATA = "data/benchmark"
DEFAULT_OUTPUT = "reports"
CASH = 10_000


def _is_multi_asset_csv(file_path: str) -> bool:
    """yfinance multi-ticker downloads carry a Price/Ticker two-row header."""
    with open(file_path) as f:
        header_line_1 = f.readline()
        header_line_2 = f.readline()
    return "Ticker" in header_line_2 or "Price" in header_line_1


def _load_multi_asset(file_path: str) -> dict[str, pd.DataFrame]:
    full_data = pd.read_csv(file_path, header=[0, 1], index_col=0)
    full_data.index.name = "date"
    out = {}
    for ticker in full_data.columns.get_level_values(1).unique().tolist():
        try:
            df = pd.DataFrame(
                {
                    col: full_data[(col, ticker)]
                    for col in ("Open", "High", "Low", "Close", "Volume")
                }
            )
        except KeyError:
            continue
        df = df.apply(pd.to_numeric, errors="coerce").dropna()
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, utc=True)
        df.index = pd.DatetimeIndex(df.index).tz_localize(None)
        out[ticker] = df
    return out


def _load_single_asset(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    df.columns = [col.capitalize() for col in df.columns]
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], utc=True)
        df.set_index("Date", inplace=True)
    if isinstance(df.index, pd.DatetimeIndex):
        df.index = df.index.tz_localize(None)
    return df.dropna()


def load_assets(data_path: str) -> dict[str, dict]:
    """
    Loads every asset under ``data_path``, a CSV file or a directory of them.

    Returns ``{asset_name: {"data": DataFrame, "source": filename}}``. A
    single-asset file is named by the part of its filename before the first
    underscore, so ``TSLA_2024-10-01_2025-11-25.csv`` becomes ``TSLA``.
    """
    files = (
        sorted(glob.glob(os.path.join(data_path, "*.csv")))
        if os.path.isdir(data_path)
        else [data_path]
    )
    assets: dict[str, dict] = {}
    for file_path in files:
        source = os.path.basename(file_path)
        try:
            if _is_multi_asset_csv(file_path):
                for ticker, df in _load_multi_asset(file_path).items():
                    assets[ticker] = {"data": df, "source": source}
                    print(f"   Loaded {ticker} from {source}")
            else:
                name = Path(file_path).stem.split("_")[0]
                assets[name] = {"data": _load_single_asset(file_path), "source": source}
                print(f"   Loaded {name} from {source}")
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    return assets


def select_strategies(names: list[str] | None = None) -> list[RegisteredStrategy]:
    """Installed strategies the benchmark can run, optionally filtered by name."""
    discovery = discover_strategies()
    print_discovery_errors(discovery)

    chosen = [discovery.by_name(n) for n in names] if names else list(discovery.strategies.values())
    runnable = []
    for s in chosen:
        if s.data_assets != 1:
            print(f"Skipping {s.name}: it trades {s.data_assets} assets at once.")
        elif s.is_unconfigured_wrapper:
            print(f"Skipping {s.name}: a wrapper with no underlying_strategy set.")
        else:
            runnable.append(s)
    return runnable


def run_benchmark(
    data_path: str = DEFAULT_DATA,
    output_dir: str = DEFAULT_OUTPUT,
    strategy_names: list[str] | None = None,
) -> str | None:
    """Runs the benchmark and returns the path of the report it wrote."""
    strategies = select_strategies(strategy_names)
    if not strategies:
        print("No runnable strategies are installed.")
        return None

    print(f"Loading data from {data_path}...")
    assets = load_assets(data_path)
    if not assets:
        print(f"No data found at {data_path}.")
        return None

    results = []
    for asset_name, asset_info in assets.items():
        print(f"\n>>> Processing Asset: {asset_name} <<<")
        for s in strategies:
            data = asset_info["data"].copy()
            data.columns = [col.capitalize() for col in data.columns]
            try:
                bt = Backtest(data, s.cls, cash=CASH, commission=ibkr_tiered_commission)  # ty:ignore[invalid-argument-type]
                start = time.time()
                stats = bt.run()
                runtime = time.time() - start
            except Exception as e:
                print(f"   Error running {s.name} on {asset_name}: {e}")
                continue

            results.append(
                {
                    "Asset": asset_name,
                    "Strategy": s.name,
                    "Return [%]": stats["Return [%]"],
                    "Sharpe Ratio": stats["Sharpe Ratio"],
                    "Max. Drawdown [%]": stats["Max. Drawdown [%]"],
                    "Win Rate [%]": stats["Win Rate [%]"],
                    "# Trades": stats["# Trades"],
                    "Runtime [s]": round(runtime, 4),
                    "Source": asset_info["source"],
                }
            )
            print(f"   Finished: {s.name} (Runtime: {runtime:.4f}s)")

    if not results:
        print("No results generated.")
        return None

    return write_report(results, strategies, output_dir)


def write_report(results: list[dict], strategies: list[RegisteredStrategy], output_dir: str) -> str:
    print("\n--- Generating Consolidated Benchmark Report ---")
    results_df = pd.DataFrame(results)
    ran = set(results_df["Strategy"])

    os.makedirs(output_dir, exist_ok=True)
    now = datetime.now()
    report_path = os.path.join(
        output_dir, f"benchmark_report_multi_asset_{now.strftime('%Y%m%d_%H%M%S')}.md"
    )

    with open(report_path, "w") as f:
        f.write("# Multi-Asset Strategy Benchmark Report\n\n")
        f.write(f"**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## Strategies\n")
        f.write("| Strategy | Registered by | Class |\n")
        f.write("| :--- | :--- | :--- |\n")
        for s in sorted(strategies, key=lambda s: (s.distribution, s.name)):
            if s.name in ran:
                f.write(f"| `{s.name}` | {s.distribution} | `{s.module}.{s.cls.__qualname__}` |\n")
        f.write(
            f"\nEvery run: ${CASH:,} starting cash, IBKR tiered commission, each "
            "strategy's default parameters.\n\n"
        )

        f.write("## Performance Metrics by Asset\n\n")
        for asset in sorted(results_df["Asset"].unique()):
            f.write(f"### {asset}\n")
            asset_results = (
                results_df[results_df["Asset"] == asset]
                .sort_values(by="Sharpe Ratio", ascending=False)
                .round(2)
            )
            f.write(f"**Test Data Source:** `{asset_results['Source'].iloc[0]}`\n\n")
            f.write(asset_results.drop(columns=["Asset", "Source"]).to_markdown(index=False))
            f.write("\n\n")

    print(f"Benchmark report saved to {report_path}")
    return report_path


def build_parser(parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    parser = parser or argparse.ArgumentParser(description="Benchmark installed strategies.")
    parser.add_argument(
        "--data",
        default=DEFAULT_DATA,
        help=f"CSV file or directory of CSV files, relative to the current directory "
        f"(default: {DEFAULT_DATA}).",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT,
        help=f"Where to write the report (default: {DEFAULT_OUTPUT}).",
    )
    parser.add_argument(
        "--strategies",
        nargs="+",
        metavar="NAME",
        help="Only run these strategies. Default: every installed strategy.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    run_benchmark(data_path=args.data, output_dir=args.output_dir, strategy_names=args.strategies)


if __name__ == "__main__":
    main()
