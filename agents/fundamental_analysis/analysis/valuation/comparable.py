import logging
from datetime import datetime
import pandas as pd
import numpy as np

from database.operations import db_ops
from database.schema import FINANCIAL_METRICS_COLLECTION, VALUATION_MODELS_COLLECTION

logger = logging.getLogger("stock_analyzer.analysis.valuation.comparable")


class ComparableAnalysis:
    
    def __init__(self):
        self.db_ops = db_ops
    
    def build_comparable_model(self, ticker, peers=None):
        try:
            ticker = ticker.upper()
            
            company = self.db_ops.find_one(
                "companies",
                {"ticker": ticker}
            )
            
            if not company:
                logger.warning(f"No company information found for {ticker}")
                return {}
            
            if not peers:
                peers = self._find_peers(ticker, company)
            
            peers = [p.upper() for p in peers if p.upper() != ticker]
            
            if not peers:
                logger.warning(f"No peer companies found for {ticker}")
                return {}
            
            metrics = self._get_valuation_metrics(ticker, peers)
            
            if not metrics or ticker not in metrics:
                logger.warning(f"No valuation metrics found for {ticker}")
                return {}
            
            fair_values = self._calculate_fair_values(ticker, metrics)
            
            summary = self._calculate_summary_statistics(metrics, fair_values)
            
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
        try:
            industry = company.get("industry")
            sector = company.get("sector")
            
            if not industry and not sector:
                logger.warning(f"No industry or sector information for {ticker}")
                return []
            
            if industry:
                industry_peers = self.db_ops.find_many(
                    "companies",
                    {"industry": industry, "ticker": {"$ne": ticker}},
                    limit=max_peers
                )
                
                if industry_peers and len(industry_peers) >= 3:
                    return [peer["ticker"] for peer in industry_peers]
            
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
        try:
            all_tickers = [ticker] + peers
            metrics = {}
            
            for t in all_tickers:
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
                
                price_data = self.db_ops.find_one(
                    "price_history",
                    {"ticker": t},
                    {"sort": [("date", -1)]}
                )
                
                if not valuation_metrics or not price_data:
                    continue
                
                financial_statement = self.db_ops.find_one(
                    "financial_statements",
                    {
                        "ticker": t,
                        "period_type": "annual"
                    },
                    {"sort": [("period_end_date", -1)]}
                )
                
                company_metrics = {}
                
                company_metrics["price"] = price_data.get("close", 0)
                
                if valuation_metrics and "metrics" in valuation_metrics:
                    for key, value in valuation_metrics["metrics"].items():
                        company_metrics[key] = value
                
                if profitability_metrics and "metrics" in profitability_metrics:
                    for key, value in profitability_metrics["metrics"].items():
                        company_metrics[key] = value
                
                if growth_metrics and "metrics" in growth_metrics:
                    if "cagr" in growth_metrics["metrics"]:
                        for key, value in growth_metrics["metrics"]["cagr"].items():
                            company_metrics[f"cagr_{key}"] = value
                    
                    if "yoy" in growth_metrics["metrics"]:
                        for key, value in growth_metrics["metrics"]["yoy"].items():
                            company_metrics[f"yoy_{key}"] = value
                
                if financial_statement:
                    income_stmt = financial_statement.get("income_statement_standardized", {})
                    balance_sheet = financial_statement.get("balance_sheet_standardized", {})
                    
                    market_cap = income_stmt.get("shares_outstanding_diluted", 0) * company_metrics["price"]
                    company_metrics["market_cap"] = market_cap
                    
                    total_debt = balance_sheet.get("long_term_debt", 0) + balance_sheet.get("short_term_debt", 0)
                    cash = balance_sheet.get("cash_and_equivalents", 0)
                    
                    company_metrics["enterprise_value"] = market_cap + total_debt - cash
                    
                    if "revenue" in income_stmt and income_stmt["revenue"] > 0:
                        company_metrics["ev_to_revenue"] = company_metrics["enterprise_value"] / income_stmt["revenue"]
                    
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
        try:
            ticker_metrics = metrics.get(ticker, {})
            if not ticker_metrics:
                return {}
            
            peers = [t for t in metrics.keys() if t != ticker]
            
            multiples = ["pe_ratio", "price_to_book", "price_to_sales", "ev_to_ebitda", "ev_to_revenue"]
            peer_medians = {}
            
            for multiple in multiples:
                values = [metrics[peer].get(multiple) for peer in peers if multiple in metrics[peer] and metrics[peer][multiple] > 0]
                
                if values:
                    median_value = np.median(values)
                    peer_medians[multiple] = median_value
            
            fair_values = {}
            
            if "pe_ratio" in peer_medians and "eps_diluted" in ticker_metrics:
                fair_values["pe_ratio"] = peer_medians["pe_ratio"] * ticker_metrics["eps_diluted"]
            
            if "price_to_book" in peer_medians and "book_value_per_share" in ticker_metrics:
                fair_values["price_to_book"] = peer_medians["price_to_book"] * ticker_metrics["book_value_per_share"]
            
            if "price_to_sales" in peer_medians and "revenue_per_share" in ticker_metrics:
                fair_values["price_to_sales"] = peer_medians["price_to_sales"] * ticker_metrics["revenue_per_share"]
            
            if "ev_to_ebitda" in peer_medians and "enterprise_value" in ticker_metrics and "market_cap" in ticker_metrics:
                ebitda = ticker_metrics["enterprise_value"] / ticker_metrics.get("ev_to_ebitda", 1)
                
                implied_ev = peer_medians["ev_to_ebitda"] * ebitda
                
                implied_equity = implied_ev - (ticker_metrics["enterprise_value"] - ticker_metrics["market_cap"])
                
                shares_outstanding = ticker_metrics["market_cap"] / ticker_metrics["price"] if ticker_metrics["price"] > 0 else 0
                
                if shares_outstanding > 0:
                    fair_values["ev_to_ebitda"] = implied_equity / shares_outstanding
            
            if "ev_to_revenue" in peer_medians and "enterprise_value" in ticker_metrics and "market_cap" in ticker_metrics:
                revenue = ticker_metrics["enterprise_value"] / ticker_metrics.get("ev_to_revenue", 1)
                
                implied_ev = peer_medians["ev_to_revenue"] * revenue
                
                implied_equity = implied_ev - (ticker_metrics["enterprise_value"] - ticker_metrics["market_cap"])
                
                shares_outstanding = ticker_metrics["market_cap"] / ticker_metrics["price"] if ticker_metrics["price"] > 0 else 0
                
                if shares_outstanding > 0:
                    fair_values["ev_to_revenue"] = implied_equity / shares_outstanding
            
            return fair_values
            
        except Exception as e:
            logger.error(f"Error calculating fair values for {ticker}: {str(e)}")
            return {}
    
    def _calculate_summary_statistics(self, metrics, fair_values):
        try:
            if not fair_values:
                return {}
            
            values = list(fair_values.values())
            avg_fair_value = np.mean(values)
            median_fair_value = np.median(values)
            min_fair_value = np.min(values)
            max_fair_value = np.max(values)
            
            ticker = list(fair_values.keys())[0].split("_")[0]  
            current_price = metrics.get(ticker, {}).get("price", 0)
            
            upside = (avg_fair_value / current_price - 1) * 100 if current_price > 0 else 0
            
            comparison = {}
            for multiple in fair_values.keys():
                if multiple in metrics.get(ticker, {}):
                    ticker_multiple = metrics[ticker][multiple]
                    
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
        try:
            model_doc = {
                "ticker": ticker,
                "model_type": "comparable",
                "date": date,
                "scenario": "base",  
                "inputs": {
                    "peers": peers,
                    "metrics": metrics
                },
                "assumptions": {},  
                "results": {
                    "fair_values": fair_values,
                    "summary": summary
                },
                "target_price": summary.get("median_fair_value", 0),
                "fair_value": summary.get("median_fair_value", 0)
            }
            
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
        try:
            ticker = ticker.upper()
            
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