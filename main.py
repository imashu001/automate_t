"""Application entry point for the Screener stock alert."""

import logging

from dotenv import load_dotenv

from utility_fcn.utility_stocks import fetch_screen_stocks
from utility_fcn.utility_telegram import (
    get_ist_timestamp,
    send_stock_list,
    send_telegram_message,
)

LOGGER = logging.getLogger(__name__)
LOG_FILE = "stock_errors.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"


def configure_logging() -> None:
    """Configure application-wide file logging."""
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format=LOG_FORMAT,
        encoding="utf-8",
    )


def run_stock_alert() -> None:
    """Fetch the current Screener results and deliver them to Telegram."""
    LOGGER.info("Starting stock alert")

    try:
        stocks = fetch_screen_stocks()
        LOGGER.info("Fetched %s stocks from Screener", len(stocks))

        if not send_stock_list(stocks):
            LOGGER.error("Stock notification was not delivered successfully")
            return

        LOGGER.info("Stock notification process completed")
    except Exception as error:
        LOGGER.exception("Stock alert failed")
        error_message = (
            "🚨 STOCK ALERT SYSTEM ERROR\n\n"
            f"📅 Time: {get_ist_timestamp()}\n\n"
            f"Error: {str(error)[:2000]}"
        )
        if not send_telegram_message(error_message):
            LOGGER.error("Could not deliver the stock alert failure notification")


def create_rebalance_plan() -> None:
    """Backward-compatible entry point retained for existing callers."""
    run_stock_alert()


def main() -> None:
    """Load local configuration, set up logging, and run the alert."""
    load_dotenv()
    configure_logging()
    run_stock_alert()


if __name__ == "__main__":
    main()
