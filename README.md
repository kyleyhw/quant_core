# Algorithmic Trading Framework (Open-Core)

This project provides a market-agnostic, Python-based algorithmic trading framework. It is designed with an "Open Core" model: the core infrastructure is public and extensible, while specific trading strategies and trained machine learning models can remain private. Its initial concrete implementation is for Interactive Brokers (IBKR).

## Purpose

The primary goal is to provide a robust, extensible foundation for developing and implementing algorithmic trading strategies. The framework is designed to evolve from traditional technical analysis to advanced Machine Learning models, with a consistent and strong emphasis on risk management, regardless of the underlying market.

While its initial concrete implementation is for Interactive Brokers (IBKR), the framework is fundamentally designed to be extended to any market or broker API.

## Core Architecture: A Market-Agnostic Framework

The system is architected around a powerful abstraction layer that decouples core trading logic from market-specific details. This allows for the development of strategies that are portable, reusable, and independent of any single broker.

The key to this design is the **Market Adapter** pattern. The core framework defines a set of abstract interfaces for handling connections, data, and execution. A concrete implementation of these interfaces, called a Market Adapter, acts as a "plug-in" for a specific market.

**The Interactive Brokers implementation provided in this repository is the first concrete instantiation of this abstract framework.**

## Tech Stack

The framework leverages the following key technologies:

*   **Core Framework:** `pandas`, `numpy`
*   **IBKR Adapter:** `ib_insync`
*   **Backtesting:** `backtesting.py`
*   **Machine Learning:** `xgboost`, `scikit-learn`
*   **Operations:** `python-dotenv`, `requests`
*   **Data Management:** Smart Caching (Ephemeral & Permanent file storage)

## Project Plan

For a detailed roadmap of the project's development phases and tasks, refer to the project plan:

*   **[Project Plan](./PROJECT_PLAN.md)**

## Project Documentation Hub

This documentation provides a detailed overview of the framework and its IBKR implementation.

### Documentation Index

1.  **[Market-Agnostic Framework](./docs/market_agnostic_framework.md)**
    -   **The best place to start.** Explains the core plug-and-play architecture, interfaces, and how to extend the framework.

2.  **[Core Infrastructure](./docs/core_infrastructure.md)**
    -   Explains the foundational modules, focusing on the IBKR Market Adapter as a concrete implementation of the core framework.

3.  **[Strategy Development](./docs/strategy_development.md)**
    -   Details the base strategy class, risk management, and example strategies.

4.  **[Backtesting and Reporting](./docs/backtesting_and_reporting.md)**
    -   Covers the process of running backtests and generating performance reports.

5.  **[Interpreting Reports](./docs/interpreting_report.md)**
    -   Provides detailed explanations of the various performance metrics found in backtest reports.

6.  **[Data Management](./docs/data_management.md)**
    -   Explains the Smart Data system, including ephemeral vs. permanent caching storage strategies.

7.  **[Building on quant-core](./docs/building_on_quant_core.md)**
    -   Registering your own strategies and `qc` commands from a separate package, the development loop across two repositories, and the conformance test.

8.  **[CLI Reference](./docs/cli_usage.md)**
    -   Every `qc` command and option.

## Sample Backtest Reports

To understand the framework's performance, begin by examining the comprehensive multi-asset benchmark report. This report provides an overview of various strategies across multiple assets. For in-depth analysis and detailed performance metrics of individual strategies, refer to their respective reports.

*   **Latest Public Benchmark Report:** [./reports/benchmark_report_multi_asset_20260921_062638.md](./reports/benchmark_report_multi_asset_20260921_062638.md)
> **Numbers moved on 2026-09-21.** Reports generated before this date ran with a
> trailing stop set roughly seventy times tighter than documented, with no stop at
> all on two of the three public strategies, with no take-profit, and fully
> invested regardless of `risk_percent`. With those fixed, mean return across the
> thirty risk-managed runs falls from +12.47% to -0.29% and mean maximum drawdown
> falls from -16.93% to -6.61%. Earlier reports are kept for history but should
> not be quoted.

*   **Individual Strategy Reports:** View all generated reports and plots in the [reports/](./reports/) directory.

## Directory Structure

