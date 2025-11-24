"""
XGBoost Regime Classifier Training Script

Trains an XGBoost model to classify market regimes (Bull, Bear, Sideways).
Can use either live IBKR data or saved CSV files.

Usage:
    python train_regime_model.py --symbol SPY --start 2015-01-01 --end 2023-12-31
    python train_regime_model.py --csv data/SPY_daily.csv
"""

import argparse
import sys
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.feature_engineering import FeatureEngineer

def load_data(csv_path=None, symbol=None, start_date=None, end_date=None):
    """Load data from CSV or fetch from IBKR."""
    if csv_path:
        print(f"Loading data from {csv_path}")
        df = pd.read_data(csv_path, index_col=0, parse_dates=True)
    else:
        print(f"Fetching {symbol} data from IBKR...")
        from research.utils import SimpleDataFetcher
        fetcher = SimpleDataFetcher()
        df = fetcher.fetch_historical_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            bar_size='1 day'
        )
    
    print(f"Loaded {len(df)} rows")
    return df

def create_labels(df, lookback=20, bull_threshold=0.05, bear_threshold=-0.05):
    """Create regime labels from forward returns."""
    df['forward_return'] = df['close'].shift(-lookback) / df['close'] - 1
    
    def classify_regime(ret):
        if ret > bull_threshold:
            return 0  # Bull
        elif ret < bear_threshold:
            return 1  # Bear
        else:
            return 2  # Sideways
    
    df['regime'] = df['forward_return'].apply(classify_regime)
   df = df[:-lookback]  # Drop last N rows without forward return
    
    return df

def train_model(X_train, y_train, X_val, y_val, feature_cols):
    """Train XGBoost model."""
    # Create DMatrix
    dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=feature_cols)
    dval = xgb.DMatrix(X_val, label=y_val, feature_names=feature_cols)
    
    # Hyperparameters
    params = {
        'objective': 'multi:softmax',
        'num_class': 3,
        'max_depth': 3,
        'learning_rate': 0.05,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'lambda': 1.0,
        'eval_metric': 'mlogloss'
    }
    
    # Train
    evals = [(dtrain, 'train'), (dval, 'val')]
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=200,
        evals=evals,
        early_stopping_rounds=20,
        verbose_eval=10
    )
    
    return model

def evaluate_model(model, X_test, y_test, feature_cols):
    """Evaluate model and print metrics."""
    dtest = xgb.DMatrix(X_test, label=y_test, feature_names=feature_cols)
    y_pred = model.predict(dtest)
    
    print("\n=== Test Set Performance ===")
    print(classification_report(y_test, y_pred, target_names=['Bull', 'Bear', 'Sideways']))
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Bull', 'Bear', 'Sideways'],
                yticklabels=['Bull', 'Bear', 'Sideways'])
    plt.ylabel('True')
    plt.xlabel('Predicted')
    plt.title('Confusion Matrix - Test Set')
    plt.tight_layout()
    plt.savefig('../reports/regime_confusion_matrix.png')
    print("Saved confusion matrix to reports/regime_confusion_matrix.png")
    
    # Feature importance
    xgb.plot_importance(model, max_num_features=15)
    plt.title('Top 15 Feature Importances')
    plt.tight_layout()
    plt.savefig('../reports/regime_feature_importance.png')
    print("Saved feature importance to reports/regime_feature_importance.png")

def main():
    parser = argparse.ArgumentParser(description='Train XGBoost regime classifier')
    parser.add_argument('--csv', type=str, help='Path to CSV file with OHLCV data')
    parser.add_argument('--symbol', type=str, default='SPY', help='Symbol to fetch from IBKR')
    parser.add_argument('--start', type=str, default='2015-01-01', help='Start date')
    parser.add_argument('--end', type=str, default='2023-12-31', help='End date')
    parser.add_argument('--output', type=str, default='../models/xgb_regime_classifier.json',
                        help='Output model path')
    
    args = parser.parse_args()
    
    # Load data
    df = load_data(args.csv, args.symbol, args.start, args.end)
    
    # Generate features
    print("\nCalculating features...")
    fe = FeatureEngineer()
    df = fe.calculate_features(df)
    df = df.dropna()
    print(f"Features calculated: {df.shape[1]} columns")
    
    # Create labels
    print("\nCreating regime labels...")
    df = create_labels(df)
    print(f"Regime distribution:\n{df['regime'].value_counts()}")
    
    # Prepare features
    feature_cols = [col for col in df.columns if col not in 
                    ['open', 'high', 'low', 'close', 'volume', 'forward_return', 'regime']]
    X = df[feature_cols].values
    y = df['regime'].values
    
    # Time-series split
    train_size = int(len(X) * 0.6)
    val_size = int(len(X) * 0.2)
    
    X_train, y_train = X[:train_size], y[:train_size]
    X_val, y_val = X[train_size:train_size+val_size], y[train_size:train_size+val_size]
    X_test, y_test = X[train_size+val_size:], y[train_size+val_size:]
    
    print(f"\nTrain: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")
    
    # Train model
    print("\nTraining XGBoost model...")
    model = train_model(X_train, y_train, X_val, y_val, feature_cols)
    print(f"Best iteration: {model.best_iteration}")
    print(f"Best validation loss: {model.best_score:.4f}")
    
    # Evaluate
    evaluate_model(model, X_test, y_test, feature_cols)
    
    # Save model
    model.save_model(args.output)
    print(f"\nModel saved to {args.output}")

if __name__ == '__main__':
    main()
