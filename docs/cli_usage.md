# Command-Line Interface (CLI) Usage

`qc` is installed with the `quant-core` package. It runs backtests and benchmarks,
downloads data, launches the dashboard, and lists installed strategies. Packages
that build on `quant-core` can add their own subcommands; see
[Building on quant-core](./building_on_quant_core.md).

Every path is relative to the directory you run `qc` from, so the same commands
work in a checkout of this repository and in a project that depends on it.

## Getting Started

```bash
uv sync
uv run qc --help
```

## Commands

### `strategies`

List every installed strategy, the package that registered it, and its class.
Exits non-zero if any registered strategy failed to load.

```bash
uv run qc strategies
```

### `backtest`

Run one installed strategy and write a Markdown report and an HTML plot.

```bash
uv run qc backtest --strategy <NAME> --data <CSV_OR_TICKER> [OPTIONS]
```

*   `--strategy`: (Required) A name from `qc strategies`.
*   `--data`: (Required) One or more CSV files or tickers. A strategy that sets
    `data_assets = 2` takes two; they are merged with `_1` and `_2` suffixes.
*   `--cash`: Starting cash (default: 10000).
*   `--commission`: A commission model name (default: `IBKR Tiered`).
*   `--start`, `--end`: The first and last dates to backtest, inclusive. They
    trim a CSV file, and set the range downloaded for a ticker (default for a
    download: 2020-01-01 to 2023-12-31).
*   `--underlying`: For a wrapper strategy, the strategy it wraps.
*   `--param KEY=VALUE`: Override a strategy parameter. Repeatable.
*   `--output-dir`: Where to write the report (default: `reports`).

```bash
uv run qc backtest --strategy SimpleMACrossover \
    --data data/benchmark/SPY_2015-01-01_2026-09-24.csv --start 2021-01-01 \
    --param stop_loss_pct=0.03
```

### `benchmark`

Run every installed strategy across a CSV file or a directory of CSV files, and
write one consolidated report.

```bash
uv run qc benchmark [--data data/benchmark] [--output-dir reports] [--strategies NAME ...]
```

Strategies that trade two assets at once (`data_assets = 2`) are skipped, as are
wrapper strategies registered without an `underlying_strategy`.

### `walkforward`

Test a strategy on data it was not fitted to. The history is cut into folds: a
training window, then a test window that starts where training ends. With
`--grid`, each parameter is searched on the training window alone and the best
values are carried into the test window unchanged; without it, the strategy's
own parameters are used throughout. The test windows never overlap, so joined end
to end they form an out-of-sample equity curve.

```bash
uv run qc walkforward --strategy <NAME> --data <TICKER> [TICKER] [OPTIONS]
```

*   `--data`: Tickers with a file in `--data-dir` (default: `data/benchmark`), or
    tickers to download. A pairs strategy takes two.
*   `--train`, `--test`: Window lengths in bars (defaults: 756 and 252, about
    three years and one). The last test window may be shorter.
*   `--step`: Bars between folds (default: the test window). `--anchored` keeps
    every training window starting at the first bar.
*   `--grid NAME=V1,V2,...`: A parameter to search on each training window.
    Repeatable. `--maximize` names the statistic to maximise (default:
    `Sharpe Ratio`).
*   `--param KEY=VALUE`: Fix a parameter for every run.
*   `--warmup N`: Bars run before each test window to prime indicators, and left
    out of its figures.
*   `--start`, `--end`, `--cash`, `--commission`, `--underlying`: As for `backtest`.

```bash
uv run qc walkforward --strategy SimpleMACrossover --data SPY \
    --grid fast_ma_period=5,10,20 --grid slow_ma_period=30,50,100
```

It prints the report and writes it, with the fold data as JSON, to `reports/`.
The report compares training and test Sharpe, gives the walk-forward efficiency
(test CAGR over mean training CAGR), and counts the test years that made money
and that beat buy and hold. From Python, use `quant_core.validation.walk_forward`.

### `download`

Download daily bars from Yahoo Finance.

```bash
uv run qc download --tickers SPY AAPL --start 2024-01-01 --end 2025-01-01 [--output data]
```

### `dashboard`

Serve the dashboard locally and open it in a browser. It lists every installed
strategy and reads price files from `data/benchmark` under the directory you run
it from.

```bash
uv run qc dashboard                       # http://localhost:8501
uv run qc dashboard --port 8600 --no-browser
uv run qc dashboard --data-dir data/multiasset
```

`--export DIR` writes a static copy instead of serving: every single-asset
strategy run on every file in the data folder under every commission model, at
default parameters, as plain files any static host can serve. The hosted copy on
GitHub Pages is built this way.

```bash
uv run qc dashboard --export site
```

The server binds to `127.0.0.1` by default and has no authentication, so keep it
on your own machine.
