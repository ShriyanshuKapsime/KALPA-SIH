package com.kalpa.android.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
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
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch

// Data Models
private data class AreaBullet(
    val text: String,
    val type: BulletType
)

private enum class BulletType { OK, WARN, ERROR }

private data class KeyArea(
    val id: Int,
    val title: String,
    val score: Int,
    val status: String,
    val statusColor: Color,
    val statusBg: Color,
    val bullets: List<AreaBullet>,
    val footerText: String,
    val footerIsRed: Boolean = false,
    val icon: ImageVector
)

private data class GapAction(
    val title: String,
    val tagLeft: String,
    val tagRight: String,
    val subtitle: String,
    val whyItMatters: String,
    val buttonText: String,
    val isExternal: Boolean = false
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EntrepreneurReadinessScreen(
    onBackClick: () -> Unit = {},
    onContinueClick: () -> Unit = {}
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val scope = rememberCoroutineScope()
    var selectedArea by remember { mutableStateOf<KeyArea?>(null) }

    val keyAreas = listOf(
        KeyArea(
            id = 1,
            title = "1. Your practical skills",
            score = 82,
            status = "STRONG",
            statusColor = KalpaScreenColors.StatusGreenText,
            statusBg = KalpaScreenColors.StatusGreenBg,
            bullets = listOf(
                AreaBullet("Experience in direct selling and live bird bargaining", BulletType.OK),
                AreaBullet("Good contact with local feed suppliers", BulletType.OK),
                AreaBullet("Need more practice in recording daily feed costs", BulletType.WARN)
            ),
            footerText = "Compared with local farm benchmark",
            icon = Icons.Filled.Diamond // Placeholder for gem/skills
        ),
        KeyArea(
            id = 2,
            title = "2. Farming experience",
            score = 74,
            status = "MODERATE",
            statusColor = KalpaScreenColors.OrangeDark,
            statusBg = KalpaScreenColors.OrangeBadgeBg,
            bullets = listOf(
                AreaBullet("2 years helping in family poultry transport", BulletType.OK),
                AreaBullet("Knows seasonal bird diseases and price swings", BulletType.OK),
                AreaBullet("First time running a farm as main owner", BulletType.WARN)
            ),
            footerText = "Verified from interview answers",
            icon = Icons.Filled.Agriculture
        ),
        KeyArea(
            id = 3,
            title = "3. Training & Certificates",
            score = 62,
            status = "ATTENTION NEEDED",
            statusColor = KalpaScreenColors.DelayRed,
            statusBg = Color(0xFFFFE5E5),
            bullets = listOf(
                AreaBullet("Knows basic chick brooding and feeding", BulletType.OK),
                AreaBullet("No official poultry training certificate yet", BulletType.ERROR),
                AreaBullet("Certificate required by bank for government subsidy", BulletType.WARN)
            ),
            footerText = "Required for bank loan",
            footerIsRed = true,
            icon = Icons.Filled.WorkspacePremium
        ),
        KeyArea(
            id = 4,
            title = "4. Your land & shed",
            score = 88,
            status = "VERY STRONG",
            statusColor = KalpaScreenColors.StatusGreenText,
            statusBg = KalpaScreenColors.StatusGreenBg,
            bullets = listOf(
                AreaBullet("0.4 acre fenced land owned near bypass", BulletType.OK),
                AreaBullet("Contact with 2 local chick suppliers", BulletType.OK),
                AreaBullet("Good concrete road for feed delivery trucks", BulletType.OK)
            ),
            footerText = "Location confirmed by GPS",
            icon = Icons.Filled.Landscape
        ),
        KeyArea(
            id = 5,
            title = "5. Daily time you can give",
            score = 85,
            status = "STRONG",
            statusColor = KalpaScreenColors.StatusGreenText,
            statusBg = KalpaScreenColors.StatusGreenBg,
            bullets = listOf(
                AreaBullet("Full-time commitment (8+ hours daily on farm)", BulletType.OK),
                AreaBullet("Borewell water pump with planned power inverter", BulletType.OK),
                AreaBullet("Plan needed for rainy season shed dampness", BulletType.WARN)
            ),
            footerText = "Batch time: 38-42 Days",
            icon = Icons.Filled.Schedule
        )
    )

    val gaps = listOf(
        GapAction(
            title = "Poultry Care & Vaccination Training",
            tagLeft = "3-Hour Course • Free",
            tagRight = "Required for Bank Subsidy",
            subtitle = "KVK Burdwan • In person or online video",
            whyItMatters = "Saves up to 6% more chicks from death and meets bank loan criteria.",
            buttonText = "Open free lesson & book visit",
            isExternal = true
        ),
        GapAction(
            title = "Simple Farm Cash-Book & Feed Calculator",
            tagLeft = "Easy Tool • 45 Mins",
            tagRight = "Learn at your pace",
            subtitle = "Simple guide for farm daily accounts",
            whyItMatters = "Prevents losing track of money and ensures fair mandi prices.",
            buttonText = "Try simple calculator"
        ),
        GapAction(
            title = "Monsoon Shed Care & Ventilation Guide",
            tagLeft = "Simple Guide • PDF / Audio",
            tagRight = "In Bengali & English",
            subtitle = "State Animal Resources Dept. Guide",
            whyItMatters = "Keeps chicks healthy and dry during heavy rainy seasons.",
            buttonText = "View Guide"
        )
    )

    val blurRadius by androidx.compose.animation.core.animateDpAsState(targetValue = if (selectedArea != null) 12.dp else 0.dp, label = "blur")
    Scaffold(
        modifier = if (blurRadius > 0.dp) Modifier.blur(blurRadius) else Modifier,
        containerColor = KalpaScreenColors.ScreenBackgroundCream,
        bottomBar = {
            BottomBar(onContinueClick = onContinueClick)
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
        ) {
            KalpaTopBar(onBackClick = onBackClick, stepText = "Page 8 of 14")

            Column(modifier = Modifier.padding(horizontal = 20.dp)) {
                Spacer(Modifier.height(8.dp))

                Text(
                    text = "Can you run this business?",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold
                )

                Spacer(Modifier.height(20.dp))

                ProjectSummaryCard()

                Spacer(Modifier.height(16.dp))

                OverallReadinessCard()

                Spacer(Modifier.height(24.dp))

                Text(
                    text = "5 Key Areas Checked",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
                
                Spacer(Modifier.height(12.dp))

                // Compact List of Key Areas to save vertical space
                keyAreas.forEach { area ->
                    CompactKeyAreaItem(area = area) {
                        selectedArea = area
                        scope.launch { sheetState.show() }
                    }
                    Spacer(Modifier.height(8.dp))
                }

                Spacer(Modifier.height(24.dp))

                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = Icons.Filled.CheckCircleOutline,
                        contentDescription = null,
                        tint = KalpaScreenColors.OrangeDark,
                        modifier = Modifier.size(20.dp)
                    )
                    Spacer(Modifier.width(8.dp))
                    Text(
                        text = "Help to close gaps",
                        color = KalpaScreenColors.TextPrimary,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "3 free steps to pass bank checks and protect your profits before buying chicks.",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 12.sp,
                    lineHeight = 16.sp
                )

                Spacer(Modifier.height(16.dp))
            }

            // Horizontal scrolling gaps to save vertical space
            LazyRow(
                contentPadding = PaddingValues(horizontal = 20.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(gaps) { gap ->
                    GapActionCard(gap)
                }
            }

            Spacer(Modifier.height(32.dp))
        }
    }

    // Bottom Sheet for Detailed Key Area
    if (selectedArea != null) {
        ModalBottomSheet(
            onDismissRequest = {
                scope.launch { sheetState.hide() }.invokeOnCompletion {
                    if (!sheetState.isVisible) {
                        selectedArea = null
                    }
                }
            },
            sheetState = sheetState,
            containerColor = KalpaScreenColors.ScreenBackgroundCream,
            dragHandle = { BottomSheetDefaults.DragHandle() }
        ) {
            selectedArea?.let { area ->
                KeyAreaDetailSheet(area = area)
            }
        }
    }
}


@Composable
private fun ProjectSummaryCard() {
    Surface(
        shape = RoundedCornerShape(12.dp),
        color = KalpaScreenColors.CardWhite
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = "TARGET FLOCK SIZE",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 0.5.sp
                )
                Text(
                    text = "1,000 Birds",
                    color = KalpaScreenColors.OrangeDark,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold
                )
            }
            Spacer(Modifier.height(4.dp))
            Text(
                text = "₹8,00,000 Total Project Cost",
                color = KalpaScreenColors.TextPrimary,
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold
            )
            Spacer(Modifier.height(8.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(modifier = Modifier.size(6.dp).background(KalpaScreenColors.Orange, CircleShape))
                Spacer(Modifier.width(6.dp))
                Text(
                    text = "Your money: ₹2,00,000 (25%) + Bank loan: ₹6,00,000",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 11.sp,
                    modifier = Modifier.weight(1f)
                )
            }
        }
    }
}

