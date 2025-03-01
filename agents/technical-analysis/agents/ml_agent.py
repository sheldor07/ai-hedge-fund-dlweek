"""
ML-based technical analysis agent implementation.
Uses LSTM and Transformer models to predict price movements.
"""

import os
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
import sys
import importlib.util
import time

# Add parent directory to path for relative imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import local modules
from agents.agent_base import AgentBase
from data.data_loader import DataLoader
from models.lstm_model import LSTMModel
from models.transformer_model import TransformerModel

class MLAgent(AgentBase):
    """Machine Learning based technical analysis agent"""
    
    def __init__(self, 
                 agent_id: str,
                 tickers: List[str],
                 personality: str = "balanced",
                 models_dir: str = "models",
                 log_dir: str = "logs",
                 data_cache_dir: str = "cache"):
        """
        Initialize ML agent
        
        Args:
            agent_id: Unique identifier for this agent
            tickers: List of stock tickers to analyze
            personality: Agent personality type (conservative, balanced, aggressive, trend)
            models_dir: Directory for model storage
            log_dir: Directory for agent logs
            data_cache_dir: Directory for data cache
        """
        super().__init__(agent_id, tickers, models_dir, log_dir)
        
        # Agent specific parameters
        self.personality = personality
        
        # Personality-specific thresholds and parameters
        self.config = self._get_personality_config(personality)
        
        # Data loader
        self.data_loader = DataLoader(tickers, cache_dir=data_cache_dir)
        
        # Models
        self.models = {}
        self._init_models()
        
        # Update state
        self.state["type"] = "ml_agent"
        self.state["personality"] = personality
        self.state["config"] = self.config
        self._save_state()
        
    def _get_personality_config(self, personality: str) -> Dict[str, Any]:
        """
        Get configuration for the given personality
        
        Args:
            personality: Agent personality type
            
        Returns:
            Dictionary with personality-specific configuration
        """
        # Common configuration
        common_config = {
            "lookback_window": 30,
            "prediction_threshold": 0.55,  # Minimum probability to consider
            "position_sizing": 0.1,  # Base position size as % of portfolio
            "max_position": 0.25,  # Maximum position size as % of portfolio
            "stop_loss": 0.05,  # Stop loss as % of position value
            "take_profit": 0.10,  # Take profit as % of position value
            "use_stop_loss": True,
            "use_take_profit": True
        }
        
        # Personality-specific configurations
        if personality == "conservative":
            return {
                **common_config,
                "prediction_threshold": 0.65,  # Higher threshold
                "position_sizing": 0.05,  # Smaller position size
                "max_position": 0.15,  # Smaller max position
                "stop_loss": 0.03,  # Tighter stop loss
                "take_profit": 0.07,  # Lower take profit
                "confidence_weight": {
                    "lstm": 0.4,
                    "transformer": 0.3,
                    "technicals": 0.3
                }
            }
        elif personality == "balanced":
            return {
                **common_config,
                "confidence_weight": {
                    "lstm": 0.4,
                    "transformer": 0.4,
                    "technicals": 0.2
                }
            }
        elif personality == "aggressive":
            return {
                **common_config,
                "prediction_threshold": 0.5,  # Lower threshold
                "position_sizing": 0.15,  # Larger position size
                "max_position": 0.35,  # Larger max position
                "stop_loss": 0.07,  # Wider stop loss
                "take_profit": 0.15,  # Higher take profit
                "confidence_weight": {
                    "lstm": 0.45,
                    "transformer": 0.45,
                    "technicals": 0.1
                }
            }
        elif personality == "trend":
            return {
                **common_config,
                "prediction_threshold": 0.6,
                "position_sizing": 0.1,
                "confidence_weight": {
                    "lstm": 0.3,
                    "transformer": 0.3,
                    "technicals": 0.4
                }
            }
        else:
            # Default to balanced
            return {
                **common_config,
                "confidence_weight": {
                    "lstm": 0.4,
                    "transformer": 0.4,
                    "technicals": 0.2
                }
            }
    
    def _init_models(self) -> None:
        """Initialize or load models for each ticker"""
        for ticker in self.tickers:
            # Model directories
            lstm_dir = os.path.join(self.models_dir, ticker, "lstm")
            transformer_dir = os.path.join(self.models_dir, ticker, "transformer")
            
            os.makedirs(lstm_dir, exist_ok=True)
            os.makedirs(transformer_dir, exist_ok=True)
            
            # Model paths
            lstm_path = os.path.join(lstm_dir, "model.keras")
            transformer_path = os.path.join(transformer_dir, "model.keras")
            
            # Initialize models dict
            self.models[ticker] = {
                "lstm": None,
                "transformer": None,
                "trained": False
            }
            
            # Check if models exist and load them
            if os.path.exists(lstm_path):
                try:
                    # For now, we'll create a placeholder. In a real implementation,
                    # we would create the LSTM model with proper input shape
                    lookback_window = self.config["lookback_window"]
                    
                    # We don't know the feature dimension yet, so we'll create later
                    self.models[ticker]["lstm"] = {
                        "model_path": lstm_path,
                        "status": "loaded"
                    }
                    self.models[ticker]["trained"] = True
                    print(f"LSTM model for {ticker} registered at {lstm_path}")
                except Exception as e:
                    print(f"Error loading LSTM model for {ticker}: {e}")
            
            if os.path.exists(transformer_path):
                try:
                    # Similar placeholder for transformer
                    self.models[ticker]["transformer"] = {
                        "model_path": transformer_path,
                        "status": "loaded"
                    }
                    self.models[ticker]["trained"] = True
                    print(f"Transformer model for {ticker} registered at {transformer_path}")
                except Exception as e:
                    print(f"Error loading Transformer model for {ticker}: {e}")
    
    def train_models(self, force_retrain: bool = False) -> Dict[str, Any]:
        """
        Train models for all tickers
        
        Args:
            force_retrain: Whether to force retraining of models
            
        Returns:
            Dictionary with training results
        """
        print("Training models...")
        start_time = time.time()
        training_results = {}
        
        for ticker in self.tickers:
            print(f"\nTraining models for {ticker}...")
            
            # Skip if already trained and not forcing retrain
            if self.models[ticker]["trained"] and not force_retrain:
                print(f"Models for {ticker} already trained. Use force_retrain=True to retrain.")
                training_results[ticker] = {"status": "skipped", "reason": "already_trained"}
                continue
            
            # Get data
            try:
                # Get historical data
                df = self.data_loader.download_historical_data(period="5y")[ticker]
                
                # Add technical indicators
                df = self.data_loader.add_technical_indicators(df)
                
                # Train/val/test split
                X_train, y_train, X_val, y_val, X_test, y_test = self.data_loader.train_test_split(
                    df, lookback=self.config["lookback_window"]
                )
                
                # Model paths
                lstm_path = os.path.join(self.models_dir, ticker, "lstm", "model.keras")
                transformer_path = os.path.join(self.models_dir, ticker, "transformer", "model.keras")
                
                # Train LSTM model
                print(f"Training LSTM model for {ticker}...")
                input_shape = (X_train.shape[1], X_train.shape[2])
                lstm_model = LSTMModel(input_shape=input_shape, model_path=None)
                lstm_history = lstm_model.train(X_train, y_train, X_val, y_val, save_path=lstm_path)
                
                # Train Transformer model
                print(f"Training Transformer model for {ticker}...")
                transformer_model = TransformerModel(
                    input_shape=input_shape, 
                    model_path=None
                )
                transformer_history = transformer_model.train(X_train, y_train, X_val, y_val, save_path=transformer_path)
                
                # Evaluate models
                lstm_eval = lstm_model.evaluate(X_test, y_test)
                transformer_eval = transformer_model.evaluate(X_test, y_test)
                
                # Update models dict
                self.models[ticker]["lstm"] = {
                    "model": lstm_model,
                    "model_path": lstm_path,
                    "performance": lstm_eval,
                    "status": "trained"
                }
                
                self.models[ticker]["transformer"] = {
                    "model": transformer_model,
                    "model_path": transformer_path,
                    "performance": transformer_eval,
                    "status": "trained"
                }
                
                self.models[ticker]["trained"] = True
                
                # Save results
                training_results[ticker] = {
                    "status": "success",
                    "lstm_eval": lstm_eval,
                    "transformer_eval": transformer_eval,
                    "data_shape": {
                        "X_train": X_train.shape,
                        "y_train": y_train.shape,
                        "X_val": X_val.shape,
                        "y_val": y_val.shape,
                        "X_test": X_test.shape,
                        "y_test": y_test.shape
                    }
                }
                
                print(f"Training for {ticker} completed successfully!")
                print(f"LSTM model accuracy: {lstm_eval['accuracy']:.4f}")
                print(f"Transformer model accuracy: {transformer_eval['accuracy']:.4f}")
                
            except Exception as e:
                print(f"Error training models for {ticker}: {e}")
                training_results[ticker] = {"status": "error", "error": str(e)}
        
        # Log training action
        elapsed_time = time.time() - start_time
        training_log = {
            "type": "training",
            "duration": elapsed_time,
            "results": training_results
        }
        self._log_action(training_log)
        
        return training_results
    
    def _check_technical_signals(self, df: pd.DataFrame) -> Tuple[str, float]:
        """
        Check technical indicators for trading signals
        
        Args:
            df: DataFrame with technical indicators
            
        Returns:
            Tuple of (signal, confidence)
        """
        # Get the latest data point
        latest = df.iloc[-1]
        
        # Calculate signals and confidences
        signals = []
        
        # 1. Moving Average signal
        if latest['Close'] > latest['sma50'] and latest['sma20'] > latest['sma50']:
            signals.append(('buy', 0.6))  # Bullish
        elif latest['Close'] < latest['sma50'] and latest['sma20'] < latest['sma50']:
            signals.append(('sell', 0.6))  # Bearish
        else:
            signals.append(('hold', 0.5))  # Neutral
        
        # 2. RSI signal
        if latest['rsi14'] < 30:
            signals.append(('buy', 0.7))  # Oversold
        elif latest['rsi14'] > 70:
            signals.append(('sell', 0.7))  # Overbought
        else:
            signals.append(('hold', 0.5))  # Neutral
        
        # 3. MACD signal
        if latest['macd'] > latest['macd_signal'] and latest['macd'] > 0:
            signals.append(('buy', 0.65))  # Bullish
        elif latest['macd'] < latest['macd_signal'] and latest['macd'] < 0:
            signals.append(('sell', 0.65))  # Bearish
        else:
            signals.append(('hold', 0.5))  # Neutral
        
        # 4. Bollinger Bands signal
        if latest['Close'] < latest['bb_low']:
            signals.append(('buy', 0.6))  # Below lower band
        elif latest['Close'] > latest['bb_high']:
            signals.append(('sell', 0.6))  # Above upper band
        else:
            signals.append(('hold', 0.5))  # Within bands
        
        # 5. ADX Trend signal
        if latest['adx'] > 25:
            if latest['DMP_14'] > latest['DMN_14']:
                signals.append(('buy', 0.7))  # Strong uptrend
            else:
                signals.append(('sell', 0.7))  # Strong downtrend
        else:
            signals.append(('hold', 0.5))  # No strong trend
        
        # Count signal types and calculate average confidence
        buy_signals = [(action, conf) for action, conf in signals if action == 'buy']
        sell_signals = [(action, conf) for action, conf in signals if action == 'sell']
        hold_signals = [(action, conf) for action, conf in signals if action == 'hold']
        
        # Decide final signal based on counts and confidence
        if len(buy_signals) > len(sell_signals) and len(buy_signals) > len(hold_signals):
            avg_confidence = sum(conf for _, conf in buy_signals) / len(buy_signals)
            return 'buy', avg_confidence
        elif len(sell_signals) > len(buy_signals) and len(sell_signals) > len(hold_signals):
            avg_confidence = sum(conf for _, conf in sell_signals) / len(sell_signals)
            return 'sell', avg_confidence
        else:
            avg_confidence = sum(conf for _, conf in hold_signals) / len(hold_signals)
            return 'hold', avg_confidence
    
    def analyze(self) -> Dict[str, Any]:
        """
        Analyze tickers and generate signals
        
        Returns:
            Dictionary with analysis results
        """
        print("Analyzing tickers...")
        analysis_results = {}
        current_prices = {}
        
        for ticker in self.tickers:
            print(f"\nAnalyzing {ticker}...")
            
            try:
                # Get latest data
                df = self.data_loader.download_historical_data(period="60d")[ticker]
                df = self.data_loader.add_technical_indicators(df)
                
                # Get current price
                current_price = df.iloc[-1]['Close']
                current_prices[ticker] = current_price
                
                # Check if models are trained
                if not self.models[ticker]["trained"]:
                    print(f"Models for {ticker} not trained. Skipping analysis.")
                    analysis_results[ticker] = {
                        "status": "error", 
                        "error": "models_not_trained",
                        "current_price": current_price
                    }
                    continue
                
                # Get technical signals
                tech_signal, tech_confidence = self._check_technical_signals(df)
                
                # Prepare data for ML predictions
                latest_data = self.data_loader.get_latest_data(ticker, lookback=self.config["lookback_window"])
                
                # Make predictions
                lstm_model_info = self.models[ticker]["lstm"]
                transformer_model_info = self.models[ticker]["transformer"]
                
                # In a real implementation, we would load the models and make predictions
                # For now, we'll simulate predictions
                lstm_pred = np.random.random()
                transformer_pred = np.random.random()
                
                # Determine signals from ML models
                lstm_signal = 'buy' if lstm_pred > 0.5 else 'sell'
                transformer_signal = 'buy' if transformer_pred > 0.5 else 'sell'
                
                # Calculate confidence scores - higher for values further from 0.5
                lstm_confidence = 0.5 + abs(lstm_pred - 0.5)
                transformer_confidence = 0.5 + abs(transformer_pred - 0.5)
                
                # Weight signals according to agent personality
                weights = self.config["confidence_weight"]
                
                # Calculate weighted confidence for buy and sell
                buy_confidence = 0
                sell_confidence = 0
                
                # Add LSTM confidence
                if lstm_signal == 'buy':
                    buy_confidence += lstm_confidence * weights["lstm"]
                else:
                    sell_confidence += lstm_confidence * weights["lstm"]
                
                # Add Transformer confidence
                if transformer_signal == 'buy':
                    buy_confidence += transformer_confidence * weights["transformer"]
                else:
                    sell_confidence += transformer_confidence * weights["transformer"]
                
                # Add Technical confidence
                if tech_signal == 'buy':
                    buy_confidence += tech_confidence * weights["technicals"]
                elif tech_signal == 'sell':
                    sell_confidence += tech_confidence * weights["technicals"]
                
                # Determine final signal
                final_signal = 'hold'
                final_confidence = 0.5
                
                if buy_confidence > sell_confidence and buy_confidence > self.config["prediction_threshold"]:
                    final_signal = 'buy'
                    final_confidence = buy_confidence
                elif sell_confidence > buy_confidence and sell_confidence > self.config["prediction_threshold"]:
                    final_signal = 'sell'
                    final_confidence = sell_confidence
                
                # Save analysis results
                analysis_results[ticker] = {
                    "status": "success",
                    "current_price": current_price,
                    "signal": final_signal,
                    "confidence": final_confidence,
                    "model_predictions": {
                        "lstm": {
                            "signal": lstm_signal,
                            "confidence": lstm_confidence,
                            "raw_prediction": float(lstm_pred)
                        },
                        "transformer": {
                            "signal": transformer_signal,
                            "confidence": transformer_confidence,
                            "raw_prediction": float(transformer_pred)
                        }
                    },
                    "technical_signals": {
                        "signal": tech_signal,
                        "confidence": tech_confidence
                    },
                    "analysis_time": datetime.now().isoformat()
                }
                
                print(f"Analysis for {ticker} completed: {final_signal.upper()} ({final_confidence:.4f})")
                
            except Exception as e:
                print(f"Error analyzing {ticker}: {e}")
                analysis_results[ticker] = {"status": "error", "error": str(e)}
        
        # Log analysis
        analysis_log = {
            "type": "analysis",
            "results": analysis_results
        }
        self._log_action(analysis_log)
        
        # Update portfolio value
        self.update_portfolio_value(current_prices)
        
        # Update last analysis time
        self.state["last_analysis_time"] = datetime.now().isoformat()
        self._save_state()
        
        return analysis_results
    
    def run(self) -> Dict[str, Any]:
        """
        Run one cycle of analysis and trading
        
        Returns:
            Dictionary with run results
        """
        print(f"Running agent {self.agent_id} ({self.personality})...")
        
        # Check if models are trained
        all_trained = all(self.models[ticker]["trained"] for ticker in self.tickers)
        
        if not all_trained:
            print("Not all models are trained. Training now...")
            self.train_models()
        
        # Analyze tickers
        analysis_results = self.analyze()
        
        # Execute trades based on analysis
        trade_results = {}
        
        for ticker, analysis in analysis_results.items():
            if analysis["status"] != "success":
                continue
            
            signal = analysis["signal"]
            confidence = analysis["confidence"]
            price = analysis["current_price"]
            
            # Calculate position size based on confidence and personality
            position_size = self.config["position_sizing"]
            
            # Adjust position size based on confidence
            adjusted_position = position_size * (confidence / 0.5)
            
            # Cap at max position
            position_allocation = min(adjusted_position, self.config["max_position"])
            
            # Execute trade
            if signal == 'buy' or signal == 'sell':
                trade_result = self.execute_trade(
                    ticker=ticker,
                    action=signal,
                    confidence=confidence,
                    price=price,
                    allocation=position_allocation
                )
                trade_results[ticker] = trade_result
            else:
                # Log hold action
                trade_result = self.execute_trade(
                    ticker=ticker,
                    action='hold',
                    confidence=confidence,
                    price=price
                )
                trade_results[ticker] = trade_result
        
        # Update status
        self.state["status"] = "active"
        self._save_state()
        
        # Return results
        return {
            "analysis": analysis_results,
            "trades": trade_results,
            "portfolio": {
                "cash": self.state["cash"],
                "positions": self.state["positions"],
                "value": self.state["portfolio_value"]
            }
        }


if __name__ == "__main__":
    # Example usage
    tickers = ["AMZN", "NVDA", "MU", "WMT", "DIS"]
    
    # Create agents with different personalities
    agents = {
        "conservative": MLAgent("conservative_agent", tickers, "conservative"),
        "balanced": MLAgent("balanced_agent", tickers, "balanced"),
        "aggressive": MLAgent("aggressive_agent", tickers, "aggressive"),
        "trend": MLAgent("trend_agent", tickers, "trend")
    }
    
    # Run all agents
    for name, agent in agents.items():
        print(f"\n\nRunning {name} agent...")
        results = agent.run()
        
        # Print portfolio summary
        portfolio = results["portfolio"]
        print(f"\nPortfolio Summary for {name}:")
        print(f"Cash: ${portfolio['cash']:.2f}")
        print(f"Portfolio Value: ${portfolio['value']:.2f}")
        print("Positions:")
        for ticker, position in portfolio["positions"].items():
            print(f"  {ticker}: {position['shares']:.2f} shares @ ${position['avg_price']:.2f}")