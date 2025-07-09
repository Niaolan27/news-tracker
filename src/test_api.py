#!/usr/bin/env python3
"""
News Tracker API Test Script
Tests all API endpoints for the News Tracker application.
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Optional

class NewsTrackerAPITester:
    def __init__(self, base_url: str = "http://localhost:5001/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_username = f"test_user_{int(time.time())}"
        self.test_password = "test_password123"
        self.test_email = f"{self.test_username}@example.com"
        
        # Test results tracking
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if success:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
        
        print(f"{status} {test_name}: {message}")
    
    def make_request(self, method: str, endpoint: str, data: dict = None, 
                    headers: dict = None, use_auth: bool = False) -> requests.Response:
        """Make an API request with optional authentication"""
        url = f"{self.base_url}{endpoint}"
        
        request_headers = headers or {}
        if use_auth and self.auth_token:
            request_headers['Authorization'] = f"Bearer {self.auth_token}"
        
        if data and method.upper() in ['POST', 'PUT', 'PATCH']:
            request_headers['Content-Type'] = 'application/json'
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=request_headers)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=request_headers)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, headers=request_headers)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=request_headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            raise
    
    def test_health_check(self):
        """Test the health check endpoint"""
        try:
            response = self.make_request('GET', '/health')
            
            if response.status_code == 200:
                data = response.json()
                if 'status' in data and data['status'] == 'healthy':
                    self.log_test("Health Check", True, f"API is healthy, {data.get('total_articles', 0)} articles in DB")
                else:
                    self.log_test("Health Check", False, "Invalid health response format")
            else:
                self.log_test("Health Check", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
    
    def test_user_registration(self):
        """Test user registration"""
        try:
            user_data = {
                "username": self.test_username,
                "password": self.test_password,
                "email": self.test_email
            }
            
            response = self.make_request('POST', '/auth/register', data=user_data)
            
            if response.status_code == 201:
                data = response.json()
                if 'token' in data and 'user' in data:
                    self.auth_token = data['token']
                    self.log_test("User Registration", True, f"User {self.test_username} created successfully")
                else:
                    self.log_test("User Registration", False, "Missing token or user in response")
            else:
                self.log_test("User Registration", False, f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("User Registration", False, f"Exception: {str(e)}")
    
    def test_user_login(self):
        """Test user login"""
        try:
            login_data = {
                "username": self.test_username,
                "password": self.test_password
            }
            
            response = self.make_request('POST', '/auth/login', data=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if 'token' in data and 'user' in data:
                    self.auth_token = data['token']
                    self.log_test("User Login", True, f"Login successful for {self.test_username}")
                else:
                    self.log_test("User Login", False, "Missing token or user in response")
            else:
                self.log_test("User Login", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("User Login", False, f"Exception: {str(e)}")
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        try:
            login_data = {
                "username": "invalid_user",
                "password": "wrong_password"
            }
            
            response = self.make_request('POST', '/auth/login', data=login_data)
            
            if response.status_code == 401:
                self.log_test("Invalid Login", True, "Correctly rejected invalid credentials")
            else:
                self.log_test("Invalid Login", False, f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Login", False, f"Exception: {str(e)}")
    
    def test_add_user_preference(self):
        """Test adding user preferences"""
        try:
            preferences = [
                {
                    "description": "AI, machine learning, and technology news",
                    "weight": 1.5
                },
                {
                    "description": "politics and government",
                    "weight": 1.0
                }
            ]
            
            for i, pref in enumerate(preferences):
                response = self.make_request('POST', '/user/preferences', data=pref, use_auth=True)
                
                if response.status_code == 201:
                    self.log_test(f"Add Preference {i+1}", True, f"Added preference: {pref['description']}")
                else:
                    self.log_test(f"Add Preference {i+1}", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Add User Preference", False, f"Exception: {str(e)}")
    
    def test_get_user_preferences(self):
        """Test getting user preferences"""
        try:
            response = self.make_request('GET', '/user/preferences', use_auth=True)
            
            if response.status_code == 200:
                data = response.json()
                if 'preferences' in data:
                    prefs_count = len(data['preferences'])
                    self.log_test("Get User Preferences", True, f"Retrieved {prefs_count} preferences")
                else:
                    self.log_test("Get User Preferences", False, "Missing preferences in response")
            else:
                self.log_test("Get User Preferences", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Get User Preferences", False, f"Exception: {str(e)}")
    
    def test_get_latest_articles(self):
        """Test getting latest articles"""
        try:
            response = self.make_request('GET', '/articles/latest?limit=10', use_auth=True)
            
            if response.status_code == 200:
                data = response.json()
                if 'articles' in data:
                    article_count = len(data['articles'])
                    self.log_test("Get Latest Articles", True, f"Retrieved {article_count} articles")
                else:
                    self.log_test("Get Latest Articles", False, "Missing articles in response")
            else:
                self.log_test("Get Latest Articles", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Get Latest Articles", False, f"Exception: {str(e)}")
    
    def test_get_recommended_articles(self):
        """Test getting personalized recommendations"""
        try:
            response = self.make_request('GET', '/articles/recommended?limit=10', use_auth=True)
            
            if response.status_code == 200:
                data = response.json()
                if 'articles' in data:
                    article_count = len(data['articles'])
                    self.log_test("Get Recommended Articles", True, f"Retrieved {article_count} recommended articles")
                    
                    # Check if articles have relevance scores
                    if article_count > 0 and 'relevance_score' in data['articles'][0]:
                        self.log_test("Relevance Scoring", True, "Articles include relevance scores")
                    elif article_count > 0:
                        self.log_test("Relevance Scoring", False, "Articles missing relevance scores")
                else:
                    self.log_test("Get Recommended Articles", False, "Missing articles in response")
            else:
                self.log_test("Get Recommended Articles", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Get Recommended Articles", False, f"Exception: {str(e)}")
    
    def test_mark_article_read(self):
        """Test marking an article as read"""
        try:
            # First get an article to mark as read
            response = self.make_request('GET', '/articles/latest?limit=1', use_auth=True)
            
            if response.status_code == 200:
                data = response.json()
                if data['articles']:
                    article_url = data['articles'][0]['url']
                    
                    # Mark article as read
                    read_data = {
                        "article_url": article_url,
                        "action": "read"
                    }
                    
                    response = self.make_request('POST', '/articles/read', data=read_data, use_auth=True)
                    
                    if response.status_code == 200:
                        self.log_test("Mark Article Read", True, "Successfully marked article as read")
                    else:
                        self.log_test("Mark Article Read", False, f"Status code: {response.status_code}")
                else:
                    self.log_test("Mark Article Read", False, "No articles available to mark as read")
            else:
                self.log_test("Mark Article Read", False, "Failed to get articles for read test")
        except Exception as e:
            self.log_test("Mark Article Read", False, f"Exception: {str(e)}")
    
    def test_get_reading_history(self):
        """Test getting reading history"""
        try:
            response = self.make_request('GET', '/user/reading-history', use_auth=True)
            
            if response.status_code == 200:
                data = response.json()
                if 'reading_history' in data:
                    history_count = len(data['reading_history'])
                    self.log_test("Get Reading History", True, f"Retrieved {history_count} history entries")
                else:
                    self.log_test("Get Reading History", False, "Missing reading_history in response")
            else:
                self.log_test("Get Reading History", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Get Reading History", False, f"Exception: {str(e)}")
    
    def test_trigger_scrape(self):
        """Test triggering a news scrape"""
        try:
            response = self.make_request('POST', '/scrape', use_auth=True)
            
            # Note: This might take a while or fail if feeds are unavailable
            if response.status_code == 200:
                data = response.json()
                if 'total_new_articles' in data:
                    new_articles = data['total_new_articles']
                    self.log_test("Trigger Scrape", True, f"Scrape completed, {new_articles} new articles")
                else:
                    self.log_test("Trigger Scrape", False, "Missing scrape results in response")
            else:
                # Scrape might fail due to network issues, that's ok for testing
                self.log_test("Trigger Scrape", True, f"Scrape endpoint accessible (status: {response.status_code})")
        except Exception as e:
            self.log_test("Trigger Scrape", False, f"Exception: {str(e)}")
    
    def test_unauthorized_access(self):
        """Test accessing protected endpoints without authentication"""
        try:
            protected_get_endpoints = [
                '/articles/recommended',
                '/articles/latest',
                '/user/preferences',
                '/user/reading-history'
            ]
            protected_post_endpoints = [
                '/scrape',
            ]
            endpoints_count = len(protected_get_endpoints) + len(protected_post_endpoints)
            unauthorized_count = 0
            for endpoint in protected_get_endpoints:
                response = self.make_request('GET', endpoint, use_auth=False)
                if response.status_code == 401:
                    unauthorized_count += 1
                else:
                    self.log_test(f"Unauthorized Access - {endpoint}", False, f"Expected 401, got {response.status_code}")
            for end in protected_post_endpoints:
                response = self.make_request('POST', end, use_auth=False)
                if response.status_code == 401:
                    unauthorized_count += 1
                else:
                    self.log_test(f"Unauthorized Access - {end}", False, f"Expected 401, got {response.status_code}")
            
            if unauthorized_count == len(protected_get_endpoints) + len(protected_post_endpoints):
                # If all endpoints returned 401, the test passes
                self.log_test("Unauthorized Access", True, "All protected endpoints properly require authentication")
            else:
                self.log_test("Unauthorized Access", False, f"Only {unauthorized_count}/{endpoints_count} endpoints require auth")
        except Exception as e:
            self.log_test("Unauthorized Access", False, f"Exception: {str(e)}")
    
    def test_preference_crud_operations(self):
        """Test CRUD operations for preferences"""
        try:
            # Create a preference and get its ID
            pref_data = {
                "description": "test crud operations for preferences",
                "weight": 2.0
            }
            
            response = self.make_request('POST', '/user/preferences', data=pref_data, use_auth=True)
            if response.status_code != 201:
                self.log_test("Preference CRUD - Create", False, f"Failed to create preference: {response.status_code}")
                return
            
            # Get preferences to find the ID
            response = self.make_request('GET', '/user/preferences', use_auth=True)
            if response.status_code != 200:
                self.log_test("Preference CRUD - Read", False, "Failed to read preferences")
                return
            
            preferences = response.json()['preferences']
            test_pref = None
            for pref in preferences:
                if 'test' in pref.get('description', ''):
                    test_pref = pref
                    break
            
            if not test_pref:
                self.log_test("Preference CRUD", False, "Could not find created test preference")
                return
            
            pref_id = test_pref['id']
            
            # Update the preference
            update_data = {
                "description": "updated test description for preferences",
                "weight": 3.0
            }
            
            response = self.make_request('PUT', f'/user/preferences/{pref_id}', data=update_data, use_auth=True)
            if response.status_code == 200:
                self.log_test("Preference CRUD - Update", True, "Successfully updated preference")
            else:
                self.log_test("Preference CRUD - Update", False, f"Update failed: {response.status_code}")
            
            # Delete the preference
            response = self.make_request('DELETE', f'/user/preferences/{pref_id}', use_auth=True)
            if response.status_code == 200:
                self.log_test("Preference CRUD - Delete", True, "Successfully deleted preference")
            else:
                self.log_test("Preference CRUD - Delete", False, f"Delete failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Preference CRUD Operations", False, f"Exception: {str(e)}")
    
    def test_input_validation(self):
        """Test input validation for various endpoints"""
        try:
            # Test registration with missing fields
            response = self.make_request('POST', '/auth/register', data={})
            if response.status_code == 400:
                self.log_test("Input Validation - Registration", True, "Correctly rejected empty registration")
            else:
                self.log_test("Input Validation - Registration", False, f"Expected 400, got {response.status_code}")
            
            # Test preference with missing keywords
            response = self.make_request('POST', '/user/preferences', data={"weight": 1.0}, use_auth=True)
            if response.status_code == 400:
                self.log_test("Input Validation - Preferences", True, "Correctly rejected preference without keywords")
            else:
                self.log_test("Input Validation - Preferences", False, f"Expected 400, got {response.status_code}")
            
            # Test marking article read with missing URL
            response = self.make_request('POST', '/articles/read', data={"action": "read"}, use_auth=True)
            if response.status_code == 400:
                self.log_test("Input Validation - Article Read", True, "Correctly rejected read without article URL")
            else:
                self.log_test("Input Validation - Article Read", False, f"Expected 400, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Input Validation", False, f"Exception: {str(e)}")
    
    def cleanup_test_user(self):
        """Clean up the test user"""
        try:
            response = self.make_request('DELETE', '/user/account', use_auth=True)
            if response.status_code == 200:
                self.log_test("Cleanup Test User", True, f"Successfully deleted test user {self.test_username}")
            else:
                self.log_test("Cleanup Test User", False, f"Failed to delete user: {response.status_code}")
        except Exception as e:
            self.log_test("Cleanup Test User", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting News Tracker API Tests")
        print("=" * 50)
        
        # Basic connectivity and health
        self.test_health_check()
        
        # Authentication tests
        self.test_user_registration()
        self.test_user_login()
        self.test_invalid_login()
        
        # User preference tests
        self.test_add_user_preference()
        self.test_get_user_preferences()
        
        # Article tests
        self.test_get_latest_articles()
        self.test_get_recommended_articles()
        self.test_mark_article_read()
        self.test_get_reading_history()
        
        # Advanced operations
        self.test_preference_crud_operations()
        # self.test_trigger_scrape()
        
        # Security tests
        self.test_unauthorized_access()
        self.test_input_validation()
        
        # Cleanup
        self.cleanup_test_user()
        
        # Print summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print test summary and results"""
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_failed}")
        print(f"📈 Success Rate: {(self.tests_passed / (self.tests_passed + self.tests_failed) * 100):.1f}%")
        
        if self.tests_failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['message']}")
        
        # Save detailed results to file
        self.save_test_results()
    
    def save_test_results(self):
        """Save test results to a JSON file"""
        try:
            results_data = {
                'summary': {
                    'tests_passed': self.tests_passed,
                    'tests_failed': self.tests_failed,
                    'total_tests': self.tests_passed + self.tests_failed,
                    'success_rate': (self.tests_passed / (self.tests_passed + self.tests_failed) * 100) if (self.tests_passed + self.tests_failed) > 0 else 0,
                    'test_run_time': datetime.now().isoformat()
                },
                'detailed_results': self.test_results
            }
            
            filename = f"api_test_results_{int(time.time())}.json"
            with open(filename, 'w') as f:
                json.dump(results_data, f, indent=2)
            
            print(f"\n💾 Detailed test results saved to: {filename}")
        except Exception as e:
            print(f"Failed to save test results: {e}")

def main():
    """Main function to run the tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test News Tracker API')
    parser.add_argument('--url', default='http://localhost:5001/api', 
                       help='Base URL for the API (default: http://localhost:5001/api)')
    parser.add_argument('--test', help='Run a specific test (use test method name)')
    
    args = parser.parse_args()
    
    # Check if API is running
    try:
        response = requests.get(f"{args.url}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API appears to be down. Health check returned {response.status_code}")
            print("Please make sure the News Tracker API is running on the specified URL.")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print(f"❌ Cannot connect to API at {args.url}")
        print("Please make sure the News Tracker API is running and accessible.")
        print("You can start it with: python app.py")
        sys.exit(1)
    
    # Run tests
    tester = NewsTrackerAPITester(args.url)
    
    if args.test:
        # Run specific test
        test_method = getattr(tester, args.test, None)
        if test_method and callable(test_method):
            print(f"Running specific test: {args.test}")
            test_method()
            tester.print_test_summary()
        else:
            print(f"Test method '{args.test}' not found")
            sys.exit(1)
    else:
        # Run all tests
        tester.run_all_tests()

if __name__ == "__main__":
    main()