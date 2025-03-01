"""
SEC report parser module.
"""

import logging
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd

from config.settings import USER_AGENT

logger = logging.getLogger("stock_analyzer.data.parsers.report")


class SECReportParser:
    """
    Parses SEC reports and extracts relevant information.
    """
    
    def __init__(self):
        """Initialize the SECReportParser."""
        self.headers = {
            "User-Agent": USER_AGENT,
        }
    
    def extract_tables_from_filing(self, filing_url):
        """
        Extract tables from an SEC filing.
        
        Args:
            filing_url (str): The URL of the SEC filing.
            
        Returns:
            list: The extracted tables.
        """
        try:
            logger.info(f"Extracting tables from filing: {filing_url}")
            
            # Get the filing HTML
            response = requests.get(filing_url, headers=self.headers)
            if response.status_code != 200:
                logger.error(f"Failed to get filing. Status code: {response.status_code}")
                return []
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract tables
            tables = []
            table_elements = soup.find_all("table")
            
            for i, table in enumerate(table_elements):
                try:
                    # Parse the table with pandas
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
        """
        Identify financial tables from a list of tables.
        
        Args:
            tables (list): The list of tables.
            filing_type (str): The type of filing.
            
        Returns:
            dict: The identified financial tables.
        """
        try:
            financial_tables = {
                "income_statement": None,
                "balance_sheet": None,
                "cash_flow_statement": None
            }
            
            # Keywords to identify each type of financial statement
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
            
            # Check each table for keywords
            for table in tables:
                df = table["dataframe"]
                table_text = " ".join(str(col).lower() for col in df.columns.tolist())
                table_text += " ".join(str(val).lower() for val in df.values.flatten() if pd.notna(val))
                
                # Check for income statement
                if financial_tables["income_statement"] is None and any(keyword in table_text for keyword in income_statement_keywords):
                    financial_tables["income_statement"] = table
                
                # Check for balance sheet
                if financial_tables["balance_sheet"] is None and any(keyword in table_text for keyword in balance_sheet_keywords):
                    financial_tables["balance_sheet"] = table
                
                # Check for cash flow statement
                if financial_tables["cash_flow_statement"] is None and any(keyword in table_text for keyword in cash_flow_keywords):
                    financial_tables["cash_flow_statement"] = table
            
            # Log the results
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
        """
        Extract data from a financial table.
        
        Args:
            table (dict): The table information.
            statement_type (str): The type of financial statement.
            
        Returns:
            dict: The extracted data.
        """
        try:
            if table is None:
                return {}
            
            df = table["dataframe"]
            
            # Try to standardize the table format
            standardized_df = self._standardize_table_format(df, statement_type)
            
            # Convert the standardized DataFrame to a dictionary
            data = self._dataframe_to_dict(standardized_df, statement_type)
            
            return data
            
        except Exception as e:
            logger.error(f"Error extracting data from {statement_type} table: {str(e)}")
            return {}
    
    def _standardize_table_format(self, df, statement_type):
        """
        Standardize the format of a financial table.
        
        Args:
            df (pandas.DataFrame): The financial table.
            statement_type (str): The type of financial statement.
            
        Returns:
            pandas.DataFrame: The standardized table.
        """
        try:
            # Make a copy to avoid modifying the original
            df = df.copy()
            
            # Drop rows where all values are NaN
            df = df.dropna(how="all")
            
            # Drop columns where all values are NaN
            df = df.dropna(axis=1, how="all")
            
            # Try to identify the structure of the table
            # Common formats:
            # 1. Items in rows, periods in columns
            # 2. Items in columns, periods in rows
            # We want format 1: Items in rows, periods in columns
            
            # Check if we have multiple columns that look like dates
            date_pattern = re.compile(r"\d{4}|\d{2}/\d{2}/\d{4}|\d{2}/\d{2}/\d{2}|Dec|December|Jan|January|Mar|March|Jun|June|Sep|September")
            date_column_count = sum(1 for col in df.columns if isinstance(col, str) and date_pattern.search(col))
            
            # If we have multiple date columns, assume items are in rows
            if date_column_count >= 2:
                # This is the format we want
                return df
            
            # Check if we have dates in the first column
            first_col_values = [str(val).strip() for val in df.iloc[:, 0] if pd.notna(val)]
            date_value_count = sum(1 for val in first_col_values if date_pattern.search(val))
            
            # If first column has dates, transpose the DataFrame
            if date_value_count >= 2:
                # Set the first column as index before transposing
                df.set_index(df.columns[0], inplace=True)
                df = df.transpose()
                return df
            
            # If we can't clearly detect the format, default to the original
            return df
            
        except Exception as e:
            logger.error(f"Error standardizing {statement_type} table: {str(e)}")
            return df
    
    def _dataframe_to_dict(self, df, statement_type):
        """
        Convert a DataFrame to a dictionary.
        
        Args:
            df (pandas.DataFrame): The DataFrame.
            statement_type (str): The type of financial statement.
            
        Returns:
            dict: The dictionary.
        """
        try:
            data = {}
            
            # Try to identify the row containing item labels
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
            
            # If we couldn't identify a label row, use the first row
            if label_row_idx is None:
                label_row_idx = 0
            
            # Get the periods (column headers)
            periods = [col for col in df.columns if col != df.index.name]
            
            # Extract data for each period
            for period in periods:
                period_data = {}
                
                for idx, row in df.iterrows():
                    if idx == label_row_idx:
                        continue
                    
                    # Get the item label and value
                    item_label = self._clean_item_label(row.name if isinstance(row.name, str) else "")
                    value = row[period]
                    
                    # Skip empty values
                    if pd.isna(value) or item_label == "":
                        continue
                    
                    # Convert value to number if possible
                    value = self._convert_to_number(value)
                    
                    # Add to period data
                    period_data[item_label] = value
                
                # Convert period to a standardized format
                period_str = self._standardize_period(period)
                
                # Add to data dictionary
                data[period_str] = period_data
            
            return data
            
        except Exception as e:
            logger.error(f"Error converting {statement_type} DataFrame to dict: {str(e)}")
            return {}
    
    def _clean_item_label(self, label):
        """
        Clean an item label.
        
        Args:
            label (str): The item label.
            
        Returns:
            str: The cleaned label.
        """
        # Remove parentheses and content inside
        label = re.sub(r"\(.*?\)", "", label)
        
        # Remove special characters
        label = re.sub(r"[^\w\s]", "", label)
        
        # Replace multiple spaces with a single space
        label = re.sub(r"\s+", " ", label)
        
        # Convert to camel case
        words = label.strip().split()
        if words:
            label = words[0].lower() + "".join(word.capitalize() for word in words[1:])
        
        return label
    
    def _convert_to_number(self, value):
        """
        Convert a value to a number if possible.
        
        Args:
            value (any): The value to convert.
            
        Returns:
            any: The converted value.
        """
        if pd.isna(value):
            return None
        
        if isinstance(value, (int, float)):
            return value
        
        try:
            # Remove currency symbols, commas, and other non-numeric characters
            value_str = str(value).strip()
            value_str = re.sub(r"[^\d\.\-]", "", value_str)
            
            # Handle empty string
            if value_str == "" or value_str == ".":
                return None
            
            # Convert to number
            return float(value_str)
        except (ValueError, TypeError):
            return value
    
    def _standardize_period(self, period):
        """
        Standardize a period string.
        
        Args:
            period (any): The period.
            
        Returns:
            str: The standardized period string.
        """
        if pd.isna(period):
            return "Unknown"
        
        period_str = str(period).strip()
        
        # Try to parse as a date
        date_formats = [
            "%Y", "%y",  # Year only
            "%b %Y", "%B %Y",  # Month and year
            "%m/%d/%Y", "%m/%d/%y",  # MM/DD/YYYY or MM/DD/YY
            "%Y-%m-%d"  # ISO format
        ]
        
        for date_format in date_formats:
            try:
                date = pd.to_datetime(period_str, format=date_format)
                return date.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                continue
        
        # Handle quarters
        quarter_pattern = re.compile(r"Q(\d)\s*(\d{4})")
        match = quarter_pattern.search(period_str)
        if match:
            quarter, year = match.groups()
            month = (int(quarter) * 3)
            return f"{year}-{month:02d}-01"
        
        # If we can't parse as a date, return as is
        return period_str
    
    def extract_management_discussion(self, filing_url):
        """
        Extract management discussion and analysis from an SEC filing.
        
        Args:
            filing_url (str): The URL of the SEC filing.
            
        Returns:
            str: The extracted management discussion.
        """
        try:
            logger.info(f"Extracting management discussion from filing: {filing_url}")
            
            # Get the filing HTML
            response = requests.get(filing_url, headers=self.headers)
            if response.status_code != 200:
                logger.error(f"Failed to get filing. Status code: {response.status_code}")
                return ""
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Look for the "Management's Discussion and Analysis" section
            mda_section = None
            
            # Common section headings for MD&A
            mda_headings = [
                "ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS",
                "ITEM 7. MANAGEMENT'S DISCUSSION",
                "MANAGEMENT'S DISCUSSION AND ANALYSIS",
                "MANAGEMENT DISCUSSION AND ANALYSIS",
                "MANAGEMENT'S DISCUSSION & ANALYSIS",
                "MD&A"
            ]
            
            for heading in mda_headings:
                # Look for headings
                heading_tags = soup.find_all(["h1", "h2", "h3", "h4", "h5", "p", "div"], string=lambda s: s and heading.lower() in s.lower())
                
                if heading_tags:
                    mda_section = heading_tags[0]
                    break
            
            if not mda_section:
                logger.warning("Could not find Management's Discussion and Analysis section")
                return ""
            
            # Extract the content of the MD&A section
            mda_content = []
            current = mda_section.next_sibling
            
            # Look for the next section heading (ITEM 7A or ITEM 8 typically)
            end_headings = ["ITEM 7A", "ITEM 8", "ITEM 9"]
            
            while current:
                # Check if we've reached the next section
                if isinstance(current, (str)):
                    text = current.strip()
                else:
                    text = current.get_text().strip()
                
                if any(end_heading.lower() in text.lower() for end_heading in end_headings):
                    break
                
                # Add content if it's not empty
                if text:
                    mda_content.append(text)
                
                current = current.next_sibling
            
            # Combine the content
            mda_text = "\n".join(mda_content)
            
            # Clean up the text
            mda_text = re.sub(r"\s+", " ", mda_text)
            
            return mda_text
            
        except Exception as e:
            logger.error(f"Error extracting management discussion: {str(e)}")
            return ""
    
    def extract_risk_factors(self, filing_url):
        """
        Extract risk factors from an SEC filing.
        
        Args:
            filing_url (str): The URL of the SEC filing.
            
        Returns:
            list: The extracted risk factors.
        """
        try:
            logger.info(f"Extracting risk factors from filing: {filing_url}")
            
            # Get the filing HTML
            response = requests.get(filing_url, headers=self.headers)
            if response.status_code != 200:
                logger.error(f"Failed to get filing. Status code: {response.status_code}")
                return []
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Look for the "Risk Factors" section
            risk_section = None
            
            # Common section headings for Risk Factors
            risk_headings = [
                "ITEM 1A. RISK FACTORS",
                "ITEM 1A. RISK FACTOR",
                "RISK FACTORS",
                "RISK FACTOR"
            ]
            
            for heading in risk_headings:
                # Look for headings
                heading_tags = soup.find_all(["h1", "h2", "h3", "h4", "h5", "p", "div"], string=lambda s: s and heading.lower() in s.lower())
                
                if heading_tags:
                    risk_section = heading_tags[0]
                    break
            
            if not risk_section:
                logger.warning("Could not find Risk Factors section")
                return []
            
            # Extract the content of the Risk Factors section
            risk_content = []
            current = risk_section.next_sibling
            
            # Look for the next section heading (ITEM 1B or ITEM 2 typically)
            end_headings = ["ITEM 1B", "ITEM 2", "ITEM 3"]
            
            # Try to find individual risk factors (often in bold or as headings)
            risk_factors = []
            in_risk_section = True
            
            while current and in_risk_section:
                # Check if we've reached the next section
                if isinstance(current, (str)):
                    text = current.strip()
                else:
                    text = current.get_text().strip()
                
                if any(end_heading.lower() in text.lower() for end_heading in end_headings):
                    in_risk_section = False
                    break
                
                # Look for potential risk factor headings
                if isinstance(current, (str)):
                    pass  # Skip plain strings
                else:
                    # Check for bold text, headings, or strong tags
                    risk_heading_tags = current.find_all(["b", "strong", "h3", "h4", "h5", "h6"])
                    
                    for tag in risk_heading_tags:
                        heading_text = tag.get_text().strip()
                        
                        # Skip if it's too short or not a proper heading
                        if len(heading_text) < 10 or heading_text.lower() in ["risk factors", "item 1a", "item 1a."]:
                            continue
                        
                        # Skip if it's all uppercase (likely a section heading)
                        if heading_text.isupper() and len(heading_text) > 15:
                            continue
                        
                        # Get the following paragraph(s) as the risk factor content
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
            
            # If we couldn't find individual risk factors, return the entire section
            if not risk_factors and risk_content:
                risk_text = " ".join(risk_content)
                # Try to split by line breaks or periods
                risk_factors = [{"heading": "Risk Factors", "content": risk_text}]
            
            return risk_factors
            
        except Exception as e:
            logger.error(f"Error extracting risk factors: {str(e)}")
            return []