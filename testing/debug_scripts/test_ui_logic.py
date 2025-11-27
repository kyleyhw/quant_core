import sys
import os
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dashboard import utils

def test_pairs_data_merging():
    print("Testing Pairs Data Merging Logic...")
    
    # Mock assets map
    assets_map = utils.get_available_assets()
    
    # Select two assets
    asset1 = 'PEP'
    asset2 = 'KO'
    
    if asset1 not in assets_map or asset2 not in assets_map:
        print(f"Error: Assets {asset1} or {asset2} not found in map.")
        return

    print(f"Loading {asset1} and {asset2}...")
    df1 = utils.load_asset_data(asset1, assets_map)
    df2 = utils.load_asset_data(asset2, assets_map)
    
    if df1 is None or df2 is None:
        print("Error: Failed to load data.")
        return

    print(f"Loaded {asset1}: {df1.shape}")
    print(f"Loaded {asset2}: {df2.shape}")

    # Merge logic from app.py
    print("Merging...")
    df1_suffixed = df1.add_suffix('_1')
    df2_suffixed = df2.add_suffix('_2')
    df = pd.merge(df1_suffixed, df2_suffixed, left_index=True, right_index=True, how='inner')
    
    # Map Asset 1 back to standard OHLCV
    df['Open'] = df['Open_1']
    df['High'] = df['High_1']
    df['Low'] = df['Low_1']
    df['Close'] = df['Close_1']
    df['Volume'] = df['Volume_1']
    
    print(f"Merged DataFrame Shape: {df.shape}")
    print("Columns:", df.columns.tolist())
    
    expected_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'Close_1', 'Close_2']
    missing = [col for col in expected_cols if col not in df.columns]
    
    if missing:
        print(f"FAILED: Missing columns: {missing}")
    else:
        print("SUCCESS: Data merged correctly with expected columns.")

if __name__ == "__main__":
    test_pairs_data_merging()
