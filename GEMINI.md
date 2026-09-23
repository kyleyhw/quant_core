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
quant_core/
├── README.md              # Readme file
├── CHANGELOG.md           # Releases and migration notes
├── docs/                  # Documentation
├── data/                  # Historical CSVs
├── reports/               # Generated backtest and benchmark reports
├── src/quant_core/        # The installable package
│   ├── backtest/          # run_backtest.py (single strategy), benchmark.py (all installed)
│   ├── dashboard/         # Streamlit app, launched with `qc dashboard`
│   ├── strategies/        # BaseStrategy and the reference strategies
│   └── market_adapters/   # Broker integrations (IBKR)
├── testing/               # pytest suite
└── GEMINI.md              # This file
```

Proprietary strategies do not live in this repository. They live in separate
packages that install `quant-core` as a dependency and register their strategies
through the `quant_core.strategies` entry-point group. This repository must never
contain, import or name them.

## Core Architectural Rules

1. **The "Open Core" Git Workflow**
    - **Triggers**:
        - **Critical**: Connection loss, Order Rejection, "Fat Finger" block.
        - **Info**: Trade execution, Daily P&L summary.
    - **Commands**:
        - `git push origin master`

2. **Development Guidelines**
    - **Type Hinting**: All functions must have Python type hints.

3. **Full Set of Reports**
    - This term refers to the complete output of the backtesting and benchmarking process. It includes:
        1.  A detailed backtest report for each reference strategy (`qc backtest`). A "report" includes both the markdown summary file and the HTML interactive plot.
        2.  A benchmark report comparing every installed strategy (`qc benchmark`).
    - Reports are written to `reports/` under the directory the command runs in. Run from this repository, only the reference strategies are installed, so nothing proprietary can appear in a report here.