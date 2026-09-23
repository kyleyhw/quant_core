# Dataset Documentation

This document describes the sample datasets shipped with `quant_core` for backtesting, benchmarks and examples.

---

## 1. SPDR S&P 500 ETF Trust (SPY)

-   **Filename:** `SPY_1hour_1year.csv`
-   **Source:** Manually downloaded from Interactive Brokers TWS.
-   **Date Range:** Approximately one year of recent hourly data. The exact range can vary depending on when the file was last updated.
-   **Timeframe:** 1-hour bars.
-   **Description:** This dataset contains hourly Open, High, Low, Close, and Volume (OHLCV) data for the SPY ETF, which tracks the S&P 500 index.
-   **Primary Use:** Single-instrument backtests on intraday bars, and examples of model training on shared features.

---

## 2. PepsiCo, Inc. (PEP)

-   **Filename:** `PEP_daily_2010_2023.csv`
-   **Source:** Downloaded from Yahoo Finance using the `yfinance` library. The script `data/download_yfinance_data.py` can be used to refresh or acquire similar datasets.
-   **Date Range:** 2010-01-01 to 2023-12-31.
-   **Timeframe:** 1-day bars.
-   **Description:** Daily OHLCV data for PepsiCo, Inc.
-   **Primary Use:** The first leg of a sample two-asset dataset (see `data_assets = 2` in [Strategy Development](./strategy_development.md)).

---

## 3. The Coca-Cola Company (KO)

-   **Filename:** `KO_daily_2010_2023.csv`
-   **Source:** Downloaded from Yahoo Finance using the `yfinance` library. The script `data/download_yfinance_data.py` can be used to refresh or acquire similar datasets.
-   **Date Range:** 2010-01-01 to 2023-12-31.
-   **Timeframe:** 1-day bars.
-   **Description:** Daily OHLCV data for The Coca-Cola Company. PEP and KO are classic examples of a stock pair that is highly correlated due to being in the same industry, making them a suitable candidate for a pairs trading strategy.
-   **Primary Use:** The second leg of the sample two-asset dataset.
