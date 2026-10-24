# RationSaathi Mobile (Flutter Android Application)

The official Flutter Android companion application for **RationSaathi**, extending the civic-service public distribution navigator to mobile devices while reusing the existing FastAPI backend and PostgreSQL / SQLite database.

---

## 📱 Features

- **Household Overview & Card Details**: View ration card reference, origin state to destination state route, and registered family members.
- **Verified Member Entitlements**: Real-time breakdown of entitled vs. drawn vs. remaining grain allocations for active distribution cycles.
- **Interstate Portability (ONORC)**: Evaluates interstate state-pairs, Fair Price Shop (FPS) stock freshness, and provides explicit travel advisories (stale stock warning).
- **Correction Safety Guard**: Simulates record updates before submission. Harmful changes (e.g. accidental member deletion or entitlement loss) are **BLOCKED** server-side with safety recommendations.
- **Offline Drafts & Sync Queue**: Local offline draft persistence using `SharedPreferences`. Drafts remain strictly labelled `NOT SUBMITTED` until receipt verification. Includes retryable background sync.
- **Grievance Resolution Tracking**: Tracks 21-day official timelines. `OVERDUE` labels require verified official deadlines. Automated generation of formal escalation letters.
- **Accessibility & Inclusion**:
  - High Contrast (WCAG AAA black/yellow palette for direct sunlight visibility).
  - Dynamic Font Scaling (100% to 160%).
  - Multi-language support: English, हिन्दी (Hindi), বাংলা (Bengali), and తెలుగు (Telugu).
  - In-memory ephemeral sessions (tokens are held in-memory only and purged on sign-out/profile switch).

---

## 🛠️ Architecture

Built following standard Flutter layered architecture:
```
mobile/
├── android/                   # Native Android wrapper (SDK 21-34, Cleartext networking enabled)
├── lib/
│   ├── core/
│   │   ├── constants/         # API endpoints & dynamic base URL configuration
│   │   └── theme/             # Material 3 standard and high-contrast themes
│   ├── data/
│   │   ├── models/            # Session, Household, Portability, Correction, Draft, Grievance
│   │   └── services/          # ApiService (HTTP + headers) & OfflineDraftStorage
│   ├── providers/             # SessionProvider, DraftProvider, AccessibilityProvider
│   ├── screens/               # Splash/Sign-in, Home, Entitlements, Portability, Corrections, Drafts, Grievances, Settings
│   └── widgets/               # StatusBadge, accessible action buttons
└── test/                      # API contracts, offline sync, safety blocking, session isolation
```

---

## 🚀 Setup & Development Guide

### 1. Prerequisites
- **Flutter SDK** (`3.10.0+` or `3.24+`) installed and added to your `PATH`.
- **Android Studio** with Android SDK Command-line Tools and an Android Virtual Device (AVD).

Verify your setup:
```bash
flutter doctor
```

### 2. Connect to the Existing Backend

Make sure the FastAPI backend is running:
```bash
# In the repository root:
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

#### Networking Notes:
- **Android Emulator**: Uses `http://10.0.2.2:8000/api/v1` (the default in `ApiEndpoints.baseUrl`).
- **Physical Device**: Connect to the same Wi-Fi network and set the IP (e.g., `http://192.168.1.50:8000/api/v1`) via **Settings → API Base URL** inside the app.
- **Live Cloud Backend**: Point the URL to your deployed Render URL (e.g., `https://rationsaathi-backend.onrender.com/api/v1`).

---

### 3. Running the App

```bash
cd mobile

# Fetch Flutter dependencies
flutter pub get

# Launch on connected Android emulator or device
flutter run
```

---

### 4. Running Automated Tests

```bash
cd mobile
flutter test
```

Test suites verify:
- `api_service_test.dart`: Correct `X-Ration-Session` header injection and automatic token purging on `401 Unauthorized`.
- `offline_draft_test.dart`: Offline draft state progression and receipt confirmation requirements.
- `safety_blocking_test.dart`: Verification that destructive corrections return `BLOCKED` and disable submission buttons.
- `session_isolation_test.dart`: Verification that member sessions isolate data and facilitator mode requires documented consent.

---

### 5. Building for Android

#### Debug APK (For local device testing)
```bash
flutter build apk --debug
```
Output location: `build/app/outputs/flutter-apk/app-debug.apk`

#### Release APK
```bash
flutter build apk --release
```
Output location: `build/app/outputs/flutter-apk/app-release.apk`

#### Release Android App Bundle (AAB for Google Play Store)
```bash
flutter build appbundle --release
```
Output location: `build/app/outputs/bundle/release/app-release.aab`

---

## 🔒 Security & Privacy Guarantees

1. **In-Memory Ephemeral Tokens**: No session credentials or tokens are saved to disk. When the app is closed or profile switched, tokens are immediately cleared from memory.
2. **Server-Enforced Rules**: All entitlement calculations, stock rules, and correction risk scoring happen exclusively on the backend.
3. **Synthetic Demo Data**: Fictional profiles only; no real PDS systems or Aadhaar credentials are touched.
