import sys
import os
import importlib

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_import() -> None:
    module_name = "strategies_private.ensemble_signal_strategy"
    try:
        module = importlib.import_module(module_name)
        print(f"Successfully imported {module_name}")
        print(f"Module file: {module.__file__}")
    except ImportError as e:
        print(f"Failed to import {module_name}: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_import()
