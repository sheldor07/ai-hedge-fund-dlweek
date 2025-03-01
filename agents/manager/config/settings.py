import os
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    APP_NAME: str = "ManagerAgent"
    
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "hedge_fund")
    
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    FUNDAMENTAL_ANALYSIS_API_URL: str = os.getenv("FUNDAMENTAL_ANALYSIS_API_URL", "http://localhost:8001")
    TECHNICAL_ANALYSIS_API_URL: str = os.getenv("TECHNICAL_ANALYSIS_API_URL", "http://localhost:8002")
    
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "secret_key")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    ROOT_DIR: Path = Path(__file__).parent.parent
    LOGS_DIR: Path = ROOT_DIR / "logs"
    REPORTS_DIR: Path = ROOT_DIR / "reports"
    GENERATED_REPORTS_DIR: Path = REPORTS_DIR / "generated"
    TEMPLATES_DIR: Path = REPORTS_DIR / "templates"
    
    def __init__(self, **data):
        super().__init__(**data)
        
        os.makedirs(self.LOGS_DIR, exist_ok=True)
        os.makedirs(self.GENERATED_REPORTS_DIR, exist_ok=True)