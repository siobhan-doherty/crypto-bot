from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api_user.router import router as api_router
import uvicorn

app = FastAPI(
    title="Crypto Dashboard API",
    description="API for serving cryptocurrency dashboard data",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "Welcome to the Crypto Dashboard API",
        "docs": "/docs",
        "redoc": "/redoc",
    }


print("\nRegistered routes:")
for route in app.routes:
    print(f"{route.path} -> {route.name}")

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
