import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/draft_model.dart';
import 'api_service.dart';

/// Manages offline-first draft persistence and sync queueing
class OfflineDraftStorage {
  static const String _storageKey = 'rationsaathi_offline_drafts';
  final SharedPreferences? _prefs;

  OfflineDraftStorage({SharedPreferences? prefs}) : _prefs = prefs;

  Future<SharedPreferences> _getPrefs() async {
    return _prefs ?? await SharedPreferences.getInstance();
  }

  Future<List<DraftModel>> loadLocalDrafts() async {
    final prefs = await _getPrefs();
    final jsonString = prefs.getString(_storageKey);
    if (jsonString == null || jsonString.isEmpty) return [];

    try {
      final list = jsonDecode(jsonString) as List<dynamic>;
      return list.map((e) => DraftModel.fromJson(e as Map<String, dynamic>)).toList();
    } catch (_) {
      return [];
    }
  }

  Future<void> saveLocalDraft(DraftModel draft) async {
    final drafts = await loadLocalDrafts();
    final index = drafts.indexWhere((d) => d.id == draft.id || d.localRef == draft.localRef);
    if (index >= 0) {
      drafts[index] = draft;
    } else {
      drafts.insert(0, draft);
    }

    final prefs = await _getPrefs();
    final jsonString = jsonEncode(drafts.map((d) => d.toJson()).toList());
    await prefs.setString(_storageKey, jsonString);
  }

  Future<void> removeDraft(String draftId) async {
    final drafts = await loadLocalDrafts();
    drafts.removeWhere((d) => d.id == draftId || d.localRef == draftId);
    final prefs = await _getPrefs();
    await prefs.setString(_storageKey, jsonEncode(drafts.map((d) => d.toJson()).toList()));
  }

  /// Attempts to synchronize queued offline drafts against the backend API
  Future<List<DraftModel>> syncAllQueuedDrafts(ApiService apiService) async {
    final drafts = await loadLocalDrafts();
    final List<DraftModel> updatedList = [];

    for (final draft in drafts) {
      if (draft.isQueued || draft.isNotSubmitted) {
        try {
          // Attempt sync
          final synced = await apiService.syncDraft(draft.id, networkOnline: true);
          updatedList.add(synced);
        } catch (_) {
          // Keep draft locally with retryable status
          updatedList.add(draft);
        }
      } else {
        updatedList.add(draft);
      }
    }

    final prefs = await _getPrefs();
    await prefs.setString(_storageKey, jsonEncode(updatedList.map((d) => d.toJson()).toList()));
    return updatedList;
  }
}
