import yfinance as yf
import pandas as pd

def download_data(ticker, start_date, end_date, filepath):
    """Downloads historical daily data from Yahoo Finance and saves it to a CSV."""
    print(f"Downloading {ticker} data from {start_date} to {end_date}...")
    data = yf.download(ticker, start=start_date, end=end_date, interval='1d')
    if data.empty:
        print(f"Error: No data found for {ticker}.")
        return
    data.to_csv(filepath)
    print(f"Data saved to {filepath}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Download historical data from Yahoo Finance.")
    parser.add_argument("--tickers", nargs="+", required=True, help="List of tickers to download")
    parser.add_argument("--start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", type=str, required=True, help="Output CSV file path")
    
    args = parser.parse_args()
    
    # If multiple tickers, download them together (for pairs or just batch)
    # But yfinance download returns a MultiIndex if multiple tickers.
    # For this project, we usually want single files or specific pair files.
    # If output is a single file, we assume we want them combined or it's a single ticker.
    
    print(f"Downloading {args.tickers} from {args.start} to {args.end}...")
    data = yf.download(args.tickers, start=args.start, end=args.end, interval='1d')
    
    if data.empty:
        print("Error: No data found.")
    else:
        # Check if output is a directory or file
        import os
        from pathlib import Path
        
        output_path = Path(args.output)
        
        # If multiple tickers and output doesn't end in .csv, treat as directory
        if len(args.tickers) > 1 and not args.output.lower().endswith('.csv'):
          # Define output directory
            DATA_DIR = Path(__file__).parent / "benchmark"
            DATA_DIR.mkdir(exist_ok=True)
            print(f"Saving individual files to {DATA_DIR}...")
            
            # yfinance returns MultiIndex (Price, Ticker) if multiple tickers
            # We need to iterate and save each
            if isinstance(data.columns, pd.MultiIndex):
                tickers = data.columns.get_level_values(1).unique()
                for ticker in tickers:
                    # Extract single ticker data
                    df = data.xs(ticker, axis=1, level=1)
                    # Drop rows where all cols are NaN (if any)
                    df = df.dropna(how='all')
                    
                    if not df.empty:
                        # Construct filename: TICKER_START_END.csv
                        filename = f"{ticker}_{args.start}_{args.end}.csv"
                        file_path = output_path / filename
                        df.to_csv(file_path)
                        print(f"Saved {ticker} to {file_path}")
            else:
                # Should not happen if len(tickers) > 1, but fallback
                print("Warning: Multiple tickers requested but single-index returned. Saving to generic file.")
                data.to_csv(output_path / "downloaded_data.csv")
                
        else:
            # Single file output (Aggregate or Single Ticker)
            data.to_csv(args.output)
            print(f"Data saved to {args.output}")
