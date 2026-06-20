"""
Data quality tests using Great Expectations to validate MongoDB data.
These tests are skipped if MongoDB is not available or requires authentication.
"""
import os

import pandas as pd
import pytest
from pymongo import MongoClient

try:
    import great_expectations as gx
except ImportError:
    pytest.skip("Great Expectations not installed", allow_module_level = True)


@pytest.fixture(scope="session")
def mongo_client():
    """Create a MongoDB client; skip tests if connection fails."""
    uri = os.environ.get("MONGO_URI")
    if not uri:
        pytest.skip("MONGO_URI not set")
    client = MongoClient(uri, serverSelectionTimeoutMS = 2000)
    try:
        client.admin.command("ping")
    except Exception as e:
        pytest.skip(f"Cannot connect to MongoDB: {e}")
    return client


@pytest.fixture
def sample_data(mongo_client):
    """Fetch a sample of 100 documents from historical_data_15m."""
    collection = mongo_client["cryptobot"]["historical_data_15m"]
    cursor = collection.find({}, {"_id": 0}).limit(100)
    df = pd.DataFrame(list(cursor))
    if df.empty:
        pytest.skip("No historical data available")
    return df


def test_historical_data_has_no_nulls(sample_data):
    df = gx.from_pandas(sample_data)
    for field in ["symbol", "open", "high", "low", "close", "volume"]:
        expect = df.expect_column_values_to_not_be_null(field)
        assert expect["success"], f"Field '{field}' has null values"


def test_prices_positive(sample_data):
    df = gx.from_pandas(sample_data)
    for field in ["open", "high", "low", "close", "volume"]:
        expect = df.expect_column_values_to_be_between(field, min_value=0)
        assert expect["success"], f"Field '{field}' has non-positive values"


def test_high_greater_than_low(sample_data):
    invalid = sample_data[sample_data["high"] < sample_data["low"]]
    assert invalid.empty, f"Found {len(invalid)} rows where high < low"


def test_close_between_high_low(sample_data):
    invalid = sample_data[
        (sample_data["close"] < sample_data["low"]) |
        (sample_data["close"] > sample_data["high"])
    ]
    assert invalid.empty, f"Found {len(invalid)} rows where close outside [low, high]"


def test_volume_positive(sample_data):
    invalid = sample_data[sample_data["volume"] <= 0]
    assert invalid.empty, f"Found {len(invalid)} rows with non positive volume"
