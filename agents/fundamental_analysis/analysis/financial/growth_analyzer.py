import logging
from datetime import datetime
import pandas as pd
import numpy as np

from database.operations import db_ops
from database.schema import FINANCIAL_STATEMENTS_COLLECTION, FINANCIAL_METRICS_COLLECTION

logger = logging.getLogger("stock_analyzer.analysis.financial.growth")


class GrowthAnalyzer:
    
    def __init__(self):
        self.db_ops = db_ops
    
    def calculate_growth_rates(self, ticker, period_type="annual"):
        try:
            ticker = ticker.upper()
            
            financial_statements = self.db_ops.find_many(
                FINANCIAL_STATEMENTS_COLLECTION,
                {"ticker": ticker, "period_type": period_type},
                sort=[("period_end_date", 1)]
            )
            
            if not financial_statements:
                logger.warning(f"No {period_type} financial statements found for {ticker}")
                return False
            
            metrics = self._extract_time_series_metrics(financial_statements)
            
            if metrics is None or metrics.empty:
                logger.warning(f"No time series metrics could be extracted for {ticker}")
                return False
            
            growth_rates = {}
            
            yoy_growth = self._calculate_yoy_growth(metrics)
            if yoy_growth:
                growth_rates["yoy"] = yoy_growth
            
            cagr = self._calculate_cagr(metrics)
            if cagr:
                growth_rates["cagr"] = cagr
            
            trends = self._calculate_trends(metrics)
            if trends:
                growth_rates["trends"] = trends
            
            latest_period = max(financial_statements, key=lambda x: x.get("period_end_date", datetime.min)).get("period_end_date")
            
            self._save_growth_rates(ticker, latest_period, period_type, growth_rates)
            
            logger.info(f"Calculated growth rates for {ticker} ({period_type})")
            return True
            
        except Exception as e:
            logger.error(f"Error calculating growth rates for {ticker}: {str(e)}")
            return False
    
    def _extract_time_series_metrics(self, financial_statements):
        try:
            time_series = {
                "dates": [],
                "revenue": [],
                "net_income": [],
                "eps": [],
                "operating_income": [],
                "operating_cash_flow": [],
                "free_cash_flow": [],
                "total_assets": [],
                "total_equity": [],
                "gross_profit": [],
                "ebitda": []
            }
            
            for statement in financial_statements:
                if not all(key in statement for key in ["income_statement_standardized", "balance_sheet_standardized", "cash_flow_statement_standardized"]):
                    continue
                
                period_date = statement.get("period_end_date")
                if not period_date:
                    continue
                
                time_series["dates"].append(period_date)
                
                income_stmt = statement.get("income_statement_standardized", {})
                time_series["revenue"].append(income_stmt.get("revenue"))
                time_series["net_income"].append(income_stmt.get("net_income"))
                time_series["eps"].append(income_stmt.get("eps_diluted"))
                time_series["operating_income"].append(income_stmt.get("operating_income"))
                time_series["gross_profit"].append(income_stmt.get("gross_profit"))
                
                ebitda = income_stmt.get("operating_income", 0)
                if "depreciation_amortization" in income_stmt:
                    ebitda += income_stmt["depreciation_amortization"]
                time_series["ebitda"].append(ebitda)
                
                balance_sheet = statement.get("balance_sheet_standardized", {})
                time_series["total_assets"].append(balance_sheet.get("total_assets"))
                time_series["total_equity"].append(balance_sheet.get("total_equity"))
                
                cash_flow = statement.get("cash_flow_statement_standardized", {})
                time_series["operating_cash_flow"].append(cash_flow.get("net_cash_from_operating_activities"))
                time_series["free_cash_flow"].append(cash_flow.get("free_cash_flow"))
            
            df = pd.DataFrame(time_series)
            df = df.set_index("dates")
            
            df = df.dropna(how="all")
            
            df = df.fillna(method="ffill").fillna(method="bfill")
            
            return df
            
        except Exception as e:
            logger.error(f"Error extracting time series metrics: {str(e)}")
            return None
    
    def _calculate_yoy_growth(self, metrics_df):
        try:
            if len(metrics_df) < 2:
                return {}
            
            yoy_growth = metrics_df.pct_change()
            
            latest_growth = yoy_growth.iloc[-1].to_dict()
            
            cleaned_growth = {}
            for key, value in latest_growth.items():
                if pd.notna(value) and not np.isinf(value):
                    cleaned_growth[key] = value
            
            return cleaned_growth
            
        except Exception as e:
            logger.error(f"Error calculating year-over-year growth: {str(e)}")
            return {}
    
    def _calculate_cagr(self, metrics_df):
        try:
            if len(metrics_df) < 2:
                return {}
            
            first_period = metrics_df.iloc[0]
            last_period = metrics_df.iloc[-1]
            
            num_years = (last_period.name - first_period.name).days / 365.25
            
            if num_years < 1:
                return {}
            
            cagr = {}
            for column in metrics_df.columns:
                first_value = first_period[column]
                last_value = last_period[column]
                
                if pd.notna(first_value) and pd.notna(last_value) and first_value > 0 and last_value > 0:
                    cagr[column] = (last_value / first_value) ** (1 / num_years) - 1
            
            return cagr
            
        except Exception as e:
            logger.error(f"Error calculating CAGR: {str(e)}")
            return {}
    
    def _calculate_trends(self, metrics_df):
        try:
            if len(metrics_df) < 3:
                return {}
            
            trends = {}
            
            for column in metrics_df.columns:
                series = metrics_df[column]
                
                if series.isna().sum() > len(series) * 0.3:
                    continue
                
                x = np.arange(len(series))
                y = series.values
                
                slope, _ = np.polyfit(x, y, 1)
                
                mean_value = np.mean(y)
                if mean_value != 0:
                    normalized_slope = slope / mean_value
                    trends[column] = normalized_slope
            
            return trends
            
        except Exception as e:
            logger.error(f"Error calculating trends: {str(e)}")
            return {}
    
    def _save_growth_rates(self, ticker, period_date, period_type, growth_rates):
        try:
            document = {
                "ticker": ticker,
                "period_end_date": period_date,
                "period_type": period_type,
                "metric_type": "growth",
                "metrics": growth_rates,
                "last_updated": datetime.now()
            }
            
            self.db_ops.update_one(
                FINANCIAL_METRICS_COLLECTION,
                {
                    "ticker": ticker,
                    "period_end_date": period_date,
                    "period_type": period_type,
                    "metric_type": "growth"
                },
                {"$set": document},
                upsert=True
            )
            
            logger.info(f"Saved growth rates for {ticker} ({period_type})")
            
        except Exception as e:
            logger.error(f"Error saving growth rates for {ticker}: {str(e)}")
    
    def get_growth_metrics(self, ticker, period_type="annual"):
        try:
            ticker = ticker.upper()
            
            growth_metrics = self.db_ops.find_one(
                FINANCIAL_METRICS_COLLECTION,
                {
                    "ticker": ticker,
                    "period_type": period_type,
                    "metric_type": "growth"
                },
                sort=[("period_end_date", -1)]
            )
            
            if not growth_metrics:
                logger.warning(f"No growth metrics found for {ticker} ({period_type})")
                return {}
            
            return growth_metrics.get("metrics", {})
            
        except Exception as e:
            logger.error(f"Error retrieving growth metrics for {ticker}: {str(e)}")
            return {}