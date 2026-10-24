import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../data/models/household_model.dart';
import '../data/services/api_service.dart';
import '../providers/session_provider.dart';
import '../widgets/status_badge.dart';

class MemberEntitlementsScreen extends StatefulWidget {
  const MemberEntitlementsScreen({super.key});

  @override
  State<MemberEntitlementsScreen> createState() => _MemberEntitlementsScreenState();
}

class _MemberEntitlementsScreenState extends State<MemberEntitlementsScreen> {
  List<EntitlementModel> _entitlements = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchEntitlements();
  }

  Future<void> _fetchEntitlements() async {
    final sessionProv = Provider.of<SessionProvider>(context, listen: false);
    final memberId = sessionProv.activeMember?.id;
    if (memberId == null) return;

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final api = Provider.of<ApiService>(context, listen: false);
      final list = await api.getMemberEntitlements(memberId);
      setState(() {
        _entitlements = list;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Unable to fetch verified member entitlements.';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final sessionProv = Provider.of<SessionProvider>(context);
    final activeMember = sessionProv.activeMember;

    return Scaffold(
      body: RefreshIndicator(
        onRefresh: _fetchEntitlements,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Entitlements for ${activeMember?.alias ?? 'Member'}',
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 6),
              const Text(
                'Verified grain quantities for the current distribution cycle.',
                style: TextStyle(color: Colors.black54),
              ),
              const SizedBox(height: 16),
              if (_loading)
                const Center(child: Padding(padding: EdgeInsets.all(32), child: CircularProgressIndicator()))
              else if (_error != null)
                Center(
                  child: Column(
                    children: [
                      Text(_error!, style: const TextStyle(color: Colors.red)),
                      const SizedBox(height: 8),
                      ElevatedButton(onPressed: _fetchEntitlements, child: const Text('Retry')),
                    ],
                  ),
                )
              else if (_entitlements.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(24.0),
                    child: Center(child: Text('No entitlements recorded for this profile.')),
                  ),
                )
              else
                ..._entitlements.map((ent) {
                  final entitled = ent.entitledQty ?? 0;
                  final drawn = ent.drawnQty ?? 0;
                  final remaining = ent.remaining.display;
                  final unit = ent.unit;

                  return Card(
                    margin: const EdgeInsets.only(bottom: 12),
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                ent.commodityName,
                                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                              ),
                              StatusBadge(
                                label: ent.verificationStatus,
                                type: ent.verificationStatus == 'VERIFIED'
                                    ? BadgeType.verified
                                    : BadgeType.unverified,
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              _buildMetric('Monthly Allocation', '$entitled $unit'),
                              _buildMetric('Drawn this Month', '$drawn $unit'),
                              _buildMetric('Remaining', '$remaining $unit', highlight: true),
                            ],
                          ),
                          const Divider(height: 24),
                          Row(
                            children: [
                              const Icon(Icons.info_outline, size: 14, color: Colors.grey),
                              const SizedBox(width: 4),
                              Expanded(
                                child: Text(
                                  'Provenance: ${ent.provenanceLabel} • Period: ${ent.period}',
                                  style: const TextStyle(fontSize: 11, color: Colors.black54),
                                ),
                              ),
                            ],
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

  Widget _buildMetric(String label, String value, {bool highlight = false}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
        const SizedBox(height: 2),
        Text(
          value,
          style: TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.bold,
            color: highlight ? Colors.green.shade800 : Colors.black87,
          ),
        ),
      ],
    );
  }
}
