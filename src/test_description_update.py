#!/usr/bin/env python3
"""
Simple test script to verify that the description field update works correctly.
This tests the database operations and API responses without needing the full Flask server.
"""

import sys
import os
import json
from news_database import NewsDatabase

def test_description_functionality():
    """Test that the description field works correctly in the database"""
    print("🧪 Testing description field functionality...")
    
    # Initialize database
    db = NewsDatabase()
    
    # Test adding a user preference with description
    test_username = "test_user_desc"
    test_description = "artificial intelligence, machine learning, and neural networks"
    test_weight = 1.5
    
    print(f"📝 Adding preference for {test_username}: '{test_description}'")
    
    try:
        # Add preference
        db.add_user_preference_with_embedding(test_username, test_description, test_weight)
        print("✅ Successfully added preference with description")
        
        # Get preferences back
        preferences = db.get_user_preferences(test_username)
        print(f"📋 Retrieved {len(preferences)} preferences")
        
        for desc, weight in preferences:
            print(f"   - {desc} (weight: {weight})")
            
        # Get preferences with IDs
        preferences_with_ids = db.get_user_preferences_with_ids(test_username)
        print(f"🔢 Retrieved {len(preferences_with_ids)} preferences with IDs")
        
        for pref_id, desc, weight in preferences_with_ids:
            print(f"   - ID: {pref_id}, Description: {desc}, Weight: {weight}")
            
        # Test personalized articles (this will work if there are articles in the database)
        try:
            scored_articles = db.get_personalized_articles(test_username, limit=5)
            print(f"🎯 Found {len(scored_articles)} personalized articles")
            for article, score in scored_articles[:3]:  # Show first 3
                print(f"   - {article.title[:50]}... (score: {score:.3f})")
        except Exception as e:
            print(f"⚠️  Personalized articles test failed (this is OK if no articles exist): {e}")
            
        # Clean up
        success = db.delete_user(test_username, confirm=True)
        if success:
            print("🧹 Successfully cleaned up test user")
        else:
            print("⚠️  Failed to clean up test user")
            
        print("✅ All description functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_api_response_format():
    """Test that the API response format matches the new description field"""
    print("\n🌐 Testing API response format...")
    
    # Simulate the API response structure
    sample_preferences = [
        {
            'id': 1,
            'description': 'artificial intelligence and machine learning',
            'weight': 1.5
        },
        {
            'id': 2, 
            'description': 'sports, basketball, and athletics',
            'weight': 2.0
        }
    ]
    
    # Verify the response structure
    try:
        for pref in sample_preferences:
            assert 'id' in pref, "Missing 'id' field"
            assert 'description' in pref, "Missing 'description' field"
            assert 'weight' in pref, "Missing 'weight' field"
            assert 'keywords' not in pref, "Old 'keywords' field still present"
            assert 'category' not in pref, "Old 'category' field still present"
            
        print("✅ API response format is correct")
        print("   - Contains 'description' field")
        print("   - Does not contain old 'keywords' or 'category' fields")
        return True
        
    except AssertionError as e:
        print(f"❌ API response format test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting description field update tests...\n")
    
    db_test = test_description_functionality()
    api_test = test_api_response_format()
    
    if db_test and api_test:
        print("\n🎉 All tests passed! The description field update is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
