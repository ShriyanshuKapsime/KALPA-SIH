package com.kalpa.android.screens

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Storefront
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// Colors live in KalpaScreenColors.kt (same package, no import needed).
// Do not redeclare a color object in this file.

private enum class StepStatus { DONE, ACTIVE, UPCOMING }

private data class ChecklistStep(
    val title: String,
    val subtitle: String,
    val status: StepStatus
)

private val checklistSteps = listOf(
    ChecklistStep("Understanding your setup", "Shed capacity, bird count & daily care", StepStatus.DONE),
    ChecklistStep("Looking at your local market", "Nearby mandi rates & daily chicken prices", StepStatus.DONE),
    ChecklistStep("Checking local demand", "Hotels, shops & buyers in your area", StepStatus.DONE),
    ChecklistStep("Calculating startup money", "Feed costs, chick prices & month-to-month cash", StepStatus.ACTIVE),
    ChecklistStep("Reviewing your experience", "Farming background & daily helpers", StepStatus.UPCOMING),
    ChecklistStep("Checking risks", "Weather changes & feed price safety", StepStatus.UPCOMING),
    ChecklistStep("Preparing your plan", "Final loan proposal and profit report", StepStatus.UPCOMING)
)

/* -------------------------------------------------------------------- */
/*  MAIN SCREEN                                                          */
/* -------------------------------------------------------------------- */
@Composable
fun KalpaIsAnalysingScreen(
    businessLabel: String = "Poultry Farming (Broiler Unit)",
    onBackClick: () -> Unit = {},
    onSeeProgressClick: () -> Unit = {}
) {
    var checksExpanded by remember { mutableStateOf(false) }
    val completedCount = checklistSteps.count { it.status == StepStatus.DONE }

    Scaffold(
        containerColor = KalpaScreenColors.ScreenBackgroundCream,
        bottomBar = {
            Surface(color = KalpaScreenColors.ScreenBackgroundCream) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Button(
                        onClick = onSeeProgressClick,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(54.dp),
                        shape = RoundedCornerShape(14.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = KalpaScreenColors.Orange)
                    ) {
                        Text(
                            text = "See Progress So Far",
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
                }
            }
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
        ) {
            KalpaTopBar(onBackClick = onBackClick, stepText = "Page 4 of 14")
            StepProgressBar(currentStep = 4, totalSteps = 14)

            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp)
            ) {
                Spacer(Modifier.height(18.dp))

                BusinessInReviewCard(businessLabel = businessLabel)

                Spacer(Modifier.height(20.dp))

                Text(
                    text = "Checking your business details",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold,
                    lineHeight = 30.sp
                )
                Spacer(Modifier.height(6.dp))
                Text(
                    text = "We are reviewing everything to build your simple business plan.",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 14.sp,
                    lineHeight = 20.sp
                )

                Spacer(Modifier.height(18.dp))

                ProgressChecklistCard(
                    steps = checklistSteps,
                    completedCount = completedCount
                )

                Spacer(Modifier.height(14.dp))

                WhatAreTheseChecksRow(
                    expanded = checksExpanded,
                    onToggle = { checksExpanded = !checksExpanded }
                )

                Spacer(Modifier.height(20.dp))
            }
        }
    }
}



/* -------------------------------------------------------------------- */
/*  PROGRESS BAR                                                         */
/* -------------------------------------------------------------------- */
@Composable
private fun StepProgressBar(currentStep: Int, totalSteps: Int) {
    val progress = currentStep.toFloat() / totalSteps.toFloat()
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(4.dp)
            .background(KalpaScreenColors.Divider)
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth(progress)
                .fillMaxHeight()
                .background(KalpaScreenColors.Orange)
        )
    }
}

/* -------------------------------------------------------------------- */
/*  "BUSINESS IN REVIEW" CARD                                            */
/* -------------------------------------------------------------------- */
@Composable
private fun BusinessInReviewCard(businessLabel: String) {
    Surface(
        shape = RoundedCornerShape(14.dp),
        color = KalpaScreenColors.ReviewCardBg,
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(38.dp)
                    .clip(RoundedCornerShape(10.dp))
                    .background(KalpaScreenColors.CardWhite),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Filled.Storefront,
                    contentDescription = null,
                    tint = KalpaScreenColors.OrangeDark,
                    modifier = Modifier.size(18.dp)
                )
            }
            Spacer(Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "BUSINESS IN REVIEW",
                    color = KalpaScreenColors.OrangeDark,
                    fontSize = 10.5.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 0.5.sp
                )
                Spacer(Modifier.height(2.dp))
                Text(
                    text = businessLabel,
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.SemiBold
                )
            }
        }
    }
}

/* -------------------------------------------------------------------- */
/*  PROGRESS CHECKLIST CARD (vertical timeline)                          */
/* -------------------------------------------------------------------- */
@Composable
private fun ProgressChecklistCard(
    steps: List<ChecklistStep>,
    completedCount: Int
) {
    Surface(
        shape = RoundedCornerShape(18.dp),
        color = KalpaScreenColors.CardWhite
    ) {
        Column(modifier = Modifier.padding(vertical = 16.dp)) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 18.dp),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = "PROGRESS CHECKLIST",
                    color = KalpaScreenColors.TextMuted,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 0.5.sp
                )
                Text(
                    text = "$completedCount of ${steps.size} completed",
                    color = KalpaScreenColors.OrangeDark,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold
                )
            }

            Spacer(Modifier.height(12.dp))

            steps.forEachIndexed { index, step ->
                ChecklistStepRow(
                    step = step,
                    isLast = index == steps.lastIndex
                )
            }
        }
    }
}

