"""
Comparable company analysis module.
"""

import logging
from datetime import datetime
import pandas as pd
import numpy as np

from database.operations import db_ops
from database.schema import FINANCIAL_METRICS_COLLECTION, VALUATION_MODELS_COLLECTION

logger = logging.getLogger("stock_analyzer.analysis.valuation.comparable")


class ComparableAnalysis:
    """
    Implements comparable company analysis for stock valuation.
    """
    
    def __init__(self):
        """Initialize the ComparableAnalysis."""
        self.db_ops = db_ops
    
    def build_comparable_model(self, ticker, peers=None):
        """
        Build a comparable company analysis model for a ticker.
        
        Args:
            ticker (str): The stock ticker symbol.
            peers (list, optional): List of peer companies. Defaults to None.
            
        Returns:
            dict: The comparable analysis results.
        """
        try:
            ticker = ticker.upper()
            
            # Get company info to determine industry/sector
            company = self.db_ops.find_one(
                "companies",
                {"ticker": ticker}
            )
            
            if not company:
                logger.warning(f"No company information found for {ticker}")
                return {}
            
            # If peers are not provided, try to find them automatically
            if not peers:
                peers = self._find_peers(ticker, company)
            
            # Make sure peers are uppercase
            peers = [p.upper() for p in peers if p.upper() != ticker]
            
            if not peers:
                logger.warning(f"No peer companies found for {ticker}")
                return {}
            
            # Get valuation metrics for ticker and peers
            metrics = self._get_valuation_metrics(ticker, peers)
            
            if not metrics or ticker not in metrics:
                logger.warning(f"No valuation metrics found for {ticker}")
                return {}
            
            # Calculate fair values based on different multiples
            fair_values = self._calculate_fair_values(ticker, metrics)
            
            # Calculate summary statistics
            summary = self._calculate_summary_statistics(metrics, fair_values)
            
            # Save the model to the database
            model_date = datetime.now()
            self._save_comparable_model(ticker, model_date, peers, metrics, fair_values, summary)
            
            return {
                "ticker": ticker,
                "peers": peers,
                "metrics": metrics,
                "fair_values": fair_values,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error building comparable model for {ticker}: {str(e)}")
            return {}
    
    def _find_peers(self, ticker, company, max_peers=10):
        """
        Find peer companies for a ticker.
        
        Args:
            ticker (str): The stock ticker symbol.
            company (dict): The company information.
            max_peers (int, optional): Maximum number of peers to return. Defaults to 10.
            
        Returns:
            list: The peer company tickers.
        """
        try:
            # Get companies in the same industry
            industry = company.get("industry")
            sector = company.get("sector")
            
            if not industry and not sector:
                logger.warning(f"No industry or sector information for {ticker}")
                return []
            
            # Try to find companies in the same industry
            if industry:
                industry_peers = self.db_ops.find_many(
                    "companies",
                    {"industry": industry, "ticker": {"$ne": ticker}},
                    limit=max_peers
                )
                
                if industry_peers and len(industry_peers) >= 3:
                    return [peer["ticker"] for peer in industry_peers]
            
            # If not enough industry peers, look for sector peers
            if sector:
                sector_peers = self.db_ops.find_many(
                    "companies",
                    {"sector": sector, "ticker": {"$ne": ticker}},
                    limit=max_peers
                )
                
                if sector_peers:
                    return [peer["ticker"] for peer in sector_peers]
            
            return []
            
        except Exception as e:
            logger.error(f"Error finding peers for {ticker}: {str(e)}")
            return []
    
    def _get_valuation_metrics(self, ticker, peers):
        """
        Get valuation metrics for a ticker and its peers.
        
        Args:
            ticker (str): The stock ticker symbol.
            peers (list): List of peer company tickers.
            
        Returns:
            dict: The valuation metrics.
        """
        try:
            all_tickers = [ticker] + peers
            metrics = {}
            
            for t in all_tickers:
                # Get financial metrics
                valuation_metrics = self.db_ops.find_one(
                    FINANCIAL_METRICS_COLLECTION,
                    {
                        "ticker": t,
                        "metric_type": "valuation",
                        "period_type": "annual"
                    },
                    {"sort": [("date", -1)]}
                )
                
                profitability_metrics = self.db_ops.find_one(
                    FINANCIAL_METRICS_COLLECTION,
                    {
                        "ticker": t,
                        "metric_type": "profitability",
                        "period_type": "annual"
                    },
                    {"sort": [("date", -1)]}
                )
                
                growth_metrics = self.db_ops.find_one(
                    FINANCIAL_METRICS_COLLECTION,
                    {
                        "ticker": t,
                        "metric_type": "growth",
                        "period_type": "annual"
                    },
                    {"sort": [("date", -1)]}
                )
                
                # Get latest price data
                price_data = self.db_ops.find_one(
                    "price_history",
                    {"ticker": t},
                    {"sort": [("date", -1)]}
                )
                
                if not valuation_metrics or not price_data:
                    continue
                
                # Get company financial data for additional metrics
                financial_statement = self.db_ops.find_one(
                    "financial_statements",
                    {
                        "ticker": t,
                        "period_type": "annual"
                    },
                    {"sort": [("period_end_date", -1)]}
                )
                
                # Combine metrics
                company_metrics = {}
                
                # Add basic price data
                company_metrics["price"] = price_data.get("close", 0)
                
                # Add valuation metrics
                if valuation_metrics and "metrics" in valuation_metrics:
                    for key, value in valuation_metrics["metrics"].items():
                        company_metrics[key] = value
                
                # Add profitability metrics
                if profitability_metrics and "metrics" in profitability_metrics:
                    for key, value in profitability_metrics["metrics"].items():
                        company_metrics[key] = value
                
                # Add growth metrics
                if growth_metrics and "metrics" in growth_metrics:
                    if "cagr" in growth_metrics["metrics"]:
                        for key, value in growth_metrics["metrics"]["cagr"].items():
                            company_metrics[f"cagr_{key}"] = value
                    
                    if "yoy" in growth_metrics["metrics"]:
                        for key, value in growth_metrics["metrics"]["yoy"].items():
                            company_metrics[f"yoy_{key}"] = value
                
                # Add financial statement data if available
                if financial_statement:
                    income_stmt = financial_statement.get("income_statement_standardized", {})
                    balance_sheet = financial_statement.get("balance_sheet_standardized", {})
                    
                    # Calculate enterprise value
                    if "shares_outstanding_diluted" in income_stmt and company_metrics["price"] > 0:
                        market_cap = income_stmt["shares_outstanding_diluted"] * company_metrics["price"]
                        company_metrics["market_cap"] = market_cap
                        
                        # Enterprise value = market cap + debt - cash
                        total_debt = balance_sheet.get("long_term_debt", 0) + balance_sheet.get("short_term_debt", 0)
                        cash = balance_sheet.get("cash_and_equivalents", 0)
                        
                        company_metrics["enterprise_value"] = market_cap + total_debt - cash
                        
                        # Calculate EV/Revenue, EV/EBITDA if not already there
                        if "revenue" in income_stmt and income_stmt["revenue"] > 0:
                            company_metrics["ev_to_revenue"] = company_metrics["enterprise_value"] / income_stmt["revenue"]
                        
                        # Calculate EBITDA if not available
                        if "operating_income" in income_stmt:
                            ebitda = income_stmt["operating_income"]
                            if "depreciation_amortization" in income_stmt:
                                ebitda += income_stmt["depreciation_amortization"]
                            
                            if ebitda > 0:
                                company_metrics["ev_to_ebitda"] = company_metrics["enterprise_value"] / ebitda
                
                metrics[t] = company_metrics
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting valuation metrics for {ticker} and peers: {str(e)}")
            return {}
    
    def _calculate_fair_values(self, ticker, metrics):
        """
        Calculate fair values based on different multiples.
        
        Args:
            ticker (str): The stock ticker symbol.
            metrics (dict): The valuation metrics.
            
        Returns:
            dict: The fair values.
        """
        try:
            ticker_metrics = metrics.get(ticker, {})
            if not ticker_metrics:
                return {}
            
            # Get all peer tickers
            peers = [t for t in metrics.keys() if t != ticker]
            
            # Calculate peer medians for different multiples
            multiples = ["pe_ratio", "price_to_book", "price_to_sales", "ev_to_ebitda", "ev_to_revenue"]
            peer_medians = {}
            
            for multiple in multiples:
                # Get values for peers
                values = [metrics[peer].get(multiple) for peer in peers if multiple in metrics[peer] and metrics[peer][multiple] > 0]
                
                if values:
                    median_value = np.median(values)
                    peer_medians[multiple] = median_value
            
            # Calculate fair values
            fair_values = {}
            
            # P/E Ratio
            if "pe_ratio" in peer_medians and "eps_diluted" in ticker_metrics:
                fair_values["pe_ratio"] = peer_medians["pe_ratio"] * ticker_metrics["eps_diluted"]
            
            # Price to Book
            if "price_to_book" in peer_medians and "book_value_per_share" in ticker_metrics:
                fair_values["price_to_book"] = peer_medians["price_to_book"] * ticker_metrics["book_value_per_share"]
            
            # Price to Sales
            if "price_to_sales" in peer_medians and "revenue_per_share" in ticker_metrics:
                fair_values["price_to_sales"] = peer_medians["price_to_sales"] * ticker_metrics["revenue_per_share"]
            
            # EV/EBITDA
            if "ev_to_ebitda" in peer_medians and "enterprise_value" in ticker_metrics and "market_cap" in ticker_metrics:
                # Get EBITDA from ticker metrics
                ebitda = ticker_metrics["enterprise_value"] / ticker_metrics.get("ev_to_ebitda", 1)
                
                # Calculate implied enterprise value
                implied_ev = peer_medians["ev_to_ebitda"] * ebitda
                
                # Calculate implied equity value (enterprise value - debt + cash)
                implied_equity = implied_ev - (ticker_metrics["enterprise_value"] - ticker_metrics["market_cap"])
                
                # Calculate implied share price
                shares_outstanding = ticker_metrics["market_cap"] / ticker_metrics["price"] if ticker_metrics["price"] > 0 else 0
                
                if shares_outstanding > 0:
                    fair_values["ev_to_ebitda"] = implied_equity / shares_outstanding
            
            # EV/Revenue
            if "ev_to_revenue" in peer_medians and "enterprise_value" in ticker_metrics and "market_cap" in ticker_metrics:
                # Get revenue from ticker metrics
                revenue = ticker_metrics["enterprise_value"] / ticker_metrics.get("ev_to_revenue", 1)
                
                # Calculate implied enterprise value
                implied_ev = peer_medians["ev_to_revenue"] * revenue
                
                # Calculate implied equity value (enterprise value - debt + cash)
                implied_equity = implied_ev - (ticker_metrics["enterprise_value"] - ticker_metrics["market_cap"])
                
                # Calculate implied share price
                shares_outstanding = ticker_metrics["market_cap"] / ticker_metrics["price"] if ticker_metrics["price"] > 0 else 0
                
                if shares_outstanding > 0:
                    fair_values["ev_to_revenue"] = implied_equity / shares_outstanding
            
            return fair_values
            
        except Exception as e:
            logger.error(f"Error calculating fair values for {ticker}: {str(e)}")
            return {}
    
    def _calculate_summary_statistics(self, metrics, fair_values):
        """
        Calculate summary statistics for the comparable analysis.
        
        Args:
            metrics (dict): The valuation metrics.
            fair_values (dict): The calculated fair values.
            
        Returns:
            dict: The summary statistics.
        """
        try:
            if not fair_values:
                return {}
            
            # Calculate average fair value
            values = list(fair_values.values())
            avg_fair_value = np.mean(values)
            median_fair_value = np.median(values)
            min_fair_value = np.min(values)
            max_fair_value = np.max(values)
            
            # Calculate current price
            ticker = list(fair_values.keys())[0].split("_")[0]  # Extract ticker from first key
            current_price = metrics.get(ticker, {}).get("price", 0)
            
            # Calculate upside/downside
            upside = (avg_fair_value / current_price - 1) * 100 if current_price > 0 else 0
            
            # Calculate metrics comparison
            comparison = {}
            for multiple in fair_values.keys():
                if multiple in metrics.get(ticker, {}):
                    ticker_multiple = metrics[ticker][multiple]
                    
                    # Get peer multiples
                    peer_multiples = [
                        metrics[peer].get(multiple) 
                        for peer in metrics 
                        if peer != ticker and multiple in metrics[peer] and metrics[peer][multiple] > 0
                    ]
                    
                    if peer_multiples:
                        peer_median = np.median(peer_multiples)
                        peer_mean = np.mean(peer_multiples)
                        peer_min = np.min(peer_multiples)
                        peer_max = np.max(peer_multiples)
                        
                        # Calculate percentile
                        all_multiples = sorted(peer_multiples + [ticker_multiple])
                        percentile = all_multiples.index(ticker_multiple) / len(all_multiples)
                        
                        comparison[multiple] = {
                            "ticker_value": ticker_multiple,
                            "peer_median": peer_median,
                            "peer_mean": peer_mean,
                            "peer_min": peer_min,
                            "peer_max": peer_max,
                            "percentile": percentile,
                            "premium_discount": (ticker_multiple / peer_median - 1) * 100 if peer_median > 0 else 0
                        }
            
            return {
                "avg_fair_value": avg_fair_value,
                "median_fair_value": median_fair_value,
                "min_fair_value": min_fair_value,
                "max_fair_value": max_fair_value,
                "current_price": current_price,
                "upside_percent": upside,
                "multiple_comparison": comparison
            }
            
        except Exception as e:
            logger.error(f"Error calculating summary statistics: {str(e)}")
            return {}
    
    def _save_comparable_model(self, ticker, date, peers, metrics, fair_values, summary):
        """
        Save the comparable company analysis model to the database.
        
        Args:
            ticker (str): The stock ticker symbol.
            date (datetime): The date of the model.
            peers (list): The peer companies.
            metrics (dict): The valuation metrics.
            fair_values (dict): The calculated fair values.
            summary (dict): The summary statistics.
        """
        try:
            # Create model document
            model_doc = {
                "ticker": ticker,
                "model_type": "comparable",
                "date": date,
                "scenario": "base",  # Comparable analysis doesn't have scenarios like DCF
                "inputs": {
                    "peers": peers,
                    "metrics": metrics
                },
                "assumptions": {},  # No assumptions needed for comparable analysis
                "results": {
                    "fair_values": fair_values,
                    "summary": summary
                },
                "target_price": summary.get("median_fair_value", 0),
                "fair_value": summary.get("median_fair_value", 0)
            }
            
            # Update or insert the model
            self.db_ops.update_one(
                VALUATION_MODELS_COLLECTION,
                {
                    "ticker": ticker,
                    "model_type": "comparable",
                    "date": date
                },
                {"$set": model_doc},
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error saving comparable model for {ticker}: {str(e)}")
    
    def get_latest_comparable_model(self, ticker):
        """
        Get the latest comparable company analysis model for a ticker.
        
        Args:
            ticker (str): The stock ticker symbol.
            
        Returns:
            dict: The comparable company analysis model.
        """
        try:
            ticker = ticker.upper()
            
            # Get the latest model
            model = self.db_ops.find_one(
                VALUATION_MODELS_COLLECTION,
                {
                    "ticker": ticker,
                    "model_type": "comparable"
                },
                {"sort": [("date", -1)]}
            )
            
            if not model:
                logger.warning(f"No comparable model found for {ticker}")
                return {}
            
            return {
                "ticker": ticker,
                "date": model["date"],
                "peers": model["inputs"].get("peers", []),
                "metrics": model["inputs"].get("metrics", {}),
                "fair_values": model["results"].get("fair_values", {}),
                "summary": model["results"].get("summary", {})
            }
            
        except Exception as e:
            logger.error(f"Error getting latest comparable model for {ticker}: {str(e)}")
            return {}