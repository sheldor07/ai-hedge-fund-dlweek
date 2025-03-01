import os
import logging
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    APP_NAME: str = "CEOAgent"
    
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    MANAGER_API_URL: str = os.getenv("MANAGER_API_URL", "http://localhost:8000")
    PORTFOLIO_MANAGER_API_URL: str = os.getenv("PORTFOLIO_MANAGER_API_URL", "http://localhost:8003")
    
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "secret_key")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    MANAGER_API_USERNAME: str = os.getenv("MANAGER_API_USERNAME", "admin")
    MANAGER_API_PASSWORD: str = os.getenv("MANAGER_API_PASSWORD", "adminpassword")
    
    PORTFOLIO_API_USERNAME: str = os.getenv("PORTFOLIO_API_USERNAME", "admin")
    PORTFOLIO_API_PASSWORD: str = os.getenv("PORTFOLIO_API_PASSWORD", "adminpassword")
    
    DEFAULT_TRADING_BUDGET: float = float(os.getenv("DEFAULT_TRADING_BUDGET", "100000"))  # Default budget per trading session
    MAX_STOCKS_TO_ANALYZE: int = int(os.getenv("MAX_STOCKS_TO_ANALYZE", "10"))  # Maximum number of stocks to analyze
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    def setup_logging(self):
        numeric_level = getattr(logging, self.LOG_LEVEL.upper(), None)
        if not isinstance(numeric_level, int):
            numeric_level = logging.INFO
            
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        return logging.getLogger(self.APP_NAME)