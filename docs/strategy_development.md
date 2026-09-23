# Strategy Development

Strategies separate two concerns. `BaseStrategy` owns risk management: the trailing
stop, the take-profit and position sizing. A strategy subclass supplies only its
entry and exit signals. This page describes that contract as of quant-core 0.2.0.

## The base strategy (`quant_core.strategies.base_strategy.BaseStrategy`)

`BaseStrategy` extends `backtesting.lib.TrailingStrategy` and can run under the
backtest engine or, later, against a live market adapter.

### The contract

- **Implement `on_bar()`, never `next()`.** `BaseStrategy.next()` runs once per
  bar. It attaches a take-profit to any open trade that lacks one, calls your
  `on_bar()`, then ratchets the trailing stop. Defining `next()` in a subclass
  raises `TypeError` when the class is created, because a subclass that forgot to
  call up used to trade with no stop at all.
- **Put setup in `on_init()`.** It runs after the base class has armed risk
  management. Only override `init()` if you genuinely need to, and call up.
- **Enter with `_default_buy()` or `_default_sell()`.** They size the order from
  the risk parameters below. Close with `self.position.close()`.

### Risk parameters

Declared as class attributes, so a subclass or an optimiser can override them:

| Attribute | Default | Meaning |
| :--- | :--- | :--- |
| `stop_loss_pct` | `0.02` | Trailing stop distance below the running peak, as a fraction of price. `0` disables it. |
| `take_profit_pct` | `0.05` | Profit target from the entry price. `0` disables it. |
| `risk_percent` | `0.01` | Fraction of equity a single stop-out should cost. |

Position size is `risk_percent / stop_loss_pct` of equity, capped at 1.0, so the
defaults commit half the account: a 2% adverse move on half the account is a 1%
loss. With no stop, size falls back to fully invested. `calculate_position_size()`
returns that fraction, and `calculate_order_quantity(price, equity)` turns it
into whole units for the live path.

A strategy that genuinely wants no stop and full size should say so explicitly,
with `stop_loss_pct = 0` and `take_profit_pct = 0`, rather than working around
the base class.

### Other class attributes the platform reads

- `data_assets` (default `1`): set to `2` for a strategy that trades a pair. The
  backtest runner and dashboard then merge two inputs with `_1` and `_2`
  suffixed columns, and the benchmark skips it.
- `underlying_strategy`: for a wrapper that drives another strategy. Register a
  subclass that sets it; the benchmark skips a wrapper with it left as `None`.

### A minimal strategy

```python
import numpy as np

from quant_core.strategies.base_strategy import BaseStrategy


class Breakout(BaseStrategy):
    lookback = 20
    stop_loss_pct = 0.03  # override a risk parameter

    def on_bar(self) -> None:
        if len(self.data.Close) <= self.lookback:
            return
        high = np.max(self.data.High[-self.lookback - 1 : -1])
        if not self.position and self.data.Close[-1] > high:
            self._default_buy()
```

Register it so the platform can find it; see
[Building on quant-core](./building_on_quant_core.md). To check it honours its
risk parameters, run the conformance test described there.

## Reference strategies

The public strategies exist to exercise and document platform features. None is
expected to have an edge.

### Simple moving average crossover (`quant_core.strategies.simple_ma_crossover`)

Enters long when a fast simple moving average crosses above a slow one, and
exits when it crosses back below, or on the base class's stop or take-profit.
Both averages are computed with `numpy` inside `on_bar()` from the recent closes.

-   **[simple ma crossover](./strategies/simple_ma_crossover.md)**: detailed mathematical description of the strategy's signals.

### RSI 2-period (`quant_core.strategies.rsi_2_period`)

Computes a 2-period relative strength index in `on_bar()`. Enters long when it
crosses below the oversold threshold and exits when it crosses above the
overbought threshold.

-   **[rsi 2-period](./strategies/rsi_2_period.md)**: detailed mathematical description of the strategy's signals.

### Bollinger bands (`quant_core.strategies.bollinger_bands`)

Computes the bands in `on_bar()`. Enters long when price crosses below the lower
band and exits when it crosses back above the middle band.

-   **[bollinger bands](./strategies/bollinger_bands.md)**: detailed mathematical description of the strategy's signals.

### Buy and hold (`quant_core.strategies.buy_and_hold`)

The baseline. It extends `backtesting.Strategy` directly and declares no risk
parameters.
