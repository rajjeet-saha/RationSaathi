import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../../core/constants/api_endpoints.dart';
import '../models/session_model.dart';
import '../models/household_model.dart';
import '../models/portability_model.dart';
import '../models/correction_model.dart';
import '../models/draft_model.dart';
import '../models/grievance_model.dart';

class ApiException implements Exception {
  final int statusCode;
  final String message;
  final dynamic details;

  ApiException({required this.statusCode, required this.message, this.details});

  @override
  String toString() => 'ApiException [$statusCode]: $message';
}

/// Core API client communicating with FastAPI backend
class ApiService {
  final http.Client _client;
  
  // In-memory token storage only
  String? _sessionToken;

  ApiService({http.Client? client}) : _client = client ?? http.Client();

  String? get sessionToken => _sessionToken;

  void setSessionToken(String? token) {
    _sessionToken = token;
  }

  void clearSession() {
    _sessionToken = null;
  }

  Map<String, String> _buildHeaders() {
    final headers = {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    };
    if (_sessionToken != null && _sessionToken!.isNotEmpty) {
      headers['X-Ration-Session'] = _sessionToken!;
    }
    return headers;
  }

  Future<dynamic> _handleResponse(http.Response response) async {
    dynamic body;
    try {
      body = jsonDecode(response.body);
    } catch (_) {
      body = {'detail': response.body};
    }

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return body;
    }

    if (response.statusCode == 401) {
      clearSession();
    }

    final message = (body is Map && body.containsKey('detail'))
        ? body['detail'].toString()
        : 'Request failed with status code ${response.statusCode}';

