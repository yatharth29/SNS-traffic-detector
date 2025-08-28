package com.example.reeldetector

import android.content.res.AssetManager
import com.google.gson.Gson
import com.google.gson.annotations.SerializedName
import java.io.InputStreamReader

data class ScalerConfig(
    val mean: List<Double>,
    @SerializedName(value = "scale", alternate = ["std"]) val scale: List<Double>?
)

class Normalizer(private val mean: FloatArray, private val scale: FloatArray) {
    companion object {
        fun fromAssets(am: AssetManager, path: String = "scaler.json"): Normalizer {
            val reader = InputStreamReader(am.open(path))
            val cfg = Gson().fromJson(reader, ScalerConfig::class.java)
            reader.close()
            val meanArr = cfg.mean.map { it.toFloat() }.toFloatArray()
            val scaleList = cfg.scale ?: cfg.mean.map { 1.0 } // fallback to ones if absent
            val scaleArr = scaleList.map { it.toFloat() }.toFloatArray()
            return Normalizer(meanArr, scaleArr)
        }
    }

    fun normalize(features: FloatArray): FloatArray {
        val out = FloatArray(features.size)
        val n = features.size
        for (i in 0 until n) {
            val m = if (i < mean.size) mean[i] else 0f
            val s = if (i < scale.size && scale[i] != 0f) scale[i] else 1f
            out[i] = (features[i] - m) / s
        }
        return out
    }
}


