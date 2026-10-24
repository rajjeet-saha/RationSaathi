import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:rationsaathi_mobile/data/models/draft_model.dart';
import 'package:rationsaathi_mobile/data/services/offline_draft_storage.dart';

void main() {
  group('Offline Drafts & Truth in State Tests', () {
    test('New draft starts with DRAFT_NOT_SUBMITTED and preserves local reference', () {
      final draft = DraftModel(
        id: 'local-test-1',
        kind: 'CORRECTION',
        status: 'DRAFT_NOT_SUBMITTED',
        householdId: 'hh-1',
        localRef: 'LOCAL-REF-99',
        version: 1,
        payload: {'field': 'alias', 'value': 'New Name'},
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
        retryable: true,
      );

      expect(draft.isNotSubmitted, isTrue);
      expect(draft.isConfirmed, isFalse);
      expect(draft.localRef, 'LOCAL-REF-99');
      expect(draft.receipt, isNull);
    });

    test('Draft requires verified adapter receipt before claiming confirmed submission', () {
      final unconfirmedDraft = DraftModel(
        id: 'draft-101',
        kind: 'GRIEVANCE',
        status: 'SUBMISSION_PENDING_VERIFICATION',
        householdId: 'hh-1',
        localRef: 'REF-101',
        version: 1,
        payload: {},
        receipt: null,
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );

      expect(unconfirmedDraft.isConfirmed, isFalse);

      final confirmedDraft = DraftModel(
        id: 'draft-101',
        kind: 'GRIEVANCE',
        status: 'SUBMITTED_CONFIRMED',
        householdId: 'hh-1',
        localRef: 'REF-101',
        version: 2,
        payload: {},
        receipt: 'SIM-RECEIPT-2026',
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );

      expect(confirmedDraft.isConfirmed, isTrue);
      expect(confirmedDraft.receipt, 'SIM-RECEIPT-2026');
    });

    test('Offline draft persistence survives store and load cycle', () async {
      SharedPreferences.setMockInitialValues({});
      final storage = OfflineDraftStorage();

      final draft = DraftModel(
        id: 'offline-001',
        kind: 'PORTABILITY_REQUEST',
        status: 'QUEUED_FOR_SYNC',
        householdId: 'hh-demo',
        localRef: 'REF-LOCAL-001',
        version: 1,
        payload: {'note': 'Staged while disconnected'},
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );

      await storage.saveLocalDraft(draft);
      final loaded = await storage.loadLocalDrafts();

      expect(loaded.length, 1);
      expect(loaded.first.id, 'offline-001');
      expect(loaded.first.payload['note'], 'Staged while disconnected');
      expect(loaded.first.isQueued, isTrue);
    });
  });
}
