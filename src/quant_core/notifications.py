import logging
import os
from enum import Enum

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class Severity(Enum):
    """Notification severity levels."""

    INFO = ("INFO", "#3498db")  # Blue
    WARNING = ("WARNING", "#f1c40f")  # Yellow
    ERROR = ("ERROR", "#e74c3c")  # Red
    CRITICAL = ("CRITICAL", "#992d22")  # Dark Red


class Notifier:
    """
    Handles sending notifications to a Discord webhook.
    """

    def __init__(self, webhook_url: str | None = None):
        """
        Initializes the Notifier.

        Args:
            webhook_url (Optional[str]): The Discord webhook URL.
                If not provided, it's read from the DISCORD_WEBHOOK_URL
                environment variable.
        """
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        if not self.webhook_url:
            logging.warning(
                "DISCORD_WEBHOOK_URL environment variable not set. Notifier will be disabled."
            )
        else:
            logging.info("Notifier initialized with a Discord webhook URL.")

    def send(
        self, message: str, severity: Severity = Severity.INFO, title: str = "Trading Bot Alert"
    ) -> bool:
        """
        Sends a formatted message to the configured Discord webhook.

        Args:
            message (str): The main content of the message.
            severity (Severity): The severity level of the message.
            title (str): The title of the embed.

        Returns:
            bool: True if the message was sent successfully, False otherwise.
        """
        if not self.webhook_url:
            logging.warning(f"Notifier is disabled. Message not sent: {message}")
            return False

        level_name, color = severity.value
        hex_color = int(color.replace("#", ""), 16)

        # Structure the payload for Discord's embed format
        payload = {
            "embeds": [
                {
                    "title": title,
                    "description": message,
                    "color": hex_color,
                    "fields": [{"name": "Severity", "value": level_name, "inline": True}],
                }
            ]
        }

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            logging.info(f"Successfully sent {severity.name} notification.")
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send notification: {e}")
            return False


if __name__ == "__main__":
    # This is an example of how to use the Notifier.
    # To test this, you MUST have a .env file in the project root with your Discord webhook URL:
    # DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/your/url"

    print("Running Notifier demonstration...")

    # Initialize notifier (it will automatically load from .env)
    notifier = Notifier()

    if not notifier.webhook_url:
        print("\nSKIPPING NOTIFIER DEMO: DISCORD_WEBHOOK_URL is not set in your .env file.")
        print("Please set it to test notifications.")
    else:
        print("\nSending test notifications...")

        # Send an info message
        success_info = notifier.send(
            "This is a test 'INFO' message from the trading bot.",
            severity=Severity.INFO,
            title="System Status Update",
        )
        print(f"INFO message sent: {success_info}")

        # Send a warning message
        success_warning = notifier.send(
            "This is a test 'WARNING' message. Something might need attention.",
            severity=Severity.WARNING,
            title="Potential Issue Detected",
        )
        print(f"WARNING message sent: {success_warning}")

        # Send an error message
        success_error = notifier.send(
            "This is a test 'ERROR' message. An operation failed.",
            severity=Severity.ERROR,
            title="Operation Failed",
        )
        print(f"ERROR message sent: {success_error}")

        # Send a critical message
        success_critical = notifier.send(
            "This is a test 'CRITICAL' message. A major component has failed "
            "and requires immediate action.",
            severity=Severity.CRITICAL,
            title="!!! CRITICAL FAILURE !!!",
        )
        print(f"CRITICAL message sent: {success_critical}")

        print("\nNotifier demonstration complete.")
