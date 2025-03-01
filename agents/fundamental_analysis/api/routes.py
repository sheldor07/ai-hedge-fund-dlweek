"""
API routes module.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from api.auth import (
    Token, User, authenticate_user, create_access_token, get_current_active_user,
    register_user, API_TOKEN_EXPIRE_MINUTES
)
from config.settings import API_HOST, API_PORT
from data.collectors.edgar_collector import EDGARCollector
from data.collectors.price_collector import PriceDataCollector
from data.collectors.news_collector import NewsCollector
from data.collectors.macro_collector import MacroCollector
from data.parsers.financial_parser import FinancialStatementParser
from analysis.financial.ratio_analyzer import RatioAnalyzer
from analysis.financial.growth_analyzer import GrowthAnalyzer
from analysis.valuation.dcf_model import DCFModel
from analysis.valuation.ddm_model import DDMModel
from analysis.valuation.comparable import ComparableAnalysis
from analysis.risk.volatility import VolatilityAnalyzer
from analysis.risk.scenario import ScenarioAnalysis
from reports.generator import ReportGenerator
from database.operations import db_ops

logger = logging.getLogger("stock_analyzer.api")

# Create API app
app = FastAPI(
    title="Stock Analyzer API",
    description="API for fundamental analysis of US stocks",
    version="1.0.0"
)

# Create routers
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
data_router = APIRouter(prefix="/data", tags=["Data Collection"])
analysis_router = APIRouter(prefix="/analysis", tags=["Analysis"])
report_router = APIRouter(prefix="/reports", tags=["Reports"])
screening_router = APIRouter(prefix="/screening", tags=["Screening"])


# Models for API
class UserRegistration(BaseModel):
    """User registration model."""
    username: str
    email: str
    password: str


class TickerRequest(BaseModel):
    """Ticker request model."""
    ticker: str


class MultiTickerRequest(BaseModel):
    """Multi-ticker request model."""
    tickers: List[str]


class ScreeningCriteria(BaseModel):
    """Screening criteria model."""
    sector: Optional[str] = None
    industry: Optional[str] = None
    min_market_cap: Optional[float] = None
    max_market_cap: Optional[float] = None
    min_pe_ratio: Optional[float] = None
    max_pe_ratio: Optional[float] = None
    min_dividend_yield: Optional[float] = None
    min_revenue_growth: Optional[float] = None
    min_roe: Optional[float] = None
    max_debt_to_equity: Optional[float] = None


# Authentication routes
@auth_router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Get an access token.
    
    Args:
        form_data (OAuth2PasswordRequestForm, optional): The form data. Defaults to Depends().
        
    Raises:
        HTTPException: If authentication fails.
        
    Returns:
        Token: The access token.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=API_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_new_user(user_data: UserRegistration):
    """
    Register a new user.
    
    Args:
        user_data (UserRegistration): The user data.
        
    Raises:
        HTTPException: If registration fails.
        
    Returns:
        dict: A success message.
    """
    success = register_user(user_data.username, user_data.email, user_data.password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed. Username may already exist."
        )
    return {"message": "User registered successfully"}


@auth_router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get the current user.
    
    Args:
        current_user (User, optional): The current user. Defaults to Depends(get_current_active_user).
        
    Returns:
        User: The current user.
    """
    return current_user


# Data collection routes
@data_router.post("/collect/prices")
async def collect_price_data(request: TickerRequest, current_user: User = Depends(get_current_active_user)):
    """
    Collect price data for a ticker.
    
    Args:
        request (TickerRequest): The ticker request.
        current_user (User, optional): The current user. Defaults to Depends(get_current_active_user).
        
    Returns:
        dict: A success message.
    """
    try:
        collector = PriceDataCollector()
        success = collector.collect_price_history(request.ticker)
        
        if success:
            # Update technical indicators
            collector.update_technical_indicators(request.ticker)
            return {"message": f"Successfully collected price data for {request.ticker}"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to collect price data for {request.ticker}"
            )
    except Exception as e:
        logger.error(f"Error collecting price data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error collecting price data: {str(e)}"
        )


