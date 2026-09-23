# Backtest Report: SimpleMACrossover

**Run Date:** 2026-04-27 23:25:23

## Data Configuration
- **Data Source:** `['data/benchmark/SPY_2024-10-01_2025-11-25.csv']`
- **Date Range:** 2024-10-01 to 2025-11-24
- **Commission Model:** IBKR Tiered

## Strategy Parameters

## Backtest Metrics
|                        | 0                    |
|:-----------------------|:---------------------|
| Start                  | 2024-10-01 00:00:00  |
| End                    | 2025-11-24 00:00:00  |
| Duration               | 419 days 00:00:00    |
| Exposure Time [%]      | 68.5121107266436     |
| Equity Final [$]       | 10049.960965330349   |
| Equity Peak [$]        | 10297.970999510037   |
| Commissions [$]        | 3.5                  |
| Return [%]             | 0.499609653303487    |
| Buy & Hold Return [%]  | 19.035570937624396   |
| Return (Ann.) [%]      | 0.435506720755896    |
| Volatility (Ann.) [%]  | 12.267552806699035   |
| CAGR [%]               | 0.30018274642396037  |
| Sharpe Ratio           | 0.0355007007198759   |
| Sortino Ratio          | 0.04347946207721858  |
| Calmar Ratio           | 0.02469753936192445  |
| Alpha [%]              | -7.3937173346693825  |
| Beta                   | 0.4146619512405307   |
| Max. Drawdown [%]      | -17.633607719937693  |
| Avg. Drawdown [%]      | -3.021220364574055   |
| Max. Drawdown Duration | 290 days 00:00:00    |
| Avg. Drawdown Duration | 42 days 00:00:00     |
| # Trades               | 5                    |
| Win Rate [%]           | 20.0                 |
| Best Trade [%]         | 23.039327398303435   |
| Worst Trade [%]        | -12.307846569748198  |
| Avg. Trade [%]         | 0.09009595277591487  |
| Max. Trade Duration    | 176 days 00:00:00    |
| Avg. Trade Duration    | 56 days 00:00:00     |
| Profit Factor          | 1.190764483134957    |
| Expectancy [%]         | 0.7381955785821478   |
| SQN                    | 0.019775704098375237 |
| Kelly Criterion        | 0.005294251850586212 |

## Equity Curve
[View interactive plot](backtest_SimpleMACrossover_20260427_232521.html)

## Trade Log
|    |   Size |   EntryBar |   ExitBar |   EntryPrice |   ExitPrice | SL   | TP   |       PnL |   Commission |   ReturnPct | EntryTime        | ExitTime         | Duration          | Tag   |
|---:|-------:|-----------:|----------:|-------------:|------------:|:-----|:-----|----------:|-------------:|------------:|:-----------------|:-----------------|:------------------|:------|
|  0 |     16 |         30 |        58 |      591.839 |     585.757 |      |      |   -98.005 |          0.7 |  -0.0103496 | 2024-11-12 00:00 | 2024-12-23 00:00 | 41 days 00:00:00  |       |
|  1 |     16 |         78 |       102 |      604.863 |     580.474 |      |      |  -390.93  |          0.7 |  -0.0403945 | 2025-01-24 00:00 | 2025-02-28 00:00 | 35 days 00:00:00  |       |
|  2 |     17 |        124 |       128 |      554.62  |     486.4   |      |      | -1160.45  |          0.7 |  -0.123078  | 2025-04-01 00:00 | 2025-04-07 00:00 | 6 days 00:00:00   |       |
|  3 |     15 |        143 |       265 |      546.129 |     672     |      |      |  1887.37  |          0.7 |   0.230393  | 2025-04-29 00:00 | 2025-10-22 00:00 | 176 days 00:00:00 |       |
|  4 |     14 |        268 |       283 |      683.08  |     669.7   |      |      |  -188.02  |          0.7 |  -0.0196609 | 2025-10-27 00:00 | 2025-11-17 00:00 | 21 days 00:00:00  |       |