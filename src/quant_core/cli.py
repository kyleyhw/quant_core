"""The ``qc`` command-line interface.

Built-in commands cover backtesting, benchmarking, walk-forward validation, data
download, the dashboard and listing installed strategies. Installed packages add more through the
``quant_core.commands`` entry-point group; see :mod:`quant_core.registry`.
"""

import argparse
import sys

from quant_core import __version__, data_downloader
from quant_core.backtest import benchmark, run_backtest, walkforward
from quant_core.registry import discover_strategies, register_plugin_commands
from quant_core.service import DEFAULT_DATA_DIR


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
        "--output-dir",
        args.output_dir,
    ]
    if args.start:
        argv += ["--start", args.start]
    if args.end:
        argv += ["--end", args.end]
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
    from quant_core.web import server

    if args.export:
        server.main_export(args.export, args.data_dir)
        return
    try:
        server.serve(args.host, args.port, args.data_dir, open_browser=not args.no_browser)
    except OSError as exc:
        sys.exit(f"Could not start the dashboard on {args.host}:{args.port}: {exc}")


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
    p.add_argument(
        "--start", help="First date to backtest, YYYY-MM-DD; also where a ticker download starts."
    )
    p.add_argument(
        "--end", help="Last date to backtest, YYYY-MM-DD; also where a ticker download ends."
    )
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

    p = subparsers.add_parser(
        "walkforward", help="Test a strategy on data it was not fitted to, fold by fold."
    )
    walkforward.build_parser(p)
    p.set_defaults(func=walkforward.main)

    p = subparsers.add_parser("download", help="Download historical market data.")
    p.add_argument("--tickers", nargs="+", required=True, help="Tickers to download.")
    p.add_argument("--start", required=True, help="Start date, YYYY-MM-DD.")
    p.add_argument("--end", required=True, help="End date, YYYY-MM-DD.")
    p.add_argument("--output", default="data", help="Directory to save into.")
    p.add_argument("--force", action="store_true", help="Download even if a file exists.")
    p.set_defaults(func=handle_download)

    p = subparsers.add_parser("strategies", help="List installed strategies and where from.")
    p.set_defaults(func=handle_strategies)

    p = subparsers.add_parser("dashboard", help="Open the dashboard in a browser.")
    p.add_argument("--port", type=int, default=8501, help="Port to serve on (default: 8501).")
    p.add_argument("--host", default="127.0.0.1", help="Address to bind (default: 127.0.0.1).")
    p.add_argument(
        "--data-dir",
        default=str(DEFAULT_DATA_DIR),
        help=f"Folder of price CSV files (default: {DEFAULT_DATA_DIR}).",
    )
    p.add_argument("--no-browser", action="store_true", help="Do not open a browser.")
    p.add_argument(
        "--export",
        metavar="DIR",
        help="Write a static copy with every default run precomputed, instead of serving.",
    )
    p.set_defaults(func=handle_dashboard)

    for warning in register_plugin_commands(subparsers):
        print(f"warning: {warning}", file=sys.stderr)

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