@Composable
private fun ChecklistStepRow(step: ChecklistStep, isLast: Boolean) {
    val rowBackground = if (step.status == StepStatus.ACTIVE) {
        KalpaScreenColors.OrangeBadgeBg
    } else {
        Color.Transparent
    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(rowBackground)
            .padding(horizontal = 18.dp, vertical = 10.dp)
    ) {
        // Circle + connecting line
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            StepCircle(status = step.status)
            if (!isLast) {
                Box(
                    modifier = Modifier
                        .width(2.dp)
                        .height(34.dp)
                        .background(KalpaScreenColors.Divider)
                )
            }
        }

        Spacer(Modifier.width(14.dp))

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 2.dp),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = step.title,
                    color = if (step.status == StepStatus.ACTIVE) {
                        KalpaScreenColors.OrangeDark
                    } else {
                        KalpaScreenColors.TextPrimary
                    },
                    fontSize = 14.5.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(2.dp))
                Text(
                    text = step.subtitle,
                    color = if (step.status == StepStatus.UPCOMING) {
                        KalpaScreenColors.TextMuted
                    } else {
                        KalpaScreenColors.TextSecondary
                    },
                    fontSize = 12.sp,
                    lineHeight = 16.sp
                )
            }

            if (step.status != StepStatus.ACTIVE) {
                Text(
                    text = if (step.status == StepStatus.DONE) "Done" else "Next",
                    color = KalpaScreenColors.TextMuted,
                    fontSize = 12.sp,
                    modifier = Modifier.padding(start = 8.dp)
                )
            }
        }
    }
}

@Composable
private fun StepCircle(status: StepStatus) {
    when (status) {
        StepStatus.DONE -> {
            Box(
                modifier = Modifier
                    .size(28.dp)
                    .clip(CircleShape)
                    .background(KalpaScreenColors.StepDoneBg),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Filled.Check,
                    contentDescription = "Done",
                    tint = KalpaScreenColors.StepDoneIcon,
                    modifier = Modifier.size(14.dp)
                )
            }
        }
        StepStatus.ACTIVE -> {
            Box(
                modifier = Modifier
                    .size(28.dp)
                    .clip(CircleShape)
                    .background(KalpaScreenColors.Orange),
                contentAlignment = Alignment.Center
            ) {
                Box(
                    modifier = Modifier
                        .size(16.dp)
                        .clip(CircleShape)
                        .background(Color.White)
                )
            }
        }
        StepStatus.UPCOMING -> {
            Box(
                modifier = Modifier
                    .size(28.dp)
                    .clip(CircleShape)
                    .background(KalpaScreenColors.StepUpcomingBg)
            )
        }
    }
}

/* -------------------------------------------------------------------- */
/*  "WHAT ARE THESE CHECKS?" EXPANDABLE ROW                              */
/* -------------------------------------------------------------------- */
@Composable
private fun WhatAreTheseChecksRow(
    expanded: Boolean,
    onToggle: () -> Unit
) {
    val rotation by animateFloatAsState(targetValue = if (expanded) 180f else 0f, label = "chevronRotation")

    Surface(
        shape = RoundedCornerShape(14.dp),
        color = KalpaScreenColors.ReviewCardBg,
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onToggle() }
    ) {
        Column(modifier = Modifier.padding(horizontal = 16.dp, vertical = 14.dp)) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                    Icon(
                        imageVector = Icons.Filled.Info,
                        contentDescription = null,
                        tint = KalpaScreenColors.OrangeDark,
                        modifier = Modifier.size(18.dp)
                    )
                    Spacer(Modifier.width(10.dp))
                    Text(
                        text = "What are these checks?",
                        color = KalpaScreenColors.TextPrimary,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
                Icon(
                    imageVector = Icons.Filled.ExpandMore,
                    contentDescription = if (expanded) "Collapse" else "Expand",
                    tint = KalpaScreenColors.TextMuted,
                    modifier = Modifier
                        .size(20.dp)
                        .rotate(rotation)
                )
            }

            if (expanded) {
                Spacer(Modifier.height(10.dp))
                Text(
                    text = "These checks look at your setup, local market, demand, " +
                            "startup costs, experience, and risks to build an accurate, " +
                            "simple business plan for you.",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 12.5.sp,
                    lineHeight = 18.sp
                )
            }
        }
    }
}

/* -------------------------------------------------------------------- */
/*  PREVIEW                                                              */
/* -------------------------------------------------------------------- */
@Preview(showBackground = true, widthDp = 390, heightDp = 1100)
@Composable
private fun KalpaIsAnalysingScreenPreview() {
    MaterialTheme {
        KalpaIsAnalysingScreen()
    }
}