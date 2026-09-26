package com.kalpa.android.screens

import androidx.compose.animation.core.*
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import com.kalpa.android.R
import kotlinx.coroutines.delay

@Composable
fun SplashScreen(
    onSplashFinished: () -> Unit
) {
    var startAnimation by remember { mutableStateOf(false) }
    
    val scale = animateFloatAsState(
        targetValue = if (startAnimation) 1.2f else 0.8f,
        animationSpec = tween(
            durationMillis = 1000,
            easing = { OvershootInterpolator().getInterpolation(it) }
        )
    )

    LaunchedEffect(key1 = true) {
        startAnimation = true
        delay(2000) // Delay for 2 seconds to show splash
        onSplashFinished()
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(KalpaScreenColors.ScreenBackgroundCream),
        contentAlignment = Alignment.Center
    ) {
        Image(
            painter = painterResource(id = R.drawable.ic_launcher_foreground),
            contentDescription = "KALPA Logo",
            modifier = Modifier
                .size(150.dp)
                .scale(scale.value)
        )
    }
}

// Simple overshoot interpolator for smooth spring effect
private class OvershootInterpolator {
    fun getInterpolation(t: Float): Float {
        val tension = 2.0f
        val t2 = t - 1.0f
        return t2 * t2 * ((tension + 1) * t2 + tension) + 1.0f
    }
}
