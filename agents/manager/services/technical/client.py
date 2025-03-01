import logging
import httpx
from typing import Dict, Any, Optional, List
from ...config import settings

logger = logging.getLogger(settings.APP_NAME)

class TechnicalClient:
    def __init__(self):
        self.base_url = settings.TECHNICAL_ANALYSIS_API_URL
    
    async def get_technical_analysis(self, stock_symbol: str, timeframe: str = "60d") -> Dict[str, Any]:
        logger.info(f"Requesting technical analysis for {stock_symbol} with timeframe {timeframe}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/analysis",
                    json={
                        "symbol": stock_symbol,
                        "timeframe": timeframe
                    },
                    timeout=60.0
                )
                
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error occurred while fetching technical analysis: {str(e)}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error occurred while fetching technical analysis: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error occurred while fetching technical analysis: {str(e)}")
                raise
    
    async def get_prediction(self, stock_symbol: str, model_type: str = "lstm") -> Dict[str, Any]:
        logger.info(f"Requesting prediction for {stock_symbol} using {model_type} model")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/predict",
                    json={
                        "symbol": stock_symbol,
                        "model": model_type,
                        "days": 5
                    },
                    timeout=60.0
                )
                
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error occurred while fetching prediction: {str(e)}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error occurred while fetching prediction: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error occurred while fetching prediction: {str(e)}")
                raise
    
    async def get_indicators(self, stock_symbol: str, indicators: List[str]) -> Dict[str, Any]:
        logger.info(f"Requesting indicators {indicators} for {stock_symbol}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/indicators",
                    json={
                        "symbol": stock_symbol,
                        "indicators": indicators
                    },
                    timeout=60.0
                )
                
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error occurred while fetching indicators: {str(e)}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error occurred while fetching indicators: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error occurred while fetching indicators: {str(e)}")
                raise