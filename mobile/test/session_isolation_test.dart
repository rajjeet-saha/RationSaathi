import 'package:flutter_test/flutter_test.dart';
import 'package:rationsaathi_mobile/data/models/session_model.dart';

void main() {
  group('Session & Cross-Member Isolation Tests', () {
    test('Member session can access only their own consent-scoped profile', () {
      final session = SessionModel(
        token: 'mem-tok-1',
        sessionId: 'sess-1',
        role: 'MEMBER',
        householdId: 'hh-1',
        householdReference: 'RC-101',
        householdLabel: 'Yadav Household',
        homeState: 'Bihar',
        destinationState: 'Delhi',
        memberId: 'm-ramesh',
        memberName: 'Ramesh Yadav',
      );

      expect(session.isMember, isTrue);
      expect(session.isFacilitator, isFalse);
      expect(session.hasConsent('m-ramesh'), isTrue);
      // Cross-member isolation check
      expect(session.hasConsent('m-sita'), isFalse);
    });

    test('Facilitator session requires explicitly documented member consent', () {
      final session = SessionModel(
        token: 'fac-tok-1',
        sessionId: 'sess-fac-1',
        role: 'FACILITATOR',
        householdId: 'hh-1',
        householdReference: 'RC-101',
        householdLabel: 'Yadav Household',
        homeState: 'Bihar',
        destinationState: 'Delhi',
        consentMemberIds: ['m-ramesh'], // Consent recorded for Ramesh only
      );

      expect(session.isFacilitator, isTrue);
      expect(session.hasConsent('m-ramesh'), isTrue);
      // No consent recorded for Sita
      expect(session.hasConsent('m-sita'), isFalse);
    });
  });
}
