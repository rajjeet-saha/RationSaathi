import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../data/models/correction_model.dart';
import '../data/services/api_service.dart';
import '../providers/session_provider.dart';
import '../widgets/status_badge.dart';

class RecordCorrectionScreen extends StatefulWidget {
  const RecordCorrectionScreen({super.key});

  @override
  State<RecordCorrectionScreen> createState() => _RecordCorrectionScreenState();
}

class _RecordCorrectionScreenState extends State<RecordCorrectionScreen> {
  String _selectedOperation = 'UPDATE_FIELD';
  CorrectionSimulationModel? _simulation;
  bool _simulating = false;
  String? _error;

  final Map<String, String> _operations = {
    'UPDATE_FIELD': 'Harmless Edit (Spelling correction in name)',
    'DELETE_MEMBER': 'Destructive Edit (Attempt to delete family member)',
    'REPLACE_MEMBER': 'Unsafe Replacement (Swap with new person)',
  };

  @override
  void initState() {
    super.initState();
    _runSimulation();
  }

  Future<void> _runSimulation() async {
    final sessionProv = Provider.of<SessionProvider>(context, listen: false);
    final memberId = sessionProv.activeMember?.id;
    if (memberId == null) return;

    setState(() {
      _simulating = true;
      _error = null;
    });

    try {
      final api = Provider.of<ApiService>(context, listen: false);
      Map<String, dynamic> fields = {};
      if (_selectedOperation == 'UPDATE_FIELD') {
        fields = {'alias': 'Corrected Name'};
      }

      final res = await api.simulateCorrection(
        operation: _selectedOperation,
        memberId: memberId,
        fields: fields,
      );

      setState(() {
        _simulation = res;
        _simulating = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Unable to run server-side safety simulation.';
        _simulating = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Record Correction Safety Guard'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Server-Enforced Correction Safety',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 6),
            const Text(
              'RationSaathi prevents accidental loss of family member allocations. Any proposal that removes a member or invalidates an entitlement is BLOCKED before submission.',
              style: TextStyle(color: Colors.black87, fontSize: 13),
            ),
            const SizedBox(height: 16),

            // Select Scenario to Simulate
            Card(
              child: Padding(
                padding: const EdgeInsets.all(12.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Test Modification Scenario:', style: TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    ..._operations.entries.map((op) {
                      return RadioListTile<String>(
                        contentPadding: EdgeInsets.zero,
                        title: Text(op.value, style: const TextStyle(fontSize: 13)),
                        value: op.key,
                        groupValue: _selectedOperation,
                        onChanged: (val) {
                          if (val != null) {
                            setState(() => _selectedOperation = val);
                            _runSimulation();
                          }
                        },
                      );
                    }),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            if (_simulating)
              const Center(child: Padding(padding: EdgeInsets.all(32), child: CircularProgressIndicator()))
            else if (_error != null)
              Container(
                padding: const EdgeInsets.all(12),
                color: Colors.red.shade50,
                child: Text(_error!, style: const TextStyle(color: Colors.red)),
              )
            else if (_simulation != null)
              _buildSimulationResult(context, _simulation!),
          ],
        ),
      ),
    );
  }

  Widget _buildSimulationResult(BuildContext context, CorrectionSimulationModel sim) {
    final isBlocked = sim.isBlocked;
    final cardColor = isBlocked ? Colors.red.shade50 : Colors.green.shade50;
    final badgeType = isBlocked ? BadgeType.blocked : BadgeType.verified;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Card(
          color: cardColor,
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Risk Assessment: ${sim.riskLevel}',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: isBlocked ? Colors.red.shade900 : Colors.green.shade900,
                      ),
                    ),
                    StatusBadge(label: sim.riskLevel, type: badgeType),
                  ],
                ),
                const SizedBox(height: 10),
                Text(
                  isBlocked
                    ? '🚫 SUBMISSION PROHIBITED: This modification would eliminate a member from the household record.'
                    : '✅ SAFE MODIFICATION: This minor update preserves all family relationship linkages.',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: isBlocked ? Colors.red.shade900 : Colors.green.shade900,
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),

        if (sim.reasons.isNotEmpty) ...[
          const Text('Reasons for Safety Evaluation:', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 6),
          ...sim.reasons.map((r) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.info_outline, size: 16, color: Colors.blueGrey),
                    const SizedBox(width: 6),
                    Expanded(child: Text(r, style: const TextStyle(fontSize: 13))),
                  ],
                ),
              )),
          const SizedBox(height: 12),
        ],

        if (sim.consequences.isNotEmpty) ...[
          const Text('Potential Consequences:', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 6),
          ...sim.consequences.map((c) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.warning_amber_rounded, size: 16, color: Colors.amber),
                    const SizedBox(width: 6),
                    Expanded(child: Text(c, style: const TextStyle(fontSize: 13))),
                  ],
                ),
              )),
          const SizedBox(height: 12),
        ],

        if (sim.recommendations.isNotEmpty) ...[
          const Text('Safe Alternatives & Recommendations:', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 6),
          ...sim.recommendations.map((rec) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.lightbulb_outline, size: 16, color: Colors.teal),
                    const SizedBox(width: 6),
                    Expanded(child: Text(rec, style: const TextStyle(fontSize: 13))),
                  ],
                ),
              )),
          const SizedBox(height: 20),
        ],

        // Submission Button (Disabled if blocked)
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: sim.canSubmit
                ? () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Safe change staged as draft.')),
                    );
                  }
                : null, // Disabled by design when blocked
            child: Text(isBlocked ? 'Blocked (Cannot Submit)' : 'Proceed With Safe Draft'),
          ),
        ),
      ],
    );
  }
}
