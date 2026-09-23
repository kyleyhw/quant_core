# Multi-Asset Strategy Benchmark Report

**Generated:** 2026-09-21 06:26:38

## Strategy Summary & Training Data
| Strategy Type | Strategies | Training Data Source |
| :--- | :--- | :--- |
| **Baseline** | `BuyAndHoldStrategy` | N/A |
| **Machine Learning** | `MLRegimeStrategy`, `EnsembleSignalStrategy` | **SPY (2010-2023)** |
| **Meta-Strategies** | `DynamicSizing`, `MetaRegimeFilter` | N/A (Uses underlying logic) |
| **Technical** | `SimpleMACrossover`, `RSI2Period`, `BollingerBands` | N/A (Rule-based) |

## Performance Metrics by Asset

### AAPL
**Test Data Source:** `AAPL_2024-10-01_2025-11-25.csv`

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |   Runtime [s] |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|--------------:|
| BuyAndHoldStrategy     |        22.89 |           0.53 |              -32.93 |         nan    |          0 |          0.03 |
| SimpleMACrossover      |        -0.2  |          -0.04 |               -5.32 |          37.5  |          8 |          0.05 |
| BollingerBandsStrategy |        -2.41 |          -0.43 |               -6.28 |          57.14 |          7 |          0.07 |
| RSI2PeriodStrategy     |       -10.99 |          -1.59 |              -12.88 |          45.16 |         31 |          0.08 |

### AMD
**Test Data Source:** `AMD_2024-10-01_2025-11-25.csv`

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |   Runtime [s] |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|--------------:|
| SimpleMACrossover      |         3.02 |           0.76 |               -2.38 |          66.67 |          3 |          0.05 |
| BuyAndHoldStrategy     |        34.31 |           0.36 |              -54.25 |         nan    |          0 |          0.03 |
| BollingerBandsStrategy |        -3.73 |          -0.42 |               -6.78 |          45.45 |         11 |          0.07 |
| RSI2PeriodStrategy     |        -7.13 |          -0.6  |              -20.18 |          43.24 |         37 |          0.08 |

### AMZN
**Test Data Source:** `AMZN_2024-10-01_2025-11-25.csv`

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |   Runtime [s] |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|--------------:|
| RSI2PeriodStrategy     |         9.86 |           0.87 |               -4.64 |          48.48 |         33 |          0.08 |
| BuyAndHoldStrategy     |        23.34 |           0.48 |              -30.61 |         nan    |          0 |          0.03 |
| SimpleMACrossover      |        -1.7  |          -0.21 |               -9.05 |          50    |          6 |          0.05 |
| BollingerBandsStrategy |        -2.67 |          -0.56 |               -5.12 |          25    |          4 |          0.07 |

### INTC
**Test Data Source:** `INTC_2024-10-01_2025-11-25.csv`

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |   Runtime [s] |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|--------------:|
| SimpleMACrossover      |         6.67 |           0.77 |               -3.01 |          66.67 |          9 |          0.05 |
| BuyAndHoldStrategy     |        60.59 |           0.52 |              -33.35 |         nan    |          0 |          0.03 |
| BollingerBandsStrategy |         5.3  |           0.47 |               -3.97 |          50    |          6 |          0.06 |
| RSI2PeriodStrategy     |         7.04 |           0.41 |              -12.14 |          52.38 |         42 |          0.08 |

### KO
**Test Data Source:** `KO_2024-10-01_2025-11-25.csv`

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |   Runtime [s] |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|--------------:|
| BollingerBandsStrategy |         3.24 |           1.06 |               -1.09 |          80    |          5 |          0.07 |
| SimpleMACrossover      |         1.52 |           0.35 |               -1.91 |          50    |          8 |          0.06 |
| BuyAndHoldStrategy     |         5.47 |           0.26 |              -13.41 |         nan    |          0 |          0.03 |
| RSI2PeriodStrategy     |        -3.5  |          -0.56 |               -5.51 |          41.18 |         34 |          0.08 |

### MSFT
**Test Data Source:** `MSFT_2024-10-01_2025-11-25.csv`

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |   Runtime [s] |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|--------------:|
| BollingerBandsStrategy |         6.11 |           1.37 |               -1.45 |          71.43 |          7 |          0.07 |
| BuyAndHoldStrategy     |        14.46 |           0.46 |              -21.69 |         nan    |          0 |          0.03 |
| RSI2PeriodStrategy     |         0.49 |           0.06 |               -7.01 |          57.58 |         33 |          0.08 |
| SimpleMACrossover      |        -1.82 |          -0.48 |               -3.73 |          25    |          8 |          0.06 |

### NVDA
**Test Data Source:** `NVDA_2024-10-01_2025-11-25.csv`

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |   Runtime [s] |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|--------------:|
| BuyAndHoldStrategy     |        50.56 |           0.59 |              -36.62 |         nan    |          0 |          0.03 |
| BollingerBandsStrategy |        -0.08 |          -0.01 |               -7.61 |          50    |          6 |          0.06 |
| RSI2PeriodStrategy     |        -5.38 |          -0.47 |              -11.73 |          45.45 |         33 |          0.08 |
| SimpleMACrossover      |        -9.11 |          -2.11 |               -9.46 |          12.5  |          8 |          0.05 |

### PEP
**Test Data Source:** `PEP_2024-10-01_2025-11-25.csv`

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |   Runtime [s] |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|--------------:|
| RSI2PeriodStrategy     |         1.89 |           0.22 |               -7.62 |          50    |         34 |          0.08 |
| BollingerBandsStrategy |         0.23 |           0.05 |               -2.45 |          36.36 |         11 |          0.07 |
| SimpleMACrossover      |        -0.02 |          -0    |               -4.54 |          28.57 |          7 |          0.05 |
| BuyAndHoldStrategy     |       -10    |          -0.44 |              -25.48 |         nan    |          0 |          0.03 |

### SPY
**Test Data Source:** `SPY_2024-10-01_2025-11-25.csv`

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |   Runtime [s] |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|--------------:|
| BuyAndHoldStrategy     |        18.39 |           0.76 |              -17.94 |         nan    |          0 |          0.03 |
| RSI2PeriodStrategy     |         3.4  |           0.67 |               -4.04 |          63.33 |         30 |          0.08 |
| BollingerBandsStrategy |        -1.3  |          -0.32 |               -4.78 |          33.33 |          9 |          0.07 |
| SimpleMACrossover      |        -1.03 |          -0.35 |               -3.14 |          20    |          5 |          0.05 |

### TSLA
**Test Data Source:** `TSLA_2024-10-01_2025-11-25.csv`

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |   Runtime [s] |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|--------------:|
| BuyAndHoldStrategy     |        69.32 |           0.49 |              -53.16 |         nan    |          0 |          0.03 |
| BollingerBandsStrategy |        -0.15 |          -0.03 |               -4.99 |          40    |          5 |          0.07 |
| RSI2PeriodStrategy     |        -1.02 |          -0.06 |              -17.75 |          46.15 |         39 |          0.08 |
| SimpleMACrossover      |        -5.18 |          -0.86 |               -7.89 |          25    |          8 |          0.06 |

