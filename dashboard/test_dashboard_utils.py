import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dashboard import dashboard_utils

def test_utils() -> None:
    print("Testing Strategy Discovery...")
    strategies = dashboard_utils.discover_strategies()
    print(f"Found {len(strategies['standalone'])} standalone strategies.")
    print(f"Found {len(strategies['meta'])} meta strategies.")
    
    if len(strategies['standalone']) > 0:
        print(f"Sample Strategy: {strategies['standalone'][0]['name']}")
    
    print("\nTesting Data Loading...")
    files = dashboard_utils.get_available_assets()
    print(f"Found {len(files)} data files.")
    
    if len(files) > 0:
        print(f"Sample File: {list(files.keys())[0]}")
        data = dashboard_utils.load_asset_data(list(files.keys())[0], files)
        if data is not None:
            print(f"Loaded {list(files.keys())[0]}: Shape {data.shape}")
        else:
            print(f"Failed to load {list(files.keys())[0]}")

if __name__ == "__main__":
    test_utils()
