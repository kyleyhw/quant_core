import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

class ExecutionManager:
    """
    Handles generic order validation and safety checks before submission.
    This class is market-agnostic and acts as a 'Fat Finger' defense layer.
    It operates on a standardized dictionary of order details.
    """

    # Hard limits - strictly enforced
    MAX_SHARES_PER_ORDER = 100
    MAX_DOLLAR_VALUE_PER_ORDER = 5000.0
    MAX_PRICE_DEVIATION_PERCENT = 0.05  # 5% deviation from current price

    def __init__(self):
        pass

    def check_order_limits(self, order_details: Dict[str, Any], current_price: float) -> bool:
        """
        Validates an order against hard-coded safety limits using a generic
        order dictionary.

        Args:
            order_details: A dictionary containing order information.
                           Expected keys: 'quantity', 'order_type', 'limit_price', 'symbol'.
            current_price: The current market price of the asset.

        Returns:
            True if the order is safe to execute.

        Raises:
            ValueError: If any safety limit is violated.
        """
        symbol = order_details.get('symbol', 'UNKNOWN')
        quantity = order_details.get('quantity', 0)
        order_type = order_details.get('order_type', 'MKT')
        limit_price = order_details.get('limit_price', 0.0)

        # 1. Check Max Shares
        if quantity > self.MAX_SHARES_PER_ORDER:
            msg = (f"SAFETY BLOCK: Order quantity {quantity} exceeds "
                   f"limit of {self.MAX_SHARES_PER_ORDER} for {symbol}.")
            logger.critical(msg)
            raise ValueError(msg)

        # 2. Check Max Dollar Value
        exec_price = limit_price if order_type in ['LMT', 'STOP_LIMIT'] else current_price
        if exec_price is None or exec_price == 0:
             exec_price = current_price

        estimated_value = exec_price * quantity

        if estimated_value > self.MAX_DOLLAR_VALUE_PER_ORDER:
            msg = (f"SAFETY BLOCK: Order value ${estimated_value:.2f} exceeds "
                   f"limit of ${self.MAX_DOLLAR_VALUE_PER_ORDER} for {symbol}.")
            logger.critical(msg)
            raise ValueError(msg)

        # 3. Fat Finger Price Check (only for Limit orders)
        if order_type in ['LMT', 'STOP_LIMIT'] and limit_price > 0:
            if current_price > 0: # Avoid division by zero
                deviation = abs(limit_price - current_price) / current_price
                if deviation > self.MAX_PRICE_DEVIATION_PERCENT:
                    msg = (f"SAFETY BLOCK: Limit price {limit_price} deviates "
                           f"{deviation*100:.2f}% from market price {current_price} for {symbol}. "
                           f"Max allowed is {self.MAX_PRICE_DEVIATION_PERCENT*100}%.")
                    logger.critical(msg)
                    raise ValueError(msg)

        logger.info(f"Order validated: {order_details.get('action')} {quantity} {symbol} @ {exec_price}")
        return True

