package com.zerobuzz.data

import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.os.Environment
import android.util.Log
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

object ZeroBuzzStorage {

    private const val TAG = "ZeroBuzzStorage"
    private const val PREFS_NAME = "zerobuzz_prefs"
    private const val KEY_WHITELIST = "whitelisted_packages"
    private const val KEY_ENGINE_ENABLED = "engine_enabled"

    // Default Whitelist for Essential Communication & System Apps
    private val DEFAULT_WHITELIST = setOf(
        "com.whatsapp",
        "com.Slack",
        "org.telegram.messenger",
        "com.google.android.talk",
        "com.discord",
        "com.samsung.android.messaging",
        "com.google.android.apps.messaging",
        "com.google.android.dialer",
        "com.samsung.android.incallui",
        "com.google.android.deskclock",
        "com.sec.android.app.clockpackage",
        "com.google.android.calendar",
        "com.samsung.android.calendar"
    )

    private lateinit var prefs: SharedPreferences
    private val whitelistedPackages = mutableSetOf<String>()

    private val _engineEnabled = MutableStateFlow(true)
    val engineEnabled: StateFlow<Boolean> = _engineEnabled.asStateFlow()

    private val _notifications = MutableStateFlow<List<NotificationRecord>>(emptyList())
    val notifications: StateFlow<List<NotificationRecord>> = _notifications.asStateFlow()

    private val _installedApps = MutableStateFlow<List<AppItem>>(emptyList())
    val installedApps: StateFlow<List<AppItem>> = _installedApps.asStateFlow()

    private val userCorrections = mutableListOf<UserCorrection>()
    private var appContext: Context? = null

    fun init(context: Context) {
        if (appContext != null) return
        appContext = context.applicationContext
        prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

        _engineEnabled.value = prefs.getBoolean(KEY_ENGINE_ENABLED, true)

        val saved = prefs.getStringSet(KEY_WHITELIST, null)
        if (saved != null) {
            whitelistedPackages.addAll(saved)
        } else {
            whitelistedPackages.addAll(DEFAULT_WHITELIST)
            saveWhitelist()
        }

        loadUserCorrections(context)
        loadInstalledApps(context)
    }

    fun isEngineEnabled(): Boolean = _engineEnabled.value

    fun setEngineEnabled(enabled: Boolean) {
        _engineEnabled.value = enabled
        prefs.edit().putBoolean(KEY_ENGINE_ENABLED, enabled).apply()
    }

    fun isWhitelisted(pkg: String): Boolean {
        return whitelistedPackages.contains(pkg)
    }

    fun setWhitelisted(pkg: String, whitelisted: Boolean) {
        if (whitelisted) {
            whitelistedPackages.add(pkg)
        } else {
            whitelistedPackages.remove(pkg)
        }
        saveWhitelist()

        // Update installed apps list state
        val updated = _installedApps.value.map {
            if (it.packageName == pkg) it.copy(isWhitelisted = whitelisted) else it
        }
        _installedApps.value = updated
    }

    private fun saveWhitelist() {
        prefs.edit().putStringSet(KEY_WHITELIST, whitelistedPackages).apply()
    }

    fun recordNotification(record: NotificationRecord) {
        val current = _notifications.value.toMutableList()
        current.add(0, record)
        if (current.size > 200) {
            current.removeAt(current.size - 1)
        }
        _notifications.value = current
    }

    /**
     * User overrides the decision for a specific notification card in the feed.
     * Toggles Blocked <-> Allowed and writes to user_corrections.json.
     */
    fun toggleNotificationPreference(id: String) {
        val current = _notifications.value.toMutableList()
        val index = current.indexOfFirst { it.id == id }
        if (index == -1) return

        val item = current[index]
        val newBlockedState = !item.isBlocked
        val correctedLabel = if (newBlockedState) 1 else 0
        val originalLabel = if (item.isBlocked) 1 else 0

        val updated = item.copy(
            isBlocked = newBlockedState,
            isUserOverridden = true,
            userOverrideLabel = correctedLabel
        )
        current[index] = updated
        _notifications.value = current

        // Record User Correction
        val correction = UserCorrection(
            title = item.title,
            text = item.text,
            packageName = item.packageName,
            originalLabel = originalLabel,
            correctedLabel = correctedLabel
        )
        userCorrections.removeAll { it.title == item.title && it.text == item.text }
        userCorrections.add(0, correction)
        exportUserCorrections()
    }

