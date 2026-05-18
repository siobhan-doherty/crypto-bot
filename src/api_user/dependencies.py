from fastapi import Depends
from pymongo import MongoClient
from .database.mongo import get_mongo_client
from .repositories.market_repo import MarketRepository
from .services.market_service import MarketService

# singleton client
_client = None


def get_db_client() -> MongoClient:
    global _client
    if _client is None:
        _client = get_mongo_client()
    return _client


def get_market_repo(client: MongoClient = Depends(
        get_db_client)) -> MarketRepository:
    return MarketRepository(client)


def get_market_service(repo: MarketRepository = Depends(
        get_market_repo)) -> MarketService:
    return MarketService(repo)
