import pandas as pd
import os
from src.data_downloader import download_data

class SmartLoader:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir

    def load_data(self, ticker: str, start: str, end: str, force_download: bool = False) -> pd.DataFrame:
        """
        Loads data for a ticker. Downloads if missing or force_download is True.
        
        Args:
            ticker: The stock ticker symbol.
            start: Start date in YYYY-MM-DD format.
            end: End date in YYYY-MM-DD format.
            force_download: If True, forces a fresh download even if data exists.
            
        Returns:
            pd.DataFrame: The loaded market data.
        """
        # Ensure data exists (download_data handles caching checks now)
        # We pass force_download locally; data_downloader handles the existence check if force is False
        download_data(
            tickers=[ticker], 
            start_date=start, 
            end_date=end, 
            output_dir=self.data_dir, 
            force_download=force_download
        )
        
        # Construct path (matching the format in data_downloader)
        file_path = os.path.join(self.data_dir, f"{ticker}_{start}_{end}.csv")
        
        if not os.path.exists(file_path):
             # This might happen if yfinance failed silent or data empty
             raise FileNotFoundError(f"Data file not found after download attempt: {file_path}. Check if ticker is valid.")
             
        # Load and return
        try:
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
            return df
        except Exception as e:
            raise IOError(f"Failed to read CSV file {file_path}: {e}")
