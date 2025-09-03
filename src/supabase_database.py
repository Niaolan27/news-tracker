import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from supabase import create_client, Client
from dotenv import load_dotenv
import json
import hashlib
from dataclasses import dataclass
from embedding_service import EmbeddingService

load_dotenv()

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
    embedding: Optional[List[float]] = None  # Changed from np.ndarray to List[float]

    def __repr__(self):
        return f"NewsArticle(title={self.title}, published_date={self.published_date}, category={self.category}, description={self.description})\n"

class SupabaseDatabase:
    def __init__(self):
        """Initialize Supabase client"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not found in environment variables")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.embedding_service = EmbeddingService()
        logger.info("Supabase client initialized")

    # User management
    def create_user(self, username: str, email: Optional[str] = None, password_hash: Optional[str] = None) -> int:
        """Create a new user"""
        try:
            data = {
                'username': username,
                'email': email,
                'password_hash': password_hash
            }
            
            result = self.supabase.table('users').insert(data).execute()
            user_id = result.data[0]['id']
            logger.info(f"Created user with ID: {user_id}")
            return user_id
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        try:
            result = self.supabase.table('users').select('*').eq('username', username).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None

    # Article management
    # Modified add_article method to accept NewsArticle object
    def add_article(self, article: NewsArticle) -> bool:
        """Add a new article to the database with embedding, return True if added, False if duplicate"""
        try:
            # Generate content hash to avoid duplicates
            content_for_hash = f"{article.title}{article.url}{article.description}"
            article.content_hash = hashlib.md5(content_for_hash.encode()).hexdigest()
            
            # Generate embedding
            embedding_array = self.embedding_service.create_article_embedding(
                article.title, article.description, article.category
            )
            
            # Convert numpy array to list for pgvector
            article.embedding = embedding_array.tolist() if embedding_array is not None else None
            
            data = {
                'title': article.title,
                'url': article.url,
                'description': article.description,
                'content': article.content,
                'published_date': article.published_date.isoformat() if article.published_date else None,
                'source': article.source,
                'category': article.category,
                'content_hash': article.content_hash,
                'embedding': article.embedding  # Store as list, pgvector will handle conversion
            }
            
            result = self.supabase.table('articles').insert(data).execute()
            logger.info(f"Added article with ID: {result.data[0]['id']}")
            return True
            
        except Exception as e:
            if "duplicate key" in str(e).lower():
                logger.debug(f"Article already exists: {article.url}")
                return False
            logger.error(f"Error adding article: {e}")
            return False

    def get_latest_articles(self, limit: int = 50) -> List[NewsArticle]:
        """Get the latest articles from the database"""
        try:
            result = self.supabase.table('articles').select('*').order('published_date', desc=True).limit(limit).execute()
            
            articles = []
            for row in result.data:
                articles.append(NewsArticle(
                    title=row['title'],
                    url=row['url'],
                    description=row['description'],
                    content=row.get('content', ''),
                    published_date=datetime.fromisoformat(row['published_date']) if row['published_date'] else None,
                    source=row['source'],
                    category=row['category'],
                    content_hash=row.get('content_hash'),
                    is_read=row.get('is_read', False),
                    user_rating=row.get('user_rating'),
                    embedding=row.get('embedding')
                ))
            
            return articles
        except Exception as e:
            logger.error(f"Error getting latest articles: {e}")
            return []

    def get_articles_by_source(self, source: str, limit: int = 20) -> List[NewsArticle]:
        """Get articles by source"""
        try:
            result = self.supabase.table('articles').select('*').eq('source', source).order('published_date', desc=True).limit(limit).execute()
            
            articles = []
            for row in result.data:
                articles.append(NewsArticle(
                    title=row['title'],
                    url=row['url'],
                    description=row['description'],
                    content=row.get('content', ''),
                    published_date=datetime.fromisoformat(row['published_date']) if row['published_date'] else None,
                    source=row['source'],
                    category=row['category'],
                    content_hash=row.get('content_hash'),
                    is_read=row.get('is_read', False),
                    user_rating=row.get('user_rating'),
                    embedding=row.get('embedding')
                ))
            
            return articles
        except Exception as e:
            logger.error(f"Error getting articles by source: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting articles by source: {e}")
            return []

    def get_articles_by_keyword(self, keyword: str, limit: int = 20) -> List[NewsArticle]:
        """Search articles by keyword in title or description"""
        try:
            result = self.supabase.table('articles').select('*').or_(
                f'title.ilike.%{keyword}%,description.ilike.%{keyword}%'
            ).order('published_date', desc=True).limit(limit).execute()
            
            articles = []
            for row in result.data:
                articles.append(NewsArticle(
                    title=row['title'],
                    url=row['url'],
                    description=row['description'],
                    content=row.get('content', ''),
                    published_date=datetime.fromisoformat(row['published_date']) if row['published_date'] else None,
                    source=row['source'],
                    category=row['category'],
                    content_hash=row.get('content_hash'),
                    is_read=row.get('is_read', False),
                    user_rating=row.get('user_rating'),
                    embedding=row.get('embedding')
                ))
            
            return articles
        except Exception as e:
            logger.error(f"Error searching articles by keyword: {e}")
            return []

    def get_articles_with_embeddings(self, limit: int = 100) -> List[NewsArticle]:
        """Get articles with their embeddings"""
        try:
            result = self.supabase.table('articles').select('*').not_('embedding', 'is', None).order('published_date', desc=True).limit(limit).execute()
            
            articles = []
            for row in result.data:
                # pgvector returns embeddings as lists, no need to deserialize
                embedding = row['embedding'] if row['embedding'] else None
                
                articles.append(NewsArticle(
                    title=row['title'],
                    url=row['url'],
                    description=row['description'],
                    content=row['content'] or "",
                    published_date=datetime.fromisoformat(row['published_date']) if row['published_date'] else None,
                    source=row['source'],
                    category=row['category'],
                    embedding=embedding
                ))
            
            return articles
        except Exception as e:
            logger.error(f"Error getting articles with embeddings: {e}")
            return []

    # User preferences
    def add_user_preference_with_embedding(self, username: str, description: str, weight: float = 1.0):
        """Add user preference with embedding"""
        try:
            # Get user ID
            user = self.get_user_by_username(username)
            if not user:
                user_id = self.create_user(username)
            else:
                user_id = user['id']
            
            # Generate embedding for the preference
            embedding_array = self.embedding_service.create_preference_embedding(description)
            embedding_list = embedding_array.tolist() if embedding_array is not None else None
            
            data = {
                'user_id': user_id,
                'description': description,
                'weight': weight,
                'embedding': embedding_list  # Store as list for pgvector
            }
            
            result = self.supabase.table('user_preferences').insert(data).execute()
            logger.info(f"Added preference for user: {username}")
            return result.data[0]['id']
            
        except Exception as e:
            logger.error(f"Error adding user preference: {e}")
            raise

    def get_user_preferences(self, username: str) -> List[Tuple[str, float]]:
        """Get user preferences (matching SQLite interface)"""
        try:
            user = self.get_user_by_username(username)
            if not user:
                return []
            
            result = self.supabase.table('user_preferences').select('description, weight').eq('user_id', user['id']).order('created_at', desc=True).execute()
            
            preferences = []
            for row in result.data:
                preferences.append((row['description'], row['weight']))
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return []

    def update_user_preference(self, preference_id: int, description: str = None, weight: float = None):
        """Update user preference"""
        try:
            data = {}
            if description is not None:
                data['description'] = description
            if weight is not None:
                data['weight'] = weight
            
            if data:
                result = self.supabase.table('user_preferences').update(data).eq('id', preference_id).execute()
                logger.info(f"Updated preference ID: {preference_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating preference: {e}")
            return False

    def delete_user_preference(self, preference_id: int):
        """Delete user preference"""
        try:
            result = self.supabase.table('user_preferences').delete().eq('id', preference_id).execute()
            logger.info(f"Deleted preference ID: {preference_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting preference: {e}")
            return False

    # Article summaries (if using AI)
    def save_article_summary(self, summary):
        """Save AI-generated article summary"""
        try:
            data = {
                'article_id': summary.article_id,
                'summary': summary.summary,
                'key_points': json.dumps(summary.key_points),
                'sentiment': summary.sentiment
            }
            
            result = self.supabase.table('article_summaries').insert(data).execute()
            logger.info(f"Saved summary for article ID: {summary.article_id}")
            return result.data[0]['id']
            
        except Exception as e:
            logger.error(f"Error saving article summary: {e}")
            return None

    def get_top_articles_with_summaries(self, limit: int = 5) -> List[Dict]:
        """Get top articles with their AI summaries"""
        try:
            result = self.supabase.table('articles').select('''
                id, title, url, published_date, source,
                article_summaries (
                    summary, key_points, sentiment
                )
            ''').order('published_date', desc=True).limit(limit).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error fetching articles with summaries: {e}")
            return []

    # Utility methods
    def get_total_articles(self) -> int:
        """Get total number of articles"""
        try:
            result = self.supabase.table('articles').select('id', count='exact').execute()
            return result.count
        except Exception as e:
            logger.error(f"Error getting article count: {e}")
            return 0

    def get_articles_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get articles within date range"""
        try:
            result = self.supabase.table('articles').select('*').gte('published_date', start_date).lte('published_date', end_date).order('published_date', desc=True).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting articles by date range: {e}")
            return []

    def get_personalized_articles(self, username: str, limit: int = 20) -> List[Tuple[NewsArticle, float]]:
        """Get articles ranked by user preferences using vector similarity"""
        try:
            user = self.get_user_by_username(username)
            if not user:
                return [(article, 0.0) for article in self.get_latest_articles(limit)]
            
            # Get user preferences with embeddings
            preferences_result = self.supabase.table('user_preferences').select('embedding, weight').eq('user_id', user['id']).not_('embedding', 'is', None).execute()
            
            if not preferences_result.data:
                return [(article, 0.0) for article in self.get_latest_articles(limit)]
            
            # Calculate average preference vector
            preference_vectors = []
            weights = []
            for row in preferences_result.data:
                if row['embedding']:
                    preference_vectors.append(row['embedding'])
                    weights.append(row['weight'])
            
            if not preference_vectors:
                return [(article, 0.0) for article in self.get_latest_articles(limit)]
            
            # Calculate weighted average of preference vectors
            weighted_prefs = []
            for i, vec in enumerate(preference_vectors):
                weighted_vec = [val * weights[i] for val in vec]
                weighted_prefs.append(weighted_vec)
            
            # Average the weighted preferences
            avg_pref = [sum(vals) / len(vals) for vals in zip(*weighted_prefs)]
            
            # Use pgvector similarity search
            result = self.supabase.rpc('find_similar_articles', {
                'query_embedding': avg_pref,
                'match_threshold': 0.5,
                'match_count': limit
            }).execute()
            
            articles = []
            for row in result.data:
                article = NewsArticle(
                    title=row['title'],
                    url=row['url'],
                    description=row['description'],
                    content=row.get('content', ''),
                    published_date=datetime.fromisoformat(row['published_date']) if row['published_date'] else None,
                    source=row['source'],
                    category=row.get('category'),
                    content_hash=row.get('content_hash'),
                    is_read=row.get('is_read', False),
                    user_rating=row.get('user_rating'),
                    embedding=row.get('embedding')
                )
                articles.append((article, row['similarity']))
            
            return articles
            
        except Exception as e:
            logger.error(f"Error getting personalized articles: {e}")
            return [(article, 0.0) for article in self.get_latest_articles(limit)]

    def get_user_preferences_with_ids(self, username: str) -> List[Tuple[int, str, float]]:
        """Get all preferences for a specific user with their IDs"""
        try:
            user = self.get_user_by_username(username)
            if not user:
                return []
            
            result = self.supabase.table('user_preferences').select('id, description, weight').eq('user_id', user['id']).order('created_at', desc=True).execute()
            
            preferences = []
            for row in result.data:
                preferences.append((row['id'], row['description'], row['weight']))
            
            return preferences
        except Exception as e:
            logger.error(f"Error getting user preferences with IDs: {e}")
            return []

    def add_reading_history(self, username: str, article_id: int, action: str):
        """Add reading history for a specific user"""
        try:
            user = self.get_user_by_username(username)
            if not user:
                user_id = self.create_user(username)
            else:
                user_id = user['id']
            
            data = {
                'user_id': user_id,
                'article_id': article_id,
                'action': action
            }
            
            result = self.supabase.table('reading_history').insert(data).execute()
            logger.info(f"Added reading history for user: {username}")
            
        except Exception as e:
            logger.error(f"Error adding reading history: {e}")

    def get_article_count(self) -> int:
        """Get total number of articles in database (alias for get_total_articles)"""
        return self.get_total_articles()

    def get_user_id(self, username: str) -> Optional[int]:
        """Get user ID by username"""
        try:
            user = self.get_user_by_username(username)
            return user['id'] if user else None
        except Exception as e:
            logger.error(f"Error getting user ID: {e}")
            return None

    def get_or_create_user(self, username: str, email: str = None) -> int:
        """Get existing user ID or create new user"""
        try:
            user_id = self.get_user_id(username)
            if user_id is None:
                user_id = self.create_user(username, email)
            return user_id
        except Exception as e:
            logger.error(f"Error getting or creating user: {e}")
            raise

    def list_users(self) -> List[Tuple[int, str, str]]:
        """List all users"""
        try:
            result = self.supabase.table('users').select('id, username, email').order('username').execute()
            
            users = []
            for row in result.data:
                users.append((row['id'], row['username'], row['email'] or ''))
            
            return users
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []

    def delete_user(self, username: str, confirm: bool = False) -> bool:
        """Delete a user and all their related data from the database"""
        try:
            user = self.get_user_by_username(username)
            if not user:
                logger.warning(f"User '{username}' not found in database.")
                return False
            
            user_id = user['id']
            
            if not confirm:
                # Get user statistics before deletion
                stats = self.get_user_deletion_stats(username)
                logger.info(f"WARNING: This will permanently delete user '{username}' and:")
                logger.info(f"   {stats['preferences']} user preferences")
                logger.info(f"   {stats['reading_history']} reading history entries")
                logger.info(f"   Email: {stats['email'] or 'None'}")
                logger.info(f"   Created: {stats['created_at']}")
                return False
            
            # Delete user preferences
            self.supabase.table('user_preferences').delete().eq('user_id', user_id).execute()
            
            # Delete reading history
            self.supabase.table('reading_history').delete().eq('user_id', user_id).execute()
            
            # Delete user
            result = self.supabase.table('users').delete().eq('id', user_id).execute()
            
            if result.data:
                logger.info(f"User '{username}' and all related data deleted successfully!")
                return True
            else:
                logger.error(f"Failed to delete user '{username}'")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting user '{username}': {e}")
            return False

    def get_user_deletion_stats(self, username: str) -> dict:
        """Get statistics about what will be deleted for a user"""
        try:
            user = self.get_user_by_username(username)
            if not user:
                return {}
            
            user_id = user['id']
            stats = {
                'username': user['username'],
                'email': user.get('email'),
                'created_at': user.get('created_at')
            }
            
            # Count preferences
            prefs_result = self.supabase.table('user_preferences').select('id', count='exact').eq('user_id', user_id).execute()
            stats['preferences'] = prefs_result.count
            
            # Count reading history
            history_result = self.supabase.table('reading_history').select('id', count='exact').eq('user_id', user_id).execute()
            stats['reading_history'] = history_result.count
            
            return stats
        except Exception as e:
            logger.error(f"Error getting user deletion stats: {e}")
            return {}

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

    def get_user_reading_history(self, username: str, limit: int = 50) -> List[Tuple[NewsArticle, datetime]]:
        """Get reading history for a specific user"""
        try:
            user = self.get_user_by_username(username)
            if not user:
                return []
            
            # Get reading history with article details
            result = self.supabase.table('reading_history').select('''
                timestamp,
                articles (
                    title, url, description, content, published_date, source, category, content_hash, is_read, user_rating, embedding
                )
            ''').eq('user_id', user['id']).order('timestamp', desc=True).limit(limit).execute()
            
            history = []
            for row in result.data:
                if row['articles']:
                    article_data = row['articles']
                    article = NewsArticle(
                        title=article_data['title'],
                        url=article_data['url'],
                        description=article_data['description'] or "",
                        content=article_data.get('content', ''),
                        published_date=datetime.fromisoformat(article_data['published_date']) if article_data['published_date'] else None,
                        source=article_data['source'],
                        category=article_data['category'],
                        content_hash=article_data.get('content_hash'),
                        is_read=article_data.get('is_read', False),
                        user_rating=article_data.get('user_rating'),
                        embedding=article_data.get('embedding')
                    )
                    timestamp = datetime.fromisoformat(row['timestamp'])
                    history.append((article, timestamp))
            
            return history
        except Exception as e:
            logger.error(f"Error getting reading history: {e}")
            return []

    def delete_old_articles(self, days_old: int = 3) -> int:
        """Delete articles older than specified number of days and return count of deleted articles"""
        try:
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # First, get the count of articles that will be deleted
            count_result = self.supabase.table('articles').select('id', count='exact').or_(
                f'published_date.lt.{cutoff_date.isoformat()},published_date.is.null'
            ).execute()
            count_to_delete = count_result.count
            
            # Delete the old articles
            self.supabase.table('articles').delete().or_(
                f'published_date.lt.{cutoff_date.isoformat()},published_date.is.null'
            ).execute()
            
            return count_to_delete
            
        except Exception as e:
            logger.error(f"Error deleting old articles: {e}")
            return 0

    def find_similar_articles(self, query_embedding: List[float], limit: int = 10) -> List[Tuple[NewsArticle, float]]:
        """Find articles similar to a given embedding vector"""
        try:
            result = self.supabase.rpc('find_similar_articles', {
                'query_embedding': query_embedding,
                'match_threshold': 0.5,
                'match_count': limit
            }).execute()
            
            articles = []
            for row in result.data:
                article = NewsArticle(
                    title=row['title'],
                    url=row['url'],
                    description=row['description'],
                    content=row.get('content', ''),
                    published_date=datetime.fromisoformat(row['published_date']) if row['published_date'] else None,
                    source=row['source'],
                    category=row.get('category'),
                    content_hash=row.get('content_hash'),
                    is_read=row.get('is_read', False),
                    user_rating=row.get('user_rating'),
                    embedding=row.get('embedding')
                )
                articles.append((article, row['similarity']))
            
            return articles
            
        except Exception as e:
            logger.error(f"Error finding similar articles: {e}")
            return []