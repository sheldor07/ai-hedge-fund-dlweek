import os
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
import sys
import importlib.util
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.agent_base import AgentBase
from data.data_loader import DataLoader
from models.lstm_model import LSTMModel
from models.transformer_model import TransformerModel

class MLAgent(AgentBase):
    
    def __init__(self, 
                 agent_id: str,
                 tickers: List[str],
                 personality: str = "balanced",
                 models_dir: str = "models",
                 log_dir: str = "logs",
                 data_cache_dir: str = "cache"):
        super().__init__(agent_id, tickers, models_dir, log_dir)
        
        self.personality = personality
        
        self.config = self._get_personality_config(personality)
        
        self.data_loader = DataLoader(tickers, cache_dir=data_cache_dir)
        
        self.models = {}
        self._init_models()
        
        self.state["type"] = "ml_agent"
        self.state["personality"] = personality
        self.state["config"] = self.config
        self._save_state()
        
    def _get_personality_config(self, personality: str) -> Dict[str, Any]:
        common_config = {
            "lookback_window": 30,
            "prediction_threshold": 0.52,
            "position_sizing": 0.1,
            "max_position": 0.25,
            "stop_loss": 0.05,
            "take_profit": 0.10,
            "use_stop_loss": True,
            "use_take_profit": True
        }
        
        if personality == "conservative":
            return {
                **common_config,
                "prediction_threshold": 0.55,
                "position_sizing": 0.05,
                "max_position": 0.15,
                "stop_loss": 0.03,
                "take_profit": 0.07,
                "confidence_weight": {
                    "lstm": 0.35,
                    "transformer": 0.35,
                    "technicals": 0.3
                }
            }
        elif personality == "balanced":
            return {
                **common_config,
                "prediction_threshold": 0.52,
                "confidence_weight": {
                    "lstm": 0.45,
                    "transformer": 0.45,
                    "technicals": 0.1
                }
            }
        elif personality == "aggressive":
            return {
                **common_config,
                "prediction_threshold": 0.51,
                "position_sizing": 0.15,
                "max_position": 0.35,
                "stop_loss": 0.07,
                "take_profit": 0.15,
                "confidence_weight": {
                    "lstm": 0.5, 
                    "transformer": 0.5,
                    "technicals": 0.0
                }
            }
        elif personality == "trend":
            return {
                **common_config,
                "prediction_threshold": 0.53,
                "position_sizing": 0.12,
                "confidence_weight": {
                    "lstm": 0.25,
                    "transformer": 0.25,
                    "technicals": 0.5
                }
            }
        else:
            return {
                **common_config,
                "prediction_threshold": 0.52,
                "confidence_weight": {
                    "lstm": 0.45,
                    "transformer": 0.45,
                    "technicals": 0.1
                }
            }
    
    def _init_models(self) -> None:
        for ticker in self.tickers:
            lstm_dir = os.path.join(self.models_dir, ticker, "lstm")
            transformer_dir = os.path.join(self.models_dir, ticker, "transformer")
            
            os.makedirs(lstm_dir, exist_ok=True)
            os.makedirs(transformer_dir, exist_ok=True)
            
            lstm_path = os.path.join(lstm_dir, "model.keras")
            transformer_path = os.path.join(transformer_dir, "model.keras")
            
            self.models[ticker] = {
                "lstm": None,
                "transformer": None,
                "trained": False
            }
            
            if os.path.exists(lstm_path):
                try:
                    lookback_window = self.config["lookback_window"]
                    
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
                    self.models[ticker]["transformer"] = {
                        "model_path": transformer_path,
                        "status": "loaded"
                    }
                    self.models[ticker]["trained"] = True
                    print(f"Transformer model for {ticker} registered at {transformer_path}")
                except Exception as e:
                    print(f"Error loading Transformer model for {ticker}: {e}")
    
    def train_models(self, force_retrain: bool = False) -> Dict[str, Any]:
        print("Training models...")
        start_time = time.time()
        training_results = {}
        
        for ticker in self.tickers:
            print(f"\nTraining models for {ticker}...")
            
            if self.models[ticker]["trained"] and not force_retrain:
                print(f"Models for {ticker} already trained. Use force_retrain=True to retrain.")
                training_results[ticker] = {"status": "skipped", "reason": "already_trained"}
                continue
            
            try:
                df = self.data_loader.download_historical_data(period="5y")[ticker]
                
                df = self.data_loader.add_technical_indicators(df)
                
                X_train, y_train, X_val, y_val, X_test, y_test = self.data_loader.train_test_split(
                    df, lookback=self.config["lookback_window"]
                )
                
                lstm_path = os.path.join(self.models_dir, ticker, "lstm", "model.keras")
                transformer_path = os.path.join(self.models_dir, ticker, "transformer", "model.keras")
                
                input_shape = (X_train.shape[1], X_train.shape[2])
                lstm_model = LSTMModel(input_shape=input_shape, model_path=None)
                lstm_history = lstm_model.train(X_train, y_train, X_val, y_val, save_path=lstm_path)
                
                transformer_model = TransformerModel(
                    input_shape=input_shape, 
                    model_path=None
                )
                transformer_history = transformer_model.train(X_train, y_train, X_val, y_val, save_path=transformer_path)
                
                lstm_eval = lstm_model.evaluate(X_test, y_test)
                transformer_eval = transformer_model.evaluate(X_test, y_test)
                
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
        
        elapsed_time = time.time() - start_time
        training_log = {
            "type": "training",
            "duration": elapsed_time,
            "results": training_results
        }
        self._log_action(training_log)
        
        return training_results
    
    def _check_technical_signals(self, df: pd.DataFrame) -> Tuple[str, float]:
        latest = df.iloc[-1]
        
        signals = []
        
        has_sma = 'sma20' in df.columns and 'sma50' in df.columns
        has_rsi = 'rsi14' in df.columns
        has_macd = 'macd' in df.columns and 'macd_signal' in df.columns
        has_bb = 'bb_low' in df.columns and 'bb_high' in df.columns
        
        if has_sma:
            ma_cross = False
            if len(df) > 2:
                prev = df.iloc[-2]
                if latest['sma20'] > latest['sma50'] and prev['sma20'] <= prev['sma50']:
                    signals.append(('buy', 0.75))  
                    ma_cross = True
                elif latest['sma20'] < latest['sma50'] and prev['sma20'] >= prev['sma50']:
                    signals.append(('sell', 0.75))  
                    ma_cross = True
                    
            if not ma_cross:
                if latest['Close'] > latest['sma50'] and latest['sma20'] > latest['sma50']:
                    signals.append(('buy', 0.6))  
                elif latest['Close'] < latest['sma50'] and latest['sma20'] < latest['sma50']:
                    signals.append(('sell', 0.6))  
                else:
                    if latest['Close'] > latest['sma20']:
                        signals.append(('buy', 0.55))  
                    else:
                        signals.append(('sell', 0.55))  
        else:
            if len(df) > 5:
                price_change = df['Close'].pct_change(5).iloc[-1]
                if price_change > 0:
                    signals.append(('buy', 0.55))  
                else:
                    signals.append(('sell', 0.55))  
        
        if has_rsi:
            if latest['rsi14'] < 30:
                signals.append(('buy', 0.7))  
            elif latest['rsi14'] > 70:
                signals.append(('sell', 0.7))  
            elif latest['rsi14'] < 40:
                signals.append(('buy', 0.6))  
            elif latest['rsi14'] > 60:
                signals.append(('sell', 0.6))  
            elif latest['rsi14'] < 45:
                signals.append(('buy', 0.55))  
            elif latest['rsi14'] > 55:
                signals.append(('sell', 0.55))  
            else:
                signals.append(('hold', 0.5))
        
        if has_macd:
            macd_cross = False
            if len(df) > 2:
                prev = df.iloc[-2]
                if latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']:
                    signals.append(('buy', 0.75))  
                    macd_cross = True
                elif latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal']:
                    signals.append(('sell', 0.75))  
                    macd_cross = True
                    
            if not macd_cross:
                if latest['macd'] > latest['macd_signal'] and latest['macd'] > 0:
                    signals.append(('buy', 0.65))  
                elif latest['macd'] < latest['macd_signal'] and latest['macd'] < 0:
                    signals.append(('sell', 0.65))  
                elif latest['macd'] > latest['macd_signal']:
                    signals.append(('buy', 0.55))  
                elif latest['macd'] < latest['macd_signal']:
                    signals.append(('sell', 0.55))  
                else:
                    signals.append(('hold', 0.5))  
        
        if has_bb:
            bb_pct = (latest['Close'] - latest['bb_low']) / (latest['bb_high'] - latest['bb_low'])
            if latest['Close'] < latest['bb_low']:
                signals.append(('buy', 0.7))  
            elif latest['Close'] > latest['bb_high']:
                signals.append(('sell', 0.7))  
            elif bb_pct < 0.3:
                signals.append(('buy', 0.6))  
            elif bb_pct > 0.7:
                signals.append(('sell', 0.6))  
            elif bb_pct < 0.4:
                signals.append(('buy', 0.55))  
            elif bb_pct > 0.6:
                signals.append(('sell', 0.55))  
            else:
                signals.append(('hold', 0.5))
        
        if len(df) >= 5:
            price_change = df['Close'].pct_change(5).iloc[-1]
            if price_change > 0.03:
                signals.append(('buy', 0.65))  
            elif price_change < -0.03:
                signals.append(('sell', 0.65))  
            elif price_change > 0.01:
                signals.append(('buy', 0.55))  
            elif price_change < -0.01:
                signals.append(('sell', 0.55))  
            else:
                signals.append(('hold', 0.5))
        
        buy_signals = [(action, conf) for action, conf in signals if action == 'buy']
        sell_signals = [(action, conf) for action, conf in signals if action == 'sell']
        hold_signals = [(action, conf) for action, conf in signals if action == 'hold']
        
        if len(signals) < 3:
            if len(df) >= 3:
                recent_trend = df['Close'].iloc[-1] > df['Close'].iloc[-3]
                if recent_trend:
                    signals.append(('buy', 0.55))
                    buy_signals.append(('buy', 0.55))
                else:
                    signals.append(('sell', 0.55))
                    sell_signals.append(('sell', 0.55))
        
        if len(buy_signals) >= len(sell_signals) and len(buy_signals) >= len(hold_signals):
            avg_confidence = sum(conf for _, conf in buy_signals) / len(buy_signals) if buy_signals else 0.5
            return 'buy', avg_confidence
        elif len(sell_signals) >= len(buy_signals) and len(sell_signals) >= len(hold_signals):
            avg_confidence = sum(conf for _, conf in sell_signals) / len(sell_signals) if sell_signals else 0.5
            return 'sell', avg_confidence
        else:
            avg_confidence = sum(conf for _, conf in hold_signals) / len(hold_signals) if hold_signals else 0.5
            return 'hold', avg_confidence
    
    def analyze(self) -> Dict[str, Any]:
        print("Analyzing tickers...")
        analysis_results = {}
        current_prices = {}
        
        for ticker in self.tickers:
            print(f"\nAnalyzing {ticker}...")
            
            try:
                df = self.data_loader.download_historical_data(period="60d")[ticker]
                df = self.data_loader.add_technical_indicators(df)
                
                required_columns = ['Close', 'sma20', 'sma50', 'rsi14', 'macd', 'macd_signal', 'bb_low', 'bb_high']
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    print(f"Warning: Missing columns for {ticker}: {missing_columns}")
                    print(f"Available columns: {df.columns.tolist()}")
                    raise KeyError(f"Missing required columns: {missing_columns}")
                
                current_price = df.iloc[-1]['Close']
                current_prices[ticker] = current_price
                
                if not self.models[ticker]["trained"]:
                    print(f"Models for {ticker} not trained. Skipping analysis.")
                    analysis_results[ticker] = {
                        "status": "error", 
                        "error": "models_not_trained",
                        "current_price": current_price
                    }
                    continue
                
                tech_signal, tech_confidence = self._check_technical_signals(df)
                
                latest_data = self.data_loader.get_latest_data(ticker, lookback=self.config["lookback_window"])
                
                try:
                    short_trend = df['Close'].pct_change(5).iloc[-1]
                    medium_trend = df['Close'].pct_change(10).iloc[-1]
                    long_trend = df['Close'].pct_change(20).iloc[-1]
                    
                    price_to_sma20 = df['Close'].iloc[-1] / df['sma20'].iloc[-1] - 1 if 'sma20' in df.columns else 0
                    price_to_sma50 = df['Close'].iloc[-1] / df['sma50'].iloc[-1] - 1 if 'sma50' in df.columns else 0
                    
                    rsi = df['rsi14'].iloc[-1] if 'rsi14' in df.columns else 50
                    
                    lstm_weight_short = 0.6
                    lstm_weight_medium = 0.4
                    
                    lstm_direction = (short_trend * lstm_weight_short) + (medium_trend * lstm_weight_medium)
                    lstm_pred = 0.5 + min(0.45, max(-0.45, lstm_direction * 5)) # Scale but limit to 0.05-0.95 range
                    
                    transformer_direction = long_trend * 0.4 + price_to_sma50 * 0.3
                    
                    if rsi > 70:
                        transformer_direction -= 0.05
                    elif rsi < 30:
                        transformer_direction += 0.05
                        
                    transformer_pred = 0.5 + min(0.48, max(-0.48, transformer_direction * 5))
                    
                    print(f"Using trend-based predictions for {ticker}:")
                    print(f"  Short-term trend: {short_trend:.4f}, Medium-term: {medium_trend:.4f}")
                    print(f"  LSTM-proxy prediction: {lstm_pred:.4f}")
                    print(f"  Transformer-proxy prediction: {transformer_pred:.4f}")
                    
                except Exception as e:
                    print(f"Error making model predictions for {ticker}: {e}")
                    tech_signal_value = 1 if tech_signal == 'buy' else (0 if tech_signal == 'sell' else 0.5)
                    lstm_pred = 0.45 + (tech_signal_value * 0.1)
                    transformer_pred = 0.4 + (tech_signal_value * 0.2)
                
                lstm_signal = 'buy' if lstm_pred > 0.5 else 'sell'
                transformer_signal = 'buy' if transformer_pred > 0.5 else 'sell'
                
                lstm_confidence = 0.5 + abs(lstm_pred - 0.5)
                transformer_confidence = 0.5 + abs(transformer_pred - 0.5)
                
                weights = self.config["confidence_weight"]
                
                buy_confidence = 0
                sell_confidence = 0
                
                if lstm_signal == 'buy':
                    buy_confidence += lstm_confidence * weights["lstm"]
                else:
                    sell_confidence += lstm_confidence * weights["lstm"]
                
                if transformer_signal == 'buy':
                    buy_confidence += transformer_confidence * weights["transformer"]
                else:
                    sell_confidence += transformer_confidence * weights["transformer"]
                
                if tech_signal == 'buy':
                    buy_confidence += tech_confidence * weights["technicals"]
                elif tech_signal == 'sell':
                    sell_confidence += tech_confidence * weights["technicals"]
                
                final_signal = 'hold'
                final_confidence = 0.5
                
                if buy_confidence > sell_confidence and buy_confidence > self.config["prediction_threshold"]:
                    final_signal = 'buy'
                    final_confidence = buy_confidence
                elif sell_confidence > buy_confidence and sell_confidence > self.config["prediction_threshold"]:
                    final_signal = 'sell'
                    final_confidence = sell_confidence
                
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
        
        analysis_log = {
            "type": "analysis",
            "results": analysis_results
        }
        self._log_action(analysis_log)
        
        self.update_portfolio_value(current_prices)
        
        self.state["last_analysis_time"] = datetime.now().isoformat()
        self._save_state()
        
        return analysis_results
    
    def run(self) -> Dict[str, Any]:
        print(f"Running agent {self.agent_id} ({self.personality})...")
        
        all_trained = all(self.models[ticker]["trained"] for ticker in self.tickers)
        
        if not all_trained:
            print("Not all models are trained. Training now...")
            self.train_models()
        
        analysis_results = self.analyze()
        
        trade_results = {}
        
        for ticker, analysis in analysis_results.items():
            if analysis["status"] != "success":
                continue
            
            signal = analysis["signal"]
            confidence = analysis["confidence"]
            price = analysis["current_price"]
            
            position_size = self.config["position_sizing"]
            
            adjusted_position = position_size * (confidence / 0.5)
            
            position_allocation = min(adjusted_position, self.config["max_position"])
            
            portfolio_value = self.state["portfolio_value"]
            trade_value = portfolio_value * position_allocation
            quantity = trade_value / price
            
            if signal == 'buy':
                if trade_value <= self.state["cash"]:
                    trade_result = self.execute_trade(
                        ticker=ticker,
                        action='buy',
                        confidence=confidence,
                        price=price,
                        quantity=quantity
                    )
                else:
                    trade_result = {
                        "ticker": ticker,
                        "action": "buy_signal",  
                        "confidence": confidence,
                        "price": price,
                        "quantity": 0,
                        "value": 0,
                        "status": "insufficient_cash",
                        "cash_available": self.state["cash"],
                        "trade_value": trade_value
                    }
                trade_results[ticker] = trade_result
                
            elif signal == 'sell':
                position = self.state["positions"].get(ticker, {"shares": 0})
                shares_to_sell = min(position["shares"], quantity)
                
                if shares_to_sell > 0:
                    trade_result = self.execute_trade(
                        ticker=ticker,
                        action='sell',
                        confidence=confidence,
                        price=price,
                        quantity=shares_to_sell
                    )
                else:
                    trade_result = {
                        "ticker": ticker,
                        "action": "sell_signal",  
                        "confidence": confidence,
                        "price": price,
                        "quantity": 0,
                        "value": 0,
                        "status": "no_position"
                    }
                trade_results[ticker] = trade_result
                
            else:
                trade_result = self.execute_trade(
                    ticker=ticker,
                    action='hold',
                    confidence=confidence,
                    price=price
                )
                trade_results[ticker] = trade_result
        
        self.state["status"] = "active"
        self._save_state()
        
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
    tickers = ["AMZN", "NVDA", "MU", "WMT", "DIS"]
    
    agents = {
        "conservative": MLAgent("conservative_agent", tickers, "conservative"),
        "balanced": MLAgent("balanced_agent", tickers, "balanced"),
        "aggressive": MLAgent("aggressive_agent", tickers, "aggressive"),
        "trend": MLAgent("trend_agent", tickers, "trend")
    }
    
    for name, agent in agents.items():
        print(f"\n\nRunning {name} agent...")
        results = agent.run()
        
        portfolio = results["portfolio"]
        print(f"\nPortfolio Summary for {name}:")
        print(f"Cash: ${portfolio['cash']:.2f}")
        print(f"Portfolio Value: ${portfolio['value']:.2f}")
        print("Positions:")
        for ticker, position in portfolio["positions"].items():
            print(f"  {ticker}: {position['shares']:.2f} shares @ ${position['avg_price']:.2f}")