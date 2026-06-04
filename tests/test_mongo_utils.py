from unittest.mock import MagicMock, patch

import pytest

from collection_admin.db.mongo_utils import get_mongo_collection, save_to_collection


@patch("collection_admin.db.mongo_utils.MongoClient")
def test_get_mongo_collection_success(mock_client):
    mock_client.return_value.admin.command.return_value = {"ok": 1}
    collection = get_mongo_collection("test_db", "test_coll")
    mock_client.assert_called_once()
    assert collection is not None


@patch("collection_admin.db.mongo_utils.MongoClient")
def test_get_mongo_collection_failure(mock_client):
    mock_client.return_value.admin.command.side_effect = Exception("conn error")
    with pytest.raises(RuntimeError):
        get_mongo_collection("test_db", "test_coll")


@patch("collection_admin.db.mongo_utils.get_mongo_collection")
def test_save_to_collection(mock_get_collection):
    mock_collection = MagicMock()
    mock_get_collection.return_value = mock_collection
    save_to_collection("test_db", "test_coll", {"key": "value"})
    mock_collection.insert_one.assert_called_once_with({"key": "value"})
