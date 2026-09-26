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
private data class EvalSummary(
    val title: String,
    val score: Int,
    val leftSubtitle: String,
    val rightSubtitle: String,
    val rightSubtitleColor: Color,
    val icon: ImageVector,
    val barColor: Color
)

private data class ProceedCondition(
    val category: String,
    val title: String,
    val shortTitle: String,
    val icon: ImageVector,
    val rootCause: String,
    val recommendedFix: String
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BusinessFeasibilityScreen(
    onBackClick: () -> Unit = {},
    onContinueClick: () -> Unit = {}
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val scope = rememberCoroutineScope()
    var selectedCondition by remember { mutableStateOf<ProceedCondition?>(null) }

    val evalSummaries = listOf(
        EvalSummary(
            title = "Market Demand",
            score = 82,
            leftSubtitle = "Buyer pull in Andal &\nDurgapur",
            rightSubtitle = "3,400 kg/day local\ndeficit",
            rightSubtitleColor = KalpaScreenColors.OrangeDark,
            icon = Icons.Filled.TrendingUp,
            barColor = KalpaScreenColors.OrangeDark
        ),
        EvalSummary(
            title = "Financial Health",
            score = 74,
            leftSubtitle = "Debt sustainability",
            rightSubtitle = "Safe 1.42x DSCR cover",
            rightSubtitleColor = KalpaScreenColors.OrangeDark,
            icon = Icons.Filled.AccountBalance,
            barColor = KalpaScreenColors.OrangeDark
        ),
        EvalSummary(
            title = "Entrepreneur Readiness",
            score = 71,
            leftSubtitle = "Prior work background",
            rightSubtitle = "Shed skills solid, vaccine gap",
            rightSubtitleColor = KalpaScreenColors.OrangeDark,
            icon = Icons.Filled.Handyman,
            barColor = KalpaScreenColors.OrangeDark
        ),
        EvalSummary(
            title = "Enterprise Risk",
            score = 63,
            leftSubtitle = "Flock mortality & climate\nsensitivity",
            rightSubtitle = "Manageable with 3\nsafeguards",
            rightSubtitleColor = KalpaScreenColors.TextPrimary,
            icon = Icons.Filled.Shield,
            barColor = KalpaScreenColors.TextMuted
        )
    )

    val conditions = listOf(
        ProceedCondition(
            category = "Readiness Condition",
            shortTitle = "Complete 3-day Brooder & Vac...",
            title = "Complete 3-day Brooder & Vaccination Training",
            icon = Icons.Filled.MedicalServices,
            rootCause = "Lack of formal training increases the risk of flock mortality during the critical first week.",
            recommendedFix = "Enroll in the free 3-day KVK Burdwan online certification. Present certificate to the bank officer."
        ),
        ProceedCondition(
            category = "Supply Chain",
            shortTitle = "Confirm Andal Hatchery Supply ...",
            title = "Confirm Andal Hatchery Supply Contract",
            icon = Icons.Filled.Inventory,
            rootCause = "Seasonal demand spikes can leave un-contracted farms without day-old chicks, delaying revenue.",
            recommendedFix = "Sign a standard advance-booking agreement with Andal Hatchery for 1,000 chicks per cycle."
        ),
        ProceedCondition(
            category = "Financial Risk",
            shortTitle = "Keep ₹25,000 Working-Capital ...",
            title = "Keep ₹25,000 Working-Capital Reserve",
            icon = Icons.Filled.AccountBalanceWallet,
            rootCause = "Unexpected feed price hikes or delayed buyer payments can cause a cash crunch before the loan clears.",
            recommendedFix = "Maintain a minimum liquid balance of ₹25,000 in your primary farm account at all times."
        )
    )

    val blurRadius by androidx.compose.animation.core.animateDpAsState(targetValue = if (selectedCondition != null) 12.dp else 0.dp, label = "blur")
    Scaffold(
        modifier = if (blurRadius > 0.dp) Modifier.blur(blurRadius) else Modifier,
        containerColor = KalpaScreenColors.ScreenBackgroundCream,
        bottomBar = {
            FeasibilityBottomBar(onContinueClick = onContinueClick)
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
        ) {
            KalpaTopBar(onBackClick = onBackClick, stepText = "Page 10 of 14")

            Column(modifier = Modifier.padding(horizontal = 20.dp)) {
                Spacer(Modifier.height(8.dp))

                Text(
                    text = "Business Feasibility\nAssessment",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 26.sp,
                    fontWeight = FontWeight.Bold,
                    lineHeight = 32.sp
                )
                Spacer(Modifier.height(8.dp))
                Text(
                    text = "KALPA has brought together your market, money, readiness, and operational risks into a verified verdict.",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 14.sp,
                    lineHeight = 20.sp
                )

                Spacer(Modifier.height(24.dp))

                VerdictCard()

                Spacer(Modifier.height(24.dp))

                Text(
                    text = "Evaluation Summary",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )

                Spacer(Modifier.height(16.dp))

                // Dense Evaluation Summary List
                Surface(
                    shape = RoundedCornerShape(16.dp),
                    color = KalpaScreenColors.CardWhite
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        evalSummaries.forEachIndexed { index, eval ->
                            EvalSummaryItem(eval)
                            if (index < evalSummaries.size - 1) {
                                HorizontalDivider(
                                    modifier = Modifier.padding(vertical = 12.dp),
                                    color = KalpaScreenColors.Divider
                                )
                            }
                        }
                    }
                }

                Spacer(Modifier.height(24.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.Bottom
                ) {
                    Text(
                        text = "Conditions to Proceed (3)",
                        color = KalpaScreenColors.TextPrimary,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "Action Required",
                        color = KalpaScreenColors.OrangeDark,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                }

                Spacer(Modifier.height(8.dp))
                Text(
                    text = "Tap each condition to inspect root cause rationale and recommended local fixes.",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 13.sp,
                    lineHeight = 18.sp
                )

                Spacer(Modifier.height(16.dp))

                conditions.forEach { condition ->
                    ConditionItem(condition) {
                        selectedCondition = condition
                        scope.launch { sheetState.show() }
                    }
                    Spacer(Modifier.height(12.dp))
                }

                Spacer(Modifier.height(32.dp))
            }
        }
    }

    // Bottom Sheet for Detailed Condition
    if (selectedCondition != null) {
        ModalBottomSheet(
            onDismissRequest = {
                scope.launch { sheetState.hide() }.invokeOnCompletion {
                    if (!sheetState.isVisible) {
                        selectedCondition = null
                    }
                }
            },
            sheetState = sheetState,
            containerColor = KalpaScreenColors.ScreenBackgroundCream,
            dragHandle = { BottomSheetDefaults.DragHandle() }
        ) {
            selectedCondition?.let { condition ->
                ConditionDetailSheet(condition = condition)
            }
        }
    }
}



@Composable
private fun VerdictCard() {
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
                Column(modifier = Modifier.weight(1f).padding(end = 12.dp)) {
                    Text(
                        text = "VERDICT STATUS",
                        color = KalpaScreenColors.TextSecondary,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.5.sp
                    )
                    Spacer(Modifier.height(8.dp))
                    Surface(
                        shape = RoundedCornerShape(16.dp),
                        color = KalpaScreenColors.Orange // matches "#d48700"
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Filled.CheckCircleOutline,
                                contentDescription = null,
                                tint = KalpaScreenColors.CardWhite,
                                modifier = Modifier.size(16.dp)
                            )
                            Spacer(Modifier.width(6.dp))
                            Text(
                                text = "VIABLE WITH CONDITIONS",
                                color = KalpaScreenColors.CardWhite,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                }
                
                // Pale orange decorative circle
                Box(
                    modifier = Modifier
                        .size(48.dp)
                        .background(KalpaScreenColors.OrangeBadgeBg, CircleShape)
                )
            }
            
            Spacer(Modifier.height(16.dp))
            
            Text(
                text = "Market demand is strong and financing is structurally sound. Address 3 readiness and biosecurity conditions before disbursing loan capital and placing day-old chicks.",
                color = KalpaScreenColors.TextPrimary,
                fontSize = 14.sp,
                lineHeight = 22.sp
            )
            
            Spacer(Modifier.height(16.dp))
            
            Row(verticalAlignment = Alignment.Top) {
                Icon(
                    imageVector = Icons.Filled.Info,
                    contentDescription = null,
                    tint = KalpaScreenColors.OrangeDark,
                    modifier = Modifier.size(18.dp).padding(top = 2.dp)
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    text = "Safe for PMEGP bank subsidy filing once conditions are cleared.",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 12.sp,
                    lineHeight = 16.sp,
                    modifier = Modifier.weight(1f)
                )
            }
        }
    }
}

