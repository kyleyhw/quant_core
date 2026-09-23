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

**Audited 2026-09-23**, after Phase 11 landed. The audit changed three things.
Phase 11 gained follow-ups, one of which is blocking for the private submodule.
Phase 14 now opens with engine invariant tests, because Phase 11 found a
double-charged commission that a ten-line invariant would have caught in
seconds. And a new Phase 25 makes the core callable over HTTP, so the dashboard
becomes one client among several rather than the only way in. Phase 11 also
established that no public strategy has an edge once its declared risk
parameters actually apply, which is why Phases 15 and 23 read more urgently than
they did a week ago; they stay where they are because the dashboard was asked for
first, and the finding is recorded in each.

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

**Follow-ups found in the 2026-09-23 audit.** The phase is complete, but it left
three things behind that belong to it.

53. [pending] **Migrate the private strategies submodule to `on_bar()`. Blocking for
   private mode.** `BaseStrategy` now raises `TypeError` at import time for any
   subclass that defines `next()`. `run_backtesting/benchmark.py` configures
   `DynamicSizingStrategy`, `MetaRegimeFilterStrategy`, `EnsembleSignalStrategy`
   and `MLRegimeStrategy` from `strategies_private`; any of them that overrides
   `next()` will fail to import, which breaks the private dashboard mode and the
   private benchmark. The submodule is a separate repository, so this cannot be
   done from here. Until it lands, pin the submodule to a commit that predates the
   Phase 11 base-class change, or expect private mode to fail loudly.
54. [pending] Update `docs/strategy_development.md`, which still tells strategy
   authors to call `super().next()` and describes the take-profit logic that was a
   `pass`. The example in `docs/feature_engineering.md` also shows `next()`.
55. [pending] The benchmark report's "Strategy Summary" table is hardcoded in
   `benchmark.py` and lists strategies that did not run. Generate it from the runs
   that actually completed.

