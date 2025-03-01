import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta

class AgentBase:
    
    def __init__(self, 
                 agent_id: str,
                 tickers: List[str],
                 models_dir: str = "models",
                 log_dir: str = "logs"):
        self.agent_id = agent_id
        self.tickers = tickers
        self.models_dir = models_dir
        self.log_dir = log_dir
        self.history = []
        
        os.makedirs(models_dir, exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(os.path.join(log_dir, agent_id), exist_ok=True)
        
        self.state = {
            "agent_id": agent_id,
            "tickers": tickers,
            "last_analysis_time": None,
            "status": "initialized",
            "positions": {},
            "cash": 100000.0,
            "portfolio_value": 100000.0,
            "performance": [],
        }
        
        self._load_state()
    
    def _load_state(self) -> None:
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
        state_file = os.path.join(self.log_dir, self.agent_id, "state.json")
        
        try:
            with open(state_file, 'w') as f:
                json.dump(self.state, f, indent=2, default=str)
            print(f"Saved agent state to {state_file}")
        except Exception as e:
            print(f"Error saving state file: {e}")
    
    def _log_action(self, action: Dict[str, Any]) -> None:
        action["timestamp"] = datetime.now().isoformat()
        
        self.history.append(action)
        
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
        return self.state
    
    def get_history(self, days: int = 7) -> List[Dict[str, Any]]:
        start_date = datetime.now() - timedelta(days=days)
        
        filtered_history = []
        for action in self.history:
            action_date = datetime.fromisoformat(action["timestamp"])
            if action_date >= start_date:
                filtered_history.append(action)
        
        return filtered_history
    
    def update_portfolio_value(self, prices: Dict[str, float]) -> float:
        portfolio_value = self.state["cash"]
        
        for ticker, position in self.state["positions"].items():
            if ticker in prices:
                portfolio_value += position["shares"] * prices[ticker]
        
        self.state["portfolio_value"] = portfolio_value
        
        today = datetime.now().strftime("%Y-%m-%d")
        self.state["performance"].append({
            "date": today,
            "value": portfolio_value
        })
        
        self._save_state()
        
        return portfolio_value
    
    def execute_trade(self, 
                      ticker: str, 
                      action: str,
                      confidence: float,
                      price: float,
                      quantity: Optional[float] = None,
                      allocation: Optional[float] = None) -> Dict[str, Any]:
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
        
        try:
            if action not in ['buy', 'sell']:
                return {
                    "status": "error",
                    "message": f"Invalid action: {action}"
                }
            
            if quantity is None and allocation is None:
                return {
                    "status": "error",
                    "message": "Either quantity or allocation must be specified"
                }
            
            if quantity is None:
                if allocation <= 0 or allocation > 1:
                    return {
                        "status": "error",
                        "message": f"Invalid allocation: {allocation}"
                    }
                
                portfolio_value = self.state["portfolio_value"]
                trade_value = portfolio_value * allocation
                quantity = trade_value / price
            
            if action == 'buy':
                trade_value = price * quantity
                
                if trade_value > self.state["cash"]:
                    return {
                        "status": "error",
                        "message": f"Insufficient funds: {self.state['cash']} < {trade_value}"
                    }
                
                if ticker not in self.state["positions"]:
                    self.state["positions"][ticker] = {
                        "shares": 0,
                        "cost_basis": 0
                    }
                
                position = self.state["positions"][ticker]
                old_shares = position["shares"]
                old_cost = position["cost_basis"]
                
                position["shares"] += quantity
                position["cost_basis"] = (old_cost * old_shares + trade_value) / position["shares"]
                
                self.state["cash"] -= trade_value
                
            elif action == 'sell':
                if ticker not in self.state["positions"]:
                    return {
                        "status": "error",
                        "message": f"No position in {ticker}"
                    }
                
                position = self.state["positions"][ticker]
                
                if quantity > position["shares"]:
                    return {
                        "status": "error",
                        "message": f"Insufficient shares: {position['shares']} < {quantity}"
                    }
                
                trade_value = price * quantity
                
                position["shares"] -= quantity
                
                if position["shares"] == 0:
                    del self.state["positions"][ticker]
                
                self.state["cash"] += trade_value
            
            self._save_state()
            
            trade_result = {
                "ticker": ticker,
                "action": action,
                "confidence": confidence,
                "price": price,
                "quantity": quantity,
                "value": price * quantity,
                "status": "success"
            }
            
            self._log_action({
                "type": "trade",
                "ticker": ticker,
                "action": action,
                "confidence": confidence,
                "price": price,
                "quantity": quantity,
                "value": price * quantity
            })
            
            return trade_result
            
        except Exception as e:
            error_msg = str(e)
            
            self._log_action({
                "type": "trade_error",
                "ticker": ticker,
                "action": action,
                "error": error_msg
            })
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    def analyze(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement analyze()")
    
    def make_decision(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement make_decision()")
    
    def run_cycle(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        try:
            analysis_results = self.analyze(data)
            
            decisions = self.make_decision(analysis_results)
            
            self.state["last_analysis_time"] = datetime.now().isoformat()
            self._save_state()
            
            self._log_action({
                "type": "cycle",
                "analysis": analysis_results,
                "decisions": decisions
            })
            
            return {
                "status": "success",
                "analysis": analysis_results,
                "decisions": decisions
            }
            
        except Exception as e:
            error_msg = str(e)
            
            self._log_action({
                "type": "cycle_error",
                "error": error_msg
            })
            
            return {
                "status": "error",
                "message": error_msg
            }