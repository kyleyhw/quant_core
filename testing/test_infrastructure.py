import unittest
import pandas as pd
import numpy as np
import sys
import os
from ib_insync import Order, Contract

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.feature_engineering import FeatureEngineer
from src.execution import ExecutionManager

class TestInfrastructure(unittest.TestCase):
    
    def setUp(self) -> None:
        self.fe = FeatureEngineer()
        self.em = ExecutionManager()

    def test_feature_engineering(self) -> None:
        print("\n--- Testing Feature Engineering ---")
        # Create dummy OHLCV data
        dates = pd.date_range(start='2023-01-01', periods=300)
        df = pd.DataFrame({
            'open': np.random.rand(300) * 100,
            'high': np.random.rand(300) * 100,
            'low': np.random.rand(300) * 100,
            'close': np.random.rand(300) * 100,
            'volume': np.random.randint(100, 1000, 300)
        }, index=dates)
        
        # Ensure high is highest and low is lowest
        df['high'] = df[['open', 'close']].max(axis=1) + 1
        df['low'] = df[['open', 'close']].min(axis=1) - 1

        df_features = self.fe.calculate_features(df)
        
        # Check if columns exist
        expected_cols = ['SMA_50', 'SMA_200', 'EMA_20', 'RSI_14', 'ATR_14']
        for col in expected_cols:
            self.assertIn(col, df_features.columns)
            print(f"Column {col} exists.")
            
        # Check RSI bounds
        self.assertTrue(df_features['RSI_14'].between(0, 100).all())
        print("RSI is within bounds [0, 100].")

    def test_execution_safety(self) -> None:
        print("\n--- Testing Execution Safety ---")
        current_price = 150.0
        symbol = 'AAPL'
        
        # 1. Valid Order
        order_valid = {'action': 'BUY', 'quantity': 10, 'order_type': 'MKT', 'symbol': symbol}
        self.assertTrue(self.em.check_order_limits(order_valid, current_price))
        print("Valid order passed.")

        # 2. Max Shares Violation
        order_shares = {'action': 'BUY', 'quantity': 101, 'order_type': 'MKT', 'symbol': symbol}
        with self.assertRaises(ValueError) as cm:
            self.em.check_order_limits(order_shares, current_price)
        print(f"Max Shares caught: {cm.exception}")

        # 3. Max Dollars Violation
        # 50 shares * $150 = $7500 > $5000 limit
        order_dollars = {'action': 'BUY', 'quantity': 50, 'order_type': 'MKT', 'symbol': symbol}
        with self.assertRaises(ValueError) as cm:
            self.em.check_order_limits(order_dollars, current_price)
        print(f"Max Dollars caught: {cm.exception}")

        # 4. Fat Finger Price Violation
        # Limit buy at $200 when price is $150 (33% deviation > 5% limit)
        order_fat_finger = {'action': 'BUY', 'quantity': 1, 'order_type': 'LMT', 'limit_price': 200.0, 'symbol': symbol}
        with self.assertRaises(ValueError) as cm:
            self.em.check_order_limits(order_fat_finger, current_price)
        print(f"Fat Finger caught: {cm.exception}")

if __name__ == '__main__':
    unittest.main()
