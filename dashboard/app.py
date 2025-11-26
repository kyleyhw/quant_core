import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os
import subprocess
from backtesting import Backtest, Strategy

# --- Add project root and check for data ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dashboard import utils
from src.commission_models import ibkr_tiered_commission

# --- Signal Executor Factory ---
def create_signal_executor(base_strategy_class):
    """
    Creates a dynamic subclass of the given strategy class that interprets
    'buy'/'sell' return values from .next() as trade execution commands.
    """
    class SignalExecutor(base_strategy_class):
        def next(self):
            # Call the underlying strategy's next method
            signal = super().next()
            
            if signal == 'buy':
                if self.position.is_short:
                    self.position.close()
                if not self.position.is_long:
                    self.buy()
            elif signal == 'sell':
                if self.position.is_long:
                    self.position.close()
                if not self.position.is_short:
                    self.sell()
    
    # Copy name and docstring for clarity
    SignalExecutor.__name__ = f"Executable{base_strategy_class.__name__}"
    SignalExecutor.__doc__ = base_strategy_class.__doc__
    return SignalExecutor

# --- Auto-Download Data on First Run ---
BENCHMARK_DATA_DIR = os.path.join(project_root, "data", "benchmark")
if not os.path.exists(BENCHMARK_DATA_DIR) or not os.listdir(BENCHMARK_DATA_DIR):
    st.info("Benchmark data not found. Downloading initial dataset...")
    
    download_script_path = os.path.join(project_root, "data", "download_yfinance_data.py")
    
    with st.spinner("Fetching data from yfinance... This may take a moment."):
        # Command to run the download script
        command = [
            sys.executable,
            download_script_path,
            "--tickers", "SPY", "AAPL", "MSFT", "NVDA", "PEP", "KO",
            "--start", "2024-01-01",
            "--end", "2025-01-01",
            "--output", BENCHMARK_DATA_DIR # Specify the directory
        ]
        
        try:
            # We use DEVNULL to hide the verbose output of the script from the user
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            st.success("Benchmark data downloaded successfully!")
            # Rerun the app to load the new data
            st.rerun()
        except subprocess.CalledProcessError as e:
            st.error(f"Failed to download data. Please run the download script manually. Error: {e}")
            st.code(f"python {download_script_path} --tickers SPY --start 2024-01-01 --end 2025-01-01 --output {BENCHMARK_DATA_DIR}")
            st.stop()
        except FileNotFoundError:
            st.error(f"Download script not found at {download_script_path}")
            st.stop()

st.set_page_config(page_title="Quant Core Dashboard", layout="wide")

st.title("Algorithmic Trading Dashboard")

st.sidebar.header("Configuration")

# --- Private Mode Status Indicator ---
# Debug: Print environment variables to console
print(f"DEBUG: QUANT_CORE_PRIVATE_MODE = {os.environ.get('QUANT_CORE_PRIVATE_MODE')}")

is_private_mode_active = os.environ.get('QUANT_CORE_PRIVATE_MODE', 'false').lower() == 'true'

if is_private_mode_active:
    st.sidebar.success("Private Mode is ON")
else:
    st.sidebar.info(
        "**Public Mode is ON.** To enable Private Mode and see your private strategies, "
        "stop this server and relaunch it with the `QUANT_CORE_PRIVATE_MODE` "
        "environment variable set to `true`."
    )
    st.sidebar.code("set QUANT_CORE_PRIVATE_MODE=true\nstreamlit run dashboard/app.py", language="shell")


# --- Mode Selection (Slider Switch) ---
download_mode = st.sidebar.toggle("Download New Data", key="mode_selection")

# 1. Strategy Selection
strategies = utils.discover_strategies(private_mode=is_private_mode_active)
all_strategies = strategies["standalone"]
strategy_names = [s["name"] for s in all_strategies]
selected_strategy_name = st.sidebar.selectbox("Select Strategy", strategy_names)
selected_strategy_config = next((s for s in all_strategies if s["name"] == selected_strategy_name), None)

# 2. Asset & Data Selection (Conditional UI)
df = pd.DataFrame()

