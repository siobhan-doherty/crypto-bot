from fastapi import APIRouter, HTTPException, status
from src.api_user.database.mongo import get_mongo_client

COLLECTION = "historical_data_15m"
router = APIRouter()


@router.get("/health", tags = ["health"])
async def health_check():
    try:
        client = get_mongo_client()
        client.server_info()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE,
            detail = {"status": "unhealthy", "error": str(e)},
        ) 
