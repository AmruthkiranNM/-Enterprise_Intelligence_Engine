import logging
import os
import feedparser
from typing import List, Dict, Any
from datetime import datetime
import time

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://www.business-standard.com/rss/companies-101.rss",
    "https://feeds.bloomberg.com/business/news.rss", # Note: Bloomberg RSS is often restricted, but good for structure
]

class NewsIngestor:
    """Ingests news from Tavily and RSS feeds."""
    
    def __init__(self, tavily_api_key: str = None):
        self.tavily_api_key = tavily_api_key or os.environ.get("TAVILY_API_KEY")
        if not self.tavily_api_key:
            logger.warning("TAVILY_API_KEY not set - general news search will be limited.")

    def fetch_company_news(self, company_name: str, domain: str) -> List[Dict[str, Any]]:
        """Fetch news for a specific company using Tavily."""
        articles = []
        if not self.tavily_api_key:
            return articles

        try:
            from company_discovery.search import search_web
            # Construct a strategic query
            query = f'"{company_name}" (funding OR IPO OR acquisition OR layoff OR "new CEO" OR "new CTO" OR "partnership") after:2025-01-01'
            results = search_web(query)
            
            if isinstance(results, list):
                for res in results:
                    articles.append({
                        "company": company_name,
                        "headline": res.get("title", "No Title"),
                        "source": res.get("source", domain),
                        "url": res.get("url", ""),
                        "published_at": datetime.utcnow(), # Tavily doesn't always return dates in a standard way
                        "raw_content": res.get("snippet", "") + " " + res.get("body", "")
                    })
        except Exception as e:
            logger.error(f"Error fetching news from Tavily for {company_name}: {e}")
            
        return articles

    def fetch_rss_news(self) -> List[Dict[str, Any]]:
        """Fetch news from predefined RSS feeds."""
        articles = []
        for feed_url in RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    articles.append({
                        "company": None, # Will be matched by detection engine
                        "headline": entry.title,
                        "source": feed.feed.get("title", feed_url),
                        "url": entry.link,
                        "published_at": datetime.fromtimestamp(time.mktime(entry.published_parsed)) if hasattr(entry, 'published_parsed') else datetime.utcnow(),
                        "raw_content": entry.get("summary", "") + " " + entry.get("description", "")
                    })
            except Exception as e:
                logger.error(f"Error fetching RSS feed {feed_url}: {e}")
        
        return articles
