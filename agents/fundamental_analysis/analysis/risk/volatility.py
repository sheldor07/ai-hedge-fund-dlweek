"""
Volatility analysis module.
"""

import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from database.operations import db_ops

logger = logging.getLogger("stock_analyzer.analysis.risk.volatility")


class VolatilityAnalyzer:
    """
    Analyzes stock price volatility and related risk metrics.
    """
    
    def __init__(self):
        """Initialize the VolatilityAnalyzer."""
        self.db_ops = db_ops
    
    def calculate_volatility_metrics(self, ticker, market_ticker="SPY", days=252):
        """
        Calculate volatility metrics for a ticker.
        
        Args:
            ticker (str): The stock ticker symbol.
            market_ticker (str, optional): The market index ticker. Defaults to "SPY".
            days (int, optional): Number of trading days to analyze. Defaults to 252 (1 year).
            
        Returns:
            dict: The volatility metrics.
        """
        try:
            ticker = ticker.upper()
            market_ticker = market_ticker.upper()
            
            # Get price history for ticker
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days * 1.5)  # Get extra data to ensure we have enough
            
            price_data = self.db_ops.find_many(
                "price_history",
                {
                    "ticker": ticker,
                    "date": {"$gte": start_date, "$lte": end_date}
                },
                sort=[("date", 1)]
            )
            
            if not price_data:
                logger.warning(f"No price data found for {ticker}")
                return {}
            
            # Get price history for market
            market_data = self.db_ops.find_many(
                "price_history",
                {
                    "ticker": market_ticker,
                    "date": {"$gte": start_date, "$lte": end_date}
                },
                sort=[("date", 1)]
            )
            
            if not market_data:
                logger.warning(f"No price data found for market index {market_ticker}")
                return {}
            
            # Convert to DataFrames
            ticker_df = pd.DataFrame(price_data)
            market_df = pd.DataFrame(market_data)
            
            # Calculate daily returns
            ticker_df["daily_return"] = ticker_df["adjusted_close"].pct_change()
            market_df["daily_return"] = market_df["adjusted_close"].pct_change()
            
            # Align dates
            merged_df = pd.merge(
                ticker_df[["date", "daily_return"]],
                market_df[["date", "daily_return"]],
                on="date",
                suffixes=("_ticker", "_market")
            )
            
            # Limit to requested days
            if len(merged_df) > days:
                merged_df = merged_df.tail(days)
            
            # Calculate volatility metrics
            volatility_metrics = {}
            
            # Standard deviation of returns (annualized)
            daily_std = merged_df["daily_return_ticker"].std()
            volatility_metrics["daily_volatility"] = daily_std
            volatility_metrics["annualized_volatility"] = daily_std * np.sqrt(252)  # Annualized
            
            # Beta
            covariance = merged_df[["daily_return_ticker", "daily_return_market"]].cov().iloc[0, 1]
            market_variance = merged_df["daily_return_market"].var()
            beta = covariance / market_variance if market_variance > 0 else 1
            volatility_metrics["beta"] = beta
            
            # Alpha (Jensen's Alpha)
            risk_free_rate = 0.01 / 252  # Assuming 1% annual risk-free rate, converted to daily
            avg_ticker_return = merged_df["daily_return_ticker"].mean()
            avg_market_return = merged_df["daily_return_market"].mean()
            
            alpha = (avg_ticker_return - risk_free_rate) - beta * (avg_market_return - risk_free_rate)
            volatility_metrics["alpha_daily"] = alpha
            volatility_metrics["alpha_annualized"] = alpha * 252  # Annualized
            
            # Sharpe Ratio
            excess_return = avg_ticker_return - risk_free_rate
            sharpe_ratio = excess_return / daily_std if daily_std > 0 else 0
            volatility_metrics["sharpe_ratio_daily"] = sharpe_ratio
            volatility_metrics["sharpe_ratio_annualized"] = sharpe_ratio * np.sqrt(252)  # Annualized
            
            # Treynor Ratio
            treynor_ratio = excess_return / beta if beta > 0 else 0
            volatility_metrics["treynor_ratio_daily"] = treynor_ratio
            volatility_metrics["treynor_ratio_annualized"] = treynor_ratio * 252  # Annualized
            
            # Value at Risk (VaR) - 95% confidence
            var_95 = np.percentile(merged_df["daily_return_ticker"].dropna(), 5)
            volatility_metrics["var_95_daily"] = -var_95  # Negative to represent a loss
            volatility_metrics["var_95_annualized"] = -var_95 * np.sqrt(252)  # Annualized
            
            # Value at Risk (VaR) - 99% confidence
            var_99 = np.percentile(merged_df["daily_return_ticker"].dropna(), 1)
            volatility_metrics["var_99_daily"] = -var_99  # Negative to represent a loss
            volatility_metrics["var_99_annualized"] = -var_99 * np.sqrt(252)  # Annualized
            
            # Maximum Drawdown
            ticker_df["cumulative_return"] = (1 + ticker_df["daily_return"]).cumprod()
            ticker_df["running_max"] = ticker_df["cumulative_return"].cummax()
            ticker_df["drawdown"] = (ticker_df["cumulative_return"] / ticker_df["running_max"]) - 1
            max_drawdown = ticker_df["drawdown"].min()
            volatility_metrics["maximum_drawdown"] = max_drawdown
            
            # Calculate upside and downside capture
            up_market = merged_df[merged_df["daily_return_market"] > 0]
            down_market = merged_df[merged_df["daily_return_market"] < 0]
            
            up_capture = (up_market["daily_return_ticker"].mean() / up_market["daily_return_market"].mean()) * 100 if len(up_market) > 0 else 100
            down_capture = (down_market["daily_return_ticker"].mean() / down_market["daily_return_market"].mean()) * 100 if len(down_market) > 0 else 100
            
            volatility_metrics["upside_capture"] = up_capture
            volatility_metrics["downside_capture"] = down_capture
            
            # Save the metrics to the database
            self._save_volatility_metrics(ticker, volatility_metrics)
            
            return volatility_metrics
            
        except Exception as e:
            logger.error(f"Error calculating volatility metrics for {ticker}: {str(e)}")
            return {}
    
    def _save_volatility_metrics(self, ticker, metrics):
        """
        Save volatility metrics to the database.
        
        Args:
            ticker (str): The stock ticker symbol.
            metrics (dict): The volatility metrics.
        """
        try:
            # Create metrics document
            metrics_doc = {
                "ticker": ticker,
                "date": datetime.now(),
                "metrics": metrics
            }
            
            # Update or insert the metrics
            self.db_ops.update_one(
                "volatility_metrics",
                {
                    "ticker": ticker
                },
                {"$set": metrics_doc},
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error saving volatility metrics for {ticker}: {str(e)}")
    
    def get_latest_volatility_metrics(self, ticker):
        """
        Get the latest volatility metrics for a ticker.
        
        Args:
            ticker (str): The stock ticker symbol.
            
        Returns:
            dict: The volatility metrics.
        """
        try:
            ticker = ticker.upper()
            
            # Get the latest metrics
            metrics_doc = self.db_ops.find_one(
                "volatility_metrics",
                {"ticker": ticker},
                {"sort": [("date", -1)]}
            )
            
            if not metrics_doc:
                logger.warning(f"No volatility metrics found for {ticker}")
                return {}
            
            return {
                "ticker": ticker,
                "date": metrics_doc["date"],
                "metrics": metrics_doc["metrics"]
            }
            
        except Exception as e:
            logger.error(f"Error getting volatility metrics for {ticker}: {str(e)}")
            return {}
    
    def calculate_correlation_matrix(self, tickers, days=252):
        """
        Calculate correlation matrix for a list of tickers.
        
        Args:
            tickers (list): List of stock ticker symbols.
            days (int, optional): Number of trading days to analyze. Defaults to 252 (1 year).
            
        Returns:
            dict: The correlation matrix.
        """
        try:
            tickers = [t.upper() for t in tickers]
            
            # Get price history for all tickers
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days * 1.5)  # Get extra data to ensure we have enough
            
            # Prepare DataFrame for returns
            returns_data = {}
            
            for ticker in tickers:
                price_data = self.db_ops.find_many(
                    "price_history",
                    {
                        "ticker": ticker,
                        "date": {"$gte": start_date, "$lte": end_date}
                    },
                    sort=[("date", 1)]
                )
                
                if not price_data:
                    logger.warning(f"No price data found for {ticker}")
                    continue
                
                # Convert to DataFrame
                df = pd.DataFrame(price_data)
                
                # Calculate daily returns
                df["daily_return"] = df["adjusted_close"].pct_change()
                
                # Store date and return
                returns_data[ticker] = df[["date", "daily_return"]].copy()
            
            if not returns_data:
                logger.warning("No price data found for any tickers")
                return {}
            
            # Merge all returns on date
            merged_df = None
            
            for ticker, df in returns_data.items():
                if merged_df is None:
                    merged_df = df.rename(columns={"daily_return": ticker})
                else:
                    merged_df = pd.merge(
                        merged_df,
                        df.rename(columns={"daily_return": ticker}),
                        on="date",
                        how="outer"
                    )
            
            # Drop rows with missing values
            merged_df = merged_df.dropna()
            
            # Limit to requested days
            if len(merged_df) > days:
                merged_df = merged_df.tail(days)
            
            # Calculate correlation matrix
            correlation_matrix = merged_df.drop("date", axis=1).corr().to_dict()
            
            # Save the correlation matrix to the database
            self._save_correlation_matrix(tickers, correlation_matrix)
            
            return {
                "tickers": tickers,
                "date": datetime.now(),
                "correlation_matrix": correlation_matrix
            }
            
        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {str(e)}")
            return {}
    
    def _save_correlation_matrix(self, tickers, correlation_matrix):
        """
        Save correlation matrix to the database.
        
        Args:
            tickers (list): List of stock ticker symbols.
            correlation_matrix (dict): The correlation matrix.
        """
        try:
            # Create matrix document
            matrix_doc = {
                "tickers": tickers,
                "date": datetime.now(),
                "correlation_matrix": correlation_matrix
            }
            
            # Update or insert the matrix
            self.db_ops.update_one(
                "correlation_matrices",
                {
                    "tickers": {"$all": tickers, "$size": len(tickers)}
                },
                {"$set": matrix_doc},
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error saving correlation matrix: {str(e)}")
    
    def get_latest_correlation_matrix(self, tickers):
        """
        Get the latest correlation matrix for a list of tickers.
        
        Args:
            tickers (list): List of stock ticker symbols.
            
        Returns:
            dict: The correlation matrix.
        """
        try:
            tickers = [t.upper() for t in tickers]
            
            # Get the latest matrix
            matrix_doc = self.db_ops.find_one(
                "correlation_matrices",
                {
                    "tickers": {"$all": tickers, "$size": len(tickers)}
                },
                {"sort": [("date", -1)]}
            )
            
            if not matrix_doc:
                logger.warning(f"No correlation matrix found for {tickers}")
                return {}
            
            return {
                "tickers": matrix_doc["tickers"],
                "date": matrix_doc["date"],
                "correlation_matrix": matrix_doc["correlation_matrix"]
            }
            
        except Exception as e:
            logger.error(f"Error getting correlation matrix: {str(e)}")
            return {}