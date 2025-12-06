# src/interfaces.py

from abc import ABC, abstractmethod
from typing import Any, Dict
import pandas as pd

class IConnection(ABC):
    """
    Abstract base class for a connection to a market data provider or broker API.
    Defines the standard interface for connecting, disconnecting, and checking
    the connection status.
    """
    @abstractmethod
    def connect(self, **kwargs: Any) -> None:
        """Establish a connection to the market."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the market."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the connection is active."""
        pass


class IDataLoader(ABC):
    """
    Abstract base class for loading market data. Defines a standard interface
    for fetching historical data, acknowledging that the data structure may
    vary significantly between different markets.
    """
    @abstractmethod
    def get_historical_data(self, symbol: str, timeframe: str, start: str, end: str, **kwargs: Any) -> pd.DataFrame:
        """
        Fetch historical market data.

        While the return type is a pandas DataFrame, the structure may vary
        (e.g., OHLCV bars for equities vs. event-driven sales data for other
        asset types).
        """
        pass


class IExecutionHandler(ABC):
    """
    Abstract base class for handling order execution. Defines a standard
    interface for placing, cancelling, and querying orders, abstracting away
    the specific order types and contract details of a given market.
    """
    @abstractmethod
    def place_order(self, order_details: Dict[str, Any]) -> Any:
        """
        Place an order in the market.

        Args:
            order_details: A dictionary containing all necessary information
                           to execute the order (e.g., symbol, quantity,
                           order_type).

        Returns:
            An order identifier for tracking.
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: Any) -> bool:
        """
        Cancel an existing order.

        Args:
            order_id: The unique identifier of the order to be cancelled.

        Returns:
            True if cancellation was successful, False otherwise.
        """
        pass

    @abstractmethod
    def get_order_status(self, order_id: Any) -> Dict[str, Any]:
        """
        Retrieve the current status of an order.

        Args:
            order_id: The unique identifier of the order.

        Returns:
            A dictionary containing status information (e.g., 'filled',
            'cancelled', 'pending').
        """
        pass


class IMarketAdapter(ABC):
    """
    Abstract composite class that bundles all market-specific components.

    This adapter provides a single, unified interface for the core application
    to interact with a specific market, abstracting away the underlying
    details of the connection, data loading, and order execution. An instance
    of a concrete implementation of this class should be the single entry
    point for all market-specific interactions.
    """
    connection: IConnection
    data_loader: IDataLoader
    execution_handler: IExecutionHandler

    def __init__(self, connection: IConnection, data_loader: IDataLoader, execution_handler: IExecutionHandler) -> None:
        self.connection = connection
        self.data_loader = data_loader
        self.execution_handler = execution_handler