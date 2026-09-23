# Documentation Hub

An overview of `quant_core`, the platform, and how to build on it.

## Start here

-   **[Market-Agnostic Framework](./market_agnostic_framework.md)**: the plug-and-play architecture, the abstract interfaces, and how to add a market adapter.
-   **[Building on quant-core](./building_on_quant_core.md)**: register your own strategies and `qc` commands from a separate package, carry quant-core as a submodule or depend on a release tag, and run the conformance test.
-   **[CLI Reference](./cli_usage.md)**: every `qc` command and option.

## Strategies

-   **[Strategy Development](./strategy_development.md)**: the `BaseStrategy` contract (`on_bar()`, `on_init()`), risk management, and sizing.
    *   **[Simple MA Crossover](./strategies/simple_ma_crossover.md)**
    *   **[RSI 2-Period](./strategies/rsi_2_period.md)**
    *   **[Bollinger Bands](./strategies/bollinger_bands.md)**
-   **[Feature Engineering](./feature_engineering.md)**: the shared indicator module that training and inference must both use.

## Running and reading backtests

-   **[Backtesting and Reporting](./backtesting_and_reporting.md)**: `qc backtest`, `qc benchmark`, and what they write.
-   **[Interpreting Reports](./interpreting_report.md)**: every metric in a report.
-   **[Financial Glossary](./financial_glossary.md)**: terms used throughout.

## Data

-   **[Data Management](./data_management.md)**: the smart data loader and its caches.
-   **[Datasets](./datasets.md)**: the sample data shipped with the repository.

## Operations and quality

-   **[Core Infrastructure](./core_infrastructure.md)**: the IBKR adapter, the first concrete implementation of the interfaces.
-   **[Safety & Recovery](./safety_and_recovery.md)**: "fat finger" hard limits and crash protocols.
-   **[Code Quality](./code_quality.md)**: linting, formatting, type checking, tests and CI.

Releases and migration notes are in the [changelog](../CHANGELOG.md), and the
roadmap is in the [project plan](../PROJECT_PLAN.md).