    private fun exportUserCorrections() {
        val ctx = appContext ?: return
        try {
            val jsonArray = JSONArray()
            for (c in userCorrections) {
                val obj = JSONObject()
                obj.put("title", c.title)
                obj.put("text", c.text)
                obj.put("package", c.packageName)
                obj.put("original_label", c.originalLabel)
                obj.put("corrected_label", c.correctedLabel)
                obj.put("timestamp", c.timestamp)
                jsonArray.put(obj)
            }
            val data = jsonArray.toString(2)

            // 1. App Internal Files
            File(ctx.filesDir, "user_corrections.json").writeText(data)

            // 2. App External Files Directory (world-accessible via ADB without root)
            val extDir = ctx.getExternalFilesDir(null)
            if (extDir != null) {
                File(extDir, "user_corrections.json").writeText(data)
            }

            // 3. Downloads directory fallback
            val downloadDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
            if (downloadDir != null && downloadDir.exists()) {
                File(downloadDir, "zerobuzz_corrections.json").writeText(data)
            }
            Log.i(TAG, "Exported ${userCorrections.size} user corrections successfully.")
        } catch (e: Exception) {
            Log.e(TAG, "Error exporting user corrections: ${e.message}")
        }
    }

    private fun loadUserCorrections(ctx: Context) {
        try {
            val file = File(ctx.filesDir, "user_corrections.json")
            if (!file.exists()) return
            val jsonArray = JSONArray(file.readText())
            userCorrections.clear()
            for (i in 0 until jsonArray.length()) {
                val obj = jsonArray.getJSONObject(i)
                userCorrections.add(
                    UserCorrection(
                        title = obj.getString("title"),
                        text = obj.getString("text"),
                        packageName = obj.getString("package"),
                        originalLabel = obj.getInt("original_label"),
                        correctedLabel = obj.getInt("corrected_label"),
                        timestamp = obj.optLong("timestamp", System.currentTimeMillis())
                    )
                )
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed loading user corrections: ${e.message}")
        }
    }

    fun loadInstalledApps(ctx: Context) {
        try {
            val pm = ctx.packageManager
            val mainIntent = Intent(Intent.ACTION_MAIN, null).apply {
                addCategory(Intent.CATEGORY_LAUNCHER)
            }
            val resolveInfos = pm.queryIntentActivities(mainIntent, 0)
            val seenPackages = mutableSetOf<String>()
            val apps = mutableListOf<AppItem>()

            for (info in resolveInfos) {
                val pkg = info.activityInfo.packageName
                if (pkg == ctx.packageName || seenPackages.contains(pkg)) continue
                seenPackages.add(pkg)

                val label = info.loadLabel(pm).toString()
                val icon = info.loadIcon(pm)
                val whitelisted = isWhitelisted(pkg)
                apps.add(AppItem(pkg, label, icon, whitelisted))
            }

            // Add standard messaging apps even if launcher intent is different
            val specialPackages = listOf(
                "com.google.android.apps.messaging",
                "com.samsung.android.messaging",
                "com.google.android.dialer",
                "com.sec.android.app.clockpackage",
                "com.google.android.deskclock"
            )
            for (sp in specialPackages) {
                if (!seenPackages.contains(sp)) {
                    try {
                        val appInfo = pm.getApplicationInfo(sp, 0)
                        val label = pm.getApplicationLabel(appInfo).toString()
                        val icon = pm.getApplicationIcon(appInfo)
                        apps.add(AppItem(sp, label, icon, isWhitelisted(sp)))
                        seenPackages.add(sp)
                    } catch (_: Exception) {}
                }
            }

            // Sort: Whitelisted first, then alphabetically
            apps.sortWith(compareByDescending<AppItem> { it.isWhitelisted }.thenBy { it.appName.lowercase() })
            _installedApps.value = apps
        } catch (e: Exception) {
            Log.e(TAG, "Failed loading installed apps: ${e.message}")
        }
    }
}
