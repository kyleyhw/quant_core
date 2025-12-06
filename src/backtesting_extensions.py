from backtesting import Backtest
from backtesting.backtesting import _Broker
from functools import partial
from typing import Any
import pandas as pd

import inspect

class CustomBroker(_Broker):
    """
    A custom Broker implementation that supports callable commission models.
    """
    def __init__(self, spread: int = 0, **kwargs: Any) -> None:
        # Extract the real commission (which might be a callable)
        commission = kwargs.pop('commission', 0.0)
        
        # Check if parent _Broker expects 'spread'
        # Some versions of backtesting.py require it, others don't (or it was removed/added)
        sig = inspect.signature(_Broker.__init__)
        if 'spread' in sig.parameters:
            kwargs['spread'] = spread
        
        # Pass 0.0 to the parent class to bypass the float validation check
        super().__init__(commission=0.0, **kwargs)
        
        # Set the real commission on the instance
        self._commission = commission

    def _adjusted_price(self, size: float | None = None, price: float | None = None) -> float:
        """
        Adjusts the price to account for commission.
        Supports both float (percentage) and callable (dynamic) commission models.
        """
        price = price or self.last_price
        commission = self._commission
        
        if callable(commission):
            # Calculate the absolute commission amount for this trade
            # Note: backtesting.py passes 'size' as signed (positive for buy, negative for sell)
            # Our commission model expects (broker, trade, price) but here we only have size/price context
            # Wait, our ibkr_tiered_commission signature is (broker, trade, price).
            # But _adjusted_price doesn't have a 'trade' object yet because the trade isn't created!
            # It's called BEFORE creating the order/trade to estimate cost.
            
            # We need to adapt the signature or use a simpler one for estimation.
            # If we use the simpler (quantity, price) signature for estimation:
            comm_amount = commission(size, price)
            
            # Adjust price to include commission
            # For buy (size > 0): price + (comm / size) -> price increases
            # For sell (size < 0): price + (comm / size) -> price decreases (since size is negative)
            return price + (comm_amount / size)
            
        return super()._adjusted_price(size, price)

class CustomBacktest(Backtest):
    """
    A custom Backtest class that uses CustomBroker to support callable commissions.
    """
    def __init__(self, data: pd.DataFrame, strategy: Any, **kwargs: Any) -> None:
        # Extract commission to prevent validation error in super().__init__
        commission = kwargs.pop('commission', 0.0)
        
        # Initialize parent with 0.0 commission
        super().__init__(data, strategy, commission=0.0, **kwargs)
        
        # Inject our CustomBroker with the real commission
        # We need to recreate the partial with all the original arguments
        self._broker = partial(
            CustomBroker, 
            cash=kwargs.get('cash', 10_000), 
            commission=commission, 
            margin=kwargs.get('margin', 1.0),
            trade_on_close=kwargs.get('trade_on_close', False), 
            hedging=kwargs.get('hedging', False),
            exclusive_orders=kwargs.get('exclusive_orders', False), 
            spread=kwargs.get('spread', 0),
            index=data.index,
        )
