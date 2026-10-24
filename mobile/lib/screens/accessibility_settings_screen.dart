import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/constants/api_endpoints.dart';
import '../providers/accessibility_provider.dart';

class AccessibilitySettingsScreen extends StatefulWidget {
  const AccessibilitySettingsScreen({super.key});

  @override
  State<AccessibilitySettingsScreen> createState() => _AccessibilitySettingsScreenState();
}

class _AccessibilitySettingsScreenState extends State<AccessibilitySettingsScreen> {
  late TextEditingController _urlController;

  @override
  void initState() {
    super.initState();
    _urlController = TextEditingController(text: ApiEndpoints.baseUrl);
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final a11y = Provider.of<AccessibilityProvider>(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Accessibility & Server Settings'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Visual Accessibility', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            const SizedBox(height: 12),

            // High Contrast Switch
            Card(
              child: SwitchListTile(
                title: const Text('High Contrast Mode', style: TextStyle(fontWeight: FontWeight.bold)),
                subtitle: const Text('WCAG AAA high-contrast black/yellow palette for enhanced visibility in direct sunlight.'),
                value: a11y.isHighContrast,
                onChanged: (val) => a11y.toggleHighContrast(val),
              ),
            ),
            const SizedBox(height: 12),

            // Text Scale Slider
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Font Size Scaling: ${(a11y.fontScale * 100).toInt()}%', style: const TextStyle(fontWeight: FontWeight.bold)),
                    Slider(
                      value: a11y.fontScale,
                      min: 1.0,
                      max: 1.6,
                      divisions: 6,
                      label: '${(a11y.fontScale * 100).toInt()}%',
                      onChanged: (val) => a11y.setFontScale(val),
                    ),
                    const Text('Sample preview: "Public Distribution without the runaround."', style: TextStyle(fontSize: 14)),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),

            // Read-Aloud / TTS
            Card(
              child: SwitchListTile(
                title: const Text('Read-Aloud Speech Support', style: TextStyle(fontWeight: FontWeight.bold)),
                subtitle: const Text('Synthesizes audio read-aloud for ration status and entitlements.'),
                value: a11y.readAloudEnabled,
                onChanged: (val) => a11y.toggleReadAloud(val),
              ),
            ),
            const SizedBox(height: 20),

            // Language Selection
            const Text('Language / भाषा / ভাষা / భాష', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            const SizedBox(height: 12),
            Card(
              child: Column(
                children: [
                  RadioListTile<String>(
                    title: const Text('English (Default)'),
                    value: 'en',
                    groupValue: a11y.currentLocale.languageCode,
                    onChanged: (val) => a11y.setLocale(val!),
                  ),
                  RadioListTile<String>(
                    title: const Text('हिन्दी (Hindi)'),
                    value: 'hi',
                    groupValue: a11y.currentLocale.languageCode,
                    onChanged: (val) => a11y.setLocale(val!),
                  ),
                  RadioListTile<String>(
                    title: const Text('বাংলা (Bengali)'),
                    value: 'bn',
                    groupValue: a11y.currentLocale.languageCode,
                    onChanged: (val) => a11y.setLocale(val!),
                  ),
                  RadioListTile<String>(
                    title: const Text('తెలుగు (Telugu)'),
                    value: 'te',
                    groupValue: a11y.currentLocale.languageCode,
                    onChanged: (val) => a11y.setLocale(val!),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Backend Connectivity Settings
            const Text('Backend Server Connection', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            const SizedBox(height: 8),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    TextField(
                      controller: _urlController,
                      decoration: const InputDecoration(
                        labelText: 'API Base URL',
                        border: OutlineInputBorder(),
                        helperText: 'Default: http://10.0.2.2:8000/api/v1 (Android Emulator)',
                      ),
                    ),
                    const SizedBox(height: 12),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        OutlinedButton(
                          onPressed: () {
                            setState(() {
                              _urlController.text = 'http://10.0.2.2:8000/api/v1';
                              ApiEndpoints.baseUrl = _urlController.text;
                            });
                          },
                          child: const Text('Reset Emulator Default'),
                        ),
                        const SizedBox(width: 8),
                        ElevatedButton(
                          onPressed: () {
                            setState(() {
                              ApiEndpoints.baseUrl = _urlController.text.trim();
                            });
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('API URL updated to: ${ApiEndpoints.baseUrl}')),
                            );
                          },
                          child: const Text('Save URL'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
