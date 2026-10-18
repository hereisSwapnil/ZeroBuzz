package com.zerobuzz.ui

import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowInsetsControllerCompat
import androidx.core.widget.doAfterTextChanged
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.google.android.material.button.MaterialButton
import com.zerobuzz.R
import com.zerobuzz.data.ZeroBuzzStorage
import com.zerobuzz.databinding.ActivityMainBinding
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var appsAdapter: AppsAdapter
    private lateinit var activityAdapter: ActivityAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Ensure light status bar and navigation bar with dark text/icons
        WindowInsetsControllerCompat(window, window.decorView).apply {
            isAppearanceLightStatusBars = true
            isAppearanceLightNavigationBars = true
        }

        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        ZeroBuzzStorage.init(this)

        setupNavigation()
        setupWhitelistTab()
        setupActivityTab()
        setupSettingsTab()
        checkPermission()
    }

    private fun checkPermission() {
        val enabledListeners = Settings.Secure.getString(contentResolver, "enabled_notification_listeners") ?: ""
        if (!enabledListeners.contains(packageName)) {
            startActivity(Intent("android.settings.ACTION_NOTIFICATION_LISTENER_SETTINGS"))
        }
    }

    private fun setupNavigation() {
        binding.bottomNavigation.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_whitelist -> {
                    switchTab(binding.viewWhitelist, "ZeroBuzz")
                    true
                }
                R.id.nav_activity -> {
                    switchTab(binding.viewActivity, "Activity")
                    true
                }
                R.id.nav_settings -> {
                    switchTab(binding.viewSettings, "Settings")
                    true
                }
                else -> false
            }
        }
    }

    private fun switchTab(targetView: View, title: String) {
        binding.tvHeaderTitle.text = title
        binding.viewWhitelist.visibility = View.GONE
        binding.viewActivity.visibility = View.GONE
        binding.viewSettings.visibility = View.GONE

        targetView.alpha = 0f
        targetView.visibility = View.VISIBLE
        targetView.animate().alpha(1f).setDuration(150).start()
    }

    private fun setupWhitelistTab() {
        appsAdapter = AppsAdapter { app, isWhitelisted ->
            ZeroBuzzStorage.setWhitelisted(app.packageName, isWhitelisted)
        }

        binding.rvApps.layoutManager = LinearLayoutManager(this)
        binding.rvApps.adapter = appsAdapter

        binding.etSearchApp.doAfterTextChanged {
            appsAdapter.filter(it?.toString() ?: "")
        }

        lifecycleScope.launch {
            ZeroBuzzStorage.installedApps.collectLatest { list ->
                appsAdapter.updateData(list)
            }
        }
    }

    private fun setupActivityTab() {
        activityAdapter = ActivityAdapter { record ->
            ZeroBuzzStorage.toggleNotificationPreference(record.id)
        }

        binding.rvNotifications.layoutManager = LinearLayoutManager(this)
        binding.rvNotifications.adapter = activityAdapter

        // Default Filter Active state: "All"
        setFilterActive(binding.btnFilterAll)

        // Filter button clicks
        binding.btnFilterAll.setOnClickListener {
            setFilterActive(binding.btnFilterAll)
            activityAdapter.applyFilter(ActivityAdapter.FilterMode.ALL)
        }
        binding.btnFilterUnbuzz.setOnClickListener {
            setFilterActive(binding.btnFilterUnbuzz)
            activityAdapter.applyFilter(ActivityAdapter.FilterMode.UNBUZZ)
        }
        binding.btnFilterBuzz.setOnClickListener {
            setFilterActive(binding.btnFilterBuzz)
            activityAdapter.applyFilter(ActivityAdapter.FilterMode.BUZZ)
        }

        lifecycleScope.launch {
            ZeroBuzzStorage.notifications.collectLatest { list ->
                activityAdapter.updateData(list)
                if (list.isEmpty()) {
                    binding.tvEmptyActivity.visibility = View.VISIBLE
                    binding.rvNotifications.visibility = View.GONE
                } else {
                    binding.tvEmptyActivity.visibility = View.GONE
                    binding.rvNotifications.visibility = View.VISIBLE
                }
            }
        }
    }

    private fun setupSettingsTab() {
        binding.switchEngine.isChecked = ZeroBuzzStorage.isEngineEnabled()
        updateEngineStatusText(binding.switchEngine.isChecked)

        binding.switchEngine.setOnCheckedChangeListener { _, isChecked ->
            ZeroBuzzStorage.setEngineEnabled(isChecked)
            updateEngineStatusText(isChecked)
        }

        binding.cardDeveloper.setOnClickListener {
            try {
                val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://github.com/hereisswapnil"))
                startActivity(intent)
            } catch (_: Exception) {}
        }
    }

    private fun updateEngineStatusText(isEnabled: Boolean) {
        binding.tvEngineStatus.text = if (isEnabled) {
            "Silencing promotional buzz on-device"
        } else {
            "All notifications buzz through"
        }
    }

    private fun setFilterActive(activeButton: MaterialButton) {
        val buttons = listOf(binding.btnFilterAll, binding.btnFilterUnbuzz, binding.btnFilterBuzz)
        for (btn in buttons) {
            if (btn == activeButton) {
                btn.setBackgroundColor(Color.parseColor("#181829"))
                btn.setTextColor(Color.WHITE)
                btn.strokeWidth = 0
            } else {
                btn.setBackgroundColor(Color.WHITE)
                btn.setTextColor(Color.parseColor("#64748B"))
                btn.setStrokeColorResource(R.color.surface_border)
                btn.strokeWidth = 2
            }
        }
    }
}
