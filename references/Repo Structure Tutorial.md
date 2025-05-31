# 📁 CryptoBot Project Folder Structure Tutorial

Welcome! This guide explains how to set up the **project structure** for your Data Engineering CryptoBot project, following best practices and matching our team agreements.

---

## **1. Why Use a Standard Project Structure?**

- 🧩 **Organization:** Keep code, data, documentation, and models separated and easy to find.
- 👩‍💻 **Teamwork:** Everyone knows where to put and find files.
- 🚀 **Production Ready:** Makes it easy to scale, deploy, and maintain.
- 🧪 **Reproducibility:** Anyone can rerun and reproduce your results.
    

---

## **2. Overview of the Project Structure**

```text
cryptobot/
├── LICENSE
├── README.md
├── data/
│   ├── external/
│   ├── interim/
│   ├── processed/
│   └── raw/
├── logs/
├── models/
├── notebooks/
├── references/
├── reports/
│   └── figures/
├── requirements.txt
├── docker-compose.yml
├── .env
└── src/
    ├── __init__.py
    ├── config/
    │   └── config.yaml
    ├── data/
    │   ├── __init__.py
    │   ├── make_dataset.py
    │   └── kafka_stream.py
    ├── db/
    │   ├── __init__.py
    │   └── mongo_utils.py
    ├── features/
    │   ├── __init__.py
    │   └── build_features.py
    ├── models/
    │   ├── __init__.py
    │   ├── train_model.py
    │   └── predict_model.py
    ├── api/
    │   ├── __init__.py
    │   └── main.py
    └── visualization/
        ├── __init__.py
        └── dash_app.py
```

---

## **3. What Is Each Folder/File For?**

|Folder/File|Purpose|
|---|---|
|LICENSE|Project license|
|README.md|Project description, setup, and usage instructions|
|data/|All project datasets (raw, processed, etc.)|
|logs/|Log files from pipelines or training|
|models/|Saved machine learning models|
|notebooks/|Jupyter Notebooks for EDA, prototyping, documentation|
|references/|Manuals, data dictionaries, useful external docs|
|reports/|Project reports, generated results|
|reports/figures/|Plots and images for reports|
|requirements.txt|Python dependencies list|
|docker-compose.yml|Multi-service setup (MongoDB, Jupyter, etc.)|
|.env|Environment variables (never commit secrets)|
|src/|All source code scripts|
|src/config/|Configuration files (e.g., database host, port)|
|src/data/|Data extraction & ingestion scripts|
|src/db/|Database setup & query utilities (MongoDB)|
|src/features/|Feature engineering scripts for ML|
|src/models/|ML model training & prediction scripts|
|src/api/|FastAPI app (for API endpoints and optional dashboard serving)|
|src/visualization/|Scripts for visualization (Dash dashboard)|

---

## **4. How To Create This Structure Quickly (Bash Script Method)**

> 💡 You can automate the creation of this folder structure using a Bash script.

**Step 1:** Open your terminal (Linux, macOS, or Windows WSL).

**Step 2:** Copy the following script and save it as `create_structure.sh` **in your parent directory**.

```bash
#!/bin/bash

ROOT="cryptobot"

# Create folders
mkdir -p $ROOT/data/external
mkdir -p $ROOT/data/interim
mkdir -p $ROOT/data/processed
mkdir -p $ROOT/data/raw
mkdir -p $ROOT/logs
mkdir -p $ROOT/models
mkdir -p $ROOT/notebooks
mkdir -p $ROOT/references
mkdir -p $ROOT/reports/figures
mkdir -p $ROOT/src/config
mkdir -p $ROOT/src/data
mkdir -p $ROOT/src/db
mkdir -p $ROOT/src/features
mkdir -p $ROOT/src/models
mkdir -p $ROOT/src/api
mkdir -p $ROOT/src/visualization

# Touch init and main files
touch $ROOT/src/__init__.py
touch $ROOT/src/data/__init__.py
touch $ROOT/src/db/__init__.py
touch $ROOT/src/features/__init__.py
touch $ROOT/src/models/__init__.py
touch $ROOT/src/api/__init__.py
touch $ROOT/src/visualization/__init__.py

# Main placeholder files (if not exist)
[ -f $ROOT/src/config/config.yaml ] || touch $ROOT/src/config/config.yaml
[ -f $ROOT/src/data/make_dataset.py ] || touch $ROOT/src/data/make_dataset.py
[ -f $ROOT/src/data/kafka_stream.py ] || touch $ROOT/src/data/kafka_stream.py
[ -f $ROOT/src/db/mongo_utils.py ] || touch $ROOT/src/db/mongo_utils.py
[ -f $ROOT/src/features/build_features.py ] || touch $ROOT/src/features/build_features.py
[ -f $ROOT/src/models/train_model.py ] || touch $ROOT/src/models/train_model.py
[ -f $ROOT/src/models/predict_model.py ] || touch $ROOT/src/models/predict_model.py
[ -f $ROOT/src/api/main.py ] || touch $ROOT/src/api/main.py
[ -f $ROOT/src/visualization/dash_app.py ] || touch $ROOT/src/visualization/dash_app.py

# Main project files
[ -f $ROOT/README.md ] || touch $ROOT/README.md
[ -f $ROOT/LICENSE ] || touch $ROOT/LICENSE
[ -f $ROOT/requirements.txt ] || touch $ROOT/requirements.txt
[ -f $ROOT/docker-compose.yml ] || touch $ROOT/docker-compose.yml
[ -f $ROOT/.env ] || touch $ROOT/.env

echo "Project structure created at $ROOT"
```

**Step 3:** In the terminal, make the script executable and run it:

```bash
chmod +x create_structure.sh
./create_structure.sh
```

**Step 4:** You now have a fully structured project ready for development.
