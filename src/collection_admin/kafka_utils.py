import json
import socket
import time
import logging
from typing import Any, Dict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def wait_for_kafka(host: str, port: int, timeout: int = 60) -> None:
    """Block until Kafka is reachable"""
    logger.info(f"Waiting for Kafka at {host}:{port} ...")
    start = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout = 2):
                logger.info("Kafka is ready!")
                return
        except Exception:
            if time.time() - start > timeout:
                logger.error(f"Timeout waiting for Kafka at {host}:{port}")
                raise TimeoutError(f"Kafka at {host}:{port} not reachable")
            time.sleep(2)


def kline_to_dict(msg: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a Binance kline WebSocket message into a flat dict"""
    k = msg["k"]
    open_time = k["t"]
    close_time = k["T"]
    open_price = float(k["o"])
    close_price = float(k["c"])
    high_price = float(k["h"])
    low_price = float(k["l"])
    volume = float(k["v"])
    quote_vol = float(k["q"])
    num_trades = k["n"]
    taker_base_vol = float(k["V"])
    taker_quote_vol = float(k["Q"])
    is_closed = k["x"]

    def iso_from_ms(ms: int) -> str:
        return datetime.fromtimestamp(ms / 1000.0, tz = timezone.utc) \
            .isoformat(timespec = "milliseconds")

    return {
        "symbol": msg["s"],
        "open_time": open_time,
        "open": open_price,
        "high": high_price,
        "low": low_price,
        "close": close_price,
        "volume": volume,
        "close_time": close_time,
        "quote_volume": quote_vol,
        "num_trades": num_trades,
        "taker_base_volume": taker_base_vol,
        "taker_quote_volume": taker_quote_vol,
        "open_datetime": iso_from_ms(open_time),
        "close_datetime": iso_from_ms(close_time),
        "price_change": close_price - open_price,
        "price_change_pct": round((close_price - open_price) / open_price * 100, 4) if open_price else 0,
        "high_low_spread": high_price - low_price,
        "high_low_spread_pct": round((high_price - low_price) / low_price * 100, 4) if low_price else 0,
        "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "is_closed": is_closed,
    }
