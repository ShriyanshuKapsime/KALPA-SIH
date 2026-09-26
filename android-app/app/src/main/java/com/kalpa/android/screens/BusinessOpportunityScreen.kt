package com.kalpa.android.screens

import androidx.compose.foundation.BorderStroke
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
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material.icons.filled.Translate
import androidx.compose.material.icons.outlined.AccountCircle
import androidx.compose.material.icons.outlined.FactCheck
import androidx.compose.material.icons.outlined.Payments
import androidx.compose.material.icons.outlined.Store
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch

// Colors live in KalpaScreenColors.kt (same package, no import needed).
// Do not redeclare a color object in this file.

/* -------------------------------------------------------------------- */
/*  PROTOTYPE DATA (values taken from the design, not live data)        */
/* -------------------------------------------------------------------- */
private val availableLanguages = listOf("English", "हिन्दी", "தமிழ்", "తెలుగు", "मराठी")

private const val OPPORTUNITY_SCORE = 78
private const val SEGMENT_COUNT = 5

private data class QuickVerdict(val label: String, val value: String, val highlight: Boolean)

private val quickVerdicts = listOf(
    QuickVerdict("Buyer Demand", "Very High", highlight = true),
    QuickVerdict("Competition", "Low", highlight = false),
    QuickVerdict("Supplies", "Easy", highlight = true)
)

/** One inspectable item (off-take cards and key market checks share this). */
private data class OpportunityDetail(
    val label: String,
    val score: String,
    val status: String,
    val summary: String,   // text shown on the card
    val fullText: String   // text shown in the detail sheet
)

private val offTakeItems = listOf(
    OpportunityDetail(
        label = "LOCAL RETAIL MEAT DEMAND",
        score = "84 / 100",
        status = "Strong Pull",
        summary = "Benachity mandi and adjacent weekly markets account for over 1.8 " +
                "tonnes of live broiler turnover every week.",
        fullText = "Benachity mandi and adjacent weekly markets account for over 1.8 " +
                "tonnes of live broiler turnover every week."
    ),
    OpportunityDetail(
        label = "CATCHMENT & BUYER CONNECTIVITY",
        score = "85 / 100",
        status = "High Penetration",
        summary = "42 registered restaurants, highway dhabas, and industrial staff " +
                "canteens are situated within a 15 km radius of your farm.",
        fullText = "42 registered restaurants, highway dhabas, and industrial staff " +
                "canteens are situated within a 15 km radius of your farm."
    )
)

private val keyChecks = listOf(
    OpportunityDetail(
        "COMPETITION", "68 / 100", "Manageable",
        "Catchment requires 9,200 birds vs 4,500 active capacity.",
        "Catchment requires 9,200 birds vs 4,500 active capacity."
    ),
    OpportunityDetail(
        "LOGISTICS & TRANSPORT", "82 / 100", "All-Weather Access",
        "Paved rural road connects to NH-19 within 2.8 km.",
        "Paved rural road connects to NH-19 within 2.8 km."
    ),
    OpportunityDetail(
        "FEED & DOC SUPPLY", "76 / 100", "Readily Available",
        "Authorized hatcheries supply direct vans twice weekly.",
        "Authorized hatcheries supply direct vans twice weekly."
    ),
    OpportunityDetail(
        "CAPITAL & SCALE", "72 / 100", "Well Balanced",
        "₹2,00,000 self-equity layout comfortably finances 1,000 broilers.",
        "₹2,00,000 self-equity layout comfortably finances 1,000 broilers."
    )
)

