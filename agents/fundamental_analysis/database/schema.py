import logging
from pymongo import ASCENDING, DESCENDING, IndexModel, TEXT

from database.mongo_client import mongo_client

logger = logging.getLogger("stock_analyzer.database")

COMPANIES_COLLECTION = "companies"
FINANCIAL_STATEMENTS_COLLECTION = "financial_statements"
FINANCIAL_METRICS_COLLECTION = "financial_metrics"
PRICE_HISTORY_COLLECTION = "price_history"
VALUATION_MODELS_COLLECTION = "valuation_models"
NEWS_SENTIMENT_COLLECTION = "news_sentiment"
ANALYSIS_REPORTS_COLLECTION = "analysis_reports"

COMMON_FIELDS = {
    "creation_date": {"type": "date", "required": True},
    "last_updated": {"type": "date", "required": True},
    "modified_by": {"type": "string", "required": True},
}

COMPANIES_SCHEMA = {
    "validator": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["ticker", "name", "sector", "industry", "exchange", "cik"] + list(COMMON_FIELDS.keys()),
            "properties": {
                "ticker": {"bsonType": "string"},
                "name": {"bsonType": "string"},
                "sector": {"bsonType": "string"},
                "industry": {"bsonType": "string"},
                "exchange": {"bsonType": "string"},
                "cik": {"bsonType": "string"},
                "description": {"bsonType": "string"},
                "website": {"bsonType": "string"},
                "executives": {"bsonType": "array"},
                **{k: {"bsonType": v["type"]} for k, v in COMMON_FIELDS.items()}
            }
        }
    }
}

FINANCIAL_STATEMENTS_SCHEMA = {
    "validator": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["ticker", "period_type", "period_end_date", "publication_date", "source"] + list(COMMON_FIELDS.keys()),
            "properties": {
                "ticker": {"bsonType": "string"},
                "period_type": {"bsonType": "string", "enum": ["annual", "quarterly"]},
                "period_end_date": {"bsonType": "date"},
                "publication_date": {"bsonType": "date"},
                "source": {"bsonType": "string"},
                "income_statement": {"bsonType": "object"},
                "balance_sheet": {"bsonType": "object"},
                "cash_flow_statement": {"bsonType": "object"},
                **{k: {"bsonType": v["type"]} for k, v in COMMON_FIELDS.items()}
            }
        }
    }
}

FINANCIAL_METRICS_SCHEMA = {
    "validator": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["ticker", "date", "metric_type"] + list(COMMON_FIELDS.keys()),
            "properties": {
                "ticker": {"bsonType": "string"},
                "date": {"bsonType": "date"},
                "metric_type": {"bsonType": "string", "enum": ["profitability", "valuation", "growth", "liquidity", "solvency", "efficiency"]},
                "period_type": {"bsonType": "string", "enum": ["annual", "quarterly", "ttm"]},
                "metrics": {"bsonType": "object"},
                "peer_comparison": {"bsonType": "object"},
                **{k: {"bsonType": v["type"]} for k, v in COMMON_FIELDS.items()}
            }
        }
    }
}

PRICE_HISTORY_SCHEMA = {
    "validator": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["ticker", "date", "open", "high", "low", "close", "volume", "adjusted_close"] + list(COMMON_FIELDS.keys()),
            "properties": {
                "ticker": {"bsonType": "string"},
                "date": {"bsonType": "date"},
                "open": {"bsonType": "double"},
                "high": {"bsonType": "double"},
                "low": {"bsonType": "double"},
                "close": {"bsonType": "double"},
                "volume": {"bsonType": "double"},
                "adjusted_close": {"bsonType": "double"},
                "technical_indicators": {"bsonType": "object"},
                **{k: {"bsonType": v["type"]} for k, v in COMMON_FIELDS.items()}
            }
        }
    }
}

VALUATION_MODELS_SCHEMA = {
    "validator": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["ticker", "model_type", "date", "scenario"] + list(COMMON_FIELDS.keys()),
            "properties": {
                "ticker": {"bsonType": "string"},
                "model_type": {"bsonType": "string", "enum": ["dcf", "ddm", "comparable"]},
                "date": {"bsonType": "date"},
                "scenario": {"bsonType": "string", "enum": ["bear", "base", "bull"]},
                "inputs": {"bsonType": "object"},
                "assumptions": {"bsonType": "object"},
                "results": {"bsonType": "object"},
                "sensitivity_analysis": {"bsonType": "object"},
                "target_price": {"bsonType": "double"},
                "fair_value": {"bsonType": "double"},
                **{k: {"bsonType": v["type"]} for k, v in COMMON_FIELDS.items()}
            }
        }
    }
}

