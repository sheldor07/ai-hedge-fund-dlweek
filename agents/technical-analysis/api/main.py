"""
FastAPI backend for technical analysis agents.
"""

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

# Add parent directory to path for relative imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import local modules
from agents.ml_agent import MLAgent
from data.data_loader import DataLoader

# Initialize FastAPI app
app = FastAPI(
    title="Technical Analysis Agent API",
    description="AI-powered technical analysis agents for stock trading",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
TICKERS = ["AMZN", "NVDA", "MU", "WMT", "DIS"]
PERSONALITIES = ["conservative", "balanced", "aggressive", "trend"]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
CACHE_DIR = os.path.join(BASE_DIR, "cache")

# Create directories
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Initialize agents
agents = {}
data_loader = None

# Scheduler for periodic tasks
scheduler = AsyncIOScheduler()

# Models
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
    signal: str  # buy, sell, hold
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

# Helper functions
def get_agent(agent_id: str) -> MLAgent:
    """Get agent by ID or raise exception"""
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return agents[agent_id]

async def initialize_agents():
    """Initialize all agents"""
    global agents, data_loader
    
    # Initialize data loader
    data_loader = DataLoader(TICKERS, cache_dir=CACHE_DIR)
    
    # Create agents for each personality
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
    """Run analysis for all agents daily"""
    print("Running scheduled daily analysis...")
    
    for agent_id, agent in agents.items():
        try:
            result = agent.run()
            print(f"Agent {agent_id} analysis completed")
        except Exception as e:
            print(f"Error running agent {agent_id}: {e}")

# Routes
@app.get("/")
async def root():
    """API root endpoint"""
    return {"message": "Technical Analysis Agent API", "version": "1.0.0"}

@app.get("/agents", response_model=List[str])
async def list_agents():
    """List all available agents"""
    return list(agents.keys())

@app.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent_status(agent_id: str):
    """Get agent status"""
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
    """Run an agent analysis cycle"""
    agent = get_agent(agent_id)
    
    # Run in background to avoid blocking
    background_tasks.add_task(agent.run)
    
    return {"message": f"Agent {agent_id} analysis started in background"}

@app.get("/predict/{ticker}")
async def get_prediction(ticker: str):
    """Get the latest prediction for a ticker across all agents"""
    if ticker not in TICKERS:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not supported")
    
    results = {}
    
    for agent_id, agent in agents.items():
        # Check if agent has analyzed this ticker
        if agent.state.get("last_analysis_time") is None:
            continue
        
        # Get latest analysis
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
        # No predictions available, let's make a new one with the balanced agent
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
    """Get detailed technical analysis for a ticker"""
    if ticker not in TICKERS:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not supported")
    
    results = {}
    
    for agent_id, agent in agents.items():
        try:
            # Run fresh analysis for this ticker
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
    """Get agent action history"""
    agent = get_agent(agent_id)
    history = agent.get_history(days=days)
    
    # Convert to response model
    return [HistoryEntry(**entry) for entry in history]

@app.post("/train")
async def train_models(background_tasks: BackgroundTasks, force: bool = False):
    """Train models for all agents"""
    # Train in background
    async def train_all():
        for agent_id, agent in agents.items():
            try:
                print(f"Training models for {agent_id}...")
                agent.train_models(force_retrain=force)
            except Exception as e:
                print(f"Error training models for {agent_id}: {e}")
    
    background_tasks.add_task(train_all)
    
    return {"message": "Model training started in background"}

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    await initialize_agents()
    
    # Schedule daily analysis at midnight
    scheduler.add_job(run_daily_analysis, 'cron', hour=0, minute=0)
    scheduler.start()

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    scheduler.shutdown()

# Run server directly when script is executed
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8100, reload=True)