package com.kalpa.android.screens

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
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.text.SpanStyle

// Data Models
private data class SWOTSection(
    val title: String,
    val subtitle: String,
    val countText: String,
    val icon: ImageVector,
    val colorTheme: Color,
    val bgTheme: Color,
    val items: List<SWOTItem>
)

private data class SWOTItem(
    val title: String,
    val description: String,
    val sectionColor: Color
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BusinessSWOTScreen(
    onBackClick: () -> Unit = {},
    onContinueClick: () -> Unit = {}
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val scope = rememberCoroutineScope()
    var selectedItem by remember { mutableStateOf<SWOTItem?>(null) }

    val sections = listOf(
        SWOTSection(
            title = "Strengths",
            subtitle = "Site profile & assets",
            countText = "3 notes",
            icon = Icons.Filled.TrendingUp,
            colorTheme = KalpaScreenColors.StatusGreenText,
            bgTheme = KalpaScreenColors.StatusGreenBg,
            items = listOf(
                SWOTItem(
                    title = "12 min highway transit",
                    description = "Direct NH-19 connectivity prevents stress-induced flock weight depletion during transport.",
                    sectionColor = KalpaScreenColors.StatusGreenText
                ),
                SWOTItem(
                    title = "Low local competition",
                    description = "Only 3 active poultry units within 8 km for a catchment demanding 3,400 kg/day.",
                    sectionColor = KalpaScreenColors.StatusGreenText
                ),
                SWOTItem(
                    title = "PMEGP subsidy eligibility",
                    description = "Meets rural agro criteria for ₹6.50L sanctioned term bank loan + 35% margin subsidy.",
                    sectionColor = KalpaScreenColors.StatusGreenText
                )
            )
        ),
        SWOTSection(
            title = "Weaknesses",
            subtitle = "Identified execution gaps",
            countText = "2 notes",
            icon = Icons.Filled.RemoveCircleOutline,
            colorTheme = KalpaScreenColors.OrangeDark, // A brown/orange tone
            bgTheme = KalpaScreenColors.OrangeBadgeBg,
            items = listOf(
                SWOTItem(
                    title = "First-time operator gap",
                    description = "No formal certification in biosecurity and acute Ranikhet/Gumboro symptom triage.",
                    sectionColor = KalpaScreenColors.OrangeDark
                ),
                SWOTItem(
                    title = "Tight equity reserve",
                    description = "₹1.0L initial equity leaves limited buffer if feed rates surge across 45-day growth window.",
                    sectionColor = KalpaScreenColors.OrangeDark
                )
            )
        ),
        SWOTSection(
            title = "Opportunities",
            subtitle = "Market & cost levers",
            countText = "3 notes",
            icon = Icons.Filled.Lightbulb,
            colorTheme = KalpaScreenColors.Orange,
            bgTheme = KalpaScreenColors.OrangeBadgeBg,
            items = listOf(
                SWOTItem(
                    title = "Local feed hub savings",
                    description = "Direct procurement from Andal junction millers saves ₹1.80/kg over Kolkata transit dealers.",
                    sectionColor = KalpaScreenColors.Orange
                ),
                SWOTItem(
                    title = "Winter demand cycle",
                    description = "+28% seasonal retail volume spike driven by regional weddings and festive catering.",
                    sectionColor = KalpaScreenColors.Orange
                ),
                SWOTItem(
                    title = "Highway dhaba contracts",
                    description = "42 institutional dining establishments within 15 km seeking scheduled farm-gate collection.",
                    sectionColor = KalpaScreenColors.Orange
                )
            )
        ),
        SWOTSection(
            title = "Threats",
            subtitle = "External operational risks",
            countText = "2 notes",
            icon = Icons.Filled.Shield,
            colorTheme = KalpaScreenColors.DelayRed,
            bgTheme = Color(0xFFFFE5E5),
            items = listOf(
                SWOTItem(
                    title = "Summer heat spikes",
                    description = "April-June temperatures exceeding 42°C risk up to 12% flock mortality without foggers.",
                    sectionColor = KalpaScreenColors.DelayRed
                ),
                SWOTItem(
                    title = "Mandi price volatility",
                    description = "Live bird wholesale fluctuates between ₹134-₹142/kg under weekly unorganized syndicates.",
                    sectionColor = KalpaScreenColors.DelayRed
                )
            )
        )
    )

    val blurRadius by androidx.compose.animation.core.animateDpAsState(targetValue = if (selectedItem != null) 12.dp else 0.dp, label = "blur")
    Scaffold(
        modifier = if (blurRadius > 0.dp) Modifier.blur(blurRadius) else Modifier,
        containerColor = KalpaScreenColors.ScreenBackgroundCream,
        bottomBar = {
            SWOTBottomBar(onContinueClick = onContinueClick)
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
        ) {
            KalpaTopBar(onBackClick = onBackClick, stepText = "Page 11 of 14")

            Column(modifier = Modifier.padding(horizontal = 20.dp)) {
                Spacer(Modifier.height(8.dp))

                Text(
                    text = "Your business at a glance",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 26.sp,
                    fontWeight = FontWeight.Bold,
                    lineHeight = 32.sp
                )

                Spacer(Modifier.height(16.dp))

                BusinessBanner()

                Spacer(Modifier.height(24.dp))

                sections.forEach { section ->
                    SWOTSectionView(
                        section = section,
                        onItemClick = { item ->
                            selectedItem = item
                            scope.launch { sheetState.show() }
                        }
                    )
                    Spacer(Modifier.height(24.dp))
                }

                Spacer(Modifier.height(16.dp))
            }
        }
    }

    // Bottom Sheet for Evidence Details
    if (selectedItem != null) {
        ModalBottomSheet(
            onDismissRequest = {
                scope.launch { sheetState.hide() }.invokeOnCompletion {
                    if (!sheetState.isVisible) {
                        selectedItem = null
                    }
                }
            },
            sheetState = sheetState,
            containerColor = KalpaScreenColors.ScreenBackgroundCream,
            dragHandle = { BottomSheetDefaults.DragHandle() }
        ) {
            selectedItem?.let { item ->
                SWOTEvidenceSheet(item = item)
            }
        }
    }
}



@Composable
private fun BusinessBanner() {
    Surface(
        shape = RoundedCornerShape(12.dp),
        color = KalpaScreenColors.FieldGray, // light warm gray
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .background(KalpaScreenColors.OrangeBadgeBg, CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Filled.Agriculture,
                    contentDescription = null,
                    tint = KalpaScreenColors.OrangeDark,
                    modifier = Modifier.size(20.dp)
                )
            }
            Spacer(Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = buildAnnotatedString {
                        withStyle(
                            style = SpanStyle(
                                color = KalpaScreenColors.TextPrimary,
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold
                            )
                        ) {
                            append("1,000 Birds Broiler Farm")
                        }
                        withStyle(
                            style = SpanStyle(
                                color = KalpaScreenColors.TextSecondary,
                                fontSize = 12.sp
                            )
                        ) {
                            append(" • Batch cycle #1")
                        }
                    },
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(Modifier.height(4.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = Icons.Filled.LocationOn,
                        contentDescription = null,
                        tint = KalpaScreenColors.TextSecondary,
                        modifier = Modifier.size(12.dp)
                    )
                    Spacer(Modifier.width(4.dp))
                    Text(
                        text = "NH-19 Corridor, Banskopa, Paschim Bardhaman",
                        color = KalpaScreenColors.TextSecondary,
                        fontSize = 11.sp
                    )
                }
            }
        }
    }
}

