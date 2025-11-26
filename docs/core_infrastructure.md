# Core Infrastructure: An Abstract Framework with a Concrete Implementation

The core infrastructure of the trading bot is defined by a market-agnostic framework centered around a set of abstract interfaces. The concrete, operational logic for a specific market—in this case, Interactive Brokers—is provided as an **instantiation** of this framework.

## 1. The Abstract Framework (`src/interfaces.py`)

The foundation of the entire system is the set of abstract base classes in `src/interfaces.py`. These interfaces define a "contract" for what a market implementation must provide:

-   **`IConnection`**: A contract for connecting to and disconnecting from a broker.
-   **`IDataLoader`**: A contract for fetching historical market data.
-   **`IExecutionHandler`**: A contract for placing and managing orders.
-   **`IMarketAdapter`**: A composite class that bundles the above components into a single, cohesive "plug-in" for a market.

For more details, refer to the main **[Market-Agnostic Framework](./market_agnostic_framework.md)** documentation.

## 2. The Interactive Brokers (IBKR) Market Adapter

The first concrete implementation of the abstract framework is the IBKR Market Adapter, located in `src/market_adapters/ibkr/`. This adapter contains all the logic necessary to connect to, fetch data from, and execute trades with Interactive Brokers.

### IBKR Connection (`src/market_adapters/ibkr/connection.py`)

-   **Purpose**: Implements the `IConnection` interface for Interactive Brokers.
-   **Logic**: It encapsulates the `ib_insync.IB` object and manages the connection to TWS or Gateway. Connection parameters (host, port, etc.) are securely loaded from a `.env` file.

### IBKR Data Loader (`src/market_adapters/ibkr/data_loader.py`)

-   **Purpose**: Implements the `IDataLoader` interface.
-   **Logic**: It requires an active `IBConnection` instance. Its `get_historical_data` method translates a generic request into a specific `ib_insync.reqHistoricalData` call and formats the returned data into a standardized `pandas.DataFrame`.

### IBKR Execution Handler (`src/market_adapters/ibkr/execution.py`)

-   **Purpose**: Implements the `IExecutionHandler` interface.
-   **Logic**: This module is responsible for translating a generic order dictionary into IBKR-specific `Contract` and `Order` objects. It then uses the active connection to place, cancel, and monitor trades.

## 3. The Market-Agnostic Safety Layer (`src/execution.py`)

Crucially, the `ExecutionManager` that handles "fat finger" checks now sits **outside** of any market-specific implementation.

-   **Purpose**: To provide a universal, market-agnostic safety layer.
-   **Logic**: It operates on a standardized Python dictionary representing an order. It checks this dictionary for violations of hard-coded limits (e.g., max order size, max dollar value) *before* the order is ever passed to a concrete market adapter like the IBKR one. This ensures that the core risk management rules are enforced consistently, regardless of which market is being traded.
