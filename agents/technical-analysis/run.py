"""
CLI runner for technical analysis agents.
"""

import os
import sys
import argparse
from typing import List
import time
from datetime import datetime

# Add parent directory to path for relative imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import local modules
from agents.ml_agent import MLAgent
from data.data_loader import DataLoader

# Default configuration
DEFAULT_TICKERS = ["AMZN", "NVDA", "MU", "WMT", "DIS"]
DEFAULT_PERSONALITIES = ["conservative", "balanced", "aggressive", "trend"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
CACHE_DIR = os.path.join(BASE_DIR, "cache")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Technical Analysis Agent Runner")
    
    # Subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Train command
    train_parser = subparsers.add_parser("train", help="Train agent models")
    train_parser.add_argument("--agent", type=str, help="Agent ID to train (default: all)")
    train_parser.add_argument("--force", action="store_true", help="Force retrain even if models exist")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run agent analysis and trading")
    run_parser.add_argument("--agent", type=str, help="Agent ID to run (default: all)")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze tickers without trading")
    analyze_parser.add_argument("--agent", type=str, help="Agent ID to use (default: balanced)")
    analyze_parser.add_argument("--ticker", type=str, help="Ticker to analyze (default: all)")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show agent status")
    status_parser.add_argument("--agent", type=str, help="Agent ID to show (default: all)")
    
    # General options
    parser.add_argument("--tickers", type=str, nargs="+", default=DEFAULT_TICKERS, 
                        help="Stock tickers to analyze")
    
    return parser.parse_args()

def create_agents(tickers: List[str], agent_id: str = None) -> dict:
    """Create agent instances"""
    agents = {}
    
    # Create directories
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    # Create requested agent or all agents
    if agent_id:
        # Extract personality from agent_id
        if "_agent" in agent_id:
            personality = agent_id.replace("_agent", "")
        else:
            personality = agent_id
            agent_id = f"{personality}_agent"
        
        if personality not in DEFAULT_PERSONALITIES:
            print(f"Warning: {personality} is not a standard personality type")
        
        agents[agent_id] = MLAgent(
            agent_id=agent_id,
            tickers=tickers,
            personality=personality,
            models_dir=MODELS_DIR,
            log_dir=LOGS_DIR,
            data_cache_dir=CACHE_DIR
        )
    else:
        # Create all personality types
        for personality in DEFAULT_PERSONALITIES:
            agent_id = f"{personality}_agent"
            agents[agent_id] = MLAgent(
                agent_id=agent_id,
                tickers=tickers,
                personality=personality,
                models_dir=MODELS_DIR,
                log_dir=LOGS_DIR,
                data_cache_dir=CACHE_DIR
            )
    
    return agents

def run_training(agents: dict, force_retrain: bool = False):
    """Run model training for all agents"""
    print(f"Training models for {len(agents)} agents...")
    start_time = time.time()
    
    for agent_id, agent in agents.items():
        print(f"\n--- Training {agent_id} ---")
        try:
            results = agent.train_models(force_retrain=force_retrain)
            print(f"Training completed for {agent_id}")
        except Exception as e:
            print(f"Error training {agent_id}: {e}")
    
    elapsed_time = time.time() - start_time
    print(f"\nTotal training time: {elapsed_time:.2f} seconds")

def run_agents(agents: dict):
    """Run all agents for analysis and trading"""
    print(f"Running {len(agents)} agents...")
    start_time = time.time()
    
    for agent_id, agent in agents.items():
        print(f"\n--- Running {agent_id} ---")
        try:
            results = agent.run()
            
            # Print portfolio summary
            portfolio = results["portfolio"]
            print(f"\nPortfolio Summary for {agent_id}:")
            print(f"Cash: ${portfolio['cash']:.2f}")
            print(f"Portfolio Value: ${portfolio['value']:.2f}")
            print("Positions:")
            for ticker, position in portfolio["positions"].items():
                print(f"  {ticker}: {position['shares']:.2f} shares @ ${position['avg_price']:.2f}")
                
            # Print trade summary
            print("\nTrades:")
            for ticker, trade in results["trades"].items():
                if trade["action"] == "hold":
                    print(f"  {ticker}: HOLD (confidence: {trade['confidence']:.4f})")
                else:
                    print(f"  {ticker}: {trade['action'].upper()} {trade['quantity']:.2f} shares @ ${trade['price']:.2f} (confidence: {trade['confidence']:.4f})")
                    
        except Exception as e:
            print(f"Error running {agent_id}: {e}")
    
    elapsed_time = time.time() - start_time
    print(f"\nTotal execution time: {elapsed_time:.2f} seconds")

def analyze_tickers(agents: dict, ticker: str = None):
    """Analyze tickers without trading"""
    print(f"Analyzing {'all tickers' if ticker is None else ticker}...")
    
    for agent_id, agent in agents.items():
        print(f"\n--- Analysis from {agent_id} ---")
        try:
            results = agent.analyze()
            
            # Filter by ticker if specified
            if ticker:
                if ticker in results and results[ticker]["status"] == "success":
                    ticker_result = results[ticker]
                    print(f"Analysis for {ticker}:")
                    print(f"  Current Price: ${ticker_result['current_price']:.2f}")
                    print(f"  Signal: {ticker_result['signal'].upper()}")
                    print(f"  Confidence: {ticker_result['confidence']:.4f}")
                    print(f"  LSTM Signal: {ticker_result['model_predictions']['lstm']['signal'].upper()} ({ticker_result['model_predictions']['lstm']['confidence']:.4f})")
                    print(f"  Transformer Signal: {ticker_result['model_predictions']['transformer']['signal'].upper()} ({ticker_result['model_predictions']['transformer']['confidence']:.4f})")
                    print(f"  Technical Signal: {ticker_result['technical_signals']['signal'].upper()} ({ticker_result['technical_signals']['confidence']:.4f})")
                else:
                    print(f"No analysis available for {ticker}")
            else:
                # Show all tickers
                for ticker, ticker_result in results.items():
                    if ticker_result["status"] == "success":
                        print(f"Analysis for {ticker}:")
                        print(f"  Current Price: ${ticker_result['current_price']:.2f}")
                        print(f"  Signal: {ticker_result['signal'].upper()}")
                        print(f"  Confidence: {ticker_result['confidence']:.4f}")
                
        except Exception as e:
            print(f"Error analyzing with {agent_id}: {e}")

def show_status(agents: dict):
    """Show agent status"""
    print("\nAgent Status:")
    print("-" * 80)
    print(f"{'Agent ID':<20} {'Status':<10} {'Portfolio Value':<20} {'Cash':<15} {'Positions'}")
    print("-" * 80)
    
    for agent_id, agent in agents.items():
        status = agent.get_status()
        positions_str = ", ".join([f"{t}: {p['shares']:.1f}" for t, p in status["positions"].items()])
        
        print(f"{agent_id:<20} {status['status']:<10} ${status['portfolio_value']:<18.2f} ${status['cash']:<13.2f} {positions_str}")
    
    print("-" * 80)

def main():
    """Main entry point"""
    args = parse_args()
    
    # Create agents
    agents = create_agents(args.tickers, args.agent)
    
    # Execute requested command
    if args.command == "train":
        run_training(agents, args.force)
    elif args.command == "run":
        run_agents(agents)
    elif args.command == "analyze":
        # Use balanced agent if not specified
        if args.agent is None and len(agents) > 1:
            balanced_agent = {"balanced_agent": agents["balanced_agent"]}
            analyze_tickers(balanced_agent, args.ticker)
        else:
            analyze_tickers(agents, args.ticker)
    elif args.command == "status":
        show_status(agents)
    else:
        # Default to showing status
        show_status(agents)
        print("\nUse --help to see available commands")

if __name__ == "__main__":
    main()