import logging
from datetime import datetime
import pandas as pd
import numpy as np

from database.operations import db_ops
from database.schema import FINANCIAL_STATEMENTS_COLLECTION

logger = logging.getLogger("stock_analyzer.analysis.risk.scenario")


class ScenarioAnalysis:
    
    def __init__(self):
        self.db_ops = db_ops
    
    def run_scenario_analysis(self, ticker, scenarios=None):
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
            
            dcf_model = self.db_ops.find_one(
                "valuation_models",
                {
                    "ticker": ticker,
                    "model_type": "dcf"
                }
            )
            
            if not scenarios:
                scenarios = {
                    "base": {
                        "probability": 0.5,
                        "description": "Base case scenario with moderate growth",
                        "revenue_growth": 0.05,
                        "margin_change": 0.0,
                        "multiple_change": 0.0,
                        "macro_factors": {
                            "interest_rates": "stable",
                            "gdp_growth": "moderate",
                            "inflation": "moderate"
                        }
                    },
                    "bull": {
                        "probability": 0.25,
                        "description": "Optimistic scenario with strong growth",
                        "revenue_growth": 0.08,
                        "margin_change": 0.02,
                        "multiple_change": 0.1,
                        "macro_factors": {
                            "interest_rates": "decreasing",
                            "gdp_growth": "strong",
                            "inflation": "low"
                        }
                    },
                    "bear": {
                        "probability": 0.25,
                        "description": "Pessimistic scenario with weak growth",
                        "revenue_growth": 0.02,
                        "margin_change": -0.02,
                        "multiple_change": -0.1,
                        "macro_factors": {
                            "interest_rates": "increasing",
                            "gdp_growth": "weak",
                            "inflation": "high"
                        }
                    }
                }
            
            inputs = self._get_scenario_inputs(ticker, latest_statement, dcf_model)
            
            if not inputs:
                logger.warning(f"Could not get scenario inputs for {ticker}")
                return {}
            
            results = {}
            for scenario_name, scenario_params in scenarios.items():
                scenario_result = self._run_scenario(ticker, inputs, scenario_params)
                results[scenario_name] = scenario_result
            
            expected_value = self._calculate_expected_value(results)
            
            analysis_date = datetime.now()
            self._save_scenario_analysis(ticker, analysis_date, inputs, scenarios, results, expected_value)
            
            return {
                "ticker": ticker,
                "date": analysis_date,
                "inputs": inputs,
                "scenarios": scenarios,
                "results": results,
                "expected_value": expected_value
            }
            
        except Exception as e:
            logger.error(f"Error running scenario analysis for {ticker}: {str(e)}")
            return {}
    
    def _get_scenario_inputs(self, ticker, statement, dcf_model):
        try:
            income_stmt = statement.get("income_statement_standardized", {})
            
            try:
                price_data_list = self.db_ops.find_many(
                    "price_history",
                    {"ticker": ticker},
                    sort=[("date", -1)],
                    limit=1
                )
                
                price_data = price_data_list[0] if price_data_list else None
                current_price = price_data.get("close", 0) if price_data else 0
                
                if current_price == 0:
                    logger.warning(f"No price data found for {ticker} in _get_scenario_inputs, using default value")
                    current_price = 100
            except Exception as e:
                logger.error(f"Error retrieving price data for {ticker} in _get_scenario_inputs: {str(e)}")
                current_price = 100
            
            revenue = income_stmt.get("revenue", 0)
            net_income = income_stmt.get("net_income", 0)
            
            profit_margin = net_income / revenue if revenue > 0 else 0
            
            eps = income_stmt.get("eps_diluted", 0)
            pe_multiple = current_price / eps if eps > 0 else 15
            
            dcf_fair_value = dcf_model.get("fair_value", current_price) if dcf_model else current_price
            
            return {
                "ticker": ticker,
                "current_price": current_price,
                "revenue": revenue,
                "net_income": net_income,
                "profit_margin": profit_margin,
                "eps": eps,
                "pe_multiple": pe_multiple,
                "dcf_fair_value": dcf_fair_value
            }
            
        except Exception as e:
            logger.error(f"Error getting scenario inputs for {ticker}: {str(e)}")
            return {}
    
    def _run_scenario(self, ticker, inputs, scenario_params):
        try:
            current_price = inputs["current_price"]
            revenue = inputs["revenue"]
            profit_margin = inputs["profit_margin"]
            pe_multiple = inputs["pe_multiple"]
            
            revenue_growth = scenario_params.get("revenue_growth", 0.05)
            margin_change = scenario_params.get("margin_change", 0.0)
            multiple_change = scenario_params.get("multiple_change", 0.0)
            
            scenario_revenue = revenue * (1 + revenue_growth)
            scenario_profit_margin = profit_margin + margin_change
            scenario_net_income = scenario_revenue * scenario_profit_margin
            
            shares_outstanding = inputs["net_income"] / inputs["eps"] if inputs["eps"] and inputs["eps"] > 0 and inputs["net_income"] and inputs["net_income"] > 0 else 1
                
            scenario_eps = scenario_net_income / shares_outstanding if shares_outstanding > 0 else 0
            
            scenario_pe = pe_multiple * (1 + multiple_change)
            
            target_price = scenario_eps * scenario_pe
            
            upside_percent = (target_price / current_price - 1) * 100 if current_price > 0 else 0
            
            revenue_change = scenario_revenue - revenue
            revenue_change_percent = (revenue_change / revenue) * 100 if revenue > 0 else 0
            
            income_change = scenario_net_income - inputs["net_income"]
            income_change_percent = (income_change / inputs["net_income"]) * 100 if inputs["net_income"] > 0 else 0
            
            return {
                "target_price": target_price,
                "upside_percent": upside_percent,
                "scenario_revenue": scenario_revenue,
                "scenario_profit_margin": scenario_profit_margin,
                "scenario_net_income": scenario_net_income,
                "scenario_eps": scenario_eps,
                "scenario_pe": scenario_pe,
                "revenue_change": revenue_change,
                "revenue_change_percent": revenue_change_percent,
                "income_change": income_change,
                "income_change_percent": income_change_percent
            }
            
        except Exception as e:
            logger.error(f"Error running scenario for {ticker}: {str(e)}")
            return {}
    
    def _calculate_expected_value(self, results):
        try:
            expected_price = 0
            target_prices = []
            probabilities = []
            
            default_probs = {
                "base": 0.5,
                "bull": 0.25,
                "bear": 0.25
            }
            
            for scenario_name, scenario_result in results.items():
                target_price = scenario_result.get("target_price", 0)
                probability = default_probs.get(scenario_name, 1/len(results))
                
                expected_price += target_price * probability
                target_prices.append(target_price)
                probabilities.append(probability)
            
            if not target_prices or all(p == 0 for p in target_prices):
                return {
                    "expected_price": 0,
                    "std_dev": 0,
                    "downside_risk": 0,
                    "coefficient_of_variation": 0
                }
                
            weighted_variance = sum(probabilities[i] * (target_prices[i] - expected_price) ** 2 for i in range(len(target_prices)))
            std_dev = np.sqrt(weighted_variance)
            
            downside_variance = sum(probabilities[i] * min(0, target_prices[i] - expected_price) ** 2 for i in range(len(target_prices)))
            downside_risk = np.sqrt(downside_variance)
            
            return {
                "expected_price": expected_price,
                "std_dev": std_dev,
                "downside_risk": downside_risk,
                "coefficient_of_variation": std_dev / expected_price if expected_price > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating expected value: {str(e)}")
            return {}
    
    def _save_scenario_analysis(self, ticker, date, inputs, scenarios, results, expected_value):
        try:
            analysis_doc = {
                "ticker": ticker,
                "date": date,
                "inputs": inputs,
                "scenarios": scenarios,
                "results": results,
                "expected_value": expected_value
            }
            
            self.db_ops.update_one(
                "scenario_analyses",
                {
                    "ticker": ticker
                },
                {"$set": analysis_doc},
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error saving scenario analysis for {ticker}: {str(e)}")
    
    def get_latest_scenario_analysis(self, ticker):
        try:
            ticker = ticker.upper()
            
            analysis = self.db_ops.find_one(
                "scenario_analyses",
                {"ticker": ticker}
            )
            
            if not analysis:
                logger.warning(f"No scenario analysis found for {ticker}")
                return {}
            
            return {
                "ticker": ticker,
                "date": analysis["date"],
                "inputs": analysis["inputs"],
                "scenarios": analysis["scenarios"],
                "results": analysis["results"],
                "expected_value": analysis["expected_value"]
            }
            
        except Exception as e:
            logger.error(f"Error getting scenario analysis for {ticker}: {str(e)}")
            return {}
    
    def run_stress_test(self, ticker, stress_factors=None):
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
            
            if not stress_factors:
                stress_factors = {
                    "revenue_shock": -0.2,
                    "margin_shock": -0.1,
                    "multiple_contraction": -0.3,
                    "market_crash": -0.4
                }
            
            inputs = self._get_stress_test_inputs(ticker, latest_statement)
            
            if not inputs:
                logger.warning(f"Could not get stress test inputs for {ticker}")
                return {}
            
            results = {}
            for factor_name, factor_value in stress_factors.items():
                stress_result = self._run_stress_factor(ticker, inputs, factor_name, factor_value)
                results[factor_name] = stress_result
            
            test_date = datetime.now()
            self._save_stress_test(ticker, test_date, inputs, stress_factors, results)
            
            return {
                "ticker": ticker,
                "date": test_date,
                "inputs": inputs,
                "stress_factors": stress_factors,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error running stress test for {ticker}: {str(e)}")
            return {}
    
    def _get_stress_test_inputs(self, ticker, statement):
        try:
            income_stmt = statement.get("income_statement_standardized", {})
            balance_sheet = statement.get("balance_sheet_standardized", {})
            
            try:
                price_data_list = self.db_ops.find_many(
                    "price_history",
                    {"ticker": ticker},
                    sort=[("date", -1)],
                    limit=1
                )
                
                price_data = price_data_list[0] if price_data_list else None
                current_price = price_data.get("close", 0) if price_data else 0
                
                if current_price == 0:
                    logger.warning(f"No price data found for {ticker} in _get_stress_test_inputs, using default value")
                    current_price = 100
            except Exception as e:
                logger.error(f"Error retrieving price data for {ticker} in _get_stress_test_inputs: {str(e)}")
                current_price = 100
            
            revenue = income_stmt.get("revenue", 0)
            net_income = income_stmt.get("net_income", 0)
            
            profit_margin = net_income / revenue if revenue > 0 else 0
            
            eps = income_stmt.get("eps_diluted", 0)
            pe_multiple = current_price / eps if eps > 0 else 15
            
            total_assets = balance_sheet.get("total_assets", 0)
            total_debt = balance_sheet.get("long_term_debt", 0) + balance_sheet.get("short_term_debt", 0)
            
            debt_to_asset = total_debt / total_assets if total_assets > 0 else 0
            
            return {
                "ticker": ticker,
                "current_price": current_price,
                "revenue": revenue,
                "net_income": net_income,
                "profit_margin": profit_margin,
                "eps": eps,
                "pe_multiple": pe_multiple,
                "total_assets": total_assets,
                "total_debt": total_debt,
                "debt_to_asset": debt_to_asset
            }
            
        except Exception as e:
            logger.error(f"Error getting stress test inputs for {ticker}: {str(e)}")
            return {}
    
    def _run_stress_factor(self, ticker, inputs, factor_name, factor_value):
        try:
            current_price = inputs["current_price"]
            revenue = inputs["revenue"]
            profit_margin = inputs["profit_margin"]
            pe_multiple = inputs["pe_multiple"]
            
            if factor_name == "revenue_shock":
                stressed_revenue = revenue * (1 + factor_value)
                stressed_profit_margin = profit_margin
                stressed_pe = pe_multiple
            elif factor_name == "margin_shock":
                stressed_revenue = revenue
                stressed_profit_margin = max(0, profit_margin + factor_value)
                stressed_pe = pe_multiple
            elif factor_name == "multiple_contraction":
                stressed_revenue = revenue
                stressed_profit_margin = profit_margin
                stressed_pe = pe_multiple * (1 + factor_value)
            elif factor_name == "market_crash":
                stressed_revenue = revenue * (1 + factor_value * 0.5)
                stressed_profit_margin = max(0, profit_margin + factor_value * 0.3)
                stressed_pe = pe_multiple * (1 + factor_value)
            else:
                stressed_revenue = revenue
                stressed_profit_margin = profit_margin
                stressed_pe = pe_multiple
            
            stressed_net_income = stressed_revenue * stressed_profit_margin
            
            shares_outstanding = inputs["net_income"] / inputs["eps"] if inputs["eps"] and inputs["eps"] > 0 and inputs["net_income"] and inputs["net_income"] > 0 else 1
                
            stressed_eps = stressed_net_income / shares_outstanding if shares_outstanding > 0 else 0
            
            stressed_price = stressed_eps * stressed_pe
            
            price_impact = stressed_price - current_price
            price_impact_percent = (price_impact / current_price) * 100 if current_price > 0 else 0
            
            return {
                "stressed_price": stressed_price,
                "price_impact": price_impact,
                "price_impact_percent": price_impact_percent,
                "stressed_revenue": stressed_revenue,
                "stressed_profit_margin": stressed_profit_margin,
                "stressed_net_income": stressed_net_income,
                "stressed_eps": stressed_eps,
                "stressed_pe": stressed_pe
            }
            
        except Exception as e:
            logger.error(f"Error running stress factor {factor_name} for {ticker}: {str(e)}")
            return {}
    
    def _save_stress_test(self, ticker, date, inputs, stress_factors, results):
        try:
            test_doc = {
                "ticker": ticker,
                "date": date,
                "inputs": inputs,
                "stress_factors": stress_factors,
                "results": results
            }
            
            self.db_ops.update_one(
                "stress_tests",
                {
                    "ticker": ticker
                },
                {"$set": test_doc},
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error saving stress test for {ticker}: {str(e)}")
    
    def get_latest_stress_test(self, ticker):
        try:
            ticker = ticker.upper()
            
            test = self.db_ops.find_one(
                "stress_tests",
                {"ticker": ticker}
            )
            
            if not test:
                logger.warning(f"No stress test found for {ticker}")
                return {}
            
            return {
                "ticker": ticker,
                "date": test["date"],
                "inputs": test["inputs"],
                "stress_factors": test["stress_factors"],
                "results": test["results"]
            }
            
        except Exception as e:
            logger.error(f"Error getting stress test for {ticker}: {str(e)}")
            return {}