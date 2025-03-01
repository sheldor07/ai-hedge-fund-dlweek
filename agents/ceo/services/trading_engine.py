import logging
import asyncio
import anthropic
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from ..config import settings
from ..models.trading_plan import TradingPlan, StockAnalysis, TradeAction
from .manager_client import ManagerClient
from .portfolio_client import PortfolioClient

logger = logging.getLogger(settings.APP_NAME)

class TradingEngine:
    def __init__(self):
        self.manager_client = ManagerClient()
        self.portfolio_client = PortfolioClient()
        self.llm_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    async def generate_trading_plan(self, portfolio_id: str, stocks: List[str] = None, budget: float = None) -> TradingPlan:
        logger.info(f"Generating trading plan for portfolio {portfolio_id}")
        
        portfolio = await self.portfolio_client.get_portfolio(portfolio_id)
        hedge_fund = await self.portfolio_client.get_hedge_fund()
        sector_allocation = await self.portfolio_client.get_sector_allocation(portfolio_id)
        
        if not budget:
            budget = settings.DEFAULT_TRADING_BUDGET
        
        if not stocks:
            prompt = self._build_stocks_selection_prompt(portfolio, hedge_fund, sector_allocation)
            stocks = await self._get_stock_recommendations(prompt, settings.MAX_STOCKS_TO_ANALYZE)
        
        trading_plan = TradingPlan(
            name=f"Trading Plan {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            description=f"Automated trading plan generated for portfolio {portfolio_id}",
            portfolio_id=portfolio_id,
            budget=budget,
            target_stocks=stocks
        )
        
        logger.info(f"Created trading plan with {len(stocks)} target stocks")
        return trading_plan
    
    async def execute_trading_plan(self, trading_plan: TradingPlan) -> TradingPlan:
        logger.info(f"Executing trading plan for {len(trading_plan.target_stocks)} stocks")
        
        trading_plan.status = "in_progress"
        
        try:
            await self._analyze_stocks(trading_plan)
            await self._generate_trade_actions(trading_plan)
            
            trading_plan.status = "completed"
            logger.info(f"Completed trading plan execution with {len(trading_plan.actions)} trade actions")
            
        except Exception as e:
            trading_plan.status = "failed"
            logger.error(f"Trading plan execution failed: {str(e)}")
        
        return trading_plan
    
    async def _analyze_stocks(self, trading_plan: TradingPlan):
        logger.info(f"Analyzing {len(trading_plan.target_stocks)} stocks")
        
        analysis_tasks = []
        
        for symbol in trading_plan.target_stocks:
            analysis = StockAnalysis(symbol=symbol)
            trading_plan.analyses.append(analysis)
            
            analysis_task = asyncio.create_task(
                self._analyze_stock(analysis)
            )
            analysis_tasks.append(analysis_task)
        
        await asyncio.gather(*analysis_tasks)
    
    async def _analyze_stock(self, stock_analysis: StockAnalysis):
        logger.info(f"Starting analysis for {stock_analysis.symbol}")
        
        try:
            task = await self.manager_client.create_analysis_task(
                stock_symbol=stock_analysis.symbol, 
                analysis_type="combined"
            )
            
            stock_analysis.task_id = task["id"]
            
            while True:
                task_status = await self.manager_client.get_task_status(task["id"])
                
                if task_status["status"] == "completed":
                    if "result" in task_status and "analysis_id" in task_status["result"]:
                        analysis_id = task_status["result"]["analysis_id"]
                        stock_analysis.analysis_id = analysis_id
                        
                        analysis_data = await self.manager_client.get_completed_analysis(analysis_id)
                        
                        if "fundamental_data" in analysis_data:
                            stock_analysis.fundamental_analysis = analysis_data["fundamental_data"]
                        
                        if "technical_data" in analysis_data:
                            stock_analysis.technical_analysis = analysis_data["technical_data"]
                        
                        if "combined_analysis" in analysis_data:
                            combined = analysis_data["combined_analysis"]
                            if "recommendation" in combined:
                                stock_analysis.recommendation = combined["recommendation"]
                            if "confidence" in combined:
                                stock_analysis.confidence = combined["confidence"]
                    
                    logger.info(f"Completed analysis for {stock_analysis.symbol}")
                    break
                
                elif task_status["status"] == "failed":
                    logger.error(f"Analysis task failed for {stock_analysis.symbol}")
                    break
                
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error(f"Error analyzing stock {stock_analysis.symbol}: {str(e)}")
    
    async def _generate_trade_actions(self, trading_plan: TradingPlan):
        logger.info("Generating trade actions")
        
        positions = await self.portfolio_client.get_positions(trading_plan.portfolio_id)
        
        portfolio_data = {
            "cash": 0,
            "positions": {}
        }
        
        portfolio = await self.portfolio_client.get_portfolio(trading_plan.portfolio_id)
        if portfolio:
            portfolio_data["cash"] = portfolio["cash"]
        
        for position in positions:
            portfolio_data["positions"][position["symbol"]] = {
                "quantity": position["quantity"],
                "avg_price": position["avg_price"],
                "current_price": position["current_price"] if "current_price" in position else position["avg_price"]
            }
        
        prompt = self._build_trade_actions_prompt(trading_plan, portfolio_data)
        trade_actions = await self._get_trade_recommendations(prompt, trading_plan)
        
        trading_plan.actions = trade_actions
    
    def _build_stocks_selection_prompt(self, portfolio: Dict[str, Any], hedge_fund: Dict[str, Any], sector_allocation: Dict[str, float]) -> str:
        current_positions = []
        if "positions" in portfolio:
            for position in portfolio["positions"]:
                current_positions.append(f"{position['symbol']}: {position['quantity']} shares at avg price ${position['avg_price']}")
        
        sectors_str = ""
        for sector, allocation in sector_allocation.items():
            sectors_str += f"{sector}: {allocation:.2f}%\n"
        
        prompt = f"""
        You are the CEO of a hedge fund called {hedge_fund['name']}. Your task is to select promising stocks to analyze for potential trading.

        Portfolio Information:
        - Cash available: ${portfolio['cash']}
        - Current positions:
          {chr(10).join(current_positions)}
        
        Current Sector Allocation:
        {sectors_str}
        
        Select {settings.MAX_STOCKS_TO_ANALYZE} promising stock symbols to analyze for potential trading. 
        Include both stocks we already own that might need position adjustments, and new stocks that could be good opportunities.
        Consider diversification across sectors.
        
        Format your response as a JSON array of stock symbols, for example:
        ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        """
        
        return prompt
    
    def _build_trade_actions_prompt(self, trading_plan: TradingPlan, portfolio_data: Dict[str, Any]) -> str:
        analyses_str = ""
        for analysis in trading_plan.analyses:
            if analysis.recommendation and analysis.confidence:
                analyses_str += f"\n{analysis.symbol}: Recommendation: {analysis.recommendation}, Confidence: {analysis.confidence:.2f}\n"
            else:
                analyses_str += f"\n{analysis.symbol}: Analysis incomplete or failed\n"
        
        positions_str = ""
        for symbol, data in portfolio_data["positions"].items():
            positions_str += f"{symbol}: {data['quantity']} shares at avg price ${data['avg_price']}, current price: ${data.get('current_price', 'unknown')}\n"
        
        prompt = f"""
        You are the CEO of a hedge fund making trading decisions based on analysis results. Generate trade actions (BUY, SELL, or HOLD) for each analyzed stock.

        Trading Plan Information:
        - Budget for this trading session: ${trading_plan.budget}
        - Risk profile: {trading_plan.risk_profile}
        - Max allocation per position: {trading_plan.max_allocation_per_position * 100}% of budget

        Portfolio Information:
        - Cash available: ${portfolio_data['cash']}
        - Current positions:
        {positions_str}

        Stock Analysis Results:
        {analyses_str}

        For each stock, decide whether to BUY, SELL, or HOLD based on the analysis results and portfolio context.
        For BUY decisions, specify quantity and a price limit if appropriate.
        For SELL decisions, specify quantity (can be 'all' to sell entire position).
        
        Your response should be a JSON array of objects with this structure:
        [
            {
                "symbol": "AAPL",
                "action": "BUY",
                "quantity": 10,
                "price_limit": 180.50,
                "confidence": 0.85,
                "rationale": "Strong fundamentals and positive technical indicators"
            },
            {
                "symbol": "MSFT",
                "action": "SELL",
                "quantity": 5,
                "price_limit": null,
                "confidence": 0.75,
                "rationale": "Bearish technical signals and overvaluation concerns"
            }
        ]
        """
        
        return prompt
    
    async def _get_stock_recommendations(self, prompt: str, max_stocks: int) -> List[str]:
        try:
            response = self.llm_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.2,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = response.content[0].text
            
            try:
                # Extract JSON array from response
                import re
                json_match = re.search(r'\[(.*?)\]', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    stocks = json.loads(json_str)
                    return stocks[:max_stocks]
                else:
                    logger.error("Could not find JSON array in LLM response")
                    return []
                    
            except json.JSONDecodeError:
                logger.error("Invalid JSON in LLM response")
                return []
                
        except Exception as e:
            logger.error(f"Error getting stock recommendations: {str(e)}")
            return []
    
    async def _get_trade_recommendations(self, prompt: str, trading_plan: TradingPlan) -> List[TradeAction]:
        try:
            response = self.llm_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                temperature=0.2,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = response.content[0].text
            
            try:
                # Extract JSON array from response
                import re
                json_match = re.search(r'\[(.*?)\]', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    actions_data = json.loads(json_str)
                    
                    actions = []
                    for action_data in actions_data:
                        action = TradeAction(**action_data)
                        actions.append(action)
                    
                    return actions
                else:
                    logger.error("Could not find JSON array in LLM response")
                    return []
                    
            except json.JSONDecodeError:
                logger.error("Invalid JSON in LLM response")
                return []
                
        except Exception as e:
            logger.error(f"Error getting trade recommendations: {str(e)}")
            return []