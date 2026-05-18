from fastapi import Depends
from pymongo import MongoClient
from api_user.database.mongo import get_mongo_client
from api_user.repositories.market_repo import MarketRepository
from api_user.services.market_service import MarketService


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
