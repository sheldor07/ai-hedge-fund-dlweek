import logging
import asyncio
from typing import Dict, Any, List, Optional
from ..config import settings
from ..database.schema import Task, StockAnalysis, TradeDecision, Report, TaskStatus, TaskType, AnalysisType
from ..database.operations import TaskOperations, AnalysisOperations, DecisionOperations, ReportOperations
from .fundamental import FundamentalClient
from .technical import TechnicalClient
from .decision import DecisionAnalyzer
from ..reports import ReportGenerator

logger = logging.getLogger(settings.APP_NAME)

class TaskProcessor:
    def __init__(self):
        self.fundamental_client = FundamentalClient()
        self.technical_client = TechnicalClient()
        self.decision_analyzer = DecisionAnalyzer()
        self.report_generator = ReportGenerator()
    
    async def process_pending_tasks(self, limit: int = 5):
        pending_tasks = TaskOperations.get_pending_tasks(limit)
        
        if not pending_tasks:
            logger.info("No pending tasks to process")
            return
        
        logger.info(f"Processing {len(pending_tasks)} pending tasks")
        
        for task in pending_tasks:
            try:
                TaskOperations.update_task_status(task.id, TaskStatus.IN_PROGRESS)
                
                if task.type == TaskType.ANALYSIS:
                    await self.process_analysis_task(task)
                elif task.type == TaskType.REPORT:
                    await self.process_report_task(task)
                elif task.type == TaskType.DECISION:
                    await self.process_decision_task(task)
                else:
                    raise ValueError(f"Unknown task type: {task.type}")
                
                TaskOperations.update_task_status(task.id, TaskStatus.COMPLETED)
                
            except Exception as e:
                logger.error(f"Error processing task {task.id}: {str(e)}")
                TaskOperations.update_task_status(task.id, TaskStatus.FAILED, error=str(e))
    
    async def process_analysis_task(self, task: Task):
        logger.info(f"Processing analysis task for {task.stock_symbol}")
        
        stock_symbol = task.stock_symbol
        analysis_type = task.analysis_type
        time_frame = task.parameters.get("time_frame", "1y")
        
        fundamental_data = None
        technical_data = None
        combined_analysis = None
        
        if analysis_type in [AnalysisType.FUNDAMENTAL, AnalysisType.COMBINED]:
            fundamental_data = await self._get_fundamental_data(stock_symbol, time_frame)
        
        if analysis_type in [AnalysisType.TECHNICAL, AnalysisType.COMBINED]:
            technical_data = await self._get_technical_data(stock_symbol)
        
        if analysis_type == AnalysisType.COMBINED:
            combined_analysis = await self._combine_analyses(stock_symbol, fundamental_data, technical_data)
        
        analysis = StockAnalysis(
            stock_symbol=stock_symbol,
            analysis_type=analysis_type,
            fundamental_data=fundamental_data,
            technical_data=technical_data,
            combined_analysis=combined_analysis
        )
        
        analysis = AnalysisOperations.create_analysis(analysis)
        
        TaskOperations.update_task_status(
            task.id, 
            TaskStatus.COMPLETED, 
            result={"analysis_id": analysis.id}
        )
        
        return analysis
    
    async def process_report_task(self, task: Task):
        logger.info(f"Processing report task for {task.stock_symbol}")
        
        stock_symbol = task.stock_symbol
        analysis_id = task.parameters.get("analysis_id")
        format = task.parameters.get("format", "html")
        
        if not analysis_id:
            latest_analysis = AnalysisOperations.get_latest_analysis(stock_symbol, AnalysisType.COMBINED)
            if not latest_analysis:
                raise ValueError(f"No analysis found for {stock_symbol}")
            analysis_id = latest_analysis.id
        
        analysis = AnalysisOperations.get_analysis(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis with ID {analysis_id} not found")
        
        report = await self.report_generator.generate_report(analysis, format)
        
        report = ReportOperations.create_report(report)
        
        AnalysisOperations.update_analysis(analysis_id, {"report_id": report.id})
        
        TaskOperations.update_task_status(
            task.id, 
            TaskStatus.COMPLETED, 
            result={"report_id": report.id}
        )
        
        return report
    
    async def process_decision_task(self, task: Task):
        logger.info(f"Processing decision task for {task.stock_symbol}")
        
        stock_symbol = task.stock_symbol
        analysis_id = task.parameters.get("analysis_id")
        
        if not analysis_id:
            latest_analysis = AnalysisOperations.get_latest_analysis(stock_symbol, AnalysisType.COMBINED)
            if not latest_analysis:
                raise ValueError(f"No analysis found for {stock_symbol}")
            analysis_id = latest_analysis.id
        
        analysis = AnalysisOperations.get_analysis(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis with ID {analysis_id} not found")
        
        decision = await self.decision_analyzer.analyze_and_decide(analysis)
        
        decision = DecisionOperations.create_decision(decision)
        
        TaskOperations.update_task_status(
            task.id, 
            TaskStatus.COMPLETED, 
            result={"decision_id": decision.id}
        )
        
        return decision
    
    async def _get_fundamental_data(self, stock_symbol: str, time_frame: str) -> Dict[str, Any]:
        try:
            financial_analysis = await self.fundamental_client.get_financial_analysis(stock_symbol, time_frame)
            valuation = await self.fundamental_client.get_valuation(stock_symbol)
            risk_assessment = await self.fundamental_client.get_risk_assessment(stock_symbol)
            
            return {
                "financial": financial_analysis.get("financial", {}),
                "ratios": financial_analysis.get("ratios", {}),
                "growth": financial_analysis.get("growth", {}),
                "valuation": valuation,
                "risk": risk_assessment
            }
        except Exception as e:
            logger.error(f"Error getting fundamental data for {stock_symbol}: {str(e)}")
            raise
    
    async def _get_technical_data(self, stock_symbol: str) -> Dict[str, Any]:
        try:
            technical_analysis = await self.technical_client.get_technical_analysis(stock_symbol)
            prediction = await self.technical_client.get_prediction(stock_symbol)
            indicators = await self.technical_client.get_indicators(
                stock_symbol, 
                ["rsi", "macd", "bollinger", "moving_averages"]
            )
            
            return {
                "indicators": indicators,
                "patterns": technical_analysis.get("patterns", []),
                "trend": technical_analysis.get("trend", {}),
                "prediction": prediction
            }
        except Exception as e:
            logger.error(f"Error getting technical data for {stock_symbol}: {str(e)}")
            raise
    
    async def _combine_analyses(self, stock_symbol: str, fundamental_data: Dict[str, Any], technical_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            combined_data = {
                "fundamental_summary": self._extract_fundamental_summary(fundamental_data),
                "technical_summary": self._extract_technical_summary(technical_data),
                "swot": self._generate_swot(stock_symbol, fundamental_data, technical_data)
            }
            
            analysis = StockAnalysis(
                stock_symbol=stock_symbol,
                analysis_type=AnalysisType.COMBINED,
                fundamental_data=fundamental_data,
                technical_data=technical_data,
                combined_analysis=combined_data
            )
            
            decision = await self.decision_analyzer.analyze_and_decide(analysis)
            
            combined_data["recommendation"] = decision.recommendation
            combined_data["confidence"] = decision.confidence
            combined_data["explanation"] = decision.explanation
            
            return combined_data
        except Exception as e:
            logger.error(f"Error combining analyses for {stock_symbol}: {str(e)}")
            raise
    
    def _extract_fundamental_summary(self, fundamental_data: Dict[str, Any]) -> str:
        if not fundamental_data:
            return "No fundamental data available."
        
        summary_points = []
        
        if "ratios" in fundamental_data:
            ratios = fundamental_data["ratios"]
            if "pe_ratio" in ratios:
                summary_points.append(f"P/E Ratio: {ratios['pe_ratio']}")
        
        if "growth" in fundamental_data:
            growth = fundamental_data["growth"]
            if "revenue_growth" in growth:
                summary_points.append(f"Revenue Growth: {growth['revenue_growth']}%")
        
        if "valuation" in fundamental_data:
            valuation = fundamental_data["valuation"]
            if "fair_value" in valuation:
                summary_points.append(f"Fair Value: ${valuation['fair_value']}")
        
        if not summary_points:
            return "Limited fundamental data available."
        
        return " | ".join(summary_points)
    
    def _extract_technical_summary(self, technical_data: Dict[str, Any]) -> str:
        if not technical_data:
            return "No technical data available."
        
        summary_points = []
        
        if "trend" in technical_data and "direction" in technical_data["trend"]:
            summary_points.append(f"Trend: {technical_data['trend']['direction']}")
        
        if "indicators" in technical_data and "rsi" in technical_data["indicators"]:
            summary_points.append(f"RSI: {technical_data['indicators']['rsi']}")
        
        if "prediction" in technical_data and "direction" in technical_data["prediction"]:
            summary_points.append(f"Prediction: {technical_data['prediction']['direction']}")
        
        if not summary_points:
            return "Limited technical data available."
        
        return " | ".join(summary_points)
    
    def _generate_swot(self, stock_symbol: str, fundamental_data: Dict[str, Any], technical_data: Dict[str, Any]) -> Dict[str, List[str]]:
        swot = {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": []
        }
        
        if fundamental_data:
            if "ratios" in fundamental_data:
                ratios = fundamental_data["ratios"]
                
                if "pe_ratio" in ratios and ratios["pe_ratio"] < 15:
                    swot["strengths"].append("Attractive P/E ratio")
                elif "pe_ratio" in ratios and ratios["pe_ratio"] > 30:
                    swot["weaknesses"].append("High P/E ratio")
                
                if "debt_to_equity" in ratios and ratios["debt_to_equity"] < 0.5:
                    swot["strengths"].append("Low debt levels")
                elif "debt_to_equity" in ratios and ratios["debt_to_equity"] > 1.5:
                    swot["weaknesses"].append("High debt levels")
            
            if "growth" in fundamental_data:
                growth = fundamental_data["growth"]
                
                if "revenue_growth" in growth and growth["revenue_growth"] > 10:
                    swot["strengths"].append("Strong revenue growth")
                elif "revenue_growth" in growth and growth["revenue_growth"] < 0:
                    swot["weaknesses"].append("Declining revenue")
                
                if "earnings_growth" in growth and growth["earnings_growth"] > 15:
                    swot["strengths"].append("Strong earnings growth")
                elif "earnings_growth" in growth and growth["earnings_growth"] < 0:
                    swot["weaknesses"].append("Declining earnings")
            
            if "valuation" in fundamental_data:
                valuation = fundamental_data["valuation"]
                
                if "upside_potential" in valuation and valuation["upside_potential"] > 20:
                    swot["opportunities"].append(f"Significant upside potential of {valuation['upside_potential']}%")
                
                if "downside_risk" in valuation and valuation["downside_risk"] > 15:
                    swot["threats"].append(f"Downside risk of {valuation['downside_risk']}%")
        
        if technical_data:
            if "trend" in technical_data:
                trend = technical_data["trend"]
                
                if "direction" in trend and trend["direction"] == "upward":
                    swot["strengths"].append("Strong upward trend")
                elif "direction" in trend and trend["direction"] == "downward":
                    swot["weaknesses"].append("Downward price trend")
            
            if "indicators" in technical_data:
                indicators = technical_data["indicators"]
                
                if "rsi" in indicators:
                    rsi = indicators["rsi"]
                    if isinstance(rsi, (int, float)) and rsi < 30:
                        swot["opportunities"].append("Oversold condition (RSI)")
                    elif isinstance(rsi, (int, float)) and rsi > 70:
                        swot["threats"].append("Overbought condition (RSI)")
            
            if "patterns" in technical_data and technical_data["patterns"]:
                bullish_patterns = [p for p in technical_data["patterns"] if "bullish" in p.lower()]
                bearish_patterns = [p for p in technical_data["patterns"] if "bearish" in p.lower()]
                
                if bullish_patterns:
                    swot["opportunities"].append(f"Bullish chart patterns: {', '.join(bullish_patterns)}")
                
                if bearish_patterns:
                    swot["threats"].append(f"Bearish chart patterns: {', '.join(bearish_patterns)}")
        
        return swot