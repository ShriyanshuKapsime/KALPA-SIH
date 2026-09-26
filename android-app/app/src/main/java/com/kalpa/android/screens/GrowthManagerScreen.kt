package com.kalpa.android.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
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
private data class StatItem(
    val title: String,
    val value: String,
    val subtitle: String,
    val isOrangeValue: Boolean = false
)

private data class OperationalAlert(
    val title: String,
    val tag: String,
    val description: String,
    val icon: ImageVector,
    val colorTheme: Color,
    val bgTheme: Color
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GrowthManagerScreen(
    onBackClick: () -> Unit = {},
    onContinueClick: () -> Unit = {}
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val scope = rememberCoroutineScope()
    var selectedAlert by remember { mutableStateOf<OperationalAlert?>(null) }

    val stats = listOf(
        StatItem("TOTAL SALES", "₹1,42,800", "This Month • 620 birds sold"),
        StatItem("OUTLAY", "₹96,400", "Feed, power & medicines"),
        StatItem("CASH ON HAND", "₹46,400", "In Current Account", isOrangeValue = true),
        StatItem("LOAN REPAYMENT", "₹14,200", "Due in 6d • PMEGP Term", isOrangeValue = true),
        StatItem("FEED STOCK", "18 Bags", "Broiler Finisher Feed"),
        StatItem("FLOCK HEALTH", "96.2%", "Batch 1 survival milestone")
    )

    val alerts = listOf(
        OperationalAlert(
            title = "Loan Auto-Debit Soon",
            tag = "10 Nov",
            description = "SBI Loan EMI of ₹14,200 is scheduled for auto-debit. Keep at least ₹15,000 balance in current account.",
            icon = Icons.Filled.AccountBalance,
            colorTheme = KalpaScreenColors.OrangeDark,
            bgTheme = KalpaScreenColors.OrangeBadgeBg
        ),
        OperationalAlert(
            title = "Finisher Feed Low",
            tag = "Action req.",
            description = "Stock reaches reorder threshold tomorrow morning. Distributor delivery takes 48 hours to Banskopa.",
            icon = Icons.Filled.Warning,
            colorTheme = KalpaScreenColors.DelayRed,
            bgTheme = Color(0xFFFFE5E5)
        ),
        OperationalAlert(
            title = "Heat Wave Advisory",
            tag = "+3°C expected",
            description = "Afternoon temperatures peaking for next 3 days. Check shed side-curtains and run sprinkler timers at 1:00 PM.",
            icon = Icons.Filled.Thermostat,
            colorTheme = KalpaScreenColors.TextSecondary,
            bgTheme = KalpaScreenColors.PillGray
        )
    )

    val blurRadius by androidx.compose.animation.core.animateDpAsState(targetValue = if (selectedAlert != null) 12.dp else 0.dp, label = "blur")
    Scaffold(
        modifier = if (blurRadius > 0.dp) Modifier.blur(blurRadius) else Modifier,
        containerColor = KalpaScreenColors.ScreenBackgroundCream,
        bottomBar = {
            GrowthManagerBottomBar(onContinueClick = onContinueClick)
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
        ) {
            KalpaTopBar(onBackClick = onBackClick, stepText = "Page 14 of 14")
            Spacer(Modifier.height(24.dp))

            Column(modifier = Modifier.padding(horizontal = 20.dp)) {
                Text(
                    text = "Keep your business moving",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "Here's what KALPA noticed about your business today.",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 13.sp
                )

                Spacer(Modifier.height(20.dp))

                NoticeCard()

                Spacer(Modifier.height(24.dp))

                Text(
                    text = "Business Statistics",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )

                Spacer(Modifier.height(16.dp))

                // Stats Grid
                Column {
                    for (i in stats.indices step 2) {
                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            StatCard(modifier = Modifier.weight(1f), item = stats[i])
                            if (i + 1 < stats.size) {
                                StatCard(modifier = Modifier.weight(1f), item = stats[i + 1])
                            }
                        }
                        Spacer(Modifier.height(12.dp))
                    }
                }

                Spacer(Modifier.height(16.dp))

                WeeklyCashSalesCard()

                Spacer(Modifier.height(24.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Operational Alerts",
                        color = KalpaScreenColors.TextPrimary,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Surface(
                        shape = RoundedCornerShape(12.dp),
                        color = KalpaScreenColors.PillGray
                    ) {
                        Text(
                            text = "3 Attention Items",
                            color = KalpaScreenColors.TextSecondary,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                        )
                    }
                }

                Spacer(Modifier.height(12.dp))

                // Compact Operational Alerts
                alerts.forEach { alert ->
                    CompactAlertItem(alert) {
                        selectedAlert = alert
                        scope.launch { sheetState.show() }
                    }
                    Spacer(Modifier.height(8.dp))
                }

                Spacer(Modifier.height(24.dp))

                GrowthOpportunityCard()

                Spacer(Modifier.height(32.dp))
            }
        }
    }

    // Bottom Sheet for Detailed Alert
    if (selectedAlert != null) {
        ModalBottomSheet(
            onDismissRequest = {
                scope.launch { sheetState.hide() }.invokeOnCompletion {
                    if (!sheetState.isVisible) {
                        selectedAlert = null
                    }
                }
            },
            sheetState = sheetState,
            containerColor = KalpaScreenColors.ScreenBackgroundCream,
            dragHandle = { BottomSheetDefaults.DragHandle() }
        ) {
            selectedAlert?.let { alert ->
                AlertDetailSheet(alert = alert)
            }
        }
    }
}

@Composable
private fun NoticeCard() {
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = KalpaScreenColors.OrangeBadgeBg
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                    Box(modifier = Modifier.size(6.dp).background(KalpaScreenColors.OrangeDark, CircleShape))
                    Spacer(Modifier.width(6.dp))
                    Text(
                        text = "KALPA NOTICED • THIS WEEK",
                        color = KalpaScreenColors.OrangeDark,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.5.sp
                    )
                }
                Icon(
                    imageVector = Icons.Filled.Lightbulb,
                    contentDescription = null,
                    tint = KalpaScreenColors.OrangeDark,
                    modifier = Modifier.size(16.dp)
                )
            }
            
            Spacer(Modifier.height(12.dp))
            
            Text(
                text = "Feed conversion ratio rose slightly while starter inventory is running low.",
                color = KalpaScreenColors.TextPrimary,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold,
                lineHeight = 20.sp
            )
            
            Spacer(Modifier.height(8.dp))
            
            Text(
                text = "Day 38 birds are consuming 8% more starter mash than projected. You have 3 days of feed remaining at current intake rate.",
                color = KalpaScreenColors.TextSecondary,
                fontSize = 12.sp,
                lineHeight = 18.sp
            )
            
            Spacer(Modifier.height(16.dp))
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.weight(1f).padding(end = 8.dp).clickable { }) {
                    Text(
                        text = "View feed replenishment rates",
                        color = KalpaScreenColors.OrangeDark,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(Modifier.width(4.dp))
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                        contentDescription = null,
                        tint = KalpaScreenColors.OrangeDark,
                        modifier = Modifier.size(12.dp)
                    )
                }
                Text(
                    text = "Calculated 3h\nago",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 9.sp,
                    lineHeight = 12.sp,
                    textAlign = androidx.compose.ui.text.style.TextAlign.End
                )
            }
        }
    }
}

