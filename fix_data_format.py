import pandas as pd
import sys

def fix_data(filepath):
    try:
        # Read with multi-index header
        df = pd.read_csv(filepath, header=[0,1,2], index_col=0, parse_dates=True)
        
        # Check if it's the weird yfinance format
        # Columns might be (Price, Ticker, something)
        # We just want to flatten or extract 'Close'
        
        # If columns are multi-index, let's try to simplify
        if isinstance(df.columns, pd.MultiIndex):
            # Dropping levels might be enough if it's just one ticker
            df.columns = df.columns.droplevel(1) # Drop Ticker
            # Now columns might be (Price, something)
            # Actually, let's just grab the 'Close' column if it exists in the top level
            
            # Let's try to just rename columns based on their order if we know it
            # Based on the file content: Price, Close, High, Low, Open, Volume
            # The columns in the file are: Date, Close, High, Low, Open, Volume (values)
            pass

        # Re-read as plain text to avoid multi-index confusion
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        # We know the data starts at line 3 (0-indexed)
        # And the columns are Date, Close, High, Low, Open, Volume
        # But wait, line 0 says: Price, Close, High, Low, Open, Volume
        # Line 1 says: Ticker, SPY, SPY, SPY, SPY, SPY
        # Line 2 says: Date,,,,,
        
        # So the columns are likely: Date, Close, High, Low, Open, Volume
        # Let's just rewrite the header
        
        header = "Date,Close,High,Low,Open,Volume\n"
        data_lines = lines[3:]
        
        with open(filepath, 'w') as f:
            f.write(header)
            f.writelines(data_lines)
            
        print(f"Fixed {filepath}")
        
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")

if __name__ == "__main__":
    fix_data("data/SPY_2010_2023_formatted.csv")
