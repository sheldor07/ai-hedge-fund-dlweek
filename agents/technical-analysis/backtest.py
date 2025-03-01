import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import copy
import json
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from agents.ml_agent import MLAgent
from data.data_loader import DataLoader

DEFAULT_TICKERS = ["AMZN", "NVDA", "MU", "WMT", "DIS"]
DEFAULT_PERSONALITIES = ["conservative", "balanced", "aggressive", "trend"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
CACHE_DIR = os.path.join(BASE_DIR, "cache")
BACKTEST_DIR = os.path.join(BASE_DIR, "backtest_results")

class Backtester:
    
    def __init__(self, 
                 tickers: List[str] = DEFAULT_TICKERS,
                 personalities: List[str] = DEFAULT_PERSONALITIES,
                 initial_capital: float = 100000.0,
                 start_date: Optional[str] = None,  
                 end_date: Optional[str] = None,    
                 commission: float = 0.001,
                 output_dir: str = BACKTEST_DIR):
        self.tickers = tickers
        self.personalities = personalities
        self.initial_capital = initial_capital
        self.commission = commission
        self.output_dir = output_dir
        
        today = datetime.now()
        if end_date:
            self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            self.end_date = today
            
        if start_date:
            self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            self.start_date = today - timedelta(days=365)
        
        os.makedirs(output_dir, exist_ok=True)
        
        self.data_loader = DataLoader(tickers, cache_dir=CACHE_DIR)
        self.historical_data = {}
        
        self.results = {}
        
    def load_historical_data(self) -> Dict[str, pd.DataFrame]:
        print(f"Loading historical data from {self.start_date.date()} to {self.end_date.date()}")
        
        raw_data = self.data_loader.download_historical_data(period="5y")
        
        for ticker, df in raw_data.items():
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index, utc=True).tz_localize(None)
                
            df = self.data_loader.add_technical_indicators(df)
            
            mask = (df.index >= pd.Timestamp(self.start_date)) & (df.index <= pd.Timestamp(self.end_date))
            filtered_df = df.loc[mask]
            
            self.historical_data[ticker] = filtered_df
            
            print(f"Loaded {len(filtered_df)} days of data for {ticker}")
            
        return self.historical_data
    
    def create_agents(self) -> Dict[str, MLAgent]:
        agents = {}
        
        backtest_models_dir = os.path.join(self.output_dir, "models")
        backtest_logs_dir = os.path.join(self.output_dir, "logs")
        os.makedirs(backtest_models_dir, exist_ok=True)
        os.makedirs(backtest_logs_dir, exist_ok=True)
        
        for personality in self.personalities:
            agent_id = f"backtest_{personality}_agent"
            agents[agent_id] = MLAgent(
                agent_id=agent_id,
                tickers=self.tickers,
                personality=personality,
                models_dir=backtest_models_dir,
                log_dir=backtest_logs_dir,
                data_cache_dir=CACHE_DIR
            )
            
        return agents
    
    def simulate_day(self, 
                     agents: Dict[str, MLAgent], 
                     date: pd.Timestamp,
                     prices: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
        day_results = {}
        
        for agent_id, agent in agents.items():
            day_str = date.strftime("%Y-%m-%d")
            
            try:
                signals = self._generate_signals_for_date(agent, date)
                
                trades = {}
                for ticker, signal_info in signals.items():
                    signal = signal_info["signal"]
                    confidence = signal_info["confidence"]
                    price = prices[ticker]
                    
                    position_size = agent.config["position_sizing"]
                    adjusted_position = position_size * (confidence / 0.5)
                    position_allocation = min(adjusted_position, agent.config["max_position"])
                    
                    portfolio_value = agent.state["portfolio_value"]
                    trade_value = portfolio_value * position_allocation
                    quantity = trade_value / price
                    
                    if signal == 'buy':
                        if trade_value <= agent.state["cash"]:
                            trade_result = agent.execute_trade(
                                ticker=ticker,
                                action='buy',
                                confidence=confidence,
                                price=price,
                                quantity=quantity
                            )
                            
                            commission_amount = trade_result["value"] * self.commission
                            agent.state["cash"] -= commission_amount
                            agent.state["portfolio_value"] -= commission_amount
                            
                            trade_result["commission"] = commission_amount
                            trades[ticker] = trade_result
                            
                        else:
                            trades[ticker] = {
                                "ticker": ticker,
                                "action": "buy_signal",
                                "confidence": confidence,
                                "price": price,
                                "quantity": 0,
                                "value": 0,
                                "status": "insufficient_cash"
                            }
                            
                    elif signal == 'sell':
                        position = agent.state["positions"].get(ticker, {"shares": 0})
                        shares_to_sell = min(position["shares"], quantity)
                        
                        if shares_to_sell > 0:
                            trade_result = agent.execute_trade(
                                ticker=ticker,
                                action='sell',
                                confidence=confidence,
                                price=price,
                                quantity=shares_to_sell
                            )
                            
                            commission_amount = trade_result["value"] * self.commission
                            agent.state["cash"] -= commission_amount
                            agent.state["portfolio_value"] -= commission_amount
                            
                            trade_result["commission"] = commission_amount
                            trades[ticker] = trade_result
                            
                        else:
                            trades[ticker] = {
                                "ticker": ticker,
                                "action": "sell_signal",
                                "confidence": confidence,
                                "price": price,
                                "quantity": 0,
                                "value": 0,
                                "status": "no_position"
                            }
                            
                    else: 
                        trades[ticker] = {
                            "ticker": ticker,
                            "action": "hold",
                            "confidence": confidence,
                            "price": price,
                            "quantity": 0,
                            "value": 0,
                            "status": "success"
                        }
                
                portfolio_value = agent.update_portfolio_value(prices)
                
                day_results[agent_id] = {
                    "date": day_str,
                    "portfolio_value": portfolio_value,
                    "cash": agent.state["cash"],
                    "positions": copy.deepcopy(agent.state["positions"]),
                    "trades": trades
                }
                
            except Exception as e:
                print(f"Error simulating day {day_str} for {agent_id}: {e}")
                day_results[agent_id] = {
                    "date": day_str,
                    "error": str(e)
                }
                
        return day_results
    
    def _generate_signals_for_date(self, agent: MLAgent, date: pd.Timestamp) -> Dict[str, Dict[str, Any]]:

        signals = {}
        
        for ticker in self.tickers:
            try:
                df = self.historical_data[ticker]
                history_cutoff = df.index <= date
                historical_df = df.loc[history_cutoff].copy()
                
                if len(historical_df) < 30:  
                    signals[ticker] = {
                        "signal": "hold",
                        "confidence": 0.5,
                        "reason": "insufficient_history"
                    }
                    continue
                
                tech_signal, tech_confidence = agent._check_technical_signals(historical_df)
                
                short_trend = historical_df['Close'].pct_change(5).iloc[-1]
                medium_trend = historical_df['Close'].pct_change(10).iloc[-1]
                long_trend = historical_df['Close'].pct_change(20).iloc[-1]
                
                lstm_weight_short = 0.6
                lstm_weight_medium = 0.4
                
                lstm_direction = (short_trend * lstm_weight_short) + (medium_trend * lstm_weight_medium)
                lstm_pred = 0.5 + min(0.45, max(-0.45, lstm_direction * 5))
                lstm_signal = 'buy' if lstm_pred > 0.5 else 'sell'
                lstm_confidence = 0.5 + abs(lstm_pred - 0.5)
                

                transformer_direction = long_trend * 0.4 + medium_trend * 0.3
                transformer_pred = 0.5 + min(0.48, max(-0.48, transformer_direction * 5))
                transformer_signal = 'buy' if transformer_pred > 0.5 else 'sell'
                transformer_confidence = 0.5 + abs(transformer_pred - 0.5)
                

                weights = agent.config["confidence_weight"]
                
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
                
                if buy_confidence > sell_confidence and buy_confidence > agent.config["prediction_threshold"]:
                    final_signal = 'buy'
                    final_confidence = buy_confidence
                elif sell_confidence > buy_confidence and sell_confidence > agent.config["prediction_threshold"]:
                    final_signal = 'sell'
                    final_confidence = sell_confidence
                
                signals[ticker] = {
                    "signal": final_signal,
                    "confidence": final_confidence,
                    "technical_signal": tech_signal,
                    "lstm_signal": lstm_signal,
                    "transformer_signal": transformer_signal
                }
                
            except Exception as e:
                print(f"Error generating signal for {ticker} on {date}: {e}")
                signals[ticker] = {
                    "signal": "hold",
                    "confidence": 0.5,
                    "error": str(e)
                }
                
        return signals
    
    def run_backtest(self) -> Dict[str, Any]:
        print(f"Starting backtest from {self.start_date.date()} to {self.end_date.date()}")
        start_time = time.time()
        
        self.load_historical_data()
        

        trading_dates = set()
        for ticker, df in self.historical_data.items():
            trading_dates.update(df.index)
        trading_dates = sorted(list(trading_dates))
        

        agents = self.create_agents()
        
        results = {
            "backtest_config": {
                "start_date": self.start_date.strftime("%Y-%m-%d"),
                "end_date": self.end_date.strftime("%Y-%m-%d"),
                "tickers": self.tickers,
                "personalities": self.personalities,
                "initial_capital": self.initial_capital,
                "commission": self.commission
            },
            "daily_results": [],
            "performance_metrics": {}
        }
        
        for date in trading_dates:

            if date < pd.Timestamp(self.start_date) or date > pd.Timestamp(self.end_date):
                continue
                
            print(f"Simulating trading day: {date.date()}")
            
            prices = {}
            for ticker, df in self.historical_data.items():
                if date in df.index:
                    prices[ticker] = df.loc[date, 'Close']
            
            if len(prices) != len(self.tickers):
                print(f"Skipping {date.date()} - missing price data for some tickers")
                continue
            
            day_results = self.simulate_day(agents, date, prices)
            
            results["daily_results"].append({
                "date": date.strftime("%Y-%m-%d"),
                "agents": day_results
            })
            
        performance_metrics = self._calculate_performance_metrics(results["daily_results"])
        results["performance_metrics"] = performance_metrics
        
        self._save_results(results)
        
        elapsed_time = time.time() - start_time
        print(f"Backtest completed in {elapsed_time:.2f} seconds")
        
        return results
    
    def _calculate_performance_metrics(self, daily_results: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        metrics = {}
        
        portfolio_series = {}
        for agent_id in self.personalities:
            backtest_agent_id = f"backtest_{agent_id}_agent"
            portfolio_series[agent_id] = []
            
            for day in daily_results:
                if backtest_agent_id in day["agents"]:
                    agent_data = day["agents"][backtest_agent_id]
                    if "portfolio_value" in agent_data:
                        portfolio_series[agent_id].append({
                            "date": day["date"],
                            "value": agent_data["portfolio_value"]
                        })
        
        for agent_id, values in portfolio_series.items():
            if not values:
                metrics[agent_id] = {
                    "total_return": 0,
                    "annualized_return": 0,
                    "max_drawdown": 0,
                    "sharpe_ratio": 0,
                    "winning_days": 0,
                    "losing_days": 0
                }
                continue
                
            values_only = [v["value"] for v in values]
            
            daily_returns = []
            for i in range(1, len(values_only)):
                daily_return = (values_only[i] / values_only[i-1]) - 1
                daily_returns.append(daily_return)
            
            total_return = (values_only[-1] / values_only[0]) - 1
            
            days = len(values_only)
            annualized_return = ((1 + total_return) ** (365 / days)) - 1
            
            max_value = values_only[0]
            max_drawdown = 0
            
            for value in values_only:
                max_value = max(max_value, value)
                drawdown = (max_value - value) / max_value
                max_drawdown = max(max_drawdown, drawdown)
            
            if len(daily_returns) > 0:
                avg_return = sum(daily_returns) / len(daily_returns)
                std_return = np.std(daily_returns) if len(daily_returns) > 1 else 0.0001
                sharpe_ratio = avg_return / std_return * np.sqrt(252) if std_return > 0 else 0
            else:
                sharpe_ratio = 0
            
            winning_days = sum(1 for r in daily_returns if r > 0)
            losing_days = sum(1 for r in daily_returns if r < 0)
            
            metrics[agent_id] = {
                "total_return": total_return,
                "annualized_return": annualized_return,
                "max_drawdown": max_drawdown,
                "sharpe_ratio": sharpe_ratio,
                "winning_days": winning_days,
                "losing_days": losing_days,
                "winning_percentage": winning_days / len(daily_returns) if daily_returns else 0
            }
            
        return metrics
    
    def _save_results(self, results: Dict[str, Any]) -> None:
    
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results_file = os.path.join(self.output_dir, f"backtest_results_{timestamp}.json")
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
        print(f"Results saved to {results_file}")
        
        self._generate_performance_charts(results, timestamp)
    
    def _generate_performance_charts(self, results: Dict[str, Any], timestamp: str) -> None:
        try:
            daily_results = results["daily_results"]
            
            dates = []
            portfolio_values = {agent_id: [] for agent_id in self.personalities}
            
            for day in daily_results:
                dates.append(datetime.strptime(day["date"], "%Y-%m-%d"))
                
                for agent_id in self.personalities:
                    backtest_agent_id = f"backtest_{agent_id}_agent"
                    
                    if backtest_agent_id in day["agents"] and "portfolio_value" in day["agents"][backtest_agent_id]:
                        portfolio_values[agent_id].append(
                            day["agents"][backtest_agent_id]["portfolio_value"]
                        )
                    else:
                        last_value = portfolio_values[agent_id][-1] if portfolio_values[agent_id] else self.initial_capital
                        portfolio_values[agent_id].append(last_value)
            
            plt.figure(figsize=(12, 8))
            
            for agent_id, values in portfolio_values.items():
                if len(dates) == len(values) and len(values) > 0:
                    plt.plot(dates, values, label=agent_id.capitalize())
            
            plt.title('Agent Performance Comparison')
            plt.xlabel('Date')
            plt.ylabel('Portfolio Value ($)')
            plt.grid(True)
            plt.legend()
            
            chart_file = os.path.join(self.output_dir, f"performance_chart_{timestamp}.png")
            plt.savefig(chart_file)
            plt.close()
            
            print(f"Performance chart saved to {chart_file}")
            
            self._generate_comparison_charts(results, timestamp)
            
        except Exception as e:
            print(f"Error generating performance charts: {e}")
    
    def _generate_comparison_charts(self, results: Dict[str, Any], timestamp: str) -> None:
        try:
            metrics = results["performance_metrics"]
            
            agent_ids = list(metrics.keys())
            total_returns = [metrics[agent_id]["total_return"] * 100 for agent_id in agent_ids]
            
            plt.figure(figsize=(10, 6))
            plt.bar(agent_ids, total_returns)
            plt.title('Total Return by Agent (%)')
            plt.ylabel('Return (%)')
            plt.grid(axis='y')
            
            for i, v in enumerate(total_returns):
                plt.text(i, v + 0.5, f"{v:.2f}%", ha='center')
            
            chart_file = os.path.join(self.output_dir, f"return_comparison_{timestamp}.png")
            plt.savefig(chart_file)
            plt.close()
            
            metrics_to_plot = ['annualized_return', 'max_drawdown', 'sharpe_ratio']
            metric_labels = ['Annualized Return', 'Maximum Drawdown', 'Sharpe Ratio']
            
            for metric, label in zip(metrics_to_plot, metric_labels):
                values = [metrics[agent_id][metric] for agent_id in agent_ids]
                
                if metric == 'annualized_return' or metric == 'max_drawdown':
                    values = [v * 100 for v in values] 
                
                plt.figure(figsize=(10, 6))
                plt.bar(agent_ids, values)
                plt.title(f'{label} by Agent')
                plt.ylabel(f'{label} {"(%)" if "return" in metric.lower() or "drawdown" in metric.lower() else ""}')
                plt.grid(axis='y')
                
                for i, v in enumerate(values):
                    suffix = "%" if "return" in metric.lower() or "drawdown" in metric.lower() else ""
                    plt.text(i, v + (max(values) * 0.02), f"{v:.2f}{suffix}", ha='center')
                
                metric_file = os.path.join(self.output_dir, f"{metric}_comparison_{timestamp}.png")
                plt.savefig(metric_file)
                plt.close()
            
            print(f"Comparison charts saved to {self.output_dir}")
            
        except Exception as e:
            print(f"Error generating comparison charts: {e}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Backtest Technical Analysis Agents")
    
    parser.add_argument("--tickers", type=str, nargs="+", default=DEFAULT_TICKERS,
                        help="Stock tickers to include in backtest")
    parser.add_argument("--personalities", type=str, nargs="+", default=DEFAULT_PERSONALITIES,
                        help="Agent personalities to test")
    parser.add_argument("--start-date", type=str, 
                        help="Backtest start date (YYYY-MM-DD, default: 1 year ago)")
    parser.add_argument("--end-date", type=str,
                        help="Backtest end date (YYYY-MM-DD, default: today)")
    parser.add_argument("--capital", type=float, default=100000.0,
                        help="Initial capital for each agent")
    parser.add_argument("--commission", type=float, default=0.001,
                        help="Trading commission as a fraction (e.g., 0.001 = 0.1%)")
    parser.add_argument("--output-dir", type=str, default=BACKTEST_DIR,
                        help="Directory to save backtest results")
    
    args = parser.parse_args()
    
    backtester = Backtester(
        tickers=args.tickers,
        personalities=args.personalities,
        initial_capital=args.capital,
        start_date=args.start_date,
        end_date=args.end_date,
        commission=args.commission,
        output_dir=args.output_dir
    )
    
    results = backtester.run_backtest()
    

    print("\nBacktest Summary:")
    print("-" * 80)
    print(f"Period: {results['backtest_config']['start_date']} to {results['backtest_config']['end_date']}")
    print(f"Tickers: {', '.join(results['backtest_config']['tickers'])}")
    print(f"Initial capital: ${results['backtest_config']['initial_capital']:,.2f}")
    print(f"Commission: {results['backtest_config']['commission'] * 100:.2f}%")
    print("-" * 80)
    

    print("\nPerformance Metrics:")
    print("-" * 80)
    for agent_id, metrics in results["performance_metrics"].items():
        print(f"{agent_id.capitalize()} Agent:")
        print(f"  Total Return: {metrics['total_return'] * 100:.2f}%")
        print(f"  Annualized Return: {metrics['annualized_return'] * 100:.2f}%")
        print(f"  Maximum Drawdown: {metrics['max_drawdown'] * 100:.2f}%")
        print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"  Win Rate: {metrics['winning_percentage'] * 100:.2f}% ({metrics['winning_days']} winning days, {metrics['losing_days']} losing days)")
        print()
    

    best_agent = max(results["performance_metrics"].items(), 
                    key=lambda x: x[1]["total_return"])
    
    print("-" * 80)
    print(f"Best performing agent: {best_agent[0].capitalize()} with {best_agent[1]['total_return'] * 100:.2f}% return")
    print("-" * 80)


if __name__ == "__main__":
    main()