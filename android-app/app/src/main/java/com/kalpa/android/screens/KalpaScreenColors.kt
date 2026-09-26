package com.kalpa.android.screens

import androidx.compose.ui.graphics.Color

/**
 * Single source of truth for KALPA screen colors.
 *
 * IMPORTANT: declare colors ONLY here, never inline inside an individual
 * screen file. Every screen in this package can already see this object
 * with no import needed (same package). Duplicating a color object inside
 * a screen file is what causes "Redeclaration" / "private in file" errors
 * when files are copy-pasted or edited by hand — keeping exactly one
 * declaration here makes that class of error impossible.
 */
internal object KalpaScreenColors {
    // Screen backgrounds (some screens use white, some a warm cream)
    val ScreenBackgroundWhite = Color(0xFFFFFFFF)
    val OrangeDeep = Color(0xFF8A5A0B)
    val MapLand         = Color(0xFFF3EFE6)
    val MapWater        = Color(0xFFCFD9DC)
    val MapGreen        = Color(0xFFE2E9DB)
    val StatusGreenBg   = Color(0xFFE6EDE6)
    val StatusGreenText = Color(0xFF5B7F62)
    val DelayRed        = Color(0xFFC8452F)
    val ScreenBackgroundCream = Color(0xFFF7F3EC)
    val CardWhite = Color(0xFFFFFFFF)

    // Brand / accent
    val Orange = Color(0xFFCC7A00)
    val OrangeDark = Color(0xFFB5690A)
    val OrangeSoftMic = Color(0xFFF6E3C4)   // mic button outer ring
    val OrangeSoftAlt = Color(0xFFF3D9AE)   // alternate soft tone
    val OrangeBadgeBg = Color(0xFFFBEAD2)

    // Text
    val TextPrimary = Color(0xFF241F1B)
    val TextSecondary = Color(0xFF6F675D)
    val TextMuted = Color(0xFF9C9184)

    // Surfaces / lines
    val Divider = Color(0xFFEDE7DD)
    val PillGray = Color(0xFFF1EEE7)
    val FieldGray = Color(0xFFF5F2EC)
    val QuoteBg = Color(0xFFF7F3EC)
    val InfoBannerBg = Color(0xFFEFEAE0)
    val IconCircleBg = Color(0xFFF6E3C4)

    // Misc
    val LinkBlue = Color(0xFF3E6FB0)
    val ProfileBrown = Color(0xFF4A3B1F)

    // Progress checklist / timeline steps
    val StepDoneBg = Color(0xFFE7DCC3)       // completed step circle (tan)
    val StepDoneIcon = Color(0xFF6F675D)     // checkmark tint on a done step
    val StepUpcomingBg = Color(0xFF8C8377)   // upcoming step circle (taupe)
    val ReviewCardBg = Color(0xFFEFEBE3)     // "Business in review" info card
}