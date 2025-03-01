import uvicorn
import asyncio
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from config import settings, logging_config
from api import api_router
from services import TaskProcessor
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

logger = logging_config.setup_logging(settings.LOGS_DIR, settings.APP_NAME)

task_processor = TaskProcessor()
background_tasks = set()

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.APP_NAME} application")
    get_db_client()
    start_background_task_processing()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.APP_NAME} application")
    for task in background_tasks:
        task.cancel()
    close_db_client()

def start_background_task_processing():
    loop = asyncio.get_event_loop()
    task = loop.create_task(background_task_processor())
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

async def background_task_processor():
    while True:
        try:
            logger.debug("Running task processor...")
            await task_processor.process_pending_tasks()
        except Exception as e:
            logger.error(f"Error in background task processor: {str(e)}")
        
        await asyncio.sleep(60)

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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)