@data_router.post("/collect/financials")
async def collect_financial_data(request: TickerRequest, current_user: User = Depends(get_current_active_user)):
    """
    Collect financial data for a ticker.
    
    Args:
        request (TickerRequest): The ticker request.
        current_user (User, optional): The current user. Defaults to Depends(get_current_active_user).
        
    Returns:
        dict: A success message.
    """
    try:
        collector = EDGARCollector()
        
        # First get company info
        company_info = collector.get_company_info(request.ticker)
        
        if not company_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not find company information for {request.ticker}"
            )
        
        # Get financial data
        annual_data = collector.get_financial_data(request.ticker, "annual")
        quarterly_data = collector.get_financial_data(request.ticker, "quarterly")
        
        if annual_data or quarterly_data:
            # Standardize the financial statements
            parser = FinancialStatementParser()
            if annual_data:
                parser.standardize_financial_statements(request.ticker, "annual")
                parser.normalize_financial_data(request.ticker, "annual")
            
            if quarterly_data:
                parser.standardize_financial_statements(request.ticker, "quarterly")
                parser.normalize_financial_data(request.ticker, "quarterly")
                
            return {"message": f"Successfully collected financial data for {request.ticker}"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to collect financial data for {request.ticker}"
            )
    except Exception as e:
        logger.error(f"Error collecting financial data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error collecting financial data: {str(e)}"
        )


@data_router.post("/collect/news")
async def collect_news_data(request: TickerRequest, days: int = 7, current_user: User = Depends(get_current_active_user)):
    """
    Collect news data for a ticker.
    
    Args:
        request (TickerRequest): The ticker request.
        days (int, optional): Number of days to collect. Defaults to 7.
        current_user (User, optional): The current user. Defaults to Depends(get_current_active_user).
        
    Returns:
        dict: A success message.
    """
    try:
        collector = NewsCollector()
        success = collector.collect_news(request.ticker, days)
        
        if success:
            return {"message": f"Successfully collected news data for {request.ticker}"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to collect news data for {request.ticker}"
            )
    except Exception as e:
        logger.error(f"Error collecting news data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error collecting news data: {str(e)}"
        )


@data_router.post("/collect/macro")
async def collect_macro_data(current_user: User = Depends(get_current_active_user)):
    """
    Collect macroeconomic data.
    
    Args:
        current_user (User, optional): The current user. Defaults to Depends(get_current_active_user).
        
    Returns:
        dict: A success message.
    """
    try:
        collector = MacroCollector()
        success = collector.collect_macro_data()
        
        if success:
            return {"message": "Successfully collected macroeconomic data"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to collect macroeconomic data"
            )
    except Exception as e:
        logger.error(f"Error collecting macro data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error collecting macro data: {str(e)}"
        )


@data_router.post("/collect/all")
async def collect_all_data(request: TickerRequest, current_user: User = Depends(get_current_active_user)):
    """
    Collect all data for a ticker.
    
    Args:
        request (TickerRequest): The ticker request.
        current_user (User, optional): The current user. Defaults to Depends(get_current_active_user).
        
    Returns:
        dict: A success message.
    """
    try:
        # Collect company and financial data
        edgar_collector = EDGARCollector()
        company_info = edgar_collector.get_company_info(request.ticker)
        
        if not company_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not find company information for {request.ticker}"
            )
        
        annual_data = edgar_collector.get_financial_data(request.ticker, "annual")
        quarterly_data = edgar_collector.get_financial_data(request.ticker, "quarterly")
        
        # Standardize financial statements
        parser = FinancialStatementParser()
        if annual_data:
            parser.standardize_financial_statements(request.ticker, "annual")
            parser.normalize_financial_data(request.ticker, "annual")
        
        if quarterly_data:
            parser.standardize_financial_statements(request.ticker, "quarterly")
            parser.normalize_financial_data(request.ticker, "quarterly")
        
        # Collect price data
        price_collector = PriceDataCollector()
        price_success = price_collector.collect_price_history(request.ticker)
        
        if price_success:
            price_collector.update_technical_indicators(request.ticker)
        
        # Collect news data
        news_collector = NewsCollector()
        news_collector.collect_news(request.ticker)
        
        return {"message": f"Successfully collected all data for {request.ticker}"}
    except Exception as e:
        logger.error(f"Error collecting all data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error collecting all data: {str(e)}"
        )


