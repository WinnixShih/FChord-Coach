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
                .setNumHands(1)
                .setMinHandDetectionConfidence(0.5f)
                .setMinTrackingConfidence(0.5f)
                .build()
            handLandmarker = HandLandmarker.createFromOptions(context, options)
        }

        val mpImage = BitmapImageBuilder(bitmap).build()
        val detectionResult = handLandmarker!!.detect(mpImage)

        if (detectionResult.landmarks().isEmpty()) return null

        return detectionResult.landmarks()[0].map { landmark ->
            mapOf(
                "x" to landmark.x().toDouble(),
                "y" to landmark.y().toDouble(),
                "z" to landmark.z().toDouble(),
            )
        }
    }
}
