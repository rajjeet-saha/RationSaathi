import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AccessibilityProvider extends ChangeNotifier {
  bool _isHighContrast = false;
  double _fontScale = 1.0;
  Locale _currentLocale = const Locale('en');
  bool _readAloudEnabled = false;

  bool get isHighContrast => _isHighContrast;
  double get fontScale => _fontScale;
  Locale get currentLocale => _currentLocale;
  bool get readAloudEnabled => _readAloudEnabled;

  AccessibilityProvider() {
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _isHighContrast = prefs.getBool('pref_high_contrast') ?? false;
      _fontScale = prefs.getDouble('pref_font_scale') ?? 1.0;
      final langCode = prefs.getString('pref_lang') ?? 'en';
      _currentLocale = Locale(langCode);
      _readAloudEnabled = prefs.getBool('pref_read_aloud') ?? false;
      notifyListeners();
    } catch (_) {}
  }

  void toggleHighContrast(bool value) async {
    _isHighContrast = value;
    notifyListeners();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool('pref_high_contrast', value);
    } catch (_) {}
  }

  void setFontScale(double scale) async {
    _fontScale = scale.clamp(1.0, 1.6);
    notifyListeners();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setDouble('pref_font_scale', _fontScale);
    } catch (_) {}
  }

  void setLocale(String languageCode) async {
    _currentLocale = Locale(languageCode);
    notifyListeners();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('pref_lang', languageCode);
    } catch (_) {}
  }

  void toggleReadAloud(bool value) async {
    _readAloudEnabled = value;
    notifyListeners();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool('pref_read_aloud', value);
    } catch (_) {}
  }
}