# Analysis routes
@analysis_router.post("/financial/ratios")
async def analyze_financial_ratios(request: TickerRequest, current_user: User = Depends(get_current_active_user)):
    """
    Analyze financial ratios for a ticker.
    
    Args:
        request (TickerRequest): The ticker request.
        current_user (User, optional): The current user. Defaults to Depends(get_current_active_user).
        
    Returns:
        dict: A success message.
    """
    try:
        analyzer = RatioAnalyzer()
        success = analyzer.calculate_all_ratios(request.ticker)
        
        if success:
            return {"message": f"Successfully analyzed financial ratios for {request.ticker}"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to analyze financial ratios for {request.ticker}"
            )
    except Exception as e:
        logger.error(f"Error analyzing financial ratios: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing financial ratios: {str(e)}"
        )


@analysis_router.post("/financial/growth")
async def analyze_growth(request: TickerRequest, current_user: User = Depends(get_current_active_user)):
    """
    Analyze growth metrics for a ticker.
    
    Args:
        request (TickerRequest): The ticker request.
        current_user (User, optional): The current user. Defaults to Depends(get_current_active_user).
        
    Returns:
        dict: A success message.
    """
    try:
        analyzer = GrowthAnalyzer()
        success = analyzer.calculate_growth_rates(request.ticker)
        
        if success:
            # Also forecast future growth
            analyzer.forecast_future_growth(request.ticker)
            return {"message": f"Successfully analyzed growth metrics for {request.ticker}"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to analyze growth metrics for {request.ticker}"
            )
    except Exception as e:
        logger.error(f"Error analyzing growth metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing growth metrics: {str(e)}"
        )


@analysis_router.post("/valuation/dcf")
async def run_dcf_model(request: TickerRequest, current_user: User = Depends(get_current_active_user)):
    """
    Run DCF model for a ticker.
    
    Args:
        request (TickerRequest): The ticker request.
        current_user (User, optional): The current user. Defaults to Depends(get_current_active_user).
        
    Returns:
        dict: The DCF model results.
    """
    try:
        model = DCFModel()
        result = model.build_dcf_model(request.ticker)
        
        if result and "results" in result:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to run DCF model for {request.ticker}"
            )
    except Exception as e:
        logger.error(f"Error running DCF model: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running DCF model: {str(e)}"
        )


@analysis_router.post("/valuation/ddm")
async def run_ddm_model(request: TickerRequest, current_user: User = Depends(get_current_active_user)):
    """
    Run DDM model for a ticker.
    
    Args:
        request (TickerRequest): The ticker request.
        current_user (User, optional): The current user. Defaults to Depends(get_current_active_user).
        
    Returns:
        dict: The DDM model results.
    """
    try:
        model = DDMModel()
        result = model.build_ddm_model(request.ticker)
        
        if not result or "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", f"Failed to run DDM model for {request.ticker}")
            )
            
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running DDM model: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running DDM model: {str(e)}"
        )


@analysis_router.post("/valuation/comparable")
async def run_comparable_analysis(
    request: TickerRequest, 
    peers: Optional[List[str]] = None, 
    current_user: User = Depends(get_current_active_user)
):
    """
    Run comparable company analysis for a ticker.
    
    Args:
        request (TickerRequest): The ticker request.
        peers (Optional[List[str]], optional): List of peer tickers. Defaults to None.
        current_user (User, optional): The current user. Defaults to Depends(get_current_active_user).
        
    Returns:
        dict: The comparable analysis results.
    """
    try:
        model = ComparableAnalysis()
        result = model.build_comparable_model(request.ticker, peers)
        
        if result and "metrics" in result:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to run comparable analysis for {request.ticker}"
            )
    except Exception as e:
        logger.error(f"Error running comparable analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running comparable analysis: {str(e)}"
        )


