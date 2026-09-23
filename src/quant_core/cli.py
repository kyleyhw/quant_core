"""The ``qc`` command-line interface.

Built-in commands cover backtesting, benchmarking, data download, the dashboard
and listing installed strategies. Installed packages add more through the
``quant_core.commands`` entry-point group; see :mod:`quant_core.registry`.
"""

import argparse
import subprocess
import sys
from pathlib import Path

from quant_core import __version__, data_downloader
from quant_core.backtest import benchmark, run_backtest
from quant_core.registry import discover_strategies, register_plugin_commands


def handle_backtest(args: argparse.Namespace) -> None:
    argv = [
        "--strategy",
        args.strategy,
        "--data",
        *args.data,
        "--cash",
        str(args.cash),
        "--commission",
        args.commission,
        "--start",
        args.start,
        "--end",
        args.end,
        "--output-dir",
        args.output_dir,
    ]
    if args.underlying:
        argv += ["--underlying", args.underlying]
    for param in args.param:
        argv += ["--param", param]
    run_backtest.main(argv)


def handle_benchmark(args: argparse.Namespace) -> None:
    benchmark.run_benchmark(
        data_path=args.data, output_dir=args.output_dir, strategy_names=args.strategies
    )


def handle_download(args: argparse.Namespace) -> None:
    argv = ["--tickers", *args.tickers, "--start", args.start, "--end", args.end]
    argv += ["--output", args.output]
    if args.force:
        argv.append("--force")
    data_downloader.main(argv)


def handle_strategies(args: argparse.Namespace) -> None:
    discovery = discover_strategies()
    if discovery.strategies:
        width = max(len(n) for n in discovery.strategies)
        for name, s in sorted(discovery.strategies.items()):
            print(f"{name:<{width}}  {s.distribution:<20}  {s.module}.{s.cls.__qualname__}")
    else:
        print("No strategies are installed.")
    for message in discovery.errors:
        print(f"warning: {message}", file=sys.stderr)
    if discovery.errors:
        sys.exit(1)


def handle_dashboard(args: argparse.Namespace) -> None:
    app = Path(__file__).parent / "dashboard" / "app.py"
    sys.exit(subprocess.call([sys.executable, "-m", "streamlit", "run", str(app), *args.extra]))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qc", description="quant-core: the algorithmic trading platform's command line."
    )
    parser.add_argument("--version", action="version", version=f"quant-core {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    p = subparsers.add_parser("backtest", help="Run one installed strategy.")
    p.add_argument("--strategy", required=True, help="Strategy name, as shown by `qc strategies`.")
    p.add_argument(
        "--data",
        nargs="+",
        required=True,
        help="CSV file(s) or ticker(s). Two-asset strategies take two.",
    )
    p.add_argument("--cash", type=int, default=10000, help="Starting cash.")
    p.add_argument("--commission", default="IBKR Tiered", help="Commission model name.")
    p.add_argument("--start", default="2020-01-01", help="Start date when fetching a ticker.")
    p.add_argument("--end", default="2023-12-31", help="End date when fetching a ticker.")
    p.add_argument("--underlying", help="Underlying strategy name, for a wrapper strategy.")
    p.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override a strategy parameter. Repeatable.",
    )
    p.add_argument("--output-dir", default=run_backtest.DEFAULT_OUTPUT, help="Report directory.")
    p.set_defaults(func=handle_backtest)

    p = subparsers.add_parser("benchmark", help="Run every installed strategy across a dataset.")
    benchmark.build_parser(p)
    p.set_defaults(func=handle_benchmark)

    p = subparsers.add_parser("download", help="Download historical market data.")
    p.add_argument("--tickers", nargs="+", required=True, help="Tickers to download.")
    p.add_argument("--start", required=True, help="Start date, YYYY-MM-DD.")
    p.add_argument("--end", required=True, help="End date, YYYY-MM-DD.")
    p.add_argument("--output", default="data", help="Directory to save into.")
    p.add_argument("--force", action="store_true", help="Download even if a file exists.")
    p.set_defaults(func=handle_download)

    p = subparsers.add_parser("strategies", help="List installed strategies and where from.")
    p.set_defaults(func=handle_strategies)

    p = subparsers.add_parser("dashboard", help="Launch the Streamlit dashboard.")
    p.add_argument("extra", nargs=argparse.REMAINDER, help="Passed through to streamlit run.")
    p.set_defaults(func=handle_dashboard)

    for warning in register_plugin_commands(subparsers):
        print(f"warning: {warning}", file=sys.stderr)

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
