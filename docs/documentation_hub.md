# documentation hub

This documentation provides a detailed overview of the ibkr open-core algorithmic trading bot. Each section covers a specific part of the system's architecture and logic.

## documentation index

-   **[project plan](../PROJECT_PLAN.md)**
    -   outlines the planned phases and tasks for the project's development.

-   **[core infrastructure](./core_infrastructure.md)**
    -   explains the foundational modules for connecting to interactive brokers, loading data, and sending notifications.

-   **[feature engineering](./feature_engineering.md)**
    -   technical indicator definitions and usage.

-   **[strategy development](./strategy_development.md)**
    -   details the base strategy class, risk management framework, and the implementation of a simple example strategy.
        *   **[simple ma crossover](./strategies/simple_ma_crossover.md)**: mathematical formulation for the simple ma crossover strategy.
        *   **[rsi 2-period](./strategies/rsi_2_period.md)**: mathematical formulation for the rsi 2-period strategy.
        *   **[bollinger bands](./strategies/bollinger_bands.md)**: mathematical formulation for the bollinger bands strategy.

-   **[backtesting and reporting](./run_backtesting/backtesting_and_reporting.md)**
    -   covers the process of running backtests, generating performance reports, and interpreting the results.

-   **[interpreting report](./interpreting_report.md)**
    -   provides detailed explanations of the various performance metrics found in backtest reports.

-   **[financial glossary](./finance_glossary.md)**
    -   definitions for common financial terms.
