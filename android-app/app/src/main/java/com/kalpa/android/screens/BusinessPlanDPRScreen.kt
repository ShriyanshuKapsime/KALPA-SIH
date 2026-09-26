package com.kalpa.android.screens

import androidx.compose.animation.AnimatedVisibility
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
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.platform.LocalContext
import com.kalpa.android.utils.PdfGeneratorHelper
import kotlinx.coroutines.launch

// Data Models
private data class DirectoryCategory(
    val title: String,
    val itemsReady: Int,
    val icon: ImageVector,
    val items: List<DirectoryItem>
)

private data class DirectoryItem(
    val title: String,
    val subtitle: String
)

@OptIn(ExperimentalLayoutApi::class, ExperimentalMaterial3Api::class)
@Composable
fun BusinessPlanDPRScreen(
    onBackClick: () -> Unit = {},
    onContinueClick: () -> Unit = {}
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val scope = rememberCoroutineScope()
    var selectedCategory by remember { mutableStateOf<DirectoryCategory?>(null) }
    val context = LocalContext.current

    val categories = listOf(
        DirectoryCategory(
            title = "1. Core Identity & Strategy",
            itemsReady = 3,
            icon = Icons.Filled.AccountBalanceWallet,
            items = listOf(
                DirectoryItem("Executive Summary", "2 pages snapshot, objectives & target ..."),
                DirectoryItem("Entrepreneur Profile", "Promoter bio, 4 yrs livestock handling, ..."),
                DirectoryItem("Business Model & Ecosystem", "Hatchery chick sourcing + direct weekl...")
            )
        ),
        DirectoryCategory(
            title = "2. Market & Competition",
            itemsReady = 3,
            icon = Icons.Filled.Storefront,
            items = listOf(
                DirectoryItem("Local Market Catchment", "5km radius, daily demand ~1.4 tonnes, ..."),
                DirectoryItem("Competition & Buyer Network", "3 proximate farms, 42 registered dhaba..."),
                DirectoryItem("SWOT Synthesis", "Feed pricing risks mapped to pre-nego...")
            )
        ),
        DirectoryCategory(
            title = "3. Technical & CapEx Plan",
            itemsReady = 3,
            icon = Icons.Filled.Engineering,
            items = listOf(
                DirectoryItem("Operations & Cycle Scheduling", "1,000 birds/batch • 6 cycles/yr • 42-da..."),
                DirectoryItem("Itemized Project Cost (CapEx)", "Shed ₹4.80 L, Equip ₹1.70 L, Deep Well ..."),
                DirectoryItem("PMEGP Subsidy & Equity Mix", "10% Own (₹1.0L) • 25% Subsidy (₹2.5L)...")
            )
        ),
        DirectoryCategory(
            title = "4. Financial Forecasts & Risk",
            itemsReady = 5,
            icon = Icons.Filled.CurrencyRupee,
            items = listOf(
                DirectoryItem("Loan & EMI Amortization", "₹6,50,000 @ 10.5% p.a., 7-year tenure ..."),
                DirectoryItem("OpEx & Cyclical Revenue", "Feed conversion ratio 1.62 • Net revenu..."),
                DirectoryItem("Profitability, DSCR & Break-even", "Average DSCR: 1.84 • Break-even reac..."),
                DirectoryItem("Biosecurity & Price Risk Matrix", "Poultry insurance coverage + vaccine c..."),
                DirectoryItem("Implementation Timeline", "8-week Gantt: Shed building to Day-Ol...")
            )
        )
    )

    val checklist = listOf(
        "Summary", "Promoter Profile", "Business Model", 
        "Market Catchment", "Off-take", "CapEx ₹10.0L", 
        "DSCR 1.84", "Mitigation Matrix", "Timeline (8 Wks)"
    )

    val blurRadius by androidx.compose.animation.core.animateDpAsState(targetValue = if (selectedCategory != null) 12.dp else 0.dp, label = "blur")
    Scaffold(
        modifier = if (blurRadius > 0.dp) Modifier.blur(blurRadius) else Modifier,
        containerColor = KalpaScreenColors.ScreenBackgroundCream,
        bottomBar = {
            DPRBottomBar(onContinueClick = onContinueClick)
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
        ) {
            KalpaTopBar(onBackClick = onBackClick, stepText = "Page 12 of 14")

            Column(modifier = Modifier.padding(horizontal = 20.dp)) {
                Spacer(Modifier.height(8.dp))

                Text(
                    text = "Your business plan",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 26.sp,
                    fontWeight = FontWeight.Bold
                )

                Spacer(Modifier.height(16.dp))

                // Header Card
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = KalpaScreenColors.CardWhite,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Surface(
                            shape = RoundedCornerShape(8.dp),
                            color = KalpaScreenColors.OrangeBadgeBg
                        ) {
                            Icon(
                                imageVector = Icons.Filled.Description,
                                contentDescription = null,
                                tint = KalpaScreenColors.OrangeDark,
                                modifier = Modifier.padding(10.dp).size(20.dp)
                            )
                        }
                        Spacer(Modifier.width(16.dp))
                        Column {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text(
                                    text = "Bankable DPR",
                                    color = KalpaScreenColors.OrangeDark,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold
                                )
                                Spacer(Modifier.width(2.dp))
                                Icon(
                                    imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                                    contentDescription = null,
                                    tint = KalpaScreenColors.OrangeDark,
                                    modifier = Modifier.size(10.dp)
                                )
                            }
                            Spacer(Modifier.height(4.dp))
                            Text(
                                text = "Broiler Poultry (1,000 birds/cycle)",
                                color = KalpaScreenColors.TextPrimary,
                                fontSize = 14.sp,
                                fontWeight = FontWeight.Bold
                            )
                            Spacer(Modifier.height(2.dp))
                            Text(
                                text = "Banskopa Gram Panchayat, Paschim Bardhaman",
                                color = KalpaScreenColors.TextSecondary,
                                fontSize = 11.sp
                            )
                        }
                    }
                }

                Spacer(Modifier.height(16.dp))

                // Status Card (Greenish)
                Surface(
                    shape = RoundedCornerShape(16.dp),
                    color = KalpaScreenColors.StatusGreenBg
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.Top
                        ) {
                            Text(
                                text = "100% Complete & Bank-\nReady",
                                color = KalpaScreenColors.StatusGreenText,
                                fontSize = 16.sp,
                                fontWeight = FontWeight.Bold,
                                lineHeight = 22.sp,
                                modifier = Modifier.weight(1f).padding(end = 8.dp)
                            )
                            Surface(
                                shape = RoundedCornerShape(8.dp),
                                color = KalpaScreenColors.CardWhite
                            ) {
                                Text(
                                    text = "9 / 9\nverified",
                                    color = KalpaScreenColors.TextPrimary,
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    textAlign = TextAlign.Center,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                                )
                            }
                        }
                        
                        Spacer(Modifier.height(12.dp))
                        
                        Text(
                            text = "Pre-screened against current NABARD Guidelines & PMEGP 2024-25 Subsidy norms.",
                            color = KalpaScreenColors.TextPrimary,
                            fontSize = 12.sp,
                            lineHeight = 18.sp
                        )
                        
                        Spacer(Modifier.height(16.dp))
                        
                        FlowRow(
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            checklist.forEach { item ->
                                Surface(
                                    shape = RoundedCornerShape(12.dp),
                                    color = KalpaScreenColors.CardWhite
                                ) {
                                    Row(
                                        verticalAlignment = Alignment.CenterVertically,
                                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 6.dp)
                                    ) {
                                        Icon(
                                            imageVector = Icons.Filled.CheckCircle,
                                            contentDescription = null,
                                            tint = KalpaScreenColors.StatusGreenText,
                                            modifier = Modifier.size(12.dp)
                                        )
                                        Spacer(Modifier.width(4.dp))
                                        Text(
                                            text = item,
                                            color = KalpaScreenColors.TextSecondary,
                                            fontSize = 10.sp,
                                            fontWeight = FontWeight.SemiBold
                                        )
                                    }
                                }
                            }
                        }
                    }
                }

                Spacer(Modifier.height(16.dp))

                // Actions
                Button(
                    onClick = { /* TODO */ },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(48.dp),
                    shape = RoundedCornerShape(24.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = KalpaScreenColors.Orange)
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Filled.Visibility,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(Modifier.width(8.dp))
                        Text(
                            text = "Preview Full Bankable Report",
                            color = Color.White,
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(Modifier.width(8.dp))
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(16.dp)
                        )
                    }
                }
                
                Spacer(Modifier.height(12.dp))
                
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Surface(
                        modifier = Modifier.weight(1f).height(44.dp).clickable { },
                        shape = RoundedCornerShape(22.dp),
                        color = KalpaScreenColors.PillGray,
                        border = BorderStroke(1.dp, KalpaScreenColors.Divider)
                    ) {
                        Row(
                            horizontalArrangement = Arrangement.Center,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(Icons.Filled.Edit, contentDescription = null, tint = KalpaScreenColors.OrangeDark, modifier = Modifier.size(16.dp))
                            Spacer(Modifier.width(6.dp))
                            Text("Edit Sections", color = KalpaScreenColors.TextPrimary, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                        }
                    }
                    Surface(
                        modifier = Modifier.weight(1f).height(44.dp).clickable { PdfGeneratorHelper.generatePlaceholderPdf(context) },
                        shape = RoundedCornerShape(22.dp),
                        color = KalpaScreenColors.PillGray,
                        border = BorderStroke(1.dp, KalpaScreenColors.Divider)
                    ) {
                        Row(
                            horizontalArrangement = Arrangement.Center,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(Icons.Filled.PictureAsPdf, contentDescription = null, tint = KalpaScreenColors.OrangeDark, modifier = Modifier.size(16.dp))
                            Spacer(Modifier.width(6.dp))
                            Text("Export PDF", color = KalpaScreenColors.TextPrimary, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                        }
                    }
                }

                Spacer(Modifier.height(32.dp))

                // Document Live Preview
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = Icons.Filled.MenuBook,
                        contentDescription = null,
                        tint = KalpaScreenColors.OrangeDark,
                        modifier = Modifier.size(18.dp)
                    )
                    Spacer(Modifier.width(8.dp))
                    Text(
                        text = "Document Live Preview",
                        color = KalpaScreenColors.TextPrimary,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold
                    )
                }

                Spacer(Modifier.height(16.dp))

                DocumentPreviewCard()

                Spacer(Modifier.height(32.dp))

                // Sections Directory
                Text(
                    text = "Sections Directory",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "Tap any section to review, verify field notes, or re-run analysis",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 12.sp
                )

                Spacer(Modifier.height(16.dp))

                // Compact Categories List triggering BottomSheet
                categories.forEach { category ->
                    DirectoryCategoryItem(
                        category = category,
                        onClick = {
                            selectedCategory = category
                            scope.launch { sheetState.show() }
                        }
                    )
                    Spacer(Modifier.height(12.dp))
                }

                Spacer(Modifier.height(32.dp))
            }
        }
    }

    // Bottom Sheet for Directory Category Details
    if (selectedCategory != null) {
        ModalBottomSheet(
            onDismissRequest = {
                scope.launch { sheetState.hide() }.invokeOnCompletion {
                    if (!sheetState.isVisible) {
                        selectedCategory = null
                    }
                }
            },
            sheetState = sheetState,
            containerColor = KalpaScreenColors.ScreenBackgroundCream,
            dragHandle = { BottomSheetDefaults.DragHandle() }
        ) {
            selectedCategory?.let { category ->
                DirectoryCategorySheet(category = category)
            }
        }
    }
}



