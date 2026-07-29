"""
MongoDB Time Series repository for sentiment history.
Optimized for high-frequency sentiment data storage and retrieval.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pymongo import MongoClient, IndexModel
from pymongo.errors import ConnectionFailure, OperationFailure

logger = logging.getLogger(__name__)


class SentimentRepository:
    """
    Repository for storing and retrieving sentiment history in MongoDB Time Series.
    Features:
    - Automatic compression (90%+ storage reduction)
    - Built-in retention policy
    - Optimized time-range queries
    - Indexed metadata for fast filtering
    """
    DATABASE_NAME = "cryptobot"
    COLLECTION_NAME = "sentiment_history"
    # retention: keep 1 year of data by default
    DEFAULT_RETENTION_SECONDS = 365 * 24 * 60 * 60  # 1 year


    def __init__(
        self,
        mongo_uri: str,
        database_name: str = DATABASE_NAME,
        collection_name: str = COLLECTION_NAME,
        retention_seconds: int = DEFAULT_RETENTION_SECONDS,
    ):
        self.mongo_uri = mongo_uri
        self.database_name = database_name
        self.collection_name = collection_name
        self.retention_seconds = retention_seconds
        self._collection = None
        self._ensure_collection()


    def _get_client(self) -> MongoClient:
        """Create MongoDB client with timeout configuration."""
        return MongoClient(
            self.mongo_uri,
            serverSelectionTimeoutMS = 5000,
            socketTimeoutMS = 30000,
            connectTimeoutMS = 10000,
        )


    def _ensure_collection(self):
        """Ensure time series collection exists with proper configuration."""
        if self._collection:
            return self._collection

        client = self._get_client()
        try:
            db = client[self.database_name]
            # check if collection exists
            if self.collection_name in db.list_collection_names():
                self._collection = db[self.collection_name]
                return self._collection

            # create time series collection
            self._collection = db.create_collection(
                self.collection_name,
                timeseries = {
                    "timeField": "timestamp",  # required field containing time data
                    "metaField": "metadata",   # optional field containing metadata
                    "granularity": "seconds",  # time unit for bucketing
                },
                expireAfterSeconds = self.retention_seconds,
            )

            # create indexes on frequently queried fields
            self._collection.create_indexes([
                IndexModel([("metadata.symbol", 1)]),
                IndexModel([("metadata.provider", 1)]),
                IndexModel([("metadata.sentiment_label", 1)]),
                IndexModel([("metadata.exchange", 1)]),
                IndexModel([("timestamp", 1)]),
            ])

            logger.info(
                f"Created time series collection '{self.database_name}.{self.collection_name}' "
                f"with {self.retention_seconds}s retention"
            )

        except ConnectionFailure as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise
        except OperationFailure as e:
            logger.error(f"Failed to create collection: {e}")
            raise
        finally:
            client.close()

        return self._collection


    def store_sentiment(
        self,
        symbol: str,
        sentiment_label: str,
        confidence: float,
        text: str,
        provider: str,
        price: float,
        exchange: str,
        timestamp: Optional[datetime] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store a sentiment record in the time series collection.
        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            sentiment_label: Sentiment classification ("bullish", "bearish", "neutral")
            confidence: Confidence score (0-1)
            text: Original text/message that was analyzed
            provider: Sentiment provider ("mistral", "huggingface")
            price: Current price at time of sentiment analysis
            exchange: Exchange where price was fetched
            timestamp: When the sentiment was generated (defaults to now UTC)
            additional_metadata: Any extra fields to store
        Returns:
            Inserted document _id
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        # ensure timestamp is timezone-aware
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo = timezone.utc)

        document = {
            "timestamp": timestamp,
            "sentiment_label": sentiment_label,
            "confidence": float(confidence),
            "symbol": symbol,
            "text": text,
            "provider": provider,
            "price": float(price),
            "exchange": exchange,
            "metadata": {
                "symbol": symbol,
                "provider": provider,
                "sentiment_label": sentiment_label,
                "exchange": exchange,
                **(additional_metadata or {}),
            },
        }
        client = self._get_client()
        try:
            self._collection = client[self.database_name][self.collection_name]
            result = self._collection.insert_one(document)
            logger.debug(
                f"Stored sentiment: {symbol} @ {price} -> {sentiment_label} "
                f"({confidence:.2f}) from {provider}"
            )
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Failed to store sentiment: {e}")
            raise
        finally:
            client.close()


    def store_batch(
        self,
        sentiment_records: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Store multiple sentiment records efficiently.
        Args:
            sentiment_records: List of sentiment record dictionaries
        Returns:
            List of inserted document _ids
        """
        if not sentiment_records:
            return []

        client = self._get_client()
        try:
            self._collection = client[self.database_name][self.collection_name]
            result = self._collection.insert_many(sentiment_records)
            logger.info(f"Stored batch of {len(result.inserted_ids)} sentiment records")
            return [str(_id) for _id in result.inserted_ids]

        except Exception as e:
            logger.error(f"Failed to store sentiment batch: {e}")
            raise
        finally:
            client.close()


    def get_sentiment_trend(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        provider: Optional[str] = None,
        limit: int = 10000,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve sentiment records for trend analysis.
        Args:
            symbol: Trading pair to filter by
            start_time: Start of time range (inclusive)
            end_time: End of time range (inclusive)
            provider: Optional filter by provider
            limit: Maximum number of records to return
        Returns:
            List of sentiment records sorted by timestamp
        """
        client = self._get_client()
        try:
            self._collection = client[self.database_name][self.collection_name]
            query = {
                "timestamp": {
                    "$gte": start_time,
                    "$lte": end_time,
                },
                "symbol": symbol,
            }
            if provider:
                query["provider"] = provider
            cursor = self._collection.find(query).sort("timestamp", 1).limit(limit)
            return list(cursor)

        except Exception as e:
            logger.error(f"Failed to query sentiment trend: {e}")
            raise
        finally:
            client.close()


    def get_sentiment_price_correlation(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        time_window: str = "1h",
    ) -> List[Dict[str, Any]]:
        """
        Retrieve sentiment and price data aggregated by time window for correlation.
        Args:
            symbol: Trading pair
            start_time: Start of time range
            end_time: End of time range
            time_window: Aggregation window ("1h", "4h", "1d", etc.)
        Returns:
            List of aggregated records with avg sentiment, avg price, count
        """
        client = self._get_client()
        try:
            self._collection = client[self.database_name][self.collection_name]
            # convert time_window to aggregation pipeline
            group_id = {
                "symbol": "$symbol",
                "year": {"$year": "$timestamp"},
                "month": {"$month": "$timestamp"},
                "day": {"$dayOfMonth": "$timestamp"},
                "hour": {"$hour": "$timestamp"},
            }
            if time_window == "1d":
                group_id = {
                    "symbol": "$symbol",
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"},
                    "day": {"$dayOfMonth": "$timestamp"},
                }
            elif time_window == "4h":
                group_id = {
                    "symbol": "$symbol",
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"},
                    "day": {"$dayOfMonth": "$timestamp"},
                    "hour": {"$floor": {"$divide": ["$hour", 4]}},
                }
            pipeline = [
                {
                    "$match": {
                        "timestamp": {"$gte": start_time, "$lte": end_time},
                        "symbol": symbol,
                    }
                },
                {
                    "$group": {
                        "_id": group_id,
                        "timestamp": {"$first": "$timestamp"},
                        "avg_sentiment_score": {"$avg": "$confidence"},
                        "avg_price": {"$avg": "$price"},
                        "count": {"$sum": 1},
                        "bullish_count": {
                            "$sum": {
                                "$cond": [{"$eq": ["$sentiment_label", "bullish"]}, 1, 0]
                            }
                        },
                        "bearish_count": {
                            "$sum": {
                                "$cond": [{"$eq": ["$sentiment_label", "bearish"]}, 1, 0]
                            }
                        },
                        "neutral_count": {
                            "$sum": {
                                "$cond": [{"$eq": ["$sentiment_label", "neutral"]}, 1, 0]
                            }
                        },
                    }
                },
                {"$sort": {"_id": 1}},
            ]

            return list(self._collection.aggregate(pipeline))

        except Exception as e:
            logger.error(f"Failed to aggregate sentiment-price correlation: {e}")
            raise
        finally:
            client.close()


    def get_aggregated_sentiment(
        self,
        start_time: datetime,
        end_time: datetime,
        group_by: str = "hour",
    ) -> List[Dict[str, Any]]:
        """
        Get aggregated sentiment statistics over time.
        Args:
            start_time: Start of time range
            end_time: End of time range
            group_by: Time grouping ("hour", "day", "week", "month")
        Returns:
            Aggregated sentiment statistics
        """
        client = self._get_client()
        try:
            self._collection = client[self.database_name][self.collection_name]
            group_id = {
                "year": {"$year": "$timestamp"},
                "month": {"$month": "$timestamp"},
                "day": {"$dayOfMonth": "$timestamp"},
            }
            if group_by == "hour":
                group_id["hour"] = {"$hour": "$timestamp"}
            elif group_by == "day":
                pass  # already have day, month, year
            elif group_by == "week":
                group_id = {
                    "year": {"$year": "$timestamp"},
                    "week": {"$week": "$timestamp"},
                }
            elif group_by == "month":
                group_id = {
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"},
                }
            pipeline = [
                {"$match": {"timestamp": {"$gte": start_time, "$lte": end_time}}},
                {"$group": {
                    "_id": group_id,
                    "count": {"$sum": 1},
                    "avg_confidence": {"$avg": "$confidence"},
                    "bullish": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "bullish"]}, 1, 0]}},
                    "bearish": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "bearish"]}, 1, 0]}},
                    "neutral": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "neutral"]}, 1, 0]}},
                }},
                {"$sort": {"_id": 1}},
            ]

            return list(self._collection.aggregate(pipeline))

        except Exception as e:
            logger.error(f"Failed to aggregate sentiment: {e}")
            raise
        finally:
            client.close()


    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the sentiment collection."""
        client = self._get_client()
        try:
            db = client[self.database_name]
            collection = db[self.collection_name]

            return {
                "count": collection.estimated_document_count(),
                "size": db.command({"collStats": self.collection_name})["size"],
                "avg_obj_size": db.command({"collStats": self.collection_name})["avgObjSize"],
            }

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            raise
        finally:
            client.close()


    def close(self) -> None:
        """Close any open connections."""
        pass  # connection pooling handles this
