package com.example.reeldetector

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Intent
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.IntentFilter
import android.net.VpnService
import android.os.Build
import android.os.ParcelFileDescriptor
import android.util.Log
import java.io.File
import java.io.FileOutputStream
import java.io.FileInputStream
import java.net.InetAddress
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.concurrent.thread

class CaptureVpnService : VpnService() {
    private var vpnInterface: ParcelFileDescriptor? = null
    private val deviceIp = "10.0.0.2"
    private val TAG = "CaptureVpnService"
    private lateinit var outFile: File
    private var featureBuffer: FeatureBuffer? = null
    private var classifier: TFLiteClassifier? = null
    private var normalizer: Normalizer? = null
    private var isRealtime = false
    private var notifyManager: NotificationManager? = null
    private val channelId = "reel_channel"
    private var currentNotification: Notification? = null
    private var lastUiUpdateMs: Long = 0L
    private var lastScore: Float = -1f
    private var lastNotifyMs: Long = 0L
    private var lastIsReel: Boolean? = null
    // Smoothing and hysteresis to reduce flapping
    private var smoothedScore: Float = -1f
    private val smoothingAlpha: Float = 0.25f
    private var isReelState: Boolean = false
    private val onThreshold: Float = 0.7f
    private val offThreshold: Float = 0.4f
    private var consecutiveAbove: Int = 0
    private var consecutiveBelow: Int = 0
    private val requiredStable: Int = 2
    // Debounce: minimum time to hold a state before flipping (ms)
    private val minHoldMs: Long = 4000
    private var lastStateChangeMs: Long = 0L
    // Temporary fallback to avoid blocking internet: use OS traffic stats instead of TUN capture
    private val useNetworkStatsFallback = true

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        try {
            Log.i(TAG, "Starting VPN service...")
            startForegroundNotification()
            
            if (vpnInterface == null) {
                if (!useNetworkStatsFallback) {
                    Log.i(TAG, "Setting up VPN interface...")
                    setupVpn()
                    startCaptureLoop()
                } else {
                    Log.i(TAG, "Using NetworkStats fallback (no VPN routing)")
                    startStatsLoop()
                }
                tryLoadModel()
            }
            
            intent?.action?.let {
                if (it == "LABEL_START") writeLabel("LABEL_START")
                if (it == "LABEL_END") writeLabel("LABEL_END")
                if (it == "REALTIME_ON") { isRealtime = true }
                if (it == "REALTIME_OFF") { isRealtime = false }
            }
            
            Log.i(TAG, "VPN service started successfully")
            return START_STICKY
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start VPN service: ${e.message}")
            e.printStackTrace()
            // Don't crash the service, just return START_NOT_STICKY
            return START_NOT_STICKY
        }
    }

    private fun startForegroundNotification() {
        try {
            val nm = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
            notifyManager = nm
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                val channel = NotificationChannel(channelId, "Reel Detector", NotificationManager.IMPORTANCE_HIGH)
                nm.createNotificationChannel(channel)
            }
            
            val notificationBuilder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                Notification.Builder(this, channelId)
            } else {
                @Suppress("DEPRECATION")
                Notification.Builder(this)
            }
            
            val launchIntent = Intent(this, MainActivity::class.java)
            val pi = PendingIntent.getActivity(this, 0, launchIntent, PendingIntent.FLAG_IMMUTABLE)
            val not = notificationBuilder
                .setContentTitle("Reel Detector")
                .setContentText("Capturing metadata")
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentIntent(pi)
                .setCategory(Notification.CATEGORY_SERVICE)
                .setPriority(Notification.PRIORITY_DEFAULT)
                .setOnlyAlertOnce(true)
                .setOngoing(true)
                .build()
                
            currentNotification = not
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                try {
                    // Use reflection to access FOREGROUND_SERVICE_TYPE_VPN for Android 12+
                    if (Build.VERSION.SDK_INT >= 31) {
                        val serviceInfoClass = Class.forName("android.content.pm.ServiceInfo")
                        val foregroundServiceTypeVpn = serviceInfoClass.getField("FOREGROUND_SERVICE_TYPE_VPN").getInt(null)
                        startForeground(101, not, foregroundServiceTypeVpn)
                    } else {
                        startForeground(101, not)
                    }
                } catch (e: Exception) {
                    // Fallback to regular startForeground if reflection fails
                    startForeground(101, not)
                }
            } else {
                startForeground(101, not)
            }
            
            Log.i(TAG, "Foreground service started successfully")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start foreground service: ${e.message}")
            throw e
        }
    }

    private fun tryLoadModel() {
        try {
            classifier = TFLiteClassifier(assets, "model_quant.tflite")
            normalizer = Normalizer.fromAssets(assets, "scaler.json")
            featureBuffer = FeatureBuffer(deviceIp)
            Log.i(TAG, "Model and scaler loaded; realtime ready")
        } catch (e: Exception) {
            Log.w(TAG, "Model/scaler not found, realtime predictions disabled: ${e.message}")
        }
    }

    private fun setupVpn() {
        val builder = Builder()
        builder.addAddress(deviceIp, 32)
        // Remove default route to avoid intercepting all traffic in fallback mode
        builder.setSession("ReelVpn")
        builder.setMtu(1400)
        vpnInterface = builder.establish()
        outFile = File(filesDir, "capture.csv")
        if (!outFile.exists()) {
            outFile.writeText("ts,length,src,dst\n")
        }
        Log.i(TAG, "VPN established, writing to ${outFile.absolutePath}")
    }

    private fun startCaptureLoop() {
        val pfd = vpnInterface ?: return
        val input = FileInputStream(pfd.fileDescriptor)
        val fout = FileOutputStream(File(filesDir, "capture.csv"), true)
        thread(start = true) {
            try {
                val buffer = ByteArray(32768)
                while (true) {
                    val read = input.read(buffer)
                    if (read > 0) {
                        val ts = System.currentTimeMillis().toDouble()/1000.0
                        try {
                            val bb = ByteBuffer.wrap(buffer, 0, read).order(ByteOrder.BIG_ENDIAN)
                            val verIhl = bb.get(0).toInt()
                            val ver = (verIhl shr 4) and 0xF
                            if (ver == 4) {
                                val ihl = (verIhl and 0xF) * 4
                            // ihl is calculated but not used in current implementation
                                val srcBytes = ByteArray(4)
                                val dstBytes = ByteArray(4)
                                bb.position(12)
                                bb.get(srcBytes); bb.get(dstBytes)
                                val srcIp = InetAddress.getByAddress(srcBytes).hostAddress
                                val dstIp = InetAddress.getByAddress(dstBytes).hostAddress
                                val line = String.format("%.6f,%d,%s,%s\n", ts, read, srcIp, dstIp)
                                fout.write(line.toByteArray())
                                fout.flush()

                                // feed features and maybe infer
                                featureBuffer?.let { fb ->
                                    fb.addPacket(PacketMeta(ts, read, srcIp, dstIp))
                                    if (isRealtime) {
                                        val feats = fb.computeLatestWindow()
                                        if (feats != null && classifier != null && normalizer != null) {
                                            val norm = normalizer!!.normalize(feats)
                                            val score = classifier!!.predictNormalized(norm)
                                            // Smooth score
                                            smoothedScore = if (smoothedScore < 0f) score else (smoothingAlpha * score + (1f - smoothingAlpha) * smoothedScore)
                                            // Hysteresis logic with stability requirement
                                            if (smoothedScore >= onThreshold) {
                                                consecutiveAbove += 1
                                                consecutiveBelow = 0
                                            } else if (smoothedScore <= offThreshold) {
                                                consecutiveBelow += 1
                                                consecutiveAbove = 0
                                            } else {
                                                consecutiveAbove = 0
                                                consecutiveBelow = 0
                                            }
                                            var stateChanged = false
                                            val now = System.currentTimeMillis()
                                            if (!isReelState && consecutiveAbove >= requiredStable) {
                                                if (now - lastStateChangeMs >= minHoldMs) {
                                                    isReelState = true
                                                    stateChanged = true
                                                    lastStateChangeMs = now
                                                }
                                            } else if (isReelState && consecutiveBelow >= requiredStable) {
                                                if (now - lastStateChangeMs >= minHoldMs) {
                                                    isReelState = false
                                                    stateChanged = true
                                                    lastStateChangeMs = now
                                                }
                                            }

                                            val deltaOk = if (lastScore < 0f) true else kotlin.math.abs(smoothedScore - lastScore) >= 0.02f
                                            if (now - lastUiUpdateMs >= 1000 && (deltaOk || stateChanged)) {
                                                updateNotification(smoothedScore, isReelState)
                                                broadcastPrediction(smoothedScore, isReelState)
                                                lastUiUpdateMs = now
                                                lastScore = smoothedScore
                                            }
                                        }
                                    }
                                }
                            }
                        } catch (e: Exception) {
                            // ignore
                        }
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "capture loop ended: ${e.message}")
            } finally {
                fout.close()
            }
        }
    }

    // Fallback monitoring without intercepting traffic: poll TrafficStats and synthesize features
    private fun startStatsLoop() {
        thread(start = true) {
            try {
                var lastRx = android.net.TrafficStats.getTotalRxBytes()
                var lastTx = android.net.TrafficStats.getTotalTxBytes()
                var lastTs = System.currentTimeMillis()
                while (true) {
                    Thread.sleep(1000)
                    val now = System.currentTimeMillis()
                    val rx = android.net.TrafficStats.getTotalRxBytes()
                    val tx = android.net.TrafficStats.getTotalTxBytes()
                    val dt = (now - lastTs) / 1000.0
                    if (dt <= 0) continue
                    val downBytes = (rx - lastRx).coerceAtLeast(0)
                    val upBytes = (tx - lastTx).coerceAtLeast(0)

                    // Build a minimal feature vector compatible with model (best-effort)
                    val feats = floatArrayOf(
                        downBytes.toFloat(),
                        0f, // pkt_count_down unknown
                        0f, // avg_pkt_size_down unknown
                        0f,
                        upBytes.toFloat(),
                        0f,
                        0f,
                        0f,
                        (downBytes / dt).toFloat(), // bitrate_down
                        0f,
                        0f,
                        0f,
                        (if (upBytes == 0L) (downBytes.toFloat()) else (downBytes.toFloat() / upBytes.toFloat()))
                    )

                    if (classifier != null && normalizer != null && isRealtime) {
                        val norm = normalizer!!.normalize(feats)
                        var score = classifier!!.predictNormalized(norm)

                        // Heuristic boost for video-like traffic when using fallback stats
                        val bitrateBps = (downBytes * 8.0) / dt
                        val ratio = if (upBytes == 0L) downBytes.toDouble() else downBytes.toDouble() / upBytes.toDouble()
                        if (bitrateBps > 1_500_000.0 && ratio > 3.0) {
                            score = kotlin.math.min(1f, (score + 0.15f))
                        } else if (bitrateBps < 150_000.0) {
                            score = kotlin.math.max(0f, (score - 0.10f))
                        }

                        val nowMs = System.currentTimeMillis()
                        if (nowMs - lastUiUpdateMs >= 1000) {
                            updateNotification(score)
                            broadcastPrediction(score)
                            lastUiUpdateMs = nowMs
                            lastScore = score
                        }
                    }

                    lastRx = rx
                    lastTx = tx
                    lastTs = now
                }
            } catch (e: Exception) {
                Log.e(TAG, "stats loop ended: ${e.message}")
            }
        }
    }

    private fun writeLabel(event: String) {
        val ts = System.currentTimeMillis().toDouble()/1000.0
        val f = File(filesDir, "capture.csv")
        f.appendText("#EVENT,$event,$ts\n")
    }

    override fun onDestroy() {
        vpnInterface?.close()
        super.onDestroy()
    }

    private fun updateNotification(score: Float, isReel: Boolean? = null) {
        try {
            val nm = notifyManager ?: return
            val label = if ((isReel ?: (score > 0.5f))) "REEL DETECTED" else "Normal Traffic"
            val text = String.format("%s (%.0f%%)", label, score * 100f)
            val builder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                Notification.Builder(this, channelId)
            } else {
                @Suppress("DEPRECATION")
                Notification.Builder(this)
            }
            val launchIntent2 = Intent(this, MainActivity::class.java)
            val pi2 = PendingIntent.getActivity(this, 0, launchIntent2, PendingIntent.FLAG_IMMUTABLE)
            val not = builder
                .setContentTitle("Reel Detector")
                .setContentText(text)
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentIntent(pi2)
                .setCategory(Notification.CATEGORY_SERVICE)
                .setPriority(Notification.PRIORITY_DEFAULT)
                .setOnlyAlertOnce(true)
                .setOngoing(true)
                .build()
            nm.notify(101, not)
            currentNotification = not
        } catch (e: Exception) {
            Log.w(TAG, "Failed to update notification: ${e.message}")
        }
    }

    private fun broadcastPrediction(score: Float, isReel: Boolean? = null) {
        val intent = Intent("REEL_PREDICTION_UPDATE")
            .setPackage(packageName)
            .addFlags(Intent.FLAG_RECEIVER_FOREGROUND)
        intent.putExtra("score", score)
        isReel?.let { intent.putExtra("isReel", it) }
        try {
            sendBroadcast(intent)
        } catch (e: Exception) {
            Log.w(TAG, "broadcast failed: ${e.message}")
        }
    }
}
