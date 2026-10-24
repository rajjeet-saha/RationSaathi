import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/constants/api_endpoints.dart';
import '../data/services/api_service.dart';
import '../providers/session_provider.dart';
import 'home_overview_screen.dart';

class SplashSignInScreen extends StatefulWidget {
  const SplashSignInScreen({super.key});

  @override
  State<SplashSignInScreen> createState() => _SplashSignInScreenState();
}

class _SplashSignInScreenState extends State<SplashSignInScreen> {
  List<Map<String, dynamic>> _profiles = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchProfiles();
  }

  Future<void> _fetchProfiles() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final api = Provider.of<ApiService>(context, listen: false);
      final list = await api.getDemoProfiles();
      setState(() {
        _profiles = list;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Unable to connect to backend at ${ApiEndpoints.baseUrl}.\nEnsure backend server is running.';
        _loading = false;
      });
    }
  }

  void _showFacilitatorConsentDialog(String householdId, List members) {
    String? selectedMemberId = members.isNotEmpty ? members[0]['id'].toString() : null;
    bool explained = false;
    bool given = false;

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              title: const Text('Facilitator Consent Gate'),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Server-enforced privacy: A facilitator cannot view or edit member entitlements without documented, explicit consent.',
                      style: TextStyle(fontSize: 13, color: Colors.black87),
                    ),
                    const SizedBox(height: 12),
                    const Text('Select Household Member:', style: TextStyle(fontWeight: FontWeight.bold)),
                    DropdownButton<String>(
                      isExpanded: true,
                      value: selectedMemberId,
                      items: members.map<DropdownMenuItem<String>>((m) {
                        return DropdownMenuItem<String>(
                          value: m['id'].toString(),
                          child: Text('${m['alias'] ?? m['full_name']} (${m['relationship'] ?? 'Member'})'),
                        );
                      }).toList(),
                      onChanged: (val) {
                        setDialogState(() => selectedMemberId = val);
                      },
                    ),
                    const SizedBox(height: 12),
                    CheckboxListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('I have explained the purpose to the member in their preferred language.', style: TextStyle(fontSize: 13)),
                      value: explained,
                      onChanged: (val) => setDialogState(() => explained = val ?? false),
                    ),
                    CheckboxListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('Member has given explicit consent for this assisted session.', style: TextStyle(fontSize: 13)),
                      value: given,
                      onChanged: (val) => setDialogState(() => given = val ?? false),
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('Cancel'),
                ),
                ElevatedButton(
                  onPressed: (explained && given && selectedMemberId != null)
                      ? () async {
                          Navigator.pop(ctx);
                          final sessionProv = Provider.of<SessionProvider>(context, listen: false);
                          await sessionProv.signInAsFacilitator(householdId: householdId);
                          await sessionProv.grantFacilitatorConsent(
                            memberId: selectedMemberId!,
                            consentExplained: true,
                            consentGiven: true,
                          );
                          if (mounted && sessionProv.isAuthenticated) {
                            Navigator.pushReplacement(
                              context,
                              MaterialPageRoute(builder: (_) => const HomeOverviewScreen()),
                            );
                          }
                        }
                      : null,
                  child: const Text('Confirm & Open'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('RationSaathi — Civic Navigator'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Notice Banner
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.amber.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.amber.shade400),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.shield_outlined, color: Colors.brown),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'DEMO MODE (SYNTHETIC DATA). No live government database is connected.',
                        style: TextStyle(fontSize: 13, color: Colors.brown, fontWeight: FontWeight.w600),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
              Text(
                'Select a Synthetic Profile',
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 8),
              const Text(
                'Choose a simulated migrant household member to navigate entitlements, check stock portability, or test safety rules.',
                style: TextStyle(color: Colors.black54),
              ),
              const SizedBox(height: 16),
              if (_loading)
                const Center(child: Padding(padding: EdgeInsets.all(32), child: CircularProgressIndicator()))
              else if (_error != null)
                Column(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.red.shade50,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.red.shade300),
                      ),
                      child: Text(_error!, style: const TextStyle(color: Colors.red)),
                    ),
                    const SizedBox(height: 12),
                    ElevatedButton.icon(
                      onPressed: _fetchProfiles,
                      icon: const Icon(Icons.refresh),
                      label: const Text('Retry Connection'),
                    ),
                  ],
                )
              else
                ..._profiles.map((hh) {
                  final hhId = hh['id'].toString();
                  final ref = hh['reference'] ?? 'RATION-CARD';
                  final label = hh['label'] ?? 'Household';
                  final homeState = hh['home_state'] ?? 'Origin';
                  final destState = hh['destination_state'] ?? 'Destination';
                  final members = (hh['members'] as List<dynamic>?) ?? [];

                  return Card(
                    margin: const EdgeInsets.only(bottom: 16),
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(label, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                decoration: BoxDecoration(
                                  color: Colors.grey.shade200,
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: Text(ref, style: const TextStyle(fontSize: 12, fontFamily: 'monospace')),
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Text('$homeState → $destState', style: const TextStyle(fontSize: 13, color: Colors.blueGrey)),
                          const Divider(height: 20),
                          const Text('Sign in as Member (Self-Service):', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                          const SizedBox(height: 8),
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: members.map((m) {
                              final memberId = m['id'].toString();
                              final name = m['alias'] ?? m['full_name'];
                              return ActionChip(
                                avatar: const Icon(Icons.person, size: 16),
                                label: Text(name),
                                onPressed: () async {
                                  final prov = Provider.of<SessionProvider>(context, listen: false);
                                  await prov.signInAsMember(householdId: hhId, memberId: memberId);
                                  if (mounted && prov.isAuthenticated) {
                                    Navigator.pushReplacement(
                                      context,
                                      MaterialPageRoute(builder: (_) => const HomeOverviewScreen()),
                                    );
                                  }
                                },
                              );
                            }).toList(),
                          ),
                          const SizedBox(height: 12),
                          OutlinedButton.icon(
                            icon: const Icon(Icons.support_agent),
                            label: const Text('Facilitator Mode (Consent Required)'),
                            onPressed: () => _showFacilitatorConsentDialog(hhId, members),
                          ),
                        ],
                      ),
                    ),
                  );
                }),
            ],
          ),
        ),
      ),
    );
  }
}
