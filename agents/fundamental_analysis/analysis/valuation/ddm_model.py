import logging
from datetime import datetime

from database.operations import db_ops
from database.schema import FINANCIAL_STATEMENTS_COLLECTION, VALUATION_MODELS_COLLECTION

logger = logging.getLogger("stock_analyzer.analysis.valuation.ddm")


class DDMModel:
    
    def __init__(self):
        self.db_ops = db_ops
    
    def build_ddm_model(self, ticker, projection_years=5, scenarios=None):
        try:
            ticker = ticker.upper()
            
            financial_statements = self.db_ops.find_many(
                FINANCIAL_STATEMENTS_COLLECTION,
                {"ticker": ticker, "period_type": "annual"},
                sort=[("period_end_date", -1)]
            )
            
            if not financial_statements:
                logger.warning(f"No financial statements found for {ticker}")
                return {}
            
            latest_statement = financial_statements[0]
            
            cash_flow = latest_statement.get("cash_flow_statement_standardized", {})
            
            if "dividends_paid" not in cash_flow or cash_flow["dividends_paid"] >= 0:
                logger.warning(f"{ticker} does not pay dividends or dividend data is not available")
                return {"error": "No dividend data available"}
            
            if not scenarios:
                scenarios = {
                    "base": {
                        "dividend_growth": 0.05,
                        "required_return": 0.09
                    },
                    "bull": {
                        "dividend_growth": 0.07,
                        "required_return": 0.08
                    },
                    "bear": {
                        "dividend_growth": 0.03,
                        "required_return": 0.10
                    }
                }
            
            inputs = self._get_ddm_inputs(ticker, latest_statement)
            
            if not inputs:
                logger.warning(f"Could not get DDM inputs for {ticker}")
                return {}
            
            results = {}
            for scenario_name, scenario_params in scenarios.items():
                scenario_inputs = {**inputs, **scenario_params}
                
                ddm_result = self._build_scenario_ddm(ticker, scenario_inputs, projection_years)
                
                results[scenario_name] = ddm_result
            
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
        try:
            income_stmt = statement.get("income_statement_standardized", {})
            cash_flow = statement.get("cash_flow_statement_standardized", {})
            
            price_data = self.db_ops.find_one(
                "price_history",
                {"ticker": ticker},
                {"sort": [("date", -1)]}
            )
            
            current_price = price_data.get("close", 0) if price_data else 0
            
            shares_outstanding = income_stmt.get("shares_outstanding_diluted", 0)
            
            if "dividends_paid" in cash_flow and cash_flow["dividends_paid"] < 0 and shares_outstanding > 0:
                annual_dividend = abs(cash_flow["dividends_paid"]) / shares_outstanding
            else:
                annual_dividend = price_data.get("dividends", 0) * 4 if price_data else 0
            
            dividend_yield = annual_dividend / current_price if current_price > 0 else 0
            
            dividend_growth = 0.05
            
            previous_statements = self.db_ops.find_many(
                FINANCIAL_STATEMENTS_COLLECTION,
                {"ticker": ticker, "period_type": "annual"},
                sort=[("period_end_date", -1)],
                limit=5
            )
            
            if len(previous_statements) > 1:
                dividends = []
                for stmt in reversed(previous_statements):
                    stmt_cash_flow = stmt.get("cash_flow_statement_standardized", {})
                    stmt_income = stmt.get("income_statement_standardized", {})
                    
                    if "dividends_paid" in stmt_cash_flow and stmt_cash_flow["dividends_paid"] < 0:
                        stmt_shares = stmt_income.get("shares_outstanding_diluted", 0)
                        if stmt_shares > 0:
                            div_per_share = abs(stmt_cash_flow["dividends_paid"]) / stmt_shares
                            dividends.append(div_per_share)
                
                if len(dividends) >= 2:
                    growth_rates = []
                    for i in range(1, len(dividends)):
                        if dividends[i-1] > 0:
                            growth = (dividends[i] - dividends[i-1]) / dividends[i-1]
                            growth_rates.append(growth)
                    
                    if growth_rates:
                        dividend_growth = sum(growth_rates) / len(growth_rates)
            
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
        try:
            annual_dividend = inputs["annual_dividend"]
            dividend_growth = inputs.get("dividend_growth", 0.05)
            required_return = inputs.get("required_return", 0.09)
            
            if annual_dividend <= 0:
                return {"error": "No dividend data available"}
            
            if dividend_growth >= required_return:
                return {"error": "Dividend growth rate must be less than required return"}
            
            projected_dividends = []
            for year in range(1, projection_years + 1):
                year_dividend = annual_dividend * ((1 + dividend_growth) ** year)
                projected_dividends.append(year_dividend)
            
            terminal_dividend = projected_dividends[-1] * (1 + dividend_growth)
            terminal_value = terminal_dividend / (required_return - dividend_growth)
            
            present_values = []
            for i, dividend in enumerate(projected_dividends):
                year = i + 1
                present_value = dividend / ((1 + required_return) ** year)
                present_values.append(present_value)
            
            terminal_value_pv = terminal_value / ((1 + required_return) ** projection_years)
            
            fair_value = sum(present_values) + terminal_value_pv
            
            gordon_growth_value = annual_dividend * (1 + dividend_growth) / (required_return - dividend_growth)
            
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
        try:
            required_return = inputs.get("required_return", 0.09)
            required_return_sensitivity = {}
            
            for delta in [-0.02, -0.01, 0, 0.01, 0.02]:
                new_required_return = required_return + delta
                
                if new_required_return > inputs.get("dividend_growth", 0.05):
                    annual_dividend = inputs["annual_dividend"]
                    dividend_growth = inputs.get("dividend_growth", 0.05)
                    
                    new_value = annual_dividend * (1 + dividend_growth) / (new_required_return - dividend_growth)
                    required_return_sensitivity[f"{new_required_return:.2f}"] = new_value
            
            dividend_growth = inputs.get("dividend_growth", 0.05)
            dividend_growth_sensitivity = {}
            
            for delta in [-0.02, -0.01, 0, 0.01, 0.02]:
                new_dividend_growth = dividend_growth + delta
                
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
        try:
            for scenario_name, scenario_result in results.items():
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
        try:
            ticker = ticker.upper()
            
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