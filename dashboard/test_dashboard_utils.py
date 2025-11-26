import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dashboard import utils

def test_utils():
    print("Testing Strategy Discovery...")
    strategies = utils.discover_strategies()
    print(f"Found {len(strategies['standalone'])} standalone strategies.")
    print(f"Found {len(strategies['meta'])} meta strategies.")
    
    if len(strategies['standalone']) > 0:
        print(f"Sample Strategy: {strategies['standalone'][0]['name']}")
    
    print("\nTesting Data Loading...")
    files = utils.load_available_data()
    print(f"Found {len(files)} data files.")
    
    if len(files) > 0:
        print(f"Sample File: {files[0]}")
        data, is_multi = utils.load_data_file(files[0])
        if data is not None:
            print(f"Loaded {files[0]}: Shape {data.shape}, Multi-Asset: {is_multi}")
        else:
            print(f"Failed to load {files[0]}")

if __name__ == "__main__":
    test_utils()
