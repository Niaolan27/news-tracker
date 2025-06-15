# News Tracker

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Technology](#technology)
- [Installation](#installation)
- [Usage](#usage)
- [API Usage](#api-usage)
- [Contributing](#contributing)
- [License](#license)

## Introduction
News Tracker is your personalized assistant which reads and summarizes daily news for you. Based on your interests, News Tracker scrapes the Internet for the latest news and creates a summary of what might interest you. 

This is an easy way for you to stay updated with current affairs you care about. 

## Features
You will be presented with an interactive and simple summary of what you care about. 

The app scrapes RSS feeds from various news sources to stay updated with the latest happenings around the world. Based on your initial input and viewing history, the app learns your interests and selects the most relevant articles. 

## Technology
The news feeds are scraped using RSS feeds directly from the news sources. 

All data is currently stored in a sqlite database. 

Articles are represented as an embedding vector using Sentence Transformers. Likewise, your preferences are also represented as embedding vectors. This allows similarity matching to be done to find the most relevant articles for you. 

## Installation

### Prerequisites
- Python 3.8 or higher
- Flutter SDK
- Git

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
   pip install -r requirements.txt
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

## Usage

### Running the Backend API Server
Start the Flask API server:
```bash
python app.py
```
The API will be available at `http://localhost:5000`

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
1. **Start the backend server** (required for the app to work)
2. **Launch the Flutter app**
3. **Register a new account** in the app
4. **Set your preferences** for personalized news recommendations
5. **Browse recommended articles** based on your interests

## API Usage

### Command Line Interface
For development and testing, you can use the command line interface:

#### Web Scraping
```bash
python main.py scrape
```

#### User Management
```bash
# Add preferences for different users
python main.py add-preference --username "alice" --keywords "AI,machine learning" --weight 1.5
python main.py add-preference --username "bob" --keywords "sports,basketball" --weight 2.0

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
- User authentication (`/api/auth/register`, `/api/auth/login`)
- Article recommendations (`/api/articles/recommended`)
- User preferences (`/api/user/preferences`)
- Health check (`/api/health`)

See `API_DOCUMENTATION.md` for detailed API reference.

### Testing the API
```bash
# Test API health
curl -X GET http://localhost:5000/api/health

# Run automated API tests
python test_api.py
```