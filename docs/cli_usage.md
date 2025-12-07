# Command-Line Interface (CLI) Usage

The `quant-core` CLI provides a set of commands to interact with the framework, allowing you to run backtests, benchmarks, download data, and train models directly from your terminal.

## Getting Started

To use the CLI, you must first install the project in editable mode. This will register the `quant-core` command in your environment.

```bash
uv pip install -e .
```

Once installed, you can access all commands by calling `quant-core` from your terminal.

```bash
quant-core --help
```

## Commands

### `backtest`

Run a backtest for a single strategy.

**Usage:**

```bash
quant-core backtest --strategy <STRATEGY_NAME> --data <DATA_PATH> [OPTIONS]
```

**Arguments:**

*   `--strategy`: (Required) The name of the strategy class to test (e.g., `SimpleMACrossover`).
*   `--data`: (Required) Path to the historical data CSV file.
*   `--cash`: Initial cash for the backtest (default: 10000).
*   `--commission`: Commission model to use (default: "0.002").

**Example:**

```bash
quant-core backtest --strategy SimpleMACrossover --data data/benchmark/SPY_2024-10-01_2025-11-25.csv
```

### `benchmark`

Run a benchmark of multiple strategies.

**Usage:**

```bash
quant-core benchmark [OPTIONS]
```

**Arguments:**

*   `--scope`: The scope of strategies to benchmark (`public`, `private`, or `all`; default: `all`).
*   `--data`: Path to the data file or directory to use for benchmarking.

**Example:**

```bash
quant-core benchmark --scope public --data data/benchmark
```

### `download`

Download historical market data from Yahoo Finance.

**Usage:**

```bash
quant-core download --tickers <TICKERS> --start <START_DATE> --end <END_DATE> [OPTIONS]
```

**Arguments:**

*   `--tickers`: (Required) A list of tickers to download (e.g., `SPY AAPL`).
*   `--start`: (Required) The start date for the data in `YYYY-MM-DD` format.
*   `--end`: (Required) The end date for the data in `YYYY-MM-DD` format.
*   `--output`: The directory to save the downloaded data (default: `data`).

**Example:**

```bash
quant-core download --tickers SPY AAPL --start 2024-01-01 --end 2025-01-01
```

### `train-regime`

Train the XGBoost regime classifier.

**Usage:**

```bash
quant-core train-regime [OPTIONS]
```

**Arguments:**

*   `--csv`: Path to CSV file with OHLCV data.
*   `--symbol`: Symbol to fetch from IBKR (default: `SPY`).
*   `--start`: Start date (default: `2015-01-01`).
*   `--end`: End date (default: `2023-12-31`).
*   `--output`: Output model path (default: `strategies_private/models/xgb_regime_classifier.json`).
*   `--report`: Training report path (default: `strategies_private/research/training_report.md`).

**Example:**

```bash
quant-core train-regime --csv data/SPY_daily.csv
```

### `train-ensemble`

Train the ensemble models.

**Usage:**

```bash
quant-core train-ensemble
```

**Example:**

```bash
quant-core train-ensemble
```
