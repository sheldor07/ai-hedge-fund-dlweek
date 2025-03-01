import logging
import httpx
from typing import Dict, Any, Optional
from ...config import settings

logger = logging.getLogger(settings.APP_NAME)

class FundamentalClient:
    def __init__(self):
        self.base_url = settings.FUNDAMENTAL_ANALYSIS_API_URL
        
    async def get_financial_analysis(self, stock_symbol: str, time_frame: str = "1y") -> Dict[str, Any]:
        logger.info(f"Requesting fundamental analysis for {stock_symbol} with time frame {time_frame}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/analyze",
                    json={
                        "symbol": stock_symbol,
                        "time_frame": time_frame,
                        "include_ratios": True,
                        "include_growth": True,
                        "include_valuation": True
                    },
                    timeout=60.0
                )
                
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error occurred while fetching fundamental analysis: {str(e)}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error occurred while fetching fundamental analysis: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error occurred while fetching fundamental analysis: {str(e)}")
                raise
    
    async def get_valuation(self, stock_symbol: str) -> Dict[str, Any]:
        logger.info(f"Requesting valuation for {stock_symbol}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/valuation",
                    json={
                        "symbol": stock_symbol,
                        "include_dcf": True,
                        "include_ddm": True,
                        "include_comparable": True
                    },
                    timeout=60.0
                )
                
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error occurred while fetching valuation: {str(e)}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error occurred while fetching valuation: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error occurred while fetching valuation: {str(e)}")
                raise
    
    async def get_risk_assessment(self, stock_symbol: str) -> Dict[str, Any]:
        logger.info(f"Requesting risk assessment for {stock_symbol}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/risk",
                    json={
                        "symbol": stock_symbol,
                        "include_volatility": True,
                        "include_scenarios": True
                    },
                    timeout=60.0
                )
                
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error occurred while fetching risk assessment: {str(e)}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error occurred while fetching risk assessment: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error occurred while fetching risk assessment: {str(e)}")
                raise