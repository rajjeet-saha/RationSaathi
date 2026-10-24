import 'package:flutter/foundation.dart';
import '../data/models/session_model.dart';
import '../data/models/household_model.dart';
import '../data/services/api_service.dart';

class SessionProvider extends ChangeNotifier {
  final ApiService _apiService;

  SessionModel? _currentSession;
  HouseholdModel? _household;
  bool _isLoading = false;
  String? _errorMessage;

  SessionProvider({required ApiService apiService}) : _apiService = apiService;

  SessionModel? get currentSession => _currentSession;
  HouseholdModel? get household => _household;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  bool get isAuthenticated => _currentSession != null;
  bool get isFacilitator => _currentSession?.isFacilitator ?? false;

  MemberModel? get activeMember {
    if (_household == null || _currentSession == null) return null;
    return _household!.currentMember;
  }

  Future<void> signInAsMember({
    required String householdId,
    required String memberId,
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      _currentSession = await _apiService.startSession(
        householdId: householdId,
        role: 'MEMBER',
        memberId: memberId,
      );
      _household = await _apiService.getHouseholdOverview();
    } catch (e) {
      _errorMessage = e.toString();
      _currentSession = null;
      _household = null;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> signInAsFacilitator({
    required String householdId,
    String? deviceName,
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      _currentSession = await _apiService.startSession(
        householdId: householdId,
        role: 'FACILITATOR',
        facilitatorDevice: deviceName ?? 'Android Mobile Device',
      );
      _household = await _apiService.getHouseholdOverview();
    } catch (e) {
      _errorMessage = e.toString();
      _currentSession = null;
      _household = null;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> grantFacilitatorConsent({
    required String memberId,
    required bool consentExplained,
    required bool consentGiven,
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      await _apiService.confirmConsent(
        memberId: memberId,
        consentExplained: consentExplained,
        consentGiven: consentGiven,
      );
      // Refresh household after consent
      _household = await _apiService.getHouseholdOverview();
      return true;
    } catch (e) {
      _errorMessage = e.toString();
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> switchProfile(String memberId) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      _currentSession = await _apiService.switchProfile(memberId);
      _household = await _apiService.getHouseholdOverview();
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> refreshHousehold() async {
    if (_currentSession == null) return;
    try {
      _household = await _apiService.getHouseholdOverview();
      notifyListeners();
    } catch (_) {}
  }

  Future<void> signOut() async {
    try {
      await _apiService.endSession();
    } catch (_) {
      _apiService.clearSession();
    } finally {
      _currentSession = null;
      _household = null;
      _errorMessage = null;
      notifyListeners();
    }
  }
}
