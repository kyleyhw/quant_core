"""
The engine calls behind the dashboard, as plain Python.

This module lists what can be run (strategies and their parameters, local data,
commission models) and runs one backtest into a JSON-ready result: headline
figures, grouped metrics, the equity and price series, the trade list, a short
written summary, and the ``qc backtest`` command that reproduces the run. The
dashboard's web server and its static export both call it; nothing here knows
about HTTP.
"""

from __future__ import annotations

import contextlib
import io
import math
import re
import shlex
import warnings
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from backtesting import Backtest, Strategy

from quant_core.commission_models import COMMISSION_MODELS
from quant_core.registry import RegisteredStrategy, discover_strategies
from quant_core.strategies.base_strategy import BaseStrategy
from quant_core.strategies.buy_and_hold import BuyAndHoldStrategy

DEFAULT_DATA_DIR = Path("data") / "benchmark"
DEFAULT_CASH = 10_000
DEFAULT_COMMISSION = "IBKR Tiered"

# Class attributes that configure the engine rather than the signal.
_NOT_PARAMS = {"data_assets", "underlying_strategy"}
_PARAM_TYPES = (bool, int, float, str)
# A ticker also names the file it is downloaded to, so it is kept to these.
_TICKER = re.compile(r"[A-Z0-9^][A-Z0-9.\-^=]{0,14}")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")

# Named backtest windows, ending on the last bar of the data. The dashboard offers
# them as presets and the static export precomputes some of them.
PERIODS: list[dict[str, Any]] = [
    {"id": "all", "label": "Full history"},
    {"id": "5y", "label": "Last 5 years", "years": 5},
    {"id": "3y", "label": "Last 3 years", "years": 3},
    {"id": "1y", "label": "Last year", "years": 1},
    {"id": "ytd", "label": "Year to date"},
]
# Where a download of a ticker with no local file starts when no start is given.
DOWNLOAD_FROM = "2015-01-01"


class RunError(ValueError):
    """A backtest request that cannot run, with a message fit to show the user."""


# ---------------------------------------------------------------------------
# What can be run
# ---------------------------------------------------------------------------
def strategy_params(cls: type[Strategy]) -> list[dict[str, Any]]:
    """
    The tunable parameters of a strategy class, most specific first.

    A parameter is a public class attribute holding a bool, int, float or str,
    declared anywhere between the class and ``backtesting.Strategy``. Those
    declared on ``BaseStrategy`` are grouped as ``risk``; the rest as
    ``strategy``.
    """
    seen: dict[str, dict[str, Any]] = {}
    for klass in cls.__mro__:
        if klass is Strategy or not issubclass(klass, Strategy):
            continue
        group = "risk" if klass is BaseStrategy else "strategy"
        for name, value in vars(klass).items():
            if name.startswith("_") or name in _NOT_PARAMS or name in seen:
                continue
            if isinstance(value, _PARAM_TYPES):
                kind = type(value).__name__
                seen[name] = {
                    "name": name,
                    "default": getattr(cls, name),
                    "kind": kind,
                    "group": group,
                }
    return sorted(seen.values(), key=lambda p: p["group"] == "risk")


def _describe(s: RegisteredStrategy) -> dict[str, Any]:
    doc = (s.cls.__doc__ or "").strip()
    return {
        "name": s.name,
        "label": _label(s.name),
        "source": s.distribution,
        "data_assets": s.data_assets,
        "needs_underlying": s.is_unconfigured_wrapper,
        "summary": doc.split("\n\n")[0].replace("\n", " ").strip() if doc else "",
        "params": strategy_params(s.cls),
    }


def _label(name: str) -> str:
    """A display name: ``BollingerBandsStrategy`` becomes ``Bollinger Bands``."""
    base = name.removesuffix("Strategy") or name
    words = re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z]*|\d+", base)
    small = {"And", "Or", "Of", "On", "The"}
    words = [w.lower() if i and w in small else w for i, w in enumerate(words)]
    return " ".join(words) if words else name


def list_strategies() -> tuple[list[dict[str, Any]], list[str]]:
    """Installed strategies, described for the dashboard, and any discovery errors."""
    discovery = discover_strategies()
    described = [_describe(s) for _, s in sorted(discovery.strategies.items())]
    return described, list(discovery.errors)


