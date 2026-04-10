package com.fchordcoach.app

import android.content.Context
import android.graphics.BitmapFactory
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarker
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarkerOptions
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

/**
 * Flutter ↔ Android 橋接層：接收 camera_page.dart 傳來的 JPEG 路徑，
 * 用 MediaPipe HandLandmarker 分析後回傳 21 個關節座標。
 *
 * 使用方式（在 MainActivity.kt 的 configureFlutterEngine 裡呼叫）：
 *   MediaPipeHandsChannel.register(flutterEngine, this)
 */
object MediaPipeHandsChannel {

    private const val CHANNEL_NAME = "fchord/mediapipe"

    // HandLandmarker 只初始化一次，避免每次分析都重新載入模型（~200ms）
    private var handLandmarker: HandLandmarker? = null

    fun register(flutterEngine: FlutterEngine, context: Context) {
        val channel = MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            CHANNEL_NAME,
        )

        channel.setMethodCallHandler { call, result ->
            when (call.method) {
                "detect" -> {
                    val path = call.argument<String>("path")
                    if (path == null) {
                        result.error("INVALID_ARG", "path is required", null)
                        return@setMethodCallHandler
                    }
                    try {
                        val landmarks = detect(context, path)
                        result.success(landmarks)
                    } catch (e: Exception) {
                        result.error("DETECT_FAILED", e.message, null)
                    }
                }
                else -> result.notImplemented()
            }
        }
    }

    /**
     * 核心推論邏輯：
     * 1. 讀取 JPEG → Bitmap
     * 2. 初始化 HandLandmarker（首次呼叫時）
     * 3. 執行偵測
     * 4. 回傳 List<Map<String, Double>>，每個 Map 含 x/y/z
     *    若偵測不到手則回傳 null
     */
    private fun detect(context: Context, imagePath: String): List<Map<String, Double>>? {
        val bitmap = BitmapFactory.decodeFile(imagePath) ?: return null

        // 延遲初始化：首次呼叫時才載入模型（模型在 assets/hand_landmarker.task）
        if (handLandmarker == null) {
            val baseOptions = BaseOptions.builder()
                .setModelAssetPath("hand_landmarker.task")
                .build()
            val options = HandLandmarkerOptions.builder()
                .setBaseOptions(baseOptions)
                .setNumHands(1)          // F 和弦只需偵測一隻手
                .setMinHandDetectionConfidence(0.5f)
                .setMinTrackingConfidence(0.5f)
                .build()
            handLandmarker = HandLandmarker.createFromOptions(context, options)
        }

        val mpImage = BitmapImageBuilder(bitmap).build()
        val detectionResult = handLandmarker!!.detect(mpImage)

        // 沒偵測到手
        if (detectionResult.landmarks().isEmpty()) return null

        // 取第一隻手的 21 個關節，轉成 Flutter 可讀的 List<Map>
        return detectionResult.landmarks()[0].map { landmark ->
            mapOf(
                "x" to landmark.x().toDouble(),
                "y" to landmark.y().toDouble(),
                "z" to landmark.z().toDouble(),
            )
        }
    }
}
