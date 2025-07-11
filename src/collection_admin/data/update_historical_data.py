"""
Fetch only new 15-minute candles since last stored timestamp.
Run daily (e.g. via Airflow).
"""
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from collection_admin.db.mongo_utils import save_to_collection, get_mongo_collection


load_dotenv(dotenv_path="/app/.env", override=True)

DB = "cryptobot"
COLL = "historical_data_15m"


def get_last_ts(symbol):
    coll = get_mongo_collection(DB, COLL)
    doc = coll.find({"symbol": symbol}).sort("open_time", -1).limit(1)
    return next(doc, {}).get("open_time")


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


def main():
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    for sym in ["BTCUSDT", "ETHUSDT"]:
        last = get_last_ts(sym) or (now_ms - 1000*60*15)
        print(f"Updating {sym} from {last}")
        batch = get_klines(sym, "15m", last+1, now_ms)
        print(f"got {len(batch)} new candles")
        for r in batch:
            rec = {
                "symbol": sym,
                "open_time": int(r[0]), "open": float(r[1]),
                "high": float(r[2]), "low": float(r[3]),
                "close": float(r[4]), "volume": float(r[5]),
                "close_time": int(r[6]), "quote_volume": float(r[7]),
                "num_trades": int(r[8]), "taker_base_volume": float(r[9]),
                "taker_quote_volume": float(r[10]), "ignore": r[11]
            }
            save_to_collection(DB, COLL, rec)
        print(f"finished {sym}")


if __name__ == "__main__":
    main()

