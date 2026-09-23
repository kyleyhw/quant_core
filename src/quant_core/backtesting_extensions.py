"""Engine extensions.

This module used to carry a ``CustomBroker`` / ``CustomBacktest`` pair whose job
was to teach ``backtesting.py`` about callable commission models. The library has
supported them natively since 0.6: ``_Broker.__init__`` keeps a callable as-is,
and ``_process_orders`` charges it on each fill. The custom pair was therefore
not merely redundant, it was wrong in three ways:

* **Commission was charged twice**, once in its ``_adjusted_price`` override and
  again in the engine's own order processing. On an eleven-trade run against the
  test fixture this cost about 3.2 percentage points of return.
* **Float commissions crashed.** ``CustomBroker.__init__`` passed ``0.0`` to the
  parent, which wrapped it into ``_commission_func``, then overwrote
  ``self._commission`` with the raw value. A later call raised
  ``TypeError: 'float' object is not callable``. Three of the four entries in
  :data:`src.commission_models.COMMISSION_MODELS` are floats, so most of the
  dashboard's commission options could not complete a run.
* **Spread was silently discarded**, because the ``_adjusted_price`` override
  replaced the parent's spread adjustment rather than extending it.

``CustomBacktest`` remains as a deprecated alias so existing imports keep
working, including any in the private strategies submodule. New code should use
``backtesting.Backtest`` directly.
"""

from backtesting import Backtest

__all__ = ["CustomBacktest"]


class CustomBacktest(Backtest):
    """Deprecated alias for :class:`backtesting.Backtest`.

    Kept only so existing imports resolve. See the module docstring for why the
    original implementation was removed.
    """