@Composable
private fun SWOTSectionView(section: SWOTSection, onItemClick: (SWOTItem) -> Unit) {
    Column {
        // Section Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                Box(
                    modifier = Modifier
                        .size(40.dp)
                        .background(section.bgTheme, RoundedCornerShape(10.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = section.icon,
                        contentDescription = null,
                        tint = section.colorTheme,
                        modifier = Modifier.size(20.dp)
                    )
                }
                Spacer(Modifier.width(12.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = section.title,
                        color = KalpaScreenColors.TextPrimary,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = section.subtitle,
                        color = KalpaScreenColors.TextSecondary,
                        fontSize = 12.sp
                    )
                }
            }
            Surface(
                shape = RoundedCornerShape(12.dp),
                color = section.bgTheme
            ) {
                Text(
                    text = section.countText,
                    color = section.colorTheme,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                )
            }
        }
        
        Spacer(Modifier.height(12.dp))
        
        // Compact Items List
        section.items.forEach { item ->
            CompactSWOTItem(item = item, onClick = { onItemClick(item) })
            Spacer(Modifier.height(8.dp))
        }
    }
}

@Composable
private fun CompactSWOTItem(item: SWOTItem, onClick: () -> Unit) {
    Surface(
        shape = RoundedCornerShape(12.dp),
        color = KalpaScreenColors.CardWhite,
        modifier = Modifier.clickable { onClick() }
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = item.title,
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.weight(1f)
                )
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = "Evidence",
                        color = KalpaScreenColors.OrangeDark,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(Modifier.width(2.dp))
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                        contentDescription = null,
                        tint = KalpaScreenColors.OrangeDark,
                        modifier = Modifier.size(12.dp)
                    )
                }
            }
            Spacer(Modifier.height(6.dp))
            Text(
                text = item.description,
                color = KalpaScreenColors.TextSecondary,
                fontSize = 12.sp,
                lineHeight = 16.sp,
                maxLines = 1, // Compact view truncates the description to save space
                overflow = TextOverflow.Ellipsis
            )
        }
    }
}

