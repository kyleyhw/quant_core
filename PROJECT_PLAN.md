# Project Development Plan

This document outlines the planned phases and tasks for developing the IBKR Open-Core Algorithmic Trading Bot.

## Phase 1: Core Infrastructure Setup
1.  [completed] Verify and finalize the project directory structure.
2.  [completed] Populate `requirements.txt` with all necessary libraries.
3.  [completed] Implement the IBKR connection logic in `src/connection.py`.
4.  [completed] Implement standardized data fetching in `src/data_loader.py`.
5.  [completed] Create the base `Notifier` class in `src/notifications.py`.
6.  [completed] Set up initial documentation, including `README.md` and the `/docs` folder structure.
7.  [completed] Migrate dependency management to `uv` (`pyproject.toml`, `uv.lock`).

## Phase 2: Base Strategy & Backtesting Framework
8.  [completed] Develop the parent `base_strategy.py` to handle position sizing and stop-loss logic.
8.  [completed] Create a public `simple_ma_crossover.py` strategy (e.g., a moving average crossover) inheriting from the base strategy.
9.  [completed] Implement the backtesting script `run_backtesting/run_backtest.py` to test a single strategy.
10. [completed] Generate the first backtest report and save it to the `strategies/reports/` directory.

## Phase 3: Feature Engineering & ML Model Training
11. [completed] Develop the shared `src/feature_engineering.py` module with common technical indicators.
12. [completed] Create a script in research/ for model training.
    - [completed] Created `research/train_regime_model.py` (XGBoost regime classifier)
    - [completed] Created `research/utils.py` (simplified data fetching)
    - [completed] Run script to train and save model
13. [completed] Save the trained model artifact to the `strategies_private/models/` directory.

## Phase 4: Machine Learning Strategy Implementation
14. [completed] Create a private strategy in `strategies_private/` that uses a trained model.
15. [completed] Backtest the ML-based strategy.

## Phase 5: Advanced Strategy Development
21. [completed] Acquire and document datasets for pairs trading (GLD/GDX).
22. [completed] Implement and train a Hidden Markov Model (HMM) for regime detection.
23. [completed] Implement a private HMM-based trading strategy.
24. [completed] Backtest the HMM strategy.
25. [completed] Implement a private Pairs Trading strategy.
26. [completed] Backtest the Pairs Trading strategy.

## Phase 6: Safety & Infrastructure
27. [completed] Implement the `execution.py` module with safety checks.
    - [completed] Hard limits (Max Shares, Max Dollar, Price Deviation).