@Composable
private fun OverallReadinessCard() {
    Surface(
        shape = RoundedCornerShape(12.dp),
        color = KalpaScreenColors.CardWhite
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Column(modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                    Text(
                        text = "OVERALL READINESS SCORE",
                        color = KalpaScreenColors.TextSecondary,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.5.sp
                    )
                    Spacer(Modifier.height(4.dp))
                    Row(verticalAlignment = Alignment.Bottom) {
                        Text(
                            text = "79",
                            color = KalpaScreenColors.OrangeDark,
                            fontSize = 32.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = " /100",
                            color = KalpaScreenColors.TextSecondary,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = KalpaScreenColors.OrangeBadgeBg
                ) {
                    Text(
                        text = "High Readiness",
                        color = KalpaScreenColors.OrangeDark,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp)
                    )
                }
            }

            Spacer(Modifier.height(16.dp))

            // Progress bar
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(6.dp)
                    .clip(RoundedCornerShape(3.dp)),
                horizontalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                Box(modifier = Modifier.weight(0.5f).fillMaxHeight().background(KalpaScreenColors.OrangeBadgeBg))
                Box(modifier = Modifier.weight(0.29f).fillMaxHeight().background(KalpaScreenColors.OrangeDark))
                Box(modifier = Modifier.weight(0.21f).fillMaxHeight().background(KalpaScreenColors.Divider))
            }
            
            Spacer(Modifier.height(6.dp))
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(text = "Beginner (0-\n50)", color = KalpaScreenColors.TextMuted, fontSize = 9.sp, lineHeight = 12.sp, modifier = Modifier.weight(1f))
                Text(text = "Ready with Support (51-\n85)", color = KalpaScreenColors.OrangeDark, fontSize = 9.sp, fontWeight = FontWeight.Bold, lineHeight = 12.sp, modifier = Modifier.weight(1f), textAlign = androidx.compose.ui.text.style.TextAlign.Center)
                Text(text = "Ready on own (86-\n100)", color = KalpaScreenColors.TextMuted, fontSize = 9.sp, textAlign = androidx.compose.ui.text.style.TextAlign.End, lineHeight = 12.sp, modifier = Modifier.weight(1f))
            }
        }
    }
}

