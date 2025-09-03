import sqlite3
import hashlib
import numpy as np
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Tuple
from embedding_service import EmbeddingService
import os
import logging

logger = logging.getLogger(__name__)

@dataclass
class NewsArticle:
    title: str
    url: str
    description: str
    content: str
    published_date: datetime
    source: str
    category: Optional[str] = None
    content_hash: Optional[str] = None
    is_read: bool = False
    user_rating: Optional[float] = None
    embedding: Optional[np.ndarray] = None

    def __repr__(self):
        return f"NewsArticle(title={self.title}, published_date={self.published_date}, category={self.category}, description={self.description})\n"

class NewsDatabase:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Database is now in the same directory as the source files
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_dir, "news_tracker.db")
        
        self.db_path = db_path
        self.embedding_service = EmbeddingService()
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Articles table with content field
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                description TEXT,
                content TEXT,
                published_date DATETIME,
                source TEXT,
                category TEXT,
                content_hash TEXT UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT 0,
                user_rating REAL DEFAULT 0,
                embedding BLOB  -- Store embedding vector as binary data
            )
        ''')
        
        # User preferences table with user_id foreign key
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                description TEXT,
                weight REAL DEFAULT 1.0,
                embedding BLOB,  -- Store preference embedding
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Migration: Add description column and copy data from keyword/category if they exist
        try:
            cursor.execute("SELECT keyword FROM user_preferences LIMIT 1")
            # If this succeeds, we have old schema, need to migrate
            cursor.execute("ALTER TABLE user_preferences ADD COLUMN description_temp TEXT")
            cursor.execute('''
                UPDATE user_preferences 
                SET description_temp = CASE 
                    WHEN category IS NOT NULL THEN keyword || ' (Category: ' || category || ')'
                    ELSE keyword
                END
            ''')
            cursor.execute("CREATE TABLE user_preferences_new AS SELECT id, user_id, description_temp as description, weight, embedding, created_at FROM user_preferences")
            cursor.execute("DROP TABLE user_preferences")
            cursor.execute("ALTER TABLE user_preferences_new RENAME TO user_preferences")
        except sqlite3.OperationalError:
            # New schema already in place, no migration needed
            pass
        
        # Migration: Add content column to articles table if it doesn't exist
        try:
            cursor.execute("SELECT content FROM articles LIMIT 1")
        except sqlite3.OperationalError:
            # Content column doesn't exist, add it
            cursor.execute("ALTER TABLE articles ADD COLUMN content TEXT")
            logger.info("Added content column to articles table")
        
        # Reading history table with user_id foreign key
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reading_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                article_id INTEGER,
                action TEXT, -- 'clicked', 'read', 'dismissed'
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
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
                (title, url, description, content, published_date, source, category, content_hash, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article.title,
                article.url,
                article.description,
                article.content,
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
            SELECT title, url, description, content, published_date, source, category
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
                content=row[3] or "",
                published_date=datetime.fromisoformat(row[4]) if row[4] else None,
                source=row[5],
                category=row[6]
            ))
        
        conn.close()
        return articles
    
    def get_articles_by_keyword(self, keyword: str, limit: int = 20) -> List[NewsArticle]:
        """Search articles by keyword in title or description"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, url, description, content, published_date, source, category
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
                content=row[3] or "",
                published_date=datetime.fromisoformat(row[4]) if row[4] else None,
                source=row[5],
                category=row[6]
            ))
        
        conn.close()
        return articles
    
    def get_articles_by_source(self, source: str, limit: int = 20) -> List[NewsArticle]:
        """Get articles by source"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, url, description, content, published_date, source, category, content_hash, is_read, user_rating
            FROM articles
            WHERE source = ?
            ORDER BY published_date DESC
            LIMIT ?
        ''', (source, limit))
        
        articles = []
        for row in cursor.fetchall():
            articles.append(NewsArticle(
                title=row[0],
                url=row[1],
                description=row[2],
                content=row[3] or "",
                published_date=datetime.fromisoformat(row[4]) if row[4] else None,
                source=row[5],
                category=row[6],
                content_hash=row[7],
                is_read=bool(row[8]) if row[8] is not None else False,
                user_rating=row[9]
            ))
        
        conn.close()
        return articles
    
    def get_articles_with_embeddings(self, limit: int = 100) -> List[NewsArticle]:
        """Get articles with their embeddings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, url, description, content, published_date, source, category, content_hash, is_read, user_rating, embedding
            FROM articles
            WHERE embedding IS NOT NULL
            ORDER BY published_date DESC
            LIMIT ?
        ''', (limit,))
        
        articles = []
        for row in cursor.fetchall():
            embedding = None
            if row[10]:  # embedding column
                embedding = self.embedding_service.deserialize_embedding(row[10])
            
            articles.append(NewsArticle(
                title=row[0],
                url=row[1],
                description=row[2],
                content=row[3] or "",
                published_date=datetime.fromisoformat(row[4]) if row[4] else None,
                source=row[5],
                category=row[6],
                content_hash=row[7],
                is_read=bool(row[8]) if row[8] is not None else False,
                user_rating=row[9],
                embedding=embedding
            ))
        
        conn.close()
        return articles
    
    def add_user_preference_with_embedding(self, username: str, description: str, 
                                         weight: float = 1.0):
        """Add user preference with embedding for specific user"""
        user_id = self.get_or_create_user(username)
        embedding = self.embedding_service.create_preference_embedding(description)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_preferences (user_id, description, weight, embedding)
            VALUES (?, ?, ?, ?)
        ''', (
            user_id,
            description,
            weight,
            self.embedding_service.serialize_embedding(embedding)
        ))
        
        conn.commit()
        conn.close()
    
    def get_personalized_articles(self, username: str, limit: int = 20) -> List[Tuple[NewsArticle, float]]:
        """Get articles ranked by user preferences using embeddings for specific user"""
        user_id = self.get_user_id(username)
        if user_id is None:
            # User doesn't exist, return latest articles
            return [(article, 0.0) for article in self.get_latest_articles(limit)]
        
        # Get user preferences
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT embedding, weight FROM user_preferences 
            WHERE user_id = ? AND embedding IS NOT NULL
        ''', (user_id,))
        preferences = cursor.fetchall()
        
        if not preferences:
            # No preferences set, return latest articles
            return [(article, 0.0) for article in self.get_latest_articles(limit)]
        
        # Get articles with embeddings
        articles = self.get_articles_with_embeddings(200)  # Get more to rank
        
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
        conn.close()
        return scored_articles[:limit]
    
    def get_user_preferences(self, username: str) -> List[Tuple[str, float]]:
        """Get all preferences for a specific user"""
        user_id = self.get_user_id(username)
        if user_id is None:
            return []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT description, weight FROM user_preferences 
            WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,))
        preferences = cursor.fetchall()
        
        conn.close()
        return preferences
    
    def get_user_preferences_with_ids(self, username: str) -> List[Tuple[int, str, float]]:
        """Get all preferences for a specific user with their IDs"""
        user_id = self.get_user_id(username)
        if user_id is None:
            return []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, description, weight FROM user_preferences 
            WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,))
        preferences = cursor.fetchall()
        
        conn.close()
        return preferences
    
    def add_reading_history(self, username: str, article_id: int, action: str):
        """Add reading history for a specific user"""
        user_id = self.get_or_create_user(username)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO reading_history (user_id, article_id, action)
            VALUES (?, ?, ?)
        ''', (user_id, article_id, action))
        
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
    
    def delete_old_articles(self, days_old: int = 3) -> int:
        """Delete articles older than specified number of days and return count of deleted articles"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # First, get the count of articles that will be deleted
            cursor.execute('''
                SELECT COUNT(*) FROM articles 
                WHERE published_date < ? OR published_date IS NULL
            ''', (cutoff_date.isoformat(),))
            count_to_delete = cursor.fetchone()[0]
            
            # Delete the old articles
            cursor.execute('''
                DELETE FROM articles 
                WHERE published_date < ? OR published_date IS NULL
            ''', (cutoff_date.isoformat(),))
            
            conn.commit()
            return count_to_delete
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def create_user(self, username: str, email: str = None) -> int:
        """Create a new user and return user ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email)
                VALUES (?, ?)
            ''', (username, email))
            user_id = cursor.lastrowid
            conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            raise ValueError(f"Username '{username}' already exists")
        finally:
            conn.close()
    
    def get_user_id(self, username: str) -> Optional[int]:
        """Get user ID by username"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else None
    
    def get_or_create_user(self, username: str, email: str = None) -> int:
        """Get existing user ID or create new user"""
        user_id = self.get_user_id(username)
        if user_id is None:
            user_id = self.create_user(username, email)
        return user_id
    
    def list_users(self) -> List[Tuple[int, str, str]]:
        """List all users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, email FROM users ORDER BY username')
        users = cursor.fetchall()
        
        conn.close()
        return users
    
    def delete_user(self, username: str, confirm: bool = False) -> bool:
        """Delete a user and all their related data from the database"""
        user_id = self.get_user_id(username)
        if user_id is None:
            print(f"User '{username}' not found in database.")
            return False
        
        if not confirm:
            # Get user statistics before deletion
            stats = self.get_user_deletion_stats(username)
            print(f"\n⚠️  WARNING: This will permanently delete user '{username}' and:")
            print(f"   📊 {stats['preferences']} user preferences")
            print(f"   📚 {stats['reading_history']} reading history entries")
            print(f"   📧 Email: {stats['email'] or 'None'}")
            print(f"   📅 Created: {stats['created_at']}")
            
            response = input("\nAre you sure you want to delete this user? This cannot be undone. (yes/no): ")
            if response.lower() != 'yes':
                print("User deletion cancelled.")
                return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Due to CASCADE DELETE, deleting the user will automatically delete:
            # - user_preferences (FOREIGN KEY with ON DELETE CASCADE)
            # - reading_history (FOREIGN KEY with ON DELETE CASCADE)
            
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            
            if cursor.rowcount == 0:
                print(f"Failed to delete user '{username}'")
                return False
            
            conn.commit()
            print(f"✅ User '{username}' and all related data deleted successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting user '{username}': {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_user_deletion_stats(self, username: str) -> dict:
        """Get statistics about what will be deleted for a user"""
        user_id = self.get_user_id(username)
        if user_id is None:
            return {}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Get user info
        cursor.execute('SELECT username, email, created_at FROM users WHERE id = ?', (user_id,))
        user_info = cursor.fetchone()
        if user_info:
            stats['username'] = user_info[0]
            stats['email'] = user_info[1]
            stats['created_at'] = user_info[2]
        
        # Count preferences
        cursor.execute('SELECT COUNT(*) FROM user_preferences WHERE user_id = ?', (user_id,))
        stats['preferences'] = cursor.fetchone()[0]
        
        # Count reading history
        cursor.execute('SELECT COUNT(*) FROM reading_history WHERE user_id = ?', (user_id,))
        stats['reading_history'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def user_exists(self, username: str) -> bool:
        """Check if a user exists in the database"""
        return self.get_user_id(username) is not None
    
    def display_articles(self, articles: List[NewsArticle]):
        """Display articles in a readable format"""
        for i, article in enumerate(articles):
            print(f"{i}.Title: {article.title}")
            print(f"URL: {article.url}")
            print(f"Description: {article.description[:100]}...")
            print("#"*80)
    
    def get_user_reading_history(self, username, limit=50):
        """Get reading history for a specific user"""
        query = """
        SELECT a.id, a.title, a.url, a.description, a.published_date, 
               a.source, a.category, rh.read_date
        FROM reading_history rh
        JOIN articles a ON rh.article_id = a.id
        JOIN users u ON rh.user_id = u.id
        WHERE u.username = ?
        ORDER BY rh.read_date DESC
        LIMIT ?
        """
        
        cursor = self.conn.cursor()
        cursor.execute(query, (username, limit))
        rows = cursor.fetchall()
        
        history = []
        for row in rows:
            article = NewsArticle(
                title=row[1],
                url=row[2],
                description=row[3] or "",
                published_date=datetime.fromisoformat(row[4]) if row[4] else None,
                source=row[5],
                category=row[6]
            )
            read_date = datetime.fromisoformat(row[7])
            history.append((article, read_date))
        
        return history

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