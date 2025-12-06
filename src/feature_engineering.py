import pandas as pd

from typing import List, Optional

class FeatureEngineer:
    """
    Centralized logic for calculating technical indicators.
    Ensures consistency between Backtesting (Training) and Live Trading (Inference).
    """

    def __init__(self) -> None:
        pass

    def calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies all defined technical indicators to the dataframe.
        
        Args:
            df: OHLCV DataFrame.
            
        Returns:
            DataFrame with added feature columns.
        """
        # Ensure we have a copy to avoid SettingWithCopy warnings on the original df
        df = df.copy()
        
        # Helper for RSI
        def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
            delta = series.diff().astype(float)
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))

        # Helper for Stochastic
        def calculate_stoch(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> tuple[pd.Series, pd.Series]:
            low_min = low.rolling(window=k_period).min()
            high_max = high.rolling(window=k_period).max()
            k = 100 * ((close - low_min) / (high_max - low_min))
            d = k.rolling(window=d_period).mean()
            return k, d

        # Helper for ATR
        def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
            tr1 = high - low
            tr2 = (high - close.shift()).abs()
            tr3 = (low - close.shift()).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            return tr.rolling(window=period).mean()

        # --- Trend Indicators ---
        # Simple Moving Averages
        df['SMA_50'] = df['close'].rolling(window=50).mean()
        df['SMA_200'] = df['close'].rolling(window=200).mean()
        
        # Exponential Moving Averages
        df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
        
        # MACD (12, 26, 9)
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD_12_26_9'] = ema12 - ema26
        df['MACDS_12_26_9'] = df['MACD_12_26_9'].ewm(span=9, adjust=False).mean()
        df['MACDH_12_26_9'] = df['MACD_12_26_9'] - df['MACDS_12_26_9']

        # --- Momentum Indicators ---
        # RSI (14)
        df['RSI_14'] = calculate_rsi(df['close'], period=14)
        
        # Stochastic Oscillator
        slowk, slowd = calculate_stoch(df['high'], df['low'], df['close'], k_period=14, d_period=3)
        df['STOCHk_14_3_3'] = slowk
        df['STOCHd_14_3_3'] = slowd

        # --- Volatility Indicators ---
        # Bollinger Bands (20, 2)
        middle = df['close'].rolling(window=20).mean()
        std = df['close'].rolling(window=20).std()
        df['BBM_20_2.0'] = middle
        df['BBU_20_2.0'] = middle + (std * 2)
        df['BBL_20_2.0'] = middle - (std * 2)
            
        # ATR (14)
        df['ATR_14'] = calculate_atr(df['high'], df['low'], df['close'], period=14)

        # --- Volume Indicators ---
        # VWAP - Note: VWAP requires a datetime index to reset correctly, 
        # but talib does not have a direct VWAP implementation.
        # For simplicity in standard OHLCV without intraday resets, we might skip or use a rolling VWAP approximation
        # df['VWAP'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])

        # Reorder columns to match the expected feature order of the trained XGBoost models
        expected_order = [
            'close', 'high', 'low', 'open', 'volume', 
            'SMA_50', 'SMA_200', 'EMA_20', 
            'MACD_12_26_9', 'MACDS_12_26_9', 'MACDH_12_26_9', 
            'RSI_14', 'STOCHk_14_3_3', 'STOCHd_14_3_3', 
            'BBL_20_2.0', 'BBM_20_2.0', 'BBU_20_2.0', 
            'ATR_14'
        ]
        
        return df[expected_order]

    def get_required_lookback(self) -> int:
        """
        Returns the minimum number of rows required to calculate all indicators.
        Useful for live trading to fetch just enough data.
        """
        return 200  # Based on SMA_200