@Composable
private fun StatCard(modifier: Modifier, item: StatItem) {
    Surface(
        shape = RoundedCornerShape(12.dp),
        color = KalpaScreenColors.CardWhite,
        modifier = modifier
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = item.title,
                color = KalpaScreenColors.TextSecondary,
                fontSize = 9.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 0.5.sp
            )
            Spacer(Modifier.height(8.dp))
            Text(
                text = item.value,
                color = if (item.isOrangeValue) KalpaScreenColors.OrangeDark else KalpaScreenColors.TextPrimary,
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold
            )
            Spacer(Modifier.height(8.dp))
            Text(
                text = item.subtitle,
                color = KalpaScreenColors.TextSecondary,
                fontSize = 11.sp,
                lineHeight = 14.sp
            )
        }
    }
}

@Composable
private fun WeeklyCashSalesCard() {
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = KalpaScreenColors.FieldGray
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Column(modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                    Text(
                        text = "Weekly Cash & Sales",
                        color = KalpaScreenColors.TextPrimary,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(Modifier.height(2.dp))
                    Text(
                        text = "Tangible revenue vs expenses (Weeks\n1 to 4)",
                        color = KalpaScreenColors.TextSecondary,
                        fontSize = 11.sp,
                        lineHeight = 14.sp
                    )
                }
                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = KalpaScreenColors.OrangeBadgeBg
                ) {
                    Text(
                        text = "+₹46,400\nNet",
                        color = KalpaScreenColors.OrangeDark,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                        modifier = Modifier.padding(6.dp)
                    )
                }
            }

            Spacer(Modifier.height(16.dp))

            // Chart Rows
            val wks = listOf(
                Pair("Wk 1", Triple(0.4f, 0.3f, "₹26.2k")),
                Pair("Wk 2", Triple(0.5f, 0.4f, "₹38.5k")),
                Pair("Wk 3", Triple(0.6f, 0.3f, "₹44.1k")),
                Pair("Wk 4", Triple(0.45f, 0.2f, "₹34.0k"))
            )

            wks.forEach { (wk, data) ->
                val (inflow, feed, amount) = data
                Row(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(text = wk, color = KalpaScreenColors.TextSecondary, fontSize = 11.sp, modifier = Modifier.width(36.dp))
                    
                    Row(modifier = Modifier.weight(1f).height(12.dp)) {
                        Box(modifier = Modifier.weight(inflow).fillMaxHeight().background(KalpaScreenColors.OrangeDark, RoundedCornerShape(topStart = 2.dp, bottomStart = 2.dp)))
                        Spacer(Modifier.width(2.dp))
                        Box(modifier = Modifier.weight(feed).fillMaxHeight().background(KalpaScreenColors.Divider, RoundedCornerShape(topEnd = 2.dp, bottomEnd = 2.dp)))
                        Box(modifier = Modifier.weight(1f - inflow - feed)) // padding
                    }
                    
                    Text(text = amount, color = KalpaScreenColors.TextSecondary, fontSize = 11.sp, modifier = Modifier.width(42.dp), textAlign = androidx.compose.ui.text.style.TextAlign.End)
                }
            }

            Spacer(Modifier.height(12.dp))

            // Legend
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(modifier = Modifier.size(8.dp).background(KalpaScreenColors.OrangeDark, RoundedCornerShape(2.dp)))
                    Spacer(Modifier.width(6.dp))
                    Text(text = "Inflow (Sales)", color = KalpaScreenColors.TextSecondary, fontSize = 10.sp)
                    Spacer(Modifier.width(12.dp))
                    Box(modifier = Modifier.size(8.dp).background(KalpaScreenColors.Divider, RoundedCornerShape(2.dp)))
                    Spacer(Modifier.width(6.dp))
                    Text(text = "Feed & Power", color = KalpaScreenColors.TextSecondary, fontSize = 10.sp)
                }
                Text(text = "Safe surplus", color = KalpaScreenColors.TextPrimary, fontSize = 10.sp, fontWeight = FontWeight.Bold)
            }

            Spacer(Modifier.height(16.dp))
            HorizontalDivider(color = KalpaScreenColors.Divider)
            Spacer(Modifier.height(16.dp))

            // Timeline
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(text = "Flock Cycle 2 Timeline", color = KalpaScreenColors.TextPrimary, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                Text(text = "Day 38 of 42", color = KalpaScreenColors.OrangeDark, fontSize = 11.sp, fontWeight = FontWeight.Bold)
            }
            
            Spacer(Modifier.height(8.dp))
            
            Row(modifier = Modifier.fillMaxWidth().height(6.dp).background(KalpaScreenColors.Divider, RoundedCornerShape(3.dp))) {
                Box(modifier = Modifier.fillMaxWidth(0.9f).fillMaxHeight().background(KalpaScreenColors.OrangeDark, RoundedCornerShape(3.dp)))
            }
            
            Spacer(Modifier.height(6.dp))
            
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(text = "Chicks arrived", color = KalpaScreenColors.TextSecondary, fontSize = 10.sp)
                Text(text = "Harvest in 4 days", color = KalpaScreenColors.OrangeDark, fontSize = 10.sp, fontWeight = FontWeight.Bold)
            }
        }
    }
}

