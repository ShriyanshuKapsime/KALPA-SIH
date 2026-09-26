package com.kalpa.android.utils

import android.content.Context
import android.media.MediaRecorder
import android.os.Build
import android.util.Log
import java.io.File
import java.io.IOException

class AudioRecorderHelper(private val context: Context) {
    private var mediaRecorder: MediaRecorder? = null
    private var audioFile: File? = null

    fun startRecording() {
        val cacheDir = context.cacheDir
        audioFile = File(cacheDir, "kalpa_recording_${System.currentTimeMillis()}.3gp")

        mediaRecorder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            MediaRecorder(context)
        } else {
            @Suppress("DEPRECATION")
            MediaRecorder()
        }.apply {
            setAudioSource(MediaRecorder.AudioSource.MIC)
            setOutputFormat(MediaRecorder.OutputFormat.THREE_GPP)
            setAudioEncoder(MediaRecorder.AudioEncoder.AMR_NB)
            setOutputFile(audioFile?.absolutePath)

            try {
                prepare()
                start()
                Log.d("AudioRecorderHelper", "Recording started: ${audioFile?.absolutePath}")
            } catch (e: IOException) {
                Log.e("AudioRecorderHelper", "prepare() failed", e)
            }
        }
    }

    fun stopRecording(): String? {
        try {
            mediaRecorder?.apply {
                stop()
                release()
            }
            mediaRecorder = null
            Log.d("AudioRecorderHelper", "Recording stopped")
            return audioFile?.absolutePath
        } catch (e: Exception) {
            Log.e("AudioRecorderHelper", "stop() failed", e)
            return null
        }
    }
}
