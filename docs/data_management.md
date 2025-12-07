# Data Management & Caching strategies

The framework utilizes a **"Smart Data"** system to optimize backtesting performance and disk usage. This system ensures that your workspace remains clean while providing fast access to frequently used data.

## Caching Mechanism

Our caching strategy is file-based (storage), not RAM-based. Data is downloaded from providers (like Yahoo Finance) and stored as `.csv` files in the `data/` directory.

### Ephemeral vs. Permanent Caching

To balance performance with disk cleanliness, we employ two types of caching:

1.  **Permanent Caching**:
    *   **Purpose**: For assets that are frequently backtested or serve as benchmarks.
    *   **Behavior**: Files are downloaded once and **persisted** in the `data/` directory. They are only re-downloaded if explicitly forced.
    *   **Default Permanent Tickers**: `SPY`, `QQQ`, `IWM`, `GLD`, `TLT`.

2.  **Ephemeral Caching**:
    *   **Purpose**: For ad-hoc backtests on arbitrary assets.
    *   **Behavior**: When you request a backtest for a non-permanent ticker (e.g., `NVDA`), the system follows this workflow:
        1.  **Download**: Fetches the data to a temporary file in `data/` (e.g., `NVDA_2024-01-01_2024-02-01.csv`).
        2.  **Execute**: Runs the backtest using this file.
        3.  **Cleanup**: Automatically **deletes** the file immediately after the backtest completes.

## Usage

### In CLI

You can trigger these behaviors directly via the CLI:

-   **Ephemeral Test**:
    ```bash
    uv run qc backtest --strategy SimpleMACrossover --data NVDA --start 2024-01-01 --end 2024-02-01
    ```
    *Outcome*: Downloads NVDA, runs test, deletes NVDA data.

-   **Permanent Test**:
    ```bash
    uv run qc backtest --strategy SimpleMACrossover --data SPY
    ```
    *Outcome*: Uses existing SPY data (or downloads and keeps it if missing).

-   **Forced Refresh**:
    ```bash
    uv run qc download --tickers SPY --force
    ```
    *Outcome*: Re-downloads SPY data, overwriting the existing cache.

### Programmatic Usage

You can use the `SmartLoader` context manager in your own scripts to leverage this logic:

```python
from src.data_loader import SmartLoader

# "NVDA" will be cleaned up on exit; "SPY" will be kept.
with SmartLoader() as loader:
    df_ephemeral = loader.load_data("NVDA", start="2024-01-01", end="2024-02-01")
    df_permanent = loader.load_data("SPY", start="2024-01-01", end="2024-02-01")
    
    # Run your analysis...
```
