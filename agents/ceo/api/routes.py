from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from .auth import Token, User, authenticate_user, create_access_token, get_current_active_user
from ..services.trading_engine import TradingEngine
from ..models.trading_plan import TradingPlan, StockAnalysis, TradeAction
from ..config import settings

api_router = APIRouter()
trading_engine = TradingEngine()

class StartTradingRequest(BaseModel):
    portfolio_id: str
    stocks: Optional[List[str]] = None
    budget: Optional[float] = None

class TradingResponse(BaseModel):
    trading_plan_id: str
    status: str
    message: str

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

@api_router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@api_router.post("/trading/start", response_model=TradingResponse)
async def start_trading(
    request: StartTradingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    try:
        trading_plan = await trading_engine.generate_trading_plan(
            portfolio_id=request.portfolio_id,
            stocks=request.stocks,
            budget=request.budget
        )
        
        background_tasks.add_task(
            trading_engine.execute_trading_plan,
            trading_plan
        )
        
        return TradingResponse(
            trading_plan_id=trading_plan.id or "temp_id",
            status="initiated",
            message=f"Trading plan initiated with {len(trading_plan.target_stocks)} target stocks"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start trading: {str(e)}"
        )

@api_router.get("/trading/plan/{trading_plan_id}", response_model=TradingPlan)
async def get_trading_plan(
    trading_plan_id: str,
    current_user: User = Depends(get_current_active_user)
):
    # In a real implementation, this would retrieve the trading plan from a database
    # For now, we'll raise an exception since we don't have a persistence layer
    raise HTTPException(
        status_code=501,
        detail="This endpoint is not yet implemented. Data persistence layer is required."
    )