@Composable
private fun CompactAlertItem(alert: OperationalAlert, onClick: () -> Unit) {
    Surface(
        shape = RoundedCornerShape(12.dp),
        color = alert.bgTheme,
        modifier = Modifier.clickable { onClick() }
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .background(Color.White.copy(alpha = 0.5f), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = alert.icon,
                    contentDescription = null,
                    tint = alert.colorTheme,
                    modifier = Modifier.size(20.dp)
                )
            }
            Spacer(Modifier.width(12.dp))
            
            Text(
                text = alert.title,
                color = KalpaScreenColors.TextPrimary,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.weight(1f)
            )
            
            Spacer(Modifier.width(8.dp))
            
            Text(
                text = alert.tag,
                color = alert.colorTheme,
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

@Composable
private fun AlertDetailSheet(alert: OperationalAlert) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 24.dp, vertical = 16.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .background(alert.bgTheme, CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = alert.icon,
                    contentDescription = null,
                    tint = alert.colorTheme,
                    modifier = Modifier.size(24.dp)
                )
            }
            Spacer(Modifier.width(16.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = alert.title,
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = alert.tag,
                    color = alert.colorTheme,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }
        
        Spacer(Modifier.height(24.dp))
        
        Surface(
            shape = RoundedCornerShape(12.dp),
            color = KalpaScreenColors.CardWhite,
            border = androidx.compose.foundation.BorderStroke(1.dp, KalpaScreenColors.Divider),
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(
                text = alert.description,
                color = KalpaScreenColors.TextPrimary,
                fontSize = 15.sp,
                lineHeight = 22.sp,
                modifier = Modifier.padding(16.dp)
            )
        }
        
        Spacer(Modifier.height(32.dp))
    }
}

