#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
INTEGRATION_DIR="${REPO_ROOT}/tests/integration"
COMPOSE_FILE="${INTEGRATION_DIR}/docker-compose.e2e.yml"

cleanup() {
    status=$?
    if [ $status -ne 0 ]; then
        echo "=== E2E failed: dumping logs ==="
        docker compose -f "${COMPOSE_FILE}" logs --tail=200
    fi
    echo "=== Stopping and cleaning up E2E stack ==="
    docker compose -f "${COMPOSE_FILE}" down -v || true
    exit $status
}

trap cleanup EXIT

# build required images first
echo "=== Building required images ==="
docker build -f "${REPO_ROOT}/src/collection_admin/docker/Dockerfile.data_collector" -t crypto_data_collector .
docker build -f "${REPO_ROOT}/src/api_user/docker/Dockerfile.fastapi" -t crypto-bot-fastapi .

echo "=== Starting E2E test stack ==="
docker compose -f "${COMPOSE_FILE}" up -d --wait

echo "=== Waiting for services to be healthy ==="
sleep 15

echo "=== Running E2E test ==="
cd "${REPO_ROOT}"
export KAFKA_ENDPOINT=localhost:9092
export MONGO_ENDPOINT=mongodb://localhost:27018
export FASTAPI_URL=http://localhost:8003
E2E_TEST=1 pytest tests/test_e2e_pipeline.py -v

echo "=== E2E test completed successfully ==="
