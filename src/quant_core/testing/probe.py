"""Helper for observing a strategy's risk management from inside a backtest."""

from dataclasses import dataclass, field
from typing import Any

from backtesting import Backtest

CASH = 10_000


@dataclass
class Observation:
    """One open trade, as seen at the top of a bar."""

    bar: int
    close: float
    entry: float
    size: float
    sl: float | None
    tp: float | None

    @property
    def stop_distance_pct(self) -> float | None:
        """
        How far the stop sits from the close, as a fraction of the close.

        Measured on the losing side of the trade: below the close for a long,
        above it for a short. Positive whenever the stop is where it should be.
        """
        if self.sl is None or self.close <= 0:
            return None
        gap = self.close - self.sl if self.size > 0 else self.sl - self.close
        return gap / self.close


@dataclass
class ProbeResult:
    stats: Any
    observations: list[Observation] = field(default_factory=list)

    def with_stop(self) -> list[Observation]:
        return [o for o in self.observations if o.sl is not None]

    def mean_stop_distance_pct(self) -> float:
        distances = [d for o in self.with_stop() if (d := o.stop_distance_pct) is not None]
        if not distances:
            raise AssertionError("no open trade ever carried a stop-loss")
        return sum(distances) / len(distances)


def probe(strategy_cls: type, data: Any, **params: Any) -> ProbeResult:
    """
    Runs `strategy_cls` over `data`, recording every open trade on every bar.

    The probe hooks `on_bar`, so it observes trades after take-profit has been
    armed and after the previous bar's trailing-stop update.
    """
    observations: list[Observation] = []

    class Probed(strategy_cls):  # ty:ignore[unsupported-base]
        def on_bar(self) -> None:
            super().on_bar()
            bar = len(self.data) - 1
            for trade in self.trades:
                observations.append(
                    Observation(
                        bar=bar,
                        close=float(self.data.Close[-1]),
                        entry=float(trade.entry_price),
                        size=float(trade.size),
                        sl=None if trade.sl is None else float(trade.sl),
                        tp=None if trade.tp is None else float(trade.tp),
                    )
                )

    Probed.__name__ = f"Probed{strategy_cls.__name__}"
    stats = Backtest(data, Probed, cash=CASH, commission=0.0, finalize_trades=True).run(**params)
    return ProbeResult(stats=stats, observations=observations)
