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
        # Flatten columns if MultiIndex (Open, Ticker) -> (Open_Ticker) or just keep as is?
        # The project expects: Date, Open, High, Low, Close, Volume (lowercase or capitalized)
        # If multiple tickers, yf returns (Price, Ticker).
        
        if len(args.tickers) > 1:
            # For pairs, we might want to keep it as is or format it.
            # The PairsTradingStrategy expects columns like 'Close_PEP', 'Close_KO' or just 'PEP', 'KO' for close prices?
            # Let's check the pairs strategy data loading.
            # It expects a CSV with columns.
            # For now, just save it.
            pass
            
        data.to_csv(args.output)
        print(f"Data saved to {args.output}")
