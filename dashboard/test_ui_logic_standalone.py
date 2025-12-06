import pandas as pd
import os

def load_csv(file_path: str) -> pd.DataFrame | None:
    try:
        df = pd.read_csv(file_path)
        df.rename(columns={'date': 'Date'}, inplace=True)
        date_col = [col for col in df.columns if col.lower() == 'date'][0]
        df[date_col] = pd.to_datetime(df[date_col], utc=True)
        df.set_index(date_col, inplace=True)
        df.index.name = 'Date'
        if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        df.columns = [col.capitalize() for col in df.columns]
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df.dropna(inplace=True)
        return df
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def test_merging() -> None:
    print("Testing Merging Logic...")
    file1 = "data/benchmark/PEP_2024-10-01_2025-11-25.csv"
    file2 = "data/benchmark/KO_2024-10-01_2025-11-25.csv"
    
    if not os.path.exists(file1) or not os.path.exists(file2):
        print("Data files not found.")
        return

    df1 = load_csv(file1)
    df2 = load_csv(file2)
    
    if df1 is None or df2 is None:
        print("Failed to load one or both dataframes.")
        return
    
    print(f"Loaded PEP: {df1.shape}")
    print(f"Loaded KO: {df2.shape}")
    
    # Merge logic
    df1_suffixed = df1.add_suffix('_1')
    df2_suffixed = df2.add_suffix('_2')
    df = pd.merge(df1_suffixed, df2_suffixed, left_index=True, right_index=True, how='inner')
    
    df['Open'] = df['Open_1']
    df['High'] = df['High_1']
    df['Low'] = df['Low_1']
    df['Close'] = df['Close_1']
    df['Volume'] = df['Volume_1']
    
    print(f"Merged Shape: {df.shape}")
    print("Columns:", df.columns.tolist())
    
    expected = ['Open', 'High', 'Low', 'Close', 'Volume', 'Close_1', 'Close_2']
    if all(col in df.columns for col in expected):
        print("SUCCESS: Merging logic verified.")
    else:
        print("FAILED: Missing columns.")

if __name__ == "__main__":
    test_merging()