@analysis_router.post("/risk/volatility")
async def analyze_volatility(request: TickerRequest, current_user: User = Depends(get_current_active_user)):
    """
    Analyze volatility for a ticker.
    
    Args:
        request (TickerRequest): The ticker request.
        current_user (User, optional): The current user. Defaults to Depends(get_current_active_user).
        
    Returns:
        dict: The volatility metrics.
    """
    try:
        analyzer = VolatilityAnalyzer()
        metrics = analyzer.calculate_volatility_metrics(request.ticker)
        
        if metrics:
            return metrics
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to analyze volatility for {request.ticker}"
            )
    except Exception as e:
        logger.error(f"Error analyzing volatility: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing volatility: {str(e)}"
        )


@analysis_router.post("/risk/scenario")
async def run_scenario_analysis(request: TickerRequest, current_user: User = Depends(get_current_active_user)):
    """
    Run scenario analysis for a ticker.
    
    Args:
        request (TickerRequest): The ticker request.
        current_user (User, optional): The current user. Defaults to Depends(get_current_active_user).
        
    Returns:
        dict: The scenario analysis results.
    """
    try:
        analyzer = ScenarioAnalysis()
        result = analyzer.run_scenario_analysis(request.ticker)
        
        if result:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to run scenario analysis for {request.ticker}"
            )
    except Exception as e:
        logger.error(f"Error running scenario analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running scenario analysis: {str(e)}"
        )


@analysis_router.post("/risk/correlation")
async def analyze_correlation(
    request: MultiTickerRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Analyze correlation between tickers.
    
    Args:
        request (MultiTickerRequest): The multi-ticker request.
        current_user (User, optional): The current user. Defaults to Depends(get_current_active_user).
        
    Returns:
        dict: The correlation matrix.
    """
    try:
        if len(request.tickers) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 tickers are required for correlation analysis"
            )
            
        analyzer = VolatilityAnalyzer()
        matrix = analyzer.calculate_correlation_matrix(request.tickers)
        
        if matrix:
            return matrix
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to calculate correlation matrix"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing correlation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing correlation: {str(e)}"
        )


@analysis_router.post("/run_all")
async def run_all_analysis(request: TickerRequest, current_user: User = Depends(get_current_active_user)):
    """
    Run all analyses for a ticker.
    
    Args:
        request (TickerRequest): The ticker request.
        current_user (User, optional): The current user. Defaults to Depends(get_current_active_user).
        
    Returns:
        dict: A success message.
    """
    try:
        # Financial ratios
        ratio_analyzer = RatioAnalyzer()
        ratio_analyzer.calculate_all_ratios(request.ticker)
        
        # Growth metrics
        growth_analyzer = GrowthAnalyzer()
        growth_analyzer.calculate_growth_rates(request.ticker)
        growth_analyzer.forecast_future_growth(request.ticker)
        
        # Valuation models
        dcf_model = DCFModel()
        dcf_model.build_dcf_model(request.ticker)
        
        ddm_model = DDMModel()
        ddm_model.build_ddm_model(request.ticker)
        
        comparable_model = ComparableAnalysis()
        comparable_model.build_comparable_model(request.ticker)
        
        # Risk analysis
        volatility_analyzer = VolatilityAnalyzer()
        volatility_analyzer.calculate_volatility_metrics(request.ticker)
        
        scenario_analyzer = ScenarioAnalysis()
        scenario_analyzer.run_scenario_analysis(request.ticker)
        
        return {"message": f"Successfully ran all analyses for {request.ticker}"}
    except Exception as e:
        logger.error(f"Error running all analyses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running all analyses: {str(e)}"
        )


# Report routes
@report_router.post("/generate")
async def generate_report(
    request: TickerRequest, 
    report_type: str = "comprehensive",
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate a report for a ticker.
    
    Args:
        request (TickerRequest): The ticker request.
        report_type (str, optional): The type of report. Defaults to "comprehensive".
        current_user (User, optional): The current user. Defaults to Depends(get_current_active_user).
        
    Returns:
        dict: The report URL.
    """
    try:
        generator = ReportGenerator()
        report_url = generator.generate_report(request.ticker, report_type)
        
        if report_url:
            return {"report_url": report_url}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate report for {request.ticker}"
            )
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )


