package com.example.handgesturecontroller

import android.content.Context
import android.media.AudioManager
import android.os.SystemClock
import androidx.camera.core.ImageProxy
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.framework.image.MPImage
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarker
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarkerResult

class SingleHandController(
    private val context: Context,
    private val onNext: () -> Unit,
    private val onPrevious: () -> Unit,
    private val onTap: () -> Unit
) {

    private var handLandmarker: HandLandmarker? = null
    private val audioManager = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager

    // State latch to enforce strict one-time action per gesture
    private var previousGesture = "NONE"

    init {
        setupLandmarker()
    }

    private fun setupLandmarker() {
        val baseOptions = BaseOptions.builder()
            .setModelAssetPath("hand_landmarker.task")
            .build()

        val options = HandLandmarker.HandLandmarkerOptions.builder()
            .setBaseOptions(baseOptions)
            .setRunningMode(RunningMode.LIVE_STREAM)
            .setNumHands(1)
            .setMinHandDetectionConfidence(0.4f)
            .setMinTrackingConfidence(0.4f)
            .setResultListener { result, _ -> processLandmarks(result) }
            .build()

        handLandmarker = HandLandmarker.createFromOptions(context, options)
    }

    fun processFrame(imageProxy: ImageProxy) {
        val bitmap = imageProxy.toBitmap()
        val mpImage: MPImage = BitmapImageBuilder(bitmap).build()
        val frameTime = SystemClock.uptimeMillis()

        handLandmarker?.detectAsync(mpImage, frameTime)
        imageProxy.close()
    }

    private fun processLandmarks(result: HandLandmarkerResult) {
        val landmarksList = result.landmarks()
        if (landmarksList.isEmpty()) {
            previousGesture = "NONE"
            return
        }

        val landmarks = landmarksList[0]

        val indexTip = landmarks[8]
        val middleTip = landmarks[12]
        val ringTip = landmarks[16]
        val pinkyTip = landmarks[20]

        // Extensions
        val indexUp = indexTip.y() < landmarks[6].y()
        val middleUp = middleTip.y() < landmarks[10].y()
        val ringUp = ringTip.y() < landmarks[14].y()
        val pinkyUp = pinkyTip.y() < landmarks[18].y()

        val isFist = !indexUp && !middleUp && !ringUp && !pinkyUp
        val isPalm = indexUp && middleUp && ringUp && pinkyUp
        val oneFinger = indexUp && !middleUp && !ringUp && !pinkyUp
        val twoFingers = indexUp && middleUp && !ringUp && !pinkyUp
        val threeFingers = indexUp && middleUp && ringUp && !pinkyUp

        val currentDetected = when {
            oneFinger -> "ONE_FINGER"
            twoFingers -> "TWO_FINGERS"
            threeFingers -> "THREE_FINGERS"
            isPalm -> "PALM"
            isFist -> "FIST"
            else -> "UNKNOWN"
        }

        // Latch: trigger once when transitioning into a new gesture
        if (currentDetected != previousGesture) {
            when (currentDetected) {
                "ONE_FINGER" -> onTap()
                "TWO_FINGERS" -> audioManager.adjustVolume(AudioManager.ADJUST_RAISE, AudioManager.FLAG_SHOW_UI)
                "THREE_FINGERS" -> audioManager.adjustVolume(AudioManager.ADJUST_LOWER, AudioManager.FLAG_SHOW_UI)
                "PALM" -> onNext()
                "FIST" -> onPrevious()
            }
            previousGesture = currentDetected
        }
    }

    fun close() {
        handLandmarker?.close()
    }
}