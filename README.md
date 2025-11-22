# IBKR Open-Core Algorithmic Trading Bot

This project is a Python-based algorithmic trading system designed for Interactive Brokers (IBKR). It follows an "Open Core" model, meaning the core infrastructure is public, while specific trading strategies and trained machine learning models remain private and proprietary.

## Purpose

The primary goal of this project is to develop and implement algorithmic trading strategies, evolving from traditional technical analysis to advanced Machine Learning (XGBoost) models. A strong emphasis is placed on robust risk management and "fat finger" safety checks to ensure secure and reliable trading operations.

## Tech Stack

The system leverages the following key technologies:

*   **Broker API:** `ib_insync` (a Pythonic wrapper for the native IB API)
*   **Data/Analysis:** `pandas`, `numpy`, `pandas-ta` (for technical indicators)
*   **Backtesting:** `backtesting.py` (for strategy simulation and evaluation)
*   **Machine Learning:** `xgboost`, `scikit-learn`
*   **Operations:** `python-dotenv` (for secure handling of secrets), `requests` (for notifications via Discord/Telegram webhooks)

## Project Plan

For a detailed roadmap of the project's development phases and tasks, refer to the project plan:

*   **[Project Plan](./PROJECT_PLAN.md)**

## Project Documentation Hub

This documentation provides a detailed overview of the IBKR Open-Core Algorithmic Trading Bot. Each section covers a specific part of the system's architecture and logic.

### Documentation Index

1.  **[core infrastructure](./docs/core_infrastructure.md)**
    -   explains the foundational modules for connecting to interactive brokers, loading data, and sending notifications.

2.  **[strategy development](./docs/strategy_development.md)**
    -   details the base strategy class, risk management framework, and the implementation of example strategies.
        -   **simple ma crossover**: a strategy based on the crossover of two simple moving averages.
        -   **rsi 2-period**: a strategy based on overbought/oversold signals from a 2-period relative strength index.
        -   **bollinger bands**: a strategy utilizing volatility bands around a moving average for entry and exit signals.


3.  **[backtesting and reporting](./run_backtesting/backtesting_and_reporting.md)**
    -   covers the process of running backtests, generating performance reports, and interpreting the results.

-   **[interpreting report](./docs/interpreting_report.md)**
    -   provides detailed explanations of the various performance metrics found in backtest reports.

## Sample Backtest Reports

View the generated backtest reports and plots in the [reports/](./reports/) directory. These reports demonstrate the performance of various strategies against historical data.

## Directory Structure

The project adheres to a strict directory structure for organization and clarity:

```
ibkr_quant_core/
├── .env                  # Local environment variables (IGNORED BY GIT)
├── .gitignore            # Specifies files and directories to be ignored by Git
├── GEMINI.md             # Gemini-specific instructions and project context
├── PROJECT_PLAN.md       # High-level project development plan
├── README.md             # This file: Project overview and high-level documentation
├── requirements.txt      # Project dependencies
├── run_backtesting/
│   ├── run_backtest.py   # Script for single strategy deep-dive backtesting
│   └── benchmark.py      # Script for multi-strategy comparison
├── data/                 # Historical CSV data (Ignored by Git)
├── docs/                 # Detailed project documentation
│   ├── documentation_hub.md
│   ├── core_infrastructure.md
│   ├── strategy_development.md
│   ├── backtesting_and_reporting.md
│   ├── interpreting_report.md
│   └── formulations/
│       └── simple_ma_crossover_formulation.md
├── logs/                 # Execution logs (Ignored by Git)
├── models/               # Trained ML models (Ignored by Git)
├── reports/              # Backtest reports and plots (NOT IGNORED BY GIT)
├── research/             # Jupyter notebooks for training & analysis
├── src/
│   ├── connection.py     # Handles connection to TWS/Gateway
│   ├── data_loader.py    # Standardized data fetching utilities
│   ├── execution.py      # Order placement with safety checks
│   ├── feature_engineering.py # Shared logic for indicator calculation
│   ├── metrics.py        # Math utilities for Sharpe, Drawdown, etc.
│   └── notifications.py  # Discord/Telegram webhook alerts
└── strategies/
    ├── base_strategy.py  # Parent class for all strategies
    ├── simple_demo.py    # Public example strategy
    └── private/          # Git Submodule for proprietary strategies
```

## Getting Started

To get started with the IBKR Open-Core Algorithmic Trading Bot, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone [repository-url]
    cd ibkr_trading_bot
    ```
2.  **Install dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    pip install -r requirements.txt
    ```
3.  **Set up environment variables:**
    Create a `.env` file in the root directory for sensitive information (e.g., API keys, IBKR TWS/Gateway connection details). Refer to `python-dotenv` documentation for more details.
4.  **Connect to IBKR TWS/Gateway:**
    Ensure your Interactive Brokers Trader Workstation (TWS) or IB Gateway is running and configured to accept API connections.
5.  **Explore strategies:**
    Review the `strategies/simple_demo.py` for an example trading strategy. For proprietary strategies, refer to the `strategies/private/` submodule.
6.  **Run backtests:**
    Utilize the scripts in the `run_backtesting/` directory to evaluate strategy performance.

## Core Architectural Rules

### 1. The "Open Core" Git Workflow
Public strategies reside in `strategies/`.

Proprietary strategies reside in `strategies/private/` (a Git Submodule).

Imports must be robust to handle the absence of the private submodule:
```python
try:
    from strategies.private import MyPrivateStrategy
except ImportError:
    MyPrivateStrategy = None # Or handle appropriately
```
**NEVER** output code that hardcodes credentials. Use `.env` for all secrets.

### 2. Machine Learning Workflow (Prevention of Skew)
- **Training:** Happens in `research/`. Saves models to `models/`.
- **Inference:** Happens in `strategies/`. Loads models from `models/`.
- **Feature Consistency:** Both Training and Inference **MUST** import features (RSI, SMA, etc.) from `src/feature_engineering.py`. Never rewrite indicator logic inside a strategy file. This is critical to prevent training-serving skew.

### 3. Execution & Safety (The "Fat Finger" Layer)
- **Position Sizing:** Calculated dynamically in `base_strategy.py` based on a risk percentage of equity (e.g., 1%).
- **Hard Limits:** `src/execution.py` must enforce hard safety limits, such as:
  - `MAX_SHARES_PER_ORDER` (e.g., 100)
  - `MAX_DOLLAR_VALUE` (e.g., $5,000)
- If a strategy requests an order that exceeds these limits, the system **MUST** raise an `Exception` and send a critical notification.

### 4. Notifications
- The system must define a `Notifier` class in `src/notifications.py`.
- **Triggers:**
  - **Critical:** Connection loss, Order Rejection, "Fat Finger" block.
  - **Info:** Trade execution, Daily P&L summary.

## Development Guidelines
- **Type Hinting:** All functions must have Python type hints.
- **Documentation:** Docstrings should focus on **"Why"** a component exists, not just "What" it does.
- **Backtesting:** When creating a backtest, assume a realistic **0.005 (0.5%)** for commission and slippage to avoid over-optimistic results.
- **Benchmarking:** When comparing strategies, use the **Sharpe Ratio** as the primary metric, not total return.
