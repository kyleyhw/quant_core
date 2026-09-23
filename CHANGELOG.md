# Changelog

All notable changes to quant-core. Versions follow semantic versioning. Before
1.0, a minor version bump signals a breaking change.

## [0.2.1] - 2026-09-23

### Fixed

- `quant_core.testing`: the probe measured a short trade's stop distance as
  `close - sl`, which is negative because a short's stop sits above the price.
  The conformance test's stop-distance check therefore failed for any strategy
  that goes short, and one trading both sides averaged towards zero.
  `Observation.stop_distance_pct` now measures on the losing side of the trade.
  Long-only strategies see identical numbers.

## [0.2.0] - 2026-09-23

The platform becomes an installable package that other packages build on. Code
that is not part of the platform, including proprietary strategies, now lives in
separate packages that depend on `quant-core` and register themselves through
entry points. This release also fixes the strategy base class, whose declared
risk parameters did nothing or the wrong thing.

Every breaking change a downstream package has to absorb is in this one release.

### Breaking

- **Package namespace.** Everything importable now lives under `quant_core`, in a
  `src/` layout. The old top-level packages `src`, `strategies`, `run_backtesting`
  and `dashboard` are gone, with no compatibility shims. See the import table
  under Migration.
- **Strategy contract.** `BaseStrategy` owns `next()`. Subclasses implement
  `on_bar()` for their signal logic and `on_init()` for setup. A subclass that
  defines `next()` raises `TypeError` when the class is created.
- **`CustomBacktest` and `CustomBroker` are removed**, along with
  `quant_core.backtesting_extensions`. Use `backtesting.Backtest`, which accepts
  callable commission models natively.
- **Strategy discovery uses entry points.** The platform no longer scans
  directories, and the dashboard's private mode is gone. A strategy is available
  if an installed package registers it in the `quant_core.strategies` group.
- **The `train-regime` and `train-ensemble` commands are removed from `qc`.**
  They trained models that are not part of the platform. A package can register
  its own commands through the `quant_core.commands` group.
- **`qc benchmark`:** `--scope` is removed. Use `--strategies NAME ...` to filter,
  and `--output-dir` to choose where the report goes.
- **`qc backtest` / `run_backtest`:** `--strategy-type` is removed. Use the
  generic `--param KEY=VALUE`, which is repeatable and overrides any strategy
  parameter.
- **Reports are written to `reports/`** under the working directory, instead of
  `strategies/reports/`. Every path is now relative to where the command runs,
  not to the source tree.
- **Benchmark configuration moves out of the platform.** The benchmark no longer
  carries a table of named strategies with their data files, wrapped strategy or
  parameters. Configure a wrapper by registering a subclass that sets
  `underlying_strategy`.

### Changed: backtest numbers move

These are corrections, and every strategy built on `BaseStrategy` will report
different results, usually worse:

- **The trailing stop now trails at `stop_loss_pct` of price.** It was set with
  `set_trailing_sl()`, which takes a multiple of average true range, so a 2% stop
  sat about 0.03% below price, roughly seventy times too tight.
- **Subclasses can no longer bypass the stop.** Before, a subclass that
  overrode `next()` without calling up ran with no stop at all.
- **Take-profit works.** It attaches an order at `entry * (1 + take_profit_pct)`
  for longs. Before, it was a bare `pass`.
- **Position size follows the risk budget:** `risk_percent / stop_loss_pct` of
  equity, capped at 1.0. With the defaults that is half the account. Before,
  backtests went all in regardless of `risk_percent`.
- **Commission is charged once, per order.** The removed `CustomBroker` charged a
  callable commission model twice: once through backtesting.py's own commission
  handling, and again by folding `commission(size, price) / size` into the fill
  price. For an order sized as a fraction of equity, such as an all-in `buy()`,
  `size` is that fraction, not a share count, so the second charge added roughly
  the whole minimum ticket fee to the price of every share. On a one-year daily
  backtest this came to 16 times the correct commission for a stock near $230,
  and 37 times for one near $24. It also raised `TypeError` for float rates.
  With commission set to zero, the old and new engines give identical results.

A strategy that genuinely wants the old behaviour of no stop and full size
should set `stop_loss_pct = 0` and `take_profit_pct = 0` explicitly.

### Added

- `qc strategies`: lists installed strategies, the package that registered each,
  and any that failed to load.
- `qc dashboard`: launches the bundled Streamlit dashboard from any project.
- `qc --version`.
- `quant_core.registry`: strategy and command discovery.
- `quant_core.testing`: `probe`, which records every open trade on every bar of a
  backtest, and `synthetic_ohlcv`, deterministic price data. These back the
  conformance test described below.
- `data_assets` class attribute. Set it to `2` for a strategy that trades a pair.
  `qc backtest` and the dashboard merge two inputs with `_1` and `_2` suffixes,
  and the benchmark skips the strategy.
- CI guard that fails if public files reference private code, and a CI job that
  installs the built wheel into a clean environment and runs everything from
  outside the source tree.
- [Building on quant-core](docs/building_on_quant_core.md), a guide for
  downstream packages.
