import sys
import os
from pathlib import Path
import pandas as pd
import joblib
import xgboost as xgb
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.feature_engineering import FeatureEngineer

def check_regime_counts(ticker, data_path):
    print(f"\n--- Checking Regime Counts for {ticker} ---")
    
    # Load Data
    try:
        df = pd.read_csv(data_path)
        # Standardize to lowercase for consistency with FeatureEngineer
        df.columns = [col.lower() for col in df.columns]
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], utc=True)
            df.set_index('date', inplace=True)
            df.index = df.index.tz_localize(None)
            
        print(f"Columns: {df.columns.tolist()}")
        
        # Feature Engineering
        fe = FeatureEngineer()
        # FeatureEngineer expects lowercase columns usually
        df_features = fe.calculate_features(df)
        
        # --- Check XGBoost (MLRegimeStrategy) ---
        model_path_xgb = project_root / "models" / "xgb_regime_classifier.json"
        if model_path_xgb.exists():
            model_xgb = xgb.Booster()
            model_xgb.load_model(model_path_xgb)
            
            feature_cols = model_xgb.feature_names
            valid_data = df_features[feature_cols].dropna()
            
            if not valid_data.empty:
                dmatrix = xgb.DMatrix(valid_data.values, feature_names=feature_cols)
                preds = model_xgb.predict(dmatrix)
                counts = pd.Series(preds).value_counts().sort_index()
                print(f"XGBoost Regime Counts (0=Bull, 1=Bear, 2=Sideways):")
                print(counts)
            else:
                print("Not enough data for XGBoost features.")
        else:
            print("XGBoost model not found.")

        # --- Check HMM (HmmRegimeStrategy) ---
        model_path_hmm = project_root / "models" / "hmm_regime_model.pkl"
        if model_path_hmm.exists():
            model_hmm = joblib.load(model_path_hmm)
            
            # HMM Features: Log Return, Volatility
            close_series = df['close']
            log_return = np.log(close_series / close_series.shift(1))
            volatility = np.log(close_series / close_series.shift(1)).rolling(window=20).std()
            
            hmm_features = pd.concat([log_return, volatility], axis=1).dropna()
            hmm_features.columns = ['log_ret', 'vol']
            
            if not hmm_features.empty:
                preds = model_hmm.predict(hmm_features.values)
                counts = pd.Series(preds).value_counts().sort_index()
                print(f"HMM Regime Counts (0, 1, 2):")
                print(counts)
            else:
                print("Not enough data for HMM features.")
        else:
            print("HMM model not found.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Check TSLA
    tsla_path = project_root / "data" / "stocks_2024_2025" / "TSLA_2024-10-01_2025-11-25.csv"
    if tsla_path.exists():
        check_regime_counts("TSLA", tsla_path)
    else:
        print(f"Data file not found: {tsla_path}")
