import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from bson import ObjectId
from ..database import get_db_client
from ..models.portfolio import Portfolio, Position, Trade, HedgeFund
from ..config import settings

logger = logging.getLogger(settings.APP_NAME)

def _convert_id(item):
    if item and "_id" in item:
        item["id"] = str(item["_id"])
        del item["_id"]
    return item

class PortfolioService:
    @staticmethod
    def get_portfolio(portfolio_id: str) -> Optional[Portfolio]:
        db = get_db_client()
        portfolio_data = db.portfolios.find_one({"_id": ObjectId(portfolio_id)})
        
        if not portfolio_data:
            return None
        
        portfolio_data = _convert_id(portfolio_data)
        return Portfolio(**portfolio_data)
    
    @staticmethod
    def get_all_portfolios() -> List[Portfolio]:
        db = get_db_client()
        portfolios = list(db.portfolios.find())
        
        return [Portfolio(**_convert_id(p)) for p in portfolios]
    
    @staticmethod
    def get_positions(portfolio_id: str) -> List[Position]:
        portfolio = PortfolioService.get_portfolio(portfolio_id)
        if not portfolio:
            return []
        
        return portfolio.positions
    
    @staticmethod
    def get_position_by_symbol(portfolio_id: str, symbol: str) -> Optional[Position]:
        portfolio = PortfolioService.get_portfolio(portfolio_id)
        if not portfolio:
            return None
        
        for position in portfolio.positions:
            if position.symbol == symbol:
                return position
        
        return None
    
    @staticmethod
    def get_trade_history(portfolio_id: str, limit: int = 50) -> List[Trade]:
        db = get_db_client()
        trades = list(db.trades.find(
            {"portfolio_id": portfolio_id},
            sort=[("timestamp", -1)],
            limit=limit
        ))
        
        return [Trade(**_convert_id(t)) for t in trades]
    
    @staticmethod
    def get_hedge_fund() -> Optional[HedgeFund]:
        db = get_db_client()
        fund_data = db.hedge_funds.find_one()
        
        if not fund_data:
            return None
        
        fund_data = _convert_id(fund_data)
        return HedgeFund(**fund_data)
    
    @staticmethod
    def get_fund_performance(time_period: str = "1y") -> Dict[str, Any]:
        db = get_db_client()
        fund = db.hedge_funds.find_one()
        
        if not fund or "performance" not in fund:
            return {}
        
        if time_period in fund["performance"]:
            return fund["performance"][time_period]
        
        return fund["performance"]
    
    @staticmethod
    def get_fund_metrics() -> Dict[str, Any]:
        db = get_db_client()
        fund = db.hedge_funds.find_one()
        
        if not fund or "metrics" not in fund:
            return {}
        
        return fund["metrics"]
    
    @staticmethod
    def get_position_sector_allocation(portfolio_id: str) -> Dict[str, float]:
        positions = PortfolioService.get_positions(portfolio_id)
        
        if not positions:
            return {}
        
        total_value = sum(p.value or 0 for p in positions)
        
        if total_value == 0:
            return {}
        
        sector_allocation = {}
        for position in positions:
            if not position.sector:
                continue
            
            sector_value = position.value or 0
            if position.sector in sector_allocation:
                sector_allocation[position.sector] += sector_value
            else:
                sector_allocation[position.sector] = sector_value
        
        return {sector: (value / total_value) * 100 for sector, value in sector_allocation.items()}