import uvicorn
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from config import settings
from api import api_router
from database import get_db_client, close_db_client

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

logger = logging.getLogger(settings.APP_NAME)
logging.basicConfig(level=logging.INFO)

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.APP_NAME} application")
    get_db_client()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.APP_NAME} application")
    close_db_client()

@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)