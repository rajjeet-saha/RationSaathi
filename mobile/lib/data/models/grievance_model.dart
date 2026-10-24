/// Grievance & Escalation Models

class GrievanceEventModel {
  final String id;
  final String eventType;
  final String description;
  final DateTime recordedAt;
  final String performedBy;

  GrievanceEventModel({
    required this.id,
    required this.eventType,
    required this.description,
    required this.recordedAt,
    required this.performedBy,
  });

  factory GrievanceEventModel.fromJson(Map<String, dynamic> json) {
    return GrievanceEventModel(
      id: json['id'] as String? ?? '',
      eventType: json['event_type'] as String? ?? '',
      description: json['description'] as String? ?? '',
      recordedAt: json['recorded_at'] != null
          ? DateTime.tryParse(json['recorded_at'].toString()) ?? DateTime.now()
          : DateTime.now(),
      performedBy: json['performed_by'] as String? ?? 'System',
    );
  }
}

class GrievanceModel {
  final String id;
  final String trackingNumber;
  final String category;
  final String status; // 'FILED' | 'ACKNOWLEDGED' | 'IN_PROGRESS' | 'RESOLVED' | 'REJECTED' | 'ESCALATED'
  final bool isOverdue;
  final DateTime? targetResolutionDate;
  final bool deadlineVerified;
  final int daysElapsed;
  final String summary;
  final String details;
  final bool canEscalate;
  final List<GrievanceEventModel> events;

  GrievanceModel({
    required this.id,
    required this.trackingNumber,
    required this.category,
    required this.status,
    required this.isOverdue,
    this.targetResolutionDate,
    required this.deadlineVerified,
    required this.daysElapsed,
    required this.summary,
    required this.details,
    required this.canEscalate,
    this.events = const [],
  });

  factory GrievanceModel.fromJson(Map<String, dynamic> json) {
    final evs = (json['events'] as List<dynamic>?)
            ?.map((e) => GrievanceEventModel.fromJson(e as Map<String, dynamic>))
            .toList() ??
        [];

    return GrievanceModel(
      id: json['id'] as String? ?? '',
      trackingNumber: json['tracking_number'] as String? ?? '',
      category: json['category'] as String? ?? 'GENERAL',
      status: json['status'] as String? ?? 'FILED',
      isOverdue: json['is_overdue'] as bool? ?? false,
      targetResolutionDate: json['target_resolution_date'] != null
          ? DateTime.tryParse(json['target_resolution_date'].toString())
          : null,
      deadlineVerified: json['deadline_verified'] as bool? ?? false,
      daysElapsed: json['days_elapsed'] as int? ?? 0,
      summary: json['summary'] as String? ?? '',
      details: json['details'] as String? ?? '',
      canEscalate: json['can_escalate'] as bool? ?? false,
      events: evs,
    );
  }
}
