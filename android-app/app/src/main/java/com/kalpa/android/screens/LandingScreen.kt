package com.kalpa.android.screens

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowForward
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.Language
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.outlined.Description
import androidx.compose.material.icons.outlined.Explore
import androidx.compose.material.icons.outlined.Image as ImageIcon
import androidx.compose.material.icons.outlined.Lightbulb
import androidx.compose.material.icons.outlined.LocalFlorist
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// ---------- Color palette pulled from the design ----------
private val BackgroundCream = Color(0xFFF8F4EC)
private val TopBarBeige = Color(0xFFEFE8DA)
private val OrangePrimary = Color(0xFFDB8B1F)
private val OrangeText = Color(0xFFC77E1B)
private val TextBlack = Color(0xFF1C1B19)
private val TextGraySubtle = Color(0xFF9C9385)
private val IllustrationBg = Color(0xFFF1E9DA)
private val AvatarBrown = Color(0xFF5B3E22)
private val BorderGray = Color(0xFFE6E0D4)
private val StepIconBg = Color(0xFFF3EEE3)

@Composable
fun KalpaLandingScreen(onStartBusiness: () -> Unit) {
    Surface(modifier = Modifier.fillMaxSize(), color = BackgroundCream) {
        Column(modifier = Modifier.fillMaxSize()) {
            TopBar()
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 20.dp)
            ) {
                Spacer(modifier = Modifier.height(20.dp))
                HeroSection()
                Spacer(modifier = Modifier.height(20.dp))
                IllustrationCard()
                Spacer(modifier = Modifier.height(20.dp))
                StartBusinessButton(onClick = onStartBusiness)
                Spacer(modifier = Modifier.height(12.dp))
                ContinueJourneyButton()
                Spacer(modifier = Modifier.height(16.dp))
                YourJourneySection()
                Spacer(modifier = Modifier.height(24.dp))
            }
        }
    }
}

@Composable
private fun TopBar() {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(TopBarBeige)
            .padding(horizontal = 16.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        // Logo
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(16.dp)
                    .clip(RoundedCornerShape(3.dp))
                    .background(OrangePrimary)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = "KALPA",
                color = TextBlack,
                fontWeight = FontWeight.ExtraBold,
                fontSize = 18.sp,
                letterSpacing = 0.5.sp
            )
        }

        Row(verticalAlignment = Alignment.CenterVertically) {
            // Language selector pill
            Surface(
                shape = RoundedCornerShape(50),
                color = Color.White,
                border = androidx.compose.foundation.BorderStroke(1.dp, BorderGray),
                modifier = Modifier.height(34.dp)
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.Default.Language,
                        contentDescription = "Language",
                        tint = TextBlack,
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(text = "English", color = TextBlack, fontSize = 13.sp)
                    Spacer(modifier = Modifier.width(2.dp))
                    Icon(
                        imageVector = Icons.Default.KeyboardArrowDown,
                        contentDescription = null,
                        tint = TextBlack,
                        modifier = Modifier.size(16.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.width(10.dp))

            // Avatar
            Box(
                modifier = Modifier
                    .size(34.dp)
                    .clip(CircleShape)
                    .background(AvatarBrown),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.Person,
                    contentDescription = "Profile",
                    tint = Color.White,
                    modifier = Modifier.size(18.dp)
                )
            }
        }
    }
}

@Composable
private fun HeroSection() {
    Column {
        Text(
            text = "Build a business with confidence.",
            color = TextBlack,
            fontSize = 27.sp,
            fontWeight = FontWeight.ExtraBold,
            lineHeight = 33.sp
        )
        Spacer(modifier = Modifier.height(10.dp))
        Text(
            text = "KALPA helps you understand your market, money and risks before you invest.",
            color = OrangeText,
            fontSize = 15.sp,
            lineHeight = 21.sp,
            fontWeight = FontWeight.Medium
        )
    }
}