def list_assets(data_dir: Path | str = DEFAULT_DATA_DIR) -> dict[str, Path]:
    """
    Single-asset CSV files in ``data_dir``, keyed by ticker.

    The ticker is the file name up to the first underscore, as ``qc download``
    writes it (``MSFT_2024-10-01_2025-11-25.csv``). Where two files share a
    ticker the last in sorted order, normally the most recent, wins.
    """
    folder = Path(data_dir)
    if not folder.is_dir():
        return {}
    return {p.name.split("_")[0].upper(): p for p in sorted(folder.glob("*.csv"))}


def asset_range(path: Path) -> tuple[str, str]:
    """First and last dates in a price file, read from its first and last rows."""
    with open(path, "rb") as f:
        f.readline()
        first = f.readline().decode().split(",", 1)[0][:10]
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - 4096))
        tail = [ln for ln in f.read().decode(errors="ignore").splitlines() if ln.strip()]
    last = tail[-1].split(",", 1)[0][:10]
    return first, last


def resolve_period(period: str, first: str, last: str) -> tuple[str, str]:
    """
    The start and end dates of a named period for data running ``first`` to
    ``last``. A period longer than the data starts at ``first``.
    """
    end, earliest = date.fromisoformat(last), date.fromisoformat(first)
    if period == "all":
        start = earliest
    elif period == "ytd":
        start = date(end.year, 1, 1)
    else:
        spec = next((p for p in PERIODS if p["id"] == period and "years" in p), None)
        if spec is None:
            raise RunError(f"Unknown period {period!r}.")
        year = end.year - int(spec["years"])
        # 29 February has no counterpart in most years; use the 28th.
        start = end.replace(year=year, day=min(end.day, 28 if end.month == 2 else end.day))
        start += timedelta(days=1)
    return max(start, earliest).isoformat(), end.isoformat()


def meta(data_dir: Path | str = DEFAULT_DATA_DIR) -> dict[str, Any]:
    """Everything the dashboard needs to build its controls."""
    strategies, errors = list_strategies()
    assets = list_assets(data_dir)
    ranges = {}
    for ticker, path in assets.items():
        try:
            ranges[ticker] = asset_range(path)
        except (OSError, IndexError, UnicodeDecodeError):
            continue
    return {
        "strategies": strategies,
        "assets": sorted(assets),
        "asset_ranges": ranges,
        "periods": PERIODS,
        "download_from": DOWNLOAD_FROM,
        "commissions": list(COMMISSION_MODELS),
        "defaults": {
            "strategy": _default_strategy(strategies),
            "asset": _default_asset(sorted(assets)),
            "commission": DEFAULT_COMMISSION,
            "cash": DEFAULT_CASH,
            "period": "all",
        },
        "data_dir": str(data_dir),
        "errors": errors,
    }


def _default_strategy(strategies: list[dict[str, Any]]) -> str | None:
    runnable = [
        s["name"] for s in strategies if s["data_assets"] == 1 and not s["needs_underlying"]
    ]
    for preferred in ("BollingerBandsStrategy", "SimpleMACrossover"):
        if preferred in runnable:
            return preferred
    return runnable[0] if runnable else None


