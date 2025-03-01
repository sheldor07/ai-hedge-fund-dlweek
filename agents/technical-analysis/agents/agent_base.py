"""
Base class for technical analysis agents.
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta

class AgentBase:
    """Base class for all technical analysis agents"""
    
    def __init__(self, 
                 agent_id: str,
                 tickers: List[str],
                 models_dir: str = "models",
                 log_dir: str = "logs"):
        """
        Initialize agent base
        
        Args:
            agent_id: Unique identifier for this agent
            tickers: List of stock tickers to analyze
            models_dir: Directory for model storage
            log_dir: Directory for agent logs
        """
        self.agent_id = agent_id
        self.tickers = tickers
        self.models_dir = models_dir
        self.log_dir = log_dir
        self.history = []
        
        # Create directories if they don't exist
        os.makedirs(models_dir, exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(os.path.join(log_dir, agent_id), exist_ok=True)
        
        # Agent state
        self.state = {
            "agent_id": agent_id,
            "tickers": tickers,
            "last_analysis_time": None,
            "status": "initialized",
            "positions": {},  # Current positions
            "cash": 100000.0,  # Starting cash
            "portfolio_value": 100000.0,  # Total portfolio value
            "performance": [],  # Daily performance
        }
        
        # Load agent state if it exists
        self._load_state()
    
    def _load_state(self) -> None:
        """Load agent state from disk"""
        state_file = os.path.join(self.log_dir, self.agent_id, "state.json")
        
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    saved_state = json.load(f)
                self.state.update(saved_state)
                print(f"Loaded agent state from {state_file}")
            except Exception as e:
                print(f"Error loading state file: {e}")
    
    def _save_state(self) -> None:
        """Save agent state to disk"""
        state_file = os.path.join(self.log_dir, self.agent_id, "state.json")
        
        try:
            with open(state_file, 'w') as f:
                json.dump(self.state, f, indent=2, default=str)
            print(f"Saved agent state to {state_file}")
        except Exception as e:
            print(f"Error saving state file: {e}")
    
    def _log_action(self, action: Dict[str, Any]) -> None:
        """
        Log an agent action
        
        Args:
            action: Dictionary with action details
        """
        # Add timestamp
        action["timestamp"] = datetime.now().isoformat()
        
        # Add to history
        self.history.append(action)
        
        # Save to log file
        log_file = os.path.join(
            self.log_dir, self.agent_id, 
            f"actions_{datetime.now().strftime('%Y%m%d')}.jsonl"
        )
        
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(action, default=str) + "\n")
        except Exception as e:
            print(f"Error logging action: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status
        
        Returns:
            Dictionary with agent status
        """
        return self.state
    
    def get_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get agent action history
        
        Args:
            days: Number of days of history to return
            
        Returns:
            List of action dictionaries
        """
        # Calculate start date
        start_date = datetime.now() - timedelta(days=days)
        
        # Filter history by date
        filtered_history = []
        for action in self.history:
            action_date = datetime.fromisoformat(action["timestamp"])
            if action_date >= start_date:
                filtered_history.append(action)
        
        return filtered_history
    
    def update_portfolio_value(self, prices: Dict[str, float]) -> float:
        """
        Update portfolio value based on current prices
        
        Args:
            prices: Dictionary mapping ticker to current price
            
        Returns:
            Updated portfolio value
        """
        # Start with cash
        portfolio_value = self.state["cash"]
        
        # Add value of positions
        for ticker, position in self.state["positions"].items():
            if ticker in prices:
                portfolio_value += position["shares"] * prices[ticker]
        
        # Update state
        self.state["portfolio_value"] = portfolio_value
        
        # Record performance
        today = datetime.now().strftime("%Y-%m-%d")
        self.state["performance"].append({
            "date": today,
            "value": portfolio_value
        })
        
        # Save state
        self._save_state()
        
        return portfolio_value
    
    def execute_trade(self, 
                      ticker: str, 
                      action: str,  # 'buy', 'sell', 'hold'
                      confidence: float,
                      price: float,
                      quantity: Optional[float] = None,
                      allocation: Optional[float] = None) -> Dict[str, Any]:
        """
        Execute a trade
        
        Args:
            ticker: Stock ticker
            action: 'buy', 'sell', or 'hold'
            confidence: Confidence score (0-1)
            price: Current price
            quantity: Number of shares (if None, use allocation)
            allocation: Percentage of portfolio to allocate (0-1)
            
        Returns:
            Dictionary with trade details
        """
        if action == 'hold':
            trade_result = {
                "ticker": ticker,
                "action": "hold",
                "confidence": confidence,
                "price": price,
                "quantity": 0,
                "value": 0,
                "status": "success"
            }
            self._log_action({
                "type": "trade",
                "ticker": ticker,
                "action": "hold",
                "confidence": confidence,
                "price": price
            })
            return trade_result
        
        # Calculate quantity if using allocation
        if quantity is None and allocation is not None:
            # Maximum value to trade
            max_value = self.state["portfolio_value"] * allocation
            
            if action == 'buy':
                # Check if we have enough cash
                max_value = min(max_value, self.state["cash"])
                quantity = max_value / price
            elif action == 'sell':
                # Check if we have enough shares
                current_position = self.state["positions"].get(ticker, {"shares": 0})
                max_shares = current_position["shares"]
                quantity = max_shares * allocation
        
        # Validate quantity
        if quantity is None or quantity <= 0:
            return {
                "ticker": ticker,
                "action": action,
                "confidence": confidence,
                "price": price,
                "quantity": 0,
                "value": 0,
                "status": "failed",
                "reason": "Invalid quantity"
            }
        
        # Execute trade
        value = quantity * price
        
        if action == 'buy':
            # Check if we have enough cash
            if value > self.state["cash"]:
                return {
                    "ticker": ticker,
                    "action": action,
                    "confidence": confidence,
                    "price": price,
                    "quantity": quantity,
                    "value": value,
                    "status": "failed",
                    "reason": "Insufficient cash"
                }
            
            # Update cash
            self.state["cash"] -= value
            
            # Update position
            if ticker not in self.state["positions"]:
                self.state["positions"][ticker] = {
                    "shares": 0,
                    "avg_price": 0,
                    "cost_basis": 0
                }
            
            position = self.state["positions"][ticker]
            new_shares = position["shares"] + quantity
            new_cost = position["cost_basis"] + value
            
            position["shares"] = new_shares
            position["cost_basis"] = new_cost
            position["avg_price"] = new_cost / new_shares
        
        elif action == 'sell':
            # Check if we have enough shares
            if ticker not in self.state["positions"]:
                return {
                    "ticker": ticker,
                    "action": action,
                    "confidence": confidence,
                    "price": price,
                    "quantity": quantity,
                    "value": value,
                    "status": "failed",
                    "reason": "No position"
                }
            
            position = self.state["positions"][ticker]
            
            if quantity > position["shares"]:
                return {
                    "ticker": ticker,
                    "action": action,
                    "confidence": confidence,
                    "price": price,
                    "quantity": quantity,
                    "value": value,
                    "status": "failed",
                    "reason": "Insufficient shares"
                }
            
            # Update cash
            self.state["cash"] += value
            
            # Update position
            position["shares"] -= quantity
            
            # Calculate realized P&L
            realized_pl = value - (quantity * position["avg_price"])
            
            # Remove position if no shares left
            if position["shares"] <= 0:
                del self.state["positions"][ticker]
                
        # Log trade
        trade_result = {
            "ticker": ticker,
            "action": action,
            "confidence": confidence,
            "price": price,
            "quantity": quantity,
            "value": value,
            "status": "success"
        }
        
        self._log_action({
            "type": "trade",
            "ticker": ticker,
            "action": action,
            "confidence": confidence,
            "price": price,
            "quantity": quantity,
            "value": value
        })
        
        # Save state
        self._save_state()
        
        return trade_result
    
    def analyze(self) -> Dict[str, Any]:
        """
        Analyze tickers and generate signals
        This method should be implemented by subclasses
        
        Returns:
            Dictionary with analysis results
        """
        raise NotImplementedError("Subclasses must implement analyze()")
    
    def run(self) -> Dict[str, Any]:
        """
        Run one cycle of analysis and trading
        This method should be implemented by subclasses
        
        Returns:
            Dictionary with run results
        """
        raise NotImplementedError("Subclasses must implement run()")