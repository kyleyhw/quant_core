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
8.  [completed] Create a public `simple_demo.py` strategy (e.g., a moving average crossover) inheriting from the base strategy.
9.  [completed] Implement the backtesting script `backtesting/run_backtest.py` to test a single strategy.
10. [completed] Generate the first backtest report and save it to the `reports/` directory.

## Phase 3: Feature Engineering & ML Model Training
11. [pending] Create a script in research/ for model training.
12. [pending] Create a Jupyter notebook in `research/` for model training.
13. [pending] Save the trained model artifact to the `models/` directory.

## Phase 4: Machine Learning Strategy Implementation
14. [pending] Create a private strategy in `strategies/private/` that uses a trained model.
15. [pending] Backtest the ML-based strategy.

## Phase 5: Live Execution & Safety
16. [pending] Implement the `execution.py` module with safety checks.
17. [pending] Integrate the execution module with the base strategy.

## Phase 6: System Finalization
18. [pending] Implement the strategy benchmarking script `backtesting/benchmark.py`.
19. [pending] Integrate the `Notifier` class for alerts.
20. [pending] Complete all documentation.
