import os
import glob
import sys

path = r"c:\Users\Kyle\PycharmProjects\ibkr_quant_core\data\stocks_2024_2025"
print(f"Checking path: {path}")
if os.path.isdir(path):
    print("Path is a directory.")
    files = glob.glob(os.path.join(path, "*.csv"))
    print(f"Found {len(files)} CSV files:")
    for f in files:
        print(f" - {os.path.basename(f)}")
else:
    print("Path is NOT a directory.")
    print(f"Exists? {os.path.exists(path)}")
