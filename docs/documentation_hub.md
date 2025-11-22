# documentation hub

This documentation provides a detailed overview of the ibkr open-core algorithmic trading bot. Each section covers a specific part of the system's architecture and logic.

## documentation index

-   **[project plan](../PROJECT_PLAN.md)**
    -   outlines the planned phases and tasks for the project's development.

-   **[core infrastructure](./core_infrastructure.md)**
    -   explains the foundational modules for connecting to interactive brokers, loading data, and sending notifications.

-   **[strategy development](./strategy_development.md)**
    -   details the base strategy class, risk management framework, and the implementation of a simple example strategy.
        *   **[simple ma crossover formulation](./formulations/simple_ma_crossover_formulation.md)**: mathematical formulation for the simple ma crossover strategy.

-   **[backtesting and reporting](./backtest_runners/backtesting_and_reporting.md)**
    -   covers the process of running backtests, generating performance reports, and interpreting the results.

-   **[interpreting report](./interpreting_report.md)**
    -   provides detailed explanations of the various performance metrics found in backtest reports.
