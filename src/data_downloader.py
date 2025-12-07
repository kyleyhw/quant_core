import yfinance as yf
import pandas as pd
import argparse
import os
from typing import List

def download_data(tickers: List[str], start_date: str, end_date: str, output_dir: str):
    """
    Downloads historical market data from Yahoo Finance and saves it to a CSV file.
    """
    print(f"Downloading data for {tickers} from {start_date} to {end_date}...")
    data = yf.download(tickers, start=start_date, end=end_date)
    
    if data.empty:
        print("No data downloaded. Please check the tickers and date range.")
        return

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Save each ticker to a separate CSV file
    if len(tickers) == 1:
        output_path = os.path.join(output_dir, f"{tickers[0]}_{start_date}_{end_date}.csv")
        data.to_csv(output_path)
        print(f"Data saved to {output_path}")
    else:
        for ticker in tickers:
            output_path = os.path.join(output_dir, f"{ticker}_{start_date}_{end_date}.csv")
            data.loc[:, (slice(None), ticker)].to_csv(output_path)
            print(f"Data for {ticker} saved to {output_path}")

def main(argv: list[str] | None = None):
    """Main entry point for the data downloader script."""
    parser = argparse.ArgumentParser(description="Download historical market data from Yahoo Finance.")
    parser.add_argument("--tickers", nargs="+", required=True, help="A list of tickers to download.")
    parser.add_argument("--start", required=True, help="The start date for the data in YYYY-MM-DD format.")
    parser.add_argument("--end", required=True, help="The end date for the data in YYYY-MM-DD format.")
    parser.add_argument("--output", default="data", help="The directory to save the downloaded data.")
    args = parser.parse_args(argv)

    download_data(args.tickers, args.start, args.end, args.output)

if __name__ == "__main__":
    main()