    throw ApiException(
      statusCode: response.statusCode,
      message: message,
      details: body,
    );
  }

  // Health
  Future<Map<String, dynamic>> checkHealth() async {
    final url = Uri.parse('${ApiEndpoints.baseUrl}${ApiEndpoints.health}');
    final res = await _client.get(url, headers: _buildHeaders());
    return await _handleResponse(res) as Map<String, dynamic>;
  }

  // Demo Profiles Directory
  Future<List<Map<String, dynamic>>> getDemoProfiles() async {
    final url = Uri.parse('${ApiEndpoints.baseUrl}${ApiEndpoints.demoProfiles}');
    final res = await _client.get(url, headers: _buildHeaders());
    final data = await _handleResponse(res) as Map<String, dynamic>;
    return (data['households'] as List<dynamic>?)
            ?.map((e) => e as Map<String, dynamic>)
            .toList() ??
        [];
  }

  // Start Session (Member or Facilitator)
  Future<SessionModel> startSession({
    required String householdId,
    String role = 'MEMBER',
    String? memberId,
    String purpose = 'MEMBER_SELF_SERVICE',
    String? facilitatorDevice,
  }) async {
    final url = Uri.parse('${ApiEndpoints.baseUrl}${ApiEndpoints.sessions}');
    final body = jsonEncode({
      'household_id': householdId,
      'role': role,
      'member_id': memberId,
      'purpose': purpose,
      'facilitator_device': facilitatorDevice,
    });

    final res = await _client.post(url, headers: _buildHeaders(), body: body);
    final data = await _handleResponse(res) as Map<String, dynamic>;
    
    // Extract token from header or body
    final token = res.headers['x-ration-session'] ?? data['token'] ?? data['session_id'] ?? '';
    setSessionToken(token);
    return SessionModel.fromJson(data, token);
  }

  // Facilitator Confirm Consent
  Future<void> confirmConsent({
    required String memberId,
    required bool consentExplained,
    required bool consentGiven,
  }) async {
    final url = Uri.parse('${ApiEndpoints.baseUrl}${ApiEndpoints.sessionConsent}');
    final body = jsonEncode({
      'member_id': memberId,
      'consent_explained': consentExplained,
      'consent_given': consentGiven,
    });
    final res = await _client.post(url, headers: _buildHeaders(), body: body);
    await _handleResponse(res);
  }

  // Safe Profile Switch
  Future<SessionModel> switchProfile(String memberId) async {
    final url = Uri.parse('${ApiEndpoints.baseUrl}${ApiEndpoints.sessionSwitch}');
    final body = jsonEncode({'member_id': memberId});
    final res = await _client.post(url, headers: _buildHeaders(), body: body);
    final data = await _handleResponse(res) as Map<String, dynamic>;
    final token = res.headers['x-ration-session'] ?? _sessionToken ?? '';
    return SessionModel.fromJson(data, token);
  }

  // End Session
  Future<void> endSession() async {
    try {
      final url = Uri.parse('${ApiEndpoints.baseUrl}${ApiEndpoints.sessionEnd}');
      final body = jsonEncode({
        'reason': 'USER_LOGOUT',
        'client_cleanup_confirmed': true,
      });
      await _client.post(url, headers: _buildHeaders(), body: body);
    } finally {
      clearSession();
    }
  }

  // Household Overview
  Future<HouseholdModel> getHouseholdOverview() async {
    final url = Uri.parse('${ApiEndpoints.baseUrl}${ApiEndpoints.householdCurrent}');
    final res = await _client.get(url, headers: _buildHeaders());
    final data = await _handleResponse(res) as Map<String, dynamic>;
    return HouseholdModel.fromJson(data);
  }

  // Member Entitlements
  Future<List<EntitlementModel>> getMemberEntitlements(String memberId) async {
    final url = Uri.parse('${ApiEndpoints.baseUrl}${ApiEndpoints.memberEntitlements(memberId)}');
    final res = await _client.get(url, headers: _buildHeaders());
    final data = await _handleResponse(res) as Map<String, dynamic>;
    final list = data['entitlements'] as List<dynamic>? ?? [];
    return list.map((e) => EntitlementModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  // Portability Evaluation
  Future<PortabilityDecisionModel> evaluatePortability({
    required String memberId,
    required String commodityCode,
  }) async {
    final url = Uri.parse('${ApiEndpoints.baseUrl}${ApiEndpoints.portabilityEvaluate}');
    final body = jsonEncode({
      'member_id': memberId,
      'commodity_code': commodityCode,
    });
    final res = await _client.post(url, headers: _buildHeaders(), body: body);
    final data = await _handleResponse(res) as Map<String, dynamic>;
    return PortabilityDecisionModel.fromJson(data);
  }

  // Safe Correction Simulation
  Future<CorrectionSimulationModel> simulateCorrection({
    required String operation,
    required String memberId,
    Map<String, dynamic>? fields,
    Map<String, dynamic>? newMember,
    List<String> evidence = const [],
    String? reason,
  }) async {
    final url = Uri.parse('${ApiEndpoints.baseUrl}${ApiEndpoints.correctionSimulate}');
    final body = jsonEncode({
      'operation': operation,
      'member_id': memberId,
      'fields': fields ?? {},
      'new_member': newMember,
      'evidence': evidence,
      'reason': reason,
    });
    final res = await _client.post(url, headers: _buildHeaders(), body: body);
    final data = await _handleResponse(res) as Map<String, dynamic>;
    return CorrectionSimulationModel.fromJson(data);
  }

  // Drafts: List
  Future<List<DraftModel>> getDrafts() async {
    final url = Uri.parse('${ApiEndpoints.baseUrl}${ApiEndpoints.drafts}');
    final res = await _client.get(url, headers: _buildHeaders());
    final data = await _handleResponse(res) as Map<String, dynamic>;
    final list = data['drafts'] as List<dynamic>? ?? [];
    return list.map((e) => DraftModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  // Drafts: Sync
  Future<DraftModel> syncDraft(String draftId, {bool networkOnline = true}) async {
    final url = Uri.parse('${ApiEndpoints.baseUrl}${ApiEndpoints.draftSync(draftId)}');
    final body = jsonEncode({'network_online': networkOnline});
    final res = await _client.post(url, headers: _buildHeaders(), body: body);
    final data = await _handleResponse(res) as Map<String, dynamic>;
    return DraftModel.fromJson(data);
  }

  // Drafts: Verify Submission Receipt
  Future<DraftModel> verifyDraftSubmission(String draftId, {bool simulateReceipt = true}) async {
    final url = Uri.parse('${ApiEndpoints.baseUrl}${ApiEndpoints.draftVerify(draftId)}');
    final body = jsonEncode({'simulate_receipt': simulateReceipt});
    final res = await _client.post(url, headers: _buildHeaders(), body: body);
    final data = await _handleResponse(res) as Map<String, dynamic>;
    return DraftModel.fromJson(data);
  }

  // Grievances: List
  Future<List<GrievanceModel>> getGrievances() async {
    final url = Uri.parse('${ApiEndpoints.baseUrl}${ApiEndpoints.grievances}');
    final res = await _client.get(url, headers: _buildHeaders());
    final data = await _handleResponse(res) as Map<String, dynamic>;
    final list = data['grievances'] as List<dynamic>? ?? [];
    return list.map((e) => GrievanceModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  // Grievance: Detail
  Future<GrievanceModel> getGrievanceDetail(String id) async {
    final url = Uri.parse('${ApiEndpoints.baseUrl}${ApiEndpoints.grievance(id)}');
    final res = await _client.get(url, headers: _buildHeaders());
    final data = await _handleResponse(res) as Map<String, dynamic>;
    return GrievanceModel.fromJson(data);
  }

  // Grievance: Generate Escalation Draft
  Future<Map<String, dynamic>> createEscalationDraft(String id, {String? recipientOffice}) async {
    final url = Uri.parse('${ApiEndpoints.baseUrl}${ApiEndpoints.escalationDraft(id)}');
    final body = jsonEncode({'recipient_office': recipientOffice});
    final res = await _client.post(url, headers: _buildHeaders(), body: body);
    return await _handleResponse(res) as Map<String, dynamic>;
  }
}
