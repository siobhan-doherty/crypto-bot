# Crypto Data Pipeline Project

 1. **The project**:
This project provides a modular and containerized architecture for collecting, storing, streaming, and visualizing cryptocurrency data using tools like **PySpark**, **Kafka**, **MongoDB**, **Dash**, and **Jupyter**.

---

## Features

-  **Data Collection**:
  - Batch ingestion of historical data using PySpark.
  - Real-time streaming with Kafka from Binance API (planned).
  
-  **Data Storage**:
  - NoSQL storage using MongoDB for fast document-based querying.

-  **Data Visualization**:
  - Interactive dashboards built with Plotly Dash.
  - Jupyter Notebooks for exploration and development.

-  **Dockerized Architecture**:
  - All services run in isolated containers managed by Docker Compose.

---

##  Project Structure
pr25_bde_int_opa_team_a
├── docker-compose.yml
├── LICENSE
├── notebooks
│   ├── Check Mongodb.ipynb
│   ├── Historical_data.ipynb
│   ├── Historical_data_mit_api_sd_v1.ipynb
│   └── Kafka.ipynb
├── README.md
├── references
│   ├── API explanation.md
│   ├── command.md
│   ├── Repo Structure Tutorial.md
│   └── Step 1.md
└── src
    ├── api_admin
    │   ├── data
    │   │   ├── collect_historical_data.py
    │   │   ├── __init__.py
    │   │   ├── kafka_consume.py
    │   │   └── kafka_producer.py
    │   ├── db
    │   │   ├── __init__.py
    │   │   └── mongo_utils.py
    │   ├── docker
    │   │   └── Dockerfile.jupyter
    │   ├── __init__.py
    │   └── requirements.txt
    └── api_user
        ├── docker
        │   └── Dockerfile.dash
        ├── __init__.py
        ├── requirements.txt
        └── visualization
            ├── dash_app.py
            ├── dash_stream.py
            └── __init__.py

2. **Check container status**:

```bash
docker ps
```

3. **Access services**:

* Jupyter: [http://localhost:8888](http://localhost:8888)
* Dash app (after launching manually): [http://localhost:8050](http://localhost:8050)
* MongoDB: `localhost:27017`

---

## Running Data Collector Scripts 
Seed 3–6 months of 15m data: 
```bash
docker exec -it crypto_data_collector python /app/src/api_admin/data/initialize_historical_data.py
```
Pull only new 15m candles:
```bash
docker exec -it crypto_data_collector python /app/src/api_admin/data/update_historical_data.py
```
Start 1-minute Kafka producer:
```bash
docker exec -it crypto_data_collector python /app/src/api_admin/data/kafka_producer.py
```
Start Kafka consumer:
```bash
docker exec -it crypto_data_collector python /app/src/api_admin/data/kafka_consumer.py
``````


## Running Dash Apps

```bash
docker exec -it crypto_dash python3 src/api_user/visualization/dash_app.py
```


## Services Overview

| Service     | Description                   | Port  |
| ----------- | ----------------------------- | ----- |
| `jupyter`   | PySpark + Jupyter Notebook    | 8888  |
| `kafka`     | Kafka broker                  | 9092  |
| `zookeeper` | Manages Kafka                 | 2181  |
| `mongo`     | NoSQL document DB             | 27017 |
| `dash`      | Dash dashboard (run manually) | 8050  |


## Environment Variables

Create a `.env` file in the root directory:

```dotenv
MONGO_INITDB_ROOT_USERNAME=your_user
MONGO_INITDB_ROOT_PASSWORD=your_pass
```

Create a `.env` file in src/api_admin directory:
```dotenv
MONGO_INITDB_ROOT_USERNAME=your_user
MONGO_INITDB_ROOT_PASSWORD=your_pass
MONGO_URI=mongodb://your_user:your_pass@crypto_mongo:27017/
BINANCE_API_KEY=api_key
BINANCE_SECRET_KEY=api_secret
```

Create a `.env` file in src/api_user directory:

```dotenv
MONGO_URI=mongodb://your_user:your_pass@crypto_mongo:27017/
```
## Tools Used

* Python 3.9
* PySpark
* Kafka (Bitnami images)
* MongoDB
* Dash (Plotly)
* Docker & Docker Compose


## Authors

* Team A – DataScientest : Bootcamp Data Engineer Project (April 2025)
  * Indira Burga 
  * Katharina Klat
  * Siobhan Doherty


---

## License

Licensed under the [Apache License 2.0](./LICENSE).
