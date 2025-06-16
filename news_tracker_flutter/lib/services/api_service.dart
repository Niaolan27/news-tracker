import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String baseUrl = 'https://1fdf-118-189-200-13.ngrok-free.app/api';
  String? _token;

  // Helper method to get common headers
  Map<String, String> _getHeaders({bool includeAuth = false}) {
    final headers = {
      'Content-Type': 'application/json',
      'ngrok-skip-browser-warning': 'true',
    };
    
    if (includeAuth && _token != null) {
      headers['Authorization'] = 'Bearer $_token';
    }
    
    return headers;
  }

  // Get stored token
  Future<String?> getToken() async {
    if (_token != null) return _token;
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString('auth_token');
    return _token;
  }

  // Store token
  Future<void> setToken(String token) async {
    _token = token;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('auth_token', token);
  }

  // Clear token
  Future<void> clearToken() async {
    _token = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
  }

  // Register user
  Future<AuthResponse> register(String username, String password, [String? email]) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: _getHeaders(),
      body: jsonEncode({
        'username': username,
        'password': password,
        if (email != null) 'email': email,
      }),
    );

    if (response.statusCode == 201) {
      final data = jsonDecode(response.body);
      await setToken(data['token']);
      return AuthResponse.fromJson(data);
    } else {
      final error = jsonDecode(response.body);
      throw ApiException(error['error'] ?? 'Registration failed');
    }
  }

  // Login user
  Future<AuthResponse> login(String username, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: _getHeaders(),
      body: jsonEncode({
        'username': username,
        'password': password,
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      await setToken(data['token']);
      return AuthResponse.fromJson(data);
    } else {
      final error = jsonDecode(response.body);
      throw ApiException(error['error'] ?? 'Login failed');
    }
  }

  // Get recommended articles
  Future<List<Article>> getRecommendedArticles([int limit = 20]) async {
    final token = await getToken();
    if (token == null) throw ApiException('Not authenticated');

    final response = await http.get(
      Uri.parse('$baseUrl/articles/recommended?limit=$limit'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
      },
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final articles = (data['articles'] as List)
          .map((article) => Article.fromJson(article))
          .toList();
      return articles;
    } else {
      final error = jsonDecode(response.body);
      throw ApiException(error['error'] ?? 'Failed to fetch articles');
    }
  }

  // Get user preferences
  Future<List<UserPreference>> getUserPreferences() async {
    final token = await getToken();
    if (token == null) throw ApiException('Not authenticated');

    final response = await http.get(
      Uri.parse('$baseUrl/user/preferences'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
      },
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final preferences = (data['preferences'] as List)
          .map((pref) => UserPreference.fromJson(pref))
          .toList();
      return preferences;
    } else {
      final error = jsonDecode(response.body);
      throw ApiException(error['error'] ?? 'Failed to fetch preferences');
    }
  }

  // Add user preference
  Future<void> addUserPreference(String keywords, [String? categories, double weight = 1.0]) async {
    final token = await getToken();
    if (token == null) throw ApiException('Not authenticated');

    final response = await http.post(
      Uri.parse('$baseUrl/user/preferences'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
      },
      body: jsonEncode({
        'keywords': keywords,
        if (categories != null) 'categories': categories,
        'weight': weight,
      }),
    );

    if (response.statusCode != 201) {
      final error = jsonDecode(response.body);
      throw ApiException(error['error'] ?? 'Failed to add preference');
    }
  }

  // Delete user preference
  Future<void> deleteUserPreference(int preferenceId) async {
    final token = await getToken();
    if (token == null) throw ApiException('Not authenticated');

    final response = await http.delete(
      Uri.parse('$baseUrl/user/preferences/$preferenceId'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
      },
    );

    if (response.statusCode != 200) {
      final error = jsonDecode(response.body);
      throw ApiException(error['error'] ?? 'Failed to delete preference');
    }
  }

  // Mark article as read
  Future<void> markArticleRead(String articleUrl, [String action = 'read']) async {
    final token = await getToken();
    if (token == null) throw ApiException('Not authenticated');

    final response = await http.post(
      Uri.parse('$baseUrl/articles/read'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
      },
      body: jsonEncode({
        'article_url': articleUrl,
        'action': action,
      }),
    );

    if (response.statusCode != 200) {
      final error = jsonDecode(response.body);
      throw ApiException(error['error'] ?? 'Failed to mark article as read');
    }
  }

  // Get reading history
  Future<ReadingHistoryResponse> getReadingHistory() async {
    final token = await getToken();
    if (token == null) throw ApiException('Not authenticated');

    final response = await http.get(
      Uri.parse('$baseUrl/user/reading-history'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
      },
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return ReadingHistoryResponse.fromJson(data);
    } else {
      final error = jsonDecode(response.body);
      throw ApiException(error['error'] ?? 'Failed to fetch reading history');
    }
  }
}

// Models
class AuthResponse {
  final String message;
  final User user;
  final String token;

  AuthResponse({required this.message, required this.user, required this.token});

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    return AuthResponse(
      message: json['message'],
      user: User.fromJson(json['user']),
      token: json['token'],
    );
  }
}

class User {
  final int id;
  final String username;
  final String? email;

  User({required this.id, required this.username, this.email});

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      username: json['username'],
      email: json['email'],
    );
  }
}

class Article {
  final String title;
  final String url;
  final String description;
  final String? publishedDate;
  final String source;
  final String? category;
  final double? relevanceScore;

  Article({
    required this.title,
    required this.url,
    required this.description,
    this.publishedDate,
    required this.source,
    this.category,
    this.relevanceScore,
  });

  factory Article.fromJson(Map<String, dynamic> json) {
    return Article(
      title: json['title'],
      url: json['url'],
      description: json['description'],
      publishedDate: json['published_date'],
      source: json['source'],
      category: json['category'],
      relevanceScore: json['relevance_score']?.toDouble(),
    );
  }
}

class UserPreference {
  final int id;
  final String keywords;
  final double weight;
  final String? category;

  UserPreference({
    required this.id,
    required this.keywords,
    required this.weight,
    this.category,
  });

  factory UserPreference.fromJson(Map<String, dynamic> json) {
    return UserPreference(
      id: json['id'],
      keywords: json['keywords'],
      weight: json['weight']?.toDouble() ?? 1.0,
      category: json['category'],
    );
  }
}

class ReadingHistoryResponse {
  final List<ReadingHistoryItem> readingHistory;
  final int total;

  ReadingHistoryResponse({required this.readingHistory, required this.total});

  factory ReadingHistoryResponse.fromJson(Map<String, dynamic> json) {
    return ReadingHistoryResponse(
      readingHistory: (json['reading_history'] as List)
          .map((item) => ReadingHistoryItem.fromJson(item))
          .toList(),
      total: json['total'],
    );
  }
}

class ReadingHistoryItem {
  final String title;
  final String url;
  final String source;
  final String action;
  final String timestamp;

  ReadingHistoryItem({
    required this.title,
    required this.url,
    required this.source,
    required this.action,
    required this.timestamp,
  });

  factory ReadingHistoryItem.fromJson(Map<String, dynamic> json) {
    return ReadingHistoryItem(
      title: json['title'],
      url: json['url'],
      source: json['source'],
      action: json['action'],
      timestamp: json['timestamp'],
    );
  }
}

class ApiException implements Exception {
  final String message;
  ApiException(this.message);

  @override
  String toString() => 'ApiException: $message';
}