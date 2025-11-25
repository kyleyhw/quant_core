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

Core Architectural Rules
1. The "Open Core" Git Workflow
Triggers:

Critical: Connection loss, Order Rejection, "Fat Finger" block.

Info: Trade execution, Daily P&L summary.

Development Guidelines
Type Hinting: All functions must have Python type hints.

Documentation: Docstrings should focus on "Why" this exists, not just "What" it does.

Backtesting: When creating a backtest, assume 0.005 (0.5%) commission/slippage to remain realistic.

Benchmarking: When comparing strategies, use Sharpe Ratio as the primary metric, not total return.