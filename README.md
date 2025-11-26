# Algorithmic Trading Framework (Open-Core)

This project provides a market-agnostic, Python-based algorithmic trading framework. It is designed with an "Open Core" model: the core infrastructure is public and extensible, while specific trading strategies and trained machine learning models can remain private.

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

## Project Documentation Hub

This documentation provides a detailed overview of the framework and its IBKR implementation.

### Documentation Index

1.  **[Market-Agnostic Framework](./docs/market_agnostic_framework.md)**
    -   **START HERE.** Explains the core plug-and-play architecture, interfaces, and how to extend the framework to other markets.

2.  **[Core Infrastructure](./docs/core_infrastructure.md)**
    -   Explains the foundational modules, including the IBKR Market Adapter implementation.

3.  **[Strategy Development](./docs/strategy_development.md)**
    -   Details the base strategy class, risk management, and example strategies.

4.  **[Backtesting and Reporting](./docs/backtesting_and_reporting.md)**
    -   Covers the process of running backtests and generating performance reports.

## Directory Structure

```
ibkr_quant_core/
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
│   └── ...
└── strategies/
    ├── base_strategy.py  # Parent class for all strategies (for backtesting & live)
    └── private/          # Git Submodule for proprietary strategies
```

## Getting Started

1.  **Clone the repository:**
    ```bash
    git clone --recurse-submodules [repository-url]
    cd ibkr_quant_core
    ```
2.  **Install dependencies:**
    It is recommended to use a virtual environment. The core framework can be installed as an editable package. For the IBKR adapter, install the `[ibkr]` extras.
    ```bash
    pip install -e .[ibkr]
    ```
3.  **Set up environment variables:**
    Create a `.env` file in the root directory for IBKR TWS/Gateway connection details.
4.  **Run backtests:**
    Utilize the benchmark script to evaluate strategy performance.
    ```bash
    python run_backtesting/benchmark.py
    ```

## Core Architectural Rules

### 1. Extensibility
New markets can be added by creating a new adapter in `src/market_adapters/` and implementing the classes from `src/interfaces.py`. The core logic in strategies should not be changed.

### 2. Machine Learning Workflow (Prevention of Skew)
- **Training:** Happens in `research/`. Saves models to `models/`.
- **Inference:** Happens in `strategies/`. Loads models from `models/`.
- **Feature Consistency:** Both Training and Inference **MUST** import features from `src/feature_engineering.py`. This is critical to prevent training-serving skew.

### 3. Execution & Safety (The "Fat Finger" Layer)
- **Position Sizing:** Calculated in `base_strategy.py`.
- **Hard Limits:** The market-agnostic `src/execution.py` enforces safety limits (max shares, max dollar value) on a generic order dictionary before it is passed to a market adapter.
- If a strategy generates an order that exceeds these limits, the system **MUST** raise an `Exception` and send a critical notification.
