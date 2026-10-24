import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../data/models/portability_model.dart';
import '../data/services/api_service.dart';
import '../providers/session_provider.dart';
import '../widgets/status_badge.dart';

class PortabilityScreen extends StatefulWidget {
  const PortabilityScreen({super.key});

  @override
  State<PortabilityScreen> createState() => _PortabilityScreenState();
}

class _PortabilityScreenState extends State<PortabilityScreen> {
  String _selectedCommodity = 'WHEAT';
  PortabilityDecisionModel? _decision;
  bool _evaluating = false;
  String? _error;

  final List<Map<String, String>> _commodities = [
    {'code': 'WHEAT', 'name': 'Wheat Grain'},
    {'code': 'RICE', 'name': 'Rice Grain'},
    {'code': 'SUGAR', 'name': 'Sugar'},
    {'code': 'KEROSENE', 'name': 'Kerosene'},
  ];

  @override
  void initState() {
    super.initState();
    _evaluatePortability();
  }

  Future<void> _evaluatePortability() async {
    final sessionProv = Provider.of<SessionProvider>(context, listen: false);
    final memberId = sessionProv.activeMember?.id;
    if (memberId == null) return;

    setState(() {
      _evaluating = true;
      _error = null;
    });

    try {
      final api = Provider.of<ApiService>(context, listen: false);
      final res = await api.evaluatePortability(
        memberId: memberId,
        commodityCode: _selectedCommodity,
      );
      setState(() {
        _decision = res;
        _evaluating = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Unable to evaluate portability rules with server.';
        _evaluating = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final sessionProv = Provider.of<SessionProvider>(context);
    final hh = sessionProv.household;

    return Scaffold(
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Interstate Portability (ONORC)', style: Theme.of(context).textTheme.headlineMedium),
            const SizedBox(height: 6),
            Text(
              'Route: ${hh?.homeState ?? 'Home'} → ${hh?.destinationState ?? 'Destination'}',
              style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.teal),
            ),
            const SizedBox(height: 16),

            // Commodity Selector
            Card(
              child: Padding(
                padding: const EdgeInsets.all(12.0),
                child: Row(
                  children: [
                    const Text('Commodity: ', style: TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(width: 8),
                    Expanded(
                      child: DropdownButton<String>(
                        isExpanded: true,
                        value: _selectedCommodity,
                        items: _commodities.map((c) {
                          return DropdownMenuItem<String>(
                            value: c['code'],
                            child: Text(c['name']!),
                          );
                        }).toList(),
                        onChanged: (val) {
                          if (val != null) {
                            setState(() => _selectedCommodity = val);
                            _evaluatePortability();
                          }
                        },
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            if (_evaluating)
              const Center(child: Padding(padding: EdgeInsets.all(32), child: CircularProgressIndicator()))
            else if (_error != null)
              Container(
                padding: const EdgeInsets.all(12),
                color: Colors.red.shade50,
                child: Text(_error!, style: const TextStyle(color: Colors.red)),
              )
            else if (_decision != null)
              _buildDecisionCard(context, _decision!),
          ],
        ),
      ),
    );
  }

  Widget _buildDecisionCard(BuildContext context, PortabilityDecisionModel dec) {
    Color cardColor = Colors.green.shade50;
    BadgeType badge = BadgeType.verified;

    if (dec.status == 'CONDITIONALLY_ELIGIBLE') {
      cardColor = Colors.amber.shade50;
      badge = BadgeType.pending;
    } else if (dec.status == 'INELIGIBLE') {
      cardColor = Colors.red.shade50;
      badge = BadgeType.blocked;
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Primary Decision
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
                      dec.status.replaceAll('_', ' '),
                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    StatusBadge(label: dec.status, type: badge),
                  ],
                ),
                const SizedBox(height: 12),
                if (dec.allowedQuantity != null)
                  Text(
                    'Portable Quota: ${dec.allowedQuantity} ${dec.unit}',
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                  ),
                if (dec.advisory != null) ...[
                  const SizedBox(height: 6),
                  Text(dec.advisory!, style: const TextStyle(fontSize: 13, color: Colors.black87)),
                ],
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),

        // FPS Stock Freshness Card
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    Icon(Icons.storefront, color: Colors.blueGrey),
                    SizedBox(width: 8),
                    Text('Shop Stock Freshness', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  ],
                ),
                const Divider(height: 20),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Reported State: ${dec.stockState.label}'),
                    StatusBadge(
                      label: dec.stockState.fresh ? 'FRESH OBSERVATION' : 'STALE / UNVERIFIED',
                      type: dec.stockState.fresh ? BadgeType.verified : BadgeType.unverified,
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.grey.shade100,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    dec.stockState.advisory ??
                        'Official policy: Do not make an unverified journey based solely on unverified stock claims.',
                    style: const TextStyle(fontSize: 12, color: Colors.black87),
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),

        // Required Actions & Cautions
        if (dec.actions.isNotEmpty) ...[
          const Text('Recommended Actions:', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 6),
          ...dec.actions.map((act) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  children: [
                    const Icon(Icons.check_circle_outline, size: 16, color: Colors.green),
                    const SizedBox(width: 6),
                    Expanded(child: Text(act, style: const TextStyle(fontSize: 13))),
                  ],
                ),
              )),
          const SizedBox(height: 12),
        ],

        if (dec.cautions.isNotEmpty) ...[
          const Text('Cautions & Warnings:', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.red)),
          const SizedBox(height: 6),
          ...dec.cautions.map((cau) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  children: [
                    const Icon(Icons.warning_amber_rounded, size: 16, color: Colors.red),
                    const SizedBox(width: 6),
                    Expanded(child: Text(cau, style: const TextStyle(fontSize: 13, color: Colors.red))),
                  ],
                ),
              )),
        ],
      ],
    );
  }
}
