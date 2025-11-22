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
├── readme.md              # Readme file
├── docs/                  # Documentation
├── data/                  # Historical CSVs (GitIgnored)
├── models/                # Trained XGBoost/ML models (GitIgnored)
├── logs/                  # Execution logs (GitIgnored)
├── reports/               # Backtest comparison results (GitIgnored)
├── research/              # Jupyter notebooks for training & analysis
├── src/
│   ├── connection.py      # Connects to TWS/Gateway
│   ├── data_loader.py     # Standardized data fetching
│   ├── feature_engineering.py  # CRITICAL: Shared logic for indicator calculation
│   ├── execution.py       # Order placement with SAFETY CHECKS
│   ├── notifications.py   # Discord/Telegram webhook alerts
│   └── metrics.py         # Math for Sharpe, Drawdown, Position Sizing
├── strategies/
│   ├── private/           # Git Submodule for proprietary strategies
│   ├── base_strategy.py   # Parent class (handling stops/sizing)
│   └── simple_demo.py     # Public example strategy
├── backtesting/
│   ├── run_backtest.py    # Single strategy deep-dive
│   └── benchmark.py       # Multi-strategy comparison tournament
└── GEMINI.md              # This file
```

Core Architectural Rules
1. The "Open Core" Git Workflow
Public strategies reside in strategies/.

Proprietary strategies reside in strategies/private/ (a Git Submodule).

Imports must be robust: try: from strategies.private import X except ImportError: pass.

NEVER output code that hardcodes credentials. Use .env.

2. Machine Learning Workflow (Prevention of Skew)
Training: Happens in research/. Saves models to models/.

Inference: Happens in strategies/. Loads models from models/.

Feature Consistency: Both Training and Inference MUST import features (RSI, SMA, etc.) from src/feature_engineering.py. Never rewrite indicator logic inside a strategy file.

3. Execution & Safety (The "Fat Finger" Layer)
Position Sizing: Calculated dynamically in base_strategy.py based on risk percentage (e.g., 1% of equity).

Hard Limits: src/execution.py must enforce:

MAX_SHARES_PER_ORDER (e.g., 100)

MAX_DOLLAR_VALUE (e.g., $5,000)

If a strategy requests more, the system must raise an Exception and alert the user.

4. Notifications
The system must define a Notifier class in src/notifications.py.

Triggers:

Critical: Connection loss, Order Rejection, "Fat Finger" block.

Info: Trade execution, Daily P&L summary.

Development Guidelines
Type Hinting: All functions must have Python type hints.

Documentation: Docstrings should focus on "Why" this exists, not just "What" it does.

Backtesting: When creating a backtest, assume 0.005 (0.5%) commission/slippage to remain realistic.

Benchmarking: When comparing strategies, use Sharpe Ratio as the primary metric, not total return.