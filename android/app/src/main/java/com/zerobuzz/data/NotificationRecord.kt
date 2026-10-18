package com.zerobuzz.data

import java.util.UUID

data class NotificationRecord(
    val id: String = UUID.randomUUID().toString(),
    val timestamp: Long = System.currentTimeMillis(),
    val packageName: String,
    val appName: String,
    val title: String,
    val text: String,
    val channelId: String,
    var isBlocked: Boolean,
    var isUserOverridden: Boolean = false,
    var userOverrideLabel: Int? = null // 0 = Allowed, 1 = Blocked
)

data class UserCorrection(
    val title: String,
    val text: String,
    val packageName: String,
    val originalLabel: Int,
    val correctedLabel: Int,
    val timestamp: Long = System.currentTimeMillis()
)
