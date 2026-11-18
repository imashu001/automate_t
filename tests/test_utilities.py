"""Offline tests for Screener parsing and Telegram notification helpers."""

import os
import unittest
from datetime import datetime
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

import pandas as pd
import requests

from utility_fcn.utility_stocks import fetch_screen_stocks, parse_stock_table
from utility_fcn.utility_telegram import (
    STOCK_COLUMNS,
    chunk_message,
    format_stock_notification,
    get_ist_timestamp,
    send_stock_list,
    send_telegram_message,
)


def make_stock_table() -> pd.DataFrame:
    """Build a representative Screener result without network access."""
    return pd.DataFrame(
        [
            [
                "Example Ltd.",
                125.5,
                18.2,
                2400,
                21.3,
                12.5,
                8.7,
                150.0,
            ]
        ],
        columns=STOCK_COLUMNS,
    )


class ScreenerParsingTests(unittest.TestCase):
    def test_parse_stock_table_returns_largest_table(self) -> None:
        html = """
        <table><tr><th>Note</th></tr><tr><td>Small</td></tr></table>
        <table>
          <tr><th>Company</th><th>CMP</th></tr>
          <tr><td>Example Ltd.</td><td>125.5</td></tr>
          <tr><td>Other Ltd.</td><td>80</td></tr>
        </table>
        """

        stocks = parse_stock_table(html)

        self.assertEqual(len(stocks), 2)
        self.assertEqual(stocks.iloc[0]["Company"], "Example Ltd.")

    def test_parse_stock_table_reports_missing_table(self) -> None:
        with self.assertRaisesRegex(ValueError, "readable table"):
            parse_stock_table("<html><body>No stock table</body></html>")

    @patch("utility_fcn.utility_stocks.requests.get")
    def test_fetch_screen_stocks_checks_response_and_parses_html(
        self, get: Mock
    ) -> None:
        response = Mock()
        response.text = (
            "<table><tr><th>Company</th></tr>"
            "<tr><td>Example Ltd.</td></tr></table>"
        )
        get.return_value = response

        stocks = fetch_screen_stocks()

        response.raise_for_status.assert_called_once_with()
        self.assertEqual(stocks.iloc[0]["Company"], "Example Ltd.")


class TelegramFormattingTests(unittest.TestCase):
    def test_timestamp_is_formatted_in_ist(self) -> None:
        moment = datetime(2026, 1, 2, 3, 4, 5, tzinfo=ZoneInfo("UTC"))

        self.assertEqual(
            get_ist_timestamp(moment),
            "02-Jan-2026 08:34:05 AM IST",
        )

    def test_format_stock_notification_includes_company_and_fields(self) -> None:
        message = format_stock_notification(make_stock_table())

        self.assertIn("Example Ltd.", message)
        self.assertIn("CMP: ₹125.5", message)
        self.assertIn("Market Cap: 2400 Cr", message)
        self.assertIn("52W High: ₹150.0", message)

    def test_format_stock_notification_marks_missing_values(self) -> None:
        stocks = make_stock_table()
        stocks.loc[0, "P/E"] = float("nan")

        self.assertIn("P/E: N/A", format_stock_notification(stocks))

    def test_format_stock_notification_reports_missing_columns(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing required columns"):
            format_stock_notification(pd.DataFrame({"Company": ["Example"]}))

    def test_empty_stock_table_has_informational_message(self) -> None:
        message = format_stock_notification(pd.DataFrame())

        self.assertIn("No stocks were found", message)

    def test_chunk_message_preserves_text_within_limit(self) -> None:
        message = "first line\n" + ("x" * 25) + "\nlast line"

        chunks = chunk_message(message, max_length=12)

        self.assertEqual("".join(chunks), message)
        self.assertTrue(all(len(chunk) <= 12 for chunk in chunks))

    def test_chunk_message_rejects_non_positive_limit(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            chunk_message("message", max_length=0)


class TelegramDeliveryTests(unittest.TestCase):
    @patch.dict(
        os.environ,
        {"TELEGRAM_BOT_TOKEN": "test-token", "TELEGRAM_CHAT_ID": "123"},
    )
    @patch("utility_fcn.utility_telegram.requests.post")
    def test_send_telegram_message_posts_to_bot_api(self, post: Mock) -> None:
        response = Mock()
        response.json.return_value = {"ok": True}
        post.return_value = response

        sent = send_telegram_message("Hello")

        self.assertTrue(sent)
        post.assert_called_once_with(
            "https://api.telegram.org/bottest-token/sendMessage",
            json={"chat_id": "123", "text": "Hello"},
            timeout=20,
        )

    @patch.dict(
        os.environ,
        {"TELEGRAM_BOT_TOKEN": "test-token", "TELEGRAM_CHAT_ID": "123"},
    )
    @patch("utility_fcn.utility_telegram.time.sleep")
    @patch("utility_fcn.utility_telegram.requests.post")
    def test_send_telegram_message_retries_transient_failures(
        self, post: Mock, sleep: Mock
    ) -> None:
        response = Mock()
        response.json.return_value = {"ok": True}
        post.side_effect = [requests.Timeout, response]

        self.assertTrue(send_telegram_message("Hello", retries=2))
        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once_with(10)

    @patch.dict(os.environ, {}, clear=True)
    def test_send_telegram_message_requires_credentials(self) -> None:
        with self.assertRaisesRegex(ValueError, "TELEGRAM_BOT_TOKEN"):
            send_telegram_message("Hello")

    @patch("utility_fcn.utility_telegram.send_telegram_message")
    def test_send_stock_list_sends_formatted_message(self, send: Mock) -> None:
        self.assertTrue(send_stock_list(make_stock_table()))

        send.assert_called_once()
        self.assertIn("Example Ltd.", send.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