28. [completed] Develop System Safety & Recovery Protocols.
    - [completed] Define Crash Recovery steps (State reconciliation).
    - [completed] Implement Heartbeat/System Health monitoring (via `tools/supervisor.py`).
    - [completed] Create `docs/safety_and_recovery.md`.
    - [pending] (Future) Implement External Heartbeat (Dead Man's Switch) for Supervisor monitoring.

## Phase 7: System Finalization
29. [completed] Implement the strategy benchmarking script `run_backtesting/benchmark.py`.
30. [completed] Integrate the `Notifier` class for alerts.
31. [completed] Complete all documentation.

## Phase 8: Expanded Strategy Research (Planning)
32. [pending] Brainstorm new strategy concepts (e.g., Sentiment Analysis, Statistical Arbitrage, Reinforcement Learning).
33. [pending] Select candidates for implementation.
34. [pending] Backtest and validate new strategies.

## Phase 9: High-Frequency & Intraday Strategy Research
35. [pending] Research Intraday Logic (VWAP, Order Flow Imbalance).
36. [pending] Implement Intraday Data Handling (1-minute / 5-minute bars).
37. [pending] Develop Intraday Strategy (e.g., Gap & Go, Mean Reversion).

## Phase 10: Web UI Dashboard (Streamlit)
38. [completed] Create `dashboard/app.py`.
39. [completed] Implement Strategy & Asset selectors.
40. [completed] Visualize Backtest Results (Equity Curve, Drawdown, Trade Log).

## Phase 11: Paper Trading & Live Execution
41. [pending] Integrate the execution module with the base strategy.
    - [pending] Route every live order through `ExecutionManager.check_order_limits`.
      `BaseStrategy.buy_instrument` / `sell_instrument` currently call the adapter
      directly, so the documented "fat finger" gate is not in the live path.
42. [pending] Set up Paper Trading environment.
    - [pending] Implement streaming bar subscription in the IBKR data loader.
      `IBKRDataLoader` only implements `get_historical_data`; nothing feeds a
      strategy in real time.
    - [pending] Build the live runner: an event-driven entry point that advances a
      strategy per bar. `BaseStrategy.next` is backtest-only today.
    - [pending] Track order lifecycle through `ib_insync` callbacks (fills, partial
      fills, rejections). `get_order_status` reads a snapshot once.
    - [pending] Reconcile state against IBKR positions on startup, as described in
      `docs/safety_and_recovery.md`. No code implements this yet.
43. [pending] Conduct "Dry Run" with live market data (no execution).
44. [pending] Begin Paper Trading with small capital allocation.

## Phase 12: Dashboard Rebuild
Supersedes the Streamlit dashboard delivered in Phase 10. Direction: the "Ledger
surface, Desk structure" merge from the design canvas
(https://claude.ai/artifact/29p1Qjgebz9qRHS8f3nnhb).

45. [pending] Establish the design system: colour tokens, type scale, and the
    Spectral / IBM Plex Sans / IBM Plex Mono stack, injected as CSS.
46. [pending] Build the application shell: nav rail, masthead, specification strip,
    tab bar.
47. [pending] Build the run configuration drawer. Must expose strategy parameters,
    universe, period, data source, capital, commission, and the three
    `base_strategy` risk parameters, which the current UI does not surface at all.
48. [pending] Add a run history store so runs persist and can be reloaded and
    compared. Today each run overwrites the last.
49. [pending] Replace the embedded `backtesting.py` Bokeh HTML with native equity and
    drawdown charts sharing one x axis.
50. [pending] Overview tab: six headline figures plus a plain-language reading of the
    result.
51. [pending] Trades tab.
52. [pending] Metrics tab, grouped into Returns, Risk, Trade Quality, and Run Details
    instead of the current unsorted stats dump.
53. [pending] Execution log tab, surfacing `ExecutionManager` blocks and `Notifier`
    events, which are invisible in the UI today.
54. [pending] Benchmark screen: strategy matrix, return-against-drawdown scatter, and
    overlaid equity curves. `run_backtesting/benchmark.py` currently has no UI.
55. [pending] Reports screen for browsing and exporting `strategies/reports/`.
56. [pending] Paper trading monitor screen (depends on Phase 11 and Phase 13).
57. [pending] Tests for dashboard helpers and a smoke test that the app renders.

## Phase 13: Account-Level Risk Controls
The limits in `src/execution.py` are per-order only. A per-order cap cannot stop a
slow bleed across many orders.

58. [pending] Daily loss limit, measured against a configurable reset time, counting
    open position P&L.
59. [pending] Total drawdown limit against a persisted high-water mark.
60. [pending] Auto-flatten and halt on breach.
61. [pending] Kill switch reachable from both the dashboard and the CLI.
62. [pending] Persist risk state across restarts so a limit survives a crash.
63. [pending] Move hard limits out of class attributes into configuration.

## Phase 14: Testing, Quality & CI
The suite is currently three test methods across two files, run by hand.

64. [pending] Adopt `pytest` and migrate the existing `unittest` tests.
65. [pending] Unit tests for strategies, feature engineering, commission models, and
    the data loader.
66. [pending] Property-based tests for `ExecutionManager` using `hypothesis`, already
    a dev dependency but unused.
67. [pending] Regression tests pinning backtest metrics for a fixed dataset, so a
    refactor cannot silently change results.
68. [pending] GitHub Actions workflow running ruff, ty, and the test suite. There is
    no `.github/` directory today.
69. [pending] Coverage reporting.
70. [pending] Fold `testing/debug_scripts/` into the test suite or delete it.

## Phase 15: Operational Readiness
71. [pending] Structured logging to `logs/` with rotation.
72. [pending] External heartbeat / dead man's switch for the supervisor. Carried over
    from Phase 6, item 28.
73. [pending] Telegram notifier. `docs/safety_and_recovery.md` promises
    "Discord/Telegram" but `src/notifications.py` implements Discord only.
74. [pending] Daily summary notification at market close.
75. [pending] Deployment and operations runbook.

## Phase 16: Housekeeping
76. [pending] Implement or delete `src/metrics.py`, which is an empty file.
77. [pending] Replace the `main.py` hello-world stub, or remove it in favour of the
    `qc` console script.
78. [pending] Reconcile documentation with behaviour, including the safety and
    recovery doc's claims about reconciliation and notification channels.