## Phase 12: Dashboard Rebuild
Supersedes the Streamlit dashboard delivered in Phase 10. Direction: the "Ledger
surface, Desk structure" merge from the design canvas
(https://claude.ai/artifact/29p1Qjgebz9qRHS8f3nnhb). Pulled ahead of the deeper
engine work so progress is visible early.

56. [pending] Decide the UI stack and write the decision down. Recommendation:
   stay on Streamlit for this phase. It gets the design on screen fastest, which
   is what this phase is for, and it will fight the design in exactly three
   places: the persistent nav rail, tab state across reruns, and the slide-over
   drawer. Accept those, and put every engine call behind the next item so that
   the frontend can be replaced in Phase 25 without touching the engine.
57. [pending] A service module, `src/service/`, that the dashboard, the CLI and the
   benchmark all call for the same things: run a backtest, list strategies and
   their parameters, load data, read and write the run store. Plain Python, no
   HTTP. This is the seam Phase 25 wraps in an API, and it is the reason
   `run_backtest.py` and `benchmark.py` can stop carrying two copies of strategy
   discovery, data loading and report writing.
58. [pending] Establish the design system: colour tokens, type scale, and the
   Spectral / IBM Plex Sans / IBM Plex Mono stack, injected as CSS.
59. [pending] Build the application shell: nav rail, masthead, specification strip,
   tab bar.
60. [pending] Build the run configuration drawer. Must expose strategy parameters,
   universe, period, data source, capital, commission, and the three
   `base_strategy` risk parameters, which the current UI does not surface at all.
61. [pending] Add a run history store so runs persist and can be reloaded and
   compared. Today each run overwrites the last.
62. [pending] Replace the embedded `backtesting.py` Bokeh HTML with native equity and
   drawdown charts sharing one x axis.
63. [pending] Overview tab: six headline figures plus a plain-language reading of the
   result.
64. [pending] Trades tab.
65. [pending] Metrics tab, grouped into Returns, Risk, Trade Quality, and Run Details
   instead of the current unsorted stats dump.
66. [pending] Execution log tab, surfacing `ExecutionManager` blocks and `Notifier`
   events, which are invisible in the UI today.
67. [pending] Benchmark screen: strategy matrix, return-against-drawdown scatter, and
   overlaid equity curves. `run_backtesting/benchmark.py` currently has no UI.
68. [pending] Reports screen for browsing and exporting `strategies/reports/`.
69. [pending] Paper trading monitor screen. Ships disabled until Phase 17 and 18.
70. [pending] Tests for dashboard helpers and a smoke test that the app renders.

## Phase 13: Dashboard Experience
71. [pending] Persist the last configuration between sessions. Strategy, asset,
   dates, and commission all reset on every rerun today.
72. [pending] Write a reproducibility manifest per run: data hash, strategy hash,
   parameters, library versions, so any saved report can be regenerated.
73. [pending] Surface real errors. The traceback is commented out in `dashboard/app.py`
   and failures show as a single line.
74. [pending] Validate configuration before running, rather than failing after the
   button is pressed. A pairs strategy with one asset selected is the current
   example.
75. [pending] Progress reporting and cancellation for long runs.
76. [pending] Named runs with tags and free-text notes.
77. [pending] Shareable deep links to a specific run.
78. [pending] Side-by-side run comparison with metric deltas.
79. [pending] Inline metric definitions drawn from `docs/interpreting_report.md`.
80. [pending] Annotate the equity curve with trade markers and regime shading.
81. [pending] Export a run as PDF, Markdown, CSV, or a runnable notebook.
82. [pending] Theme toggle, with the dark "Tape" direction from the design canvas as
   the alternate theme.
83. [pending] First-run onboarding. The app currently downloads a hardcoded ticker
   list for a hardcoded date range with no explanation and no choice.
84. [pending] Keyboard shortcuts for run, compare, and tab switching.
85. [pending] Parameter sweep view: pick ranges, run the grid, see the sensitivity
   surface. The front end for Phase 15's optimisation items.
86. [pending] Strategy health view: for each strategy, rolling out-of-sample
   performance on data that arrived after its last run. The front end for
   Phase 15's decay item.

## Phase 14: Backtest Realism
Nothing here changes whether a backtest is correct, only whether it is honest.
Each item shifts reported returns downward, so expect the numbers on the new
dashboard to get worse and truer. The phase opens with invariants because it is
about to change the engine, and Phase 11 showed how quietly the engine can be
wrong.

87. [pending] Engine invariant tests, before touching anything else. Buy-and-hold at
   zero cost equals the price return. Closed-trade P&L plus open P&L equals the
   change in equity. Commission drag equals rate times notional per side. A
   decision on bar N is unchanged when every bar after N is replaced. The
   double-charged commission Phase 11 found would have failed the third of these
   on the first run.
88. [pending] Differential test against an independent engine, either vectorbt or a
   hand-rolled vectorised replay, for the moving-average crossover on the test
   fixture. Two engines agreeing is the strongest evidence this project can have
   that its numbers mean what they say.
89. [pending] Slippage model, configurable as fixed basis points or a fraction of
   the bar range. Nothing models it today; market orders fill exactly at the next
   open.
90. [pending] Bid-ask spread. The engine supports the parameter and nothing passes
   it.
91. [pending] Set `finalize_trades=True`. A position still open on the final bar is
   currently dropped from returns and trade statistics. The regenerated benchmark
   still warns about this on every run.
92. [pending] Liquidity ceiling: cap order size at a fraction of the bar's volume so
   a strategy cannot buy more than the market traded.
93. [pending] Exclude the warm-up window from results. The ATR calculation
   back-fills its first hundred bars, so early trades use a value that was not
   observable at the time.
94. [pending] State `auto_adjust` explicitly in the downloader. `yf.download` is
   called without it, so whether prices are split and dividend adjusted depends on
   the installed library version.
95. [pending] Model borrow cost and short availability for short positions.
96. [pending] Model overnight financing on margin.
97. [pending] Build a survivorship-free universe, or state the bias plainly in every
   report. The benchmark universe is ten large caps that all still exist.
98. [pending] Multi-timeframe data alignment, so a daily strategy can consult hourly
   bars without look-ahead. Phase 20 builds the strategy pattern on top of it.

## Phase 15: Statistical Validation
The engine can already produce a number. This phase is about knowing whether to
believe it. Phase 11 showed that the reported edge of every public strategy was
an artefact of a stop that never fired; this phase is how the project avoids
being fooled a second time. Each item has a natural home on the dashboard built
in Phase 12.

99. [pending] Walk-forward analysis harness: rolling train and test windows with
   out-of-sample stitching.
100. [pending] Parameter optimisation. `backtesting.py` ships an `optimize` method
   that nothing in the repo calls.
101. [pending] Parameter sensitivity surfaces, so a result that only works at one
   setting is visible as a spike rather than a plateau.
102. [pending] Purged, embargoed k-fold cross-validation for the machine learning
   strategies. Nothing currently enforces a train and test split.
103. [pending] Monte Carlo trade resampling to put confidence intervals on Sharpe,
   drawdown, and terminal equity.
104. [pending] Deflated Sharpe ratio and probability of backtest overfitting, to
   discount results for the number of configurations tried.
105. [pending] Bootstrap confidence bands on the equity curve.
106. [pending] Benchmark-relative statistics: alpha, beta, information ratio,
   tracking error, up and down capture.
107. [pending] Performance attribution by regime, calendar month, weekday, and
   holding-period bucket.
108. [pending] A significance test for "strategy A beats strategy B": bootstrap the
   difference in Sharpe over paired windows. The benchmark table currently invites
   ranking by a single point estimate, which is how a 97% return on AMD looked
   like a result.
109. [pending] Strategy decay monitoring: re-run every strategy on each new week of
   data and track out-of-sample performance against its in-sample expectation.
110. [pending] Minimum track-record length: for a Sharpe of this size, how many years
   of data before it is distinguishable from zero. Print it next to the Sharpe.

## Phase 16: Test Coverage
Phase 11 built the harness and pinned the critical behaviour. This widens it.

111. [pending] Unit tests for strategies, feature engineering, commission models, and
   the data loader.
112. [pending] Property-based tests for `ExecutionManager` using `hypothesis`, already
   a dev dependency but unused.
113. [pending] Tests for the `qc` command-line entry points.
114. [pending] Make `ty` blocking in CI. It is advisory today because of thirty
   pre-existing diagnostics in the dashboard and the IBKR adapter; Phase 28 clears
   them.
115. [pending] Coverage reporting with a floor enforced in CI.
116. [pending] Fold `testing/debug_scripts/` into the test suite or delete it. It is
   excluded from collection today because its scripts need the network.

## Phase 17: Account-Level Risk Controls
The limits in `src/execution.py` are per-order only. A per-order cap cannot stop a
slow bleed across many orders. Must land before any live order is sent.

117. [pending] Daily loss limit, measured against a configurable reset time, counting
   open position P&L.
118. [pending] Total drawdown limit against a persisted high-water mark.
119. [pending] Auto-flatten and halt on breach.
120. [pending] Kill switch reachable from both the dashboard and the CLI.
121. [pending] Persist risk state across restarts so a limit survives a crash.
122. [pending] A typed, validated settings object for every runtime setting: order
   and account limits, connection details, notification channels, data paths.
   Hard-coded class attributes and loose `.env` reads both go, and a bad value
   fails at startup rather than at the first order.
123. [pending] Pre-trade risk check combining order limits, account limits, and
   portfolio concentration in one gate.

## Phase 18: Paper Trading & Live Execution
Carried forward from the original Phase 11. Gated on Phases 11 and 17: do not
paper trade a strategy whose backtest is known to be wrong, or without
account-level loss limits.

124. [pending] Route every live order through `ExecutionManager.check_order_limits`.
   `BaseStrategy.buy_instrument` / `sell_instrument` currently call the adapter
   directly, so the documented "fat finger" gate is not in the live path.
125. [pending] Implement streaming bar subscription in the IBKR data loader.
   `IBKRDataLoader` only implements `get_historical_data`; nothing feeds a strategy
   in real time.
126. [pending] Build the live runner: an event-driven entry point that advances a
   strategy per bar. `on_bar()` is called only by the backtest engine today.
127. [pending] Track order lifecycle through `ib_insync` callbacks (fills, partial
   fills, rejections). `get_order_status` reads a snapshot once.
128. [pending] Reconcile state against IBKR positions on startup, as described in
   `docs/safety_and_recovery.md`. No code implements this yet.
129. [pending] Enable the paper trading monitor screen built in Phase 12.
130. [pending] Conduct a dry run against live market data with execution disabled.
131. [pending] Begin paper trading with a small capital allocation.
132. [pending] Shadow reconciliation: replay each day's live bars through the backtest
   engine and diff the simulated fills against the real ones. The gap is
   implementation shortfall, and it is the one number that says whether
   Phase 14's cost models are honest.
133. [pending] A scheduled daily run that writes the day's signals, fills and P&L as
   a report, so paper trading leaves an audit trail whether or not anyone was
   watching.

## Phase 19: Live Execution Hardening
134. [pending] A simulated broker adapter implementing `IMarketAdapter`, so the live
   path can be tested end to end without IBKR running.
135. [pending] Bracket orders and native IBKR trailing stops, so protection survives a
   process crash.
136. [pending] Partial fill handling and order amendment.
137. [pending] Reconnect with exponential backoff and session resumption.
138. [pending] Idempotent order submission, so a restart mid-send cannot double-fill.
139. [pending] Clock and timezone discipline, including market calendar and half days.
140. [pending] A second market adapter to prove the abstraction, which the README
   claims but has never been exercised. Recommendation: crypto through `ccxt`. It
   trades around the clock, the data is free, and a venue with no market hours,
   no share lots and no tiered commissions stresses every assumption the IBKR
   adapter baked into `src/interfaces.py`.
141. [pending] Transaction cost analysis: expected fill against realised fill for
   every live order, aggregated by symbol and order type.
142. [pending] Feed measured costs back into the Phase 14 slippage and commission
   models, so the backtest's cost assumptions are calibrated from fills rather
   than guessed.

## Phase 20: Strategy Framework
143. [pending] Strategy registry with declared metadata: asset class, required
   lookback, supported timeframes, author, version.
144. [pending] Parameter schema on each strategy, so the dashboard can generate its
   controls instead of hardcoding them. `get_params` is a start but is
   return-only.
145. [pending] Content-hash each strategy and record the hash on every run, so a
   result can always be traced to the exact code that produced it.
146. [pending] First-class meta-strategies. `_default_buy` already refers to a
   `DynamicSizingStrategy` that lives only in the private tree.
147. [pending] Replace per-bar `numpy` recomputation with the engine's indicator API.
   `SimpleMACrossover` recomputes both moving averages from scratch on every bar,
   which is quadratic and leaves nothing to plot.
148. [pending] Multi-timeframe strategies as a supported pattern, on the alignment
   built in Phase 14.
149. [pending] Regime detection as a public, shared feature any strategy can read,
   rather than something each private strategy reimplements.
150. [pending] Retire the dashboard's `create_signal_executor` wrapper or make it
   real. No strategy returns a signal, so it is dead code.
151. [pending] Strategy scaffolding command that generates a new strategy, its tests,
   and its docs entry.
152. [pending] An event-driven backtest engine as an alternative to `backtesting.py`,
   which is single-asset and assumes bar data.

## Phase 21: Portfolio & Multi-Asset
The framework backtests one symbol at a time. Portfolio behaviour is where most
real risk lives.

153. [pending] Multi-asset portfolio backtest with a shared cash account.
154. [pending] Separate signal generation from position sizing: strategies emit
   target weights, a sizer turns weights into orders.
155. [pending] Portfolio construction methods: equal weight, volatility targeting,
   risk parity, and Kelly-fraction sizing.
156. [pending] Strategy ensembles with capital allocated across several strategies.
157. [pending] Rebalancing schedules with turnover and cost accounting.
158. [pending] Correlation matrix and portfolio-level drawdown reporting.
159. [pending] Exposure reporting by sector and by factor.
160. [pending] Portfolio-level risk limits: gross and net exposure, per-symbol
   concentration, per-sector concentration.
161. [pending] Realised and unrealised P&L with lot-level accounting, first in first
   out, which is what a broker statement and a tax return both expect.
162. [pending] Multi-currency support: positions in non-USD instruments, with FX
   conversion for equity and for every risk limit.

## Phase 22: Data Platform
Absorbs the data half of the original Phase 9.

163. [pending] Add data providers behind the existing `IDataLoader` interface, so
   yfinance is not the only source.
164. [pending] Intraday bar handling at one and five minute resolution. Original
   Phase 9, item 36.
165. [pending] Data quality checks: index gaps, duplicate timestamps, zero-volume
   bars, price outliers, timezone consistency. Fail loudly rather than backtest on
   bad data.
166. [pending] Explicit corporate action handling, independent of provider defaults.
167. [pending] Point-in-time universe membership, so a backtest sees the index as it
   was, not as it is.
168. [pending] Universe screening: choose symbols by liquidity, volatility and price
   floor rather than from a hardcoded list.
169. [pending] Incremental cache updates instead of re-downloading whole histories.
170. [pending] Scheduled refresh of cached data, so the catalogue is never stale by
   accident.
171. [pending] Store cached data as Parquet rather than CSV.
172. [pending] A data catalogue screen showing what is cached, its date range,
   quality flags, and freshness.
173. [pending] Record a content hash of the input data on every run.
174. [pending] A plain note on data licensing. yfinance scrapes Yahoo and automated
   use sits outside its terms; say so in the docs and name the provider to move
   to before anything trades real money.

## Phase 23: Strategy Research
Absorbs the original Phase 8 and the strategy half of the original Phase 9.
Phase 11 established that no public strategy has an edge once its own risk
parameters apply, so research starts from zero rather than from a portfolio of
working strategies. Placed here because research is only worth doing once
results can be trusted (Phase 11), measured (Phase 15), and viewed (Phase 12).

175. [pending] An edge audit of every existing strategy, public and private, under
   the Phase 14 costs and the Phase 15 statistics. Retire what fails. Only what
   survives earns screen space on the dashboard.
176. [pending] A research notebook workflow: a template that loads the fixture, runs
   a strategy through the service module, and renders the Phase 15 statistics, so
   an idea can be tried and judged in an hour.
177. [pending] Brainstorm new strategy concepts: sentiment analysis, statistical
   arbitrage, reinforcement learning. Original Phase 8, item 32.
178. [pending] Select candidates for implementation. Original Phase 8, item 33.
179. [pending] Backtest and validate them under the Phase 15 harness. Original
   Phase 8, item 34.
180. [pending] Intraday logic research: VWAP and order flow imbalance. Original
   Phase 9, item 35.
181. [pending] Develop an intraday strategy such as gap-and-go or mean reversion.
   Original Phase 9, item 37.

## Phase 24: Machine Learning Lifecycle
182. [pending] A test that asserts training and inference produce identical features.
   `README.md` calls this critical; nothing enforces it.
183. [pending] Feature store with point-in-time correctness.
184. [pending] Model registry recording training data range, hyperparameters, metrics,
   and the code hash.
185. [pending] Drift monitoring on live feature distributions against training.
186. [pending] Explainability reporting for the regime model.
187. [pending] Automated retraining schedule with promotion gates, using the purged
   cross-validation from Phase 15 as the gate.

## Phase 25: Service Layer & API
Phase 12's service module made the core callable from Python. This makes it
callable from anywhere. The dashboard becomes one client among several and can be
replaced without touching the engine, and a phone can reach the kill switch.

188. [pending] An HTTP API over the service module: runs, strategies, the data
   catalogue, risk state, live status, and the kill switch.
189. [pending] Authentication. It will expose live positions.
190. [pending] Move the dashboard and the CLI onto the API, so there is one path into
   the engine.
191. [pending] A minimal status page that works on a phone: equity, open positions,
   the last few events, the kill switch. The page to open when an alert fires.
192. [pending] Decide whether the Streamlit dashboard stays or is replaced by a
   frontend built against the API, with the Phase 12 design canvas as the
   specification. The three places Streamlit fought the design in Phase 12 are
   the evidence for this decision.

## Phase 26: Operational Readiness
Run continuously alongside the phases above rather than as a block.

193. [pending] Structured logging to `logs/` with rotation.
194. [pending] External heartbeat / dead man's switch for the supervisor. Carried over
   from Phase 6, item 28.
195. [pending] Telegram notifier. `docs/safety_and_recovery.md` promises
   "Discord/Telegram" but `src/notifications.py` implements Discord only.
196. [pending] Daily summary notification at market close.
197. [pending] Alert routing rules by severity and channel.
198. [pending] Health endpoint exposing connection state, last bar time, and open
   position count.
199. [pending] A scheduler for the recurring jobs this plan has accumulated: data
   refresh (Phase 22), the daily paper run (Phase 18), the decay check
   (Phase 15), retraining (Phase 24). One place to define them, one log to read.
200. [pending] A nightly benchmark against the test fixture, checked against the
   regression baseline, so an engine regression surfaces overnight rather than at
   the next release.
201. [pending] Move run storage to SQLite once the file-based store strains.
202. [pending] Deployment and operations runbook.

## Phase 27: Distribution & Documentation
203. [pending] Docker image and a one-command local setup.
204. [pending] Example notebook gallery, seeded by the Phase 23 template.
205. [pending] A public demo running on sample data with private strategies disabled.
206. [pending] Document the market adapter plugin contract for third-party adapters.
207. [pending] Published documentation site generated from `docs/`.
208. [pending] Contribution guide and pull request template.

## Phase 28: Housekeeping
Run continuously. None of these blocks anything.

209. [pending] Deduplicate `run_backtesting/run_backtest.py` and `benchmark.py`, 845
   lines between them sharing strategy discovery, data loading and report
   writing, onto the Phase 12 service module.
210. [pending] Reconcile the codebase with its own type annotations so `ty` can
   become blocking in Phase 16.
211. [pending] Implement or delete `src/metrics.py`, which is an empty file. It is the
   natural home for the Phase 15 statistics.
212. [pending] Replace the `main.py` hello-world stub, or remove it in favour of the
   `qc` console script.
213. [pending] Reconcile documentation with behaviour, including the safety and
   recovery doc's claims about reconciliation and notification channels.
