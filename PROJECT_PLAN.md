# Project Development Plan

This document outlines the planned phases and tasks for developing the IBKR Open-Core Algorithmic Trading Bot.

## Phase 1: Core Infrastructure Setup
1.  [completed] Verify and finalize the project directory structure.
2.  [completed] Populate `requirements.txt` with all necessary libraries.
3.  [completed] Implement the IBKR connection logic in `src/connection.py`.
4.  [completed] Implement standardized data fetching in `src/data_loader.py`.
5.  [completed] Create the base `Notifier` class in `src/notifications.py`.
6.  [completed] Set up initial documentation, including `README.md` and the `/docs` folder structure.
7.  [completed] Migrate dependency management to `uv` (`pyproject.toml`, `uv.lock`).

## Phase 2: Base Strategy & Backtesting Framework
8.  [completed] Develop the parent `base_strategy.py` to handle position sizing and stop-loss logic.
8.  [completed] Create a public `simple_ma_crossover.py` strategy (e.g., a moving average crossover) inheriting from the base strategy.
9.  [completed] Implement the backtesting script `run_backtesting/run_backtest.py` to test a single strategy.
10. [completed] Generate the first backtest report and save it to the `strategies/reports/` directory.

## Phase 3: Feature Engineering & ML Model Training
11. [completed] Develop the shared `src/feature_engineering.py` module with common technical indicators.
12. [completed] Create a script in research/ for model training.
    - [completed] Created `research/train_regime_model.py` (XGBoost regime classifier)
    - [completed] Created `research/utils.py` (simplified data fetching)
    - [completed] Run script to train and save model
13. [completed] Save the trained model artifact to the `strategies_private/models/` directory.

## Phase 4: Machine Learning Strategy Implementation
14. [completed] Create a private strategy in `strategies_private/` that uses a trained model.
15. [completed] Backtest the ML-based strategy.

## Phase 5: Advanced Strategy Development
21. [completed] Acquire and document datasets for pairs trading (GLD/GDX).
22. [completed] Implement and train a Hidden Markov Model (HMM) for regime detection.
23. [completed] Implement a private HMM-based trading strategy.
24. [completed] Backtest the HMM strategy.
25. [completed] Implement a private Pairs Trading strategy.
26. [completed] Backtest the Pairs Trading strategy.

## Phase 6: Safety & Infrastructure
27. [completed] Implement the `execution.py` module with safety checks.
    - [completed] Hard limits (Max Shares, Max Dollar, Price Deviation).
