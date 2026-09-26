package com.kalpa.android.navigation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.kalpa.android.screens.BusinessFeasibilityScreen
import com.kalpa.android.screens.BusinessIntakeScreen
import com.kalpa.android.screens.BusinessPlanDPRScreen
import com.kalpa.android.screens.BusinessSWOTScreen
import com.kalpa.android.screens.BusinessUnderstandingClassificationScreen
import com.kalpa.android.screens.EnterpriseRiskScreen
import com.kalpa.android.screens.EntrepreneurProfileScreen
import com.kalpa.android.screens.EntrepreneurReadinessScreen
import com.kalpa.android.screens.GrowthManagerScreen
import com.kalpa.android.screens.KalpaBusinessAssistantScreen
import com.kalpa.android.screens.KalpaIsAnalysingScreen
import com.kalpa.android.screens.KalpaScreenColors
import com.kalpa.android.screens.LandingScreen
import com.kalpa.android.screens.YourLocalMarketScreen
import com.kalpa.android.screens.BusinessOpportunityScreen
import com.kalpa.android.screens.YourMoneyScreen
import com.kalpa.android.screens.SplashScreen

/**
 * Route names for the fixed 15-screen journey.
 *
 * [JOURNEY] is the single source of truth for ordering. "Next" is always the
 * following entry in this list, so screens never need to know their successor.
 */
object KalpaRoutes {
    const val SPLASH_SCREEN = "splash_screen"
    const val LANDING = "landing"
    const val BUSINESS_INTAKE = "business_intake"
    const val BUSINESS_UNDERSTANDING_CLASSIFICATION = "business_understanding_classification"
    const val ENTREPRENEUR_PROFILE = "entrepreneur_profile"
    const val KALPA_IS_ANALYSING = "kalpa_is_analysing"
    const val YOUR_LOCAL_MARKET = "your_local_market"
    const val BUSINESS_OPPORTUNITY = "business_opportunity"
    const val YOUR_MONEY = "your_money"
    const val ENTREPRENEUR_READINESS = "entrepreneur_readiness"
    const val ENTERPRISE_RISK = "enterprise_risk"
    const val BUSINESS_FEASIBILITY = "business_feasibility"
    const val BUSINESS_SWOT = "business_swot"
    const val BUSINESS_PLAN_DPR = "business_plan_dpr"
    const val KALPA_BUSINESS_ASSISTANT = "kalpa_business_assistant"
    const val GROWTH_MANAGER = "growth_manager"

    val JOURNEY: List<String> = listOf(
        LANDING,
        BUSINESS_INTAKE,
        BUSINESS_UNDERSTANDING_CLASSIFICATION,
        ENTREPRENEUR_PROFILE,
        KALPA_IS_ANALYSING,
        YOUR_LOCAL_MARKET,
        BUSINESS_OPPORTUNITY,
        YOUR_MONEY,
        ENTREPRENEUR_READINESS,
        ENTERPRISE_RISK,
        BUSINESS_FEASIBILITY,
        BUSINESS_SWOT,
        BUSINESS_PLAN_DPR,
        KALPA_BUSINESS_ASSISTANT,
        GROWTH_MANAGER
    )
}

/** Navigates to the screen after [current] in the journey. No-op on the last screen. */
private fun NavHostController.goToNext(current: String) {
    val index = KalpaRoutes.JOURNEY.indexOf(current)
    if (index < 0) return
    val next = KalpaRoutes.JOURNEY.getOrNull(index + 1) ?: return
    navigate(next) { launchSingleTop = true } // launchSingleTop guards against double-taps
}

/** Goes back one screen; safe if there is nothing left to pop. */
private fun NavHostController.goBack() {
    if (previousBackStackEntry != null) popBackStack()
}

