import logging
from datetime import datetime
import pandas as pd

from database.operations import db_ops
from database.schema import FINANCIAL_STATEMENTS_COLLECTION, FINANCIAL_METRICS_COLLECTION

logger = logging.getLogger("stock_analyzer.analysis.financial.ratio")


class RatioAnalyzer:
    
    def __init__(self):
        self.db_ops = db_ops
    
    def calculate_all_ratios(self, ticker, period_type="annual"):
        try:
            ticker = ticker.upper()
            
            financial_statements = self.db_ops.find_many(
                FINANCIAL_STATEMENTS_COLLECTION,
                {"ticker": ticker, "period_type": period_type},
                sort=[("period_end_date", -1)]
            )
            
            if not financial_statements:
                logger.warning(f"No {period_type} financial statements found for {ticker}")
                return False
            
            for statement in financial_statements:
                if not all(key in statement for key in ["income_statement_standardized", "balance_sheet_standardized", "cash_flow_statement_standardized"]):
                    logger.warning(f"Missing standardized statements for {ticker} on {statement.get('period_end_date')}")
                    continue
                
                profitability_ratios = self._calculate_profitability_ratios(statement)
                valuation_ratios = self._calculate_valuation_ratios(ticker, statement)
                growth_ratios = self._calculate_growth_ratios(ticker, statement, financial_statements)
                liquidity_ratios = self._calculate_liquidity_ratios(statement)
                solvency_ratios = self._calculate_solvency_ratios(statement)
                efficiency_ratios = self._calculate_efficiency_ratios(statement)
                
                period_date = statement.get("period_end_date")
                
                self._save_ratios(
                    ticker=ticker,
                    date=period_date,
                    metric_type="profitability",
                    period_type=period_type,
                    metrics=profitability_ratios
                )
                
                self._save_ratios(
                    ticker=ticker,
                    date=period_date,
                    metric_type="valuation",
                    period_type=period_type,
                    metrics=valuation_ratios
                )
                
                self._save_ratios(
                    ticker=ticker,
                    date=period_date,
                    metric_type="growth",
                    period_type=period_type,
                    metrics=growth_ratios
                )
                
                self._save_ratios(
                    ticker=ticker,
                    date=period_date,
                    metric_type="liquidity",
                    period_type=period_type,
                    metrics=liquidity_ratios
                )
                
                self._save_ratios(
                    ticker=ticker,
                    date=period_date,
                    metric_type="solvency",
                    period_type=period_type,
                    metrics=solvency_ratios
                )
                
                self._save_ratios(
                    ticker=ticker,
                    date=period_date,
                    metric_type="efficiency",
                    period_type=period_type,
                    metrics=efficiency_ratios
                )
            
            logger.info(f"Calculated financial ratios for {ticker} ({period_type})")
            return True
            
        except Exception as e:
            logger.error(f"Error calculating financial ratios for {ticker}: {str(e)}")
            return False
    
    def _save_ratios(self, ticker, date, metric_type, period_type, metrics):
        try:
            metrics_doc = {
                "ticker": ticker,
                "date": date,
                "metric_type": metric_type,
                "period_type": period_type,
                "metrics": metrics
            }
            
            self.db_ops.update_one(
                FINANCIAL_METRICS_COLLECTION,
                {
                    "ticker": ticker,
                    "date": date,
                    "metric_type": metric_type,
                    "period_type": period_type
                },
                {"$set": metrics_doc},
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error saving {metric_type} ratios for {ticker}: {str(e)}")
    
    def _calculate_profitability_ratios(self, statement):
        try:
            income_stmt = statement.get("income_statement_standardized", {})
            balance_sheet = statement.get("balance_sheet_standardized", {})
            
            ratios = {}
            
            if "revenue" in income_stmt and "gross_profit" in income_stmt and income_stmt["revenue"] != 0:
                ratios["gross_margin"] = income_stmt["gross_profit"] / income_stmt["revenue"]
            
            if "revenue" in income_stmt and "operating_income" in income_stmt and income_stmt["revenue"] != 0:
                ratios["operating_margin"] = income_stmt["operating_income"] / income_stmt["revenue"]
            
            if "revenue" in income_stmt and "net_income" in income_stmt and income_stmt["revenue"] != 0:
                ratios["net_profit_margin"] = income_stmt["net_income"] / income_stmt["revenue"]
            
            if "net_income" in income_stmt and "total_assets" in balance_sheet and balance_sheet["total_assets"] != 0:
                ratios["return_on_assets"] = income_stmt["net_income"] / balance_sheet["total_assets"]
            
            if "net_income" in income_stmt and "total_equity" in balance_sheet and balance_sheet["total_equity"] != 0:
                ratios["return_on_equity"] = income_stmt["net_income"] / balance_sheet["total_equity"]
            
            if "operating_income" in income_stmt and "total_assets" in balance_sheet and "current_liabilities" in balance_sheet:
                invested_capital = balance_sheet["total_assets"] - balance_sheet.get("current_liabilities", 0)
                if invested_capital != 0:
                    ratios["return_on_invested_capital"] = income_stmt["operating_income"] * (1 - 0.25) / invested_capital
            
            ebitda = income_stmt.get("operating_income", 0) + income_stmt.get("depreciation_amortization", 0)
            if "revenue" in income_stmt and income_stmt["revenue"] != 0:
                ratios["ebitda_margin"] = ebitda / income_stmt["revenue"]
            
            if "operating_income" in income_stmt and "interest_expense" in income_stmt and income_stmt["interest_expense"] != 0:
                ratios["interest_coverage"] = income_stmt["operating_income"] / income_stmt["interest_expense"]
            
            return ratios
            
        except Exception as e:
            logger.error(f"Error calculating profitability ratios: {str(e)}")
            return {}
    
    def _calculate_valuation_ratios(self, ticker, statement):
        try:
            income_stmt = statement.get("income_statement_standardized", {})
            balance_sheet = statement.get("balance_sheet_standardized", {})
            cash_flow = statement.get("cash_flow_statement_standardized", {})
            
            ratios = {}
            
            price_data = self.db_ops.find_one(
                "price_history",
                {"ticker": ticker}
            )
            
            current_price = price_data.get("close", 0) if price_data else 0
            
            if current_price > 0 and "eps_diluted" in income_stmt and income_stmt["eps_diluted"] > 0:
                ratios["pe_ratio"] = current_price / income_stmt["eps_diluted"]
            
            if "total_assets" in balance_sheet and "total_liabilities" in balance_sheet:
                market_cap = current_price * income_stmt.get("shares_outstanding_diluted", 0)
                enterprise_value = market_cap + balance_sheet.get("total_liabilities", 0) - balance_sheet.get("cash_and_equivalents", 0)
                
                ebitda = income_stmt.get("operating_income", 0) + income_stmt.get("depreciation_amortization", 0)
                
                if ebitda > 0:
                    ratios["ev_to_ebitda"] = enterprise_value / ebitda
            
            if current_price > 0 and "total_equity" in balance_sheet and "shares_outstanding_diluted" in income_stmt and income_stmt["shares_outstanding_diluted"] > 0:
                book_value_per_share = balance_sheet["total_equity"] / income_stmt["shares_outstanding_diluted"]
                if book_value_per_share > 0:
                    ratios["price_to_book"] = current_price / book_value_per_share
            
            if current_price > 0 and "revenue" in income_stmt and "shares_outstanding_diluted" in income_stmt and income_stmt["shares_outstanding_diluted"] > 0:
                sales_per_share = income_stmt["revenue"] / income_stmt["shares_outstanding_diluted"]
                if sales_per_share > 0:
                    ratios["price_to_sales"] = current_price / sales_per_share
            
            if current_price > 0 and "net_cash_from_operating_activities" in cash_flow and "shares_outstanding_diluted" in income_stmt and income_stmt["shares_outstanding_diluted"] > 0:
                cash_flow_per_share = cash_flow["net_cash_from_operating_activities"] / income_stmt["shares_outstanding_diluted"]
                if cash_flow_per_share > 0:
                    ratios["price_to_cash_flow"] = current_price / cash_flow_per_share
            
            if current_price > 0 and "dividends_paid" in cash_flow and "shares_outstanding_diluted" in income_stmt and income_stmt["shares_outstanding_diluted"] > 0:
                dividend_per_share = abs(cash_flow.get("dividends_paid", 0)) / income_stmt["shares_outstanding_diluted"]
                ratios["dividend_yield"] = dividend_per_share / current_price
            
            if "net_income" in income_stmt and income_stmt["net_income"] > 0 and "dividends_paid" in cash_flow:
                ratios["dividend_payout_ratio"] = abs(cash_flow.get("dividends_paid", 0)) / income_stmt["net_income"]
            
            return ratios
            
        except Exception as e:
            logger.error(f"Error calculating valuation ratios for {ticker}: {str(e)}")
            return {}
    
    def _calculate_growth_ratios(self, ticker, statement, all_statements):
        try:
            current_date = statement.get("period_end_date")
            
            sorted_statements = sorted(all_statements, key=lambda x: x.get("period_end_date", datetime.min))
            
            prev_year_stmt = None
            for stmt in reversed(sorted_statements):
                stmt_date = stmt.get("period_end_date")
                if stmt_date and stmt_date < current_date and (current_date.year - stmt_date.year) == 1:
                    prev_year_stmt = stmt
                    break
            
            if not prev_year_stmt:
                return {}
            
            current_income = statement.get("income_statement_standardized", {})
            current_balance = statement.get("balance_sheet_standardized", {})
            current_cash_flow = statement.get("cash_flow_statement_standardized", {})
            
            prev_income = prev_year_stmt.get("income_statement_standardized", {})
            prev_balance = prev_year_stmt.get("balance_sheet_standardized", {})
            prev_cash_flow = prev_year_stmt.get("cash_flow_statement_standardized", {})
            
            ratios = {}
            
            if "revenue" in current_income and "revenue" in prev_income and prev_income["revenue"] != 0:
                ratios["revenue_growth"] = (current_income["revenue"] - prev_income["revenue"]) / prev_income["revenue"]
            
            if "net_income" in current_income and "net_income" in prev_income and prev_income["net_income"] != 0:
                ratios["earnings_growth"] = (current_income["net_income"] - prev_income["net_income"]) / prev_income["net_income"]
            
            if "eps_diluted" in current_income and "eps_diluted" in prev_income and prev_income["eps_diluted"] != 0:
                ratios["eps_growth"] = (current_income["eps_diluted"] - prev_income["eps_diluted"]) / prev_income["eps_diluted"]
            
            if "operating_income" in current_income and "operating_income" in prev_income and prev_income["operating_income"] != 0:
                ratios["operating_income_growth"] = (current_income["operating_income"] - prev_income["operating_income"]) / prev_income["operating_income"]
            
            if "net_cash_from_operating_activities" in current_cash_flow and "net_cash_from_operating_activities" in prev_cash_flow and prev_cash_flow["net_cash_from_operating_activities"] != 0:
                ratios["operating_cash_flow_growth"] = (current_cash_flow["net_cash_from_operating_activities"] - prev_cash_flow["net_cash_from_operating_activities"]) / prev_cash_flow["net_cash_from_operating_activities"]
            
            if "free_cash_flow" in current_cash_flow and "free_cash_flow" in prev_cash_flow and prev_cash_flow["free_cash_flow"] != 0:
                ratios["free_cash_flow_growth"] = (current_cash_flow["free_cash_flow"] - prev_cash_flow["free_cash_flow"]) / prev_cash_flow["free_cash_flow"]
            
            if "total_assets" in current_balance and "total_assets" in prev_balance and prev_balance["total_assets"] != 0:
                ratios["total_assets_growth"] = (current_balance["total_assets"] - prev_balance["total_assets"]) / prev_balance["total_assets"]
            
            if "total_equity" in current_balance and "total_equity" in prev_balance and prev_balance["total_equity"] != 0:
                ratios["equity_growth"] = (current_balance["total_equity"] - prev_balance["total_equity"]) / prev_balance["total_equity"]
            
            if "total_equity" in current_balance and "shares_outstanding_diluted" in current_income and "total_equity" in prev_balance and "shares_outstanding_diluted" in prev_income:
                current_bvps = current_balance["total_equity"] / current_income["shares_outstanding_diluted"]
                prev_bvps = prev_balance["total_equity"] / prev_income["shares_outstanding_diluted"]
                
                if prev_bvps != 0:
                    ratios["book_value_per_share_growth"] = (current_bvps - prev_bvps) / prev_bvps
            
            return ratios
            
        except Exception as e:
            logger.error(f"Error calculating growth ratios for {ticker}: {str(e)}")
            return {}
    
    def _calculate_liquidity_ratios(self, statement):
        try:
            balance_sheet = statement.get("balance_sheet_standardized", {})
            
            ratios = {}
            
            if "current_assets" in balance_sheet and "current_liabilities" in balance_sheet and balance_sheet["current_liabilities"] != 0:
                ratios["current_ratio"] = balance_sheet["current_assets"] / balance_sheet["current_liabilities"]
            
            if "current_assets" in balance_sheet and "inventory" in balance_sheet and "current_liabilities" in balance_sheet and balance_sheet["current_liabilities"] != 0:
                quick_assets = balance_sheet["current_assets"] - balance_sheet["inventory"]
                ratios["quick_ratio"] = quick_assets / balance_sheet["current_liabilities"]
            
            if "cash_and_equivalents" in balance_sheet and "short_term_investments" in balance_sheet and "current_liabilities" in balance_sheet and balance_sheet["current_liabilities"] != 0:
                cash_and_equivalents = balance_sheet["cash_and_equivalents"] + balance_sheet.get("short_term_investments", 0)
                ratios["cash_ratio"] = cash_and_equivalents / balance_sheet["current_liabilities"]
            
            if "current_assets" in balance_sheet and "current_liabilities" in balance_sheet:
                ratios["working_capital"] = balance_sheet["current_assets"] - balance_sheet["current_liabilities"]
            
            if "current_assets" in balance_sheet and "current_liabilities" in balance_sheet and "total_assets" in balance_sheet and balance_sheet["total_assets"] != 0:
                working_capital = balance_sheet["current_assets"] - balance_sheet["current_liabilities"]
                ratios["working_capital_to_total_assets"] = working_capital / balance_sheet["total_assets"]
            
            return ratios
            
        except Exception as e:
            logger.error(f"Error calculating liquidity ratios: {str(e)}")
            return {}
    
    def _calculate_solvency_ratios(self, statement):
        try:
            income_stmt = statement.get("income_statement_standardized", {})
            balance_sheet = statement.get("balance_sheet_standardized", {})
            
            ratios = {}
            
            if "total_liabilities" in balance_sheet and "total_assets" in balance_sheet and balance_sheet["total_assets"] != 0:
                ratios["debt_ratio"] = balance_sheet["total_liabilities"] / balance_sheet["total_assets"]
            
            if "total_liabilities" in balance_sheet and "total_equity" in balance_sheet and balance_sheet["total_equity"] != 0:
                ratios["debt_to_equity"] = balance_sheet["total_liabilities"] / balance_sheet["total_equity"]
            
            if "long_term_debt" in balance_sheet and "total_equity" in balance_sheet and balance_sheet["total_equity"] != 0:
                ratios["long_term_debt_to_equity"] = balance_sheet["long_term_debt"] / balance_sheet["total_equity"]
            
            if "total_assets" in balance_sheet and "total_equity" in balance_sheet and balance_sheet["total_equity"] != 0:
                ratios["equity_multiplier"] = balance_sheet["total_assets"] / balance_sheet["total_equity"]
            
            if "operating_income" in income_stmt and "interest_expense" in income_stmt and income_stmt["interest_expense"] != 0:
                ratios["interest_coverage"] = income_stmt["operating_income"] / income_stmt["interest_expense"]
            
            if "net_cash_from_operating_activities" in statement.get("cash_flow_statement_standardized", {}) and "total_liabilities" in balance_sheet and balance_sheet["total_liabilities"] != 0:
                ratios["cash_flow_to_debt"] = statement["cash_flow_statement_standardized"]["net_cash_from_operating_activities"] / balance_sheet["total_liabilities"]
            
            return ratios
            
        except Exception as e:
            logger.error(f"Error calculating solvency ratios: {str(e)}")
            return {}
    
    def _calculate_efficiency_ratios(self, statement):
        try:
            income_stmt = statement.get("income_statement_standardized", {})
            balance_sheet = statement.get("balance_sheet_standardized", {})
            
            ratios = {}
            
            if "revenue" in income_stmt and "total_assets" in balance_sheet and balance_sheet["total_assets"] != 0:
                ratios["asset_turnover"] = income_stmt["revenue"] / balance_sheet["total_assets"]
            
            if "cost_of_revenue" in income_stmt and "inventory" in balance_sheet and balance_sheet["inventory"] != 0:
                ratios["inventory_turnover"] = income_stmt["cost_of_revenue"] / balance_sheet["inventory"]
            
            if "revenue" in income_stmt and "accounts_receivable" in balance_sheet and balance_sheet["accounts_receivable"] != 0:
                ratios["receivables_turnover"] = income_stmt["revenue"] / balance_sheet["accounts_receivable"]
            
            if "receivables_turnover" in ratios and ratios["receivables_turnover"] != 0:
                ratios["days_sales_outstanding"] = 365 / ratios["receivables_turnover"]
            
            if "inventory_turnover" in ratios and ratios["inventory_turnover"] != 0:
                ratios["days_inventory_outstanding"] = 365 / ratios["inventory_turnover"]
            
            if "cost_of_revenue" in income_stmt and "accounts_payable" in balance_sheet and balance_sheet["accounts_payable"] != 0:
                ratios["payables_turnover"] = income_stmt["cost_of_revenue"] / balance_sheet["accounts_payable"]
            
            if "payables_turnover" in ratios and ratios["payables_turnover"] != 0:
                ratios["days_payables_outstanding"] = 365 / ratios["payables_turnover"]
            
            if "days_inventory_outstanding" in ratios and "days_sales_outstanding" in ratios and "days_payables_outstanding" in ratios:
                ratios["cash_conversion_cycle"] = ratios["days_inventory_outstanding"] + ratios["days_sales_outstanding"] - ratios["days_payables_outstanding"]
            
            if "days_inventory_outstanding" in ratios and "days_sales_outstanding" in ratios:
                ratios["operating_cycle"] = ratios["days_inventory_outstanding"] + ratios["days_sales_outstanding"]
            
            return ratios
            
        except Exception as e:
            logger.error(f"Error calculating efficiency ratios: {str(e)}")
            return {}
    
    def get_peer_comparison(self, ticker, peers, metric_type, period_type="annual"):
        try:
            ticker = ticker.upper()
            peers = [p.upper() for p in peers]
            
            ticker_metrics = self.db_ops.find_one(
                FINANCIAL_METRICS_COLLECTION,
                {
                    "ticker": ticker,
                    "metric_type": metric_type,
                    "period_type": period_type
                }
            )
            
            if not ticker_metrics:
                logger.warning(f"No {metric_type} metrics found for {ticker}")
                return {}
            
            peer_metrics = {}
            for peer in peers:
                peer_data = self.db_ops.find_one(
                    FINANCIAL_METRICS_COLLECTION,
                    {
                        "ticker": peer,
                        "metric_type": metric_type,
                        "period_type": period_type
                    }
                )
                
                if peer_data:
                    peer_metrics[peer] = peer_data.get("metrics", {})
            
            comparison = {
                "ticker": ticker,
                "ticker_metrics": ticker_metrics.get("metrics", {}),
                "peer_metrics": peer_metrics,
                "average": {},
                "median": {},
                "percentile": {},
                "peer_list": peers
            }
            
            ticker_metric_values = ticker_metrics.get("metrics", {})
            for metric, value in ticker_metric_values.items():
                all_values = [value]
                for peer, metrics in peer_metrics.items():
                    if metric in metrics:
                        all_values.append(metrics[metric])
                
                if all_values:
                    comparison["average"][metric] = sum(all_values) / len(all_values)
                    comparison["median"][metric] = pd.Series(all_values).median()
                    
                    if len(all_values) > 1:
                        sorted_values = sorted(all_values)
                        ticker_rank = sorted_values.index(value)
                        comparison["percentile"][metric] = ticker_rank / (len(sorted_values) - 1)
            
            self.db_ops.update_one(
                FINANCIAL_METRICS_COLLECTION,
                {
                    "ticker": ticker,
                    "metric_type": metric_type,
                    "period_type": period_type,
                    "date": ticker_metrics["date"]
                },
                {"$set": {"peer_comparison": comparison}}
            )
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error getting peer comparison for {ticker}: {str(e)}")
            return {}