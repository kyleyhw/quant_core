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
> Still open. Carried forward as Phase 24.
32. [pending] Brainstorm new strategy concepts (e.g., Sentiment Analysis, Statistical Arbitrage, Reinforcement Learning).
33. [pending] Select candidates for implementation.
34. [pending] Backtest and validate new strategies.

## Phase 9: High-Frequency & Intraday Strategy Research
> Still open. Data work carried forward as Phase 23, strategy work as Phase 24.
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
are carried forward into Phases 23 and 24.

**What this repository is.** The public repository is a platform. Its strategies
are reference implementations: each exists to exercise and document a platform
capability, and none is expected to have an edge. Benchmark numbers on them are a
demonstration of the platform's output, not a performance claim. Edge is developed
privately, on top of this platform, in a repository that consumes it. A phase
belongs in this plan if it makes the platform more correct, more capable, or
easier to build on; finding alpha does not.

**Which way the dependency runs.** The private repository depends on this
platform, so containment runs the same way: the private repository installs
`quant-core` as a package and registers its strategies through an entry point,
and this repository never contains, imports, builds or names private code.
Phase 12 makes that true, and a CI guard keeps it true.

**Audited 2026-09-23**, after Phase 11 landed. The audit changed three things.
Phase 11 gained follow-ups, one of which is blocking for the private submodule.
Phase 15 now opens with engine invariant tests, because Phase 11 found a
double-charged commission that a ten-line invariant would have caught in
seconds. And a new Phase 26 makes the core callable over HTTP, so the dashboard
becomes one client among several rather than the only way in. Phase 11 also
showed the reference strategies had been reporting an edge they did not have,
which for a platform is the worse failure: a demo that lies about what the
platform does. They now report honestly. Phase 16 gives the platform the tools
to keep it that way. Phase 12 gives the private repository a versioned platform
to depend on, which item 63 shows it did not have, and Phase 21 makes that
contract enforceable.

**Restructured 2026-09-23.** A new Phase 12 separates the public and private
repositories, ahead of the dashboard, so the dashboard is built on entry-point
discovery rather than on a private-mode toggle that would be torn out later.
Every phase after it moved down by one.

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
three things behind. The private repository's migration to `on_bar()` and the
hardcoded benchmark header both turned out to be symptoms of this repository
containing the private one, so they moved to Phase 12, which fixes that. One
remains here.

53. [pending] Update `docs/strategy_development.md`, which still tells strategy
   authors to call `super().next()` and describes the take-profit logic that was a
   `pass`. The example in `docs/feature_engineering.md` also shows `next()`.

## Phase 12: Separate the Public and Private Repositories
Containment follows dependency. The private strategies depend on this platform, so
the platform must not contain, import, build or name them. Today it does all four,
and the costs are measured rather than hypothetical:

- `qc --help` fails with `ModuleNotFoundError` in any public checkout, because
  `src/cli.py` imports from `strategies_private` at module level.
- The build config includes `strategies_private*`, so a wheel built from a checkout
  with the submodule populated ships the private code inside the public artifact.
- This repository is public, and fifteen of its commits narrate private research,
  one per submodule bump.
- The Phase 11 base-class change breaks the private strategies with no version to
  pin and no warning. It is not yet on `master`, so nothing is broken today; it
  will be the moment the Phase 11 branch merges.

The end state is two sibling repositories. The private one installs `quant-core`
pinned to a tag, registers its strategies and commands through entry points, and
runs the platform's dashboard and CLI from its own environment. Neither repository
contains the other.

54. [pending] Tag `v0.1.0` at `ed9b804`, the tip of `master` before Phase 11, so the
   private repository has a version to pin while it migrates.
