import logging
from typing import Optional, Any

import pandas as pd
from ib_insync import Contract, BarData

from src.interfaces import IDataLoader
from src.market_adapters.ibkr.connection import IBConnection

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class IBKRDataLoader(IDataLoader):
    """
    Implements the IDataLoader interface for Interactive Brokers.
    It handles fetching and formatting historical data using an established
    IBConnection.
    """

    def __init__(self, ib_connection: IBConnection) -> None:
        """
        Initializes the DataLoader with an IBConnection instance.

        Args:
            ib_connection (IBConnection): An active IBConnection instance.
        """
        if not isinstance(ib_connection, IBConnection):
            raise TypeError("ib_connection must be an instance of IBConnection")
        self.ib_connection = ib_connection
        self.ib = ib_connection.ib
        logging.info("IBKRDataLoader initialized.")

    def create_contract(self, symbol: str, sec_type: str, exchange: str, currency: str) -> Optional[Contract]:
        """
        Creates and qualifies an IB Contract object.
        """
        contract = Contract(symbol=symbol, secType=sec_type, exchange=exchange, currency=currency)
        logging.info(f"Attempting to qualify contract: {contract}")
        try:
            qualified_contracts = self.ib.qualifyContracts(contract)
            if not qualified_contracts:
                logging.warning(f"No contract details found for {symbol}")
                return None
            qualified_contract = qualified_contracts[0]
            logging.info(f"Qualified contract: {qualified_contract.localSymbol}")
            return qualified_contract
        except Exception as e:
            logging.error(f"Error qualifying contract for {symbol}: {e}")
            return None

    def get_historical_data(self,
                              symbol: str,
                              timeframe: str,
                              start: str,
                              end: str,
                              sec_type: str = 'STK',
                              exchange: str = 'ARCA',
                              currency: str = 'USD',
                              **kwargs: Any
                              ) -> pd.DataFrame:
        """
        Fetches historical market data for a given symbol.
        This method implements the IDataLoader interface.
        """
        if not self.ib_connection.is_connected():
            logging.error("IB not connected. Cannot fetch historical data.")
            return pd.DataFrame()

        contract = self.create_contract(symbol, sec_type, exchange, currency)
        if not contract:
            return pd.DataFrame()

        # Note: This is a simplified mapping. A robust implementation would
        # need a more sophisticated way to handle duration and bar size based
        # on the 'start' and 'end' dates and the 'timeframe'.
        # For now, we use placeholder values for demonstration.
        duration_str = '1 Y'  # Placeholder
        bar_size_setting = timeframe  # e.g., '1 day', '1 hour'

        try:
            bars: list[BarData] = self.ib.reqHistoricalData(
                contract,
                endDateTime=end,
                durationStr=duration_str,
                barSizeSetting=bar_size_setting,
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1
            )

            if not bars:
                logging.warning(f"No historical data returned for {symbol}")
                return pd.DataFrame()

            df = pd.DataFrame([b.__dict__ for b in bars])
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            df = df[['open', 'high', 'low', 'close', 'volume']]
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            logging.info(f"Successfully fetched {len(df)} bars for {symbol}.")
            return df

        except Exception as e:
            logging.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()


def main() -> None:
    """
    Main function to demonstrate DataLoader usage.
    """
    conn = IBConnection()
    try:
        conn.connect()
        if conn.is_connected():
            data_loader = IBKRDataLoader(conn)

            logging.info("Attempting to fetch data for SPY...")
            df_spy = data_loader.get_historical_data(
                symbol='SPY',
                timeframe='1 day',
                start='',  # Not used in this simplified example
                end=''     # IB defaults to now if end is empty
            )

            if not df_spy.empty:
                print("\nFetched SPY 1-day data:")
                print(df_spy.head())
            else:
                print("\nFailed to fetch SPY data.")

    except Exception as e:
        logging.error(f"An error occurred in the main execution block: {e}")
    finally:
        if conn.is_connected():
            conn.disconnect()
            logging.info("IB connection closed.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Program terminated by user.")
    except Exception as e:
        logging.critical(f"A critical error occurred: {e}")