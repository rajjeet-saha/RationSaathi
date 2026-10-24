/// Portability & Interstate Grain Allocation Evaluation Models

class StockStateModel {
  final String source;
  final String state; // 'AVAILABLE' | 'OUT_OF_STOCK' | 'STALE' | 'UNKNOWN'
  final bool fresh;
  final String label;
  final String? advisory;
  final String? asOf;

  StockStateModel({
    required this.source,
    required this.state,
    required this.fresh,
    required this.label,
    this.advisory,
    this.asOf,
  });

  factory StockStateModel.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return StockStateModel(
        source: 'UNKNOWN',
        state: 'UNKNOWN',
        fresh: false,
        label: 'Stock unverified',
      );
    }
    return StockStateModel(
      source: json['source'] as String? ?? 'UNKNOWN',
      state: json['state'] as String? ?? 'UNKNOWN',
      fresh: json['fresh'] as bool? ?? false,
      label: json['label'] as String? ?? 'Unknown',
      advisory: json['advisory'] as String?,
      asOf: json['as_of'] as String?,
    );
  }
}

class PortabilityDecisionModel {
  final String status; // 'ELIGIBLE' | 'CONDITIONALLY_ELIGIBLE' | 'INELIGIBLE' | 'UNABLE_TO_DETERMINE'
  final String commodityCode;
  final String commodityName;
  final String unit;
  final double? allowedQuantity;
  final StockStateModel stockState;
  final List<String> actions;
  final List<String> cautions;
  final String? advisory;
  final String? notice;

  PortabilityDecisionModel({
    required this.status,
    required this.commodityCode,
    required this.commodityName,
    required this.unit,
    this.allowedQuantity,
    required this.stockState,
    this.actions = const [],
    this.cautions = const [],
    this.advisory,
    this.notice,
  });

  bool get isEligible => status == 'ELIGIBLE';
  bool get isConditional => status == 'CONDITIONALLY_ELIGIBLE';
  bool get isBlocked => status == 'INELIGIBLE';

  factory PortabilityDecisionModel.fromJson(Map<String, dynamic> json) {
    final commodity = json['commodity'] as Map<String, dynamic>? ?? {};
    final stock = json['stock_state'] as Map<String, dynamic>?;

    return PortabilityDecisionModel(
      status: json['status'] as String? ?? 'UNABLE_TO_DETERMINE',
      commodityCode: commodity['code'] as String? ?? json['commodity_code'] as String? ?? '',
      commodityName: commodity['name'] as String? ?? 'Commodity',
      unit: commodity['unit'] as String? ?? 'kg',
      allowedQuantity: (json['allowed_quantity'] as num?)?.toDouble(),
      stockState: StockStateModel.fromJson(stock),
      actions: (json['actions'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      cautions: (json['cautions'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      advisory: json['advisory'] as String?,
      notice: json['notice'] as String?,
    );
  }
}
