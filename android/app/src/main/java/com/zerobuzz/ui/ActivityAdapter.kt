package com.zerobuzz.ui

import android.graphics.Color
import android.graphics.drawable.Drawable
import android.text.format.DateUtils
import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.zerobuzz.R
import com.zerobuzz.data.NotificationRecord
import com.zerobuzz.databinding.ItemNotificationBinding

class ActivityAdapter(
    private val onTogglePreference: (NotificationRecord) -> Unit
) : ListAdapter<NotificationRecord, ActivityAdapter.ActivityViewHolder>(DiffCallback) {

    private var currentFilter: FilterMode = FilterMode.ALL
    private var rawList: List<NotificationRecord> = emptyList()
    private val iconCache = mutableMapOf<String, Drawable?>()

    enum class FilterMode { ALL, UNBUZZ, BUZZ }

    fun updateData(list: List<NotificationRecord>) {
        // Group notifications by app, sorted by most recent within each app group
        rawList = list.sortedWith(
            compareBy<NotificationRecord> { it.appName.lowercase() }
                .thenByDescending { it.timestamp }
        )
        applyFilter(currentFilter)
    }

    fun applyFilter(mode: FilterMode) {
        currentFilter = mode
        val filtered = when (mode) {
            FilterMode.ALL -> rawList
            FilterMode.UNBUZZ -> rawList.filter { it.isBlocked }
            FilterMode.BUZZ -> rawList.filter { !it.isBlocked }
        }
        submitList(filtered)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ActivityViewHolder {
        val binding = ItemNotificationBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ActivityViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ActivityViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    inner class ActivityViewHolder(private val binding: ItemNotificationBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(record: NotificationRecord) {
            binding.tvAppName.text = record.appName
            binding.tvTitle.text = record.title.ifBlank { "Notification" }
            binding.tvBody.text = record.text.ifBlank { "(No message body)" }

            // Load app icon
            val icon = iconCache.getOrPut(record.packageName) {
                try {
                    binding.root.context.packageManager.getApplicationIcon(record.packageName)
                } catch (_: Exception) {
                    null
                }
            }
            if (icon != null) {
                binding.ivAppIcon.setImageDrawable(icon)
            } else {
                binding.ivAppIcon.setImageResource(R.drawable.ic_bell)
            }

            // Relative timestamp
            val timeSpan = DateUtils.getRelativeTimeSpanString(
                record.timestamp,
                System.currentTimeMillis(),
                DateUtils.MINUTE_IN_MILLIS
            )
            binding.tvTime.text = timeSpan

            // Single Action Icon Button to Silence / Unsilence with icon theme tints
            if (record.isBlocked) {
                binding.btnToggleSilence.setImageResource(R.drawable.ic_bell_off)
                binding.btnToggleSilence.setColorFilter(Color.parseColor("#7C3AED"))
                binding.btnToggleSilence.contentDescription = "Silenced (Tap to allow)"
            } else {
                binding.btnToggleSilence.setImageResource(R.drawable.ic_bell)
                binding.btnToggleSilence.setColorFilter(Color.parseColor("#06B6D4"))
                binding.btnToggleSilence.contentDescription = "Active (Tap to silence)"
            }

            binding.btnToggleSilence.setOnClickListener {
                onTogglePreference(record)
            }
        }
    }

    companion object DiffCallback : DiffUtil.ItemCallback<NotificationRecord>() {
        override fun areItemsTheSame(oldItem: NotificationRecord, newItem: NotificationRecord) = oldItem.id == newItem.id
        override fun areContentsTheSame(oldItem: NotificationRecord, newItem: NotificationRecord) = oldItem == newItem
    }
}
