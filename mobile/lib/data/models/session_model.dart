/// In-Memory Session and Authentication Model
/// Note: Authentication tokens are stored in-memory only and never persisted to local disk,
/// ensuring zero leakage on shared devices or profile switches.
class SessionModel {
  final String token;
  final String sessionId;
  final String role; // 'MEMBER' | 'FACILITATOR' | 'ADMIN' | 'PUBLIC'
  final String householdId;
  final String householdReference;
  final String householdLabel;
  final String homeState;
  final String destinationState;
  final String? memberId;
  final String? memberName;
  final List<String> permissions;
  final List<String> consentMemberIds;
  final DateTime? expiresAt;
  final String? demoNotice;

  SessionModel({
    required this.token,
    required this.sessionId,
    required this.role,
    required this.householdId,
    required this.householdReference,
    required this.householdLabel,
    required this.homeState,
    required this.destinationState,
    this.memberId,
    this.memberName,
    this.permissions = const [],
    this.consentMemberIds = const [],
    this.expiresAt,
    this.demoNotice,
  });

  bool get isFacilitator => role == 'FACILITATOR';
  bool get isMember => role == 'MEMBER';

  bool hasConsent(String targetMemberId) {
    if (isMember) return memberId == targetMemberId;
    return consentMemberIds.contains(targetMemberId);
  }

  factory SessionModel.fromJson(Map<String, dynamic> json, String token) {
    final household = json['household'] as Map<String, dynamic>? ?? {};
    final member = json['member'] as Map<String, dynamic>?;

    return SessionModel(
      token: token,
      sessionId: json['session_id'] as String? ?? '',
      role: json['role'] as String? ?? 'MEMBER',
      householdId: household['id'] as String? ?? '',
      householdReference: household['reference'] as String? ?? '',
      householdLabel: household['label'] as String? ?? '',
      homeState: household['home_state'] as String? ?? '',
      destinationState: household['destination_state'] as String? ?? '',
      memberId: member?['id'] as String?,
      memberName: member?['full_name'] as String? ?? member?['alias'] as String?,
      permissions: (json['permissions'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      consentMemberIds: (json['consent_member_ids'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      expiresAt: json['expires_at'] != null ? DateTime.tryParse(json['expires_at'].toString()) : null,
      demoNotice: json['demo_notice'] as String?,
    );
  }
}