def _default_asset(assets: list[str]) -> str | None:
    for preferred in ("MSFT", "SPY"):
        if preferred in assets:
            return preferred
    return assets[0] if assets else None


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def _normalise(df: pd.DataFrame) -> pd.DataFrame:
    idx = pd.to_datetime(df.index, utc=True)
    df.index = pd.DatetimeIndex(idx).tz_localize(None)
    df.index.name = "Date"
    df.columns = [str(c).capitalize() for c in df.columns]
    for col in ("Open", "High", "Low", "Close", "Volume"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna()


def load_prices(
    asset: str,
    data_dir: Path | str = DEFAULT_DATA_DIR,
    start: str | None = None,
    end: str | None = None,
) -> tuple[pd.DataFrame, str]:
    """
    Daily prices for ``asset`` from ``start`` to ``end`` inclusive, and where
    they came from. Either date may be left out to run to that end of the data.

    A ticker with a file in ``data_dir`` is read from it. Any other ticker is
    downloaded, from ``DOWNLOAD_FROM`` and up to today unless the dates say
    otherwise.
    """
    local = list_assets(data_dir)
    key = asset.strip().upper()
    if not _TICKER.fullmatch(key):
        raise RunError(f"{asset!r} is not a ticker. Use letters, digits, '.', '-', '^' or '='.")
    check_window(start, end)
    if key in local:
        df, source = _normalise(pd.read_csv(local[key], index_col=0)), str(local[key])
    else:
        from quant_core.data_loader import SmartLoader

        first = start or DOWNLOAD_FROM
        # The downloader's end date is exclusive; the window's is inclusive.
        stop = (date.fromisoformat(end) + timedelta(days=1)) if end else date.today()
        try:
            with SmartLoader(data_dir=str(data_dir)) as loader:
                df = _normalise(loader.load_data(key, first, stop.isoformat()))
        except Exception as exc:  # the downloader raises several kinds
            raise RunError(f"Could not download {key}: {exc}") from exc
        source = key
    window = df.loc[start:end] if (start or end) else df
    if window.empty:
        span = f"{df.index[0]:%Y-%m-%d} to {df.index[-1]:%Y-%m-%d}" if len(df) else "nothing"
        raise RunError(
            f"{key} has no prices between {start or 'the start'} and {end or 'the end'}; "
            f"its data covers {span}."
        )
    return window, source


def check_window(start: str | None, end: str | None) -> None:
    """Rejects malformed or reversed dates."""
    for label, value in (("start", start), ("end", end)):
        if value and not _DATE.fullmatch(value):
            raise RunError(f"The {label} date must be YYYY-MM-DD; got {value!r}.")
    if start and end and start >= end:
        raise RunError(f"The start date {start} must come before the end date {end}.")


def _merge_pair(first: pd.DataFrame, second: pd.DataFrame) -> pd.DataFrame:
    """Two assets side by side, as ``qc backtest`` merges them for a pairs strategy."""
    data = first.add_suffix("_1").merge(
        second.add_suffix("_2"), left_index=True, right_index=True, how="inner"
    )
    for col in ("Open", "High", "Low", "Close", "Volume"):
        data[col] = data[f"{col}_1"]
    return data


# ---------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------
def run_backtest(
    strategy: str,
    assets: list[str],
    *,
    commission: str = DEFAULT_COMMISSION,
    cash: float = DEFAULT_CASH,
    params: dict[str, Any] | None = None,
    underlying: str | None = None,
    data_dir: Path | str = DEFAULT_DATA_DIR,
    start: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    """
    Runs one backtest and returns it in the dashboard's result format.

    The result is compared against buying and holding the first asset with the
    same cash and commission model.
    """
    discovery = discover_strategies()
    try:
        registered = discovery.by_name(strategy)
    except KeyError as exc:
        raise RunError(str(exc.args[0])) from exc
    if commission not in COMMISSION_MODELS:
        raise RunError(f"Unknown commission model {commission!r}.")
    if not cash or cash <= 0:
        raise RunError("Starting cash must be positive.")

    cls: type[Strategy] = registered.cls
    if registered.is_unconfigured_wrapper:
        if not underlying:
            raise RunError(f"{strategy} wraps another strategy. Choose the one it wraps.")
        try:
            inner = discovery.by_name(underlying).cls
        except KeyError as exc:
            raise RunError(str(exc.args[0])) from exc
        cls = type(strategy, (cls,), {"underlying_strategy": inner})

    wanted = registered.data_assets
    assets = [a.strip().upper() for a in assets if a and a.strip()]
    if len(assets) != wanted:
        raise RunError(
            f"{strategy} trades {wanted} asset{'s' if wanted > 1 else ''}; got {len(assets)}."
        )

    frames, sources = [], []
    for asset in assets:
        df, source = load_prices(asset, data_dir, start, end)
        frames.append(df)
        sources.append(source)
    data = _merge_pair(*frames) if wanted == 2 else frames[0]
    if len(data) < 30:
        raise RunError(
            f"Only {len(data)} bars in this period; a backtest needs at least 30. "
            "Choose a longer period."
        )

    if params is not None and not isinstance(params, dict):
        raise RunError("Parameters must be an object of name and value.")
    known = {p["name"]: p for p in strategy_params(cls)}
    overrides = {}
    for key, value in (params or {}).items():
        if key not in known:
            raise RunError(f"{strategy} has no parameter {key!r}.")
        overrides[key] = _coerce(value, known[key])

    model = COMMISSION_MODELS[commission]
    stats = _run(data, cls, cash, model, overrides)
    hold = _run(frames[0], BuyAndHoldStrategy, cash, model, {})

    effective = {name: overrides.get(name, p["default"]) for name, p in known.items()}
    return _result(
        strategy=strategy,
        underlying=underlying if registered.is_unconfigured_wrapper else None,
        assets=assets,
        sources=sources,
        commission=commission,
        cash=cash,
        params=effective,
        overrides=overrides,
        start=start,
        end=end,
        data=data,
        stats=stats,
        hold=hold,
    )


def _coerce(value: Any, spec: dict[str, Any]) -> Any:
    kind = spec["kind"]
    try:
        if kind == "bool":
            if isinstance(value, str):
                return value.strip().lower() in ("1", "true", "yes", "on")
            return bool(value)
        if kind == "int":
            as_float = float(value)
            if not as_float.is_integer():
                raise ValueError
            return int(as_float)
        if kind == "float":
            return float(value)
        return str(value)
    except (TypeError, ValueError) as exc:
        raise RunError(
            f"{spec['name']} must be {'an' if kind == 'int' else 'a'} {kind}; got {value!r}."
        ) from exc


def _run(
    data: pd.DataFrame, cls: type[Strategy], cash: float, model: Any, params: dict
) -> pd.Series:
    # Configured exactly as `qc backtest` configures it, so the reproduce command
    # gives the same numbers. A trade still open on the last bar is not counted.
    with warnings.catch_warnings(), contextlib.redirect_stdout(io.StringIO()):
        warnings.simplefilter("ignore")
        try:
            return Backtest(data, cls, cash=cash, commission=model).run(**params)
        except Exception as exc:
            raise RunError(f"The backtest failed: {type(exc).__name__}: {exc}") from exc


# ---------------------------------------------------------------------------
# Result format
# ---------------------------------------------------------------------------
def _num(value: Any) -> float | None:
    """A finite float, or None for NaN, infinities and missing values."""
    if value is None:
        return None
    if isinstance(value, pd.Timedelta):
        return float(value.days)
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _commission_paid(stats: pd.Series) -> float:
    paid = _num(stats.get("Commissions [$]"))
    if paid is None:
        trades = stats["_trades"]
        paid = float(trades["Commission"].sum()) if "Commission" in trades else 0.0
    return paid


# (key in the result, label, stats field, unit). Units: pct, usd, ratio, count, days.
METRIC_GROUPS: list[tuple[str, list[tuple[str, str, str, str]]]] = [
    (
        "Returns",
        [
            ("return", "Total return", "Return [%]", "pct"),
            ("return_ann", "Annual return", "Return (Ann.) [%]", "pct"),
            ("cagr", "CAGR", "CAGR [%]", "pct"),
            ("equity_final", "Final equity", "Equity Final [$]", "usd"),
            ("equity_peak", "Peak equity", "Equity Peak [$]", "usd"),
        ],
    ),
    (
        "Risk",
        [
            ("volatility", "Volatility, annual", "Volatility (Ann.) [%]", "pct"),
            ("max_drawdown", "Max drawdown", "Max. Drawdown [%]", "pct"),
            ("avg_drawdown", "Average drawdown", "Avg. Drawdown [%]", "pct"),
            ("max_dd_duration", "Longest drawdown", "Max. Drawdown Duration", "days"),
            ("sharpe", "Sharpe ratio", "Sharpe Ratio", "ratio"),
            ("sortino", "Sortino ratio", "Sortino Ratio", "ratio"),
            ("calmar", "Calmar ratio", "Calmar Ratio", "ratio"),
        ],
    ),
    (
        "Trade quality",
        [
            ("trades", "Trades", "# Trades", "count"),
            ("win_rate", "Win rate", "Win Rate [%]", "pct"),
            ("best_trade", "Best trade", "Best Trade [%]", "pct"),
            ("worst_trade", "Worst trade", "Worst Trade [%]", "pct"),
            ("avg_trade", "Average trade", "Avg. Trade [%]", "pct"),
            ("profit_factor", "Profit factor", "Profit Factor", "ratio"),
            ("expectancy", "Expectancy", "Expectancy [%]", "pct"),
            ("sqn", "SQN", "SQN", "ratio"),
            ("avg_trade_duration", "Average holding time", "Avg. Trade Duration", "days"),
        ],
    ),
    (
        "Run details",
        [
            ("exposure", "Time in the market", "Exposure Time [%]", "pct"),
            ("commission_paid", "Commission paid", "", "usd"),
            ("duration", "Calendar span", "Duration", "days"),
        ],
    ),
]


def _metric(stats: pd.Series, key: str, field: str) -> float | None:
    if key == "commission_paid":
        return _commission_paid(stats)
    return _num(stats.get(field))


def _result(
    *,
    strategy: str,
    underlying: str | None,
    assets: list[str],
    sources: list[str],
    commission: str,
    cash: float,
    params: dict[str, Any],
    overrides: dict[str, Any],
    start: str | None,
    end: str | None,
    data: pd.DataFrame,
    stats: pd.Series,
    hold: pd.Series,
) -> dict[str, Any]:
    # backtesting.py measures trades, exposure and commission from closed trades.
    # Buy and hold never closes its one trade, so those read as zero; show none.
    hold_blind = {"trades", "exposure", "commission_paid"} if hold["_trades"].empty else set()
    groups, flat, flat_hold = [], {}, {}
    for title, rows in METRIC_GROUPS:
        out = []
        for key, label, field, unit in rows:
            value = _metric(stats, key, field)
            base = None if key in hold_blind else _metric(hold, key, field)
            flat[key], flat_hold[key] = value, base
            out.append({"key": key, "label": label, "unit": unit, "value": value, "hold": base})
        groups.append({"title": title, "rows": out})

    trades = []
    index = data.index
    for t in stats["_trades"].itertuples():
        entry, exit_ = str(t.EntryTime)[:10], str(t.ExitTime)[:10]
        trades.append(
            {
                "side": "long" if t.Size > 0 else "short",
                "size": int(abs(t.Size)),
                "entry": entry,
                "exit": exit_,
                "entry_bar": int(t.EntryBar),
                "exit_bar": int(t.ExitBar),
                "entry_price": round(float(t.EntryPrice), 4),
                "exit_price": round(float(t.ExitPrice), 4),
                "pnl": round(float(t.PnL), 2),
                "return_pct": round(float(t.ReturnPct) * 100, 3),
                "days": int((pd.Timestamp(t.ExitTime) - pd.Timestamp(t.EntryTime)).days),
                "commission": round(float(getattr(t, "Commission", 0.0) or 0.0), 2),
            }
        )

    equity = stats["_equity_curve"]["Equity"].reindex(index).ffill()
    hold_equity = hold["_equity_curve"]["Equity"].reindex(index).ffill()
    run = {
        "strategy": strategy,
        "label": _label(strategy),
        "underlying": underlying,
        "assets": assets,
        "sources": sources,
        "commission": commission,
        "cash": cash,
        "params": params,
        "first_date": index[0].date().isoformat(),
        "last_date": index[-1].date().isoformat(),
        "bars": len(index),
    }
    run["window"] = {"start": start, "end": end}
    run["command"] = reproduce_command(run, overrides, start, end)
    return {
        "run": run,
        "metrics": flat,
        "hold": flat_hold,
        "groups": groups,
        "series": {
            "dates": [d.date().isoformat() for d in index],
            "equity": [round(float(v), 2) for v in equity],
            "hold": [round(float(v), 2) for v in hold_equity],
            "close": [round(float(v), 4) for v in data["Close"]],
        },
        "trades": trades,
        "summary": summarise(run, flat, flat_hold, trades),
    }


def reproduce_command(
    run: dict[str, Any], overrides: dict[str, Any], start: str | None, end: str | None
) -> str:
    """The ``qc backtest`` command line that repeats a run."""
    parts = ["qc", "backtest", "--strategy", run["strategy"]]
    if run.get("underlying"):
        parts += ["--underlying", run["underlying"]]
    local = [s for s in run["sources"] if s.endswith(".csv")]
    parts += ["--data", *(local if len(local) == len(run["sources"]) else run["assets"])]
    downloaded = len(local) != len(run["sources"])
    if start or downloaded:
        parts += ["--start", start or DOWNLOAD_FROM]
    if end or downloaded:
        parts += ["--end", end or run["last_date"]]
    parts += ["--cash", f"{run['cash']:g}", "--commission", run["commission"]]
    for key, value in overrides.items():
        parts += ["--param", f"{key}={value!r}" if isinstance(value, str) else f"{key}={value}"]
    return shlex.join(parts)


# ---------------------------------------------------------------------------
# Written summary
# ---------------------------------------------------------------------------
def _pct(x: float | None, signed: bool = True) -> str:
    if x is None:
        return "n/a"
    s = f"{x:+.2f}%" if signed else f"{abs(x):.2f}%"
    return s.replace("-", "−")


def _usd(x: float) -> str:
    s = f"${abs(x):,.2f}"
    return ("−" + s) if x < 0 else s


def summarise(
    run: dict[str, Any], m: dict[str, Any], h: dict[str, Any], trades: list[dict[str, Any]]
) -> list[str]:
    """A few plain sentences about the run, most important first."""
    asset = " and ".join(run["assets"])
    first = run["assets"][0]
    is_hold = run["strategy"] == BuyAndHoldStrategy.__name__
    opening = (
        f"{run['label']} on {asset} returned {_pct(m['return'])} over {run['bars']} trading days."
    )
    if not is_hold:
        opening += f" Buying and holding {first} with the same cash returned {_pct(h['return'])}."
    lines = [opening]

    dd, hdd = m.get("max_drawdown"), h.get("max_drawdown")
    if dd is not None and hdd is not None and not is_hold:
        line = (
            f"Its worst drawdown was {_pct(dd, signed=False)}, "
            f"against {_pct(hdd, signed=False)} for holding"
        )
        if dd < 0 and hdd / dd >= 2:
            line += f", about {hdd / dd:.0f} times smaller"
        elif dd < hdd:
            line += ", so it fell further than the stock did"
        lines.append(line + ".")

    n = len(trades)
    if n == 0 and is_hold:
        lines.append("It bought on the first day and held to the last, so no trade closed.")
    elif n == 0 and (m.get("exposure") or 0) > 0:
        lines.append("Its position was still open on the last day, so no trade closed.")
    elif n == 0:
        lines.append("It made no trades in this period.")
    else:
        won = sum(1 for t in trades if t["pnl"] > 0)
        exposure = m.get("exposure") or 0.0
        lines.append(
            f"It was in the market {exposure:.0f}% of the time and made "
            f"{n} trade{'s' if n != 1 else ''}, "
            f"winning {won}. Commission came to {_usd(m.get('commission_paid') or 0.0)}."
        )

    stretch = best_stretch(trades)
    if stretch:
        lines.append(stretch)

    lines.append(
        "This is one period of history. A strategy tuned on it will look better here "
        "than it will on data it has not seen."
    )
    return lines


def best_stretch(trades: list[dict[str, Any]], window_days: int = 92) -> str | None:
    """
    Names the three-month stretch that made most of a profitable run's money,
    when one stretch made most of it and the run had trades outside it.
    """
    net = sum(t["pnl"] for t in trades)
    if len(trades) < 4 or net <= 0:
        return None
    exits = sorted(trades, key=lambda t: t["exit"])
    best, best_group = 0.0, []
    for i, t in enumerate(exits):
        start = pd.Timestamp(t["exit"])
        group = [u for u in exits[i:] if (pd.Timestamp(u["exit"]) - start).days <= window_days]
        total = sum(u["pnl"] for u in group)
        if total > best:
            best, best_group = total, group
    if len(best_group) >= len(trades) or best < 0.6 * net:
        return None
    first = pd.Timestamp(best_group[0]["exit"])
    last = pd.Timestamp(best_group[-1]["exit"])
    if (first.year, first.month) == (last.year, last.month):
        when = f"in {first:%B %Y}"
    elif first.year == last.year:
        when = f"between {first:%B} and {last:%B %Y}"
    else:
        when = f"between {first:%B %Y} and {last:%B %Y}"
    k, rest = len(best_group), len(trades) - len(best_group)
    lead = f"The {k} trades that closed {when}" if k > 1 else f"One trade, closed {when},"
    return f"{lead} made {_usd(best)}. The other {rest} trade{'s' if rest != 1 else ''} " + (
        f"lost {_usd(best - net)}, leaving {_usd(net)}."
        if net < best
        else f"made {_usd(net - best)}."
    )
