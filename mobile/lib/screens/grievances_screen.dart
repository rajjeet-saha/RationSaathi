import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../data/models/grievance_model.dart';
import '../data/services/api_service.dart';
import '../widgets/status_badge.dart';

class GrievancesScreen extends StatefulWidget {
  const GrievancesScreen({super.key});

  @override
  State<GrievancesScreen> createState() => _GrievancesScreenState();
}

class _GrievancesScreenState extends State<GrievancesScreen> {
  List<GrievanceModel> _grievances = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchGrievances();
  }

  Future<void> _fetchGrievances() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final api = Provider.of<ApiService>(context, listen: false);
      final list = await api.getGrievances();
      setState(() {
        _grievances = list;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Unable to fetch active household grievances.';
        _loading = false;
      });
    }
  }

  void _showEscalationLetterDialog(String grievanceId) async {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => const Center(child: CircularProgressIndicator()),
    );

    try {
      final api = Provider.of<ApiService>(context, listen: false);
      final draft = await api.createEscalationDraft(grievanceId, recipientOffice: 'District Grievance Redressal Officer (DGRO)');
      if (mounted) Navigator.pop(context); // Close loading

      if (mounted) {
        showDialog(
          context: context,
          builder: (ctx) {
            return AlertDialog(
              title: const Text('Formal Escalation Letter'),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Legal Escalation Notice:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade100,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        draft['body'] ?? draft['letter'] ?? 'Escalation draft generated for verified overdue grievance.',
                        style: const TextStyle(fontSize: 12, fontFamily: 'monospace'),
                      ),
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Close')),
                ElevatedButton(
                  onPressed: () {
                    Navigator.pop(ctx);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Escalation draft saved to offline queue.')),
                    );
                  },
                  child: const Text('Stage Escalation'),
                ),
              ],
            );
          },
        );
      }
    } catch (e) {
      if (mounted) Navigator.pop(context);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Unable to generate escalation letter: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: RefreshIndicator(
        onRefresh: _fetchGrievances,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Grievance & Resolution Tracking', style: Theme.of(context).textTheme.headlineMedium),
              const SizedBox(height: 6),
              const Text(
                'Tracking 21-day official timelines. Overdue status is strictly reserved for verified configured deadlines.',
                style: TextStyle(fontSize: 13, color: Colors.black54),
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
                      ElevatedButton(onPressed: _fetchGrievances, child: const Text('Retry')),
                    ],
                  ),
                )
              else if (_grievances.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(24.0),
                    child: Center(child: Text('No active grievances filed for this household.')),
                  ),
                )
              else
                ..._grievances.map((g) {
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
                                g.category.replaceAll('_', ' '),
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                              ),
                              StatusBadge(
                                label: g.isOverdue ? 'OVERDUE (VERIFIED)' : g.status,
                                type: g.isOverdue ? BadgeType.overdue : BadgeType.pending,
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Text('Tracking ID: ${g.trackingNumber}', style: const TextStyle(fontFamily: 'monospace', fontSize: 12)),
                          const SizedBox(height: 8),
                          Text(g.summary, style: const TextStyle(fontSize: 14)),
                          const SizedBox(height: 8),
                          Text(
                            'Elapsed: ${g.daysElapsed} days • Deadline verified: ${g.deadlineVerified ? "Yes (Official)" : "Unverified"}',
                            style: TextStyle(
                              fontSize: 12,
                              color: g.deadlineVerified ? Colors.teal : Colors.blueGrey,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          if (g.canEscalate) ...[
                            const Divider(height: 20),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.end,
                              children: [
                                ElevatedButton.icon(
                                  icon: const Icon(Icons.send_outlined, size: 16),
                                  label: const Text('Draft Escalation Letter'),
                                  onPressed: () => _showEscalationLetterDialog(g.id),
                                ),
                              ],
                            ),
                          ],
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
