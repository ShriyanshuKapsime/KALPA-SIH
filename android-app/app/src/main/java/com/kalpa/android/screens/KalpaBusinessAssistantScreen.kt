package com.kalpa.android.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun KalpaBusinessAssistantScreen(
    onBackClick: () -> Unit = {},
    onContinueClick: () -> Unit = {} // Added to fulfill routing flow if needed
) {
    Scaffold(
        containerColor = KalpaScreenColors.ScreenBackgroundCream,
        bottomBar = {
            AssistantBottomBar(onContinueClick = onContinueClick)
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            KalpaTopBar(onBackClick = onBackClick, stepText = "Page 13 of 14")
            
            Column(modifier = Modifier.padding(horizontal = 16.dp)) {
                Text(
                    text = "Ask about your business, market, money or plan.",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 14.sp
                )
                
                Spacer(Modifier.height(16.dp))
                
                ActiveContextCard()
                
                Spacer(Modifier.height(16.dp))
            }
            
            QuickPromptsRow()
            
            Spacer(Modifier.height(16.dp))
            
            // Chat Area
            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .padding(horizontal = 16.dp),
                contentPadding = PaddingValues(bottom = 16.dp)
            ) {
                item {
                    UserMessage(
                        text = "Why is my DSCR low in the first quarter?",
                        time = "10:42 AM"
                    )
                    Spacer(Modifier.height(24.dp))
                }
                
                item {
                    AgentMessageHeader()
                    Spacer(Modifier.height(8.dp))
                    AgentMessageCard()
                }
            }
        }
    }
}



@Composable
private fun ActiveContextCard() {
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = KalpaScreenColors.CardWhite,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(modifier = Modifier.size(8.dp).background(KalpaScreenColors.OrangeDark, CircleShape))
                Spacer(Modifier.width(8.dp))
                Text(
                    text = "1,000 Broiler Poultry Farm (Banskopa)",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold
                )
            }
            Spacer(Modifier.height(8.dp))
            Row(verticalAlignment = Alignment.Top) {
                Icon(
                    imageVector = Icons.Filled.FactCheck,
                    contentDescription = null,
                    tint = KalpaScreenColors.OrangeDark,
                    modifier = Modifier.size(16.dp).padding(top = 2.dp)
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    text = "Case loaded: DPR, Bank Loan, Risk engine synced",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 12.sp,
                    modifier = Modifier.weight(1f),
                    lineHeight = 16.sp
                )
                Spacer(Modifier.width(8.dp))
                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = KalpaScreenColors.OrangeBadgeBg
                ) {
                    Text(
                        text = "₹10.0L\nOutlay",
                        color = KalpaScreenColors.OrangeDark,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        lineHeight = 14.sp
                    )
                }
            }
        }
    }
}

@Composable
private fun QuickPromptsRow() {
    val prompts = listOf(
        Pair("Finance", "Why is my DSCR low?"),
        Pair("Readiness", "What to do about training?")
    )
    
    LazyRow(
        contentPadding = PaddingValues(horizontal = 16.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(prompts) { (tag, text) ->
            Surface(
                shape = RoundedCornerShape(20.dp),
                color = KalpaScreenColors.CardWhite,
                border = androidx.compose.foundation.BorderStroke(1.dp, KalpaScreenColors.Divider)
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Surface(
                        shape = RoundedCornerShape(8.dp),
                        color = if (tag == "Finance") KalpaScreenColors.OrangeBadgeBg else KalpaScreenColors.PillGray
                    ) {
                        Text(
                            text = tag,
                            color = if (tag == "Finance") KalpaScreenColors.OrangeDark else KalpaScreenColors.TextSecondary,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                    Spacer(Modifier.width(8.dp))
                    Text(
                        text = text,
                        color = KalpaScreenColors.TextPrimary,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }
        }
    }
}

@Composable
private fun UserMessage(text: String, time: String) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.End
    ) {
        Surface(
            shape = RoundedCornerShape(
                topStart = 16.dp,
                topEnd = 16.dp,
                bottomStart = 16.dp,
                bottomEnd = 4.dp
            ),
            color = KalpaScreenColors.PillGray
        ) {
            Text(
                text = text,
                color = KalpaScreenColors.TextPrimary,
                fontSize = 15.sp,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp)
            )
        }
        Spacer(Modifier.height(4.dp))
        Text(
            text = "$time • You",
            color = KalpaScreenColors.TextSecondary,
            fontSize = 11.sp
        )
    }
}

@Composable
private fun AgentMessageHeader() {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(
            modifier = Modifier
                .size(32.dp)
                .background(KalpaScreenColors.OrangeDark, CircleShape),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = "K",
                color = Color.White,
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold
            )
        }
        Spacer(Modifier.width(12.dp))
        Text(
            text = "KALPA Business\nAdvisor",
            color = KalpaScreenColors.TextPrimary,
            fontSize = 13.sp,
            fontWeight = FontWeight.Bold,
            lineHeight = 16.sp,
            modifier = Modifier.weight(1f).padding(end = 8.dp)
        )
        Spacer(Modifier.width(16.dp))
        Text(
            text = "• Grounded in PMEGP\n  Model",
            color = KalpaScreenColors.TextSecondary,
            fontSize = 11.sp,
            lineHeight = 14.sp,
            modifier = Modifier.weight(1f)
        )
    }
}

