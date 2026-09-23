"""quant-core: a market-agnostic algorithmic trading platform."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("quant-core")
except PackageNotFoundError:  # running from a source tree that is not installed
    __version__ = "0.0.0+unknown"
