import sqlite3
import os
from supabase import create_client, Client
from news_database import NewsDatabase
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseMigrationDatabase:
    def __init__(self):
        """Initialize Supabase client with SERVICE ROLE key for migration"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE')  # Use service role key
        
        if not self.supabase_url or not self.service_role_key:
            raise ValueError("Supabase credentials not found in environment variables")
        
        self.supabase: Client = create_client(self.supabase_url, self.service_role_key)
        logger.info("Supabase migration client initialized with service role")

    def create_user(self, username: str, email: str = None, password_hash: str = None) -> int:
        """Create a new user using service role"""
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

    def add_article(self, title: str, url: str, description: str = None, 
                   published_date: str = None, source: str = None, 
                   category: str = None, content_hash: str = None) -> int:
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

    def add_user_preference_with_embedding(self, username: str, description: str, weight: float = 1.0):
        """Add user preference"""
        try:
            # Get user ID
            user_result = self.supabase.table('users').select('id').eq('username', username).execute()
            if not user_result.data:
                raise ValueError(f"User not found: {username}")
            
            user_id = user_result.data[0]['id']
            
            data = {
                'user_id': user_id,
                'description': description,
                'weight': weight
            }
            
            result = self.supabase.table('user_preferences').insert(data).execute()
            logger.info(f"Added preference for user: {username}")
            return result.data[0]['id']
            
        except Exception as e:
            logger.error(f"Error adding user preference: {e}")
            raise
    def add_reading_history(self, user_id: int, article_id: int, action: str, timestamp: str = None):
        """Add reading history entry"""
        try:
            data = {
                'user_id': user_id,
                'article_id': article_id,
                'action': action,
                'timestamp': timestamp
            }
            
            result = self.supabase.table('reading_history').insert(data).execute()
            logger.info(f"Added reading history for user {user_id}, article {article_id}, action {action}")
            return result.data[0]['id']
            
        except Exception as e:
            logger.error(f"Error adding reading history: {e}")
            return None

def migrate_sqlite_to_supabase():
    """Migrate data from SQLite to Supabase"""
    
    # Initialize databases
    sqlite_db = NewsDatabase()
    supabase_db = SupabaseMigrationDatabase()
    
    try:
        conn = sqlite3.connect(sqlite_db.db_path)
        cursor = conn.cursor()
        
        # Migrate users
        logger.info("Migrating users...")
        cursor.execute("SELECT username, email, password_hash FROM users")
        users = cursor.fetchall()
        
        user_id_mapping = {}  # old_username -> new_user_id
        for user in users:
            username, email, password_hash = user
            try:
                new_user_id = supabase_db.create_user(username, email, password_hash)
                user_id_mapping[username] = new_user_id
                logger.info(f"Migrated user: {username}")
            except Exception as e:
                logger.error(f"Error migrating user {username}: {e}")
        
        # Remove the breakpoint
        # breakpoint()  # Remove this line
        
        # Migrate articles
        logger.info("Migrating articles...")
        cursor.execute("SELECT id, title, url, description, published_date, source, category, content_hash FROM articles")
        articles = cursor.fetchall()
        
        article_id_mapping = {}  # old_article_id -> new_article_id
        article_count = 0
        for article in articles:
            old_article_id, title, url, description, published_date, source, category, content_hash = article
            try:
                new_article_id = supabase_db.add_article(title, url, description, published_date, source, category, content_hash)
                if new_article_id:
                    article_id_mapping[old_article_id] = new_article_id
                    article_count += 1
            except Exception as e:
                logger.error(f"Error migrating article {title}: {e}")
        
        logger.info(f"Migrated {article_count} articles")
        
        # Migrate user preferences
        logger.info("Migrating user preferences...")
        cursor.execute("""
            SELECT u.username, up.description, up.weight 
            FROM user_preferences up 
            JOIN users u ON up.user_id = u.id
        """)
        preferences = cursor.fetchall()
        
        pref_count = 0
        for pref in preferences:
            username, description, weight = pref
            try:
                supabase_db.add_user_preference_with_embedding(username, description, weight)
                pref_count += 1
            except Exception as e:
                logger.error(f"Error migrating preference for {username}: {e}")
        
        logger.info(f"Migrated {pref_count} user preferences")
        
        # Migrate reading history
        logger.info("Migrating reading history...")
        
        # Check if reading_history table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reading_history'")
        if cursor.fetchone():
            cursor.execute("""
                SELECT rh.user_id, rh.article_id, rh.action, rh.timestamp,
                       u.username
                FROM reading_history rh
                JOIN users u ON rh.user_id = u.id
            """)
            reading_history = cursor.fetchall()
            
            history_count = 0
            for history in reading_history:
                old_user_id, old_article_id, action, timestamp, username = history
                
                # Get new user_id and article_id from mappings
                new_user_id = user_id_mapping.get(username)
                new_article_id = article_id_mapping.get(old_article_id)
                breakpoint()
                if new_user_id and new_article_id:
                    try:
                        supabase_db.add_reading_history(new_user_id, new_article_id, action, timestamp)
                        history_count += 1
                    except Exception as e:
                        logger.error(f"Error migrating reading history for user {username}: {e}")
                else:
                    logger.warning(f"Skipping reading history - user or article not found: user={username}, article_id={old_article_id}")
            
            logger.info(f"Migrated {history_count} reading history entries")
        else:
            logger.info("No reading_history table found in SQLite database")
        
        conn.close()
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate_sqlite_to_supabase()