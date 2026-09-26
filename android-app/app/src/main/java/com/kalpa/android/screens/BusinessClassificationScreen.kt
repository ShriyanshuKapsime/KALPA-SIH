package com.kalpa.android.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// Colors now live in KalpaScreenColors.kt (same package, no import needed).
// Do not redeclare a color object in this file — see that file's header comment.

/* -------------------------------------------------------------------- */
/*  DATA MODELS                                                          */
/* -------------------------------------------------------------------- */
data class VerifiedField(
    val label: String,
    val value: String,
    val suffix: String? = null,
    val leadingEmojiOrIcon: androidx.compose.ui.graphics.vector.ImageVector? = null
)



/* -------------------------------------------------------------------- */
/*  MAIN SCREEN                                                          */
/* -------------------------------------------------------------------- */
@Composable
fun BusinessUnderstandingClassificationScreen(
    onBackClick: () -> Unit = {},
    onContinueClick: () -> Unit = {},
    onChangeSomethingClick: () -> Unit = {},
    onFieldEditClick: (String) -> Unit = {},
    onSeeClassificationDetailsClick: () -> Unit = {}
) {

    val fields = remember {
        listOf(
            VerifiedField("BUSINESS", "Poultry farming"),
            VerifiedField("BUSINESS TYPE", "New business"),
            VerifiedField("LOCATION", "Near Durgapur"),
            VerifiedField("YOUR MONEY", "₹2,00,000", suffix = "(Self contribution)"),
            VerifiedField("ENTREPRENEUR INTENT", "Starting a business")
        )
    }

    Scaffold(
        containerColor = KalpaScreenColors.ScreenBackgroundCream,
        topBar = {
            KalpaTopBar(
                onBackClick = onBackClick,
                stepText = "Page 2 of 14"
            )
        },
        bottomBar = {
            BottomActionBar(
                onContinueClick = onContinueClick,
                onChangeSomethingClick = onChangeSomethingClick
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScrollWorkaround()
        ) {
            StepProgressBar(currentStep = 2, totalSteps = 14)

            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp)
            ) {
                Spacer(Modifier.height(18.dp))

                UnderstoodIdeaHeader()

                Spacer(Modifier.height(18.dp))



                VerifiedBusinessBasicsCard(
                    fields = fields,
                    onFieldEditClick = onFieldEditClick,
                    onSeeClassificationDetailsClick = onSeeClassificationDetailsClick
                )

                Spacer(Modifier.height(16.dp))

                InfoBanner(
                    text = "Your inputs are matched with West Bengal MSME and NABARD dairy/poultry subsidy rules to find eligible grants automatically."
                )

                Spacer(Modifier.height(28.dp))

                Text(
                    text = "Is this correct?",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(Modifier.height(6.dp))
                Text(
                    text = "Tap continue to map your local buyer market and bird feed vendors.",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 13.sp,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth()
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
/*  "I UNDERSTOOD YOUR IDEA" HEADER                                      */
/* -------------------------------------------------------------------- */
@Composable
private fun UnderstoodIdeaHeader() {
    Row(verticalAlignment = Alignment.Top) {
        Box(
            modifier = Modifier
                .size(44.dp)
                .clip(CircleShape)
                .background(KalpaScreenColors.IconCircleBg),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = Icons.Filled.Hearing,
                contentDescription = null,
                tint = KalpaScreenColors.OrangeDark,
                modifier = Modifier.size(20.dp)
            )
        }
        Spacer(Modifier.width(14.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = "I understood your idea",
                color = KalpaScreenColors.TextPrimary,
                fontSize = 19.sp,
                fontWeight = FontWeight.Bold
            )
            Spacer(Modifier.height(4.dp))
            Text(
                text = "Here's what I gathered from what you told me. You can adjust anything anytime.",
                color = KalpaScreenColors.TextSecondary,
                fontSize = 13.sp,
                lineHeight = 18.sp
            )
        }
    }
}



/* -------------------------------------------------------------------- */
/*  VERIFIED BUSINESS BASICS CARD                                        */
/* -------------------------------------------------------------------- */
@Composable
private fun VerifiedBusinessBasicsCard(
    fields: List<VerifiedField>,
    onFieldEditClick: (String) -> Unit,
    onSeeClassificationDetailsClick: () -> Unit
) {
    Surface(
        shape = RoundedCornerShape(18.dp),
        color = KalpaScreenColors.CardWhite,
        shadowElevation = 0.dp
    ) {
        Column {
            // Header
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 14.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    imageVector = Icons.Filled.FactCheck,
                    contentDescription = null,
                    tint = KalpaScreenColors.OrangeDark,
                    modifier = Modifier.size(18.dp)
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    text = "Verified Business Basics",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.weight(1f)
                )
                Surface(
                    shape = RoundedCornerShape(20.dp),
                    color = KalpaScreenColors.OrangeBadgeBg
                ) {
                    Text(
                        text = "5 of 5 confirmed",
                        color = KalpaScreenColors.OrangeDark,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp)
                    )
                }
            }

            fields.forEachIndexed { index, field ->
                VerifiedFieldRow(
                    field = field,
                    onEditClick = { onFieldEditClick(field.label) }
                )
                if (index != fields.lastIndex) {
                    HorizontalDivider(color = KalpaScreenColors.Divider, thickness = 1.dp)
                }
            }

            HorizontalDivider(color = KalpaScreenColors.Divider, thickness = 1.dp)

            // "See official classification details" row
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { onSeeClassificationDetailsClick() }
                    .padding(horizontal = 16.dp, vertical = 14.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(34.dp)
                        .clip(CircleShape)
                        .background(KalpaScreenColors.OrangeBadgeBg),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Filled.Shield,
                        contentDescription = null,
                        tint = KalpaScreenColors.OrangeDark,
                        modifier = Modifier.size(16.dp)
                    )
                }
                Spacer(Modifier.width(12.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = "See official classification details",
                        color = KalpaScreenColors.TextPrimary,
                        fontSize = 13.5.sp,
                        fontWeight = FontWeight.Medium
                    )
                    Text(
                        text = "NIC Code 01461 & Govt Scheme mapping",
                        color = KalpaScreenColors.TextSecondary,
                        fontSize = 12.sp
                    )
                }
                Icon(
                    imageVector = Icons.Filled.ChevronRight,
                    contentDescription = null,
                    tint = KalpaScreenColors.TextMuted
                )
            }
        }
    }
}

