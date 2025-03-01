import logging
import anthropic
from typing import Dict, Any, List, Optional
from ...config import settings
from ...database.schema import StockAnalysis, TradeDecision

logger = logging.getLogger(settings.APP_NAME)

class DecisionAnalyzer:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    async def analyze_and_decide(self, analysis: StockAnalysis) -> TradeDecision:
        logger.info(f"Analyzing data and making a decision for {analysis.stock_symbol}")
        
        fundamental_insights = self._extract_fundamental_insights(analysis.fundamental_data)
        technical_insights = self._extract_technical_insights(analysis.technical_data)
        
        prompt = self._build_decision_prompt(
            stock_symbol=analysis.stock_symbol,
            fundamental_insights=fundamental_insights,
            technical_insights=technical_insights
        )
        
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            decision_text = response.content[0].text
            
            decision_data = self._parse_decision(decision_text)
            
            return TradeDecision(
                stock_symbol=analysis.stock_symbol,
                recommendation=decision_data["recommendation"],
                confidence=decision_data["confidence"],
                analysis_id=analysis.id,
                explanation=decision_data["explanation"]
            )
            
        except Exception as e:
            logger.error(f"Error making decision with LLM: {str(e)}")
            raise
    
    def _extract_fundamental_insights(self, fundamental_data: Optional[Dict[str, Any]]) -> List[str]:
        if not fundamental_data:
            return []
        
        insights = []
        
        if "ratios" in fundamental_data:
            ratios = fundamental_data["ratios"]
            if "pe_ratio" in ratios:
                insights.append(f"PE Ratio: {ratios['pe_ratio']}")
            if "price_to_book" in ratios:
                insights.append(f"Price to Book: {ratios['price_to_book']}")
            if "debt_to_equity" in ratios:
                insights.append(f"Debt to Equity: {ratios['debt_to_equity']}")
        
        if "growth" in fundamental_data:
            growth = fundamental_data["growth"]
            if "revenue_growth" in growth:
                insights.append(f"Revenue Growth: {growth['revenue_growth']}%")
            if "earnings_growth" in growth:
                insights.append(f"Earnings Growth: {growth['earnings_growth']}%")
        
        if "valuation" in fundamental_data:
            valuation = fundamental_data["valuation"]
            if "fair_value" in valuation:
                insights.append(f"Fair Value Estimate: ${valuation['fair_value']}")
            if "upside_potential" in valuation:
                insights.append(f"Upside Potential: {valuation['upside_potential']}%")
        
        return insights
    
    def _extract_technical_insights(self, technical_data: Optional[Dict[str, Any]]) -> List[str]:
        if not technical_data:
            return []
        
        insights = []
        
        if "indicators" in technical_data:
            indicators = technical_data["indicators"]
            if "macd" in indicators:
                insights.append(f"MACD Signal: {indicators['macd']}")
            if "rsi" in indicators:
                insights.append(f"RSI: {indicators['rsi']}")
            if "moving_averages" in indicators:
                insights.append(f"Moving Averages: {indicators['moving_averages']}")
        
        if "patterns" in technical_data:
            patterns = technical_data["patterns"]
            for pattern in patterns:
                insights.append(f"Pattern: {pattern}")
        
        if "prediction" in technical_data:
            prediction = technical_data["prediction"]
            if "direction" in prediction:
                insights.append(f"Predicted Direction: {prediction['direction']}")
            if "price_target" in prediction:
                insights.append(f"Price Target: ${prediction['price_target']}")
        
        return insights
    
    def _build_decision_prompt(self, stock_symbol: str, fundamental_insights: List[str], technical_insights: List[str]) -> str:
        prompt = f"""
        You are a stock market analyst making investment decisions for {stock_symbol}.
        
        Fundamental Analysis Insights:
        {self._format_bullet_points(fundamental_insights)}
        
        Technical Analysis Insights:
        {self._format_bullet_points(technical_insights)}
        
        Based on the above insights, provide a trading recommendation with the following structure:
        
        RECOMMENDATION: [BUY/SELL/HOLD]
        CONFIDENCE: [a number between 0.0 and 1.0 representing your confidence]
        EXPLANATION: [brief explanation for your decision in 2-3 sentences]
        """
        
        return prompt
    
    def _format_bullet_points(self, items: List[str]) -> str:
        if not items:
            return "No insights available."
        
        return "\n".join([f"- {item}" for item in items])
    
    def _parse_decision(self, decision_text: str) -> Dict[str, Any]:
        lines = decision_text.strip().split("\n")
        
        recommendation = "HOLD"
        confidence = 0.5
        explanation = "Insufficient data for a strong recommendation."
        
        for line in lines:
            if line.startswith("RECOMMENDATION:"):
                recommendation = line.replace("RECOMMENDATION:", "").strip()
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.replace("CONFIDENCE:", "").strip())
                except ValueError:
                    pass
            elif line.startswith("EXPLANATION:"):
                explanation = line.replace("EXPLANATION:", "").strip()
        
        return {
            "recommendation": recommendation,
            "confidence": confidence,
            "explanation": explanation
        }