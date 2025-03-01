"""
Configuration settings module for the stock analyzer application.
Loads environment variables and provides configuration for various services.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv(
    "MONGODB_URI", 
    "mongodb+srv://shrivardhangoenka:admin12345@cluster0.azmqa.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "stock_analyzer")

# API Keys
SEC_API_KEY = os.getenv("SEC_API_KEY", "")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")  # Using demo key as fallback
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "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")

# API Configuration
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "your-secret-key-for-development")
API_ALGORITHM = "HS256"
API_TOKEN_EXPIRE_MINUTES = 30

# Data collection settings
DEFAULT_PRICE_HISTORY_YEARS = 5
DEFAULT_FINANCIAL_HISTORY_YEARS = 5
SEC_FILING_TYPES = ["10-K", "10-Q", "8-K"]
USER_AGENT = "StockAnalyzer/0.1.0 (contact@example.com)"

# Analysis settings
DCF_DEFAULT_PERIODS = 5  # 5 years of projection
DCF_DEFAULT_TERMINAL_GROWTH = 0.025  # 2.5% terminal growth rate
DCF_DEFAULT_DISCOUNT_RATE = 0.10  # 10% discount rate

# Cache settings
CACHE_EXPIRY = 3600  # 1 hour

# Report settings
REPORT_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", "templates")

# Use mock data when API fails
USE_MOCK_DATA_ON_FAILURE = os.getenv("USE_MOCK_DATA_ON_FAILURE", "True").lower() == "true"

# LLM settings
LLM_MODEL = os.getenv("LLM_MODEL", "claude-3-opus-20240229")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4000"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))