/* -------------------------------------------------------------------- */
/*  MAIN SCREEN                                                          */
/* -------------------------------------------------------------------- */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BusinessOpportunityScreen(
    onBackClick: () -> Unit = {},
    onContinueClick: () -> Unit = {},
    onProfileClick: () -> Unit = {},
    onLanguageSelected: (String) -> Unit = {},
    onDetailClick: (label: String) -> Unit = {}
) {
    var selectedLanguage by remember { mutableStateOf(availableLanguages.first()) }
    var selectedDetail by remember { mutableStateOf<OpportunityDetail?>(null) }

    val openDetail: (OpportunityDetail) -> Unit = {
        selectedDetail = it
        onDetailClick(it.label)
    }

    val blurRadius by androidx.compose.animation.core.animateDpAsState(targetValue = if (selectedDetail != null) 12.dp else 0.dp, label = "blur")
    Scaffold(
        modifier = if (blurRadius > 0.dp) Modifier.blur(blurRadius) else Modifier,
        containerColor = KalpaScreenColors.ScreenBackgroundCream,
        bottomBar = {
            Column {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(1.dp)
                        .background(KalpaScreenColors.Divider)
                )
                Surface(color = KalpaScreenColors.ScreenBackgroundCream) {
                    Box(modifier = Modifier.padding(horizontal = 20.dp, vertical = 14.dp)) {
                        Button(
                            onClick = onContinueClick,
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(56.dp),
                            shape = RoundedCornerShape(30.dp),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = KalpaScreenColors.Orange,
                                contentColor = Color.White
                            )
                        ) {
                            Text("Continue", fontSize = 17.sp, fontWeight = FontWeight.Bold)
                            Spacer(Modifier.width(8.dp))
                            Icon(
                                imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                                contentDescription = null,
                                modifier = Modifier.size(18.dp)
                            )
                        }
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
            var languageMenuExpanded by remember { mutableStateOf(false) }
            KalpaTopBar(
                onBackClick = onBackClick,
                stepText = "Page 6 of 14"
            )

            Column(modifier = Modifier.padding(horizontal = 20.dp)) {
                Spacer(Modifier.height(8.dp))
                Text(
                    text = "Business Opportunity",
                    fontSize = 28.sp,
                    fontWeight = FontWeight.Bold,
                    color = KalpaScreenColors.TextPrimary
                )
                Spacer(Modifier.height(14.dp))

                FeasibilityCard()

                Spacer(Modifier.height(22.dp))
                SectionHeader(Icons.Outlined.Payments, "Price Benchmarks", "Live benchmark")
                Spacer(Modifier.height(10.dp))
                PriceBenchmarkCard()

                Spacer(Modifier.height(22.dp))
                SectionHeader(Icons.Outlined.Store, "Buyer Off-take Capacity", "Catchment analysis")
                Spacer(Modifier.height(10.dp))
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    offTakeItems.forEach { item ->
                        OffTakeCard(item = item, onClick = { openDetail(item) })
                    }
                }

                Spacer(Modifier.height(22.dp))
                SectionHeader(Icons.Outlined.FactCheck, "Key Market Checks", "Tap any item to see details")
                Spacer(Modifier.height(10.dp))
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    keyChecks.chunked(2).forEach { rowItems ->
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(IntrinsicSize.Min),
                            horizontalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            rowItems.forEach { item ->
                                KeyCheckCard(
                                    item = item,
                                    onClick = { openDetail(item) },
                                    modifier = Modifier
                                        .weight(1f)
                                        .fillMaxHeight()
                                )
                            }
                        }
                    }
                }

                Spacer(Modifier.height(20.dp))
            }
        }
    }

    // ---- Detail bottom sheet ------------------------------------------
    selectedDetail?.let { detail ->
        val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
        val scope = rememberCoroutineScope()
        val closeSheet: () -> Unit = {
            scope.launch { sheetState.hide() }.invokeOnCompletion {
                if (!sheetState.isVisible) selectedDetail = null
            }
        }
        ModalBottomSheet(
            onDismissRequest = { selectedDetail = null },
            sheetState = sheetState,
            containerColor = KalpaScreenColors.CardWhite,
            shape = RoundedCornerShape(topStart = 24.dp, topEnd = 24.dp)
        ) {
            DetailSheet(detail = detail, onClose = closeSheet)
        }
    }
}



@Composable
private fun CircleIconButton(
    icon: ImageVector,
    contentDescription: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        shape = CircleShape,
        color = KalpaScreenColors.CardWhite,
        shadowElevation = 2.dp,
        modifier = modifier.size(44.dp)
    ) {
        IconButton(onClick = onClick, modifier = Modifier.fillMaxSize()) {
            Icon(
                imageVector = icon,
                contentDescription = contentDescription,
                tint = KalpaScreenColors.TextPrimary,
                modifier = Modifier.size(22.dp)
            )
        }
    }
}

