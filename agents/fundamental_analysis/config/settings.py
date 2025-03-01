import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv(
    "MONGODB_URI", 
    "mongodb+srv://shrivardhangoenka:admin12345@cluster0.azmqa.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "stock_analyzer")

SEC_API_KEY = os.getenv("SEC_API_KEY", "")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")  
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "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")

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "your-secret-key-for-development")
API_ALGORITHM = "HS256"
API_TOKEN_EXPIRE_MINUTES = 30

DEFAULT_PRICE_HISTORY_YEARS = 5
DEFAULT_FINANCIAL_HISTORY_YEARS = 5
SEC_FILING_TYPES = ["10-K", "10-Q", "8-K"]
USER_AGENT = "StockAnalyzer/0.1.0 (contact@example.com)"

DCF_DEFAULT_PERIODS = 5  
DCF_DEFAULT_TERMINAL_GROWTH = 0.025  
DCF_DEFAULT_DISCOUNT_RATE = 0.10  

CACHE_EXPIRY = 3600  

REPORT_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", "templates")

USE_MOCK_DATA_ON_FAILURE = os.getenv("USE_MOCK_DATA_ON_FAILURE", "True").lower() == "true"

LLM_MODEL = os.getenv("LLM_MODEL", "claude-3-opus-20240229")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4000"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))