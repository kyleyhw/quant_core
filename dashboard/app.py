import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os
import subprocess
from typing import Type

from backtesting import Backtest, Strategy
from src.backtesting_extensions import CustomBacktest

# --- Add project root and check for data ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dashboard import dashboard_utils
from src.commission_models import COMMISSION_MODELS

# --- Signal Executor Factory ---
def create_signal_executor(base_strategy_class: Type[Strategy]) -> Type[Strategy]:
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

# --- Private Mode Toggle ---
is_private_mode_active = st.sidebar.toggle("Enable Private Mode", value=False, help="Toggle to show/hide private strategies.")

if is_private_mode_active:
    st.sidebar.success("Private Mode is ON")
else:
    st.sidebar.info("Private Mode is OFF. Private strategies are hidden.")

# --- Mode Selection (Slider Switch) ---
download_mode = st.sidebar.toggle("Download New Data (Cache Only)", key="mode_selection", help="Download data temporarily for backtesting without saving to disk.")

# 1. Strategy Selection
# We need to call discover_strategies AFTER the toggle to ensure it picks up the new state
strategies = dashboard_utils.discover_strategies(private_mode=is_private_mode_active)
all_strategies = strategies["standalone"]
strategy_names = [s["name"] for s in all_strategies]
selected_strategy_name = st.sidebar.selectbox("Select Strategy", strategy_names)
selected_strategy_config = next((s for s in all_strategies if s["name"] == selected_strategy_name), None)

# 2. Commission Model Selection
commission_names = list(COMMISSION_MODELS.keys())
selected_commission_name = st.sidebar.selectbox("Select Commission Model", commission_names)
selected_commission = COMMISSION_MODELS[selected_commission_name]

if not download_mode: # Corresponds to "Use Existing Data"
    st.sidebar.subheader("Asset Selection")
    assets_map = dashboard_utils.get_available_assets()
    all_assets = sorted(list(assets_map.keys()))
    
    selected_asset = None
    
    is_pairs_strategy = "PairsTrading" in selected_strategy_name
    
    if is_pairs_strategy:
        st.sidebar.write("Select assets for the pair (Select 2).")
        # Filter out pre-combined pairs from the list if we want to force individual selection, 
        # or keep them. The user wants "individual data files".
        # Let's show single assets.
        single_assets = [asset for asset in all_assets if '-' not in asset]
        if not single_assets:
            st.sidebar.warning("No single-asset data found.")
            st.stop()
            
        selected_assets = st.sidebar.multiselect("Select Assets", single_assets, default=single_assets[:2] if len(single_assets) >= 2 else None)
        
        if len(selected_assets) == 2:
            # Load and merge
            dfs = []
            for asset in selected_assets:
                d = dashboard_utils.load_asset_data(asset, assets_map)
                if d is not None:
                    dfs.append(d)
            
            if len(dfs) == 2:
                # Merge logic similar to run_backtest.py
                df1 = dfs[0].add_suffix('_1')
                df2 = dfs[1].add_suffix('_2')
                df = pd.merge(df1, df2, left_index=True, right_index=True, how='inner')
                
                # Map Asset 1 back to standard OHLCV for Backtesting.py execution
                df['Open'] = df['Open_1']
                df['High'] = df['High_1']
                df['Low'] = df['Low_1']
                df['Close'] = df['Close_1']
                df['Volume'] = df['Volume_1']
                
                selected_asset = f"{selected_assets[0]}-{selected_assets[1]}" # Construct a name
            else:
                st.error("Failed to load data for selected assets.")
                st.stop()
        elif len(selected_assets) > 0:
             st.warning("Please select exactly 2 assets.")
             selected_asset = None # Prevent running
        else:
             selected_asset = None

    else:
        st.sidebar.write("Select a single asset.")
        single_assets = [asset for asset in all_assets if '-' not in asset]
        if not single_assets:
            st.sidebar.warning("No single-asset data found.")
            st.stop()
        
        selected_asset = st.sidebar.selectbox("Select Asset", single_assets)
        
        # Load from local file
        if selected_asset:
            df_loaded = dashboard_utils.load_asset_data(selected_asset, assets_map)
            if df_loaded is None:
                st.error(f"Failed to load data for {selected_asset}")
                st.stop()
            df = df_loaded

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
            df_loaded = dashboard_utils.download_data_cached(tickers, start_date_download, end_date_download)
        
        if df_loaded is None:
            st.error("Data download failed. Check tickers and date range.")
            st.stop()
        df = df_loaded
        if len(tickers) == 1 and not isinstance(df.columns, pd.MultiIndex):
            df.columns = [col.capitalize() for col in df.columns]
            

