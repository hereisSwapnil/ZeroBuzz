# AI Agent Workspace & Architecture Context

This directory contains specifications, architectural plans, and context guides for AI agents pair-programming and maintaining **ZeroBuzz**.

---

## 📂 Directory Contents

- [ARCHITECTURE.md](file:///Users/hereisswapnil/Desktop/ZeroBuzz/.agents/ARCHITECTURE.md): Technical deep-dive into the Android NotificationListenerService, semantic ML engine, on-device state flows, and USB synchronization pipeline.
- [plans/ARCHITECTURE_SPEC.md](file:///Users/hereisswapnil/Desktop/ZeroBuzz/.agents/plans/ARCHITECTURE_SPEC.md): Full dataset composition, feature extraction formulas, subword tokenization, and semantic classification architecture.
- [plans/ZEROBUZZ_UI_SPEC.md](file:///Users/hereisswapnil/Desktop/ZeroBuzz/.agents/plans/ZEROBUZZ_UI_SPEC.md): Design system tokens, icon palette, 3-tab navigation, and card interaction specs.
- [plans/ROADMAP.md](file:///Users/hereisswapnil/Desktop/ZeroBuzz/.agents/plans/ROADMAP.md): Future enhancement milestones and planned features.

---

## 🤖 Guidelines for AI Agents

1. **Strict 0 Internet Requirement**:
   - ZeroBuzz is architected on pure local privacy. Never request or introduce `android.permission.INTERNET`.
   - Never send notifications or telemetry to third-party APIs or remote cloud endpoints.
2. **Sub-Millisecond Budget**:
   - The notification interception pipeline runs inside `NotificationListenerService.onNotificationPosted()`.
   - Evaluations must complete in `< 0.1ms` using compiled feature weights directly in Kotlin. Avoid heavy reflective parsers or dynamic disk reads on the critical path.
3. **Whitelist Bypassing**:
   - Apps toggled in the **Whitelist** tab bypass all semantic evaluation immediately with zero latency, and are deliberately NOT recorded or transacted in the Activity log.
4. **Clean Design Principles**:
   - Strictly avoid unnecessary AI buzzwords, flashy badges, or redundant indicators in the UI.
   - Maintain the monochromatic, minimalist aesthetic with seamless adaptive squircle icon styling.
