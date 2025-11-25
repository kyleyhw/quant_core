# Project Development Plan

This document outlines the planned phases and tasks for developing the IBKR Open-Core Algorithmic Trading Bot.

## Phase 1: Core Infrastructure Setup
1.  [completed] Verify and finalize the project directory structure.
2.  [completed] Populate `requirements.txt` with all necessary libraries.
3.  [completed] Implement the IBKR connection logic in `src/connection.py`.
4.  [completed] Implement standardized data fetching in `src/data_loader.py`.
5.  [completed] Create the base `Notifier` class in `src/notifications.py`.
6.  [completed] Set up initial documentation, including `README.md` and the `/docs` folder structure.

## Phase 2: Base Strategy & Backtesting Framework
7.  [completed] Develop the parent `base_strategy.py` to handle position sizing and stop-loss logic.
8.  [completed] Create a public `simple_ma_crossover.py` strategy (e.g., a moving average crossover) inheriting from the base strategy.
9.  [completed] Implement the backtesting script `run_backtesting/run_backtest.py` to test a single strategy.
10. [completed] Generate the first backtest report and save it to the `reports/` directory.

## Phase 3: Feature Engineering & ML Model Training
11. [completed] Develop the shared `src/feature_engineering.py` module with common technical indicators.
12. [completed] Create a script in research/ for model training.
    - [completed] Created `research/train_regime_model.py` (XGBoost regime classifier)
    - [completed] Created `research/utils.py` (simplified data fetching)
    - [completed] Run script to train and save model
13. [completed] Save the trained model artifact to the `models/` directory.

## Phase 4: Machine Learning Strategy Implementation
14. [completed] Create a private strategy in `strategies/private/` that uses a trained model.
15. [completed] Backtest the ML-based strategy.

## Phase 5: Advanced Strategy Development
21. [completed] Acquire and document datasets for pairs trading (GLD/GDX).
22. [completed] Implement and train a Hidden Markov Model (HMM) for regime detection.
23. [completed] Implement a private HMM-based trading strategy.
24. [completed] Backtest the HMM strategy.
25. [completed] Implement a private Pairs Trading strategy.
26. [completed] Backtest the Pairs Trading strategy.

## Phase 6: Live Execution & Safety
27. [pending] Implement the `execution.py` module with safety checks.
    - [completed] Hard limits (Max Shares, Max Dollar, Price Deviation).
28. [pending] Integrate the execution module with the base strategy.
29. [completed] Develop System Safety & Recovery Protocols.
    - [completed] Define Crash Recovery steps (State reconciliation).
    - [completed] Implement Heartbeat/System Health monitoring (via `tools/supervisor.py`).
    - [completed] Create `docs/safety_and_recovery.md`.
    - [pending] (Future) Implement External Heartbeat (Dead Man's Switch) for Supervisor monitoring.

## Phase 7: System Finalization
29. [pending] Implement the strategy benchmarking script `run_backtesting/benchmark.py`.
30. [pending] Integrate the `Notifier` class for alerts.
31. [pending] Complete all documentation.