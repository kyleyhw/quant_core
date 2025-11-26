import asyncio
import os
import logging
from typing import Optional, List

from ib_insync import IB
from ib_insync import IB
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

from src.interfaces import IConnection

class IBConnection(IConnection):
    """
    Manages the connection to Interactive Brokers TWS or Gateway.
    This class implements the IConnection interface for the IBKR market.
    """

    def __init__(self,
                 host: Optional[str] = None,
                 port: Optional[int] = None,
                 client_id: Optional[int] = None):
        """
        Initializes the IBConnection.
        """
        self.ib = IB()
        self.host = host or os.getenv('IB_HOST', '127.0.0.1')
        self.port = port or int(os.getenv('IB_PORT', 7497))
        self.client_id = client_id or int(os.getenv('IB_CLIENT_ID', 1))
        logging.info(f"Initialized IBConnection with host={self.host}, port={self.port}, client_id={self.client_id}")

    def connect(self) -> None:
        """
        Establishes a connection to the IB TWS/Gateway.
        `ib_insync` manages the connection and event loop in a background thread.
        """
        try:
            if not self.ib.isConnected():
                self.ib.connect(self.host, self.port, self.client_id)
                logging.info("Successfully connected to IB TWS/Gateway.")
            else:
                logging.info("Already connected to IB TWS/Gateway.")
        except Exception as e:
            logging.error(f"Failed to connect to IB TWS/Gateway: {e}")
            raise  # Re-raise the exception to be handled by the caller

    def disconnect(self) -> None:
        """
        Disconnects from the IB TWS/Gateway.
        """
        if self.ib.isConnected():
            self.ib.disconnect()
            logging.info("Disconnected from IB TWS/Gateway.")
        else:
            logging.info("Not connected to IB TWS/Gateway.")

    def is_connected(self) -> bool:
        """
        Checks if the connection to IB TWS/Gateway is active.
        """
        return self.ib.isConnected()

    def get_account_summary(self) -> List[AccountValue]:
        """
        Retrieves the account summary from IB.
        Note: This is an example of a method specific to this concrete
        implementation and not part of the generic IConnection interface.
        """
        if not self.is_connected():
            logging.error("Not connected to IB. Cannot fetch account summary.")
            return []
        return self.ib.accountSummary()


def main():
    """
    Main function to demonstrate IBConnection usage.
    """
    conn = IBConnection()
    try:
        conn.connect()
        if conn.is_connected():
            print("Connection successful! Getting account summary...")
            summary = conn.get_account_summary()
            if not summary:
                print("Could not retrieve account summary.")
            else:
                for item in summary:
                    if item.tag == 'NetLiquidation':
                        print(f"Net Liquidation: {item.value} {item.currency}")
                        break
    except Exception as e:
        logging.error(f"An error occurred during the connection test: {e}")
    finally:
        conn.disconnect()


if __name__ == "__main__":
    # Example usage:
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Program terminated by user.")
    except Exception as e:
        logging.critical(f"A critical error occurred in connection test: {e}")


