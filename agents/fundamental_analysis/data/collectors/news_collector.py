"""
News and sentiment data collector.
"""

import logging
from datetime import datetime, timedelta
import requests
from newsapi import NewsApiClient
from textblob import TextBlob

from config.settings import NEWS_API_KEY
from database.operations import db_ops
from database.schema import NEWS_SENTIMENT_COLLECTION

logger = logging.getLogger("stock_analyzer.data.collectors.news")


class NewsCollector:
    """
    Collects news articles and performs sentiment analysis.
    """
    
    def __init__(self):
        """Initialize the NewsCollector."""
        self.db_ops = db_ops
        self.api_key = NEWS_API_KEY
        
        # Initialize the News API client if API key is available
        self.news_api = None
        if self.api_key:
            self.news_api = NewsApiClient(api_key=self.api_key)
    
    def collect_news(self, ticker, days=7, force_update=False):
        """
        Collect news articles for a ticker.
        
        Args:
            ticker (str): The stock ticker symbol.
            days (int, optional): Number of days of news to collect. Defaults to 7.
            force_update (bool, optional): Whether to force an update even if recent data exists. Defaults to False.
            
        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        try:
            ticker = ticker.upper()
            
            if not self.news_api:
                logger.error("News API key is not available")
                return False
            
            # Check if we already have recent news for this ticker
            if not force_update:
                latest_news = self.db_ops.find_one(
                    NEWS_SENTIMENT_COLLECTION,
                    {"ticker": ticker},
                    {"sort": [("date", -1)]}
                )
                
                if latest_news and (datetime.utcnow() - latest_news["date"]).days < 1:
                    logger.info(f"Recent news already exists for {ticker}, skipping collection")
                    return True
            
            # Calculate the date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Format dates for News API
            from_date = start_date.strftime("%Y-%m-%d")
            to_date = end_date.strftime("%Y-%m-%d")
            
            logger.info(f"Collecting news for {ticker} from {from_date} to {to_date}")
            
            # Query for company name and ticker
            company = self.db_ops.find_one(
                "companies",
                {"ticker": ticker},
                {"name": 1, "_id": 0}
            )
            
            company_name = company.get("name", ticker) if company else ticker
            
            # Get news from News API
            news = self.news_api.get_everything(
                q=f'"{ticker}" OR "{company_name}"',
                from_param=from_date,
                to=to_date,
                language="en",
                sort_by="relevancy",
                page_size=100
            )
            
            if news["status"] != "ok" or "articles" not in news:
                logger.error(f"Failed to get news for {ticker}: {news.get('message', 'Unknown error')}")
                return False
            
            articles = news["articles"]
            
            if not articles:
                logger.warning(f"No news articles found for {ticker}")
                return True
            
            logger.info(f"Found {len(articles)} news articles for {ticker}")
            
            # Process each article
            news_records = []
            for article in articles:
                # Perform sentiment analysis
                sentiment = self._analyze_sentiment(article["title"] + " " + (article["description"] or ""))
                
                # Calculate impact score (a simple heuristic based on source and sentiment)
                source = article["source"]["name"]
                source_credibility = self._get_source_credibility(source)
                impact_score = abs(sentiment["sentiment_score"]) * source_credibility
                
                # Create news record
                news_record = {
                    "ticker": ticker,
                    "date": datetime.strptime(article["publishedAt"][:19], "%Y-%m-%dT%H:%M:%S"),
                    "source": source,
                    "title": article["title"],
                    "content": article["description"] or "",
                    "url": article["url"],
                    "sentiment_score": sentiment["sentiment_score"],
                    "impact_score": impact_score,
                    "source_credibility": source_credibility
                }
                
                news_records.append(news_record)
            
            # Store news records in MongoDB
            if news_records:
                inserted_ids = self.db_ops.insert_many(NEWS_SENTIMENT_COLLECTION, news_records)
                logger.info(f"Inserted {len(inserted_ids)} news records for {ticker}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error collecting news for {ticker}: {str(e)}")
            return False
    
    def _analyze_sentiment(self, text):
        """
        Analyze sentiment of a text.
        
        Args:
            text (str): The text to analyze.
            
        Returns:
            dict: Sentiment analysis results.
        """
        try:
            if not text:
                return {"sentiment_score": 0, "sentiment_label": "neutral"}
            
            # Use TextBlob for sentiment analysis
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            # Determine sentiment label
            if polarity > 0.1:
                label = "positive"
            elif polarity < -0.1:
                label = "negative"
            else:
                label = "neutral"
            
            return {
                "sentiment_score": polarity,
                "sentiment_label": label
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {"sentiment_score": 0, "sentiment_label": "neutral"}
    
    def _get_source_credibility(self, source):
        """
        Get the credibility score for a news source.
        
        Args:
            source (str): The news source.
            
        Returns:
            float: The credibility score (0.0 to 1.0).
        """
        # This is a simple heuristic; in a real system, you'd have a more sophisticated model
        high_credibility_sources = [
            "Bloomberg", "Reuters", "Financial Times", "Wall Street Journal", 
            "CNBC", "The Economist", "Forbes", "Business Insider", "MarketWatch"
        ]
        
        medium_credibility_sources = [
            "Yahoo Finance", "Seeking Alpha", "Motley Fool", "Investopedia", 
            "Barron's", "CNN Business", "NASDAQ", "TheStreet"
        ]
        
        source_lower = source.lower()
        
        for high_source in high_credibility_sources:
            if high_source.lower() in source_lower:
                return 0.9  # High credibility
        
        for medium_source in medium_credibility_sources:
            if medium_source.lower() in source_lower:
                return 0.7  # Medium credibility
        
        return 0.5  # Default moderate credibility
    
    def get_sentiment_summary(self, ticker, days=30):
        """
        Get a summary of sentiment for a ticker over a period.
        
        Args:
            ticker (str): The stock ticker symbol.
            days (int, optional): Number of days to analyze. Defaults to 30.
            
        Returns:
            dict: Sentiment summary.
        """
        try:
            ticker = ticker.upper()
            
            # Calculate the date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get news from MongoDB
            news = self.db_ops.find_many(
                NEWS_SENTIMENT_COLLECTION,
                {
                    "ticker": ticker,
                    "date": {"$gte": start_date, "$lte": end_date}
                }
            )
            
            if not news:
                logger.warning(f"No news found for {ticker} in the last {days} days")
                return {
                    "ticker": ticker,
                    "period_days": days,
                    "article_count": 0,
                    "average_sentiment": 0,
                    "sentiment_trend": "neutral",
                    "high_impact_articles": []
                }
            
            # Calculate average sentiment
            total_sentiment = sum(article["sentiment_score"] for article in news)
            average_sentiment = total_sentiment / len(news)
            
            # Determine sentiment trend
            if average_sentiment > 0.1:
                sentiment_trend = "positive"
            elif average_sentiment < -0.1:
                sentiment_trend = "negative"
            else:
                sentiment_trend = "neutral"
            
            # Get high impact articles
            high_impact_articles = sorted(
                news, 
                key=lambda x: abs(x["impact_score"]), 
                reverse=True
            )[:5]
            
            # Simplify high impact articles for summary
            high_impact_summary = []
            for article in high_impact_articles:
                high_impact_summary.append({
                    "date": article["date"],
                    "title": article["title"],
                    "source": article["source"],
                    "sentiment_score": article["sentiment_score"],
                    "impact_score": article["impact_score"],
                    "url": article["url"]
                })
            
            return {
                "ticker": ticker,
                "period_days": days,
                "article_count": len(news),
                "average_sentiment": average_sentiment,
                "sentiment_trend": sentiment_trend,
                "high_impact_articles": high_impact_summary
            }
            
        except Exception as e:
            logger.error(f"Error getting sentiment summary for {ticker}: {str(e)}")
            return None