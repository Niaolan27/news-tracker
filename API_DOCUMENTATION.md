# News Tracker RESTful API Documentation

## Base URL
```
http://localhost:5000/api
```

## Authentication
The API uses JWT (JSON Web Token) for authentication. After login or registration, include the token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### 1. Health Check
**GET** `/health`
- No authentication required
- Returns API status and basic statistics

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-12T10:30:00",
  "total_articles": 1250
}
```

### 2. User Registration
**POST** `/auth/register`
- Create a new user account
- No authentication required

**Request Body:**
```json
{
  "username": "alice",
  "password": "password123",
  "email": "alice@example.com"  // optional
}
```

**Response:**
```json
{
  "message": "User created successfully",
  "user": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com"
  },
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 3. User Login
**POST** `/auth/login`
- Authenticate user and get JWT token
- No authentication required

**Request Body:**
```json
{
  "username": "alice",
  "password": "password123"
}
```

**Response:**
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com"
  },
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 4. Get Recommended Articles
**GET** `/articles/recommended?limit=20`
- Get personalized article recommendations based on user preferences
- Requires authentication

**Query Parameters:**
- `limit` (optional): Number of articles to return (default: 20, max: 100)

**Response:**
```json
{
  "articles": [
    {
      "title": "Latest AI Breakthrough in Machine Learning",
      "url": "https://example.com/ai-news",
      "description": "Researchers have developed a new...",
      "published_date": "2025-06-12T08:30:00",
      "source": "Tech News",
      "category": "Technology",
      "relevance_score": 0.85
    }
  ],
  "total": 20,
  "username": "alice"
}
```

### 5. Mark Article as Read
**POST** `/articles/read`
- Update reading history when user interacts with an article
- Requires authentication

**Request Body:**
```json
{
  "article_url": "https://example.com/ai-news",
  "action": "read"  // options: "read", "clicked", "dismissed"
}
```

**Response:**
```json
{
  "message": "Article marked as read",
  "article_url": "https://example.com/ai-news",
  "action": "read"
}
```

### 6. Get User Preferences
**GET** `/user/preferences`
- Get current user's preferences
- Requires authentication

**Response:**
```json
{
  "preferences": [
    {
      "id": 1,
      "description": "AI, machine learning, and neural networks",
      "weight": 1.5
    }
  ],
  "username": "alice"
}
```

### 7. Add User Preference
**POST** `/user/preferences`
- Add new preference for personalization
- Requires authentication

**Request Body:**
```json
{
  "description": "AI, machine learning, and neural networks",
  "weight": 1.5                                      // optional, default: 1.0
}
```

**Response:**
```json
{
  "message": "Preference added successfully",
  "description": "AI, machine learning, and neural networks",
  "weight": 1.5
}
```

### 8. Delete User Account
**DELETE** `/user/account`
- Permanently delete the current user's account and all associated data
- Requires authentication

**Response:**
```json
{
  "message": "User account deleted successfully",
  "username": "alice"
}
```

### 9. Get Latest Articles (Non-personalized)
**GET** `/articles/latest?limit=20`
- Get latest articles without personalization
- Requires authentication

**Query Parameters:**
- `limit` (optional): Number of articles to return (default: 20, max: 100)

**Response:**
```json
{
  "articles": [
    {
      "title": "Breaking News Today",
      "url": "https://example.com/breaking-news",
      "description": "Important news happening...",
      "published_date": "2025-06-12T09:00:00",
      "source": "News Source",
      "category": "World"
    }
  ],
  "total": 20
}
```

### 10. Get Reading History
**GET** `/user/reading-history`
- Get user's reading history
- Requires authentication

**Response:**
```json
{
  "reading_history": [
    {
      "title": "Article Title",
      "url": "https://example.com/article",
      "source": "News Source",
      "action": "read",
      "timestamp": "2025-06-12T08:30:00"
    }
  ],
  "total": 50
}
```

### 11. Trigger News Scrape
**POST** `/scrape`
- Manually trigger news scraping from all RSS feeds
- Requires authentication
- This can take a few minutes to complete

**Response:**
```json
{
  "message": "Scrape completed successfully",
  "results": {
    "BBC News": 15,
    "CNN": 12,
    "Reuters": 8
  },
  "total_new_articles": 35,
  "total_articles_in_db": 1285
}
```

## Error Responses

All endpoints may return these error responses:

**400 Bad Request:**
```json
{
  "error": "Username and password are required"
}
```

**401 Unauthorized:**
```json
{
  "error": "Token is missing"
}
```

**404 Not Found:**
```json
{
  "error": "Endpoint not found"
}
```

**409 Conflict:**
```json
{
  "error": "Username already exists"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error"
}
```

## Usage Examples

### Using curl

1. **Register a new user:**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password123", "email": "alice@example.com"}'
```

2. **Login:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password123"}'
```

3. **Get recommendations (with token):**
```bash
curl -X GET http://localhost:5000/api/articles/recommended?limit=10 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

4. **Add preference:**
```bash
curl -X POST http://localhost:5000/api/user/preferences \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"keywords": "AI,technology", "weight": 1.5}'
```

5. **Mark article as read:**
```bash
curl -X POST http://localhost:5000/api/articles/read \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"article_url": "https://example.com/article", "action": "read"}'
```

### Using JavaScript (fetch)

```javascript
// Login and get token
const loginResponse = await fetch('http://localhost:5000/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'alice',
    password: 'password123'
  })
});

const loginData = await loginResponse.json();
const token = loginData.token;

// Get recommendations
const recsResponse = await fetch('http://localhost:5000/api/articles/recommended?limit=20', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const recommendations = await recsResponse.json();
console.log(recommendations);
```

## Running the API

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the API:**
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## Security Notes

- Change the `SECRET_KEY` in `app.py` for production use
- JWT tokens expire after 24 hours
- Passwords are hashed using Werkzeug's security functions
- The API includes CORS support for web browser access
- All user data is stored locally in the SQLite database