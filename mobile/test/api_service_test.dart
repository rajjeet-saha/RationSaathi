import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'dart:convert';

import 'package:rationsaathi_mobile/data/services/api_service.dart';
import 'package:rationsaathi_mobile/core/constants/api_endpoints.dart';

void main() {
  group('ApiService Tests', () {
    test('Token is injected into X-Ration-Session header', () async {
      final mockClient = MockClient((request) async {
        expect(request.headers['X-Ration-Session'], 'test-token-123');
        return http.Response(jsonEncode({'status': 'ok'}), 200);
      });

      final api = ApiService(client: mockClient);
      api.setSessionToken('test-token-123');

      final res = await api.checkHealth();
      expect(res['status'], 'ok');
    });

    test('401 response clears in-memory session token', () async {
      final mockClient = MockClient((request) async {
        return http.Response(jsonEncode({'detail': 'Session expired'}), 401);
      });

      final api = ApiService(client: mockClient);
      api.setSessionToken('valid-looking-token');
      expect(api.sessionToken, isNotNull);

      expect(() => api.checkHealth(), throwsA(isA<ApiException>()));
      
      // Token should now be purged
      expect(api.sessionToken, isNull);
    });

    test('Demo profile directory maps households and members correctly', () async {
      final mockClient = MockClient((request) async {
        return http.Response(
          jsonEncode({
            'households': [
              {
                'id': 'hh-1',
                'reference': 'RC-1001',
                'label': 'Test Household',
                'home_state': 'Bihar',
                'destination_state': 'Delhi',
                'members': [
                  {'id': 'm-1', 'alias': 'Ramesh', 'relationship': 'Self'}
                ]
              }
            ]
          }),
          200,
        );
      });

      final api = ApiService(client: mockClient);
      final profiles = await api.getDemoProfiles();

      expect(profiles.length, 1);
      expect(profiles.first['reference'], 'RC-1001');
      expect(profiles.first['members'].length, 1);
    });
  });
}