@Composable
private fun VerifiedFieldRow(field: VerifiedField, onEditClick: () -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = field.label,
                color = KalpaScreenColors.TextMuted,
                fontSize = 11.sp,
                fontWeight = FontWeight.SemiBold,
                letterSpacing = 0.4.sp
            )
            Spacer(Modifier.height(4.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                if (field.label == "LOCATION") {
                    Icon(
                        imageVector = Icons.Filled.LocationOn,
                        contentDescription = null,
                        tint = KalpaScreenColors.TextPrimary,
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(Modifier.width(4.dp))
                }
                Text(
                    text = field.value,
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.weight(1f, fill = false)
                )
                if (field.suffix != null) {
                    Spacer(Modifier.width(6.dp))
                    Text(
                        text = field.suffix,
                        color = KalpaScreenColors.TextSecondary,
                        fontSize = 13.sp
                    )
                }
            }
        }

        IconButton(
            onClick = onEditClick,
            modifier = Modifier
                .size(38.dp)
                .clip(CircleShape)
                .background(KalpaScreenColors.PillGray)
        ) {
            Icon(
                imageVector = Icons.Filled.Edit,
                contentDescription = "Edit ${field.label}",
                tint = KalpaScreenColors.TextPrimary,
                modifier = Modifier.size(16.dp)
            )
        }
    }
}

/* -------------------------------------------------------------------- */
/*  INFO BANNER                                                          */
/* -------------------------------------------------------------------- */
@Composable
private fun InfoBanner(text: String) {
    Surface(
        shape = RoundedCornerShape(14.dp),
        color = KalpaScreenColors.InfoBannerBg
    ) {
        Row(
            modifier = Modifier.padding(14.dp),
            verticalAlignment = Alignment.Top
        ) {
            Icon(
                imageVector = Icons.Filled.Info,
                contentDescription = null,
                tint = KalpaScreenColors.TextSecondary,
                modifier = Modifier.size(18.dp)
            )
            Spacer(Modifier.width(10.dp))
            Text(
                text = text,
                color = KalpaScreenColors.TextSecondary,
                fontSize = 13.sp,
                lineHeight = 18.sp,
                modifier = Modifier.weight(1f)
            )
        }
    }
}

/* -------------------------------------------------------------------- */
/*  BOTTOM ACTION BAR                                                    */
/* -------------------------------------------------------------------- */
@Composable
private fun BottomActionBar(
    onContinueClick: () -> Unit,
    onChangeSomethingClick: () -> Unit
) {
    Surface(color = KalpaScreenColors.ScreenBackgroundCream) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp, vertical = 14.dp)
        ) {
            Button(
                onClick = onContinueClick,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.buttonColors(containerColor = KalpaScreenColors.Orange)
            ) {
                Text(
                    text = "Yes, continue",
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
                onClick = onChangeSomethingClick,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(50.dp),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.outlinedButtonColors(
                    containerColor = KalpaScreenColors.PillGray,
                    contentColor = KalpaScreenColors.TextPrimary
                ),
                border = null
            ) {
                Icon(
                    imageVector = Icons.Filled.Tune,
                    contentDescription = null,
                    modifier = Modifier.size(16.dp)
                )
                Spacer(Modifier.width(8.dp))
                Text(text = "Change something", fontSize = 15.sp, fontWeight = FontWeight.Medium)
            }

            Spacer(Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Next: Local Market Demand & Customer Check",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 12.sp
                )
                Spacer(Modifier.width(6.dp))
                Icon(
                    imageVector = Icons.Filled.Storefront,
                    contentDescription = null,
                    tint = KalpaScreenColors.TextSecondary,
                    modifier = Modifier.size(14.dp)
                )
            }
        }
    }
}

/* -------------------------------------------------------------------- */
/*  Small helper: keeps the body scrollable without adding a dependency  */
/*  on a separate ScrollState variable at the call site.                 */
/* -------------------------------------------------------------------- */
@Composable
private fun Modifier.verticalScrollWorkaround(): Modifier {
    val scrollState = rememberScrollState()
    return this.then(Modifier.verticalScroll(scrollState))
}

/* -------------------------------------------------------------------- */
/*  PREVIEW                                                              */
/* -------------------------------------------------------------------- */
@Preview(showBackground = true, widthDp = 390, heightDp = 844)
@Composable
private fun BusinessUnderstandingClassificationScreenPreview() {
    MaterialTheme {
        BusinessUnderstandingClassificationScreen()
    }
}