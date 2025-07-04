#!/usr/bin/env bash
set -euo pipefail

# import all your env vars from the top‐level .env
export $(grep -vE '^(#|$)' /app/.env | xargs)

echo "--- Initializing historical 15m data (one-off seed)"
python /app/src/collection_admin/data/initialize_historical_data.py

echo "--- Updating historical 15m data (daily catch-up)"
python /app/src/collection_admin/data/update_historical_data.py

echo "--- Starting Kafka producer (1m stream)"
python /app/src/collection_admin/data/kafka_producer.py &

echo "--- Starting Kafka consumer (persist 1m stream)"
python /app/src/collection_admin/data/kafka_consumer.py &

wait

# If someone passed a different command, run it now
exec "$@"