@Composable
private fun DocumentPreviewCard() {
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = KalpaScreenColors.CardWhite,
        border = BorderStroke(1.dp, KalpaScreenColors.Divider)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = "PMEGP / NABARD FORMAT",
                        color = KalpaScreenColors.OrangeDark,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.5.sp
                    )
                    Spacer(Modifier.height(4.dp))
                    Text(
                        text = "PROJECT APPRAISAL\nDOSSIER",
                        color = KalpaScreenColors.TextPrimary,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        lineHeight = 22.sp
                    )
                    Spacer(Modifier.height(8.dp))
                    Text(
                        text = "Prepared via KALPA Automated Appraisal\nEngine",
                        color = KalpaScreenColors.TextSecondary,
                        fontSize = 11.sp,
                        lineHeight = 16.sp
                    )
                }
                Icon(
                    imageVector = Icons.Filled.AccountBalance,
                    contentDescription = null,
                    tint = KalpaScreenColors.PillGray, // Faint watermark-like
                    modifier = Modifier.size(40.dp)
                )
            }

            Spacer(Modifier.height(24.dp))

            // Subtitle
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Bottom
            ) {
                Text(
                    text = "1. Total Project Cost & Means of Finance",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "₹ in Lakhs",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 10.sp
                )
            }
            
            Spacer(Modifier.height(8.dp))

            // Table
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(8.dp))
                    .background(KalpaScreenColors.CardWhite)
            ) {
                // Table Header
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(KalpaScreenColors.PillGray)
                        .padding(horizontal = 12.dp, vertical = 8.dp)
                ) {
                    Text("Component", color = KalpaScreenColors.TextSecondary, fontSize = 10.sp, modifier = Modifier.weight(2f))
                    Text("Amount", color = KalpaScreenColors.TextSecondary, fontSize = 10.sp, modifier = Modifier.weight(1f), textAlign = TextAlign.End)
                    Text("Share", color = KalpaScreenColors.TextSecondary, fontSize = 10.sp, modifier = Modifier.weight(0.8f), textAlign = TextAlign.End)
                }
                
                // Rows
                val rows = listOf(
                    Triple("Civil Construction (Poultry Shed)", "₹4.80 L", "48%"),
                    Triple("Cages, Feeders & Drinkers", "₹1.70 L", "17%"),
                    Triple("Electrification & Deep Tube Well", "₹1.00 L", "10%"),
                    Triple("1st Cycle Working Capital (Feed+Chicks)", "₹2.50 L", "25%")
                )
                
                rows.forEach { (comp, amt, share) ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 12.dp, vertical = 10.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(comp, color = KalpaScreenColors.TextSecondary, fontSize = 11.sp, lineHeight = 14.sp, modifier = Modifier.weight(2f))
                        Text(amt, color = KalpaScreenColors.TextPrimary, fontSize = 11.sp, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f), textAlign = TextAlign.End)
                        Text(share, color = KalpaScreenColors.TextSecondary, fontSize = 11.sp, modifier = Modifier.weight(0.8f), textAlign = TextAlign.End)
                    }
                    HorizontalDivider(color = KalpaScreenColors.Divider, thickness = 0.5.dp)
                }
                
                // Total Row
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(KalpaScreenColors.OrangeBadgeBg)
                        .padding(horizontal = 12.dp, vertical = 12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("Total Project Cost", color = KalpaScreenColors.OrangeDark, fontSize = 11.sp, fontWeight = FontWeight.Bold, modifier = Modifier.weight(2f))
                    Text("₹10.00 L", color = KalpaScreenColors.OrangeDark, fontSize = 12.sp, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f), textAlign = TextAlign.End)
                    Text("100%", color = KalpaScreenColors.OrangeDark, fontSize = 11.sp, fontWeight = FontWeight.Bold, modifier = Modifier.weight(0.8f), textAlign = TextAlign.End)
                }
            }
            
            Spacer(Modifier.height(16.dp))
            
            // Means of Finance
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("Promoter Equity\n(10%)", color = KalpaScreenColors.TextSecondary, fontSize = 9.sp, textAlign = TextAlign.Center, lineHeight = 12.sp)
                    Spacer(Modifier.height(4.dp))
                    Text("₹1.00 Lakh", color = KalpaScreenColors.TextPrimary, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("Govt Subsidy\n(25%)", color = KalpaScreenColors.TextSecondary, fontSize = 9.sp, textAlign = TextAlign.Center, lineHeight = 12.sp)
                    Spacer(Modifier.height(4.dp))
                    Text("₹2.50 Lakh", color = KalpaScreenColors.StatusGreenText, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("Term Loan (65%)", color = KalpaScreenColors.TextSecondary, fontSize = 9.sp, textAlign = TextAlign.Center, lineHeight = 12.sp)
                    Spacer(Modifier.height(4.dp))
                    Text("₹6.50 Lakh", color = KalpaScreenColors.OrangeDark, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                }
            }
            
            Spacer(Modifier.height(24.dp))
            
            Surface(
                modifier = Modifier.fillMaxWidth().clickable { },
                shape = RoundedCornerShape(8.dp),
                color = KalpaScreenColors.PillGray
            ) {
                Row(
                    modifier = Modifier.padding(12.dp),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("Expand 18-Page Institutional Draft", color = KalpaScreenColors.OrangeDark, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    Spacer(Modifier.width(4.dp))
                    Icon(Icons.Filled.OpenInNew, contentDescription = null, tint = KalpaScreenColors.OrangeDark, modifier = Modifier.size(12.dp))
                }
            }
        }
    }
}

