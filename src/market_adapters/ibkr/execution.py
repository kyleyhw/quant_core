# src/market_adapters/ibkr/execution.py
import logging
from typing import Any, Dict, Optional

from ib_insync import Contract, Order, IB
from src.interfaces import IExecutionHandler
from .connection import IBConnection

logger = logging.getLogger(__name__)

class IBKRExecutionHandler(IExecutionHandler):
    """
    Concrete implementation of the IExecutionHandler interface for Interactive Brokers.
    This class is responsible for translating generic order requests into
    IB-specific Contract and Order objects and submitting them.
    """

    def __init__(self, ib_connection: IBConnection):
        if not isinstance(ib_connection, IBConnection):
            raise TypeError("ib_connection must be an instance of IBConnection")
        self.ib_connection = ib_connection
        self.ib: IB = ib_connection.ib
        logger.info("IBKRExecutionHandler initialized.")

    def _create_contract(self, symbol: str, sec_type: str = 'STK', exchange: str = 'SMART', currency: str = 'USD') -> Optional[Contract]:
        """Creates and qualifies an IB Contract object."""
        contract = Contract(symbol=symbol, secType=sec_type, exchange=exchange, currency=currency)
        try:
            qualified_contracts = self.ib.qualifyContracts(contract)
            if not qualified_contracts:
                logger.warning(f"No contract details found for {symbol}")
                return None
            return qualified_contracts[0]
        except Exception as e:
            logger.error(f"Error qualifying contract for {symbol}: {e}")
            return None

    def _create_order(self, order_details: Dict[str, Any]) -> Order:
        """Creates an IB Order object from a generic dictionary."""
        return Order(
            orderType=order_details.get('order_type', 'MKT'),
            action=order_details.get('action', 'BUY'),
            totalQuantity=order_details.get('quantity', 0),
            lmtPrice=order_details.get('limit_price'),
            auxPrice=order_details.get('stop_price')
        )

    def place_order(self, order_details: Dict[str, Any]) -> Any:
        """
        Places an order with Interactive Brokers.

        Args:
            order_details (Dict[str, Any]): A dictionary with order info, e.g.,
                {
                    'symbol': 'SPY',
                    'quantity': 10,
                    'order_type': 'LMT',
                    'action': 'BUY',
                    'limit_price': 450.50
                }
        Returns:
            The IB Trade object if the order is placed successfully.
        """
        if not self.ib_connection.is_connected():
            logger.error("Cannot place order: Not connected to IB.")
            return None

        contract = self._create_contract(order_details.get('symbol'))
        if not contract:
            logger.error(f"Could not create contract for {order_details.get('symbol')}, order cancelled.")
            return None

        order = self._create_order(order_details)

        try:
            trade = self.ib.placeOrder(contract, order)
            logger.info(f"Placed order: {trade}")
            return trade
        except Exception as e:
            logger.error(f"Error placing order for {contract.symbol}: {e}")
            return None

    def cancel_order(self, order_id: Any) -> bool:
        """
        Cancels an order. For ib_insync, the order_id is the Order object
        from the Trade returned by place_order.
        """
        if not isinstance(order_id, Order):
            logger.error("To cancel an IB order, the 'order_id' must be the ib_insync Order object.")
            return False
        
        if not self.ib_connection.is_connected():
            logger.error("Cannot cancel order: Not connected to IB.")
            return False
            
        try:
            self.ib.cancelOrder(order_id)
            logger.info(f"Cancellation request sent for orderId {order_id.orderId}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order {order_id.orderId}: {e}")
            return False

    def get_order_status(self, order_id: Any) -> Dict[str, Any]:
        """
        Retrieves the status of an order. For ib_insync, we can check the
        status of the Trade that contains the order.
        """
        # This is a simplified example. A robust implementation would involve
        # tracking trade statuses via callbacks.
        if hasattr(order_id, 'orderStatus'):
            return {
                "status": order_id.orderStatus.status,
                "filled": order_id.orderStatus.filled,
                "remaining": order_id.orderStatus.remaining,
                "avgFillPrice": order_id.orderStatus.avgFillPrice
            }
        return {"status": "Unknown"}
