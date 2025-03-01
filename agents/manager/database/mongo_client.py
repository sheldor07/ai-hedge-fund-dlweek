import logging
from pymongo import MongoClient
from ..config import settings

logger = logging.getLogger(settings.APP_NAME)
mongo_client = None

def get_db_client():
    global mongo_client
    if mongo_client is None:
        try:
            mongo_client = MongoClient(settings.MONGODB_URL)
            logger.info("MongoDB connection established")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    return mongo_client[settings.DATABASE_NAME]

def close_db_client():
    global mongo_client
    if mongo_client:
        mongo_client.close()
        mongo_client = None
        logger.info("MongoDB connection closed")