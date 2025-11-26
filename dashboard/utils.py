import streamlit as st
import yfinance as yf
import os
import sys
import importlib
import inspect
import glob
from pathlib import Path
import pandas as pd
from backtesting import Strategy

# --- Add project root to path ---
# Assuming this file is in project_root/dashboard/utils.py
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from strategies.base_strategy import BaseStrategy

# Default Data Path
DEFAULT_DATA_PATH = os.path.join(project_root, "data", "benchmark")

def discover_strategies(private_mode=False):
    """
    Dynamically discovers and imports strategies from the project directories.
    Returns a dictionary of strategies.
    If private_mode is True, it will also search the private strategies directory.
    """
    strategies = {"standalone": [], "meta": {}}
    
    # Define search paths for public and private strategies
    public_path = Path(project_root) / 'strategies'
    search_paths = [public_path]

    # --- Secure Private Strategy Discovery ---
    # Only look for private strategies if the flag is set
    if private_mode:
        private_path = Path(project_root) / 'strategies_private'
        if private_path.exists() and any(private_path.iterdir()):
            search_paths.append(private_path)
            print("Private mode enabled: Searching for private strategies.")
        else:
            print("Warning: Private mode enabled, but private strategies directory not found.")
    
    for path in search_paths:
        # In private mode, we need to look one level deeper for the actual strategy files
        strategy_files_path = path
        if private_mode and path.name == 'strategies_private':
             strategy_files_path = path

        for file in strategy_files_path.glob('*.py'):
            if file.name.startswith(('__init__', 'base_')):
                continue

            # Construct module name for import
            # e.g., strategies.bollinger_bands or strategies_private.pairs_trading_strategy
            relative_path_parts = path.relative_to(Path(project_root)).parts
            module_prefix = '.'.join(relative_path_parts)
            module_name = f"{module_prefix}.{file.stem}"
            
            try:
                module = importlib.import_module(module_name)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Check if it's a valid, non-base strategy class
                    if issubclass(obj, (Strategy, BaseStrategy)) and obj not in (Strategy, BaseStrategy):
                        scope = "private" if "strategies_private" in module_name else "public"
                        
                        is_meta = hasattr(obj, 'underlying_strategy')

                        config = {
                            "name": name,
                            "class": obj,
                            "scope": scope,
                            "is_meta": is_meta
                        }
                        
                        if is_meta:
                            strategies["meta"][name] = config
                        else:
                            strategies["standalone"].append(config)

            except ImportError as e:
                print(f"Error importing module {module_name}: {e}")

    return strategies
def get_data_files():

    """Scans all relevant data directories for CSV files."""

    search_paths = [os.path.join(project_root, "data", "benchmark")]

    

    # Securely add private data path if in private mode

    private_mode = os.environ.get('QUANT_CORE_PRIVATE_MODE', 'false').lower() == 'true'

    if private_mode:

        private_data_path = os.path.join(project_root, "strategies_private", "data")

        if os.path.exists(private_data_path):

            search_paths.append(private_data_path)



    all_files = []

    for path in search_paths:

        if os.path.exists(path):

            all_files.extend(glob.glob(os.path.join(path, "*.csv")))

    return all_files



def get_available_assets():
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
            with open(file_path, 'r') as f:
                header_line_1 = f.readline()
                header_line_2 = f.readline()
            
            is_multi_asset = "Ticker" in header_line_2 or "Price" in header_line_1
            
            if is_multi_asset:
                # For multi-asset files, get tickers from columns
                df_peek = pd.read_csv(file_path, header=[0, 1], index_col=0, nrows=0)
                tickers = df_peek.columns.get_level_values(1).unique().tolist()
                
                # If it looks like a pair file by name, also add a pair entry
                parts = filename.split('_')
                if len(tickers) == 2 and parts[1].isalpha():
                     asset_name = f"{parts[0]}-{parts[1]}"
                     assets[asset_name] = file_path

                # Add each individual ticker
                for ticker in tickers:
                    assets[ticker] = file_path
            else:
                # For single asset files, infer from filename
                asset_name = filename.split('_')[0]
                assets[asset_name] = file_path
        except Exception as e:
            print(f"Could not parse {filename}: {e}")
            
    return assets


def load_asset_data(asset_name, assets_map):
    """
    Loads data for a specific asset (ticker or pair) using the assets map.
    - For pairs (e.g., 'PEP-KO'), it loads the full multi-asset file.
    - For single tickers (e.g., 'AAPL') from a multi-asset file, it extracts just that ticker's data.
    - For single tickers from a single-asset file, it loads that file.
    """
    if asset_name not in assets_map:
        return None
        
    file_path = assets_map[asset_name]
    
    try:
        # First, determine if the source file is multi-asset by inspecting its headers
        with open(file_path, 'r') as f:
            header_line_1 = f.readline()
            header_line_2 = f.readline()
        is_multi_asset_file = "Ticker" in header_line_2 or "Price" in header_line_1

        if is_multi_asset_file:
            df_multi = pd.read_csv(file_path, header=[0, 1], index_col=0, parse_dates=True)
            df_multi.index = pd.to_datetime(df_multi.index, utc=True).tz_localize(None)
            df_multi.columns.names = ['Price', 'Ticker']

            # If the asset is a pair (e.g., 'PEP-KO'), we're done. Return the whole thing.
            if '-' in asset_name:
                return df_multi
            
            # Otherwise, it's a single ticker from a multi-asset file. Extract it.
            single_df = df_multi.xs(asset_name, axis=1, level='Ticker').copy()
            single_df.columns = [col.capitalize() for col in single_df.columns]
            single_df.index.name = 'Date'
            single_df.dropna(inplace=True)
            return single_df
        else:
            # It's a single-asset file
            df_single = pd.read_csv(file_path, header=0, index_col=0, parse_dates=True)
            df_single.index = pd.to_datetime(df_single.index, utc=True).tz_localize(None)
            df_single.columns = [col.capitalize() for col in df_single.columns]
            df_single.index.name = 'Date'
            df_single.dropna(inplace=True)
            return df_single

    except Exception as e:
        print(f"Error loading data for {asset_name} from {file_path}: {e}")
        return None
@st.cache_data
def download_data_cached(tickers, start_date, end_date):
    """
    Downloads data from yfinance and caches it for the session.
    Returns a pandas DataFrame.
    """
    try:
        # yfinance expects a space-separated string for multiple tickers
        ticker_str = " ".join(tickers)
        data = yf.download(ticker_str, start=start_date, end=end_date, interval='1d')
        if data.empty:
            st.error(f"No data found for tickers: {ticker_str}")
            return None
        
        # Clean and format data
        if len(tickers) == 1:
            # For single ticker, yfinance returns a simple DataFrame
            # Ensure columns are standard capitalized format for backtesting.py
            data.columns = [str(col).capitalize() for col in data.columns]
        else:
            # Multi-ticker download returns a MultiIndex
            data.columns.names = ['Price', 'Ticker']
            
        data.index = pd.to_datetime(data.index, utc=True).tz_localize(None)
        data.index.name = 'Date'
        data.dropna(how='all', inplace=True) # Drop rows where all data is missing
        return data
        
    except Exception as e:
        st.error(f"An error occurred during data download: {e}")
        return None