@Composable
private fun CompactKeyAreaItem(area: KeyArea, onClick: () -> Unit) {
    Surface(
        shape = RoundedCornerShape(12.dp),
        color = KalpaScreenColors.CardWhite,
        modifier = Modifier.clickable { onClick() }
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .background(KalpaScreenColors.PillGray, CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = area.icon,
                    contentDescription = null,
                    tint = KalpaScreenColors.TextSecondary,
                    modifier = Modifier.size(20.dp)
                )
            }
            Spacer(Modifier.width(12.dp))
            
            Text(
                text = area.title,
                color = KalpaScreenColors.TextPrimary,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.weight(1f)
            )
            
            Spacer(Modifier.width(8.dp))
            
            Column(horizontalAlignment = Alignment.End) {
                Row(verticalAlignment = Alignment.Bottom) {
                    Text(
                        text = "${area.score}",
                        color = area.statusColor,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "/100",
                        color = KalpaScreenColors.TextSecondary,
                        fontSize = 11.sp
                    )
                }
                Spacer(Modifier.height(2.dp))
                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = area.statusBg
                ) {
                    Text(
                        text = area.status,
                        color = area.statusColor,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }
            }
            
            Spacer(Modifier.width(8.dp))
            Icon(
                imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                contentDescription = null,
                tint = KalpaScreenColors.TextMuted,
                modifier = Modifier.size(16.dp)
            )
        }
    }
}

