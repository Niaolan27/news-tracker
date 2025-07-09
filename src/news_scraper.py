import feedparser
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urljoin
import logging
from news_database import NewsDatabase, NewsArticle

logger = logging.getLogger(__name__)

class NewsScraper:
    def __init__(self, database: NewsDatabase):
        """Initialize the news scraper with a database connection"""
        self.db = database
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NewsTracker/1.0 (RSS Feed Reader)'
        })
        
        # Default RSS feeds - you can expand this list
        self.rss_feeds = {
            'BBC News': 'http://feeds.bbci.co.uk/news/rss.xml',
            'Reuters': 'https://ir.thomsonreuters.com/rss/events.xml?items=15',
            'CNN': 'http://rss.cnn.com/rss/edition.rss',
            'CNN World': 'http://rss.cnn.com/rss/edition_world.rss',
            'NPR': 'https://feeds.npr.org/1001/rss.xml',
            'The Guardian': 'https://www.theguardian.com/world/rss',
            'New York Times': 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
            "New York Times World": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
            "Yahoo News": "https://news.yahoo.com/rss/",
            "ABC News International": "https://abcnews.go.com/abcnews/internationalheadlines",
            "The Guardian US": "https://www.theguardian.com/world/usa/rss",
            "South China Morning Post": "https://www.scmp.com/rss/91/feed",
        }
    
    def scrape_all_feeds(self) -> Dict[str, int]:
        """Scrape all configured RSS feeds and return count of new articles per feed"""
        # Delete articles older than 3 days before scraping new ones
        try:
            deleted_count = self.db.delete_old_articles(days_old=3)
            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} articles older than 3 days")
        except Exception as e:
            logger.error(f"Error deleting old articles: {e}")
        
        results = {}
        
        for feed_name, feed_url in self.rss_feeds.items():
            try:
                logger.info(f"Scraping {feed_name}...")
                count = self.scrape_feed(feed_name, feed_url)
                results[feed_name] = count
                logger.info(f"Found {count} new articles from {feed_name}")
            except Exception as e:
                logger.error(f"Error scraping {feed_name}: {e}")
                results[feed_name] = 0
        
        return results
    
    def scrape_feed(self, feed_name: str, feed_url: str) -> int:
        """Scrape a single RSS feed and return count of new articles"""
        try:
            # Parse the RSS feed
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                logger.warning(f"Feed {feed_name} has parsing issues: {feed.bozo_exception}")
            
            new_articles_count = 0
            
            for entry in feed.entries:
                article = self._parse_entry(entry, feed_name)
                if article:
                    # Try to add article to database
                    if self.db.add_article(article):
                        new_articles_count += 1
            
            return new_articles_count
            
        except Exception as e:
            logger.error(f"Failed to scrape feed {feed_name}: {e}")
            raise
    
    def _parse_entry(self, entry, source: str) -> Optional[NewsArticle]:
        """Parse a single RSS entry into a NewsArticle"""
        try:
            # Extract title
            title = entry.get('title', '').strip()
            if not title:
                return None
            
            # Extract URL
            url = entry.get('link', '').strip()
            if not url:
                return None
            
            # Extract description/summary
            description = ''
            if hasattr(entry, 'summary'):
                description = entry.summary
            elif hasattr(entry, 'description'):
                description = entry.description
            
            # Clean up description (remove HTML tags)
            description = self._clean_html(description)
            
            # Extract published date
            published_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass
            
            # If no published date, try updated date
            if not published_date and hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                try:
                    published_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass
            
            # If still no date, use current time
            if not published_date:
                published_date = datetime.now(timezone.utc)
            
            # Extract category/tags
            category = None
            if hasattr(entry, 'tags') and entry.tags:
                # Use the first tag as category
                category = entry.tags[0].get('term', '').strip()
            elif hasattr(entry, 'category'):
                category = entry.category.strip()
            
            return NewsArticle(
                title=title,
                url=url,
                description=description,
                published_date=published_date,
                source=source,
                category=category
            )
            
        except Exception as e:
            logger.error(f"Error parsing RSS entry: {e}")
            return None
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and clean up text"""
        if not text:
            return ''
        
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Replace HTML entities
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        text = text.replace('&nbsp;', ' ')
        # Clean up whitespace
        text = ' '.join(text.split())
        return text.strip()
    
    def test_feed(self, feed_url: str) -> bool:
        """Test if an RSS feed URL is valid and accessible"""
        try:
            # Try to parse the feed
            feed = feedparser.parse(feed_url)
            
            # Check if feed has entries and basic structure
            if hasattr(feed, 'entries') and len(feed.entries) > 0:
                # Check if at least one entry has title and link
                first_entry = feed.entries[0]
                if hasattr(first_entry, 'title') and hasattr(first_entry, 'link'):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error testing feed {feed_url}: {e}")
            return False
    
    def add_custom_feed(self, name: str, url: str):
        """Add a custom RSS feed to the list"""
        self.rss_feeds[name] = url
        logger.info(f"Added custom feed: {name} -> {url}")
    
    def remove_feed(self, name: str) -> bool:
        """Remove a feed from the list"""
        if name in self.rss_feeds:
            del self.rss_feeds[name]
            logger.info(f"Removed feed: {name}")
            return True
        return False
    
    def get_feed_info(self, feed_url: str) -> Dict:
        """Get information about an RSS feed"""
        try:
            feed = feedparser.parse(feed_url)
            
            info = {
                'title': getattr(feed.feed, 'title', 'Unknown'),
                'description': getattr(feed.feed, 'description', ''),
                'link': getattr(feed.feed, 'link', ''),
                'last_updated': getattr(feed.feed, 'updated', ''),
                'entry_count': len(feed.entries),
                'valid': not feed.bozo
            }
            
            if feed.bozo:
                info['error'] = str(feed.bozo_exception)
            
            return info
            
        except Exception as e:
            return {
                'title': 'Error',
                'description': f'Failed to parse feed: {e}',
                'valid': False,
                'error': str(e)
            }
    
    def scrape_single_feed(self, feed_name: str) -> int:
        """Scrape a single named feed from the configured feeds"""
        if feed_name not in self.rss_feeds:
            raise ValueError(f"Feed '{feed_name}' not found in configured feeds")
        
        feed_url = self.rss_feeds[feed_name]
        return self.scrape_feed(feed_name, feed_url)

# Example usage and testing
if __name__ == "__main__":
    # Test the scraper
    from news_database import NewsDatabase
    
    db = NewsDatabase()
    scraper = NewsScraper(db)
    
    # Test a single feed
    print("Testing BBC News feed...")
    count = scraper.scrape_single_feed('BBC News')
    print(f"Added {count} new articles from BBC News")
    
    # Test feed validation
    print("\nTesting feed validation...")
    test_feeds = [
        'http://feeds.bbci.co.uk/news/rss.xml',  # Valid
        'https://invalid-feed-url.com/rss.xml'   # Invalid
    ]
    
    for url in test_feeds:
        is_valid = scraper.test_feed(url)
        print(f"{url}: {'Valid' if is_valid else 'Invalid'}")