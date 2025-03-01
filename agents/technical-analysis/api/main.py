import os
import sys
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.ml_agent import MLAgent
from data.data_loader import DataLoader

app = FastAPI(
    title="Technical Analysis Agent API",
    description="AI-powered technical analysis agents for stock trading",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TICKERS = ["AMZN", "NVDA", "MU", "WMT", "DIS"]
PERSONALITIES = ["conservative", "balanced", "aggressive", "trend"]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
CACHE_DIR = os.path.join(BASE_DIR, "cache")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

agents = {}
data_loader = None

scheduler = AsyncIOScheduler()

class AgentResponse(BaseModel):
    agent_id: str
    status: str
    last_analysis_time: Optional[str]
    portfolio_value: float
    cash: float
    positions: Dict[str, Any]

class PredictionResponse(BaseModel):
    ticker: str
    current_price: float
    signal: str
    confidence: float
    timestamp: str

class AnalysisResponse(BaseModel):
    ticker: str
    current_price: float
    signal: str
    confidence: float
    model_predictions: Dict[str, Any]
    technical_signals: Dict[str, Any]
    timestamp: str

class HistoryEntry(BaseModel):
    type: str
    timestamp: str
    ticker: Optional[str] = None
    action: Optional[str] = None
    confidence: Optional[float] = None
    price: Optional[float] = None
    quantity: Optional[float] = None
    value: Optional[float] = None

def get_agent(agent_id: str) -> MLAgent:
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return agents[agent_id]

async def initialize_agents():
    global agents, data_loader
    
    data_loader = DataLoader(TICKERS, cache_dir=CACHE_DIR)
    
    for personality in PERSONALITIES:
        agent_id = f"{personality}_agent"
        agents[agent_id] = MLAgent(
            agent_id=agent_id,
            tickers=TICKERS,
            personality=personality,
            models_dir=MODELS_DIR,
            log_dir=LOGS_DIR,
            data_cache_dir=CACHE_DIR
        )
    
    print(f"Initialized {len(agents)} agents")

async def run_daily_analysis():
    print("Running scheduled daily analysis...")
    
    for agent_id, agent in agents.items():
        try:
            result = agent.run()
            print(f"Agent {agent_id} analysis completed")
        except Exception as e:
            print(f"Error running agent {agent_id}: {e}")

@app.get("/")
async def root():
    return {"message": "Technical Analysis Agent API", "version": "1.0.0"}

@app.get("/agents", response_model=List[str])
async def list_agents():
    return list(agents.keys())

@app.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent_status(agent_id: str):
    agent = get_agent(agent_id)
    status = agent.get_status()
    
    return AgentResponse(
        agent_id=status["agent_id"],
        status=status["status"],
        last_analysis_time=status["last_analysis_time"],
        portfolio_value=status["portfolio_value"],
        cash=status["cash"],
        positions=status["positions"]
    )

@app.post("/agents/{agent_id}/run")
async def run_agent(agent_id: str, background_tasks: BackgroundTasks):
    agent = get_agent(agent_id)
    
    background_tasks.add_task(agent.run)
    
    return {"message": f"Agent {agent_id} analysis started in background"}

@app.get("/predict/{ticker}")
async def get_prediction(ticker: str):
    if ticker not in TICKERS:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not supported")
    
    results = {}
    
    for agent_id, agent in agents.items():
        if agent.state.get("last_analysis_time") is None:
            continue
        
        try:
            analysis = agent.analyze()
            if ticker in analysis and analysis[ticker]["status"] == "success":
                ticker_analysis = analysis[ticker]
                results[agent_id] = {
                    "signal": ticker_analysis["signal"],
                    "confidence": ticker_analysis["confidence"],
                    "price": ticker_analysis["current_price"],
                    "timestamp": ticker_analysis["analysis_time"]
                }
        except Exception as e:
            print(f"Error getting prediction for {ticker} from {agent_id}: {e}")
    
    if not results:
        try:
            agent = agents["balanced_agent"]
            analysis = agent.analyze()
            if ticker in analysis and analysis[ticker]["status"] == "success":
                ticker_analysis = analysis[ticker]
                results["balanced_agent"] = {
                    "signal": ticker_analysis["signal"],
                    "confidence": ticker_analysis["confidence"],
                    "price": ticker_analysis["current_price"],
                    "timestamp": ticker_analysis["analysis_time"]
                }
        except Exception as e:
            print(f"Error getting new prediction for {ticker}: {e}")
    
    if not results:
        raise HTTPException(status_code=404, detail=f"No predictions available for {ticker}")
    
    return results

@app.get("/analysis/{ticker}", response_model=Dict[str, AnalysisResponse])
async def get_analysis(ticker: str):
    if ticker not in TICKERS:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not supported")
    
    results = {}
    
    for agent_id, agent in agents.items():
        try:
            analysis = agent.analyze()
            
            if ticker in analysis and analysis[ticker]["status"] == "success":
                ticker_analysis = analysis[ticker]
                results[agent_id] = AnalysisResponse(
                    ticker=ticker,
                    current_price=ticker_analysis["current_price"],
                    signal=ticker_analysis["signal"],
                    confidence=ticker_analysis["confidence"],
                    model_predictions=ticker_analysis["model_predictions"],
                    technical_signals=ticker_analysis["technical_signals"],
                    timestamp=ticker_analysis["analysis_time"]
                )
        except Exception as e:
            print(f"Error analyzing {ticker} with {agent_id}: {e}")
    
    if not results:
        raise HTTPException(status_code=500, detail=f"Failed to analyze {ticker}")
    
    return results

@app.get("/agents/{agent_id}/history", response_model=List[HistoryEntry])
async def get_agent_history(agent_id: str, days: int = 7):
    agent = get_agent(agent_id)
    history = agent.get_history(days=days)
    
    return [HistoryEntry(**entry) for entry in history]

@app.post("/train")
async def train_models(background_tasks: BackgroundTasks, force: bool = False):
    async def train_all():
        for agent_id, agent in agents.items():
            try:
                print(f"Training models for {agent_id}...")
                agent.train_models(force_retrain=force)
            except Exception as e:
                print(f"Error training models for {agent_id}: {e}")
    
    background_tasks.add_task(train_all)
    
    return {"message": "Model training started in background"}

@app.on_event("startup")
async def startup_event():
    await initialize_agents()
    
    scheduler.add_job(run_daily_analysis, 'cron', hour=0, minute=0)
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8100, reload=True)