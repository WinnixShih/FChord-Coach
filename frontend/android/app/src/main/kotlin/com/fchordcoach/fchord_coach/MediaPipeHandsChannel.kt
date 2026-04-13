package com.fchordcoach.fchord_coach

import android.content.Context
import android.graphics.BitmapFactory
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarker
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarkerOptions
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

object MediaPipeHandsChannel {

    private const val CHANNEL_NAME = "fchord/mediapipe"

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

    private fun detect(context: Context, imagePath: String): List<Map<String, Double>>? {
        val bitmap = BitmapFactory.decodeFile(imagePath) ?: return null

        if (handLandmarker == null) {
            val baseOptions = BaseOptions.builder()
                .setModelAssetPath("hand_landmarker.task")
                .build()
            val options = HandLandmarkerOptions.builder()
                .setBaseOptions(baseOptions)
                .setNumHands(2)  // 偵測雙手，再篩出按弦手
                .setMinHandDetectionConfidence(0.5f)
                .setMinTrackingConfidence(0.5f)
                .build()
            handLandmarker = HandLandmarker.createFromOptions(context, options)
        }

        val mpImage = BitmapImageBuilder(bitmap).build()
        val detectionResult = handLandmarker!!.detect(mpImage)

        if (detectionResult.landmarks().isEmpty()) return null

        // 只取按弦手（左手）。前鏡頭儲存的 JPEG 未鏡像，
        // MediaPipe 依手部解剖學判斷左右，左手 = "Left"。
        val handednesses = detectionResult.handednesses()
        val chordHandIndex = handednesses.indexOfFirst { categories ->
            categories.firstOrNull()?.categoryName() == "Left"
        }
        if (chordHandIndex == -1) return null

        return detectionResult.landmarks()[chordHandIndex].map { landmark ->
            mapOf(
                "x" to landmark.x().toDouble(),
                "y" to landmark.y().toDouble(),
                "z" to landmark.z().toDouble(),
            )
        }
    }
}
