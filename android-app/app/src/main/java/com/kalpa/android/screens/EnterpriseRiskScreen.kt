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
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch

// Data Models
private data class RiskDetail(
    val title: String,
    val subtitle: String,
    val level: String,
    val levelColor: Color,
    val levelBg: Color,
    val description: String,
    val actionText: String,
    val icon: ImageVector
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EnterpriseRiskScreen(
    onBackClick: () -> Unit = {},
    onContinueClick: () -> Unit = {}
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val scope = rememberCoroutineScope()
    var selectedRisk by remember { mutableStateOf<RiskDetail?>(null) }
    
    val riskDetails = listOf(
        RiskDetail(
            title = "Money & Loan Risk",
            subtitle = "Repaying loan on time & cash in hand",
            level = "Medium",
            levelColor = KalpaScreenColors.OrangeDark,
            levelBg = KalpaScreenColors.OrangeBadgeBg,
            description = "You have a safe 1.42x buffer to easily pay your ₹44,505 quarterly bank loan. Extra savings cover over 1 batch if sales get delayed.",
            actionText = "See loan repayment plan",
            icon = Icons.Filled.CurrencyRupee
        ),
        RiskDetail(
            title = "Market Prices",
            subtitle = "Seasonal price drops & vegetarian festivals",
            level = "Low to Medium",
            levelColor = KalpaScreenColors.TextSecondary,
            levelBg = KalpaScreenColors.PillGray,
            description = "Chicken prices fall during Shravan and Navratri fasting weeks. Direct supply contracts with highway dhabas keep prices steady.",
            actionText = "See festival pricing plan",
            icon = Icons.Filled.TrendingDown
        ),
        RiskDetail(
            title = "Disease & Farm Care",
            subtitle = "Vaccines & clean shed habits",
            level = "Medium-High",
            levelColor = KalpaScreenColors.DelayRed,
            levelBg = Color(0xFFFFE5E5),
            description = "Vaccinations need a strict routine. Following a basic vet logbook prevents common illness and avoids 4-6% chick loss.",
            actionText = "See chick vaccine checklist",
            icon = Icons.Filled.MedicalServices
        ),
        RiskDetail(
            title = "Rainy Season",
            subtitle = "Humid weather & damp floor bedding",
            level = "Moderate",
            levelColor = KalpaScreenColors.OrangeDark,
            levelBg = KalpaScreenColors.OrangeBadgeBg,
            description = "July and August rains make sawdust wet and smelly. Dusting dry lime powder on the shed floor keeps chicks healthy and dry.",
            actionText = "See dry floor steps",
            icon = Icons.Filled.WaterDrop
        ),
        RiskDetail(
            title = "Chicks & Feed Supply",
            subtitle = "Getting baby chicks & feed easily",
            level = "Low",
            levelColor = KalpaScreenColors.TextSecondary,
            levelBg = KalpaScreenColors.PillGray,
            description = "2 chick suppliers and a feed store are just 8 km away, so supplies will arrive on time with almost zero wait.",
            actionText = "See nearby suppliers",
            icon = Icons.Filled.LocalShipping
        ),
        RiskDetail(
            title = "Competition",
            subtitle = "Other local poultry sheds nearby",
            level = "Low",
            levelColor = KalpaScreenColors.TextSecondary,
            levelBg = KalpaScreenColors.PillGray,
            description = "Only 3 other small sheds exist within 7 km. Nearby market demand is large enough to easily buy all your chickens.",
            actionText = "See local market demand",
            icon = Icons.Filled.Storefront
        ),
        RiskDetail(
            title = "Electricity & Water",
            subtitle = "Power cuts, well water & fans",
            level = "Low",
            levelColor = KalpaScreenColors.TextSecondary,
            levelBg = KalpaScreenColors.PillGray,
            description = "A backup inverter handles village power cuts, and your own sweet-water borewell with a 1,500L tank keeps drinking water steady.",
            actionText = "See power & water setup",
            icon = Icons.Filled.ElectricBolt
        )
    )

    val blurRadius by androidx.compose.animation.core.animateDpAsState(targetValue = if (selectedRisk != null) 12.dp else 0.dp, label = "blur")
    Scaffold(
        modifier = if (blurRadius > 0.dp) Modifier.blur(blurRadius) else Modifier,
        containerColor = KalpaScreenColors.ScreenBackgroundCream,
        bottomBar = {
            RiskBottomBar(onContinueClick = onContinueClick)
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
        ) {
            KalpaTopBar(onBackClick = onBackClick, stepText = "Page 9 of 14")

            Column(modifier = Modifier.padding(horizontal = 20.dp)) {
                Spacer(Modifier.height(8.dp))

                Text(
                    text = "What Could Go Wrong?",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold
                )

                Spacer(Modifier.height(16.dp))

                // Checked against 4 project details banner
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = KalpaScreenColors.FieldGray,
                    modifier = Modifier.fillMaxWidth().clickable { /* Expand/collapse logic */ }
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = Icons.Filled.FactCheck,
                            contentDescription = null,
                            tint = KalpaScreenColors.OrangeDark,
                            modifier = Modifier.size(20.dp)
                        )
                        Spacer(Modifier.width(12.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = "Checked against 4 project details",
                                color = KalpaScreenColors.TextPrimary,
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold
                            )
                            Text(
                                text = "Tap to see previous review steps",
                                color = KalpaScreenColors.TextSecondary,
                                fontSize = 11.sp
                            )
                        }
                        Icon(
                            imageVector = Icons.Filled.KeyboardArrowDown,
                            contentDescription = null,
                            tint = KalpaScreenColors.TextSecondary
                        )
                    }
                }

                Spacer(Modifier.height(24.dp))

                Text(
                    text = "Things to Watch Out For",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold
                )
                
                Spacer(Modifier.height(12.dp))
                
                PriorityRisksCard()

                Spacer(Modifier.height(24.dp))

                Text(
                    text = "Detailed Risk Breakdown",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold
                )

                Spacer(Modifier.height(12.dp))

                // Compact Risk List
                riskDetails.forEach { risk ->
                    CompactRiskItem(risk = risk) {
                        selectedRisk = risk
                        scope.launch { sheetState.show() }
                    }
                    Spacer(Modifier.height(8.dp))
                }

                Spacer(Modifier.height(32.dp))
            }
        }
    }

    // Bottom Sheet for Detailed Risk
    if (selectedRisk != null) {
        ModalBottomSheet(
            onDismissRequest = {
                scope.launch { sheetState.hide() }.invokeOnCompletion {
                    if (!sheetState.isVisible) {
                        selectedRisk = null
                    }
                }
            },
            sheetState = sheetState,
            containerColor = KalpaScreenColors.ScreenBackgroundCream,
            dragHandle = { BottomSheetDefaults.DragHandle() }
        ) {
            selectedRisk?.let { risk ->
                RiskDetailSheet(risk = risk)
            }
        }
    }
}


