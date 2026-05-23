from typing import Optional

from fastapi import APIRouter, Depends, Query

from api_user.dependencies import get_market_service
from api_user.services.market_service import MarketService

router = APIRouter()


@router.get("/market/range")
async def get_date_range(service: MarketService = Depends(get_market_service)):
    return service.get_date_range()


@router.get("/market/ohlcv")
async def get_ohlcv(
    symbol: Optional[str] = Query(default=None),
    interval: str = Query(default="15m"),
    start_time: Optional[int] = Query(default=None),
    end_time: Optional[int] = Query(default=None),
    limit: Optional[int] = Query(default=None, ge=1),
    service: MarketService = Depends(get_market_service),
):
    return service.get_ohlcv(symbol, interval, start_time, end_time, limit)
