"""Shared fixtures for quant-core's own test suite."""

import pandas as pd
import pytest

from quant_core.testing import synthetic_ohlcv

__all__ = ["synthetic_ohlcv"]


@pytest.fixture(scope="session")
def ohlcv() -> pd.DataFrame:
    return synthetic_ohlcv()
