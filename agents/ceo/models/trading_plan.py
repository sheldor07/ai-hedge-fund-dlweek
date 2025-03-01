from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

class TradeAction(BaseModel):
    symbol: str
    action: str  # BUY, SELL, HOLD
    quantity: Optional[float] = None
    price_limit: Optional[float] = None
    confidence: float
    rationale: str
    status: str = "pending"  # pending, executed, failed
    execution_details: Optional[Dict[str, Any]] = None
    
class StockAnalysis(BaseModel):
    symbol: str
    current_price: Optional[float] = None
    fundamental_analysis: Optional[Dict[str, Any]] = None
    technical_analysis: Optional[Dict[str, Any]] = None
    recommendation: Optional[str] = None
    confidence: Optional[float] = None
    analysis_id: Optional[str] = None
    task_id: Optional[str] = None
    
class TradingPlan(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    start_date: datetime = Field(default_factory=datetime.now)
    portfolio_id: str
    budget: float
    target_sectors: List[str] = []
    excluded_sectors: List[str] = []
    target_stocks: List[str] = []
    excluded_stocks: List[str] = []
    risk_profile: str = "moderate"  # conservative, moderate, aggressive
    max_allocation_per_position: float = 0.1  # as a percentage of total budget
    analyses: List[StockAnalysis] = []
    actions: List[TradeAction] = []
    status: str = "draft"  # draft, in_progress, completed, failed
    result: Optional[Dict[str, Any]] = None
    
    class Config:
        arbitrary_types_allowed = True