@Composable
private fun GrowthOpportunityCard() {
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = KalpaScreenColors.CardWhite,
        border = androidx.compose.foundation.BorderStroke(1.dp, KalpaScreenColors.Divider)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = KalpaScreenColors.OrangeBadgeBg
                ) {
                    Text(
                        text = "GROWTH OPPORTUNITY",
                        color = KalpaScreenColors.OrangeDark,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.5.sp,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                    )
                }
                Icon(
                    imageVector = Icons.Filled.Storefront,
                    contentDescription = null,
                    tint = KalpaScreenColors.OrangeDark,
                    modifier = Modifier.size(18.dp)
                )
            }
            
            Spacer(Modifier.height(12.dp))
            
            Text(
                text = "Institutional buyer demand in Durgapur wholesale hub",
                color = KalpaScreenColors.TextPrimary,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold,
                lineHeight = 20.sp
            )
            
            Spacer(Modifier.height(8.dp))
            
            Text(
                text = "Hotel and mess buyers are offering ₹98/kg live weight for 1.8kg+ birds (+₹6 over mandi spot price).",
                color = KalpaScreenColors.TextSecondary,
                fontSize = 12.sp,
                lineHeight = 18.sp
            )
            
            Spacer(Modifier.height(16.dp))
            
            Surface(
                shape = RoundedCornerShape(12.dp),
                color = KalpaScreenColors.PillGray,
                modifier = Modifier.fillMaxWidth().clickable { }
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                        Icon(
                            imageVector = Icons.Filled.CheckCircleOutline,
                            contentDescription = null,
                            tint = KalpaScreenColors.OrangeDark,
                            modifier = Modifier.size(16.dp)
                        )
                        Spacer(Modifier.width(8.dp))
                        Text(
                            text = "See opportunity & evidence",
                            color = KalpaScreenColors.TextPrimary,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                    Icon(
                        imageVector = Icons.Filled.OpenInNew,
                        contentDescription = null,
                        tint = KalpaScreenColors.TextPrimary,
                        modifier = Modifier.size(16.dp)
                    )
                }
            }
        }
    }
}

@Composable
private fun GrowthManagerBottomBar(onContinueClick: () -> Unit) {
    Surface(color = KalpaScreenColors.ScreenBackgroundCream) {
        Column(modifier = Modifier.padding(20.dp)) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Surface(
                    modifier = Modifier.weight(1f).height(44.dp).clickable { },
                    shape = RoundedCornerShape(22.dp),
                    color = KalpaScreenColors.PillGray
                ) {
                    Row(
                        horizontalArrangement = Arrangement.Center,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(Icons.Filled.History, contentDescription = null, tint = KalpaScreenColors.TextSecondary, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(6.dp))
                        Text("What changed", color = KalpaScreenColors.TextPrimary, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    }
                }
                Surface(
                    modifier = Modifier.weight(1f).height(44.dp).clickable { },
                    shape = RoundedCornerShape(22.dp),
                    color = KalpaScreenColors.PillGray
                ) {
                    Row(
                        horizontalArrangement = Arrangement.Center,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(Icons.Filled.Mic, contentDescription = null, tint = KalpaScreenColors.OrangeDark, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(6.dp))
                        Text("Ask KALPA", color = KalpaScreenColors.TextPrimary, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
            
            Spacer(Modifier.height(16.dp))
            
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
                        text = "Plan next month",
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
fun GrowthManagerScreenPreview() {
    MaterialTheme {
        GrowthManagerScreen()
    }
}