@Composable
private fun AgentMessageCard() {
    Surface(
        shape = RoundedCornerShape(
            topStart = 4.dp,
            topEnd = 24.dp,
            bottomStart = 24.dp,
            bottomEnd = 24.dp
        ),
        color = KalpaScreenColors.CardWhite
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            // 1. DIRECT ANSWER
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(modifier = Modifier.size(width = 4.dp, height = 14.dp).background(KalpaScreenColors.OrangeDark, RoundedCornerShape(2.dp)))
                Spacer(Modifier.width(8.dp))
                Text(
                    text = "1. THE DIRECT ANSWER",
                    color = KalpaScreenColors.OrangeDark,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 0.5.sp
                )
            }
            Spacer(Modifier.height(8.dp))
            Text(
                text = buildAnnotatedString {
                    append("Your Year 1 Q1 Debt Service Coverage Ratio is ")
                    withStyle(style = SpanStyle(fontWeight = FontWeight.Bold, color = KalpaScreenColors.OrangeDark)) {
                        append("1.18x")
                    }
                    append(" because your initial flock harvest cycle spans 42-45 days. This creates a temporary cash inflow lag while feed purchases and chick placement costs occur on Day 1.")
                },
                color = KalpaScreenColors.TextPrimary,
                fontSize = 14.sp,
                lineHeight = 22.sp
            )
            
            Spacer(Modifier.height(20.dp))
            
            // 2. WHAT IT MEANS FOR THE BANK
            Surface(
                shape = RoundedCornerShape(12.dp),
                color = KalpaScreenColors.ScreenBackgroundCream // Slightly tinted
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(modifier = Modifier.size(width = 4.dp, height = 14.dp).background(Color(0xFF8C5A2B), RoundedCornerShape(2.dp)))
                        Spacer(Modifier.width(8.dp))
                        Text(
                            text = "2. WHAT IT MEANS FOR THE BANK",
                            color = Color(0xFF8C5A2B), // Brownish
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 0.5.sp
                        )
                    }
                    Spacer(Modifier.height(8.dp))
                    Text(
                        text = buildAnnotatedString {
                            append("Lenders prefer 1.30x-1.50x. While your full annual average is a resilient ")
                            withStyle(style = SpanStyle(fontWeight = FontWeight.Bold)) {
                                append("1.62x")
                            }
                            append(", tight Q1 margins leave little cushion if bird mortality rises above 4% or Banskopa mandi prices dip below ₹88/kg live weight.")
                        },
                        color = KalpaScreenColors.TextSecondary,
                        fontSize = 13.sp,
                        lineHeight = 20.sp
                    )
                }
            }
            
            Spacer(Modifier.height(20.dp))
            
            // 3. ACTIONABLE STEPS
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(modifier = Modifier.size(width = 4.dp, height = 14.dp).background(KalpaScreenColors.TextSecondary, RoundedCornerShape(2.dp)))
                Spacer(Modifier.width(8.dp))
                Text(
                    text = "3. ACTIONABLE STEPS FOR YOU",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 0.5.sp
                )
            }
            Spacer(Modifier.height(12.dp))
            ActionableStep(
                text = buildAnnotatedString {
                    append("Reserve ")
                    withStyle(style = SpanStyle(fontWeight = FontWeight.Bold)) {
                        append("₹45,000")
                    }
                    append(" working capital buffer directly from your PMEGP subsidy advance.")
                }
            )
            ActionableStep(
                text = buildAnnotatedString {
                    append("Stagger bird batch arrivals by 12-15 days to convert single lump-sum sales into predictable bi-weekly cashflow.")
                }
            )
            ActionableStep(
                text = buildAnnotatedString {
                    append("Apply for a standard 3-month principal moratorium during loan disbursement at your bank branch.")
                }
            )
            
            Spacer(Modifier.height(24.dp))
            
            // VERIFIED DPR REFERENCES
            Text(
                text = "VERIFIED DPR REFERENCES",
                color = KalpaScreenColors.TextSecondary,
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 0.5.sp
            )
            Spacer(Modifier.height(12.dp))
            
            ReferenceChip(icon = Icons.Filled.BarChart, text = "See Finance Details (DSCR 1.18x) →", isPrimary = true)
            ReferenceChip(icon = Icons.Filled.Storefront, text = "Banskopa Mandi Data →")
            ReferenceChip(icon = Icons.Filled.Description, text = "DPR Section 4.2 →")
        }
    }
}