/* -------------------------------------------------------------------- */
/*  OVERALL FEASIBILITY CARD                                             */
/* -------------------------------------------------------------------- */
@Composable
private fun FeasibilityCard() {
    // 78/100 -> 4 of 5 segments filled (each segment covers 20 points).
    val filledSegments = ((OPPORTUNITY_SCORE + 19) / 20).coerceIn(0, SEGMENT_COUNT)

    Surface(
        shape = RoundedCornerShape(20.dp),
        color = KalpaScreenColors.CardWhite,
        border = BorderStroke(1.dp, KalpaScreenColors.Divider),
        shadowElevation = 2.dp,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = "OVERALL FEASIBILITY",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Medium,
                        letterSpacing = 0.8.sp,
                        color = KalpaScreenColors.TextSecondary
                    )
                    Spacer(Modifier.height(2.dp))
                    Text(
                        text = "High Opportunity",
                        fontSize = 26.sp,
                        fontWeight = FontWeight.Bold,
                        color = KalpaScreenColors.OrangeDeep
                    )
                }
                Spacer(Modifier.width(8.dp))
                Surface(
                    shape = RoundedCornerShape(26.dp),
                    color = KalpaScreenColors.FieldGray
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 18.dp, vertical = 8.dp),
                        verticalAlignment = Alignment.Bottom
                    ) {
                        Text(
                            text = "$OPPORTUNITY_SCORE",
                            fontSize = 32.sp,
                            fontWeight = FontWeight.Bold,
                            color = KalpaScreenColors.TextPrimary
                        )
                        Spacer(Modifier.width(2.dp))
                        Text(
                            text = "/100",
                            fontSize = 13.sp,
                            color = KalpaScreenColors.TextSecondary,
                            modifier = Modifier.padding(bottom = 5.dp)
                        )
                    }
                }
            }

            Spacer(Modifier.height(16.dp))

            // Segmented scale (not a plain percentage bar)
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                repeat(SEGMENT_COUNT) { index ->
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .height(8.dp)
                            .clip(CircleShape)
                            .background(
                                if (index < filledSegments) KalpaScreenColors.Orange
                                else KalpaScreenColors.Divider
                            )
                    )
                }
            }
            Spacer(Modifier.height(6.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text("Cautious", fontSize = 12.sp, color = KalpaScreenColors.TextSecondary, modifier = Modifier.weight(1f), textAlign = TextAlign.Start)
                Text(
                    "Strong Market Fit",
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = KalpaScreenColors.Orange,
                    modifier = Modifier.weight(1f),
                    textAlign = TextAlign.Center
                )
                Text("Saturated", fontSize = 12.sp, color = KalpaScreenColors.TextSecondary, modifier = Modifier.weight(1f), textAlign = TextAlign.End)
            }

            Spacer(Modifier.height(12.dp))
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(1.dp)
                    .background(KalpaScreenColors.Divider)
            )
            Spacer(Modifier.height(12.dp))

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                quickVerdicts.forEach { verdict ->
                    Surface(
                        shape = RoundedCornerShape(12.dp),
                        color = KalpaScreenColors.FieldGray,
                        modifier = Modifier.weight(1f)
                    ) {
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 10.dp, horizontal = 4.dp),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Text(
                                text = verdict.label,
                                fontSize = 11.sp,
                                color = KalpaScreenColors.TextSecondary,
                                textAlign = TextAlign.Center,
                                maxLines = 2,
                                lineHeight = 14.sp
                            )
                            Spacer(Modifier.height(2.dp))
                            Text(
                                text = verdict.value,
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold,
                                textAlign = TextAlign.Center,
                                color = if (verdict.highlight) KalpaScreenColors.OrangeDeep
                                else KalpaScreenColors.TextPrimary,
                                maxLines = 2,
                                lineHeight = 16.sp
                            )
                        }
                    }
                }
            }
        }
    }
}

/* -------------------------------------------------------------------- */
/*  SECTION HEADER                                                       */
/* -------------------------------------------------------------------- */
@Composable
private fun SectionHeader(icon: ImageVector, title: String, trailing: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = KalpaScreenColors.OrangeDeep,
            modifier = Modifier.size(20.dp)
        )
        Spacer(Modifier.width(8.dp))
        Text(
            text = title,
            fontSize = 19.sp,
            fontWeight = FontWeight.Bold,
            color = KalpaScreenColors.TextPrimary,
            modifier = Modifier.weight(1f)
        )
        Spacer(Modifier.width(8.dp))
        Text(
            text = trailing,
            fontSize = 12.sp,
            color = KalpaScreenColors.TextSecondary,
            maxLines = 1
        )
    }
}

/* -------------------------------------------------------------------- */
/*  PRICE BENCHMARK                                                      */
/* -------------------------------------------------------------------- */
@Composable
private fun PriceBenchmarkCard() {
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = KalpaScreenColors.CardWhite,
        border = BorderStroke(1.dp, KalpaScreenColors.Divider),
        shadowElevation = 1.dp,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "CURRENT LOCAL MANDI RATE",
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold,
                    letterSpacing = 0.4.sp,
                    color = KalpaScreenColors.OrangeDeep,
                    modifier = Modifier.weight(1f).padding(end = 8.dp)
                )
                Text(
                    text = "Last 90 days",
                    fontSize = 12.sp,
                    color = KalpaScreenColors.TextSecondary,
                    maxLines = 1
                )
            }
            Spacer(Modifier.height(8.dp))
            Row(verticalAlignment = Alignment.Bottom) {
                Text(
                    text = "₹134 – ₹142",
                    fontSize = 28.sp,
                    fontWeight = FontWeight.Bold,
                    color = KalpaScreenColors.TextPrimary
                )
                Spacer(Modifier.width(4.dp))
                Text(
                    text = "/ kg",
                    fontSize = 15.sp,
                    color = KalpaScreenColors.TextSecondary,
                    modifier = Modifier.padding(bottom = 4.dp)
                )
            }
            Spacer(Modifier.height(6.dp))
            Text(
                text = "Average selling price across nearby wholesale markets.",
                fontSize = 14.sp,
                lineHeight = 20.sp,
                color = KalpaScreenColors.TextSecondary
            )
        }
    }
}

