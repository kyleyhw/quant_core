"""Discovery of strategies and CLI commands through package entry points.

Any installed distribution can extend the platform by declaring entry points
in its ``pyproject.toml``. There is no directory scanning and no knowledge of
where a strategy's code lives: what is installed is what is found.

Strategies::

    [project.entry-points."quant_core.strategies"]
    MyStrategy = "my_package.my_module:MyStrategy"

Each entry point resolves to a ``backtesting.Strategy`` subclass, usually a
``quant_core.strategies.base_strategy.BaseStrategy`` subclass. The entry point
name is the strategy's display name in reports, the CLI and the dashboard.

Commands::

    [project.entry-points."quant_core.commands"]
    my-command = "my_package.cli:register"

Each entry point resolves to a function ``register(subparsers)`` that adds one
or more ``argparse`` subcommands to ``qc``. The subcommand should call
``set_defaults(func=...)`` with a handler that takes the parsed arguments.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from importlib.metadata import EntryPoint, entry_points
from typing import Any

from backtesting import Strategy

STRATEGY_GROUP = "quant_core.strategies"
COMMAND_GROUP = "quant_core.commands"


@dataclass(frozen=True)
class RegisteredStrategy:
    """A strategy found through the ``quant_core.strategies`` entry-point group."""

    name: str
    cls: type[Strategy]
    distribution: str

    @property
    def module(self) -> str:
        return self.cls.__module__

    @property
    def data_assets(self) -> int:
        """How many assets the strategy trades at once. See ``data_assets`` below."""
        return int(getattr(self.cls, "data_assets", 1))

    @property
    def is_unconfigured_wrapper(self) -> bool:
        """
        A meta-strategy declares ``underlying_strategy`` and wraps another strategy.
        One registered with that attribute still ``None`` cannot run on its own;
        register a subclass that sets it instead.
        """
        return hasattr(self.cls, "underlying_strategy") and self.cls.underlying_strategy is None


@dataclass
class Discovery:
    """The result of a discovery pass: what loaded, and what failed and why."""

    strategies: dict[str, RegisteredStrategy] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def by_name(self, name: str) -> RegisteredStrategy:
        if name not in self.strategies:
            available = ", ".join(sorted(self.strategies)) or "none"
            raise KeyError(f"Unknown strategy {name!r}. Installed strategies: {available}")
        return self.strategies[name]


def _distribution_name(ep: EntryPoint) -> str:
    dist = getattr(ep, "dist", None)
    return dist.name if dist is not None else "unknown"


def discover_strategies() -> Discovery:
    """
    Loads every strategy registered in the ``quant_core.strategies`` group.

    A strategy that fails to import, or resolves to something that is not a
    ``backtesting.Strategy`` subclass, is reported in ``Discovery.errors``
    rather than raised, so one broken plugin cannot take down the CLI or the
    dashboard. Two distributions registering the same name is also an error:
    the first one found is kept and the clash is reported.
    """
    found = Discovery()
    for ep in sorted(entry_points(group=STRATEGY_GROUP), key=lambda e: e.name):
        source = _distribution_name(ep)
        try:
            obj = ep.load()
        except Exception as exc:  # any plugin import failure is reported
            found.errors.append(f"{ep.name} ({source}): failed to import {ep.value}: {exc}")
            continue

        if not (isinstance(obj, type) and issubclass(obj, Strategy)):
            found.errors.append(
                f"{ep.name} ({source}): {ep.value} is not a backtesting.Strategy subclass"
            )
            continue

        if ep.name in found.strategies:
            first = found.strategies[ep.name]
            found.errors.append(
                f"{ep.name}: registered by both {first.distribution} and {source}; "
                f"keeping the one from {first.distribution}"
            )
            continue

        found.strategies[ep.name] = RegisteredStrategy(name=ep.name, cls=obj, distribution=source)
    return found


def register_plugin_commands(subparsers: Any) -> list[str]:
    """
    Lets every installed ``quant_core.commands`` entry point add subcommands.

    Returns a warning per plugin that failed, so the caller can print them. A
    failing plugin never prevents the built-in commands from working.
    """
    warnings: list[str] = []
    for ep in sorted(entry_points(group=COMMAND_GROUP), key=lambda e: e.name):
        source = _distribution_name(ep)
        try:
            register = ep.load()
            register(subparsers)
        except Exception as exc:  # any plugin failure is reported
            warnings.append(f"command plugin {ep.name} ({source}) failed to register: {exc}")
    return warnings


def print_discovery_errors(discovery: Discovery, stream: Any = None) -> None:
    for message in discovery.errors:
        print(f"warning: {message}", file=stream or sys.stderr)
