# ZeroBuzz Architecture Guide

## 1. System Overview

ZeroBuzz is built on an on-device architecture designed for zero false positives on critical notifications, sub-millisecond evaluation, and complete user privacy.

```
Incoming Push Notification
         │
         ▼
[NotificationListenerService]
         │
         ├───► Is Package in User Whitelist?
         │         ├── YES ──► Pass through immediately (0ms delay, no logging)
         │         └── NO
         │              │
         │              ▼
         ├───► Is Engine Enabled? ("Want buzz in your life")
         │         ├── NO ──► Pass through without suppression
         │         └── YES
         │              │
         │              ▼
         ├───► [SemanticClassifier.classify()]
         │         │
         │         ├── Hard Whitelist Patterns (OTP, Debit/Credit, Delivery, Meds) ──► DELIVER
         │         └── Linear Subword / N-gram Score Evaluation (Threshold: 0.50)
         │                   │
         │                   ├── Is Promo Spam (p >= 0.50) ──► cancelNotification() [SILENCED]
         │                   └── Is Essential (p < 0.50)   ──► DELIVER
         │
         ▼
[ZeroBuzzStorage (Encrypted JSON / SharedPrefs)]
         │
         ▼
[MainActivity UI (3 Tabs: Whitelist, Activity, Settings)]
```

---

## 2. Component Reference

### `com.zerobuzz.service.ZeroBuzzListenerService`
- Extends Android's `NotificationListenerService`.
- Registered in `AndroidManifest.xml` with permission `BIND_NOTIFICATION_LISTENER_SERVICE`.
- Inspects `StatusBarNotification` in `onNotificationPosted()`.
- Extracts `Notification.EXTRA_TITLE`, `EXTRA_TEXT`, `EXTRA_BIG_TEXT`, and `channelId`.
- Calls `cancelNotification(sbn.key)` when promotional spam is confirmed.

### `com.zerobuzz.ml.SemanticClassifier`
- Zero-dependency Kotlin singleton.
- Compiles 2,500+ n-gram and subword feature weights directly into memory.
- Contains hard regex rules guaranteeing delivery of mission-critical alerts (banking, OTPs, medicine, driver dispatch).
- Evaluates text in `< 0.1ms` using hash-map lookups and sigmoid activation.

### `com.zerobuzz.data.ZeroBuzzStorage`
- Thread-safe repository managing:
  - Whitelisted packages set.
  - Intercepted notifications history (in-memory buffer + JSON).
  - User feedback overrides (`user_corrections.json`).
  - Master engine state toggle (`engine_enabled`).

### `com.zerobuzz.ui.MainActivity`
- Clean, monochromatic 3-tab interface:
  - `Whitelist`: Searchable list of installed packages with toggle switches.
  - `Activity`: Grouped feed of notifications with single-tap silence/unsilence toggles (`Buzz` / `Unbuzz`).
  - `Settings`: "Want buzz in your life" engine toggle, version information, and developer link.

---

## 3. Laptop Sync & Retraining Pipeline (`scripts/sync_and_retrain.py`)

1. Connects to device via ADB.
2. Pulls user feedback overrides from `/sdcard/Android/data/com.zerobuzz/files/user_corrections.json`.
3. Ingests feedback into the training corpus.
4. Executes `ml/train.py` to recompute model weights and export updated Kotlin code for `SemanticClassifier.kt`.
5. Compiles and hot-updates the APK using `adb install -r`.
