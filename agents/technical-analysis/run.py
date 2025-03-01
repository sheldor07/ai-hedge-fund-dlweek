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
            
            # Print portfolio summary with performance metrics
            portfolio = results["portfolio"]
            
            # Calculate profit/loss (P&L) and return
            initial_value = 100000.00  # Starting value
            p_l = portfolio['value'] - initial_value
            percent_return = (p_l / initial_value) * 100
            
            print(f"\nPortfolio Summary for {agent_id}:")
            print(f"Cash: ${portfolio['cash']:.2f}")
            print(f"Portfolio Value: ${portfolio['value']:.2f}")
            print(f"Profit/Loss: ${p_l:.2f} ({percent_return:.2f}%)")
            
            print("Positions:")
            if portfolio["positions"]:
                for ticker, position in portfolio["positions"].items():
                    current_value = position['shares'] * results["analysis"][ticker]["current_price"]
                    cost_basis = position['cost_basis'] if 'cost_basis' in position else position['shares'] * position['avg_price']
                    unrealized_gain = current_value - cost_basis
                    position_return = (unrealized_gain / cost_basis) * 100 if cost_basis > 0 else 0
                    
                    print(f"  {ticker}: {position['shares']:.2f} shares @ ${position['avg_price']:.2f} " +
                          f"(Current: ${results['analysis'][ticker]['current_price']:.2f}, " +
                          f"Value: ${current_value:.2f}, P&L: ${unrealized_gain:.2f} / {position_return:.2f}%)")
            else:
                print("  No positions")
                
            # Print trade summary
            print("\nTrades:")
            for ticker, trade in results["trades"].items():
                if trade["action"] == "hold":
                    print(f"  {ticker}: HOLD (confidence: {trade['confidence']:.4f})")
                elif trade["action"] in ["buy", "sell"]:
                    print(f"  {ticker}: {trade['action'].upper()} {trade['quantity']:.2f} shares @ ${trade['price']:.2f} " +
                          f"(${trade['value']:.2f}, confidence: {trade['confidence']:.4f})")
                elif trade["action"] == "buy_signal" and trade["status"] == "insufficient_cash":
                    print(f"  {ticker}: BUY SIGNAL but insufficient cash " +
                          f"(needed: ${trade['trade_value']:.2f}, available: ${trade['cash_available']:.2f}, confidence: {trade['confidence']:.4f})")
                elif trade["action"] == "sell_signal" and trade["status"] == "no_position":
                    print(f"  {ticker}: SELL SIGNAL but no position (confidence: {trade['confidence']:.4f})")
                else:
                    print(f"  {ticker}: {trade['action'].upper()} (status: {trade['status']}, confidence: {trade['confidence']:.4f})")
                    
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
    """Show agent status with performance metrics"""
    print("\nAgent Status and Performance:")
    print("-" * 100)
    header = f"{'Agent ID':<15} {'Status':<10} {'Portfolio Value':<15} {'Cash':<15} {'P&L':<15} {'Return %':<10} {'Positions'}"
    print(header)
    print("-" * 100)
    
    initial_value = 100000.00  # Starting value
    
    for agent_id, agent in agents.items():
        status = agent.get_status()
        
        # Calculate P&L and return
        p_l = status['portfolio_value'] - initial_value
        percent_return = (p_l / initial_value) * 100
        
        # Format positions string
        if status["positions"]:
            positions_str = ", ".join([f"{t}: {p['shares']:.1f}" for t, p in status["positions"].items()])
        else:
            positions_str = "None"
        
        # Print row with performance metrics
        print(f"{agent_id:<15} {status['status']:<10} " +
              f"${status['portfolio_value']:<14.2f} ${status['cash']:<14.2f} " +
              f"${p_l:<14.2f} {percent_return:<9.2f}% {positions_str}")
    
    print("-" * 100)
    
    # Check if there's performance history to display
    has_performance = False
    for agent_id, agent in agents.items():
        status = agent.get_status()
        if "performance" in status and len(status["performance"]) > 1:  # Need at least 2 points for history
            has_performance = True
            break
    
    if has_performance:
        print("\nPerformance History:")
        print("-" * 80)
        
        # Find all dates across all agents
        all_dates = set()
        for agent_id, agent in agents.items():
            status = agent.get_status()
            if "performance" in status:
                for entry in status["performance"]:
                    all_dates.add(entry["date"])
        
        all_dates = sorted(list(all_dates))
        
        # Print header
        date_header = f"{'Date':<12}"
        agent_headers = " ".join([f"{agent_id[:10]:<15}" for agent_id in agents.keys()])
        print(f"{date_header} {agent_headers}")
        print("-" * 80)
        
        # Print value for each date and agent
        for date in all_dates:
            row = f"{date:<12}"
            
            for agent_id, agent in agents.items():
                status = agent.get_status()
                value = ""
                
                if "performance" in status:
                    for entry in status["performance"]:
                        if entry["date"] == date:
                            value = f"${entry['value']:<14.2f}"
                            break
                
                if not value:
                    value = f"{'N/A':<15}"
                    
                row += f" {value}"
            
            print(row)
        
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