@Composable
private fun DirectoryCategoryItem(category: DirectoryCategory, onClick: () -> Unit) {
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
                    .background(KalpaScreenColors.PillGray, RoundedCornerShape(8.dp)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = category.icon,
                    contentDescription = null,
                    tint = KalpaScreenColors.OrangeDark,
                    modifier = Modifier.size(20.dp)
                )
            }
            Spacer(Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = category.title,
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(4.dp))
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = KalpaScreenColors.StatusGreenBg
                ) {
                    Text(
                        text = "${category.itemsReady} items ready",
                        color = KalpaScreenColors.StatusGreenText,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }
            }
            Spacer(Modifier.width(8.dp))
            Icon(
                imageVector = Icons.Filled.KeyboardArrowDown,
                contentDescription = null,
                tint = KalpaScreenColors.TextSecondary
            )
        }
    }
}

@Composable
private fun DirectoryCategorySheet(category: DirectoryCategory) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 24.dp, vertical = 16.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(
                imageVector = category.icon,
                contentDescription = null,
                tint = KalpaScreenColors.OrangeDark,
                modifier = Modifier.size(24.dp)
            )
            Spacer(Modifier.width(12.dp))
            Text(
                text = category.title,
                color = KalpaScreenColors.TextPrimary,
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.weight(1f)
            )
        }
        
        Spacer(Modifier.height(16.dp))
        
        category.items.forEach { item ->
            Surface(
                shape = RoundedCornerShape(12.dp),
                color = KalpaScreenColors.PillGray,
                modifier = Modifier.fillMaxWidth().clickable { }
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Row(verticalAlignment = Alignment.Top, modifier = Modifier.weight(1f)) {
                        Icon(
                            imageVector = Icons.Filled.CheckCircleOutline,
                            contentDescription = null,
                            tint = KalpaScreenColors.StatusGreenText,
                            modifier = Modifier.size(18.dp).padding(top = 2.dp)
                        )
                        Spacer(Modifier.width(12.dp))
                        Column {
                            Text(
                                text = item.title,
                                color = KalpaScreenColors.TextPrimary,
                                fontSize = 14.sp,
                                fontWeight = FontWeight.Bold
                            )
                            Spacer(Modifier.height(4.dp))
                            Text(
                                text = item.subtitle,
                                color = KalpaScreenColors.TextSecondary,
                                fontSize = 12.sp,
                                maxLines = 1,
                                overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis
                            )
                        }
                    }
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                        contentDescription = null,
                        tint = KalpaScreenColors.TextMuted,
                        modifier = Modifier.size(16.dp)
                    )
                }
            }
            Spacer(Modifier.height(8.dp))
        }
        
        Spacer(Modifier.height(32.dp))
    }
}

@Composable
private fun DPRBottomBar(onContinueClick: () -> Unit) {
    Surface(color = KalpaScreenColors.ScreenBackgroundCream) {
        Row(
            modifier = Modifier.padding(20.dp).fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Button(
                onClick = onContinueClick,
                modifier = Modifier
                    .weight(1f)
                    .height(54.dp),
                shape = RoundedCornerShape(27.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = KalpaScreenColors.OrangeDark
                )
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = Icons.Filled.Visibility,
                        contentDescription = null,
                        tint = Color.White,
                        modifier = Modifier.size(18.dp)
                    )
                    Spacer(Modifier.width(8.dp))
                    Text(
                        text = "View Full DPR",
                        color = Color.White,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
            
            IconButton(
                onClick = { },
                modifier = Modifier
                    .size(54.dp)
                    .background(KalpaScreenColors.OrangeDark, CircleShape)
            ) {
                Icon(
                    imageVector = Icons.Filled.Share,
                    contentDescription = "Share",
                    tint = Color.White
                )
            }
        }
    }
}

@Preview
@Composable
fun BusinessPlanDPRScreenPreview() {
    MaterialTheme {
        BusinessPlanDPRScreen()
    }
}
