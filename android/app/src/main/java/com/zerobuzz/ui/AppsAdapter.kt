package com.zerobuzz.ui

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.zerobuzz.data.AppItem
import com.zerobuzz.databinding.ItemAppBinding

class AppsAdapter(
    private val onToggle: (AppItem, Boolean) -> Unit
) : ListAdapter<AppItem, AppsAdapter.AppViewHolder>(DiffCallback) {

    private var fullList: List<AppItem> = emptyList()

    fun updateData(list: List<AppItem>) {
        fullList = list
        submitList(list)
    }

    fun filter(query: String) {
        if (query.isBlank()) {
            submitList(fullList)
        } else {
            val filtered = fullList.filter {
                it.appName.contains(query, ignoreCase = true) ||
                it.packageName.contains(query, ignoreCase = true)
            }
            submitList(filtered)
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): AppViewHolder {
        val binding = ItemAppBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return AppViewHolder(binding)
    }

    override fun onBindViewHolder(holder: AppViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    inner class AppViewHolder(private val binding: ItemAppBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(item: AppItem) {
            binding.tvAppName.text = item.appName
            binding.tvPackageName.text = item.packageName
            if (item.icon != null) {
                binding.ivAppIcon.setImageDrawable(item.icon)
            } else {
                binding.ivAppIcon.setImageResource(android.R.drawable.sym_def_app_icon)
            }

            // Remove previous listener to avoid triggering during recycle
            binding.switchWhitelist.setOnCheckedChangeListener(null)
            binding.switchWhitelist.isChecked = item.isWhitelisted

            binding.switchWhitelist.setOnCheckedChangeListener { _, isChecked ->
                item.isWhitelisted = isChecked
                onToggle(item, isChecked)
            }
        }
    }

    companion object DiffCallback : DiffUtil.ItemCallback<AppItem>() {
        override fun areItemsTheSame(oldItem: AppItem, newItem: AppItem) = oldItem.packageName == newItem.packageName
        override fun areContentsTheSame(oldItem: AppItem, newItem: AppItem) = oldItem == newItem
    }
}