@report_router.get("/list")
async def list_reports(
    ticker: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    List reports.
    
    Args:
        ticker (Optional[str], optional): The ticker to filter by. Defaults to None.
        current_user (User, optional): The current user. Defaults to Depends(get_current_active_user).
        
    Returns:
        list: The list of reports.
    """
    try:
        query = {}
        if ticker:
            query["ticker"] = ticker.upper()
            
        reports = db_ops.find_many(
            "analysis_reports",
            query,
            sort=[("date", -1)]
        )
        
        return [
            {
                "ticker": report["ticker"],
                "date": report["date"],
                "report_type": report["report_type"],
                "url": report.get("report_url", "")
            }
            for report in reports
        ]
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing reports: {str(e)}"
        )


# Screening routes
@screening_router.post("/screen")
async def screen_stocks(
    criteria: ScreeningCriteria,
    current_user: User = Depends(get_current_active_user)
):
    """
    Screen stocks based on criteria.
    
    Args:
        criteria (ScreeningCriteria): The screening criteria.
        current_user (User, optional): The current user. Defaults to Depends(get_current_active_user).
        
    Returns:
        list: The list of matching stocks.
    """
    try:
        # Build the query based on criteria
        query = {}
        
        # Sector and industry criteria (from companies collection)
        company_query = {}
        if criteria.sector:
            company_query["sector"] = criteria.sector
        if criteria.industry:
            company_query["industry"] = criteria.industry
            
        # Get matching companies
        matching_companies = db_ops.find_many("companies", company_query)
        
        if not matching_companies:
            return []
            
        matching_tickers = [company["ticker"] for company in matching_companies]
        
        # Market cap criteria
        if criteria.min_market_cap or criteria.max_market_cap:
            market_cap_query = {"ticker": {"$in": matching_tickers}}
            
            # Get latest price data and financial statements to calculate market cap
            price_data = {}
            for ticker in matching_tickers:
                latest_price = db_ops.find_one(
                    "price_history",
                    {"ticker": ticker},
                    {"sort": [("date", -1)]}
                )
                
                if latest_price:
                    price_data[ticker] = latest_price["close"]
            
            # Get shares outstanding from financial statements
            shares_data = {}
            for ticker in matching_tickers:
                latest_statement = db_ops.find_one(
                    "financial_statements",
                    {"ticker": ticker, "period_type": "annual"},
                    {"sort": [("period_end_date", -1)]}
                )
                
                if latest_statement and "income_statement_standardized" in latest_statement:
                    income_stmt = latest_statement["income_statement_standardized"]
                    shares_data[ticker] = income_stmt.get("shares_outstanding_diluted", 0)
            
            # Calculate market cap and filter
            filtered_tickers = []
            for ticker in matching_tickers:
                if ticker in price_data and ticker in shares_data:
                    market_cap = price_data[ticker] * shares_data[ticker]
                    
                    if criteria.min_market_cap and market_cap < criteria.min_market_cap:
                        continue
                    if criteria.max_market_cap and market_cap > criteria.max_market_cap:
                        continue
                        
                    filtered_tickers.append(ticker)
            
            matching_tickers = filtered_tickers
        
        # Financial metrics criteria
        if any([
            criteria.min_pe_ratio, criteria.max_pe_ratio, criteria.min_dividend_yield,
            criteria.min_revenue_growth, criteria.min_roe, criteria.max_debt_to_equity
        ]):
            # Filter by valuation metrics
            if criteria.min_pe_ratio or criteria.max_pe_ratio:
                filtered_tickers = []
                
                for ticker in matching_tickers:
                    valuation_metrics = db_ops.find_one(
                        "financial_metrics",
                        {
                            "ticker": ticker,
                            "metric_type": "valuation",
                            "period_type": "annual"
                        },
                        {"sort": [("date", -1)]}
                    )
                    
                    if valuation_metrics and "metrics" in valuation_metrics:
                        pe_ratio = valuation_metrics["metrics"].get("pe_ratio", 0)
                        
                        if criteria.min_pe_ratio and pe_ratio < criteria.min_pe_ratio:
                            continue
                        if criteria.max_pe_ratio and pe_ratio > criteria.max_pe_ratio:
                            continue
                            
                        filtered_tickers.append(ticker)
                
                matching_tickers = filtered_tickers
            
            # Filter by dividend yield
            if criteria.min_dividend_yield:
                filtered_tickers = []
                
                for ticker in matching_tickers:
                    valuation_metrics = db_ops.find_one(
                        "financial_metrics",
                        {
                            "ticker": ticker,
                            "metric_type": "valuation",
                            "period_type": "annual"
                        },
                        {"sort": [("date", -1)]}
                    )
                    
                    if valuation_metrics and "metrics" in valuation_metrics:
                        dividend_yield = valuation_metrics["metrics"].get("dividend_yield", 0)
                        
                        if dividend_yield >= criteria.min_dividend_yield:
                            filtered_tickers.append(ticker)
                
                matching_tickers = filtered_tickers
            
            # Filter by revenue growth
            if criteria.min_revenue_growth:
                filtered_tickers = []
                
                for ticker in matching_tickers:
                    growth_metrics = db_ops.find_one(
                        "financial_metrics",
                        {
                            "ticker": ticker,
                            "metric_type": "growth",
                            "period_type": "annual"
                        },
                        {"sort": [("date", -1)]}
                    )
                    
                    if growth_metrics and "metrics" in growth_metrics:
                        if "yoy" in growth_metrics["metrics"]:
                            revenue_growth = growth_metrics["metrics"]["yoy"].get("revenue", 0)
                            
                            if revenue_growth >= criteria.min_revenue_growth:
                                filtered_tickers.append(ticker)
                
                matching_tickers = filtered_tickers
            
            # Filter by ROE
            if criteria.min_roe:
                filtered_tickers = []
                
                for ticker in matching_tickers:
                    profitability_metrics = db_ops.find_one(
                        "financial_metrics",
                        {
                            "ticker": ticker,
                            "metric_type": "profitability",
                            "period_type": "annual"
                        },
                        {"sort": [("date", -1)]}
                    )
                    
                    if profitability_metrics and "metrics" in profitability_metrics:
                        roe = profitability_metrics["metrics"].get("return_on_equity", 0)
                        
                        if roe >= criteria.min_roe:
                            filtered_tickers.append(ticker)
                
                matching_tickers = filtered_tickers
            
            # Filter by debt to equity
            if criteria.max_debt_to_equity:
                filtered_tickers = []
                
                for ticker in matching_tickers:
                    solvency_metrics = db_ops.find_one(
                        "financial_metrics",
                        {
                            "ticker": ticker,
                            "metric_type": "solvency",
                            "period_type": "annual"
                        },
                        {"sort": [("date", -1)]}
                    )
                    
                    if solvency_metrics and "metrics" in solvency_metrics:
                        debt_to_equity = solvency_metrics["metrics"].get("debt_to_equity", 0)
                        
                        if debt_to_equity <= criteria.max_debt_to_equity:
                            filtered_tickers.append(ticker)
                
                matching_tickers = filtered_tickers
        
        # Get full company details for matching tickers
        results = []
        for ticker in matching_tickers:
            company = db_ops.find_one("companies", {"ticker": ticker})
            
            if company:
                # Get latest price
                latest_price = db_ops.find_one(
                    "price_history",
                    {"ticker": ticker},
                    {"sort": [("date", -1)]}
                )
                
                price = latest_price.get("close", 0) if latest_price else 0
                
                results.append({
                    "ticker": ticker,
                    "name": company.get("name", ""),
                    "sector": company.get("sector", ""),
                    "industry": company.get("industry", ""),
                    "price": price
                })
        
        return results
    except Exception as e:
        logger.error(f"Error screening stocks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error screening stocks: {str(e)}"
        )


# Register routers
app.include_router(auth_router)
app.include_router(data_router)
app.include_router(analysis_router)
app.include_router(report_router)
app.include_router(screening_router)


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    
    Returns:
        dict: A welcome message.
    """
    return {"message": "Welcome to the Stock Analyzer API"}


def start_api():
    """Start the API server."""
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)