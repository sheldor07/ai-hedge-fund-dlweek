"""
Report generation module.
"""

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
    """
    Generates analysis reports.
    """
    
    def __init__(self, use_llm=True):
        """
        Initialize the ReportGenerator.
        
        Args:
            use_llm (bool): Whether to use LLM for enhancing report content
        """
        self.db_ops = db_ops
        self.template_env = Environment(loader=FileSystemLoader(REPORT_TEMPLATE_DIR))
        self.use_llm = use_llm
        
        # Initialize LLM assistant if enabled
        if self.use_llm:
            self.llm_assistant = LLMAssistant()
        
        # Create reports directory if it doesn't exist
        self.reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", "generated")
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def generate_report(self, ticker, report_type="comprehensive"):
        """
        Generate a report for a ticker.
        
        Args:
            ticker (str): The stock ticker symbol.
            report_type (str, optional): The type of report. Defaults to "comprehensive".
            
        Returns:
            str: The URL of the generated report.
        """
        try:
            ticker = ticker.upper()
            
            # Get company information
            company = self.db_ops.find_one("companies", {"ticker": ticker})
            
            if not company:
                logger.warning(f"No company information found for {ticker}")
                return None
            
            # Get report data based on report type
            report_data = self._get_report_data(ticker, report_type)
            
            if not report_data:
                logger.warning(f"No data available for {ticker} {report_type} report")
                return None
            
            # Generate report content
            report_content = self._generate_report_content(ticker, report_type, company, report_data)
            
            # Save report to file - this is the most important part for the user
            report_url = self._save_report(ticker, report_type, report_content)
            
            # Try to save report to database, but don't fail if this doesn't work
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
        """
        Get data for a report.
        
        Args:
            ticker (str): The stock ticker symbol.
            report_type (str): The type of report.
            
        Returns:
            dict: The report data.
        """
        try:
            report_data = {
                "ticker": ticker,
                "report_type": report_type,
                "report_date": datetime.now()
            }
            
            # Get company information
            company_info = self.db_ops.find_one("companies", {"ticker": ticker})
            
            # Get latest price data
            price_data = self.db_ops.find_one("price_history", {"ticker": ticker})
            
            # Initialize price data even if none is found
            report_data["price"] = {
                "current": price_data.get("close", 0) if price_data else 0,
                "date": price_data.get("date") if price_data else datetime.now().strftime("%Y-%m-%d"),
                "change": (price_data.get("close", 0) - price_data.get("open", 0)) if price_data else 0,
                "change_percent": ((price_data.get("close", 0) / price_data.get("open", 0) - 1) * 100) if price_data and price_data.get("open", 0) else 0
            }
            
            # Get financial statements
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
            
            # Get financial metrics
            for metric_type in ["profitability", "valuation", "growth", "liquidity", "solvency", "efficiency"]:
                metrics = self.db_ops.find_one("financial_metrics", {"ticker": ticker, "metric_type": metric_type, "period_type": "annual"})
                
                if metrics:
                    if "metrics" not in report_data:
                        report_data["metrics"] = {}
                    report_data["metrics"][metric_type] = metrics.get("metrics", {})
            
            # Get valuation models
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
            
            # Get risk metrics
            volatility_metrics = self.db_ops.find_one("volatility_metrics", {"ticker": ticker})
            
            if volatility_metrics:
                report_data["risk"] = {
                    "volatility": volatility_metrics.get("metrics", {})
                }
            
            # Get scenario analysis
            scenario_analysis = self.db_ops.find_one("scenario_analyses", {"ticker": ticker})
            
            if scenario_analysis:
                if "risk" not in report_data:
                    report_data["risk"] = {}
                report_data["risk"]["scenarios"] = {
                    "scenarios": scenario_analysis.get("scenarios", {}),
                    "results": scenario_analysis.get("results", {}),
                    "expected_value": scenario_analysis.get("expected_value", {})
                }
            
            # Get news sentiment
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
            
            # Enhance report with LLM if enabled
            if self.use_llm:
                self._enhance_report_with_llm(ticker, report_data, company_info)
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error getting report data for {ticker}: {str(e)}")
            return None
            
    def _enhance_report_with_llm(self, ticker, report_data, company_info):
        """
        Enhance report data with LLM-generated content.
        
        Args:
            ticker (str): The company ticker symbol
            report_data (dict): The report data to enhance
            company_info (dict): Company information
        """
        try:
            logger.info(f"Enhancing report for {ticker} with LLM")
            
            # Enhance company description if available
            if company_info and "description" in company_info and company_info["description"]:
                try:
                    enhanced_description = self.llm_assistant.enhance_company_description(
                        ticker, company_info["description"]
                    )
                    company_info["enhanced_description"] = enhanced_description
                except Exception as e:
                    logger.error(f"Error enhancing company description: {str(e)}")
            
            # Generate investment thesis
            if report_data.get("metrics") or report_data.get("valuation_models"):
                try:
                    investment_thesis = self.llm_assistant.generate_investment_thesis(
                        ticker,
                        company_info or {},
                        report_data.get("metrics", {}),
                        report_data.get("valuation_models", {})
                    )
                    if "analysis" not in report_data:
                        report_data["analysis"] = {}
                    report_data["analysis"]["investment_thesis"] = investment_thesis
                except Exception as e:
                    logger.error(f"Error generating investment thesis: {str(e)}")
            
            # Analyze financial results
            if report_data.get("financial_statements"):
                try:
                    financial_analysis = self.llm_assistant.analyze_financial_results(
                        ticker,
                        report_data["financial_statements"]
                    )
                    if "analysis" not in report_data:
                        report_data["analysis"] = {}
                    report_data["analysis"]["financial_summary"] = financial_analysis
                except Exception as e:
                    logger.error(f"Error analyzing financial results: {str(e)}")
            
            # Explain valuation models
            if report_data.get("valuation_models"):
                try:
                    valuation_analysis = self.llm_assistant.explain_valuation_models(
                        ticker,
                        report_data["valuation_models"]
                    )
                    if "analysis" not in report_data:
                        report_data["analysis"] = {}
                    report_data["analysis"]["valuation_explanation"] = valuation_analysis
                except Exception as e:
                    logger.error(f"Error explaining valuation models: {str(e)}")
            
            # Analyze risks
            if report_data.get("risk"):
                try:
                    risk_analysis = self.llm_assistant.analyze_risks(
                        ticker,
                        report_data["risk"]
                    )
                    if "analysis" not in report_data:
                        report_data["analysis"] = {}
                    report_data["analysis"]["risk_assessment"] = risk_analysis
                except Exception as e:
                    logger.error(f"Error analyzing risks: {str(e)}")
            
            # Synthesize news sentiment
            if report_data.get("news"):
                try:
                    news_synthesis = self.llm_assistant.synthesize_news_sentiment(
                        ticker,
                        report_data["news"]
                    )
                    if "analysis" not in report_data:
                        report_data["analysis"] = {}
                    report_data["analysis"]["news_summary"] = news_synthesis
                except Exception as e:
                    logger.error(f"Error synthesizing news sentiment: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error enhancing report with LLM: {str(e)}")
    
    def _generate_report_content(self, ticker, report_type, company, report_data):
        """
        Generate report content.
        
        Args:
            ticker (str): The stock ticker symbol.
            report_type (str): The type of report.
            company (dict): The company information.
            report_data (dict): The report data.
            
        Returns:
            str: The report content.
        """
        try:
            # Choose template based on report type
            template_file = f"{report_type}_report.html"
            try:
                template = self.template_env.get_template(template_file)
            except Exception as e:
                logger.error(f"Error loading template {template_file}: {str(e)}")
                # Fall back to default template
                template = self.template_env.get_template("default_report.html")
            
            # Generate charts
            try:
                charts = self._generate_charts(ticker, report_data)
            except Exception as e:
                logger.error(f"Error generating charts for {ticker}: {str(e)}")
                charts = {}
            
            # Prepare template context
            context = {
                "ticker": ticker,
                "company": company,
                "report_data": report_data,
                "charts": charts,
                "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Render template
            try:
                content = template.render(**context)
                return content
            except ZeroDivisionError as e:
                logger.error(f"Error rendering template for {ticker}: {str(e)}")
                return f"<html><body><h1>Error generating report for {ticker}</h1><p>Division by zero error occurred.</p></body></html>"
            except Exception as e:
                logger.error(f"Error rendering template for {ticker}: {str(e)}")
                return f"<html><body><h1>Error generating report for {ticker}</h1><p>{str(e)}</p></body></html>"
            
        except Exception as e:
            logger.error(f"Error generating report content for {ticker}: {str(e)}")
            return f"<html><body><h1>Error generating report for {ticker}</h1><p>{str(e)}</p></body></html>"
    
    def _generate_charts(self, ticker, report_data):
        """
        Generate charts for the report.
        
        Args:
            ticker (str): The stock ticker symbol.
            report_data (dict): The report data.
            
        Returns:
            dict: The chart files.
        """
        try:
            charts = {}
            
            # Create charts directory
            charts_dir = os.path.join(self.reports_dir, ticker, "charts")
            os.makedirs(charts_dir, exist_ok=True)
            
            # Generate price chart
            price_history = self.db_ops.find_many(
                "price_history", 
                {"ticker": ticker}, 
                sort=[("date", 1)],
                limit=252  # 1 year of trading days
            )
            
            if price_history:
                price_chart = self._generate_price_chart(ticker, price_history)
                if price_chart:
                    charts["price"] = price_chart
            
            # Generate financial charts
            if "financial_statements" in report_data:
                financial_charts = self._generate_financial_charts(ticker, report_data)
                if financial_charts:
                    charts.update(financial_charts)
            
            # Generate valuation charts
            if "valuation_models" in report_data:
                valuation_charts = self._generate_valuation_charts(ticker, report_data)
                if valuation_charts:
                    charts.update(valuation_charts)
            
            # Generate risk charts
            if "risk" in report_data:
                risk_charts = self._generate_risk_charts(ticker, report_data)
                if risk_charts:
                    charts.update(risk_charts)
            
            return charts
            
        except Exception as e:
            logger.error(f"Error generating charts for {ticker}: {str(e)}")
            return {}
    
    def _generate_price_chart(self, ticker, price_history):
        """
        Generate price chart.
        
        Args:
            ticker (str): The stock ticker symbol.
            price_history (list): The price history data.
            
        Returns:
            str: The chart file path.
        """
        try:
            chart_file = os.path.join(self.reports_dir, ticker, "charts", "price_chart.png")
            
            # Convert to pandas DataFrame
            df = pd.DataFrame(price_history)
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
            
            # Create figure
            plt.figure(figsize=(10, 6))
            
            # Plot price
            plt.plot(df.index, df["close"], label="Close Price", color="blue")
            
            # Add moving averages
            if len(df) >= 50:
                df["ma50"] = df["close"].rolling(window=50).mean()
                plt.plot(df.index, df["ma50"], label="50-day MA", color="orange")
            
            if len(df) >= 200:
                df["ma200"] = df["close"].rolling(window=200).mean()
                plt.plot(df.index, df["ma200"], label="200-day MA", color="red")
            
            # Add labels and title
            plt.xlabel("Date")
            plt.ylabel("Price ($)")
            plt.title(f"{ticker} Price History")
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Save figure
            plt.savefig(chart_file, dpi=100, bbox_inches="tight")
            plt.close()
            
            return os.path.basename(chart_file)
            
        except Exception as e:
            logger.error(f"Error generating price chart for {ticker}: {str(e)}")
            return None
    
    def _generate_financial_charts(self, ticker, report_data):
        """
        Generate financial charts.
        
        Args:
            ticker (str): The stock ticker symbol.
            report_data (dict): The report data.
            
        Returns:
            dict: The chart files.
        """
        try:
            charts = {}
            
            # Get historical financial data
            financial_statements = self.db_ops.find_many(
                "financial_statements", 
                {"ticker": ticker, "period_type": "annual"}, 
                sort=[("period_end_date", 1)]
            )
            
            if not financial_statements:
                return {}
            
            # Extract key metrics for historical analysis
            dates = []
            revenue = []
            net_income = []
            eps = []
            operating_cash_flow = []
            
            for stmt in financial_statements:
                if "income_statement_standardized" in stmt and "cash_flow_statement_standardized" in stmt:
                    period_date = stmt.get("period_end_date")
                    if period_date:
                        dates.append(period_date)
                        
                        income_stmt = stmt["income_statement_standardized"]
                        cash_flow = stmt["cash_flow_statement_standardized"]
                        
                        revenue.append(income_stmt.get("revenue", 0))
                        net_income.append(income_stmt.get("net_income", 0))
                        eps.append(income_stmt.get("eps_diluted", 0))
                        operating_cash_flow.append(cash_flow.get("net_cash_from_operating_activities", 0))
            
            if not dates:
                return {}
            
            # Revenue and Net Income chart
            chart_file = os.path.join(self.reports_dir, ticker, "charts", "revenue_income_chart.png")
            
            plt.figure(figsize=(10, 6))
            
            fig, ax1 = plt.subplots(figsize=(10, 6))
            
            color = "tab:blue"
            ax1.set_xlabel("Year")
            ax1.set_ylabel("Revenue ($)", color=color)
            ax1.bar(range(len(dates)), revenue, color=color, alpha=0.7, label="Revenue")
            ax1.tick_params(axis="y", labelcolor=color)
            
            ax2 = ax1.twinx()
            
            color = "tab:red"
            ax2.set_ylabel("Net Income ($)", color=color)
            ax2.plot(range(len(dates)), net_income, color=color, marker="o", label="Net Income")
            ax2.tick_params(axis="y", labelcolor=color)
            
            plt.title(f"{ticker} Revenue and Net Income")
            plt.xticks(range(len(dates)), [d.strftime("%Y") for d in dates])
            
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
            
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            plt.savefig(chart_file, dpi=100, bbox_inches="tight")
            plt.close()
            
            charts["revenue_income"] = os.path.basename(chart_file)
            
            # EPS chart
            chart_file = os.path.join(self.reports_dir, ticker, "charts", "eps_chart.png")
            
            plt.figure(figsize=(10, 6))
            
            plt.bar(range(len(dates)), eps, color="green", alpha=0.7)
            
            plt.xlabel("Year")
            plt.ylabel("EPS ($)")
            plt.title(f"{ticker} Earnings Per Share (EPS)")
            plt.xticks(range(len(dates)), [d.strftime("%Y") for d in dates])
            plt.grid(True, alpha=0.3)
            
            plt.savefig(chart_file, dpi=100, bbox_inches="tight")
            plt.close()
            
            charts["eps"] = os.path.basename(chart_file)
            
            # Cash Flow chart
            chart_file = os.path.join(self.reports_dir, ticker, "charts", "cash_flow_chart.png")
            
            plt.figure(figsize=(10, 6))
            
            plt.bar(range(len(dates)), operating_cash_flow, color="purple", alpha=0.7)
            
            plt.xlabel("Year")
            plt.ylabel("Operating Cash Flow ($)")
            plt.title(f"{ticker} Operating Cash Flow")
            plt.xticks(range(len(dates)), [d.strftime("%Y") for d in dates])
            plt.grid(True, alpha=0.3)
            
            plt.savefig(chart_file, dpi=100, bbox_inches="tight")
            plt.close()
            
            charts["cash_flow"] = os.path.basename(chart_file)
            
            return charts
            
        except Exception as e:
            logger.error(f"Error generating financial charts for {ticker}: {str(e)}")
            return {}
    
    def _generate_valuation_charts(self, ticker, report_data):
        """
        Generate valuation charts.
        
        Args:
            ticker (str): The stock ticker symbol.
            report_data (dict): The report data.
            
        Returns:
            dict: The chart files.
        """
        try:
            charts = {}
            
            if "valuation_models" not in report_data:
                return {}
            
            # Fair Value Comparison chart
            chart_file = os.path.join(self.reports_dir, ticker, "charts", "fair_value_chart.png")
            
            plt.figure(figsize=(10, 6))
            
            # Collect fair values from different models
            models = []
            fair_values = []
            
            current_price = report_data.get("price", {}).get("current", 0)
            
            if current_price > 0:
                models.append("Current Price")
                fair_values.append(current_price)
            
            for model_type, model_data in report_data["valuation_models"].items():
                if "fair_value" in model_data and model_data["fair_value"] > 0:
                    models.append(model_type.upper())
                    fair_values.append(model_data["fair_value"])
            
            if not models:
                return {}
            
            # Plot fair values
            colors = ["blue", "green", "red", "orange", "purple"]
            plt.bar(range(len(models)), fair_values, color=colors[:len(models)], alpha=0.7)
            
            plt.xlabel("Valuation Model")
            plt.ylabel("Fair Value ($)")
            plt.title(f"{ticker} Fair Value Comparison")
            plt.xticks(range(len(models)), models)
            plt.grid(True, alpha=0.3)
            
            # Add horizontal line for current price
            if current_price > 0:
                plt.axhline(y=current_price, color="black", linestyle="--", alpha=0.7, label=f"Current Price: ${current_price:.2f}")
                plt.legend()
            
            plt.savefig(chart_file, dpi=100, bbox_inches="tight")
            plt.close()
            
            charts["fair_value"] = os.path.basename(chart_file)
            
            # DCF Sensitivity chart
            if "dcf" in report_data["valuation_models"] and "results" in report_data["valuation_models"]["dcf"]:
                dcf_results = report_data["valuation_models"]["dcf"]["results"]
                
                if "sensitivity" in dcf_results:
                    sensitivity = dcf_results["sensitivity"]
                    
                    if "discount_rate" in sensitivity:
                        chart_file = os.path.join(self.reports_dir, ticker, "charts", "dcf_sensitivity_chart.png")
                        
                        plt.figure(figsize=(10, 6))
                        
                        discount_rates = []
                        fair_values = []
                        
                        for rate, value in sensitivity["discount_rate"].items():
                            try:
                                discount_rates.append(float(rate))
                                fair_values.append(value)
                            except (ValueError, TypeError):
                                continue
                        
                        if discount_rates:
                            # Sort by discount rate
                            sorted_data = sorted(zip(discount_rates, fair_values))
                            discount_rates, fair_values = zip(*sorted_data)
                            
                            plt.plot(discount_rates, fair_values, marker="o", color="blue")
                            
                            plt.xlabel("Discount Rate")
                            plt.ylabel("Fair Value ($)")
                            plt.title(f"{ticker} DCF Sensitivity to Discount Rate")
                            plt.grid(True, alpha=0.3)
                            
                            # Add horizontal line for current price
                            if current_price > 0:
                                plt.axhline(y=current_price, color="red", linestyle="--", alpha=0.7, label=f"Current Price: ${current_price:.2f}")
                                plt.legend()
                            
                            plt.savefig(chart_file, dpi=100, bbox_inches="tight")
                            plt.close()
                            
                            charts["dcf_sensitivity"] = os.path.basename(chart_file)
            
            return charts
            
        except Exception as e:
            logger.error(f"Error generating valuation charts for {ticker}: {str(e)}")
            return {}
    
    def _generate_risk_charts(self, ticker, report_data):
        """
        Generate risk charts.
        
        Args:
            ticker (str): The stock ticker symbol.
            report_data (dict): The report data.
            
        Returns:
            dict: The chart files.
        """
        try:
            charts = {}
            
            if "risk" not in report_data:
                return {}
            
            # Scenario Analysis chart
            if "scenarios" in report_data["risk"]:
                scenarios_data = report_data["risk"]["scenarios"]
                
                if "results" in scenarios_data:
                    chart_file = os.path.join(self.reports_dir, ticker, "charts", "scenarios_chart.png")
                    
                    plt.figure(figsize=(10, 6))
                    
                    scenarios = []
                    target_prices = []
                    probabilities = []
                    
                    current_price = report_data.get("price", {}).get("current", 0)
                    
                    for scenario_name, scenario_result in scenarios_data["results"].items():
                        if "target_price" in scenario_result and scenario_name in scenarios_data.get("scenarios", {}):
                            scenarios.append(scenario_name.title())
                            target_prices.append(scenario_result["target_price"])
                            probabilities.append(scenarios_data["scenarios"][scenario_name].get("probability", 0.33))
                    
                    if not scenarios:
                        return {}
                    
                    # Plot target prices
                    colors = ["green" if tp > current_price else "red" for tp in target_prices]
                    bars = plt.bar(range(len(scenarios)), target_prices, color=colors, alpha=0.7)
                    
                    # Add probability labels
                    for i, (bar, prob) in enumerate(zip(bars, probabilities)):
                        height = bar.get_height()
                        plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                                f"{prob*100:.0f}%",
                                ha="center", va="bottom", rotation=0)
                    
                    plt.xlabel("Scenario")
                    plt.ylabel("Target Price ($)")
                    plt.title(f"{ticker} Scenario Analysis")
                    plt.xticks(range(len(scenarios)), scenarios)
                    plt.grid(True, alpha=0.3)
                    
                    # Add horizontal line for current price
                    if current_price > 0:
                        plt.axhline(y=current_price, color="black", linestyle="--", alpha=0.7, label=f"Current Price: ${current_price:.2f}")
                        plt.legend()
                    
                    plt.savefig(chart_file, dpi=100, bbox_inches="tight")
                    plt.close()
                    
                    charts["scenarios"] = os.path.basename(chart_file)
            
            # Volatility Metrics chart
            if "volatility" in report_data["risk"]:
                volatility_metrics = report_data["risk"]["volatility"]
                
                if volatility_metrics:
                    chart_file = os.path.join(self.reports_dir, ticker, "charts", "volatility_chart.png")
                    
                    plt.figure(figsize=(10, 6))
                    
                    metrics = ["beta", "annualized_volatility", "sharpe_ratio_annualized", "maximum_drawdown"]
                    labels = ["Beta", "Annualized Volatility", "Sharpe Ratio", "Maximum Drawdown"]
                    values = []
                    
                    for metric in metrics:
                        if metric in volatility_metrics:
                            values.append(volatility_metrics[metric])
                        else:
                            values.append(0)
                    
                    # Plot volatility metrics
                    colors = ["blue", "red", "green", "purple"]
                    plt.bar(range(len(labels)), values, color=colors, alpha=0.7)
                    
                    plt.xlabel("Metric")
                    plt.ylabel("Value")
                    plt.title(f"{ticker} Volatility Metrics")
                    plt.xticks(range(len(labels)), labels)
                    plt.grid(True, alpha=0.3)
                    
                    plt.savefig(chart_file, dpi=100, bbox_inches="tight")
                    plt.close()
                    
                    charts["volatility"] = os.path.basename(chart_file)
            
            return charts
            
        except Exception as e:
            logger.error(f"Error generating risk charts for {ticker}: {str(e)}")
            return {}
    
    def _save_report(self, ticker, report_type, report_content):
        """
        Save report to file.
        
        Args:
            ticker (str): The stock ticker symbol.
            report_type (str): The type of report.
            report_content (str): The report content.
            
        Returns:
            str: The report URL.
        """
        try:
            # Create report directory
            report_dir = os.path.join(self.reports_dir, ticker)
            os.makedirs(report_dir, exist_ok=True)
            
            # Generate filename with date
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{ticker}_{report_type}_{date_str}.html"
            
            # Save report to file
            report_path = os.path.join(report_dir, filename)
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            
            # Return report URL
            return f"/reports/{ticker}/{filename}"
            
        except Exception as e:
            logger.error(f"Error saving report for {ticker}: {str(e)}")
            return None
    
    def _save_report_to_db(self, ticker, report_type, report_data, report_url):
        """
        Save report to database.
        
        Args:
            ticker (str): The stock ticker symbol.
            report_type (str): The type of report.
            report_data (dict): The report data.
            report_url (str): The report URL.
        """
        try:
            # Create a safe copy of report data without LLM content to prevent validation issues
            safe_report_data = self._create_db_safe_report_data(report_data)
            
            # Create report document
            report_doc = {
                "ticker": ticker,
                "date": datetime.now(),
                "report_type": report_type,
                "data_snapshot": safe_report_data,
                "report_url": report_url,
                "analysis": {
                    "summary": self._generate_report_summary(ticker, report_data),
                    "key_metrics": self._extract_key_metrics(report_data),
                    "valuation": self._extract_valuation_summary(report_data),
                    "risk_assessment": self._extract_risk_assessment(report_data)
                },
                "recommendations": self._generate_recommendations(ticker, report_data)
            }
            
            # Update or insert the report
            self.db_ops.insert_one(ANALYSIS_REPORTS_COLLECTION, report_doc)
            
        except Exception as e:
            logger.error(f"Error saving report to DB for {ticker}: {str(e)}")
            
    def _create_db_safe_report_data(self, report_data):
        """
        Create a MongoDB-safe version of the report data.
        
        Args:
            report_data (dict): The original report data.
            
        Returns:
            dict: A sanitized copy of the report data safe for MongoDB storage.
        """
        try:
            # Create a deep copy of the report data to avoid modifying the original
            import copy
            safe_data = copy.deepcopy(report_data)
            
            # Remove LLM-generated analysis to prevent validation issues
            if 'analysis' in safe_data:
                # We're removing LLM-specific content from the data_snapshot
                # but keeping it in the rendered HTML report
                del safe_data['analysis']
            
            # Limit string lengths and sanitize content
            self._sanitize_dict_recursively(safe_data)
            
            return safe_data
            
        except Exception as e:
            logger.error(f"Error creating DB-safe report data: {str(e)}")
            # If sanitization fails, return a minimal version with just the basic info
            return {
                "ticker": report_data.get("ticker", ""),
                "report_type": report_data.get("report_type", ""),
                "report_date": report_data.get("report_date", datetime.now())
            }
            
    def _sanitize_dict_recursively(self, data, max_string_length=10000):
        """
        Recursively sanitize a dictionary to ensure it's safe for MongoDB.
        
        Args:
            data: The data to sanitize (dict, list, or scalar value).
            max_string_length (int): Maximum allowed string length.
        """
        if isinstance(data, dict):
            # Process each key-value pair in the dictionary
            for key, value in list(data.items()):  # Use list() to avoid modification during iteration
                # Skip keys that might cause issues or LLM content
                if key in ['enhanced_description', 'investment_thesis', 'financial_summary', 
                          'valuation_explanation', 'risk_assessment', 'news_summary']:
                    del data[key]
                    continue
                    
                # Recursively process nested dictionaries and lists
                if isinstance(value, (dict, list)):
                    self._sanitize_dict_recursively(value, max_string_length)
                elif isinstance(value, str) and len(value) > max_string_length:
                    # Truncate long strings
                    data[key] = value[:max_string_length] + "... [truncated]"
                
        elif isinstance(data, list):
            # Process each item in the list
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    self._sanitize_dict_recursively(item, max_string_length)
                elif isinstance(item, str) and len(item) > max_string_length:
                    data[i] = item[:max_string_length] + "... [truncated]"
    
    def _generate_report_summary(self, ticker, report_data):
        """
        Generate a summary for the report.
        
        Args:
            ticker (str): The stock ticker symbol.
            report_data (dict): The report data.
            
        Returns:
            dict: The report summary.
        """
        try:
            summary = {
                "ticker": ticker,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "price": report_data.get("price", {}).get("current", 0),
                "overview": ""
            }
            
            # Get valuation comparison
            current_price = report_data.get("price", {}).get("current", 0)
            fair_values = []
            
            if "valuation_models" in report_data:
                for model_type, model_data in report_data["valuation_models"].items():
                    if "fair_value" in model_data and model_data["fair_value"] > 0:
                        fair_values.append(model_data["fair_value"])
            
            if fair_values:
                avg_fair_value = sum(fair_values) / len(fair_values)
                upside = (avg_fair_value / current_price - 1) * 100 if current_price > 0 else 0
                
                summary["avg_fair_value"] = avg_fair_value
                summary["upside_percent"] = upside
                
                # Generate overview text
                if upside > 15:
                    rating = "Significantly Undervalued"
                elif upside > 5:
                    rating = "Undervalued"
                elif upside > -5:
                    rating = "Fairly Valued"
                elif upside > -15:
                    rating = "Overvalued"
                else:
                    rating = "Significantly Overvalued"
                
                summary["valuation_rating"] = rating
                
                direction = "upside" if upside > 0 else "downside"
                summary["overview"] = f"{ticker} appears {rating.lower()} with {abs(upside):.1f}% potential {direction} based on our analysis."
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating report summary for {ticker}: {str(e)}")
            return {
                "ticker": ticker,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
    
    def _extract_key_metrics(self, report_data):
        """
        Extract key metrics from report data.
        
        Args:
            report_data (dict): The report data.
            
        Returns:
            dict: The key metrics.
        """
        try:
            metrics = {}
            
            if "metrics" in report_data:
                # Profitability metrics
                if "profitability" in report_data["metrics"]:
                    prof_metrics = report_data["metrics"]["profitability"]
                    metrics["profitability"] = {
                        "gross_margin": prof_metrics.get("gross_margin"),
                        "operating_margin": prof_metrics.get("operating_margin"),
                        "net_profit_margin": prof_metrics.get("net_profit_margin"),
                        "return_on_equity": prof_metrics.get("return_on_equity"),
                        "return_on_assets": prof_metrics.get("return_on_assets")
                    }
                
                # Valuation metrics
                if "valuation" in report_data["metrics"]:
                    val_metrics = report_data["metrics"]["valuation"]
                    metrics["valuation"] = {
                        "pe_ratio": val_metrics.get("pe_ratio"),
                        "price_to_book": val_metrics.get("price_to_book"),
                        "price_to_sales": val_metrics.get("price_to_sales"),
                        "ev_to_ebitda": val_metrics.get("ev_to_ebitda"),
                        "dividend_yield": val_metrics.get("dividend_yield")
                    }
                
                # Growth metrics
                if "growth" in report_data["metrics"]:
                    growth_metrics = report_data["metrics"]["growth"]
                    metrics["growth"] = {}
                    
                    if "cagr" in growth_metrics:
                        cagr = growth_metrics["cagr"]
                        metrics["growth"]["revenue_cagr"] = cagr.get("revenue")
                        metrics["growth"]["earnings_cagr"] = cagr.get("net_income")
                        metrics["growth"]["eps_cagr"] = cagr.get("eps")
                    
                    if "yoy" in growth_metrics:
                        yoy = growth_metrics["yoy"]
                        metrics["growth"]["revenue_growth"] = yoy.get("revenue")
                        metrics["growth"]["earnings_growth"] = yoy.get("net_income")
                        metrics["growth"]["eps_growth"] = yoy.get("eps")
            
            # Financial health metrics
            if "metrics" in report_data and "solvency" in report_data["metrics"]:
                solv_metrics = report_data["metrics"]["solvency"]
                metrics["financial_health"] = {
                    "debt_to_equity": solv_metrics.get("debt_to_equity"),
                    "interest_coverage": solv_metrics.get("interest_coverage"),
                    "debt_ratio": solv_metrics.get("debt_ratio")
                }
            
            if "metrics" in report_data and "liquidity" in report_data["metrics"]:
                liq_metrics = report_data["metrics"]["liquidity"]
                if "financial_health" not in metrics:
                    metrics["financial_health"] = {}
                metrics["financial_health"].update({
                    "current_ratio": liq_metrics.get("current_ratio"),
                    "quick_ratio": liq_metrics.get("quick_ratio"),
                    "cash_ratio": liq_metrics.get("cash_ratio")
                })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error extracting key metrics: {str(e)}")
            return {}
    
    def _extract_valuation_summary(self, report_data):
        """
        Extract valuation summary from report data.
        
        Args:
            report_data (dict): The report data.
            
        Returns:
            dict: The valuation summary.
        """
        try:
            valuation = {}
            
            if "valuation_models" in report_data:
                for model_type, model_data in report_data["valuation_models"].items():
                    if "fair_value" in model_data:
                        valuation[model_type] = {
                            "fair_value": model_data["fair_value"],
                            "assumptions": model_data.get("assumptions", {})
                        }
            
            if valuation:
                # Calculate average fair value
                fair_values = [v["fair_value"] for v in valuation.values() if v["fair_value"] > 0]
                if fair_values:
                    valuation["average"] = {
                        "fair_value": sum(fair_values) / len(fair_values),
                        "min_fair_value": min(fair_values),
                        "max_fair_value": max(fair_values)
                    }
                    
                    # Calculate upside/downside
                    current_price = report_data.get("price", {}).get("current", 0)
                    if current_price > 0:
                        avg_fair_value = valuation["average"]["fair_value"]
                        upside = (avg_fair_value / current_price - 1) * 100
                        valuation["average"]["upside_percent"] = upside
            
            return valuation
            
        except Exception as e:
            logger.error(f"Error extracting valuation summary: {str(e)}")
            return {}
    
    def _extract_risk_assessment(self, report_data):
        """
        Extract risk assessment from report data.
        
        Args:
            report_data (dict): The report data.
            
        Returns:
            dict: The risk assessment.
        """
        try:
            risk = {}
            
            if "risk" in report_data:
                # Volatility metrics
                if "volatility" in report_data["risk"]:
                    volatility = report_data["risk"]["volatility"]
                    risk["volatility"] = {
                        "beta": volatility.get("beta"),
                        "annualized_volatility": volatility.get("annualized_volatility"),
                        "sharpe_ratio": volatility.get("sharpe_ratio_annualized"),
                        "maximum_drawdown": volatility.get("maximum_drawdown"),
                        "var_95": volatility.get("var_95_annualized")
                    }
                
                # Scenario analysis
                if "scenarios" in report_data["risk"] and "expected_value" in report_data["risk"]["scenarios"]:
                    expected_value = report_data["risk"]["scenarios"]["expected_value"]
                    risk["scenario_analysis"] = {
                        "expected_price": expected_value.get("expected_price"),
                        "std_dev": expected_value.get("std_dev"),
                        "downside_risk": expected_value.get("downside_risk")
                    }
            
            return risk
            
        except Exception as e:
            logger.error(f"Error extracting risk assessment: {str(e)}")
            return {}
    
    def _generate_recommendations(self, ticker, report_data):
        """
        Generate recommendations based on report data.
        
        Args:
            ticker (str): The stock ticker symbol.
            report_data (dict): The report data.
            
        Returns:
            dict: The recommendations.
        """
        try:
            recommendations = {}
            
            # Get valuation data
            current_price = report_data.get("price", {}).get("current", 0)
            fair_values = []
            
            if "valuation_models" in report_data:
                for model_type, model_data in report_data["valuation_models"].items():
                    if "fair_value" in model_data and model_data["fair_value"] > 0:
                        fair_values.append(model_data["fair_value"])
            
            if fair_values and current_price > 0:
                avg_fair_value = sum(fair_values) / len(fair_values)
                upside = (avg_fair_value / current_price - 1) * 100
                
                # Generate recommendation
                if upside > 25:
                    rating = "Strong Buy"
                    position = "significantly undervalued"
                elif upside > 10:
                    rating = "Buy"
                    position = "undervalued"
                elif upside > -10:
                    rating = "Hold"
                    position = "fairly valued"
                elif upside > -25:
                    rating = "Sell"
                    position = "overvalued"
                else:
                    rating = "Strong Sell"
                    position = "significantly overvalued"
                
                recommendations["rating"] = rating
                recommendations["position"] = position
                recommendations["upside_percent"] = upside
                recommendations["target_price"] = avg_fair_value
                
                # Generate rationale
                rationale = []
                
                # Check if company is profitable
                if "metrics" in report_data and "profitability" in report_data["metrics"]:
                    net_margin = report_data["metrics"]["profitability"].get("net_profit_margin")
                    roe = report_data["metrics"]["profitability"].get("return_on_equity")
                    
                    if net_margin and net_margin > 0.1:  # 10% net margin
                        rationale.append("The company has strong profitability with a net margin of {:.1f}%.".format(net_margin * 100))
                    elif net_margin and net_margin < 0:
                        rationale.append("The company is currently unprofitable with a net margin of {:.1f}%.".format(net_margin * 100))
                    
                    if roe and roe > 0.15:  # 15% ROE
                        rationale.append("The company has good returns on equity at {:.1f}%.".format(roe * 100))
                
                # Check growth metrics
                if "metrics" in report_data and "growth" in report_data["metrics"]:
                    growth_metrics = report_data["metrics"]["growth"]
                    
                    if "cagr" in growth_metrics and "revenue" in growth_metrics["cagr"]:
                        revenue_growth = growth_metrics["cagr"]["revenue"]
                        if revenue_growth and revenue_growth > 0.1:  # 10% growth
                            rationale.append("The company shows strong revenue growth at {:.1f}% CAGR.".format(revenue_growth * 100))
                    
                    if "cagr" in growth_metrics and "net_income" in growth_metrics["cagr"]:
                        earnings_growth = growth_metrics["cagr"]["net_income"]
                        if earnings_growth and earnings_growth > 0.15:  # 15% growth
                            rationale.append("The company shows strong earnings growth at {:.1f}% CAGR.".format(earnings_growth * 100))
                
                # Check valuation metrics
                if "metrics" in report_data and "valuation" in report_data["metrics"]:
                    valuation_metrics = report_data["metrics"]["valuation"]
                    
                    pe_ratio = valuation_metrics.get("pe_ratio")
                    price_to_book = valuation_metrics.get("price_to_book")
                    
                    if pe_ratio and pe_ratio < 15:
                        rationale.append("The stock appears attractively valued with a P/E ratio of {:.1f}.".format(pe_ratio))
                    elif pe_ratio and pe_ratio > 30:
                        rationale.append("The stock has a high P/E ratio of {:.1f}, which may indicate overvaluation.".format(pe_ratio))
                    
                    if price_to_book and price_to_book < 1.5:
                        rationale.append("The stock is trading below {:.1f}x book value, which may indicate undervaluation.".format(price_to_book))
                
                # Check financial health
                if "metrics" in report_data and "solvency" in report_data["metrics"]:
                    solvency_metrics = report_data["metrics"]["solvency"]
                    
                    debt_to_equity = solvency_metrics.get("debt_to_equity")
                    
                    if debt_to_equity and debt_to_equity > 2:
                        rationale.append("The company has a high debt-to-equity ratio of {:.1f}, which may increase financial risk.".format(debt_to_equity))
                    elif debt_to_equity and debt_to_equity < 0.5:
                        rationale.append("The company has a conservative balance sheet with a low debt-to-equity ratio of {:.1f}.".format(debt_to_equity))
                
                recommendations["rationale"] = rationale
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations for {ticker}: {str(e)}")
            return {}