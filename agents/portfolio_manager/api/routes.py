from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from .auth import Token, User, authenticate_user, create_access_token, get_current_active_user
from ..models.portfolio import Portfolio, Position, Trade, HedgeFund
from ..services.portfolio_service import PortfolioService
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

@api_router.get("/portfolios", response_model=List[Portfolio])
async def get_portfolios(current_user: User = Depends(get_current_active_user)):
    portfolios = PortfolioService.get_all_portfolios()
    return portfolios

@api_router.get("/portfolios/{portfolio_id}", response_model=Portfolio)
async def get_portfolio(
    portfolio_id: str,
    current_user: User = Depends(get_current_active_user)
):
    portfolio = PortfolioService.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio

@api_router.get("/portfolios/{portfolio_id}/positions", response_model=List[Position])
async def get_positions(
    portfolio_id: str,
    current_user: User = Depends(get_current_active_user)
):
    positions = PortfolioService.get_positions(portfolio_id)
    return positions

@api_router.get("/portfolios/{portfolio_id}/positions/{symbol}", response_model=Position)
async def get_position(
    portfolio_id: str,
    symbol: str,
    current_user: User = Depends(get_current_active_user)
):
    position = PortfolioService.get_position_by_symbol(portfolio_id, symbol)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position

@api_router.get("/portfolios/{portfolio_id}/trades", response_model=List[Trade])
async def get_trades(
    portfolio_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user)
):
    trades = PortfolioService.get_trade_history(portfolio_id, limit)
    return trades

@api_router.get("/hedge-fund", response_model=HedgeFund)
async def get_hedge_fund(current_user: User = Depends(get_current_active_user)):
    fund = PortfolioService.get_hedge_fund()
    if not fund:
        raise HTTPException(status_code=404, detail="Hedge fund information not found")
    return fund

@api_router.get("/hedge-fund/performance", response_model=Dict[str, Any])
async def get_fund_performance(
    time_period: str = "1y",
    current_user: User = Depends(get_current_active_user)
):
    performance = PortfolioService.get_fund_performance(time_period)
    return performance

@api_router.get("/hedge-fund/metrics", response_model=Dict[str, Any])
async def get_fund_metrics(current_user: User = Depends(get_current_active_user)):
    metrics = PortfolioService.get_fund_metrics()
    return metrics

@api_router.get("/portfolios/{portfolio_id}/sector-allocation", response_model=Dict[str, float])
async def get_sector_allocation(
    portfolio_id: str,
    current_user: User = Depends(get_current_active_user)
):
    allocation = PortfolioService.get_position_sector_allocation(portfolio_id)
    return allocation