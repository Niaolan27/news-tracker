# News Tracker

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Technology](#technology)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Usage](#api-usage)
- [Migration & Deployment](#migration--deployment)
- [AI Features](#ai-features)
- [Contributing](#contributing)
- [License](#license)

## Introduction
News Tracker is your personalized AI-powered news assistant that scrapes, analyzes, and summarizes daily news based on your interests. Using advanced machine learning techniques, it learns from your reading habits and preferences to deliver the most relevant articles with intelligent summaries.

This is an intelligent way to stay updated with current affairs that matter to you, with AI-generated insights and personalized recommendations.

## Features
- **Personalized Recommendations**: AI-powered article recommendations based on your preferences and reading history
- **Intelligent Summarization**: AI-generated summaries with key points and sentiment analysis  
- **Multi-source Aggregation**: Scrapes RSS feeds from various trusted news sources
- **Reading Analytics**: Tracks your reading patterns and preferences
- **Cross-platform**: Flutter mobile app with responsive web support
- **Real-time Updates**: Background scraping every 2 hours with automatic updates
- **Natural Language Preferences**: Describe your interests in plain English
- **Smart Content Analysis**: Full article content extraction and embedding-based matching

## Technology
**Backend:**
- **Python Flask API** with JWT authentication
- **PostgreSQL (Supabase)** for scalable cloud database storage
- **Sentence Transformers** for semantic article embeddings
- **RSS Feed Scraping** from major news sources
- **OpenAI/Hugging Face Models** for AI summarization
- **pgvector** extension for efficient similarity search
- **APScheduler** for automated news scraping

**Frontend:**
- **Flutter** for cross-platform mobile and web apps
- **Provider** state management
- **HTTP API integration** with JWT token handling

**AI/ML:**
- **Embedding-based similarity matching** for personalized recommendations
- **Vector database** with cosine similarity search
- **Natural language processing** for content analysis
- **Automated content extraction** from article URLs 

## Installation

### Prerequisites
- Python 3.8 or higher
- Flutter SDK 3.0+
- Git
- Supabase account (for production deployment)

### Backend Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd news-tracker
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   cd src
   pip install -r ../requirements.txt
   ```

### Flutter App Setup
1. Navigate to the Flutter project:
   ```bash
   cd news_tracker_flutter
   ```

2. Install Flutter dependencies:
   ```bash
   flutter pub get
   ```

3. Verify Flutter setup:
   ```bash
   flutter doctor
   ```

## Configuration

### Environment Variables
Create a `.env` file in the project root with the following variables:

```env
# Supabase Configuration (Production)
SUPABASE_URL=your-supabase-project-url
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# AI Configuration (Optional)
OPENAI_API_KEY=your-openai-api-key-here
ENABLE_AI_SUMMARIES=true

# Flask Configuration
SECRET_KEY=your-secret-key-for-jwt-tokens
FLASK_ENV=development
```

### Database Setup
The application supports both SQLite (development) and Supabase (production):

**For Development (SQLite):**
- Database is automatically created as `src/news_tracker.db`
- No additional setup required

**For Production (Supabase):**
1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Run the SQL schema from the project documentation
3. Update your `.env` file with Supabase credentials
4. Use the migration script to transfer data from SQLite to Supabase

## Usage

### Running the Backend API Server
Start the Flask API server:
```bash
cd src
python app.py
```
The API will be available at `http://localhost:5002` (updated port)

### Running the Flutter App

#### Mobile/Desktop App
```bash
cd news_tracker_flutter
flutter run
```

Choose your target device:
- **iOS Simulator**: `flutter run -d "iPhone 15 Pro"`
- **Android Emulator**: `flutter run -d android`
- **Web Browser**: `flutter run -d chrome`
- **macOS Desktop**: `flutter run -d macos`

#### Development Features
- **Hot Reload**: Press `r` in terminal or save files in VS Code
- **Hot Restart**: Press `R` in terminal

### First Time Setup
1. **Configure environment** (create `.env` file with required credentials)
2. **Start the backend server** (required for the app to work)
3. **Launch the Flutter app**
4. **Register a new account** in the app
5. **Set your preferences** using natural language descriptions
6. **Browse AI-recommended articles** based on your interests
7. **Read AI-generated summaries** for quick insights

## API Usage

### Command Line Interface
For development and testing, you can use the command line interface:

#### Web Scraping
```bash
cd src
python main.py scrape
```

#### User Management
```bash
# Add preferences using natural language descriptions
python main.py add-preference --username "alice" --description "AI, machine learning, and technology news" --weight 1.5
python main.py add-preference --username "bob" --description "sports, basketball, and athletics" --weight 2.0

# Get personalized recommendations for specific users
python main.py personalized --username "alice" --limit 10
python main.py personalized --username "bob" --limit 15

# List all users in the system
python main.py list-users

# View a user's preferences
python main.py user-preferences --username "alice"

# Delete a user
python main.py delete-user --username "alice"
```

### REST API
The Flask API provides endpoints for:
- **User authentication**: `/api/auth/register`, `/api/auth/login`
- **Article recommendations**: `/api/articles/recommended`
- **User preferences**: `/api/user/preferences`
- **Article details**: `/api/articles/<id>` (with full content)
- **Search functionality**: `/api/articles/search`
- **Health monitoring**: `/api/health`
- **Manual scraping**: `/api/scrape` (admin)

See `API_DOCUMENTATION.md` for detailed API reference.

### Testing the API
```bash
# Test API health
curl -X GET http://localhost:5002/api/health

# Run automated API tests
cd src
python test_api.py
```

## Migration & Deployment

### SQLite to Supabase Migration
To migrate from local SQLite to Supabase cloud database:

1. **Set up Supabase project** and configure environment variables
2. **Run the migration script**:
   ```bash
   cd src
   python migrate_to_supabase.py
   ```
3. **Verify migration** with the check script:
   ```bash
   python check_migration.py
   ```

### Production Deployment
1. **Deploy backend** to services like Heroku, Railway, or DigitalOcean
2. **Update Flutter API endpoints** to use production URLs
3. **Build and deploy Flutter app**:
   ```bash
   # Web deployment
   flutter build web
   
   # Mobile app stores
   flutter build apk --release  # Android
   flutter build ios --release  # iOS
   ```

## AI Features

### Article Summarization
- **AI Models**: OpenAI GPT or Hugging Face transformers
- **Content Extraction**: Full article content scraping and analysis
- **Summary Generation**: Key points, sentiment analysis, and concise summaries
- **Supported Models**: 
  - `facebook/bart-large-cnn` (recommended)
  - `google/pegasus-newsroom` (news-optimized)
  - `sshleifer/distilbart-cnn-12-6` (lightweight)

### Personalization
- **Semantic Matching**: Vector embeddings for content similarity
- **Reading History**: Tracks user engagement and preferences
- **Natural Language Preferences**: Users describe interests in plain English
- **Adaptive Learning**: Recommendations improve over time

### Configuration
Enable AI features in your `.env` file:
```env
ENABLE_AI_SUMMARIES=true
OPENAI_API_KEY=your-key-here  # For OpenAI models
SUMMARIZER_MODEL=facebook/bart-large-cnn  # For Hugging Face models
USE_GPU=false  # Set to true if GPU available
```

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Flutter App   │    │   Flask API      │    │   Supabase      │
│                 │    │                  │    │   PostgreSQL    │
│ • Cross-platform│◄──►│ • JWT Auth       │◄──►│ • Vector DB     │
│ • State Mgmt    │    │ • Embeddings     │    │ • Row Level     │
│ • HTTP Client   │    │ • AI Integration │    │   Security      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌────────▼────────┐
                       │   AI Services   │
                       │                 │
                       │ • OpenAI        │
                       │ • Hugging Face  │
                       │ • Transformers  │
                       └─────────────────┘
```

## Project Structure

```
news-tracker/
├── src/                          # Backend Python code
│   ├── app.py                   # Flask API server (port 5002)
│   ├── news_database.py         # SQLite database (development)
│   ├── supabase_database.py     # Supabase database (production)
│   ├── news_scraper.py          # RSS feed scraping
│   ├── embedding_service.py     # AI embeddings and similarity
│   ├── scheduler.py             # Automated scraping (every 2 hours)
│   ├── main.py                  # CLI interface
│   ├── migrate_to_supabase.py   # Database migration script
│   └── test_api.py              # API testing
├── news_tracker_flutter/        # Flutter cross-platform app
│   ├── lib/
│   │   ├── main.dart           # App entry point
│   │   ├── services/           # API and business logic
│   │   ├── screens/            # UI screens
│   │   └── providers/          # State management
│   └── build/web/              # Web build output
├── requirements.txt             # Python dependencies
├── .env                        # Environment configuration
├── README.md                   # This file
└── API_DOCUMENTATION.md        # Detailed API docs
```

## Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Run tests**: `python src/test_api.py`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 for Python code
- Use meaningful commit messages
- Add tests for new features
- Update documentation as needed
- Ensure Flutter code follows Dart conventions

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: Report bugs and request features via GitHub Issues
- **Documentation**: See `API_DOCUMENTATION.md` for detailed API reference
- **Migration Help**: Use `check_migration.py` for database migration assistance

---

**News Tracker** - Stay informed with AI-powered personalized news recommendations 🚀