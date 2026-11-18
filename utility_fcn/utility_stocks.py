"""Helpers for fetching stock data from the configured Screener screen."""

import logging
import os
from io import StringIO

import pandas as pd
import requests

LOGGER = logging.getLogger(__name__)

DEFAULT_SCREEN_URL = "https://www.screener.in/screens/3766436/momentum/"
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0"}
REQUEST_TIMEOUT_SECONDS = 30


def get_screen_url() -> str:
    """Return the configured Screener URL or the project's default screen."""
    screen_url = os.getenv("SCREENER_SCREEN_URL", DEFAULT_SCREEN_URL).strip()
    if not screen_url:
        raise ValueError("SCREENER_SCREEN_URL must not be empty.")
    return screen_url


def parse_stock_table(html: str) -> pd.DataFrame:
    """Parse the largest HTML table in a Screener response."""
    try:
        tables = pd.read_html(StringIO(html), flavor="lxml")
    except ValueError as error:
        raise ValueError("The Screener response did not contain a readable table.") from error

    if not tables:
        raise ValueError("The Screener response did not contain a stock table.")

    stocks = max(tables, key=len).reset_index(drop=True)
    if stocks.empty:
        raise ValueError("The Screener stock table is empty.")

    return stocks


def fetch_screen_stocks() -> pd.DataFrame:
    """Fetch and parse the stock table returned by the configured Screener screen."""
    response = requests.get(
        get_screen_url(),
        headers=REQUEST_HEADERS,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    stocks = parse_stock_table(response.text)
    LOGGER.info("Fetched %s stocks from Screener", len(stocks))
    return stocks


def fetch_top_five() -> pd.DataFrame:
    """Backward-compatible name for fetching the full Screener table.

    The configured screen determines its own results; this function does not
    truncate the table to five rows.
    """
    return fetch_screen_stocks()
