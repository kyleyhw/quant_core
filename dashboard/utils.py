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

def discover_strategies():
    """
    Dynamically discovers and imports strategies from the project directories.
    Returns a dictionary of strategies.
    """
    strategies = {"standalone": [], "meta": {}}
    
    # Define search paths for public and private strategies
    public_path = Path(project_root) / 'strategies'
    private_path = public_path / 'private' / 'strategies_private'
    search_paths = [public_path]
    
    if private_path.exists() and any(private_path.iterdir()):
        search_paths.append(private_path)

    for path in search_paths:
        for file in path.glob('*.py'):
            if file.name.startswith(('__init__', 'base_')):
                continue

            module_name = f"{path.relative_to(Path(project_root)).as_posix().replace('/', '.')}.{file.stem}"
            
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

def load_available_data(data_path=None):
    """
    Scans the data directory for available CSV files.
    Returns a list of filenames.
    """
    if data_path is None:
        data_path = DEFAULT_DATA_PATH
        
    if not os.path.exists(data_path):
        return []
        
    csv_files = glob.glob(os.path.join(data_path, "*.csv"))
    return [os.path.basename(f) for f in csv_files]

def load_data_file(filename, data_path=None):
    """
    Loads a specific CSV file into a DataFrame formatted for Backtesting.py.
    """
    if data_path is None:
        data_path = DEFAULT_DATA_PATH
        
    file_path = os.path.join(data_path, filename)
    
    try:
        # Check for MultiIndex (Price/Ticker structure)
        with open(file_path, 'r') as f:
            header_line_1 = f.readline()
            header_line_2 = f.readline()
        
        if "Ticker" in header_line_2 or "Price" in header_line_1:
            # Multi-asset file
            full_data = pd.read_csv(file_path, header=[0, 1], index_col=0)
            full_data.index.name = 'date'
            return full_data, True # Return data and is_multi_asset flag
        else:
            # Single asset file
            df = pd.read_csv(file_path)
            
            # Standardize columns
            df.columns = [col.capitalize() for col in df.columns]
            
            # Standardize Index
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], utc=True)
                df.set_index('Date', inplace=True)
            elif 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], utc=True)
                df.set_index('date', inplace=True)
                df.index.name = 'Date'
            
            if isinstance(df.index, pd.DatetimeIndex):
                df.index = df.index.tz_localize(None)
            
            # Clean data
            df.dropna(inplace=True)
            
            return df, False # is_multi_asset = False
            
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None, False
