#!/usr/bin/env bash
set -euo pipefail

# ——— load all environment variables from .env ———
export $(grep -vE '^(#|$)' /app/.env | xargs)

# ——— prepare cron log ———
mkdir -p /var/log
: > /var/log/cron.log
chmod 0644 /var/log/cron.log

# ——— install cron jobs ———
cat <<EOF >/etc/cron.d/historical_update
# Run update_historical_data every 5 minutes (for quick testing)
*/5 * * * *   root   python /app/src/collection_admin/data/update_historical_data.py >> /var/log/cron.log 2>&1
# Run update_historical_data daily at midnight
0   0 * * *   root   python /app/src/collection_admin/data/update_historical_data.py >> /var/log/cron.log 2>&1
EOF

chmod 0644 /etc/cron.d/historical_update
crontab /etc/cron.d/historical_update

# ——— start cron in background ———
service cron start

# ——— one-time seeding of historical data ———
echo "--- Seeding 15m historical data (once) ---"
python /app/src/collection_admin/data/initialize_historical_data.py

# ——— launch real-time streams ———
echo "--- Launching Kafka producer (1m stream) ---"
python /app/src/collection_admin/data/kafka_producer.py &

echo "--- Launching Kafka consumer (persist 1m stream) ---"
python /app/src/collection_admin/data/kafka_consumer.py &

# ——— keep container alive by tailing cron log ———
tail -f /var/log/cron.log
