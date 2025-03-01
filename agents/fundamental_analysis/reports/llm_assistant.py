import logging
from typing import Dict, Any, List, Optional
import anthropic
from anthropic.types import MessageParam

from config.settings import ANTHROPIC_API_KEY, LLM_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE

logger = logging.getLogger("stock_analyzer.reports.llm")

class LLMAssistant:
    
    def __init__(self):
        """Initialize the LLM assistant."""
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = LLM_MODEL
        self.max_tokens = LLM_MAX_TOKENS
        self.temperature = LLM_TEMPERATURE
    
    def enhance_company_description(self, ticker: str, description: str) -> str:
        """
        Enhance a company description with more detailed and engaging content.
        
        Args:
            ticker (str): The company ticker symbol
            description (str): The original description
            
        Returns:
            str: Enhanced company description
        """
        prompt = f"""
        You are a financial analyst writing a stock report. Please enhance the following company description 
        for {ticker} to make it more informative and engaging. Keep it concise (max 3-4 sentences),
        but include key information about their business model, products/services, competitive position, 
        and market opportunities.
        
        Original description: 
        {description}
        
        Enhanced description:
        """
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text.strip()
        except Exception as e:
            logger.error(f"Error enhancing company description: {str(e)}")
            return description
    
    def generate_investment_thesis(self, ticker: str, company_data: Dict[str, Any], 
                                  financial_metrics: Dict[str, Any], 
                                  valuation_data: Dict[str, Any]) -> str:

        company_str = "\n".join([f"{k}: {v}" for k, v in company_data.items() if v])
        
        metrics_str = ""
        for category, metrics in financial_metrics.items():
            if metrics:
                metrics_str += f"\n{category.upper()}:\n"
                metrics_str += "\n".join([f"  {k}: {v}" for k, v in metrics.items() if v is not None])
        
        valuation_str = ""
        for model, data in valuation_data.items():
            if data and "fair_value" in data:
                valuation_str += f"\n{model.upper()} Model: ${data['fair_value']:.2f}"
                if "assumptions" in data:
                    valuation_str += "\nAssumptions:\n"
                    valuation_str += "\n".join([f"  {k}: {v}" for k, v in data["assumptions"].items()])
        
        prompt = f"""
        You are a financial analyst writing a stock report for {ticker}. Please generate a concise
        investment thesis (2-3 paragraphs) based on the following information. Focus on why someone 
        should or should not invest in this company, highlighting key strengths, weaknesses, 
        opportunities, and valuation considerations.
        
        COMPANY INFORMATION:
        {company_str}
        
        FINANCIAL METRICS:
        {metrics_str}
        
        VALUATION:
        {valuation_str}
        
        Investment Thesis:
        """
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text.strip()
        except Exception as e:
            logger.error(f"Error generating investment thesis: {str(e)}")
            return f"Investment thesis for {ticker} could not be generated due to insufficient data."
    
    def analyze_financial_results(self, ticker: str, financial_data: Dict[str, Any]) -> str:

        financial_str = ""
        for statement_type, statement in financial_data.items():
            if statement and isinstance(statement, dict):
                financial_str += f"\n{statement_type.upper()}:\n"
                financial_str += "\n".join([f"  {k}: {v}" for k, v in statement.items() if v is not None])
        
        prompt = f"""
        You are a financial analyst reviewing {ticker}'s financial statements. Please provide a concise 
        analysis (1-2 paragraphs) of the company's financial performance based on the following data.
        Focus on key metrics, trends, strengths, and areas of concern.
        
        FINANCIAL DATA:
        {financial_str}
        
        Financial Analysis:
        """
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text.strip()
        except Exception as e:
            logger.error(f"Error analyzing financial results: {str(e)}")
            return "Financial analysis could not be generated due to insufficient data."
    
    def explain_valuation_models(self, ticker: str, valuation_data: Dict[str, Any]) -> str:

        valuation_str = ""
        for model, data in valuation_data.items():
            if data and "fair_value" in data:
                valuation_str += f"\n{model.upper()} Model: ${data['fair_value']:.2f}"
                if "assumptions" in data:
                    valuation_str += "\nAssumptions:\n"
                    valuation_str += "\n".join([f"  {k}: {v}" for k, v in data["assumptions"].items()])
        
        prompt = f"""
        You are a financial analyst explaining valuation models for {ticker}. Please provide a concise
        explanation (1-2 paragraphs) of the following valuation models, what they suggest about the 
        company's fair value, and the key assumptions that drive these valuations.
        
        VALUATION DATA:
        {valuation_str}
        
        Valuation Analysis:
        """
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text.strip()
        except Exception as e:
            logger.error(f"Error explaining valuation models: {str(e)}")
            return "Valuation analysis could not be generated due to insufficient data."
    
    def analyze_risks(self, ticker: str, risk_data: Dict[str, Any]) -> str:


        risk_str = ""
        if "volatility" in risk_data:
            risk_str += "\nVOLATILITY METRICS:\n"
            risk_str += "\n".join([f"  {k}: {v}" for k, v in risk_data["volatility"].items() if v is not None])
        
        if "scenarios" in risk_data and "results" in risk_data["scenarios"]:
            risk_str += "\n\nSCENARIO ANALYSIS:\n"
            for scenario, result in risk_data["scenarios"]["results"].items():
                risk_str += f"\n  {scenario.upper()}:\n"
                risk_str += "\n".join([f"    {k}: {v}" for k, v in result.items() if v is not None])
        
        prompt = f"""
        You are a financial analyst assessing the risks for {ticker}. Please provide a concise
        analysis (1-2 paragraphs) of the following risk metrics and scenarios. Include insights on
        volatility, potential downside risks, and key factors that could impact the investment thesis.
        
        RISK DATA:
        {risk_str}
        
        Risk Analysis:
        """
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text.strip()
        except Exception as e:
            logger.error(f"Error analyzing risks: {str(e)}")
            return "Risk analysis could not be generated due to insufficient data."
    
    def synthesize_news_sentiment(self, ticker: str, news_data: Dict[str, Any]) -> str:
        # Format the news data for the prompt
        news_str = f"Overall Sentiment Score: {news_data.get('sentiment_score', 0)}\n\nRECENT ARTICLES:\n"
        
        if "articles" in news_data:
            for article in news_data["articles"][:5]:  # Limit to 5 articles
                news_str += f"\nTitle: {article.get('title', 'N/A')}"
                news_str += f"\nDate: {article.get('date', 'N/A')}"
                news_str += f"\nSource: {article.get('source', 'N/A')}"
                news_str += f"\nSentiment Score: {article.get('sentiment_score', 0)}"
                news_str += f"\nSummary: {article.get('summary', 'N/A')}"
                news_str += "\n---"
        
        prompt = f"""
        You are a financial analyst summarizing recent news for {ticker}. Please provide a concise
        synthesis (1 paragraph) of the following news articles and sentiment data. Focus on key themes,
        recent developments, and how the news might impact the investment outlook.
        
        NEWS DATA:
        {news_str}
        
        News Synthesis:
        """
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text.strip()
        except Exception as e:
            logger.error(f"Error synthesizing news sentiment: {str(e)}")
            return "News sentiment analysis could not be generated due to insufficient data."