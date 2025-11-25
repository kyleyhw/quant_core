# Feature Engineering Documentation

## Overview
The `src/feature_engineering.py` module is the **single source of truth** for all technical indicator calculations in the IBKR Quant Core system.

**Purpose:**
- **Consistency:** Ensures that the indicators used during model training (Research) are mathematically identical to those used during live trading (Inference).
- **Centralization:** Prevents logic duplication and "drift" where a strategy calculates RSI differently than the training script.

## Usage
### 1. In Strategies
Strategies should import the `FeatureEngineer` class and use it in their `next()` method (or `init` for vector operations) to calculate indicators.

```python
from src.feature_engineering import FeatureEngineer

class MyStrategy(Strategy):
    def init(self):
        self.fe = FeatureEngineer()
        # ...
    
    def next(self):
        # Calculate features for the current window
        df_features = self.fe.calculate_features(self.data.df)
```

### 2. In Research (Training)
Training scripts import the same class to generate features for the entire historical dataset.

```python
from src.feature_engineering import FeatureEngineer

df = pd.read_csv("data/SPY_2010_2023.csv")
fe = FeatureEngineer()
df_features = fe.calculate_features(df)
```

## Available Indicators
The `calculate_features` method adds the following columns to the DataFrame:

### Trend
- **SMA_50**: 50-period Simple Moving Average.
- **SMA_200**: 200-period Simple Moving Average.
- **EMA_20**: 20-period Exponential Moving Average.
- **MACD**: Moving Average Convergence Divergence (12, 26, 9).

### Momentum
- **RSI_14**: Relative Strength Index (14-period).
- **STOCH**: Stochastic Oscillator (14, 3, 3).

### Volatility
- **BBANDS**: Bollinger Bands (20-period, 2 std dev).
    - `BBU_20_2.0`: Upper Band
    - `BBM_20_2.0`: Middle Band
    - `BBL_20_2.0`: Lower Band
- **ATR_14**: Average True Range (14-period).

## Adding New Indicators
1.  Open `src/feature_engineering.py`.
2.  Add the calculation logic using `talib` or `pandas`.
3.  Ensure the column name is descriptive and unique.
4.  Update this documentation.