@Composable
private fun EvalSummaryItem(eval: EvalSummary) {
    Column {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                Icon(
                    imageVector = eval.icon,
                    contentDescription = null,
                    tint = KalpaScreenColors.TextSecondary,
                    modifier = Modifier.size(18.dp)
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    text = eval.title,
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.SemiBold
                )
            }
            Row(verticalAlignment = Alignment.Bottom) {
                Text(
                    text = "${eval.score}",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "/100",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 12.sp
                )
            }
        }
        
        Spacer(Modifier.height(8.dp))
        
        // Progress Bar
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .height(6.dp)
                .clip(RoundedCornerShape(3.dp))
                .background(KalpaScreenColors.PillGray)
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth(eval.score / 100f)
                    .fillMaxHeight()
                    .background(eval.barColor)
            )
        }
        
        Spacer(Modifier.height(8.dp))
        
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.Top
        ) {
            Text(
                text = eval.leftSubtitle,
                color = KalpaScreenColors.TextSecondary,
                fontSize = 11.sp,
                lineHeight = 16.sp,
                modifier = Modifier.weight(1f)
            )
            Spacer(Modifier.width(16.dp))
            Text(
                text = eval.rightSubtitle,
                color = eval.rightSubtitleColor,
                fontSize = 11.sp,
                fontWeight = FontWeight.SemiBold,
                lineHeight = 16.sp,
                modifier = Modifier.weight(1f),
                textAlign = androidx.compose.ui.text.style.TextAlign.Right
            )
        }
    }
}