55. [pending] Move the code under a `quant_core` namespace in the `src/` layout.
   Today the project installs top-level packages named `src`, `strategies` and
   `run_backtesting`, which will collide with other packages once `quant-core` is
   somebody's dependency. The mapping: `src/*` becomes `quant_core.*`,
   `strategies/*` becomes `quant_core.strategies.*`, `run_backtesting/*` becomes
   `quant_core.backtest.*`, `dashboard/*` becomes `quant_core.dashboard.*`. One
   move, imports updated repository-wide, no compatibility shims: the only
   downstream consumer migrates in this same phase.
56. [pending] Remove every reference to private code from public code, config and
   docs: the module-level import in `src/cli.py`; `strategies_private*` in the build
   config; the private strategy configs and hardcoded "Strategy Summary" header in
   `benchmark.py` (previously a Phase 11 follow-up); private report routing in
   `run_backtest.py`; the dashboard's private-mode toggle; the lint, format,
   type-check and secrets-scan entries that name `strategies_private`; and the
   README's clone-with-submodules instructions, directory tree and Private Mode
   section.
57. [pending] A CI guard that fails the build if `strategies_private` or
   `quant_strategies` appears in any tracked file other than `CHANGELOG.md` and this
   plan, so the coupling cannot creep back.
58. [pending] Strategy discovery through a `quant_core.strategies` entry-point group,
   where each entry point resolves to a strategy class and its name is the display
   name. The benchmark, the backtest runner and the dashboard all list strategies
   from it, and the public reference strategies register through the same group,
   so both repositories share one discovery path.
59. [pending] A `quant_core.commands` entry-point group, where each entry point
   resolves to a function `register(subparsers)` that adds an `argparse`
   subcommand to `qc`. The model-training commands in `src/cli.py` train private
   models, so they move to the private repository and keep working as
   `qc train-regime` and `qc train-ensemble` from its environment.
60. [pending] Remove the submodule: the `.gitmodules` entry and the gitlink. This
   stops private activity being recorded in public history. Existing history is
   left as it is; scrubbing it means rewriting and force-pushing public history,
   which is a separate decision and is not planned.
61. [pending] Drop the deprecated `CustomBacktest` alias, so every breaking change the
   private repository has to absorb lands in one release rather than several.
62. [pending] Start `CHANGELOG.md` and release `v0.2.0`: the Phase 11 base-class
   contract, the namespace move, entry-point discovery and the alias removal, each
   with a migration note giving old and new import paths. Before 1.0, a minor
   version bump is how a breaking change is signalled; the deprecation policy for
   1.0 and later is Phase 21.
63. [pending] **Migrate the private repository onto `v0.2.0`. Blocking for private
   work.** Done in the private repository, not here. It depends on `quant-core` by
   tag instead of living inside it; becomes an installable package; migrates every
   `BaseStrategy` subclass to `on_bar()`; registers its strategies and the training
   commands through the two entry-point groups; updates imports to the
   `quant_core` namespace; and keeps its own reports, models and data. The
   `on_bar()` rename is mechanical, but the behaviour change is not: every migrated
   strategy gains a working trailing stop, a working take-profit and risk-derived
   sizing, so its numbers will move. A strategy that genuinely wants the old
   all-in, no-stop behaviour sets `stop_loss_pct = 0` and `take_profit_pct = 0`
   explicitly. Until the migration lands, private work stays pinned to `v0.1.0`.
64. [pending] Document the two-repository development loop: an editable path source
   under `[tool.uv.sources]` for changing the platform and a private strategy
   together, and the tag pin for everything else.
65. [pending] Public CI proves the public repository stands alone: build the wheel,
   install it into a clean environment with no private code anywhere, and run
   `qc --help`, the test suite, and the benchmark on the synthetic fixture.