@Composable
private fun KeyAreaDetailSheet(area: KeyArea) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 24.dp, vertical = 16.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(48.dp)
                        .background(KalpaScreenColors.PillGray, CircleShape),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = area.icon,
                        contentDescription = null,
                        tint = KalpaScreenColors.TextSecondary,
                        modifier = Modifier.size(24.dp)
                    )
                }
                Spacer(Modifier.width(16.dp))
                Text(
                    text = area.title,
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }
        
        Spacer(Modifier.height(16.dp))
        
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = "Score:",
                color = KalpaScreenColors.TextSecondary,
                fontSize = 14.sp
            )
            Spacer(Modifier.width(8.dp))
            Text(
                text = "${area.score}/100",
                color = area.statusColor,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold
            )
            Spacer(Modifier.width(12.dp))
            Surface(
                shape = RoundedCornerShape(12.dp),
                color = area.statusBg
            ) {
                Text(
                    text = area.status,
                    color = area.statusColor,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp)
                )
            }
        }
        
        Spacer(Modifier.height(24.dp))
        
        area.bullets.forEach { bullet ->
            Row(
                modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp),
                verticalAlignment = Alignment.Top
            ) {
                val (icon, tint) = when (bullet.type) {
                    BulletType.OK -> Icons.Filled.CheckCircle to KalpaScreenColors.StatusGreenText
                    BulletType.WARN -> Icons.Filled.Info to KalpaScreenColors.Orange
                    BulletType.ERROR -> Icons.Filled.Cancel to KalpaScreenColors.DelayRed
                }
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = tint,
                    modifier = Modifier.size(18.dp).padding(top = 2.dp)
                )
                Spacer(Modifier.width(10.dp))
                Text(
                    text = bullet.text,
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 14.sp,
                    lineHeight = 20.sp,
                    modifier = Modifier.weight(1f)
                )
            }
        }
        
        Spacer(Modifier.height(16.dp))
        HorizontalDivider(color = KalpaScreenColors.Divider)
        Spacer(Modifier.height(16.dp))
        
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = area.footerText,
                color = if (area.footerIsRed) KalpaScreenColors.DelayRed else KalpaScreenColors.TextSecondary,
                fontSize = 12.sp
            )
            
            Surface(
                shape = RoundedCornerShape(16.dp),
                color = KalpaScreenColors.OrangeBadgeBg
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp)
                ) {
                    Text(
                        text = "How calculated",
                        color = KalpaScreenColors.OrangeDark,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(Modifier.width(4.dp))
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                        contentDescription = null,
                        tint = KalpaScreenColors.OrangeDark,
                        modifier = Modifier.size(14.dp)
                    )
                }
            }
        }
        
        Spacer(Modifier.height(32.dp))
    }
}

@Composable
private fun GapActionCard(gap: GapAction) {
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = KalpaScreenColors.CardWhite,
        modifier = Modifier.width(300.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Surface(
                    shape = RoundedCornerShape(6.dp),
                    color = KalpaScreenColors.PillGray
                ) {
                    Text(
                        text = gap.tagLeft,
                        color = KalpaScreenColors.TextPrimary,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 4.dp)
                    )
                }
                Text(
                    text = gap.tagRight,
                    color = KalpaScreenColors.OrangeDark,
                    fontSize = 9.sp,
                    fontWeight = FontWeight.Bold
                )
            }
            
            Spacer(Modifier.height(12.dp))
            
            Text(
                text = gap.title,
                color = KalpaScreenColors.TextPrimary,
                fontSize = 15.sp,
                fontWeight = FontWeight.Bold,
                lineHeight = 20.sp
            )
            Spacer(Modifier.height(4.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = Icons.Filled.MenuBook,
                    contentDescription = null,
                    tint = KalpaScreenColors.TextSecondary,
                    modifier = Modifier.size(12.dp)
                )
                Spacer(Modifier.width(4.dp))
                Text(
                    text = gap.subtitle,
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 11.sp,
                    modifier = Modifier.weight(1f)
                )
            }
            
            Spacer(Modifier.height(12.dp))
            
            Surface(
                shape = RoundedCornerShape(8.dp),
                color = KalpaScreenColors.ScreenBackgroundCream
            ) {
                Text(
                    text = "Why it matters: ${gap.whyItMatters}",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 11.sp,
                    lineHeight = 16.sp,
                    modifier = Modifier.padding(10.dp)
                )
            }
            
            Spacer(Modifier.height(16.dp))
            
            Surface(
                shape = RoundedCornerShape(20.dp),
                color = KalpaScreenColors.PillGray,
                modifier = Modifier.fillMaxWidth().clickable { /* TODO */ }
            ) {
                Row(
                    modifier = Modifier.padding(vertical = 12.dp),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = gap.buttonText,
                        color = KalpaScreenColors.TextPrimary,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(Modifier.width(8.dp))
                    if (gap.isExternal) {
                        Icon(
                            imageVector = Icons.Filled.OpenInNew,
                            contentDescription = null,
                            tint = KalpaScreenColors.TextPrimary,
                            modifier = Modifier.size(14.dp)
                        )
                    } else {
                        Icon(
                            imageVector = Icons.Filled.PlayCircleOutline,
                            contentDescription = null,
                            tint = KalpaScreenColors.TextPrimary,
                            modifier = Modifier.size(16.dp)
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun BottomBar(onContinueClick: () -> Unit) {
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
                    Text(
                        text = "Check Loan Eligibility",
                        color = Color.White,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold
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
}

@Preview
@Composable
fun EntrepreneurReadinessScreenPreview() {
    MaterialTheme {
        EntrepreneurReadinessScreen()
    }
}
