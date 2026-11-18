import requests
import pandas as pd
from io import StringIO

SCREEN_URL = "https://www.screener.in/screens/3766436/momentum/"

def fetch_top_five():

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        SCREEN_URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    tables = pd.read_html(StringIO(response.text))

    if not tables:
        raise ValueError("No stock table found")

    df = max(tables, key=len)

    print(f"Fetched {len(df)} stocks from Screener")

    print("Available columns:", df)

    return df