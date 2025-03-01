import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from config.settings import MONGODB_URI, MONGODB_DATABASE

logger = logging.getLogger("stock_analyzer.database")


class MongoDBClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.client = None
        self.db = None
        self.is_connected = False
        self.connection_string = MONGODB_URI
        self.database_name = MONGODB_DATABASE
    
    def connect(self):
        if self.is_connected:
            return True
        
        try:
            logger.info(f"Connecting to MongoDB database: {self.database_name}")
            self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
            
            self.client.admin.command('ping')
            
            self.db = self.client[self.database_name]
            self.is_connected = True
            logger.info("Successfully connected to MongoDB")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        if self.client:
            self.client.close()
            self.is_connected = False
            logger.info("Disconnected from MongoDB")
    
    def get_database(self):
        if not self.is_connected:
            self.connect()
        return self.db
    
    def get_collection(self, collection_name):
        if not self.is_connected:
            self.connect()
        return self.db[collection_name]

mongo_client = MongoDBClient()