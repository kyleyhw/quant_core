import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os
from backtesting import Backtest

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dashboard import utils
from src.commission_models import ibkr_tiered_commission

st.set_page_config(page_title="IBKR Quant Core Dashboard", layout="wide")

st.title("Algo Trading Dashboard")

# --- Sidebar: Configuration ---
st.sidebar.header("Configuration")

# 1. Strategy Selection
strategies = utils.discover_strategies()
all_strategies = strategies["standalone"] # + list(strategies["meta"].values()) # TODO: Add meta support

strategy_names = [s["name"] for s in all_strategies]
selected_strategy_name = st.sidebar.selectbox("Select Strategy", strategy_names)

selected_strategy_config = next((s for s in all_strategies if s["name"] == selected_strategy_name), None)

# 2. Data Selection
data_files = utils.load_available_data()
selected_file = st.sidebar.selectbox("Select Data File", data_files)

# Load Data
if selected_file:
    data, is_multi_asset = utils.load_data_file(selected_file)
    
    if is_multi_asset:
        # Extract tickers from MultiIndex columns
        tickers = data.columns.get_level_values(1).unique().tolist()
        selected_ticker = st.sidebar.selectbox("Select Ticker", tickers)
        
        # Extract specific ticker data
        df = pd.DataFrame()
        try:
            df['Open'] = data[('Open', selected_ticker)]
            df['High'] = data[('High', selected_ticker)]
            df['Low'] = data[('Low', selected_ticker)]
            df['Close'] = data[('Close', selected_ticker)]
            df['Volume'] = data[('Volume', selected_ticker)]
            df.dropna(inplace=True)
        except KeyError:
            st.error(f"Data missing for {selected_ticker}")
            st.stop()
    else:
        df = data

    # Date Range Filter
    if not df.empty:
        min_date = df.index.min().date()
        max_date = df.index.max().date()
        
        start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
        end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)
        
        if start_date <= end_date:
            mask = (df.index.date >= start_date) & (df.index.date <= end_date)
            df = df.loc[mask]
        else:
            st.error("Start date must be before end date.")

# 3. Run Backtest
if st.sidebar.button("Run Backtest"):
    if selected_strategy_config and not df.empty:
        st.write(f"Running **{selected_strategy_name}** on **{selected_file}**...")
        
        strategy_class = selected_strategy_config["class"]
        
        try:
            bt = Backtest(df, strategy_class, cash=10000, commission=ibkr_tiered_commission)
            stats = bt.run()
            
            # --- Results Display ---
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Return [%]", f"{stats['Return [%]']:.2f}%")
            col2.metric("Sharpe Ratio", f"{stats['Sharpe Ratio']:.2f}")
            col3.metric("Max Drawdown [%]", f"{stats['Max. Drawdown [%]']:.2f}%")
            col4.metric("Win Rate [%]", f"{stats['Win Rate [%]']:.2f}%")
            
            st.subheader("Equity Curve")
            equity_curve = stats['_equity_curve']
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=equity_curve.index, y=equity_curve['Equity'], mode='lines', name='Equity'))
            fig.update_layout(title='Portfolio Equity', xaxis_title='Date', yaxis_title='Equity ($)')
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Trade Log")
            trades = stats['_trades']
            st.dataframe(trades)
            
            st.subheader("Full Stats")
            st.text(stats)
            
        except Exception as e:
            st.error(f"An error occurred during backtest: {e}")
    else:
        st.warning("Please select a valid strategy and data file.")
