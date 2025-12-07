import yfinance as yf
import pandas as pd
import argparse
import os
from typing import List

def download_data(tickers: List[str], start_date: str, end_date: str, output_dir: str, force_download: bool = False) -> List[str]:
    """
    Downloads historical market data from Yahoo Finance and saves it to a CSV file.
    Checks for existing files to avoid redundant downloads unless force_download is True.
    Returns a list of paths to the data files (including those found in cache if force_download=False).
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    tickers_to_download = []
    cached_files = []
    
    # Check cache for each ticker
    if not force_download:
        for ticker in tickers:
            expected_path = os.path.join(output_dir, f"{ticker}_{start_date}_{end_date}.csv")
            if os.path.exists(expected_path):
                print(f"Cache hit for {ticker}: {expected_path}")
                cached_files.append(expected_path)
            else:
                tickers_to_download.append(ticker)
    else:
        tickers_to_download = tickers
        
    if not tickers_to_download:
        print("All requested data found in cache.")
        return cached_files

    print(f"Downloading data for {tickers_to_download} from {start_date} to {end_date}...")
    try:
        data = yf.download(tickers_to_download, start=start_date, end=end_date)
    except Exception as e:
        print(f"Failed to download data: {e}")
        return
    
    if data.empty:
        print("No data downloaded. Please check the tickers and date range.")
        return

    # Save each ticker to a separate CSV file
    created_files = []
    if len(tickers_to_download) == 1:
        ticker = tickers_to_download[0]
        output_path = os.path.join(output_dir, f"{ticker}_{start_date}_{end_date}.csv")
        data.to_csv(output_path)
        print(f"Data saved to {output_path}")
        created_files.append(output_path)
    else:
        for ticker in tickers_to_download:
            output_path = os.path.join(output_dir, f"{ticker}_{start_date}_{end_date}.csv")
            # Handle MultiIndex columns if multiple tickers returned
            try:
                ticker_data = data.xs(ticker, axis=1, level=1)
            except KeyError:
                # Fallback implementation if level 1 is not ticker (depends on yfinance version/structure)
                # Ensure we are robust to structure
                 ticker_data = data.loc[:, (slice(None), ticker)]
                 
            ticker_data.to_csv(output_path)
            print(f"Data for {ticker} saved to {output_path}")
            created_files.append(output_path)
            
    return cached_files + created_files

def main(argv: list[str] | None = None):
    """Main entry point for the data downloader script."""
    parser = argparse.ArgumentParser(description="Download historical market data from Yahoo Finance.")
    parser.add_argument("--tickers", nargs="+", required=True, help="A list of tickers to download.")
    parser.add_argument("--start", required=True, help="The start date for the data in YYYY-MM-DD format.")
    parser.add_argument("--end", required=True, help="The end date for the data in YYYY-MM-DD format.")
    parser.add_argument("--output", default="data", help="The directory to save the downloaded data.")
    parser.add_argument("--force", action="store_true", help="Force download even if file exists.")
    args = parser.parse_args(argv)

    download_data(args.tickers, args.start, args.end, args.output, getattr(args, 'force', False))

if __name__ == "__main__":
    main()
