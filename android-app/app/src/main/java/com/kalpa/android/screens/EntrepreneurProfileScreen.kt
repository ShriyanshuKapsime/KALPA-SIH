package com.kalpa.android.screens

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
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
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.outlined.AddCircle
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// Colors live in KalpaScreenColors.kt (same package, no import needed).
// Do not redeclare a color object in this file.

private data class ExperienceOption(
    val title: String,
    val subtitle: String? = null
)

private val experienceOptions = listOf(
    ExperienceOption("No, I'm new to this"),
    ExperienceOption("1 to 2 years", "Helped in family or local shop"),
    ExperienceOption("3 to 5 years"),
    ExperienceOption("More than 5 years"),
    ExperienceOption("Different work entirely")
)

private val skillOptions = listOf(
    "Making products",
    "Buying materials",
    "Selling",
    "Money & accounts",
    "Managing workers",
    "Talking to customers",
    "Not sure yet"
)

private data class QuickCheck(
    val title: String,
    val options: List<String>
)

private val quickChecks = listOf(
    QuickCheck("Training", listOf("Planning to learn", "Already trained", "No training needed")),
    QuickCheck("What you already have", listOf("Land / workspace, Supplier connections", "Just land", "Nothing yet")),
    QuickCheck("How much time can you spend?", listOf("Full-time", "Part-time", "Weekends only"))
)

/* -------------------------------------------------------------------- */
/*  MAIN SCREEN                                                          */
/* -------------------------------------------------------------------- */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun EntrepreneurProfileScreen(
    onBackClick: () -> Unit = {},
    onExperienceWhyLinkClick: () -> Unit = {},
    onContinueClick: (
        selectedExperienceIndex: Int,
        selectedSkills: Set<String>
    ) -> Unit = { _, _ -> }
) {
    var selectedExperienceIndex by remember { mutableStateOf(1) }
    var selectedSkills by remember {
        mutableStateOf(setOf("Making products", "Buying materials", "Selling"))
    }
    val expandedChecks = remember { mutableStateListOf(false, false, false) }
    val selectedCheckOptions = remember { mutableStateListOf(0, 0, 0) }

    Scaffold(
        containerColor = KalpaScreenColors.ScreenBackgroundCream,
        bottomBar = {
            Surface(color = KalpaScreenColors.ScreenBackgroundCream) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Button(
                        onClick = { onContinueClick(selectedExperienceIndex, selectedSkills) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(54.dp),
                        shape = RoundedCornerShape(14.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = KalpaScreenColors.Orange)
                    ) {
                        Text(
                            text = "Continue",
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
            KalpaTopBar(onBackClick = onBackClick, stepText = "Page 3 of 14")
            StepProgressBar(currentStep = 3, totalSteps = 14)

            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp)
            ) {
                Spacer(Modifier.height(20.dp))

                Text(
                    text = "Tell us about your work",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 22.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(6.dp))
                Text(
                    text = "This helps us check your loan eligibility and grant options.",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 13.sp,
                    lineHeight = 18.sp
                )

                Spacer(Modifier.height(22.dp))

                Text(
                    text = "Have you done this work before?",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Bold
                )

                Spacer(Modifier.height(10.dp))

                experienceOptions.forEachIndexed { index, option ->
                    ExperienceCard(
                        option = option,
                        selected = selectedExperienceIndex == index,
                        onClick = { selectedExperienceIndex = index }
                    )
                    if (index != experienceOptions.lastIndex) {
                        Spacer(Modifier.height(10.dp))
                    }
                }

                Spacer(Modifier.height(12.dp))

                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.clickable { onExperienceWhyLinkClick() }
                ) {
                    Icon(
                        imageVector = Icons.Filled.Lightbulb,
                        contentDescription = null,
                        tint = KalpaScreenColors.OrangeDark,
                        modifier = Modifier.size(14.dp)
                    )
                    Spacer(Modifier.width(4.dp))
                    Text(
                        text = "Why experience helps you get a loan",
                        color = KalpaScreenColors.OrangeDark,
                        fontSize = 12.5.sp,
                        fontWeight = FontWeight.Medium,
                        textDecoration = TextDecoration.Underline
                    )
                }

                Spacer(Modifier.height(24.dp))

                Text(
                    text = "What work can you do?",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Bold
                )

                Spacer(Modifier.height(10.dp))

                FlowRow(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    skillOptions.forEach { skill ->
                        val isSelected = selectedSkills.contains(skill)
                        SkillChip(
                            label = skill,
                            selected = isSelected,
                            onClick = {
                                selectedSkills = if (isSelected) {
                                    selectedSkills - skill
                                } else {
                                    selectedSkills + skill
                                }
                            }
                        )
                    }
                }

                Spacer(Modifier.height(24.dp))

                Text(
                    text = "A few quick checks",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Bold
                )

                Spacer(Modifier.height(10.dp))

                quickChecks.forEachIndexed { index, check ->
                    QuickCheckRow(
                        check = check,
                        expanded = expandedChecks[index],
                        selectedOptionIndex = selectedCheckOptions[index],
                        onToggle = { expandedChecks[index] = !expandedChecks[index] },
                        onOptionSelected = { optionIndex ->
                            selectedCheckOptions[index] = optionIndex
                            expandedChecks[index] = false
                        },
                        onDismissRequest = { expandedChecks[index] = false }
                    )
                    if (index != quickChecks.lastIndex) {
                        Spacer(Modifier.height(10.dp))
                    }
                }

                Spacer(Modifier.height(40.dp))
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
/*  EXPERIENCE CARD (single-select radio row)                            */
/* -------------------------------------------------------------------- */
@Composable
private fun ExperienceCard(
    option: ExperienceOption,
    selected: Boolean,
    onClick: () -> Unit
) {
    Surface(
        shape = RoundedCornerShape(14.dp),
        color = if (selected) KalpaScreenColors.OrangeBadgeBg else KalpaScreenColors.CardWhite,
        border = androidx.compose.foundation.BorderStroke(
            1.dp,
            if (selected) KalpaScreenColors.Orange else KalpaScreenColors.Divider
        ),
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() }
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = option.title,
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 14.5.sp,
                    fontWeight = FontWeight.SemiBold
                )
                if (option.subtitle != null) {
                    Spacer(Modifier.height(2.dp))
                    Text(
                        text = option.subtitle,
                        color = KalpaScreenColors.OrangeDark,
                        fontSize = 12.sp
                    )
                }
            }

            Box(
                modifier = Modifier
                    .size(22.dp)
                    .clip(CircleShape)
                    .background(if (selected) KalpaScreenColors.Orange else KalpaScreenColors.PillGray),
                contentAlignment = Alignment.Center
            ) {
                if (selected) {
                    Icon(
                        imageVector = Icons.Filled.Check,
                        contentDescription = null,
                        tint = Color.White,
                        modifier = Modifier.size(14.dp)
                    )
                }
            }
        }
    }
}

