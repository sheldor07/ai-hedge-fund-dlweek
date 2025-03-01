from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

class Position(BaseModel):
    symbol: str
    quantity: float
    avg_price: float
    current_price: Optional[float] = None
    value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_percent: Optional[float] = None
    sector: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.now)

class Trade(BaseModel):
    id: Optional[str] = None
    symbol: str
    quantity: float
    price: float
    trade_type: str  # buy or sell
    timestamp: datetime = Field(default_factory=datetime.now)
    executed_by: str

class Portfolio(BaseModel):
    id: Optional[str] = None
    name: str
    cash: float
    positions: List[Position] = []
    total_value: Optional[float] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.now)
    trade_history: List[Trade] = []

class HedgeFund(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    portfolio_id: str
    aum: float  # Assets Under Management
    inception_date: datetime
    performance: Dict[str, Any] = {}
    metrics: Dict[str, Any] = {}
    last_updated: datetime = Field(default_factory=datetime.now)