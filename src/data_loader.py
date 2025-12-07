import pandas as pd
import os
from typing import List, Set
from src.data_downloader import download_data

DEFAULT_PERMANENT_TICKERS = {"SPY", "QQQ", "IWM", "GLD", "TLT"}

class SmartLoader:
    def __init__(self, data_dir: str = "data", permanent_tickers: Set[str] = None):
        self.data_dir = data_dir
        self.permanent_tickers = permanent_tickers if permanent_tickers is not None else DEFAULT_PERMANENT_TICKERS
        self.created_files = [] # Track files created during this session

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup ephemeral files on exit."""
        self.cleanup()

    def cleanup(self):
        """Deletes files for non-permanent tickers created during this session."""
        for file_path in self.created_files:
            if not os.path.exists(file_path):
                continue
            
            # Extract ticker from filename to check permanence
            # Filename format: {ticker}_{start}_{end}.csv
            filename = os.path.basename(file_path)
            # Simple heuristic: Split by first underscore. 
            # Note: This assumes ticker doesn't have underscores, which is standard for Yahoo (e.g. BRK-B)
            # If complex tickers involved, might need more robust parsing, but strictly 
            # relying on download_data naming convention: f"{ticker}_{start}_{end}.csv"
            
            parts = filename.split('_')
            if not parts:
                continue
                
            ticker = parts[0]
            
            if ticker not in self.permanent_tickers:
                try:
                    os.remove(file_path)
                    print(f"Cleaned up ephemeral data: {file_path}")
                except OSError as e:
                    print(f"Error cleaning up {file_path}: {e}")

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
        new_files = download_data(
            tickers=[ticker], 
            start_date=start, 
            end_date=end, 
            output_dir=self.data_dir, 
            force_download=force_download
        )
        
        # Register new files for potential cleanup
        if new_files:
             self.created_files.extend(new_files)
        
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