NEWS_SENTIMENT_SCHEMA = {
    "validator": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["ticker", "date", "source", "title", "sentiment_score"] + list(COMMON_FIELDS.keys()),
            "properties": {
                "ticker": {"bsonType": "string"},
                "date": {"bsonType": "date"},
                "source": {"bsonType": "string"},
                "title": {"bsonType": "string"},
                "content": {"bsonType": "string"},
                "url": {"bsonType": "string"},
                "sentiment_score": {"bsonType": "double"},
                "impact_score": {"bsonType": "double"},
                "source_credibility": {"bsonType": "double"},
                **{k: {"bsonType": v["type"]} for k, v in COMMON_FIELDS.items()}
            }
        }
    }
}

ANALYSIS_REPORTS_SCHEMA = {
    "validator": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["ticker", "date", "report_type"] + list(COMMON_FIELDS.keys()),
            "properties": {
                "ticker": {"bsonType": "string"},
                "date": {"bsonType": "date"},
                "report_type": {"bsonType": "string"},
                "data_snapshot": {"bsonType": "object"},
                "analysis": {"bsonType": "object"},
                "recommendations": {"bsonType": "object"},
                "historical_recommendations": {"bsonType": "array"},
                **{k: {"bsonType": v["type"]} for k, v in COMMON_FIELDS.items()}
            }
        }
    }
}

COLLECTION_CONFIGS = {
    COMPANIES_COLLECTION: {
        "schema": COMPANIES_SCHEMA,
        "indexes": [
            IndexModel([("ticker", ASCENDING)], unique=True),
            IndexModel([("cik", ASCENDING)], unique=True),
            IndexModel([("name", TEXT), ("description", TEXT)]),
            IndexModel([("sector", ASCENDING), ("industry", ASCENDING)]),
        ]
    },
    FINANCIAL_STATEMENTS_COLLECTION: {
        "schema": FINANCIAL_STATEMENTS_SCHEMA,
        "indexes": [
            IndexModel([("ticker", ASCENDING), ("period_type", ASCENDING), ("period_end_date", DESCENDING)], unique=True),
            IndexModel([("ticker", ASCENDING), ("period_end_date", DESCENDING)]),
            IndexModel([("publication_date", DESCENDING)]),
        ]
    },
    FINANCIAL_METRICS_COLLECTION: {
        "schema": FINANCIAL_METRICS_SCHEMA,
        "indexes": [
            IndexModel([("ticker", ASCENDING), ("date", DESCENDING), ("metric_type", ASCENDING), ("period_type", ASCENDING)], unique=True),
            IndexModel([("ticker", ASCENDING), ("metric_type", ASCENDING), ("date", DESCENDING)]),
        ]
    },
    PRICE_HISTORY_COLLECTION: {
        "schema": PRICE_HISTORY_SCHEMA,
        "indexes": [
            IndexModel([("ticker", ASCENDING), ("date", DESCENDING)], unique=True),
            IndexModel([("date", DESCENDING)]),
        ]
    },
    VALUATION_MODELS_COLLECTION: {
        "schema": VALUATION_MODELS_SCHEMA,
        "indexes": [
            IndexModel([("ticker", ASCENDING), ("model_type", ASCENDING), ("date", DESCENDING), ("scenario", ASCENDING)], unique=True),
            IndexModel([("ticker", ASCENDING), ("date", DESCENDING)]),
        ]
    },
    NEWS_SENTIMENT_COLLECTION: {
        "schema": NEWS_SENTIMENT_SCHEMA,
        "indexes": [
            IndexModel([("ticker", ASCENDING), ("date", DESCENDING)]),
            IndexModel([("sentiment_score", DESCENDING)]),
            IndexModel([("impact_score", DESCENDING)]),
            IndexModel([("title", TEXT), ("content", TEXT)]),
        ]
    },
    ANALYSIS_REPORTS_COLLECTION: {
        "schema": ANALYSIS_REPORTS_SCHEMA,
        "indexes": [
            IndexModel([("ticker", ASCENDING), ("date", DESCENDING), ("report_type", ASCENDING)], unique=True),
            IndexModel([("ticker", ASCENDING), ("date", DESCENDING)]),
        ]
    },
}


def setup_database():
    try:
        db = mongo_client.get_database()
        
        existing_collections = db.list_collection_names()
        
        for collection_name, config in COLLECTION_CONFIGS.items():
            if collection_name not in existing_collections:
                logger.info(f"Creating collection: {collection_name}")
                db.create_collection(collection_name, **config["schema"])
            
            collection = db[collection_name]
            for index in config["indexes"]:
                logger.info(f"Creating index for {collection_name}: {index.document}")
                collection.create_indexes([index])
                
        logger.info("Database setup completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        return False