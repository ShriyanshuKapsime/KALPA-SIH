package com.kalpa.android.screens

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.automirrored.filled.TrendingUp
import androidx.compose.material.icons.filled.AccountBalance
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Explore
import androidx.compose.material.icons.filled.FactCheck
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Inventory2
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.SpanStyle
import com.kalpa.android.R
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// Colors live in KalpaScreenColors.kt (same package, no import needed).
// Do not redeclare a color object in this file.



private data class RoadmapStep(
    val label: String,
    val icon: ImageVector,
    val isActive: Boolean = false
)

private val roadmapSteps = listOf(
    RoadmapStep("Understand", Icons.Filled.Lightbulb, isActive = true),
    RoadmapStep("Discover", Icons.Filled.Explore),
    RoadmapStep("Validate", Icons.Filled.FactCheck),
    RoadmapStep("Finance", Icons.Filled.AccountBalance),
    RoadmapStep("Prepare", Icons.Filled.Inventory2),
    RoadmapStep("Grow", Icons.AutoMirrored.Filled.TrendingUp)
)

/* -------------------------------------------------------------------- */
/*  MAIN SCREEN                                                          */
/* -------------------------------------------------------------------- */
@Composable
fun LandingScreen(
    onStartJourneyClick: () -> Unit = {},
    onResumeJourneyClick: () -> Unit = {},
    onRoadmapStepClick: (stepIndex: Int) -> Unit = {},
    onProfileClick: () -> Unit = {}
) {
    Scaffold(
        containerColor = KalpaScreenColors.ScreenBackgroundCream
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
        ) {
            LandingTopBar(onProfileClick = onProfileClick)

            // Thin brand accent bar under the header
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(3.dp)
                    .background(KalpaScreenColors.Orange)
            )

            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp)
            ) {
                Spacer(Modifier.height(22.dp))

                Text(
                    text = "Start your business with confidence.",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 26.sp,
                    fontWeight = FontWeight.Bold,
                    lineHeight = 32.sp
                )

                Spacer(Modifier.height(10.dp))

                Text(
                    text = buildAnnotatedString {
                        withStyle(
                            SpanStyle(
                                color = KalpaScreenColors.OrangeDark,
                                fontWeight = FontWeight.Bold
                            )
                        ) {
                            append("KALPA")
                        }
                        append(" checks local demand, profits, and startup costs before you spend money.")
                    },
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 14.sp,
                    lineHeight = 20.sp
                )

                Spacer(Modifier.height(18.dp))

                HeroIllustration()

                Spacer(Modifier.height(20.dp))

                Button(
                    onClick = onStartJourneyClick,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(54.dp),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = KalpaScreenColors.Orange)
                ) {
                    Text(
                        text = "Start Business Journey",
                        color = Color.White,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                    Spacer(Modifier.width(8.dp))
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                        contentDescription = null,
                        tint = Color.White,
                        modifier = Modifier.size(18.dp)
                    )
                }

                Spacer(Modifier.height(10.dp))

                OutlinedButton(
                    onClick = onResumeJourneyClick,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(50.dp),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.outlinedButtonColors(
                        containerColor = KalpaScreenColors.PillGray,
                        contentColor = KalpaScreenColors.OrangeDark
                    ),
                    border = null
                ) {
                    Icon(
                        imageVector = Icons.Filled.History,
                        contentDescription = null,
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(Modifier.width(8.dp))
                    Text(
                        text = "Resume Journey",
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Medium
                    )
                }

                Spacer(Modifier.height(20.dp))

                JourneyRoadmapCard(
                    steps = roadmapSteps,
                    onStepClick = onRoadmapStepClick
                )

                Spacer(Modifier.height(24.dp))
            }
        }
    }
}

