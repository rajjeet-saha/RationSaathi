import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../data/models/draft_model.dart';
import '../providers/draft_provider.dart';
import '../providers/session_provider.dart';
import '../widgets/status_badge.dart';

class OfflineDraftsScreen extends StatefulWidget {
  const OfflineDraftsScreen({super.key});

  @override
  State<OfflineDraftsScreen> createState() => _OfflineDraftsScreenState();
}

class _OfflineDraftsScreenState extends State<OfflineDraftsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<DraftProvider>(context, listen: false).loadDrafts();
    });
  }

  void _showNewDraftDialog() {
    final sessionProv = Provider.of<SessionProvider>(context, listen: false);
    final householdId = sessionProv.household?.id ?? '';
    final memberId = sessionProv.activeMember?.id;
    final noteController = TextEditingController();

    showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          title: const Text('Create Offline Draft'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Drafts are stored securely on this device and are clearly marked "NOT SUBMITTED" until receipt confirmation.',
                style: TextStyle(fontSize: 12, color: Colors.black54),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: noteController,
                decoration: const InputDecoration(
                  labelText: 'Draft Purpose / Note',
                  border: OutlineInputBorder(),
                  hintText: 'e.g., Update residential address for migrant grain quota',
                ),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () async {
                if (noteController.text.isNotEmpty) {
                  Navigator.pop(ctx);
                  final draftProv = Provider.of<DraftProvider>(context, listen: false);
                  await draftProv.stageOfflineDraft(
                    kind: 'PORTABILITY_REQUEST',
                    householdId: householdId,
                    memberId: memberId,
                    payload: {'note': noteController.text, 'client_staged': true},
                  );
                }
              },
              child: const Text('Save Offline'),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final draftProv = Provider.of<DraftProvider>(context);

    return Scaffold(
      body: RefreshIndicator(
        onRefresh: draftProv.loadDrafts,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('Offline Drafts Queue', style: Theme.of(context).textTheme.headlineMedium),
                  IconButton(
                    icon: const Icon(Icons.add_circle, color: Colors.teal, size: 28),
                    tooltip: 'New Offline Draft',
                    onPressed: _showNewDraftDialog,
                  ),
                ],
              ),
              const SizedBox(height: 6),
              const Text(
                'Truth in state: Drafts remain local until connected to an authorised adapter with a cryptographic receipt.',
                style: TextStyle(fontSize: 13, color: Colors.black54),
              ),
              const SizedBox(height: 12),

              // Sync & Network Actions
              Card(
                color: Colors.blueGrey.shade50,
                child: Padding(
                  padding: const EdgeInsets.all(12.0),
                  child: Row(
                    children: [
                      const Icon(Icons.sync, color: Colors.blueGrey),
                      const SizedBox(width: 10),
                      const Expanded(
                        child: Text(
                          'Sync Worker Ready',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                        ),
                      ),
                      ElevatedButton(
                        onPressed: draftProv.isLoading ? null : draftProv.syncAllDrafts,
                        child: const Text('Sync All'),
                      ),
                    ],
                  ),
                ),
              ),
              if (draftProv.syncStatusMessage != null) ...[
                const SizedBox(height: 8),
                Text(
                  draftProv.syncStatusMessage!,
                  style: TextStyle(fontSize: 12, color: Colors.blueGrey.shade800, fontStyle: FontStyle.italic),
                ),
              ],
              const SizedBox(height: 16),

              if (draftProv.isLoading && draftProv.drafts.isEmpty)
                const Center(child: Padding(padding: EdgeInsets.all(32), child: CircularProgressIndicator()))
              else if (draftProv.drafts.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(24.0),
                    child: Center(
                      child: Text('No offline drafts pending. Click + above to stage an offline request.'),
                    ),
                  ),
                )
              else
                ...draftProv.drafts.map((d) => _buildDraftCard(context, d, draftProv)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDraftCard(BuildContext context, DraftModel draft, DraftProvider prov) {
    BadgeType badge = BadgeType.unverified;
    if (draft.isConfirmed) {
      badge = BadgeType.verified;
    } else if (draft.isQueued) {
      badge = BadgeType.pending;
    }

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
                  draft.kind.replaceAll('_', ' '),
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                ),
                StatusBadge(label: draft.status.replaceAll('_', ' '), type: badge),
              ],
            ),
            const SizedBox(height: 6),
            Text('Local Reference: ${draft.localRef}', style: const TextStyle(fontSize: 12, fontFamily: 'monospace')),
            if (draft.receipt != null) ...[
              const SizedBox(height: 4),
              Text(
                'Receipt: ${draft.receipt}',
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.teal),
              ),
            ],
            if (draft.payload.containsKey('note')) ...[
              const SizedBox(height: 8),
              Text('Note: ${draft.payload['note']}', style: const TextStyle(fontSize: 13)),
            ],
            const Divider(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                if (!draft.isConfirmed) ...[
                  OutlinedButton(
                    onPressed: () => prov.verifySubmissionReceipt(draft.id),
                    child: const Text('Verify Receipt'),
                  ),
                ] else
                  const Text('✅ Verified in adapter', style: TextStyle(fontSize: 12, color: Colors.green, fontWeight: FontWeight.bold)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
