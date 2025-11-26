# Market-Agnostic Framework

## 1. Overview

The `ibkr_quant_core` repository has been architected as a market-agnostic trading framework. This design allows the core logic for strategy development, risk management, and execution safety to be completely decoupled from the specific details of any single broker or market.

The primary goal is to enable the framework to be extended to support various markets (e.g., different brokers for equities, cryptocurrencies, or even non-financial markets) without modifying the core codebase. This is achieved through a powerful abstraction layer.

## 2. The Abstraction Layer: `src/interfaces.py`

The heart of this architecture is the `src/interfaces.py` file, which defines a set of abstract base classes (ABCs). These interfaces act as a formal "contract" that any market-specific implementation must adhere to.

-   `IConnection`: Defines the standard for connecting to and disconnecting from a market's API.
-   `IDataLoader`: Defines the standard for fetching historical and real-time market data.
-   `IExecutionHandler`: Defines the standard for placing, canceling, and querying orders.
-   `IMarketAdapter`: A composite interface that bundles the three components above into a single, cohesive unit.

## 3. Market Adapters: The "Plug-ins"

A "Market Adapter" is a concrete implementation of the `IMarketAdapter` interface for a specific market. It contains all the necessary logic to interact with that market's API, handle its specific data formats, and manage its order types.

All market adapters are located in the `src/market_adapters/` directory, with each market having its own subdirectory (e.g., `src/market_adapters/ibkr/`).

### The IBKR Adapter

The initial and reference implementation is the `IBKRMarketAdapter`, which handles all interactions with the Interactive Brokers API via the `ib_insync` library. It consists of:

-   `IBConnection`: Implements `IConnection`.
-   `IBKRDataLoader`: Implements `IDataLoader`.
-   `IBKRExecutionHandler`: Implements `IExecutionHandler`.
-   `IBKRMarketAdapter`: The composite class that bundles them all.

## 4. How to Extend the Framework (Adding a New Market)

To add support for a new market (e.g., a cryptocurrency exchange), you would follow these steps:

1.  **Create a New Directory**:
    Create a new subdirectory under `src/market_adapters/`, for example, `src/market_adapters/new_market/`.

2.  **Implement the Interfaces**:
    Inside this new directory, create Python classes that inherit from and implement the methods defined in `src/interfaces.py`.
    -   `NewMarketConnection(IConnection)`
    -   `NewMarketDataLoader(IDataLoader)`
    -   `NewMarketExecutionHandler(IExecutionHandler)`

3.  **Create the Composite Adapter**:
    Create a final class, `NewMarketAdapter(IMarketAdapter)`, that bundles your new concrete implementations together.

4.  **Instantiate and Use**:
    In your main application entry point, you can now instantiate your `NewMarketAdapter`. This adapter object can then be passed to the `BaseStrategy` or any other part of the core framework, which will be able to use it without knowing any of the implementation details.

## 5. Benefits of this Architecture

-   **Extensibility**: Adding new markets is straightforward and does not require changes to the core, battle-tested logic.
-   **Reusability**: The core framework can be installed as a Python package (`pip install .`) and used in other projects. A separate project can provide its own market adapter implementation.
-   **Testability**: Market-specific logic is isolated, making it easier to test each component independently.
-   **Maintainability**: The clear separation of concerns makes the codebase easier to understand, debug, and maintain over time.
