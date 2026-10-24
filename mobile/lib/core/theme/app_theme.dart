import 'package:flutter/material.dart';

/// Accessible Theme configuration for RationSaathi Mobile
class AppTheme {
  // Standard Civic Palette
  static const Color primaryGreen = Color(0xFF1E3A2F);
  static const Color accentAmber = Color(0xFFD97706);
  static const Color surfaceWarm = Color(0xFFF9FAFB);
  static const Color cardBorder = Color(0xFFE5E7EB);
  static const Color textDark = Color(0xFF1F2937);
  static const Color textMuted = Color(0xFF6B7280);

  // Status & Safety Colors
  static const Color verifiedGreen = Color(0xFF047857);
  static const Color pendingAmber = Color(0xFFB45309);
  static const Color blockedRed = Color(0xFFB91C1C);
  static const Color noticeBlue = Color(0xFF1D4ED8);

  // High Contrast Palette (for visual accessibility)
  static const Color hcBackground = Color(0xFF000000);
  static const Color hcSurface = Color(0xFF121212);
  static const Color hcText = Color(0xFFFFFFFF);
  static const Color hcYellow = Color(0xFFFFEB3B);
  static const Color hcCyan = Color(0xFF00E5FF);
  static const Color hcRed = Color(0xFFFF5252);

  static ThemeData standardTheme(double fontScale) {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryGreen,
        primary: primaryGreen,
        secondary: accentAmber,
        surface: surfaceWarm,
      ),
      scaffoldBackgroundColor: surfaceWarm,
      appBarTheme: const AppBarTheme(
        backgroundColor: primaryGreen,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: false,
      ),
      cardTheme: CardTheme(
        color: Colors.white,
        elevation: 1,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: cardBorder),
        ),
      ),
      textTheme: _buildTextTheme(textDark, fontScale),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primaryGreen,
          foregroundColor: Colors.white,
          minimumSize: const Size(88, 48), // Accessible touch target
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          textStyle: TextStyle(fontSize: 16 * fontScale, fontWeight: FontWeight.w600),
        ),
      ),
    );
  }

  static ThemeData highContrastTheme(double fontScale) {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: hcBackground,
      colorScheme: const ColorScheme.dark(
        primary: hcYellow,
        secondary: hcCyan,
        surface: hcSurface,
        onSurface: hcText,
        error: hcRed,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: hcSurface,
        foregroundColor: hcYellow,
        elevation: 2,
        centerTitle: false,
      ),
      cardTheme: CardTheme(
        color: hcSurface,
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: hcYellow, width: 2),
        ),
      ),
      textTheme: _buildTextTheme(hcText, fontScale),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: hcYellow,
          foregroundColor: Colors.black,
          minimumSize: const Size(88, 48),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          textStyle: TextStyle(fontSize: 16 * fontScale, fontWeight: FontWeight.bold),
        ),
      ),
    );
  }

  static TextTheme _buildTextTheme(Color color, double scale) {
    return TextTheme(
      headlineLarge: TextStyle(fontSize: 28 * scale, fontWeight: FontWeight.bold, color: color),
      headlineMedium: TextStyle(fontSize: 22 * scale, fontWeight: FontWeight.bold, color: color),
      titleLarge: TextStyle(fontSize: 18 * scale, fontWeight: FontWeight.w600, color: color),
      titleMedium: TextStyle(fontSize: 16 * scale, fontWeight: FontWeight.w600, color: color),
      bodyLarge: TextStyle(fontSize: 16 * scale, color: color),
      bodyMedium: TextStyle(fontSize: 14 * scale, color: color),
      bodySmall: TextStyle(fontSize: 12 * scale, color: color.withOpacity(0.8)),
    );
  }
}
