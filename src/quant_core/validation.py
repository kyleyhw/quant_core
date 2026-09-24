"""
Walk-forward validation: does a strategy hold up on data it was not fitted to?

The history is cut into folds. Each fold has a training window followed by a test
window that starts where training ends. If a parameter grid is given, the grid is
searched on the training window alone and the best parameters are carried into
the test window unchanged; without a grid the strategy's own parameters are used
throughout, which measures a strategy that was tuned elsewhere on each later
stretch of history. The test windows never overlap, so joining them end to end
gives an out-of-sample equity curve that no parameter choice has seen.

Folds roll forward by ``step_bars`` (default: one test window). An anchored walk
keeps every training window starting at the first bar, so it grows each fold. The
last test window may be shorter than the rest, so the latest data is tested too.

Statistics here are computed from equity curves by one formula for every window,
so in-sample and out-of-sample figures compare like with like. The Sharpe ratio
is the annualised mean daily return over its standard deviation, with no
risk-free rate; it can differ slightly from the figure ``backtesting.py`` prints.
"""

from __future__ import annotations

import contextlib
import io
import math
import warnings
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, cast

import pandas as pd
from backtesting import Backtest, Strategy

TRADING_DAYS = 252


@dataclass
class Fold:
    """One training window and the test window after it."""

    index: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    params: dict[str, Any]
    train: dict[str, float | None]
    test: dict[str, float | None]
    hold: dict[str, float | None]


@dataclass
class WalkForwardResult:
    folds: list[Fold]
    oos_equity: pd.Series
    summary: dict[str, Any] = field(default_factory=dict)


def segment_stats(equity: pd.Series, trades: pd.DataFrame | None = None) -> dict[str, float | None]:
    """Return, CAGR, volatility, Sharpe and drawdown of one stretch of an equity curve."""
    equity = equity.dropna()
    if len(equity) < 2:
        return {k: None for k in ("return", "cagr", "volatility", "sharpe", "max_drawdown")} | {
            "trades": 0,
            "win_rate": None,
        }
    daily = equity.pct_change().dropna()
    total = equity.iloc[-1] / equity.iloc[0] - 1
    years = len(daily) / TRADING_DAYS
    cagr = (1 + total) ** (1 / years) - 1 if years > 0 and total > -1 else None
    sd = daily.std()
    sharpe = (daily.mean() / sd) * math.sqrt(TRADING_DAYS) if sd and sd > 0 else None
    drawdown = (equity / equity.cummax() - 1).min()
    n = 0 if trades is None else len(trades)
    win = float((trades["PnL"] > 0).mean() * 100) if trades is not None and n else None
    return {
        "return": float(total * 100),
        "cagr": None if cagr is None else float(cagr * 100),
        "volatility": float(sd * math.sqrt(TRADING_DAYS) * 100) if sd == sd else None,
        "sharpe": None if sharpe is None else float(sharpe),
        "max_drawdown": float(drawdown * 100),
        "trades": n,
        "win_rate": win,
    }


def _quiet(fn: Callable[[], Any]) -> Any:
    with warnings.catch_warnings(), contextlib.redirect_stdout(io.StringIO()):
        warnings.simplefilter("ignore")
        return fn()


def _run(
    data: pd.DataFrame, cls: type[Strategy], cash: float, commission: Any, params: dict
) -> pd.Series:
    return _quiet(lambda: Backtest(data, cls, cash=cash, commission=commission).run(**params))


def _optimise(
    data: pd.DataFrame,
    cls: type[Strategy],
    cash: float,
    commission: Any,
    grid: dict[str, list],
    maximize: str,
    constraint: Callable[[Any], bool] | None,
) -> tuple[dict[str, Any], pd.Series]:
    def go() -> Any:
        # Typed as Any: optimize() takes the grid as keyword arguments.
        bt = cast(Any, Backtest(data, cls, cash=cash, commission=commission))
        return bt.optimize(**grid, maximize=maximize, constraint=constraint)

    stats = _quiet(go)
    best = {name: getattr(stats._strategy, name) for name in grid}
    return best, stats


