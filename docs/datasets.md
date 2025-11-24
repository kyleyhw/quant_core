# Dataset Documentation

This document provides metadata and descriptions for all datasets used in the `ibkr_quant_core` project for research, backtesting, and model training.

---

## 1. SPDR S&P 500 ETF Trust (SPY)

-   **Filename:** `SPY_1hour_1year.csv`
-   **Source:** Manually downloaded from Interactive Brokers TWS.
-   **Date Range:** Approximately one year of recent hourly data. The exact range can vary depending on when the file was last updated.
-   **Timeframe:** 1-hour bars.
-   **Description:** This dataset contains hourly Open, High, Low, Close, and Volume (OHLCV) data for the SPY ETF, which tracks the S&P 500 index.
-   **Primary Use:**
    -   Used as the primary dataset for developing and backtesting single-instrument strategies.
    -   Serves as the input for training the XGBoost and Hidden Markov Model (HMM) regime detection models.

---

## 2. SPDR Gold Shares (GLD)

-   **Filename:** `GLD_daily_2010_2023.csv`
-   **Source:** Downloaded from Yahoo Finance using the `yfinance` library. The script `data/download_yfinance_data.py` can be used to refresh or acquire similar datasets.
-   **Date Range:** 2010-01-01 to 2023-12-31.
-   **Timeframe:** 1-day bars.
-   **Description:** Daily OHLCV data for the GLD ETF, which tracks the price of gold bullion.
-   **Primary Use:**
    -   Serves as the first leg in the GLD/GDX pairs trading strategy.

---

## 3. VanEck Gold Miners ETF (GDX)

-   **Filename:** `GDX_daily_2010_2023.csv`
-   **Source:** Downloaded from Yahoo Finance using the `yfinance` library. The script `data/download_yfinance_data.py` can be used to refresh or acquire similar datasets.
-   **Date Range:** 2010-01-01 to 2023-12-31.
-   **Timeframe:** 1-day bars.
-   **Description:** Daily OHLCV data for the GDX ETF, which invests in a portfolio of gold mining companies. GDX is often highly correlated with the price of gold (GLD), making it a suitable partner for a pairs trading strategy.
-   **Primary Use:**
    -   Serves as the second leg in the GLD/GDX pairs trading strategy.
