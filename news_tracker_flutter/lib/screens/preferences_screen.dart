import 'package:flutter/material.dart';
import '../services/api_service.dart';

class PreferencesScreen extends StatefulWidget {
  const PreferencesScreen({super.key});

  @override
  State<PreferencesScreen> createState() => _PreferencesScreenState();
}

class _PreferencesScreenState extends State<PreferencesScreen> {
  final ApiService _apiService = ApiService();
  final _keywordsController = TextEditingController();
  final _categoriesController = TextEditingController();
  final _weightController = TextEditingController(text: '1.0');
  
  List<UserPreference> _preferences = [];
  bool _isLoading = false;
  bool _isAddingPreference = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadPreferences();
  }

  @override
  void dispose() {
    _keywordsController.dispose();
    _categoriesController.dispose();
    _weightController.dispose();
    super.dispose();
  }

  Future<void> _loadPreferences() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final preferences = await _apiService.getUserPreferences();
      setState(() {
        _preferences = preferences;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString().replaceFirst('ApiException: ', '');
        _isLoading = false;
      });
    }
  }

  Future<void> _addPreference() async {
    if (_keywordsController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter keywords')),
      );
      return;
    }

    setState(() {
      _isAddingPreference = true;
    });

    try {
      final weight = double.tryParse(_weightController.text) ?? 1.0;
      final categories = _categoriesController.text.trim().isEmpty 
          ? null 
          : _categoriesController.text.trim();

      await _apiService.addUserPreference(
        _keywordsController.text.trim(),
        categories,
        weight,
      );

      // Clear form
      _keywordsController.clear();
      _categoriesController.clear();
      _weightController.text = '1.0';

      // Reload preferences
      await _loadPreferences();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Preference added successfully!')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: ${e.toString()}')),
        );
      }
    } finally {
      setState(() {
        _isAddingPreference = false;
      });
    }
  }

  Future<void> _deletePreference(UserPreference preference) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Preference'),
        content: Text('Are you sure you want to delete the preference for "${preference.keywords}"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        await _apiService.deleteUserPreference(preference.id);
        await _loadPreferences();
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Preference deleted successfully!')),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error: ${e.toString()}')),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Your Preferences'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          IconButton(
            icon: const Icon(Icons.help_outline),
            onPressed: _showHelpDialog,
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    return Column(
      children: [
        // Add preference form
        Card(
          margin: const EdgeInsets.all(16),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Add New Preference',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _keywordsController,
                  decoration: const InputDecoration(
                    labelText: 'Keywords (comma-separated)',
                    hintText: 'e.g., AI, machine learning, technology',
                    border: OutlineInputBorder(),
                    helperText: 'Enter topics you\'re interested in',
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _categoriesController,
                  decoration: const InputDecoration(
                    labelText: 'Categories (optional)',
                    hintText: 'e.g., Technology, Science',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _weightController,
                  decoration: const InputDecoration(
                    labelText: 'Weight',
                    hintText: '1.0',
                    border: OutlineInputBorder(),
                    helperText: 'Higher weights increase importance (0.1 - 5.0)',
                  ),
                  keyboardType: TextInputType.number,
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _isAddingPreference ? null : _addPreference,
                    child: _isAddingPreference
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('Add Preference'),
                  ),
                ),
              ],
            ),
          ),
        ),

        // Preferences list
        Expanded(
          child: _buildPreferencesList(),
        ),
      ],
    );
  }

  Widget _buildPreferencesList() {
    if (_isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Loading preferences...'),
          ],
        ),
      );
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: Colors.red[300],
            ),
            const SizedBox(height: 16),
            Text(
              'Error loading preferences',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            Text(
              _error!,
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey[600]),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadPreferences,
              child: const Text('Try Again'),
            ),
          ],
        ),
      );
    }

    if (_preferences.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.settings_outlined,
              size: 64,
              color: Colors.grey[400],
            ),
            const SizedBox(height: 16),
            Text(
              'No preferences set',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            const Text(
              'Add your first preference above to get personalized recommendations',
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
          child: Text(
            'Your Preferences (${_preferences.length})',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            itemCount: _preferences.length,
            itemBuilder: (context, index) {
              final preference = _preferences[index];
              return _buildPreferenceCard(preference);
            },
          ),
        ),
      ],
    );
  }

  Widget _buildPreferenceCard(UserPreference preference) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        title: Text(
          preference.keywords,
          style: const TextStyle(fontWeight: FontWeight.w500),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (preference.category != null) ...[
              const SizedBox(height: 4),
              Text('Categories: ${preference.category}'),
            ],
            const SizedBox(height: 4),
            Text('Weight: ${preference.weight}'),
          ],
        ),
        trailing: IconButton(
          icon: const Icon(Icons.delete, color: Colors.red),
          onPressed: () => _deletePreference(preference),
        ),
        isThreeLine: preference.category != null,
      ),
    );
  }

  void _showHelpDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('How Preferences Work'),
        content: const SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Keywords:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              Text('Enter topics you\'re interested in, separated by commas. Examples: "AI, machine learning", "sports, basketball", "climate change".'),
              SizedBox(height: 12),
              Text(
                'Categories:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              Text('Optional. Specify news categories like "Technology", "Science", "Politics", etc.'),
              SizedBox(height: 12),
              Text(
                'Weight:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              Text('Controls how important this preference is. Higher weights (e.g., 2.0) make articles matching this preference rank higher. Lower weights (e.g., 0.5) make them rank lower.'),
              SizedBox(height: 12),
              Text(
                'Tips:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              Text('• Use specific keywords for better results\n• Set higher weights for topics you care most about\n• You can always edit or delete preferences later'),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Got it'),
          ),
        ],
      ),
    );
  }
}