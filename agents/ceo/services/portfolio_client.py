import logging
import httpx
from typing import Dict, List, Any, Optional
from ..config import settings

logger = logging.getLogger(settings.APP_NAME)

class PortfolioClient:
    def __init__(self):
        self.base_url = settings.PORTFOLIO_MANAGER_API_URL
        self.token = None
    
    async def authenticate(self):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/token",
                    data={
                        "username": settings.PORTFOLIO_API_USERNAME,
                        "password": settings.PORTFOLIO_API_PASSWORD
                    },
                    timeout=10.0
                )
                
                response.raise_for_status()
                data = response.json()
                self.token = data["access_token"]
                logger.info("Successfully authenticated with Portfolio API")
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error during Portfolio API authentication: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error during Portfolio API authentication: {str(e)}")
                raise
    
    async def get_portfolios(self) -> List[Dict[str, Any]]:
        if not self.token:
            await self.authenticate()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/portfolios",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10.0
                )
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error getting portfolios: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error getting portfolios: {str(e)}")
                raise
    
    async def get_portfolio(self, portfolio_id: str) -> Dict[str, Any]:
        if not self.token:
            await self.authenticate()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/portfolios/{portfolio_id}",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10.0
                )
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error getting portfolio: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error getting portfolio: {str(e)}")
                raise
    
    async def get_positions(self, portfolio_id: str) -> List[Dict[str, Any]]:
        if not self.token:
            await self.authenticate()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/portfolios/{portfolio_id}/positions",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10.0
                )
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error getting positions: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error getting positions: {str(e)}")
                raise
    
    async def get_position(self, portfolio_id: str, symbol: str) -> Dict[str, Any]:
        if not self.token:
            await self.authenticate()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/portfolios/{portfolio_id}/positions/{symbol}",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10.0
                )
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return None
                    
                logger.error(f"HTTP error getting position: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error getting position: {str(e)}")
                raise
    
    async def get_sector_allocation(self, portfolio_id: str) -> Dict[str, float]:
        if not self.token:
            await self.authenticate()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/portfolios/{portfolio_id}/sector-allocation",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10.0
                )
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error getting sector allocation: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error getting sector allocation: {str(e)}")
                raise
    
    async def get_hedge_fund(self) -> Dict[str, Any]:
        if not self.token:
            await self.authenticate()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/hedge-fund",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10.0
                )
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error getting hedge fund info: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error getting hedge fund info: {str(e)}")
                raise
    
    async def get_fund_metrics(self) -> Dict[str, Any]:
        if not self.token:
            await self.authenticate()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/hedge-fund/metrics",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10.0
                )
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error getting fund metrics: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error getting fund metrics: {str(e)}")
                raise