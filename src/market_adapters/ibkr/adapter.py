# src/market_adapters/ibkr/adapter.py
from typing import Any
from src.interfaces import IMarketAdapter
from .connection import IBConnection
from .data_loader import IBKRDataLoader
from .execution import IBKRExecutionHandler

class IBKRMarketAdapter(IMarketAdapter):
    """
    Concrete implementation of the IMarketAdapter for Interactive Brokers.

    This class bundles the IB-specific connection, data loading, and
    execution handling components into a single, cohesive unit.
    """

    def __init__(self, **connection_params: Any) -> None:
        """
        Initializes the adapter and its components.

        Args:
            **connection_params: Connection parameters for IBConnection
                                 (e.g., host, port, client_id).
        """
        self.connection = IBConnection(**connection_params)
        self.data_loader = IBKRDataLoader(self.connection)
        self.execution_handler = IBKRExecutionHandler(self.connection)