## Phase 13: Dashboard Rebuild
Supersedes the Streamlit dashboard delivered in Phase 10. Direction: the "Ledger
surface, Desk structure" merge from the design canvas
(https://claude.ai/artifact/29p1Qjgebz9qRHS8f3nnhb). Pulled ahead of the deeper
engine work so progress is visible early. Lists strategies from the entry-point
group added in Phase 12, so it has no private mode: what is installed is what
shows.

66. [pending] Decide the UI stack and write the decision down. Recommendation:
   stay on Streamlit for this phase. It gets the design on screen fastest, which
   is what this phase is for, and it will fight the design in exactly three
   places: the persistent nav rail, tab state across reruns, and the slide-over
   drawer. Accept those, and put every engine call behind the next item so that
   the frontend can be replaced in Phase 26 without touching the engine.
67. [pending] A service module, `src/service/`, that the dashboard, the CLI and the
   benchmark all call for the same things: run a backtest, list strategies and
   their parameters, load data, read and write the run store. Plain Python, no
   HTTP. This is the seam Phase 26 wraps in an API, and it is the reason
   `run_backtest.py` and `benchmark.py` can stop carrying two copies of strategy
   discovery, data loading and report writing.
68. [pending] Establish the design system: colour tokens, type scale, and the
   Spectral / IBM Plex Sans / IBM Plex Mono stack, injected as CSS.
69. [pending] Build the application shell: nav rail, masthead, specification strip,
   tab bar.
70. [pending] Build the run configuration drawer. Must expose strategy parameters,
   universe, period, data source, capital, commission, and the three
   `base_strategy` risk parameters, which the current UI does not surface at all.
71. [pending] Add a run history store so runs persist and can be reloaded and
   compared. Today each run overwrites the last.
72. [pending] Replace the embedded `backtesting.py` Bokeh HTML with native equity and
   drawdown charts sharing one x axis.
73. [pending] Overview tab: six headline figures plus a plain-language reading of the
   result.
74. [pending] Trades tab.
75. [pending] Metrics tab, grouped into Returns, Risk, Trade Quality, and Run Details
   instead of the current unsorted stats dump.
76. [pending] Execution log tab, surfacing `ExecutionManager` blocks and `Notifier`
   events, which are invisible in the UI today.
77. [pending] Benchmark screen: strategy matrix, return-against-drawdown scatter, and
   overlaid equity curves. `run_backtesting/benchmark.py` currently has no UI.
78. [pending] Reports screen for browsing and exporting `strategies/reports/`.
79. [pending] Paper trading monitor screen. Ships disabled until Phase 18 and 19.
80. [pending] Tests for dashboard helpers and a smoke test that the app renders.

## Phase 14: Dashboard Experience
81. [pending] Persist the last configuration between sessions. Strategy, asset,
   dates, and commission all reset on every rerun today.
82. [pending] Write a reproducibility manifest per run: data hash, strategy hash,
   parameters, library versions, so any saved report can be regenerated.
83. [pending] Surface real errors. The traceback is commented out in `dashboard/app.py`
   and failures show as a single line.
84. [pending] Validate configuration before running, rather than failing after the
   button is pressed. A pairs strategy with one asset selected is the current
   example.
85. [pending] Progress reporting and cancellation for long runs.
86. [pending] Named runs with tags and free-text notes.
87. [pending] Shareable deep links to a specific run.
88. [pending] Side-by-side run comparison with metric deltas.
89. [pending] Inline metric definitions drawn from `docs/interpreting_report.md`.
90. [pending] Annotate the equity curve with trade markers and regime shading.
91. [pending] Export a run as PDF, Markdown, CSV, or a runnable notebook.
92. [pending] Theme toggle, with the dark "Tape" direction from the design canvas as
   the alternate theme.
93. [pending] First-run onboarding. The app currently downloads a hardcoded ticker
   list for a hardcoded date range with no explanation and no choice.
94. [pending] Keyboard shortcuts for run, compare, and tab switching.
95. [pending] Parameter sweep view: pick ranges, run the grid, see the sensitivity
   surface. The front end for Phase 16's optimisation items.
96. [pending] Strategy health view: for each strategy, rolling out-of-sample
   performance on data that arrived after its last run. The front end for
   Phase 16's decay item.

## Phase 15: Backtest Realism
Nothing here changes whether a backtest is correct, only whether it is honest.
Each item shifts reported returns downward, so expect the numbers on the new
dashboard to get worse and truer. The phase opens with invariants because it is
about to change the engine, and Phase 11 showed how quietly the engine can be
wrong.

97. [pending] Engine invariant tests, before touching anything else. Buy-and-hold at
   zero cost equals the price return. Closed-trade P&L plus open P&L equals the
   change in equity. Commission drag equals rate times notional per side. A
   decision on bar N is unchanged when every bar after N is replaced. The
   double-charged commission Phase 11 found would have failed the third of these
   on the first run.
98. [pending] Differential test against an independent engine, either vectorbt or a
   hand-rolled vectorised replay, for the moving-average crossover on the test
   fixture. Two engines agreeing is the strongest evidence this project can have
   that its numbers mean what they say.
99. [pending] Slippage model, configurable as fixed basis points or a fraction of
   the bar range. Nothing models it today; market orders fill exactly at the next
   open.
100. [pending] Bid-ask spread. The engine supports the parameter and nothing passes
   it.
101. [pending] Set `finalize_trades=True`. A position still open on the final bar is
   currently dropped from returns and trade statistics. The regenerated benchmark
   still warns about this on every run.
102. [pending] Liquidity ceiling: cap order size at a fraction of the bar's volume so
   a strategy cannot buy more than the market traded.
103. [pending] Exclude the warm-up window from results. The ATR calculation
   back-fills its first hundred bars, so early trades use a value that was not
   observable at the time.
104. [pending] State `auto_adjust` explicitly in the downloader. `yf.download` is
   called without it, so whether prices are split and dividend adjusted depends on
   the installed library version.
105. [pending] Model borrow cost and short availability for short positions.
106. [pending] Model overnight financing on margin.
107. [pending] Build a survivorship-free universe, or state the bias plainly in every
   report. The benchmark universe is ten large caps that all still exist.
108. [pending] Multi-timeframe data alignment, so a daily strategy can consult hourly
   bars without look-ahead. Phase 21 builds the strategy pattern on top of it.

## Phase 16: Statistical Validation
The engine can already produce a number. This phase is about knowing whether to
believe it. These are platform tools: the private repository is where they will
earn their keep, and Phase 11 showed what happens without them. Each item has a
natural home on the dashboard built in Phase 13.

109. [pending] Walk-forward analysis harness: rolling train and test windows with
   out-of-sample stitching.
110. [pending] Parameter optimisation. `backtesting.py` ships an `optimize` method
   that nothing in the repo calls.
111. [pending] Parameter sensitivity surfaces, so a result that only works at one
   setting is visible as a spike rather than a plateau.
112. [pending] Purged, embargoed k-fold cross-validation for the machine learning
   strategies. Nothing currently enforces a train and test split.
113. [pending] Monte Carlo trade resampling to put confidence intervals on Sharpe,
   drawdown, and terminal equity.
114. [pending] Deflated Sharpe ratio and probability of backtest overfitting, to
   discount results for the number of configurations tried.
115. [pending] Bootstrap confidence bands on the equity curve.
116. [pending] Benchmark-relative statistics: alpha, beta, information ratio,
   tracking error, up and down capture.
117. [pending] Performance attribution by regime, calendar month, weekday, and
   holding-period bucket.
118. [pending] A significance test for "strategy A beats strategy B": bootstrap the
   difference in Sharpe over paired windows. The benchmark table currently invites
   ranking by a single point estimate, which is how a 97% return on AMD looked
   like a result before Phase 11.
119. [pending] Strategy decay monitoring: re-run every strategy on each new week of
   data and track out-of-sample performance against its in-sample expectation.
120. [pending] Minimum track-record length: for a Sharpe of this size, how many years
   of data before it is distinguishable from zero. Print it next to the Sharpe.

## Phase 17: Test Coverage
Phase 11 built the harness and pinned the critical behaviour. This widens it.

121. [pending] Unit tests for strategies, feature engineering, commission models, and
   the data loader.
122. [pending] Property-based tests for `ExecutionManager` using `hypothesis`, already
   a dev dependency but unused.
123. [pending] Tests for the `qc` command-line entry points.
124. [pending] Make `ty` blocking in CI. It is advisory today because of thirty
   pre-existing diagnostics in the dashboard and the IBKR adapter; Phase 29 clears
   them.
125. [pending] Coverage reporting with a floor enforced in CI.
126. [pending] Fold `testing/debug_scripts/` into the test suite or delete it. It is
   excluded from collection today because its scripts need the network.

## Phase 18: Account-Level Risk Controls
The limits in `src/execution.py` are per-order only. A per-order cap cannot stop a
slow bleed across many orders. Must land before any live order is sent.

127. [pending] Daily loss limit, measured against a configurable reset time, counting
   open position P&L.
128. [pending] Total drawdown limit against a persisted high-water mark.
129. [pending] Auto-flatten and halt on breach.
130. [pending] Kill switch reachable from both the dashboard and the CLI.
131. [pending] Persist risk state across restarts so a limit survives a crash.
132. [pending] A typed, validated settings object for every runtime setting: order
   and account limits, connection details, notification channels, data paths.
   Hard-coded class attributes and loose `.env` reads both go, and a bad value
   fails at startup rather than at the first order. Ships with a committed
   `.env.example` naming every variable, so a new checkout of the platform, or of
   a private repository built on it, knows what it needs without reading source.
133. [pending] Pre-trade risk check combining order limits, account limits, and
   portfolio concentration in one gate.

## Phase 19: Paper Trading & Live Execution
Carried forward from the original Phase 11. Gated on Phases 11 and 18: do not
paper trade a strategy whose backtest is known to be wrong, or without
account-level loss limits.

134. [pending] Route every live order through `ExecutionManager.check_order_limits`.
   `BaseStrategy.buy_instrument` / `sell_instrument` currently call the adapter
   directly, so the documented "fat finger" gate is not in the live path.
135. [pending] Implement streaming bar subscription in the IBKR data loader.
   `IBKRDataLoader` only implements `get_historical_data`; nothing feeds a strategy
   in real time.
136. [pending] Build the live runner: an event-driven entry point that advances a
   strategy per bar. `on_bar()` is called only by the backtest engine today.
137. [pending] Track order lifecycle through `ib_insync` callbacks (fills, partial
   fills, rejections). `get_order_status` reads a snapshot once.
138. [pending] Reconcile state against IBKR positions on startup, as described in
   `docs/safety_and_recovery.md`. No code implements this yet.
139. [pending] Enable the paper trading monitor screen built in Phase 13.
140. [pending] Conduct a dry run against live market data with execution disabled.
141. [pending] Paper trade a reference strategy for long enough to exercise every
   part of the live path: signals, fills, partial fills, a rejection, a
   reconnect, a restart with open positions. The P&L is not the deliverable; the
   event log and the reconciliation are.
142. [pending] Shadow reconciliation: replay each day's live bars through the backtest
   engine and diff the simulated fills against the real ones. The gap is
   implementation shortfall, and it is the one number that says whether
   Phase 15's cost models are honest.
143. [pending] A scheduled daily run that writes the day's signals, fills and P&L as
   a report, so paper trading leaves an audit trail whether or not anyone was
   watching.

## Phase 20: Live Execution Hardening
144. [pending] A simulated broker adapter implementing `IMarketAdapter`, so the live
   path can be tested end to end without IBKR running.
145. [pending] Bracket orders and native IBKR trailing stops, so protection survives a
   process crash.
146. [pending] Partial fill handling and order amendment.
147. [pending] Reconnect with exponential backoff and session resumption.
148. [pending] Idempotent order submission, so a restart mid-send cannot double-fill.
149. [pending] Clock and timezone discipline, including market calendar and half days.
150. [pending] A second market adapter to prove the abstraction, which the README
   claims but has never been exercised. Recommendation: crypto through `ccxt`. It
   trades around the clock, the data is free, and a venue with no market hours,
   no share lots and no tiered commissions stresses every assumption the IBKR
   adapter baked into `src/interfaces.py`.
151. [pending] Transaction cost analysis: expected fill against realised fill for
   every live order, aggregated by symbol and order type.
152. [pending] Feed measured costs back into the Phase 15 slippage and commission
   models, so the backtest's cost assumptions are calibrated from fills rather
   than guessed.

## Phase 21: Platform Contract & Strategy Framework
A platform is a promise to the code built on it. Phase 12 gave the promise a
shape: a version, a changelog, and one discovery path. This phase makes it
enforceable before Phases 22 through 25 widen it, so that the next breaking change
is caught in the private repository's own CI rather than discovered at import
time the way item 63 was.

153. [pending] A written deprecation policy for 1.0 and later: a breaking change to
   `BaseStrategy`, `IMarketAdapter`, `IDataLoader` or the commission signature is
   announced one minor release ahead with a runtime warning, then removed in the
   next major version with a migration note.
154. [pending] A conformance suite the private repository runs against its own
   strategies and adapters, exported as `quant_core.testing`. Phase 11's
   risk-parameter test is its first member: import it, point it at a strategy,
   and it proves the strategy honours what it declares. An adapter suite follows
   in Phase 20 once the simulated broker exists to run it against.
155. [pending] Strategy registry with declared metadata: asset class, required
   lookback, supported timeframes, author, version.
156. [pending] Parameter schema on each strategy, so the dashboard can generate its
   controls instead of hardcoding them. `get_params` is a start but is
   return-only.
157. [pending] Content-hash each strategy and record the hash on every run, so a
   result can always be traced to the exact code that produced it.
158. [pending] First-class meta-strategies as a platform pattern: wrap any strategy
   to scale, filter or gate it. `BaseStrategy.size_factor` exists for exactly this
   and nothing public uses it; the pattern belongs in the platform, specific
   wrappers do not.
159. [pending] Replace per-bar `numpy` recomputation with the engine's indicator API.
   `SimpleMACrossover` recomputes both moving averages from scratch on every bar,
   which is quadratic and leaves nothing to plot.
160. [pending] Multi-timeframe strategies as a supported pattern, on the alignment
   built in Phase 15.
161. [pending] Regime detection as a public, shared feature any strategy can read,
   rather than something each private strategy reimplements.
162. [pending] Retire the dashboard's `create_signal_executor` wrapper or make it
   real. No strategy returns a signal, so it is dead code.
163. [pending] Strategy scaffolding command that generates a new strategy, its tests,
   and its docs entry.
164. [pending] An event-driven backtest engine as an alternative to `backtesting.py`,
   which is single-asset and assumes bar data.

## Phase 22: Portfolio & Multi-Asset
The framework backtests one symbol at a time. Portfolio behaviour is where most
real risk lives.

165. [pending] Multi-asset portfolio backtest with a shared cash account.
166. [pending] Separate signal generation from position sizing: strategies emit
   target weights, a sizer turns weights into orders.
167. [pending] Portfolio construction methods: equal weight, volatility targeting,
   risk parity, and Kelly-fraction sizing.
168. [pending] Strategy ensembles with capital allocated across several strategies.
169. [pending] Rebalancing schedules with turnover and cost accounting.
170. [pending] Correlation matrix and portfolio-level drawdown reporting.
171. [pending] Exposure reporting by sector and by factor.
172. [pending] Portfolio-level risk limits: gross and net exposure, per-symbol
   concentration, per-sector concentration.
173. [pending] Realised and unrealised P&L with lot-level accounting, first in first
   out, which is what a broker statement and a tax return both expect.
174. [pending] Multi-currency support: positions in non-USD instruments, with FX
   conversion for equity and for every risk limit.

## Phase 23: Data Platform
Absorbs the data half of the original Phase 9.

175. [pending] Add data providers behind the existing `IDataLoader` interface, so
   yfinance is not the only source.
176. [pending] Intraday bar handling at one and five minute resolution. Original
   Phase 9, item 36.
177. [pending] Data quality checks: index gaps, duplicate timestamps, zero-volume
   bars, price outliers, timezone consistency. Fail loudly rather than backtest on
   bad data.
178. [pending] Explicit corporate action handling, independent of provider defaults.
179. [pending] Point-in-time universe membership, so a backtest sees the index as it
   was, not as it is.
180. [pending] Universe screening: choose symbols by liquidity, volatility and price
   floor rather than from a hardcoded list.
181. [pending] Incremental cache updates instead of re-downloading whole histories.
182. [pending] Scheduled refresh of cached data, so the catalogue is never stale by
   accident.
183. [pending] Store cached data as Parquet rather than CSV.
184. [pending] A data catalogue screen showing what is cached, its date range,
   quality flags, and freshness.
185. [pending] Record a content hash of the input data on every run.
186. [pending] Decide what data the platform ships. The deterministic synthetic
   fixture in `testing/conftest.py` is redistributable and drives the tests; the
   cached Yahoo CSVs under `data/benchmark/` are not clearly redistributable and
   should not be what a fresh checkout depends on. Either find a permissively
   licensed real dataset for the demo and the reference strategies, or make the
   synthetic fixture good enough to be the demo.
187. [pending] A plain note on data licensing. yfinance scrapes Yahoo and automated
   use sits outside its terms; say so in the docs and name the provider to move
   to before anything trades real money.

## Phase 24: Reference Strategies
Absorbs the original Phase 8 and the strategy half of the original Phase 9, and
changes what they are for. This repository does not do strategy research. It
ships one small, documented, tested reference strategy per platform capability,
so that every capability is demonstrated publicly and regression-tested in CI.
Each reference strategy comes with a doc page saying which platform features it
exercises and, plainly, that it is not expected to make money. The private
repository is where research happens, with these as its worked examples.

188. [pending] A research notebook template: load the fixture, run a strategy
   through the service module, render the Phase 16 statistics. The private
   repository's starting point for trying an idea.
189. [pending] Reference pairs strategy on public data, exercising two-asset data
   loading and the Phase 22 signal-and-sizer split. The private pairs strategy
   currently has no public counterpart, so the platform's pairs support is
   untested in the open.
190. [pending] Reference regime-aware strategy, exercising the shared regime feature
   from Phase 21.
191. [pending] Reference multi-timeframe strategy, exercising the alignment from
   Phase 15.
192. [pending] Reference machine-learning strategy with a small model trained on
   public data, exercising the whole Phase 25 lifecycle: feature store, registry,
   drift check, retrain gate.
193. [pending] Reference portfolio strategy, exercising Phase 22's multi-asset
   engine, a construction method and the rebalance schedule.
194. [pending] Reference intraday strategy on the Phase 23 minute bars. Original
   Phase 9, items 35 and 37, reframed: VWAP and gap logic as a demonstration of
   intraday support, not as a candidate for capital.
195. [pending] Retire or rewrite the existing four technical strategies to the same
   standard: one doc page each, one conformance run each, and the same
   disclaimer.

## Phase 25: Machine Learning Lifecycle
196. [pending] A test that asserts training and inference produce identical features.
   `README.md` calls this critical; nothing enforces it.
197. [pending] Feature store with point-in-time correctness.
198. [pending] Model registry recording training data range, hyperparameters, metrics,
   and the code hash.
199. [pending] Drift monitoring on live feature distributions against training.
200. [pending] Explainability reporting for any registered model, demonstrated on
   the Phase 24 reference model.
201. [pending] Automated retraining schedule with promotion gates, using the purged
   cross-validation from Phase 16 as the gate.

## Phase 26: Service Layer & API
Phase 13's service module made the core callable from Python. This makes it
callable from anywhere. The dashboard becomes one client among several and can be
replaced without touching the engine, and a phone can reach the kill switch.

202. [pending] An HTTP API over the service module: runs, strategies, the data
   catalogue, risk state, live status, and the kill switch.
203. [pending] Authentication. It will expose live positions.
204. [pending] Move the dashboard and the CLI onto the API, so there is one path into
   the engine.
205. [pending] A minimal status page that works on a phone: equity, open positions,
   the last few events, the kill switch. The page to open when an alert fires.
206. [pending] Decide whether the Streamlit dashboard stays or is replaced by a
   frontend built against the API, with the Phase 13 design canvas as the
   specification. The three places Streamlit fought the design in Phase 13 are
   the evidence for this decision.

## Phase 27: Operational Readiness
Run continuously alongside the phases above rather than as a block.

207. [pending] Structured logging to `logs/` with rotation.
208. [pending] External heartbeat / dead man's switch for the supervisor. Carried over
   from Phase 6, item 28.
209. [pending] Telegram notifier. `docs/safety_and_recovery.md` promises
   "Discord/Telegram" but `src/notifications.py` implements Discord only.
210. [pending] Daily summary notification at market close.
211. [pending] Alert routing rules by severity and channel.
212. [pending] Health endpoint exposing connection state, last bar time, and open
   position count.
213. [pending] A scheduler for the recurring jobs this plan has accumulated: data
   refresh (Phase 23), the daily paper run (Phase 19), the decay check
   (Phase 16), retraining (Phase 25). One place to define them, one log to read.
214. [pending] A nightly benchmark against the test fixture, checked against the
   regression baseline, so an engine regression surfaces overnight rather than at
   the next release.
215. [pending] Move run storage to SQLite once the file-based store strains.
216. [pending] Deployment and operations runbook.

## Phase 28: Distribution & Documentation
For a platform, this phase is the product surface.

217. [pending] Publish the package to an index, so the private repository can depend
   on a version range rather than a git tag. Phase 12 already made it
   installable.
218. [pending] A release process: tag, changelog entry, package build, docs build,
   in one command.
219. [pending] Docker image and a one-command local setup.
220. [pending] Example notebook gallery, seeded by the Phase 24 template.
221. [pending] A public demo running on sample data with private strategies disabled.
222. [pending] Document every extension point as a contract: strategies, market
   adapters, data providers, commission models, risk checks, notifiers. Each page
   names the interface, the conformance test to run, and the versioning promise.
223. [pending] Published documentation site generated from `docs/`.
224. [pending] Contribution guide and pull request template.

## Phase 29: Housekeeping
Run continuously. None of these blocks anything.

225. [pending] Deduplicate `run_backtesting/run_backtest.py` and `benchmark.py`, 845
   lines between them sharing strategy discovery, data loading and report
   writing, onto the Phase 13 service module.
226. [pending] Reconcile the codebase with its own type annotations so `ty` can
   become blocking in Phase 17.
227. [pending] Implement or delete `src/metrics.py`, which is an empty file. It is the
   natural home for the Phase 16 statistics.
228. [pending] Replace the `main.py` hello-world stub, or remove it in favour of the
   `qc` console script.
229. [pending] Reconcile documentation with behaviour, including the safety and
   recovery doc's claims about reconciliation and notification channels.
230. [pending] Reframe `README.md`. It opens the reports section with "to understand
   the framework's performance", which invites reading reference-strategy numbers
   as a track record. Say what the strategies are for and what the numbers are.
