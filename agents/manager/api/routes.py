from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from .auth import Token, User, authenticate_user, create_access_token, get_current_active_user
from ..database.schema import Task, StockAnalysis, TradeDecision, Report, TaskType, AnalysisType, TaskStatus
from ..database.operations import TaskOperations, AnalysisOperations, DecisionOperations, ReportOperations
from ..database.mongo_client import get_db_client
from ..database.operations import _convert_id
from ..config import settings

api_router = APIRouter()

@api_router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

class TaskCreate:
    class Analysis(BaseModel):
        stock_symbol: str
        analysis_type: str
        time_frame: Optional[str] = "1y"
        
    class Report(BaseModel):
        stock_symbol: str
        analysis_id: Optional[str] = None
        format: Optional[str] = "html"
        
    class Decision(BaseModel):
        stock_symbol: str
        analysis_id: Optional[str] = None
        parameters: Dict[str, Any] = {}

@api_router.post("/tasks/analysis", response_model=Task)
async def create_analysis_task(
    analysis: TaskCreate.Analysis,
    current_user: User = Depends(get_current_active_user)
):
    task = Task(
        type=TaskType.ANALYSIS,
        stock_symbol=analysis.stock_symbol,
        analysis_type=analysis.analysis_type,
        parameters={"time_frame": analysis.time_frame}
    )
    
    return TaskOperations.create_task(task)

@api_router.post("/tasks/report", response_model=Task)
async def create_report_task(
    report: TaskCreate.Report,
    current_user: User = Depends(get_current_active_user)
):
    task = Task(
        type=TaskType.REPORT,
        stock_symbol=report.stock_symbol,
        analysis_type=AnalysisType.COMBINED,
        parameters={
            "analysis_id": report.analysis_id,
            "format": report.format
        }
    )
    
    return TaskOperations.create_task(task)

@api_router.post("/tasks/decision", response_model=Task)
async def create_decision_task(
    decision: TaskCreate.Decision,
    current_user: User = Depends(get_current_active_user)
):
    task = Task(
        type=TaskType.DECISION,
        stock_symbol=decision.stock_symbol,
        analysis_type=AnalysisType.COMBINED,
        parameters={
            "analysis_id": decision.analysis_id,
            **decision.parameters
        }
    )
    
    return TaskOperations.create_task(task)

@api_router.get("/tasks/{task_id}", response_model=Task)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    task = TaskOperations.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task

@api_router.get("/tasks/status/{status}", response_model=List[Task])
async def get_tasks_by_status(
    status: str,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user)
):
    if status == TaskStatus.PENDING:
        return TaskOperations.get_pending_tasks(limit)
    
    db = get_db_client()
    tasks = list(db.tasks.find(
        {"status": status},
        sort=[("updated_at", -1)],
        limit=limit
    ))
    
    return [Task(**_convert_id(task)) for task in tasks]

@api_router.get("/analysis/{analysis_id}", response_model=StockAnalysis)
async def get_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user)
):
    analysis = AnalysisOperations.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis

@api_router.get("/analysis/latest/{stock_symbol}/{analysis_type}", response_model=StockAnalysis)
async def get_latest_analysis(
    stock_symbol: str,
    analysis_type: str,
    current_user: User = Depends(get_current_active_user)
):
    analysis = AnalysisOperations.get_latest_analysis(stock_symbol, analysis_type)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis

@api_router.get("/decisions/{decision_id}", response_model=TradeDecision)
async def get_decision(
    decision_id: str,
    current_user: User = Depends(get_current_active_user)
):
    decision = DecisionOperations.get_decision(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    return decision

@api_router.get("/decisions/latest/{stock_symbol}", response_model=TradeDecision)
async def get_latest_decision(
    stock_symbol: str,
    current_user: User = Depends(get_current_active_user)
):
    decision = DecisionOperations.get_latest_decision(stock_symbol)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    return decision

@api_router.get("/reports/{report_id}", response_model=Report)
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_active_user)
):
    report = ReportOperations.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report

@api_router.get("/reports/by-analysis/{analysis_id}", response_model=Report)
async def get_report_by_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user)
):
    report = ReportOperations.get_report_by_analysis(analysis_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report