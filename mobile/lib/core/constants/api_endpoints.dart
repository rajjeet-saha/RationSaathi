/// API Endpoint constants and Base URL configuration for RationSaathi Mobile
class ApiEndpoints {
  // Default for Android Emulator communicating with host machine's FastAPI server.
  // Can be adjusted dynamically via Settings or during initialization.
  static String baseUrl = 'http://10.0.2.2:8000/api/v1';

  static const String health = '/health';
  
  // Sessions & Auth
  static const String sessions = '/sessions';
  static const String sessionCurrent = '/sessions/current';
  static const String sessionConsent = '/sessions/consent';
  static const String sessionSwitch = '/sessions/switch';
  static const String sessionEnd = '/sessions/end';
  
  // Household & Member Entitlements
  static const String householdCurrent = '/households/current';
  static String member(String id) => '/members/$id';
  static String memberEntitlements(String id) => '/members/$id/entitlements';
  
  // Portability & Stock
  static const String portabilityEvaluate = '/portability/evaluate';
  static const String portabilityRules = '/portability/rules';
  static String shopStock(String shopId) => '/shops/$shopId/stock-status';
  
  // Safe Corrections Simulator
  static const String correctionSimulate = '/corrections/simulate';
  static String correctionDraft(String proposalId) => '/corrections/$proposalId/draft';
  static String correctionSubmit(String proposalId) => '/corrections/$proposalId/submit';
  
  // Offline Drafts & Sync
  static const String drafts = '/drafts';
  static String draft(String id) => '/drafts/$id';
  static String draftSync(String id) => '/drafts/$id/sync';
  static String draftVerify(String id) => '/drafts/$id/verify-submission';
  
  // Grievance Tracking & Escalations
  static const String grievances = '/grievances';
  static String grievance(String id) => '/grievances/$id';
  static String grievanceVerify(String id) => '/grievances/$id/verify-status';
  static String escalationDraft(String id) => '/grievances/$id/escalation-draft';
  static String escalationUpdate(String id) => '/grievances/escalations/$id';
  static String escalationSubmit(String id) => '/grievances/escalations/$id/submit';
  
  // Public & Demo
  static const String publicAggregates = '/public/aggregates';
  static const String demoProfiles = '/demo/profiles';
  static const String demoReset = '/demo/reset';
}
