# Screener Telegram Stock Alerts

Fetches the stock table from a configured [Screener.in](https://www.screener.in/)
screen, formats the results into readable Telegram messages, and sends them to a
Telegram chat. It is a small notification tool: it does **not** connect to a
broker, read a portfolio, place orders, or rebalance investments.

## What it does

1. Requests the configured Screener page and selects its largest HTML table.
2. Formats each returned row with company, price, valuation, market
   capitalization, growth, ROCE, and 52-week-high details.
3. Splits long notifications into Telegram-safe chunks and sends them with
   retries.
4. Sends an informational alert if the screen has no results.

The Screener screen controls which companies appear. The application does not
rank or limit the result to five stocks, despite the legacy
`fetch_top_five()` function name. It also does not validate whether the
displayed data is current or suitable for an investment decision.

## Requirements

- Windows
- Python 3.11 or newer
- A Telegram bot token and the destination chat ID
- Network access to Screener.in and the Telegram Bot API

## Setup

Open PowerShell in the project directory and run:

```powershell
py -3 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set your Telegram credentials:

```dotenv
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

Create a bot with Telegram's BotFather, then make sure the bot can send
messages to the destination chat. A group chat ID is often negative. Keep
`.env` private; it is excluded from Git.

## Run

With the virtual environment active:

```powershell
python -m main
```

Or, after completing setup, double-click `run_stocks.bat` or run it from
PowerShell. The batch file uses the `venv` beside itself and appends captured
console output to `stock_log.txt`.

To run the alert on a schedule, create a Windows Task Scheduler task that
starts `run_stocks.bat`. Configure the task to run whether or not a user is
logged in, and verify that the account running the task can access the project
directory and its `.env` file.

## Project layout

```text
.
├── main.py                         # Startup, logging, and alert orchestration
├── requirements.txt                # Direct Python dependencies
├── .env.example                    # Safe template for local configuration
├── run_stocks.bat                  # Windows launcher / scheduler target
├── utility_fcn/
│   ├── utility_stocks.py            # Screener HTTP request and table parsing
│   └── utility_telegram.py          # Formatting, chunking, and Telegram delivery
└── tests/
    └── test_utilities.py            # Offline unit tests
```

## Tests

The tests use mocked HTTP responses and do not contact Screener or Telegram:

```powershell
python -m unittest discover -s tests -v
```

## Configuration and operational notes

- The Screener screen URL, request headers, and request timeout are constants
  in `utility_fcn/utility_stocks.py`.
- Telegram credentials are read from the process environment when a message
  is sent. `main.py` loads `.env` at startup.
- Telegram sends are retried up to three times, with a ten-second pause
  between attempts. Messages are divided into chunks of at most 3,500
  characters.
- Application errors are written to `stock_errors.log`. The batch launcher
  separately captures console output in `stock_log.txt`. Both files are
  ignored by Git.
- The screen's HTML structure or column names may change. If they do, table
  parsing or notification formatting will report an error rather than sending
  a partial stock summary.

## Security and investment disclaimer

Never commit bot tokens, chat credentials, or other secrets. The messages are
informational output from a third-party screen, not financial advice. Review
the data and make independent decisions; this application does not trade on
your behalf.
