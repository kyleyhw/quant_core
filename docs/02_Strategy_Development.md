# Strategy Development

The strategies for this trading bot are built upon a hierarchical framework designed to separate risk management from signal generation. This is achieved through a parent `BaseStrategy` class and child classes for specific strategies.

## 1. The Base Strategy (`strategies/base_strategy.py`)

### Purpose
The `BaseStrategy` class serves as the foundation for all trading strategies within the project. Its primary purpose is to enforce a consistent risk management framework and to provide common utilities that can be inherited by all child strategies. This promotes code reuse and ensures that core logic is not duplicated.

### Design and Logic
-   **Inheritance**: `BaseStrategy` inherits from `backtesting.lib.TrailingStrategy`. This choice was made to natively incorporate a percentage-based trailing stop-loss, which is a more dynamic risk management technique than a fixed stop-loss price.
-   **Configurable Risk Parameters**: The class defines several key risk parameters at the class level:
    -   `risk_percent`: The portion of equity to risk on a single trade.
    -   `stop_loss_pct`: The percentage drop from the entry price that triggers the initial stop-loss. This is also used as the trailing stop percentage.
    -   `take_profit_pct`: The percentage gain from the entry price that triggers a take-profit order.
    These parameters can be easily overridden in child strategies or tuned during optimization.
-   **Position Sizing**: The `calculate_position_size` method is intended to provide a standardized way to determine the size of a trade. In its current implementation for the `backtesting.py` library, it returns a fixed fraction of the portfolio to invest. *Note: A more sophisticated implementation would calculate the exact number of shares based on the stop-loss distance and the amount of equity being risked, but this often requires a more complex setup in many backtesting libraries.*
-   **Exit Logic**: The `next` method in `BaseStrategy` contains generic logic to close a position if the `take_profit_pct` is reached. The trailing stop-loss is handled automatically by the parent `TrailingStrategy`. By calling `super().next()` from a child strategy, this exit logic is preserved.

## 2. Example Strategy (`strategies/simple_demo.py`)

### Purpose
The `SimpleMACrossover` class is a public, example strategy that demonstrates how to build upon the `BaseStrategy`. It implements a classic and easily understood trading signal: the moving average crossover.

### Design and Logic
-   **Inheritance**: It inherits directly from `BaseStrategy`, and therefore gains all of its risk management features.
-   **Signal Generation**: The core logic is in the `next` method:
    1.  It uses the `crossover()` function from the `backtesting.lib` to detect the exact bar on which the fast moving average crosses above the slow one.
    2.  If this signal occurs and no position is currently open, it calls `self.buy_instrument()`, a method inherited from `BaseStrategy`.
    3.  A sell signal is generated if the slow MA crosses back over the fast MA, which closes the open position.
-   **Indicator Handling**: The strategy expects the moving average indicators to be **pre-calculated** on the data `DataFrame` before being passed to the `Backtest` object. In the `init` method, it accesses these indicator columns (e.g., `self.data.SMA_10`) and assigns them to class attributes for use in the `next` method. This design choice is explained further in the Backtesting documentation.
