import logging
from datetime import datetime
from pymongo.errors import DuplicateKeyError, PyMongoError

from database.mongo_client import mongo_client
from database.schema import COMPANIES_COLLECTION, FINANCIAL_STATEMENTS_COLLECTION, FINANCIAL_METRICS_COLLECTION, \
    PRICE_HISTORY_COLLECTION, VALUATION_MODELS_COLLECTION, NEWS_SENTIMENT_COLLECTION, ANALYSIS_REPORTS_COLLECTION

logger = logging.getLogger("stock_analyzer.database")


class DatabaseOperations:
    def __init__(self):
        self.mongo_client = mongo_client
        self.db = mongo_client.get_database()
    
    def _add_metadata(self, document, modified_by="system"):
        current_time = datetime.utcnow()
        if "creation_date" not in document:
            document["creation_date"] = current_time
        document["last_updated"] = current_time
        document["modified_by"] = modified_by
        return document
    
    def insert_one(self, collection_name, document, modified_by="system"):
        try:
            collection = self.db[collection_name]
            document = self._add_metadata(document, modified_by)
            result = collection.insert_one(document)
            logger.info(f"Document inserted in {collection_name}: {result.inserted_id}")
            return result.inserted_id
        except DuplicateKeyError:
            logger.error(f"Duplicate key error when inserting into {collection_name}")
            return None
        except PyMongoError as e:
            logger.error(f"Error inserting document into {collection_name}: {str(e)}")
            return None
    
    def insert_many(self, collection_name, documents, modified_by="system"):
        try:
            collection = self.db[collection_name]
            for doc in documents:
                self._add_metadata(doc, modified_by)
            result = collection.insert_many(documents, ordered=False)
            logger.info(f"{len(result.inserted_ids)} documents inserted in {collection_name}")
            return result.inserted_ids
        except PyMongoError as e:
            logger.error(f"Error inserting multiple documents into {collection_name}: {str(e)}")
            return []
    
    def find_one(self, collection_name, query):
        try:
            collection = self.db[collection_name]
            result = collection.find_one(query)
            return result
        except PyMongoError as e:
            logger.error(f"Error finding document in {collection_name}: {str(e)}")
            return None
    
    def find_many(self, collection_name, query, sort=None, limit=0, skip=0, projection=None):
        try:
            collection = self.db[collection_name]
            cursor = collection.find(query, projection=projection)
            
            if sort:
                cursor = cursor.sort(sort)
            
            if skip > 0:
                cursor = cursor.skip(skip)
            
            if limit > 0:
                cursor = cursor.limit(limit)
            
            return list(cursor)
        except PyMongoError as e:
            logger.error(f"Error finding documents in {collection_name}: {str(e)}")
            return []
    
    def update_one(self, collection_name, query, update, modified_by="system", upsert=False):
        try:
            collection = self.db[collection_name]
            
            if "$set" not in update:
                update["$set"] = {}
            update["$set"]["last_updated"] = datetime.utcnow()
            update["$set"]["modified_by"] = modified_by
            
            if upsert and "creation_date" not in update.get("$setOnInsert", {}):
                if "$setOnInsert" not in update:
                    update["$setOnInsert"] = {}
                update["$setOnInsert"]["creation_date"] = datetime.utcnow()
            
            result = collection.update_one(query, update, upsert=upsert)
            
            if result.modified_count > 0:
                logger.info(f"Document updated in {collection_name}: {result.modified_count} modified")
            elif result.upserted_id:
                logger.info(f"Document upserted in {collection_name}: {result.upserted_id}")
            
            return result.modified_count
        except PyMongoError as e:
            logger.error(f"Error updating document in {collection_name}: {str(e)}")
            return 0
    
    def update_many(self, collection_name, query, update, modified_by="system"):
        try:
            collection = self.db[collection_name]
            
            if "$set" not in update:
                update["$set"] = {}
            update["$set"]["last_updated"] = datetime.utcnow()
            update["$set"]["modified_by"] = modified_by
            
            result = collection.update_many(query, update)
            logger.info(f"Documents updated in {collection_name}: {result.modified_count} modified")
            return result.modified_count
        except PyMongoError as e:
            logger.error(f"Error updating documents in {collection_name}: {str(e)}")
            return 0
    
    def delete_one(self, collection_name, query):
        try:
            collection = self.db[collection_name]
            result = collection.delete_one(query)
            logger.info(f"Document deleted from {collection_name}: {result.deleted_count} deleted")
            return result.deleted_count
        except PyMongoError as e:
            logger.error(f"Error deleting document from {collection_name}: {str(e)}")
            return 0
    
    def delete_many(self, collection_name, query):
        try:
            collection = self.db[collection_name]
            result = collection.delete_many(query)
            logger.info(f"Documents deleted from {collection_name}: {result.deleted_count} deleted")
            return result.deleted_count
        except PyMongoError as e:
            logger.error(f"Error deleting documents from {collection_name}: {str(e)}")
            return 0
    
    def count_documents(self, collection_name, query=None):
        try:
            collection = self.db[collection_name]
            query = query or {}
            count = collection.count_documents(query)
            return count
        except PyMongoError as e:
            logger.error(f"Error counting documents in {collection_name}: {str(e)}")
            return 0
    
    def create_index(self, collection_name, keys, unique=False, sparse=False, background=True):
        try:
            collection = self.db[collection_name]
            index_name = collection.create_index(keys, unique=unique, sparse=sparse, background=background)
            logger.info(f"Index created on {collection_name}: {index_name}")
            return index_name
        except PyMongoError as e:
            logger.error(f"Error creating index on {collection_name}: {str(e)}")
            return None
    
    def drop_index(self, collection_name, index_name):
        try:
            collection = self.db[collection_name]
            collection.drop_index(index_name)
            logger.info(f"Index dropped from {collection_name}: {index_name}")
            return True
        except PyMongoError as e:
            logger.error(f"Error dropping index from {collection_name}: {str(e)}")
            return False
    
    def aggregate(self, collection_name, pipeline):
        try:
            collection = self.db[collection_name]
            result = list(collection.aggregate(pipeline))
            return result
        except PyMongoError as e:
            logger.error(f"Error executing aggregation on {collection_name}: {str(e)}")
            return []

db_ops = DatabaseOperations()