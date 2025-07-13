# Useful Docker & Project Commands

A collection of commands for managing and troubleshooting the CryptoBot data architecture, including Docker services, volumes, Kafka streaming.

---

## Clean Up Services & Volumes

```bash
# List running containers
docker ps

# View logs for a specific container
docker logs crypto_kafka

# Test network connectivity from PySpark container to Kafka
docker exec -it crypto_pyspark ping kafka
docker exec -it crypto_pyspark telnet kafka 9092

# Remove all containers and associated volumes
docker-compose down -v

# Remove stopped containers that are not defined in the Compose file
docker-compose down --remove-orphans
```

---

## Launch Data Architecture

```bash
# Build Docker images
docker-compose build

# Build images without using cache
docker-compose build --no-cache

# Start services in detached mode
docker-compose up -d
```

---

## 🔄 Launch Scripts for test (kafka and pyspark)

> **Note:** Run these commands in different terminals as needed.

```bash
# Initialize historical data
docker exec -it crypto_data_collector python3 src/collection_admin/data/initialize_historical_data.py

# Update historical data (incremental)
docker exec -it crypto_data_collector python3 src/collection_admin/data/update_historical_data.py

# Start Kafka producer
docker exec -it crypto_kafka_producer python3 src/collection_admin/data/kafka_producer.py

# Start Kafka consumer
docker exec -it crypto_kafka_consumer python3 src/collection_admin/data/kafka_consumer.py
```

---

## Manage Docker Volumes

```bash
# Inspect MongoDB data volume
docker volume inspect apr25_bde_int_opa_team_a_mongo_data
docker logs crypto_kafka_producer
docker logs crypto_kafka_consumer

#  Check Process List
docker exec -it crypto_kafka_producer ps aux
docker exec -it crypto_kafka_consumer ps aux
```

---

## Reset Project (Full Clean & Rebuild)

```bash
docker-compose down -v
docker-compose up --build --force-recreate
```

## Airflow implementation
### Create folder
```bash
mkdir -p airflow/dags
mkdir -p airflow/logs
mkdir -p airflow/plugins
```

### Give them permissions
```bash
sudo chown -R 50000:0 airflow/logs
```

