# Multi-Asset Strategy Benchmark Report

**Generated:** 2025-11-26 19:14:24

## Strategy Summary & Training Data
| Strategy Type | Strategies | Training Data Source |
| :--- | :--- | :--- |
| **Baseline** | `BuyAndHoldStrategy` | N/A |
| **Machine Learning** | `MLRegimeStrategy`, `EnsembleSignalStrategy` | **SPY (2010-2023)** |
| **Meta-Strategies** | `DynamicSizing`, `MetaRegimeFilter` | N/A (Uses underlying logic) |
| **Technical** | `SimpleMACrossover`, `RSI2Period`, `BollingerBands` | N/A (Rule-based) |

## Performance Metrics by Asset

### AAPL
**Test Data Source:** `TECH_2024_2025.csv`

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |   Runtime [s] |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|--------------:|
| BuyAndHoldStrategy     |        22.89 |           0.53 |              -32.93 |         nan    |          0 |          0.11 |
| RSI2PeriodStrategy     |         3.08 |           0.11 |              -20.82 |          53.85 |         26 |          0.19 |
| SimpleMACrossover      |         1.37 |           0.06 |              -23.48 |          42.86 |          7 |          0.17 |
| BollingerBandsStrategy |       -11.58 |          -1.61 |              -12.22 |          42.86 |          7 |          0.24 |

### AMD
**Test Data Source:** `TECH_2024_2025.csv`

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |   Runtime [s] |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|--------------:|
| SimpleMACrossover      |        97.72 |           1.02 |              -26.83 |          66.67 |          3 |          0.07 |
| RSI2PeriodStrategy     |        27.06 |           0.45 |              -33.83 |          71.43 |         28 |          0.09 |
| BuyAndHoldStrategy     |        34.31 |           0.36 |              -54.25 |         nan    |          0 |          0.12 |
| BollingerBandsStrategy |       -11.69 |          -0.88 |              -11.85 |          36.36 |         11 |          0.3  |

### AMZN
**Test Data Source:** `TECH_2024_2025.csv`

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |   Runtime [s] |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|--------------:|
| RSI2PeriodStrategy     |        32.69 |           0.84 |              -12.37 |          70.83 |         24 |          0.44 |
| BuyAndHoldStrategy     |        23.34 |           0.48 |              -30.61 |         nan    |          0 |          0.04 |
| SimpleMACrossover      |        -0.78 |          -0.03 |              -17.7  |          50    |          6 |          0.12 |
| BollingerBandsStrategy |        -6.13 |          -0.73 |               -8.42 |          25    |          4 |          0.08 |

### INTC
**Test Data Source:** `TECH_2024_2025.csv`

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |   Runtime [s] |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|--------------:|
| RSI2PeriodStrategy     |        44.36 |           0.65 |              -26.12 |          70.37 |         27 |          0.16 |
| BollingerBandsStrategy |        13.58 |           0.56 |               -5.59 |          50    |          6 |          0.12 |
| BuyAndHoldStrategy     |        60.59 |           0.52 |              -33.35 |         nan    |          0 |          0.04 |
| SimpleMACrossover      |       -17.49 |          -0.42 |              -48.18 |          22.22 |          9 |          0.12 |

### KO
**Test Data Source:** `PEP_KO_2024_2025.csv`

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |   Runtime [s] |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|--------------:|
| SimpleMACrossover      |        20.95 |           1.14 |               -7.17 |          71.43 |          7 |          0.11 |
| RSI2PeriodStrategy     |         9.21 |           0.66 |               -9.84 |          58.62 |         29 |          0.11 |
| BuyAndHoldStrategy     |         5.47 |           0.26 |              -13.41 |         nan    |          0 |          0.08 |
| BollingerBandsStrategy |        -0.22 |          -0.08 |               -2.42 |          60    |          5 |          0.47 |

### MSFT
**Test Data Source:** `TECH_2024_2025.csv`

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |   Runtime [s] |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|--------------:|
| BollingerBandsStrategy |         6.85 |           1.22 |               -1.67 |          85.71 |          7 |          0.23 |
| RSI2PeriodStrategy     |        21.43 |           0.86 |               -8.2  |          71.43 |         28 |          0.63 |
| SimpleMACrossover      |        11.46 |           0.57 |              -16.38 |          37.5  |          8 |          0.4  |
| BuyAndHoldStrategy     |        14.46 |           0.46 |              -21.69 |         nan    |          0 |          0.09 |

### NVDA
**Test Data Source:** `TECH_2024_2025.csv`

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |   Runtime [s] |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|--------------:|
| RSI2PeriodStrategy     |        48.44 |           0.83 |              -23.45 |          66.67 |         27 |          0.28 |
| BuyAndHoldStrategy     |        50.56 |           0.59 |              -36.62 |         nan    |          0 |          0.26 |
| SimpleMACrossover      |        -0.57 |          -0.02 |              -29.99 |          25    |          8 |          0.09 |
| BollingerBandsStrategy |        -4.31 |          -0.35 |              -13.71 |          66.67 |          6 |          0.61 |

### PEP
**Test Data Source:** `PEP_KO_2024_2025.csv`

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |   Runtime [s] |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|--------------:|
| RSI2PeriodStrategy     |        -2.42 |          -0.13 |              -16.72 |          50    |         26 |          0.3  |
| BuyAndHoldStrategy     |       -10    |          -0.44 |              -25.48 |         nan    |          0 |          0.1  |
| BollingerBandsStrategy |        -2.65 |          -0.55 |               -3.64 |          45.45 |         11 |          0.2  |
| SimpleMACrossover      |        -9.96 |          -0.69 |              -13.27 |          14.29 |          7 |          0.09 |

### SPY
**Test Data Source:** `SPY_2024_2025.csv`

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |   Runtime [s] |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|--------------:|
| RSI2PeriodStrategy     |        25.03 |           1.23 |               -8.3  |          76.92 |         26 |          0.28 |
| BuyAndHoldStrategy     |        18.39 |           0.76 |              -17.94 |         nan    |          0 |          0.09 |
| SimpleMACrossover      |         0.64 |           0.05 |              -17.51 |          20    |          5 |          0.22 |
| BollingerBandsStrategy |        -6.61 |          -1.2  |               -8.66 |          20    |         10 |          0.26 |

### TSLA
**Test Data Source:** `TECH_2024_2025.csv`

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |   Runtime [s] |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|--------------:|
| SimpleMACrossover      |        63.85 |           0.63 |              -29.48 |          50    |          8 |          0.14 |
| BuyAndHoldStrategy     |        69.32 |           0.49 |              -53.16 |         nan    |          0 |          0.1  |
| RSI2PeriodStrategy     |        19.52 |           0.25 |              -42.78 |          67.86 |         28 |          0.26 |
| BollingerBandsStrategy |         0.84 |           0.07 |               -7.05 |          40    |          5 |          0.2  |

