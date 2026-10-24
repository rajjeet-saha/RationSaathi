import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/session_provider.dart';
import '../widgets/status_badge.dart';
import 'splash_sign_in_screen.dart';
import 'member_entitlements_screen.dart';
import 'portability_screen.dart';
import 'record_correction_screen.dart';
import 'offline_drafts_screen.dart';
import 'grievances_screen.dart';
import 'accessibility_settings_screen.dart';

class HomeOverviewScreen extends StatefulWidget {
  const HomeOverviewScreen({super.key});

  @override
  State<HomeOverviewScreen> createState() => _HomeOverviewScreenState();
}

class _HomeOverviewScreenState extends State<HomeOverviewScreen> {
  int _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    final sessionProv = Provider.of<SessionProvider>(context);
    final household = sessionProv.household;
    final currentMember = sessionProv.activeMember;

    if (!sessionProv.isAuthenticated) {
      return const SplashSignInScreen();
    }

    final pages = [
      _buildOverviewTab(context, household, currentMember, sessionProv),
      const MemberEntitlementsScreen(),
      const PortabilityScreen(),
      const OfflineDraftsScreen(),
      const GrievancesScreen(),
    ];

    return Scaffold(
      appBar: AppBar(
        title: Text(sessionProv.isFacilitator ? 'Facilitator Session' : 'RationSaathi'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            tooltip: 'Accessibility Settings',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const AccessibilitySettingsScreen()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Safe Sign Out',
            onPressed: () async {
              await sessionProv.signOut();
              if (mounted) {
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (_) => const SplashSignInScreen()),
                );
              }
            },
          ),
        ],
      ),
      body: pages[_currentIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (idx) => setState(() => _currentIndex = idx),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Overview'),
          NavigationDestination(icon: Icon(Icons.receipt_long_outlined), selectedIcon: Icon(Icons.receipt_long), label: 'Rations'),
          NavigationDestination(icon: Icon(Icons.swap_horiz), label: 'Portability'),
          NavigationDestination(icon: Icon(Icons.edit_note), label: 'Drafts'),
          NavigationDestination(icon: Icon(Icons.report_problem_outlined), selectedIcon: Icon(Icons.report_problem), label: 'Grievance'),
        ],
      ),
    );
  }

  Widget _buildOverviewTab(
    BuildContext context,
    dynamic household,
    dynamic currentMember,
    SessionProvider sessionProv,
  ) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Active Member Banner
          Card(
            color: Colors.green.shade50,
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Row(
                children: [
                  CircleAvatar(
                    backgroundColor: Colors.green.shade800,
                    foregroundColor: Colors.white,
                    child: Text(currentMember?.alias?.substring(0, 1) ?? 'M'),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          currentMember?.fullName ?? currentMember?.alias ?? 'Active Member',
                          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                        Text(
                          'Relationship: ${currentMember?.relationship ?? 'Household Member'} • Age: ${currentMember?.age ?? 'N/A'}',
                          style: TextStyle(color: Colors.green.shade900, fontSize: 13),
                        ),
                      ],
                    ),
                  ),
                  const StatusBadge(label: 'VERIFIED', type: BadgeType.verified),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Household Details Card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(household?.label ?? 'Ration Card', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                      Text(household?.reference ?? '', style: const TextStyle(fontFamily: 'monospace', color: Colors.grey)),
                    ],
                  ),
                  const Divider(height: 24),
                  Row(
                    children: [
                      const Icon(Icons.location_on_outlined, size: 20, color: Colors.teal),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Route: ${household?.homeState ?? 'Origin'} → ${household?.destinationState ?? 'Destination'}',
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      const Icon(Icons.people_outline, size: 20, color: Colors.blueGrey),
                      const SizedBox(width: 8),
                      Text('Registered Members: ${household?.memberCount ?? 1} members'),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Quick Action: Record Mismatch / Correction Simulator
          Card(
            child: ListTile(
              leading: const CircleAvatar(
                backgroundColor: Color(0xFFFEF3C7),
                child: Icon(Icons.security, color: Color(0xFFB45309)),
              ),
              title: const Text('Simulate Record Correction', style: TextStyle(fontWeight: FontWeight.bold)),
              subtitle: const Text('Test safety rules: harmful edits (e.g. member deletion) are automatically BLOCKED.'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const RecordCorrectionScreen()),
                );
              },
            ),
          ),
          const SizedBox(height: 12),

          // Public Distribution System Principles
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: Colors.blue.shade50,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: Colors.blue.shade200),
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Civic Guarantees:', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.indigo)),
                SizedBox(height: 6),
                Text('• You cannot be removed from a ration card by an online error.', style: TextStyle(fontSize: 13)),
                Text('• Unverified stock status will never promise available grains.', style: TextStyle(fontSize: 13)),
                Text('• Draft complaints are never submitted without receipt tokens.', style: TextStyle(fontSize: 13)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
