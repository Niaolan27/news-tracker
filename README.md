# News Tracker

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
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
Provide step-by-step instructions on how to install and set up the project.

## Usage
Explain how to use the project, including examples if applicable.

To perform a web scrape
`python main.py scrape`

To add preferences for different users
```# Add preferences for different users
python main.py add-preference --username "alice" --keywords "AI,machine learning" --weight 1.5
python main.py add-preference --username "bob" --keywords "sports,basketball" --weight 2.0

# Get personalized recommendations for specific users
python main.py personalized --username "alice" --limit 10
python main.py personalized --username "bob" --limit 15

# List all users in the system
python main.py list-users

# View a user's preferences
python main.py user-preferences --username "alice"
```