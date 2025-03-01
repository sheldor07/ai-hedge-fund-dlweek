"""
Discounted Cash Flow (DCF) model module.
"""

import logging
from datetime import datetime
import numpy as np

from config.settings import DCF_DEFAULT_PERIODS, DCF_DEFAULT_TERMINAL_GROWTH, DCF_DEFAULT_DISCOUNT_RATE
from database.operations import db_ops
from database.schema import FINANCIAL_STATEMENTS_COLLECTION, VALUATION_MODELS_COLLECTION

logger = logging.getLogger("stock_analyzer.analysis.valuation.dcf")


class DCFModel:
    """
    Implements a Discounted Cash Flow (DCF) model for stock valuation.
    """
    
    def __init__(self):
        """Initialize the DCFModel."""
        self.db_ops = db_ops
    
    def build_dcf_model(self, ticker, projection_years=None, scenarios=None):
        """
        Build a DCF model for a ticker.
        
        Args:
            ticker (str): The stock ticker symbol.
            projection_years (int, optional): Number of years to project. Defaults to DCF_DEFAULT_PERIODS.
            scenarios (dict, optional): Custom scenarios. Defaults to None.
            
        Returns:
            dict: The DCF model results.
        """
        try:
            ticker = ticker.upper()
            projection_years = projection_years or DCF_DEFAULT_PERIODS
            
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
            
            # Define default scenarios if not provided
            if not scenarios:
                scenarios = {
                    "base": {
                        "revenue_growth": 0.05,  # 5% annual growth
                        "fcf_margin": 0.15,      # 15% free cash flow margin
                        "terminal_growth": DCF_DEFAULT_TERMINAL_GROWTH,  # 2.5% terminal growth
                        "discount_rate": DCF_DEFAULT_DISCOUNT_RATE       # 10% discount rate
                    },
                    "bull": {
                        "revenue_growth": 0.08,  # 8% annual growth
                        "fcf_margin": 0.18,      # 18% free cash flow margin
                        "terminal_growth": 0.03,  # 3% terminal growth
                        "discount_rate": 0.09     # 9% discount rate
                    },
                    "bear": {
                        "revenue_growth": 0.02,  # 2% annual growth
                        "fcf_margin": 0.12,      # 12% free cash flow margin
                        "terminal_growth": 0.02,  # 2% terminal growth
                        "discount_rate": 0.11     # 11% discount rate
                    }
                }
            
            # Get inputs for the DCF model
            inputs = self._get_dcf_inputs(ticker, latest_statement)
            
            if not inputs:
                logger.warning(f"Could not get DCF inputs for {ticker}")
                return {}
            
            # Build the model for each scenario
            results = {}
            for scenario_name, scenario_params in scenarios.items():
                # Merge default inputs with scenario parameters
                scenario_inputs = {**inputs, **scenario_params}
                
                # Build DCF model for this scenario
                dcf_result = self._build_scenario_dcf(ticker, scenario_inputs, projection_years)
                
                # Store the result
                results[scenario_name] = dcf_result
            
            # Save the model to the database
            model_date = datetime.now()
            self._save_dcf_model(ticker, model_date, inputs, scenarios, results)
            
            return {
                "inputs": inputs,
                "scenarios": scenarios,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error building DCF model for {ticker}: {str(e)}")
            return {}
    
    def _get_dcf_inputs(self, ticker, statement):
        """
        Get inputs for the DCF model.
        
        Args:
            ticker (str): The stock ticker symbol.
            statement (dict): The financial statement.
            
        Returns:
            dict: The DCF inputs.
        """
        try:
            income_stmt = statement.get("income_statement_standardized", {})
            balance_sheet = statement.get("balance_sheet_standardized", {})
            cash_flow = statement.get("cash_flow_statement_standardized", {})
            
            # Get latest stock price
            price_data = self.db_ops.find_one(
                "price_history",
                {"ticker": ticker}
            )
            
            current_price = price_data.get("close", 0) if price_data else 0
            
            # Get key financial metrics
            revenue = income_stmt.get("revenue", 0)
            net_income = income_stmt.get("net_income", 0)
            free_cash_flow = cash_flow.get("free_cash_flow")
            
            # If free cash flow is not directly available, calculate it
            if free_cash_flow is None:
                operating_cash_flow = cash_flow.get("net_cash_from_operating_activities", 0)
                capital_expenditures = cash_flow.get("capital_expenditures", 0)
                free_cash_flow = operating_cash_flow - abs(capital_expenditures)
            
            # Get historical growth rates from financial metrics
            growth_metrics = self.db_ops.find_one(
                "financial_metrics",
                {
                    "ticker": ticker,
                    "metric_type": "growth",
                    "period_type": "annual"
                }
            )
            
            # Default growth rate if not available
            revenue_growth = 0.05  # 5% default
            
            if growth_metrics and "metrics" in growth_metrics:
                # Try to get 5-year CAGR if available
                if "cagr" in growth_metrics["metrics"] and "revenue_5yr" in growth_metrics["metrics"]["cagr"]:
                    revenue_growth = growth_metrics["metrics"]["cagr"]["revenue_5yr"]
                # Otherwise use YoY growth
                elif "yoy" in growth_metrics["metrics"] and "revenue" in growth_metrics["metrics"]["yoy"]:
                    revenue_growth = growth_metrics["metrics"]["yoy"]["revenue"]
            
            # Calculate FCF margin
            fcf_margin = free_cash_flow / revenue if revenue > 0 else 0.1  # Default 10% if can't calculate
            
            # Get shares outstanding
            shares_outstanding = income_stmt.get("shares_outstanding_diluted", 0)
            
            # Get debt and cash
            total_debt = balance_sheet.get("long_term_debt", 0) + balance_sheet.get("short_term_debt", 0)
            cash_and_equivalents = balance_sheet.get("cash_and_equivalents", 0)
            
            return {
                "revenue": revenue,
                "net_income": net_income,
                "free_cash_flow": free_cash_flow,
                "fcf_margin": fcf_margin,
                "revenue_growth": revenue_growth,
                "shares_outstanding": shares_outstanding,
                "current_price": current_price,
                "total_debt": total_debt,
                "cash_and_equivalents": cash_and_equivalents
            }
            
        except Exception as e:
            logger.error(f"Error getting DCF inputs for {ticker}: {str(e)}")
            return {}
    
    def _build_scenario_dcf(self, ticker, inputs, projection_years):
        """
        Build a DCF model for a specific scenario.
        
        Args:
            ticker (str): The stock ticker symbol.
            inputs (dict): The model inputs.
            projection_years (int): Number of years to project.
            
        Returns:
            dict: The DCF model results.
        """
        try:
            # Extract inputs
            revenue = inputs["revenue"]
            fcf_margin = inputs["fcf_margin"]
            revenue_growth = inputs["revenue_growth"]
            terminal_growth = inputs.get("terminal_growth", DCF_DEFAULT_TERMINAL_GROWTH)
            discount_rate = inputs.get("discount_rate", DCF_DEFAULT_DISCOUNT_RATE)
            shares_outstanding = inputs["shares_outstanding"]
            total_debt = inputs["total_debt"]
            cash_and_equivalents = inputs["cash_and_equivalents"]
            
            # Project revenue and free cash flow
            projected_revenue = []
            projected_fcf = []
            
            for year in range(1, projection_years + 1):
                if year == 1:
                    year_revenue = revenue * (1 + revenue_growth)
                else:
                    year_revenue = projected_revenue[-1] * (1 + revenue_growth)
                
                year_fcf = year_revenue * fcf_margin
                
                projected_revenue.append(year_revenue)
                projected_fcf.append(year_fcf)
            
            # Calculate terminal value
            terminal_fcf = projected_fcf[-1] * (1 + terminal_growth)
            terminal_value = terminal_fcf / (discount_rate - terminal_growth)
            
            # Calculate present value of projected cash flows
            present_values = []
            for i, fcf in enumerate(projected_fcf):
                year = i + 1
                present_value = fcf / ((1 + discount_rate) ** year)
                present_values.append(present_value)
            
            # Calculate present value of terminal value
            terminal_value_pv = terminal_value / ((1 + discount_rate) ** projection_years)
            
            # Sum present values
            total_present_value = sum(present_values) + terminal_value_pv
            
            # Calculate enterprise value and equity value
            enterprise_value = total_present_value
            equity_value = enterprise_value - total_debt + cash_and_equivalents
            
            # Calculate fair value per share
            if shares_outstanding > 0:
                fair_value_per_share = equity_value / shares_outstanding
            else:
                fair_value_per_share = 0
            
            # Calculate sensitivity analysis
            sensitivity = self._calculate_sensitivity(inputs, fair_value_per_share)
            
            return {
                "projected_revenue": projected_revenue,
                "projected_fcf": projected_fcf,
                "terminal_value": terminal_value,
                "present_values": present_values,
                "terminal_value_pv": terminal_value_pv,
                "total_present_value": total_present_value,
                "enterprise_value": enterprise_value,
                "equity_value": equity_value,
                "fair_value_per_share": fair_value_per_share,
                "sensitivity": sensitivity
            }
            
        except Exception as e:
            logger.error(f"Error building scenario DCF for {ticker}: {str(e)}")
            return {}
    
    def _calculate_sensitivity(self, inputs, base_fair_value):
        """
        Calculate sensitivity analysis for the DCF model.
        
        Args:
            inputs (dict): The model inputs.
            base_fair_value (float): The base fair value per share.
            
        Returns:
            dict: The sensitivity analysis results.
        """
        try:
            # Sensitivity to discount rate
            discount_rate = inputs.get("discount_rate", DCF_DEFAULT_DISCOUNT_RATE)
            discount_rate_sensitivity = {}
            
            for delta in [-0.02, -0.01, 0, 0.01, 0.02]:
                new_discount_rate = discount_rate + delta
                
                # Recalculate fair value with new discount rate
                new_inputs = inputs.copy()
                new_inputs["discount_rate"] = new_discount_rate
                
                # Build a simplified model for sensitivity analysis
                new_result = self._build_simplified_dcf(new_inputs)
                
                discount_rate_sensitivity[f"{new_discount_rate:.2f}"] = new_result.get("fair_value_per_share", 0)
            
            # Sensitivity to terminal growth rate
            terminal_growth = inputs.get("terminal_growth", DCF_DEFAULT_TERMINAL_GROWTH)
            terminal_growth_sensitivity = {}
            
            for delta in [-0.01, -0.005, 0, 0.005, 0.01]:
                new_terminal_growth = terminal_growth + delta
                
                # Recalculate fair value with new terminal growth
                new_inputs = inputs.copy()
                new_inputs["terminal_growth"] = new_terminal_growth
                
                # Build a simplified model for sensitivity analysis
                new_result = self._build_simplified_dcf(new_inputs)
                
                terminal_growth_sensitivity[f"{new_terminal_growth:.2f}"] = new_result.get("fair_value_per_share", 0)
            
            # Sensitivity to revenue growth
            revenue_growth = inputs.get("revenue_growth", 0.05)
            revenue_growth_sensitivity = {}
            
            for delta in [-0.02, -0.01, 0, 0.01, 0.02]:
                new_revenue_growth = revenue_growth + delta
                
                # Recalculate fair value with new revenue growth
                new_inputs = inputs.copy()
                new_inputs["revenue_growth"] = new_revenue_growth
                
                # Build a simplified model for sensitivity analysis
                new_result = self._build_simplified_dcf(new_inputs)
                
                revenue_growth_sensitivity[f"{new_revenue_growth:.2f}"] = new_result.get("fair_value_per_share", 0)
            
            # Sensitivity to FCF margin
            fcf_margin = inputs.get("fcf_margin", 0.15)
            fcf_margin_sensitivity = {}
            
            for delta in [-0.03, -0.015, 0, 0.015, 0.03]:
                new_fcf_margin = fcf_margin + delta
                
                # Recalculate fair value with new FCF margin
                new_inputs = inputs.copy()
                new_inputs["fcf_margin"] = new_fcf_margin
                
                # Build a simplified model for sensitivity analysis
                new_result = self._build_simplified_dcf(new_inputs)
                
                fcf_margin_sensitivity[f"{new_fcf_margin:.2f}"] = new_result.get("fair_value_per_share", 0)
            
            return {
                "discount_rate": discount_rate_sensitivity,
                "terminal_growth": terminal_growth_sensitivity,
                "revenue_growth": revenue_growth_sensitivity,
                "fcf_margin": fcf_margin_sensitivity
            }
            
        except Exception as e:
            logger.error(f"Error calculating DCF sensitivity: {str(e)}")
            return {}
    
    def _build_simplified_dcf(self, inputs, projection_years=5):
        """
        Build a simplified DCF model for sensitivity analysis.
        
        Args:
            inputs (dict): The model inputs.
            projection_years (int, optional): Number of years to project. Defaults to 5.
            
        Returns:
            dict: The simplified DCF model results.
        """
        try:
            # Extract inputs
            revenue = inputs["revenue"]
            fcf_margin = inputs["fcf_margin"]
            revenue_growth = inputs["revenue_growth"]
            terminal_growth = inputs.get("terminal_growth", DCF_DEFAULT_TERMINAL_GROWTH)
            discount_rate = inputs.get("discount_rate", DCF_DEFAULT_DISCOUNT_RATE)
            shares_outstanding = inputs["shares_outstanding"]
            total_debt = inputs["total_debt"]
            cash_and_equivalents = inputs["cash_and_equivalents"]
            
            # Project FCF (simplified)
            last_fcf = revenue * fcf_margin
            for year in range(1, projection_years + 1):
                last_fcf *= (1 + revenue_growth)
            
            # Calculate terminal value
            terminal_fcf = last_fcf * (1 + terminal_growth)
            terminal_value = terminal_fcf / (discount_rate - terminal_growth)
            
            # Calculate present value of terminal value
            terminal_value_pv = terminal_value / ((1 + discount_rate) ** projection_years)
            
            # Simplify present value of projected cash flows
            present_value_sum = 0
            fcf = revenue * fcf_margin
            for year in range(1, projection_years + 1):
                fcf *= (1 + revenue_growth)
                present_value_sum += fcf / ((1 + discount_rate) ** year)
            
            # Sum present values
            total_present_value = present_value_sum + terminal_value_pv
            
            # Calculate enterprise value and equity value
            enterprise_value = total_present_value
            equity_value = enterprise_value - total_debt + cash_and_equivalents
            
            # Calculate fair value per share
            if shares_outstanding > 0:
                fair_value_per_share = equity_value / shares_outstanding
            else:
                fair_value_per_share = 0
            
            return {
                "enterprise_value": enterprise_value,
                "equity_value": equity_value,
                "fair_value_per_share": fair_value_per_share
            }
            
        except Exception as e:
            logger.error(f"Error building simplified DCF: {str(e)}")
            return {}
    
    def _save_dcf_model(self, ticker, date, inputs, scenarios, results):
        """
        Save the DCF model to the database.
        
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
                model_doc = {
                    "ticker": ticker,
                    "model_type": "dcf",
                    "date": date,
                    "scenario": scenario_name,
                    "inputs": inputs,
                    "assumptions": scenarios[scenario_name],
                    "results": scenario_result,
                    "target_price": scenario_result.get("fair_value_per_share", 0),
                    "fair_value": scenario_result.get("fair_value_per_share", 0),
                    "sensitivity_analysis": scenario_result.get("sensitivity", {})
                }
                
                # Update or insert the model
                self.db_ops.update_one(
                    VALUATION_MODELS_COLLECTION,
                    {
                        "ticker": ticker,
                        "model_type": "dcf",
                        "date": date,
                        "scenario": scenario_name
                    },
                    {"$set": model_doc},
                    upsert=True
                )
            
        except Exception as e:
            logger.error(f"Error saving DCF model for {ticker}: {str(e)}")
    
    def get_latest_dcf_model(self, ticker):
        """
        Get the latest DCF model for a ticker.
        
        Args:
            ticker (str): The stock ticker symbol.
            
        Returns:
            dict: The DCF model.
        """
        try:
            ticker = ticker.upper()
            
            # Get all scenarios for the latest date
            latest_date_model = self.db_ops.find_one(
                VALUATION_MODELS_COLLECTION,
                {
                    "ticker": ticker,
                    "model_type": "dcf"
                }
            )
            
            if not latest_date_model:
                logger.warning(f"No DCF model found for {ticker}")
                return {}
            
            latest_date = latest_date_model["date"]
            
            # Get all scenarios for this date
            scenarios = self.db_ops.find_many(
                VALUATION_MODELS_COLLECTION,
                {
                    "ticker": ticker,
                    "model_type": "dcf",
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
            logger.error(f"Error getting latest DCF model for {ticker}: {str(e)}")
            return {}