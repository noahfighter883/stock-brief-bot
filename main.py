import os
import json
import time
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://www.alphavantage.co/query"

def fetch_daily(symbol: str, api_key: str) -> dict:
    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": symbol,
        "apikey": api_key,
        "outputsize": "compact",
}
    print("Request params:", params)
    r = requests.get(API_URL, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def pct_change(prev_close: float, last_close: float) -> float:
    return (last_close - prev_close) / prev_close * 100.0

def main():
    api_key = os.getenv("ALPHAVANTAGE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ALPHAVANTAGE_API_KEY. Create a .env file from .env.example")

    symbols = ["AAPL", "MSFT", "SPY"]  # keep small due to rate limits
    results = []

    for i, sym in enumerate(symbols):
        data = fetch_daily(sym, api_key)

        # API sometimes returns throttling messages; handle gracefully
        if "Time Series (Daily)" not in data:
            raise RuntimeError(f"Unexpected response for {sym}: {data}")

        ts = data["Time Series (Daily)"]
        dates = sorted(ts.keys(), reverse=True)  # most recent first
        d0, d1 = dates[0], dates[1]

        last_close = float(ts[d0]["4. close"])
        prev_close = float(ts[d1]["4. close"])

        results.append({
            "symbol": sym,
            "date": d0,
            "close": last_close,
            "prev_close": prev_close,
            "pct_change": round(pct_change(prev_close, last_close), 3),
        })

        # Alpha Vantage free tier is rate-limited; be polite
        if i < len(symbols) - 1:
            time.sleep(15)

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "items": results,
    }

    # Write JSON
    with open("report.json", "w") as f:
        json.dump(payload, f, indent=2)

    # Write Markdown
    lines = [
        f"# Daily Stock Brief",
        f"Generated: {payload['generated_at']}",
        "",
        "| Symbol | Date | Close | Prev Close | % Change |",
        "|---|---:|---:|---:|---:|",
    ]
    for item in results:
        lines.append(
            f"| {item['symbol']} | {item['date']} | {item['close']:.2f} | {item['prev_close']:.2f} | {item['pct_change']:.3f}% |"
        )

    with open("report.md", "w") as f:
        f.write("\n".join(lines) + "\n")

    print("Wrote report.md and report.json")

if __name__ == "__main__":
    main()
