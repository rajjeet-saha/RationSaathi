import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';

import 'core/theme/app_theme.dart';
import 'data/services/api_service.dart';
import 'data/services/offline_draft_storage.dart';
import 'providers/accessibility_provider.dart';
import 'providers/draft_provider.dart';
import 'providers/session_provider.dart';
import 'screens/splash_sign_in_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  final apiService = ApiService();
  final draftStorage = OfflineDraftStorage();

  runApp(
    MultiProvider(
      providers: [
        Provider<ApiService>.value(value: apiService),
        Provider<OfflineDraftStorage>.value(value: draftStorage),
        ChangeNotifierProvider<SessionProvider>(
          create: (_) => SessionProvider(apiService: apiService),
        ),
        ChangeNotifierProvider<DraftProvider>(
          create: (_) => DraftProvider(apiService: apiService, storage: draftStorage),
        ),
        ChangeNotifierProvider<AccessibilityProvider>(
          create: (_) => AccessibilityProvider(),
        ),
      ],
      child: const RationSaathiApp(),
    ),
  );
}

class RationSaathiApp extends StatelessWidget {
  const RationSaathiApp({super.key});

  @override
  Widget build(BuildContext context) {
    final a11y = Provider.of<AccessibilityProvider>(context);

    final themeData = a11y.isHighContrast
        ? AppTheme.highContrastTheme(a11y.fontScale)
        : AppTheme.standardTheme(a11y.fontScale);

    return MaterialApp(
      title: 'RationSaathi Mobile',
      debugShowCheckedModeBanner: false,
      theme: themeData,
      locale: a11y.currentLocale,
      supportedLocales: const [
        Locale('en', ''),
        Locale('hi', ''),
        Locale('bn', ''),
        Locale('te', ''),
      ],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      home: const SplashSignInScreen(),
    );
  }
}
