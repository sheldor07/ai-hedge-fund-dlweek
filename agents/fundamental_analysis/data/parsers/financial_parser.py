"""
Financial statement parser.
"""

import logging
import re
from datetime import datetime

from database.operations import db_ops
from database.schema import FINANCIAL_STATEMENTS_COLLECTION

logger = logging.getLogger("stock_analyzer.data.parsers.financial")


class FinancialStatementParser:
    """
    Parses financial statements from various sources.
    """
    
    def __init__(self):
        """Initialize the FinancialStatementParser."""
        self.db_ops = db_ops
    
    def standardize_financial_statements(self, ticker, period_type="annual"):
        """
        Standardize financial statements in the database for a specific ticker.
        
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
                sort=[("period_end_date", -1)]
            )
            
            if not financial_statements:
                logger.warning(f"No {period_type} financial statements found for {ticker}")
                return False
            
            # Process each statement
            for statement in financial_statements:
                standardized = self._standardize_statement(statement)
                
                # Update the database with standardized statement
                self.db_ops.update_one(
                    FINANCIAL_STATEMENTS_COLLECTION,
                    {"_id": statement["_id"]},
                    {"$set": standardized}
                )
            
            logger.info(f"Standardized {len(financial_statements)} {period_type} financial statements for {ticker}")
            return True
            
        except Exception as e:
            logger.error(f"Error standardizing financial statements for {ticker}: {str(e)}")
            return False
    
    def _standardize_statement(self, statement):
        """
        Standardize a financial statement.
        
        Args:
            statement (dict): The financial statement.
            
        Returns:
            dict: The standardized financial statement.
        """
        standardized = {
            "income_statement_standardized": self._standardize_income_statement(statement.get("income_statement", {})),
            "balance_sheet_standardized": self._standardize_balance_sheet(statement.get("balance_sheet", {})),
            "cash_flow_statement_standardized": self._standardize_cash_flow(statement.get("cash_flow_statement", {}))
        }
        
        return standardized
    
    def _standardize_income_statement(self, income_statement):
        """
        Standardize an income statement.
        
        Args:
            income_statement (dict): The income statement.
            
        Returns:
            dict: The standardized income statement.
        """
        # Map of standard fields to possible source fields
        field_mapping = {
            "revenue": ["revenue", "totalrevenue", "netrevenue", "sales", "netsales"],
            "cost_of_revenue": ["costofrevenue", "costofgoodssold", "cogs"],
            "gross_profit": ["grossprofit"],
            "operating_expenses": ["operatingexpenses", "totaloperatingexpenses"],
            "research_development": ["researchanddevelopment", "r&d", "researchdevelopment"],
            "selling_general_admin": ["sellinggeneralandadministrative", "sga"],
            "operating_income": ["operatingincome", "operatingprofit", "ebit"],
            "interest_expense": ["interestexpense"],
            "interest_income": ["interestincome"],
            "other_income_expense": ["otherincome", "otherexpense", "otherincomesexpenses"],
            "income_before_tax": ["incomebeforetax", "pretaxincome", "ebt"],
            "income_tax_expense": ["incometaxexpense", "taxexpense"],
            "net_income": ["netincome", "netearnings", "profit"],
            "eps_basic": ["basiceps", "earningspersharebasic"],
            "eps_diluted": ["dilutedeps", "earningspersharediluted"],
            "shares_outstanding_basic": ["weightedaverageshares", "basicshares"],
            "shares_outstanding_diluted": ["weightedaveragesharesiluted", "dilutedshares"]
        }
        
        # Create standardized statement
        standardized = {}
        
        for standard_field, source_fields in field_mapping.items():
            for source_field in source_fields:
                # Try to find a matching field (case-insensitive)
                value = self._find_field_case_insensitive(income_statement, source_field)
                if value is not None:
                    standardized[standard_field] = value
                    break
        
        # Calculate derived metrics if possible
        if "revenue" in standardized and "cost_of_revenue" in standardized and "gross_profit" not in standardized:
            standardized["gross_profit"] = standardized["revenue"] - standardized["cost_of_revenue"]
        
        if "gross_profit" in standardized and "operating_expenses" in standardized and "operating_income" not in standardized:
            standardized["operating_income"] = standardized["gross_profit"] - standardized["operating_expenses"]
        
        if "operating_income" in standardized and "interest_expense" in standardized and "income_before_tax" not in standardized:
            standardized["income_before_tax"] = standardized["operating_income"] - standardized["interest_expense"]
        
        if "income_before_tax" in standardized and "income_tax_expense" in standardized and "net_income" not in standardized:
            standardized["net_income"] = standardized["income_before_tax"] - standardized["income_tax_expense"]
        
        return standardized
    
    def _standardize_balance_sheet(self, balance_sheet):
        """
        Standardize a balance sheet.
        
        Args:
            balance_sheet (dict): The balance sheet.
            
        Returns:
            dict: The standardized balance sheet.
        """
        # Map of standard fields to possible source fields
        field_mapping = {
            # Assets
            "total_assets": ["totalassets", "assets"],
            "current_assets": ["currentassets"],
            "cash_and_equivalents": ["cashandcashequivalents", "cash"],
            "short_term_investments": ["shorterminvestments", "marketablesecurities"],
            "accounts_receivable": ["accountsreceivable", "tradereceivables"],
            "inventory": ["inventory", "inventories"],
            "other_current_assets": ["othercurrentassets"],
            
            # Non-current assets
            "long_term_investments": ["longterminvestments", "investments"],
            "property_plant_equipment": ["propertyplantandequipment", "ppe", "fixedassets"],
            "goodwill": ["goodwill"],
            "intangible_assets": ["intangibleassets"],
            "other_non_current_assets": ["othernoncurrentassets", "otherlongtermassets"],
            
            # Liabilities
            "total_liabilities": ["totalliabilities", "liabilities"],
            "current_liabilities": ["currentliabilities"],
            "accounts_payable": ["accountspayable", "tradepayables"],
            "short_term_debt": ["shorttermdebt", "currentportionoflongtermdebt"],
            "other_current_liabilities": ["othercurrentliabilities"],
            
            # Non-current liabilities
            "long_term_debt": ["longtermdebt", "debtlongterm"],
            "deferred_revenue": ["deferredrevenue", "unearnedrevenue"],
            "deferred_tax_liabilities": ["deferredtaxliabilities"],
            "other_non_current_liabilities": ["othernoncurrentliabilities", "otherlongtermliabilities"],
            
            # Equity
            "total_equity": ["totalequity", "stockholdersequity", "shareholdersequity"],
            "common_stock": ["commonstock", "parvalue"],
            "additional_paid_in_capital": ["additionalpaidincapital", "capitalsurplus"],
            "retained_earnings": ["retainedearnings", "accumulateddeficit"],
            "treasury_stock": ["treasurystock"],
            "accumulated_other_comprehensive_income": ["accumulatedothercomprehensiveincome", "aoci"]
        }
        
        # Create standardized statement
        standardized = {}
        
        for standard_field, source_fields in field_mapping.items():
            for source_field in source_fields:
                # Try to find a matching field (case-insensitive)
                value = self._find_field_case_insensitive(balance_sheet, source_field)
                if value is not None:
                    standardized[standard_field] = value
                    break
        
        # Calculate derived metrics if possible
        if "current_assets" not in standardized and all(field in standardized for field in ["cash_and_equivalents", "short_term_investments", "accounts_receivable", "inventory", "other_current_assets"]):
            standardized["current_assets"] = (
                standardized.get("cash_and_equivalents", 0) + 
                standardized.get("short_term_investments", 0) + 
                standardized.get("accounts_receivable", 0) + 
                standardized.get("inventory", 0) + 
                standardized.get("other_current_assets", 0)
            )
        
        if "total_assets" not in standardized and "current_assets" in standardized:
            standardized["total_assets"] = standardized["current_assets"] + sum([
                standardized.get(field, 0) for field in [
                    "long_term_investments", "property_plant_equipment", "goodwill", 
                    "intangible_assets", "other_non_current_assets"
                ]
            ])
        
        if "current_liabilities" not in standardized and all(field in standardized for field in ["accounts_payable", "short_term_debt", "other_current_liabilities"]):
            standardized["current_liabilities"] = (
                standardized.get("accounts_payable", 0) + 
                standardized.get("short_term_debt", 0) + 
                standardized.get("other_current_liabilities", 0)
            )
        
        if "total_liabilities" not in standardized and "current_liabilities" in standardized:
            standardized["total_liabilities"] = standardized["current_liabilities"] + sum([
                standardized.get(field, 0) for field in [
                    "long_term_debt", "deferred_revenue", "deferred_tax_liabilities", 
                    "other_non_current_liabilities"
                ]
            ])
        
        if "total_equity" not in standardized and all(field in standardized for field in ["common_stock", "additional_paid_in_capital", "retained_earnings"]):
            standardized["total_equity"] = (
                standardized.get("common_stock", 0) + 
                standardized.get("additional_paid_in_capital", 0) + 
                standardized.get("retained_earnings", 0) + 
                standardized.get("treasury_stock", 0) + 
                standardized.get("accumulated_other_comprehensive_income", 0)
            )
        
        # Check balance sheet equation: assets = liabilities + equity
        if "total_assets" in standardized and "total_liabilities" in standardized and "total_equity" in standardized:
            # Allow for some rounding error
            if abs(standardized["total_assets"] - (standardized["total_liabilities"] + standardized["total_equity"])) > 1:
                logger.warning("Balance sheet equation doesn't balance")
        
        return standardized
    
    def _standardize_cash_flow(self, cash_flow):
        """
        Standardize a cash flow statement.
        
        Args:
            cash_flow (dict): The cash flow statement.
            
        Returns:
            dict: The standardized cash flow statement.
        """
        # Map of standard fields to possible source fields
        field_mapping = {
            # Operating activities
            "net_income": ["netincome", "netearnings", "profit"],
            "depreciation_amortization": ["depreciationandamortization", "depreciation", "amortization"],
            "deferred_taxes": ["deferredtaxes", "deferredincometaxes"],
            "stock_based_compensation": ["stockbasedcompensation", "sharebasedcompensation"],
            "change_in_working_capital": ["changeinworkingcapital"],
            "accounts_receivable_change": ["changesaccountsreceivable", "accountsreceivablechange"],
            "inventory_change": ["changesinventory", "inventorychange"],
            "accounts_payable_change": ["changesaccountspayable", "accountspayablechange"],
            "other_operating_activities": ["otheroperatingactivities"],
            "net_cash_from_operating_activities": ["netcashfromoperatingactivities", "cashfromoperations", "operatingcashflow"],
            
            # Investing activities
            "capital_expenditures": ["capitalexpenditures", "capex", "purchasesfixedassets"],
            "investments": ["investments", "purchaseinvestments", "saleofinvestments"],
            "acquisitions": ["acquisitions", "acquisitionsbusinesses"],
            "other_investing_activities": ["otherinvestingactivities"],
            "net_cash_from_investing_activities": ["netcashfrominvestingactivities", "cashfrominvesting", "investingcashflow"],
            
            # Financing activities
            "debt_repayment": ["debtrepayment", "repaymentofdebt"],
            "common_stock_issued": ["commonstockissued", "issuanceofcommonstock"],
            "common_stock_repurchased": ["commonstockrepurchased", "repurchaseofcommonstock"],
            "dividends_paid": ["dividendspaid", "cashividends"],
            "other_financing_activities": ["otherfinancingactivities"],
            "net_cash_from_financing_activities": ["netcashfromfinancingactivities", "cashfromfinancing", "financingcashflow"],
            
            # Summary
            "net_change_in_cash": ["netchangeincash", "netincreaseincash", "netdecreaseincash"],
            "cash_at_beginning_of_period": ["cashatbeginningofperiod", "beginningcashposition"],
            "cash_at_end_of_period": ["cashatendofperiod", "endingcashposition"]
        }
        
        # Create standardized statement
        standardized = {}
        
        for standard_field, source_fields in field_mapping.items():
            for source_field in source_fields:
                # Try to find a matching field (case-insensitive)
                value = self._find_field_case_insensitive(cash_flow, source_field)
                if value is not None:
                    standardized[standard_field] = value
                    break
        
        # Calculate derived metrics if possible
        if "net_cash_from_operating_activities" not in standardized and "net_income" in standardized:
            operating_adjustments = sum([
                standardized.get(field, 0) for field in [
                    "depreciation_amortization", "deferred_taxes", "stock_based_compensation", 
                    "change_in_working_capital", "accounts_receivable_change", "inventory_change", 
                    "accounts_payable_change", "other_operating_activities"
                ]
            ])
            standardized["net_cash_from_operating_activities"] = standardized["net_income"] + operating_adjustments
        
        if "free_cash_flow" not in standardized and "net_cash_from_operating_activities" in standardized and "capital_expenditures" in standardized:
            standardized["free_cash_flow"] = standardized["net_cash_from_operating_activities"] - standardized["capital_expenditures"]
        
        if "net_change_in_cash" not in standardized and all(field in standardized for field in ["net_cash_from_operating_activities", "net_cash_from_investing_activities", "net_cash_from_financing_activities"]):
            standardized["net_change_in_cash"] = (
                standardized["net_cash_from_operating_activities"] + 
                standardized["net_cash_from_investing_activities"] + 
                standardized["net_cash_from_financing_activities"]
            )
        
        if "cash_at_end_of_period" not in standardized and "cash_at_beginning_of_period" in standardized and "net_change_in_cash" in standardized:
            standardized["cash_at_end_of_period"] = standardized["cash_at_beginning_of_period"] + standardized["net_change_in_cash"]
        
        return standardized
    
    def _find_field_case_insensitive(self, data, field):
        """
        Find a field in a dictionary case-insensitively.
        
        Args:
            data (dict): The dictionary to search.
            field (str): The field to find.
            
        Returns:
            any: The value if found, None otherwise.
        """
        # Try direct match first
        if field in data:
            return data[field]
        
        # Try case-insensitive match
        field_lower = field.lower()
        for key in data:
            if key.lower() == field_lower:
                return data[key]
        
        # Try removing spaces and special characters
        field_normalized = re.sub(r'[^a-zA-Z0-9]', '', field_lower)
        for key in data:
            key_normalized = re.sub(r'[^a-zA-Z0-9]', '', key.lower())
            if key_normalized == field_normalized:
                return data[key]
        
        return None


    def normalize_financial_data(self, ticker, period_type="annual"):
        """
        Normalize financial data for a ticker by calculating per-share and percentage metrics.
        
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
                sort=[("period_end_date", -1)]
            )
            
            if not financial_statements:
                logger.warning(f"No {period_type} financial statements found for {ticker}")
                return False
            
            # Process each statement
            for statement in financial_statements:
                # Make sure we have standardized statements
                if not all(key in statement for key in ["income_statement_standardized", "balance_sheet_standardized", "cash_flow_statement_standardized"]):
                    logger.warning(f"Missing standardized statements for {ticker} on {statement.get('period_end_date')}")
                    continue
                
                normalized = self._normalize_statements(
                    statement["income_statement_standardized"],
                    statement["balance_sheet_standardized"],
                    statement["cash_flow_statement_standardized"]
                )
                
                # Update the database with normalized metrics
                self.db_ops.update_one(
                    FINANCIAL_STATEMENTS_COLLECTION,
                    {"_id": statement["_id"]},
                    {"$set": {"normalized_metrics": normalized}}
                )
            
            logger.info(f"Normalized {len(financial_statements)} {period_type} financial statements for {ticker}")
            return True
            
        except Exception as e:
            logger.error(f"Error normalizing financial data for {ticker}: {str(e)}")
            return False
    
    def _normalize_statements(self, income_statement, balance_sheet, cash_flow):
        """
        Normalize financial statements by calculating per-share and percentage metrics.
        
        Args:
            income_statement (dict): The standardized income statement.
            balance_sheet (dict): The standardized balance sheet.
            cash_flow (dict): The standardized cash flow statement.
            
        Returns:
            dict: The normalized metrics.
        """
        normalized = {
            "per_share": {},
            "margins": {},
            "growth_rates": {},
            "returns": {},
            "financial_health": {}
        }
        
        # Get number of shares (try diluted first, then basic)
        shares = income_statement.get("shares_outstanding_diluted") or income_statement.get("shares_outstanding_basic")
        
        # Per-share metrics
        if shares:
            for field, value in income_statement.items():
                if isinstance(value, (int, float)) and field not in ["shares_outstanding_basic", "shares_outstanding_diluted", "eps_basic", "eps_diluted"]:
                    normalized["per_share"][f"{field}_per_share"] = value / shares
            
            # Book value per share
            if "total_equity" in balance_sheet:
                normalized["per_share"]["book_value_per_share"] = balance_sheet["total_equity"] / shares
            
            # Cash flow per share
            if "net_cash_from_operating_activities" in cash_flow:
                normalized["per_share"]["operating_cash_flow_per_share"] = cash_flow["net_cash_from_operating_activities"] / shares
            
            if "free_cash_flow" in cash_flow:
                normalized["per_share"]["free_cash_flow_per_share"] = cash_flow["free_cash_flow"] / shares
        
        # Margin metrics
        if "revenue" in income_statement and income_statement["revenue"] > 0:
            revenue = income_statement["revenue"]
            
            for field, value in income_statement.items():
                if isinstance(value, (int, float)) and field not in ["shares_outstanding_basic", "shares_outstanding_diluted", "eps_basic", "eps_diluted", "revenue"]:
                    normalized["margins"][f"{field}_margin"] = value / revenue
        
        # Return metrics
        if "total_assets" in balance_sheet and balance_sheet["total_assets"] > 0:
            # Return on Assets
            if "net_income" in income_statement:
                normalized["returns"]["return_on_assets"] = income_statement["net_income"] / balance_sheet["total_assets"]
        
        if "total_equity" in balance_sheet and balance_sheet["total_equity"] > 0:
            # Return on Equity
            if "net_income" in income_statement:
                normalized["returns"]["return_on_equity"] = income_statement["net_income"] / balance_sheet["total_equity"]
        
        # Financial health metrics
        if "current_assets" in balance_sheet and "current_liabilities" in balance_sheet and balance_sheet["current_liabilities"] > 0:
            # Current ratio
            normalized["financial_health"]["current_ratio"] = balance_sheet["current_assets"] / balance_sheet["current_liabilities"]
            
            # Quick ratio (acid test)
            if "inventory" in balance_sheet:
                normalized["financial_health"]["quick_ratio"] = (balance_sheet["current_assets"] - balance_sheet["inventory"]) / balance_sheet["current_liabilities"]
        
        if "total_liabilities" in balance_sheet and "total_equity" in balance_sheet and balance_sheet["total_equity"] > 0:
            # Debt-to-Equity ratio
            normalized["financial_health"]["debt_to_equity"] = balance_sheet["total_liabilities"] / balance_sheet["total_equity"]
        
        if "total_assets" in balance_sheet and balance_sheet["total_assets"] > 0:
            # Debt ratio
            if "total_liabilities" in balance_sheet:
                normalized["financial_health"]["debt_ratio"] = balance_sheet["total_liabilities"] / balance_sheet["total_assets"]
        
        if "operating_income" in income_statement and "interest_expense" in income_statement and income_statement["interest_expense"] > 0:
            # Interest coverage ratio
            normalized["financial_health"]["interest_coverage"] = income_statement["operating_income"] / income_statement["interest_expense"]
        
        return normalized