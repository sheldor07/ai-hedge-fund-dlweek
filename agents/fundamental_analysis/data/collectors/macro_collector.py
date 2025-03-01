import logging
from datetime import datetime, timedelta
import pandas as pd
from fredapi import Fred

from config.settings import FRED_API_KEY
from database.operations import db_ops

logger = logging.getLogger("stock_analyzer.data.collectors.macro")


class MacroCollector:
    
    def __init__(self):
        self.db_ops = db_ops
        self.fred_api_key = FRED_API_KEY
        
        self.fred = None
        if self.fred_api_key:
            self.fred = Fred(api_key=self.fred_api_key)
        
        self.collection_name = "macro_indicators"
        
        self.indicators = {
            "GDP": "GDP",
            "UNRATE": "UNRATE",
            "CPIAUCSL": "CPIAUCSL",
            "FEDFUNDS": "FEDFUNDS",
            "M2SL": "M2SL",
            "INDPRO": "INDPRO",
            "HOUST": "HOUST",
            "T10Y2Y": "T10Y2Y",
            "DCOILWTICO": "DCOILWTICO",
            "VIXCLS": "VIXCLS",
        }
    
    def collect_macro_data(self, force_update=False):
        try:
            if not self.fred:
                logger.error("FRED API key is not available")
                return False
            
            if not force_update:
                latest_data = self.db_ops.find_one(
                    self.collection_name,
                    {},
                    {"sort": [("date", -1)]}
                )
                
                if latest_data and (datetime.utcnow() - latest_data["date"]).days < 7:
                    logger.info("Recent macroeconomic data already exists, skipping collection")
                    return True
            
            all_successful = True
            for indicator_id, series_id in self.indicators.items():
                success = self._collect_indicator(indicator_id, series_id)
                if not success:
                    all_successful = False
            
            return all_successful
            
        except Exception as e:
            logger.error(f"Error collecting macroeconomic data: {str(e)}")
            return False
    
    def _collect_indicator(self, indicator_id, series_id):
        try:
            logger.info(f"Collecting data for indicator: {indicator_id} (Series: {series_id})")
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365 * 10)
            
            series = self.fred.get_series(
                series_id,
                observation_start=start_date.strftime("%Y-%m-%d"),
                observation_end=end_date.strftime("%Y-%m-%d")
            )
            
            if series.empty:
                logger.warning(f"No data available for indicator {indicator_id}")
                return False
            
            df = pd.DataFrame(series)
            df.reset_index(inplace=True)
            df.columns = ["date", "value"]
            
            records = df.to_dict("records")
            
            series_info = self.fred.get_series_info(series_id)
            
            for record in records:
                macro_record = {
                    "indicator_id": indicator_id,
                    "series_id": series_id,
                    "date": record["date"],
                    "value": float(record["value"]) if pd.notnull(record["value"]) else None,
                    "title": series_info.title,
                    "units": series_info.units,
                    "frequency": series_info.frequency,
                    "seasonal_adjustment": series_info.seasonal_adjustment,
                    "last_updated": datetime.utcnow()
                }
                
                self.db_ops.update_one(
                    self.collection_name,
                    {
                        "indicator_id": indicator_id,
                        "date": record["date"]
                    },
                    {"$set": macro_record},
                    upsert=True
                )
            
            logger.info(f"Successfully collected {len(records)} data points for indicator {indicator_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error collecting data for indicator {indicator_id}: {str(e)}")
            return False
    
    def get_indicator_data(self, indicator_id, start_date=None, end_date=None):
        try:
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(days=365)
            
            query = {
                "indicator_id": indicator_id,
                "date": {"$gte": start_date, "$lte": end_date}
            }
            
            data = self.db_ops.find_many(
                self.collection_name,
                query,
                sort=[("date", 1)]
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting data for indicator {indicator_id}: {str(e)}")
            return []
    
    def get_latest_indicators(self):
        try:
            latest_indicators = {}
            
            for indicator_id in self.indicators.keys():
                latest_data = self.db_ops.find_one(
                    self.collection_name,
                    {"indicator_id": indicator_id},
                    {"sort": [("date", -1)]}
                )
                
                if latest_data:
                    latest_indicators[indicator_id] = {
                        "value": latest_data["value"],
                        "date": latest_data["date"],
                        "title": latest_data.get("title", indicator_id),
                        "units": latest_data.get("units", "")
                    }
            
            return latest_indicators
            
        except Exception as e:
            logger.error(f"Error getting latest indicators: {str(e)}")
            return {}