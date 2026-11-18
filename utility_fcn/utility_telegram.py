"""Telegram delivery and message-formatting helpers for stock alerts."""

import logging
import os
import time
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import pandas as pd
import requests

LOGGER = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"
TELEGRAM_TIMEOUT_SECONDS = 20
TELEGRAM_MAX_MESSAGE_LENGTH = 3500
TELEGRAM_RETRY_DELAY_SECONDS = 10
IST = ZoneInfo("Asia/Kolkata")

STOCK_COLUMNS = (
    "Company",
    "CMP  Rs.",
    "P/E",
    "Mar Cap  Rs.Cr.",
    "ROCE  %",
    "Qtr Profit Var  %",
    "Qtr Sales Var  %",
    "52w High  Rs.",
)


def _now_in_ist(now: Optional[datetime] = None) -> datetime:
    """Return the supplied time or current time in Indian Standard Time."""
    current_time = now or datetime.now(IST)
    if current_time.tzinfo is None:
        return current_time.replace(tzinfo=IST)
    return current_time.astimezone(IST)


def get_ist_timestamp(now: Optional[datetime] = None) -> str:
    """Format a timestamp in Indian Standard Time."""
    return _now_in_ist(now).strftime("%d-%b-%Y %I:%M:%S %p IST")


def _display_value(value: object) -> str:
    """Convert a table cell to readable text, including missing values."""
    if pd.isna(value):
        return "N/A"
    return str(value)


def format_stock_notification(
    stocks: Optional[pd.DataFrame],
    now: Optional[datetime] = None,
) -> str:
    """Create the human-readable Telegram text for a stock table."""
    current_time = _now_in_ist(now)
    if stocks is None or stocks.empty:
        return (
            "⚠️ STOCK ALERT\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "No stocks were found in the Screener results.\n"
            f"📅 Time: {current_time.strftime('%d-%b-%Y %I:%M:%S %p')} IST"
        )

    missing_columns = [column for column in STOCK_COLUMNS if column not in stocks.columns]
    if missing_columns:
        raise ValueError(
            "The Screener table is missing required columns: "
            + ", ".join(missing_columns)
        )

    lines = [
        "📈 SCREENER MOMENTUM STOCKS",
        "━━━━━━━━━━━━━━━━━━",
        f"📅 Date: {current_time.strftime('%d-%b-%Y')}",
        f"🕒 Time: {current_time.strftime('%I:%M:%S %p')} IST",
        "━━━━━━━━━━━━━━━━━━",
        "",
    ]

    for stock_number, (_, row) in enumerate(stocks.iterrows(), start=1):
        lines.extend(
            [
                f"🔹 {stock_number}. {_display_value(row['Company'])}",
                f"💰 CMP: ₹{_display_value(row['CMP  Rs.'])}",
                f"📊 P/E: {_display_value(row['P/E'])}",
                f"🏢 Market Cap: {_display_value(row['Mar Cap  Rs.Cr.'])} Cr",
                f"📈 ROCE: {_display_value(row['ROCE  %'])}%",
                f"💹 Profit Growth: {_display_value(row['Qtr Profit Var  %'])}%",
                f"📊 Sales Growth: {_display_value(row['Qtr Sales Var  %'])}%",
                f"🔝 52W High: ₹{_display_value(row['52w High  Rs.'])}",
                "━━━━━━━━━━━━━━━━━━",
                "",
            ]
        )

    return "\n".join(lines).rstrip()


def chunk_message(
    message: str,
    max_length: int = TELEGRAM_MAX_MESSAGE_LENGTH,
) -> list[str]:
    """Split text into bounded chunks without dropping any characters."""
    if max_length < 1:
        raise ValueError("max_length must be a positive integer.")

    chunks = []
    current_chunk = ""

    for line in message.splitlines(keepends=True):
        while len(line) > max_length:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            chunks.append(line[:max_length])
            line = line[max_length:]

        if len(current_chunk) + len(line) > max_length:
            chunks.append(current_chunk)
            current_chunk = ""
        current_chunk += line

    if current_chunk:
        chunks.append(current_chunk)
    elif not chunks and message == "":
        return [""]

    return chunks


def send_telegram_message(message: str, retries: int = 3) -> bool:
    """Send one message, retrying transient failures and reporting the outcome."""
    if retries < 1:
        raise ValueError("retries must be at least 1.")

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        raise ValueError(
            "Telegram credentials are missing. Set TELEGRAM_BOT_TOKEN and "
            "TELEGRAM_CHAT_ID in the environment or .env file."
        )

    url = TELEGRAM_API_URL.format(token=bot_token)
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                url,
                json={"chat_id": chat_id, "text": message},
                timeout=TELEGRAM_TIMEOUT_SECONDS,
            )
            response.raise_for_status()

            result = response.json()
            if not isinstance(result, dict) or not result.get("ok"):
                description = (
                    result.get("description", "Telegram rejected the message.")
                    if isinstance(result, dict)
                    else "Telegram returned an invalid response."
                )
                raise RuntimeError(description)

            LOGGER.info("Telegram message sent successfully")
            return True
        except (requests.RequestException, RuntimeError) as error:
            LOGGER.warning(
                "Telegram attempt %s/%s failed (%s)",
                attempt,
                retries,
                type(error).__name__,
            )
            if attempt < retries:
                time.sleep(TELEGRAM_RETRY_DELAY_SECONDS)

    return False


def send_stock_list(stocks: Optional[pd.DataFrame]) -> bool:
    """Format and deliver a stock table, returning whether delivery succeeded."""
    message = format_stock_notification(stocks)
    for chunk in chunk_message(message):
        if not send_telegram_message(chunk):
            LOGGER.error("Stock notification delivery failed")
            return False
    return True