/* -------------------------------------------------------------------- */
/*  OFF-TAKE CARD (tap -> detail sheet)                                  */
/* -------------------------------------------------------------------- */
@Composable
private fun OffTakeCard(item: OpportunityDetail, onClick: () -> Unit) {
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = KalpaScreenColors.CardWhite,
        border = BorderStroke(1.dp, KalpaScreenColors.Divider),
        shadowElevation = 1.dp,
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .clickable(onClick = onClick)
                .padding(16.dp),
            verticalAlignment = Alignment.Top
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = item.label,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold,
                    letterSpacing = 0.4.sp,
                    color = KalpaScreenColors.OrangeDeep
                )
                Spacer(Modifier.height(6.dp))
                Text(
                    text = "${item.score} • ${item.status}",
                    fontSize = 17.sp,
                    fontWeight = FontWeight.Bold,
                    color = KalpaScreenColors.TextPrimary
                )
                Spacer(Modifier.height(6.dp))
                Text(
                    text = item.summary,
                    fontSize = 14.sp,
                    lineHeight = 20.sp,
                    color = KalpaScreenColors.TextSecondary,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
            }
            Spacer(Modifier.width(8.dp))
            Icon(
                imageVector = Icons.AutoMirrored.Filled.KeyboardArrowRight,
                contentDescription = "See details",
                tint = KalpaScreenColors.TextSecondary,
                modifier = Modifier.size(20.dp)
            )
        }
    }
}

/* -------------------------------------------------------------------- */
/*  KEY MARKET CHECK CARD (tap -> detail sheet)                          */
/* -------------------------------------------------------------------- */
@Composable
private fun KeyCheckCard(
    item: OpportunityDetail,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = KalpaScreenColors.CardWhite,
        border = BorderStroke(1.dp, KalpaScreenColors.Divider),
        shadowElevation = 1.dp,
        modifier = modifier
    ) {
        Column(
            modifier = Modifier
                .clickable(onClick = onClick)
                .padding(14.dp)
        ) {
            Text(
                text = item.label,
                fontSize = 11.sp,
                fontWeight = FontWeight.SemiBold,
                letterSpacing = 0.4.sp,
                color = KalpaScreenColors.OrangeDeep
            )
            Spacer(Modifier.height(6.dp))
            Text(
                text = item.score,
                fontSize = 17.sp,
                fontWeight = FontWeight.Bold,
                color = KalpaScreenColors.TextPrimary
            )
            Text(
                text = item.status,
                fontSize = 13.sp,
                fontWeight = FontWeight.Medium,
                color = KalpaScreenColors.OrangeDeep
            )
            Spacer(Modifier.height(8.dp))
            Text(
                text = item.summary,
                fontSize = 12.sp,
                lineHeight = 17.sp,
                color = KalpaScreenColors.TextSecondary
            )
        }
    }
}

/* -------------------------------------------------------------------- */
/*  DETAIL BOTTOM-SHEET CONTENT                                          */
/* -------------------------------------------------------------------- */
@Composable
private fun DetailSheet(detail: OpportunityDetail, onClose: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .navigationBarsPadding()
            .padding(horizontal = 20.dp)
            .padding(bottom = 20.dp)
    ) {
        Text(
            text = detail.label,
            fontSize = 12.sp,
            fontWeight = FontWeight.SemiBold,
            letterSpacing = 0.4.sp,
            color = KalpaScreenColors.OrangeDeep
        )
        Spacer(Modifier.height(6.dp))
        Text(
            text = "${detail.score} • ${detail.status}",
            fontSize = 22.sp,
            fontWeight = FontWeight.Bold,
            color = KalpaScreenColors.TextPrimary
        )
        Spacer(Modifier.height(12.dp))
        Text(
            text = detail.fullText,
            fontSize = 15.sp,
            lineHeight = 22.sp,
            color = KalpaScreenColors.TextPrimary,
            textAlign = TextAlign.Start
        )
        Spacer(Modifier.height(20.dp))
        Button(
            onClick = onClose,
            modifier = Modifier
                .fillMaxWidth()
                .height(50.dp),
            shape = RoundedCornerShape(30.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = KalpaScreenColors.Orange,
                contentColor = Color.White
            )
        ) {
            Text("Got it", fontSize = 16.sp, fontWeight = FontWeight.Bold)
        }
    }
}

@Preview(showBackground = true, heightDp = 1200)
@Composable
private fun BusinessOpportunityScreenPreview() {
    BusinessOpportunityScreen()
}