@Composable
private fun PriorityRisksCard() {
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = KalpaScreenColors.CardWhite
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                    Icon(
                        imageVector = Icons.Filled.Security,
                        contentDescription = null,
                        tint = KalpaScreenColors.OrangeDark,
                        modifier = Modifier.size(18.dp)
                    )
                    Spacer(Modifier.width(8.dp))
                    Text(
                        text = "Priority Risks to Watch",
                        color = KalpaScreenColors.TextPrimary,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.weight(1f)
                    )
                }
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = KalpaScreenColors.OrangeBadgeBg
                ) {
                    Text(
                        text = "Ranked by urgency",
                        color = KalpaScreenColors.OrangeDark,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        maxLines = 1,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                    )
                }
            }
            
            Spacer(Modifier.height(16.dp))
            
            // Needs Active Care block
            Surface(
                shape = RoundedCornerShape(12.dp),
                color = Color(0xFFFFF5F5) // Very pale red
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                            Box(modifier = Modifier.size(6.dp).background(KalpaScreenColors.DelayRed, CircleShape))
                            Spacer(Modifier.width(6.dp))
                            Text(
                                text = "Needs Active Care",
                                color = KalpaScreenColors.DelayRed,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                        Text(
                            text = "2 key items",
                            color = KalpaScreenColors.DelayRed,
                            fontSize = 10.sp
                        )
                    }
                    Spacer(Modifier.height(8.dp))
                    Text(
                        text = "Rainy season dampness & Disease outbreak",
                        color = KalpaScreenColors.TextPrimary,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                    Spacer(Modifier.height(4.dp))
                    Text(
                        text = "Highest impact on flock health • Preventable with daily routine",
                        color = KalpaScreenColors.TextSecondary,
                        fontSize = 11.sp,
                        lineHeight = 16.sp
                    )
                }
            }
            
            Spacer(Modifier.height(12.dp))
            
            // Manageable with Planning block
            Surface(
                shape = RoundedCornerShape(12.dp),
                color = KalpaScreenColors.FieldGray
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                            Box(modifier = Modifier.size(6.dp).background(KalpaScreenColors.OrangeDark, CircleShape))
                            Spacer(Modifier.width(6.dp))
                            Text(
                                text = "Manageable with Planning",
                                color = KalpaScreenColors.OrangeDark,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                        Text(
                            text = "5 key items",
                            color = KalpaScreenColors.TextSecondary,
                            fontSize = 10.sp
                        )
                    }
                    Spacer(Modifier.height(8.dp))
                    Text(
                        text = "Market price dips, festive seasons & water supply",
                        color = KalpaScreenColors.TextPrimary,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                    Spacer(Modifier.height(4.dp))
                    Text(
                        text = "Normal business cycles • Covered by emergency buffer",
                        color = KalpaScreenColors.TextSecondary,
                        fontSize = 11.sp,
                        lineHeight = 16.sp
                    )
                }
            }
        }
    }
}