28. [completed] Develop System Safety & Recovery Protocols.
    - [completed] Define Crash Recovery steps (State reconciliation).
    - [completed] Implement Heartbeat/System Health monitoring (via `tools/supervisor.py`).
    - [completed] Create `docs/safety_and_recovery.md`.
    - [pending] (Future) Implement External Heartbeat (Dead Man's Switch) for Supervisor monitoring.

## Phase 7: System Finalization
29. [completed] Implement the strategy benchmarking script `run_backtesting/benchmark.py`.
30. [completed] Integrate the `Notifier` class for alerts.
31. [completed] Complete all documentation.

## Phase 8: Expanded Strategy Research (Planning)
> Still open. Carried forward as Phase 23.
32. [pending] Brainstorm new strategy concepts (e.g., Sentiment Analysis, Statistical Arbitrage, Reinforcement Learning).
33. [pending] Select candidates for implementation.
34. [pending] Backtest and validate new strategies.

## Phase 9: High-Frequency & Intraday Strategy Research
> Still open. Data work carried forward as Phase 22, strategy work as Phase 23.
35. [pending] Research Intraday Logic (VWAP, Order Flow Imbalance).
36. [pending] Implement Intraday Data Handling (1-minute / 5-minute bars).
37. [pending] Develop Intraday Strategy (e.g., Gap & Go, Mean Reversion).

## Phase 10: Web UI Dashboard (Streamlit)
38. [completed] Create `dashboard/app.py`.
39. [completed] Implement Strategy & Asset selectors.
40. [completed] Visualize Backtest Results (Equity Curve, Drawdown, Trade Log).

# Roadmap

Phases 1-10 above are the historical record and keep their original numbering.
From here the phase number **is** the build order. Phases 8 and 9 remain open and
are carried forward into Phases 22 and 23.

## Phase 11: Engine Correctness (blocking)
Bugs found by reading the code against the documentation. Every benchmark report
currently in `strategies/reports/` was produced under these and is not
trustworthy. This phase is small on purpose: it is the only thing standing between
here and building on a foundation that lies. It ends by locking the fixes in with
CI so they cannot regress while the dashboard work is underway.

41. [completed] Fix the trailing stop units. `BaseStrategy.init` calls
   `set_trailing_sl(self.stop_loss_pct)`, but that method takes a multiple of ATR,
   not a percentage. The library provides `set_trailing_pct` for this. Measured on
   a synthetic series, the stop lands at 0.028% of price instead of 2%, roughly
   seventy times tighter, cutting average hold from 7.33 bars to 1.46.
42. [completed] Fix the `next()` contract. `SimpleMACrossover` and
   `RSI2PeriodStrategy` override `next()` without calling `super().next()`, so the
   trailing stop never runs for them at all. `BollingerBandsStrategy` does call it.
   The three public strategies therefore run under three different exit regimes and
   are not comparable.
43. [completed] Restructure `BaseStrategy` so this cannot recur: make `next()` final
   and give strategies an `on_bar()` hook that the base class always wraps, rather
   than relying on every subclass remembering to call up.
44. [completed] Implement take profit. The take-profit branch in `BaseStrategy.next`
   is a bare `pass`. The documentation advertises a 5% take profit.
45. [completed] Unify position sizing. Backtests call `buy()` with no size, which
   commits all available cash, while the live path calls `calculate_position_size`,
   which returns a hardcoded fraction. The two disagree and `risk_percent` is read
   by neither.
46. [completed] Make `risk_percent` real: size from account equity and stop distance,
   so that a losing trade costs approximately the configured fraction of equity.
47. [completed] Remove `CustomBroker` / `CustomBacktest`. The intended fix was a
   guard on the division in `_adjusted_price`, but the class turned out to be
   obsolete and harmful: backtesting.py has supported callable commissions
   natively since 0.6, so the override charged commission twice (3.2 points of
   return on an eleven-trade run), crashed with `TypeError: 'float' object is not
   callable` for the three float models in `COMMISSION_MODELS`, and silently
   discarded `spread`. `CustomBacktest` survives as a deprecated alias for
   `backtesting.Backtest` so existing imports keep resolving.
48. [completed] Adopt `pytest` and migrate the two existing `unittest` files.
49. [completed] A test asserting that every strategy honours the risk parameters it
   declares. This is the test that would have caught the three bugs above.
50. [completed] Regression tests pinning backtest metrics for a fixed dataset, so no
   later refactor can silently change results.
51. [completed] GitHub Actions workflow running ruff, ty, and the test suite. There is
   no `.github/` directory today.
52. [completed] Regenerate every report in `strategies/reports/` once the above land,
   and update the benchmark linked from `README.md`. Across the thirty
   risk-managed runs, mean return fell from +12.47% to -0.29% and mean maximum
   drawdown fell from -16.93% to -6.61%. `BuyAndHoldStrategy` is unchanged, since
   it declares no risk parameters. The reported edge of the public strategies was
   largely an artifact of trading the full book with a stop that never fired.

## Phase 12: Dashboard Rebuild
Supersedes the Streamlit dashboard delivered in Phase 10. Direction: the "Ledger
surface, Desk structure" merge from the design canvas
(https://claude.ai/artifact/29p1Qjgebz9qRHS8f3nnhb). Pulled ahead of the deeper
engine work so progress is visible early.

53. [pending] Establish the design system: colour tokens, type scale, and the
   Spectral / IBM Plex Sans / IBM Plex Mono stack, injected as CSS.
54. [pending] Build the application shell: nav rail, masthead, specification strip,
   tab bar.
55. [pending] Build the run configuration drawer. Must expose strategy parameters,
   universe, period, data source, capital, commission, and the three
   `base_strategy` risk parameters, which the current UI does not surface at all.
56. [pending] Add a run history store so runs persist and can be reloaded and
   compared. Today each run overwrites the last.
57. [pending] Replace the embedded `backtesting.py` Bokeh HTML with native equity and
   drawdown charts sharing one x axis.
58. [pending] Overview tab: six headline figures plus a plain-language reading of the
   result.
59. [pending] Trades tab.
60. [pending] Metrics tab, grouped into Returns, Risk, Trade Quality, and Run Details
   instead of the current unsorted stats dump.
61. [pending] Execution log tab, surfacing `ExecutionManager` blocks and `Notifier`
   events, which are invisible in the UI today.
62. [pending] Benchmark screen: strategy matrix, return-against-drawdown scatter, and
   overlaid equity curves. `run_backtesting/benchmark.py` currently has no UI.
63. [pending] Reports screen for browsing and exporting `strategies/reports/`.
64. [pending] Paper trading monitor screen. Ships disabled until Phase 17 and 18.
65. [pending] Tests for dashboard helpers and a smoke test that the app renders.

## Phase 13: Dashboard Experience
66. [pending] Persist the last configuration between sessions. Strategy, asset,
   dates, and commission all reset on every rerun today.
67. [pending] Write a reproducibility manifest per run: data hash, strategy hash,
   parameters, library versions, so any saved report can be regenerated.
68. [pending] Surface real errors. The traceback is commented out in `dashboard/app.py`
   and failures show as a single line.
69. [pending] Validate configuration before running, rather than failing after the
   button is pressed. A pairs strategy with one asset selected is the current
   example.
70. [pending] Progress reporting and cancellation for long runs.
71. [pending] Named runs with tags and free-text notes.
72. [pending] Shareable deep links to a specific run.
73. [pending] Side-by-side run comparison with metric deltas.
74. [pending] Inline metric definitions drawn from `docs/interpreting_report.md`.
75. [pending] Annotate the equity curve with trade markers and regime shading.
76. [pending] Export a run as PDF, Markdown, CSV, or a runnable notebook.
77. [pending] Theme toggle, with the dark "Tape" direction from the design canvas as
   the alternate theme.
78. [pending] First-run onboarding. The app currently downloads a hardcoded ticker
   list for a hardcoded date range with no explanation and no choice.
79. [pending] Keyboard shortcuts for run, compare, and tab switching.

## Phase 14: Backtest Realism
Nothing here changes whether a backtest is correct, only whether it is honest.
Each item shifts reported returns downward, so expect the numbers on the new
dashboard to get worse and truer.

80. [pending] Slippage model, configurable as fixed basis points or a fraction of
   the bar range. Nothing models it today; market orders fill exactly at the next
   open.
81. [pending] Bid-ask spread. `CustomBacktest` passes `spread=0`; the engine
   supports the parameter.
82. [pending] Set `finalize_trades=True`. A position still open on the final bar is
   currently dropped from returns and trade statistics.
83. [pending] Liquidity ceiling: cap order size at a fraction of the bar's volume so
   a strategy cannot buy more than the market traded.
84. [pending] Exclude the warm-up window from results. The ATR calculation
   back-fills its first hundred bars, so early trades use a value that was not
   observable at the time.
85. [pending] State `auto_adjust` explicitly in the downloader. `yf.download` is
   called without it, so whether prices are split and dividend adjusted depends on
   the installed library version.
86. [pending] Model borrow cost and short availability for short positions.
87. [pending] Model overnight financing on margin.
88. [pending] Build a survivorship-free universe, or state the bias plainly in every
   report. The benchmark universe is six large caps that all still exist.

## Phase 15: Statistical Validation
The engine can already produce a number. This phase is about knowing whether to
believe it. Each item has a natural home on the dashboard built in Phase 12.

89. [pending] Walk-forward analysis harness: rolling train and test windows with
   out-of-sample stitching.
90. [pending] Parameter optimisation. `backtesting.py` ships an `optimize` method
   that nothing in the repo calls.
91. [pending] Parameter sensitivity surfaces, so a result that only works at one
   setting is visible as a spike rather than a plateau.
92. [pending] Purged, embargoed k-fold cross-validation for the machine learning
   strategies. Nothing currently enforces a train and test split.
93. [pending] Monte Carlo trade resampling to put confidence intervals on Sharpe,
   drawdown, and terminal equity.
94. [pending] Deflated Sharpe ratio and probability of backtest overfitting, to
   discount results for the number of configurations tried.
95. [pending] Bootstrap confidence bands on the equity curve.
96. [pending] Benchmark-relative statistics: alpha, beta, information ratio,
   tracking error, up and down capture.
97. [pending] Performance attribution by regime, calendar month, weekday, and
   holding-period bucket.

## Phase 16: Test Coverage
Phase 11 built the harness and pinned the critical behaviour. This widens it.

98. [pending] Unit tests for strategies, feature engineering, commission models, and
   the data loader.
99. [pending] Property-based tests for `ExecutionManager` using `hypothesis`, already
   a dev dependency but unused.
100. [pending] Coverage reporting with a floor enforced in CI.
101. [pending] Fold `testing/debug_scripts/` into the test suite or delete it.

## Phase 17: Account-Level Risk Controls
The limits in `src/execution.py` are per-order only. A per-order cap cannot stop a
slow bleed across many orders. Must land before any live order is sent.

102. [pending] Daily loss limit, measured against a configurable reset time, counting
   open position P&L.
103. [pending] Total drawdown limit against a persisted high-water mark.
104. [pending] Auto-flatten and halt on breach.
105. [pending] Kill switch reachable from both the dashboard and the CLI.
106. [pending] Persist risk state across restarts so a limit survives a crash.
107. [pending] Move hard limits out of class attributes into configuration.
108. [pending] Pre-trade risk check combining order limits, account limits, and
   portfolio concentration in one gate.

## Phase 18: Paper Trading & Live Execution
Carried forward from the original Phase 11. Gated on Phases 11 and 17: do not
paper trade a strategy whose backtest is known to be wrong, or without
account-level loss limits.

109. [pending] Route every live order through `ExecutionManager.check_order_limits`.
   `BaseStrategy.buy_instrument` / `sell_instrument` currently call the adapter
   directly, so the documented "fat finger" gate is not in the live path.
110. [pending] Implement streaming bar subscription in the IBKR data loader.
   `IBKRDataLoader` only implements `get_historical_data`; nothing feeds a strategy
   in real time.
111. [pending] Build the live runner: an event-driven entry point that advances a
   strategy per bar. `BaseStrategy.next` is backtest-only today.
112. [pending] Track order lifecycle through `ib_insync` callbacks (fills, partial
   fills, rejections). `get_order_status` reads a snapshot once.
113. [pending] Reconcile state against IBKR positions on startup, as described in
   `docs/safety_and_recovery.md`. No code implements this yet.
114. [pending] Enable the paper trading monitor screen built in Phase 12.
115. [pending] Conduct a dry run against live market data with execution disabled.
116. [pending] Begin paper trading with a small capital allocation.

## Phase 19: Live Execution Hardening
117. [pending] A simulated broker adapter implementing `IMarketAdapter`, so the live
   path can be tested end to end without IBKR running.
118. [pending] Bracket orders and native IBKR trailing stops, so protection survives a
   process crash.
119. [pending] Partial fill handling and order amendment.
120. [pending] Reconnect with exponential backoff and session resumption.
121. [pending] Idempotent order submission, so a restart mid-send cannot double-fill.
122. [pending] Clock and timezone discipline, including market calendar and half days.
123. [pending] A second market adapter to prove the abstraction, which the README
   claims but has never been exercised.

## Phase 20: Strategy Framework
124. [pending] Strategy registry with declared metadata: asset class, required
   lookback, supported timeframes, author, version.
125. [pending] Parameter schema on each strategy, so the dashboard can generate its
   controls instead of hardcoding them. `get_params` is a start but is
   return-only.
126. [pending] Content-hash each strategy and record the hash on every run, so a
   result can always be traced to the exact code that produced it.
127. [pending] First-class meta-strategies. `_default_buy` already refers to a
   `DynamicSizingStrategy` that does not exist in the public tree.
128. [pending] Replace per-bar `numpy` recomputation with the engine's indicator API.
   `SimpleMACrossover` recomputes both moving averages from scratch on every bar,
   which is quadratic and leaves nothing to plot.
129. [pending] Strategy scaffolding command that generates a new strategy, its tests,
   and its docs entry.
130. [pending] An event-driven backtest engine as an alternative to `backtesting.py`,
   which is single-asset and assumes bar data.

## Phase 21: Portfolio & Multi-Asset
The framework backtests one symbol at a time. Portfolio behaviour is where most
real risk lives.

131. [pending] Multi-asset portfolio backtest with a shared cash account.
132. [pending] Separate signal generation from position sizing: strategies emit
   target weights, a sizer turns weights into orders.
133. [pending] Portfolio construction methods: equal weight, volatility targeting,
   risk parity, and Kelly-fraction sizing.
134. [pending] Strategy ensembles with capital allocated across several strategies.
135. [pending] Rebalancing schedules with turnover and cost accounting.
136. [pending] Correlation matrix and portfolio-level drawdown reporting.
137. [pending] Exposure reporting by sector and by factor.
138. [pending] Portfolio-level risk limits: gross and net exposure, per-symbol
   concentration, per-sector concentration.

## Phase 22: Data Platform
Absorbs the data half of the original Phase 9.

139. [pending] Add data providers behind the existing `IDataLoader` interface, so
   yfinance is not the only source.
140. [pending] Intraday bar handling at one and five minute resolution. Original
   Phase 9, item 36.
141. [pending] Data quality checks: index gaps, duplicate timestamps, zero-volume
   bars, price outliers, timezone consistency. Fail loudly rather than backtest on
   bad data.
142. [pending] Explicit corporate action handling, independent of provider defaults.
143. [pending] Point-in-time universe membership, so a backtest sees the index as it
   was, not as it is.
144. [pending] Incremental cache updates instead of re-downloading whole histories.
145. [pending] Store cached data as Parquet rather than CSV.
146. [pending] A data catalogue screen showing what is cached, its date range,
   quality flags, and freshness.
147. [pending] Record a content hash of the input data on every run.

## Phase 23: Strategy Research
Absorbs the original Phase 8 and the strategy half of the original Phase 9. Placed
here because research is only worth doing once results can be trusted (Phase 11),
measured (Phase 15), and viewed (Phase 12).

148. [pending] Brainstorm new strategy concepts: sentiment analysis, statistical
   arbitrage, reinforcement learning. Original Phase 8, item 32.
149. [pending] Select candidates for implementation. Original Phase 8, item 33.
150. [pending] Backtest and validate them under the Phase 15 harness. Original
   Phase 8, item 34.
151. [pending] Intraday logic research: VWAP and order flow imbalance. Original
   Phase 9, item 35.
152. [pending] Develop an intraday strategy such as gap-and-go or mean reversion.
   Original Phase 9, item 37.

## Phase 24: Machine Learning Lifecycle
153. [pending] A test that asserts training and inference produce identical features.
   `README.md` calls this critical; nothing enforces it.
154. [pending] Feature store with point-in-time correctness.
155. [pending] Model registry recording training data range, hyperparameters, metrics,
   and the code hash.
156. [pending] Drift monitoring on live feature distributions against training.
157. [pending] Explainability reporting for the regime model.
158. [pending] Automated retraining schedule with promotion gates.

## Phase 25: Operational Readiness
Run continuously alongside the phases above rather than as a block.

159. [pending] Structured logging to `logs/` with rotation.
160. [pending] External heartbeat / dead man's switch for the supervisor. Carried over
   from Phase 6, item 28.
161. [pending] Telegram notifier. `docs/safety_and_recovery.md` promises
   "Discord/Telegram" but `src/notifications.py` implements Discord only.
162. [pending] Daily summary notification at market close.
163. [pending] Alert routing rules by severity and channel.
164. [pending] Health endpoint exposing connection state, last bar time, and open
   position count.
165. [pending] Move run storage to SQLite once the file-based store strains.
166. [pending] Deployment and operations runbook.

## Phase 26: Distribution & Documentation
167. [pending] Docker image and a one-command local setup.
168. [pending] Example notebook gallery.
169. [pending] A public demo running on sample data with private strategies disabled.
170. [pending] Document the market adapter plugin contract for third-party adapters.
171. [pending] Published documentation site generated from `docs/`.
172. [pending] Contribution guide and pull request template.

## Phase 27: Housekeeping
Run continuously. None of these blocks anything.

173. [pending] Implement or delete `src/metrics.py`, which is an empty file. It is the
   natural home for the Phase 15 statistics.
174. [pending] Replace the `main.py` hello-world stub, or remove it in favour of the
   `qc` console script.
175. [pending] Reconcile documentation with behaviour, including the safety and
   recovery doc's claims about reconciliation and notification channels, and the
   moving average strategy's docstring claim that the parent class manages its
   exits.
