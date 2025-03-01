import logging
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd

from config.settings import USER_AGENT

logger = logging.getLogger("stock_analyzer.data.parsers.report")


class SECReportParser:
    
    def __init__(self):
        self.headers = {
            "User-Agent": USER_AGENT,
        }
    
    def extract_tables_from_filing(self, filing_url):
        try:
            logger.info(f"Extracting tables from filing: {filing_url}")
            
            response = requests.get(filing_url, headers=self.headers)
            if response.status_code != 200:
                logger.error(f"Failed to get filing. Status code: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            tables = []
            table_elements = soup.find_all("table")
            
            for i, table in enumerate(table_elements):
                try:
                    table_html = str(table)
                    dfs = pd.read_html(table_html)
                    
                    if dfs:
                        tables.append({
                            "index": i,
                            "dataframe": dfs[0],
                            "html": table_html
                        })
                except Exception as e:
                    logger.warning(f"Error parsing table {i}: {str(e)}")
            
            logger.info(f"Extracted {len(tables)} tables from filing")
            return tables
            
        except Exception as e:
            logger.error(f"Error extracting tables from filing: {str(e)}")
            return []
    
    def identify_financial_tables(self, tables, filing_type):
        try:
            financial_tables = {
                "income_statement": None,
                "balance_sheet": None,
                "cash_flow_statement": None
            }
            
            income_statement_keywords = [
                "statement of operations", "income statement", "consolidated statement of operations",
                "consolidated income statement", "operations", "statement of earnings", "consolidated statement of earnings",
                "statement of income", "consolidated statement of income", "results of operations",
                "revenues", "sales", "net revenue", "net sales", "total revenue", "total sales",
                "cost of revenue", "cost of sales", "gross profit", "operating income", "net income"
            ]
            
            balance_sheet_keywords = [
                "balance sheet", "consolidated balance sheet", "statement of financial position",
                "consolidated statement of financial position", "financial position",
                "assets", "liabilities", "equity", "current assets", "current liabilities",
                "total assets", "total liabilities", "stockholders' equity", "shareholders' equity"
            ]
            
            cash_flow_keywords = [
                "statement of cash flows", "consolidated statement of cash flows", "cash flows",
                "cash flow statement", "consolidated cash flow statement",
                "operating activities", "investing activities", "financing activities",
                "net cash provided by operating activities", "net cash used in investing activities"
            ]
            
            for table in tables:
                df = table["dataframe"]
                table_text = " ".join(str(col).lower() for col in df.columns.tolist())
                table_text += " ".join(str(val).lower() for val in df.values.flatten() if pd.notna(val))
                
                if financial_tables["income_statement"] is None and any(keyword in table_text for keyword in income_statement_keywords):
                    financial_tables["income_statement"] = table
                
                if financial_tables["balance_sheet"] is None and any(keyword in table_text for keyword in balance_sheet_keywords):
                    financial_tables["balance_sheet"] = table
                
                if financial_tables["cash_flow_statement"] is None and any(keyword in table_text for keyword in cash_flow_keywords):
                    financial_tables["cash_flow_statement"] = table
            
            for statement_type, table in financial_tables.items():
                if table:
                    logger.info(f"Identified {statement_type} table (index: {table['index']})")
                else:
                    logger.warning(f"Could not identify {statement_type} table")
            
            return financial_tables
            
        except Exception as e:
            logger.error(f"Error identifying financial tables: {str(e)}")
            return financial_tables
    
    def extract_table_data(self, table, statement_type):
        try:
            if table is None:
                return {}
            
            df = table["dataframe"]
            
            standardized_df = self._standardize_table_format(df, statement_type)
            
            data = self._dataframe_to_dict(standardized_df, statement_type)
            
            return data
            
        except Exception as e:
            logger.error(f"Error extracting data from {statement_type} table: {str(e)}")
            return {}
    
    def _standardize_table_format(self, df, statement_type):
        try:
            df = df.copy()
            
            df = df.dropna(how="all")
            
            df = df.dropna(axis=1, how="all")
            
            date_pattern = re.compile(r"\d{4}|\d{2}/\d{2}/\d{4}|\d{2}/\d{2}/\d{2}|Dec|December|Jan|January|Mar|March|Jun|June|Sep|September")
            date_column_count = sum(1 for col in df.columns if isinstance(col, str) and date_pattern.search(col))
            
            if date_column_count >= 2:
                return df
            
            first_col_values = [str(val).strip() for val in df.iloc[:, 0] if pd.notna(val)]
            date_value_count = sum(1 for val in first_col_values if date_pattern.search(val))
            
            if date_value_count >= 2:
                df.set_index(df.columns[0], inplace=True)
                df = df.transpose()
                return df
            
            return df
            
        except Exception as e:
            logger.error(f"Error standardizing {statement_type} table: {str(e)}")
            return df
    
    def _dataframe_to_dict(self, df, statement_type):
        try:
            data = {}
            
            label_row_idx = None
            for i, row in df.iterrows():
                row_str = " ".join(str(val).lower() for val in row if pd.notna(val))
                
                if statement_type == "income_statement" and any(keyword in row_str for keyword in ["revenue", "sales", "income"]):
                    label_row_idx = i
                    break
                elif statement_type == "balance_sheet" and any(keyword in row_str for keyword in ["assets", "liabilities", "equity"]):
                    label_row_idx = i
                    break
                elif statement_type == "cash_flow_statement" and any(keyword in row_str for keyword in ["operating", "investing", "financing"]):
                    label_row_idx = i
                    break
            
            if label_row_idx is None:
                label_row_idx = 0
            
            periods = [col for col in df.columns if col != df.index.name]
            
            for period in periods:
                period_data = {}
                
                for idx, row in df.iterrows():
                    if idx == label_row_idx:
                        continue
                    
                    item_label = self._clean_item_label(row.name if isinstance(row.name, str) else "")
                    value = row[period]
                    
                    if pd.isna(value) or item_label == "":
                        continue
                    
                    value = self._convert_to_number(value)
                    
                    period_data[item_label] = value
                
                period_str = self._standardize_period(period)
                
                data[period_str] = period_data
            
            return data
            
        except Exception as e:
            logger.error(f"Error converting {statement_type} DataFrame to dict: {str(e)}")
            return {}
    
    def _clean_item_label(self, label):
        label = re.sub(r"\(.*?\)", "", label)
        
        label = re.sub(r"[^\w\s]", "", label)
        
        label = re.sub(r"\s+", " ", label)
        
        words = label.strip().split()
        if words:
            label = words[0].lower() + "".join(word.capitalize() for word in words[1:])
        
        return label
    
    def _convert_to_number(self, value):
        if pd.isna(value):
            return None
        
        if isinstance(value, (int, float)):
            return value
        
        try:
            value_str = str(value).strip()
            value_str = re.sub(r"[^\d\.\-]", "", value_str)
            
            if value_str == "" or value_str == ".":
                return None
            
            return float(value_str)
        except (ValueError, TypeError):
            return value
    
    def _standardize_period(self, period):
        if pd.isna(period):
            return "Unknown"
        
        period_str = str(period).strip()
        
        date_formats = [
            "%Y", "%y",  
            "%b %Y", "%B %Y",  
            "%m/%d/%Y", "%m/%d/%y",  
            "%Y-%m-%d"  
        ]
        
        for date_format in date_formats:
            try:
                date = pd.to_datetime(period_str, format=date_format)
                return date.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                continue
        
        quarter_pattern = re.compile(r"Q(\d)\s*(\d{4})")
        match = quarter_pattern.search(period_str)
        if match:
            quarter, year = match.groups()
            month = (int(quarter) * 3)
            return f"{year}-{month:02d}-01"
        
        return period_str
    
    def extract_management_discussion(self, filing_url):
        try:
            logger.info(f"Extracting management discussion from filing: {filing_url}")
            
            response = requests.get(filing_url, headers=self.headers)
            if response.status_code != 200:
                logger.error(f"Failed to get filing. Status code: {response.status_code}")
                return ""
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            mda_section = None
            
            mda_headings = [
                "ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS",
                "ITEM 7. MANAGEMENT'S DISCUSSION",
                "MANAGEMENT'S DISCUSSION AND ANALYSIS",
                "MANAGEMENT DISCUSSION AND ANALYSIS",
                "MANAGEMENT'S DISCUSSION & ANALYSIS",
                "MD&A"
            ]
            
            for heading in mda_headings:
                heading_tags = soup.find_all(["h1", "h2", "h3", "h4", "h5", "p", "div"], string=lambda s: s and heading.lower() in s.lower())
                
                if heading_tags:
                    mda_section = heading_tags[0]
                    break
            
            if not mda_section:
                logger.warning("Could not find Management's Discussion and Analysis section")
                return ""
            
            mda_content = []
            current = mda_section.next_sibling
            
            end_headings = ["ITEM 7A", "ITEM 8", "ITEM 9"]
            
            while current:
                if isinstance(current, (str)):
                    text = current.strip()
                else:
                    text = current.get_text().strip()
                
                if any(end_heading.lower() in text.lower() for end_heading in end_headings):
                    break
                
                if text:
                    mda_content.append(text)
                
                current = current.next_sibling
            
            mda_text = "\n".join(mda_content)
            
            mda_text = re.sub(r"\s+", " ", mda_text)
            
            return mda_text
            
        except Exception as e:
            logger.error(f"Error extracting management discussion: {str(e)}")
            return ""
    
    def extract_risk_factors(self, filing_url):
        try:
            logger.info(f"Extracting risk factors from filing: {filing_url}")
            
            response = requests.get(filing_url, headers=self.headers)
            if response.status_code != 200:
                logger.error(f"Failed to get filing. Status code: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            risk_section = None
            
            risk_headings = [
                "ITEM 1A. RISK FACTORS",
                "ITEM 1A. RISK FACTOR",
                "RISK FACTORS",
                "RISK FACTOR"
            ]
            
            for heading in risk_headings:
                heading_tags = soup.find_all(["h1", "h2", "h3", "h4", "h5", "p", "div"], string=lambda s: s and heading.lower() in s.lower())
                
                if heading_tags:
                    risk_section = heading_tags[0]
                    break
            
            if not risk_section:
                logger.warning("Could not find Risk Factors section")
                return []
            
            risk_content = []
            current = risk_section.next_sibling
            
            end_headings = ["ITEM 1B", "ITEM 2", "ITEM 3"]
            
            risk_factors = []
            in_risk_section = True
            
            while current and in_risk_section:
                if isinstance(current, (str)):
                    text = current.strip()
                else:
                    text = current.get_text().strip()
                
                if any(end_heading.lower() in text.lower() for end_heading in end_headings):
                    in_risk_section = False
                    break
                
                risk_heading_tags = current.find_all(["b", "strong", "h3", "h4", "h5", "h6"])
                
                for tag in risk_heading_tags:
                    heading_text = tag.get_text().strip()
                    
                    if len(heading_text) < 10 or heading_text.lower() in ["risk factors", "item 1a", "item 1a."]:
                        continue
                    
                    if heading_text.isupper() and len(heading_text) > 15:
                        continue
                    
                    content = []
                    next_tag = tag.parent.next_sibling
                    
                    while next_tag and not next_tag.find(["b", "strong", "h3", "h4", "h5", "h6"]):
                        if isinstance(next_tag, (str)):
                            text = next_tag.strip()
                        else:
                            text = next_tag.get_text().strip()
                        
                        if text:
                            content.append(text)
                        
                        next_tag = next_tag.next_sibling
                    
                    risk_factor = {
                        "heading": heading_text,
                        "content": " ".join(content)
                    }
                    
                    risk_factors.append(risk_factor)
                
                current = current.next_sibling
            
            if not risk_factors and risk_content:
                risk_text = " ".join(risk_content)
                risk_factors = [{"heading": "Risk Factors", "content": risk_text}]
            
            return risk_factors
            
        except Exception as e:
            logger.error(f"Error extracting risk factors: {str(e)}")
            return []