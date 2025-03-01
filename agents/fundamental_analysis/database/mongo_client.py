"""
MongoDB client module for connecting to and managing the MongoDB database.
"""

import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from config.settings import MONGODB_URI, MONGODB_DATABASE

logger = logging.getLogger("stock_analyzer.database")


class MongoDBClient:
    """
    MongoDB client for connecting to and managing the MongoDB database.
    
    Implements the singleton pattern to ensure only one connection is established.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the MongoDB client connection."""
        self.client = None
        self.db = None
        self.is_connected = False
        self.connection_string = MONGODB_URI
        self.database_name = MONGODB_DATABASE
    
    def connect(self):
        """
        Connect to the MongoDB database.
        
        Returns:
            bool: True if connection is successful, False otherwise.
        """
        if self.is_connected:
            return True
        
        try:
            logger.info(f"Connecting to MongoDB database: {self.database_name}")
            self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
            
            # Verify the connection
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
        """
        Disconnect from the MongoDB database.
        """
        if self.client:
            self.client.close()
            self.is_connected = False
            logger.info("Disconnected from MongoDB")
    
    def get_database(self):
        """
        Get the MongoDB database instance.
        
        Returns:
            pymongo.database.Database: The MongoDB database instance.
        """
        if not self.is_connected:
            self.connect()
        return self.db
    
    def get_collection(self, collection_name):
        """
        Get a collection from the MongoDB database.
        
        Args:
            collection_name (str): The name of the collection.
            
        Returns:
            pymongo.collection.Collection: The MongoDB collection.
        """
        if not self.is_connected:
            self.connect()
        return self.db[collection_name]


# Create a global instance of the MongoDB client
mongo_client = MongoDBClient()