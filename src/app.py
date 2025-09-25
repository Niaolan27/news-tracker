from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps
import sqlite3
from news_database import NewsDatabase
from supabase_database import SupabaseDatabase
from dotenv import load_dotenv
import os
from news_scraper import NewsScraper
from scheduler import start_background_scraping, get_scheduler
import logging

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')
app.config['JWT_EXPIRATION_DELTA'] = timedelta(hours=24)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database - use Supabase if configured, fallback to SQLite
use_supabase = os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_PUBLISHABLE_KEY')
if use_supabase:
    logger.info("Using Supabase database")
    db = SupabaseDatabase()
else:
    logger.info("Using SQLite database")
    db = NewsDatabase()

scraper = NewsScraper(db)

# Start background news scraping
try:
    scheduler_instance = start_background_scraping()
    logger.info("Background news scraping started - articles will be scraped every 2 hours")
except Exception as e:
    logger.error(f"Failed to start background scraping: {e}")

def token_required(f):
    """Decorator to require JWT token for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
            current_username = data['username']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(current_user_id, current_username, *args, **kwargs)
    
    return decorated

def get_user_by_credentials(username, password):
    """Get user by username and verify password"""
    if use_supabase:
        user = db.get_user_by_username(username)
        if user and check_password_hash(user.get('password_hash', ''), password):
            return {
                'id': user['id'],
                'username': user['username'],
                'email': user.get('email')
            }
        return None
    else:
        # SQLite fallback
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, email, password_hash FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2]
            }
        return None

def update_user_table_for_auth():
    """Add password_hash column to users table if it doesn't exist (SQLite only)"""
    if not use_supabase:
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN password_hash TEXT')
            conn.commit()
            logger.info("Added password_hash column to users table")
        except sqlite3.OperationalError:
            # Column already exists
            pass
        finally:
            conn.close()

# Initialize auth table updates (only for SQLite)
if not use_supabase:
    update_user_table_for_auth()

# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        total_articles = db.get_total_articles() if use_supabase else db.get_article_count()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'supabase' if use_supabase else 'sqlite',
            'total_articles': total_articles
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Create a new user account"""
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        username = data['username'].strip()
        password = data['password']
        email = data.get('email', '').strip() or None
        
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters long'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Check if user already exists
        if use_supabase:
            existing_user = db.get_user_by_username(username)
            if existing_user:
                return jsonify({'error': 'Username already exists'}), 409
        else:
            if db.user_exists(username):
                return jsonify({'error': 'Username already exists'}), 409
        
        # Hash password and create user
        password_hash = generate_password_hash(password)
        
        if use_supabase:
            user_id = db.create_user(username, email, password_hash)
        else:
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            ''', (username, email, password_hash))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + app.config['JWT_EXPIRATION_DELTA']
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'message': 'User created successfully',
            'user': {
                'id': user_id,
                'username': username,
                'email': email
            },
            'token': token
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Log in to user account"""
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        username = data['username'].strip()
        password = data['password']
        
        user = get_user_by_credentials(username, password)
        
        if not user:
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user['id'],
            'username': user['username'],
            'exp': datetime.utcnow() + app.config['JWT_EXPIRATION_DELTA']
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'message': 'Login successful',
            'user': user,
            'token': token
        }), 200
        
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/articles/recommended', methods=['GET'])
@token_required
def get_recommended_articles(current_user_id, current_username):
    """Get personalized article recommendations for the current user"""
    try:
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 100)  # Cap at 100 articles
        
        scored_articles = db.get_personalized_articles(current_username, limit)
        
        articles_data = []
        for article, score in scored_articles:
            articles_data.append({
                'title': article.title,
                'url': article.url,
                'description': article.description,
                'published_date': article.published_date.isoformat() if article.published_date else None,
                'source': article.source,
                'category': article.category,
                'relevance_score': round(score, 3)
            })
        
        return jsonify({
            'articles': articles_data,
            'total': len(articles_data),
            'username': current_username
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/articles/read', methods=['POST'])
@token_required
def mark_article_read(current_user_id, current_username):
    """Mark an article as read by the current user"""
    try:
        data = request.get_json()
        
        if not data or not data.get('article_url'):
            return jsonify({'error': 'article_url is required'}), 400
        
        article_url = data['article_url']
        action = data.get('action', 'read')  # 'read', 'clicked', 'dismissed'
        
        # Find article by URL
        if use_supabase:
            # For Supabase, query the articles table
            result = db.supabase.table('articles').select('id').eq('url', article_url).execute()
            if not result.data:
                return jsonify({'error': 'Article not found'}), 404
            article_id = result.data[0]['id']
        else:
            # For SQLite, use direct connection
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM articles WHERE url = ?', (article_url,))
            article = cursor.fetchone()
            conn.close()
            
            if not article:
                return jsonify({'error': 'Article not found'}), 404
            article_id = article[0]
        
        # Add to reading history
        db.add_reading_history(current_username, article_id, action)
        
        return jsonify({
            'message': f'Article marked as {action}',
            'article_url': article_url,
            'action': action
        }), 200
        
    except Exception as e:
        logger.error(f"Error marking article as read: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/preferences', methods=['GET'])
@token_required
def get_user_preferences(current_user_id, current_username):
    """Get current user's preferences"""
    try:
        preferences = db.get_user_preferences_with_ids(current_username)
        
        preferences_data = []
        for pref_id, description, weight in preferences:
            preferences_data.append({
                'id': pref_id,
                'description': description,
                'weight': weight
            })
        
        return jsonify({
            'preferences': preferences_data,
            'username': current_username
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/preferences', methods=['POST'])
@token_required
def add_user_preference(current_user_id, current_username):
    """Add a new preference for the current user"""
    try:
        data = request.get_json()
        
        if not data or not data.get('description'):
            return jsonify({'error': 'description is required'}), 400
        
        description = data['description'].strip()
        weight = data.get('weight', 1.0)
        
        if not description:
            return jsonify({'error': 'description cannot be empty'}), 400
        
        db.add_user_preference_with_embedding(current_username, description, weight)
        
        return jsonify({
            'message': 'Preference added successfully',
            'description': description,
            'weight': weight
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding user preference: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/preferences/<int:preference_id>', methods=['PUT'])
@token_required
def update_user_preference(current_user_id, current_username, preference_id):
    """Update an existing preference for the current user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        if use_supabase:
            # For Supabase, use the database method
            description = data.get('description')
            weight = data.get('weight')
            
            # Check if preference belongs to current user
            user = db.get_user_by_username(current_username)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Get existing preference to check ownership
            pref_result = db.supabase.table('user_preferences').select('*').eq('id', preference_id).eq('user_id', user['id']).execute()
            if not pref_result.data:
                return jsonify({'error': 'Preference not found or access denied'}), 404
            
            existing_pref = pref_result.data[0]
            
            # Use existing values if not provided
            if description is None:
                description = existing_pref['description']
            else:
                description = description.strip()
                if not description:
                    return jsonify({'error': 'description cannot be empty'}), 400
            
            if weight is None:
                weight = existing_pref['weight']
            
            # Generate new embedding and update
            embedding = db.embedding_service.create_preference_embedding(description)
            
            update_data = {
                'description': description,
                'weight': weight,
                'embedding': db.embedding_service.serialize_embedding(embedding)
            }
            
            db.supabase.table('user_preferences').update(update_data).eq('id', preference_id).execute()
            
        else:
            # For SQLite, use direct connection
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, description, weight FROM user_preferences 
                WHERE id = ? AND user_id = ?
            ''', (preference_id, current_user_id))
            
            existing_pref = cursor.fetchone()
            if not existing_pref:
                conn.close()
                return jsonify({'error': 'Preference not found or access denied'}), 404
            
            # Get updated values or keep existing ones
            description = data.get('description')
            weight = data.get('weight', existing_pref[2])
            
            if description is None:
                # Keep existing description if not provided
                description = existing_pref[1]
            else:
                description = description.strip()
                if not description:
                    conn.close()
                    return jsonify({'error': 'description cannot be empty'}), 400
            
            # Generate new embedding
            embedding = db.embedding_service.create_preference_embedding(description)
            
            # Update preference
            cursor.execute('''
                UPDATE user_preferences 
                SET description = ?, weight = ?, embedding = ?
                WHERE id = ? AND user_id = ?
            ''', (
                description,
                weight,
                db.embedding_service.serialize_embedding(embedding),
                preference_id,
                current_user_id
            ))
            
            conn.commit()
            conn.close()
        
        return jsonify({
            'message': 'Preference updated successfully',
            'preference_id': preference_id,
            'description': description,
            'weight': weight
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating user preference: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/preferences/<int:preference_id>', methods=['DELETE'])
@token_required
def delete_user_preference(current_user_id, current_username, preference_id):
    """Delete a specific preference for the current user"""
    try:
        if use_supabase:
            # For Supabase
            user = db.get_user_by_username(current_username)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Check if preference exists and belongs to current user
            pref_result = db.supabase.table('user_preferences').select('description').eq('id', preference_id).eq('user_id', user['id']).execute()
            if not pref_result.data:
                return jsonify({'error': 'Preference not found or access denied'}), 404
            
            deleted_description = pref_result.data[0]['description']
            
            # Delete the preference
            db.supabase.table('user_preferences').delete().eq('id', preference_id).eq('user_id', user['id']).execute()
            
        else:
            # For SQLite
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            
            # Check if preference exists and belongs to current user
            cursor.execute('''
                SELECT description FROM user_preferences 
                WHERE id = ? AND user_id = ?
            ''', (preference_id, current_user_id))
            
            existing_pref = cursor.fetchone()
            if not existing_pref:
                conn.close()
                return jsonify({'error': 'Preference not found or access denied'}), 404
            
            deleted_description = existing_pref[0]
            
            # Delete the preference
            cursor.execute('''
                DELETE FROM user_preferences 
                WHERE id = ? AND user_id = ?
            ''', (preference_id, current_user_id))
            
            conn.commit()
            conn.close()
        
        return jsonify({
            'message': 'Preference deleted successfully',
            'preference_id': preference_id,
            'deleted_description': deleted_description
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting user preference: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/preferences/clear', methods=['DELETE'])
@token_required
def clear_all_user_preferences(current_user_id, current_username):
    """Clear all preferences for the current user"""
    try:
        if use_supabase:
            # For Supabase
            user = db.get_user_by_username(current_username)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Count existing preferences
            count_result = db.supabase.table('user_preferences').select('id', count='exact').eq('user_id', user['id']).execute()
            count = count_result.count
            
            if count == 0:
                return jsonify({'message': 'No preferences to clear'}), 200
            
            # Delete all preferences for user
            db.supabase.table('user_preferences').delete().eq('user_id', user['id']).execute()
            
        else:
            # For SQLite
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            
            # Count existing preferences
            cursor.execute('SELECT COUNT(*) FROM user_preferences WHERE user_id = ?', (current_user_id,))
            count = cursor.fetchone()[0]
            
            if count == 0:
                conn.close()
                return jsonify({'message': 'No preferences to clear'}), 200
            
            # Delete all preferences for user
            cursor.execute('DELETE FROM user_preferences WHERE user_id = ?', (current_user_id,))
            conn.commit()
            conn.close()
        
        return jsonify({
            'message': f'All {count} preferences cleared successfully',
            'cleared_count': count
        }), 200
        
    except Exception as e:
        logger.error(f"Error clearing user preferences: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/account', methods=['DELETE'])
@token_required
def delete_user_account(current_user_id, current_username):
    """Delete the current user's account"""
    try:
        # Delete user and all related data
        success = db.delete_user(current_username, confirm=True)
        
        if success:
            return jsonify({
                'message': 'User account deleted successfully',
                'username': current_username
            }), 200
        else:
            return jsonify({'error': 'Failed to delete user account'}), 500
            
    except Exception as e:
        logger.error(f"Error deleting user account: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/articles/latest', methods=['GET'])
@token_required
def get_latest_articles(current_user_id, current_username):
    """Get latest articles (non-personalized)"""
    try:
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 100)  # Cap at 100 articles
        
        articles = db.get_latest_articles(limit)
        
        articles_data = []
        for article in articles:
            articles_data.append({
                'title': article.title,
                'url': article.url,
                'description': article.description,
                'published_date': article.published_date.isoformat() if article.published_date else None,
                'source': article.source,
                'category': article.category
            })
        
        return jsonify({
            'articles': articles_data,
            'total': len(articles_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting latest articles: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/scrape', methods=['POST'])
@token_required
def trigger_scrape(current_user_id, current_username):
    """Trigger a news scrape (admin functionality)"""
    try:
        results = scraper.scrape_all_feeds()
        
        total_new = sum(results.values())
        
        return jsonify({
            'message': 'Scrape completed successfully',
            'results': results,
            'total_new_articles': total_new,
            'total_articles_in_db': db.get_total_articles() if use_supabase else db.get_article_count()
        }), 200
        
    except Exception as e:
        logger.error(f"Error during scrape: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/reading-history', methods=['GET'])
@token_required
def get_reading_history(current_user_id, current_username):
    """Get reading history for the current user"""
    try:
        if use_supabase:
            # For Supabase
            user = db.get_user_by_username(current_username)
            if not user:
                return jsonify({'reading_history': [], 'total': 0}), 200
            
            # Get reading history with article details
            result = db.supabase.table('reading_history').select('''
                action, timestamp,
                articles (
                    title, url, source
                )
            ''').eq('user_id', user['id']).order('timestamp', desc=True).limit(100).execute()
            
            history = []
            for row in result.data:
                if row['articles']:
                    article_data = row['articles']
                    history.append({
                        'title': article_data['title'],
                        'url': article_data['url'],
                        'source': article_data['source'],
                        'action': row['action'],
                        'timestamp': row['timestamp']
                    })
            
        else:
            # For SQLite
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT a.title, a.url, a.source, rh.action, rh.timestamp
                FROM reading_history rh
                JOIN articles a ON rh.article_id = a.id
                WHERE rh.user_id = ?
                ORDER BY rh.timestamp DESC
                LIMIT 100
            ''', (current_user_id,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'title': row[0],
                    'url': row[1],
                    'source': row[2],
                    'action': row[3],
                    'timestamp': row[4]
                })
            
            conn.close()
        
        return jsonify({
            'reading_history': history,
            'total': len(history)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting reading history: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/scheduler/status', methods=['GET'])
@token_required
def get_scheduler_status(current_user_id, current_username):
    """Get current scheduler status"""
    try:
        scheduler = get_scheduler()
        status = scheduler.get_scheduler_status()
        
        # Convert datetime objects to strings for JSON serialization
        if status['next_run_time']:
            status['next_run_time'] = status['next_run_time'].isoformat()
        
        for job in status['jobs']:
            if job['next_run_time']:
                job['next_run_time'] = job['next_run_time'].isoformat()
        
        return jsonify({
            'scheduler_status': status,
            'message': 'Articles are automatically scraped every 2 hours' if status['is_running'] else 'Scheduler is not running'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

if __name__ == '__main__':
    # Run the Flask development server
    app.run(debug=True, host='0.0.0.0', port=5002)