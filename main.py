
import logging

from utility_fcn.utility_stocks import fetch_top_five
from utility_fcn.utility_telegram import (
    send_stock_list,
    send_telegram_message,
    get_ist_timestamp
)

logging.basicConfig(
    filename="stock_errors.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def create_rebalance_plan():

    try:

        logging.info("Starting daily stock fetch")

        top_n = fetch_top_five()

        logging.info("Fetched %s stocks", len(top_n))

        send_stock_list(stocks=top_n)

        logging.info("Stock notification process completed")

    except Exception as error:

        logging.exception("Stock fetching failed")

        print(f"Application error: {error}")

        send_telegram_message(
            "🚨 STOCK ALERT SYSTEM ERROR\n\n"
            f"📅 Time: {get_ist_timestamp()}\n\n"
            f"Error: {str(error)[:2000]}"
        )


if __name__ == "__main__":
    create_rebalance_plan()
