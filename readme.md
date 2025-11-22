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

## Directory Structure

The project adheres to a strict directory structure for organization and clarity:

```
ibkr_trading_bot/
├── readme.md              # Project overview and documentation
├── docs/                  # Documentation and additional guides
├── data/                  # Historical CSVs (GitIgnored)
├── models/                # Trained XGBoost/ML models (GitIgnored)
├── logs/                  # Execution logs (GitIgnored)
├── reports/               # Backtest comparison results (GitIgnored)
├── research/              # Jupyter notebooks for training & analysis
├── src/
│   ├── connection.py      # Handles connection to TWS/Gateway
│   ├── data_loader.py     # Standardized data fetching utilities
│   ├── feature_engineering.py  # CRITICAL: Shared logic for indicator calculation
│   ├── execution.py       # Order placement with SAFETY CHECKS
│   ├── notifications.py   # Discord/Telegram webhook alerts
│   └── metrics.py         # Mathematical utilities for Sharpe, Drawdown, Position Sizing
├── strategies/
│   ├── private/           # Git Submodule for proprietary strategies
│   ├── base_strategy.py   # Parent class for all trading strategies (handles stops/sizing)
│   └── simple_demo.py     # Public example strategy for demonstration
├── backtesting/
│   ├── run_backtest.py    # Script for single strategy deep-dive backtesting
│   └── benchmark.py       # Script for multi-strategy comparison and benchmarking
└── GEMINI.md              # Gemini's context and instructions for this project
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
    Utilize the scripts in the `backtesting/` directory to evaluate strategy performance.
7.  **Develop new features:**
    Adhere to the core architectural rules and development guidelines outlined in the `GEMINI.md` file.

## Core Architectural Rules & Development Guidelines

Please refer to the `GEMINI.md` file for detailed information on:

*   The "Open Core" Git Workflow
*   Machine Learning Workflow (Prevention of Skew)
*   Execution & Safety (The "Fat Finger" Layer)
*   Notifications
*   Type Hinting and Documentation standards
*   Backtesting and Benchmarking assumptions

```