"""
Fetch 3 to 6 months of 15-minute candles from Binance and seed MongoDB.
Run once at beginning.
"""

from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from pyspark.sql import SparkSession, Row
import time, requests, findspark
from api_admin.db.mongo_utils import save_to_collection

findspark.init()
load_dotenv(dotenv_path="/app/.env", override=True)

DB = "cryptobot"
COLL = "historical_data_15m"

# Spark setup
spark = SparkSession.builder.appName("InitHistorical15m").getOrCreate()

def get_klines(symbol, interval, start_ms, end_ms, limit=1000):
    """Public (no-signature) Binance klines endpoint."""
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": int(start_ms),
        "endTime": int(end_ms),
        "limit": min(limit, 1000)
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()

def fetch_15m(symbol="BTCUSDT", months=6):
    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=30*months)
    start_ms, end_ms = int(start_dt.timestamp()*1000), int(end_dt.timestamp() * 1000)
    rows = []

    while start_ms < end_ms:
        batch = get_klines(symbol, "15m", start_ms, end_ms)
        if not batch:
            break
        for r in batch:
            rows.append(Row(
                symbol=symbol,
                open_time=int(r[0]), open=float(r[1]), high=float(r[2]),
                low=float(r[3]), close=float(r[4]), volume=float(r[5]),
                close_time=int(r[6]), quote_volume=float(r[7]),
                num_trades=int(r[8]), taker_base_volume=float(r[9]),
                taker_quote_volume=float(r[10]), ignore=r[11]
            ))
        start_ms = batch[-1][6] + 1
        time.sleep(0.2)

    return rows

def main():
    for sym in ["BTCUSDT", "ETHUSDT"]:
        print(f"initialising {sym} 15m data…")
        rows = fetch_15m(sym, months=6)
        print(f"fetched {len(rows)} rows, saving to Mongo…")
        for row in rows:
            save_to_collection(DB, COLL, row.asDict())
        print(f"done seeding {sym}")

if __name__ == "__main__":
    main()