@Composable
private fun ConditionItem(condition: ProceedCondition, onClick: () -> Unit) {
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
                    imageVector = condition.icon,
                    contentDescription = null,
                    tint = KalpaScreenColors.OrangeDark,
                    modifier = Modifier.size(20.dp)
                )
            }
            Spacer(Modifier.width(16.dp))
            
            Column(modifier = Modifier.weight(1f)) {
                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = KalpaScreenColors.PillGray
                ) {
                    Text(
                        text = condition.category,
                        color = KalpaScreenColors.TextSecondary,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }
                Spacer(Modifier.height(4.dp))
                Text(
                    text = condition.shortTitle,
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold
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
private fun ConditionDetailSheet(condition: ProceedCondition) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 24.dp, vertical = 16.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .background(KalpaScreenColors.PillGray, CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = condition.icon,
                    contentDescription = null,
                    tint = KalpaScreenColors.OrangeDark,
                    modifier = Modifier.size(24.dp)
                )
            }
            Spacer(Modifier.width(16.dp))
            Column(modifier = Modifier.weight(1f)) {
                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = KalpaScreenColors.OrangeBadgeBg
                ) {
                    Text(
                        text = condition.category,
                        color = KalpaScreenColors.OrangeDark,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                    )
                }
                Spacer(Modifier.height(4.dp))
                Text(
                    text = condition.title,
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold,
                    lineHeight = 24.sp
                )
            }
        }
        
        Spacer(Modifier.height(24.dp))
        
        Text(
            text = "Root Cause Rationale",
            color = KalpaScreenColors.TextSecondary,
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold,
            letterSpacing = 0.5.sp
        )
        Spacer(Modifier.height(8.dp))
        Surface(
            shape = RoundedCornerShape(12.dp),
            color = KalpaScreenColors.CardWhite,
            border = androidx.compose.foundation.BorderStroke(1.dp, KalpaScreenColors.Divider),
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(
                text = condition.rootCause,
                color = KalpaScreenColors.TextPrimary,
                fontSize = 14.sp,
                lineHeight = 22.sp,
                modifier = Modifier.padding(16.dp)
            )
        }
        
        Spacer(Modifier.height(16.dp))
        
        Text(
            text = "Recommended Local Fix",
            color = KalpaScreenColors.TextSecondary,
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold,
            letterSpacing = 0.5.sp
        )
        Spacer(Modifier.height(8.dp))
        Surface(
            shape = RoundedCornerShape(12.dp),
            color = KalpaScreenColors.OrangeBadgeBg,
            modifier = Modifier.fillMaxWidth()
        ) {
            Row(modifier = Modifier.padding(16.dp), verticalAlignment = Alignment.Top) {
                Icon(
                    imageVector = Icons.Filled.CheckCircle,
                    contentDescription = null,
                    tint = KalpaScreenColors.OrangeDark,
                    modifier = Modifier.size(20.dp).padding(top = 2.dp)
                )
                Spacer(Modifier.width(12.dp))
                Text(
                    text = condition.recommendedFix,
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 14.sp,
                    lineHeight = 22.sp,
                    modifier = Modifier.weight(1f)
                )
            }
        }
        
        Spacer(Modifier.height(32.dp))
    }
}

@Composable
private fun FeasibilityBottomBar(onContinueClick: () -> Unit) {
    Surface(color = KalpaScreenColors.ScreenBackgroundCream) {
        Column(modifier = Modifier.padding(20.dp)) {
            Button(
                onClick = onContinueClick,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(54.dp),
                shape = RoundedCornerShape(27.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = KalpaScreenColors.Orange // Matches primary
                )
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = "Generate Business Plan",
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
fun BusinessFeasibilityScreenPreview() {
    MaterialTheme {
        BusinessFeasibilityScreen()
    }
}
