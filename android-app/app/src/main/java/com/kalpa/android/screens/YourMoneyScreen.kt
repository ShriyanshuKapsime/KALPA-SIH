package com.kalpa.android.screens

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
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
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.LocalDrink
import androidx.compose.material.icons.filled.WaterDrop
import androidx.compose.material.icons.filled.Tune
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay

@Composable
fun YourMoneyScreen(
    onBackClick: () -> Unit = {},
    onContinueClick: () -> Unit = {}
) {
    // Basic state for the tab
    var selectedTab by remember { mutableStateOf(0) }
    
    // Animation for progress bar on load
    var progressAnim by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) {
        delay(100)
        progressAnim = true
    }

    Scaffold(
        containerColor = KalpaScreenColors.ScreenBackgroundCream,
        bottomBar = {
            YourMoneyBottomBar(onContinueClick = onContinueClick)
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
        ) {
            KalpaTopBar(onBackClick = onBackClick, stepText = "Page 7 of 14")
            
            Column(modifier = Modifier.padding(horizontal = 20.dp)) {
                Spacer(Modifier.height(8.dp))
                
                Text(
                    text = "Your money & loan plan",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "For 1,000 birds broiler farm in Banskopa",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 14.sp
                )
                
                Spacer(Modifier.height(20.dp))
                
                TotalCostCard()
                
                Spacer(Modifier.height(16.dp))
                
                TabsRow(
                    selectedTab = selectedTab,
                    onTabSelected = { selectedTab = it }
                )
                
                Spacer(Modifier.height(24.dp))
                
                WhoPaysWhatSection(isAnimated = progressAnim)
                
                Spacer(Modifier.height(24.dp))
                
                WhereMoneyGoesSection()
                
                Spacer(Modifier.height(20.dp))
                
                TryAnotherLoanCard()
                
                Spacer(Modifier.height(32.dp))
            }
        }
    }
}


