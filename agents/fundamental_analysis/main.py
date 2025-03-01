import argparse
import logging
import sys
from datetime import datetime

from config.logging_config import setup_logging
logger = setup_logging()

from database.schema import setup_database
from database.mongo_client import mongo_client

from data.collectors.edgar_collector import EDGARCollector
from data.collectors.price_collector import PriceDataCollector
from data.collectors.news_collector import NewsCollector
from data.collectors.macro_collector import MacroCollector

from data.parsers.financial_parser import FinancialStatementParser

from analysis.financial.ratio_analyzer import RatioAnalyzer
from analysis.financial.growth_analyzer import GrowthAnalyzer
from analysis.valuation.dcf_model import DCFModel
from analysis.valuation.ddm_model import DDMModel
from analysis.valuation.comparable import ComparableAnalysis
from analysis.risk.volatility import VolatilityAnalyzer
from analysis.risk.scenario import ScenarioAnalysis

from reports.generator import ReportGenerator

from api.routes import start_api


def collect_data(ticker, years=5):
    logger.info(f"Collecting data for {ticker}")
    
    price_collector = PriceDataCollector()
    price_success = price_collector.collect_price_history(ticker, years)
    
    if price_success:
        price_collector.update_technical_indicators(ticker)
    
    edgar_collector = EDGARCollector()
    company_info = edgar_collector.get_company_info(ticker)
    
    if not company_info:
        logger.error(f"Could not find company information for {ticker}")
        return False
    
    annual_data = edgar_collector.get_financial_data(ticker, "annual")
    quarterly_data = edgar_collector.get_financial_data(ticker, "quarterly")
    
    parser = FinancialStatementParser()
    
    if annual_data:
        parser.standardize_financial_statements(ticker, "annual")
        parser.normalize_financial_data(ticker, "annual")
    
    if quarterly_data:
        parser.standardize_financial_statements(ticker, "quarterly")
        parser.normalize_financial_data(ticker, "quarterly")
    
    news_collector = NewsCollector()
    news_collector.collect_news(ticker)
    
    return True


def analyze_stock(ticker):
    logger.info(f"Analyzing {ticker}")
    
    ratio_analyzer = RatioAnalyzer()
    ratio_analyzer.calculate_all_ratios(ticker)
    
    growth_analyzer = GrowthAnalyzer()
    growth_analyzer.calculate_growth_rates(ticker)
    growth_analyzer.forecast_future_growth(ticker)
    
    dcf_model = DCFModel()
    dcf_model.build_dcf_model(ticker)
    
    ddm_model = DDMModel()
    ddm_model.build_ddm_model(ticker)
    
    comparable_model = ComparableAnalysis()
    comparable_model.build_comparable_model(ticker)
    
    volatility_analyzer = VolatilityAnalyzer()
    volatility_analyzer.calculate_volatility_metrics(ticker)
    
    scenario_analyzer = ScenarioAnalysis()
    scenario_analyzer.run_scenario_analysis(ticker)
    
    return True


def generate_report(ticker, report_type="comprehensive", use_llm=True):
    logger.info(f"Generating {report_type} report for {ticker}")
    
    generator = ReportGenerator(use_llm=use_llm)
    report_url = generator.generate_report(ticker, report_type)
    
    if report_url:
        logger.info(f"Report generated successfully: {report_url}")
        return report_url
    else:
        logger.error(f"Failed to generate report for {ticker}")
        return None


def full_analysis(ticker, years=5, report_type="comprehensive", use_llm=True):
    logger.info(f"Starting full analysis for {ticker}")
    
    if not setup_database():
        logger.error("Failed to setup database")
        return None
    
    if not collect_data(ticker, years):
        logger.error(f"Failed to collect data for {ticker}")
        return None
    
    if not analyze_stock(ticker):
        logger.error(f"Failed to analyze {ticker}")
        return None
    
    report_url = generate_report(ticker, report_type, use_llm=use_llm)
    
    return report_url


def main():
    parser = argparse.ArgumentParser(description="Stock Analyzer - Fundamental Analysis Tool")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    collect_parser = subparsers.add_parser("collect", help="Collect data for a ticker")
    collect_parser.add_argument("ticker", help="Stock ticker symbol")
    collect_parser.add_argument("--years", type=int, default=5, help="Number of years of data to collect")
    
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a ticker")
    analyze_parser.add_argument("ticker", help="Stock ticker symbol")
    
    report_parser = subparsers.add_parser("report", help="Generate a report for a ticker")
    report_parser.add_argument("ticker", help="Stock ticker symbol")
    report_parser.add_argument("--type", default="comprehensive", choices=["comprehensive", "valuation", "financial", "risk"], help="Type of report")
    report_parser.add_argument("--no-llm", action="store_true", help="Disable LLM enhancement")
    
    full_parser = subparsers.add_parser("full", help="Run full analysis workflow")
    full_parser.add_argument("ticker", help="Stock ticker symbol")
    full_parser.add_argument("--years", type=int, default=5, help="Number of years of data to collect")
    full_parser.add_argument("--report-type", default="comprehensive", choices=["comprehensive", "valuation", "financial", "risk"], help="Type of report")
    full_parser.add_argument("--no-llm", action="store_true", help="Disable LLM enhancement")
    
    macro_parser = subparsers.add_parser("macro", help="Collect macroeconomic data")
    
    api_parser = subparsers.add_parser("api", help="Start the API server")
    
    args = parser.parse_args()
    
    if not mongo_client.connect():
        logger.error("Failed to connect to MongoDB")
        return 1
    
    try:
        if args.command == "collect":
            collect_data(args.ticker, args.years)
        elif args.command == "analyze":
            analyze_stock(args.ticker)
        elif args.command == "report":
            use_llm = not args.no_llm
            generate_report(args.ticker, args.type, use_llm=use_llm)
        elif args.command == "full":
            use_llm = not args.no_llm
            full_analysis(args.ticker, args.years, args.report_type, use_llm=use_llm)
        elif args.command == "macro":
            macro_collector = MacroCollector()
            macro_collector.collect_macro_data()
        elif args.command == "api":
            start_api()
        else:
            parser.print_help()
            return 1
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        return 1
    finally:
        mongo_client.disconnect()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())