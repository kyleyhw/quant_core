# Core Infrastructure

The core infrastructure of the trading bot is handled by a set of modules within the `src/` directory. These modules provide the foundational services needed for the bot to operate, including connecting to the broker, fetching data, and sending notifications.

## 1. IBKR Connection (`src/connection.py`)

### Purpose
The `connection.py` module is responsible for establishing and managing the connection to the Interactive Brokers (IBKR) Trader Workstation (TWS) or Gateway. It abstracts the complexities of the `ib_insync` library's connection handling into a simple, reusable class.

### Design and Logic
-   **Asynchronous Operations**: The entire connection logic was refactored to be fully asynchronous using Python's `asyncio` library. This is a critical design choice because `ib_insync` is an async-native library. Using `async`/`await` ensures that network operations (like connecting or requesting data) are non-blocking, allowing the bot to remain responsive.
-   **`IBConnection` Class**: This class encapsulates the `ib_insync.IB` object. A single instance of this class can be created and passed to other modules (like the `DataLoader`), ensuring that all parts of the application share the same connection. This is an example of **Dependency Injection**.
-   **Environment Variables**: To maintain security and avoid hard-coding credentials, the connection parameters (host, port, client ID) are loaded from a `.env` file using the `python-dotenv` library. This allows for different configurations between development and production environments without code changes. The `.env` file is explicitly listed in `.gitignore` to prevent it from being committed to the repository.

## 2. Data Loading (`src/data_loader.py`)

### Purpose
The `data_loader.py` module provides a standardized interface for fetching market data from IBKR. Its primary goal is to ensure that data is retrieved and formatted consistently for use in other parts of the application, such as strategies or backtesting preparation.

### Design and Logic
-   **`DataLoader` Class**: This class requires an active `IBConnection` instance to be passed during initialization.
-   **Asynchronous Data Fetching**: Similar to the connection module, all data requests (`qualifyContractsAsync`, `reqHistoricalDataAsync`) are asynchronous to prevent blocking the application's event loop.
-   **Robust Contract Creation**: The `create_contract` method was designed to be robust. Instead of creating a contract with many `None` values (which the IBKR API can reject), it dynamically builds a dictionary of non-None parameters. This ensures that only relevant information is sent to the API, preventing errors for securities that do not have properties like `strike` or `right` (e.g., stocks, forex).
-   **Standardized DataFrame Format**: The `get_historical_data` method returns a `pandas.DataFrame` with standardized column names (`Open`, `High`, `Low`, `Close`, `Volume`). This consistency is crucial for the `backtesting` library and any other component that consumes this data.

## 3. Notifications (`src/notifications.py`)

### Purpose
The `notifications.py` module provides a simple way to send alerts to an external service. This is essential for monitoring the bot's status, receiving notifications about trades, or being alerted to critical errors that require manual intervention.

### Design and Logic
-   **`Notifier` Class**: A simple class that handles the formatting and sending of messages.
-   **Discord Webhook**: The initial implementation uses Discord webhooks, a common and easy-to-use notification method. The webhook URL is loaded from the `DISCORD_WEBHOOK_URL` environment variable, again ensuring that this secret is not hard-coded.
-   **Severity Levels**: The `send` method includes a `Severity` enum (`INFO`, `WARNING`, `ERROR`, `CRITICAL`). This allows for color-coded and prioritized messages in Discord, making it easy to distinguish between routine updates and urgent problems at a glance.
-   **Error Handling**: The `send` method includes `try...except` blocks to gracefully handle network errors or an unset webhook URL, preventing the entire bot from crashing if a notification fails to send.
