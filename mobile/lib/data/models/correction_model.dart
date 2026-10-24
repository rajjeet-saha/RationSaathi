/// Correction Simulation & Safety Models

class CorrectionSimulationModel {
  final String? proposalId;
  final String operation;
  final String riskLevel; // 'LOW' | 'REVIEW_REQUIRED' | 'HIGH' | 'BLOCKED'
  final List<String> reasons;
  final List<String> consequences;
  final List<String> recommendations;
  final bool canSubmit;
  final bool canDraft;
  final String? notice;

  CorrectionSimulationModel({
    this.proposalId,
    required this.operation,
    required this.riskLevel,
    this.reasons = const [],
    this.consequences = const [],
    this.recommendations = const [],
    required this.canSubmit,
    required this.canDraft,
    this.notice,
  });

  bool get isBlocked => riskLevel == 'BLOCKED';
  bool get isReviewRequired => riskLevel == 'REVIEW_REQUIRED' || riskLevel == 'HIGH';
  bool get isSafe => riskLevel == 'LOW';

  factory CorrectionSimulationModel.fromJson(Map<String, dynamic> json) {
    return CorrectionSimulationModel(
      proposalId: json['proposal_id'] as String?,
      operation: json['operation'] as String? ?? 'UPDATE_FIELD',
      riskLevel: json['risk_level'] as String? ?? 'REVIEW_REQUIRED',
      reasons: (json['reasons'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      consequences: (json['consequences'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      recommendations: (json['recommendations'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      canSubmit: json['can_submit'] as bool? ?? false,
      canDraft: json['can_draft'] as bool? ?? false,
      notice: json['notice'] as String?,
    );
  }
}
