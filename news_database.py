import sqlite3
import hashlib
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class NewsArticle:
    title: str
    url: str
    description: str
    published_date: datetime
    source: str
    category: Optional[str] = None
    content_hash: Optional[str] = None

class NewsDatabase:
    def __init__(self, db_path: str = "news_tracker.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Articles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                description TEXT,
                published_date DATETIME,
                source TEXT,
                category TEXT,
                content_hash TEXT UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT 0,
                user_rating INTEGER DEFAULT 0
            )
        ''')
        
        # User preferences table (for future ML features)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT,
                weight REAL DEFAULT 1.0,
                category TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Reading history table (for learning preferences)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reading_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                action TEXT, -- 'clicked', 'read', 'dismissed'
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_article(self, article: NewsArticle) -> bool:
        """Add a new article to the database, return True if added, False if duplicate"""
        # Generate content hash to avoid duplicates
        content_for_hash = f"{article.title}{article.url}{article.description}"
        article.content_hash = hashlib.md5(content_for_hash.encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO articles 
                (title, url, description, published_date, source, category, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                article.title,
                article.url,
                article.description,
                article.published_date,
                article.source,
                article.category,
                article.content_hash
            ))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Article already exists
            return False
        finally:
            conn.close()
    
    def get_latest_articles(self, limit: int = 50) -> List[NewsArticle]:
        """Get the latest articles from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, url, description, published_date, source, category
            FROM articles
            ORDER BY published_date DESC
            LIMIT ?
        ''', (limit,))
        
        articles = []
        for row in cursor.fetchall():
            articles.append(NewsArticle(
                title=row[0],
                url=row[1],
                description=row[2],
                published_date=datetime.fromisoformat(row[3]) if row[3] else None,
                source=row[4],
                category=row[5]
            ))
        
        conn.close()
        return articles
    
    def get_articles_by_keyword(self, keyword: str, limit: int = 20) -> List[NewsArticle]:
        """Search articles by keyword in title or description"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, url, description, published_date, source, category
            FROM articles
            WHERE title LIKE ? OR description LIKE ?
            ORDER BY published_date DESC
            LIMIT ?
        ''', (f'%{keyword}%', f'%{keyword}%', limit))
        
        articles = []
        for row in cursor.fetchall():
            articles.append(NewsArticle(
                title=row[0],
                url=row[1],
                description=row[2],
                published_date=datetime.fromisoformat(row[3]) if row[3] else None,
                source=row[4],
                category=row[5]
            ))
        
        conn.close()
        return articles
    
    def add_user_preference(self, keyword: str, weight: float = 1.0, category: str = None):
        """Add a user preference for content curation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_preferences (keyword, weight, category)
            VALUES (?, ?, ?)
        ''', (keyword, weight, category))
        
        conn.commit()
        conn.close()
    
    def get_article_count(self) -> int:
        """Get total number of articles in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM articles')
        count = cursor.fetchone()[0]
        
        conn.close()
        return count

# Example usage
if __name__ == "__main__":
    # Initialize database
    db = NewsDatabase()
    
    # Example article
    sample_article = NewsArticle(
        title="Sample News Article",
        url="https://example.com/news1",
        description="This is a sample news article for testing",
        published_date=datetime.now(),
        source="Example News",
        category="Technology"
    )
    
    # Add article
    added = db.add_article(sample_article)
    print(f"Article added: {added}")
    
    # Get article count
    count = db.get_article_count()
    print(f"Total articles: {count}")
    
    # Get latest articles
    articles = db.get_latest_articles(limit=10)
    print(f"Found {len(articles)} articles")