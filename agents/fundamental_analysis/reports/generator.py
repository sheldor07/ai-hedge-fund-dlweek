import logging
import os
from datetime import datetime
import json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from jinja2 import Environment, FileSystemLoader

from config.settings import REPORT_TEMPLATE_DIR
from database.operations import db_ops
from database.schema import ANALYSIS_REPORTS_COLLECTION
from reports.llm_assistant import LLMAssistant

logger = logging.getLogger("stock_analyzer.reports")


class ReportGenerator:
    
    def __init__(self, use_llm=True):
        self.db_ops = db_ops
        self.template_env = Environment(loader=FileSystemLoader(REPORT_TEMPLATE_DIR))
        self.use_llm = use_llm
        
        if self.use_llm:
            self.llm_assistant = LLMAssistant()
        
        self.reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", "generated")
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def generate_report(self, ticker, report_type="comprehensive"):
        try:
            ticker = ticker.upper()
            
            company = self.db_ops.find_one("companies", {"ticker": ticker})
            
            if not company:
                logger.warning(f"No company information found for {ticker}")
                return None
            
            report_data = self._get_report_data(ticker, report_type)
            
            if not report_data:
                logger.warning(f"No data available for {ticker} {report_type} report")
                return None
            
            report_content = self._generate_report_content(ticker, report_type, company, report_data)
            
            report_url = self._save_report(ticker, report_type, report_content)
            
            try:
                self._save_report_to_db(ticker, report_type, report_data, report_url)
            except Exception as db_e:
                logger.error(f"Error saving report to database for {ticker}: {str(db_e)}")
                logger.info("Continuing without database storage - report file was successfully created.")
            
            return report_url
            
        except Exception as e:
            logger.error(f"Error generating report for {ticker}: {str(e)}")
            return None
    
    def _get_report_data(self, ticker, report_type):
        try:
            report_data = {
                "ticker": ticker,
                "report_type": report_type,
                "report_date": datetime.now()
            }
            
            company_info = self.db_ops.find_one("companies", {"ticker": ticker})
            
            price_data = self.db_ops.find_one("price_history", {"ticker": ticker})
            
            report_data["price"] = {
                "current": price_data.get("close", 0) if price_data else 0,
                "date": price_data.get("date") if price_data else datetime.now().strftime("%Y-%m-%d"),
                "change": (price_data.get("close", 0) - price_data.get("open", 0)) if price_data else 0,
                "change_percent": ((price_data.get("close", 0) / price_data.get("open", 0) - 1) * 100) if price_data and price_data.get("open", 0) else 0
            }
            
            financial_statements = self.db_ops.find_many(
                "financial_statements", 
                {"ticker": ticker, "period_type": "annual"}, 
                sort=[("period_end_date", 1)]
            )
            
            if financial_statements:
                report_data["financial_statements"] = {
                    "income_statement": financial_statements[-1].get("income_statement_standardized", {}),
                    "balance_sheet": financial_statements[-1].get("balance_sheet_standardized", {}),
                    "cash_flow": financial_statements[-1].get("cash_flow_statement_standardized", {}),
                    "period_end_date": financial_statements[-1].get("period_end_date")
                }
            
            for metric_type in ["profitability", "valuation", "growth", "liquidity", "solvency", "efficiency"]:
                metrics = self.db_ops.find_one("financial_metrics", {"ticker": ticker, "metric_type": metric_type, "period_type": "annual"})
                
                if metrics:
                    if "metrics" not in report_data:
                        report_data["metrics"] = {}
                    report_data["metrics"][metric_type] = metrics.get("metrics", {})
            
            for model_type in ["dcf", "ddm", "comparable"]:
                model = self.db_ops.find_one("valuation_models", {"ticker": ticker, "model_type": model_type, "scenario": "base"})
                
                if model:
                    if "valuation_models" not in report_data:
                        report_data["valuation_models"] = {}
                    report_data["valuation_models"][model_type] = {
                        "fair_value": model.get("fair_value", 0),
                        "date": model.get("date"),
                        "assumptions": model.get("assumptions", {}),
                        "results": model.get("results", {})
                    }
            
            volatility_metrics = self.db_ops.find_one("volatility_metrics", {"ticker": ticker})
            
            if volatility_metrics:
                report_data["risk"] = {
                    "volatility": volatility_metrics.get("metrics", {})
                }
            
            scenario_analysis = self.db_ops.find_one("scenario_analyses", {"ticker": ticker})
            
            if scenario_analysis:
                if "risk" not in report_data:
                    report_data["risk"] = {}
                report_data["risk"]["scenarios"] = {
                    "scenarios": scenario_analysis.get("scenarios", {}),
                    "results": scenario_analysis.get("results", {}),
                    "expected_value": scenario_analysis.get("expected_value", {})
                }
            
            news_sentiment = self.db_ops.find_many(
                "news_sentiment", 
                {"ticker": ticker}, 
                sort=[("date", -1)],
                limit=10
            )
            
            if news_sentiment:
                report_data["news"] = {
                    "articles": news_sentiment,
                    "sentiment_score": sum(article.get("sentiment_score", 0) for article in news_sentiment) / len(news_sentiment)
                }
            
            if self.use_llm:
                self._enhance_report_with_llm(ticker, report_data, company_info)
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error getting report data for {ticker}: {str(e)}")
            return None
    
    def _enhance_report_with_llm(self, ticker, report_data, company_info):
        try:
            if not self.llm_assistant:
                return
            
            if company_info and "description" in company_info and company_info["description"]:
                enhanced_description = self.llm_assistant.enhance_company_description(
                    ticker, 
                    company_info["description"]
                )
                report_data["enhanced_description"] = enhanced_description
            
            if "metrics" in report_data and "valuation_models" in report_data:
                investment_thesis = self.llm_assistant.generate_investment_thesis(
                    ticker,
                    {k: v for k, v in company_info.items() if k in ["name", "sector", "industry"]},
                    report_data["metrics"],
                    report_data["valuation_models"]
                )
                report_data["investment_thesis"] = investment_thesis
            
            if "financial_statements" in report_data:
                financial_analysis = self.llm_assistant.analyze_financial_results(
                    ticker,
                    report_data["financial_statements"]
                )
                report_data["financial_analysis"] = financial_analysis
            
            if "valuation_models" in report_data:
                valuation_explanation = self.llm_assistant.explain_valuation_models(
                    ticker,
                    report_data["valuation_models"]
                )
                report_data["valuation_explanation"] = valuation_explanation
            
            if "risk" in report_data:
                risk_analysis = self.llm_assistant.analyze_risk_factors(
                    ticker,
                    report_data["risk"]
                )
                report_data["risk_analysis"] = risk_analysis
            
            if "news" in report_data and "articles" in report_data["news"]:
                news_analysis = self.llm_assistant.analyze_news_sentiment(
                    ticker,
                    report_data["news"]["articles"],
                    report_data["news"].get("sentiment_score", 0)
                )
                report_data["news_analysis"] = news_analysis
            
            report_data["recommendations"] = self.llm_assistant.generate_recommendations(
                ticker,
                report_data
            )
            
        except Exception as e:
            logger.error(f"Error enhancing report with LLM for {ticker}: {str(e)}")
    
    def _generate_report_content(self, ticker, report_type, company, report_data):
        try:
            template_name = f"{report_type}_report.html"
            template = self.template_env.get_template(template_name)
            
            context = {
                "company": company,
                "report_data": report_data,
                "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "charts": self._generate_charts(ticker, report_data)
            }
            
            return template.render(**context)
            
        except Exception as e:
            logger.error(f"Error generating report content for {ticker}: {str(e)}")
            
            fallback_template = self.template_env.get_template("basic_report.html")
            return fallback_template.render(
                company=company,
                report_data=report_data,
                generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                error=str(e)
            )
    
    def _generate_charts(self, ticker, report_data):
        charts = {}
        
        try:
            if "price_history" in report_data:
                price_chart = self._generate_price_chart(ticker, report_data["price_history"])
                if price_chart:
                    charts["price"] = price_chart
            
            if "financial_statements" in report_data and "income_statement" in report_data["financial_statements"]:
                revenue_chart = self._generate_revenue_chart(ticker, report_data["financial_statements"])
                if revenue_chart:
                    charts["revenue"] = revenue_chart
            
            if "metrics" in report_data and "valuation" in report_data["metrics"]:
                valuation_chart = self._generate_valuation_chart(ticker, report_data["metrics"]["valuation"])
                if valuation_chart:
                    charts["valuation"] = valuation_chart
            
            if "valuation_models" in report_data:
                fair_value_chart = self._generate_fair_value_chart(ticker, report_data["valuation_models"])
                if fair_value_chart:
                    charts["fair_value"] = fair_value_chart
            
        except Exception as e:
            logger.error(f"Error generating charts for {ticker}: {str(e)}")
        
        return charts
    
    def _generate_price_chart(self, ticker, price_history):
        try:
            if not price_history or len(price_history) < 5:
                return None
            
            chart_path = os.path.join(self.reports_dir, f"{ticker}_price_chart.png")
            
            df = pd.DataFrame(price_history)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            plt.figure(figsize=(10, 6))
            plt.plot(df['date'], df['close'])
            plt.title(f"{ticker} Price History")
            plt.xlabel("Date")
            plt.ylabel("Price ($)")
            plt.grid(True)
            plt.savefig(chart_path)
            plt.close()
            
            return os.path.basename(chart_path)
            
        except Exception as e:
            logger.error(f"Error generating price chart for {ticker}: {str(e)}")
            return None
    
    def _generate_revenue_chart(self, ticker, financial_statements):
        try:
            if not financial_statements or "income_statement" not in financial_statements:
                return None
            
            chart_path = os.path.join(self.reports_dir, f"{ticker}_revenue_chart.png")
            
            income_statement = financial_statements["income_statement"]
            
            if not income_statement or "revenue" not in income_statement:
                return None
            
            plt.figure(figsize=(8, 5))
            plt.bar(["Revenue"], [income_statement["revenue"]])
            plt.title(f"{ticker} Revenue")
            plt.ylabel("Amount ($)")
            plt.grid(True, axis='y')
            plt.savefig(chart_path)
            plt.close()
            
            return os.path.basename(chart_path)
            
        except Exception as e:
            logger.error(f"Error generating revenue chart for {ticker}: {str(e)}")
            return None
    
    def _generate_valuation_chart(self, ticker, valuation_metrics):
        try:
            if not valuation_metrics:
                return None
            
            chart_path = os.path.join(self.reports_dir, f"{ticker}_valuation_chart.png")
            
            metrics = {k: v for k, v in valuation_metrics.items() 
                      if k in ["pe_ratio", "ps_ratio", "pb_ratio", "ev_ebitda"] and v is not None}
            
            if not metrics:
                return None
            
            plt.figure(figsize=(10, 6))
            plt.bar(metrics.keys(), metrics.values())
            plt.title(f"{ticker} Valuation Metrics")
            plt.ylabel("Ratio")
            plt.grid(True, axis='y')
            plt.savefig(chart_path)
            plt.close()
            
            return os.path.basename(chart_path)
            
        except Exception as e:
            logger.error(f"Error generating valuation chart for {ticker}: {str(e)}")
            return None
    
    def _generate_fair_value_chart(self, ticker, valuation_models):
        try:
            if not valuation_models:
                return None
            
            chart_path = os.path.join(self.reports_dir, f"{ticker}_fair_value_chart.png")
            
            models = {}
            for model_type, model_data in valuation_models.items():
                if "fair_value" in model_data and model_data["fair_value"] is not None:
                    models[model_type] = model_data["fair_value"]
            
            if not models:
                return None
            
            plt.figure(figsize=(10, 6))
            plt.bar(models.keys(), models.values())
            plt.title(f"{ticker} Fair Value Estimates")
            plt.ylabel("Fair Value ($)")
            plt.grid(True, axis='y')
            plt.savefig(chart_path)
            plt.close()
            
            return os.path.basename(chart_path)
            
        except Exception as e:
            logger.error(f"Error generating fair value chart for {ticker}: {str(e)}")
            return None
    
    def _save_report(self, ticker, report_type, report_content):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{ticker}_{report_type}_report_{timestamp}.html"
            report_path = os.path.join(self.reports_dir, filename)
            
            with open(report_path, 'w') as f:
                f.write(report_content)
            
            logger.info(f"Report saved to {report_path}")
            
            return report_path
            
        except Exception as e:
            logger.error(f"Error saving report for {ticker}: {str(e)}")
            return None
    
    def _save_report_to_db(self, ticker, report_type, report_data, report_url):
        try:
            report_doc = {
                "ticker": ticker,
                "date": datetime.now(),
                "report_type": report_type,
                "data_snapshot": report_data,
                "report_url": report_url,
                "recommendations": report_data.get("recommendations", {})
            }
            
            result = self.db_ops.insert_one(ANALYSIS_REPORTS_COLLECTION, report_doc)
            
            if result:
                logger.info(f"Report saved to database with ID: {result}")
            else:
                logger.warning(f"Failed to save report to database for {ticker}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error saving report to database for {ticker}: {str(e)}")
            return None