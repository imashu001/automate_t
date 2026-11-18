
import os
import time
import logging
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Configure local error logging
logging.basicConfig(
    filename="telegram_errors.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_ist_timestamp():

    ist = ZoneInfo("Asia/Kolkata")

    return datetime.now(ist).strftime(
        "%d-%b-%Y %I:%M:%S %p IST"
    )


def send_telegram_message(message, retries=3):

    if not BOT_TOKEN or not CHAT_ID:
        raise ValueError("Telegram credentials are missing!")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    for attempt in range(1, retries + 1):

        try:
            response = requests.post(
                url,
                json={
                    "chat_id": CHAT_ID,
                    "text": message
                },
                timeout=20
            )

            response.raise_for_status()

            result = response.json()

            if not result.get("ok"):
                raise RuntimeError(result.get("description"))

            print("Telegram message sent successfully!")
            return True

        except (requests.RequestException, RuntimeError) as error:

            logging.exception(
                "Telegram attempt %s failed", attempt
            )

            print(f"Telegram attempt {attempt} failed: {error}")

            if attempt < retries:
                time.sleep(10)

    return False


def send_stock_list(stocks):

    try:

        if stocks is None or stocks.empty:
            send_telegram_message(
                "⚠️ STOCK ALERT\n\nNo stocks found in Screener."
                f"📅 Time: {get_ist_timestamp()}\n\n"
            )
            return False

        ist = ZoneInfo("Asia/Kolkata")

        current_time = datetime.now(ist)

        formatted_time = current_time.strftime("%d-%b-%Y | %I:%M:%S %p")

        message = (
            "📈 SCREENER MOMENTUM STOCKS\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"📅 Date: {current_time.strftime('%d-%b-%Y')}\n"
            f"🕒 Time: {current_time.strftime('%I:%M:%S %p')} IST\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
        )

        for index, row in stocks.iterrows():

            message += (
                f"🔹 {index + 1}. {row['Company']}\n"
                f"💰 CMP: ₹{row['CMP  Rs.']}\n"
                f"📊 P/E: {row['P/E']}\n"
                f"🏢 Market Cap: {row['Mar Cap  Rs.Cr.']} Cr\n"
                f"📈 ROCE: {row['ROCE  %']}%\n"
                f"💹 Profit Growth: {row['Qtr Profit Var  %']}%\n"
                f"📊 Sales Growth: {row['Qtr Sales Var  %']}%\n"
                f"🔝 52W High: ₹{row['52w High  Rs.']}\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
            )

        # Split into Telegram-safe message sizes
        chunks = []
        current_message = ""

        for line in message.splitlines(keepends=True):

            if len(current_message) + len(line) > 3500:
                chunks.append(current_message)
                current_message = ""

            current_message += line

        if current_message:
            chunks.append(current_message)

        # Send all chunks
        for chunk in chunks:

            success = send_telegram_message(chunk)

            if not success:
                raise RuntimeError(
                    "Failed to deliver stock notification"
                )

        return True

    except Exception as error:

        logging.exception("Stock notification failed")

        print(f"Stock notification error: {error}")

        # Try to notify about the failure
        send_telegram_message(
            "🚨 STOCK ALERT SYSTEM ERROR\n\n"
            f"📅 Time: {get_ist_timestamp()}\n\n"
            f"Error: {str(error)[:2000]}"
        )

        return False
