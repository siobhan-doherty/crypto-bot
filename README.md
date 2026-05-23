# Binance Crypto Bot Project

Welcome!
We’re excited to present Binance CryptoBot, our capstone project for the Data Engineer Bootcamp at DataScientest. Our solution applies best practices in data engineering, implements robust monitoring, and leverages workflow automation tools to provide a scalable, production-like pipeline for cryptocurrency data.

---

## Project Overview

Binance CryptoBot is a microservices-based platform designed to collect, process, and visualize both historical and real-time cryptocurrency data from Binance. The project demonstrates full-lifecycle data engineering, from raw data ingestion to dashboard analytics, using containerized services and orchestration with Docker Compose and Apache Airflow.

### What is Binance?

[Binance](https://www.binance.com/) is one of the world’s top cryptocurrency exchanges, ranking in the global top 3 by trading volume.
For this project, we focused on the two most liquid trading pairs:

* **BTC/USDT** (Bitcoin)
* **ETH/USDT** (Ethereum)

### Data Sources Identified

  | Source                | Access Method             | Data Type                            |
  | --------------------- | ------------------------- | ------------------------------------ |
  | Binance REST API      | `https://api.binance.com` | Market data (prices, trades, klines) |
  | Binance WebSocket API | Real-time JSON stream     | Live market changes                  |

---
## Architecture & Components

### **Main Services:**

| Service                    | Description                      | Port  | Healthcheck     |
| -------------------------- | -------------------------------- | ----- | --------------- |
| `zookeeper`                | Kafka manager                    | 2181  | ✔️              |
| `kafka`                    | Kafka broker                     | 9092  | ✔️              |
| `mongodb`                  | Data warehouse for all events    | 27017 | ✔️              |
| `crypto_data_collector`    | Spark, batch & streaming scripts |       | (manual launch) |
| `kafka_producer`           | Real-time data producer          |       | ✔️              |
| `kafka_consumer`           | Real-time data consumer          |       | ✔️              |
| `fastapi`                  | REST API for analytics           | 8000  | ✔️              |
| `dash`                     | Dash analytics web dashboard     | 8050  | ✔️              |
| `crypto_postgres`          | PostgreSQL for Airflow metadata  | 5432  | ✔️              |
| `crypto_airflow_init`      | Airflow DB/user initialization   |       |                 |
| `crypto_airflow`           | Airflow Web UI                   | 8080  | ✔️              |
| `crypto_airflow_scheduler` | Airflow Scheduler                |       | ✔️              |

---

## Key Features

### **Data Extraction**

* **Historical Data:**
  6 months of 15-minute interval price data via Binance REST API, ingested with PySpark.
* **Real-Time Data:**
  Streams 1-minute market data from Binance WebSocket, routed through Kafka and stored in MongoDB.
* **Incremental Extraction:**
  Automatically fetches every 15-minute interval that has occurred since the last successful extraction, typically covering all intervals from the previous day.

### **Automation & Scheduling**

* **Airflow Orchestration:**

  * **DAG: `initialize_historical_data`** (manual, one-off) – loads historical data at project start.
  * **DAG: `update_historical_data`** (scheduled daily) – pulls new data automatically.
* **Docker Compose:** All services are managed and monitored as containers.
* **Healthchecks:** All containers except `crypto_data_collector` are monitored for uptime using Docker healthchecks.
Note: Due to time constraints, we deployed a minimal viable version (MVP) of Airflow for initial implementation

### **Processing & Storage**

* **MongoDB:** Stores both historical and streaming data in separate collections for historical (`historical_data_15m`) and streaming (`streaming_data_1m`) data.
* **PySpark:** Efficient ETL for historical ingestion.

### **Streaming Pipeline**

* **Kafka Producer:** Publishes real-time data to a topic.
* **Kafka Consumer:** Consumes and persists real-time messages to MongoDB.
* **Automatic Restart:** Kafka producer/consumer containers auto-restart if they crash.

### **API & Visualization**

* **Dashboard:** Dash application with interactive charts for historical and streaming data.
* **FastAPI:** Provides an interface for the Dash dashboard to retrieve historical and streaming data directly from MongoDB.

* For development purposes, the API and dashboard can be run outside of containers:
	* launch the data collector containers: `docker compose up data_collector`
	* in the root folder, execute `python3 run_api.py all` to run fastapi and dash in separated processes
	* access the dashboard at `localhost:8050`

### **Automation & Deployment**

* **Containerization:** All components are Dockerized and orchestrated using Docker Compose.
* **Scheduling (legacy):** Cron jobs automate regular historical data extraction tasks.

### **CI/CD**

* **GitHub Actions:**

  * Linting, testing, and Docker image builds for each commit (`ci.yaml`)
  * Automatic deployment of Docker images to DockerHub on release (`release.yaml`)

Note : For demo purposes, the streaming data was reset to ensure a consistent real-time view.

### **Data Achitecture**

```mermaid
flowchart TD
    A[Binance REST API] --> B[PySpark Extraction]
    B --> C[Preprocessing]
    C --> D[MongoDB<br>historical_data_15m]
    E[Binance WebSocket API] --> F[Kafka Streaming]
    F --> G[Preprocessing]
    G --> H[MongoDB<br>streaming_data_1m]
    D --> I[Processing]
    H --> I
    I --> J[Dash/REST API]
```
![](./references/ArchichectureProjectOPA_v2.png)


---

##  Project Overview
### 1. Project Structure:
```markdown
apr25_bde_int_opa_team_a
├── airflow
│   └── dags
│       ├── initialize_historical_data.py
│       └── update_historical_data.py
├── docker-compose.yml
├── LICENSE
├── notebooks
│   ├── Check Mongodb.ipynb
│   ├── Historical_data.ipynb
│   ├── Historical_data_mit_api_sd_v1.ipynb
│   └── Kafka.ipynb
├── README_1.md
├── README.md
├── references
│   ├── API explanation.md
│   ├── ArchichectureProjectOPA.png
│   ├── commands.md
│   ├── commands_mongoDB.md
│   ├── docker_ps.png
│   ├── FastAPI_api_user.png
│   └── historical_dashboard.png
├── requirements-dev.txt
├── run_api.py
├── src
│   ├── api_user
│   │   ├── docker
│   │   │   ├── Dockerfile.dash
│   │   │   └── Dockerfile.fastapi
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── router.py
│   │   └── visualization
│   │       ├── assets
│   │       │   └── style.css
│   │       ├── callbacks.py
│   │       ├── dash_app.py
│   │       ├── fetch_data.py
│   │       ├── __init__.py
│   │       ├── layout
│   │       │   ├── controls.py
│   │       │   └── theme.py
│   │       └── plots
│   │           ├── candlestickplot.py
│   │           ├── lineplot.py
│   │           ├── volatilityplot.py
│   │           └── volumeplot.py
│   └── collection_admin
│       ├── data
│       │   ├── initialize_historical_data.py
│       │   ├── __init__.py
│       │   ├── kafka_consumer.py
│       │   ├── kafka_producer.py
│       │   └── update_historical_data.py
│       ├── db
│       │   ├── __init__.py
│       │   └── mongo_utils.py
│       ├── docker
│       │   └── Dockerfile.data_collector
│       ├── __init__.py
│       └── requirements.txt
└── tests
    ├── __init__.py
    └── test_fastapi_endpoints.py
```

### 2. Set up the project

#### 2.1 Environment Variables

Create a `.env` file in the root directory:

```dotenv
MONGO_INITDB_ROOT_USERNAME=your_user
MONGO_INITDB_ROOT_PASSWORD=your_pass

# airflow configuration
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow
AIRFLOW__CORE__FERNET_KEY=your_fernet_key
AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=False
AIRFLOW__CORE__LOAD_EXAMPLES=False
AIRFLOW_UID=50000
# admin credentials
AIRFLOW_ADMIN_USERNAME=your_user
AIRFLOW_ADMIN_PASSWORD=your_pass
AIRFLOW_ADMIN_FIRSTNAME=your_firsname
AIRFLOW_ADMIN_LASTNAME=your_lastname
AIRFLOW_ADMIN_EMAIL=your_email
```

You can generete the Fernet key by running in Python:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```
Or from the terminal (if you have Airflow installed):
```bash
airflow generate-fernet-key

```

Create a `.env` file in src/collection_admin directory:
```dotenv
MONGO_INITDB_ROOT_USERNAME=your_user
MONGO_INITDB_ROOT_PASSWORD=your_pass
MONGO_URI=mongodb://your_user:your_pass@crypto_mongo:27017/cryptobot?authSource=admin
BINANCE_API_KEY=api_key
BINANCE_SECRET_KEY=api_secret
```

Create a `.env` file in src/api_user directory:

```dotenv
MONGO_URI=mongodb://your_user:your_pass@crypto_mongo:27017/cryptobot?authSource=admin
```
#### 2.2 **Launch containers**:

  ```bash
  docker-compose build
  docker-compose up -d
  # It will display 8 containers
  docker ps
  ```
  ![](./references/docker_ps.png)

#### 2.3. **Running Batch and Streaming Jobs**

* **One-time historical data:**

  * Trigger Airflow DAG `initialize_historical_data` from the Airflow UI.

* **Daily historical update:**

  * Airflow DAG `update_historical_data` runs every midnight (can be triggered manually).

* **Streaming (real-time):**

  * Kafka producer and consumer start **automatically** with Docker Compose.
  * Use `docker logs crypto_kafka_producer` or `docker logs crypto_kafka_consumer` to monitor live activity.
  *
#### 2.4 Running Data Collector Scripts for testing outside the airflow

  Seed 3–6 months of 15m data:
  ```bash
  docker exec -it crypto_data_collector python /app/src/collection_admin/data/initialize_historical_data.py
  ```
  Pull only new 15m candles:
  ```bash
  docker exec -it crypto_data_collector python /app/src/collection_admin/data/update_historical_data.py
  ```
  Start 1-minute Kafka producer:
  ```bash
  docker exec -it crypto_data_collector python /app/src/collection_admin/data/kafka_producer.py
  ```
  Start Kafka consumer:
  ```bash
  docker exec -it crypto_data_collector python /app/src/collection_admin/data/kafka_consumer.py
  ```


---
#### 2.4 Access services:

* `crypto_airflow` (Web UI) at [http://localhost:8080](http://localhost:8080)
  ![](/references/airflow_home.png)
* `crypto_dash` (dashboard) at [http://localhost:8050](http://localhost:8050)
  ![](/references/historical_dashboard.png)
* `crypto_fastapi` (API) at [http://localhost:8000/docs](http://localhost:8000/docs)
  ![](/references/FastAPI_api_user.png)

## Notes & MVP Scope

* **Airflow is used as the workflow orchestrator** (MVP: runs batch ETL scripts; future work could expand to full data pipeline monitoring and alerting).
* **Healthchecks** allow robust Docker restarts and easier debugging of failing containers.
* **Logs, DAG output, and temporary files are excluded from version control.**
  Additions to `.gitignore`:

  ```
  airflow/logs/
  ```
* **Demo Data Reset:** For demo purposes, streaming collections may be cleared to guarantee a fresh, consistent real-time view.


## Authors

* Team A – DataScientest : Bootcamp Data Engineer Project (April 2025)
  * Indira Burga
  * Katharina Klat
  * Siobhan Doherty

Data Engineer Bootcamp | DataScientest (April 2025)

---

## License

Licensed under the [Apache License 2.0](./LICENSE).
