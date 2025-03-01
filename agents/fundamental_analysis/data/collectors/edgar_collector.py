import logging
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from config.settings import SEC_API_KEY, SEC_FILING_TYPES, USER_AGENT
from database.operations import db_ops
from database.schema import COMPANIES_COLLECTION, FINANCIAL_STATEMENTS_COLLECTION

logger = logging.getLogger("stock_analyzer.data.collectors.edgar")


class EDGARCollector:
    
    def __init__(self):
        self.db_ops = db_ops
        self.sec_api_key = SEC_API_KEY
        self.headers = {
            "User-Agent": USER_AGENT,
        }
        
        self.cik_lookup_url = "https://www.sec.gov/cgi-bin/browse-edgar?CIK={}&action=getcompany"
        self.company_facts_url = "https://data.sec.gov/api/xbrl/companyfacts/CIK{}.json"
        self.company_concept_url = "https://data.sec.gov/api/xbrl/companyconcept/CIK{}/us-gaap/{}.json"
        self.submissions_url = "https://data.sec.gov/submissions/CIK{}.json"
        
        self.filing_types = SEC_FILING_TYPES
    
    def get_company_cik(self, ticker):
        try:
            ticker = ticker.upper()
            
            company = self.db_ops.find_one(COMPANIES_COLLECTION, {"ticker": ticker})
            if company and "cik" in company:
                return company["cik"]
            
            url = self.cik_lookup_url.format(ticker)
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to get CIK for {ticker}. Status code: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            cik = None
            
            search_results = soup.find_all("a", href=True)
            for link in search_results:
                if "/cgi-bin/browse-edgar" in link["href"] and "CIK=" in link["href"]:
                    cik_part = link["href"].split("CIK=")[1]
                    if "&" in cik_part:
                        cik = cik_part.split("&")[0]
                    else:
                        cik = cik_part
                    break
            
            if not cik:
                for text in soup.stripped_strings:
                    if "CIK#:" in text or "CIK:" in text:
                        if "CIK#:" in text:
                            cik_start = text.find("CIK#:") + 5
                        else:
                            cik_start = text.find("CIK:") + 4
                        
                        cik_text = text[cik_start:].strip()
                        cik = ""
                        for char in cik_text:
                            if char.isdigit():
                                cik += char
                            else:
                                if cik:
                                    break
                        
                        if cik:
                            break
            
            if not cik or not cik.isdigit():
                logger.warning(f"Could not find valid CIK for {ticker}")
                return None
            
            if not company:
                title_tag = soup.find("title")
                if title_tag and " - " in title_tag.text:
                    company_name = title_tag.text.split(" - ")[0].strip()
                else:
                    company_name = ticker
                self.db_ops.insert_one(
                    COMPANIES_COLLECTION,
                    {
                        "ticker": ticker,
                        "name": company_name,
                        "cik": cik,
                        "sector": "Unknown",
                        "industry": "Unknown",
                        "exchange": "Unknown",
                    }
                )
            else:
                self.db_ops.update_one(
                    COMPANIES_COLLECTION,
                    {"ticker": ticker},
                    {"$set": {"cik": cik}}
                )
            
            return cik
            
        except Exception as e:
            logger.error(f"Error getting CIK for {ticker}: {str(e)}")
            return None
    
    def get_company_info(self, ticker):
        try:
            ticker = ticker.upper()
            
            cik = self.get_company_cik(ticker)
            if not cik:
                return None
            
            padded_cik = cik.zfill(10)
            
            url = self.submissions_url.format(padded_cik)
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to get company info for {ticker}. Status code: {response.status_code}")
                return None
            
            company_data = response.json()
            
            company_info = {
                "ticker": ticker,
                "cik": cik,
                "name": company_data.get("name", ""),
                "sic": company_data.get("sic", ""),
                "sicDescription": company_data.get("sicDescription", ""),
                "exchange": company_data.get("exchanges", [""])[0] if company_data.get("exchanges") else "",
                "fiscalYearEnd": company_data.get("fiscalYearEnd", ""),
                "industry": company_data.get("sicDescription", "").split(" - ")[0] if " - " in company_data.get("sicDescription", "") else "",
                "sector": "Unknown",
                "description": "",
                "website": "",
                "executives": []
            }
            
            self.db_ops.update_one(
                COMPANIES_COLLECTION,
                {"ticker": ticker},
                {"$set": company_info},
                upsert=True
            )
            
            return company_info
            
        except Exception as e:
            logger.error(f"Error getting company info for {ticker}: {str(e)}")
            return None
    
    def get_filing_links(self, ticker, filing_type, limit=10):
        try:
            ticker = ticker.upper()
            
            cik = self.get_company_cik(ticker)
            if not cik:
                return []
            
            url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={filing_type}&count={limit}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to get {filing_type} filings for {ticker}. Status code: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, "html.parser")
            filing_table = soup.find("table", {"class": "tableFile2"})
            
            if not filing_table:
                logger.warning(f"No {filing_type} filings found for {ticker}")
                return []
            
            filing_links = []
            rows = filing_table.find_all("tr")
            
            for row in rows[1:]:
                cols = row.find_all("td")
                if len(cols) >= 4:
                    filing_type_col = cols[0].text.strip()
                    filing_date = cols[3].text.strip()
                    
                    if filing_type_col == filing_type:
                        filing_detail_link = cols[1].find("a")["href"]
                        filing_detail_url = f"https://www.sec.gov{filing_detail_link}"
                        
                        filing_links.append({
                            "type": filing_type,
                            "date": filing_date,
                            "url": filing_detail_url
                        })
            
            return filing_links
            
        except Exception as e:
            logger.error(f"Error getting filing links for {ticker}: {str(e)}")
            return []
    
    def get_financial_data(self, ticker, period_type="annual"):
        try:
            ticker = ticker.upper()
            
            cik = self.get_company_cik(ticker)
            if not cik:
                return None
            
            padded_cik = cik.zfill(10)
            
            url = self.company_facts_url.format(padded_cik)
            response = requests.get(url, headers=self.headers)
            
            time.sleep(0.1)
            
            if response.status_code != 200:
                logger.error(f"Failed to get financial data for {ticker}. Status code: {response.status_code}")
                return None
            
            company_facts = response.json()
            
            financial_data = {}
            
            income_statement = {}
            income_items = [
                "Revenue", "CostOfRevenue", "GrossProfit", "OperatingExpenses", 
                "OperatingIncome", "InterestExpense", "IncomeTaxExpense", "NetIncome"
            ]
            
            for item in income_items:
                item_data = self._extract_financial_item(company_facts, item, period_type)
                if item_data:
                    income_statement[item] = item_data
            
            financial_data["income_statement"] = income_statement
            
            balance_sheet = {}
            balance_items = [
                "Assets", "CurrentAssets", "Cash", "Inventory", "AccountsReceivable",
                "Liabilities", "CurrentLiabilities", "AccountsPayable", "LongTermDebt",
                "StockholdersEquity", "CommonStock", "RetainedEarnings"
            ]
            
            for item in balance_items:
                item_data = self._extract_financial_item(company_facts, item, period_type)
                if item_data:
                    balance_sheet[item] = item_data
            
            financial_data["balance_sheet"] = balance_sheet
            
            cash_flow = {}
            cash_flow_items = [
                "OperatingCashFlow", "InvestingCashFlow", "FinancingCashFlow",
                "CapitalExpenditure", "Depreciation", "FreeCashFlow"
            ]
            
            for item in cash_flow_items:
                item_data = self._extract_financial_item(company_facts, item, period_type)
                if item_data:
                    cash_flow[item] = item_data
            
            financial_data["cash_flow_statement"] = cash_flow
            
            periods = set()
            for statement in financial_data.values():
                for item_data in statement.values():
                    for period, _ in item_data.items():
                        periods.add(period)
            
            for period in periods:
                period_date = datetime.strptime(period, "%Y-%m-%d")
                
                period_data = {
                    "ticker": ticker,
                    "period_type": period_type,
                    "period_end_date": period_date,
                    "publication_date": period_date,
                    "source": "SEC EDGAR",
                    "income_statement": {},
                    "balance_sheet": {},
                    "cash_flow_statement": {}
                }
                
                for statement_type, statement_data in financial_data.items():
                    for item, item_data in statement_data.items():
                        if period in item_data:
                            period_data[statement_type][item] = item_data[period]
                
                self.db_ops.update_one(
                    FINANCIAL_STATEMENTS_COLLECTION,
                    {
                        "ticker": ticker,
                        "period_type": period_type,
                        "period_end_date": period_date
                    },
                    {"$set": period_data},
                    upsert=True
                )
            
            return financial_data
            
        except Exception as e:
            logger.error(f"Error getting financial data for {ticker}: {str(e)}")
            return None
    
    def _extract_financial_item(self, company_facts, item, period_type):
        try:
            if "us-gaap" not in company_facts.get("facts", {}):
                return None
            
            us_gaap = company_facts["facts"]["us-gaap"]
            
            possible_items = [
                item, 
                item.lower(), 
                item.upper(),
                item + "s"
            ]
            
            found_item = None
            for candidate in possible_items:
                if candidate in us_gaap:
                    found_item = candidate
                    break
            
            if not found_item:
                return None
            
            item_data = us_gaap[found_item]
            
            units_key = list(item_data["units"].keys())[0]
            units = item_data["units"][units_key]
            
            period_filter = "CY" if period_type == "annual" else "QTD"
            period_data = {}
            
            for entry in units:
                if "frame" in entry and period_filter in entry["frame"]:
                    frame = entry["frame"]
                    year = frame[2:6]
                    
                    if period_type == "annual":
                        date = f"{year}-12-31"
                    else:
                        quarter = frame[-2:]
                        month = {"Q1": "03", "Q2": "06", "Q3": "09", "Q4": "12"}.get(quarter, "12")
                        date = f"{year}-{month}-31"
                    
                    period_data[date] = entry["val"]
            
            return period_data
            
        except Exception as e:
            logger.error(f"Error extracting financial item {item}: {str(e)}")
            return None