@Composable
private fun SWOTEvidenceSheet(item: SWOTItem) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 24.dp, vertical = 16.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(
                imageVector = Icons.Filled.Analytics,
                contentDescription = null,
                tint = item.sectionColor,
                modifier = Modifier.size(24.dp)
            )
            Spacer(Modifier.width(12.dp))
            Text(
                text = "Detailed Evidence",
                color = item.sectionColor,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold
            )
        }
        
        Spacer(Modifier.height(16.dp))
        
        Text(
            text = item.title,
            color = KalpaScreenColors.TextPrimary,
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
            lineHeight = 26.sp
        )
        
        Spacer(Modifier.height(16.dp))
        
        Surface(
            shape = RoundedCornerShape(12.dp),
            color = KalpaScreenColors.CardWhite,
            border = androidx.compose.foundation.BorderStroke(1.dp, KalpaScreenColors.Divider),
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(
                text = item.description,
                color = KalpaScreenColors.TextPrimary,
                fontSize = 15.sp,
                lineHeight = 22.sp,
                modifier = Modifier.padding(16.dp)
            )
        }
        
        Spacer(Modifier.height(24.dp))
        
        Text(
            text = "Data Source",
            color = KalpaScreenColors.TextSecondary,
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold,
            letterSpacing = 0.5.sp
        )
        Spacer(Modifier.height(8.dp))
        Surface(
            shape = RoundedCornerShape(12.dp),
            color = KalpaScreenColors.PillGray,
            modifier = Modifier.fillMaxWidth()
        ) {
            Row(modifier = Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = Icons.Filled.CheckCircle,
                    contentDescription = null,
                    tint = KalpaScreenColors.StatusGreenText,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(Modifier.width(12.dp))
                Text(
                    text = "Verified via Local Market APIs and PMEGP Guidelines.",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 13.sp,
                    lineHeight = 18.sp,
                    modifier = Modifier.weight(1f)
                )
            }
        }
        
        Spacer(Modifier.height(32.dp))
    }
}

@Composable
private fun SWOTBottomBar(onContinueClick: () -> Unit) {
    Surface(color = KalpaScreenColors.ScreenBackgroundCream) {
        Column(modifier = Modifier.padding(20.dp)) {
            Button(
                onClick = onContinueClick,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(54.dp),
                shape = RoundedCornerShape(27.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = KalpaScreenColors.OrangeDark
                )
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = Icons.Filled.CheckCircleOutline,
                        contentDescription = null,
                        tint = Color.White,
                        modifier = Modifier.size(18.dp)
                    )
                    Spacer(Modifier.width(8.dp))
                    Text(
                        text = "Confirm & Continue",
                        color = Color.White,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }
}

@Preview
@Composable
fun BusinessSWOTScreenPreview() {
    MaterialTheme {
        BusinessSWOTScreen()
    }
}
