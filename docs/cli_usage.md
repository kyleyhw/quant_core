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
*   `--start`, `--end`: Date range when `--data` is a ticker.
*   `--underlying`: For a wrapper strategy, the strategy it wraps.
*   `--param KEY=VALUE`: Override a strategy parameter. Repeatable.
*   `--output-dir`: Where to write the report (default: `reports`).

```bash
uv run qc backtest --strategy SimpleMACrossover \
    --data data/benchmark/SPY_2024-10-01_2025-11-25.csv --param stop_loss_pct=0.03
```

### `benchmark`

Run every installed strategy across a CSV file or a directory of CSV files, and
write one consolidated report.

```bash
uv run qc benchmark [--data data/benchmark] [--output-dir reports] [--strategies NAME ...]
```

Strategies that trade two assets at once (`data_assets = 2`) are skipped, as are
wrapper strategies registered without an `underlying_strategy`.

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
