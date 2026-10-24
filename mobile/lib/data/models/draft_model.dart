/// Offline Draft & Synchronization Models

class DraftModel {
  final String id;
  final String kind; // 'CORRECTION' | 'GRIEVANCE' | 'PORTABILITY_REQUEST' | 'ASSISTED_FORM'
  final String status; // 'DRAFT_NOT_SUBMITTED' | 'QUEUED_FOR_SYNC' | 'SYNC_IN_PROGRESS' | 'SUBMISSION_PENDING_VERIFICATION' | 'SUBMITTED_CONFIRMED' | 'SUBMISSION_FAILED' | 'CANCELLED'
  final String householdId;
  final String? memberId;
  final String localRef;
  final int version;
  final Map<String, dynamic> payload;
  final String? receipt;
  final String? submissionStatus;
  final bool retryable;
  final DateTime createdAt;
  final DateTime updatedAt;

  DraftModel({
    required this.id,
    required this.kind,
    required this.status,
    required this.householdId,
    this.memberId,
    required this.localRef,
    required this.version,
    required this.payload,
    this.receipt,
    this.submissionStatus,
    this.retryable = true,
    required this.createdAt,
    required this.updatedAt,
  });

  bool get isConfirmed => status == 'SUBMITTED_CONFIRMED';
  bool get isPendingVerification => status == 'SUBMISSION_PENDING_VERIFICATION';
  bool get isQueued => status == 'QUEUED_FOR_SYNC';
  bool get isNotSubmitted => status == 'DRAFT_NOT_SUBMITTED';

  factory DraftModel.fromJson(Map<String, dynamic> json) {
    return DraftModel(
      id: json['id'] as String? ?? '',
      kind: json['kind'] as String? ?? 'CORRECTION',
      status: json['status'] as String? ?? 'DRAFT_NOT_SUBMITTED',
      householdId: json['household_id'] as String? ?? '',
      memberId: json['member_id'] as String?,
      localRef: json['local_ref'] as String? ?? 'local-draft',
      version: json['version'] as int? ?? 1,
      payload: json['payload'] as Map<String, dynamic>? ?? {},
      receipt: json['receipt'] as String?,
      submissionStatus: json['submission_status'] as String?,
      retryable: json['retryable'] as bool? ?? true,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString()) ?? DateTime.now()
          : DateTime.now(),
      updatedAt: json['updated_at'] != null
          ? DateTime.tryParse(json['updated_at'].toString()) ?? DateTime.now()
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'kind': kind,
      'status': status,
      'household_id': householdId,
      'member_id': memberId,
      'local_ref': localRef,
      'version': version,
      'payload': payload,
      'receipt': receipt,
      'submission_status': submissionStatus,
      'retryable': retryable,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}
