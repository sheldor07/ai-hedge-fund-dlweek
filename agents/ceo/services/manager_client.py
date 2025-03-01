import logging
import httpx
from typing import Dict, List, Any, Optional
from ..config import settings

logger = logging.getLogger(settings.APP_NAME)

class ManagerClient:
    def __init__(self):
        self.base_url = settings.MANAGER_API_URL
        self.token = None
    
    async def authenticate(self):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/token",
                    data={
                        "username": settings.MANAGER_API_USERNAME,
                        "password": settings.MANAGER_API_PASSWORD
                    },
                    timeout=10.0
                )
                
                response.raise_for_status()
                data = response.json()
                self.token = data["access_token"]
                logger.info("Successfully authenticated with Manager API")
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error during Manager API authentication: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error during Manager API authentication: {str(e)}")
                raise
    
    async def create_analysis_task(self, stock_symbol: str, analysis_type: str, time_frame: str = "1y") -> Dict[str, Any]:
        if not self.token:
            await self.authenticate()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/tasks/analysis",
                    json={
                        "stock_symbol": stock_symbol,
                        "analysis_type": analysis_type,
                        "time_frame": time_frame
                    },
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=30.0
                )
                
                response.raise_for_status()
                task = response.json()
                logger.info(f"Created analysis task {task['id']} for {stock_symbol}")
                return task
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error creating analysis task: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error creating analysis task: {str(e)}")
                raise
    
    async def create_decision_task(self, stock_symbol: str, analysis_id: Optional[str] = None) -> Dict[str, Any]:
        if not self.token:
            await self.authenticate()
        
        request_data = {
            "stock_symbol": stock_symbol,
            "parameters": {}
        }
        
        if analysis_id:
            request_data["analysis_id"] = analysis_id
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/tasks/decision",
                    json=request_data,
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=30.0
                )
                
                response.raise_for_status()
                task = response.json()
                logger.info(f"Created decision task {task['id']} for {stock_symbol}")
                return task
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error creating decision task: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error creating decision task: {str(e)}")
                raise
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        if not self.token:
            await self.authenticate()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/tasks/{task_id}",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10.0
                )
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error getting task status: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error getting task status: {str(e)}")
                raise
    
    async def get_completed_analysis(self, analysis_id: str) -> Dict[str, Any]:
        if not self.token:
            await self.authenticate()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/analysis/{analysis_id}",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10.0
                )
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error getting analysis: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error getting analysis: {str(e)}")
                raise
    
    async def get_latest_analysis(self, stock_symbol: str, analysis_type: str) -> Dict[str, Any]:
        if not self.token:
            await self.authenticate()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/analysis/latest/{stock_symbol}/{analysis_type}",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10.0
                )
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error getting latest analysis: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error getting latest analysis: {str(e)}")
                raise
    
    async def get_decision(self, decision_id: str) -> Dict[str, Any]:
        if not self.token:
            await self.authenticate()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/decisions/{decision_id}",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10.0
                )
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error getting decision: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error getting decision: {str(e)}")
                raise