```
quant_core/
├── README.md
├── CHANGELOG.md          # Releases and migration notes
├── PROJECT_PLAN.md       # Roadmap
├── pyproject.toml        # Package metadata, entry points, tool config
├── data/                 # Sample price data (CSV)
├── docs/                 # Detailed documentation
├── reports/              # Generated backtest and benchmark reports
├── src/quant_core/       # The installable package
│   ├── interfaces.py     # << CORE: Abstract interfaces for the framework
│   ├── registry.py       # Strategy and command discovery via entry points
│   ├── execution.py      # Market-agnostic safety check layer
│   ├── feature_engineering.py
│   ├── notifications.py
│   ├── cli.py            # The `qc` command
│   ├── backtest/         # run_backtest.py and benchmark.py
│   ├── dashboard/        # Streamlit app
│   ├── market_adapters/
│   │   └── ibkr/         # The IBKR "plug-in"
│   └── strategies/
│       ├── base_strategy.py  # Parent class for all strategies
│       └── ...               # Reference strategies
└── testing/              # pytest suite, including the strategy conformance test
```

Proprietary strategies are not part of this repository. They live in their own
packages, which install `quant-core` and register their strategies through an
entry point. See [Building on quant-core](./docs/building_on_quant_core.md).

## Getting Started

1.  **Clone and install:**
    ```bash
    git clone https://github.com/kyleyhw/quant_core.git
    cd quant_core
    uv sync
    ```
2.  **Set up environment variables:**
    Create a `.env` file in the root directory for sensitive information (e.g., IBKR connection details).
3.  **Connect to IBKR TWS/Gateway:**
    Only needed for live or paper trading. Ensure Trader Workstation (TWS) or IB Gateway is running and configured to accept API connections.
4.  **Launch the Dashboard (UI):**
    ```bash
    uv run qc dashboard
    ```
    **Using the Dashboard:**
    - **Select Strategy**: Choose any installed strategy from the sidebar.
    - **Select Asset**: Choose an asset (e.g., SPY), or two assets for a strategy that trades a pair.
    - **Date Range**: Adjust the start and end dates for the backtest.
    - **Run Backtest**: Click the "Run Backtest" button to execute.
    - **View Results**: Analyze the interactive plots, metrics, and trade logs.
    - **Download Data**: Enable this toggle to fetch fresh data from Yahoo Finance for the session, without saving to disk.
5.  **Run from the command line:**
    ```bash
    uv run qc strategies    # what is installed
    uv run qc benchmark     # every installed strategy across data/benchmark
    ```
    See the **[CLI reference](./docs/cli_usage.md)** for every command.

## Core Architectural Rules

### 1. Extensibility via Market Adapters
The framework is designed to be extended. New markets can be added by creating a new adapter under `quant_core.market_adapters` and implementing the classes defined in `quant_core.interfaces`. The core logic in strategies should remain unchanged.

### 2. Machine Learning Workflow (Prevention of Skew)
- **Training and models:** Live with the package that owns the strategy, not in this repository.
- **Inference:** Occurs within strategies.
- **Feature Consistency:** Both training and inference code **MUST** import feature generation logic (e.g., indicators) from `quant_core.feature_engineering`. This is a critical rule to prevent training-serving skew.

### 3. Execution & Safety (The "Fat Finger" Layer)
- **Position Sizing:** Calculated dynamically in `quant_core.strategies.base_strategy`.
- **Hard Limits:** The market-agnostic `quant_core.execution` module enforces hard safety limits (e.g., `MAX_SHARES_PER_ORDER`, `MAX_DOLLAR_VALUE_PER_ORDER`) on a generic order dictionary *before* it is passed to a specific market adapter.
- If a strategy generates an order that exceeds these limits, the system **MUST** raise an `Exception` and send a critical notification.

### 4. Notifications
- The system defines a `Notifier` class in `quant_core.notifications`.
- **Triggers:**
  - **Critical:** Connection loss, Order Rejection, "Fat Finger" block.
  - **Info:** Trade execution, Daily P&L summary.

## Development Guidelines
- **Type Hinting:** All functions must have Python type hints.
- **Documentation:** Docstrings should focus on **"Why"** a component exists, not just "What" it does.
- **Backtesting:** Use the `ibkr_tiered_commission` function to simulate realistic IBKR Pro Tiered pricing.
- **Benchmarks:** Use the **Sharpe Ratio** as the primary metric for comparing strategies, not total return.

## Code Quality Workflow

We enforce strict code quality using `ruff` (linting/formatting) and `ty` (type checking).

1.  **Install Hooks:** `uv run pre-commit install`
2.  **Manual Check:** `uv run ruff check --fix .` and `uvx ty check`

For detailed instructions, see **[Code Quality Documentation](./docs/code_quality.md)**.
