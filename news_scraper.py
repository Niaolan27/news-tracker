
import feedparser
import requests
from datetime import datetime
import time
from typing import List, Dict
import logging
from news_database import NewsDatabase, NewsArticle

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsScraper:
    def __init__(self, db: NewsDatabase):
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Popular RSS feeds - you can customize this list
        self.rss_feeds = {
            'BBC News': 'http://feeds.bbci.co.uk/news/rss.xml',
            'Reuters': 'https://ir.thomsonreuters.com/rss/events.xml',
            'CNN': 'http://rss.cnn.com/rss/edition.rss',
            'TechCrunch': 'https://techcrunch.com/feed/',
            'Hacker News': 'https://hnrss.org/frontpage',
            'NPR': 'https://feeds.npr.org/1001/rss.xml',
            'The Guardian': 'https://www.theguardian.com/world/rss'
        }
    
    def parse_date(self, date_string: str) -> datetime:
        """Parse various date formats commonly found in RSS feeds"""
        if not date_string:
            return datetime.now()
        
        # Try different date formats
        date_formats = [
            '%a, %d %b %Y %H:%M:%S %z',  # RFC 2822
            '%a, %d %b %Y %H:%M:%S %Z',  # RFC 2822 with timezone name
            '%Y-%m-%dT%H:%M:%S%z',       # ISO 8601
            '%Y-%m-%dT%H:%M:%SZ',        # ISO 8601 UTC
            '%Y-%m-%d %H:%M:%S',         # Simple format
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        # If all else fails, use current time
        logger.warning(f"Could not parse date: {date_string}")
        return datetime.now()
    
    def scrape_feed(self, feed_name: str, feed_url: str) -> List[NewsArticle]:
        """Scrape a single RSS feed and return list of articles"""
        articles = []
        
        try:
            logger.info(f"Scraping {feed_name}...")
            
            # Parse the RSS feed
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                logger.warning(f"Feed {feed_name} has parsing issues: {feed.bozo_exception}")
            
            # Extract articles from feed entries
            for entry in feed.entries:
                try:
                    # Extract article data
                    title = entry.get('title', 'No Title')
                    url = entry.get('link', '')
                    description = entry.get('summary', entry.get('description', ''))
                    
                    # Parse publication date
                    pub_date = None
                    if hasattr(entry, 'published'):
                        pub_date = self.parse_date(entry.published)
                    elif hasattr(entry, 'updated'):
                        pub_date = self.parse_date(entry.updated)
                    else:
                        pub_date = datetime.now()
                    
                    # Determine category from tags if available
                    category = None
                    if hasattr(entry, 'tags') and entry.tags:
                        category = entry.tags[0].term
                    
                    # Create article object
                    article = NewsArticle(
                        title=title,
                        url=url,
                        description=description,
                        published_date=pub_date,
                        source=feed_name,
                        category=category
                    )
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.error(f"Error processing entry from {feed_name}: {e}")
                    continue
            
            logger.info(f"Scraped {len(articles)} articles from {feed_name}")
            
        except Exception as e:
            logger.error(f"Error scraping {feed_name}: {e}")
        
        return articles
    
    def scrape_all_feeds(self) -> Dict[str, int]:
        """Scrape all configured RSS feeds and store articles in database"""
        results = {}
        total_new_articles = 0
        
        for feed_name, feed_url in self.rss_feeds.items():
            try:
                articles = self.scrape_feed(feed_name, feed_url)
                new_articles = 0
                
                # Store articles in database
                for article in articles:
                    if self.db.add_article(article):
                        new_articles += 1
                
                results[feed_name] = new_articles
                total_new_articles += new_articles
                
                # Be respectful to servers
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to process {feed_name}: {e}")
                results[feed_name] = 0
        
        logger.info(f"Scraping complete. Total new articles: {total_new_articles}")
        return results
    
    def add_custom_feed(self, name: str, url: str):
        """Add a custom RSS feed to the scraper"""
        self.rss_feeds[name] = url
        logger.info(f"Added custom feed: {name}")
    
    def remove_feed(self, name: str):
        """Remove an RSS feed from the scraper"""
        if name in self.rss_feeds:
            del self.rss_feeds[name]
            logger.info(f"Removed feed: {name}")
    
    def test_feed(self, feed_url: str) -> bool:
        """Test if an RSS feed is valid and accessible"""
        try:
            feed = feedparser.parse(feed_url)
            return len(feed.entries) > 0 and not feed.bozo
        except:
            return False

# Example usage
if __name__ == "__main__":
    # Initialize database and scraper
    db = NewsDatabase()
    scraper = NewsScraper(db)
    
    # Test scraping a single feed
    print("Testing single feed scrape...")
    articles = scraper.scrape_feed("BBC News", scraper.rss_feeds["BBC News"])
    print(f"Found {len(articles)} articles from BBC")
    
    # Store them in database
    new_count = 0
    for article in articles[:5]:  # Just store first 5 for testing
        if db.add_article(article):
            new_count += 1
    
    print(f"Added {new_count} new articles to database")
    
    # Show current database stats
    total_articles = db.get_article_count()
    print(f"Total articles in database: {total_articles}")
    
    # Show latest articles
    latest = db.get_latest_articles(limit=3)
    print("\nLatest articles:")
    for i, article in enumerate(latest, 1):
        print(f"{i}. {article.title}")
        print(f"   Source: {article.source}")
        print(f"   Published: {article.published_date}")
        print()