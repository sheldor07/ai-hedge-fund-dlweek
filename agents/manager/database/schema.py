from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

class TaskStatus:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskType:
    ANALYSIS = "analysis"
    REPORT = "report"
    DECISION = "decision"

class AnalysisType:
    FUNDAMENTAL = "fundamental"
    TECHNICAL = "technical"
    COMBINED = "combined"

class Task(BaseModel):
    id: Optional[str] = None
    type: str
    stock_symbol: str
    analysis_type: str
    parameters: Dict[str, Any] = {}
    status: str = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class StockAnalysis(BaseModel):
    id: Optional[str] = None
    stock_symbol: str
    analysis_type: str
    fundamental_data: Optional[Dict[str, Any]] = None
    technical_data: Optional[Dict[str, Any]] = None
    combined_analysis: Optional[Dict[str, Any]] = None
    report_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class TradeDecision(BaseModel):
    id: Optional[str] = None
    stock_symbol: str
    recommendation: str
    confidence: float
    analysis_id: str
    explanation: str
    created_at: datetime = Field(default_factory=datetime.now)

class Report(BaseModel):
    id: Optional[str] = None
    stock_symbol: str
    analysis_id: str
    content: str
    format: str
    created_at: datetime = Field(default_factory=datetime.now)