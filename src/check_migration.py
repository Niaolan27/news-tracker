#!/usr/bin/env python3
"""
Migration script to help transition from keywords/categories to description field.
This script is mainly for documentation purposes since the migration logic
is already built into the NewsDatabase class.
"""

import sqlite3
import os

def check_migration_status(db_path=None):
    """Check if the database has been migrated to use description field"""
    if db_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, "news_tracker.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the table has the new schema
        cursor.execute("PRAGMA table_info(user_preferences)")
        columns = [column[1] for column in cursor.fetchall()]
        
        has_description = 'description' in columns
        has_old_keyword = 'keyword' in columns
        has_old_category = 'category' in columns
        
        print(f"📊 Database migration status:")
        print(f"   - Has 'description' field: {'✅' if has_description else '❌'}")
        print(f"   - Has old 'keyword' field: {'⚠️' if has_old_keyword else '✅'}")
        print(f"   - Has old 'category' field: {'⚠️' if has_old_category else '✅'}")
        
        if has_description and not has_old_keyword and not has_old_category:
            print("✅ Database is fully migrated to use description field!")
            
            # Show some sample data
            cursor.execute("SELECT description, weight FROM user_preferences LIMIT 5")
            preferences = cursor.fetchall()
            
            if preferences:
                print(f"\n📋 Sample preferences (showing {len(preferences)} of total):")
                for desc, weight in preferences:
                    print(f"   - {desc[:60]}{'...' if len(desc) > 60 else ''} (weight: {weight})")
            else:
                print("\n📭 No user preferences found in database")
                
        elif has_description and (has_old_keyword or has_old_category):
            print("⚠️  Database is partially migrated - both old and new fields exist")
            print("   This is normal during transition. The new description field will be used.")
            
        else:
            print("❌ Database still uses old schema. Migration needed.")
            
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error checking database: {e}")
        return False
        
    finally:
        conn.close()

def show_migration_examples():
    """Show examples of how keywords/categories translate to descriptions"""
    print("\n📝 Migration Examples:")
    print("=" * 50)
    
    examples = [
        {
            "keywords": "AI,machine learning,neural networks",
            "categories": "Technology,Science",
            "description": "AI, machine learning, neural networks, and technology science news"
        },
        {
            "keywords": "basketball,NBA,sports",
            "categories": "Sports",
            "description": "basketball, NBA, and sports news"
        },
        {
            "keywords": "climate change,environment",
            "categories": "Environment,Politics",
            "description": "climate change, environment, environmental politics news"
        },
        {
            "keywords": "cybersecurity,privacy",
            "categories": None,
            "description": "cybersecurity and privacy news"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. Before (Keywords + Categories):")
        print(f"   Keywords: {example['keywords']}")
        print(f"   Categories: {example['categories'] or 'None'}")
        print(f"   After (Description):")
        print(f"   Description: {example['description']}")

if __name__ == "__main__":
    print("🔄 News Tracker - Description Field Migration Check")
    print("=" * 55)
    
    # Check current migration status
    migrated = check_migration_status()
    
    if migrated:
        # Show examples
        show_migration_examples()
        
        print("\n💡 Tips for writing good descriptions:")
        print("   • Use natural language to describe your interests")
        print("   • Be specific about topics you care about")
        print("   • Include relevant keywords naturally in sentences")
        print("   • Consider the context and domain of news you want")
        
        print("\n🚀 The migration is complete! Users can now add preferences using natural language descriptions.")
    else:
        print("\n❌ Migration check failed. Please ensure the database exists and is accessible.")
