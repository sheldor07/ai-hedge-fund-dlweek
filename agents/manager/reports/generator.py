import logging
import anthropic
import jinja2
import os
from datetime import datetime
from typing import Dict, Any
from ..config import settings
from ..database.schema import StockAnalysis, Report

logger = logging.getLogger(settings.APP_NAME)

class ReportGenerator:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(settings.TEMPLATES_DIR)
        )
    
    async def generate_report(self, analysis: StockAnalysis, format: str = "html") -> Report:
        logger.info(f"Generating {format} report for {analysis.stock_symbol}")
        
        report_content = await self._generate_report_content(analysis, format)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{analysis.stock_symbol}_{timestamp}.{format}"
        file_path = os.path.join(settings.GENERATED_REPORTS_DIR, filename)
        
        with open(file_path, "w") as f:
            f.write(report_content)
        
        report = Report(
            stock_symbol=analysis.stock_symbol,
            analysis_id=analysis.id,
            content=report_content,
            format=format
        )
        
        return report
    
    async def _generate_report_content(self, analysis: StockAnalysis, format: str) -> str:
        if format == "html":
            return await self._generate_html_report(analysis)
        elif format == "markdown" or format == "md":
            return await self._generate_markdown_report(analysis)
        else:
            raise ValueError(f"Unsupported report format: {format}")
    
    async def _generate_html_report(self, analysis: StockAnalysis) -> str:
        template = self.template_env.get_template("comprehensive_report.html")
        
        context = self._prepare_report_context(analysis)
        
        return template.render(**context)
    
    async def _generate_markdown_report(self, analysis: StockAnalysis) -> str:
        prompt = self._build_markdown_report_prompt(analysis)
        
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error generating markdown report with LLM: {str(e)}")
            raise
    
    def _prepare_report_context(self, analysis: StockAnalysis) -> Dict[str, Any]:
        context = {
            "stock_symbol": analysis.stock_symbol,
            "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fundamental_data": analysis.fundamental_data or {},
            "technical_data": analysis.technical_data or {},
            "combined_analysis": analysis.combined_analysis or {}
        }
        
        return context
    
    def _build_markdown_report_prompt(self, analysis: StockAnalysis) -> str:
        prompt = f"""
        Generate a comprehensive investment analysis report for {analysis.stock_symbol} in Markdown format.
        
        Include the following sections:
        
        1. Executive Summary
        2. Fundamental Analysis
           - Key Financial Metrics
           - Growth Analysis
           - Valuation Assessment
        3. Technical Analysis
           - Price Trends
           - Technical Indicators
           - Pattern Recognition
        4. Combined Insights
           - Strengths
           - Weaknesses
           - Opportunities
           - Threats
        5. Investment Recommendation
        
        Use the following data for the report:
        
        Fundamental Data:
        ```
        {analysis.fundamental_data}
        ```
        
        Technical Data:
        ```
        {analysis.technical_data}
        ```
        
        Combined Analysis:
        ```
        {analysis.combined_analysis}
        ```
        
        Format the report nicely with appropriate Markdown headers, bullet points, and emphasis.
        """
        
        return prompt