@Composable
private fun ActionableStep(text: androidx.compose.ui.text.AnnotatedString) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp),
        verticalAlignment = Alignment.Top
    ) {
        Icon(
            imageVector = Icons.Filled.CheckCircleOutline,
            contentDescription = null,
            tint = KalpaScreenColors.OrangeDark,
            modifier = Modifier.size(18.dp).padding(top = 2.dp)
        )
        Spacer(Modifier.width(12.dp))
        Text(
            text = text,
            color = KalpaScreenColors.TextPrimary,
            fontSize = 13.sp,
            lineHeight = 20.sp,
            modifier = Modifier.weight(1f)
        )
    }
}

@Composable
private fun ReferenceChip(icon: ImageVector, text: String, isPrimary: Boolean = false) {
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = if (isPrimary) KalpaScreenColors.OrangeBadgeBg else KalpaScreenColors.PillGray,
        modifier = Modifier.padding(bottom = 8.dp)
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = if (isPrimary) KalpaScreenColors.OrangeDark else KalpaScreenColors.TextSecondary,
                modifier = Modifier.size(14.dp)
            )
            Spacer(Modifier.width(8.dp))
            Text(
                text = text,
                color = if (isPrimary) KalpaScreenColors.OrangeDark else KalpaScreenColors.TextPrimary,
                fontSize = 11.sp,
                fontWeight = FontWeight.SemiBold
            )
        }
    }
}

@Composable
private fun AssistantBottomBar(onContinueClick: () -> Unit = {}) {
    Surface(
        color = KalpaScreenColors.ScreenBackgroundCream,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(modifier = Modifier.size(6.dp).background(KalpaScreenColors.OrangeDark, CircleShape))
                Spacer(Modifier.width(8.dp))
                Text(
                    text = "Tap mic to speak in Hindi or English",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 12.sp
                )
            }
            Spacer(Modifier.height(12.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(52.dp)
                        .background(KalpaScreenColors.OrangeDark, CircleShape),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Filled.Mic,
                        contentDescription = "Microphone",
                        tint = Color.White,
                        modifier = Modifier.size(24.dp)
                    )
                }
                
                Spacer(Modifier.width(12.dp))
                
                Surface(
                    modifier = Modifier.weight(1f).height(52.dp),
                    shape = RoundedCornerShape(26.dp),
                    color = KalpaScreenColors.CardWhite
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 16.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Ask KALPA about loan, buyers, risk",
                            color = KalpaScreenColors.TextSecondary,
                            fontSize = 14.sp,
                            modifier = Modifier.weight(1f),
                            maxLines = 1,
                            overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis
                        )
                    }
                }
                
                Spacer(Modifier.width(12.dp))
                
                Surface(
                    modifier = Modifier.size(52.dp),
                    shape = CircleShape,
                    color = KalpaScreenColors.ScreenBackgroundCream // Blend in or use PillGray
                ) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.Send,
                        contentDescription = "Send",
                        tint = Color(0xFF8C5A2B), // Brownish
                        modifier = Modifier.padding(14.dp)
                    )
                }
            }
            Spacer(Modifier.height(16.dp))
            Button(
                onClick = onContinueClick,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(54.dp),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.buttonColors(containerColor = KalpaScreenColors.Orange)
            ) {
                Text(
                    text = "Go to Growth Manager",
                    color = Color.White,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}

@Preview
@Composable
fun KalpaBusinessAssistantScreenPreview() {
    MaterialTheme {
        KalpaBusinessAssistantScreen()
    }
}
