# Strategy Benchmark Report

**Generated:** 2025-11-24 22:13:09

This report compares the performance of all implemented trading strategies using the IBKR Tiered commission model.

## Performance Summary

| Strategy               |   Return [%] |   Sharpe Ratio |   Max. Drawdown [%] |   Win Rate [%] |   # Trades |
|:-----------------------|-------------:|---------------:|--------------------:|---------------:|-----------:|
| ML Regime (XGBoost)    |    38.1978   |       1.86068  |           -8.99132  |        49.9515 |       1031 |
| HMM Regime             |    20.4502   |       1.06002  |          -11.9761   |        52.9312 |       1177 |
| Pairs Trading (PEP/KO) |   -17.9684   |      -0.164758 |          -34.3542   |        46.0481 |        582 |
| Simple MA Crossover    |    -0.175287 |      -0.539162 |           -0.264314 |        40.3226 |         62 |
| Bollinger Bands        |    -0.377172 |      -1.09881  |           -0.383835 |        37.1795 |         78 |
| RSI(2) Strategy        |    -1.95711  |      -3.1282   |           -1.95711  |        32.5    |        320 |