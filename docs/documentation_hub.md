# documentation hub

This documentation provides a detailed overview of the ibkr open-core algorithmic trading bot. Each section covers a specific part of the system's architecture and logic.

## documentation index

-   **[Market-Agnostic Framework](./market_agnostic_framework.md)**
    -   **START HERE.** Explains the core plug-and-play architecture, interfaces, and how to extend the framework to other markets.

-   **[project plan](../PROJECT_PLAN.md)**
    -   outlines the planned phases and tasks for the project's development.

-   **[core infrastructure](./core_infrastructure.md)**
    -   explains the foundational modules, focusing on the IBKR Market Adapter as a concrete implementation of the core framework.

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

-   **[safety & recovery](./safety_and_recovery.md)**
    -   details the "fat finger" hard limits, risk management settings, and protocols for handling system crashes.

-   **[financial glossary](./financial_glossary.md)**
    -   definitions for common financial terms.
