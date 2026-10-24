import 'package:flutter/foundation.dart';
import '../data/models/draft_model.dart';
import '../data/services/api_service.dart';
import '../data/services/offline_draft_storage.dart';

class DraftProvider extends ChangeNotifier {
  final ApiService _apiService;
  final OfflineDraftStorage _storage;

  List<DraftModel> _drafts = [];
  bool _isLoading = false;
  String? _syncStatusMessage;

  DraftProvider({
    required ApiService apiService,
    required OfflineDraftStorage storage,
  })  : _apiService = apiService,
        _storage = storage;

  List<DraftModel> get drafts => _drafts;
  bool get isLoading => _isLoading;
  String? get syncStatusMessage => _syncStatusMessage;

  Future<void> loadDrafts() async {
    _isLoading = true;
    notifyListeners();

    try {
      // 1. Load local offline drafts
      final localDrafts = await _storage.loadLocalDrafts();

      // 2. Fetch server drafts if session is active
      List<DraftModel> serverDrafts = [];
      if (_apiService.sessionToken != null) {
        try {
          serverDrafts = await _apiService.getDrafts();
        } catch (_) {}
      }

      // Merge avoiding duplicates (server takes precedence if synced)
      final Map<String, DraftModel> merged = {};
      for (final d in localDrafts) {
        merged[d.id.isNotEmpty ? d.id : d.localRef] = d;
      }
      for (final d in serverDrafts) {
        merged[d.id] = d;
      }

      _drafts = merged.values.toList();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> stageOfflineDraft({
    required String kind,
    required String householdId,
    String? memberId,
    required Map<String, dynamic> payload,
  }) async {
    final newDraft = DraftModel(
      id: 'local-${DateTime.now().millisecondsSinceEpoch}',
      kind: kind,
      status: 'DRAFT_NOT_SUBMITTED',
      householdId: householdId,
      memberId: memberId,
      localRef: 'REF-${DateTime.now().millisecondsSinceEpoch}',
      version: 1,
      payload: payload,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
      retryable: true,
    );

    await _storage.saveLocalDraft(newDraft);
    await loadDrafts();
  }

  Future<void> syncAllDrafts() async {
    _isLoading = true;
    _syncStatusMessage = 'Synchronizing drafts with server...';
    notifyListeners();

    try {
      await _storage.syncAllQueuedDrafts(_apiService);
      await loadDrafts();
      _syncStatusMessage = 'Sync completed.';
    } catch (e) {
      _syncStatusMessage = 'Sync failed. Drafts remain securely stored offline.';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> verifySubmissionReceipt(String draftId) async {
    _isLoading = true;
    notifyListeners();

    try {
      final updated = await _apiService.verifyDraftSubmission(draftId, simulateReceipt: true);
      await _storage.saveLocalDraft(updated);
      await loadDrafts();
      return true;
    } catch (_) {
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
