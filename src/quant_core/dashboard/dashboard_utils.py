import glob
import os
from typing import Any

import pandas as pd
import streamlit as st
import yfinance as yf

from quant_core.registry import discover_strategies as _discover

# Data lives under the directory the dashboard was launched from, so the same
# dashboard works from a checkout of the platform or from a project using it.
DEFAULT_DATA_PATH = os.path.join("data", "benchmark")


def discover_strategies() -> dict:
    """
    Installed strategies, from the ``quant_core.strategies`` entry-point group.

    Returns ``{"standalone": [config, ...], "meta": {name: config}, "errors": [...]}``
    where each config has ``name``, ``class``, ``source`` (the distribution that
    registered it), ``is_meta`` and ``data_assets``.
    """
    discovery = _discover()
    standalone: list[dict[str, Any]] = []
    meta: dict[str, dict[str, Any]] = {}
    for name, s in discovery.strategies.items():
        config = {
            "name": name,
            "class": s.cls,
            "source": s.distribution,
            "is_meta": hasattr(s.cls, "underlying_strategy"),
            "data_assets": s.data_assets,
        }
        if config["is_meta"]:
            meta[name] = config
        else:
            standalone.append(config)
    return {"standalone": standalone, "meta": meta, "errors": discovery.errors}


def get_data_files() -> list[str]:
    """CSV files under ``data/benchmark`` in the current working directory."""
    if not os.path.exists(DEFAULT_DATA_PATH):
        return []
    return sorted(glob.glob(os.path.join(DEFAULT_DATA_PATH, "*.csv")))


def get_available_assets() -> dict[str, str]:
    """
    Scans data files and builds a dictionary of available assets.
    It reads headers to find all tickers in multi-asset files.
    Returns a dictionary mapping asset names to their source file.
    e.g., {'SPY': 'path/SPY.csv', 'AAPL': 'path/TECH.csv', 'PEP-KO': 'path/PEP_KO.csv'}
    """
    assets = {}
    files = get_data_files()

    for file_path in files:
        filename = os.path.basename(file_path)
        try:
            # Check for MultiIndex (Price/Ticker structure) by reading first two lines
            with open(file_path) as f:
                header_line_1 = f.readline()
                header_line_2 = f.readline()

            is_multi_asset = "Ticker" in header_line_2 or "Price" in header_line_1

            if is_multi_asset:
                # For multi-asset files, get tickers from columns
                df_peek = pd.read_csv(file_path, header=[0, 1], index_col=0, nrows=0)
                tickers = df_peek.columns.get_level_values(1).unique().tolist()

                # If it looks like a pair file by name, also add a pair entry
                # e.g. PEP_KO.csv -> PEP-KO
                parts = filename.replace(".csv", "").split("_")
                if len(parts) == 2 and len(tickers) == 2:
                    asset_name = f"{parts[0]}-{parts[1]}"
                    assets[asset_name] = file_path

                # Add each individual ticker
                for ticker in tickers:
                    assets[ticker] = file_path
            else:
                # For single asset files, infer from filename
                asset_name = filename.replace(".csv", "").split("_")[0]
                assets[asset_name] = file_path
        except Exception as e:
            print(f"Could not parse {filename}: {e}")

    return assets


def load_asset_data(asset_name: str, assets_map: dict[str, str]) -> pd.DataFrame | None:
    """
    Loads data for a specific asset (ticker or pair) using the assets map.
    - For pairs (e.g., 'PEP-KO'), it loads the full multi-asset file.
    - For single tickers (e.g., 'AAPL') from a multi-asset file, it extracts
      just that ticker's data.
    - For single tickers from a single-asset file, it loads that file.
    """
    if asset_name not in assets_map:
        return None

    file_path = assets_map[asset_name]

    try:
        # First, determine if the source file is multi-asset by inspecting its headers
        with open(file_path) as f:
            header_line_1 = f.readline()
            header_line_2 = f.readline()
        is_multi_asset_file = "Ticker" in header_line_2 or "Price" in header_line_1

        if is_multi_asset_file:
            df_multi = pd.read_csv(file_path, header=[0, 1], index_col=0, parse_dates=True)
            df_multi.index = pd.to_datetime(df_multi.index, utc=True).tz_localize(None)
            df_multi.columns.names = ["Price", "Ticker"]

            # If the asset is a pair (e.g., 'PEP-KO'), we're done. Return the whole thing.
            if "-" in asset_name:
                return df_multi

            # Otherwise, it's a single ticker from a multi-asset file. Extract it.
            extracted = df_multi.xs(asset_name, axis=1, level="Ticker").copy()
            if not isinstance(extracted, pd.DataFrame):
                extracted = extracted.to_frame()
            extracted.columns = [col.capitalize() for col in extracted.columns]
            extracted.index.name = "Date"
            extracted.dropna(inplace=True)
            return extracted
        else:
            # It's a single-asset file
            df_single = pd.read_csv(file_path, header=0, index_col=0, parse_dates=True)
            df_single.index = pd.to_datetime(df_single.index, utc=True).tz_localize(None)
            df_single.columns = [col.capitalize() for col in df_single.columns]
            df_single.index.name = "Date"
            df_single.dropna(inplace=True)
            return df_single

    except Exception as e:
        print(f"Error loading data for {asset_name} from {file_path}: {e}")
        return None


@st.cache_data
def download_data_cached(tickers: list[str], start_date: Any, end_date: Any) -> pd.DataFrame | None:
    """
    Downloads data from yfinance and caches it for the session.
    Returns a pandas DataFrame.
    """
    try:
        # yfinance expects a space-separated string for multiple tickers
        ticker_str = " ".join(tickers)
        data = yf.download(ticker_str, start=start_date, end=end_date, interval="1d")
        if data.empty:
            st.error(f"No data found for tickers: {ticker_str}")
            return None

        # Clean and format data
        # Flatten MultiIndex if present (yfinance often returns Price/Ticker levels)
        if isinstance(data.columns, pd.MultiIndex):
            # If we requested a single ticker, we might still get a MultiIndex.
            # We need to drop the Ticker level if it exists and we only have one ticker.
            if len(tickers) == 1:
                data = data.xs(tickers[0], axis=1, level=1)

        # Ensure columns are standard capitalized format for backtesting.py
        # This handles both 'Open' and 'open', and ensures we have the right columns
        data.columns = [str(col).capitalize() for col in data.columns]

        # Filter for required columns
        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        available_cols = [col for col in required_cols if col in data.columns]
        data = data[available_cols]

        data.index = pd.to_datetime(data.index, utc=True).tz_localize(None)
        data.index.name = "Date"
        data.dropna(how="all", inplace=True)  # Drop rows where all data is missing
        return data

    except Exception as e:
        st.error(f"An error occurred during data download: {e}")
        return None
