package com.example.reeldetector

import android.app.Activity
import android.Manifest
import android.content.pm.PackageManager
import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import android.widget.Switch
import android.os.Handler
import android.os.Looper
import android.os.Build
import android.content.BroadcastReceiver
import android.content.Context
import android.content.IntentFilter
import android.net.VpnService
import com.google.gson.Gson
import java.io.InputStreamReader

class MainActivity : Activity() {
    lateinit var featureBuffer: FeatureBuffer
    lateinit var classifier: TFLiteClassifier
    private val handler = Handler(Looper.getMainLooper())
    private var isMonitoring = false
    
    // UI elements
    lateinit var btnStart: Button
    lateinit var btnLabelStart: Button
    lateinit var btnLabelEnd: Button
    lateinit var tvStatus: TextView
    lateinit var tvPrediction: TextView
    lateinit var tvConfidence: TextView
    lateinit var switchMonitoring: Switch
    private var predictionReceiver: BroadcastReceiver? = null
    private val REQ_VPN = 2001

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        ensureNotificationPermission()

        // Initialize UI elements
        btnStart = findViewById(R.id.btnStart)
        btnLabelStart = findViewById(R.id.btnLabelStart)
        btnLabelEnd = findViewById(R.id.btnLabelEnd)
        tvStatus = findViewById(R.id.tvStatus)
        tvPrediction = findViewById(R.id.tvPrediction)
        tvConfidence = findViewById(R.id.tvConfidence)
        switchMonitoring = findViewById(R.id.switchMonitoring)
        
        // Initialize feature buffer
        featureBuffer = FeatureBuffer("192.168.1.100") // Replace with your device IP
        
        // Try to load the classifier
        try {
            classifier = TFLiteClassifier(assets, "model_quant.tflite")
            tvStatus.text = "Model loaded successfully"
        } catch (e: Exception) {
            tvStatus.text = "Model not found. Use synthetic data for now."
        }

        btnStart.setOnClickListener {
            ensureVpnConsent {
                val intent = Intent(this, CaptureVpnService::class.java)
                startService(intent)
                tvStatus.text = "Capture started"
            }
        }

        btnLabelStart.setOnClickListener {
            val intent = Intent(this, CaptureVpnService::class.java)
            intent.action = "LABEL_START"
            startService(intent)
            tvStatus.text = "Label REEL started"
        }

        btnLabelEnd.setOnClickListener {
            val intent = Intent(this, CaptureVpnService::class.java)
            intent.action = "LABEL_END"
            startService(intent)
            tvStatus.text = "Label ended"
        }
        
        switchMonitoring.setOnCheckedChangeListener { _, isChecked ->
            isMonitoring = isChecked
            if (isChecked) {
                ensureVpnConsent {
                    startMonitoring()
                    val i = Intent(this, CaptureVpnService::class.java)
                    i.action = "REALTIME_ON"
                    startService(i)
                }
            } else {
                stopMonitoring()
                val i = Intent(this, CaptureVpnService::class.java)
                i.action = "REALTIME_OFF"
                startService(i)
            }
        }
    }

    private fun ensureNotificationPermission() {
        if (Build.VERSION.SDK_INT >= 33) {
            val granted = checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED
            if (!granted) {
                requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1001)
            }
        }
    }
    
    private fun startMonitoring() {
        tvStatus.text = "Real-time monitoring started"
        registerPredictionReceiver()
    }
    
    private fun stopMonitoring() {
        tvStatus.text = "Monitoring stopped"
        tvPrediction.text = "No prediction"
        tvConfidence.text = "Confidence: --"
        unregisterPredictionReceiver()
    }
    
    private fun registerPredictionReceiver() {
        if (predictionReceiver != null) return
        predictionReceiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context?, intent: Intent?) {
                if (intent?.action == "REEL_PREDICTION_UPDATE") {
                    val score = intent.getFloatExtra("score", 0f)
                    val isReel = intent.getBooleanExtra("isReel", score > 0.5f)
                    tvPrediction.text = if (isReel) "REEL DETECTED! 🎬" else "Normal Traffic 📱"
                    tvConfidence.text = "Confidence: ${(score * 100).toInt()}%"
                }
            }
        }
        val filter = IntentFilter("REEL_PREDICTION_UPDATE")
        filter.priority = IntentFilter.SYSTEM_HIGH_PRIORITY
        if (Build.VERSION.SDK_INT >= 34) {
            registerReceiver(predictionReceiver, filter, RECEIVER_NOT_EXPORTED)
        } else {
            registerReceiver(predictionReceiver, filter)
        }
    }

    private fun ensureVpnConsent(onGranted: () -> Unit) {
        val intent = VpnService.prepare(this)
        if (intent != null) {
            try {
                startActivityForResult(intent, REQ_VPN)
            } catch (_: Exception) {
                // fallback: if something goes wrong, do nothing; user can try again
            }
        } else {
            onGranted()
        }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQ_VPN && resultCode == RESULT_OK) {
            // Start capture after consent
            val intent = Intent(this, CaptureVpnService::class.java)
            startService(intent)
            if (isMonitoring) {
                val i = Intent(this, CaptureVpnService::class.java)
                i.action = "REALTIME_ON"
                startService(i)
            }
            tvStatus.text = "VPN consent granted; capture started"
        }
    }

    private fun unregisterPredictionReceiver() {
        predictionReceiver?.let {
            try { unregisterReceiver(it) } catch (_: Exception) {}
        }
        predictionReceiver = null
    }
    
    override fun onDestroy() {
        super.onDestroy()
        stopMonitoring()
    }
}
