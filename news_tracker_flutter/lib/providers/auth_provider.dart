import 'package:flutter/foundation.dart';
import '../services/api_service.dart';

class AuthProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();
  User? _currentUser;
  bool _isLoading = false;
  String? _error;

  User? get currentUser => _currentUser;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isAuthenticated => _currentUser != null;

  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void _setError(String? error) {
    _error = error;
    notifyListeners();
  }

  Future<void> checkAuthStatus() async {
    try {
      final token = await _apiService.getToken();
      if (token != null) {
        // Token exists, but we don't have user info stored locally
        // In a real app, you might want to validate the token with the server
        // For now, we'll just clear it and require re-login
        await _apiService.clearToken();
      }
    } catch (e) {
      print('Error checking auth status: $e');
    }
  }

  Future<bool> register(String username, String password, [String? email]) async {
    _setLoading(true);
    _setError(null);

    try {
      final response = await _apiService.register(username, password, email);
      _currentUser = response.user;
      _setLoading(false);
      notifyListeners();
      return true;
    } catch (e) {
      _setError(e.toString().replaceFirst('ApiException: ', ''));
      _setLoading(false);
      return false;
    }
  }

  Future<bool> login(String username, String password) async {
    _setLoading(true);
    _setError(null);

    try {
      final response = await _apiService.login(username, password);
      _currentUser = response.user;
      _setLoading(false);
      notifyListeners();
      return true;
    } catch (e) {
      _setError(e.toString().replaceFirst('ApiException: ', ''));
      _setLoading(false);
      return false;
    }
  }

  Future<void> logout() async {
    await _apiService.clearToken();
    _currentUser = null;
    notifyListeners();
  }

  void clearError() {
    _setError(null);
  }
}