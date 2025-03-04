import os
import logging
import logging.config
from datetime import datetime

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

current_date = datetime.now().strftime("%Y-%m-%d")
LOG_FILENAME = os.path.join(LOGS_DIR, f"stock_analyzer_{current_date}.log")

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": LOG_FILENAME,
            "maxBytes": 10485760,  
            "backupCount": 5,
            "encoding": "utf8",
        },
    },
    "loggers": {
        "": {  
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": True
        },
        "stock_analyzer": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False
        },
        "stock_analyzer.data": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False
        },
        "stock_analyzer.analysis": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False
        },
        "stock_analyzer.database": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False
        },
        "stock_analyzer.api": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False
        },
    }
}


def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger("stock_analyzer")
    logger.info("Logging configured successfully")
    return logger