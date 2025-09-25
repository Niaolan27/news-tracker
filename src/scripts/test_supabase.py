# test_supabase_connection.py
from dotenv import load_dotenv
import os
from supabase import create_client

import requests 

load_dotenv()

def test_supabase_connection():
    try:
        # Get credentials
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_PUBLISHABLE_KEY')
        # print(repr(url), repr(key))
        # url = "https://ovfrtiqldlhvcjgpicpr.supabase.co" 
        # headers = {"apikey": key} 
        # r = requests.get(url, headers=headers) 
        # print(r.status_code, r.text)
        
        # print(f"Testing connection to: {url}")
        # print(f"Using key: {key[:20]}..." if key else "No key found")
        
        # # Create client
        supabase = create_client(url, key)
        
        # Test with a simple query
        result = supabase.table('users').select('count').execute()
        print(f"✅ Connection successful! Found {result.count} users")
        
        # Test articles table
        articles_result = supabase.table('articles').select('count').execute()
        print(f"✅ Articles table accessible! Found {articles_result.count} articles")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_supabase_connection()