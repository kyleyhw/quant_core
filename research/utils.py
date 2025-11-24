"""
Helper utilities for research and ML training.
Provides simplified synchronous wrappers around async IBConnection/DataLoader.
"""

import asyncio
from typing import Optional
import pandas as pd
from src.connection import IBConnection
from src.data_loader import DataLoader

class SimpleDataFetcher:
    """
    Simplified synchronous wrapper for fetching historical data.
    Useful for Jupyter notebooks and scripting.
    """
    
    def __init__(self):
        self.conn = None
        self.loader = None
    
    def fetch_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        bar_size: str = '1 day',
        sec_type: str = 'STK',
        exchange: str = 'SMART',
        currency: str = 'USD'
    ) -> pd.DataFrame:
        """
        Fetch historical data synchronously.
        
        Args:
            symbol: Ticker symbol (e.g., 'SPY')
            start_date: Start date 'YYYY-MM-DD'
            end_date: End date 'YYYY-MM-DD'
            bar_size: '1 day', '1 hour', '1 min', etc.
            sec_type: 'STK', 'FUT', 'CASH', etc.
            exchange: Exchange name
            currency: Base currency
            
        Returns:
            DataFrame with OHLCV data
        """
        return asyncio.run(self._fetch_async(
            symbol, start_date, end_date, bar_size, sec_type, exchange, currency
        ))
    
    async def _fetch_async(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        bar_size: str,
        sec_type: str,
        exchange: str,
        currency: str
    ) -> pd.DataFrame:
        """
        Internal async implementation.
        """
        self.conn = IBConnection()
        
        try:
            # Connect
            if not await self.conn.connect():
                raise ConnectionError("Failed to connect to IBKR TWS/Gateway")
            
            self.loader = DataLoader(self.conn)
            
            # Create contract
            contract = await self.loader.create_contract(
                symbol=symbol,
                sec_type=sec_type,
                exchange=exchange,
                currency=currency
            )
            
            if not contract:
                raise ValueError(f"Failed to qualify contract for {symbol}")
            
            # Calculate duration
            from datetime import datetime
start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            days = (end_dt - start_dt).days
            
            # IBKR duration string
            if days > 365:
                duration_str = f"{days // 365} Y"
            elif days > 30:
                duration_str = f"{days // 30} M"
            else:
                duration_str = f"{days} D"
            
            # Fetch data
            df = await self.loader.get_historical_data(
                contract=contract,
                duration_str=duration_str,
                bar_size_setting=bar_size,
                what_to_show='TRADES',
                end_date_time=end_date.replace('-', '') + " 23:59:59"
            )
            
            # Standardize column names to lowercase
            df.columns = [col.lower() for col in df.columns]
            
            return df
            
        finally:
            # Always disconnect
            if self.conn and self.conn.is_connected:
                await self.conn.disconnect()
