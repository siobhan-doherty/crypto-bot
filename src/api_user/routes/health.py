from fastapi import APIRouter, HTTPException, status
from api_user.database.mongo import get_mongo_client

router = APIRouter()


@router.get("/health", tags=["health"])
async def health_check():
    client = None
    try:
        client = get_mongo_client()
        client.server_info()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "error": str(e)},
        ) from e
    finally:
        if client is not None:
            client.close()
