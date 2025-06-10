import sqlite3
import hashlib
import numpy as np
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Tuple
from embedding_service import EmbeddingService

@dataclass
class NewsArticle:
    title: str
    url: str
    description: str
    published_date: datetime
    source: str
    category: Optional[str] = None
    content_hash: Optional[str] = None
    embedding: Optional[np.ndarray] = None

class NewsDatabase:
    def __init__(self, db_path: str = "news_tracker.db"):
        self.db_path = db_path
        self.embedding_service = EmbeddingService()
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
                user_rating INTEGER DEFAULT 0,
                embedding BLOB  -- Store embedding vector as binary data
            )
        ''')
        
        # User preferences table with embeddings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT,
                weight REAL DEFAULT 1.0,
                category TEXT,
                embedding BLOB,  -- Store preference embedding
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
        """Add a new article to the database with embedding, return True if added, False if duplicate"""
        # Generate content hash to avoid duplicates
        content_for_hash = f"{article.title}{article.url}{article.description}"
        article.content_hash = hashlib.md5(content_for_hash.encode()).hexdigest()
        
        # Generate embedding
        article.embedding = self.embedding_service.create_article_embedding(
            article.title, article.description, article.category
        )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO articles 
                (title, url, description, published_date, source, category, content_hash, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article.title,
                article.url,
                article.description,
                article.published_date,
                article.source,
                article.category,
                article.content_hash,
                self.embedding_service.serialize_embedding(article.embedding)
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
    
    def get_articles_with_embeddings(self, limit: int = 100) -> List[NewsArticle]:
        """Get articles with their embeddings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, url, description, published_date, source, category, embedding
            FROM articles
            WHERE embedding IS NOT NULL
            ORDER BY published_date DESC
            LIMIT ?
        ''', (limit,))
        
        articles = []
        for row in cursor.fetchall():
            embedding = None
            if row[6]:  # embedding column
                embedding = self.embedding_service.deserialize_embedding(row[6])
            
            articles.append(NewsArticle(
                title=row[0],
                url=row[1],
                description=row[2],
                published_date=datetime.fromisoformat(row[3]) if row[3] else None,
                source=row[4],
                category=row[5],
                embedding=embedding
            ))
        
        conn.close()
        return articles
    
    def add_user_preference_with_embedding(self, keywords: List[str], 
                                         categories: List[str] = None, 
                                         weight: float = 1.0):
        """Add user preference with embedding"""
        embedding = self.embedding_service.create_preference_embedding(keywords, categories)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_preferences (keyword, weight, category, embedding)
            VALUES (?, ?, ?, ?)
        ''', (
            " ".join(keywords),
            weight,
            " ".join(categories) if categories else None,
            self.embedding_service.serialize_embedding(embedding)
        ))
        
        conn.commit()
        conn.close()
    
    def get_personalized_articles(self, limit: int = 20) -> List[Tuple[NewsArticle, float]]:
        """Get articles ranked by user preferences using embeddings"""
        # Get user preferences
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT embedding, weight FROM user_preferences WHERE embedding IS NOT NULL')
        preferences = cursor.fetchall()
        
        if not preferences:
            # No preferences set, return latest articles
            return [(article, 0.0) for article in self.get_latest_articles(limit)]
        
        # Get articles with embeddings
        articles = self.get_articles_with_embeddings(limit * 3)  # Get more to rank
        
        # Calculate scores for each article
        scored_articles = []
        for article in articles:
            if article.embedding is None:
                continue
                
            total_score = 0.0
            for pref_embedding_bytes, weight in preferences:
                pref_embedding = self.embedding_service.deserialize_embedding(pref_embedding_bytes)
                similarity = self.embedding_service.calculate_similarity(
                    article.embedding, pref_embedding
                )
                total_score += similarity * weight
            
            scored_articles.append((article, total_score))
        
        # Sort by score and return top articles
        scored_articles.sort(key=lambda x: x[1], reverse=True)
        return scored_articles[:limit]
    
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