@Composable
fun KalpaNavGraph(
    navController: NavHostController = rememberNavController(),
    startDestination: String = KalpaRoutes.SPLASH_SCREEN
) {
    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        composable(KalpaRoutes.SPLASH_SCREEN) {
            SplashScreen(
                onSplashFinished = {
                    navController.navigate(KalpaRoutes.LANDING) {
                        popUpTo(KalpaRoutes.SPLASH_SCREEN) { inclusive = true }
                    }
                }
            )
        }

        // ---- 1. Landing / Journey Hub ---------------------------------
        composable(KalpaRoutes.LANDING) {
            LandingScreen(
                onStartJourneyClick = { navController.goToNext(KalpaRoutes.LANDING) },
                onResumeJourneyClick = {
                    // TODO: once progress is persisted, resume at the user's
                    // last completed step instead of always going to Intake.
                    navController.goToNext(KalpaRoutes.LANDING)
                },
                onRoadmapStepClick = { stepIndex ->
                    // Optional: jump to a specific step in the roadmap.
                },
                onProfileClick = {
                    // Navigate to a profile/account screen if you add one.
                }
            )
        }

        // ---- 2. Business Intake ---------------------------------------
        composable(KalpaRoutes.BUSINESS_INTAKE) {
            BusinessIntakeScreen(
                onBackClick = { navController.goBack() },
                onConfirmContinue = { businessIdeaText ->
                    // TODO: stash businessIdeaText in a shared ViewModel if later
                    // screens need it.
                    navController.goToNext(KalpaRoutes.BUSINESS_INTAKE)
                },
                onMicToggle = { isRecording ->
                    // Hook up real speech-to-text here if/when you add it.
                }
            )
        }

        // ---- 3. Business Understanding / Classification ----------------
        composable(KalpaRoutes.BUSINESS_UNDERSTANDING_CLASSIFICATION) {
            BusinessUnderstandingClassificationScreen(
                onBackClick = { navController.goBack() },
                onContinueClick = {
                    navController.goToNext(KalpaRoutes.BUSINESS_UNDERSTANDING_CLASSIFICATION)
                },
                onChangeSomethingClick = { navController.goBack() },
                onFieldEditClick = { fieldLabel ->
                    // Open an edit dialog/bottom sheet for the tapped field.
                },
                onSeeClassificationDetailsClick = {
                    // Show the NIC code / scheme mapping details.
                }
            )
        }

        // ---- 4. Entrepreneur Profile -----------------------------------
        composable(KalpaRoutes.ENTREPRENEUR_PROFILE) {
            EntrepreneurProfileScreen(
                onBackClick = { navController.goBack() },
                onExperienceWhyLinkClick = {
                    // Show the "why experience helps you get a loan" explanation.
                },
                onContinueClick = { selectedExperienceIndex, selectedSkills ->
                    // TODO: stash these in a shared ViewModel if later screens need them.
                    navController.goToNext(KalpaRoutes.ENTREPRENEUR_PROFILE)
                }
            )
        }

        // ---- 5. KALPA Is Analysing -------------------------------------
        composable(KalpaRoutes.KALPA_IS_ANALYSING) {
            KalpaIsAnalysingScreen(
                onBackClick = { navController.goBack() },
                onSeeProgressClick = { navController.goToNext(KalpaRoutes.KALPA_IS_ANALYSING) }
            )
        }
        
        // ---- 6. Your Local Market --------------------------------------
        composable(KalpaRoutes.YOUR_LOCAL_MARKET) {
            YourLocalMarketScreen(
                onBackClick = { navController.goBack() },
                onContinueClick = { navController.goToNext(KalpaRoutes.YOUR_LOCAL_MARKET) }
            )
        }

        // ---- 7. Business Opportunity -----------------------------------
        composable(KalpaRoutes.BUSINESS_OPPORTUNITY) {
            BusinessOpportunityScreen(
                onBackClick = { navController.goBack() },
                onContinueClick = { navController.goToNext(KalpaRoutes.BUSINESS_OPPORTUNITY) }
            )
        }

        // ---- 8. Your Money ---------------------------------------------
        composable(KalpaRoutes.YOUR_MONEY) {
            YourMoneyScreen(
                onBackClick = { navController.goBack() },
                onContinueClick = { navController.goToNext(KalpaRoutes.YOUR_MONEY) }
            )
        }
        
        // ---- 9. Entrepreneur Readiness ---------------------------------
        composable(KalpaRoutes.ENTREPRENEUR_READINESS) {
            EntrepreneurReadinessScreen(
                onBackClick = { navController.goBack() },
                onContinueClick = { navController.goToNext(KalpaRoutes.ENTREPRENEUR_READINESS) }
            )
        }
        
        // ---- 10. Enterprise Risk ---------------------------------------
        composable(KalpaRoutes.ENTERPRISE_RISK) {
            EnterpriseRiskScreen(
                onBackClick = { navController.goBack() },
                onContinueClick = { navController.goToNext(KalpaRoutes.ENTERPRISE_RISK) }
            )
        }
        
        // ---- 11. Business Feasibility ----------------------------------
        composable(KalpaRoutes.BUSINESS_FEASIBILITY) {
            BusinessFeasibilityScreen(
                onBackClick = { navController.goBack() },
                onContinueClick = { navController.goToNext(KalpaRoutes.BUSINESS_FEASIBILITY) }
            )
        }
        
        // ---- 12. Business SWOT -----------------------------------------
        composable(KalpaRoutes.BUSINESS_SWOT) {
            BusinessSWOTScreen(
                onBackClick = { navController.goBack() },
                onContinueClick = { navController.goToNext(KalpaRoutes.BUSINESS_SWOT) }
            )
        }
        
        // ---- 13. Business Plan / DPR -----------------------------------
        composable(KalpaRoutes.BUSINESS_PLAN_DPR) {
            BusinessPlanDPRScreen(
                onBackClick = { navController.goBack() },
                onContinueClick = { navController.goToNext(KalpaRoutes.BUSINESS_PLAN_DPR) }
            )
        }
        
        // ---- 14. KALPA Business Assistant ------------------------------
        composable(KalpaRoutes.KALPA_BUSINESS_ASSISTANT) {
            KalpaBusinessAssistantScreen(
                onBackClick = { navController.goBack() },
                onContinueClick = { navController.goToNext(KalpaRoutes.KALPA_BUSINESS_ASSISTANT) }
            )
        }
        
        // ---- 15. Growth Manager ----------------------------------------
        composable(KalpaRoutes.GROWTH_MANAGER) {
            GrowthManagerScreen(
                onBackClick = { navController.goBack() },
                onContinueClick = { navController.goToNext(KalpaRoutes.GROWTH_MANAGER) }
            )
        }

        // ---- remaining: screens not built yet -------------------------------
        // Each gets a temporary placeholder so the full 1 -> 15 flow works now.
        // When a real screen file exists, replace its entry here with:
        //
        //   composable(KalpaRoutes.XXX) {
        //       XxxScreen(
        //           onBackClick = { navController.goBack() },
        //           onContinueClick = { navController.goToNext(KalpaRoutes.XXX) }
        //       )
        //   }
        //
        // and remove its line from PENDING_SCREENS.
        PENDING_SCREENS.forEach { (route, title) ->
            composable(route) {
                val hasNext = KalpaRoutes.JOURNEY.indexOf(route) < KalpaRoutes.JOURNEY.lastIndex
                PendingScreen(
                    title = title,
                    position = KalpaRoutes.JOURNEY.indexOf(route) + 1,
                    onBackClick = { navController.goBack() },
                    onContinueClick = if (hasNext) {
                        { navController.goToNext(route) }
                    } else null
                )
            }
        }
    }
}