# --- Date Range Filter ---
if not df.empty:
    # If in download mode, we use the download dates as the backtest range
    # So we don't need a second filter.
    if download_mode:
        start_date = start_date_download
        end_date = end_date_download
        # Ensure df is sliced to this range (it should be already, but good to be safe)
        if isinstance(df.index, pd.DatetimeIndex):
            mask = (df.index.date >= start_date) & (df.index.date <= end_date)
            df = df.loc[mask]
        st.sidebar.info(f"Backtest Range: {start_date} to {end_date}")
    else:
        st.sidebar.subheader("Date Range Filter")
        if isinstance(df.index, pd.DatetimeIndex):
            min_date = df.index.min().date()
            max_date = df.index.max().date()
            
            start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
            end_date = st.sidebar.date_input("End Date", max_date, min_value=start_date, max_value=max_date)

            if start_date <= end_date:
                mask = (df.index.date >= start_date) & (df.index.date <= end_date)
                df = df.loc[mask]

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
            if "PairsTrading" in selected_strategy_name and isinstance(df.columns, pd.MultiIndex):
                pass # Already in the right multi-index format
            elif "PairsTrading" in selected_strategy_name:
                # Check if we have merged data (from multi-select)
                if not any(col.endswith('_1') for col in df.columns):
                     st.error("Pairs trading requires 2 tickers. Please select 2 assets.")
                     st.stop()
            
            bt = CustomBacktest(
                df,
                bt_strategy_class,
                cash=10000, # Default cash
                commission=selected_commission
            )
            
            stats = bt.run()
            
            # --- 1. Key Metrics (Top) ---
            st.subheader("Backtest Results")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Return [%]", f"{stats['Return [%]']:.2f}%")
            with col2:
                st.metric("Sharpe Ratio", f"{stats['Sharpe Ratio']:.2f}")
            with col3:
                st.metric("Max Drawdown [%]", f"{stats['Max. Drawdown [%]']:.2f}%")
            with col4:
                st.metric("Win Rate [%]", f"{stats['Win Rate [%]']:.2f}%")

            # --- 2. Equity Curve (Middle) ---
            st.subheader("Equity Curve")
            
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
                bt.plot(filename=tmp.name, open_browser=False)
                with open(tmp.name, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                # Reduced height to minimize whitespace, scrolling=False to fit better
                st.components.v1.html(html_content, height=750, scrolling=False)
            
            try:
                os.remove(tmp.name)
            except:
                pass

            # --- 3. Detailed Metrics (Bottom) ---
            st.subheader("Detailed Metrics")
            # Filter out internal keys (starting with _)
            stats_to_report = stats[~stats.index.str.startswith('_')]
            # Convert to DataFrame for better display properties
            stats_df = pd.DataFrame(stats_to_report).rename(columns={0: "Value"})
            st.dataframe(stats_df, use_container_width=True, height=400)
            
            # --- 4. Trade Log (Very Bottom, Collapsed) ---
            trades = stats['_trades']
            with st.expander("View Trade Log", expanded=False):
                if not trades.empty:
                    # Format trade log for readability
                    trades_formatted = trades.copy()
                    if 'EntryTime' in trades_formatted.columns:
                        trades_formatted['EntryTime'] = trades_formatted['EntryTime'].dt.strftime('%Y-%m-%d %H:%M')
                    if 'ExitTime' in trades_formatted.columns:
                        trades_formatted['ExitTime'] = trades_formatted['ExitTime'].dt.strftime('%Y-%m-%d %H:%M')
                    st.dataframe(trades_formatted, use_container_width=True)
                else:
                    st.info("No trades executed.")

        except Exception as e:
            st.error(f"An error occurred during backtest: {e}")
            # st.exception(e) # Uncomment for full traceback
    else:
        st.warning("Please select a valid strategy and asset/data.")
else:
    st.info("Configure your backtest in the sidebar and click 'Run Backtest'.")
