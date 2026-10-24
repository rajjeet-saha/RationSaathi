import 'package:flutter_test/flutter_test.dart';
import 'package:rationsaathi_mobile/data/models/correction_model.dart';

void main() {
  group('Server-Side Safety Blocking Verification', () {
    test('Destructive member deletion proposal returns BLOCKED with canSubmit=false', () {
      final json = {
        'proposal_id': 'prop-blocked-99',
        'operation': 'DELETE_MEMBER',
        'risk_level': 'BLOCKED',
        'reasons': [
          'Member deletion would irreversibly terminate household entitlement quota.'
        ],
        'consequences': [
          'Family quota reduced by 5 kg grain per month'
        ],
        'recommendations': [
          'Use temporary absent status instead of record deletion.'
        ],
        'can_submit': false,
        'can_draft': false,
        'notice': 'BLOCKED_BY_SERVER_POLICY',
      };

      final sim = CorrectionSimulationModel.fromJson(json);

      expect(sim.isBlocked, isTrue);
      expect(sim.canSubmit, isFalse);
      expect(sim.canDraft, isFalse);
      expect(sim.reasons.first, contains('irreversibly terminate'));
    });

    test('Harmless field update returns LOW risk with canSubmit=true', () {
      final json = {
        'proposal_id': 'prop-safe-12',
        'operation': 'UPDATE_FIELD',
        'risk_level': 'LOW',
        'reasons': ['Field edit does not modify family relationship structure.'],
        'consequences': [],
        'recommendations': [],
        'can_submit': true,
        'can_draft': true,
      };

      final sim = CorrectionSimulationModel.fromJson(json);

      expect(sim.isSafe, isTrue);
      expect(sim.isBlocked, isFalse);
      expect(sim.canSubmit, isTrue);
    });
  });
}
