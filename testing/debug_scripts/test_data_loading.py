
import os
import sys
import pandas as pd
import unittest
from unittest.mock import patch, mock_open

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from unittest.mock import patch, mock_open, MagicMock

# Mock streamlit before importing utils
sys.modules['streamlit'] = MagicMock()

from dashboard import dashboard_utils

class TestDataLoading(unittest.TestCase):
    
    @patch('dashboard.dashboard_utils.get_data_files')
    @patch('builtins.open', new_callable=mock_open, read_data="Price,Close,Close\nTicker,PEP,KO\n2023-01-01,100,50\n")
    def test_get_available_assets_pair(self, mock_file: MagicMock, mock_get_files: MagicMock) -> None:
        # Mock finding a pair file
        mock_get_files.return_value = ['/path/to/PEP_KO.csv']
        
        # We need to mock pd.read_csv to return the peek dataframe
        with patch('pandas.read_csv') as mock_read_csv:
            # Mock the peek dataframe (header=[0,1], nrows=0)
            mock_df = pd.DataFrame(columns=pd.MultiIndex.from_tuples([('Close', 'PEP'), ('Close', 'KO')], names=['Price', 'Ticker']))
            mock_read_csv.return_value = mock_df
            
            assets = dashboard_utils.get_available_assets()
            
            print(f"Assets found: {assets}")
            
            self.assertIn('PEP-KO', assets)
            self.assertIn('PEP', assets)
            self.assertIn('KO', assets)
            self.assertEqual(assets['PEP-KO'], '/path/to/PEP_KO.csv')

    @patch('dashboard.dashboard_utils.get_data_files')
    @patch('builtins.open', new_callable=mock_open, read_data="Date,Close\n2023-01-01,100\n")
    def test_get_available_assets_single(self, mock_file: MagicMock, mock_get_files: MagicMock) -> None:
        # Mock finding a single asset file
        mock_get_files.return_value = ['/path/to/SPY.csv']
        
        assets = dashboard_utils.get_available_assets()
        print(f"Assets found: {assets}")
        
        self.assertIn('SPY', assets)
        self.assertEqual(assets['SPY'], '/path/to/SPY.csv')

if __name__ == '__main__':
    unittest.main()
