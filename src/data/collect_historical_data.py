import os
import requests
import time
import hmac
import hashlib
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv
from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import from_unixtime, col, round as spark_round
import findspark
findspark.init()


# Load environment variables
load_dotenv(dotenv_path="/home/jovyan/.env", override=True)
API_KEY = os.getenv("BINANCE_API_KEY")
SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

# Spark setup
spark = SparkSession.builder \
    .appName("BinanceToMongoDB_Enhanced") \
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.1.1") \
    .config("spark.mongodb.write.connection.uri", "mongodb://crypto_project:dst123@crypto_mongo:27017/cryptobot.historical_data?authSource=admin") \
    .config("spark.mongodb.read.connection.uri", "mongodb://crypto_project:dst123@crypto_mongo:27017/cryptobot.historical_data?authSource=admin") \
    .getOrCreate()

def create_signature(query_string, secret_key): 
    return hmac.new(secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

def get_authenticated_klines(symbol, interval, limit=1000, start_time=None, end_time=None):
    base_url = "https://api.binance.com"
    endpoint = "/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": min(limit, 1000),
        "timestamp": int(time.time() * 1000)
    }
    if start_time: params["startTime"] = int(start_time)
    if end_time: params["endTime"] = int(end_time)

    query_string = urllib.parse.urlencode(params)
    params["signature"] = create_signature(query_string, SECRET_KEY)
    headers = {"X-MBX-APIKEY": API_KEY}

    try:
        response = requests.get(base_url + endpoint, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return get_public_klines(symbol, interval, limit, start_time, end_time)

def get_public_klines(symbol, interval, limit=1000, start_time=None, end_time=None):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    if start_time: params["startTime"] = int(start_time)
    if end_time: params["endTime"] = int(end_time)

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def fetch_historical_data(symbol="BTCUSDT", target_count=3000):
    intervals = [("1m", 60), ("3m", 180), ("5m", 300), ("15m", 900), ("30m", 1800), ("1h", 3600)]
    all_rows, best_config = [], None

    for interval, seconds in intervals:
        print(f"\nTrying interval: {interval}")
        end_time = int(time.time() * 1000)
        lookback = seconds * 1000
        current_rows, fetched_batches = [], 0

        while len(current_rows) < target_count and fetched_batches < 10:
            start_time = end_time - (lookback * 1000)
            data = get_authenticated_klines(symbol, interval, 1000, start_time, end_time)
            if not data: break

            for row in data:
                current_rows.append(Row(
                    symbol=symbol,
                    open_time=int(row[0]),
                    open=float(row[1]),
                    high=float(row[2]),
                    low=float(row[3]),
                    close=float(row[4]),
                    volume=float(row[5]),
                    close_time=int(row[6]),
                    quote_volume=float(row[7]),
                    num_trades=int(row[8]),
                    taker_base_volume=float(row[9]),
                    taker_quote_volume=float(row[10]),
                    ignore=row[11]
                ))

            end_time = start_time - 1
            fetched_batches += 1
            time.sleep(0.2)

            if len(data) < 1000: break

        # deduplication and retention of best config
        unique_rows = list({r.open_time: r for r in current_rows}.values())
        if len(unique_rows) >= target_count:
            all_rows, best_config = unique_rows, (symbol, interval)
            break
        elif len(unique_rows) > len(all_rows):
            all_rows, best_config = unique_rows, (symbol, interval)

    return all_rows, best_config

def enrich_and_save_to_mongo(rows):
    df = spark.createDataFrame(rows)
    df = df.withColumn("open_datetime", from_unixtime(df.open_time / 1000)) \
        .withColumn("close_datetime", from_unixtime(df.close_time / 1000)) \
        .withColumn("price_change", col("close") - col("open")) \
        .withColumn("price_change_pct", spark_round(((col("close") - col("open")) / col("open")) * 100, 4)) \
        .withColumn("high_low_spread", col("high") - col("low")) \
        .withColumn("high_low_spread_pct", spark_round(((col("high") - col("low")) / col("open")) * 100, 4))

    df.write.format("mongodb").mode("overwrite").save()
    print(f"Saved {df.count()} records to MongoDB")
    return df


if __name__ == "__main__":
    rows, config = fetch_historical_data("BTCUSDT", 3000)
    print(f"Fetched {len(rows)} records using {config}")
    if rows:
        enrich_and_save_to_mongo(rows)