@Composable
private fun TotalCostCard() {
    Surface(
        shape = RoundedCornerShape(16.dp),
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
                        text = "TOTAL COST TO START",
                        color = KalpaScreenColors.TextSecondary,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.5.sp
                    )
                    Spacer(Modifier.height(2.dp))
                    Text(
                        text = "₹10,00,000",
                        color = KalpaScreenColors.TextPrimary,
                        fontSize = 28.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text(
                        text = "FARM SIZE",
                        color = KalpaScreenColors.TextSecondary,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.5.sp
                    )
                    Spacer(Modifier.height(2.dp))
                    Text(
                        text = "1,000 Birds /",
                        color = KalpaScreenColors.TextPrimary,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium
                    )
                    Text(
                        text = "cycle",
                        color = KalpaScreenColors.TextPrimary,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
            }
            
            Spacer(Modifier.height(16.dp))
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                // Savings
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = KalpaScreenColors.ScreenBackgroundCream,
                    modifier = Modifier.weight(1f)
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text(
                            text = "Your savings (10%)",
                            color = KalpaScreenColors.TextSecondary,
                            fontSize = 12.sp
                        )
                        Spacer(Modifier.height(4.dp))
                        Text(
                            text = "₹1,00,000",
                            color = KalpaScreenColors.OrangeDark,
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(Modifier.height(4.dp))
                        Text(
                            text = "Money you put in",
                            color = KalpaScreenColors.TextMuted,
                            fontSize = 11.sp
                        )
                    }
                }
                
                // Loan
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = KalpaScreenColors.ScreenBackgroundCream,
                    modifier = Modifier.weight(1f)
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text(
                            text = "Bank loan needed (90%)",
                            color = KalpaScreenColors.TextSecondary,
                            fontSize = 12.sp
                        )
                        Spacer(Modifier.height(4.dp))
                        Text(
                            text = "₹9,00,000",
                            color = KalpaScreenColors.TextPrimary,
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(Modifier.height(4.dp))
                        Text(
                            text = "Loan from bank",
                            color = KalpaScreenColors.TextMuted,
                            fontSize = 11.sp
                        )
                    }
                }
            }
            
            Spacer(Modifier.height(16.dp))
            
            Surface(
                shape = RoundedCornerShape(12.dp),
                color = KalpaScreenColors.OrangeBadgeBg,
                border = androidx.compose.foundation.BorderStroke(1.dp, KalpaScreenColors.StepDoneBg)
            ) {
                Row(modifier = Modifier.padding(12.dp), verticalAlignment = Alignment.Top) {
                    Icon(
                        imageVector = Icons.Filled.CheckCircle,
                        contentDescription = null,
                        tint = KalpaScreenColors.Orange,
                        modifier = Modifier.size(20.dp)
                    )
                    Spacer(Modifier.width(10.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = "Can you get this loan? Yes, easily.",
                            color = KalpaScreenColors.TextPrimary,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(Modifier.height(2.dp))
                        Text(
                            text = "Eligible for PMEGP government subsidy with standard approved rates for 1,000 bird sheds.",
                            color = KalpaScreenColors.TextSecondary,
                            fontSize = 12.sp,
                            lineHeight = 16.sp
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun TabsRow(selectedTab: Int, onTabSelected: (Int) -> Unit) {
    val tabs = listOf("Money", "Loan", "Scheme")
    
    Surface(
        shape = RoundedCornerShape(24.dp),
        color = KalpaScreenColors.PillGray,
        modifier = Modifier.fillMaxWidth().height(44.dp)
    ) {
        Row(
            modifier = Modifier.padding(4.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            tabs.forEachIndexed { index, title ->
                val isSelected = selectedTab == index
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight()
                        .clip(RoundedCornerShape(20.dp))
                        .background(if (isSelected) KalpaScreenColors.CardWhite else Color.Transparent)
                        .clickable { onTabSelected(index) },
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = title,
                        color = if (isSelected) KalpaScreenColors.TextPrimary else KalpaScreenColors.TextSecondary,
                        fontSize = 14.sp,
                        fontWeight = if (isSelected) FontWeight.SemiBold else FontWeight.Medium
                    )
                }
            }
        }
    }
}

@Composable
private fun WhoPaysWhatSection(isAnimated: Boolean) {
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = KalpaScreenColors.CardWhite
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Bottom
            ) {
                Text(
                    text = "Who pays what",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "Total: ₹10,00,000",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 12.sp
                )
            }
            
            Spacer(Modifier.height(16.dp))
            
            // Progress Bar
            val savingsWeight = 0.10f
            val grantWeight = 0.25f
            val loanWeight = 0.65f
            
            val animSavings by animateFloatAsState(
                targetValue = if (isAnimated) savingsWeight else 0f, 
                animationSpec = tween(800)
            )
            val animGrant by animateFloatAsState(
                targetValue = if (isAnimated) grantWeight else 0f, 
                animationSpec = tween(800, delayMillis = 200)
            )
            val animLoan by animateFloatAsState(
                targetValue = if (isAnimated) loanWeight else 0f, 
                animationSpec = tween(800, delayMillis = 400)
            )

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(12.dp)
                    .clip(RoundedCornerShape(6.dp))
                    .background(KalpaScreenColors.Divider)
            ) {
                if (animSavings > 0f) {
                    Box(modifier = Modifier.weight(animSavings).fillMaxHeight().background(KalpaScreenColors.ProfileBrown))
                }
                if (animGrant > 0f) {
                    Box(modifier = Modifier.weight(animGrant).fillMaxHeight().background(KalpaScreenColors.TextMuted))
                }
                if (animLoan > 0f) {
                    Box(modifier = Modifier.weight(animLoan).fillMaxHeight().background(KalpaScreenColors.Orange))
                }
                // Fill the rest if animation is ongoing
                val remaining = 1f - (animSavings + animGrant + animLoan)
                if (remaining > 0.01f) {
                    Box(modifier = Modifier.weight(remaining).fillMaxHeight().background(Color.Transparent))
                }
            }
            
            Spacer(Modifier.height(12.dp))
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                LegendItem(color = KalpaScreenColors.ProfileBrown, label = "Your savings", amount = "₹1.00L (10%)")
                LegendItem(color = KalpaScreenColors.TextMuted, label = "Govt grant", amount = "₹2.50L (25%)")
                LegendItem(color = KalpaScreenColors.Orange, label = "Bank loan", amount = "₹6.50L (65%)")
            }
            
            Spacer(Modifier.height(16.dp))
            
            Surface(
                shape = RoundedCornerShape(12.dp),
                color = KalpaScreenColors.ScreenBackgroundCream // Light beige
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth().padding(12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Filled.CheckCircle,
                            contentDescription = null,
                            tint = KalpaScreenColors.OrangeDark,
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(Modifier.width(8.dp))
                        Text(
                            text = "Any extra money\nneeded?",
                            color = KalpaScreenColors.TextPrimary,
                            fontSize = 12.sp,
                            lineHeight = 16.sp
                        )
                    }
                    Text(
                        text = "₹0 (Fully\nCovered)",
                        color = KalpaScreenColors.TextPrimary,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold,
                        textAlign = androidx.compose.ui.text.style.TextAlign.Right,
                        lineHeight = 16.sp
                    )
                }
            }
        }
    }
}

