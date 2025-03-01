"""
Growth metrics analyzer module.
"""

import logging
from datetime import datetime
import pandas as pd
import numpy as np

from database.operations import db_ops
from database.schema import FINANCIAL_STATEMENTS_COLLECTION, FINANCIAL_METRICS_COLLECTION

logger = logging.getLogger("stock_analyzer.analysis.financial.growth")


class GrowthAnalyzer:
    """
    Analyzes growth metrics for a company.
    """
    
    def __init__(self):
        """Initialize the GrowthAnalyzer."""
        self.db_ops = db_ops
    
    def calculate_growth_rates(self, ticker, period_type="annual"):
        """
        Calculate growth rates for a ticker.
        
        Args:
            ticker (str): The stock ticker symbol.
            period_type (str, optional): The type of period ("annual" or "quarterly"). Defaults to "annual".
            
        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        try:
            ticker = ticker.upper()
            
            # Get financial statements from the database
            financial_statements = self.db_ops.find_many(
                FINANCIAL_STATEMENTS_COLLECTION,
                {"ticker": ticker, "period_type": period_type},
                sort=[("period_end_date", 1)]  # Sort by date ascending for time series analysis
            )
            
            if not financial_statements:
                logger.warning(f"No {period_type} financial statements found for {ticker}")
                return False
            
            # Extract key metrics for time series analysis
            metrics = self._extract_time_series_metrics(financial_statements)
            
            if metrics is None or metrics.empty:
                logger.warning(f"No time series metrics could be extracted for {ticker}")
                return False
            
            # Calculate growth rates
            growth_rates = {}
            
            # Annual growth rates (year-over-year)
            yoy_growth = self._calculate_yoy_growth(metrics)
            if yoy_growth:
                growth_rates["yoy"] = yoy_growth
            
            # Compound Annual Growth Rate (CAGR)
            cagr = self._calculate_cagr(metrics)
            if cagr:
                growth_rates["cagr"] = cagr
            
            # Trend analysis (linear regression slopes)
            trends = self._calculate_trends(metrics)
            if trends:
                growth_rates["trends"] = trends
            
            # Get the latest period date
            latest_period = max(financial_statements, key=lambda x: x.get("period_end_date", datetime.min)).get("period_end_date")
            
            # Save growth rates to the database
            self._save_growth_rates(ticker, latest_period, period_type, growth_rates)
            
            logger.info(f"Calculated growth rates for {ticker} ({period_type})")
            return True
            
        except Exception as e:
            logger.error(f"Error calculating growth rates for {ticker}: {str(e)}")
            return False
    
    def _extract_time_series_metrics(self, financial_statements):
        """
        Extract key metrics for time series analysis.
        
        Args:
            financial_statements (list): The financial statements.
            
        Returns:
            dict: The extracted metrics.
        """
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
                # Skip if we don't have standardized statements
                if not all(key in statement for key in ["income_statement_standardized", "balance_sheet_standardized", "cash_flow_statement_standardized"]):
                    continue
                
                period_date = statement.get("period_end_date")
                if not period_date:
                    continue
                
                # Add the date
                time_series["dates"].append(period_date)
                
                # Extract metrics from income statement
                income_stmt = statement.get("income_statement_standardized", {})
                time_series["revenue"].append(income_stmt.get("revenue"))
                time_series["net_income"].append(income_stmt.get("net_income"))
                time_series["eps"].append(income_stmt.get("eps_diluted"))
                time_series["operating_income"].append(income_stmt.get("operating_income"))
                time_series["gross_profit"].append(income_stmt.get("gross_profit"))
                
                # Calculate EBITDA
                ebitda = income_stmt.get("operating_income", 0)
                if "depreciation_amortization" in income_stmt:
                    ebitda += income_stmt["depreciation_amortization"]
                time_series["ebitda"].append(ebitda)
                
                # Extract metrics from balance sheet
                balance_sheet = statement.get("balance_sheet_standardized", {})
                time_series["total_assets"].append(balance_sheet.get("total_assets"))
                time_series["total_equity"].append(balance_sheet.get("total_equity"))
                
                # Extract metrics from cash flow statement
                cash_flow = statement.get("cash_flow_statement_standardized", {})
                time_series["operating_cash_flow"].append(cash_flow.get("net_cash_from_operating_activities"))
                time_series["free_cash_flow"].append(cash_flow.get("free_cash_flow"))
            
            # Convert to pandas DataFrame for easier analysis
            df = pd.DataFrame(time_series)
            df = df.set_index("dates")
            
            # Drop rows with all NaN values
            df = df.dropna(how="all")
            
            # Fill remaining NaN values with forward fill then backward fill
            df = df.fillna(method="ffill").fillna(method="bfill")
            
            return df
            
        except Exception as e:
            logger.error(f"Error extracting time series metrics: {str(e)}")
            return None
    
    def _calculate_yoy_growth(self, metrics_df):
        """
        Calculate year-over-year growth rates.
        
        Args:
            metrics_df (pandas.DataFrame): The metrics DataFrame.
            
        Returns:
            dict: The year-over-year growth rates.
        """
        try:
            if len(metrics_df) < 2:
                return {}
            
            # Calculate percentage change
            yoy_growth = metrics_df.pct_change()
            
            # Get the latest growth rates
            latest_growth = yoy_growth.iloc[-1].to_dict()
            
            # Clean up the results (remove NaN, infinity, etc.)
            cleaned_growth = {}
            for key, value in latest_growth.items():
                if pd.notna(value) and not np.isinf(value):
                    cleaned_growth[key] = value
            
            return cleaned_growth
            
        except Exception as e:
            logger.error(f"Error calculating year-over-year growth: {str(e)}")
            return {}
    
    def _calculate_cagr(self, metrics_df):
        """
        Calculate Compound Annual Growth Rate (CAGR).
        
        Args:
            metrics_df (pandas.DataFrame): The metrics DataFrame.
            
        Returns:
            dict: The CAGR values.
        """
        try:
            if len(metrics_df) < 2:
                return {}
            
            # Get the first and last values
            first_values = metrics_df.iloc[0]
            last_values = metrics_df.iloc[-1]
            
            # Get the time period in years
            time_period = (metrics_df.index[-1] - metrics_df.index[0]).days / 365.25
            
            if time_period <= 0:
                return {}
            
            # Calculate CAGR for each metric
            cagr = {}
            for column in metrics_df.columns:
                first_value = first_values[column]
                last_value = last_values[column]
                
                if pd.notna(first_value) and pd.notna(last_value) and first_value > 0:
                    cagr[column] = ((last_value / first_value) ** (1 / time_period)) - 1
            
            # Calculate CAGRs for different time periods if we have enough data
            if time_period >= 3:
                # 3-year CAGR
                three_year_ago_idx = metrics_df.index.get_indexer([metrics_df.index[-1] - pd.DateOffset(years=3)], method="nearest")[0]
                if three_year_ago_idx >= 0:
                    three_year_values = metrics_df.iloc[three_year_ago_idx]
                    for column in metrics_df.columns:
                        three_year_value = three_year_values[column]
                        last_value = last_values[column]
                        
                        if pd.notna(three_year_value) and pd.notna(last_value) and three_year_value > 0:
                            cagr[f"{column}_3yr"] = ((last_value / three_year_value) ** (1 / 3)) - 1
            
            if time_period >= 5:
                # 5-year CAGR
                five_year_ago_idx = metrics_df.index.get_indexer([metrics_df.index[-1] - pd.DateOffset(years=5)], method="nearest")[0]
                if five_year_ago_idx >= 0:
                    five_year_values = metrics_df.iloc[five_year_ago_idx]
                    for column in metrics_df.columns:
                        five_year_value = five_year_values[column]
                        last_value = last_values[column]
                        
                        if pd.notna(five_year_value) and pd.notna(last_value) and five_year_value > 0:
                            cagr[f"{column}_5yr"] = ((last_value / five_year_value) ** (1 / 5)) - 1
            
            # Clean up the results (remove NaN, infinity, etc.)
            cleaned_cagr = {}
            for key, value in cagr.items():
                if pd.notna(value) and not np.isinf(value):
                    cleaned_cagr[key] = value
            
            return cleaned_cagr
            
        except Exception as e:
            logger.error(f"Error calculating CAGR: {str(e)}")
            return {}
    
    def _calculate_trends(self, metrics_df):
        """
        Calculate linear regression trends.
        
        Args:
            metrics_df (pandas.DataFrame): The metrics DataFrame.
            
        Returns:
            dict: The trend slopes.
        """
        try:
            if len(metrics_df) < 3:  # Need at least 3 points for meaningful trend
                return {}
            
            # Create numeric X values (days since first date)
            x = [(date - metrics_df.index[0]).days for date in metrics_df.index]
            x = np.array(x).reshape(-1, 1)
            
            trends = {}
            for column in metrics_df.columns:
                values = metrics_df[column].values
                
                if pd.notna(values).all():
                    # Fit linear regression
                    from sklearn.linear_model import LinearRegression
                    model = LinearRegression().fit(x, values)
                    
                    # Get the slope (coefficient)
                    slope = model.coef_[0]
                    
                    # Normalize the slope as a percentage of the average value
                    avg_value = np.mean(values)
                    if avg_value != 0:
                        normalized_slope = (slope * 365) / avg_value  # Daily slope to annual percentage
                        trends[column] = normalized_slope
                    
                    # Add R-squared value to measure goodness of fit
                    r_squared = model.score(x, values)
                    trends[f"{column}_r_squared"] = r_squared
            
            # Clean up the results (remove NaN, infinity, etc.)
            cleaned_trends = {}
            for key, value in trends.items():
                if pd.notna(value) and not np.isinf(value):
                    cleaned_trends[key] = value
            
            return cleaned_trends
            
        except Exception as e:
            logger.error(f"Error calculating trends: {str(e)}")
            return {}
    
    def _save_growth_rates(self, ticker, date, period_type, growth_rates):
        """
        Save growth rates to the database.
        
        Args:
            ticker (str): The stock ticker symbol.
            date (datetime): The date of the growth rates.
            period_type (str): The type of period.
            growth_rates (dict): The growth rates to save.
        """
        try:
            # Create metrics document
            metrics_doc = {
                "ticker": ticker,
                "date": date,
                "metric_type": "growth",
                "period_type": period_type,
                "metrics": growth_rates
            }
            
            # Update or insert the metrics
            self.db_ops.update_one(
                FINANCIAL_METRICS_COLLECTION,
                {
                    "ticker": ticker,
                    "date": date,
                    "metric_type": "growth",
                    "period_type": period_type
                },
                {"$set": metrics_doc},
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error saving growth rates for {ticker}: {str(e)}")
    
    def forecast_future_growth(self, ticker, years=5, period_type="annual"):
        """
        Forecast future growth for a ticker.
        
        Args:
            ticker (str): The stock ticker symbol.
            years (int, optional): Number of years to forecast. Defaults to 5.
            period_type (str, optional): The type of period. Defaults to "annual".
            
        Returns:
            dict: The forecast results.
        """
        try:
            ticker = ticker.upper()
            
            # Get financial statements from the database
            financial_statements = self.db_ops.find_many(
                FINANCIAL_STATEMENTS_COLLECTION,
                {"ticker": ticker, "period_type": period_type},
                sort=[("period_end_date", 1)]
            )
            
            if not financial_statements:
                logger.warning(f"No {period_type} financial statements found for {ticker}")
                return {}
            
            # Extract key metrics for time series analysis
            metrics = self._extract_time_series_metrics(financial_statements)
            
            if metrics is None or metrics.empty or len(metrics) < 3:
                logger.warning(f"Not enough time series data for forecasting {ticker}")
                return {}
            
            # Select key metrics to forecast
            forecast_metrics = ["revenue", "net_income", "eps", "operating_cash_flow"]
            
            # Forecast each metric
            forecasts = {}
            for metric in forecast_metrics:
                if metric in metrics.columns:
                    # Get historical values
                    historical_values = metrics[metric].values
                    dates = metrics.index.to_list()
                    
                    # Create forecast using simple exponential smoothing
                    forecast = self._simple_exponential_smoothing(historical_values, years)
                    
                    # Create forecast dates
                    last_date = dates[-1]
                    forecast_dates = []
                    for i in range(1, years + 1):
                        if period_type == "annual":
                            # Add one year
                            forecast_date = datetime(last_date.year + i, last_date.month, last_date.day)
                        else:
                            # Add 3 months for quarterly
                            forecast_date = last_date + pd.DateOffset(months=3 * i)
                        forecast_dates.append(forecast_date)
                    
                    # Store the forecast
                    forecasts[metric] = {
                        "historical": list(zip([d.strftime("%Y-%m-%d") for d in dates], historical_values.tolist())),
                        "forecast": list(zip([d.strftime("%Y-%m-%d") for d in forecast_dates], forecast.tolist())),
                        "growth_rates": self._calculate_forecast_growth_rates(historical_values, forecast)
                    }
            
            # Get the latest period date
            latest_period = max(financial_statements, key=lambda x: x.get("period_end_date", datetime.min)).get("period_end_date")
            
            # Save the forecast to the database
            self._save_forecast(ticker, latest_period, period_type, forecasts, years)
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Error forecasting growth for {ticker}: {str(e)}")
            return {}
    
    def _simple_exponential_smoothing(self, values, forecast_periods, alpha=0.3):
        """
        Perform simple exponential smoothing forecast.
        
        Args:
            values (numpy.ndarray): The historical values.
            forecast_periods (int): Number of periods to forecast.
            alpha (float, optional): The smoothing factor. Defaults to 0.3.
            
        Returns:
            numpy.ndarray: The forecast values.
        """
        n = len(values)
        
        # Calculate level (smoothed value)
        level = np.zeros(n)
        level[0] = values[0]
        
        for i in range(1, n):
            level[i] = alpha * values[i] + (1 - alpha) * level[i-1]
        
        # Forecast future values
        forecast = np.zeros(forecast_periods)
        for i in range(forecast_periods):
            forecast[i] = level[-1]
        
        return forecast
    
    def _calculate_forecast_growth_rates(self, historical, forecast):
        """
        Calculate growth rates for forecast values.
        
        Args:
            historical (numpy.ndarray): The historical values.
            forecast (numpy.ndarray): The forecast values.
            
        Returns:
            dict: The growth rates.
        """
        growth_rates = {}
        
        # Year-over-year growth rates for forecast
        yoy_growth = []
        for i in range(1, len(forecast)):
            if forecast[i-1] != 0:
                growth = (forecast[i] - forecast[i-1]) / forecast[i-1]
                yoy_growth.append(growth)
        
        growth_rates["yoy"] = yoy_growth
        
        # CAGR from latest historical to end of forecast
        if len(historical) > 0 and len(forecast) > 0 and historical[-1] is not None and forecast[-1] is not None and historical[-1] > 0 and forecast[-1] > 0:
            cagr = ((forecast[-1] / historical[-1]) ** (1 / len(forecast))) - 1
            growth_rates["cagr"] = cagr
        
        return growth_rates
    
    def _save_forecast(self, ticker, date, period_type, forecasts, years):
        """
        Save growth forecast to the database.
        
        Args:
            ticker (str): The stock ticker symbol.
            date (datetime): The date of the forecast.
            period_type (str): The type of period.
            forecasts (dict): The forecasts to save.
            years (int): Number of years forecasted.
        """
        try:
            # Create forecast document
            forecast_doc = {
                "ticker": ticker,
                "date": date,
                "forecast_date": datetime.now(),
                "period_type": period_type,
                "years": years,
                "forecasts": forecasts
            }
            
            # Update or insert the forecast
            self.db_ops.update_one(
                "growth_forecasts",
                {
                    "ticker": ticker,
                    "date": date,
                    "period_type": period_type
                },
                {"$set": forecast_doc},
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error saving growth forecast for {ticker}: {str(e)}")
    
    def get_growth_summary(self, ticker, period_type="annual"):
        """
        Get a summary of growth metrics for a ticker.
        
        Args:
            ticker (str): The stock ticker symbol.
            period_type (str, optional): The type of period. Defaults to "annual".
            
        Returns:
            dict: The growth summary.
        """
        try:
            ticker = ticker.upper()
            
            # Get the latest growth metrics
            growth_metrics = self.db_ops.find_one(
                FINANCIAL_METRICS_COLLECTION,
                {
                    "ticker": ticker,
                    "metric_type": "growth",
                    "period_type": period_type
                }
            )
            
            if not growth_metrics:
                logger.warning(f"No growth metrics found for {ticker}")
                return {}
            
            # Get the latest forecast
            forecast = self.db_ops.find_one(
                "growth_forecasts",
                {
                    "ticker": ticker,
                    "period_type": period_type
                }
            )
            
            # Prepare summary
            summary = {
                "ticker": ticker,
                "period_type": period_type,
                "as_of_date": growth_metrics.get("date"),
                "historical_growth": {},
                "forecast_growth": {}
            }
            
            # Add historical growth metrics
            metrics = growth_metrics.get("metrics", {})
            for category, values in metrics.items():
                summary["historical_growth"][category] = values
            
            # Add forecast growth if available
            if forecast:
                summary["forecast_growth"] = forecast.get("forecasts", {})
                summary["forecast_years"] = forecast.get("years", 0)
                summary["forecast_date"] = forecast.get("forecast_date")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting growth summary for {ticker}: {str(e)}")
            return {}