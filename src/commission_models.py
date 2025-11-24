"""
This module contains functions that model various broker commission structures
for use in the backtesting engine.
"""

def ibkr_tiered_commission(quantity: int, price: float) -> float:
    """
    Calculates trade commission based on the Interactive Brokers (IBKR) Pro
    Tiered pricing structure for US stocks.

    This model uses the rates for the lowest volume tier (<= 300,000 shares/month).
    It does not include exchange, clearing, or regulatory fees for simplicity.

    Args:
        quantity: The number of shares traded (positive for buy, negative for sell).
        price: The execution price per share.

    Returns:
        The calculated commission fee for the trade.
    """
    # --- Commission Rates (as of late 2025 for US stocks) ---
    PER_SHARE_RATE = 0.0035
    MINIMUM_PER_ORDER = 0.35
    MAXIMUM_PERCENT_OF_TRADE_VALUE = 0.01  # 1%

    trade_value = abs(quantity) * price
    
    # Calculate base commission
    commission = abs(quantity) * PER_SHARE_RATE
    
    # Enforce maximum
    max_commission = MAXIMUM_PERCENT_OF_TRADE_VALUE * trade_value
    commission = min(commission, max_commission)
    
    # Enforce minimum
    commission = max(commission, MINIMUM_PER_ORDER)
    
    return commission
