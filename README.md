# CryptoBot Project

Welcome!
We’re excited to present **CryptoBot**, our capstone project for the Data Engineer Bootcamp at DataScientest. Our solution applies data engineering best practices, incorporates team agreements, and is tailored to fit the assignment timeline.

Below, we’ll outline our project’s objectives, main features, and quick setup instructions so you can get started easily.

---

## 🚀 Project Overview

**CryptoBot** is a scalable, microservices-based platform designed to collect, store, process, and analyze both historical and real-time cryptocurrency data from Binance. The system delivers processed metrics and visual analytics through a unified API layer and interactive Dash dashboard.

### What is Binance?

[Binance](https://www.binance.com/) is one of the world’s top cryptocurrency exchanges, ranking in the global top 3 by trading volume.
For this project, we focused on the two most liquid trading pairs:

* **BTC/USDT** (Bitcoin)
* **ETH/USDT** (Ethereum)

---

## 🛠️ Key Features

### **Data Extraction**

* **Historical Data:**
  Collects 6 months of 15-minute interval price data using the Binance REST API.
* **Real-Time Data:**
  Streams live market data using the Binance WebSocket API.
* **Incremental Extraction:**
  Automatically fetches only the latest 15-minute intervals each day.

### **Data Pipeline**

* **Batch Extraction:** PySpark for efficient historical data ingestion.
* **Streaming:** Kafka for real-time event streaming.
* **Storage:** MongoDB, with separate collections for historical (`historical_data_15m`) and streaming (`streaming_data_1m`) data.

### **Processing**

* **Analysis:** Jupyter Notebooks for data exploration and initial analysis.
* **Streaming Processing:** Python scripts to manage and process live data.

### **Visualization**

* **Dashboard:** Dash application for interactive, real-time, and historical charts.

### **API Layer**

* **FastAPI:** Provides an interface for the Dash dashboard to retrieve processed historical data directly from MongoDB.

### **Automation & Deployment**

* **Containerization:** All components are Dockerized and orchestrated using Docker Compose.
* **Scheduling:** Cron jobs automate regular historical data extraction tasks.

### **CI/CD**

* **GitHub Actions:**

  * Linting, testing, and Docker image builds for each commit (`ci.yaml`)
  * Automatic deployment of Docker images to DockerHub on release (`release.yaml`)

### **Data Achitecture**

```mermaid
flowchart TD
    A[Binance REST API] --> B[PySpark Extraction]
    B --> C[Preprocessing]
    C --> D[MongoDB<br>historical_data]
    E[Binance WebSocket API] --> F[Kafka Streaming]
    F --> G[Preprocessing]
    G --> H[MongoDB<br>streaming_data]
    D --> I[Processing]
    H --> I
    I --> J[Dashboards]
```
![](./references/ArchichectureProjectOPA.png)


---

##  Project Overview
### 1. Project Structure:
**apr25_bde_int_opa_team_a**
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
    ├── collection_admin
    │   ├── data
    │   │   ├── initialize_historical_data.py
    │   │   ├── update_historical_data.py
    │   │   ├── __init__.py
    │   │   ├── kafka_consumer.py
    │   │   └── kafka_producer.py
    │   ├── db
    │   │   ├── __init__.py
    │   │   └── mongo_utils.py
    │   ├── docker
    │   │   └── Dockerfile.data_collector
    │   │   └── entrypoint.sh
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


### 2. Set up the project

#### 2.1 Environment Variables

Create a `.env` file in the root directory:

```dotenv
MONGO_INITDB_ROOT_USERNAME=your_user
MONGO_INITDB_ROOT_PASSWORD=your_pass
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


#### 2.3 Running Data Collector Scripts 

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

  ### Services Overview

  | Service             | Description                   | Port  |
  | -----------         | ----------------------------- | ----- |
  | `jupyter` (Legacy)  | PySpark + Jupyter Notebook    | 8888  |
  | `kafka`             | Kafka broker                  | 9092  |
  | `fastapi`           | Dash dashboard                | 8000  |
  | `zookeeper`         | Manages Kafka                 | 2181  |
  | `mongo`             | NoSQL document DB             | 27017 |
  | `dash`              | Dash dashboard                | 8050  |


  ### Data Sources Identified

  | Source                | Access Method             | Data Type                            |
  | --------------------- | ------------------------- | ------------------------------------ |
  | Binance REST API      | `https://api.binance.com` | Market data (prices, trades, klines) |
  | Binance WebSocket API | Real-time JSON stream     | Live market changes                  |

---
#### 2.4 Access services:

* Dash app: [http://localhost:8050](http://localhost:8050)
![](/references/historical_dashboard.png)

* MongoDB (from containers): `crypto_mongo:27017`


## Tools Used

* Python 3.9
* PySpark
* Kafka (Bitnami images)
* MongoDB
* Dash (Plotly)
* Docker & Docker Compose
* FastAPI
* Pytest
* Binance API
* Flake8
* GitHub Actions
* Cron Job
* REST API
* WebSocket

## Authors

* Team A – DataScientest : Bootcamp Data Engineer Project (April 2025)
  * Indira Burga 
  * Katharina Klat
  * Siobhan Doherty

---

## License

Licensed under the [Apache License 2.0](./LICENSE).