def _window(stats: pd.Series, start: pd.Timestamp) -> tuple[pd.Series, pd.DataFrame]:
    """The equity and closed trades of a run from ``start`` on (after any warm-up)."""
    equity = stats["_equity_curve"]["Equity"]
    trades = stats["_trades"]
    equity = equity.loc[start:]
    if len(trades):
        trades = trades[pd.to_datetime(trades["ExitTime"]) >= start]
    return equity, trades


def _hold(close: pd.Series) -> dict[str, float | None]:
    return segment_stats(close)


def walk_forward(
    data: pd.DataFrame,
    strategy: type[Strategy],
    *,
    train_bars: int = 3 * TRADING_DAYS,
    test_bars: int = TRADING_DAYS,
    step_bars: int | None = None,
    anchored: bool = False,
    param_grid: dict[str, list] | None = None,
    maximize: str = "Sharpe Ratio",
    constraint: Callable[[Any], bool] | None = None,
    params: dict[str, Any] | None = None,
    warmup_bars: int = 0,
    cash: float = 10_000,
    commission: Any = 0.0,
    score_training: bool = True,
) -> WalkForwardResult:
    """
    Walks ``strategy`` forward through ``data``.

    ``params`` fixes parameters for every run. ``param_grid`` maps parameter
    names to candidate values searched on each training window, scored by the
    ``backtesting.py`` statistic named in ``maximize``. ``warmup_bars`` runs
    that many bars before each test window so indicators are primed; their
    profit and trades are left out of the test figures. With fixed parameters,
    ``score_training=False`` skips the training runs, which then only mark where
    each fold starts.
    """
    if train_bars < 20 or test_bars < 5:
        raise ValueError("Use at least 20 training bars and 5 test bars.")
    step = step_bars or test_bars
    n = len(data)
    if train_bars + test_bars > n:
        raise ValueError(
            f"{n} bars is too short for one fold of {train_bars} training "
            f"and {test_bars} test bars."
        )
    fixed = dict(params or {})
    folds: list[Fold] = []
    pieces: list[pd.Series] = []
    index = data.index

    # The last fold may have a shorter test window, so the latest data is tested
    # too, as long as it holds a quarter of a window.
    min_test = max(5, test_bars // 4)
    start = 0
    while start + train_bars + min_test <= n:
        train_lo = 0 if anchored else start
        train_hi = start + train_bars
        test_hi = min(train_hi + test_bars, n)
        train = data.iloc[train_lo:train_hi]
        if param_grid:
            chosen, train_stats = _optimise(
                train, strategy, cash, commission, param_grid, maximize, constraint
            )
            chosen = {**fixed, **chosen}
        else:
            chosen = fixed
            train_stats = (
                _run(train, strategy, cash, commission, chosen) if score_training else None
            )
        test_from = index[train_hi]
        test_slice = data.iloc[max(0, train_hi - warmup_bars) : test_hi]
        test_stats = _run(test_slice, strategy, cash, commission, chosen)
        equity, trades = _window(test_stats, test_from)
        pieces.append(equity / equity.iloc[0])
        folds.append(
            Fold(
                index=len(folds) + 1,
                train_start=f"{index[train_lo]:%Y-%m-%d}",
                train_end=f"{index[train_hi - 1]:%Y-%m-%d}",
                test_start=f"{test_from:%Y-%m-%d}",
                test_end=f"{index[test_hi - 1]:%Y-%m-%d}",
                params=chosen,
                train=(
                    segment_stats(train_stats["_equity_curve"]["Equity"], train_stats["_trades"])
                    if train_stats is not None
                    else segment_stats(pd.Series(dtype=float))
                ),
                test=segment_stats(equity, trades),
                hold=_hold(data["Close"].iloc[train_hi:test_hi]),
            )
        )
        start += step

    # Join the test windows into one curve, each continuing from where the last
    # ended. Windows do not share a bar, so every bar appears once.
    joined, level = [], 1.0
    for piece in pieces:
        scaled = piece * level
        joined.append(scaled)
        level = float(scaled.iloc[-1])
    oos = pd.concat(joined) * cash if joined else pd.Series(dtype=float)
    oos = oos[~oos.index.duplicated()]

    return WalkForwardResult(folds=folds, oos_equity=oos, summary=_summarise(folds, oos, data))


def _mean(values: list[float | None]) -> float | None:
    xs = [v for v in values if v is not None]
    return sum(xs) / len(xs) if xs else None


def _summarise(folds: list[Fold], oos: pd.Series, data: pd.DataFrame) -> dict[str, Any]:
    if not folds:
        return {}
    first, last = folds[0].test_start, folds[-1].test_end
    stats = segment_stats(oos)
    is_cagr = _mean([f.train["cagr"] for f in folds])
    oos_cagr = stats["cagr"]
    efficiency = (
        oos_cagr / is_cagr if oos_cagr is not None and is_cagr is not None and is_cagr > 0 else None
    )
    return {
        "folds": len(folds),
        "oos_start": first,
        "oos_end": last,
        "oos": stats,
        "oos_trades": sum(f.test["trades"] or 0 for f in folds),
        "hold": segment_stats(data["Close"].loc[first:last]),
        "mean_is_sharpe": _mean([f.train["sharpe"] for f in folds]),
        "mean_oos_sharpe": _mean([f.test["sharpe"] for f in folds]),
        "mean_is_cagr": is_cagr,
        "efficiency": efficiency,
        "profitable_folds": sum(1 for f in folds if (f.test["return"] or 0) > 0),
        "beat_hold_folds": sum(
            1 for f in folds if (f.test["return"] or 0) > (f.hold["return"] or 0)
        ),
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def _f(x: float | None, spec: str = ".2f", suffix: str = "") -> str:
    return "–" if x is None else f"{x:{spec}}{suffix}"


def to_markdown(result: WalkForwardResult, title: str, setup: dict[str, Any]) -> str:
    """A readable report of a walk-forward run."""
    s = result.summary
    lines = [f"# Walk-forward: {title}", ""]
    lines += [f"- **{k}:** {v}" for k, v in setup.items()]
    lines.append("")
    if not s:
        return "\n".join(lines + ["No complete fold fits in the data.", ""])
    o, h = s["oos"], s["hold"]
    lines += [
        "## Out of sample, all test windows joined",
        "",
        f"{s['oos_start']} to {s['oos_end']}, {s['folds']} folds, {s['oos_trades']} trades.",
        "",
        "| | Strategy | Buy and hold |",
        "| :--- | ---: | ---: |",
        f"| Return | {_f(o['return'], '.1f', '%')} | {_f(h['return'], '.1f', '%')} |",
        f"| CAGR | {_f(o['cagr'], '.1f', '%')} | {_f(h['cagr'], '.1f', '%')} |",
        f"| Sharpe | {_f(o['sharpe'])} | {_f(h['sharpe'])} |",
        f"| Max drawdown | {_f(o['max_drawdown'], '.1f', '%')} "
        f"| {_f(h['max_drawdown'], '.1f', '%')} |",
        "",
        f"- Mean Sharpe in training {_f(s['mean_is_sharpe'])}, "
        f"in testing {_f(s['mean_oos_sharpe'])}.",
        f"- Walk-forward efficiency (test CAGR over mean training CAGR): {_f(s['efficiency'])}.",
        f"- Profitable test windows: {s['profitable_folds']} of {s['folds']}; "
        f"windows that beat buy and hold: {s['beat_hold_folds']} of {s['folds']}.",
        "",
        "## Folds",
        "",
        "| # | Train | Test | Parameters | Train Sharpe | Test return | Test Sharpe "
        "| Test max DD | Trades | Hold return |",
        "| ---: | :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for f in result.folds:
        params = ", ".join(f"{k}={v}" for k, v in f.params.items()) or "defaults"
        lines.append(
            f"| {f.index} | {f.train_start} to {f.train_end} | {f.test_start} to {f.test_end} "
            f"| {params} | {_f(f.train['sharpe'])} | {_f(f.test['return'], '.1f', '%')} "
            f"| {_f(f.test['sharpe'])} | {_f(f.test['max_drawdown'], '.1f', '%')} "
            f"| {f.test['trades']} | {_f(f.hold['return'], '.1f', '%')} |"
        )
    lines.append("")
    return "\n".join(lines)