/* -------------------------------------------------------------------- */
/*  SKILL CHIP (multi-select pill)                                       */
/* -------------------------------------------------------------------- */
@Composable
private fun SkillChip(
    label: String,
    selected: Boolean,
    onClick: () -> Unit
) {
    Surface(
        shape = RoundedCornerShape(24.dp),
        color = if (selected) KalpaScreenColors.OrangeBadgeBg else KalpaScreenColors.CardWhite,
        border = androidx.compose.foundation.BorderStroke(
            1.dp,
            if (selected) KalpaScreenColors.Orange else KalpaScreenColors.Divider
        ),
        modifier = Modifier.clickable { onClick() }
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 9.dp)
        ) {
            Icon(
                imageVector = if (selected) Icons.Outlined.CheckCircle else Icons.Outlined.AddCircle,
                contentDescription = null,
                tint = if (selected) KalpaScreenColors.OrangeDark else KalpaScreenColors.TextMuted,
                modifier = Modifier.size(16.dp)
            )
            Spacer(Modifier.width(6.dp))
            Text(
                text = label,
                color = if (selected) KalpaScreenColors.OrangeDark else KalpaScreenColors.TextPrimary,
                fontSize = 13.sp,
                fontWeight = FontWeight.Medium
            )
        }
    }
}

/* -------------------------------------------------------------------- */
/*  QUICK CHECK ROW (expandable)                                         */
/* -------------------------------------------------------------------- */
@Composable
private fun QuickCheckRow(
    check: QuickCheck,
    expanded: Boolean,
    selectedOptionIndex: Int,
    onToggle: () -> Unit,
    onOptionSelected: (Int) -> Unit,
    onDismissRequest: () -> Unit
) {
    val rotation by animateFloatAsState(targetValue = if (expanded) 180f else 0f, label = "chevronRotation")

    Box(modifier = Modifier.fillMaxWidth()) {
        Surface(
            shape = RoundedCornerShape(14.dp),
            color = KalpaScreenColors.CardWhite,
            border = androidx.compose.foundation.BorderStroke(1.dp, KalpaScreenColors.Divider),
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
                    Text(
                        text = check.title,
                        color = KalpaScreenColors.TextPrimary,
                        fontSize = 14.5.sp,
                        fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.weight(1f).padding(end = 8.dp)
                    )
                    Icon(
                        imageVector = Icons.Filled.ExpandMore,
                        contentDescription = if (expanded) "Collapse" else "Expand",
                        tint = KalpaScreenColors.TextMuted,
                        modifier = Modifier
                            .size(20.dp)
                            .rotate(rotation)
                    )
                }
                Spacer(Modifier.height(2.dp))
                Text(
                    text = check.options.getOrElse(selectedOptionIndex) { "" },
                    color = KalpaScreenColors.OrangeDark,
                    fontSize = 12.sp
                )
            }
        }
        
        DropdownMenu(
            expanded = expanded,
            onDismissRequest = onDismissRequest,
            modifier = Modifier.background(KalpaScreenColors.CardWhite)
        ) {
            check.options.forEachIndexed { index, optionText ->
                DropdownMenuItem(
                    text = { 
                        Text(
                            text = optionText,
                            color = KalpaScreenColors.TextPrimary,
                            fontSize = 14.sp
                        ) 
                    },
                    onClick = { onOptionSelected(index) }
                )
            }
        }
    }
}

/* -------------------------------------------------------------------- */
/*  PREVIEW                                                              */
/* -------------------------------------------------------------------- */
@Preview(showBackground = true, widthDp = 390, heightDp = 1000)
@Composable
private fun EntrepreneurProfileScreenPreview() {
    MaterialTheme {
        EntrepreneurProfileScreen()
    }
}