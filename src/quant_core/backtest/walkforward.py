"""``qc walkforward``: test a strategy on data it was not fitted to. See
:mod:`quant_core.validation` for the method."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from quant_core import service
from quant_core.commission_models import COMMISSION_MODELS
from quant_core.registry import discover_strategies
from quant_core.validation import TRADING_DAYS, to_markdown, walk_forward

DEFAULT_OUTPUT = "reports"


def parse_grid(items: list[str]) -> dict[str, list]:
    """``fast_ma_period=5,10,20`` becomes ``{"fast_ma_period": [5, 10, 20]}``."""
    grid: dict[str, list] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"--grid expects NAME=V1,V2,...; got {item!r}")
        name, raw = item.split("=", 1)
        values = []
        for part in raw.split(","):
            part = part.strip()
            try:
                values.append(ast.literal_eval(part))
            except (ValueError, SyntaxError):
                values.append(part)
        grid[name.strip()] = values
    return grid


def build_parser(p: argparse.ArgumentParser) -> argparse.ArgumentParser:
    p.add_argument("--strategy", required=True, help="Strategy name, as shown by `qc strategies`.")
    p.add_argument(
        "--data",
        nargs="+",
        required=True,
        help="Ticker(s) with a file in --data-dir, or tickers to download. Pairs take two.",
    )
    p.add_argument("--data-dir", default=str(service.DEFAULT_DATA_DIR), help="Price files.")
    p.add_argument("--start", help="First date of the history to use, YYYY-MM-DD.")
    p.add_argument("--end", help="Last date of the history to use, YYYY-MM-DD.")
    p.add_argument(
        "--train",
        type=int,
        default=3 * TRADING_DAYS,
        help="Training window in bars (default: 756, about three years).",
    )
    p.add_argument(
        "--test",
        type=int,
        default=TRADING_DAYS,
        help="Test window in bars (default: 252, about one year).",
    )
    p.add_argument("--step", type=int, help="Bars between folds (default: the test window).")
    p.add_argument("--anchored", action="store_true", help="Train from the first bar every fold.")
    p.add_argument(
        "--grid",
        action="append",
        default=[],
        metavar="NAME=V1,V2",
        help="A parameter to search on each training window. Repeatable.",
    )
    p.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Fix a parameter for every run. Repeatable.",
    )
    p.add_argument(
        "--maximize", default="Sharpe Ratio", help="Statistic the grid search maximises."
    )
    p.add_argument("--warmup", type=int, default=0, help="Bars run before each test window.")
    p.add_argument("--cash", type=float, default=service.DEFAULT_CASH, help="Starting cash.")
    p.add_argument(
        "--commission",
        default=service.DEFAULT_COMMISSION,
        choices=list(COMMISSION_MODELS),
        help="Commission model.",
    )
    p.add_argument("--underlying", help="Underlying strategy, for a wrapper strategy.")
    p.add_argument("--output-dir", default=DEFAULT_OUTPUT, help="Where to write the report.")
    return p


def main(args: argparse.Namespace) -> None:
    from quant_core.backtest.run_backtest import parse_params

    discovery = discover_strategies()
    try:
        registered = discovery.by_name(args.strategy)
    except KeyError as exc:
        sys.exit(str(exc.args[0]))
    cls = registered.cls
    if registered.is_unconfigured_wrapper:
        if not args.underlying:
            sys.exit(f"{args.strategy} wraps another strategy; pass --underlying.")
        cls = type(
            args.strategy, (cls,), {"underlying_strategy": discovery.by_name(args.underlying).cls}
        )
    if len(args.data) != registered.data_assets:
        sys.exit(f"{args.strategy} trades {registered.data_assets} asset(s); got {len(args.data)}.")
    try:
        frames = [service.load_prices(a, args.data_dir, args.start, args.end)[0] for a in args.data]
        grid = parse_grid(args.grid)
        fixed = parse_params(args.param)
    except (service.RunError, ValueError) as exc:
        sys.exit(str(exc))
    data = service._merge_pair(*frames) if len(frames) == 2 else frames[0]

    try:
        result = walk_forward(
            data,
            cls,
            train_bars=args.train,
            test_bars=args.test,
            step_bars=args.step,
            anchored=args.anchored,
            param_grid=grid or None,
            maximize=args.maximize,
            params=fixed,
            warmup_bars=args.warmup,
            cash=args.cash,
            commission=COMMISSION_MODELS[args.commission],
        )
    except ValueError as exc:
        sys.exit(str(exc))

    assets = "-".join(a.upper() for a in args.data)
    setup = {
        "Strategy": args.strategy + (f" over {args.underlying}" if args.underlying else ""),
        "Data": f"{assets}, {data.index[0]:%Y-%m-%d} to {data.index[-1]:%Y-%m-%d}",
        "Windows": f"train {args.train} bars, test {args.test} bars, step {args.step or args.test}"
        + (", anchored" if args.anchored else ", rolling"),
        "Parameters": (
            "searched on each training window: "
            + "; ".join(f"{k} in {v}" for k, v in grid.items())
            + f", maximising {args.maximize}"
            if grid
            else "fixed: " + (", ".join(f"{k}={v}" for k, v in fixed.items()) or "defaults")
        ),
        "Costs": f"{args.commission}, ${args.cash:,.0f} starting cash",
    }
    report = to_markdown(result, f"{args.strategy} on {assets}", setup)
    print(report)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    stem = out / f"walkforward_{args.strategy}_{assets}_{stamp}"
    stem.with_suffix(".md").write_text(report)
    stem.with_suffix(".json").write_text(
        json.dumps(
            {
                "setup": setup,
                "summary": result.summary,
                "folds": [asdict(f) for f in result.folds],
            },
            indent=1,
            default=str,
        )
    )
    print(f"Report written to {stem}.md")
