package com.zerobuzz.service

import android.app.Notification
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import com.zerobuzz.data.NotificationRecord
import com.zerobuzz.data.ZeroBuzzStorage
import com.zerobuzz.ml.SemanticClassifier

class ZeroBuzzListenerService : NotificationListenerService() {

    companion object {
        private const val TAG = "ZeroBuzz"
    }

    override fun onCreate() {
        super.onCreate()
        ZeroBuzzStorage.init(applicationContext)
        Log.i(TAG, "ZeroBuzz Listener Service initialized.")
    }

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        if (sbn == null) return

        val pkg = sbn.packageName ?: return
        if (pkg == packageName) return // Do not intercept self
        if (!ZeroBuzzStorage.isEngineEnabled()) return // Engine disabled by user

        val notification = sbn.notification ?: return
        val extras = notification.extras ?: return

        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString() ?: ""
        val text = extras.getCharSequence(Notification.EXTRA_BIG_TEXT)?.toString()
            ?: extras.getCharSequence(Notification.EXTRA_TEXT)?.toString()
            ?: ""
        val channel = notification.channelId ?: ""

        // Skip empty notifications (progress bars, background state tokens)
        if (title.isBlank() && text.isBlank()) return

        // Resolve readable app name
        val appName = try {
            val pm = packageManager
            val info = pm.getApplicationInfo(pkg, 0)
            pm.getApplicationLabel(info).toString()
        } catch (_: Exception) {
            pkg
        }

        // 1. Check User Whitelist (Zero-latency bypass without recording to activity feed)
        if (ZeroBuzzStorage.isWhitelisted(pkg)) {
            Log.d(TAG, "Package $pkg is in Whitelist. Passing through immediately without activity logging.")
            return
        }

        // 2. High-Speed Subword Semantic Evaluation (< 0.1ms)
        val result = SemanticClassifier.classify(title, text, channel)

        val record = NotificationRecord(
            packageName = pkg,
            appName = appName,
            title = title,
            text = text,
            channelId = channel,
            isBlocked = result.isPromoSpam
        )
        ZeroBuzzStorage.recordNotification(record)

        // 3. Action
        if (result.isPromoSpam) {
            Log.i(TAG, "🚫 SILENCED Promotional Broadcast: [$appName] '$title' (p=${result.probability})")
            cancelNotification(sbn.key)
        } else {
            Log.d(TAG, "✅ DELIVERED Legitimate Update: [$appName] '$title'")
        }
    }
}