@Composable
private fun IllustrationCard() {
    // Clean elevation shadow used instead of the muddy orange gradient bleed
    // that appears at the bottom of the card in the original screenshot.
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(230.dp)
            .shadow(elevation = 6.dp, shape = RoundedCornerShape(24.dp), clip = false)
            .clip(RoundedCornerShape(24.dp))
            .background(Color.White)
            .padding(20.dp),
        contentAlignment = Alignment.Center
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .clip(RoundedCornerShape(16.dp))
                .background(IllustrationBg),
            contentAlignment = Alignment.Center
        ) {
            // Placeholder for the shop/house illustration.
            // Replace this Image with your actual asset, e.g.:
            // Image(painter = painterResource(R.drawable.shop_illustration), contentDescription = null)
            Text(
                text = "🏠",
                fontSize = 56.sp
            )
        }
    }
}

@Composable
private fun StartBusinessButton(onClick: () -> Unit) {
    Button(
        onClick = onClick,
        modifier = Modifier
            .fillMaxWidth()
            .height(56.dp),
        shape = RoundedCornerShape(16.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = OrangePrimary,
            contentColor = Color.White
        )
    ) {
        Text(
            text = "Start My Business",
            fontSize = 16.sp,
            fontWeight = FontWeight.SemiBold
        )
        Spacer(modifier = Modifier.width(8.dp))
        Icon(
            imageVector = Icons.Default.ArrowForward,
            contentDescription = null,
            modifier = Modifier.size(18.dp)
        )
    }
}

@Composable
private fun ContinueJourneyButton() {
    OutlinedButton(
        onClick = { /* TODO: navigate */ },
        modifier = Modifier
            .fillMaxWidth()
            .height(56.dp),
        shape = RoundedCornerShape(16.dp),
        colors = ButtonDefaults.outlinedButtonColors(
            containerColor = Color.White,
            contentColor = TextBlack
        ),
        border = androidx.compose.foundation.BorderStroke(1.dp, BorderGray)
    ) {
        Icon(
            imageVector = Icons.Default.History,
            contentDescription = null,
            modifier = Modifier.size(18.dp)
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = "Continue My Journey",
            fontSize = 15.sp,
            fontWeight = FontWeight.SemiBold
        )
    }
}

private data class JourneyStep(
    val label: String,
    val icon: ImageVector
)

@Composable
private fun YourJourneySection() {
    val steps = listOf(
        JourneyStep("Understand", Icons.Outlined.Lightbulb),
        JourneyStep("Discover", Icons.Outlined.Explore),
        JourneyStep("Plan", Icons.Outlined.ImageIcon),
        JourneyStep("Prepare", Icons.Outlined.Description),
        JourneyStep("Grow", Icons.Outlined.LocalFlorist)
    )

    Surface(
        shape = RoundedCornerShape(20.dp),
        color = Color.White,
        border = androidx.compose.foundation.BorderStroke(1.dp, BorderGray),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(vertical = 18.dp, horizontal = 16.dp)) {
            Text(
                text = "YOUR JOURNEY",
                color = TextGraySubtle,
                fontSize = 12.sp,
                fontWeight = FontWeight.SemiBold,
                letterSpacing = 1.sp
            )
            Spacer(modifier = Modifier.height(16.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                steps.forEach { step ->
                    JourneyStepItem(step)
                }
            }
        }
    }
}

@Composable
private fun JourneyStepItem(step: JourneyStep) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier.width(64.dp)
    ) {
        Box(
            modifier = Modifier
                .size(48.dp)
                .clip(CircleShape)
                .background(StepIconBg),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = step.icon,
                contentDescription = step.label,
                tint = TextBlack,
                modifier = Modifier.size(22.dp)
            )
        }
        Spacer(modifier = Modifier.height(6.dp))
        Text(
            text = step.label,
            fontSize = 11.sp,
            color = TextBlack,
            textAlign = TextAlign.Center,
            maxLines = 1
        )
    }
}

@Preview(showBackground = true, widthDp = 360, heightDp = 780)
@Composable
fun KalpaLandingScreenPreview() {
    MaterialTheme {
        KalpaLandingScreen(onStartBusiness = {})
    }
}