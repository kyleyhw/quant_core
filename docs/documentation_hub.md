# Documentation Hub

This documentation provides a detailed overview of the `quant_core` framework and its components. Each section covers a specific part of the system's architecture and logic.

## Documentation Index

-   **[Market-Agnostic Framework](./market_agnostic_framework.md)**
    -   **The best place to start.** Explains the core plug-and-play architecture, abstract interfaces, and the process for extending the framework with new market adapters.

-   **[Core Infrastructure](./core_infrastructure.md)**
    -   Explains the foundational modules, focusing on the **IBKR Market Adapter** as the first concrete implementation of the core framework interfaces.

-   **[Strategy Development](./strategy_development.md)**
    -   Details the `BaseStrategy` class, the risk management framework, and the implementation of example strategies.
        *   **[Simple MA Crossover](./strategies/simple_ma_crossover.md)**: Mathematical formulation for the simple moving average crossover strategy.
        *   **[RSI 2-Period](./strategies/rsi_2_period.md)**: Mathematical formulation for the 2-period Relative Strength Index strategy.
        *   **[Bollinger Bands](./strategies/bollinger_bands.md)**: Mathematical formulation for the Bollinger Bands volatility strategy.

-   **[Backtesting and Reporting](./backtesting_and_reporting.md)**
    -   Covers the process of running backtests, generating performance reports, and interpreting the results.

-   **[Interpreting Report](./interpreting_report.md)**
    -   Provides detailed explanations of the various performance metrics found in backtest reports.

-   **[Safety & Recovery](./safety_and_recovery.md)**
    -   Details the "fat finger" hard limits, risk management settings, and protocols for handling system crashes.

-   **[Financial Glossary](./financial_glossary.md)**
    -   Definitions for common financial terms used throughout the project.
