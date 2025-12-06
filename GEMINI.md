# Project: IBKR Open-Core Algorithmic Trading Bot

## Context & Purpose
I am building a Python-based algorithmic trading system for Interactive Brokers (IBKR). The system is designed as an "Open Core" project: the infrastructure is public, but the specific trading strategies and trained models are private/proprietary.

The goal is to evolve from simple technical analysis strategies to Machine Learning (XGBoost) models while maintaining strict risk management and "fat finger" safety checks.

## Tech Stack Requirements
- **Broker API:** `ib_insync` (Use this over the native IB API for Pythonic syntax).
- **Data/Analysis:** `pandas`, `numpy`, `ta-lib` (or `pandas-ta`).
- **Backtesting:** `backtesting` (backtesting.py) for strategy simulation.
- **Machine Learning:** `xgboost`, `scikit-learn`.
- **Ops:** `python-dotenv` (secrets), `requests` (Discord/Telegram notifications).
- **Package Management:** `uv` (https://github.com/astral-sh/uv).

## Directory Structure & Logic
The project strictly follows this structure. Do not suggest code that violates this hierarchy.

```text
ibkr_trading_bot/
├── README.md              # Readme file
├── docs/                  # Documentation
├── data/                  # Historical CSVs (GitIgnored)
├── backtesting/
│   ├── run_backtest.py    # Single strategy deep-dive
│   └── benchmark.py       # Multi-strategy comparison tournament
└── GEMINI.md              # This file
```

## Core Architectural Rules

1. **The "Open Core" Git Workflow**
    - **Triggers**:
        - **Critical**: Connection loss, Order Rejection, "Fat Finger" block.
        - **Info**: Trade execution, Daily P&L summary.
    - **Commands**:
        - `git push origin master` (Main)
        - `cd strategies_private; git push origin main` (Submodule)

2. **Development Guidelines**
    - **Type Hinting**: All functions must have Python type hints.

3. **Full Set of Reports**
    - This term refers to the complete output of the backtesting and benchmarking process. It includes:
        1.  A detailed backtest report for each individual strategy (both public and private). A "report" includes both the markdown summary file and the HTML interactive plot.
        2.  A public benchmark report, comparing all public strategies.
        3.  An "all" benchmark report, comparing all public and private strategies.
    - Each report is to be generated in its appropriate directory (`/strategies/reports` for public, and `/strategies_private/reports` for private and "all" benchmark reports) to ensure no private information is publicly visible.