private val PENDING_SCREENS: List<Pair<String, String>> = emptyList()

/** Temporary stand-in for a screen that hasn't been built yet. */
@Composable
private fun PendingScreen(
    title: String,
    position: Int,
    onBackClick: () -> Unit,
    onContinueClick: (() -> Unit)?
) {
    Scaffold(containerColor = KalpaScreenColors.ScreenBackgroundCream) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp, Alignment.CenterVertically),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "Screen $position of ${KalpaRoutes.JOURNEY.size}",
                fontSize = 13.sp,
                color = KalpaScreenColors.TextMuted
            )
            Text(
                text = title,
                fontSize = 24.sp,
                fontWeight = FontWeight.Bold,
                color = KalpaScreenColors.TextPrimary
            )
            Text(
                text = "This screen hasn't been built yet.",
                fontSize = 14.sp,
                color = KalpaScreenColors.TextSecondary
            )
            if (onContinueClick != null) {
                Button(
                    onClick = onContinueClick,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(54.dp),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = KalpaScreenColors.Orange,
                        contentColor = Color.White
                    )
                ) { Text("Continue") }
            }
            OutlinedButton(
                onClick = onBackClick,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(54.dp),
                shape = RoundedCornerShape(14.dp)
            ) { Text("Back", color = KalpaScreenColors.TextPrimary) }
        }
    }
}