@Composable
private fun LegendItem(color: Color, label: String, amount: String) {
    Column {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(modifier = Modifier.size(8.dp).background(color, CircleShape))
            Spacer(Modifier.width(4.dp))
            Text(
                text = label,
                color = KalpaScreenColors.TextSecondary,
                fontSize = 11.sp
            )
        }
        Spacer(Modifier.height(2.dp))
        Text(
            text = amount,
            color = KalpaScreenColors.TextPrimary,
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold
        )
    }
}

@Composable
private fun WhereMoneyGoesSection() {
    Column {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.Bottom
        ) {
            Text(
                text = "Where will the money go?",
                color = KalpaScreenColors.TextPrimary,
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = "4 Simple Parts",
                color = KalpaScreenColors.TextSecondary,
                fontSize = 12.sp
            )
        }
        
        Spacer(Modifier.height(12.dp))
        
        CostBreakdownItem(
            icon = Icons.Filled.Home,
            title = "1. Shed construction",
            desc = "Concrete floor, steel pillars, wire mesh",
            amount = "₹4,80,000"
        )
        Spacer(Modifier.height(8.dp))
        CostBreakdownItem(
            icon = Icons.Filled.Build,
            title = "2. Equipment",
            desc = "Drinkers, feeders, cages, brooding heat lamps",
            amount = "₹1,70,000"
        )
        Spacer(Modifier.height(8.dp))
        CostBreakdownItem(
            icon = Icons.Filled.LocalDrink,
            title = "3. Feed & chicks",
            desc = "1,000 day-old chicks + starter/finisher feed",
            amount = "₹2,50,000"
        )
        Spacer(Modifier.height(8.dp))
        CostBreakdownItem(
            icon = Icons.Filled.WaterDrop,
            title = "4. Water & power setup",
            desc = "Borewell connection, water pump & inverter",
            amount = "₹1,00,000"
        )
    }
}

@Composable
private fun CostBreakdownItem(
    icon: ImageVector,
    title: String,
    desc: String,
    amount: String
) {
    Surface(
        shape = RoundedCornerShape(12.dp),
        color = KalpaScreenColors.CardWhite
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
                    imageVector = icon,
                    contentDescription = null,
                    tint = KalpaScreenColors.OrangeDark,
                    modifier = Modifier.size(20.dp)
                )
            }
            Spacer(Modifier.width(16.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = title,
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(2.dp))
                Text(
                    text = desc,
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 12.sp,
                    lineHeight = 16.sp
                )
            }
            Spacer(Modifier.width(8.dp))
            Text(
                text = amount,
                color = KalpaScreenColors.TextPrimary,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

@Composable
private fun TryAnotherLoanCard() {
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = KalpaScreenColors.CardWhite,
        modifier = Modifier.clickable { /* TODO */ }
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
                    imageVector = Icons.Filled.Tune,
                    contentDescription = null,
                    tint = KalpaScreenColors.OrangeDark,
                    modifier = Modifier.size(20.dp)
                )
            }
            Spacer(Modifier.width(16.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "Try another loan amount",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(2.dp))
                Text(
                    text = "Adjust margin, outlay, or tenure to preview EMIs instantly",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 12.sp,
                    lineHeight = 16.sp
                )
            }
            Icon(
                imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                contentDescription = null,
                tint = KalpaScreenColors.OrangeDark
            )
        }
    }
}

@Composable
private fun YourMoneyBottomBar(onContinueClick: () -> Unit) {
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
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = "Continue",
                            color = Color.White,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(Modifier.width(4.dp))
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(16.dp)
                        )
                    }
                    Text(
                        text = "Next: Entrepreneur Readiness",
                        color = KalpaScreenColors.OrangeBadgeBg,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
            }
        }
    }
}

@Preview(showBackground = true, widthDp = 390, heightDp = 1200)
@Composable
fun YourMoneyScreenPreview() {
    MaterialTheme {
        YourMoneyScreen()
    }
}
