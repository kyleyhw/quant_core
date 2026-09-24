# Building on quant-core

quant-core is a platform. Strategies that are not part of it, including
proprietary ones, live in their own package, which installs quant-core as a
dependency. The platform never contains, imports or names them; it finds them
because the package declares them.

## Depend on a released version

In your package's `pyproject.toml`:

```toml
[project]
name = "my-strategies"
dependencies = ["quant-core"]

[tool.uv.sources]
quant-core = { git = "https://github.com/kyleyhw/quant_core", tag = "v0.3.0" }
```

Pin a tag, never a branch. Breaking changes and their migration notes are listed
in [CHANGELOG.md](../CHANGELOG.md).

## Register your strategies

```toml
[project.entry-points."quant_core.strategies"]
MyBreakout = "my_strategies.breakout:MyBreakout"
```

Each entry point resolves to a `backtesting.Strategy` subclass, normally a
`BaseStrategy` subclass written to the contract in
[Strategy Development](./strategy_development.md). The entry point name is the
display name everywhere: `qc`, the dashboard and reports.

Two class attributes change how the platform treats a strategy:

- `data_assets = 2` for a strategy that trades a pair. `qc backtest` and the
  dashboard merge two inputs with `_1` and `_2` suffixes; `qc benchmark` skips it.
- `underlying_strategy` for a wrapper. Register a configured subclass rather than
  the wrapper itself:

  ```python
  class ScaledBollinger(MyScalingWrapper):
      underlying_strategy = BollingerBandsStrategy
  ```

  A wrapper registered with `underlying_strategy = None` is skipped by the benchmark.

Anything a benchmark needs that used to be configured inside the platform, such as
which strategy a wrapper wraps or what parameters it runs with, now belongs on a
registered subclass in your package.

## Add `qc` commands

```toml
[project.entry-points."quant_core.commands"]
train-model = "my_strategies.cli:register"
```

```python
def register(subparsers):
    p = subparsers.add_parser("train-model", help="Train my model.")
    p.add_argument("--output", default="models/model.json")
    p.set_defaults(func=lambda args: train(args.output))
```

A plugin that fails to load prints a warning; it never stops the built-in
commands from working.

## Run the platform from your project

```bash
uv sync
uv run qc strategies    # your strategies appear next to the reference ones
uv run qc benchmark     # reads ./data/benchmark, writes ./reports
uv run qc dashboard
```

Every path is relative to the directory you run from, so data, models and
reports stay in your repository.

## Prove your strategies honour their risk parameters

Copy `testing/test_risk_parameters.py` from the quant-core tag you depend on into
your tests, and edit only the block marked "Point this at your strategies".
Its helpers and data come from `quant_core.testing` in the installed package. Run
it in your CI: when a future quant-core release changes the strategy contract,
this is the test that tells you before anything trades.

## Working on the platform and a strategy together

Two layouts work. Either way, your package depends on quant-core and never the
other way round.

**quant-core inside your repository, as a submodule.** The submodule's commit is
the pin, and editing the platform takes effect at once:

```bash
git submodule add https://github.com/kyleyhw/quant_core quant_core
git -C quant_core checkout v0.3.0
```

```toml
[tool.uv.sources]
quant-core = { path = "quant_core", editable = true }
```

CI needs `submodules: true` on its checkout step. Commit platform changes inside
the submodule and send them to quant-core as a pull request; move the submodule
to the new release once it is tagged.

**The two repositories side by side.** Pin a tag, and point at a local checkout
only while you work on both:

```toml
[tool.uv.sources]
quant-core = { git = "https://github.com/kyleyhw/quant_core", tag = "v0.3.0" }
# while working on both:
# quant-core = { path = "../quant_core", editable = true }
```

Switch back to the tag before committing, so CI and everyone else build against
a release.

## Troubleshooting

- **`qc strategies` exits non-zero.** A registered strategy failed to import or
  is not a `Strategy` subclass; the warning says which and why.
- **Strategies missing only when run from the quant_core checkout.** Delete any
  stale `quant_core.egg-info` directory at the repository root, left by builds
  from before 0.2.0. It shadows the installed package's metadata.
