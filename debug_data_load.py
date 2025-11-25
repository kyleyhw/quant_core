import pandas as pd
import sys

file_path = "data/SPY_2024_2025.csv"

print("--- Raw File Content (First 5 lines) ---")
with open(file_path, 'r') as f:
    for i in range(5):
        print(repr(f.readline()))

print("\n--- Pandas Load Attempt 1 (header=0) ---")
try:
    df = pd.read_csv(file_path, header=0)
    print("Columns:", df.columns.tolist())
    print("First 3 rows:")
    print(df.head(3))
except Exception as e:
    print(e)

print("\n--- Pandas Load Attempt 2 (header=[0,1]) ---")
try:
    df = pd.read_csv(file_path, header=[0,1])
    print("Columns:", df.columns.tolist())
    print("First 3 rows:")
    print(df.head(3))
except Exception as e:
    print(e)