if not download_mode: # Corresponds to "Use Existing Data"
    st.sidebar.subheader("Asset Selection")
    assets_map = utils.get_available_assets()
    all_assets = sorted(list(assets_map.keys()))
    
    selected_asset = None
    
    is_pairs_strategy = "PairsTrading" in selected_strategy_name
    
    if is_pairs_strategy:
        st.sidebar.write("Select a pre-defined asset pair.")
        pair_assets = [asset for asset in all_assets if '-' in asset]
        if not pair_assets:
            st.sidebar.warning("No pairs data found.")
            st.stop()
        selected_asset = st.sidebar.selectbox("Select Asset Pair", pair_assets)
    else:
        st.sidebar.write("Select a single asset.")
        single_assets = [asset for asset in all_assets if '-' not in asset]
        if not single_assets:
            st.sidebar.warning("No single-asset data found.")
            st.stop()
        
        search_term = st.sidebar.text_input("Search Asset", "")
        if search_term:
            filtered_assets = [asset for asset in single_assets if search_term.upper() in asset.upper()]
        else:
            filtered_assets = single_assets
            
        if not filtered_assets:
            st.sidebar.warning("No assets found matching your search.")
            st.stop()
            
        selected_asset = st.sidebar.selectbox("Select Asset", filtered_assets)
        
    # Load from local file
    if selected_asset:
        df = utils.load_asset_data(selected_asset, assets_map)
        if df is None:
            st.error(f"Failed to load data for {selected_asset}")
            st.stop()

else: # Corresponds to "Download New Data"
    st.sidebar.subheader("Download New Data")
    
    tickers_input = st.sidebar.text_input("Enter Tickers (comma-separated)", key="tickers_input", value="SPY")
    
    import datetime
    today = datetime.date.today()
    one_year_ago = today - datetime.timedelta(days=365)
    
    start_date_download = st.sidebar.date_input("Start Date", one_year_ago, key="start_date_download")
    end_date_download = st.sidebar.date_input("End Date", today, key="end_date_download")
    
    if tickers_input and start_date_download < end_date_download:
        tickers = [ticker.strip().upper() for ticker in tickers_input.split(',')]
        
        with st.spinner(f"Downloading data for {', '.join(tickers)}..."):
            df = utils.download_data_cached(tickers, start_date_download, end_date_download)
        
        if df is None:
            st.error("Data download failed. Check tickers and date range.")
            st.stop()
        elif len(tickers) == 1 and not isinstance(df.columns, pd.MultiIndex):
            df.columns = [col.capitalize() for col in df.columns]
            

# --- Date Range Filter (now applies to both modes) ---
if not df.empty:
    st.sidebar.subheader("Date Range Filter")
    min_date = df.index.min().date()
    max_date = df.index.max().date()
    
    start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("End Date", max_date, min_value=start_date, max_value=max_date)

    if start_date <= end_date:
        mask = (df.index.date >= start_date) & (df.index.date <= end_date)
        df = df.loc[mask]
    else:
        st.sidebar.error("Error: Start date must be before end date.")
        st.stop()
# 5. Run Backtest Button
if st.sidebar.button("Run Backtest"):
    asset_name_display = selected_asset if not download_mode else tickers_input
    
    if selected_strategy_config and not df.empty and asset_name_display:
        st.write(f"Running **{selected_strategy_name}** on **{asset_name_display}**...")
        
        strategy_class = selected_strategy_config["class"]
        
        try:
            # --- Wrapper for Signal-based Strategies ---
            if selected_strategy_name in ["SimpleMACrossover", "RSI2PeriodStrategy"]:
                bt_strategy_class = create_signal_executor(strategy_class)
            else:
                bt_strategy_class = strategy_class

            # For pairs trading with downloaded data, we need to ensure the strategy can handle it
            if "PairsTrading" in selected_strategy_name and len(df.columns.levels) > 1:
                pass # Already in the right multi-index format
            elif "PairsTrading" in selected_strategy_name:
                st.error("Pairs trading requires 2 tickers. Please download data for 2 tickers.")
                st.stop()
            
            bt = Backtest(df, bt_strategy_class, cash=10000, commission=ibkr_tiered_commission)
            stats = bt.run()
            
            # --- Results Display ---
            st.header("Backtest Results")
            
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
            st.text(str(stats))
            
        except Exception as e:
            st.error(f"An error occurred during backtest: {e}")
    else:
        st.warning("Please select a valid strategy and asset/data.")
else:
    st.info("Configure your backtest in the sidebar and click 'Run Backtest'.")
