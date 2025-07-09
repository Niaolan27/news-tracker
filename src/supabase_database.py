import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import json

load_dotenv()

logger = logging.getLogger(__name__)

class SupabaseDatabase:
    def __init__(self):
        """Initialize Supabase client"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not found in environment variables")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
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
    def add_article(self, title: str, url: str, description: str = None, 
                   published_date: str = None, source: str = None, 
                   category: str = None, content_hash: str = None) -> Optional[int]:
        """Add a new article"""
        try:
            data = {
                'title': title,
                'url': url,
                'description': description,
                'published_date': published_date,
                'source': source,
                'category': category,
                'content_hash': content_hash
            }
            
            result = self.supabase.table('articles').insert(data).execute()
            article_id = result.data[0]['id']
            logger.info(f"Added article with ID: {article_id}")
            return article_id
            
        except Exception as e:
            if "duplicate key" in str(e).lower():
                logger.debug(f"Article already exists: {url}")
                return None
            logger.error(f"Error adding article: {e}")
            return None

    def get_recent_articles(self, limit: int = 20) -> List[Dict]:
        """Get recent articles"""
        try:
            result = self.supabase.table('articles').select('*').order('published_date', desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting recent articles: {e}")
            return []

    def get_articles_by_source(self, source: str, limit: int = 20) -> List[Dict]:
        """Get articles by source"""
        try:
            result = self.supabase.table('articles').select('*').eq('source', source).order('published_date', desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting articles by source: {e}")
            return []

    # User preferences
    def add_user_preference_with_embedding(self, username: str, description: str, weight: float = 1.0):
        """Add user preference with embedding"""
        try:
            # Get user ID
            user = self.get_user_by_username(username)
            if not user:
                raise ValueError(f"User not found: {username}")
            
            data = {
                'user_id': user['id'],
                'description': description,
                'weight': weight
            }
            
            result = self.supabase.table('user_preferences').insert(data).execute()
            logger.info(f"Added preference for user: {username}")
            return result.data[0]['id']
            
        except Exception as e:
            logger.error(f"Error adding user preference: {e}")
            raise

    def get_user_preferences(self, username: str) -> List[Dict]:
        """Get user preferences"""
        try:
            user = self.get_user_by_username(username)
            if not user:
                return []
            
            result = self.supabase.table('user_preferences').select('*').eq('user_id', user['id']).execute()
            return result.data
            
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