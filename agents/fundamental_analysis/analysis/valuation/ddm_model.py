"""
Dividend Discount Model (DDM) module.
"""

import logging
from datetime import datetime

from database.operations import db_ops
from database.schema import FINANCIAL_STATEMENTS_COLLECTION, VALUATION_MODELS_COLLECTION

logger = logging.getLogger("stock_analyzer.analysis.valuation.ddm")


class DDMModel:
    """
    Implements a Dividend Discount Model (DDM) for stock valuation.
    """
    
    def __init__(self):
        """Initialize the DDMModel."""
        self.db_ops = db_ops
    
    def build_ddm_model(self, ticker, projection_years=5, scenarios=None):
        """
        Build a DDM model for a ticker.
        
        Args:
            ticker (str): The stock ticker symbol.
            projection_years (int, optional): Number of years to project. Defaults to 5.
            scenarios (dict, optional): Custom scenarios. Defaults to None.
            
        Returns:
            dict: The DDM model results.
        """
        try:
            ticker = ticker.upper()
            
            # Get the latest financial statements
            financial_statements = self.db_ops.find_many(
                FINANCIAL_STATEMENTS_COLLECTION,
                {"ticker": ticker, "period_type": "annual"},
                sort=[("period_end_date", -1)]
            )
            
            if not financial_statements:
                logger.warning(f"No financial statements found for {ticker}")
                return {}
            
            # Get the latest statement
            latest_statement = financial_statements[0]
            
            # Get cash flow statements to check for dividends
            cash_flow = latest_statement.get("cash_flow_statement_standardized", {})
            
            # Check if the company pays dividends
            if "dividends_paid" not in cash_flow or cash_flow["dividends_paid"] >= 0:
                logger.warning(f"{ticker} does not pay dividends or dividend data is not available")
                return {"error": "No dividend data available"}
            
            # Define default scenarios if not provided
            if not scenarios:
                scenarios = {
                    "base": {
                        "dividend_growth": 0.05,  # 5% annual growth
                        "required_return": 0.09   # 9% required return
                    },
                    "bull": {
                        "dividend_growth": 0.07,  # 7% annual growth
                        "required_return": 0.08   # 8% required return
                    },
                    "bear": {
                        "dividend_growth": 0.03,  # 3% annual growth
                        "required_return": 0.10   # 10% required return
                    }
                }
            
            # Get inputs for the DDM model
            inputs = self._get_ddm_inputs(ticker, latest_statement)
            
            if not inputs:
                logger.warning(f"Could not get DDM inputs for {ticker}")
                return {}
            
            # Build the model for each scenario
            results = {}
            for scenario_name, scenario_params in scenarios.items():
                # Merge default inputs with scenario parameters
                scenario_inputs = {**inputs, **scenario_params}
                
                # Build DDM model for this scenario
                ddm_result = self._build_scenario_ddm(ticker, scenario_inputs, projection_years)
                
                # Store the result
                results[scenario_name] = ddm_result
            
            # Save the model to the database
            model_date = datetime.now()
            self._save_ddm_model(ticker, model_date, inputs, scenarios, results)
            
            return {
                "inputs": inputs,
                "scenarios": scenarios,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error building DDM model for {ticker}: {str(e)}")
            return {}
    
    def _get_ddm_inputs(self, ticker, statement):
        """
        Get inputs for the DDM model.
        
        Args:
            ticker (str): The stock ticker symbol.
            statement (dict): The financial statement.
            
        Returns:
            dict: The DDM inputs.
        """
        try:
            income_stmt = statement.get("income_statement_standardized", {})
            cash_flow = statement.get("cash_flow_statement_standardized", {})
            
            # Get latest stock price
            price_data = self.db_ops.find_one(
                "price_history",
                {"ticker": ticker},
                {"sort": [("date", -1)]}
            )
            
            current_price = price_data.get("close", 0) if price_data else 0
            
            # Get shares outstanding
            shares_outstanding = income_stmt.get("shares_outstanding_diluted", 0)
            
            # Get dividend data
            if "dividends_paid" in cash_flow and cash_flow["dividends_paid"] < 0 and shares_outstanding > 0:
                # dividends_paid is negative in cash flow (outflow)
                annual_dividend = abs(cash_flow["dividends_paid"]) / shares_outstanding
            else:
                # Try to get dividend from price data
                annual_dividend = price_data.get("dividends", 0) * 4 if price_data else 0  # Assuming quarterly dividends
            
            # Calculate current dividend yield
            dividend_yield = annual_dividend / current_price if current_price > 0 else 0
            
            # Get historical dividend growth rate
            dividend_growth = 0.05  # Default to 5% if we can't calculate
            
            # Try to get historical dividend growth from previous statements
            previous_statements = self.db_ops.find_many(
                FINANCIAL_STATEMENTS_COLLECTION,
                {"ticker": ticker, "period_type": "annual"},
                sort=[("period_end_date", -1)],
                limit=5  # Get up to 5 years of data
            )
            
            if len(previous_statements) > 1:
                # Calculate average dividend growth rate
                dividends = []
                for stmt in reversed(previous_statements):  # Process oldest to newest
                    stmt_cash_flow = stmt.get("cash_flow_statement_standardized", {})
                    stmt_income = stmt.get("income_statement_standardized", {})
                    
                    if "dividends_paid" in stmt_cash_flow and stmt_cash_flow["dividends_paid"] < 0:
                        stmt_shares = stmt_income.get("shares_outstanding_diluted", 0)
                        if stmt_shares > 0:
                            div_per_share = abs(stmt_cash_flow["dividends_paid"]) / stmt_shares
                            dividends.append(div_per_share)
                
                # Calculate growth rates
                if len(dividends) >= 2:
                    growth_rates = []
                    for i in range(1, len(dividends)):
                        if dividends[i-1] > 0:
                            growth = (dividends[i] - dividends[i-1]) / dividends[i-1]
                            growth_rates.append(growth)
                    
                    if growth_rates:
                        dividend_growth = sum(growth_rates) / len(growth_rates)
            
            # Get payout ratio
            net_income = income_stmt.get("net_income", 0)
            payout_ratio = abs(cash_flow.get("dividends_paid", 0)) / net_income if net_income > 0 else 0
            
            return {
                "current_price": current_price,
                "shares_outstanding": shares_outstanding,
                "annual_dividend": annual_dividend,
                "dividend_yield": dividend_yield,
                "dividend_growth": dividend_growth,
                "payout_ratio": payout_ratio
            }
            
        except Exception as e:
            logger.error(f"Error getting DDM inputs for {ticker}: {str(e)}")
            return {}
    
    def _build_scenario_ddm(self, ticker, inputs, projection_years):
        """
        Build a DDM model for a specific scenario.
        
        Args:
            ticker (str): The stock ticker symbol.
            inputs (dict): The model inputs.
            projection_years (int): Number of years to project.
            
        Returns:
            dict: The DDM model results.
        """
        try:
            # Extract inputs
            annual_dividend = inputs["annual_dividend"]
            dividend_growth = inputs.get("dividend_growth", 0.05)
            required_return = inputs.get("required_return", 0.09)
            
            # Check if the model is applicable
            if annual_dividend <= 0:
                return {"error": "No dividend data available"}
            
            if dividend_growth >= required_return:
                return {"error": "Dividend growth rate must be less than required return"}
            
            # Project dividends
            projected_dividends = []
            for year in range(1, projection_years + 1):
                year_dividend = annual_dividend * ((1 + dividend_growth) ** year)
                projected_dividends.append(year_dividend)
            
            # Calculate terminal value using Gordon Growth Model
            terminal_dividend = projected_dividends[-1] * (1 + dividend_growth)
            terminal_value = terminal_dividend / (required_return - dividend_growth)
            
            # Calculate present value of projected dividends
            present_values = []
            for i, dividend in enumerate(projected_dividends):
                year = i + 1
                present_value = dividend / ((1 + required_return) ** year)
                present_values.append(present_value)
            
            # Calculate present value of terminal value
            terminal_value_pv = terminal_value / ((1 + required_return) ** projection_years)
            
            # Sum present values to get fair value
            fair_value = sum(present_values) + terminal_value_pv
            
            # Calculate one-stage Gordon Growth Model value for comparison
            gordon_growth_value = annual_dividend * (1 + dividend_growth) / (required_return - dividend_growth)
            
            # Calculate sensitivity analysis
            sensitivity = self._calculate_ddm_sensitivity(inputs, gordon_growth_value)
            
            return {
                "projected_dividends": projected_dividends,
                "terminal_value": terminal_value,
                "present_values": present_values,
                "terminal_value_pv": terminal_value_pv,
                "fair_value": fair_value,
                "gordon_growth_value": gordon_growth_value,
                "sensitivity": sensitivity
            }
            
        except Exception as e:
            logger.error(f"Error building scenario DDM for {ticker}: {str(e)}")
            return {}
    
    def _calculate_ddm_sensitivity(self, inputs, base_fair_value):
        """
        Calculate sensitivity analysis for the DDM model.
        
        Args:
            inputs (dict): The model inputs.
            base_fair_value (float): The base fair value per share.
            
        Returns:
            dict: The sensitivity analysis results.
        """
        try:
            # Sensitivity to required return
            required_return = inputs.get("required_return", 0.09)
            required_return_sensitivity = {}
            
            for delta in [-0.02, -0.01, 0, 0.01, 0.02]:
                new_required_return = required_return + delta
                
                # Recalculate Gordon Growth Model with new required return
                if new_required_return > inputs.get("dividend_growth", 0.05):
                    annual_dividend = inputs["annual_dividend"]
                    dividend_growth = inputs.get("dividend_growth", 0.05)
                    
                    new_value = annual_dividend * (1 + dividend_growth) / (new_required_return - dividend_growth)
                    required_return_sensitivity[f"{new_required_return:.2f}"] = new_value
            
            # Sensitivity to dividend growth rate
            dividend_growth = inputs.get("dividend_growth", 0.05)
            dividend_growth_sensitivity = {}
            
            for delta in [-0.02, -0.01, 0, 0.01, 0.02]:
                new_dividend_growth = dividend_growth + delta
                
                # Recalculate Gordon Growth Model with new dividend growth
                if new_dividend_growth < required_return:
                    annual_dividend = inputs["annual_dividend"]
                    
                    new_value = annual_dividend * (1 + new_dividend_growth) / (required_return - new_dividend_growth)
                    dividend_growth_sensitivity[f"{new_dividend_growth:.2f}"] = new_value
            
            return {
                "required_return": required_return_sensitivity,
                "dividend_growth": dividend_growth_sensitivity
            }
            
        except Exception as e:
            logger.error(f"Error calculating DDM sensitivity: {str(e)}")
            return {}
    
    def _save_ddm_model(self, ticker, date, inputs, scenarios, results):
        """
        Save the DDM model to the database.
        
        Args:
            ticker (str): The stock ticker symbol.
            date (datetime): The date of the model.
            inputs (dict): The model inputs.
            scenarios (dict): The model scenarios.
            results (dict): The model results.
        """
        try:
            # Save each scenario as a separate document
            for scenario_name, scenario_result in results.items():
                # Skip scenarios with errors
                if "error" in scenario_result:
                    continue
                
                model_doc = {
                    "ticker": ticker,
                    "model_type": "ddm",
                    "date": date,
                    "scenario": scenario_name,
                    "inputs": inputs,
                    "assumptions": scenarios[scenario_name],
                    "results": scenario_result,
                    "target_price": scenario_result.get("fair_value", 0),
                    "fair_value": scenario_result.get("fair_value", 0),
                    "sensitivity_analysis": scenario_result.get("sensitivity", {})
                }
                
                # Update or insert the model
                self.db_ops.update_one(
                    VALUATION_MODELS_COLLECTION,
                    {
                        "ticker": ticker,
                        "model_type": "ddm",
                        "date": date,
                        "scenario": scenario_name
                    },
                    {"$set": model_doc},
                    upsert=True
                )
            
        except Exception as e:
            logger.error(f"Error saving DDM model for {ticker}: {str(e)}")
    
    def get_latest_ddm_model(self, ticker):
        """
        Get the latest DDM model for a ticker.
        
        Args:
            ticker (str): The stock ticker symbol.
            
        Returns:
            dict: The DDM model.
        """
        try:
            ticker = ticker.upper()
            
            # Get all scenarios for the latest date
            latest_date_model = self.db_ops.find_one(
                VALUATION_MODELS_COLLECTION,
                {
                    "ticker": ticker,
                    "model_type": "ddm"
                },
                {"sort": [("date", -1)]}
            )
            
            if not latest_date_model:
                logger.warning(f"No DDM model found for {ticker}")
                return {}
            
            latest_date = latest_date_model["date"]
            
            # Get all scenarios for this date
            scenarios = self.db_ops.find_many(
                VALUATION_MODELS_COLLECTION,
                {
                    "ticker": ticker,
                    "model_type": "ddm",
                    "date": latest_date
                }
            )
            
            if not scenarios:
                return {}
            
            # Reconstruct the full model
            model = {
                "ticker": ticker,
                "date": latest_date,
                "inputs": scenarios[0]["inputs"],
                "scenarios": {},
                "results": {}
            }
            
            for scenario in scenarios:
                scenario_name = scenario["scenario"]
                model["scenarios"][scenario_name] = scenario["assumptions"]
                model["results"][scenario_name] = scenario["results"]
            
            return model
            
        except Exception as e:
            logger.error(f"Error getting latest DDM model for {ticker}: {str(e)}")
            return {}