- A release workflow. When a merge to `master` carries a version with no tag
  yet, it tags that commit `v<version>` and publishes a GitHub release from this
  changelog. It only creates tags, never moves or deletes them.

### Data

`data/benchmark/*.csv`, `data/SPY_1hour_1year.csv` and the files under
`data/training/` remain tracked in the repository in 0.2.0. They are not part of
the installed package. Commands read data from `./data` relative to where they
run, so a downstream project keeps its own copy. Whether this repository keeps
shipping Yahoo-sourced data is an open licensing question; if tracking stops, it
will be announced here.

### Migration

**1. Depend on the package instead of containing or being contained by it.**

```toml
[project]
dependencies = ["quant-core"]

[tool.uv.sources]
quant-core = { git = "https://github.com/kyleyhw/quant_core", tag = "v0.2.0" }
```

**2. Update imports.** The rule is mechanical:

| Old | New |
| :--- | :--- |
| `src.X` | `quant_core.X` |
| `strategies.X` | `quant_core.strategies.X` |
| `run_backtesting.X` | `quant_core.backtest.X` |
| `dashboard.X` | `quant_core.dashboard.X` |

Specific symbols:

| Old import | New import |
| :--- | :--- |
| `src.feature_engineering.FeatureEngineer` | `quant_core.feature_engineering.FeatureEngineer` |
| `src.interfaces.IMarketAdapter` | `quant_core.interfaces.IMarketAdapter` |
| `src.interfaces.IConnection`, `IDataLoader`, `IExecutionHandler` | `quant_core.interfaces.*` |
| `src.commission_models.ibkr_tiered_commission` | `quant_core.commission_models.ibkr_tiered_commission` |
| `src.commission_models.COMMISSION_MODELS` | `quant_core.commission_models.COMMISSION_MODELS` |
| `src.market_adapters.ibkr.data_loader.IBKRDataLoader` | `quant_core.market_adapters.ibkr.data_loader.IBKRDataLoader` |
| `src.market_adapters.ibkr.connection.IBConnection` | `quant_core.market_adapters.ibkr.connection.IBConnection` |
| `src.market_adapters.ibkr.execution.IBKRExecutionHandler` | `quant_core.market_adapters.ibkr.execution.IBKRExecutionHandler` |
| `src.market_adapters.ibkr.adapter.IBKRMarketAdapter` | `quant_core.market_adapters.ibkr.adapter.IBKRMarketAdapter` |
| `src.execution.ExecutionManager` | `quant_core.execution.ExecutionManager` |
| `src.notifications.Notifier`, `Severity` | `quant_core.notifications.Notifier`, `Severity` |
| `src.data_loader.SmartLoader` | `quant_core.data_loader.SmartLoader` |
| `src.data_downloader.download_data` | `quant_core.data_downloader.download_data` |
| `strategies.base_strategy.BaseStrategy` | `quant_core.strategies.base_strategy.BaseStrategy` |
| `strategies.simple_ma_crossover.SimpleMACrossover` | `quant_core.strategies.simple_ma_crossover.SimpleMACrossover` |
| `strategies.bollinger_bands.BollingerBandsStrategy` | `quant_core.strategies.bollinger_bands.BollingerBandsStrategy` |
| `strategies.rsi_2_period` (module) | `quant_core.strategies.rsi_2_period` |
| `strategies.buy_and_hold.BuyAndHoldStrategy` | `quant_core.strategies.buy_and_hold.BuyAndHoldStrategy` |
| `src.backtesting_extensions.CustomBacktest` | Removed. Use `backtesting.Backtest`. |

Remove any `sys.path` manipulation that reached into a quant-core checkout.

**3. Migrate strategies to the contract.** In every `BaseStrategy` subclass,
rename `next()` to `on_bar()` and delete `super().next()` calls. Wrappers that
drive another strategy call its `on_bar()`. Move setup from `init()` to
`on_init()`, and delete `init()` overrides that only call up.

**4. Register strategies and commands.**

```toml
[project.entry-points."quant_core.strategies"]
MyStrategy = "my_package.my_module:MyStrategy"

[project.entry-points."quant_core.commands"]
my-command = "my_package.cli:register"
```

A command entry point resolves to `register(subparsers)`, which adds an
`argparse` subcommand and calls `set_defaults(func=handler)`. Confirm with
`qc strategies` and `qc --help`.

**5. Run the conformance test.** Copy `testing/test_risk_parameters.py` from this
tag into your tests and edit only the block marked "Point this at your
strategies". It proves each strategy's stop, take-profit and sizing match what it
declares.

**6. Clean up an old checkout.** If a pre-0.2.0 checkout of this repository has a
`quant_core.egg-info` directory at its root, delete it. It shadows the installed
package's metadata when Python runs from that directory, and discovery then finds
no strategies.

## [0.1.0] - 2026-05-08

The last release before the strategy contract change and the package
restructure: `src`, `strategies` and `run_backtesting` as top-level packages,
strategies overriding `next()`, and folder-based strategy discovery. Pin to this
to keep running code that has not migrated.