/* -------------------------------------------------------------------- */
/*  TOP BAR                                                              */
/* -------------------------------------------------------------------- */
@Composable
private fun LandingTopBar(onProfileClick: () -> Unit = {}) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 20.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Image(
                painter = painterResource(id = R.drawable.ic_launcher_foreground),
                contentDescription = "KALPA Logo",
                modifier = Modifier.size(24.dp)
            )
            Spacer(Modifier.width(6.dp))
            Text(
                text = "KALPA",
                color = KalpaScreenColors.Orange,
                fontWeight = FontWeight.ExtraBold,
                fontSize = 18.sp,
                letterSpacing = 1.sp
            )
        }
        
        Row(verticalAlignment = Alignment.CenterVertically) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.clickable { }
            ) {
                Text(
                    text = "EN",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.SemiBold
                )
                Icon(
                    imageVector = Icons.Filled.ArrowDropDown,
                    contentDescription = "Language",
                    tint = KalpaScreenColors.TextPrimary,
                    modifier = Modifier.size(20.dp)
                )
            }
            Spacer(Modifier.width(16.dp))
            Box(
                modifier = Modifier
                    .size(36.dp)
                    .clip(CircleShape)
                    .background(KalpaScreenColors.PillGray)
                    .clickable { onProfileClick() },
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Filled.Person,
                    contentDescription = "Profile",
                    tint = KalpaScreenColors.TextSecondary,
                    modifier = Modifier.size(20.dp)
                )
            }
        }
    }
}

/* -------------------------------------------------------------------- */
/*  HERO ILLUSTRATION                                                    */
/* -------------------------------------------------------------------- */
@Composable
private fun HeroIllustration() {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(180.dp)
            .clip(RoundedCornerShape(18.dp))
    ) {
        Image(
            painter = painterResource(id = R.drawable.market_illustration),
            contentDescription = "Market Illustration",
            contentScale = ContentScale.Crop,
            modifier = Modifier.fillMaxSize()
        )
    }
}

/* -------------------------------------------------------------------- */
/*  JOURNEY ROADMAP CARD                                                 */
/* -------------------------------------------------------------------- */
@Composable
private fun JourneyRoadmapCard(
    steps: List<RoadmapStep>,
    onStepClick: (Int) -> Unit
) {
    Surface(
        shape = RoundedCornerShape(18.dp),
        color = KalpaScreenColors.CardWhite
    ) {
        Column(modifier = Modifier.padding(18.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = "JOURNEY ROADMAP",
                    color = KalpaScreenColors.OrangeDark,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 0.5.sp
                )
                Text(
                    text = "6 Guided Steps",
                    color = KalpaScreenColors.OrangeDark,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.SemiBold
                )
            }

            Spacer(Modifier.height(16.dp))

            // Circles connected by a line
            Row(verticalAlignment = Alignment.CenterVertically) {
                steps.forEachIndexed { index, step ->
                    Box(
                        modifier = Modifier
                            .size(34.dp)
                            .clip(CircleShape)
                            .background(
                                if (step.isActive) KalpaScreenColors.Orange
                                else KalpaScreenColors.PillGray
                            )
                            .clickable { onStepClick(index) },
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = step.icon,
                            contentDescription = step.label,
                            tint = if (step.isActive) Color.White else KalpaScreenColors.TextMuted,
                            modifier = Modifier.size(16.dp)
                        )
                    }

                    if (index != steps.lastIndex) {
                        HorizontalDivider(
                            modifier = Modifier
                                .weight(1f)
                                .height(1.dp),
                            color = KalpaScreenColors.Divider
                        )
                    }
                }
            }

            Spacer(Modifier.height(6.dp))

            // Labels under each circle
            Row(modifier = Modifier.fillMaxWidth()) {
                steps.forEach { step ->
                    Text(
                        text = step.label,
                        color = if (step.isActive) KalpaScreenColors.OrangeDark else KalpaScreenColors.TextMuted,
                        fontSize = 10.sp,
                        fontWeight = if (step.isActive) FontWeight.SemiBold else FontWeight.Normal,
                        modifier = Modifier.weight(1f),
                        textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                        maxLines = 1
                    )
                }
            }
        }
    }
}

/* -------------------------------------------------------------------- */
/*  PREVIEW                                                              */
/* -------------------------------------------------------------------- */
@Preview(showBackground = true, widthDp = 390, heightDp = 844)
@Composable
private fun LandingScreenPreview() {
    MaterialTheme {
        LandingScreen()
    }
}