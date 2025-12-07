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

## Sample Backtest Reports

To understand the framework's performance, begin by examining the comprehensive multi-asset benchmark report. This report provides an overview of various strategies across multiple assets. For in-depth analysis and detailed performance metrics of individual strategies, refer to their respective reports.

*   **Latest Public Benchmark Report:** [./strategies/reports/benchmark_report_multi_asset_20251127_010136.md](./strategies/reports/benchmark_report_multi_asset_20251127_010136.md)
*   **Individual Strategy Reports:** View all generated reports and plots in the [strategies/reports/](./strategies/reports/) directory.

## Directory Structure

```
quant_core/
├── .env                  # Local environment variables (IGNORED BY GIT)
├── README.md             # This file: Project overview and high-level documentation
├── requirements.txt      # Project dependencies
├── setup.py              # Makes the core framework installable
├── run_backtesting/
│   └── benchmark.py      # Script for multi-strategy comparison
├── data/                 # Historical CSV data (Ignored by Git)
├── docs/                 # Detailed project documentation
│   ├── market_agnostic_framework.md
│   ├── core_infrastructure.md
│   └── ...
├── src/
│   ├── interfaces.py     # << CORE: Abstract interfaces for the framework
│   ├── market_adapters/  # << CORE: Concrete market implementations
│   │   └── ibkr/         # The IBKR "plug-in"
│   │       ├── connection.py
│   │       ├── data_loader.py
│   │       └── execution.py
│   ├── execution.py      # Market-agnostic safety check layer
│   ├── feature_engineering.py
│   └── notifications.py
└── strategies/
    ├── base_strategy.py  # Parent class for all strategies (for backtesting & live)
    └── private/          # Git Submodule for proprietary strategies
```

## Getting Started

1.  **Clone the repository and its submodules:**
    ```bash
    git clone --recurse-submodules [repository-url]
    cd quant_core
    ```
2.  **Install dependencies:**
    Install the core framework in editable mode with IBKR support.
    ```bash
    pip install -e .[ibkr]
    ```
3.  **Set up environment variables:**
    Create a `.env` file in the root directory for sensitive information (e.g., IBKR connection details).
4.  **Connect to IBKR TWS/Gateway:**
    Ensure your Interactive Brokers Trader Workstation (TWS) or IB Gateway is running and configured to accept API connections.
5.  **Launch the Dashboard (UI):**
    The project includes a Streamlit-based dashboard for easy backtesting and analysis.
    ```bash
    python -m streamlit run dashboard/app.py
    ```
    **Using the Dashboard:**
    - **Select Strategy**: Choose a strategy from the sidebar.
    - **Select Asset**: Choose an asset (e.g., SPY) or multiple assets for pair strategies.
    - **Date Range**: Adjust the start and end dates for the backtest.
    - **Run Backtest**: Click the "Run Backtest" button to execute.
    - **View Results**: Analyze the interactive plots, metrics, and trade logs.
    - **Private Mode**: Enable this checkbox to load proprietary strategies from the `strategies_private` submodule.
    - **Download Data**: Enable this checkbox to force a fresh download of historical data from Yahoo Finance, overriding any locally cached files.
6.  **Run Command-Line Backtests:**
    Alternatively, use the benchmark script to evaluate strategy performance via CLI.
    ```bash
    python run_backtesting/benchmark.py
    ```

## Core Architectural Rules

### 1. Extensibility via Market Adapters
The framework is designed to be extended. New markets can be added by creating a new adapter in `src/market_adapters/` and implementing the classes defined in `src/interfaces.py`. The core logic in strategies should remain unchanged.

### 2. Machine Learning Workflow (Prevention of Skew)
- **Training:** Occurs in the `strategies_private/research/` directory. Trained models are saved to `strategies_private/models/`.
- **Inference:** Occurs within strategies. Models are loaded from `strategies_private/models/`.
- **Feature Consistency:** Both training and inference code **MUST** import feature generation logic (e.g., indicators) from `src/feature_engineering.py`. This is a critical rule to prevent training-serving skew.

### 3. Execution & Safety (The "Fat Finger" Layer)
- **Position Sizing:** Calculated dynamically in `strategies/base_strategy.py`.
- **Hard Limits:** The market-agnostic `src/execution.py` module enforces hard safety limits (e.g., `MAX_SHARES_PER_ORDER`, `MAX_DOLLAR_VALUE_PER_ORDER`) on a generic order dictionary *before* it is passed to a specific market adapter.
- If a strategy generates an order that exceeds these limits, the system **MUST** raise an `Exception` and send a critical notification.

### 4. Notifications
- The system defines a `Notifier` class in `src/notifications.py`.
- **Triggers:**
  - **Critical:** Connection loss, Order Rejection, "Fat Finger" block.
  - **Info:** Trade execution, Daily P&L summary.

## Development Guidelines
- **Type Hinting:** All functions must have Python type hints.
- **Documentation:** Docstrings should focus on **"Why"** a component exists, not just "What" it does.
- **Backtesting:** Use the `ibkr_tiered_commission` function to simulate realistic IBKR Pro Tiered pricing.
- **Benchmarking:** Use the **Sharpe Ratio** as the primary metric for comparing strategies, not total return.
