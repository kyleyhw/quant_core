"""Feature engineering produces the columns strategies and models expect.

Training and inference both import from `src.feature_engineering`, so a change
in these columns is a training-serving skew risk. A test that asserts the two
paths agree is Phase 24.
"""

import pytest

from quant_core.feature_engineering import FeatureEngineer
from testing.conftest import synthetic_ohlcv

EXPECTED_COLUMNS = ["SMA_50", "SMA_200", "EMA_20", "RSI_14", "ATR_14"]


@pytest.fixture(scope="module")
def features():
    df = synthetic_ohlcv(bars=300)
    df.columns = [c.lower() for c in df.columns]
    return FeatureEngineer().calculate_features(df)


@pytest.mark.parametrize("column", EXPECTED_COLUMNS)
def test_expected_column_is_present(features, column):
    assert column in features.columns


def test_rsi_stays_within_bounds(features):
    # Leading NaNs from the rolling window are expected, not a violation.
    rsi = features["RSI_14"].dropna()
    assert not rsi.empty
    assert rsi.between(0, 100).all()


def test_atr_is_non_negative(features):
    atr = features["ATR_14"].dropna()
    assert not atr.empty
    assert (atr >= 0).all()


def test_row_count_is_preserved(features):
    assert len(features) == 300
