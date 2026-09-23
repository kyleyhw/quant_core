# Backtesting and Reporting

`quant_core.backtest` runs strategies against historical data and writes reports.
Both entry points are `qc` subcommands, and both use `backtesting.Backtest` with
the IBKR tiered commission model by default.

## One strategy: `qc backtest`

```bash
uv run qc backtest --strategy SimpleMACrossover --data data/benchmark/SPY_2024-10-01_2025-11-25.csv
```

- `--strategy` is any name listed by `qc strategies`, including strategies a
  separate package registers.
- `--data` takes one CSV, or two for a strategy with `data_assets = 2`. Two files
  are merged on their dates into `Close_1` and `Close_2` columns, and the first
  file's prices drive execution.
- `--underlying NAME` sets the wrapped strategy for a meta-strategy.
- `--param KEY=VALUE`, repeatable, overrides a strategy parameter for this run.
- `--cash` (default 10,000) and `--commission` choose the account size and the
  commission model: `IBKR Tiered`, `Fixed 0.1%`, `Fixed 0.5%` or `Zero Commission`.
- `--output-dir` (default `reports/`) is where the output goes.

Each run writes two files, named after the strategy and a timestamp:

1. `backtest_<Strategy>_<time>.html`: an interactive chart of the equity curve,
   trades and indicators.
2. `report_<Strategy>_<time>.md`: the strategy's parameters, the performance
   metrics and a link to the chart. [Interpreting Reports](./interpreting_report.md)
   explains each metric.

## Every strategy: `qc benchmark`

```bash
uv run qc benchmark                    # everything installed, over data/benchmark
uv run qc benchmark --strategies SimpleMACrossover RSI2PeriodStrategy
```

The benchmark runs each installed single-asset strategy on every CSV in `--data`
(default `data/benchmark/`), with $10,000 and IBKR tiered commission, and writes
one `benchmark_report_multi_asset_<time>.md` to `--output-dir`. It skips strategies
it cannot run alone: two-asset strategies, and meta-strategies whose underlying
strategy is not set. Use `qc backtest` for those.

## Why the numbers are trustworthy

- The strategy base class applies the trailing stop, take-profit and sizing it
  declares. The conformance suite in `testing/test_risk_parameters.py` proves it
  for every reference strategy.
- `testing/test_backtest_regression.py` pins the reference strategies' metrics,
  so an engine change that moves them fails CI until the baseline is regenerated
  on purpose.
- Commission is charged once per order by the engine. See the 0.2.0 entry in the
  [changelog](../CHANGELOG.md) for the bug this replaced.

Paths are relative to the directory you run from, so the same commands work in a
checkout of this repository or in a project that depends on it.