@Composable
private fun CompactRiskItem(risk: RiskDetail, onClick: () -> Unit) {
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
                    .background(KalpaScreenColors.OrangeBadgeBg, CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = risk.icon,
                    contentDescription = null,
                    tint = KalpaScreenColors.OrangeDark,
                    modifier = Modifier.size(20.dp)
                )
            }
            Spacer(Modifier.width(16.dp))
            
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = risk.title,
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold
                )
            }
            
            Spacer(Modifier.width(8.dp))
            
            Surface(
                shape = RoundedCornerShape(12.dp),
                color = risk.levelBg
            ) {
                Text(
                    text = risk.level,
                    color = risk.levelColor,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                )
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
private fun RiskDetailSheet(risk: RiskDetail) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 24.dp, vertical = 16.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .background(KalpaScreenColors.OrangeBadgeBg, CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = risk.icon,
                    contentDescription = null,
                    tint = KalpaScreenColors.OrangeDark,
                    modifier = Modifier.size(24.dp)
                )
            }
            Spacer(Modifier.width(16.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = risk.title,
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(2.dp))
                Text(
                    text = risk.subtitle,
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 12.sp
                )
            }
        }
        
        Spacer(Modifier.height(16.dp))
        
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = "Risk Level:",
                color = KalpaScreenColors.TextSecondary,
                fontSize = 14.sp
            )
            Spacer(Modifier.width(8.dp))
            Surface(
                shape = RoundedCornerShape(12.dp),
                color = risk.levelBg
            ) {
                Text(
                    text = risk.level,
                    color = risk.levelColor,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp)
                )
            }
        }
        
        Spacer(Modifier.height(24.dp))
        
        Text(
            text = risk.description,
            color = KalpaScreenColors.TextPrimary,
            fontSize = 15.sp,
            lineHeight = 22.sp
        )
        
        Spacer(Modifier.height(24.dp))
        
        Surface(
            shape = RoundedCornerShape(12.dp),
            color = KalpaScreenColors.PillGray,
            modifier = Modifier.fillMaxWidth().clickable { /* action */ }
        ) {
            Row(
                modifier = Modifier.padding(16.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = risk.actionText,
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold
                )
                Icon(
                    imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                    contentDescription = null,
                    tint = KalpaScreenColors.TextPrimary,
                    modifier = Modifier.size(16.dp)
                )
            }
        }
        
        Spacer(Modifier.height(32.dp))
    }
}

@Composable
private fun RiskBottomBar(onContinueClick: () -> Unit) {
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
                        text = "Continue",
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
fun EnterpriseRiskScreenPreview() {
    MaterialTheme {
        EnterpriseRiskScreen()
    }
}
