from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api_user.dependencies import get_db_client
from api_user.routes.health import router as health_router
from api_user.routes.market import router as market_router
from api_user.streaming import router as streaming_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = get_db_client()
    yield
    client.close()


app = FastAPI(
    title="Crypto Dashboard API",
    description="API for serving cryptocurrency dashboard data",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(market_router, prefix="/api")
app.include_router(streaming_router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to the Crypto Dashboard API",
        "docs": "/docs",
        "redoc": "/redoc",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_user.main:app", host="0.0.0.0", port=8000, reload=True)  # nosec
