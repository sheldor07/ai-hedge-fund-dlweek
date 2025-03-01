import logging
from datetime import datetime
import numpy as np

from config.settings import DCF_DEFAULT_PERIODS, DCF_DEFAULT_TERMINAL_GROWTH, DCF_DEFAULT_DISCOUNT_RATE
from database.operations import db_ops
from database.schema import FINANCIAL_STATEMENTS_COLLECTION, VALUATION_MODELS_COLLECTION

logger = logging.getLogger("stock_analyzer.analysis.valuation.dcf")


class DCFModel:
    
    def __init__(self):
        self.db_ops = db_ops
    
    def build_dcf_model(self, ticker, projection_years=None, scenarios=None):
        try:
            ticker = ticker.upper()
            projection_years = projection_years or DCF_DEFAULT_PERIODS
            
            financial_statements = self.db_ops.find_many(
                FINANCIAL_STATEMENTS_COLLECTION,
                {"ticker": ticker, "period_type": "annual"},
                sort=[("period_end_date", -1)]
            )
            
            if not financial_statements:
                logger.warning(f"No financial statements found for {ticker}")
                return {}
            
            latest_statement = financial_statements[0]
            
            if not scenarios:
                scenarios = {
                    "base": {
                        "revenue_growth": 0.05,
                        "fcf_margin": 0.15,
                        "terminal_growth": DCF_DEFAULT_TERMINAL_GROWTH,
                        "discount_rate": DCF_DEFAULT_DISCOUNT_RATE
                    },
                    "bull": {
                        "revenue_growth": 0.08,
                        "fcf_margin": 0.18,
                        "terminal_growth": 0.03,
                        "discount_rate": 0.09
                    },
                    "bear": {
                        "revenue_growth": 0.02,
                        "fcf_margin": 0.12,
                        "terminal_growth": 0.02,
                        "discount_rate": 0.11
                    }
                }
            
            inputs = self._get_dcf_inputs(ticker, latest_statement)
            
            if not inputs:
                logger.warning(f"Could not get DCF inputs for {ticker}")
                return {}
            
            results = {}
            for scenario_name, scenario_params in scenarios.items():
                scenario_inputs = {**inputs, **scenario_params}
                
                dcf_result = self._build_scenario_dcf(ticker, scenario_inputs, projection_years)
                
                results[scenario_name] = dcf_result
            
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
        try:
            income_stmt = statement.get("income_statement_standardized", {})
            balance_sheet = statement.get("balance_sheet_standardized", {})
            cash_flow = statement.get("cash_flow_statement_standardized", {})
            
            price_data = self.db_ops.find_one(
                "price_history",
                {"ticker": ticker}
            )
            
            current_price = price_data.get("close", 0) if price_data else 0
            
            revenue = income_stmt.get("revenue", 0)
            net_income = income_stmt.get("net_income", 0)
            free_cash_flow = cash_flow.get("free_cash_flow")
            
            if free_cash_flow is None:
                operating_cash_flow = cash_flow.get("net_cash_from_operating_activities", 0)
                capital_expenditures = cash_flow.get("capital_expenditures", 0)
                free_cash_flow = operating_cash_flow - abs(capital_expenditures)
            
            growth_metrics = self.db_ops.find_one(
                "financial_metrics",
                {
                    "ticker": ticker,
                    "metric_type": "growth",
                    "period_type": "annual"
                }
            )
            
            revenue_growth = 0.05
            
            if growth_metrics and "metrics" in growth_metrics:
                if "cagr" in growth_metrics["metrics"] and "revenue_5yr" in growth_metrics["metrics"]["cagr"]:
                    revenue_growth = growth_metrics["metrics"]["cagr"]["revenue_5yr"]
                elif "yoy" in growth_metrics["metrics"] and "revenue" in growth_metrics["metrics"]["yoy"]:
                    revenue_growth = growth_metrics["metrics"]["yoy"]["revenue"]
            
            fcf_margin = free_cash_flow / revenue if revenue > 0 else 0.1
            
            shares_outstanding = income_stmt.get("shares_outstanding_diluted", 0)
            
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
        try:
            revenue = inputs["revenue"]
            fcf_margin = inputs["fcf_margin"]
            revenue_growth = inputs["revenue_growth"]
            terminal_growth = inputs.get("terminal_growth", DCF_DEFAULT_TERMINAL_GROWTH)
            discount_rate = inputs.get("discount_rate", DCF_DEFAULT_DISCOUNT_RATE)
            shares_outstanding = inputs["shares_outstanding"]
            total_debt = inputs["total_debt"]
            cash_and_equivalents = inputs["cash_and_equivalents"]
            
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
            
            terminal_fcf = projected_fcf[-1] * (1 + terminal_growth)
            terminal_value = terminal_fcf / (discount_rate - terminal_growth)
            
            present_values = []
            for i, fcf in enumerate(projected_fcf):
                year = i + 1
                present_value = fcf / ((1 + discount_rate) ** year)
                present_values.append(present_value)
            
            terminal_value_pv = terminal_value / ((1 + discount_rate) ** projection_years)
            
            total_present_value = sum(present_values) + terminal_value_pv
            
            enterprise_value = total_present_value
            equity_value = enterprise_value - total_debt + cash_and_equivalents
            
            if shares_outstanding > 0:
                fair_value_per_share = equity_value / shares_outstanding
            else:
                fair_value_per_share = 0
            
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
        try:
            discount_rate = inputs.get("discount_rate", DCF_DEFAULT_DISCOUNT_RATE)
            discount_rate_sensitivity = {}
            
            for delta in [-0.02, -0.01, 0, 0.01, 0.02]:
                new_discount_rate = discount_rate + delta
                
                new_inputs = inputs.copy()
                new_inputs["discount_rate"] = new_discount_rate
                
                new_result = self._build_simplified_dcf(new_inputs)
                
                discount_rate_sensitivity[f"{new_discount_rate:.2f}"] = new_result.get("fair_value_per_share", 0)
            
            terminal_growth = inputs.get("terminal_growth", DCF_DEFAULT_TERMINAL_GROWTH)
            terminal_growth_sensitivity = {}
            
            for delta in [-0.01, -0.005, 0, 0.005, 0.01]:
                new_terminal_growth = terminal_growth + delta
                
                new_inputs = inputs.copy()
                new_inputs["terminal_growth"] = new_terminal_growth
                
                new_result = self._build_simplified_dcf(new_inputs)
                
                terminal_growth_sensitivity[f"{new_terminal_growth:.2f}"] = new_result.get("fair_value_per_share", 0)
            
            revenue_growth = inputs.get("revenue_growth", 0.05)
            revenue_growth_sensitivity = {}
            
            for delta in [-0.02, -0.01, 0, 0.01, 0.02]:
                new_revenue_growth = revenue_growth + delta
                
                new_inputs = inputs.copy()
                new_inputs["revenue_growth"] = new_revenue_growth
                
                new_result = self._build_simplified_dcf(new_inputs)
                
                revenue_growth_sensitivity[f"{new_revenue_growth:.2f}"] = new_result.get("fair_value_per_share", 0)
            
            fcf_margin = inputs.get("fcf_margin", 0.15)
            fcf_margin_sensitivity = {}
            
            for delta in [-0.03, -0.015, 0, 0.015, 0.03]:
                new_fcf_margin = fcf_margin + delta
                
                new_inputs = inputs.copy()
                new_inputs["fcf_margin"] = new_fcf_margin
                
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
        try:
            revenue = inputs["revenue"]
            fcf_margin = inputs["fcf_margin"]
            revenue_growth = inputs["revenue_growth"]
            terminal_growth = inputs.get("terminal_growth", DCF_DEFAULT_TERMINAL_GROWTH)
            discount_rate = inputs.get("discount_rate", DCF_DEFAULT_DISCOUNT_RATE)
            shares_outstanding = inputs["shares_outstanding"]
            total_debt = inputs["total_debt"]
            cash_and_equivalents = inputs["cash_and_equivalents"]
            
            last_fcf = revenue * fcf_margin
            for year in range(1, projection_years + 1):
                last_fcf *= (1 + revenue_growth)
            
            terminal_fcf = last_fcf * (1 + terminal_growth)
            terminal_value = terminal_fcf / (discount_rate - terminal_growth)
            
            terminal_value_pv = terminal_value / ((1 + discount_rate) ** projection_years)
            
            present_value_sum = 0
            fcf = revenue * fcf_margin
            for year in range(1, projection_years + 1):
                fcf *= (1 + revenue_growth)
                present_value_sum += fcf / ((1 + discount_rate) ** year)
            
            total_present_value = present_value_sum + terminal_value_pv
            
            enterprise_value = total_present_value
            equity_value = enterprise_value - total_debt + cash_and_equivalents
            
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
        try:
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
        try:
            ticker = ticker.upper()
            
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