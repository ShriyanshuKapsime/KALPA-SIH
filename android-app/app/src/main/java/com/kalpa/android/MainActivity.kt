package com.kalpa.android

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.*
import com.kalpa.android.screens.BusinessIntakeScreen
import com.kalpa.android.screens.KalpaLandingScreen

private enum class KalpaScreen {
    LANDING,
    BUSINESS_INTAKE
}

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            MaterialTheme {
                var currentScreen by remember {
                    mutableStateOf(KalpaScreen.LANDING)
                }

                when (currentScreen) {

                    KalpaScreen.LANDING -> {
                        KalpaLandingScreen(
                            onStartBusiness = {
                                currentScreen = KalpaScreen.BUSINESS_INTAKE
                            }
                        )
                    }

                    KalpaScreen.BUSINESS_INTAKE -> {
                        BusinessIntakeScreen()
                    }
                }
            }
        }
    }
}