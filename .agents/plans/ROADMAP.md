# ZeroBuzz Development Roadmap

## Phase 1: Foundation (Completed)
- [x] Android NotificationListenerService implementation.
- [x] Subword n-gram on-device semantic classifier with 0.1ms inference.
- [x] 100% on-device privacy guarantee with 0 internet permissions.
- [x] Modern monochromatic Material 3 UI with 3-tab navigation.
- [x] Seamless launcher adaptive icon and header logo.
- [x] USB sync and retraining script (`scripts/sync_and_retrain.py`).

---

## Phase 2: User Experience & Controls (Next)
- [ ] Category-level whitelisting (e.g. food delivery vs finance vs social).
- [ ] Schedule mode / quiet hours (e.g. auto-silence during work or sleep hours).
- [ ] Quick Settings tile in Android notification shade for one-tap engine toggle.

---

## Phase 3: Enhanced On-Device Learning
- [ ] Pure on-device incremental SGD weight updates directly in Kotlin without laptop USB tethering.
- [ ] Custom keyword blocking rules configured directly from the UI.
