#!/usr/bin/env python3
"""
News Tracker MVP - Main Application
A simple news aggregator that scrapes RSS feeds and stores articles in a database.
"""

import sys
import argparse
from datetime import datetime, timedelta
from news_database import NewsDatabase, NewsArticle
from news_scraper import NewsScraper
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NewsTracker:
    def __init__(self):
        self.db = NewsDatabase()
        self.scraper = NewsScraper(self.db)
    
    def run_scrape(self):
        """Run a full scrape of all configured RSS feeds"""
        print("🔄 Starting news scrape...")
        print("-" * 50)
        
        results = self.scraper.scrape_all_feeds()
        
        print("\n📊 Scraping Results:")
        print("-" * 30)
        total_new = 0
        for feed_name, count in results.items():
            print(f"{feed_name:20}: {count:3} new articles")
            total_new += count
        
        print("-" * 30)
        print(f"{'Total':20}: {total_new:3} new articles")
        print(f"Database now contains {self.db.get_article_count()} articles total")
    
    def show_latest(self, limit=10):
        """Display the latest articles"""
        articles = self.db.get_latest_articles(limit)
        
        if not articles:
            print("No articles found in database. Run scrape first!")
            return
        
        print(f"\n📰 Latest {len(articles)} Articles:")
        print("=" * 80)
        
        for i, article in enumerate(articles, 1):
            print(f"\n{i}. {article.title}")
            print(f"   📅 {article.published_date.strftime('%Y-%m-%d %H:%M') if article.published_date else 'No date'}")
            print(f"   📊 {article.source}")
            if article.category:
                print(f"   🏷️  {article.category}")
            print(f"   🔗 {article.url}")
            print(f"   📝 {article.description[:150]}{'...' if len(article.description) > 150 else ''}")
    
    def search_articles(self, keyword, limit=10):
        """Search for articles containing a keyword"""
        articles = self.db.get_articles_by_keyword(keyword, limit)
        
        if not articles:
            print(f"No articles found containing '{keyword}'")
            return
        
        print(f"\n🔍 Search Results for '{keyword}' ({len(articles)} found):")
        print("=" * 80)
        
        for i, article in enumerate(articles, 1):
            print(f"\n{i}. {article.title}")
            print(f"   📅 {article.published_date.strftime('%Y-%m-%d %H:%M') if article.published_date else 'No date'}")
            print(f"   📊 {article.source}")
            print(f"   🔗 {article.url}")
    
    def show_stats(self):
        """Display database statistics"""
        total_articles = self.db.get_article_count()
        
        print("\n📈 Database Statistics:")
        print("-" * 30)
        print(f"Total articles: {total_articles}")
        
        if total_articles > 0:
            # Get articles from last 24 hours
            recent_articles = self.db.get_latest_articles(1000)  # Get more to filter by date
            today = datetime.now()
            yesterday = today - timedelta(days=1)
            
            recent_count = sum(1 for a in recent_articles 
                             if a.published_date and a.published_date > yesterday)
            
            print(f"Articles from last 24h: {recent_count}")
            
            # Show sources
            sources = {}
            for article in recent_articles[:100]:  # Sample recent articles
                source = article.source
                sources[source] = sources.get(source, 0) + 1
            
            print("\nTop sources:")
            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {source}: {count}")
    
    def add_feed(self, name, url):
        """Add a custom RSS feed"""
        if self.scraper.test_feed(url):
            self.scraper.add_custom_feed(name, url)
            print(f"✅ Added feed: {name}")
            print(f"   URL: {url}")
        else:
            print(f"❌ Failed to add feed. URL may be invalid: {url}")
    
    def list_feeds(self):
        """List all configured RSS feeds"""
        print("\n📡 Configured RSS Feeds:")
        print("-" * 50)
        
        for i, (name, url) in enumerate(self.scraper.rss_feeds.items(), 1):
            print(f"{i:2}. {name}")
            print(f"     {url}")

    def list_titles(self, limit=None):
        """List all articles by their titles"""
        articles = self.db.get_latest_articles(limit or 1000)  # Get all or specified limit
        
        if not articles:
            print("No articles found in database. Run scrape first!")
            return
        
        print(f"\n📋 All Article Titles ({len(articles)} total):")
        print("=" * 80)
        
        for i, article in enumerate(articles, 1):
            published = article.published_date.strftime('%Y-%m-%d') if article.published_date else 'No date'
            print(f"{i:4}. [{published}] {article.title}")
            print(f"      Source: {article.source}")

def main():
    parser = argparse.ArgumentParser(description='News Tracker MVP')
    parser.add_argument('command', choices=['scrape', 'latest', 'search', 'stats', 'add-feed', 'list-feeds', 'list-titles'],
                       help='Command to execute')
    parser.add_argument('--keyword', '-k', help='Keyword for search command')
    parser.add_argument('--limit', '-l', type=int, default=10, help='Limit number of results')
    parser.add_argument('--feed-name', help='Name for new RSS feed')
    parser.add_argument('--feed-url', help='URL for new RSS feed')
    
    args = parser.parse_args()
    
    tracker = NewsTracker()
    
    try:
        if args.command == 'scrape':
            tracker.run_scrape()
            
        elif args.command == 'latest':
            tracker.show_latest(args.limit)
            
        elif args.command == 'search':
            if not args.keyword:
                print("❌ Search requires --keyword parameter")
                sys.exit(1)
            tracker.search_articles(args.keyword, args.limit)
            
        elif args.command == 'stats':
            tracker.show_stats()
            
        elif args.command == 'add-feed':
            if not args.feed_name or not args.feed_url:
                print("❌ Add feed requires --feed-name and --feed-url parameters")
                sys.exit(1)
            tracker.add_feed(args.feed_name, args.feed_url)
            
        elif args.command == 'list-feeds':
            tracker.list_feeds()

        elif args.command == 'list-titles':
            tracker.list_titles(args.limit)
        
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()