"""Walk-forward validation on the synthetic fixture."""

import pandas as pd
import pytest

from quant_core.backtest import walkforward
from quant_core.strategies.simple_ma_crossover import SimpleMACrossover
from quant_core.validation import segment_stats, to_markdown, walk_forward

GRID = {"fast_ma_period": [5, 10], "slow_ma_period": [20, 30]}


def test_folds_tile_the_history_without_overlap(ohlcv):
    result = walk_forward(ohlcv, SimpleMACrossover, train_bars=200, test_bars=100)
    folds = result.folds
    assert len(folds) == 2
    dates = [f"{d:%Y-%m-%d}" for d in ohlcv.index]
    assert folds[0].train_start == dates[0]
    assert folds[0].test_start == dates[200]
    assert folds[1].test_start == dates[300]
    assert folds[0].test_end < folds[1].test_start
    assert folds[-1].test_end == dates[-1]
    # The joined curve covers exactly the test windows, once each.
    assert len(result.oos_equity) == 200
    assert result.oos_equity.index.is_unique


def test_anchored_training_always_starts_at_the_first_bar(ohlcv):
    result = walk_forward(ohlcv, SimpleMACrossover, train_bars=150, test_bars=100, anchored=True)
    assert {f.train_start for f in result.folds} == {f"{ohlcv.index[0]:%Y-%m-%d}"}
    assert result.folds[-1].train_end > result.folds[0].train_end


def test_last_fold_may_be_short(ohlcv):
    result = walk_forward(ohlcv, SimpleMACrossover, train_bars=200, test_bars=150)
    assert [f.test_start for f in result.folds][-1] == f"{ohlcv.index[350]:%Y-%m-%d}"
    assert result.folds[-1].test_end == f"{ohlcv.index[-1]:%Y-%m-%d}"


def test_grid_is_searched_on_training_data_only(ohlcv):
    result = walk_forward(ohlcv, SimpleMACrossover, train_bars=200, test_bars=100, param_grid=GRID)
    for fold in result.folds:
        assert fold.params["fast_ma_period"] in GRID["fast_ma_period"]
        assert fold.params["slow_ma_period"] in GRID["slow_ma_period"]
    # The test windows are scored with the chosen parameters and nothing else.
    first = result.folds[0]
    from backtesting import Backtest

    stats = Backtest(ohlcv.iloc[200:300], SimpleMACrossover, cash=10_000).run(**first.params)
    assert first.test["return"] == pytest.approx(stats["Return [%]"], abs=1e-9)


def test_joined_curve_compounds_the_folds(ohlcv):
    result = walk_forward(ohlcv, SimpleMACrossover, train_bars=200, test_bars=100)
    product = 1.0
    for f in result.folds:
        ret = f.test["return"]
        assert ret is not None
        product *= 1 + ret / 100
    assert result.summary["oos"]["return"] == pytest.approx((product - 1) * 100, rel=1e-9)


def test_warmup_is_run_but_not_scored(ohlcv):
    result = walk_forward(ohlcv, SimpleMACrossover, train_bars=200, test_bars=100, warmup_bars=50)
    assert result.folds[0].test_start == f"{ohlcv.index[200]:%Y-%m-%d}"
    assert result.oos_equity.index[0] == ohlcv.index[200]


def test_too_little_data_is_refused(ohlcv):
    with pytest.raises(ValueError, match="too short"):
        walk_forward(ohlcv, SimpleMACrossover, train_bars=380, test_bars=100)


def test_segment_stats_on_a_known_curve():
    equity = pd.Series([100.0, 110.0, 99.0, 121.0])
    s = segment_stats(equity)
    assert s["return"] == pytest.approx(21.0)
    assert s["max_drawdown"] == pytest.approx(-10.0)


def test_report_and_grid_parsing(ohlcv):
    assert walkforward.parse_grid(["a=1,2", "b=0.5,x"]) == {"a": [1, 2], "b": [0.5, "x"]}
    with pytest.raises(ValueError):
        walkforward.parse_grid(["nonsense"])
    result = walk_forward(ohlcv, SimpleMACrossover, train_bars=200, test_bars=100)
    text = to_markdown(result, "SMA on FIX", {"Data": "synthetic"})
    assert "## Out of sample" in text
    assert text.count("\n| 1 |") == 1 and "\n| 2 |" in text


def test_short_windows_do_not_break_the_trailing_stop(ohlcv):
    """A window under 100 bars used to leave the ATR all NaN and the stop at -inf."""
    from backtesting import Backtest

    for bars in (40, 99, 100):
        stats = Backtest(ohlcv.iloc[:bars], SimpleMACrossover, cash=10_000).run()
        assert stats["# Trades"] >= 0
