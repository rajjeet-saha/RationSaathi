/// Household, Member, and Entitlement Domain Models

class RemainingQty {
  final String state; // 'VERIFIED' | 'SYNTHETIC_UNVERIFIED' | 'UNABLE_TO_VERIFY'
  final String display;
  final String note;

  RemainingQty({required this.state, required this.display, required this.note});

  factory RemainingQty.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return RemainingQty(state: 'UNABLE_TO_VERIFY', display: '0', note: 'Not verified');
    }
    return RemainingQty(
      state: json['state'] as String? ?? 'UNABLE_TO_VERIFY',
      display: json['display'] as String? ?? '0',
      note: json['note'] as String? ?? '',
    );
  }
}

class EntitlementModel {
  final String id;
  final String commodityCode;
  final String commodityName;
  final String period;
  final String unit;
  final double? entitledQty;
  final double? drawnQty;
  final RemainingQty remaining;
  final String provenance;
  final String provenanceLabel;
  final String verificationStatus;
  final bool isSynthetic;

  EntitlementModel({
    required this.id,
    required this.commodityCode,
    required this.commodityName,
    required this.period,
    required this.unit,
    this.entitledQty,
    this.drawnQty,
    required this.remaining,
    required this.provenance,
    required this.provenanceLabel,
    required this.verificationStatus,
    required this.isSynthetic,
  });

  factory EntitlementModel.fromJson(Map<String, dynamic> json) {
    return EntitlementModel(
      id: json['id'] as String? ?? '',
      commodityCode: json['commodity_code'] as String? ?? '',
      commodityName: json['commodity_name'] as String? ?? json['commodity_code'] as String? ?? 'Grain',
      period: json['period'] as String? ?? '',
      unit: json['unit'] as String? ?? 'kg',
      entitledQty: (json['entitled_qty'] as num?)?.toDouble(),
      drawnQty: (json['drawn_qty'] as num?)?.toDouble(),
      remaining: RemainingQty.fromJson(json['remaining'] as Map<String, dynamic>?),
      provenance: json['provenance'] as String? ?? 'SYNTHETIC_DEMO',
      provenanceLabel: json['provenance_label'] as String? ?? 'Synthetic Demo',
      verificationStatus: json['verification_status'] as String? ?? 'UNVERIFIED',
      isSynthetic: json['is_synthetic'] as bool? ?? true,
    );
  }
}

class MemberModel {
  final String id;
  final String householdId;
  final String alias;
  final String fullName;
  final int? age;
  final String? ageBand;
  final String membershipStatus;
  final String? relationship;
  final String verificationState;
  final String provenance;
  final String provenanceLabel;
  final bool isHead;
  final bool isAbsent;
  final bool isDependent;
  final String? privacyNotice;
  final List<EntitlementModel> entitlements;

  MemberModel({
    required this.id,
    required this.householdId,
    required this.alias,
    required this.fullName,
    this.age,
    this.ageBand,
    required this.membershipStatus,
    this.relationship,
    required this.verificationState,
    required this.provenance,
    required this.provenanceLabel,
    this.isHead = false,
    this.isAbsent = false,
    this.isDependent = false,
    this.privacyNotice,
    this.entitlements = const [],
  });

  factory MemberModel.fromJson(Map<String, dynamic> json) {
    final entList = (json['entitlements'] as List<dynamic>?)
            ?.map((e) => EntitlementModel.fromJson(e as Map<String, dynamic>))
            .toList() ??
        [];

    return MemberModel(
      id: json['id'] as String? ?? '',
      householdId: json['household_id'] as String? ?? '',
      alias: json['alias'] as String? ?? '',
      fullName: json['full_name'] as String? ?? json['alias'] as String? ?? '',
      age: json['age'] as int?,
      ageBand: json['age_band'] as String?,
      membershipStatus: json['membership_status'] as String? ?? 'ACTIVE',
      relationship: json['relationship'] as String?,
      verificationState: json['verification_state'] as String? ?? 'UNVERIFIED',
      provenance: json['provenance'] as String? ?? 'SYNTHETIC_DEMO',
      provenanceLabel: json['provenance_label'] as String? ?? 'Synthetic Demo',
      isHead: json['is_head'] as bool? ?? false,
      isAbsent: json['is_absent'] as bool? ?? false,
      isDependent: json['is_dependent'] as bool? ?? false,
      privacyNotice: json['privacy_notice'] as String?,
      entitlements: entList,
    );
  }
}

class HouseholdModel {
  final String id;
  final String reference;
  final String label;
  final String homeState;
  final String destinationState;
  final int memberCount;
  final bool isSynthetic;
  final MemberModel? currentMember;
  final List<EntitlementModel> ownEntitlements;
  final String? notice;

  HouseholdModel({
    required this.id,
    required this.reference,
    required this.label,
    required this.homeState,
    required this.destinationState,
    required this.memberCount,
    required this.isSynthetic,
    this.currentMember,
    this.ownEntitlements = const [],
    this.notice,
  });

  factory HouseholdModel.fromJson(Map<String, dynamic> json) {
    final memberJson = json['current_member'] as Map<String, dynamic>?;
    final ownEnts = (json['own_entitlements'] as List<dynamic>?)
            ?.map((e) => EntitlementModel.fromJson(e as Map<String, dynamic>))
            .toList() ??
        [];

    return HouseholdModel(
      id: json['id'] as String? ?? '',
      reference: json['reference'] as String? ?? '',
      label: json['label'] as String? ?? '',
      homeState: json['home_state'] as String? ?? '',
      destinationState: json['destination_state'] as String? ?? '',
      memberCount: json['member_count'] as int? ?? 1,
      isSynthetic: json['is_synthetic'] as bool? ?? true,
      currentMember: memberJson != null ? MemberModel.fromJson(memberJson) : null,
      ownEntitlements: ownEnts,
      notice: json['notice'] as String?,
    );
  }
}
